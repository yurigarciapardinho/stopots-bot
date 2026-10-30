"""Sonda privada em quatro rodadas: caso de STOP na letra I e pacote instalado."""
import asyncio
from dataclasses import asdict
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import sys
import tempfile
import time
import uuid

from stopots_lab import Lab, RUNTIME
from validate_v2 import configure
from validate_public_v2 import cli_completion
from stopots_v2 import __version__
from stopots_v2.adapters.web import StopotsWeb, ADAPTER_VERSION
from stopots_v2.application import Controller, EventLog, Planner, Policy
from stopots_v2.domain import Kind, Phase, Status
from stopots_v2.vocabulary import Vocabulary, atomic_write, canonical

WORK=Path(__file__).resolve().parents[1]
POOL=['Vestuário','Série','Time Esportivo','FLV','Cantor','Sabor de Sorvete','Vilão',
      'Instrumento Musical','Tem na academia','Game','Sobrenome','Palavra em Inglês',
      'Profissão','Animal','Objeto','Ave']


class ProbeLab(Lab):
    async def observe(self, player='principal', save=False):
        return await super().observe(player,False)


async def main():
    from playwright.async_api import async_playwright
    run=uuid.uuid4().hex[:12];lab=ProbeLab();child=None
    dest=WORK/f'evidence/v2/curadoria-{run}.json';control=RUNTIME/f'controle-curadoria-{run}.json'
    log=RUNTIME/f'curadoria-{run}-cli.log';events=RUNTIME/f'curadoria-{run}-cli.jsonl'
    vocab=Vocabulary.bundled()
    report={'schema_version':1,'run_id':run,'subject':'installed-cli-private-FIMO-curated-I','status':'preparing',
      'observed_at':datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),
      'versions':{'package':__version__,'adapter':ADAPTER_VERSION,'vocabulary':vocab.version},
      'scenario':{'private':True,'controlled_clients':2,'letters':list('FIMO'),'pool':POOL,'configured_rounds':4,'time_mode':'Rápido'},
      'assertions':{},'final_result_verified':False,'cleanup':{},
      'limitations':['Cenário privado FIMO; não certifica autonomia pública nem todas as modalidades.','Uma resposta e a tentativa parcial de STOP são sondas separadas do adaptador, antes da retomada da CLI.','Tempos são desde a primeira observação de escrita; mínimo universal não estabelecido.']}
    def save():atomic_write(dest,canonical(report)+b'\n')
    try:
        if 'site-packages' not in __import__('stopots_v2').__file__:raise ValueError('Sonda exige wheel instalado')
        wheel=RUNTIME/f'dist/stopots_bot-{__version__}-py3-none-any.whl'
        report['versions']['wheel_sha256']=hashlib.sha256(wheel.read_bytes()).hexdigest()
        os.environ['TMPDIR']=str(RUNTIME/'tmp');tempfile.tempdir=None
        lab.pw=await async_playwright().start()
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        lab.browser=await lab.pw.chromium.launch(channel='chrome',headless=True,args=[f'--remote-debugging-port={port}'])
        lab.guest_browser=await lab.pw.chromium.launch(channel='chrome',headless=True)
        lab.context=await lab.browser.new_context(locale='pt-BR')
        lab.pages['principal']=await lab.context.new_page()
        report['versions']['chrome']=lab.browser.version
        await lab.create_private();await configure(lab,pool=POOL,letters='FIMO')
        speed=lab.pages['host'].locator('select').filter(has=lab.pages['host'].locator('option',has_text='Rápido'))
        await speed.select_option(label='Rápido')
        ports={who:StopotsWeb(lab.pages[who]) for who in ('host','convidado')}
        guest=Controller(ports['convidado'],vocab,Policy(request_stop=False,set_votes=True,confirm_review=True,continue_results=True),
                         EventLog(RUNTIME/f'curadoria-{run}-guest.jsonl'))
        atomic_write(control,b'{"paused":true}\n')
        with log.open('wb') as output:
            child=await asyncio.create_subprocess_exec(str(Path(sys.executable).with_name('stopots-v2')),'executar',
              '--cdp',f'http://127.0.0.1:{port}','--url',lab.pages['host'].url,'--modo','automatico',
              '--stop','--votos','--avaliar','--continuar','--eventos',str(events),'--controle',str(control),
              '--tempo-limite','630',stdout=output,stderr=asyncio.subprocess.STDOUT)
        for p in ports.values():await p.observe()
        await lab.click('host','INICIAR')
        report['status']='playing';save();print(json.dumps({'run_id':run,'status':'playing'}),flush=True)
        anchor=None;one_fill=False;partial=None;rankings={};finals={};target_round=None;deadline=time.monotonic()+620
        while time.monotonic()<deadline:
            obs=await ports['host'].observe()
            if obs.phase==Phase.WRITING and obs.letter=='I' and partial is None:
                atomic_write(control,b'{"paused":true}\n')
            await guest.step()
            report['stage']={'phase':obs.phase,'notice_code':obs.notice.code if obs.notice else None,'fields':len(obs.fields),'round':obs.context.round_index}
            if obs.notice and obs.notice.code=='UNKNOWN':
                node=lab.pages['host'].locator(obs.notice.ref)
                if await node.count()==1:
                    text=await node.inner_text()
                    report['startup_notice']=lab.clean(text).replace('LabHost','[host]').replace('LabGuest','[convidado]')
                raise RuntimeError('Aviso não reconhecido impediu prosseguimento')
            if child.returncode not in (None,0):raise RuntimeError('CLI encerrou antes do final')
            if obs.phase==Phase.WRITING:
                report.setdefault('round_letters',{})[str(obs.context.round_index)]=obs.letter
                if obs.letter!='I':
                    atomic_write(control,b'{"paused":false}\n')
                    save();await asyncio.sleep(.1);continue
                target_round=obs.context.round_index
                anchor=anchor or time.monotonic();elapsed=round(time.monotonic()-anchor,3)
                if obs.stop:
                    if obs.stop.enabled:report.setdefault('first_stop_enabled_s',elapsed)
                    elif 'first_stop_enabled_s' not in report:report['last_stop_disabled_s']=elapsed
                if obs.fields_stable and not one_fill:
                    action=Planner(vocab).plan(obs)
                    if not action or action.kind!=Kind.FILL:raise ValueError('Sem candidato para a primeira resposta')
                    result=await ports['host'].apply(action)
                    report['initial_adapter_fill']={'status':result.status,'category':action.expected_label}
                    one_fill=result.status==Status.APPLIED
                elif one_fill and partial is None and obs.stop and obs.stop.enabled:
                    planner=Planner(vocab,Policy(fill_blanks=False,request_stop=True,require_all_filled=False))
                    action=planner.plan(obs)
                    result=await ports['host'].apply(action);planner.record(action,result)
                    after=await ports['host'].observe()
                    partial={'status':result.status,'attempted':result.attempted,'notice_closed':after.notice is None,
                             'filled':sum(bool(f.value) for f in after.fields),'fields':len(after.fields),
                             'same_round_retry_suppressed':planner.plan(after) is None,'elapsed_s':elapsed}
                    report['partial_stop_probe']=partial
                    if result.status!=Status.BLOCKED or after.notice is not None:raise ValueError('Recusa não reconhecida ou aviso não fechado')
                    atomic_write(control,b'{"paused":false}\n');report['cli_resumed']=True
                report['writing']={'letter':obs.letter,'fields':len(obs.fields),'filled':sum(bool(f.value) for f in obs.fields),'stable':obs.fields_stable}
                if len(obs.fields)==12 and all(f.value for f in obs.fields):report['all_fields_filled_verified']=True
            if partial and obs.context.round_index==target_round and obs.phase in (Phase.REVIEW,Phase.ROUND_RESULT):
                report.setdefault('accepted_stop_transition_s',round(time.monotonic()-anchor,3))
            if obs.phase==Phase.REVIEW and obs.context.round_index==target_round:
                steps=report.setdefault('review_steps',[])
                if obs.context.review_index not in steps:steps.append(obs.context.review_index)
            for who,o in [('host',obs),('convidado',guest.last_observation)]:
                if o and o.phase==Phase.ROUND_RESULT and o.ranking and o.context.round_index==target_round:rankings[who]=asdict(o.ranking)
                if o and o.phase==Phase.FINAL_RESULT and o.ranking:finals[who]=asdict(o.ranking)
            if len(finals)==2:
                report['rankings']=rankings;report['finals']=finals;report['final_result_verified']=True;save()
                if child.returncode is None:await asyncio.wait_for(child.wait(),8)
                report['status']='probe_completed';break
            save();await asyncio.sleep(.1)
        else:raise TimeoutError('Sonda excedeu o prazo')
        cli_events=[json.loads(line) for line in events.read_text().splitlines() if line]
        actions=[e for e in cli_events if e['event']=='acao']
        fills=[e for e in actions if e['kind']=='PREENCHER' and e['context']['round_index']==target_round];stops=[e for e in actions if e['kind']=='PEDIR_STOP' and e['context']['round_index']==target_round]
        report['all_fields_filled_verified']=report.get('all_fields_filled_verified',False) or any(e.get('filled')==12 and e.get('fields')==12 for e in stops)
        ids=[e['action_id'] for e in actions if e['status']=='APLICADA']
        completion=cli_completion(child.returncode,log)
        report['cli_result']=completion
        round_scores={}
        for event in cli_events:
            if event.get('phase')=='RESULTADO_RODADA' and event.get('ranking'):
                round_scores[event['context']['round_index']]=dict(event['ranking']['rows'])
        totals={}
        for values in round_scores.values():
            for alias,points in values.items():totals[alias]=totals.get(alias,0)+points
        report['cli_actions']={'fills':len(fills),'stop':len(stops),'statuses':[e['status'] for e in stops]}
        report['assertions']={'partial_stop_blocked':partial['status']=='BLOQUEADA','notice_closed':partial['notice_closed'],
          'retry_suppressed':partial['same_round_retry_suppressed'],'all_twelve_filled':report.get('all_fields_filled_verified',False),
          'cli_filled_remaining_eleven':len(fills)==11,'cli_requested_stop':bool(stops),
          'single_cli_stop_in_target_round':len(stops)==1,
          'review_observed':bool(report.get('review_steps')),'two_finals':len(finals)==2,
          'finals_agree':sorted(p for _,p in finals['host']['rows'])==sorted(p for _,p in finals['convidado']['rows']),
          'all_letters_observed':set(report.get('round_letters',{}).values())==set('FIMO'),
          'cli_exit_zero':child.returncode==0,
          'cli_final_verified':bool(completion),'round_sums_reconciled':bool(completion) and totals==dict(completion['ranking']['rows']),
          'no_duplicate_applied_ids':len(ids)==len(set(ids))}
        if not all(report['assertions'].values()):report['status']='failed'
    except Exception as e:report.update(status='failed',error=type(e).__name__)
    finally:
        if child and child.returncode is None:
            child.send_signal(signal.SIGINT)
            try:await asyncio.wait_for(child.wait(),7)
            except TimeoutError:child.kill();await child.wait()
        if child:
            report['cli_exit_code']=child.returncode
        for c in lab.test_contexts:await c.close()
        if lab.context:await lab.context.close()
        for b in (lab.guest_browser,lab.browser):
            if b:await b.close()
        if lab.pw:await lab.pw.stop()
        report['cleanup']={'owned_browsers_disconnected':all(not b.is_connected() for b in (lab.browser,lab.guest_browser) if b)}
        control.unlink(missing_ok=True);save()
        print(json.dumps({k:report.get(k) for k in ('run_id','status','error','assertions','cleanup')},ensure_ascii=False),flush=True)
    return 0 if report['status']=='probe_completed' else 1


if __name__=='__main__':raise SystemExit(asyncio.run(main()))
