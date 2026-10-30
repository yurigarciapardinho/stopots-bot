# Fontes do vocabulário

O JSON editorial separa lexemas de associações semânticas. Cada associação contém estado, fontes e nota de revisão quando aprovada. O arquivo distribuído inclui somente associações aprovadas e um manifesto com hashes e contagens.

| Fonte | Aquisição e uso |
| --- | --- |
| Legado Lucas8x/stopots-bot | Commit 92eda1341cb391da77bad21bbe6a82417928a3c6, arquivo preservado em stopots_bot/dictionary.json; 2.688 entradas importadas como pendentes |
| Bootstrap local | 293 associações revisadas para o perfil pt-BR, incluindo os 16 temas / letras A–D; MIT |
| Revisão público-revisado-v1 | 122 associações, 56 referências datadas em `publico-revisado-v1.json`; fontes oficiais de entidades/produtos e dicionários para fatos lexicais |
| Wikidata selecionado | 12 entidades revisadas com rótulos, aliases e revisões imutáveis em `wikidata-fatos-2026-10-29.json`; fatos estruturados CC0 |
| IBGE Localidades | 5.571 pares código/nome obtidos em 29/10/2026; atribuição IBGE, snapshot, data, resposta SHA-256 e regra ibge-city-v1 registrados |

Fonte oficial: https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome  
Documentação: https://servicodados.ibge.gov.br/api/docs/localidades  
Política de dados abertos: https://www.ibge.gov.br/acesso-informacao/dados-abertos.html

O identificador nominal de licença não é fornecido pela resposta da API e está registrado assim nos metadados. A atribuição da fonte acompanha os fatos geográficos. A licença MIT do projeto abrange o código e sua curadoria própria.

A importação IBGE começa pendente. A regra `ibge-city-v1` confere esquema, códigos únicos, integridade do snapshot e correspondência exata dos pares id/nome; aprova somente Cidade. CEP aceita Cidade pela relação explícita da taxonomia. Nenhuma outra categoria é aprovada por essa regra. O código de origem diferencia municípios homônimos, enquanto a seleção elimina repetição da palavra digitada.

A release atual contém 5.986 associações aprovadas, 5.973 entidades lexicais e 2.531 associações pendentes. Essas contagens não equivalem a palavras distintas nem a cobertura completa do jogo. Limites da UI são filtrados por consulta; nomes longos são preservados na fonte e não são truncados para caber no formulário.

Para compilar a curadoria existente, executar `tools/build_vocabulary.py`. O parâmetro `--recriar` é uma operação explícita que substitui a fonte editorial pela migração reproduzível. Para alterações normais, usar os comandos `vocabulario editar` e `vocabulario publicar`, preservando a versão anterior.

A revisão factual acrescenta somente palavras e associações explicitamente conferidas. Não reproduz definições, letras musicais ou textos comerciais. As URLs, datas e notas por associação permitem revisar a decisão; a presença de uma fonte não aprova automaticamente outras categorias. As consultas Wikidata em massa não foram incorporadas. Fonte: https://www.wikidata.org/wiki/Wikidata:Licensing.

`tools/review_vocabulary.py data/source/publico-revisado-v1.json --publicar` é idempotente para a revisão exata já aplicada. Um ID reutilizado com conteúdo diferente, checksum divergente, idioma incompatível ou snapshot alterado interrompe a operação antes da escrita. As 2.531 pendências continuam fora da distribuição. PDA, PCH e JLR não receberam expansão especulativa.
