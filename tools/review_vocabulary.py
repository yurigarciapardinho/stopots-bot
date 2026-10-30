"""Aplicar revisão factual explícita à fonte atual, sem promover sugestões por padrão."""
from pathlib import Path
import json
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from stopots_v2.vocabulary import Taxonomy, atomic_write, canonical, compile_release, digest, lexeme_id, publish, validate
from stopots_v2.normalization import lookup


def apply_review(document, patch, source_root=ROOT):
    result=json.loads(json.dumps(validate(document)))
    if patch.get('schema_version')!=1 or not patch.get('id'):
        raise ValueError('Revisão sem esquema ou identidade')
    fingerprint=digest(patch)
    prior=result.get('applied_reviews',{}).get(patch['id'])
    if prior:
        if prior!=fingerprint:raise ValueError('Identidade de revisão reutilizada com outro conteúdo')
        return result
    if digest(document)!=patch['base_sha256']:
        raise ValueError('Fonte mudou; revisar a diferença antes de reaplicar')
    snapshots={};verified_names={};verified_categories={};verified_pairs={}
    for sid,source in patch['sources'].items():
        if sid in result['sources'] and result['sources'][sid]!=source:
            raise ValueError('Fonte já cadastrada com metadados diferentes')
        if source.get('kind')=='user_category_definitions':
            if not source.get('provided_at') or not source.get('definitions'):
                raise ValueError('Definição do usuário sem data ou significados explícitos')
            verified_pairs[sid]={(lookup(word),cid) for cid,words in source.get('examples',{}).items() for word in words}
        elif not source.get('url','').startswith('https://') or not source.get('accessed_at'):
            raise ValueError('Referência factual precisa de URL e data')
        if source.get('kind') in ('wikidata_snapshot_review','tabular_snapshot_review'):
            path=(source_root/source['snapshot']).resolve()
            if not path.is_relative_to(source_root.resolve()):raise ValueError('Snapshot fora do projeto')
            if str(path) not in snapshots:snapshots[str(path)]=json.loads(path.read_text())
            snapshot=snapshots[str(path)]
            if digest(snapshot['payload'])!=source['snapshot_sha256']:
                raise ValueError('Checksum do snapshot factual inválido')
            if source.get('kind')=='tabular_snapshot_review':
                table=snapshot['payload']['tables'][source['table']]
                if table.get('error') or not table.get('records') or not source.get('allowed_categories'):
                    raise ValueError('Tabela factual vazia, incompleta ou sem categorias revisadas')
                names=[record['name'] for record in table['records']]
                verified_categories[sid]=set(source['allowed_categories'])
            else:
                record=next((r for r in snapshot['payload']['records'] if r['id']==source['entity_id']),None)
                if not record or record['lastrevid']!=source['revision']:
                    raise ValueError('Entidade ou revisão não corresponde ao snapshot')
                names=[v['value'] for v in record.get('labels',{}).values()]
                names += [v['value'] for values in record.get('aliases',{}).values() for v in values]
            verified_names[sid]={lookup(name) for name in names}
        result['sources'][sid]=source
    for cid,category in patch.get('new_categories',{}).items():
        if cid in result['categories'] and result['categories'][cid]!=category:
            raise ValueError('Categoria existente não pode ser substituída pela revisão')
        result['categories'][cid]=category
    for cid,children in patch.get('includes_additions',{}).items():
        result['categories'][cid]['includes']=sorted(set(result['categories'][cid].get('includes',[]))|set(children))
    for cid,review in patch.get('taxonomy_reviews',{}).items():
        if cid not in result['categories'] or review['source'] not in patch['sources']:
            raise ValueError('Revisão de tema sem categoria ou fonte da revisão')
        source=patch['sources'][review['source']]
        if source.get('kind')=='user_category_definitions' and source['definitions'].get(cid)!=review['definition']:
            raise ValueError('Significado não corresponde à definição fornecida pelo usuário')
        category=result['categories'][cid]
        category.update(definition=review['definition'],definition_source=review['source'],definition_status='reviewed')
        category['aliases']=list(dict.fromkeys([*category.get('aliases',[]),*review.get('aliases',[])]))
    tax=Taxonomy(result)
    for cid,review in patch.get('taxonomy_reviews',{}).items():
        if any(tax.resolve(alias).category!=cid for alias in review.get('aliases',[])):
            raise ValueError('Alias de tema ambíguo ou conflitante')
    protected={a['lexeme_id'] for a in result['associations'] if a['state'] in ('approved','rejected')}
    protected_spelling={w['id']:w['display'] for w in result['lexemes'] if w['id'] in protected}
    words={w['id']:w for w in result['lexemes']}
    pairs={(a['lexeme_id'],a['category']):a for a in result['associations']}
    for entry in patch['entries']:
        if entry['source'] not in patch['sources']:raise ValueError('Associação sem referência da revisão')
        if entry['source'] in verified_names and lookup(entry['word']) not in verified_names[entry['source']]:
            raise ValueError('Grafia não confirmada na entidade do snapshot')
        resolution=tax.resolve(entry['category'])
        if resolution.state!='resolved':raise ValueError('Categoria da revisão não resolvida')
        if tax.categories[resolution.category].get('definition_status')=='unresolved':
            raise ValueError('Tema ainda sem significado confirmado')
        if entry['source'] in verified_categories and resolution.category not in verified_categories[entry['source']]:
            raise ValueError('Tabela factual não foi revisada para essa categoria')
        if entry['source'] in verified_pairs and (lookup(entry['word']),resolution.category) not in verified_pairs[entry['source']]:
            raise ValueError('Exemplo não foi fornecido pelo usuário para essa categoria')
        lang=entry.get('language',tax.categories[resolution.category].get('language','pt'))
        if lang!=tax.categories[resolution.category].get('language','pt'):
            raise ValueError('Idioma lexical incompatível com a categoria')
        lid=lexeme_id(entry['word'],lang,entry.get('sense',''))
        pair=(lid,resolution.category)
        existing=pairs.get(pair)
        if existing and existing['state'] in ('approved','rejected'):
            continue  # decisões anteriores, inclusive rejeições, são preservadas
        spelling=unicodedata.normalize('NFC',protected_spelling.get(lid,entry['word']).strip())
        state=entry.get('state','pending')
        word=words.get(lid)
        if word is None:
            word={'id':lid,'display':spelling,'key':lookup(spelling),'language':lang,'sense':entry.get('sense',''),'variants':[spelling]}
            words[lid]=word;result['lexemes'].append(word)
        elif state=='approved':
            word['display']=spelling
            if spelling not in word['variants']:word['variants'].append(spelling)
        if existing is None:
            existing={'lexeme_id':lid,'category':resolution.category,'sources':[]}
            pairs[pair]=existing;result['associations'].append(existing)
        if entry['source'] not in existing['sources']:existing['sources'].append(entry['source'])
        existing.update(state=state,review_note=entry.get('review_note',''))
        if state in ('approved','rejected'):protected_spelling.setdefault(lid,word['display'])
    result.setdefault('applied_reviews',{})[patch['id']]=fingerprint
    return validate(result)


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('patch',type=Path)
    parser.add_argument('--publicar',action='store_true')
    args=parser.parse_args()
    path=ROOT/'data/source/editorial.json'
    original=json.loads(path.read_text())
    result=apply_review(original,json.loads(args.patch.read_text()))
    release=compile_release(result)
    if digest(json.loads(path.read_text()))!=digest(original):raise ValueError('Fonte editada durante a revisão')
    atomic_write(path,canonical(result)+b'\n')
    if args.publicar:publish(result,ROOT/'src/stopots_v2/resources/vocabulary.json')
    print(json.dumps({'review_saved':True,'published':args.publicar,'manifest':release['manifest']},ensure_ascii=False))


if __name__=='__main__':main()
