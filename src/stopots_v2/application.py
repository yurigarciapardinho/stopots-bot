# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time

from .domain import Action, Kind, Phase, Status, Supervisor, Verdict


@dataclass(frozen=True)
class Policy:
    fill_blanks: bool = True
    request_stop: bool = False
    require_all_filled: bool = True
    set_votes: bool = False
    confirm_review: bool = False
    continue_results: bool = False
    observe_only: bool = False
    seed: str = "stopots-v2"


class Planner:
    def __init__(self, vocabulary, policy=Policy()):
        self.vocabulary = vocabulary
        self.policy = policy
        self.attempted = set()

    def action(self, obs, kind, ref, desired=None, expected=None, label=None):
        # Etapa/rodada identifica controles únicos; o seletor pode mudar no DOM.
        # O alvo atual continua sendo revalidado pelo adaptador antes de agir.
        c = obs.context
        identity_target = ref if kind in (Kind.FILL, Kind.VOTE) else None
        identity = [c.session_id, c.room_epoch, c.match_epoch, c.round_epoch,
                    c.round_index, c.review_epoch if kind in (Kind.VOTE, Kind.CONFIRM) else None,
                    kind, identity_target, desired]
        aid = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
        if aid in self.attempted:
            return None
        return Action(aid, kind, c, ref, desired, obs.at + 4, expected, label)

    def plan(self, obs):
        p = self.policy
        if p.observe_only or not obs.connected or obs.notice:
            return None
        if obs.phase == Phase.WRITING and obs.fields_stable:
            if p.fill_blanks:
                for field in obs.fields:
                    if field.value or not field.editable:
                        continue
                    seed = f"{p.seed}:{obs.context.match_epoch}:{obs.context.round_epoch}:{field.label}"
                    candidate = self.vocabulary.choose(field.label, obs.letter, field.max_length, seed)
                    if candidate:
                        action = self.action(obs, Kind.FILL, field.ref, candidate[1], "", field.label)
                        if action:
                            return action
            if p.request_stop and obs.stop and obs.stop.enabled:
                if p.require_all_filled and not all(f.value.strip() for f in obs.fields):
                    return None
                return self.action(obs, Kind.STOP, obs.stop.ref)
        if obs.phase == Phase.REVIEW:
            if p.set_votes:
                for group in obs.groups:
                    verdict, _ = self.vocabulary.evaluate(obs.review_theme or "", obs.letter, group.text)
                    if verdict == Verdict.UNKNOWN or not group.enabled:
                        continue
                    desired = verdict == Verdict.COMPATIBLE
                    if group.checked != desired:
                        action = self.action(obs, Kind.VOTE, group.ref, desired, group.checked, obs.review_theme)
                        if action:
                            return action
            if p.confirm_review and obs.confirm and obs.confirm.enabled:
                return self.action(obs, Kind.CONFIRM, obs.confirm.ref)
        if obs.phase == Phase.ROUND_RESULT and p.continue_results and obs.ranking and obs.proceed and obs.proceed.enabled:
            return self.action(obs, Kind.CONTINUE, obs.proceed.ref)
        return None

    def record(self, action, result):
        if result.attempted or result.status in (Status.APPLIED, Status.SATISFIED, Status.INDETERMINATE, Status.FAILED):
            self.attempted.add(action.id)


class EventLog:
    """Esquema permitido; nunca serializa DOM, URL, nome ou senha."""

    def __init__(self, path: Path | None = None):
        self.path = path
        self.events = []
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event, observation=None, action=None, result=None, reason=None):
        data = {"schema_version": 1, "event": event, "at": time.time()}
        if observation:
            data.update(context=asdict(observation.context), phase=observation.phase,
                        connected=observation.connected, fields=len(observation.fields),
                        filled=sum(bool(f.value.strip()) for f in observation.fields),
                        review_index=observation.context.review_index, review_total=observation.review_total,
                        notice_code=observation.notice.code if observation.notice else None)
            if observation.ranking:
                data['ranking'] = asdict(observation.ranking)
        if action:
            data.update(action_id=action.id, kind=action.kind)
        if result:
            data.update(status=result.status, reason=result.reason,interaction_attempted=result.attempted)
        if reason:
            data["reason"] = reason
        self.events.append(data)
        if self.path:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(data, ensure_ascii=False) + "\n")
        return data


class Controller:
    def __init__(self, port, vocabulary, policy=Policy(), events=None, control_file=None):
        self.port = port
        self.planner = Planner(vocabulary, policy)
        self.events = events or EventLog()
        self.control_file = Path(control_file) if control_file else None
        self.supervisor = Supervisor.ACTIVE
        self.last_observation = None
        self.last_signature = None
        self.lock = asyncio.Lock()

    def paused(self):
        if not self.control_file or not self.control_file.exists():
            return False
        try:
            return bool(json.loads(self.control_file.read_text())["paused"])
        except (ValueError, OSError, KeyError):
            return True  # controle inválido suspende mutações

    async def step(self):
        async with self.lock:
            observation = await self.port.observe()
            self.last_observation = observation
            new_state = Supervisor.PAUSED if self.paused() else (Supervisor.ACTIVE if observation.connected else Supervisor.DISCONNECTED)
            if self.supervisor != new_state:
                self.events.emit("supervisor", observation, reason=new_state)
            self.supervisor = new_state
            signature = (observation.context, observation.phase, observation.connected, observation.ranking)
            if signature != self.last_signature:
                self.events.emit("observacao", observation)
                self.last_signature = signature
            if new_state != Supervisor.ACTIVE:
                return observation, None
            action = self.planner.plan(observation)
            if action:
                result = await self.port.apply(action)
                self.planner.record(action, result)
                self.events.emit("acao", observation, action, result)
                return result.observed or observation, result
            return observation, None

    async def run(self, timeout=1800, stop_on_final=True):
        deadline = time.monotonic() + timeout
        disconnected_since = unknown_since = None
        failures = 0
        while time.monotonic() < deadline:
            try:
                obs, result = await self.step()
                failures = 0
            except (OSError, TimeoutError) as exc:
                failures += 1
                self.supervisor = Supervisor.RECOVERING
                self.events.emit("falha_observacao", reason=type(exc).__name__)
                if failures >= 5:
                    return {"status": "bloqueado", "reason": "Falha de observação persistente"}
                await asyncio.sleep(min(2, failures * .3))
                continue
            now = time.monotonic()
            if obs.phase == Phase.CLOSED:
                return {"status": "encerrado", "final_result_verified": False}
            disconnected_since = (disconnected_since or now) if not obs.connected else None
            unknown_since = (unknown_since or now) if obs.phase == Phase.UNKNOWN else None
            if disconnected_since and now - disconnected_since > 60:
                return {"status": "bloqueado", "reason": "Conexão não recuperada em 60 s"}
            if unknown_since and now - unknown_since > 45:
                return {"status": "bloqueado", "reason": "Interface não reconhecida; nenhuma mutação pendente"}
            if stop_on_final and obs.phase == Phase.FINAL_RESULT and obs.ranking:
                return {"status": "concluido", "final_result_verified": True,
                        "ranking": asdict(obs.ranking)}
            await asyncio.sleep(.15 if result else .25)
        return {"status": "prazo_encerrado", "final_result_verified": False}
