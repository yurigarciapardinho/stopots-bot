import asyncio
from dataclasses import replace
import json
import pytest

from stopots_v2.desktop_model import Invitation, Preferences, PRESETS, invitation_url
from stopots_v2.desktop_engine import DesktopEngine
from stopots_v2.application import Controller, Policy
from stopots_v2.domain import Context, Observation, Phase, Ranking
from stopots_v2.vocabulary import Vocabulary


def test_invite_preserves_leading_zero_and_rejects_other_targets():
    assert invitation_url(' https://stopots.com/pt/08193/ ') == 'https://stopots.com/pt/08193'
    for value in ['http://stopots.com/pt/08193', 'https://stopots.com.evil/pt/08193',
                  'https://user@stopots.com/pt/08193', 'https://stopots.com/pt/game',
                  'https://stopots.com/pt/٠٨١٩٣', 'https://stopots.com/pt/08193?x=1']:
        with pytest.raises(ValueError): invitation_url(value)


def test_password_is_exact_and_not_in_representation():
    password = ' A9áÇ!$&\'"\\e\u0301 '
    request = Invitation('https://stopots.com/pt/08193', 'Jogador', True, password).validate()
    assert request.password == password
    assert password not in repr(request)
    with pytest.raises(ValueError): Invitation(request.url, 'Jogador', True, '').validate()


def test_preferences_presets_and_persistence_are_explicit(tmp_path):
    p = Preferences(tmp_path/'preferences.json')
    p.preset('Automático')
    assert p.policy.request_stop and p.policy.confirm_review
    p.action('request_stop', False)
    q = Preferences(p.path)
    assert q.profile == 'Personalizado' and not q.policy.request_stop
    assert q.policy.confirm_review
    q.preset('Só preencher')
    assert q.policy == Policy()
    q.preset('Só observar')
    assert q.policy.observe_only and not q.policy.fill_blanks
    data=json.loads(q.path.read_text(encoding="utf-8"))
    assert not {'password','url','active','endpoint'} & data.keys()
    q.path.write_text('[]', encoding="utf-8")
    assert Preferences(q.path).policy == Policy()


def test_final_pauses_but_next_match_can_be_observed_without_actions(tmp_path):
    async def case():
        c=Context('desktop',1,1,4,4)
        class Port:
            obs=Observation(c,1,1,Phase.FINAL_RESULT,ranking=Ranking((('p1',50),),'total_partida','podium'))
            async def observe(self): return self.obs
            async def apply(self,action): raise AssertionError('A ajuda deveria estar pausada')
        port=Port();engine=DesktopEngine(tmp_path,Policy(),lambda _:None)
        engine.vocabulary=Vocabulary.bundled()
        engine.controller=Controller(port,engine.vocabulary)
        engine.controller.paused=lambda:not engine.active.is_set()
        engine.active.set();await engine.tick()
        assert not engine.active.is_set() and engine.state['connected']
        port.obs=replace(port.obs,context=replace(c,match_epoch=2,round_epoch=5,round_index=1),phase=Phase.WRITING,ranking=None)
        await engine.tick()
        assert not engine.active.is_set() and engine.state['phase']==Phase.WRITING
        attempted={'already-sent'};engine.controller.planner.attempted=attempted
        await engine.handle(None,'policy',(PRESETS['Automático'],7))
        assert engine.state['revision']==7 and not engine.active.is_set()
        assert engine.controller.planner.attempted is attempted
    asyncio.run(case())


def test_commands_are_not_lost_before_loop_is_ready(tmp_path):
    engine=DesktopEngine(tmp_path,Policy(),lambda _:None)
    engine.submit('policy',(Policy(request_stop=True),1))
    command,payload=engine.queue.get_nowait()
    assert command=='policy' and payload[1]==1
    engine.active.set();engine.submit('pause')
    assert not engine.active.is_set()


def test_ready_is_a_single_event_and_does_not_force_compact_forever(tmp_path):
    snapshots=[]
    engine=DesktopEngine(tmp_path,Policy(),snapshots.append)
    engine.publish(ready=True)
    engine.publish(filled=1)
    assert snapshots[0]['ready'] is True
    assert 'ready' not in snapshots[1] and 'ready' not in engine.state
