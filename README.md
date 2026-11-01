# StopotS Bot

Projeto pessoal de **Yuri Garcia Pardinho** para jogar StopotS no Chrome com
ajuda ajustável. O aplicativo oferece preenchimento de respostas, entrada por
convite e controles para pausar ou escolher as ações automáticas. Desenvolvido
em Python, com Qt e Playwright.

[Downloads](https://github.com/yurigarciapardinho/stopots-bot/releases/latest) ·
[Documentação](docs/README.md) ·
[Reportar problema](https://github.com/yurigarciapardinho/stopots-bot/issues)

## Instalar no Ubuntu

Com Google Chrome instalado, baixe o pacote da release e execute:

```bash
sudo apt install ./stopots-assistente_2.0.1_amd64.deb
```

Abra **StopotS Bot** pelo lançador de aplicativos. Também há uma versão
portátil para Linux. As instruções de Windows e instalação por fonte estão no
[guia de instalação](docs/INSTALACAO.md).

## Começar a jogar

1. Mantenha o perfil **Só preencher** e escolha **Escolher no jogo**.
2. Entre em uma partida pelo Chrome ou use **Entrar por convite** no aplicativo.
3. O assistente preenche campos vazios; você controla STOP, votos e avanço.
4. Expanda o painel para ajustar as ações ou pause a ajuda para jogar manualmente.

Ao terminar a partida, a ajuda pausa. **Fechar a janela mantém o Chrome aberto**;
ao reabrir o aplicativo, a sessão dedicada é reutilizada com a ajuda pausada.
Veja os perfis e controles no [guia de uso](docs/USO.md).

## Recursos

- Perfis Só preencher, Só observar, Automático e Personalizado.
- Convites com ou sem senha, preservando acentos, símbolos e zeros do código.
- Temas claro, escuro e do sistema; painel compacto e ajustes durante a sessão.
- Preservação de edições manuais e verificação do contexto antes de cada ação.
- Vocabulário pt-BR com 80 temas e 7.986 associações aprovadas, com
  [fontes e lacunas documentadas](docs/VOCABULARIO.md).

## Compatibilidade

| Plataforma | Suporte |
| --- | --- |
| Ubuntu 24.04/26.04 amd64 | Distribuição Linux principal |
| Pop!_OS 24.04 / COSMIC | Interface verificada em Wayland |
| Windows x64 | Experimental |
| macOS | Planejado |

Google Chrome é instalado separadamente. O [guia de validação](docs/VALIDACAO.md)
detalha os ambientes testados e os limites conhecidos. O aplicativo usa um
perfil Chrome dedicado; [configuração e privacidade](docs/CONFIGURACAO.md).

## Créditos e licença

Desenvolvimento e manutenção: **Yuri Garcia Pardinho**. Base original:
[Lucas8x/stopots-bot](https://github.com/Lucas8x/stopots-bot).

Os componentes próprios abrangidos pela **YGP NoResale 1.0** permitem
redistribuição gratuita; a venda exige autorização separada. Permissões MIT
anteriores e licenças de terceiros permanecem válidas. Consulte
[licença](LICENSE), [créditos](CREDITS.md) e [licenciamento](docs/LICENCIAMENTO.md).
Projeto independente, sem vínculo oficial com o StopotS.
