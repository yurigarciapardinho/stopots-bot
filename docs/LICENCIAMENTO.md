# Licenciamento

O [mapa de procedência](PROCEDENCIA.md) identifica os termos de cada parte do
projeto. Os componentes próprios abrangidos pela
[YGP NoResale 1.0](../LICENSES/LicenseRef-YGP-NoResale-1.0.txt) permitem uso,
estudo, modificação e redistribuição gratuita. Sua revenda, cobrança de cópias
ou inclusão em pacotes pagos exige autorização separada.

Uso interno, doações voluntárias não condicionantes e suporte vendido
separadamente seguem o tratamento do texto integral. A YGP não revoga
permissões anteriores nem limita direitos de terceiros. O código legado e os
materiais identificados como MIT continuam sob essa licença. O projeto é
código disponível sob termos específicos, sem declaração de licença open
source aprovada pela OSI.

## Bibliotecas Qt

O aplicativo usa PySide6-Essentials e bibliotecas dinâmicas Qt 6.10.2 sob a
opção LGPL. Os textos LGPL/GPL e os avisos acompanham os arquivos legais da
distribuição. O manifesto de fontes de terceiros registra URLs, versões e
hashes. As fontes correspondentes são disponibilizadas junto da release e
mantêm suas próprias licenças.

No portátil, as bibliotecas ficam em `StopotsAssistente/_internal`; no `.deb`,
em /opt/stopots-assistente/_internal. Faça uma cópia da instalação antes de
substituir bibliotecas Qt/PySide por uma compilação modificada compatível,
preservando arquitetura, ABI e caminhos relativos. Não há assinatura ou DRM
que impeça essa substituição.

Para modificações incompatíveis de ABI, reconstrua o aplicativo com a sua
versão de Qt/PySide, seguindo o [fluxo de desenvolvimento](DESENVOLVIMENTO.md).
É permitida a engenharia reversa necessária à depuração dessas modificações
das bibliotecas LGPL; a licença YGP não veda essa atividade.

## Redistribuição

Mantenha `LICENSE`, `THIRD_PARTY_NOTICES.md`, `LICENSES/`, inventário e SBOM junto
de cada redistribuição, conforme os termos aplicáveis. O inventário e os
textos legais não constituem parecer jurídico sobre todos os usos possíveis.
Consulte também os [avisos de terceiros](../THIRD_PARTY_NOTICES.md).
