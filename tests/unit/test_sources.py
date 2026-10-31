import json
from pathlib import Path
import pytest

from stopots_v2.sources import IBGE_SOURCE, approve_ibge_geography, import_ibge, validate_ibge
from stopots_v2.vocabulary import Vocabulary, import_legacy
from stopots_v2.domain import Verdict

ROOT = Path(__file__).resolve().parents[2]


def documents():
    editorial = json.loads((ROOT/'data/source/editorial.json').read_text(encoding="utf-8"))
    legacy = import_legacy(ROOT/'stopots_bot/dictionary.json', editorial['categories'])
    snapshot = json.loads((ROOT/'data/source/ibge-municipios.json').read_text(encoding="utf-8"))
    return legacy, snapshot


def test_source_import_is_pending_until_explicit_rule_review():
    legacy, snapshot = documents()
    imported = import_ibge(legacy, snapshot)
    assert len(snapshot['records']) == 5571
    associations = [a for a in imported['associations'] if IBGE_SOURCE in a['sources']]
    assert len(associations) == 5571 and all(a['state']=='pending' for a in associations)
    approved = approve_ibge_geography(imported, snapshot)
    assert all(a['state']=='pending' for a in approved['associations'] if a['sources']==['legacy'])


def test_source_corruption_rejected_and_duplicate_names_keep_entities():
    legacy, snapshot = documents()
    broken = json.loads(json.dumps(snapshot))
    broken['records'].append(broken['records'][0])
    with pytest.raises(ValueError, match='duplicado'):
        validate_ibge(broken)
    imported = import_ibge(legacy, snapshot)
    entry = next(a for a in imported['associations'] if IBGE_SOURCE in a['sources'])
    entry['category'] = 'animal'
    with pytest.raises(ValueError, match='ibge-city-v1'):
        approve_ibge_geography(imported, snapshot)


def test_city_candidates_and_limits():
    v = Vocabulary.bundled()
    assert v.evaluate('Cidade','S','São Paulo')[0] == Verdict.COMPATIBLE
    assert v.evaluate('CEP','B','Belo Horizonte')[0] == Verdict.COMPATIBLE
    candidates = v.candidates('Cidade', 'S', 20)
    from stopots_v2.normalization import lookup, game_value, utf16_length
    assert len({lookup(x[1]) for x in candidates}) == len(candidates)
    assert all(utf16_length(game_value(x[1])) <= 20 for x in candidates)
