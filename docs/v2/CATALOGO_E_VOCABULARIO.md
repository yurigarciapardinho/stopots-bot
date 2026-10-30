# Catálogo público e vocabulário — versão 2.0.3

Cinco coletas úteis pelo JOGAR reuniram **31 temas visíveis**. Foram seis entradas: uma caiu direto no final, sem categorias, e foi substituída. A coleta leu os rótulos e fechou cada contexto, sem preencher, votar ou pedir STOP. O tempo somado das entradas foi de 80.2 s; não são cinco partidas completas.

A nova release contém **7.986 associações aprovadas / 7.762 lexemas**, com 2.050 associações pendentes. São **2.000 associações aprovadas a mais** que a 2.0.2. Todos os **80 temas cadastrados** têm candidatos utilizáveis em pelo menos oito iniciais. As lacunas restantes estão na matriz abaixo.

| Medição offline | Antes, 2.0.2 | Depois, 2.0.3 |
| --- | ---: | ---: |
| Pares tema/letra das cinco coletas | 16/38 | 38/38 |
| Campos do recorte público histórico | 64/72 | 72/72 |
| Células dos 80 temas × 26 letras | 441/2.080 | 1.692/2.080 |

A matriz geral tem **81,35% das células com candidato**. O denominador antes/depois inclui os mesmos 80 temas; os sete novos estavam vazios no baseline. Os 38/38 e 72/72 medem consulta ao vocabulário, sem pontuação, preenchimento online ou garantia de aceitação por jogadores. O resultado público histórico continua preservando seus 5/72 reais na 2.0.1.

## Siglas e taxonomia

Os significados abaixo foram fornecidos pelo usuário nesta sessão; a fonte editorial registra essa procedência. Não são apresentados como definições extraídas da ajuda oficial.

| Sigla | Significado | Tratamento |
| --- | --- | --- |
| PDA | Personagem de Desenho Animado | Categoria de personagens; independente do tema Desenho Animado |
| PCH | Partes do Corpo Humano | Respostas anatômicas; aliases para singular/plural |
| JLR | Jornal, Livro ou Revista | União explícita de Jornal, Livro e Revista |
| FLV | Fruta, Legume ou Verdura | Composição já existente, com aliases completos |
| CEP | Cidade, Estado ou País | Composição já existente, com aliases completos |
| MSÉ | Minha Sogra É | Associações próprias, com concordância feminina |
| MST | Minha Sogra Tem | Associações próprias de posse |
| MSU | Minha Sogra Usa | Associações próprias de uso |
| PÁF / PAF | Planta, Árvore ou Flor | União explícita das três categorias |

MST e MSU não foram transformadas em aliases de Objeto. PDA não é alias de Desenho Animado. A relação de personagem fictício inclui PDA e Super-Herói de forma direcional. JLR não incorpora automaticamente programas jornalísticos da TV.

## Catálogo observado

ADJETIVO, ATOR, BRINQUEDO, CANTOR, CARRO, CIDADE, COMIDA, ELETRO ELETRÔNICO, ESPORTE, ESPORTISTA, FILME, FRUTA, GENTÍLICO, IDIOMA, INSETO, MEIO DE TRANSPORTE, MÚSICA, NOME FEMININO, NOME MASCULINO, PALAVRA EM INGLÊS, PCH, PDA, PROFISSÃO, PÁF, REMÉDIO, SABOR DE PIZZA, SABOR DE SORVETE, SUPER-HERÓI, SÉRIE, VESTUÁRIO, ÁRVORE.

As evidências brutas são `evidence/v2/catalogo-publico-9fc3352d2f43.json` e `catalogo-publico-467c40ed0cdc.json`. A rota pública `/pt/game` não revela identidade de servidor; os registros demonstram entradas e temas observados, sem provar seis servidores distintos. Os dois navegadores e todos os contextos próprios foram fechados.

## Curadoria, fontes e validação

A revisão principal contém 2.116 pares explicitamente aprovados; pares já aprovados são preservados. Um reforço posterior acrescentou Ratatouille, Rola-bosta e Resedá com referências diretas, fechando três lacunas R da coleta. O saldo líquido é de 2.000 novas aprovações, incluindo 481 promoções do legado pendente. A fonte editorial conserva as decisões anteriores e as demais 2.050 pendências fora da distribuição.

A seleção combina curadoria editorial local do assistente, registros Wikidata com predicados conferidos, UFs do IBGE e nomes de raças do diretório oficial CBKC. O snapshot retém 2.265 linhas Wikidata, 27 UFs e 248 raças; sua presença não equivale a aprovação. Foram excluídas associações ocasionais de tipagem externa e casos como sintoma tratado como doença, canal de notícias tratado como jornal, aranha como inseto e quibe como sobremesa. Distrito Federal não foi aprovado como Estado.

Os fatos estruturados Wikidata têm atribuição e licença CC0. Os nomes/códigos oficiais mantêm referência, data e checksum; padrões textuais da CBKC e definições dos dicionários não foram copiados. A curadoria local é identificada como tal e não se apresenta como validação do servidor. Fontes e decisões: `data/source/catalogo-revisado-v1.json`, `catalogo-reforco-r-v1.json` e `catalogo-fatos-2026-10-30.json`.

58 testes passaram em 15,10 s, incluindo contratos em Chrome, fontes alteradas, aliases conflitantes, idioma, preservação de decisões/grafia e uma aceitação mínima de diversidade para todos os temas. O processamento em lote preserva o contrato do editor e valida uma cópia antes da publicação. A antiga asserção de que Vilão/Z era vazio foi substituída por um tema desconhecido: Zurg agora é candidato aprovado.

Os quatro candidatos editoriais acima de 20 unidades UTF-16 foram mantidos fora dessa revisão: Helicóptero de brinquedo, Xilofone de brinquedo, Bicicleta ergométrica e Orgulho e Preconceito. Não houve truncamento nem remoção de palavras longas já preservadas no baseline.

Esta versão tem testes locais, medição offline e instalação independente. As partidas privadas da 2.0.0 e 2.0.2 conservam suas versões, hashes e escopos; as coletas desta tarefa não recertificam o pacote jogando publicamente. Host, Desativado, Maioria e recuperação de rede seguem sem certificação online.

## Cobertura por tema

Contagens após composição/aliases, com limite de 20 unidades UTF-16. A tabela explicita iniciais sem candidato, sem inventar palavras para fechar o alfabeto.

| Tema | Candidatos utilizáveis | Iniciais cobertas | Iniciais sem candidato |
| --- | ---: | ---: | --- |
| adjetivo | 24 | 23/26 | K, W, Y |
| animal | 105 | 26/26 | — |
| Animal Aquático | 21 | 20/26 | I, K, Q, W, Y, Z |
| app ou site | 28 | 25/26 | H |
| ator | 25 | 25/26 | Y |
| ave | 21 | 21/26 | O, V, W, Y, Z |
| banda | 62 | 26/26 | — |
| brinquedo | 25 | 17/26 | H, K, N, O, S, W, X, Y, Z |
| cantor | 27 | 26/26 | — |
| capital | 24 | 22/26 | F, G, X, Y |
| carro | 27 | 26/26 | — |
| celebridade | 26 | 26/26 | — |
| cep | 5069 | 25/26 | Y |
| cidade | 4894 | 25/26 | Y |
| comida | 30 | 22/26 | K, W, X, Z |
| comida saudável | 33 | 18/26 | D, H, O, S, W, X, Y, Z |
| cor | 32 | 17/26 | H, J, K, Q, U, W, X, Y, Z |
| desenho animado | 28 | 25/26 | E |
| doce | 22 | 16/26 | I, L, N, O, U, V, W, X, Y, Z |
| doença | 29 | 20/26 | J, K, N, W, X, Y |
| eletro eletrônico | 23 | 23/26 | Q, Y, Z |
| esporte | 25 | 23/26 | U, Y, Z |
| esportista | 26 | 26/26 | — |
| Estado | 76 | 21/26 | J, Q, X, Y, Z |
| fantasia | 25 | 24/26 | K, Q |
| filme | 44 | 19/26 | F, N, V, W, X, Y, Z |
| flor | 25 | 19/26 | K, Q, S, U, W, X, Y |
| flv | 71 | 20/26 | H, O, W, X, Y, Z |
| fruta | 34 | 17/26 | E, H, O, Q, V, W, X, Y, Z |
| game | 48 | 19/26 | E, J, N, Q, U, X, Z |
| gentílico | 23 | 23/26 | W, X, Y |
| idioma | 67 | 25/26 | Y |
| ingrediente | 28 | 20/26 | D, K, W, X, Y, Z |
| inseto | 27 | 17/26 | H, K, N, O, S, U, W, X, Y |
| instrumento musical | 29 | 21/26 | J, K, N, W, Y |
| jlr | 72 | 24/26 | X, Y |
| Jornal | 20 | 11/26 | A, B, G, I, J, K, P, Q, R, S, U, W, X, Y, Z |
| Legume | 21 | 13/26 | D, F, G, H, K, L, O, S, U, W, X, Y, Z |
| Livro | 24 | 23/26 | O, X, Y |
| líquido | 26 | 15/26 | B, F, H, I, J, K, N, W, X, Y, Z |
| mamífero | 36 | 22/26 | K, S, X, Y |
| marca | 26 | 26/26 | — |
| meio de transporte | 26 | 23/26 | W, X, Y |
| MST | 23 | 23/26 | K, W, Y |
| MSU | 23 | 23/26 | K, W, Y |
| msé | 23 | 23/26 | K, W, Y |
| música | 66 | 21/26 | Q, U, V, X, Z |
| Nome | 89 | 26/26 | — |
| nome feminino | 45 | 26/26 | — |
| nome masculino | 44 | 26/26 | — |
| objeto | 39 | 23/26 | K, W, Y |
| palavra em espanhol | 27 | 23/26 | W, X, Y |
| palavra em inglês | 52 | 26/26 | — |
| país | 122 | 22/26 | K, W, X, Y |
| pch | 54 | 22/26 | K, W, X, Y |
| pda | 34 | 25/26 | X |
| personagem fictício | 64 | 25/26 | X |
| Planta | 28 | 18/26 | I, K, N, P, Q, W, X, Y |
| presente | 27 | 22/26 | K, W, Y, Z |
| profissão | 40 | 22/26 | K, W, X, Y |
| programa de tv | 23 | 17/26 | I, K, L, O, Q, U, W, Y, Z |
| PÁF | 76 | 22/26 | K, W, X, Y |
| raça de cachorro | 55 | 21/26 | E, I, Q, U, Z |
| remédio | 28 | 20/26 | J, K, U, W, X, Y |
| Revista | 28 | 17/26 | A, J, M, O, Q, W, X, Y, Z |
| sabor de pizza | 27 | 14/26 | E, H, I, J, K, O, U, V, W, X, Y, Z |
| sabor de sorvete | 36 | 14/26 | E, G, H, J, K, Q, R, V, W, X, Y, Z |
| sobremesa | 23 | 13/26 | H, I, J, K, L, N, O, U, V, W, X, Y, Z |
| sobrenome | 64 | 23/26 | Q, U, X |
| super-herói | 19 | 19/26 | E, K, O, Q, X, Y, Z |
| série | 25 | 22/26 | K, Q, U, Y |
| Tem na academia | 21 | 14/26 | F, G, J, K, N, O, Q, U, W, X, Y, Z |
| Tem na Praia | 30 | 18/26 | H, K, N, U, W, X, Y, Z |
| Tem no Hospital | 27 | 19/26 | H, K, N, W, X, Y, Z |
| time esportivo | 26 | 24/26 | O, X |
| verbo | 24 | 23/26 | K, W, Y |
| Verdura | 16 | 8/26 | D, F, G, H, I, J, K, L, N, O, P, Q, U, V, W, X, Y, Z |
| vestuário | 27 | 21/26 | O, W, X, Y, Z |
| vilão | 25 | 22/26 | Q, W, X, Y |
| Árvore | 26 | 20/26 | H, K, W, X, Y, Z |

A matriz completa e a comparação por célula estão em `evidence/v2/CATALOGO_COBERTURA.json`.

```bash
./scripts/lab.sh testar
./scripts/v2.sh vocabulario cobertura --letras ABCDEFGHIJKLMNOPQRSTUVWXYZ --temas PDA PCH JLR PÁF MSÉ MST MSU
```

## Pacote instalado

Wheel `stopots_bot-2.0.3-py3-none-any.whl`, SHA-256 `6e6c5d80c4c963aaeb13c81d5033844c1df165e00aa91509acb19f9cd3c20ad5`. Os 14 arquivos de runtime do wheel e da instalação em ambiente separado coincidem com a fonte. A CLI de cobertura resolveu as siglas e retornou código 0. Nenhum processo dos perfis headless do laboratório permaneceu ativo. Evidência: `evidence/v2/PACOTE_CATALOGO_INSTALADO.json`.
