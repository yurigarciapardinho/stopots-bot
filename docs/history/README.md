# StopotS Assistente 2.1

Aplicativo local em pt-BR, com painel compacto, temas claro/escuro e ajuda ajustável durante o jogo. O perfil padrão **Só preencher** mantém STOP, votos e avanço sob seu controle. O Chrome dedicado permanece aberto quando você fecha o aplicativo; ao final de uma partida a ajuda é pausada.

## Aplicativo visual

No computador preparado, abra `StopotS Assistente.desktop` na pasta `/home/yuzlkk/hack/stopots`. O desenvolvimento 2.1 fica em `stopots-desktop/`; `stopots-v2/` conserva a versão funcional 2.0.3. Também é possível iniciar com `stopots-desktop/scripts/desktop.sh`.

Escolha **Entrar por convite**, cole o link, confira seu apelido e selecione **Sim** ou **Não** para senha. Com **Sim**, informe a senha exatamente como recebeu. O aplicativo preenche a entrada pela interface real do jogo e confirma a sala antes de iniciar a ajuda. O código `08193` mantém seu zero inicial. A senha não é salva nas preferências ou no histórico.

Em **Sua ajuda**, escolha um perfil e ajuste cada ação. Mudanças valem para as próximas ações após a indicação de aplicação. Trocar o perfil mantém uma pausa existente. **Pausar ajuda** mantém o jogo disponível para você; **Retomar ajuda** lê novamente a situação da partida.

O pacote Ubuntu `.deb` e a distribuição portátil ficam em `../.runtime/dist-desktop`. O Chrome é necessário para jogar. Instalação por fonte: `python -m pip install '.[desktop]'` e `stopots-assistente`. A autoverificação `stopots-assistente --verificar-ui` exercita as telas em um runtime separado sem entrar em uma partida. Guia, alcance dos testes e opções Windows em [DESKTOP_2_1.md](docs/v2/DESKTOP_2_1.md).

## Núcleo e vocabulário preservados

Assistente local em Python 3.12 e Playwright, com interface e mensagens em português. O pacote v2 substitui a integração Selenium 3; o código original permanece em `stopots_bot/` e sua documentação em `docs/LEGADO.md`.

**Versão 2.0.3: catálogo público e vocabulário nos 80 temas cadastrados.** Cinco coletas rápidas trouxeram 31 temas; a base ganhou 2.000 aprovações e reconhece PDA, PCH, JLR, PÁF e as siglas da sogra. A matriz atende 1.692/2.080 células; todos os temas têm candidatos, com lacunas de letras explícitas. Os replays são offline e a partida pública integral permanece pendente. Consulte `docs/v2/CATALOGO_E_VOCABULARIO.md` e `stopots-v2 diagnostico` para o alcance atual. A certificação histórica de partidas mantém suas versões e perfis.

## CLI da versão funcional preservada

```bash
cd /home/yuzlkk/hack/stopots/stopots-v2
./scripts/lab.sh testar
./scripts/v2.sh diagnostico
./scripts/v2.sh executar
```

Os exemplos `config/assistido.toml` e `config/automatico.toml` podem ser carregados com `--config`.

O último comando abre um Chrome dedicado. Entre na sala pela interface. Por padrão, a v2 preenche campos vazios com candidatos aprovados; as demais ações dependem de opções explícitas:

```bash
./scripts/v2.sh executar --modo automatico --stop --votos --avaliar --continuar
./scripts/v2.sh executar --modo observar
./scripts/v2.sh pausar
./scripts/v2.sh retomar
```

Pausa e retomada são comandos de outro terminal. A versão carregada do vocabulário fica fixa durante a execução. Texto já presente é preservado; o modo observar não faz alterações. O encerramento por Ctrl+C fecha os recursos próprios da sessão.

`--stop` espera o botão habilitado e, por padrão, todos os campos preenchidos. `--no-exigir-todos` altera somente essa política local. A recusa conhecida por categorias incompletas é retornada como bloqueio; o adaptador fecha o aviso somente quando ele surge após sua própria tentativa. Avisos anteriores ou desconhecidos suspendem as ações. Uma tentativa de controle é deduplicada pela rodada/etapa, mesmo que o seletor mude. Não há número de segundos fixado como regra do servidor. Respostas sem categoria ou candidato aprovado ficam em branco, com possibilidade de preenchimento manual.

`--votos` marca associações conhecidas e desmarca inicial incompatível. Ausência no dicionário preserva o voto existente. `--avaliar` confirma a etapa quando AVALIAR permite. `--continuar` usa ESTOU PRONTO após ranking de rodada; não inicia outra partida após o ranking final.

## Instalação independente

Com Python 3.12+, Chrome instalado e ambiente virtual:

```bash
python -m pip install .
stopots-v2 diagnostico
stopots-v2 executar --perfil /caminho/para/perfil-dedicado
```

As dependências de runtime estão fixadas em `requirements.txt`; o ambiente de testes em `requirements-lab.lock`. `scripts/preparar-lab.sh` refaz a preparação isolada no computador de referência e instala o pacote editável. Nenhuma credencial é necessária no fluxo anônimo.

Por padrão, dados de execução vão para `.runtime/v2` no diretório atual. `scripts/v2.sh` utiliza o `.runtime` preparado na raiz autorizada. `STOPOTS_RUNTIME` altera essa raiz. Não compartilhe perfis de navegador ou arquivos de controle do laboratório.

## Configuração

As flags da CLI prevalecem sobre uma tabela TOML `[automacao]`, passada em `--config`:

```toml
[automacao]
preencher = true
stop = false
exigir_todos = true
votos = false
avaliar = false
continuar = false
```

Para reutilizar uma página já preparada num Chrome dedicado, use `--cdp http://127.0.0.1:PORTA --url URL_DA_SALA`. A seleção precisa ser única e a conexão não fecha contextos externos.

Outras opções: `--tempo-limite`, `--eventos`, `--controle`, `--semente`, `--vocabulario`, `--url` e `--headless`. Use `stopots-v2 executar --help`.

## Vocabulário e curadoria

A fonte editorial está em `data/source/editorial.json`. A distribuição contém somente a release aprovada em `src/stopots_v2/resources/vocabulary.json`, com checksum e procedência. A migração reproduz 2.688 entradas, 269 células vazias e 10 duplicatas normalizadas excedentes do legado. Importação começa como pendente.

O bootstrap local contém **293 associações aprovadas / 286 lexemas**. Cobre os 16 temas do perfil de validação nas letras A–D, respeitando o limite de 20 unidades UTF-16. Não cobre todos os temas e letras do jogo. Aprovação editorial local não garante consenso entre jogadores. A API do IBGE forneceu 5.571 municípios nesta execução. A release contém **7.986 associações aprovadas / 7.762 lexemas**, incluindo as revisões posteriores ao ensaio público. A regra editorial `ibge-city-v1` valida os pares id/nome e aprova somente Cidade, que pode ser usada por CEP. Homônimos mantêm entidades distintas; candidatos com a mesma palavra não ganham peso adicional. Há 2.050 associações pendentes. A curadoria atual combina decisões editoriais locais e seleções revisadas de Wikidata, IBGE e CBKC. As siglas fornecidas pelo usuário têm fonte explícita e aliases completos. PÁF e JLR são composições, e PDA permanece separado de Desenho Animado. A matriz de 80 temas × 26 letras tem candidatos em 1.692/2.080 células; os 72/72 do recorte público são replay offline.

```bash
./scripts/v2.sh vocabulario cobertura --letras ABCD --temas Animal Ave CEP
./scripts/v2.sh vocabulario editar data/source/editorial.json Animal Ariranha \
  --estado approved --fonte bootstrap-2026-10-29 --nota 'Associação revisada: mamífero'
./scripts/v2.sh vocabulario publicar data/source/editorial.json /caminho/atual.json
```

Revisões em lote usam `tools/review_vocabulary.py`: exigem checksum da fonte, referência factual e decisão explícita; entradas sem decisão ficam pendentes. Decisões anteriores e grafias já revisadas são preservadas. A revisão aplicada fica identificada por hash para impedir reaplicação divergente.

Publicar valida antes de substituir; a versão anterior fica em `atual.json.previous`. Editar duas vezes mantém listas e apóstrofos válidos. Acentos são preservados na grafia e normalizados na busca. Na UI medida, hífen vira espaço e apóstrofo é removido; o adaptador confirma a forma resultante e reconhece essa forma na apuração. Inglês é tratado como idioma lexical próprio. Ave inclui-se em Animal, sem a relação inversa; CEP e FLV têm composição explícita. Consulte `docs/v2/ARQUITETURA.md`.

## Verificação

```bash
./scripts/lab.sh testar
../.runtime/venv/bin/python tools/build_vocabulary.py
# --recriar refaz a migração e substitui edições da fonte editorial.
# Somente quando quiser iniciar partidas privadas reais:
../.runtime/venv/bin/python tools/validate_v2.py --partidas 3 --cli
```

O laboratório `tools/stopots_lab.py` é ferramenta de preparação. O bot distribuído está em `src/stopots_v2` e não depende dele. Os ensaios de integração usam o laboratório somente para montar a sala privada. Eventos sanitizados omitem nomes, URLs de sala, senhas e conteúdo de campos pessoais. Evidências de teste ficam em `evidence/v2`.

MIT. Baseado em [Lucas8x/stopots-bot](https://github.com/Lucas8x/stopots-bot).

Os inicializadores `.bat` preservados pertencem à v1. A entrada da v2 é `stopots-v2`; a matriz de validação atual cobre Linux e Chrome no computador de referência.
