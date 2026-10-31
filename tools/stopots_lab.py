"""Laboratório persistente de interface. Ainda não é o bot v2."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORKTREE = Path(__file__).resolve().parents[1]
ROOT = WORKTREE.parent
RUNTIME = ROOT / ".runtime"
STATE = RUNTIME / "lab-control.json"
FIXTURES = WORKTREE / "tests/lab/fixtures"
EVIDENCE = WORKTREE / "evidence/lab"
URL = "https://stopots.com/pt"

SNAPSHOT_JS = r"""() => {
 const visible = e => {
   if (!e || !e.getClientRects().length) return false;
   for(let p=e;p;p=p.parentElement){
     const s=getComputedStyle(p);
     if(p.hidden || p.getAttribute('aria-hidden')==='true' || s.display==='none' || s.visibility==='hidden') return false;
   }
   return true;
 };
 const txt=e=>(e.innerText||e.textContent||'').trim();
 const q=s=>[...document.querySelectorAll(s)].filter(visible);
 const inputs=q('input,textarea').map(e=>({id:e.id,type:e.type,name:e.name,placeholder:e.placeholder,maxLength:e.maxLength,value:e.type==='password'?'[REDACTED]':e.value,disabled:e.disabled,readOnly:e.readOnly,label:[...(e.labels||[])].map(txt).join(' ') || (e.closest('fieldset')?.querySelector('legend')?.innerText||''),outer:e.outerHTML.replace(/value="[^"]*"/g,'value="[REDACTED]"')}));
 const fields=inputs.filter(e=>/^inputText-\d+$/.test(e.id));
 const buttons=q('button').map(e=>({text:txt(e),disabled:e.disabled}));
 const headings=q('h1,h2,h3,h4,legend').map(txt);
 const review=q('label[for]').map(e=>{const c=document.getElementById(e.htmlFor);return {text:txt(e),for:e.htmlFor,checked:c?.checked,type:c?.type}}).filter(e=>e.type==='checkbox');
 const selects=q('select').map(e=>({id:e.id,value:e.value,options:[...e.options].map(o=>({value:o.value,text:o.text,selected:o.selected}))}));
 return {url:location.href,title:document.title,visibility:document.visibilityState,focused:document.hasFocus(),text:document.body.innerText.slice(0,16000),fields,inputs,buttons,headings,review,selects};
}"""


def normalize(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).strip().upper()


def classify(s: dict) -> str:
    headings = " ".join(s.get("headings", []))
    text = s.get("text", "")
    if re.search(r"VALIDE AS RESPOSTAS\s+\d+\s*/\s*\d+", headings) and s.get("review"):
        return "REVISAO"
    if "GERANDO RANKING FINAL" in text:
        return "TRANSICAO_FINAL"
    if "RANKING FINAL" in headings and "GERANDO" not in headings:
        return "RESULTADO_PARTIDA"
    if "RANKING" in headings:
        return "RESULTADO"
    if "RESULTADO" in headings:
        return "RESULTADO"
    if s.get("fields") and "PREENCHA AS CATEGORIAS" in headings:
        return "ESCRITA"
    if "CONFIGURAÇÕES" in headings or "CONFIGURAÇÕES" in text:
        return "SALA"
    if any(x.get("type") == "password" for x in s.get("inputs", [])):
        return "ENTRADA_PRIVADA"
    if any(b["text"] == "ENTRAR" for b in s.get("buttons", [])) and "Você foi convidado" in text:
        return "CONVITE"
    if any(b["text"] == "CRIAR SALA" for b in s.get("buttons", [])):
        return "INICIO"
    if re.search(r"inatividade|foi removido|desconectad", text, re.I):
        return "SESSAO_EXPIRADA"
    return "DESCONHECIDO"


def context_of(s: dict) -> tuple:
    round_match = re.search(r"RODADAS:\s*(\d+)\s*/\s*(\d+)", s.get("text", ""))
    review_match = re.search(r"VALIDE AS RESPOSTAS\s+(\d+)\s*/\s*(\d+)", " ".join(s.get("headings", [])))
    return (s.get("epoch"), classify(s), round_match.groups() if round_match else None,
            review_match.groups() if review_match else None,
            tuple((f["id"], f.get("label")) for f in s.get("fields", [])))


def answers_match(state, expected):
    fields = state.get("fields", [])
    return bool(expected) and state.get("phase") == "ESCRITA" and len(fields) == len(expected) and all(expected.get(f["id"]) == f["value"] for f in fields)


class Lab:
    def __init__(self):
        self.pw = self.context = self.browser = None
        self.guest_browser = None
        self.pages = {}
        self.test_contexts = []
        self.epoch = uuid.uuid4().hex
        self.password = ""
        self.events = []
        self.loop = None
        self.server = None
        self.is_closing = False
        self.job = None
        self.report = {}
        self.stop_watch = None

    def clean(self, data):
        raw = json.dumps(data, ensure_ascii=False)
        if self.password:
            raw = raw.replace(self.password, "[SENHA_REMOVIDA]")
        raw = re.sub(r"https://stopots\.com/pt/\d+", "https://stopots.com/pt/[sala]", raw)
        raw = re.sub(r"(?<!https://)stopots\.com/pt/\d+", "stopots.com/pt/[sala]", raw)
        raw = re.sub(r"SALA \d+", "SALA [teste]", raw)
        return json.loads(raw)

    async def launch(self):
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().start()
        self.context = await self.pw.chromium.launch_persistent_context(
            str(RUNTIME / "chrome-lab"), channel="chrome", headless=False,
            locale="pt-BR", viewport={"width": 1440, "height": 1000},
            args=["--no-first-run", "--no-default-browser-check"])
        self.browser = self.context.browser
        self.guest_browser = await self.pw.chromium.launch(channel="chrome", headless=True)
        self.pages["principal"] = self.context.pages[0] if self.context.pages else await self.context.new_page()
        await self.pages["principal"].goto(URL, wait_until="domcontentloaded", timeout=45000)
        await self.pages["principal"].get_by_role("button", name="CRIAR SALA", exact=True).wait_for(timeout=45000)

    async def observe(self, player="principal", save=False):
        page = self.pages[player]
        s = await page.evaluate(SNAPSHOT_JS)
        s.update(epoch=self.epoch, observed_at=time.time(), player=player)
        s["phase"] = classify(s)
        s["context"] = context_of(s)
        safe = self.clean(s)
        if save:
            FIXTURES.mkdir(parents=True, exist_ok=True)
            dest = FIXTURES / f"{safe['phase'].lower()}-{player}.json"
            dest.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return safe

    async def click(self, player, text, role="button"):
        page = self.pages[player]
        await page.bring_to_front()
        if text == "INICIAR":
            share = page.locator(".popupSystem.share").filter(visible=True)
            if await share.count():
                close = share.locator("button.close")
                if await share.count() != 1 or await close.count() != 1:
                    raise ValueError("Popup de compartilhamento ambíguo")
                await close.click(timeout=5000)
                await share.wait_for(state="hidden", timeout=5000)
        target = (page.get_by_text(text, exact=True) if role == "text" else page.get_by_role(role, name=text, exact=True)).filter(visible=True)
        if await target.count() != 1:
            raise ValueError(f"Botão ambíguo ou ausente: {text}")
        await target.click(timeout=6000)

    async def fill(self, player, selector, value, method="fill", expected=None):
        await self.pages[player].bring_to_front()
        before = await self.observe(player)
        if expected and json.loads(json.dumps(before["context"])) != expected:
            return {"status": "OBSOLETA"}
        target = self.pages[player].locator(selector).filter(visible=True)
        if await target.count() != 1:
            raise ValueError("Campo ambíguo ou ausente")
        if not await target.is_enabled() or not await target.is_editable():
            return {"status": "BLOQUEADA"}
        if method == "type":
            await target.fill("")
            await target.press_sequentially(value, delay=20)
        else:
            await target.fill(value, timeout=4000)
        actual = await target.input_value()
        return {"status": "APLICADA", "requested": value, "actual": actual}

    async def reset(self):
        for ctx in self.test_contexts:
            await ctx.close()
        self.test_contexts.clear()
        self.pages = {"principal": self.pages["principal"]}
        self.epoch = uuid.uuid4().hex
        self.events.clear()
        for name in ["host", "convidado"]:
            engine = self.browser if name == "host" else self.guest_browser
            ctx = await engine.new_context(locale="pt-BR", viewport={"width": 1440, "height": 1000})
            self.test_contexts.append(ctx)
            self.pages[name] = await ctx.new_page()
            await self.pages[name].goto(URL, wait_until="domcontentloaded", timeout=45000)
            await self.pages[name].get_by_role("button", name="CRIAR SALA", exact=True).wait_for(timeout=45000)
        return await self.observe("host")

    async def wait_for(self, player, predicate, timeout=30):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            state = await self.observe(player)
            if predicate(state):
                return state
            await asyncio.sleep(0.2)
        raise TimeoutError(f"Condição não observada em {timeout}s; participante={player}; fase={state['phase']}")

    async def stable_writing(self, player):
        previous = None
        changed = time.monotonic()
        end = changed + 15
        while time.monotonic() < end:
            state = await self.observe(player)
            signature = tuple((f["id"], f["label"]) for f in state["fields"])
            if state["phase"] != "ESCRITA" or not signature or signature != previous:
                previous, changed = signature, time.monotonic()
            elif time.monotonic() - changed >= 1:
                return state
            await asyncio.sleep(.1)
        raise TimeoutError("A lista de campos da rodada não estabilizou")

    async def create_private(self):
        await self.reset()
        self.password = secrets.token_hex(7)
        for player, name in [("host", "LabHost"), ("convidado", "LabGuest")]:
            await self.fill(player, 'input[maxlength="15"]', name)
            await self.observe(player, True)
        await self.click("host", "CRIAR SALA")
        await self.click("host", "SALA PRIVADA", "text")
        await self.click("host", "CONFIRMAR")
        password = self.pages["host"].locator('input[type="password"]').filter(visible=True)
        await password.fill(self.password)
        await self.click("host", "OK")
        await self.wait_for("host", lambda s: s["phase"] == "SALA", 45)
        share = self.pages["host"].locator(".popupSystem.share").filter(visible=True)
        if await share.count():
            close = share.locator("button.close")
            if await share.count() != 1 or await close.count() != 1:
                raise ValueError("Popup de compartilhamento ambíguo")
            await close.click(timeout=5000)
            await share.wait_for(state="hidden", timeout=5000)
        room_url = self.pages["host"].url
        if not re.fullmatch(r"https://stopots\.com/pt/\d+/?", room_url):
            raise ValueError("URL da sala privada não reconhecida")
        guest = self.pages["convidado"]
        await guest.goto(room_url, wait_until="domcontentloaded", timeout=45000)
        guest_state = await self.wait_for("convidado", lambda s: s["phase"] in ["CONVITE", "ENTRADA_PRIVADA", "SALA"], 35)
        if guest_state["phase"] == "CONVITE":
            await self.click("convidado", "ENTRAR")
            await self.wait_for("convidado", lambda s: s["phase"] in ["ENTRADA_PRIVADA", "SALA"], 35)
        if (await self.observe("convidado"))["phase"] == "ENTRADA_PRIVADA":
            password = guest.locator('input[type="password"]').filter(visible=True)
            await password.fill(self.password)
            modal = password.locator("xpath=ancestor::*[.//button[normalize-space(.)='ENTRAR']][1]")
            enter = modal.get_by_role("button", name="ENTRAR", exact=True)
            if await enter.count() != 1:
                raise ValueError("Entrada da senha ambígua")
            await enter.click(timeout=6000)
        await self.wait_for("host", lambda s: bool(re.search(r"JOGADORES\s+2\s*/", s["text"])), 35)
        await self.wait_for("convidado", lambda s: s["phase"] == "SALA", 35)
        for label in ["4 Rodadas", "Mais lento"]:
            select = self.pages["host"].locator("select").filter(has=self.pages["host"].locator("option", has_text=re.compile("^" + re.escape(label) + "$")))
            if await select.count() != 1:
                raise ValueError("Configuração de sala ambígua: " + label)
            await select.select_option(label=label)
        for player in ["host", "convidado"]:
            await self.observe(player, True)
        return {"private": True, "participants": 2, "phase": "SALA", "epoch": self.epoch}

    def checkpoint(self, event, **details):
        item = self.clean({"event": event, "at": time.time(), **details})
        self.report.setdefault("events", []).append(item)
        self.report["stage"] = event
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        target = EVIDENCE / ("spike-" + self.report["run_id"] + ".json")
        temp = target.with_suffix(".novo")
        temp.write_text(json.dumps(self.report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(target)

    async def set_vote(self, player, group, desired):
        page = self.pages[player]
        await page.bring_to_front()
        target = page.locator("[id=" + json.dumps(group["for"]) + "]")
        if await target.count() != 1:
            raise ValueError("Grupo de avaliação ambíguo")
        before = await target.is_checked()
        if before != desired:
            if await target.is_visible():
                await target.set_checked(desired, timeout=4000)
            else:
                await page.locator("label[for=" + json.dumps(group["for"]) + "]").click(timeout=4000)
        actual = await target.is_checked()
        if actual != desired:
            raise AssertionError("Voto não confirmou estado desejado")
        return {"before": before, "desired": desired, "actual": actual}

    async def spike(self):
        self.report = {"schema_version": "1.0.0", "run_id": uuid.uuid4().hex[:12],
                       "subject": "adapter-spike", "status": "running", "browser": self.browser.version,
                       "final_result_verified": False, "events": [], "assertions": [],
                       "limitations": ["Laboratório e adaptador mínimo; não certifica pacote v2 completo.", "Candidatos usados para testar UI não representam vocabulário aprovado."]}
        self.checkpoint("preparando_sala")
        try:
            setup = await self.create_private()
            self.checkpoint("sala_privada_pronta", setup=setup)
            host = await self.observe("host")
            self.checkpoint("configuracao", buttons=host["buttons"], selects=host["selects"])
            await self.click("host", "INICIAR")
            states = {}
            for player in ["host", "convidado"]:
                states[player] = await self.wait_for(player, lambda s: s["phase"] == "ESCRITA", 40)
                await self.observe(player, True)
            round_anchor = time.monotonic()
            timing = {"anchor": "Primeira observação conjunta da escrita; não é o relógio interno do servidor", "mode": "Padrão", "time_mode": "Mais lento", "players": {p: {"last_disabled_s": None, "first_enabled_s": None} for p in states}, "samples": []}
            self.report["stop_timing"] = timing
            def sample_stop(observations):
                elapsed = time.monotonic() - round_anchor
                sample = {"elapsed_s": round(elapsed, 3), "players": {}}
                for player, state in observations.items():
                    button = next((b for b in state["buttons"] if b["text"] == "STOP!"), None)
                    enabled = state["phase"] == "ESCRITA" and button is not None and not button["disabled"]
                    sample["players"][player] = {"enabled": enabled, "filled": sum(bool(f["value"]) for f in state["fields"]), "phase": state["phase"], "visibility": state.get("visibility"), "focused": state.get("focused")}
                    if enabled and timing["players"][player]["first_enabled_s"] is None:
                        timing["players"][player]["first_enabled_s"] = round(elapsed, 3)
                    elif not enabled and timing["players"][player]["first_enabled_s"] is None:
                        timing["players"][player]["last_disabled_s"] = round(elapsed, 3)
                timing["samples"].append(sample)
            sample_stop(states)
            async def measure_window():
                checkpoint_at = 0
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline:
                    current_list = await asyncio.gather(*(self.observe(p) for p in ["host", "convidado"]))
                    current = dict(zip(["host", "convidado"], current_list))
                    sample_stop(current)
                    if all(v["first_enabled_s"] is not None for v in timing["players"].values()):
                        return
                    if any(s["phase"] != "ESCRITA" for s in current.values()):
                        raise RuntimeError("Rodada mudou antes de medir a liberação do STOP")
                    if time.monotonic() - checkpoint_at >= 2:
                        self.checkpoint("medindo_stop", elapsed_s=round(time.monotonic() - round_anchor, 3), players=timing["samples"][-1]["players"])
                        checkpoint_at = time.monotonic()
                    first_host = timing["players"]["host"]["first_enabled_s"]
                    if first_host is not None and time.monotonic() - round_anchor > first_host + 2:
                        return
                    await asyncio.sleep(.2)
                raise TimeoutError("A liberação do STOP não foi observada")
            self.stop_watch = asyncio.create_task(measure_window())
            stable_list = await asyncio.gather(*(self.stable_writing(p) for p in ["host", "convidado"]))
            states = dict(zip(["host", "convidado"], stable_list))
            fields = states["host"]["fields"]
            self.checkpoint("escrita_reconhecida", count=len(fields), fields=fields, headings=states["host"]["headings"])
            first = fields[0]
            selector = "[id=" + json.dumps(first["id"]) + "]"
            probe_fill = await self.fill("host", selector, "águia")
            probe_type = await self.fill("host", selector, "águia", "type")
            self.report["assertions"].append({"id": "normalizacao", "passed": probe_fill["actual"] == probe_type["actual"] == "AGUIA", "fill": probe_fill, "typing": probe_type})
            match = re.search(r"RODADAS:\s*\d+\s*/\s*\d+\s*([A-Z])\b", states["host"]["text"])
            if not match:
                raise ValueError("Letra não identificada pela interface")
            letter = match.group(1)
            wrong = "ZEBRA" if letter != "Z" else "ARARA"
            async def fill_player(player):
                expected = {}
                for i, field in enumerate(states[player]["fields"]):
                    value = wrong if player == "convidado" and i == 0 else letter + "teste" + chr(65 + i)
                    expected[field["id"]] = normalize(value)
                    result = await self.fill(player, "[id=" + json.dumps(field["id"]) + "]", value, "type")
                    if result["status"] != "APLICADA" or result["actual"] != normalize(value):
                        raise AssertionError("Preenchimento não confirmado")
                await self.pages[player].locator("[id=" + json.dumps(states[player]["fields"][-1]["id"]) + "]").press("Tab")
                stable = await self.wait_for(player, lambda s: answers_match(s, expected), 10)
                await asyncio.sleep(.3)
                stable = await self.observe(player, True)
                if not answers_match(stable, expected):
                    raise AssertionError("Valores não permaneceram após atualização da interface")
                self.checkpoint("valores_persistentes", player=player, count=len(stable["fields"]))
            await fill_player("host")
            await self.stop_watch
            self.checkpoint("janela_stop_medida", timing=timing["players"], guest_blank=True)
            await fill_player("convidado")
            self.checkpoint("preenchimento_confirmado", letter=letter, fields_per_player={p: len(s["fields"]) for p, s in states.items()})
            await self.wait_for("host", lambda s: any(b["text"] == "STOP!" and not b["disabled"] for b in s["buttons"]), 100)
            await self.click("host", "STOP!")
            self.checkpoint("stop_enviado")
            for topic in range(1, len(fields) + 1):
                reviews = {}
                for player in ["host", "convidado"]:
                    def active(s):
                        m = re.search(r"VALIDE AS RESPOSTAS\s+(\d+)\s*/\s*(\d+)", " ".join(s["headings"]))
                        return s["phase"] == "REVISAO" and m and int(m.group(1)) == topic and any(b["text"] == "AVALIAR" and not b["disabled"] for b in s["buttons"])
                    state = await self.wait_for(player, active, 35)
                    reviews[player] = state
                    await self.observe(player, True)
                    if topic == 1:
                        group = next((g for g in state["review"] if g["checked"]), None)
                        if group:
                            unset = await self.set_vote(player, group, False)
                            restored = await self.set_vote(player, group, True)
                            self.report["assertions"].append({"id": "voto_desejado_" + player, "passed": not unset["actual"] and restored["actual"]})
                    await self.click(player, "AVALIAR")
                self.checkpoint("etapa_confirmada", topic=topic, groups={p: s["review"] for p, s in reviews.items()})
            result = await self.wait_for("host", lambda s: s["phase"] in ["RESULTADO", "RESULTADO_PARTIDA"], 30)
            await self.observe("host", True)
            self.report["assertions"].append({"id": "resultado_rodada", "passed": True})
            self.checkpoint("apos_revisao", phase=result["phase"], headings=result["headings"], buttons=result["buttons"], text=result["text"])
            self.report["status"] = "passed" if all(a["passed"] for a in self.report["assertions"]) else "failed"
        except Exception as exc:
            self.report["status"] = "failed"
            self.report["error"] = self.clean(str(exc))[:1800]
            for player in ["host", "convidado"]:
                if player in self.pages:
                    try:
                        s = await self.observe(player, True)
                        self.checkpoint("diagnostico", player=player, phase=s["phase"], text=s["text"], headings=s["headings"], buttons=s["buttons"], selects=s["selects"])
                    except Exception:
                        pass
        finally:
            if self.stop_watch and not self.stop_watch.done():
                self.stop_watch.cancel()
                try:
                    await self.stop_watch
                except asyncio.CancelledError:
                    pass
            for ctx in self.test_contexts:
                try:
                    await ctx.close()
                except Exception:
                    pass
            self.test_contexts.clear()
            self.pages = {"principal": self.pages["principal"]}
            self.report["cleanup"] = {"test_contexts_closed": True, "remaining_pages": list(self.pages)}
            self.checkpoint("concluido")
        return self.report

    async def route(self, request):
        op = request.get("op", "status")
        player = request.get("player", "principal")
        if self.job and not self.job.done() and op not in {"status", "observe", "inspect", "spike_status", "spike_start", "shutdown"}:
            raise RuntimeError("Teste em execução; aguarde resultado antes de alterar a sessão")
        if op == "status":
            return {"ready": not self.is_closing and self.browser.is_connected(), "pid": os.getpid(), "epoch": self.epoch,
                    "browser": self.browser.version, "pages": list(self.pages), "subject": "adapter-spike"}
        if op == "observe":
            return await self.observe(player, request.get("save", False))
        if op == "home":
            await self.pages[player].goto(URL, wait_until="domcontentloaded", timeout=45000)
            return await self.observe(player)
        if op == "reset":
            return await self.reset()
        if op == "private":
            return await self.create_private()
        if op == "spike_start":
            if self.job and not self.job.done():
                return {"status": "already_running", "run_id": self.report.get("run_id")}
            self.job = asyncio.create_task(self.spike())
            await asyncio.sleep(0)
            return {"status": "started", "run_id": self.report["run_id"]}
        if op == "spike_status":
            return self.report
        if op == "click":
            await self.click(player, request["text"], request.get("role", "button"))
            return await self.observe(player)
        if op == "inspect":
            return self.clean(await self.pages[player].locator(request["selector"]).evaluate_all("(els) => els.map(e => e.outerHTML.slice(0,9000))"))
        if op == "navigate":
            if not re.fullmatch(r"https://stopots\.com/pt(?:/\d+)?/?", request["url"]):
                raise ValueError("Navegação restrita ao StopotS em português")
            await self.pages[player].goto(request["url"], wait_until="domcontentloaded", timeout=45000)
            return await self.observe(player)
        if op == "fill":
            return await self.fill(player, request["selector"], request["value"], request.get("method", "fill"), request.get("expected"))
        if op == "select":
            target = self.pages[player].locator(request["selector"]).filter(visible=True)
            if await target.count() != 1:
                raise ValueError("Select ambíguo ou ausente")
            await target.select_option(label=request["label"])
            return await self.observe(player)
        if op == "check":
            target = self.pages[player].locator(request["selector"])
            if await target.count() != 1:
                raise ValueError("Controle de voto ambíguo ou ausente")
            await target.set_checked(request["checked"], timeout=5000)
            return {"checked": await target.is_checked()}
        if op == "cleanup":
            for ctx in self.test_contexts:
                await ctx.close()
            self.test_contexts.clear()
            self.pages = {"principal": self.pages["principal"]}
            return {"owned_test_contexts_closed": True, "remaining_pages": list(self.pages)}
        if op == "shutdown":
            self.is_closing = True
            asyncio.get_running_loop().call_later(0.5, lambda: asyncio.create_task(self.shutdown()))
            return {"shutting_down": True}
        raise ValueError(f"Operação desconhecida: {op}")

    async def shutdown(self):
        self.is_closing = True
        try:
            for ctx in self.test_contexts:
                try:
                    await ctx.close()
                except Exception:
                    pass
            for owner in [self.guest_browser, self.context]:
                if owner:
                    try:
                        await owner.close()
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            try:
                if self.pw:
                    await self.pw.stop()
            finally:
                if self.server:
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                STATE.unlink(missing_ok=True)
                self.done.set()

    async def serve(self):
        RUNTIME.mkdir(exist_ok=True)
        await self.launch()
        self.loop = asyncio.get_running_loop()
        self.done = asyncio.Event()
        lab = self
        token = secrets.token_hex(32)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                if self.headers.get("Authorization") != "Bearer " + token:
                    self.send_error(403)
                    return
                try:
                    size = int(self.headers.get("Content-Length", 0))
                    if size > 65536:
                        raise ValueError("Pedido grande demais")
                    request = json.loads(self.rfile.read(size))
                    result = asyncio.run_coroutine_threadsafe(lab.route(request), lab.loop).result(timeout=180)
                    body = json.dumps({"ok": True, "result": result}, ensure_ascii=False).encode()
                except Exception as exc:
                    body = json.dumps({"ok": False, "error": str(exc)[:2200]}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        state = {"pid": os.getpid(), "port": self.server.server_port, "token": token,
                 "root": str(ROOT), "epoch": self.epoch, "started_at": time.time()}
        STATE.write_text(json.dumps(state), encoding="utf-8")
        STATE.chmod(0o600)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        print(json.dumps({"ready": True, "pid": os.getpid(), "browser": self.browser.version}), flush=True)
        for sig in [signal.SIGTERM, signal.SIGINT]:
            self.loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
        await self.done.wait()


def request(payload):
    state = json.loads(STATE.read_text(encoding="utf-8"))
    req = urllib.request.Request(f"http://127.0.0.1:{state['port']}/", data=json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + state["token"], "Content-Type": "application/json"})
    result = json.load(urllib.request.urlopen(req, timeout=190))
    if not result["ok"]:
        raise RuntimeError(result["error"])
    return result["result"]


def start():
    try:
        status = request({"op": "status"})
        if status["ready"]:
            return status
        for _ in range(75):
            if not STATE.exists():
                break
            time.sleep(0.2)
        if STATE.exists():
            raise RuntimeError("Sessão anterior ainda está encerrando")
    except Exception:
        if STATE.exists():
            state = json.loads(STATE.read_text(encoding="utf-8"))
            pid = state.get("pid")
            cmdline = Path(f"/proc/{pid}/cmdline")
            if cmdline.exists() and str(Path(__file__).resolve()).encode() in cmdline.read_bytes():
                raise RuntimeError("Laboratório existente não responde; encerre o PID próprio registrado antes de reiniciar")
    RUNTIME.mkdir(exist_ok=True)
    log = open(RUNTIME / "lab.log", "a")
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "serve"],
                               cwd=WORKTREE, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError("Chrome não iniciou; consulte .runtime/lab.log")
        try:
            status = request({"op": "status"})
            if status["ready"] and status["pid"] == process.pid:
                return status
        except Exception:
            time.sleep(0.4)
    raise TimeoutError("Inicialização do laboratório excedeu 60 segundos")


def main():
    parser = argparse.ArgumentParser(description="Laboratório StopotS — preparação da v2")
    parser.add_argument("command", choices=["serve", "iniciar", "doctor", "observar", "inicio", "novo", "limpar", "encerrar", "acao", "replay", "sala", "teste-chrome", "resultado"])
    parser.add_argument("--player", default="principal")
    parser.add_argument("--json", default="{}")
    args = parser.parse_args()
    if args.command == "serve":
        asyncio.run(Lab().serve())
        return
    if args.command == "iniciar":
        data = start()
    elif args.command == "doctor":
        data = {"python": sys.version.split()[0], "playwright": importlib.metadata.version("playwright"),
                "root": str(ROOT), "worktree": str(WORKTREE), "chrome": subprocess.check_output(["google-chrome", "--version"], text=True).strip()}
        try:
            data["lab"] = request({"op": "status"})
        except Exception:
            data["lab"] = "parado; execute iniciar"
    elif args.command == "replay":
        data = [{"fixture": p.name, "phase": classify(json.loads(p.read_text(encoding="utf-8"))), "fields": len(json.loads(p.read_text(encoding="utf-8")).get("fields", []))} for p in sorted(FIXTURES.glob("*.json"))]
    elif args.command == "acao":
        data = request(json.loads(args.json))
    elif args.command in ["sala", "teste-chrome", "resultado"]:
        if args.command != "resultado":
            start()
        data = request({"op": {"sala": "private", "teste-chrome": "spike_start", "resultado": "spike_status"}[args.command]})
        if args.command == "resultado" and data:
            data = {"run_id": data["run_id"], "status": data["status"], "stage": data.get("stage"), "error": data.get("error"), "assertions": data["assertions"], "stop_timing": data.get("stop_timing", {}).get("players"), "review_topics": sum(e["event"] == "etapa_confirmada" for e in data["events"]), "final_result_verified": data["final_result_verified"], "cleanup": data.get("cleanup")}
    else:
        op = {"observar": "observe", "inicio": "home", "novo": "reset", "limpar": "cleanup", "encerrar": "shutdown"}[args.command]
        data = request({"op": op, "player": args.player, "save": args.command == "observar"})
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
