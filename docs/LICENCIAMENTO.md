# Licença, redistribuição e bibliotecas

O mapa de aplicação está em [PROCEDENCIA.md](PROCEDENCIA.md). A licença
[YGP NoResale](../LICENSES/LicenseRef-YGP-NoResale-1.0.txt) permite uso, estudo,
modificação e redistribuição gratuita dos componentes abrangidos. Proíbe sua
revenda, cobrança de cópias e inclusão em pacotes pagos sem autorização separada.
Uso interno, doações voluntárias não condicionantes e suporte vendido
separadamente têm o tratamento expresso no texto. Direitos de terceiros e
permissões anteriores permanecem válidos. Isso não é uma proteção técnica
anticópia nem garantia de prevenção de infrações.

## Bibliotecas Qt

O aplicativo usa PySide6-Essentials e bibliotecas dinâmicas Qt 6.10.2 sob a opção
LGPL. Os textos LGPL/GPL e avisos acompanham os arquivos legais da distribuição.
O manifesto de fontes de terceiros registra URLs, versões e hashes dos arquivos
correspondentes. As fontes são disponibilizadas junto à release, sob controle
do distribuidor, e mantêm suas próprias licenças.

No portátil, as bibliotecas ficam em `StopotsAssistente/_internal`; no `.deb`,
em `/opt/stopots-assistente/_internal`. Faça uma cópia da instalação e substitua
as bibliotecas Qt/PySide compatíveis pela sua compilação modificada, preservando
a arquitetura, a ABI e os caminhos relativos. Não há verificação de assinatura
ou DRM que impeça essa substituição. Para modificações incompatíveis de ABI,
reconstrua o aplicativo a partir do fonte com sua versão de Qt/PySide, usando o
procedimento de empacotamento documentado. Licenças YGP não vedam essa depuração.

Arquivos `THIRD_PARTY_NOTICES.md`, `LICENSES/`, inventário e SBOM devem acompanhar
cada redistribuição. Texto de licença e inventário automatizado não representam
parecer jurídico sobre todas as utilizações possíveis.
