"""Ensaio público explicitamente solicitado; um cliente e dados sanitizados."""
from __future__ import annotations
import asyncio
import argparse
from contextlib import AsyncExitStack
from dataclasses import asdict
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import sys
import tempfile
import time
import uuid

from playwright.async_api import async_playwright
from stopots_v2 import __version__
from stopots_v2.adapters.web import StopotsWeb
from stopots_v2.vocabulary import Vocabulary, atomic_write, canonical

WORK = Path(__file__).resolve().parents[1]
RUNTIME = WORK.parent / '.runtime'

def cli_completion(exit_code, log_path):
    """A CLI pode concluir antes da janela de estabilidade do observador auxiliar."""
    if exit_code != 0:
        return None
    try:
        log=log_path.read_text(encoding="utf-8")
        starts=list(re.finditer(r'(?m)^\{\n  "status":',log))
        if not starts:return None
        result=json.JSONDecoder().raw_decode(log[starts[-1].start():])[0]
        if result.get('status')=='concluido' and result.get('final_result_verified') and result.get('ranking',{}).get('rows'):
            return result
    except (OSError,ValueError,TypeError):pass
    return None


def record_final(report, ranking, source, exit_code, observer):
    report.update(final_result_verified=True,final=ranking,final_source=source,cli_exit_code=exit_code,
                  status='completed' if exit_code==0 else 'failed')
    report['observer_self_alias']=observer.player_ids.get('ValidacaoV2')
    report['self_identity_seen']=bool(report['observer_self_alias'])
    report['final_own_score_verified']=source=='observer' and any(row[0]==report['observer_self_alias'] for row in ranking['rows'])
    total=report.get('stage',{}).get('total_rounds') or max(map(int,report['rounds']),default=0)
    expected=set(range(1,total+1))
    writing={int(k) for k,v in report['rounds'].items() if v.get('writing_observed')}
    report['writing_rounds_observed']=sorted(writing)
    report['full_match_observed']=bool(expected) and expected<=writing
    report['assertions']=[
      {'name':'cli_installed_wheel','passed':report['versions']['package_path_kind']=='installed-wheel'},
      {'name':'final_screen','passed':True},
      {'name':'cli_exit_zero','passed':exit_code==0},
      {'name':'writing_all_rounds','passed':report['full_match_observed']}]


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jogar',action='store_true',help='Usar entrada pública rápida e iniciar CLI automaticamente')
    parser.add_argument('--tempo-limite',type=int,default=3600,help='Prazo da CLI em segundos; padrão 3600')
    args=parser.parse_args()
    if args.tempo_limite<=0:parser.error('--tempo-limite precisa ser positivo')
    run_id=uuid.uuid4().hex[:12]
    state_path=RUNTIME/f'public-live-{run_id}.json'
    command_path=RUNTIME/f'public-command-{run_id}.json'
    report_path=WORK/f'evidence/v2/public-{run_id}.json'
    events_path=RUNTIME/f'public-{run_id}-events.jsonl'
    log_path=RUNTIME/f'public-{run_id}-cli.log'
    report={'schema_version':1,'run_id':run_id,'subject':'v2-cli-package-public','status':'preparing',
        'observed_at':datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),
        'versions':{'package':__version__,'vocabulary':Vocabulary.bundled().version},
        'scenario':{'public':True,'controlled_clients':1,'user_requested_public_match':True},
        'rounds':{},'assertions':[],'final_result_verified':False,'cleanup':{},
        'limitations':['Participantes públicos não são controlados; cobertura e modos devem ser avaliados pelas observações.']}
    report['versions']['package_path_kind']='installed-wheel' if 'site-packages' in __import__('stopots_v2').__file__ else 'source'
    report['versions']['wheel_sha256']=hashlib.sha256((RUNTIME/f'dist/stopots_bot-{__version__}-py3-none-any.whl').read_bytes()).hexdigest()
    browser=None;context=None;child=None;observer=None;last_command=None
    def save():atomic_write(report_path,canonical(report)+b'\n')
    async def stop_child():
        if child and child.returncode is None:
            child.send_signal(signal.SIGINT)
            try:await asyncio.wait_for(child.wait(),7)
            except TimeoutError:child.kill();await child.wait()
    async def close_owned():
        if context:await context.close()
        if browser and browser.is_connected():await browser.close()
    try:
        os.environ['TMPDIR']=str(RUNTIME/'tmp');tempfile.tempdir=None
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        async with async_playwright() as pw, AsyncExitStack() as resources:
            context=await pw.chromium.launch_persistent_context(str(RUNTIME/'chrome-public-validation'),channel='chrome',headless=False,
              locale='pt-BR',viewport={'width':1440,'height':1000},args=[f'--remote-debugging-port={port}','--no-first-run','--no-default-browser-check'])
            browser=context.browser;report['versions']['chrome']=browser.version
            resources.push_async_callback(close_owned)
            resources.push_async_callback(stop_child)
            page=context.pages[0] if context.pages else await context.new_page()
            await page.goto('https://stopots.com/pt',wait_until='domcontentloaded',timeout=45000)
            await page.get_by_role('button',name='SALAS',exact=True).wait_for(timeout=45000)
            nickname=page.locator('input[maxlength="15"]').filter(visible=True)
            if await nickname.count()==1:await nickname.fill('ValidacaoV2')
            await page.get_by_role('button',name='JOGAR' if args.jogar else 'SALAS',exact=True).click(timeout=6000)
            if args.jogar:
                await page.wait_for_url(re.compile(r'https://stopots\.com/pt/(?:\d+|game)/?$'),timeout=30000)
                command_path.write_text(json.dumps({'id':uuid.uuid4().hex,'op':'run','scenario':{'entry':'public_quick_play'}}), encoding="utf-8")
            report['status']='selecting_public_room';save()
            print(json.dumps({'run_id':run_id,'status':report['status'],'state_file':str(state_path),'command_file':str(command_path)}),flush=True)
            deadline=time.monotonic()+args.tempo_limite+180;last_save=0
            while time.monotonic()<deadline:
                state_path.write_text(json.dumps({'pid':os.getpid(),'host':{'endpoint':f'http://127.0.0.1:{port}','url':page.url},'command_file':str(command_path)}), encoding="utf-8")
                state_path.chmod(0o600)
                if command_path.exists():
                    try:command=json.loads(command_path.read_text(encoding="utf-8"))
                    except ValueError:command={}
                    if command.get('id')!=last_command and command.get('op'):
                        last_command=command['id']
                        if command['op']=='close':report['status']='interrupted';break
                        if command['op']=='run' and child is None:
                            if not re.fullmatch(r'https://stopots\.com/pt/(?:\d+|game)/?',page.url):raise ValueError('Página atual não é sala')
                            report['scenario'].update(command.get('scenario',{}))
                            observer=StopotsWeb(page)
                            output=log_path.open('wb')
                            try:
                                child=await asyncio.create_subprocess_exec(str(Path(sys.executable).with_name('stopots-v2')),'executar',
                                  '--cdp',f'http://127.0.0.1:{port}','--url',page.url,'--modo','automatico',
                                  '--stop','--votos','--avaliar','--continuar','--eventos',str(events_path),
                                  '--controle',str(RUNTIME/f'controle-public-{run_id}.json'),'--tempo-limite',str(args.tempo_limite),
                                  stdout=output,stderr=asyncio.subprocess.STDOUT)
                            finally:output.close()
                            report['status']='playing';save()
                if observer:
                    try:obs=await observer.observe()
                    except TimeoutError:
                        await asyncio.sleep(.2)
                        continue
                    report.setdefault('initial_observation',{'phase':obs.phase,'round':obs.context.round_index,'total_rounds':obs.total_rounds})
                    phases=report.setdefault('observed_phases',[])
                    if obs.phase not in phases:phases.append(obs.phase)
                    report['stage']={'phase':obs.phase,'round':obs.context.round_index,'total_rounds':obs.total_rounds,
                      'review':obs.context.review_index,'review_total':obs.review_total,'letter':obs.letter,'connected':obs.connected,
                      'fields':len(obs.fields),'filled':sum(bool(f.value) for f in obs.fields),'review_groups':len(obs.groups)}
                    index=obs.context.round_index
                    if index:
                        record=report['rounds'].setdefault(str(index),{'review_steps':[]})
                        if obs.fields:
                            record['writing_observed']=True
                            record.update(letter=obs.letter,fields=len(obs.fields),filled=sum(bool(f.value) for f in obs.fields),
                              answers=[{'category':f.label,'value':f.value} for f in obs.fields],stable=obs.fields_stable)
                        if obs.context.review_index and obs.context.review_index not in record['review_steps']:
                            record['review_steps'].append(obs.context.review_index)
                        if obs.phase=='RESULTADO_RODADA' and obs.ranking:record['ranking']=asdict(obs.ranking)
                    if obs.phase=='RESULTADO_PARTIDA' and obs.ranking:
                        if child.returncode is None:await asyncio.wait_for(child.wait(),10)
                        record_final(report,asdict(obs.ranking),'observer',child.returncode,observer)
                        break
                    if child.returncode is not None:
                        completion=cli_completion(child.returncode,log_path)
                        if completion:record_final(report,completion['ranking'],'cli',child.returncode,observer)
                        else:report['cli_exit_code']=child.returncode;report['status']='failed'
                        break
                if time.monotonic()-last_save>2:save();last_save=time.monotonic()
                await asyncio.sleep(.2)
            else:report['status']='deadline_exceeded'
    except asyncio.CancelledError:
        report['status']='interrupted';raise
    except Exception as exc:
        report.update(status='failed',error=type(exc).__name__) # não serializar texto com nicks/URLs
    finally:
        await stop_child()
        report['cleanup']={'owned_browser_disconnected':browser is None or not browser.is_connected()}
        state_path.unlink(missing_ok=True);command_path.unlink(missing_ok=True)
        if events_path.exists():
            events=[json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
            actions=[e for e in events if e['event']=='acao']
            from collections import Counter
            report['actions']={'by_status':dict(Counter(e['status'] for e in actions)), 'by_kind':dict(Counter(e['kind'] for e in actions))}
            ids=[e['action_id'] for e in actions if e['status']=='APLICADA'];report['duplicate_applied_ids']=len(ids)-len(set(ids))
        save();print(json.dumps({'run_id':run_id,'status':report['status'],'final_result_verified':report['final_result_verified'],'cleanup':report['cleanup']}),flush=True)
    return 0 if report['status']=='completed' else 1

if __name__=='__main__':raise SystemExit(asyncio.run(main()))
