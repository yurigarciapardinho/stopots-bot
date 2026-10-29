"""Inspeção somente leitura dos contextos pertencentes ao ensaio v2 ativo."""
import argparse
import asyncio
import json
from pathlib import Path
import re


async def main(args):
    from playwright.async_api import async_playwright
    from stopots_v2.adapters.web import SNAPSHOT
    state = json.loads(args.controle.read_text())
    target = state[args.player]
    if not re.fullmatch(r'http://127\.0\.0\.1:\d+', target['endpoint']):
        raise ValueError('Endpoint local inválido')
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(target['endpoint'])
        pages = [p for c in browser.contexts for p in c.pages if p.url == target['url']]
        if len(pages) != 1:
            raise ValueError('Página do ensaio ausente ou ambígua')
        page = pages[0]
        raw = await page.evaluate(SNAPSHOT)
        detail = await page.evaluate('''() => {
          const q=s=>[...document.querySelectorAll(s)].filter(e=>e.getClientRects().length);
          return {headings:q('h1,h2,h3,h4,h5,h6').map(e=>e.innerText),
            text:(document.querySelector('main')?.innerText||'').slice(0,12000),
            buttons:q('button').map(e=>({text:e.innerText,disabled:e.disabled}))};
        }''')
        # Somente participantes anônimos criados pelo ensaio; nenhuma conta pessoal.
        result = {'phase':raw['phase'], 'round':raw.get('round_index'), 'ranking':raw.get('ranking'),
                  'fields':len(raw['fields']), 'filled':sum(bool(f['value']) for f in raw['fields']), **detail}
        if not args.detalhes:
            result.pop('text')
        safe = re.sub(r'Anonimo\d+|LabHost|LabGuest', '[participante]', json.dumps(result,ensure_ascii=False))
        safe = re.sub(r'(?:https://)?stopots\.com/pt/\d+', '[sala]', safe)
        print(safe)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Ler Chrome do ensaio em andamento; não altera a partida')
    p.add_argument('controle', type=Path, help='Arquivo privado .runtime/v2-live-ID.json')
    p.add_argument('--player', choices=['host','convidado'], default='host')
    p.add_argument('--detalhes', action='store_true')
    asyncio.run(main(p.parse_args()))
