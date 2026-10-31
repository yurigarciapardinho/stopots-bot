# Validação e limites

O registro de preparação offline é [RESULTADO.json](../evidence/releases/2.0.0/RESULTADO.json).
A comprovação final do wheel distribuído fica em `VALIDACAO_2.0.0.json`, nos
[assets da release](https://github.com/yurigarciapardinho/stopots-bot/releases/tag/v2.0.0),
vinculada ao SHA e ao hash do pacote testado. Consulte também os runs de Actions associados ao commit publicado. Um teste
local não é um teste online; uma entrada em sala não é partida completa.

Histórico de 30/10/2026: 69 testes passaram no computador e em Ubuntu 24.04
isolado. A GUI a partir do fonte interno 2.1.0 concluiu uma partida privada de
quatro rodadas, 240 × 240, pausou no final e reabriu o mesmo Chrome pausado.
Entrada sem senha em sala pública controlada confirmou apelido e dois
participantes, sem certificar partida integral. A certificação histórica Padrão
de três partidas pertence ao run interno b03849d5f071 e ao seu commit, não é uma
nova certificação produzida pela renumeração pública.

A 2.0.0 possui evidências próprias, identificando pacote, formato instalado,
ambiente, assertions, limpeza e limitações. Números de versão antigos não foram
editados para produzir essa comprovação.

Ubuntu 24.04 é a plataforma principal. Ubuntu 26.04 em container/Xvfb cobre
instalação e renderização, não todos os compositores. Pop!_OS/COSMIC é a referência
física. Windows é experimental até o alcance de teste nativo registrado;
macOS permanece posterior. Host, Maioria, Desativado, recuperação geral de rede,
partida pública desde o início e tempo mínimo universal de STOP não têm nova
certificação nesta entrega. Aprovação editorial lexical não garante consenso
dos jogadores nem preenchimento de todos os campos em todas as letras.
