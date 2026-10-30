# Alterações

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
