# Instalação

Google Chrome deve estar instalado pelo fornecedor. O aplicativo utiliza um
perfil dedicado e não copia o perfil pessoal do navegador.

## Ubuntu 24.04/26.04 amd64

Baixe o arquivo `.deb` nos [downloads](https://github.com/yurigarciapardinho/stopots-bot/releases/latest).
Confira seu SHA-256 com `SHA256SUMS_FINAL` e instale pelo gerenciador de
aplicativos ou pelo terminal:

```bash
sudo apt install ./stopots-assistente_2.0.1_amd64.deb
```

Abra **StopotS Assistente** pelo lançador. Python e Qt acompanham o pacote;
Google Chrome é instalado separadamente. A distribuição Linux é destinada a
Ubuntu 24.04 ou mais recente, na arquitetura amd64.

Para atualizar, pause a ajuda, feche a janela e instale a nova versão. O Chrome
dedicado pode permanecer aberto. Os dados da sessão são mantidos. Para remover
o pacote, use `sudo apt remove stopots-assistente`; os dados pessoais locais são
preservados e podem ser apagados separadamente, se desejado.

## Linux portátil

Extraia `stopots-assistente-2.0.1-linux-x86_64.tar.gz` e execute
`StopotsAssistente/StopotsAssistente`. Mantenha as pastas `_internal` e `legal` ao
lado do executável. As bibliotecas gráficas do sistema devem estar disponíveis;
o portátil tem o mesmo alvo Ubuntu/amd64 do pacote `.deb`.

## Windows x64 — experimental

Extraia `stopots-assistente-2.0.1-windows-x86_64.zip` e execute
``StopotsAssistente/StopotsAssistente`.exe`, mantendo as pastas que acompanham o
executável. Google Chrome deve estar instalado.

O [guia de validação](VALIDACAO.md) descreve os testes Windows. O suporte
permanece experimental. Como alternativa por fonte, o script
[instalar-windows.ps1](../scripts/instalar-windows.ps1) usa Python 3.12 já
instalado, prepara um ambiente separado e cria um atalho.

## Código-fonte

Com Python 3.12 ou mais recente e Google Chrome:

```bash
git clone https://github.com/yurigarciapardinho/stopots-bot.git
cd stopots-bot
python3 -m venv .venv
. .venv/bin/activate
python -m pip install '.[desktop]'
stopots-assistente
```

No PowerShell, use `py -3.12 -m venv .venv` e ative com
`.venv/Scripts/Activate.ps1` antes da instalação. A CLI se chama `stopots-v2`.
O fluxo com dependências travadas está no [guia de desenvolvimento](DESENVOLVIMENTO.md).

## Verificar a interface

Execute `stopots-assistente --verificar-ui` para exercitar a interface sem
entrar em uma partida. Se houver falha, consulte [problemas comuns](TROUBLESHOOTING.md).
macOS permanece planejado, sem pacote ou validação nativa anunciados.
