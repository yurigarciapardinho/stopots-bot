# StopotS — experiência desktop

Versão do desenho: 0.3 · 30/10/2026 · idioma pt-BR.

Estado: desenho concluído, com implementação posterior na 2.1.0 documentada em DESKTOP_2_1.md. Este documento conserva as decisões anteriores à implementação. As escolhas de produto abaixo foram respondidas pelo usuário em doze perguntas nesta conversa, com requisito adicional explícito de entrada por convite. Telas, dimensões e detalhes de interação são propostas para avaliação visual. Nenhuma funcionalidade deste documento deve ser anunciada como implementada.

Base examinada: v2.0.3, commit `38906ec5bc1937b993003c3dfcfa48c246e42ff4`, worktree `stopots-v2`. Na etapa de desenho o código de execução permaneceu inalterado; a implementação posterior usa worktree separado e preserva essa versão funcional.

## Problema e resultado desejado

Hoje a CLI acompanha uma partida: `Controller.run()` retorna ao reconhecer o resultado final e `execute()` fecha o contexto persistente que abriu. O mesmo fechamento acontece ao terminar o prazo de execução ou encerrar a CLI. Isso interrompe o uso manual do Chrome e exige novos comandos para jogar novamente.

O aplicativo deve permitir abrir o jogo, escolher a ajuda e jogar várias partidas com o mesmo Chrome. O padrão é preencher campos vazios; o usuário dá STOP, avalia respostas e avança entre rodadas. Final de partida, pausa da ajuda e fechamento do aplicativo têm comportamentos próprios e visíveis.

## Decisões do usuário

| Tema | Escolha confirmada |
| --- | --- |
| Final da partida | Manter Chrome aberto e pausar a ajuda até decisão do usuário |
| Formato | Aplicativo separado do Chrome |
| Ajuda padrão | Preencher campos vazios automaticamente; STOP, votos e avanço manuais |
| Aparência | Temas claro e escuro, inspiração Pop!_OS, formas arredondadas e orgânicas |
| Escolha dos modos | Perfis prontos com ajustes por ação |
| X da janela | Encerrar o aplicativo e a ajuda, mantendo o Chrome aberto |
| Uso durante o jogo | Painel compacto, expansível para configurações e detalhes |
| Mudanças de configuração | Valer para as próximas ações assim que aplicadas |
| Informação principal | Resumo da rodada e pendências; detalhes sob demanda |
| Convite | Colar link, indicar se há senha e informar a senha quando houver; assistente executa a entrada |
| Apelido no convite | Último apelido salvo, visível e editável antes de entrar |
| Ajuda após convite | Começar assim que reconhecer a fase disponível, inclusive em partida já iniciada |
| Refinamento da prévia | Mais orgânica: acentuar curvas e assimetria suave das superfícies, mantendo campos e textos alinhados |

Prioridade de plataformas, definida no pedido: Ubuntu obrigatório; Windows em segundo lugar; macOS como possibilidade posterior.

## Fluxos principais

### Primeiro uso

1. Abrir pelo ícone do aplicativo.
2. Ver o perfil **Só preencher**, com o resumo **STOP, votos e avanço ficam com você**.
3. Escolher **Escolher no jogo** ou **Entrar por convite**.
4. No primeiro caminho, **Abrir jogo** abre o Chrome e a escolha da sala é manual. No segundo, **Entrar com ajuda** executa o convite após o preenchimento do formulário abaixo.
5. Acompanhar a ajuda no painel compacto. O jogo continua no Chrome.

A seleção de perfil ajusta permissões; a entrada ocorre pela ação explícita de abrir o jogo ou enviar o convite.

### Entrar por convite

O formulário aparece no próprio aplicativo, com divulgação progressiva do campo de senha:

| Campo ou controle | Comportamento |
| --- | --- |
| Link do convite | Aceita link de sala StopotS em português; exemplo fornecido pelo usuário: `https://stopots.com/pt/08193` |
| Seu apelido | Exibe o último apelido salvo e permite editar antes de entrar |
| A sala tem senha? | Escolha explícita obrigatória: **Não** ou **Sim** |
| Senha da sala | Só aparece com **Sim**; mascarada, com botão Mostrar/Ocultar e colagem permitida |
| Perfil de ajuda | Mantém visível o perfil que será usado, com acesso aos ajustes |
| Entrar com ajuda | Abre ou reutiliza o Chrome dedicado e realiza a entrada pela interface real |

O código da sala é texto: **08193 conserva o zero inicial**. Validar domínio e formato do link; remover espaços externos do link, preservando seu identificador. O link do exemplo é referência de desenho; não é instrução para entrar nessa sala real durante o planejamento.

A senha é um valor opaco: preservar exatamente letras maiúsculas/minúsculas, números, símbolos, acentos e espaços que o usuário fornecer. Não aplicar `strip`, normalização Unicode, conversão de caixa, transliteração nem reaproveitar a normalização das respostas do jogo. Enviar pelo preenchimento do campo, como dado, sem colocá-la na URL ou em comando de terminal.

Usar a senha somente para a tentativa solicitada, em memória; não salvar em preferências, histórico, eventos, linha de comando ou evidências. Reter o apelido é uma escolha confirmada; reter a senha não faz parte do fluxo. Ao concluir ou cancelar a entrada, descartar a cópia da senha mantida pelo aplicativo.

Passos do executor proposto:

1. Validar formulário e identificar a sessão dedicada. Se houver outra partida ativa, oferecer uma ação explícita **Sair da sala atual e entrar no convite**, antes de navegar.
2. Abrir o convite; reconhecer painel ativo e preencher o apelido quando necessário.
3. Aceitar o convite pelo botão correspondente ao painel atual. Há evidência histórica de mais de um **ENTRAR** coexistindo; não selecionar o primeiro botão global.
4. Se a interface pedir senha, preencher o valor informado e confirmar no próprio painel. Um campo de senha desabilitado no lobby não é um pedido de entrada.
5. Confirmar que entrou na sala pelo estado observado; carregar a configuração real da sala e observar a fase. Navegação ou clique, isoladamente, não significam entrada bem-sucedida.
6. Começar a ajuda selecionada assim que o contexto estiver estável. Se a partida já estiver na escrita, ajudar nessa rodada; em revisão com votos manuais, mostrar **Sua vez de avaliar**.

O assistente não altera configuração da sala para tentar entrar e não tenta adivinhar senhas. Tratamentos de erro:

| Situação | Resposta do aplicativo |
| --- | --- |
| Link inválido | Explicar o formato esperado junto ao campo, antes de abrir o Chrome |
| Sim selecionado sem senha | Solicitar preenchimento; não enviar senha vazia por engano |
| Não selecionado, mas a sala pede senha | Informar **Esta sala pede senha**, revelar o campo e aguardar o usuário |
| Senha recusada | Mostrar **A senha não foi aceita**, permitir corrigir e tentar novamente sem reiniciar tudo |
| Sala inexistente, indisponível ou cheia | Mostrar a mensagem reconhecida e permitir corrigir o convite ou voltar |
| Desconexão ou tela desconhecida | Suspender a entrada, preservar Chrome e dados não sensíveis do formulário; permitir nova tentativa explícita |

O aplicativo preservará os caracteres solicitados; o suporte do servidor a cada combinação precisa ser confirmado em ensaio dirigido. Se o jogo impuser limite ou rejeitar um formato, exibir a restrição real sem modificar a senha silenciosamente. Cada tentativa tem prazo e cancelamento; não repetir automaticamente a mesma senha recusada.

### Durante a rodada

O painel mostra conexão, ajuda ativa ou pausada, fase, rodada, letra e preenchimento observado. A área de pendências lista temas sem candidato ou que precisam de atenção. Um dado ainda não observado aparece como **Aguardando dados**, sem números inventados.

**Pausar ajuda** suspende novas ações do assistente. O usuário continua no jogo. **Retomar ajuda** faz nova leitura da interface antes de agir. Edições já feitas pelo usuário são preservadas.

O botão **STOP** pertence ao jogo. O botão **Pausar ajuda** controla o assistente; rótulos, ícones e posição devem deixar essa diferença clara.

### Ao terminar uma partida

1. Reconhecer a tela final e conservar o resultado observado, com o alcance efetivamente disponível.
2. Pausar a ajuda e descartar planos que pertenciam à partida anterior.
3. Mostrar **Partida encerrada · Ajuda pausada**.
4. Oferecer **Retomar ajuda** e **Ver detalhes**; manter o Chrome aberto.
5. Se o usuário iniciar outra partida enquanto a ajuda está pausada, continuar observando e permanecer sem executar ações até a retomada.

Manter o Chrome aberto não garante permanência na sala: expulsão por inatividade e transições do servidor continuam sendo regras do jogo. O aplicativo deve reconhecer a perda de sala e orientar a retomada, sem simular presença indefinidamente.

### Ao fechar e reabrir o aplicativo

O X interrompe a ajuda e encerra o aplicativo, preservando o Chrome dedicado. Uma ação já enviada à página pode ter produzido efeito; o aplicativo não promete desfazê-la. Novas ações deixam de ser programadas.

Na reabertura, identificar o Chrome dedicado existente e oferecer **Retomar ajuda**, inicialmente pausada. Não abrir um segundo processo usando o mesmo perfil. Se o usuário fechou o Chrome, mostrar **Chrome fechado** e oferecer **Abrir jogo**.

O comando separado **Fechar jogo e aplicativo** fica em um menu secundário, com rótulo explícito. Ele só fecha o Chrome dedicado desta ferramenta.

## Estrutura das telas

| Tela | Conteúdo e ação principal |
| --- | --- |
| Início | Entrada escolhida, perfil, resumo das permissões, estado do Chrome e ação de iniciar |
| Convite | Link, apelido editável, Sim/Não para senha, senha condicional, perfil e Entrar com ajuda |
| Painel compacto | Estado da ajuda, fase/rodada/letra, preenchimento, pendências, Pausar/Retomar, Abrir jogo e Expandir |
| Painel expandido | Mesmos dados, seletor de perfil e ações individuais; detalhes recolhíveis |
| Aparência | Sistema/Claro/Escuro, prévia imediata e opção de reduzir movimento |
| Detalhes | Atividade recente e explicação de pendências; diagnóstico técnico acessível por uma seção secundária |

O painel compacto abre como proposta em aproximadamente 360 × 480 unidades lógicas; o expandido em 920 × 680. Dimensões serão ajustadas no protótipo para 1366 × 768, escala de 125%/150% e fontes ampliadas. Não depender de janela sempre por cima, bandeja ou atalho global para os controles essenciais.

### Hierarquia do painel compacto

1. Cabeçalho: nome do assistente e Expandir.
2. Estado: **Ajuda ativa**, **Ajuda pausada** ou causa da interrupção.
3. Perfil: **Só preencher**, com acesso aos ajustes.
4. Contexto: fase, rodada e letra, quando observadas.
5. Resumo: campos com resposta e pendências. Separar preenchimento observado de ações atribuídas ao assistente.
6. Ação primária: **Pausar ajuda** ou **Retomar ajuda**.
7. Ação secundária: **Abrir jogo**. Focar janela existente é uma melhoria dependente da plataforma; sempre oferecer um caminho funcional para acessar o Chrome.

## Perfis e controles

| Perfil | Preencher vazios | Pedir STOP | Ajustar votos | Confirmar AVALIAR | Avançar entre rodadas |
| --- | --- | --- | --- | --- | --- |
| Só preencher — padrão | Sim | Manual | Manual | Manual | Manual |
| Só observar | Não | Manual | Manual | Manual | Manual |
| Automático | Sim | Sim, sujeito às condições | Sim, apenas quando há decisão fundamentada | Sim | Sim |
| Personalizado | Conforme ajustes | Conforme ajustes | Conforme ajustes | Conforme ajustes | Conforme ajustes |

Escolher um perfil aplica um conjunto explícito de permissões. Alterar qualquer chave passa a indicar **Personalizado**. A tela sempre resume as permissões efetivas; o nome do modo não pode ocultar opções herdadas de arquivo ou execução anterior.

Mesmo no perfil Automático, o final da partida pausa a ajuda, conforme escolha do usuário. O perfil não promete resolver todos os temas, avaliar respostas desconhecidas ou certificar modalidades ainda não testadas.

| Controle visível | Explicação breve |
| --- | --- |
| Preencher campos vazios | Preserva respostas e edições que já estão no formulário |
| Pedir STOP automaticamente | Aguarda o botão real ficar disponível; política padrão exige todos os campos respondidos |
| Ajustar votos | Preserva votos quando a validade é desconhecida |
| Confirmar apuração — AVALIAR | Envia a confirmação da etapa de revisão |
| Avançar entre rodadas | Continua após o resultado de uma rodada |

**Aplicação de ajustes:** mostrar **Aplicando…** até confirmação do executor. A interface só apresenta **Aplicado** depois de reconhecer a revisão efetiva da configuração. Novas ações seguem essa revisão; planos ainda não enviados são revalidados ou descartados. Cliques ou preenchimentos já enviados não são revertidos.

Pausar não apaga o perfil nem desfaz respostas. Trocar de perfil não retoma a ajuda se ela estiver pausada. Retomar não reutiliza planos de uma rodada ou partida anterior.

## Estados e mensagens

| Situação | Mensagem principal | Próximo passo |
| --- | --- | --- |
| Sem Chrome dedicado | Pronto para começar | Iniciar ajuda |
| Conectando | Abrindo o jogo… | Aguardar, com possibilidade de cancelar |
| Abrindo convite | Entrando na sala… | Cancelar ou aguardar confirmação |
| Convite com senha necessária | Esta sala pede senha | Informar senha e entrar |
| Senha recusada | A senha não foi aceita | Corrigir e tentar novamente |
| Home ou sala sem rodada | Aguardando partida | Entrar ou iniciar pelo jogo |
| Escrita, preenchimento ativo | Preenchendo campos vazios | Pausar ajuda |
| Escrita, sem candidato | Alguns temas precisam de você | Ver pendências e responder pelo jogo |
| Revisão com votos manuais | Sua vez de avaliar | Avaliar pelo jogo |
| Ranking com avanço manual | Resultado da rodada | Continuar pelo jogo |
| Pausa solicitada | Ajuda pausada | Retomar ajuda |
| Final de partida | Partida encerrada · Ajuda pausada | Retomar quando quiser |
| Conexão perdida | Conexão interrompida · Ajuda suspensa | Verificar jogo e tentar reconectar |
| Interface desconhecida | Não consegui reconhecer esta tela | Verificar o Chrome; novas ações suspensas |
| Chrome fechado pelo usuário | Chrome fechado | Abrir jogo |

Conexão, estado da ajuda e fase da partida são informações diferentes. Um painel pode estar conectado e pausado durante a escrita. Nunca apresentar **Ativo** apenas porque o processo está aberto.

## Direção visual

Inspiração: Pop!_OS/COSMIC, respeitando a preferência do usuário por formas mais orgânicas. A inspiração visual não exige usar a biblioteca nativa COSMIC e não implica integração automática com o tema do sistema.

- Dois temas completos, claro e escuro, com proposta adicional de seguir o sistema. Persistir a escolha localmente.
- Superfícies quentes no claro; carvão com leve matiz azulado no escuro. Destaque azul-petróleo/ciano suave e cor de atenção usada com parcimônia.
- Contornos orgânicos mais presentes, com curvatura contínua, cantos assimétricos e superfícies suaves que acolhem os grupos de controles. O usuário pediu esse refinamento após ver a primeira prancha. Controles mantêm alinhamento previsível e áreas de clique regulares.
- Formas orgânicas aparecem nas superfícies e pequenos detalhes. Tipografia, tabelas, textos e foco de teclado permanecem estáveis.
- Pouca decoração, sem transparência obrigatória nem blur pesado. O jogo recebe a maior parte da atenção.
- Tipografia de sistema, corpo proposto em 16, apoio em 14 e títulos em 22–26 unidades lógicas. Não depender de downloads de fontes no primeiro uso.
- Transições curtas e opcionais; nenhum conteúdo essencial depende de animação.

### Paleta candidata

| Papel | Claro | Escuro |
| --- | --- | --- |
| Fundo | #F4F2ED | #20282C |
| Superfície | #FFFDF8 | #2B353B |
| Texto principal | #233239 | #EEF3F2 |
| Texto secundário | #52636A | #B7C4C7 |
| Ação principal | #176678 | #79D1D6 |
| Texto na ação | #FFFFFF | #163136 |

São propostas de desenho, não tokens já implementados. Os seis pares candidatos de texto/superfície e texto/ação foram calculados: claro 13,02 / 6,16 / 6,55; escuro 11,19 / 7,00 / 7,80. Essa medição de paleta não valida o bitmap gerado nem os futuros componentes. Medir contraste, foco e estados desabilitados no protótipo, incluindo diferenciação sem depender apenas de cor. Botões essenciais têm alvo proposto de pelo menos 44 × 44 unidades lógicas; todas as ações essenciais devem funcionar pelo teclado.

## Contrato técnico necessário

O desenho requer separar quatro ciclos: janela do aplicativo, executor de ajuda, Chrome dedicado e partida. Encerrar um desses ciclos não deve fechar os demais implicitamente.

1. Chrome dedicado com vida independente da janela. O caminho atual de `launch_persistent_context` seguido por `context.close()` precisa ser revisto para este fluxo; remover apenas o fechamento final não resolve toda a propriedade do processo.
2. Um executor de ações por sessão. A interface envia comandos explícitos de pausa, retomada e revisão de permissões, recebendo confirmação.
3. Estado exposto por eventos tipados e snapshot atual: conexão, supervisor, fase, contexto da partida, permissões efetivas, revisão aplicada e pendências.
4. Nova partida invalida planos e deduplicação que pertenciam ao contexto anterior. Retomada exige nova observação, sem usar a letra como identidade da rodada.
5. Reconexão identifica exatamente o Chrome/perfil dedicado. Uma segunda instância do aplicativo deve encaminhar para a primeira ou informar que já existe uma sessão.
6. Timeout ou falha de observação suspende ajuda, preservando o navegador. Não trocar um encerramento inesperado por automação indefinida sem indicação na tela.
7. Persistir tema, tamanho da janela e perfil; estado ativo não reaparece silenciosamente após reinício. Não transformar arquivos privados de runtime em elementos da configuração cotidiana.
8. O núcleo continua independente da interface. O caminho gráfico deve funcionar sem scripts Bash para possibilitar Windows depois do Ubuntu.
9. Entrada por convite é um fluxo próprio do executor, com etapas e pós-condição de sala reconhecida. O helper do laboratório já exercitou convite com senha, mas a CLI atual exige entrada pela interface; não apresentar o helper como funcionalidade distribuída do novo aplicativo.
10. Segredos do formulário têm transporte próprio em memória e redação nas evidências. Credenciais não entram no modelo público de estado ou nas revisões de permissões.

A tecnologia da interface ainda não foi escolhida. A decisão será registrada depois do desenho visual, considerando encaixe com o núcleo Python, acessibilidade, Wayland, distribuição Ubuntu e posterior empacotamento Windows. Os ensaios de preservação e reanexação do Chrome serão obrigatórios para qualquer alternativa.

## Plataformas e distribuição

| Prioridade | Alvo planejado | Evidência exigida |
| --- | --- | --- |
| 1 — obrigatório | Ubuntu Desktop 24.04 e 26.04 LTS, inicialmente x86_64 | Instalação limpa, ícone no lançador, primeiro uso sem terminal, Chrome, Wayland, teclado e escala |
| Ambiente atual | Pop!_OS 24.04 LTS, COSMIC/Wayland | Usabilidade e integração no computador do usuário; não substitui ensaio em Ubuntu |
| 2 | Windows 11 x64 | Instalador, caminhos, processos, permissões, Chrome, DPI e teclado exercitados no Windows |
| 3 — posterior | macOS | Decisão de viabilidade e testes próprios; sem compromisso de suporte nesta etapa |

O formato de instalação Ubuntu deve permitir uso cotidiano por ícone. `.deb` é a primeira opção a avaliar; dependências e distribuição do navegador precisam ser verificadas no empacotamento. Não anunciar suporte multiplataforma por haver uma biblioteca que teoricamente o permite.

O ambiente atual foi consultado em 30/10/2026: `/etc/os-release` identifica Pop!_OS 24.04 LTS, base noble; sessão COSMIC e Wayland. Nenhuma troca de desktop, tema do sistema ou configuração pessoal foi realizada.

## Sequência de entrega

| Marco | Entrega | Critério de saída |
| --- | --- | --- |
| UX1 — este desenho | Decisões, fluxos, estados, controles e direção visual | Doze respostas e requisito de convite representados; propostas separadas das decisões |
| UX2 — conceito visual | Prancha com claro, escuro, convite e painel compacto | Revisão de hierarquia, arredondamento, legibilidade e personalidade antes da implementação |
| UI1 — protótipo de navegação | Telas com estados simulados, sem partida real | Fluxos de iniciar, pausar, ajustar, terminar e fechar compreensíveis; teclado e escala verificados |
| APP1 — integração local | Janela ligada ao núcleo, convite e ciclo independente do Chrome | Uma sessão, entrada confirmada, permissões com confirmação e preservação do navegador comprovadas localmente |
| APP2 — Ubuntu | Pacote instalável e validação de uso | Instalação limpa e fluxo completo certificado no Ubuntu, além do teste no computador atual |
| APP3 — Windows | Empacotamento e validação próprios | Mesmos fluxos no Windows; macOS permanece posterior |

O marco visual pode receber ajustes sem alterar adaptador, vocabulário ou comportamento do jogo. A implementação só passa a existir nos marcos seguintes.

## Critérios de aceite da experiência

1. Abrir pelo ícone e entender o perfil padrão sem terminal ou arquivo TOML.
2. Ver, antes e durante o jogo, quais ações estão automáticas e quais dependem do usuário.
3. Preencher campos vazios e preservar edições manuais; tratamento de limpeza manual de um campo deve ser verificado para evitar preenchimento indesejado.
4. Pausar e retomar sem fechar Chrome, perder a sala por ação do aplicativo ou reutilizar ações de contexto antigo.
5. Finalizar uma partida, permanecer no Chrome e jogar outra; a ajuda permanece pausada até retomada explícita.
6. Fechar a janela pelo X, continuar jogando manualmente e reabrir o aplicativo conectado à mesma sessão dedicada, com ajuda pausada.
7. Alterar permissões durante a rodada e receber confirmação fiel; nenhuma nova ação proibida começa após aplicação da revisão.
8. Distinguir ajuda pausada, conexão perdida, espera pelo usuário e ausência de candidato.
9. Usar claro/escuro, teclado e escala de tela sem perder controles ou depender apenas de cor.
10. Fechar manualmente o Chrome e ver estado coerente, sem reabertura automática inesperada.
11. Comprovar os fluxos de ciclo de vida em fixture e Chrome local antes de uma partida privada dirigida. Não entrar em várias partidas públicas para depurar a nova janela.
12. Relatar o alcance do placar observado; não transformar pódio parcial em lista completa ou pontuação própria não capturada.
13. Entrar por convite sem senha e com senha, preservando o código da sala e confirmando entrada. Exercitar apelido salvo editável e partida já iniciada.
14. Exercitar senha com números, letras, símbolos e acentos; preservar exatamente o valor enviado. Incluir erros e restrições reais do jogo no relatório. Nunca registrar o segredo em logs ou screenshots entregues.
15. Tratar senha incorreta, escolha inicial Não em sala protegida, link inválido e cancelamento sem travar nem tentar senhas automaticamente.

## Referências examinadas

- `src/stopots_v2/application.py`: `Controller.run`, encerramento por final/prazo e condições de recuperação.
- `src/stopots_v2/cli.py`: permissões efetivas, abertura do contexto e fechamento em `finally`.
- `config/assistido.toml`: preenchimento ligado e ações de STOP/apuração/avanço desligadas.
- `tools/stopots_lab.py`: convite, painel de senha e seleção do ENTRAR no painel ativo; prova auxiliar anterior, não entrada automatizada na CLI distribuída.
- `docs/v2/ARQUITETURA.md` e `AGENTS.md`: separação de componentes e preservação da participação manual.
- System76, COSMIC Theming: https://system76.com/cosmic/theming — referência visual, consultada em 30/10/2026.
- Canonical, Ubuntu 26.04 LTS release notes: https://documentation.ubuntu.com/release-notes/26.04/ — seleção dos alvos de validação, consultada em 30/10/2026.
- Playwright Python, BrowserType: https://playwright.dev/python/docs/api/class-browsertype — fechamento do contexto persistente e conexão CDP; a documentação ressalta limitações desta conexão, a validar no fluxo proposto.

Registro histórico da etapa de desenho: nesse marco foi escrita somente documentação. Não houve nova partida, instalação de framework, alteração de runtime ou fechamento de Chrome do usuário.
