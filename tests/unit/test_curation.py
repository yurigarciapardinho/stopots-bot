import copy
import importlib.util
import json
from pathlib import Path
import pytest
from stopots_v2.domain import Verdict
from stopots_v2.vocabulary import Vocabulary, compile_release, digest, upsert

ROOT=Path(__file__).parents[2]
spec=importlib.util.spec_from_file_location('curation',ROOT/'tools/review_vocabulary.py')
curation=importlib.util.module_from_spec(spec);spec.loader.exec_module(curation)


def case():
    doc={'schema_version':1,'categories':{'animal':{'label':'Animal','language':'pt','includes':[]}},
         'sources':{'original':{'kind':'test_fixture'}},'lexemes':[],'associations':[]}
    doc=upsert(doc,'Animal','Gato','approved','original','Decisão original da fixture')
    doc=upsert(doc,'Animal','Arara','rejected','original','Rejeição sintética que deve ser preservada')
    patch={'schema_version':1,'id':'fixture-review','base_sha256':digest(doc),
           'sources':{'review':{'kind':'test_fixture','url':'https://example.org/fixture','accessed_at':'2026-10-29'}},
           'entries':[{'category':'Animal','word':word,'source':'review','state':state,'review_note':'Fixture, sem publicação real'}
                      for word,state in [('Gato','approved'),('Arara','approved'),('Baleia','approved')]]}
    patch['entries'].append({'category':'Animal','word':'Capivara','source':'review'})
    patch['new_categories']={'fixture':{'label':'Fixture','language':'pt','includes':[]}}
    patch['entries'].append({'category':'Fixture','word':'gato','source':'review','state':'approved','review_note':'Outra associação da fixture'})
    patch['entries'].append({'category':'Fixture','word':'baleia','source':'review','state':'approved','review_note':'Grafia aprovada na mesma revisão deve permanecer'})
    return doc,patch


def test_review_preserves_decisions_defaults_pending_and_is_idempotent():
    doc,patch=case();before=digest(doc)
    reviewed=curation.apply_review(doc,patch)
    assert digest(doc)==before
    assert next(a for a in reviewed['associations'] if a['review_note']=='Decisão original da fixture')['sources']==['original']
    states=[a['state'] for a in reviewed['associations']]
    assert states.count('rejected')==1 and states.count('pending')==1
    assert compile_release(reviewed)['manifest']['approved_associations']==4
    assert next(w for w in reviewed['lexemes'] if w['key']=='gato')['display']=='Gato'
    assert next(w for w in reviewed['lexemes'] if w['key']=='baleia')['display']=='Baleia'
    assert curation.apply_review(reviewed,patch)==reviewed
    changed=copy.deepcopy(patch);changed['entries'][0]['word']='Cachorro'
    with pytest.raises(ValueError,match='reutilizada'):curation.apply_review(reviewed,changed)


def test_stale_source_is_not_overwritten():
    doc,patch=case();doc['categories']['animal']['aliases']=['Bicho']
    before=digest(doc)
    with pytest.raises(ValueError,match='Fonte mudou'):curation.apply_review(doc,patch)
    assert digest(doc)==before


def test_batch_preserves_public_editorial_upsert_contract():
    doc,patch=case()
    patch['new_categories']={}
    patch['entries']=[{'category':'Animal','word':word,'source':'review','state':state,'review_note':'Revisão da fixture'}
                      for word,state in [('Baleia','approved'),('Capivara','pending'),('Leão','rejected')]]
    expected=copy.deepcopy(doc);expected['sources'].update(patch['sources'])
    for entry in patch['entries']:
        expected=upsert(expected,entry['category'],entry['word'],entry['state'],entry['source'],entry['review_note'])
    actual=curation.apply_review(doc,patch);actual.pop('applied_reviews')
    assert actual==expected


def test_snapshot_corruption_blocks_review(tmp_path):
    doc,patch=case();payload={'records':[{'id':'Q1','lastrevid':1,'labels':{'pt':{'value':'Baleia'}}}]}
    snapshot=tmp_path/'snapshot.json';snapshot.write_text(json.dumps({'payload':payload}), encoding="utf-8")
    patch['sources']['review'].update(kind='wikidata_snapshot_review',snapshot='snapshot.json',snapshot_sha256=digest(payload),entity_id='Q1',revision=1)
    payload['records'][0]['lastrevid']=2;snapshot.write_text(json.dumps({'payload':payload}), encoding="utf-8")
    with pytest.raises(ValueError,match='Checksum'):curation.apply_review(doc,patch,tmp_path)


def test_public_curation_retains_language_and_directional_semantics():
    vocab=Vocabulary.bundled()
    assert vocab.evaluate('Palavra em Espanhol','G','Gato')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('Mamífero','G','Gato')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('Animal Aquático','G','Gato')[0]==Verdict.UNKNOWN
    assert vocab.evaluate('Animal','P','Peixe')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('Sobrenome','I','Iglesias')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('Série','I','iCarly')[0]==Verdict.COMPATIBLE
    assert vocab.candidates('PDA','F',20)


def test_user_definitions_are_explicit_and_alias_conflicts_are_rejected():
    doc,patch=case()
    patch['sources']['definition']={'kind':'user_category_definitions','provided_at':'2026-10-30',
                                  'definitions':{'fixture':'Tema da fixture'}}
    patch['taxonomy_reviews']={'fixture':{'source':'definition','definition':'Tema da fixture','aliases':['Tema explícito']}}
    reviewed=curation.apply_review(doc,patch)
    assert Vocabulary(compile_release(reviewed)).taxonomy.resolve('Tema explícito').category=='fixture'
    patch['taxonomy_reviews']['fixture']['definition']='Outro significado'
    with pytest.raises(ValueError,match='definição fornecida'):curation.apply_review(doc,patch)
    patch['taxonomy_reviews']['fixture'].update(definition='Tema da fixture',aliases=['Animal'])
    with pytest.raises(ValueError,match='conflitante'):curation.apply_review(doc,patch)


def test_tabular_proof_cannot_promote_another_category(tmp_path):
    doc,patch=case()
    payload={'tables':{'animals':{'records':[{'id':'1','name':word} for word in ['Gato','Arara','Baleia','Capivara']]}}}
    (tmp_path/'facts.json').write_text(json.dumps({'payload':payload}), encoding="utf-8")
    patch['sources']['review'].update(kind='tabular_snapshot_review',snapshot='facts.json',snapshot_sha256=digest(payload),
                                      table='animals',allowed_categories=['animal'])
    with pytest.raises(ValueError,match='essa categoria'):curation.apply_review(doc,patch,tmp_path)
    patch['entries']=[e for e in patch['entries'] if e['category']=='Animal']
    assert curation.apply_review(doc,patch,tmp_path)
    patch['entries'][2]['word']='Palavra não observada'
    with pytest.raises(ValueError,match='Grafia não confirmada'):curation.apply_review(doc,patch,tmp_path)


def test_all_registered_topics_have_usable_diverse_answers():
    vocab=Vocabulary.bundled()
    for category in vocab.taxonomy.categories.values():
        coverage={letter:vocab.candidates(category['label'],letter,20) for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
        assert sum(bool(words) for words in coverage.values())>=5, category['label']
    for label in ['PDA','PCH','JLR','MSÉ','MST','MSU','PÁF','PAF','Planta, Árvore ou Flor']:
        assert vocab.taxonomy.resolve(label).state=='resolved'
    assert vocab.taxonomy.resolve('PDA').category!=vocab.taxonomy.resolve('Desenho Animado').category
    assert vocab.evaluate('PÁF','A','Alecrim')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('PÁF','G','Goiabeira')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('PÁF','R','Rosa')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('PCH','P','Perna')[0]==Verdict.COMPATIBLE
    assert vocab.evaluate('JLR','P','Peter Pan')[0]==Verdict.COMPATIBLE
    for label,letter,word in [('Inseto','A','Aranha'),('Doença','F','Febre'),('Sobremesa','Q','Quibe'),('JLR','J','Jornal Hoje')]:
        assert vocab.evaluate(label,letter,word)[0]==Verdict.UNKNOWN
