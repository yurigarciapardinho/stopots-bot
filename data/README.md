# Fontes do vocabulário

O JSON editorial separa lexemas de associações semânticas. Cada associação contém estado, fontes e nota de revisão quando aprovada. O arquivo distribuído inclui somente associações aprovadas e um manifesto com hashes e contagens.

| Fonte | Aquisição e uso |
| --- | --- |
| Legado Lucas8x/stopots-bot | Commit 92eda1341cb391da77bad21bbe6a82417928a3c6, arquivo preservado em stopots_bot/dictionary.json; 2.688 entradas importadas como pendentes |
| Bootstrap local | 293 associações revisadas para o perfil pt-BR, incluindo os 16 temas / letras A–D; MIT |
| IBGE Localidades | 5.571 pares código/nome obtidos em 29/10/2026; atribuição IBGE, snapshot, data, resposta SHA-256 e regra ibge-city-v1 registrados |

Fonte oficial: https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome  
Documentação: https://servicodados.ibge.gov.br/api/docs/localidades  
Política de dados abertos: https://www.ibge.gov.br/acesso-informacao/dados-abertos.html

O identificador nominal de licença não é fornecido pela resposta da API e está registrado assim nos metadados. A atribuição da fonte acompanha os fatos geográficos. A licença MIT do projeto abrange o código e sua curadoria própria.

A importação IBGE começa pendente. A regra `ibge-city-v1` confere esquema, códigos únicos, integridade do snapshot e correspondência exata dos pares id/nome; aprova somente Cidade. CEP aceita Cidade pela relação explícita da taxonomia. Nenhuma outra categoria é aprovada por essa regra. O código de origem diferencia municípios homônimos, enquanto a seleção elimina repetição da palavra digitada.

A release atual contém 5.864 associações aprovadas, 5.857 entidades lexicais e 2.562 associações pendentes. Essas contagens não equivalem a palavras distintas nem a cobertura completa do jogo. Limites da UI são filtrados por consulta; nomes longos são preservados na fonte e não são truncados para caber no formulário.

Para compilar a curadoria existente, executar `tools/build_vocabulary.py`. O parâmetro `--recriar` é uma operação explícita que substitui a fonte editorial pela migração reproduzível. Para alterações normais, usar os comandos `vocabulario editar` e `vocabulario publicar`, preservando a versão anterior.
