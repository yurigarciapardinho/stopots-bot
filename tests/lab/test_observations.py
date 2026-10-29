import importlib.util
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "tools/stopots_lab.py"
spec = importlib.util.spec_from_file_location("stopots_lab", PATH)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def test_final_generation_is_not_final_ranking():
    s = {"headings": ["GERANDO RANKING FINAL"], "text": "GERANDO RANKING FINAL"}
    assert lab.classify(s) == "TRANSICAO_FINAL"


def test_dictionary_lookup_normalization_preserves_original():
    original = "águia"
    assert lab.normalize(original) == "AGUIA"
    assert original == "águia"


def test_epoch_invalidates_equal_letter_and_field_identity():
    s = {"epoch": "a", "headings": ["PREENCHA AS CATEGORIAS"], "text": "RODADAS: 1/4", "fields": [{"id": "inputText-0", "label": "AVE"}]}
    before = lab.context_of(s)
    s["epoch"] = "b"
    assert before != lab.context_of(s)


def test_password_modal_takes_precedence_over_background_home():
    s = {"inputs": [{"type": "password"}], "buttons": [{"text": "CRIAR SALA"}]}
    assert lab.classify(s) == "ENTRADA_PRIVADA"


def test_empty_or_partial_form_is_not_confirmed_as_complete():
    expected = {"inputText-0": "ARARA", "inputText-1": "AMARELO"}
    assert not lab.answers_match({"phase": "ESCRITA", "fields": []}, expected)
    assert not lab.answers_match({"phase": "ESCRITA", "fields": [{"id": "inputText-0", "value": "ARARA"}]}, expected)


def test_new_field_invalidates_confirmation_without_key_error():
    s = {"phase": "ESCRITA", "fields": [{"id": "inputText-0", "value": "ARARA"}, {"id": "inputText-1", "value": ""}]}
    assert not lab.answers_match(s, {"inputText-0": "ARARA"})


def test_recorded_fixtures_do_not_reinvent_field_count():
    fixtures = list((Path(__file__).parent / "fixtures").glob("escrita-*.json"))
    assert fixtures, "Capture a fixture real de escrita antes do aceite do laboratório"
    for p in fixtures:
        s = json.loads(p.read_text())
        assert lab.classify(s) == "ESCRITA"
        assert len(s["fields"]) > 0
        assert len({f["id"] for f in s["fields"]}) == len(s["fields"])
