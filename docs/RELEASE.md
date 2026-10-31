# Publicar uma release

## Preparar a versão

1. Crie uma branch a partir do ramo principal e preserve a versão anterior.
2. Atualize a versão em `pyproject.toml` e `src/stopots_v2/__init__.py` e sincronize o lock.
3. Revise CHANGELOG, instruções de instalação, autoria, licenças e avisos de terceiros.
4. Execute os checks de metadados, testes e instalação limpa do wheel.
5. Integre a alteração somente com os checks exigidos pelo repositório aprovados.

Os comandos de preparação estão em [DESENVOLVIMENTO.md](DESENVOLVIMENTO.md).
Revisões documentais devem conferir também o README incorporado aos metadados,
os arquivos legais e o conteúdo da distribuição fonte.

## Construir os pacotes

Acione o workflow `release.yml` manualmente ou crie uma branch
`release-candidate/X.Y.Z` apontando para um commit aprovado no ramo principal.
O workflow verifica essa origem e produz `release-linux` e, quando o job
correspondente conclui, release-windows-experimental.

O pacote Linux inclui wheel, distribuição fonte, portátil, `.deb`, avisos,
fontes de terceiros e registros de integridade. Confira o resultado dos jobs,
os hashes dos arquivos e os relatórios de instalação. O SBOM e a atestação
devem identificar o conjunto a que se referem.

## Verificar e publicar

Teste o formato instalado, a interface e o cenário funcional necessário à
mudança. Para teste no jogo, use o wheel instalado sem o código-fonte no
sys.path. Capture o final real, pausa, fechamento da janela, persistência do
Chrome, reabertura e limpeza. Partidas públicas não são iniciadas pela CI.

Uma revisão só de texto pode usar evidência funcional anterior, desde que
a comparação do código e das dependências seja registrada e o alcance fique
claro. Não apresente essa comparação como uma nova partida executada.

Crie `VALIDACAO_X.Y.Z.json` com o commit, os pacotes, os testes e os limites.
Gere o manifesto final e `SHA256SUMS_FINAL` para os arquivos publicados. Crie
a tag vX.Y.Z no mesmo commit e prepare uma release em rascunho. Confira a
descrição, os downloads e os avisos antes de publicar.

## Integridade e permissões

Uma tag pública e os arquivos já distribuídos permanecem imutáveis. Correções
de conteúdo dos pacotes geram uma nova versão. O texto da página da release
pode ser atualizado sem substituir silenciosamente seus arquivos.

Os workflows de PR usam permissões somente de leitura. A CI constrói os
candidatos; a publicação é uma ação separada do mantenedor. O job Linux tem
permissões específicas para atestações e identidade OIDC, sem escrita de código.
Credenciais de publicação não devem integrar o repositório ou os pacotes.
Uma atestação registra procedência e não substitui teste funcional.
