from pathlib import Path
import json
import pytest

from stopots_v2.domain import Verdict
from stopots_v2.normalization import game_value, lookup, utf16_length
from stopots_v2.vocabulary import Vocabulary, Taxonomy, compile_release, import_legacy, publish, read_release, upsert, validate

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def editorial():
    return json.loads((ROOT / "data/source/editorial.json").read_text(encoding="utf-8"))


def test_import_counts_and_pending(editorial):
    doc = import_legacy(ROOT / "stopots_bot/dictionary.json", editorial["categories"])
    assert doc["import_metrics"] == {"letters": 26, "categories": 64, "cells": 1664,
        "entries": 2688, "empty_cells": 269, "normalized_duplicate_excess": 10}
    assert all(a["state"] == "pending" for a in doc["associations"])
    assert compile_release(doc)["manifest"]["approved_associations"] == 0


def test_normalization_and_utf16():
    assert lookup("  ÁGUIA\tAzul ") == "aguia azul"
    assert lookup("D'Ávila") == "d'avila"
    assert lookup("bem-te-vi") == "bem-te-vi"
    assert game_value("águia") == "AGUIA"
    assert utf16_length("a😀") == 3


def test_observed_real_input_normalization_fixture():
    fixture = json.loads((ROOT/'tests/contracts/fixtures/normalizacao-real.json').read_text(encoding="utf-8"))
    assert fixture['status']=='probe_completed'
    for case in fixture['cases']:
        actual = case.get('after_blur', case.get('actual'))
        assert game_value(case['requested']) == actual
    # Busca lexical preserva grafia; a compatibilidade usa a forma renderizada.
    assert lookup('Bem-te-vi') == 'bem-te-vi'


def test_review_recognizes_observed_game_spelling(editorial):
    v = Vocabulary.bundled()
    assert v.evaluate('Ave', 'B', 'BEM TE VI')[0] == Verdict.COMPATIBLE
    assert v.evaluate('Animal', 'B', 'BEM TE VI')[0] == Verdict.COMPATIBLE
    assert v.evaluate('Ave', 'B', 'Bem-te-vi')[0] == Verdict.COMPATIBLE
    fixture = upsert(editorial, 'Marca', 'A & B', 'approved', 'bootstrap-2026-10-29', 'Marca sintética de fixture')
    assert Vocabulary(compile_release(fixture)).evaluate('Marca', 'A', 'A  B')[0] == Verdict.COMPATIBLE


def test_directional_composition_and_unknown():
    v = Vocabulary.bundled()
    assert v.evaluate("Animal", "A", "Águia")[0] == Verdict.COMPATIBLE
    assert v.evaluate("Ave", "A", "Arara")[0] == Verdict.UNKNOWN
    assert v.evaluate("CEP", "D", "Diadema")[0] == Verdict.COMPATIBLE
    assert v.evaluate("Cidade", "D", "Dinamarca")[0] == Verdict.UNKNOWN
    assert v.evaluate("FLV", "B", "Banana")[0] == Verdict.COMPATIBLE
    assert v.evaluate("Tema inexistente", "A", "Arara")[0] == Verdict.UNKNOWN
    assert v.evaluate("Animal", "A", "Baleia")[0] == Verdict.INCOMPATIBLE
    assert v.evaluate("Animal", "A", "")[0] == Verdict.UNKNOWN


def test_absence_does_not_reject():
    assert Vocabulary.bundled().evaluate("Animal", "A", "Ariranha")[0] == Verdict.UNKNOWN


def test_english_limit_and_determinism():
    v = Vocabulary.bundled()
    assert v.evaluate("Palavra em Inglês", "A", "Apple")[0] == Verdict.COMPATIBLE
    assert not v.candidates("Palavra em Inglês", "A", 3)
    assert v.choose("Animal", "A", 20, "seed") == v.choose("Animal", "A", 20, "seed")
    assert not v.candidates("Tema sem categoria cadastrada", "Z", 20)


def test_two_edits_apostrophe_accent_and_snapshot(editorial, tmp_path):
    before = json.dumps(editorial, sort_keys=True)
    first = upsert(editorial, "Nome", "Álvaro", "approved", "bootstrap-2026-10-29", "Nome próprio")
    second = upsert(first, "Sobrenome", "D'Ávila", "approved", "bootstrap-2026-10-29", "Sobrenome")
    path = tmp_path / "release.json"
    publish(second, path)
    v = Vocabulary(read_release(path))
    assert v.evaluate("Nome", "A", "Álvaro")[0] == Verdict.COMPATIBLE
    assert v.evaluate("Sobrenome", "D", "D'Ávila")[0] == Verdict.COMPATIBLE
    assert json.dumps(editorial, sort_keys=True) == before
    assert isinstance(second["associations"], list)


def test_atomic_validation_preserves_old_release(editorial, tmp_path):
    path = tmp_path / "current.json"
    publish(editorial, path)
    first = path.read_bytes()
    broken = json.loads(json.dumps(editorial))
    broken["lexemes"] = "corrompido"
    with pytest.raises(ValueError):
        publish(broken, path)
    assert path.read_bytes() == first
    updated = upsert(editorial, "Animal", "Ariranha", "approved", "bootstrap-2026-10-29", "Mamífero")
    publish(updated, path)
    assert path.with_suffix(".json.previous").read_bytes() == first
    assert read_release(path)["manifest"]["sha256"] != read_release(path.with_suffix(".json.previous"))["manifest"]["sha256"]


def test_corrupt_release_and_alias_ambiguity(editorial, tmp_path):
    path = tmp_path / "v.json"
    release = compile_release(editorial)
    release["payload"]["lexemes"][0]["display"] = "alterado"
    path.write_text(json.dumps(release), encoding="utf-8")
    with pytest.raises(ValueError, match="Checksum"):
        read_release(path)
    tax = json.loads(json.dumps(editorial["categories"]))
    tax["animal"]["aliases"].append("ambíguo")
    tax["ave"]["aliases"].append("ambíguo")
    assert Taxonomy({"categories": tax}).resolve("ambíguo").state == "ambiguous"


def test_cycle_and_invalid_state_rejected(editorial):
    editorial["categories"]["ave"]["includes"] = ["animal"]
    with pytest.raises(ValueError, match="Ciclo"):
        validate(editorial)


def test_bootstrap_pool_a_to_d():
    labels = ["Profissão", "Programa de TV", "Fantasia", "Vilão", "Animal", "Carro", "Brinquedo", "Objeto",
              "Sabor de Pizza", "Palavra em Inglês", "Tem na academia", "Remédio", "Comida", "Time Esportivo", "Música", "Ave"]
    v = Vocabulary.bundled()
    assert all(v.candidates(label, letter, 20) for label in labels for letter in "ABCD")


def test_valid_previous_release_loaded_without_overwriting_corruption(editorial, tmp_path):
    from stopots_v2.cli import load_vocab
    path = tmp_path / "v.json"
    publish(editorial, path)
    publish(editorial, path)
    path.write_text('{"truncado":', encoding="utf-8")
    recovered = load_vocab(path)
    assert recovered.version == read_release(path.with_suffix('.json.previous'))['manifest']['sha256']
    assert path.read_text(encoding="utf-8") == '{"truncado":'
