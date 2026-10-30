"""Preparar uma revisão editorial explícita; não publica a fonte automaticamente."""
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from stopots_v2.normalization import lookup,game_value,utf16_length
from stopots_v2.vocabulary import Taxonomy,digest


def main():
 now=datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat()
 document=json.loads((ROOT/'data/source/editorial.json').read_text())
 snapshot=json.loads((ROOT/'data/source/catalogo-fatos-2026-10-30.json').read_text())
 seeds=json.loads((ROOT/'data/review/catalogo-sementes-2026-10-30.json').read_text())
 definitions={'pda':'Personagem de Desenho Animado','pch':'Partes do Corpo Humano','jlr':'Jornal, Livro ou Revista',
              'flv':'Fruta, Legume ou Verdura','cep':'Cidade, Estado ou País','mse':'Minha Sogra É','mst':'Minha Sogra Tem','msu':'Minha Sogra Usa','paf':'Planta, Árvore ou Flor'}
 user_id='definicoes-usuario-2026-10-30';local_id='editorial-catalogo-2026-10-30'
 sources={user_id:{'kind':'user_category_definitions','provided_at':now,'definitions':definitions,
                    'examples':{'pda':['Bob Esponja','Pikachu','Patolino'],'pch':['Perna','Coração','Hímen'],'jlr':['Jogo dos Tronos','Veja','Recreio']},
                    'scope':'Definições fornecidas pelo usuário nesta sessão; não atribuídas à ajuda oficial. Exemplos não implicam promoção automática.'},
          local_id:{'kind':'local_editorial_review','url':'https://github.com/Lucas8x/stopots-bot','accessed_at':now,'license':'MIT',
                    'scope':'Seleção editorial explícita do assistente nesta tarefa: palavras usuais, grafias revisadas e associações por contexto. Não é validação semântica do servidor nem importação de respostas de jogadores.',
                    'candidate_file':'data/review/catalogo-sementes-2026-10-30.json','candidate_sha256':digest(seeds),
                    'references':['https://dicionario.priberam.org/','https://www.gov.br/saude/pt-br/composicao/sectics/rename','https://www.wikidata.org/wiki/Wikidata:Data_access'],
                    'review_decisions':['Sintomas não são promovidos em bloco a doenças. HIV não foi aprovado como doença.','Aranha não foi aprovada como inseto. Quibe não foi aprovado como sobremesa.','Jornal Hoje é programa de TV, sem aprovação como jornal escrito.','Nomes maiores que 20 unidades UTF-16 não são truncados.','Nenhum papel de vilão/super-herói é inferido só da presença do personagem no universo.']}}
 new={cid:{'label':label,'language':'pt','aliases':[],'includes':[]} for cid,label in [('mst','MST'),('msu','MSU'),('jornal','Jornal'),('livro','Livro'),('revista','Revista'),('planta','Planta'),('paf','PÁF')]}
 aliases={'pda':['Personagem de Desenho Animado','Personagens de Desenho Animado'],
          'pch':['Parte do Corpo Humano','Partes do Corpo Humano'],
          'jlr':['Jornal, Livro ou Revista','Jornal Livro ou Revista','Jornais, Livros e Revistas'],
          'flv':['Fruta, Legume ou Verdura','Frutas, Legumes e Verduras'],
          'cep':['Cidade, Estado ou País','Cidade Estado País'],
          'mse':['Minha Sogra É'],'mst':['Minha Sogra Tem'],'msu':['Minha Sogra Usa'],
          'paf':['PAF','Planta, Árvore ou Flor','Planta Árvore Flor']}
 patch={'schema_version':1,'id':'catalogo-publico-e-siglas-2026-10-30-v1','base_sha256':digest(document),
        'sources':sources,'new_categories':new,'taxonomy_reviews':{cid:{'source':user_id,'definition':meaning,'aliases':aliases[cid]} for cid,meaning in definitions.items()},
        'includes_additions':{'jlr':['jornal','livro','revista'],'paf':['planta','arvore','flor'],'personagem_ficticio':['pda','super_heroi']},'entries':[]}
 working=json.loads(json.dumps(document));working['categories'].update(new)
 tax=Taxonomy(working)
 table_map={'estado_eua':'estado','unidades_federativas':'estado','cbkc_racas':'raca_de_cachorro'}
 # Estas tabelas têm condição de origem objetiva; os demais grupos usam somente
 # a seleção nominal revisada abaixo para evitar tipagens ocasionais da Wikidata.
 expanded={'pais','estado_eua','unidades_federativas','cbkc_racas','sobrenome','idioma','banda','filme','game','musica'}
 indexed=defaultdict(dict);sources_by_table={}
 for table_id,table in snapshot['payload']['tables'].items():
  cid=table_map.get(table_id,table_id)
  if not table.get('records') or cid not in working['categories']:continue
  sid='catalogo-fatos-'+table_id
  sources[sid]={'kind':'tabular_snapshot_review','url':table['url'],'accessed_at':snapshot['observed_at'],
                'snapshot':'data/source/catalogo-fatos-2026-10-30.json','snapshot_sha256':digest(snapshot['payload']),
                'table':table_id,'allowed_categories':[cid],
                'review_rule':'Nome corresponde ao registro datado; associação limitada à categoria explicitamente revisada. Tipagem externa não é consenso do jogo.'}
  sources_by_table[table_id]=sid
  for row in table['records']:indexed[cid].setdefault(lookup(row['name']),(sid,row))
 excluded=[];pairs=set()
 user_examples={(cid,lookup(word)) for cid,values in sources[user_id]['examples'].items() for word in values}
 def add(cid,name,source=None,record=None):
  key=lookup(name)
  if not key or not 'a'<=key[0]<='z' or utf16_length(game_value(name))>20:
   excluded.append({'category':cid,'word':name,'reason':'initial_or_ui_limit'});return
  if (cid,key) in pairs:return
  pairs.add((cid,key))
  if source is None:
   if (cid,key) in user_examples:source=user_id
   elif key in indexed[cid]:source,record=indexed[cid][key]
   else:source=local_id
  entry={'category':working['categories'][cid]['label'],'word':name,'source':source,'state':'approved','review_note':'Associação revisada explicitamente para o contexto do tema; não garante consenso de outros jogadores.'}
  if record:entry['review_note']+=' Registro '+record['id']+'.'
  patch['entries'].append(entry)
 for label,values in seeds['categories'].items():
  resolved=tax.resolve(label)
  if resolved.state!='resolved':raise ValueError('Tema editorial não resolvido: '+label)
  for name in values.split('|'):add(resolved.category,name)
 blocked={'BBC News','Wikinotícias em russo','Regresso ao Futuro','Ur So Gay'}
 for table_id in sorted(expanded):
  table=snapshot['payload']['tables'][table_id];cid=table_map.get(table_id,table_id);counts=defaultdict(int)
  for row in table['records']:
   name=row['name'];key=lookup(name)
   if name in blocked or any(c in name for c in '()[]:'):continue
   if table_id=='unidades_federativas' and row['abbreviation']=='DF':continue
   if not key or not 'a'<=key[0]<='z' or utf16_length(game_value(name))>20:continue
   maximum=10 if table_id in ('pais','estado_eua','unidades_federativas') else 3
   if counts[key[0]]>=maximum:continue
   counts[key[0]]+=1;add(cid,name,sources_by_table[table_id],row)
 patch['review_metrics']={'seed_candidates':sum(len(v.split('|')) for v in seeds['categories'].values()),'explicit_reviewed_pairs':len(patch['entries']),'excluded':excluded,
                         'external_records_not_automatically_approved':sum(len(t['records']) for t in snapshot['payload']['tables'].values())}
 path=ROOT/'data/source/catalogo-revisado-v1.json'
 if path.exists():raise ValueError('Revisão já preparada; não sobrescrever uma identidade publicada')
 path.write_text(json.dumps(patch,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'review_pairs':len(patch['entries']),'sources':len(sources),'excluded':len(excluded),'new_categories':len(new)},ensure_ascii=False))


if __name__=='__main__':main()
