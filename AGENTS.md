# Trabalho no StopotS desktop 2.1

Usar este worktree para desenvolver. A raiz autorizada no computador é /home/yuzlkk/hack/stopots. O clone stopots-bot é o baseline legado; stopots-v2 preserva a versão funcional 2.0.3. Este worktree é stopots-desktop, branch codex/v2-desktop. Conferir branch e alterações do usuário antes de editar.

Ler primeiro docs/v2/DESKTOP_2_1.md e evidence/v2/DESKTOP_RESULTADO.json. O checkpoint ../.runtime/checkpoint-v2-desenvolvimento.json identifica a entrega atual. ../planejamento-v2/RETOMADA_V2.md e os arquivos associados conservam o histórico da 2.0.3; não tratá-los como descrição da interface desktop atual. Não reinstalar nem repetir o estudo inicial sem uma causa concreta. As skills stopots-v2-desenvolver e stopots-ui-validar complementam o procedimento.

Ambiente desktop: ../.runtime/venv-desktop/bin/python. Wheel isolado: ../.runtime/venv-desktop-release/bin/python. scripts/desktop.sh abre a interface; executar python -m pytest -q pelo ambiente desktop para regressão e stopots-assistente --verificar-ui para telas sem partida. O laboratório antigo usa ../.runtime/venv e scripts/lab.sh; tools/stopots_lab.py continua sendo preparação auxiliar. Não misturar o resultado do helper com o da GUI distribuída. Consultar docs/LABORATORIO.md e o guia desktop.

Separar domínio/controlador/adaptador/curadoria na v2. Tema cadastrado, campo da rodada e grupo de revisão são coleções distintas. Descobrir a lista completa de campos e confirmar estabilidade antes de preencher. Não interpretar snapshots parciais de animação como formulário completo.

Ações precisam de fase/contexto, prazo e efeito confirmado. STOP deve aguardar habilitação real; não fixar duração a partir de medição incompleta. Preservar edição manual e voto desconhecido. Ausência do vocabulário não prova resposta inválida. Serializar e publicar dados sem transformar listas em strings.

Testes online usam sala privada e participantes controlados. scripts/lab.sh sala cria outra sala e descarta contextos antigos; a sala anterior pode expirar. Priorizar fixtures locais durante desenvolvimento e testar online uma hipótese específica. Não manter salas indefinidamente para preservar estado.

Perfis, caches, tokens e logs de runtime ficam em ../.runtime. Não adicionar runtime ao Git, entregar perfis, publicar credenciais ou fechar Chrome pessoal. Fechar apenas recursos próprios. Separar observação real, fixture e hipótese nos relatos. Placar final só é validado quando sua tela foi capturada; retorno ao lobby não basta.
