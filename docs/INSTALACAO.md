# Instalação

## Ubuntu 24.04/26.04 amd64

Instale Google Chrome pelo fornecedor. Baixe o `.deb` em Releases deste
repositório, confira SHA256SUMS e execute `sudo apt install ./arquivo.deb`.
Abra StopotS Assistente pelo lançador. Python e Qt acompanham o aplicativo;
Chrome é externo. O pacote não instala navegador nem copia seu perfil pessoal.

No portátil, extraia o `.tar.gz` e execute `StopotsAssistente/StopotsAssistente`.
Mantenha `_internal` e `legal` junto ao executável. Bibliotecas gráficas do
sistema precisam estar disponíveis. A distribuição é destinada a Ubuntu 24.04+
amd64, não a qualquer distribuição ou arquitetura Linux.

Para atualizar, pause a ajuda, feche a janela e instale a nova versão. O Chrome
dedicado pode permanecer aberto. Não apague o diretório de dados para atualizar.
Remoção: `sudo apt remove stopots-assistente`; os dados pessoais locais são
preservados. Apague-os separadamente apenas quando desejar perder a sessão.

## Fonte e Windows

Python 3.12+, ambiente virtual e `python -m pip install '.[desktop]'` fornecem
`stopots-assistente` e `stopots-v2`. No Windows, o script
`scripts/instalar-windows.ps1` usa Python 3.12 instalado e cria atalho `.lnk`.
Um portátil Windows só deve ser classificado como testado conforme o relatório
da release. macOS permanece posterior.

Autoverificação sem partida: `stopots-assistente --verificar-ui`.
Instalação por fonte e empacotamento completo estão em DESENVOLVIMENTO.md.
