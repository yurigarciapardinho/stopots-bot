# Validação direcionada — StopotS Bot 2.0.2

A versão reúne curadoria factual, tratamento de recusa de STOP e identificação explícita do pódio. A execução final `bfa590fc26f8` concluiu quatro rodadas privadas no pacote instalado: **155 × 155**, CLI com código 0, duas telas finais e soma das rodadas conciliada. O alcance desta entrega é direcionado; a partida pública integral ainda está pendente.

## Vocabulário e alcance

A revisão `publico-revisado-2026-10-29-v1` contém 122 associações explicitamente revisadas, com 56 referências datadas. Inclui 12 entidades Wikidata selecionadas, com revisões imutáveis e snapshot verificável. A release tem 5.986 associações aprovadas, 5.973 lexemas e 2.531 associações pendentes. Foram acrescentadas Tem na Praia, Tem no Hospital, Árvore e Animal Aquático; a inclusão em Animal é direcional.

| Medição offline | Antes | Depois |
| --- | ---: | ---: |
| Campos do segmento público histórico com candidato aprovado | 5/72 | 64/72 |
| Células de 73 rótulos registrados × 26 letras com candidato | 356/1.898 | 441/1.898 |

Os 64/72 equivalem a 88,89% apenas no recorte já observado. A matriz mais ampla tem 23,23% das células com candidato; o ensaio não mede todos os temas personalizados possíveis. PDA, PCH e JLR continuam sem significado confirmado; Fantasia com G também ficou sem candidato no replay. O perfil privado A–D conserva exatamente seus candidatos anteriores. Aprovação editorial não garante consenso dos jogadores.

`evidence/v2/CURADORIA_COBERTURA.json` registra o replay offline. O resultado histórico `PUBLICA_RESULTADO.json` mantém seus 5/72: não houve nova partida pública nesta revisão. `data/source/publico-revisado-v1.json` registra as decisões e fontes; o compilador distribui somente as aprovadas. Não foram importadas respostas de jogadores nem sugestões em massa. A ferramenta de revisão exige checksum da fonte, protege decisões e grafias existentes e rejeita reaplicação divergente.

## Contratos e ambiente

54 testes passaram em 13,16 s, incluindo contratos no Chrome e a troca de seletor de STOP, AVALIAR e ESTOU PRONTO depois de uma tentativa bloqueada ou indeterminada. O wheel foi instalado em ambiente separado. Os 14 arquivos de runtime do pacote foram conferidos contra a fonte usada na construção, sem divergências. Os mesmos 14 arquivos do pacote instalado também coincidem com a fonte.

Uma recusa conhecida de STOP é `BLOQUEADA` e registra que houve tentativa. O adaptador reconhece e fecha apenas o aviso de categorias incompletas surgido após sua própria ação, na mesma rodada. Avisos anteriores, desconhecidos ou ambíguos suspendem ações e são preservados. A tentativa não se repete quando o seletor muda; o controle corrente continua sendo revalidado antes de agir. A extração do final identifica `scope=podium`, sem declarar ranking completo.

Ambiente: Linux Pop!_OS, Python 3.12.3, Playwright 1.64.1 e Google Chrome 151.0.7922.137. O teste usa dois clientes anônimos próprios e a interface web real, sem conta pessoal. Configuração: sala privada, Padrão, Rápido, quatro rodadas e letras FIMO, pool de 16 temas com 12 campos sorteados por rodada. Na letra I, a CLI fica pausada durante uma resposta e uma tentativa parcial do adaptador; depois retoma como único escritor do host. O convidado tem controlador separado.

## Tentativas preservadas

| Execução | Resultado e correção |
| --- | --- |
| d80c35a2aedf | Configuração com uma letra e quatro rodadas não iniciou; prazo encerrado e recursos fechados |
| ab6bbbfaf2f0 | Aviso real confirmou que letras devem ser pelo menos iguais às rodadas; UI oferece mínimo de quatro rodadas neste perfil |
| 28767b56ad98 | Quatro rodadas e final 150 × 150; monitor interrompeu a CLI antes da saída natural, código -2; espera de encerramento corrigida |
| f77887875872 | Final 150 × 150 e CLI 0; eventos revelaram duas solicitações de STOP por mudança de seletor; deduplicação corrigida e teste de regressão acrescentado |

Essas tentativas têm relatórios próprios e não são contabilizadas como novas certificações da release final. A certificação anterior de três partidas permanece vinculada à 2.0.0 e ao perfil A–D. Host, Desativado, Maioria, recuperação de rede e partida pública integral sem intervenção continuam pendentes.

## Resultado do wheel final

Na ordem O, M, I, F, os dois clientes chegaram a FIM DE JOGO! com 155 pontos cada. A CLI retornou `concluido`, `final_result_verified=true` e código 0; a soma dos quatro rankings de rodada do mesmo observador conferiu com o final. Todos os recursos próprios foram fechados; nenhum processo com os perfis headless do laboratório permaneceu ativo e o arquivo de controle da execução foi removido.

Na rodada I, a resposta inicial do adaptador foi confirmada e a tentativa com 1/12 campos preenchidos retornou `BLOQUEADA`, `attempted=true`. O aviso foi fechado e nova tentativa pelo mesmo planejador ficou suspensa. Ao retomar, a CLI preencheu os outros 11 campos e solicitou STOP uma única vez, com 12/12 preenchidos. A confirmação imediata dessa solicitação foi `INDETERMINADA`; não houve repetição. Depois foram observadas as 12 etapas de apuração e o placar de rodada 60 × 60. A transição posterior comprova o avanço do fluxo, sem converter a confirmação imediata em `APLICADA`.

O STOP estava desabilitado na amostra de 20,658 s e habilitado em 20,851 s, desde a primeira observação da escrita de I. A apuração apareceu em 29,012 s nessa mesma âncora. São amostras do modo Rápido, com criação e observação assíncronas; não estabelecem mínimo universal do servidor. O programa continua consultando a habilitação real do botão e o preenchimento exigido.

- Wheel instalado: `stopots_bot-2.0.2-py3-none-any.whl`.
- SHA-256 do wheel: `d572802d7167ef956005f3fa2798659a33b21c6302069798038c6f7ad8a5ba33`.
- Release de vocabulário: `b690d5ae4225c48dbed21351e94e83040d8d7638abba62afaae17159db3368d0`.
- Fonte editorial: `f0a9f52a39104c29618d13299c41acfe1b7a8efff8cb3d2cf6d2155b795d7288`.
- Evidência consolidada: `evidence/v2/CURADORIA_RESULTADO.json`.
- Relatório bruto: `evidence/v2/curadoria-bfa590fc26f8.json`.
- Eventos sanitizados: `evidence/v2/curadoria-bfa590fc26f8-cli.jsonl`.

Para reproduzir somente esse cenário real, executar explicitamente `../.runtime/venv-release/bin/python tools/probe_curated_round.py`. O helper cria outra sala privada com dois clientes próprios, usa o wheel instalado e fecha seus recursos ao concluir. O processo leva aproximadamente cinco minutos no ambiente medido. Ele não depende de manter uma sala aberta entre sessões.
