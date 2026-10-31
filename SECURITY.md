# Segurança

A linha pública atual é 2.0.x. O código Selenium legado é histórico e não recebe
promessa de manutenção. Nenhum prazo de resposta garantido é oferecido.

Não publique credenciais, cookies, perfis Chrome, URLs privadas de sala ou
endpoints CDP em uma issue. Para vulnerabilidade com conteúdo sensível, use a
opção de relato privado na aba Security quando disponível; caso não esteja,
abra uma issue sem detalhes exploráveis solicitando um canal privado.

Informe versão, sistema, impacto e reprodução sanitizada. A execução do Chrome
usa perfil exclusivo e endpoint local vinculado ao próprio perfil. Não exponha
essa porta à rede. A senha de sala é transitória; não deve ser persistida.

Dependências são verificadas pela automação. Um relatório limpo não comprova
ausência de vulnerabilidades; falhas serão avaliadas com contexto e correção
verificada. Tokens usados para preparar a release não fazem parte do produto.
