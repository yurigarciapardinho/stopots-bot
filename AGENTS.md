# Trabalho no StopotS v2

Usar este worktree para desenvolver. A raiz autorizada no computador é /home/yuzlkk/hack/stopots. O clone stopots-bot é o baseline legado; este worktree fica em stopots-v2. Conferir branch e alterações do usuário antes de editar.

Ler primeiro ../planejamento-v2/RETOMADA_V2.md, depois PLANO_V2_PTBR.md e BACKLOG_V2.json apenas nas partes do marco em execução. Não reinstalar nem repetir o estudo inicial sem uma causa concreta. As skills stopots-v2-desenvolver e stopots-ui-validar complementam o procedimento.

Ambiente: ../.runtime/venv/bin/python, requirements-lab.lock e scripts/lab.sh. Executar scripts/lab.sh testar para regressão local e scripts/lab.sh doctor para diagnóstico. O laboratório e o adaptador mínimo estão em tools/stopots_lab.py; eles não são a implementação completa da v2. Consultar docs/LABORATORIO.md.

Separar domínio/controlador/adaptador/curadoria na v2. Tema cadastrado, campo da rodada e grupo de revisão são coleções distintas. Descobrir a lista completa de campos e confirmar estabilidade antes de preencher. Não interpretar snapshots parciais de animação como formulário completo.

Ações precisam de fase/contexto, prazo e efeito confirmado. STOP deve aguardar habilitação real; não fixar duração a partir de medição incompleta. Preservar edição manual e voto desconhecido. Ausência do vocabulário não prova resposta inválida. Serializar e publicar dados sem transformar listas em strings.

Testes online usam sala privada e participantes controlados. scripts/lab.sh sala cria outra sala e descarta contextos antigos; a sala anterior pode expirar. Priorizar fixtures locais durante desenvolvimento e testar online uma hipótese específica. Não manter salas indefinidamente para preservar estado.

Perfis, caches, tokens e logs de runtime ficam em ../.runtime. Não adicionar runtime ao Git, entregar perfis, publicar credenciais ou fechar Chrome pessoal. Fechar apenas recursos próprios. Separar observação real, fixture e hipótese nos relatos. Placar final só é validado quando sua tela foi capturada; retorno ao lobby não basta.
