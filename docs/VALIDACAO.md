# Validação e limites

Cada release disponibiliza um arquivo `VALIDACAO_X.Y.Z.json` com a identidade
dos pacotes, o commit, o ambiente e o alcance das verificações. Esses arquivos
estão nos [downloads das releases](https://github.com/yurigarciapardinho/stopots-bot/releases).
Os logs da [CI](https://github.com/yurigarciapardinho/stopots-bot/actions)
registram a execução dos testes e dos checks associados a cada commit.

## Verificações automatizadas

A suíte possui 79 testes, executados em Linux e Windows. Ela cobre domínio,
identidade de contexto, política de ajuda, persistência, taxonomia, convites e
contratos de navegador com DOM local. A instalação do wheel compara os
arquivos com a fonte e exercita a interface e o driver Playwright em ambiente
separado. As verificações de segurança abrangem workflows, segredos e
dependências de execução e construção.

Os pacotes desktop também passam por verificações de recursos e interface.
O relatório de cada versão informa quais formatos e ambientes foram
efetivamente exercitados. A aprovação dos testes locais não comprova uma
partida no serviço real.

## Ensaio funcional no jogo

A evidência online da 2.0.0 concluiu uma partida privada de quatro rodadas com
dois participantes controlados, pool de 16 temas e letras A–D. O resultado
final foi 240 × 240, com soma das rodadas conciliada, pausa no final, Chrome
preservado ao fechar a janela e reabertura pausada na mesma sessão.

O [relatório da 2.0.0](https://github.com/yurigarciapardinho/stopots-bot/releases/download/v2.0.0/VALIDACAO_2.0.0.json)
identifica o wheel usado nessa partida. O wheel publicado recebeu uma alteração
posterior restrita ao autodiagnóstico gráfico; os demais arquivos e as versões
das dependências foram comparados. A partida não foi repetida após essa
alteração.

A 2.0.1 revisa documentação e ferramentas de construção. O código de execução
preserva o comportamento da 2.0.0, com atualização do identificador de versão.
Seu relatório registra a comparação, a instalação e os testes dos novos
pacotes. A evidência funcional no jogo continua sendo o ensaio identificado
acima, sem uma nova partida atribuída à revisão documental.

## Plataformas

| Ambiente | Alcance |
| --- | --- |
| Ubuntu 24.04 amd64 | Plataforma principal de distribuição Linux |
| Ubuntu 26.04 amd64 | Instalação e interface em ambiente isolado |
| Pop!_OS 24.04 / COSMIC / Wayland | Interface no desktop nativo e sessão Chrome dedicada |
| Windows Server 2022, x64 | Build, testes e GUI do wheel; suporte Windows permanece experimental |
| macOS | Sem pacote ou validação nativa anunciados |

Renderização em offscreen ou Xvfb não abrange todos os compositores e GPUs.
O alcance específico de cada pacote Linux está no relatório da sua release.
No Windows, os testes citados não constituem uma partida nativa nem uma
verificação interativa completa do executável portátil.

## Limites conhecidos

- Os ensaios não cobrem todas as modalidades, categorias ou letras possíveis.
- Host, Maioria, Desativado e recuperação geral de rede não têm validação online abrangente.
- O segmento público observado em testes anteriores não equivale a uma partida pública desde a primeira rodada.
- As amostras de STOP não estabelecem um tempo mínimo universal do servidor; o aplicativo consulta a habilitação real do controle.
- A aprovação editorial de uma palavra não garante consenso entre os jogadores nem cobertura de todos os campos.
- A sala pode expirar ou expulsar por inatividade, mesmo com o Chrome aberto.

Consulte [vocabulário](VOCABULARIO.md) para as métricas de cobertura e
[laboratório](LABORATORIO.md) para os cenários de reprodução.
