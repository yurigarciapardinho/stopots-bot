# Alterações

## 2.1.0 — aplicativo desktop

- Interface Qt Quick/PySide6 em português, com temas claro, escuro e sistema, superfícies orgânicas e painel compacto expansível.
- Perfis Só preencher, Só observar, Automático e Personalizado; permissões aplicadas ao executor em execução, com confirmação da revisão.
- Chrome dedicado com vida independente do aplicativo; fechamento pelo X preserva o navegador, final pausa a ajuda e reabertura observa inicialmente pausada.
- Entrada por convite com apelido salvo editável, senha condicional preservada exatamente e confirmação de sala. Aviso vazio de acessibilidade não é tratado como modal bloqueante.
- Empacotamento Linux portátil e `.deb`, autoverificação das telas e instalador por fonte para Windows.
- Vocabulário e decisões editoriais da 2.0.3 preservados. O alcance específico desta entrega está em docs/v2/DESKTOP_2_1.md; evidências históricas mantêm suas versões.

## 2.0.3 — 30/10/2026, catálogo e cobertura dos temas

- Cinco coletas públicas úteis, 31 temas observados; seis entradas porque uma encontrou somente o final.
- Significados e aliases de PDA, PCH, JLR, PÁF, MSÉ, MST, MSU, CEP e FLV registrados conforme definição do usuário. PÁF e JLR têm composição explícita.
- Mais 2.000 aprovações: 7.986 associações / 7.762 lexemas, com 2.050 pendências preservadas.
- Todos os 80 temas têm candidatos em pelo menos oito iniciais; matriz 1.692/2.080 células. Replay da coleta 16→38/38; recorte histórico 64→72/72, ambos offline.
- Revisão em lote com preservação de decisões/grafia e validação de fontes, idioma, aliases e snapshots; 58 testes aprovados.
- Partida pública integral e modalidades adicionais permanecem sem certificação desta versão.

## 2.0.2 — 30/10/2026, curadoria e controle de avisos

- Revisão factual de 122 associações, com 56 referências e 12 entidades Wikidata selecionadas; total de 5.986 associações aprovadas e 5.973 lexemas.
- Replay offline dos 72 campos públicos: 5 → 64 com candidato aprovado; matriz de 73 rótulos × 26 letras: 356 → 441 células cobertas. Autonomia pública ampla permanece pendente.
- Recusa conhecida de STOP retorna bloqueio; fechamento restrito ao aviso surgido após tentativa própria. Avisos manuais ou desconhecidos suspendem ações.
- Deduplicação dos controles por rodada/etapa, preservada quando o seletor muda. Pódio explicitamente distinguido das linhas visíveis do ranking.
- Ferramenta de revisão idempotente com checksum da base, fontes verificáveis, decisões explícitas e preservação da grafia já revisada.
- 54 testes locais aprovados; pacote instalado em ambiente separado. Ensaio privado direcionado e limitações em docs/v2/VALIDACAO_CURADORIA.md.

## 2.0.1 — 29/10/2026, integração pública exercitada

- Aceita a rota `/pt/game` e reconhece lobby com senha desabilitada.
- Segmento público real das rodadas 3–8 até FIM DE JOGO!, com CLI concluída e pódio reconciliado.
- 47 testes locais aprovados; monitor corrigido após corrida de conclusão e encerramento.
- Vocabulário cobriu 5/72 campos públicos observados. Partida pública desde a primeira rodada e autonomia ampla seguem pendentes.
- STOP com campos incompletos foi recusado pela interface; tempo mínimo não foi estabelecido.

## 2.0.0 — 29/10/2026, Padrão validado

- Novo pacote Python com domínio imutável, controlador serial, adaptador Playwright e CLI pt-BR.
- Descoberta dinâmica dos campos, revalidação antes de ações e preservação de edição manual.
- STOP pela disponibilidade real do controle, voto por estado desejado e confirmação por etapa.
- Pausa, observação sem escrita, perfis próprios e conexão CDP local com seleção única da página.
- Vocabulário aprovado separado do legado pendente, taxonomia direcional e publicação atômica.
- Fonte factual IBGE com 5.571 municípios e bootstrap editorial, totalizando 5.864 associações aprovadas.
- Testes puros, contratos em Chrome, instalação limpa e ensaio privado pelo comando distribuído.

A matriz de certificação e os resultados são mantidos em docs/v2/VALIDACAO.md. Modalidades adicionais só são declaradas quando exercitadas em cenário próprio.
