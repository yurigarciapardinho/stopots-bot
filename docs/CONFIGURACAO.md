# Configuração e dados locais

O programa não exige `.env`, token de GitHub ou credenciais de infraestrutura.
Não salve senhas de sala em arquivos de configuração.

| Localização padrão | Sistema |
| --- | --- |
| `$XDG_STATE_HOME/stopots-assistente`, ou `~/.local/state/stopots-assistente` | Linux |
| `%LOCALAPPDATA%/StopotsAssistente` | Windows |
| `~/Library/Application Support/StopotsAssistente` | macOS, ainda sem validação nativa |

`STOPOTS_RUNTIME` substitui a raiz de dados. Ela contém preferências permitidas,
eventos e o perfil Chrome dedicado. Não compartilhe esse diretório. A GUI
preserva apelido, tema, perfil e permissões; não persiste senha, URL de convite,
endpoint ou estado ativo como preferências. Só uma janela controla o runtime.

Na CLI, `--config config/assistido.toml` ou `config/automatico.toml` carrega
`[automacao]`. Flags prevalecem sobre TOML. Consulte `stopots-v2 executar --help`.
A CLI histórica encerra sua sessão própria ao terminar; a preservação da janela
Chrome descrita no guia de uso pertence ao aplicativo desktop.

`QT_QUICK_BACKEND=software` é o padrão gráfico da GUI. Alterá-lo é uma opção
avançada, sem ampliar a matriz de GPU verificada. `STOPOTS_BUILD_ROOT` define
saídas de ferramentas de build/teste, separadamente do runtime do usuário.
