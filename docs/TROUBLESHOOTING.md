# Problemas comuns

| Sintoma | Ação |
| --- | --- |
| Chrome não abre | Confira a instalação do Google Chrome e se o executável está acessível |
| Perfil ocupado ou segunda instância | Use somente uma janela do assistente por diretório de execução; confira a sessão dedicada existente |
| Várias abas do jogo | Deixe apenas a aba desejada no Chrome dedicado e reconecte |
| Senha necessária ou recusada | Corrija Sim/Não e o campo; preserve maiúsculas, espaços, símbolos e acentos |
| Ajuda pausada após o final | Retome quando quiser continuar; a pausa é o comportamento esperado |
| Janela fecha e Chrome permanece | O X preserva o jogo; use Fechar jogo e aplicativo para fechar ambos |
| Campo sem resposta | Pode faltar um candidato aprovado ou uma categoria reconhecida; preencha manualmente |
| Tela desconhecida | Confira o aviso no jogo e mantenha as ações suspensas até reconhecer o contexto |
| Falha gráfica | Execute `stopots-assistente --verificar-ui` e informe sistema, versão e formato instalado |
| Expulsão por inatividade | Entre novamente pelo jogo; manter o Chrome aberto não muda a política do servidor |

O renderer padrão é software. Se estiver usando outro backend gráfico,
repita o diagnóstico com a configuração padrão. As diferenças entre perfil
dedicado e dados do aplicativo estão em [configuração](CONFIGURACAO.md).

Ao [reportar um problema](https://github.com/yurigarciapardinho/stopots-bot/issues),
informe versão do aplicativo e do Chrome, sistema, formato instalado e passos
para reproduzir. Revise os logs antes de enviar e retire dados pessoais.
Não envie pastas de perfil, cookies, tokens, senhas ou endpoints de conexão.
Vulnerabilidades devem seguir [SECURITY.md](../SECURITY.md).
