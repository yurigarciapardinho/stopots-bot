"""Contratos em Chrome local com DOM sintético; não certificam o site online."""
import asyncio
from dataclasses import replace
from pathlib import Path
import pytest

from stopots_v2.adapters.web import StopotsWeb
from stopots_v2.application import Planner, Policy
from stopots_v2.domain import Kind, Phase, Status
from stopots_v2.vocabulary import Vocabulary

pytestmark = pytest.mark.browser

WRITING = '''<header>RODADAS: 1 / 4 A</header><section id="writing">
<h2>PREENCHA AS CATEGORIAS</h2>
<fieldset><legend>Animal</legend><input id="inputText-0" maxlength="20" oninput="this.value=this.value.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toUpperCase()"></fieldset>
<button id="stop" disabled>STOP!</button></section>'''
REVIEW = '''<section id="review"><h2 id="step">VALIDE AS RESPOSTAS 1/16</h2><h3>Animal</h3>
<input type="checkbox" id="g" style="display:none" checked><label id="gl" for="g">BALEIA</label>
<input type="checkbox" id="unknown" checked><label for="unknown">ARIRANHA</label>
<button id="confirm" onclick="this.disabled=true">AVALIAR</button></section>'''


def browser_test(fn):
    async def scenario():
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(channel="chrome", headless=True)
            try:
                page = await browser.new_page()
                now = [100.0]
                await fn(page, now)
            finally:
                await browser.close()
    asyncio.run(scenario())


def test_active_review_over_old_writing_and_hidden_disconnection():
    async def case(page, now):
        await page.set_content(WRITING + REVIEW + '<div hidden>Conexão perdida. Tentando reconectar...</div>')
        port = StopotsWeb(page, clock=lambda: now[0])
        obs = await port.observe()
        assert obs.phase == Phase.REVIEW and obs.connected and obs.stop is None
        assert obs.review_theme == "Animal" and obs.review_total == 16
        assert len(obs.groups) == 2
    browser_test(case)


def test_public_lobby_disabled_password_is_not_entry_form():
    async def case(page, now):
        await page.set_content('<h6>CONFIGURAÇÕES</h6><h4>CATEGORIAS (12)</h4>'
                               '<input type="password" disabled placeholder="Sala pública">')
        port = StopotsWeb(page, clock=lambda: now[0])
        assert (await port.observe()).phase == Phase.ROOM
        await page.set_content('<input type="password"><button>ENTRAR</button>')
        assert (await port.observe()).phase == Phase.ENTERING
    browser_test(case)


def test_fill_normalization_manual_race_and_round_invalidation():
    async def case(page, now):
        await page.set_content(WRITING)
        port = StopotsWeb(page, clock=lambda: now[0])
        await port.observe()
        now[0] += 2
        obs = await port.observe()
        planner = Planner(Vocabulary.bundled())
        action = planner.plan(obs)
        await page.locator('#inputText-0').fill('MINHA RESPOSTA')
        result = await port.apply(action)
        assert result.status == Status.STALE
        assert await page.locator('#inputText-0').input_value() == 'MINHA RESPOSTA'
        await page.locator('#inputText-0').fill('')
        action = replace(planner.plan(await port.observe()), desired='águia')
        assert (await port.apply(action)).status == Status.APPLIED
        assert await page.locator('#inputText-0').input_value() == 'AGUIA'
        await page.locator('header').evaluate("e=>e.innerText='RODADAS: 2 / 4 A'")
        assert (await port.apply(action)).status == Status.STALE
    browser_test(case)


def test_vote_desired_state_and_confirmation_dedup():
    async def case(page, now):
        await page.set_content('<header>RODADAS: 1 / 4 A</header>' + REVIEW)
        port = StopotsWeb(page, clock=lambda: now[0])
        obs = await port.observe()
        planner = Planner(Vocabulary.bundled(), Policy(set_votes=True, confirm_review=True))
        action = planner.plan(obs)
        assert action.kind == Kind.VOTE and action.desired is False
        result = await port.apply(action)
        assert result.status == Status.APPLIED and not await page.locator('#g').is_checked()
        assert await page.locator('#unknown').is_checked()
        assert (await port.apply(action)).status == Status.SATISFIED
        confirm = planner.plan(await port.observe())
        assert confirm.kind == Kind.CONFIRM
        result = await port.apply(confirm)
        assert result.status == Status.APPLIED
        planner.record(confirm, result)
        assert planner.plan(await port.observe()) is None
    browser_test(case)


def test_16_fields_20_groups_and_round_final_rankings():
    async def case(page, now):
        fields = ''.join(f'<fieldset><legend>Animal</legend><input id="inputText-{i}" maxlength="20"></fieldset>' for i in range(16))
        await page.set_content('<header>RODADAS: 1 / 4 A</header><h2>PREENCHA AS CATEGORIAS</h2>' + fields)
        port = StopotsWeb(page, clock=lambda: now[0])
        assert len((await port.observe()).fields) == 16
        now[0] += 2
        assert (await port.observe()).fields_stable
        groups = ''.join(f'<input type="checkbox" id="g{i}"><label for="g{i}">ARARA</label>' for i in range(20))
        await page.set_content('<header>RODADAS: 1 / 4 A</header><section><h2>VALIDE AS RESPOSTAS 1/12</h2><h3>Animal</h3>' + groups + '</section>')
        assert len((await port.observe()).groups) == 20
        await page.set_content('<section class="ranking"><h2>RANKING DA RODADA 1/4</h2><div class="userRkg"><span class="nick">Nome privado</span><span class="points">65</span></div></section>')
        assert (await port.observe()).ranking is None
        now[0] += 1
        obs = await port.observe()
        assert obs.phase == Phase.ROUND_RESULT and obs.ranking.rows == (("participante_1", 65),)
        await page.set_content('<section class="ranking"><h2>RANKING FINAL</h2><div class="userRkg"><span class="nick">Nome privado</span><span class="points">260</span></div></section>')
        await port.observe()
        now[0] += 1
        obs = await port.observe()
        assert obs.phase == Phase.FINAL_RESULT and obs.ranking.semantic == "total_partida"
    browser_test(case)


def test_ranking_uses_own_counter_and_final_over_background():
    async def case(page, now):
        await page.set_content('<header>RODADAS: 3 / 4 A</header><section class="ranking"><h2>RANKING DA RODADA 2/4</h2><div class="userRkg"><span class="nick">A</span><span class="points">65</span></div></section>')
        port = StopotsWeb(page, clock=lambda: now[0])
        obs = await port.observe()
        assert obs.context.round_index == 2
        await page.set_content('<section class="ranking" style="opacity:0"><h2>RANKING DA RODADA 4/4</h2><div class="userRkg"><span class="nick">A</span><span class="points">60</span></div></section><section class="ranking"><h2>RANKING\nFINAL</h2><div class="userRkg"><span class="nick">A</span><span class="points">250</span></div></section>')
        assert (await port.observe()).phase == Phase.FINAL_RESULT
        now[0] += 1
        assert (await port.observe()).ranking.rows == (("participante_1", 250),)
    browser_test(case)


def test_actual_end_screen_and_animated_rows():
    async def case(page, now):
        await page.set_content((Path(__file__).parent/'fixtures/fim-de-jogo.html').read_text(encoding="utf-8"))
        port = StopotsWeb(page, clock=lambda: now[0])
        obs = await port.observe()
        assert obs.phase == Phase.FINAL_RESULT and obs.ranking is None
        now[0] += 1
        obs = await port.observe()
        assert obs.ranking.rows == (("participante_1",250),("participante_2",250))
        assert obs.ranking.semantic == 'total_partida'
        assert obs.ranking.scope == 'podium'
    browser_test(case)


def test_stop_rejection_is_blocked_acknowledged_and_not_retried():
    async def case(page, now):
        popup="<div class='popupSystem'><h4>AVISO</h4><p>Preencha corretamente todas as categorias para dar Stop</p><button onclick='this.parentElement.remove()'>OK</button></div>"
        import json
        await page.set_content(WRITING.replace('disabled','')+'<script>document.querySelector("#stop").onclick=()=>document.body.insertAdjacentHTML("beforeend",'+json.dumps(popup)+')</script>')
        port=StopotsWeb(page,clock=lambda:now[0])
        await port.observe();now[0]+=2
        obs=await port.observe()
        planner=Planner(Vocabulary.bundled(),Policy(fill_blanks=False,request_stop=True,require_all_filled=False))
        action=planner.plan(obs)
        result=await port.apply(action)
        assert result.status==Status.BLOCKED and result.attempted
        assert result.observed.notice is None
        assert await page.locator('.popupSystem').count()==0
        planner.record(action,result)
        assert planner.plan(await port.observe()) is None
    browser_test(case)


def test_existing_unknown_or_manual_notice_is_preserved():
    async def case(page, now):
        await page.set_content(WRITING)
        port=StopotsWeb(page,clock=lambda:now[0])
        await port.observe();now[0]+=2
        planner=Planner(Vocabulary.bundled())
        action=planner.plan(await port.observe())
        await page.locator('body').evaluate("e=>e.insertAdjacentHTML('beforeend','<div class=\"popupSystem\"><p>Aviso que exige leitura manual</p><button>OK</button></div>')")
        obs=await port.observe()
        assert obs.notice.code=='UNKNOWN' and obs.notice.acknowledge is None
        assert planner.plan(obs) is None
        assert (await port.apply(action)).status==Status.STALE
        assert await page.locator('.popupSystem').count()==1
        assert not await page.locator('#inputText-0').input_value()
    browser_test(case)


@pytest.mark.parametrize('kind,pause_at', [
    (Kind.FILL,'focus'),(Kind.FILL,'observation'),(Kind.FILL,'read'),
    (Kind.VOTE,'focus'),(Kind.VOTE,'observation'),(Kind.VOTE,'read'),
    (Kind.CONFIRM,'focus'),(Kind.CONFIRM,'observation'),
])
def test_pause_during_pending_action_prevents_dispatch_and_allows_resume(kind,pause_at,monkeypatch,tmp_path):
    async def case(page, now):
        from playwright.async_api import Locator
        from stopots_v2.desktop_engine import DesktopEngine
        engine=DesktopEngine(tmp_path,Policy(),lambda _:None)
        engine.active.set()
        await page.set_content(WRITING if kind==Kind.FILL else '<header>RODADAS: 1 / 4 A</header>'+REVIEW)
        port=StopotsWeb(page,clock=lambda:now[0],cancelled=lambda:not engine.active.is_set())
        await port.observe();now[0]+=2
        policy=Policy(set_votes=kind==Kind.VOTE,confirm_review=kind==Kind.CONFIRM)
        action=Planner(Vocabulary.bundled(),policy).plan(await port.observe())
        assert action.kind==kind
        if pause_at=='focus':
            original=page.bring_to_front
            async def focus():
                engine.submit('pause')
                await original()
            monkeypatch.setattr(page,'bring_to_front',focus)
        elif pause_at=='observation':
            original=port.observe;calls=0
            async def observe():
                nonlocal calls
                obs=await original();calls+=1
                if calls==2:engine.submit('pause')
                return obs
            monkeypatch.setattr(port,'observe',observe)
        else:
            method='input_value' if kind==Kind.FILL else 'is_visible'
            original=getattr(Locator,method)
            async def read(locator,*args,**kwargs):
                value=await original(locator,*args,**kwargs)
                engine.submit('pause')
                return value
            monkeypatch.setattr(Locator,method,read)
        result=await port.apply(action)
        assert result.status==Status.BLOCKED and not result.attempted
        assert action.id not in port.attempted
        if kind==Kind.FILL:assert await page.locator('#inputText-0').input_value()==''
        elif kind==Kind.VOTE:assert await page.locator('#g').is_checked()
        else:assert await page.locator('#confirm').is_enabled()
        monkeypatch.undo();engine.active.set()
        assert (await port.apply(action)).status==Status.APPLIED
    browser_test(case)


def test_pause_after_fill_prevents_followup_tab(monkeypatch):
    async def case(page,now):
        from playwright.async_api import Locator
        paused=False
        await page.set_content(WRITING+'<script>window.tabs=0;document.onkeydown=e=>{if(e.key==="Tab")window.tabs++}</script>')
        port=StopotsWeb(page,clock=lambda:now[0],cancelled=lambda:paused)
        await port.observe();now[0]+=2
        action=Planner(Vocabulary.bundled()).plan(await port.observe())
        original=Locator.fill
        async def fill(locator,*args,**kwargs):
            nonlocal paused
            await original(locator,*args,**kwargs);paused=True
        monkeypatch.setattr(Locator,'fill',fill)
        result=await port.apply(action)
        assert result.status==Status.APPLIED and result.attempted
        assert await page.evaluate('window.tabs')==0
    browser_test(case)


def test_pause_preserves_stop_rejection_notice(monkeypatch):
    async def case(page,now):
        import json
        paused=False
        popup='<div class="popupSystem"><p>Preencha corretamente todas as categorias para dar Stop</p><button onclick="this.parentElement.remove()">OK</button></div>'
        await page.set_content(WRITING.replace('disabled','')+'<script>document.querySelector("#stop").onclick=()=>document.body.insertAdjacentHTML("beforeend",'+json.dumps(popup)+')</script>')
        port=StopotsWeb(page,clock=lambda:now[0],cancelled=lambda:paused)
        await port.observe();now[0]+=2
        action=Planner(Vocabulary.bundled(),Policy(fill_blanks=False,request_stop=True,require_all_filled=False)).plan(await port.observe())
        original=port.observe
        async def observe():
            nonlocal paused
            obs=await original()
            if obs.notice:paused=True
            return obs
        monkeypatch.setattr(port,'observe',observe)
        result=await port.apply(action)
        assert result.status==Status.BLOCKED and result.attempted
        assert await page.locator('.popupSystem').count()==1
    browser_test(case)
