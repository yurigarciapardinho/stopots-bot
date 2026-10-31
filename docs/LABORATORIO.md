# Laboratório de testes

O laboratório é uma ferramenta auxiliar para observar a interface, reproduzir
transições e criar cenários privados com dois participantes controlados. O
aplicativo distribuído não depende desse serviço.

## Preparação

O fluxo principal de dependências e testes está em
[DESENVOLVIMENTO.md](DESENVOLVIMENTO.md). O laboratório possui um ambiente
auxiliar, preparado a partir de `requirements-lab.lock`:

```bash
./scripts/preparar-lab.sh
./scripts/lab.sh doctor
```

Esses scripts criam ou reutilizam `../.runtime`, ao lado do clone, incluindo o
ambiente Python, caches e arquivos de controle. Escolha um diretório de
trabalho onde essa criação seja apropriada. O preparo instala o projeto de
forma editável para o laboratório; a validação de distribuição usa o wheel
instalado em ambiente separado.

## Comandos

| Comando | Efeito |
| --- | --- |
| ./scripts/lab.sh iniciar | Inicia serviço e Chrome de teste; reutiliza um serviço saudável |
| ./scripts/lab.sh sala | Cria uma sala privada com dois participantes próprios |
| ./scripts/lab.sh observar --player host | Captura uma observação sanitizada do anfitrião |
| ./scripts/lab.sh `teste-chrome` | Inicia um ensaio de uma rodada e retorna sua identificação |
| ./scripts/lab.sh resultado | Consulta progresso e resultado |
| ./scripts/lab.sh replay | Reclassifica snapshots sem entrar no jogo |
| ./scripts/lab.sh testar | Executa os testes com o ambiente auxiliar |
| ./scripts/lab.sh limpar | Fecha os contextos da sala de teste |
| ./scripts/lab.sh encerrar | Encerra o serviço e seus navegadores |

Use replay e a suíte de testes durante o desenvolvimento. Uma sala pode expirar
por inatividade; crie outra quando houver um objetivo de validação real. O
laboratório não precisa de uma conta pessoal. Senhas são geradas em memória.

## Observações e evidências

O anfitrião usa Chrome visível com perfil dedicado; o convidado usa outra
instância. O controle HTTP fica em loopback, com segredo em
../.runtime/lab-control.json. Esse arquivo é privado e não deve ser compartilhado.

Fixtures de transição ficam em tests/lab/fixtures. Relatórios devem distinguir
ensaio iniciado, rodada concluída e partida completa. Um snapshot parcial pode
servir a uma regressão, mas não estabelece o número universal de campos do jogo.
Uma execução de `teste-chrome` deve ser acompanhada por resultado; sua
identificação isolada não comprova sucesso.

Textos sintéticos verificam controles e não aprovam palavras para o vocabulário.
Amostras de tempo são relativas à observação; o pedido de STOP continua
dependendo do controle disponível na interface. A validade da medição deve
considerar também o preenchimento exigido pela sala.

## Encerramento e recuperação

Consulte doctor e use encerrar antes de reiniciar um laboratório inconsistente.
Confira a identidade de um processo antes de encerrá-lo e limite a limpeza aos
recursos do próprio ensaio. Não use comandos globais para matar instâncias do
Chrome. Preserve código, lock e fixtures ao descartar dados temporários.
