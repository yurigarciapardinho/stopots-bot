# Preparar e publicar uma release

1. Preserve o snapshot funcional e a versão anterior. Faça as mudanças em branch.
2. Atualize a versão autoritativa do pyproject e a versão exposta; execute o
   check de metadados, regressão e instalação limpa do wheel.
3. Confira autoria, mapa de licenças, avisos, fontes de terceiros e conteúdo do
   pacote. O publicador PyPI legado não faz parte deste fluxo.
4. Construa todos os assets a partir de um SHA aprovado na história da main.
   Teste instalação, interface e o cenário dirigido necessário.
5. Gere SBOM, inventários, SHA256SUMS e manifesto. Vincule-os ao commit e ao
   digest de cada arquivo; atestação de procedência não prova correção funcional.
6. Acione release.yml manualmente ou crie a branch `release-candidate/X.Y.Z`
   apontando para o SHA aprovado na main. O workflow gera os artifacts
   `release-linux` e, quando aprovado no runner, `release-windows-experimental`.
7. O mantenedor baixa os artifacts, verifica seus hashes, instala o wheel para
   o ensaio online e anexa `VALIDACAO_X.Y.Z.json` ao conjunto. Cria a tag
   `vX.Y.Z` no mesmo SHA e uma release em rascunho, usando sua credencial com
   permissão Contents. Depois de conferir evidências, fontes e assets, publica
   o conjunto aprovado. Windows sem ensaio no jogo permanece experimental.

Se houver interrupção, confira SHA, versão e hashes antes de retomar. Não
sobrescreva asset publicado com bytes diferentes. Corrija em nova versão e
documente o problema. Uma tag pública não é deslocada silenciosamente.

Para o ensaio online, use o wheel instalado sem fonte no sys.path. Capture o
final real e comprove pausa, X, persistência do Chrome, reabertura e limpeza.
Partidas públicas não são iniciadas automaticamente pela CI.

Permissões de PR são somente leitura. A CI constrói candidatos, sem publicar
automaticamente. O job Linux pode escrever atestações e obter identidade OIDC;
não recebe escrita de código. O PAT de preparação não é colocado em secrets de CI. Regras de
branch só exigem checks depois de sua primeira execução bem-sucedida.
