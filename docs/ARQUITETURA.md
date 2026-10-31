# Arquitetura

Um processo local reúne a janela Qt e um executor serial. A janela opera na
thread Qt; Playwright usa uma thread com event loop próprio. Comandos passam
por fila, e mudanças de política possuem revisão confirmada. Sinais levam
observações à interface; a GUI não acessa diretamente objetos Playwright.

O domínio puro representa contexto, fases e ações. O controlador observa,
planeja, revalida, executa e confirma efeitos. Sessão, sala, partida, rodada e
etapa invalidam planos antigos; memória de ações enviadas evita repetição de
controles. Coleções de temas, campos e grupos de avaliação são distintas.

O adaptador concentra seletores e a interpretação da interface. Painéis antigos
podem coexistir durante animações. Preenchimento preserva valores presentes;
voto é estado desejado, não alternância cega. Ausência lexical é desconhecida.

ChromeSession mantém Chrome independente do driver, com perfil exclusivo e
endpoint local validado pelo identificador do próprio perfil. Fechar o driver
desanexa; fechar o navegador é comando explícito. Reabertura inicia pausada.

O vocabulário separa lexemas, associações, decisões e fontes. Somente aprovações
entram no índice distribuído. Taxonomia expressa inclusão/composição sem
equivalências indevidas. A curadoria e a publicação são separadas do jogo.

Contratos detalhados e decisões anteriores estão em v2/ARQUITETURA.md. Eles
preservam sua data e contexto. Não há serviço distribuído nem backend remoto
próprio necessário para a operação desktop.
