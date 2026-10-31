"""Coleta breve de temas pelo JOGAR público, sem preencher ou votar."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import uuid

from playwright.async_api import async_playwright
from stopots_v2.adapters.web import StopotsWeb
from stopots_v2.domain import Phase
from stopots_v2.vocabulary import atomic_write, canonical

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT.parent / '.runtime'


async def main(entries=5):
    run = uuid.uuid4().hex[:12]
    path = ROOT / f'evidence/v2/catalogo-publico-{run}.json'
    report = {'schema_version': 1, 'run_id': run, 'subject': 'ui-only-public-topic-catalog',
              'observed_at': datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),
              'requested_entries': entries, 'entries': [], 'status': 'collecting',
              'answer_actions': 0, 'vote_actions': 0, 'stop_actions': 0,
              'limitations': ['Entradas breves; não são partidas completas nem certificação do pacote.',
                             'A rota /pt/game não identifica a sala; entradas não provam cinco servidores distintos.',
                             'Pool oculto no DOM é auxiliar e separado dos temas visíveis.'], 'cleanup': {}}
    def save():
        atomic_write(path, canonical(report) + b'\n')

    os.environ['TMPDIR'] = str(RUNTIME / 'tmp')
    tempfile.tempdir = None
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel='chrome', headless=True)
        report['chrome'] = browser.version
        try:
            for index in range(1, entries + 1):
                started = time.monotonic()
                row = {'entry': index, 'status': 'opening', 'visible_topics': [],
                       'pool_dom': [], 'writing_topics': [], 'review_topics': []}
                report['entries'].append(row)
                context = await browser.new_context(locale='pt-BR')
                try:
                    page = await context.new_page()
                    await page.goto('https://stopots.com/pt', wait_until='domcontentloaded', timeout=45000)
                    await page.get_by_role('button', name='JOGAR', exact=True).wait_for(timeout=45000)
                    nickname = page.locator('input[maxlength="15"]').filter(visible=True)
                    if await nickname.count() == 1:
                        await nickname.fill('CatalogoV2')
                    await page.get_by_role('button', name='JOGAR', exact=True).click(timeout=6000)
                    await page.wait_for_url(re.compile(r'https://stopots\.com/pt/(?:\d+|game)/?$'), timeout=30000)
                    row['route_kind'] = 'quick-play' if '/game' in page.url else 'numeric'
                    port = StopotsWeb(page)
                    deadline = time.monotonic() + 40
                    previous = None
                    stable_since = time.monotonic()
                    while time.monotonic() < deadline:
                        obs = await port.observe()
                        row['phase'] = obs.phase
                        row['round'] = obs.context.round_index
                        row['letter'] = obs.letter
                        if obs.notice:
                            row['status'] = 'blocked_by_notice'
                            row['notice_code'] = obs.notice.code
                            break
                        if obs.phase == Phase.FINAL_RESULT:
                            row['status'] = 'final_without_topics'
                            break
                        pool = await page.locator('.listThemes .theme').evaluate_all('''nodes => nodes.map(e => ({
                          label:(e.innerText || e.textContent || '').trim(),
                          visible:!!e.getClientRects().length && getComputedStyle(e).visibility!=='hidden'
                        }))''')
                        pool = [p for p in pool if p['label'] and len(p['label']) <= 120]
                        fields = [f.label.strip() for f in obs.fields if f.label.strip()]
                        review = [obs.review_theme.strip()] if obs.phase == Phase.REVIEW and obs.review_theme else []
                        visible = sorted(set(fields + review + [p['label'] for p in pool if p['visible']]))
                        signature = (obs.phase, tuple(visible), tuple(p['label'] for p in pool))
                        if signature != previous:
                            previous, stable_since = signature, time.monotonic()
                        row.update(visible_topics=visible, pool_dom=pool,
                                   writing_topics=fields, review_topics=review)
                        if visible and time.monotonic() - stable_since >= 1.3:
                            row['status'] = 'captured'
                            break
                        await asyncio.sleep(.15)
                    else:
                        row['status'] = 'no_visible_topics_in_deadline'
                    row['configuration_fingerprint'] = hashlib.sha256(canonical(sorted(p['label'] for p in row['pool_dom']))).hexdigest() if row['pool_dom'] else None
                except Exception as exc:
                    row.update(status='failed', error=type(exc).__name__)
                finally:
                    await context.close()
                    row['context_closed'] = True
                    row['elapsed_s'] = round(time.monotonic() - started, 3)
                    save()
                    print(json.dumps({k: row.get(k) for k in ('entry', 'status', 'phase', 'visible_topics', 'elapsed_s')}, ensure_ascii=False), flush=True)
            counts = Counter(topic for row in report['entries'] for topic in set(row['visible_topics']))
            report['catalog'] = [{'label': topic, 'entries_seen': count} for topic, count in sorted(counts.items())]
            report['all_entries_captured'] = all(row['status'] == 'captured' for row in report['entries'])
            report['status'] = 'completed' if report['all_entries_captured'] else 'partial'
        finally:
            await browser.close()
            report['cleanup'] = {'owned_browser_disconnected': not browser.is_connected(),
                                 'all_entry_contexts_closed': all(row.get('context_closed') for row in report['entries'])}
            save()
    print(json.dumps({'run_id': run, 'status': report['status'], 'topics': len(report.get('catalog', [])), 'cleanup': report['cleanup']}), flush=True)
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entradas', type=int, default=5, choices=range(1, 6))
    raise SystemExit(asyncio.run(main(parser.parse_args().entradas)))
