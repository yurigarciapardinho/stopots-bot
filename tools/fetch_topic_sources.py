"""Obter fatos por pesquisa tipada e API Wikidata; não aprova associações."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
UA='StopotsVocabularyResearch/2.0 (local educational curation; https://github.com/Lucas8x/stopots-bot)'
RULES={
 'idioma':('P31','Q34770','language'), 'pais':('P31','Q6256','country'),
 'estado_eua':('P31','Q35657','U.S. state'), 'capital':('P31','Q5119','capital city'),
 'ator':('P106','Q33999','actor'), 'cantor':('P106','Q177220','singer'),
 'esportista':('P106','Q2066131','athlete'), 'banda':('P31','Q215380','musical group'),
 'filme':('P31','Q11424','film'), 'serie':('P31','Q5398426','television series'),
 'desenho_animado':('P31','Q581714','animated series'), 'programa_de_tv':('P31','Q15416','television program'),
 'game':('P31','Q7889','video game'), 'sobrenome':('P31','Q101352','family name'),
 'super_heroi':('P31','Q188784','superhero'), 'musica':('P31','Q7366','song'),
 'livro':('P31','Q8261','novel'), 'revista':('P31','Q41298','magazine'),
 'jornal':('P31','Q11032','newspaper'), 'doenca':('P31','Q12136','disease')}


def read(url):
 request=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
 with urllib.request.urlopen(request,timeout=18) as response:body=response.read()
 return gzip.decompress(body) if body.startswith(b'\x1f\x8b') else body


def api(**params):
 url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode(dict(format='json',maxlag=5,**params))
 data=json.loads(read(url))
 if data.get('error'):raise ValueError('API Wikidata: '+data['error']['code'])
 return data,url


def values(entity,prop):
 output=[]
 for claim in entity.get('claims',{}).get(prop,[]):
  snak=claim['mainsnak']
  if claim.get('rank')!='deprecated' and snak.get('snaktype')=='value':
   value=snak['datavalue']['value']
   output.append(value.get('id',value) if isinstance(value,dict) else value)
 return output


def fetch_table(pair):
 category,(prop,type_id,_) = pair
 query=f'haswbstatement:{prop}={type_id} haslabel:pt'
 if category=='pais':query+=' haswbstatement:P463=Q1065'
 try:
  found,url=api(action='query',list='search',srsearch=query,srnamespace=0,srlimit=150)
  ids=[r['title'] for r in found['query']['search']]
  records=[]
  for start in range(0,len(ids),50):
   data,_=api(action='wbgetentities',ids='|'.join(ids[start:start+50]),props='labels|descriptions|claims|info',languages='pt|en')
   for qid,entity in data['entities'].items():
    if type_id not in values(entity,prop):continue
    if category=='pais' and ('Q1065' not in values(entity,'P463') or values(entity,'P576')):continue
    if category=='capital' and values(entity,'P576'):continue
    label=entity.get('labels',{}).get('pt')
    if not label:continue
    claims={p:values(entity,p) for p in ('P31','P106','P463','P36','P1549') if values(entity,p)}
    records.append({'id':qid,'name':label['value'],'language':'pt','entity_revision':entity['lastrevid'],
                    'description':entity.get('descriptions',{}).get('pt',{}).get('value',''), 'facts':claims})
  print(json.dumps({'table':category,'records':len(records)}),flush=True)
  return category,{'url':url,'search':query,'predicate':prop,'required_value':type_id,'records':records}
 except Exception as exc:
  print(json.dumps({'table':category,'error':type(exc).__name__}),flush=True)
  return category,{'search':query,'error':type(exc).__name__,'records':[]}


def main():
 path=ROOT/'data/source/catalogo-fatos-2026-10-30.json'
 if path.exists():raise ValueError('Snapshot já existe; preservar a versão revisada e usar novo nome/data para nova obtenção')
 types=sorted({rule[1] for rule in RULES.values()})
 classes,_=api(action='wbgetentities',ids='|'.join(types),props='labels|info',languages='en|pt')
 for prop,qid,expected in RULES.values():
  actual=classes['entities'][qid].get('labels',{}).get('en',{}).get('value')
  if actual!=expected:raise ValueError(f'Classe não corresponde ao contrato: {qid} {actual}')
 with ThreadPoolExecutor(max_workers=3) as executor:tables=dict(executor.map(fetch_table,RULES.items()))
 countries=tables.get('pais',{}).get('records',[])
 demonyms=[]
 for record in countries:
  for name in record['facts'].get('P1549',[]):
   if isinstance(name,dict) and name.get('language') in ('pt','pt-br'):
    demonyms.append({'id':record['id'],'name':name['text'],'language':'pt','entity_revision':record['entity_revision']})
 tables['gentilico']={'url':tables['pais'].get('url'),'rule':'P1549 português dos países membros da ONU obtidos; não inferir gentílico da grafia do país','records':demonyms}
 uf_url='https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome'
 body=read(uf_url)
 records=[{'id':str(row['id']),'name':row['nome'],'abbreviation':row['sigla']} for row in json.loads(body)]
 tables['unidades_federativas']={'url':uf_url,'response_sha256':hashlib.sha256(body).hexdigest(),'records':records}
 cbkc_url='https://cbkc.org/racas/lista/por_grupo/page/1'
 body=read(cbkc_url);records=[]
 for tag,name in re.findall(r'<option([^>]*data-idcbkc[^>]*)>(.*?)</option>',body.decode(),re.S|re.I):
  records.append({'id':re.search(r'data-idcbkc="([^"]+)"',tag).group(1),'name':html.unescape(re.sub('<[^>]*>','',name)).strip()})
 if not records:raise ValueError('Diretório CBKC não foi reconhecido')
 tables['cbkc_racas']={'url':cbkc_url,'response_sha256':hashlib.sha256(body).hexdigest(),'records':records}
 payload={'classes':{qid:{'en':entity['labels']['en']['value'],'revision':entity['lastrevid']} for qid,entity in classes['entities'].items()},'tables':tables}
 canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
 snapshot={'schema_version':1,'observed_at':datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),
           'subject':'source-facts-not-editorial-approval','sha256':hashlib.sha256(canonical).hexdigest(),
           'wikidata_license':'CC0','wikidata_attribution':'Wikidata contributors','payload':payload}
 path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'saved':str(path.relative_to(ROOT)),'tables':len(tables),'records':sum(len(t['records']) for t in tables.values()),'sha256':snapshot['sha256']}),flush=True)


if __name__=='__main__':main()
