# Fontes e curadoria do vocabulário

A fonte editorial separa lexemas de associações semânticas. Uma associação
registra categoria, estado, fontes e decisão de revisão. O arquivo distribuído
contém somente associações aprovadas, com manifesto, contagens e hashes.

## Fontes

| Fonte | Aquisição e uso |
| --- | --- |
| Dicionário de Lucas8x/stopots-bot | Commit 92eda1341cb391da77bad21bbe6a82417928a3c6; 2.688 entradas importadas de `stopots_bot/dictionary.json` como pendentes |
| Curadoria própria | Seleção e revisão editorial pt-BR, incluindo categorias, siglas e exemplos; organização e curadoria sob MIT |
| `publico-revisado-v1.json` | 122 associações revisadas, com 56 referências datadas |
| Wikidata | Fatos estruturados selecionados sob CC0, com revisões imutáveis e snapshots verificáveis |
| IBGE Localidades | 5.571 pares código/nome de municípios obtidos em 29/10/2026; nomes de UFs em revisão posterior |
| CBKC | Nomes factuais de raças, com referência e data; padrões textuais não reproduzidos |

O índice contém **7.986 associações aprovadas**, **7.762 lexemas** e
**2.050 associações pendentes**. Associações não equivalem a palavras distintas.
As categorias, siglas e lacunas estão no [guia do vocabulário](../docs/VOCABULARIO.md).

## Procedência e revisão

Os arquivos em `source/` registram fontes, datas, revisões e decisões. Um
snapshot pode conter dados não aprovados: somente decisões explícitas entram
no índice. A curadoria não importa automaticamente respostas de jogadores ou
associações de uma base externa.

A revisão factual usa nomes e associações conferidos, sem reproduzir
definições, letras musicais ou textos comerciais. As definições de siglas
adotadas pelo catálogo são editoriais; seus registros de origem permanecem
preservados e não são atribuídos à ajuda oficial do jogo.

Para IBGE, a regra `ibge-city-v1` verifica esquema, códigos únicos, integridade
e correspondência dos pares id/nome. Ela aprova somente Cidade. CEP aceita
Cidade pela relação explícita da taxonomia. Homônimos mantêm suas identidades
de origem; candidatos com a mesma palavra não ganham peso adicional.

O identificador nominal de licença não é fornecido pela resposta da API do
IBGE e está registrado dessa forma nos metadados. A atribuição acompanha os
fatos geográficos. A organização e a curadoria própria mantêm MIT; o código
do aplicativo segue o [mapa de procedência](../docs/PROCEDENCIA.md).

## Editar e publicar

`tools/build_vocabulary.py` compila a curadoria existente. O parâmetro `--recriar`
substitui a fonte editorial pela migração reproduzível e deve ser usado somente
quando essa substituição for intencional. Alterações normais usam os comandos
`vocabulario editar` e `vocabulario publicar` da CLI.

`tools/review_vocabulary.py` aplica revisões em lote sobre uma cópia validada.
Reaplicar uma revisão idêntica é idempotente. Um identificador com conteúdo
divergente, checksum alterado, idioma incompatível ou snapshot inconsistente
interrompe a operação antes da escrita. Decisões anteriores e grafias revisadas
são preservadas; pendências ficam fora do arquivo distribuído.

As revisões `catalogo-revisado-v1.json` e `catalogo-reforco-r-v1.json` registram
as decisões do catálogo. `catalogo-fatos-2026-10-30.json` conserva os registros
de origem; as sementes em `review/` são propostas, sem aprovação automática.
Nomes longos permanecem na fonte: o limite da interface é aplicado na consulta,
sem truncamento silencioso.

## Referências

- [API de Localidades do IBGE](https://servicodados.ibge.gov.br/api/docs/localidades).
- [Municípios, ordenados por nome](https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome).
- [Dados abertos do IBGE](https://www.ibge.gov.br/acesso-informacao/dados-abertos.html).
- [Licenciamento do Wikidata](https://www.wikidata.org/wiki/Wikidata:Licensing).
