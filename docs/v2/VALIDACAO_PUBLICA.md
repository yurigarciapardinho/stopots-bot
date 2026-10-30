# Validação pública — StopotS Bot 2.0.1

Executada em 2026-10-29T21:43:42.351690-03:00. **O pacote instalado concluiu com código 0 e reconheceu FIM DE JOGO!; a captura independente confirmou o pódio.** A entrada ocorreu no ranking da rodada 2 de 8. Foram acompanhadas escrita, apuração e resultados das rodadas 3–8. Esta evidência valida esse segmento público; a certificação de uma partida pública desde a primeira rodada permanece pendente.

## Cenário e resultado

Entrada pública normal pelo botão JOGAR, um participante controlado e demais participantes públicos. Houve até dez linhas nos rankings observados, com entradas e saídas de jogadores. Chrome visível 151.0.7922.137, Playwright 1.64.1, pacote 2.0.1 instalado por wheel em ambiente separado. Código do produto: `3454838b4f3ba41cc0891d6a63f1f94bda119342`. Wheel SHA-256: `6b6c137c8ff6a1296c0a888fd5b66f6d1a03823cdd2012cb71663fd640ac286b`.

O pódio mostrou **490, 215 e 170 pontos**. As somas dos pontos de rodada dos mesmos aliases no log da CLI conferiram com cada total. Esses valores são do pódio; o placar final do participante controlado não foi reconciliado. O adaptador extraiu as três posições exibidas em `.end`, sem afirmar que representam todos os jogadores.

A CLI registrou **5 preenchimentos, 67 confirmações e 6 ações de continuar**. Foram 71 efeitos confirmados, 7 confirmações imediatas indeterminadas e nenhuma aplicação duplicada do mesmo ID. As indeterminações foram seis ações de continuar e uma confirmação de etapa; as fases e os resultados posteriores foram observados. Não se apresentam esses registros como falhas comprovadas do jogo nem como confirmações imediatas de efeito.

## Cobertura real do vocabulário

| Rodada | Letra | Campos | Com candidato aprovado | Não vazios ao fim da escrita |
| --- | --- | --- | --- | --- |
| 3 | F | 12 | 2 | 6 |
| 4 | M | 12 | 1 | 6 |
| 5 | I | 12 | 1 | 3 |
| 6 | O | 12 | 1 | 2 |
| 7 | G | 12 | 0 | 5 |
| 8 | P | 12 | 0 | 4 |

A release aprovada cobriu **5/72 campos (6.94%)** neste recorte. Os 26 campos não vazios não são 26 respostas do bot: a CLI registrou somente cinco preenchimentos, e surgiram valores não atribuíveis às suas ações. Essas edições foram preservadas. O ensaio não certifica execução pública sem intervenção.

As lacunas incluem letras fora do perfil privado A–D e temas como Banda, Instrumento Musical, Palavra em Espanhol e categorias abreviadas. Não se inferiu o significado de PDA, PCH ou JLR. Respostas de outros participantes e aceitação por votação não foram incorporadas como vocabulário aprovado. A base geográfica extensa não resolve a cobertura dos demais temas.

## STOP e pré-condições

A política padrão da CLI continuou exigindo todos os campos preenchidos; ela não pediu STOP nesta execução. Duas sondas separadas do adaptador, nas rodadas 5 e 6, tentaram STOP pela UI com apenas um campo preenchido. O botão estava habilitado, mas não houve encerramento confirmado por essas ações. A segunda tentativa capturou o aviso de que é necessário preencher corretamente todas as categorias; o aviso foi reconhecido e fechado pela UI.

Os intervalos de 28,119 s e 45,969 s são desde a primeira observação de escrita de cada sonda. A rejeição por preenchimento incompleto impede usá-los para medir um tempo mínimo de STOP. Esse mínimo continua não estabelecido. Não codificar esses intervalos como regra, nem tratar botão habilitado como garantia de aceitação.

## Correções e verificação

A versão 2.0.1 aceita a rota pública `/pt/game` e não confunde o campo de senha desabilitado do lobby com formulário de entrada. Salas públicas da listagem também podem usar caminho numérico: a forma da URL não determina sua visibilidade.

**47 testes locais passaram em 10,52 s**, incluindo as duas regressões do produto e a correção posterior do monitor. O monitor auxiliar original marcou falha quando a CLI terminou antes da sua janela de estabilidade. A saída JSON da CLI e a captura independente comprovam sucesso do produto. O monitor foi corrigido para consumir a conclusão explícita da CLI, preservar a distinção entre segmento observado e partida completa e fechar os recursos antes de encerrar Playwright. Essas mudanças do monitor foram verificadas localmente; a partida pública não foi repetida após elas. O prazo padrão futuro do ensaio público passou de 1.500 para 3.600 segundos.

A captura independente manteve brevemente o processo do monitor disponível perto do limite de tempo; não pausou o jogo nem o processo da CLI. A CLI concluiu dentro de seu prazo. O Chrome próprio foi encerrado: a identidade do processo, conferida por PID e instante de criação, não permaneceu ativa. O indicador de conexão em cache do monitor original não foi usado como prova de processo vivo. O Chrome pessoal e o acesso remoto foram preservados.

## Evidências e alcance

- `evidence/v2/PUBLICA_RESULTADO.json`: conclusão consolidada, assertions, cobertura e limites.
- `public-af6fb103c8a8-cli-result.json` e `public-af6fb103c8a8-cli-events.jsonl`: saída e eventos do comando distribuído.
- `public-af6fb103c8a8-final-guard.json`: DOM final sanitizado e captura independente do pódio; aliases têm escopo local a cada observador.
- `public-af6fb103c8a8-stop-probe*.json`: sondas de STOP, distintas das ações do planejador da CLI.
- `public-af6fb103c8a8.json`: resultado bruto do monitor, preservado com sua classificação incorreta para auditoria.

As tentativas anteriores interrompidas durante preparação e a conexão de leitura iniciada depois do fechamento do Chrome não entram na contagem de partidas validadas. A certificação privada anterior permanece vinculada aos seus commits e cenários. Esta execução não amplia suporte a Host, Maioria, Desativado ou recuperação de rede.

## Próximos critérios de aceite

Curar os temas e letras públicos com fonte verificável; resolver abreviações por evidência; reconhecer avisos de recusa como bloqueio explícito; representar pódio como resultado parcial; medir STOP com as demais pré-condições satisfeitas; e executar uma partida pública desde a rodada 1, com o pacote como único escritor. Até lá, a integração pública tem evidência de funcionamento, mas a autonomia geral permanece pendente.
