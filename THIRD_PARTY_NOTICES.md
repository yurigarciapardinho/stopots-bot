# Componentes de terceiros

A licença YGP não se aplica aos componentes abaixo nem limita as permissões de
seus titulares. A MIT original está preservada em [LICENSES/MIT.txt](LICENSES/MIT.txt).

| Componente | Licença declarada / observação |
| --- | --- |
| Código legado de Lucas8x | MIT; copyright (c) 2019 Lucas8x |
| Python | PSF e avisos de componentes da biblioteca padrão |
| Playwright e driver | Apache-2.0 e avisos incluídos no driver/Node |
| greenlet | MIT e Python-2.0, conforme distribuição |
| pyee | MIT |
| typing-extensions | PSF-2.0 |
| PySide6-Essentials / Shiboken6 / Qt essencial | Opção LGPL-3.0, com termos e exceções específicos dos componentes |
| ICU 73, incorporado ao Qt Linux | Avisos Unicode e ICU em `LICENSES/ICU-73.txt`, obtidos do fornecedor |
| PyInstaller bootloader | GPL-2.0-or-later com exceção de distribuição do bootloader |
| Dados de terceiros | Atribuições e termos em data/README.md e registros de fonte |

Os pacotes desktop usam bibliotecas dinâmicas. É permitida sua substituição e
a engenharia reversa necessária à depuração de modificações de bibliotecas
LGPL. O [guia de licenciamento](docs/LICENCIAMENTO.md) descreve as fontes
correspondentes, o inventário e as instruções. Módulos Qt adicionais de gráficos,
WebEngine e teclado virtual não são necessários ao assistente e não fazem
parte do conjunto distribuído.

O inventário de cada pacote registra bibliotecas e avisos efetivamente
incluídos. A lista de dependências do ambiente de construção pode conter
ferramentas que não acompanham o aplicativo. Google Chrome é um requisito
externo e não é distribuído com o assistente.
