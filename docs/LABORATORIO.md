# Laboratório de preparação do StopotS v2

Raiz: /home/yuzlkk/hack/stopots. Desenvolvimento no worktree stopots-v2, branch codex/v2-desenvolvimento. A implementação v2 está em src/stopots_v2, com entrada por scripts/v2.sh; este documento descreve o laboratório auxiliar. Ler ../planejamento-v2/RETOMADA_V2.md para resultados e pendências atuais.

## Início rápido

    cd /home/yuzlkk/hack/stopots/stopots-v2
    ./scripts/lab.sh doctor
    ./scripts/lab.sh testar

O preparo reproduzível é ./scripts/preparar-lab.sh. Reutiliza ambiente/cache e sincroniza requirements-lab.lock. Python 3.12.3, Playwright 1.64.1 e Chrome 151.0.7922.137 foram instalados/verificados.

## Comandos

| Comando | Efeito |
| --- | --- |
| ./scripts/lab.sh iniciar | Inicia serviço local e Chrome de teste; reutiliza serviço saudável |
| ./scripts/lab.sh sala | Inicia se necessário e cria sala privada nova com dois participantes |
| ./scripts/lab.sh observar --player host | Captura observação sanitizada do anfitrião |
| ./scripts/lab.sh teste-chrome | Inicia ensaio assíncrono de uma rodada e medição do STOP; retorna ID, sem declarar sucesso |
| ./scripts/lab.sh resultado | Mostra resultado/progresso compacto |
| ./scripts/lab.sh replay | Reclassifica snapshots locais sem partida |
| ./scripts/lab.sh testar | Executa testes locais sem conexão ao jogo |
| ./scripts/lab.sh limpar | Fecha contextos da sala de teste |
| ./scripts/lab.sh encerrar | Fecha serviço e navegadores próprios |

Não presumir que a sala sobreviva à inatividade. Durante desenvolvimento, usar replay e testar. Para UI real, criar outra sala com sala ou teste-chrome. A senha é gerada em memória; não exige conta pessoal. O convidado pode aparecer com nome anônimo do site; o laboratório identifica o contexto, sem depender da persistência de um nome após navegação.

## Implementação e evidências

Anfitrião: Chrome visível com perfil dedicado. Convidado: outra instância Chrome headless. A observação registra visibilidade/foco para investigar diferenças de temporização. Nenhum perfil pessoal é usado. Controle HTTP somente em loopback, com segredo em ../.runtime/lab-control.json; não compartilhar esse arquivo.

A entrada privada exige convite, ENTRAR e formulário de senha. O botão da senha fica restrito ao formulário, pois outro ENTRAR pode coexistir ao fundo. O popup de compartilhamento é fechado pelo controle publicado antes de iniciar. Opacidade de animação não reduz artificialmente a enumeração dos campos.

Snapshots: tests/lab/fixtures. Relatórios: evidence/lab/spike-*.json. O mais recente não é necessariamente aprovado: conferir status, assertions e limitações. Snapshots de transição podem estar parciais e servem para regressão. Não certificam quantidade fixa de campos.

O ensaio compara fill e digitação, verifica valores depois da atualização da UI, deixa inicialmente o convidado sem respostas e amostra STOP. Relógio relativo à observação, não ao servidor. Medição inconsistente não vira tempo mínimo oficial. O pedido continua condicionado ao botão disponível.

Textos sintéticos testam controles; não aprovam vocabulário. Uma rodada do laboratório não certifica partida completa nem substitui M2–M6. A pendência está no checkpoint.

## Recuperação

Se o Chrome de teste fechar, consultar doctor e executar encerrar antes de iniciar. Não usar pkill global. Se o processo próprio não responder, conferir PID/caminho em .runtime antes de encerrar. Runtime é descartável após fechar o serviço; código, lock e fixtures permanecem no worktree.
