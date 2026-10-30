import asyncio
import json
from pathlib import Path
import pytest

from stopots_v2.adapters.chrome_session import ChromeSession
from stopots_v2.adapters.invitation import enter_invitation, EntryError
from stopots_v2.adapters.web import StopotsWeb
from stopots_v2.desktop_model import Invitation
from stopots_v2.domain import Phase

pytestmark=pytest.mark.browser


@pytest.mark.parametrize('protected', [False, True])
def test_invitation_real_controls_exact_secret_and_ambiguous_enter(protected):
    async def case():
        from playwright.async_api import async_playwright
        password=' A9áÇ!$&\'"\\e\u0301 '
        room='<h6>CONFIGURAÇÕES</h6><h4>CATEGORIAS (12)</h4><input type="password" disabled>'
        script='''function enter(){window.sent=document.querySelector('#pw').value;
        document.body.innerHTML=ROOM;}function accept(){window.joinNick=document.querySelector('#nick').value;document.querySelector('#invite').innerHTML=FORM;}'''
        form='<input type="password" id="pw"><button onclick="enter()">ENTRAR</button>'
        html='<div role="alert"></div><button id="old">ENTRAR</button><section id="invite" class="popupSystem"><h2>Você foi convidado</h2><input id="nick" maxlength="15"><button onclick="accept()">ENTRAR</button></section>'
        html+='<script>const ROOM='+json.dumps(room)+';const FORM='+json.dumps(form if protected else room)+';'+script+'</script>'
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='chrome',headless=True)
            try:
                page=await browser.new_page()
                async def route(r):
                    await r.fulfill(content_type='text/html; charset=utf-8',body='<input maxlength="15"><button>CRIAR SALA</button>' if r.request.url.rstrip('/')=='https://stopots.com/pt' else html)
                await page.route('https://stopots.com/**',route)
                request=Invitation('https://stopots.com/pt/08193','Jogador',protected,password if protected else '')
                obs=await enter_invitation(page,request,StopotsWeb(page),timeout=10)
                assert obs.phase==Phase.ROOM and request.password==''
                assert await page.evaluate('window.joinNick')=='Jogador'
                if protected: assert await page.evaluate('window.sent')==password
            finally:await browser.close()
    asyncio.run(case())


def test_missing_password_is_actionable_and_not_guessed():
    async def case():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='chrome',headless=True)
            try:
                page=await browser.new_page()
                await page.route('https://stopots.com/**',lambda r:r.fulfill(content_type='text/html; charset=utf-8',body='<input maxlength="15"><button>CRIAR SALA</button>' if r.request.url.rstrip('/')=='https://stopots.com/pt' else '<input type="password"><button>ENTRAR</button>'))
                with pytest.raises(EntryError) as e:
                    await enter_invitation(page,Invitation('https://stopots.com/pt/08193','Jogador',False),StopotsWeb(page),timeout=10)
                assert e.value.code=='PASSWORD_REQUIRED'
            finally:await browser.close()
    asyncio.run(case())


def test_chrome_survives_driver_exit_and_reconnects_same_page(tmp_path):
    async def case():
        from playwright.async_api import async_playwright
        session=ChromeSession(tmp_path/'persistent',headless=True)
        try:
            async with async_playwright() as pw:
                page=await session.connect(pw)
                await page.set_content('<title>Contrato de persistência</title><h1>Manual</h1>')
            assert session.process.poll() is None
            async with async_playwright() as pw:
                second=ChromeSession(session.directory,headless=True)
                page=await second.connect(pw)
                assert await page.title()=='Contrato de persistência'
                assert second.process is None
                await second.close_game()
            for _ in range(50):
                if session.process.poll() is not None:break
                await asyncio.sleep(.1)
            assert session.process.poll() is not None
        finally:
            if session.process and session.process.poll() is None:
                session.process.terminate();session.process.wait(timeout=10)
    asyncio.run(case())


def test_wrong_password_is_reported_once_without_exposing_secret():
    async def case():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='chrome',headless=True)
            try:
                page=await browser.new_page()
                html='''<div id="entry"><input type="password"><button onclick="window.attempts=(window.attempts||0)+1;document.querySelector('#error').hidden=false">ENTRAR</button></div><div class="popupSystem" id="error" hidden>Senha incorreta</div>'''
                await page.route('https://stopots.com/**',lambda r:r.fulfill(content_type='text/html; charset=utf-8',body='<input maxlength="15"><button>CRIAR SALA</button>' if r.request.url.rstrip('/')=='https://stopots.com/pt' else html))
                request=Invitation('https://stopots.com/pt/08193','Jogador',True,'SENHA-SINTETICA-á!')
                with pytest.raises(EntryError) as e:await enter_invitation(page,request,StopotsWeb(page),timeout=10)
                assert e.value.code=='PASSWORD_REJECTED'
                assert 'SENHA-SINTETICA' not in str(e.value) and not request.password
                assert await page.evaluate('window.attempts')==1
            finally:await browser.close()
    asyncio.run(case())
