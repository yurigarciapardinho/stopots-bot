from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class Phase(StrEnum):
    HOME = "INICIO"
    ENTERING = "ENTRANDO"
    ROOM = "SALA"
    COUNTDOWN = "CONTAGEM"
    WRITING = "ESCRITA"
    REVIEW = "REVISAO"
    ROUND_RESULT = "RESULTADO_RODADA"
    FINAL_RESULT = "RESULTADO_PARTIDA"
    UNKNOWN = "DESCONHECIDO"
    CLOSED = "ENCERRADO"


class Supervisor(StrEnum):
    ACTIVE = "ATIVO"
    PAUSED = "PAUSADO"
    DISCONNECTED = "DESCONECTADO"
    RECOVERING = "RECUPERANDO"


class Verdict(StrEnum):
    COMPATIBLE = "COMPATIVEL"
    INCOMPATIBLE = "INCOMPATIVEL"
    UNKNOWN = "DESCONHECIDA"


class Kind(StrEnum):
    FILL = "PREENCHER"
    STOP = "PEDIR_STOP"
    VOTE = "DEFINIR_VOTO"
    CONFIRM = "CONFIRMAR_ETAPA"
    CONTINUE = "CONTINUAR"


class Status(StrEnum):
    APPLIED = "APLICADA"
    SATISFIED = "JA_SATISFEITA"
    STALE = "OBSOLETA"
    BLOCKED = "BLOQUEADA"
    INDETERMINATE = "INDETERMINADA"
    FAILED = "FALHOU"


@dataclass(frozen=True)
class Context:
    session_id: str
    room_epoch: int = 0
    match_epoch: int = 0
    round_epoch: int = 0
    round_index: int | None = None
    review_epoch: int = 0
    review_index: int | None = None
    ui_revision: int = 0


@dataclass(frozen=True)
class Field:
    ref: str
    label: str
    value: str
    editable: bool
    max_length: int | None


@dataclass(frozen=True)
class Group:
    ref: str
    text: str
    checked: bool
    label_ref: str
    enabled: bool = True


@dataclass(frozen=True)
class Control:
    ref: str
    enabled: bool


@dataclass(frozen=True)
class Rules:
    locale: str = "pt-BR"
    stop_mode: str | None = None
    time_mode: str | None = None
    letters: tuple[str, ...] = ()
    category_pool: tuple[str, ...] = ()
    is_host: bool | None = None
    revision: str = ""


@dataclass(frozen=True)
class Ranking:
    rows: tuple[tuple[str, int], ...] = ()
    semantic: str = "desconhecida"


@dataclass(frozen=True)
class Observation:
    context: Context
    seq: int
    at: float
    phase: Phase
    letter: str | None = None
    total_rounds: int | None = None
    fields: tuple[Field, ...] = ()
    fields_stable: bool = False
    review_theme: str | None = None
    review_total: int | None = None
    groups: tuple[Group, ...] = ()
    stop: Control | None = None
    confirm: Control | None = None
    proceed: Control | None = None
    connected: bool = True
    rules: Rules = Rules()
    ranking: Ranking | None = None


@dataclass(frozen=True)
class Action:
    id: str
    kind: Kind
    context: Context
    target: str
    desired: str | bool | None
    deadline: float
    expected_value: str | bool | None = None
    expected_label: str | None = None


@dataclass(frozen=True)
class ActionResult:
    status: Status
    reason: str
    observed: Observation | None = None


class BrowserPort(Protocol):
    async def observe(self) -> Observation: ...
    async def apply(self, action: Action) -> ActionResult: ...
    async def close(self) -> None: ...
