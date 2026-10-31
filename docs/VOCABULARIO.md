# Vocabulário

O vocabulário pt-BR é mantido por curadoria e distribuído com o aplicativo.
Somente associações aprovadas podem ser selecionadas para preenchimento.
Uma palavra ausente pode ser válida; sua ausência não autoriza rejeição
automática na apuração.

## Composição e cobertura

| Medida | Valor |
| --- | ---: |
| Temas cadastrados | 80 |
| Associações aprovadas | 7.986 |
| Lexemas | 7.762 |
| Associações pendentes, fora do índice distribuído | 2.050 |
| Células tema/inicial com candidato | 1.692 de 2.080 (81,35%) |

A cobertura considera os 80 temas e as 26 letras A–Z, com limite de 20
unidades UTF-16. Todos os temas possuem candidatos em pelo menos oito
iniciais. Essa medição é uma consulta ao índice: não representa pontuação,
preenchimento online ou aceitação garantida por outros jogadores.

Um lexema pode ter associações com várias categorias. Por isso, as contagens
de associações, lexemas e palavras distintas têm significados diferentes.
O manifesto em `src/stopots_v2/resources/vocabulary.json` identifica o conteúdo
distribuído e a fonte editorial.

## Siglas

As definições abaixo são as adotadas pela curadoria do projeto. Não são
apresentadas como classificações extraídas da ajuda oficial do StopotS.

| Sigla | Significado |
| --- | --- |
| PDA | Personagem de Desenho Animado |
| PCH | Partes do Corpo Humano |
| JLR | Jornal, Livro ou Revista |
| FLV | Fruta, Legume ou Verdura |
| CEP | Cidade, Estado ou País |
| MSÉ | Minha Sogra É |
| MST | Minha Sogra Tem |
| MSU | Minha Sogra Usa |
| PÁF / PAF | Planta, Árvore ou Flor |

JLR, FLV, CEP e PÁF compõem categorias por inclusão explícita. PDA é separado
de Desenho Animado; MST e MSU têm associações próprias, sem equivalência geral
com Objeto. As relações de inclusão são direcionais: uma ave pode atender a
Animal, enquanto um animal qualquer não atende necessariamente a Ave.

## Escrita e seleção

A grafia editorial preserva acentos e variantes. A busca e a confirmação
consideram a forma exibida pelo input do jogo. Nas observações registradas,
hífen virou espaço e apóstrofo foi removido; a grafia original permanece nos
dados. O limite do campo é aplicado na consulta, sem cortar uma resposta longa
para fazê-la caber.

As fontes combinam o legado de Lucas8x, curadoria própria e fatos selecionados
de IBGE, Wikidata e CBKC. [Fontes e revisão](../data/README.md) descrevem
procedência, estados e publicação. Os comandos para edição estão disponíveis
em `stopots-v2` vocabulario --help.

## Cobertura por tema

Contagens após aliases e composição, com o mesmo limite de 20 unidades UTF-16.
As iniciais vazias permanecem explícitas para permitir preenchimento manual
e orientar novas revisões.

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
