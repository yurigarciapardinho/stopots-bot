# StopotS Assistente 2.1

Aplicativo desktop em pt-BR, desenvolvido a partir das doze respostas e do requisito de convite registrados em UX_UI_DESKTOP.md. Ubuntu é a plataforma principal; Windows vem em seguida. A versão funcional anterior foi preservada antes da implementação.

## Abrir e jogar

No computador preparado, abra **StopotS Assistente.desktop** em `/home/yuzlkk/hack/stopots`. O ícone usa a distribuição portátil, sem abrir terminal. Como alternativa de desenvolvimento, execute `/home/yuzlkk/hack/stopots/stopots-desktop/scripts/desktop.sh`.

1. Escolha o perfil. **Só preencher** é o padrão: preenche vazios; STOP, votos, AVALIAR e avanço ficam com você.
2. Use **Escolher no jogo** para abrir o Chrome e escolher sua partida, ou **Entrar por convite** para colar o link.
3. No convite, confira o apelido e indique se a sala tem senha. Se tiver, informe a senha e clique **Entrar com ajuda**.
4. Depois da entrada, acompanhe letra, rodada, campos com resposta e pendências no painel compacto.
5. Expanda a janela para alterar perfil ou permissões. A indicação **Aplicando…** desaparece após confirmação do executor; ações já enviadas não são desfeitas.

O convite aceita `https://stopots.com/pt/08193`, preservando o zero. **Não** em uma sala protegida revela a necessidade de senha; senha recusada permite corrigir o formulário. O assistente não tenta adivinhar credenciais.

O valor da senha conserva caixa, números, símbolos e acentos. Não passa pela normalização de respostas do jogo. O campo é mascarado, com Mostrar/Ocultar; a senha é descartada pelo aplicativo após a tentativa e não entra nas preferências, eventos ou histórico. Limites impostos pelo jogo são informados sem truncamento silencioso.

## Controlar a ajuda

| Ação | Resultado |
| --- | --- |
| Pausar ajuda | Impede novas ações e mantém o Chrome aberto |
| Retomar ajuda | Reconecta quando necessário e observa novamente antes de agir |
| Trocar perfil durante pausa | Ajusta permissões, mantendo a ajuda pausada |
| Final da partida | Pausa a ajuda, preserva o Chrome e permite decidir quando retomar |
| X da janela | Encerra o assistente, mantendo o jogo disponível manualmente |
| Reabrir o aplicativo | Reutiliza a sessão dedicada existente, inicialmente pausada |
| Fechar jogo e aplicativo | Fecha explicitamente o Chrome dedicado e o assistente |

O Chrome pessoal não é alvo de descoberta. Uma segunda instância não pode controlar o mesmo runtime. Se houver várias abas do jogo no Chrome dedicado, o aplicativo pede que permaneça apenas a desejada.

Pausar não desfaz um preenchimento ou clique já enviado. O assistente preserva texto existente e votos desconhecidos. STOP aguarda a habilitação real; o tempo mínimo universal continua sem certificação. Manter o Chrome aberto não impede expiração ou expulsão determinada pelo servidor.

Atalhos com a janela em foco: **Ctrl+P** pausa/retoma; **Ctrl+,** abre ajustes. Os controles essenciais também ficam na janela. Bandeja e atalhos globais não são necessários.

## Instalação e plataformas

Ubuntu: pacote `stopots-assistente_2.1.0_amd64.deb` ou pasta portátil `StopotsAssistente`. O `.deb` fornece ícone no lançador e binário em `/opt/stopots-assistente`. A distribuição inclui Python e Qt; Google Chrome precisa estar instalado. Dados ficam em `XDG_STATE_HOME/stopots-assistente`, com fallback em `~/.local/state/stopots-assistente`. No ambiente do projeto, o ícone usa `.runtime` sob a raiz autorizada.

Por fonte, com Python 3.12+: `python -m pip install '.[desktop]'`; depois `stopots-assistente`. O núcleo continua acessível por `stopots-v2`. A extra `desktop` fixa PySide6 6.10.2; o adaptador mantém Playwright 1.64.1.

Windows: `scripts/instalar-windows.ps1` cria um ambiente separado e um atalho `.lnk` usando Python 3.12 e Chrome já instalados. O código contempla caminhos e processos Windows, mas instalação, DPI e Chrome precisam de validação nativa; esta entrega Linux não é certificação Windows. macOS permanece posterior.

## Organização técnica

- `desktop_model.py`: perfis, preferências permitidas e convite; senha ausente de representação e persistência.
- `desktop.py`: ciclo da janela e ponte de sinais Qt. O Playwright executa em uma thread com event loop próprio.
- `desktop_engine.py`: fila serial de comandos, revisões de política e observação contínua entre partidas. O evento de entrada confirmada é transitório para não recolher a janela repetidamente.
- `adapters/chrome_session.py`: processo Chrome independente, perfil exclusivo e reconexão CDP local vinculada ao identificador do próprio perfil.
- `adapters/invitation.py` e `entry.js`: entrada pela UI, escopo do ENTRAR, senha e erros. Avisos bloqueantes são distinguidos de anúncios acessíveis vazios.
- `ui/Main.qml`, `OrganicPanel.qml` e `ui_surface.py`: telas e superfícies vetoriais com antialiasing, incluindo renderer software.
- `desktop_diagnostics.py`: autoverificação do pacote e do driver, sem jogo online; inclui navegação após erro de senha.

A política muda sem substituir a memória de ações já enviadas. Novo contexto invalida planos no adaptador existente. Resultados preservam a distinção entre pódio e linhas visíveis; não inferir placar próprio ausente.

A interface usa renderer software por padrão, para funcionar sem depender da configuração de GPU. O preenchimento do apelido é repetido no formulário do convite: o jogo não conserva a edição feita na home durante a navegação completa. Alertas de senha levam ao formulário uma vez, preservando a navegação pelos ajustes.

## Validação e limites

Os resultados de execução são consolidados em `evidence/v2/DESKTOP_RESULTADO.json`. Testes locais incluem final/pausa, revisão de política, evento transitório, entrada por convite com senha exata, aviso vazio, campos de senha desabilitados no lobby e sobrevivência do Chrome após desconexão do driver. A autoverificação percorre temas e layouts, verifica cores, dimensão e erros QML.

O ensaio online usa sala privada, dois participantes controlados, quatro rodadas, letras A–D e pool de 16 temas. O cliente convidado usa a janela real; o anfitrião é um participante controlado pelo harness. Somente resultados efetivamente capturados entram na evidência. Tentativas falhas e interrompidas permanecem separadas.

O ensaio privado `20d13cd64f18` capturou 240 × 240, pausa no final e reabertura pausada no mesmo Chrome. A entrada sem senha `368bbcd541a4` confirmou dois participantes e o apelido solicitado em sala pública controlada, sem certificar uma partida pública. A checagem imediata de limpeza desse ensaio registrou falso enquanto o Chrome encerrava; a auditoria posterior dos recursos deve ser lida separadamente, sem alterar o registro original.

São 69 testes locais. A bateria também passou em Ubuntu 24.04 isolado. O `.deb` é instalado e exercitado em Ubuntu 24.04/26.04, em offscreen e Xvfb, com renderização em 100%, 125% e 150%. O wheel instalado é comparado aos 25 arquivos de runtime; dados da distribuição portátil também são conferidos. A GUI testa o driver Playwright inicializado e as quatro combinações de tema/layout, incluindo navegação após senha recusada.

Houve uma imagem de teste sem bibliotecas do Chrome, uma execução que excedeu o prazo e falhas de anexação CDP no container. O log posterior mostrou criação de memória compartilhada negada no TMPDIR: a limpeza transferia sua posse ao usuário do host, enquanto subprocessos do Chrome descartavam capabilities. O harness agora aplica o modo Unix 1777 à pasta temporária isolada. As tentativas anteriores permanecem registradas. A espera adicional de abas experimentada durante o diagnóstico foi retirada; o teste CDP original e suas assertions foram preservados. A causa exata do timeout mais antigo não foi estabelecida.

O pacote Linux é instalado e exercitado em ambientes Ubuntu separados. Ensaios em container/Xvfb não equivalem a testar todos os compositores GNOME; o desktop físico de referência é Pop!_OS 24.04/COSMIC/Wayland. Não há nova certificação de partidas públicas integrais, Host, Maioria, Desativado ou recuperação geral de rede.

## Backup e restauração

Antes das mudanças foi criado `/home/yuzlkk/hack/stopots/backups/stopots-v2-2.0.3-20261030-121948.tar.gz` (32.221.816 bytes), SHA-256 `3481d13082bdb5d09db96f75df9fc2c43fc6a68b22f7b1af85357a6c3508392c`. A extração conferiu os hashes dos 148 arquivos e validou o bundle Git. Inclui fonte, dados, testes, configuração, wheel 2.0.3, instruções e histórico; perfis, credenciais e caches foram excluídos.

Extraia o backup em pasta nova, confira MANIFESTO.json e siga RESTAURAR.md. O worktree original `stopots-v2` também permaneceu na 2.0.3, e o legado `stopots-bot` foi preservado. O desenvolvimento 2.1 está em `stopots-desktop`, branch `codex/v2-desktop`.

Referências técnicas: documentação oficial de [Qt for Python](https://doc.qt.io/qtforpython-6.10/), [Playwright CDP](https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect-over-cdp) e [COSMIC](https://system76.com/cosmic/theming). Essas referências orientam implementação; compatibilidade é limitada pelos ensaios registrados.
