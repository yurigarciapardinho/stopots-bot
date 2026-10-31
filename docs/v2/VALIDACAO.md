# Validação do StopotS Bot 2.0.0

Concluída em 2026-10-29T18:38:51-03:00. **Modo Padrão validado em três partidas privadas consecutivas de quatro rodadas pelo comando distribuído `stopots-v2`.**

| Partida | Placar final | Assertions |
| --- | --- | --- |
| 1 | 250 × 250 | Aprovada |
| 2 | 245 × 245 | Aprovada |
| 3 | 245 × 245 | Aprovada |

O ensaio usou dois participantes anônimos controlados, pool de 16 temas, letras A–D e tempo Mais lento. Foram verificadas 12 rodadas, 288 observações de etapas de apuração, placares de rodada e telas finais da mesma execução. A soma dos pontos conferiu com o final em cada cliente. Não foi detectada aplicação duplicada com o mesmo ID por participante. O relatório contém 586 efeitos confirmados no prazo curto, 49 registros com confirmação imediata indeterminada e 6 planos descartados como obsoletos. As transições posteriores e os resultados completos foram observados sem repetir automaticamente ações incertas; não usa retorno ao lobby como prova de final.

Relatório completo: `evidence/v2/b03849d5f071.json`. Código funcional: commit `aa7ae2dfa1c987d601318e2408d6cc689ee970c1`. Versões e hashes do pacote, adaptador e vocabulário estão no relatório e em CERTIFICACAO.json. A revisão posterior 98cfefe4e37de1deddbcfead6fceb841c2f61a59 ajustou a confirmação e a equivalência da normalização do input. A sonda real confirmou Bem-te-vi → BEM TE VI e D'Ávila → DAVILA como APLICADA, preservando os mesmos candidatos do perfil certificado. As três partidas continuam vinculadas ao commit original; a revisão tem prova específica em evidence/v2/normalizacao-adaptador-v2.json. A base de vocabulário permaneceu igual.

## Validação complementar

A sonda `evidence/v2/45d76f79ce58.json`, com anfitrião visível no Chrome e convidado controlado, confirmou campo vazio preservado, inicial errada desmarcada, resposta desconhecida com voto preservado e ranking de rodada 75 × 55 em ambos os clientes. A palavra sintética DXYZ exercitou abstenção semântica e não foi incorporada ao vocabulário. A sonda termina depois de uma rodada e não se apresenta como partida completa.

42 testes locais aprovados em 9,26 s, incluindo domínio, identidade, persistência, taxonomia, CLI e contratos em Chrome com DOM local. Instalação por wheel em ambiente separado e comando de entrada conferidos. Busca em memória: 2.000 iterações, p95 1.712 ms, máximo 4.1488 ms, carga 82.044 ms; exclui Chrome/rede.

## Interface comprovada

A tela final real é FIM DE JOGO!, em `.end`, com pódio `.rkg`, nome `h4` e pontos no `p` filho direto. Posições vazias são ignoradas. O ranking da rodada tem seu próprio número no título; o contador geral pode adiantar durante transições. O adaptador espera coleções e pontos estáveis antes de continuar. STOP respeita a habilitação da interface; as amostras não estabelecem tempo mínimo universal.

## Matriz de alcance

| Capacidade | Estado |
| --- | --- |
| Padrão, perfil privado de referência | Validado, três partidas / 12 rodadas |
| Chrome visível, preenchimento e apuração dos casos limite | Validado em sonda de uma rodada |
| Home, entrada privada, senha e configuração sincronizada | Exercitados pelo helper de preparação |
| Campos e grupos dinâmicos; 16 campos / 20 grupos | Contrato local sintético; não são quantidades universais do jogo |
| Host, Desativado e Maioria | Não certificados |
| Recuperação de rede | Invalidação local testada; recuperação online não certificada |
| Outras plataformas, idiomas e perfis de sala | Não certificados por esta matriz |

Todos os navegadores e contextos criados pelos ensaios foram encerrados. O acesso remoto do usuário foi preservado. Tentativas anteriores e sondagens permanecem identificadas como falhas ou probes; não entram na contagem das três partidas aprovadas.

## Normalização medida

A sonda evidence/v2/normalizacao-real.json registrou caixa, acentos, hífen, apóstrofo, espaços, dígito e emoji. Hífen vira espaço; apóstrofo é removido. A grafia editorial e sua chave lexical permanecem preservadas. A comparação da apuração aceita a forma renderizada pela UI, sem transformar novamente o texto recebido. Isso corrigiu as sete confirmações de preenchimento indeterminadas de Bem-te-vi na execução inicial. Validade semântica de respostas de um caractere e Unicode fora dos exemplos medidos não foi certificada.

Smoke da CLI com navegador próprio: home reconhecida, prazo controlado encerrado e mesmo perfil reaberto. O PID que detinha o perfil não permaneceu ativo após fechamento; o Chrome pode deixar um arquivo de lock residual. Evidência: smoke-navegador-proprio.json.

## Ensaio público posterior — 2.0.1

O comando instalado concluiu um segmento público das rodadas 3–8 com código 0 e FIM DE JOGO! capturado. Pódio 490/215/170 reconciliado. A base cobriu 5/72 campos; houve valores não atribuíveis às ações da CLI. São 47 testes locais após correções de rota, lobby e monitor. Não é certificação pública desde a rodada 1. Detalhes, limites e evidências em [VALIDACAO_PUBLICA.md](VALIDACAO_PUBLICA.md).

## Curadoria e controles — 2.0.2

A revisão adiciona 122 associações factualmente revisadas e o tratamento da recusa de STOP. O replay offline do recorte público passou de 5/72 para 64/72; a matriz de 73 rótulos por 26 letras possui 441/1.898 células com candidato. Foram aprovados 54 testes locais, incluindo mudança de seletor após controle já enviado. O ensaio privado FIMO, a identificação do wheel e as limitações estão em [VALIDACAO_CURADORIA.md](VALIDACAO_CURADORIA.md). A certificação histórica das três partidas acima continua vinculada à versão 2.0.0.

## Catálogo e dados — 2.0.3

58 testes locais aprovados; cinco coletas públicas de temas e instalação limpa do pacote. Todos os 80 temas têm candidatos, com 1.692/2.080 células atendidas. O recorte atual cobre 38/38 pares e o histórico 72/72 em replay offline. A coleta não escreve respostas nem certifica partida pública integral. Ver [CATALOGO_E_VOCABULARIO.md](CATALOGO_E_VOCABULARIO.md).
