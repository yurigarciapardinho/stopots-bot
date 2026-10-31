# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
from __future__ import annotations

import asyncio
from dataclasses import replace
from importlib.resources import files
import re
import time

from ..domain import ActionResult, Control, Field, Group, Kind, Notice, Observation, Phase, Ranking, Rules, Status
from ..identity import ContextTracker
from ..normalization import game_value, utf16_length

ADAPTER_VERSION = "web-2.0.2"
SNAPSHOT = files("stopots_v2").joinpath("adapters/snapshot.js").read_text(encoding="utf-8")


class StopotsWeb:
    """Um escritor serial por página; nenhuma dependência do harness de preparação."""

    def __init__(self, page, owner=None, clock=time.monotonic):
        self.page, self.owner, self.clock = page, owner, clock
        self.tracker = ContextTracker(clock=clock)
        self.lock = asyncio.Lock()
        self.attempted = set()
        self.rules = Rules()
        self.last_letter = None
        self.last_round = None
        self.player_ids = {}
        self.closed = False
        self.raw = None
        self.was_connected = True
        self.ranking_signature = None
        self.ranking_since = clock()
        self.page.on("framenavigated", self._navigation)

    def _navigation(self, frame):
        if frame == self.page.main_frame:
            self.tracker.invalidate()
            self.last_letter = self.last_round = None
            self.rules = Rules()

    def _ranking(self, raw):
        if not raw:
            self.ranking_signature = None
            return None
        rows = []
        names = set()
        for item in raw["rows"]:
            name, score = item.get('name'), item.get('points', '')
            if not name or not re.fullmatch(r'-?\d+', score):
                self.ranking_signature = None
                return None
            if name in names:
                self.ranking_signature = None
                return None  # sem identidade pública suficiente para reconciliar
            names.add(name)
            alias = self.player_ids.setdefault(name, "participante_" + str(len(self.player_ids) + 1))
            rows.append((alias, int(score)))
        signature = (raw['semantic'], raw.get('round_index'), raw.get('scope','unknown'), tuple(rows))
        if signature != self.ranking_signature:
            self.ranking_signature, self.ranking_since = signature, self.clock()
        if self.clock() - self.ranking_since < .75:
            return None
        return Ranking(tuple(rows), raw["semantic"], raw.get('scope','unknown')) if rows else None

    async def observe(self):
        if self.closed or self.page.is_closed():
            return Observation(self.tracker.context, self.tracker.seq + 1, self.clock(), Phase.CLOSED, connected=False)
        from playwright.async_api import Error
        try:
            raw = await self.page.evaluate(SNAPSHOT)
        except Error as exc:
            self.tracker.invalidate()
            raise TimeoutError("Observação indisponível durante navegação ou desconexão") from exc
        if not raw.get("connected", True) and self.was_connected:
            self.tracker.invalidate()
        self.was_connected = raw.get("connected", True)
        self.raw = raw
        phase = Phase(raw["phase"])
        if phase == Phase.WRITING:
            self.last_letter, self.last_round = raw.get("letter"), raw.get("round_index")
        elif phase in (Phase.REVIEW, Phase.ROUND_RESULT, Phase.FINAL_RESULT):
            if raw.get("round_index") == self.last_round:
                raw["letter"] = raw.get("letter") or self.last_letter
        elif phase in (Phase.HOME, Phase.ROOM):
            self.last_letter = self.last_round = None
        if phase == Phase.ROOM:
            data = raw.get("rules", {})
            self.rules = Rules(**{**data, "letters": tuple(data.get("letters", [])),
                                   "category_pool": tuple(data.get("category_pool", []))})
        raw["rules"] = {"stop_mode": self.rules.stop_mode, "time_mode": self.rules.time_mode,
                        "letters": self.rules.letters, "category_pool": self.rules.category_pool,
                        "is_host": self.rules.is_host}
        context, seq, stable = self.tracker.update(raw)
        notice=raw.get('notice')
        if notice:
            notice=Notice(notice['ref'],notice['code'],Control(**notice['acknowledge']) if notice.get('acknowledge') else None)
        return Observation(context, seq, self.clock(), phase, raw.get("letter"), raw.get("total_rounds"),
                           tuple(Field(**f) for f in raw.get("fields", [])), stable,
                           raw.get("review_theme"), raw.get("review_total"),
                           tuple(Group(**g) for g in raw.get("groups", [])),
                           *(Control(**raw[k]) if raw.get(k) else None for k in ("stop", "confirm", "proceed")),
                           raw.get("connected", True), self.rules, self._ranking(raw.get("ranking")),notice)

    def _precondition(self, action, obs):
        if action.deadline <= self.clock():
            return Status.STALE, "Prazo da ação expirou"
        if action.context != obs.context or not obs.connected:
            return Status.STALE, "Contexto mudou ou conexão indisponível"
        if obs.notice:
            return Status.BLOCKED, "Aviso ativo na interface; interação suspensa"
        if action.kind == Kind.FILL:
            field = next((f for f in obs.fields if f.ref == action.target), None)
            if obs.phase != Phase.WRITING or not obs.fields_stable or not field or field.label != action.expected_label:
                return Status.STALE, "Formulário ou categoria mudou"
            if field.value == game_value(str(action.desired)):
                return Status.SATISFIED, "Valor desejado já observado"
            if field.value != action.expected_value:
                return Status.STALE, "Edição manual preservada"
            if not field.editable:
                return Status.BLOCKED, "Campo indisponível"
            if field.max_length is not None and utf16_length(game_value(str(action.desired))) > field.max_length:
                return Status.BLOCKED, "Resposta excede o limite; nenhum truncamento aplicado"
        elif action.kind == Kind.VOTE:
            group = next((g for g in obs.groups if g.ref == action.target), None)
            if obs.phase != Phase.REVIEW or not group or obs.review_theme != action.expected_label:
                return Status.STALE, "Etapa ou grupo mudou"
            if group.checked == action.desired:
                return Status.SATISFIED, "Voto desejado já observado"
            if group.checked != action.expected_value:
                return Status.STALE, "Voto manual preservado"
            if not group.enabled:
                return Status.BLOCKED, "Voto indisponível"
        else:
            controls = {Kind.STOP: (Phase.WRITING, obs.stop), Kind.CONFIRM: (Phase.REVIEW, obs.confirm),
                        Kind.CONTINUE: (Phase.ROUND_RESULT, obs.proceed)}
            expected_phase, control = controls[action.kind]
            if obs.phase != expected_phase or not control or control.ref != action.target:
                return Status.STALE, "Controle não pertence à fase ativa"
            if not control.enabled:
                return Status.BLOCKED, "Aguardando habilitação real do controle"
        return None

    async def apply(self, action):
        from playwright.async_api import Error, TimeoutError as PlaywrightTimeout
        async with self.lock:
            before = await self.observe()
            failure = self._precondition(action, before)
            if failure:
                return ActionResult(*failure, before)
            if action.id in self.attempted:
                return ActionResult(Status.INDETERMINATE, "Ação já enviada; repetição suspensa", before,True)
            target = self.page.locator(action.target)
            if await target.count() != 1:
                return ActionResult(Status.BLOCKED, "Alvo ausente ou ambíguo", before)
            await self.page.bring_to_front()
            # Foco pode permitir uma transição: observar novamente antes da mutação.
            fresh = await self.observe()
            failure = self._precondition(action, fresh)
            if failure:
                return ActionResult(*failure, fresh)
            timeout = max(1, min(2500, int((action.deadline - self.clock()) * 1000)))
            self.attempted.add(action.id)  # inclusive timeout após envio
            try:
                if action.kind == Kind.FILL:
                    # Leitura imediatamente anterior impede sobrescrita detectável.
                    if await target.input_value() != action.expected_value:
                        return ActionResult(Status.STALE, "Edição manual preservada", await self.observe())
                    await target.fill(str(action.desired), timeout=timeout)
                    await target.press("Tab", timeout=timeout)
                elif action.kind == Kind.VOTE:
                    group = next(g for g in fresh.groups if g.ref == action.target)
                    if await target.is_checked() != action.desired:
                        if await target.is_visible():
                            await target.set_checked(bool(action.desired), timeout=timeout)
                        else:
                            label = self.page.locator(group.label_ref)
                            if await label.count() != 1:
                                return ActionResult(Status.BLOCKED, "Rótulo do voto ambíguo", fresh)
                            await label.click(timeout=timeout)
                else:
                    await target.click(timeout=timeout)
            except (PlaywrightTimeout, Error):
                # Não repete clique cujo efeito pode já ter sido enviado.
                return await self._confirm(action, before, timed_out=True)
            return await self._confirm(action, before)

    async def _confirm(self, action, before, timed_out=False):
        from playwright.async_api import Error
        end = min(action.deadline, self.clock() + 3)
        after = before
        while self.clock() < end:
            after = await self.observe()
            same_round = (after.context.room_epoch, after.context.match_epoch, after.context.round_epoch) == (
                before.context.room_epoch, before.context.match_epoch, before.context.round_epoch)
            if action.kind==Kind.STOP and same_round and before.notice is None and after.phase==Phase.WRITING and after.notice and after.notice.code=='STOP_INCOMPLETE':
                # Somente a recusa conhecida surgida após nossa própria ação.
                current=await self.observe()
                if current.context==after.context and current.notice==after.notice and current.notice.acknowledge and current.notice.acknowledge.enabled:
                    ok=self.page.locator(current.notice.acknowledge.ref)
                    if await ok.count()==1 and self.clock()<action.deadline:
                        try:
                            await ok.click(timeout=max(1,min(1000,int((action.deadline-self.clock())*1000))))
                            remaining=max(1,min(800,int((action.deadline-self.clock())*1000)))
                            await self.page.locator(current.notice.ref).wait_for(state='hidden',timeout=remaining)
                        except Error:
                            pass  # recusa comprovada; um clique incerto nunca é repetido
                        current=await self.observe()
                reason='STOP recusado: categorias incompletas'
                if current.notice is None:reason+='; aviso fechado'
                return ActionResult(Status.BLOCKED,reason,current,True)
            if action.kind == Kind.FILL:
                field = next((f for f in after.fields if f.ref == action.target), None)
                confirmed = same_round and after.phase == Phase.WRITING and field and field.value == game_value(str(action.desired))
            elif action.kind == Kind.VOTE:
                group = next((g for g in after.groups if g.ref == action.target), None)
                confirmed = after.context == before.context and group and group.checked == action.desired
            elif action.kind == Kind.STOP:
                confirmed = same_round and after.phase in (Phase.REVIEW, Phase.ROUND_RESULT, Phase.FINAL_RESULT)
            elif action.kind == Kind.CONFIRM:
                confirmed = same_round and (after.phase in (Phase.ROUND_RESULT, Phase.FINAL_RESULT) or (
                    after.phase == Phase.REVIEW and after.context.review_epoch != before.context.review_epoch))
                # O jogo pode manter a mesma etapa enquanto espera os demais.
                confirmed = confirmed or (after.context == before.context and after.confirm is not None and not after.confirm.enabled)
            else:
                confirmed = after.phase == Phase.WRITING and after.context.round_epoch != before.context.round_epoch
                confirmed = confirmed or (after.context == before.context and after.proceed is not None and not after.proceed.enabled)
            if confirmed:
                return ActionResult(Status.APPLIED, "Efeito confirmado após timeout" if timed_out else "Efeito confirmado", after,True)
            if after.context != before.context:
                break
            await asyncio.sleep(.05)
        return ActionResult(Status.INDETERMINATE, "Efeito ainda não confirmado; não repetir automaticamente", after,True)

    async def close(self):
        if not self.closed:
            self.closed = True
            self.page.remove_listener("framenavigated", self._navigation)
            if self.owner:
                await self.owner.close()
