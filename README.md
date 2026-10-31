# StopotS Assistente 2.0

**Projeto de Yuri Garcia Pardinho.** Assistente desktop em português para jogar
com ajuda ajustável: painel compacto, temas claro/escuro/sistema, perfis e entrada
por convite. A versão 2.0.0 consolida todo o desenvolvimento mais recente,
incluindo a interface desktop anteriormente numerada internamente como 2.1.0.

[Downloads](https://github.com/yurigarciapardinho/stopots-bot/releases) ·
[Instalação](docs/INSTALACAO.md) · [Como usar](docs/USO.md) ·
[Reportar problema](https://github.com/yurigarciapardinho/stopots-bot/issues) ·
[Créditos](CREDITS.md) · [Licença](LICENSE)

## Começar no Ubuntu

Baixe o `.deb` da release e instale pelo gerenciador de aplicativos, ou use:

```bash
sudo apt install ./stopots-assistente_2.0.0_amd64.deb
```

É necessário ter Google Chrome instalado. Abra **StopotS Assistente** no
lançador. O portátil Linux é alternativa sem instalação do aplicativo no sistema.

1. Deixe **Só preencher**, escolha **Escolher no jogo** e entre normalmente.
2. Para convite, cole o link, confira o apelido e escolha se a sala tem senha.
3. O assistente preenche campos vazios; você controla STOP, votos e avanço.
4. Expanda o painel para ajustar permissões. Ao fim da partida a ajuda pausa.

**Fechar a janela mantém o Chrome aberto.** Reabrir o assistente reutiliza a
sessão dedicada existente e começa pausado. Fechar jogo e aplicativo é uma ação
separada. Pausar não desfaz cliques ou texto já enviados.

## O que está incluído

- Núcleo Python/Playwright com contexto de partida, ações revalidadas e proteção
  de edições manuais; ausência de vocabulário não significa resposta inválida.
- Perfis Só preencher, Só observar, Automático e Personalizado, com mudanças
  aplicadas às próximas ações e confirmação da revisão.
- Convites com zero inicial, apelido editável e senha exata, incluindo acentos
  e símbolos. Senhas de sala não entram nas preferências ou nos eventos.
- 80 temas cadastrados, 7.986 associações aprovadas e 7.762 lexemas; cobertura
  de 1.692/2.080 células tema/letra. Há lacunas e 2.050 associações pendentes
  que não são distribuídas como respostas aprovadas.

## Plataformas e limites

| Plataforma | Alcance |
| --- | --- |
| Ubuntu 24.04 amd64 | Plataforma principal da distribuição Linux |
| Ubuntu 26.04 amd64 | Instalação e smoke em ambiente isolado |
| Pop!_OS 24.04/COSMIC | Referência física da interface e do Chrome dedicado |
| Windows | Segunda prioridade; suporte experimental até validação nativa suficiente |
| macOS | Planejado para etapa posterior |

O [relatório de validação](docs/VALIDACAO.md) identifica testes, versão e formato
de pacote realmente exercitados. Container/Xvfb não certifica todos os
compositores. Modos Host/Maioria/Desativado, recuperação geral de rede e partida
pública integral não são anunciados como certificados. STOP aguarda habilitação
real; não há um tempo mínimo universal inventado. O servidor pode expulsar por
inatividade mesmo com o Chrome aberto.

## Instalar por fonte

Com Python 3.12 e Chrome, em ambiente virtual:

```bash
git clone https://github.com/yurigarciapardinho/stopots-bot.git
cd stopots-bot
python3 -m venv .venv
. .venv/bin/activate
python -m pip install '.[desktop]'
stopots-assistente
```

A CLI é `stopots-v2`; o aplicativo é `stopots-assistente`. Consulte
[configuração](docs/CONFIGURACAO.md), [desenvolvimento](docs/DESENVOLVIMENTO.md)
e [problemas comuns](docs/TROUBLESHOOTING.md). A autoverificação
`stopots-assistente --verificar-ui` exercita a interface sem entrar no jogo.

## Privacidade

O programa usa um perfil Chrome dedicado. Não descobre o perfil pessoal nem
envia telemetria própria. Chrome e o serviço StopotS mantêm suas comunicações
normais. Dados de execução ficam no dispositivo; veja os caminhos no guia de
configuração. Nunca publique perfis, cookies, senhas ou endpoints CDP em issues.

## Autoria e licença

A geração 2.0 é desenvolvida e mantida sob a direção de **Yuri Garcia Pardinho**,
com origem em [Lucas8x/stopots-bot](https://github.com/Lucas8x/stopots-bot).
Créditos, licença MIT da base e histórico são preservados. Dependências e dados
não são atribuídos como obras exclusivas de Yuri.

Os componentes próprios abrangidos pela YGP NoResale podem ser redistribuídos
gratuitamente; sua venda exige autorização separada. Direitos MIT já concedidos
e licenças de terceiros permanecem válidos. Leia [LICENSE](LICENSE),
[procedência](docs/PROCEDENCIA.md) e [avisos](THIRD_PARTY_NOTICES.md).
É código disponível com termos específicos, não uma declaração de licença
open source aprovada pela OSI. Projeto independente, sem vínculo oficial com o jogo.
