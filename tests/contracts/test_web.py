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
        await page.set_content((Path(__file__).parent/'fixtures/fim-de-jogo.html').read_text())
        port = StopotsWeb(page, clock=lambda: now[0])
        obs = await port.observe()
        assert obs.phase == Phase.FINAL_RESULT and obs.ranking is None
        now[0] += 1
        obs = await port.observe()
        assert obs.ranking.rows == (("participante_1",250),("participante_2",250))
        assert obs.ranking.semantic == 'total_partida'
    browser_test(case)
