"""Partidas privadas: pacote instalado controla o host; helper só monta a sala.

Invocar explicitamente. O teste nunca conecta a sala pública ou conta pessoal.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, replace
import importlib.metadata
import json
import hashlib
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import time
import uuid

from stopots_lab import Lab, ROOT, RUNTIME, URL
from stopots_v2 import __version__
from stopots_v2.adapters.web import ADAPTER_VERSION, StopotsWeb
from stopots_v2.application import Controller, EventLog, Policy
from stopots_v2.domain import Kind, Phase, Status
from stopots_v2.normalization import lookup, game_value
from stopots_v2.vocabulary import Vocabulary, atomic_write, canonical

POOL = ["Profissão", "Programa de TV", "Fantasia", "Vilão", "Animal", "Carro", "Brinquedo", "Objeto",
        "Sabor de Pizza", "Palavra em Inglês", "Tem na academia", "Remédio", "Comida", "Time Esportivo", "Música", "Ave"]
WORKTREE = Path(__file__).resolve().parents[1]


class ProbeComplete(Exception):
    pass


class Observer:
    """O host é escrito pelo processo CLI; o ensaio só observa."""
    def __init__(self, port):
        self.port = port
        self.last_observation = None
    async def step(self):
        self.last_observation = await self.port.observe()
        return self.last_observation, None


async def wait(predicate, timeout=15):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if await predicate():
            return
        await asyncio.sleep(.1)
    raise TimeoutError("Pós-condição da configuração não observada")


async def configure(lab):
    page = lab.pages["host"]
    # O compartilhamento pode abrir depois da entrada do convidado.
    share = page.locator('.popupSystem.share').filter(visible=True)
    try:
        await share.wait_for(state='visible', timeout=3000)
    except Exception as exc:
        from playwright.async_api import TimeoutError as PWTimeout
        if not isinstance(exc, PWTimeout):
            raise
    async def dismiss_share():
        if await share.count():
            close = share.locator('button.close')
            if await share.count() != 1 or await close.count() != 1:
                raise ValueError('Compartilhamento ambíguo')
            await close.click(timeout=4000)
            await share.wait_for(state='hidden', timeout=4000)
    await dismiss_share()
    themes = page.locator('.listThemes .theme')
    labels = await themes.all_inner_texts()
    for label in labels:
        await dismiss_share()
        row = themes.filter(has_text=re.compile('^' + re.escape(label.strip()) + '$'))
        if await row.count() != 1:
            raise ValueError("Tema de configuração ambíguo")
        await row.locator('button.del').click(timeout=4000)
        async def removed(row=row):
            return await row.count() == 0
        await wait(removed)
    for label in POOL:
        await dismiss_share()
        await page.get_by_placeholder('Categoria', exact=True).fill(label)
        await page.get_by_role('button', name='ADD', exact=True).click(timeout=4000)
        async def added(label=label):
            return await themes.filter(has_text=re.compile('^' + re.escape(label) + '$')).count() == 1
        try:
            await wait(added)
        except TimeoutError:
            raise ValueError('Tema não inserido: ' + label + '; temas=' + repr(await themes.all_text_contents()))
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        target = page.locator('[id=' + json.dumps(letter) + ']')
        if await target.count() != 1:
            raise ValueError("Letra de configuração ambígua")
        desired = letter in 'ABCD'
        if await target.is_checked() != desired:
            await page.locator('label[for=' + json.dumps(letter) + ']').click(timeout=4000)
    for who in ('host', 'convidado'):
        async def synced(who=who):
            s = await lab.observe(who)
            letters = {r['for'] for r in s['review'] if r['checked'] and re.fullmatch('[A-Z]', r['for'])}
            # O convidado recebe letras somente para leitura, sem checkboxes.
            letters_ok = letters == set('ABCD') if who == 'host' else 'LETRAS (4)' in s['headings']
            return set(lookup(x) for x in await lab.pages[who].locator('.listThemes .theme').all_inner_texts()) == set(map(lookup, POOL)) and letters_ok
        try:
            await wait(synced)
        except TimeoutError:
            s = await lab.observe(who)
            raise ValueError('Configuração não sincronizada: ' + who + '; temas=' + repr(await lab.pages[who].locator('.listThemes .theme').all_text_contents()) + '; letras=' + repr([r for r in s['review'] if re.fullmatch('[A-Z]',r['for'])]))


async def diagnostic(page):
    # Só títulos/controles e estrutura do painel; nunca body, chat ou perfil.
    return await page.evaluate('''() => {
      const visible=e=>!!e.getClientRects().length && getComputedStyle(e).visibility!=='hidden';
      const hs=[...document.querySelectorAll('h1,h2,h3,h4,h5,h6,legend')].filter(visible);
      const titles=hs.map(x=>x.innerText);
      const relevant=hs.filter(x=>/VALIDE AS RESPOSTAS|RANKING/.test(x.innerText));
      const panels=relevant.map(x=>{const copy=x.parentElement.parentElement.cloneNode(true);copy.querySelectorAll('svg,figure,img,script').forEach(e=>e.remove());return copy.outerHTML.replace(/jsx-[a-z0-9]+/g,'').slice(0,22000)});
      return {titles,panels,text:(document.querySelector('main')?.innerText||'').slice(0,12000),buttons:[...document.querySelectorAll('button')].filter(visible).map(e=>({text:e.innerText,disabled:e.disabled}))};
    }''')


async def main(args):
    from playwright.async_api import async_playwright
    run_id = uuid.uuid4().hex[:12]
    dest = WORKTREE / 'evidence/v2' / f'{run_id}.json'
    evidence = {"schema_version": 1, "run_id": run_id, "subject": "v2-package", "status": "running",
                "observed_at": time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                "versions": {"package": __version__, "adapter": ADAPTER_VERSION,
                             "playwright": importlib.metadata.version('playwright')},
                "scenario": {"private": True, "participants": 2, "category_pool": POOL, "letters": list('ABCD'),
                             "rounds": 4, "stop_mode": "Padrão", "time_mode": "Mais lento", "matches_requested": args.partidas,
                             "edge_probe": args.casos_limite},
                "matches": [], "assertions": [], "final_result_verified": False, "cleanup": {}}
    vocab = Vocabulary.bundled()
    evidence['versions']['vocabulary'] = vocab.version
    def save():
        atomic_write(dest, canonical(evidence) + b'\n')
    lab = Lab()
    children = []
    live = RUNTIME / ('v2-live-'+run_id+'.json')
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / 'tmp').mkdir(exist_ok=True)
    os.environ['TMPDIR'] = str(RUNTIME / 'tmp')
    tempfile.tempdir = None
    import stopots_v2
    package_root = Path(stopots_v2.__file__).parent
    evidence['versions']['package_sha256'] = hashlib.sha256(canonical({
        str(p.relative_to(package_root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(package_root.rglob('*')) if p.is_file() and p.suffix in ('.py', '.js', '.json')})).hexdigest()
    evidence['subject'] = 'v2-cli-package' if args.cli else 'v2-package'
    try:
        lab.pw = await async_playwright().start()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            cdp_port = sock.getsockname()[1]
        lab.browser = await lab.pw.chromium.launch(channel='chrome', headless=not args.visivel,
                                                  args=[f'--remote-debugging-port={cdp_port}'] if args.cli else [])
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            guest_port = sock.getsockname()[1]
        lab.guest_browser = await lab.pw.chromium.launch(channel='chrome', headless=True,
                                                       args=[f'--remote-debugging-port={guest_port}'] if args.cli else [])
        lab.context = await lab.browser.new_context(locale='pt-BR')
        lab.pages['principal'] = await lab.context.new_page()
        evidence['versions']['chrome'] = lab.browser.version
        print(json.dumps({'run_id': run_id, 'status': 'iniciado', 'path': str(dest)}), flush=True)
        for match_index in range(1, args.partidas + 1):
            match = {"index": match_index, "status": "preparando", "rounds": {}, "final": {}, "actions": [], "diagnostic": {}}
            evidence['matches'].append(match)
            save()
            await lab.create_private()
            await configure(lab)
            if args.cli:
                live.write_text(json.dumps({'pid':os.getpid(), 'host':{'endpoint':f'http://127.0.0.1:{cdp_port}','url':lab.pages['host'].url},
                                             'convidado':{'endpoint':f'http://127.0.0.1:{guest_port}','url':lab.pages['convidado'].url}}))
                live.chmod(0o600)
            ports = {who: StopotsWeb(lab.pages[who]) for who in ('host', 'convidado')}
            controllers = {who: Controller(ports[who], vocab,
                           Policy(fill_blanks=not (args.casos_limite and who=='convidado'),
                                  request_stop=not (args.casos_limite and who=='convidado'), set_votes=True, confirm_review=True,
                                  continue_results=not args.casos_limite,
                                  seed='validacao-'+who),
                           EventLog(RUNTIME / f'v2-{run_id}-{match_index}-{who}.jsonl')) for who in ports}
            cli_process = None
            cli_log = RUNTIME / f'v2-{run_id}-{match_index}-cli.log'
            cli_events = RUNTIME / f'v2-{run_id}-{match_index}-cli.jsonl'
            if args.cli:
                output = cli_log.open('wb')
                try:
                    cli_process = await asyncio.create_subprocess_exec(
                        str(Path(sys.executable).with_name('stopots-v2')), 'executar',
                        '--cdp', f'http://127.0.0.1:{cdp_port}', '--url', lab.pages['host'].url,
                        '--modo', 'automatico', '--stop', '--votos', '--avaliar', '--continuar',
                        '--eventos', str(cli_events), '--controle', str(RUNTIME / f'controle-{run_id}-{match_index}.json'),
                        '--tempo-limite', str(args.tempo_limite), stdout=output, stderr=asyncio.subprocess.STDOUT)
                finally:
                    output.close()
                children.append(cli_process)
                controllers['host'] = Observer(ports['host'])
            # Fixa regras de sala antes do início; configurações somem durante escrita.
            for port in ports.values():
                await port.observe()
            await lab.click('host', 'INICIAR')
            match['status'] = 'jogando'
            save()
            deadline = time.monotonic() + args.tempo_limite
            anchors = {}
            last_save = 0
            last_diagnostic = {}
            edge = None
            while time.monotonic() < deadline and len(match['final']) < 2:
                if args.casos_limite and edge is None:
                    obs = await ports['convidado'].observe()
                    if obs.phase == Phase.WRITING and obs.fields_stable and len(obs.fields)>=3:
                        expected = {}
                        for i, field in enumerate(obs.fields):
                            candidate = vocab.choose(field.label, obs.letter, field.max_length, 'edge')
                            if not candidate:
                                raise ValueError('Sonda sem candidato para tema')
                            value = 'ZEBRA' if i==0 else ('' if i==1 else (obs.letter+'XYZ' if i==2 else candidate[1]))
                            await lab.pages['convidado'].locator(field.ref).fill(value)
                            expected[field.ref] = game_value(value)
                        await lab.pages['convidado'].locator(obs.fields[-1].ref).press('Tab')
                        actual = await ports['convidado'].observe()
                        if any(expected.get(f.ref)!=f.value for f in actual.fields):
                            raise ValueError('Valores de teste do convidado não confirmados')
                        edge = {'round':obs.context.round_index,'letter':obs.letter,
                                'wrong_theme':obs.fields[0].label,'wrong_answer':'ZEBRA',
                                'blank_theme':obs.fields[1].label,'blank_confirmed':not actual.fields[1].value,
                                'unknown_theme':obs.fields[2].label,'unknown_answer':obs.letter+'XYZ',
                                'wrong_unchecked':{},'unknown_preserved':{},'rankings':{}}
                        match['edge'] = edge
                results = await asyncio.gather(*(ctl.step() for ctl in controllers.values()))
                for who, (obs, result) in zip(controllers, results):
                    before = controllers[who].last_observation
                    if before and before.context.round_index:
                        record = match['rounds'].setdefault(str(before.context.round_index), {})
                        player = record.setdefault(who, {'review_steps':[], 'stop':{'last_disabled_s':None,'first_enabled_s':None}})
                        if before.phase==Phase.ROUND_RESULT and before.ranking:
                            player['ranking'] = asdict(before.ranking)
                        if before.phase==Phase.REVIEW:
                            if before.context.review_index not in player['review_steps']:
                                player['review_steps'].append(before.context.review_index)
                            player['review_total'] = before.review_total
                    if result:
                        event = controllers[who].events.events[-1]
                        match['actions'].append({k: v for k, v in event.items() if k in ('action_id', 'kind', 'status', 'reason') } | {'player': who})
                    index = obs.context.round_index
                    if index:
                        record = match['rounds'].setdefault(str(index), {})
                        player = record.setdefault(who, {"review_steps": [], "stop": {"last_disabled_s": None, "first_enabled_s": None}})
                        if obs.phase == Phase.WRITING:
                            anchor = anchors.setdefault((index, who), time.monotonic())
                            player.update(letter=obs.letter, fields=len(obs.fields), labels=[f.label for f in obs.fields],
                                          filled=sum(bool(f.value) for f in obs.fields), stable=obs.fields_stable)
                            if obs.stop:
                                elapsed = round(time.monotonic() - anchor, 3)
                                if obs.stop.enabled and player['stop']['first_enabled_s'] is None:
                                    player['stop']['first_enabled_s'] = elapsed
                                elif not obs.stop.enabled and player['stop']['first_enabled_s'] is None:
                                    player['stop']['last_disabled_s'] = elapsed
                        elif obs.phase == Phase.REVIEW:
                            step = obs.context.review_index
                            if step not in player['review_steps']:
                                player['review_steps'].append(step)
                            player['review_total'] = obs.review_total
                            player['max_groups'] = max(player.get('max_groups', 0), len(obs.groups))
                            player.setdefault('themes', {})[str(step)] = obs.review_theme
                            if edge:
                                for group in obs.groups:
                                    if lookup(obs.review_theme or '') == lookup(edge['wrong_theme']) and group.text == edge['wrong_answer']:
                                        edge['wrong_unchecked'][who] = not group.checked
                                    if lookup(obs.review_theme or '') == lookup(edge['unknown_theme']) and group.text == edge['unknown_answer']:
                                        edge['unknown_preserved'][who] = group.checked
                        elif obs.phase == Phase.ROUND_RESULT and obs.ranking:
                            player['ranking'] = asdict(obs.ranking)
                            if edge:
                                edge['rankings'][who] = asdict(obs.ranking)
                    if obs.phase == Phase.FINAL_RESULT and obs.ranking:
                        match['final'][who] = asdict(obs.ranking)
                        print(json.dumps({'match': match_index, 'player': who, 'final': asdict(obs.ranking)}), flush=True)
                    if obs.phase in (Phase.UNKNOWN, Phase.ROUND_RESULT, Phase.FINAL_RESULT):
                        key = who + ':' + str(index) + ':' + obs.phase
                        if key not in match['diagnostic'] or (obs.phase==Phase.UNKNOWN and time.monotonic()-last_diagnostic.get(key,0)>2):
                            diag = await diagnostic(lab.pages[who])
                            safe = re.sub(r'Anonimo\d+|LabHost|LabGuest', '[participante]', json.dumps(diag, ensure_ascii=False))
                            match['diagnostic'][key] = lab.clean(json.loads(safe))
                            last_diagnostic[key] = time.monotonic()
                        if args.sondar_ranking and obs.phase == Phase.ROUND_RESULT:
                            save()
                            raise ProbeComplete()
                if edge and len(edge['rankings'])==2:
                    evidence['assertions'] = [
                        {'id':'blank_preserved','passed':edge['blank_confirmed']},
                        {'id':'wrong_initial_unchecked','passed':edge['wrong_unchecked']=={'host':True,'convidado':True}},
                        {'id':'unknown_preserved','passed':edge['unknown_preserved']=={'host':True,'convidado':True}},
                        {'id':'round_rankings','passed':True}]
                    if not all(a['passed'] for a in evidence['assertions']):
                        raise ValueError('Sonda de casos limite falhou: '+repr(evidence['assertions']))
                    save()
                    raise ProbeComplete()
                if time.monotonic() - last_save > 2:
                    match['stage'] = {who: {'phase': ctl.last_observation.phase, 'round': ctl.last_observation.context.round_index,
                        'review': ctl.last_observation.context.review_index, 'connected': ctl.last_observation.connected,
                        'fields': len(ctl.last_observation.fields), 'filled': sum(bool(f.value) for f in ctl.last_observation.fields),
                        'theme': ctl.last_observation.review_theme, 'stop': asdict(ctl.last_observation.stop) if ctl.last_observation.stop else None}
                        for who, ctl in controllers.items() if ctl.last_observation}
                    save()
                    last_save = time.monotonic()
                await asyncio.sleep(.15)
            if cli_process:
                if cli_process.returncode is None and len(match['final']) == 2:
                    await asyncio.wait_for(cli_process.wait(), 8)
                match['cli_exit_code'] = cli_process.returncode
                output = cli_log.read_text(encoding='utf-8')
                start = output.rfind('\n{')
                if start >= 0:
                    try:
                        match['cli_result'] = json.loads(output[start+1:])
                    except ValueError:
                        pass
                if cli_events.exists():
                    cli_actions = [json.loads(line) for line in cli_events.read_text().splitlines() if line]
                    match['actions'].extend({k: v for k, v in event.items() if k in ('action_id', 'kind', 'status', 'reason')} | {'player': 'host'}
                                            for event in cli_actions if event['event'] == 'acao')
            assertions = []
            def assertion(cid, passed, detail):
                assertions.append({'id': cid, 'passed': bool(passed), 'detail': detail})
            assertion('four_rounds', set(match['rounds']) == {'1','2','3','4'}, 'Todas as quatro rodadas observadas')
            for index, record in match['rounds'].items():
                for who in ports:
                    p = record.get(who, {})
                    assertion(f'fields_{index}_{who}', p.get('fields', 0) > 0 and p.get('filled') == p.get('fields'), 'Campos reais preenchidos e lidos')
                    assertion(f'reviews_{index}_{who}', p.get('review_total', 0) > 0 and set(p['review_steps']) == set(range(1,p['review_total']+1)), 'Todas as etapas da mesma rodada')
                    assertion(f'ranking_{index}_{who}', bool(p.get('ranking',{}).get('rows')), 'Ranking da rodada capturado')
            assertion('final_both', len(match['final']) == 2, 'Final capturado em ambos os participantes')
            applied = [(a['player'],a['action_id']) for a in match['actions'] if a['status'] == Status.APPLIED]
            assertion('no_duplicate_applied', len(applied) == len(set(applied)), 'Nenhuma ação aplicada duas vezes com o mesmo ID')
            for who, final in match['final'].items():
                totals = {}
                for record in match['rounds'].values():
                    for pid, points in record.get(who,{}).get('ranking',{}).get('rows',[]):
                        totals[pid] = totals.get(pid,0) + points
                assertion('reconciled_'+who, totals == dict(final['rows']), {'sum_rounds': totals, 'final':dict(final['rows'])})
            if cli_process:
                assertion('distributed_cli', match['cli_exit_code'] == 0 and match.get('cli_result',{}).get('final_result_verified'), 'Comando distribuído encerrou com captura final')
            match['assertions'] = assertions
            match['status'] = 'passed' if all(a['passed'] for a in assertions) else 'failed'
            if match['status'] != 'passed':
                for who in ports:
                    diag = await diagnostic(lab.pages[who])
                    # Nomes dos participantes controlados também ficam fora do dump.
                    text = json.dumps(diag, ensure_ascii=False)
                    text = re.sub(r'Anonimo\d+|LabHost|LabGuest', '[participante]', text)
                    match['diagnostic'][who] = json.loads(text)
                save()
                raise RuntimeError('Partida não satisfez todas as assertions; diagnóstico salvo')
            save()
        evidence['final_result_verified'] = all(len(m['final']) == 2 for m in evidence['matches'])
        evidence['status'] = 'passed'
    except ProbeComplete:
        evidence.update(status='probe_completed')
    except asyncio.CancelledError:
        evidence.update(status='interrupted', error='Execução interrompida')
        raise
    except Exception as exc:
        evidence.update(status='failed', error=type(exc).__name__ + ': ' + lab.clean(str(exc))[:1800])
        if evidence['matches']:
            for who in ('host', 'convidado'):
                if who in lab.pages and not lab.pages[who].is_closed():
                    try:
                        s = await lab.observe(who)
                        evidence['matches'][-1]['diagnostic'].setdefault(who, {
                            'phase': s['phase'], 'headings': s['headings'],
                            'themes': await lab.pages[who].locator('.listThemes .theme').all_text_contents(),
                            'letters': [r for r in s['review'] if re.fullmatch('[A-Z]',r['for'])]})
                    except Exception:
                        pass
        print(json.dumps({'status': 'failed', 'reason': evidence['error']}), flush=True)
    finally:
        live.unlink(missing_ok=True)
        for child in children:
            if child.returncode is None:
                child.terminate()
                try:
                    await asyncio.wait_for(child.wait(), 5)
                except TimeoutError:
                    child.kill()
                    await child.wait()
        for ctx in lab.test_contexts:
            await ctx.close()
        if lab.context:
            await lab.context.close()
        for browser in (lab.guest_browser, lab.browser):
            if browser:
                await browser.close()
        if lab.pw:
            await lab.pw.stop()
        evidence['cleanup'] = {'owned_contexts_closed': all(c not in b.contexts for b in (lab.guest_browser, lab.browser) if b for c in lab.test_contexts),
                               'owned_browsers_disconnected': all(not b.is_connected() for b in (lab.guest_browser, lab.browser) if b)}
        save()
        print(json.dumps({'run_id': run_id, 'status': evidence['status'], 'final_result_verified': evidence['final_result_verified'], 'cleanup': evidence['cleanup']}), flush=True)
    return 0 if evidence['status'] in ('passed', 'probe_completed') else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validação privada explícita do pacote v2')
    parser.add_argument('--partidas', type=int, default=1)
    parser.add_argument('--tempo-limite', type=float, default=650)
    parser.add_argument('--visivel', action='store_true')
    parser.add_argument('--sondar-ranking', action='store_true', help='Encerra após capturar estrutura do primeiro ranking; não certifica partida')
    parser.add_argument('--cli', action='store_true', help='Executa o comando distribuído como único escritor do host')
    parser.add_argument('--casos-limite', action='store_true', help='Sonda uma rodada com vazio, inicial errada e palavra desconhecida; não é certificação de partida')
    raise SystemExit(asyncio.run(main(parser.parse_args())))
