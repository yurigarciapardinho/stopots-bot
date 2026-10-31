"""Uma partida privada dirigida pela GUI. Segredos transitam somente por Pipe."""
from __future__ import annotations
from datetime import datetime, timezone
import asyncio
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import re
import secrets
import subprocess
import time
import uuid

from stopots_v2 import __version__
import stopots_v2
from stopots_v2.adapters.web import StopotsWeb
from stopots_v2.adapters.chrome_session import ChromeSession
from stopots_v2.application import Controller, Policy
from stopots_v2.domain import Phase
from stopots_v2.vocabulary import Vocabulary

ROOT=Path(__file__).resolve().parents[1]
POOL=['Profissão','Programa de TV','Fantasia','Vilão','Animal','Carro','Brinquedo','Objeto',
      'Sabor de Pizza','Palavra em Inglês','Tem na academia','Remédio','Comida','Time Esportivo','Música','Ave']


async def wait_phase(port, phases, timeout=35):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        obs=await port.observe()
        if obs.phase in phases:return obs
        await asyncio.sleep(.15)
    raise TimeoutError('Fase esperada não apareceu')


def host_process(connection, private=True):
    async def run():
        from playwright.async_api import async_playwright, expect
        stage='host_start'
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='chrome',headless=True)
            try:
                page=await browser.new_page(locale='pt-BR',viewport={'width':1440,'height':1000})
                port=StopotsWeb(page)
                await page.goto('https://stopots.com/pt',wait_until='domcontentloaded')
                await page.locator('input[maxlength="15"]').fill('LabHost',timeout=15000)
                await page.get_by_role('button',name='CRIAR SALA',exact=True).click()
                await page.get_by_text('SALA PRIVADA' if private else 'SALA PÚBLICA',exact=True).click()
                await page.get_by_role('button',name='CONFIRMAR',exact=True).click()
                password=''
                if private:
                    password=secrets.token_hex(3)+'áÇ!$&'
                    field=page.locator('input[type="password"]').filter(visible=True)
                    stage='host_password'
                    await field.fill(password)
                    assert await field.input_value()==password
                    await page.get_by_role('button',name='OK',exact=True).click()
                await wait_phase(port,{Phase.ROOM})
                share=page.locator('.popupSystem.share').filter(visible=True)
                if await share.count():await share.locator('button.close').click()
                connection.send({'event':'room','url':page.url,'password':password})
                stage='host_wait_guest'
                while not connection.poll():await asyncio.sleep(.1)
                command=connection.recv()
                if command=='inspect':
                    count=None
                    end=time.monotonic()+10
                    while time.monotonic()<end:
                        match=re.search(r'JOGADORES\s+(\d+)\s*/',await page.locator('body').inner_text())
                        count=int(match[1]) if match else None
                        if count==2:break
                        await asyncio.sleep(.1)
                    nickname_applied='labguest' in (await page.locator('body').text_content()).casefold()
                    nickname_applied=nickname_applied or await page.evaluate('''() => [...document.querySelectorAll('*')].some(e=>[...e.attributes].some(a=>a.value.toLowerCase().includes('labguest')))''')
                    connection.send({'event':'host_entry','participants':count,'nickname_applied':nickname_applied})
                    while not connection.poll():await asyncio.sleep(.1)
                    connection.recv();return
                if command!='start':return
                stage='host_configure'
                for label in ['4 Rodadas','Mais lento']:
                    select=page.locator('select').filter(has=page.locator('option',has_text=re.compile('^'+re.escape(label)+'$')))
                    await select.select_option(label=label)
                if await share.count():await share.locator('button.close').click()
                themes=page.locator('.listThemes .theme')
                for remaining in range(await themes.count(),0,-1):
                    await themes.first.locator('button.del').click()
                    await expect(themes).to_have_count(remaining-1,timeout=5000)
                for label in POOL:
                    count=await themes.count()
                    await page.get_by_placeholder('Categoria',exact=True).fill(label)
                    await page.get_by_role('button',name='ADD',exact=True).click()
                    await expect(themes).to_have_count(count+1,timeout=5000)
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    target=page.locator('[id='+json.dumps(letter)+']')
                    if await target.is_checked() != (letter in 'ABCD'):
                        await page.locator('label[for='+json.dumps(letter)+']').click()
                assert await themes.count()==16
                await page.get_by_role('button',name='INICIAR',exact=True).click()
                stage='host_match'
                ctl=Controller(port,Vocabulary.bundled(),Policy(request_stop=True,set_votes=True,confirm_review=True,continue_results=True))
                sent=False
                end=time.monotonic()+360
                while time.monotonic()<end:
                    if connection.poll() and connection.recv()=='stop':return
                    obs,_=await ctl.step()
                    if obs.phase==Phase.FINAL_RESULT and obs.ranking and not sent:
                        connection.send({'event':'host_final','scores':sorted(score for _,score in obs.ranking.rows)})
                        sent=True
                    await asyncio.sleep(.15)
                raise TimeoutError('Partida excedeu o prazo')
            except Exception as exc:
                connection.send({'event':'error','stage':stage,'type':type(exc).__name__})
            finally:await browser.close()
    asyncio.run(run())


def gui_process(connection, runtime, mode, invitation=None):
    os.environ['STOPOTS_RUNTIME']=runtime
    os.environ['QT_QUICK_BACKEND']='software'
    from PySide6.QtCore import QTimer, QObject
    from stopots_v2.desktop import main
    started=time.monotonic();joined=False;last_progress=None
    def ready(app,bridge,window):
        nonlocal joined
        if mode in ('join','entry'):
            url,password=invitation
            bridge.setProfile('Só preencher' if mode=='entry' else 'Automático')
            window.setProperty('entryMode',1);window.setProperty('passwordChoice',1 if password else 0)
            def submit():
                def find(item,name):
                    if item.objectName()==name:return item
                    for child in item.childItems():
                        found=find(child,name)
                        if found is not None:return found
                try:
                    for name,value in [('inviteUrl',url),('nickname','LabGuest'),('roomPassword',password)]:
                        field=find(window.contentItem(),name)
                        assert field is not None,'Campo não encontrado: '+name
                        field.setProperty('text',value)
                        assert field.property('text')==value,'Valor não aplicado: '+name
                    button=find(window.contentItem(),'enterInvitation')
                    assert button is not None and button.property('enabled'),'Botão de entrada indisponível'
                    button.clicked.emit()
                except Exception as exc:
                    connection.send({'event':'error','stage':'gui_form','type':type(exc).__name__,'message':str(exc)})
                    bridge.shutdown(False)
            QTimer.singleShot(200,submit)
        def poll():
            nonlocal joined,last_progress
            s=bridge.state
            if mode == 'join' and s.get('phase') in (Phase.WRITING, Phase.REVIEW, Phase.ROUND_RESULT):
                progress={k:s.get(k) for k in ('phase','round','letter','filled','total','ranking_scope')}
                progress['scores']=sorted(x['points'] for x in s.get('ranking',[]))
                if progress != last_progress:
                    last_progress=progress
                    connection.send({'event':'gui_progress',**progress})
            if s.get('error_code'):
                diagnostic=[]
                if bridge.engine.chrome.page:
                    try:
                        future=asyncio.run_coroutine_threadsafe(bridge.engine.chrome.page.evaluate('''() => [...document.querySelectorAll('.popupSystem')].filter(e=>e.getClientRects().length).map(e=>({password:!!e.querySelector('input[type="password"]:not(:disabled)'),invitation:/Você foi convidado/i.test(e.innerText),buttons:[...e.querySelectorAll('button')].map(b=>b.innerText.trim()).filter(t=>['ENTRAR','OK','CANCELAR','FECHAR'].includes(t))}))'''),bridge.engine.loop)
                        diagnostic=future.result(timeout=3)
                    except Exception:pass
                connection.send({'event':'error','stage':'gui_entry','code':s['error_code'],'message':s['message'],'popup_signals':diagnostic})
                bridge.shutdown(False);return
            if mode in ('join','entry') and s.get('in_room') and not joined:
                joined=True;connection.send({'event':'joined','active':s['active'],'platform':app.platformName()})
                if mode=='entry':window.close();return
            if mode=='join' and s.get('phase')==Phase.FINAL_RESULT and s.get('ranking'):
                connection.send({'event':'gui_final','active':s['active'],'scores':sorted(x['points'] for x in s['ranking'])})
                window.close();return
            if mode=='reopen' and s.get('connected') and s.get('in_room'):
                connection.send({'event':'reopened','active':s['active'],'phase':s['phase']})
                window.close();return
            if time.monotonic()-started>400:
                connection.send({'event':'error','stage':'gui_timeout','phase':s.get('phase')})
                bridge.shutdown(False);return
            QTimer.singleShot(200,poll)
        poll()
    try:
        code=main(['stopots-live-check'],on_ready=ready)
        connection.send({'event':'gui_exit','code':code})
    except Exception as exc:connection.send({'event':'error','stage':'gui_process','type':type(exc).__name__})


def main():
    installed = 'site-packages' in Path(stopots_v2.__file__).resolve().parts
    if os.environ.get('STOPOTS_EXPECT_INSTALLED') == '1':
        assert installed, 'O ensaio exige wheel instalado, sem fonte editável'
    context=mp.get_context('spawn');run_id=uuid.uuid4().hex[:12]
    entry_only=os.environ.get('STOPOTS_VALIDATE_ENTRY_ONLY')=='1'
    runtime=ROOT.parent/'.runtime'/('desktop-live-'+run_id);runtime.mkdir()
    os.environ['TMPDIR']=str(ROOT.parent/'.runtime/tmp-desktop')
    host_conn,host_child=context.Pipe();host=context.Process(target=host_process,args=(host_child,not entry_only));host.start()
    gui=None;report={'schema_version':1,'run_id':run_id,'version':__version__,'subject':'desktop-gui-installed-wheel' if installed else 'desktop-gui-source','installed_wheel':installed,
                     'scenario':{'private':not entry_only,'participants':2,'rounds':0 if entry_only else 4,'letters':'' if entry_only else 'ABCD','pool':[] if entry_only else POOL},'events':[]}
    report['observed_at']=datetime.now(timezone.utc).isoformat()
    report['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    build=Path(os.environ.get('STOPOTS_BUILD_ROOT',ROOT/'.runtime'))
    wheels=list((build/'dist').glob('*.whl'))
    if installed and len(wheels)==1:
        report['wheel']={'name':wheels[0].name,'sha256':hashlib.sha256(wheels[0].read_bytes()).hexdigest()}
    try:
        assert host_conn.poll(75),'Host não criou a sala'
        room=host_conn.recv();assert room['event']=='room',room
        gui_conn,gui_child=context.Pipe()
        gui=context.Process(target=gui_process,args=(gui_child,str(runtime),'entry' if entry_only else 'join',(room['url'],room['password'])));gui.start()
        del room
        deadline=time.monotonic()+420;host_final=gui_final=None;entry_confirmed=False
        while time.monotonic()<deadline:
            for source,conn in [('host',host_conn),('gui',gui_conn)]:
                if conn.poll(.1):
                    event=conn.recv();report['events'].append({'source':source,**event});print(event,flush=True)
                    assert event['event']!='error',event
                    if event['event']=='joined':host_conn.send('inspect' if entry_only else 'start')
                    if event['event']=='host_entry':
                        assert event['participants']==2,event
                        assert event['nickname_applied'],event
                        entry_confirmed=True
                    if event['event']=='host_final':host_final=event['scores']
                    if event['event']=='gui_final':gui_final=event['scores'];assert event['active'] is False
            if host_final is not None and gui_final is not None:break
            if entry_only and entry_confirmed:break
        if not entry_only:assert host_final is not None and gui_final==host_final,'Finais não reconciliados'
        else:assert entry_confirmed
        gui.join(15);assert gui.exitcode==0
        session=ChromeSession(runtime/'desktop');assert session.endpoint(),'Chrome fechou com o aplicativo'
        identity=hashlib.sha256((session.profile/'DevToolsActivePort').read_bytes()).hexdigest()
        reopened_conn,reopened_child=context.Pipe()
        gui=context.Process(target=gui_process,args=(reopened_child,str(runtime),'reopen'));gui.start()
        assert reopened_conn.poll(40);event=reopened_conn.recv();report['events'].append(event)
        assert event['event']=='reopened' and event['active'] is False,event
        gui.join(15);assert gui.exitcode==0
        assert session.endpoint() and hashlib.sha256((session.profile/'DevToolsActivePort').read_bytes()).hexdigest()==identity
        report.update(final_result_verified=not entry_only,entry_only=entry_only,scores=gui_final,chrome_survived_app_exit=True,reopened_paused_same_chrome=True)
    except Exception as exc:
        report.update(final_result_verified=False,error=type(exc).__name__)
        print('VALIDATION_FAILED',type(exc).__name__,flush=True)
    finally:
        if gui and gui.is_alive():gui.terminate();gui.join(10)
        if host.is_alive():host_conn.send('stop');host.join(15)
        if host.is_alive():host.terminate();host.join(10)
        async def cleanup():
            from playwright.async_api import async_playwright
            session=ChromeSession(runtime/'desktop')
            if session.endpoint():
                async with async_playwright() as pw:await session.connect(pw);await session.close_game()
            for _ in range(50):
                if session.endpoint() is None:return True
                await asyncio.sleep(.1)
            return False
        report['cleanup']={'host_closed':not host.is_alive(),'gui_closed':not gui or not gui.is_alive(),'dedicated_chrome_closed':asyncio.run(cleanup())}
        target=ROOT/'evidence/releases/2.0.0'/('desktop-'+run_id+'.json');target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n', encoding="utf-8")
        print('REPORT',target.name,flush=True)
    return 0 if report.get('reopened_paused_same_chrome') and all(report['cleanup'].values()) else 1


if __name__=='__main__':raise SystemExit(main())
