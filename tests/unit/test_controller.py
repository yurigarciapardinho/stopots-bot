import asyncio
from dataclasses import replace
import json

from stopots_v2.application import Controller, EventLog, Planner, Policy
from stopots_v2.domain import ActionResult, Context, Control, Field, Group, Kind, Observation, Phase, Status, Supervisor
from stopots_v2.identity import ContextTracker
from stopots_v2.vocabulary import Vocabulary


def writing(**changes):
    return replace(Observation(Context("test", 1, 1, 1, 1, ui_revision=1), 1, 100, Phase.WRITING,
        "A", 4, (Field("#f", "Animal", "", True, 20),), True, stop=Control("#stop", True)), **changes)


def test_manual_text_and_disabled_controls():
    p = Planner(Vocabulary.bundled(), Policy(request_stop=True))
    obs = writing(fields=(Field("#f", "Animal", "MINHA ESCOLHA", True, 20),), stop=Control("#stop", False))
    assert p.plan(obs) is None
    assert p.plan(replace(obs, stop=Control("#stop", True))).kind == Kind.STOP


def test_partial_form_unknown_category_and_observe_only():
    p = Planner(Vocabulary.bundled(), Policy(request_stop=True))
    assert p.plan(writing(fields_stable=False)) is None
    assert p.plan(writing(fields=(Field("#f", "Tema novo", "", True, 20),))) is None
    assert Planner(Vocabulary.bundled(), Policy(observe_only=True)).plan(writing()) is None


def test_unknown_vote_preserved_and_wrong_initial_unchecked():
    obs = writing(phase=Phase.REVIEW, review_theme="Animal", groups=(Group("#g", "ARIRANHA", False, "#label"),),
                  confirm=Control("#confirm", False))
    p = Planner(Vocabulary.bundled(), Policy(set_votes=True, confirm_review=True))
    assert p.plan(obs) is None
    action = p.plan(replace(obs, groups=(Group("#g", "BALEIA", True, "#label"),)))
    assert action.kind == Kind.VOTE and action.desired is False


def test_indeterminate_click_is_not_repeated_after_ui_revision():
    p = Planner(Vocabulary.bundled(), Policy(confirm_review=True))
    obs = writing(phase=Phase.REVIEW, confirm=Control("#c", True))
    action = p.plan(obs)
    p.record(action, ActionResult(Status.INDETERMINATE, "timeout"))
    assert p.plan(replace(obs, context=replace(obs.context, ui_revision=8))) is None
    assert p.plan(replace(obs, context=replace(obs.context, review_epoch=2))) is not None


def test_letter_repeated_new_round_and_new_match():
    clock = [0.0]
    t = ContextTracker("test", clock=lambda: clock[0])
    raw = {"phase": "SALA", "room_key": "/pt/1", "rules": {}}
    t.update(raw)
    raw.update(phase="ESCRITA", round_index=1, letter="A", fields=[{"ref": "#a", "label": "Animal"}])
    first = t.update(raw)[0]
    raw.update(phase="RESULTADO_RODADA")
    t.update(raw)
    raw.update(phase="ESCRITA", round_index=2)
    second = t.update(raw)[0]
    assert second.round_epoch > first.round_epoch and second.match_epoch == first.match_epoch
    raw.update(phase="SALA")
    t.update(raw)
    raw.update(phase="DESCONHECIDO")  # contagem transitória não reconhecida
    t.update(raw)
    raw.update(phase="ESCRITA", round_index=1)
    third = t.update(raw)[0]
    assert third.match_epoch > first.match_epoch


def test_revisions_exclude_timer_values_and_votes_but_include_schema():
    now = [0.0]
    t = ContextTracker("test", clock=lambda: now[0])
    raw = {"phase": "ESCRITA", "round_index": 1, "letter": "A", "fields": [{"ref": "#a", "label": "Animal", "value": ""}]}
    c1, _, stable = t.update(raw)
    assert not stable
    now[0] = 2
    raw["fields"][0]["value"] = "ARARA"
    c2, _, stable = t.update(raw)
    assert c1 == c2 and stable
    raw["fields"].append({"ref": "#b", "label": "Cor"})
    c3, _, stable = t.update(raw)
    assert c3.ui_revision > c2.ui_revision and not stable
    t.invalidate()
    assert t.context.room_epoch > c3.room_epoch


def test_pause_resume_and_serial_execution(tmp_path):
    control = tmp_path / "control.json"
    class FakePort:
        calls = 0
        active = 0
        max_active = 0
        async def observe(self):
            return writing()
        async def apply(self, action):
            self.calls += 1
            self.active += 1
            self.max_active = max(self.active, self.max_active)
            await asyncio.sleep(.001)
            self.active -= 1
            return ActionResult(Status.APPLIED, "ok")
    async def scenario():
        port = FakePort()
        ctl = Controller(port, Vocabulary.bundled(), control_file=control)
        control.write_text('{"paused":true}')
        await ctl.step()
        assert port.calls == 0 and ctl.supervisor == Supervisor.PAUSED
        control.write_text('{"paused":false}')
        await asyncio.gather(ctl.step(), ctl.step())
        assert port.calls == 1 and port.max_active == 1
    asyncio.run(scenario())


def test_log_does_not_record_input_or_url(tmp_path):
    log = EventLog(tmp_path / "events.jsonl")
    obs = writing(fields=(Field("#secret", "Animal", "TEXTO PESSOAL", True, 20),))
    log.emit("observacao", obs)
    assert "TEXTO PESSOAL" not in log.path.read_text()
    assert "#secret" not in log.path.read_text()
