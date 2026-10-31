# Configuração e dados locais

## Preferências do aplicativo

A interface salva apelido, tema, perfil, permissões e a preferência de redução
de movimento. Senha da sala, link do convite, endpoint de conexão e estado ativo
da ajuda não são preferências persistidas.

| Sistema | Raiz padrão dos dados |
| --- | --- |
| Linux | `$XDG_STATE_HOME/stopots-assistente` ou `~/.local/state/stopots-assistente` |
| Windows | `%LOCALAPPDATA%/StopotsAssistente` |
| macOS | `~/Library/Application Support/StopotsAssistente`; plataforma ainda sem validação nativa |

`STOPOTS_RUNTIME` substitui essa raiz. O aplicativo mantém seus arquivos em
subdiretórios próprios, incluindo `desktop` para preferências e controle da
sessão. Somente uma janela pode controlar o mesmo diretório de execução.

O perfil Chrome dedicado pode conter cookies e dados de sessão. Não compartilhe
esse diretório nem o anexe a uma issue. O aplicativo não procura o perfil
pessoal do Chrome e não envia telemetria própria. Chrome e StopotS mantêm suas
comunicações normais.

## CLI

O comando `stopots-v2 executar` aceita um arquivo TOML com a tabela `[automacao]`:

```bash
stopots-v2 executar --config config/assistido.toml
```

As flags da linha de comando prevalecem sobre o arquivo. Há exemplos em
[config/](../config/); consulte `stopots-v2 executar --help` para todas as opções.
Pausa e retomada também podem usar o arquivo de controle da execução.

Sem `STOPOTS_RUNTIME`, a CLI usa `.runtime/v2` sob o diretório de trabalho. A CLI
encerra o Chrome que iniciou ao terminar. A preservação do navegador ao fechar
a janela pertence ao aplicativo desktop; uma conexão CDP anexada pela CLI
preserva os contextos externos.

## Opções avançadas

`QT_QUICK_BACKEND=software` é o padrão gráfico. Outro renderer pode ser testado,
mas não amplia a matriz de compatibilidade já verificada. `STOPOTS_BUILD_ROOT`
define a saída das ferramentas de construção e teste, separada dos dados do
usuário. Não salve senhas em arquivos TOML ou variáveis de configuração.
