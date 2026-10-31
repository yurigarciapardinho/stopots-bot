# Contribuir

Abra uma issue com um caso reproduzível ou envie um PR focado em uma mudança.
Explique o problema, o resultado esperado e como a alteração foi verificada.
Os comandos de preparação e teste estão no [guia de desenvolvimento](docs/DESENVOLVIMENTO.md).

Preserve as edições manuais, a separação entre domínio e adaptador e a avaliação
em três estados: compatível, incompatível ou desconhecida. Mudanças nos contratos
devem atualizar as fixtures correspondentes. Uma amostra da interface não basta
para estabelecer uma regra geral do jogo.

Dados novos começam pendentes e exigem fonte, revisão e decisão explícita.
Consulte [fontes do vocabulário](data/README.md) antes de alterar a curadoria.
Não copie definições, letras musicais ou textos extensos de fontes externas.

Ao contribuir, confirme que possui os direitos necessários e oferece a mudança
sob os termos da parte alterada, conforme o [mapa de procedência](docs/PROCEDENCIA.md).
Créditos e licenças de terceiros devem ser mantidos. Não há transferência
automática de titularidade nem CLA adicional implícito.

A CI verifica testes, instalação, metadados e segurança. Testes no jogo real
exigem um cenário privado controlado e um objetivo definido. Perfis Chrome,
cookies, tokens, senhas e endpoints privados não devem entrar em PRs ou
evidências públicas.
