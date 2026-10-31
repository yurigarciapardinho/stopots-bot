# Desenvolvimento

## Preparar o ambiente

Requisitos: Python 3.12, uv 0.11.16 e Google Chrome. Na raiz do repositório:

```bash
uv sync --frozen --extra desktop --extra test --group build --group audit
uv run --frozen --no-sync python tools/check_metadata.py
uv run --frozen --no-sync pytest -q
uv run --frozen --no-sync stopots-assistente --verificar-ui
```

Depois da sincronização completa, `--no-sync` mantém os extras e grupos já
instalados. O lock inclui execução, interface, construção e auditoria.
Atualizações de dependências devem trazer o lock correspondente e passar nos
checks. A instalação por pip está descrita no [guia do usuário](INSTALACAO.md).

## Construir e verificar

```bash
uv build --out-dir .runtime/dist
uv run --frozen --no-sync python tools/ci_install_wheel.py
uv run --frozen --no-sync python tools/third_party_sources.py
uv run --frozen --no-sync python tools/package_desktop.py
uv run --frozen --no-sync python tools/ci_install_wheel.py --frozen
```

A verificação do wheel usa um ambiente separado, compara arquivos instalados
com a fonte e exercita a interface e o driver Playwright. A opção `--frozen`
também confere recursos da distribuição desktop. Os relatórios ficam em
.runtime/validation/. `STOPOTS_BUILD_ROOT` permite escolher outra pasta de saída.

Em Linux sem sessão gráfica, configure QT_QPA_PLATFORM=offscreen. O script
`tools/setup_ci_linux.sh` prepara bibliotecas do runner GitHub Actions; para uso
normal, as dependências do aplicativo são resolvidas pelo pacote .deb.

## Testes

Os testes puros verificam contratos, políticas, taxonomia e persistência. Os
testes de navegador usam DOMs locais ou respostas roteadas e não entram em
salas públicas. Os testes reais são explícitos e ficam fora da suíte automática.

O [laboratório](LABORATORIO.md) oferece cenários privados controlados.
`tools/validate_desktop_live.py` exercita a interface real. Para verificar a
distribuição, execute pelo Python de `.runtime/installed`, sem `PYTHONPATH` e com
STOPOTS_EXPECT_INSTALLED=1. O relatório deve identificar o pacote usado, o
resultado final e a limpeza dos recursos criados.

O código Selenium em `stopots_bot/` e o JavaScript legado não integram o wheel.
Scripts de conveniência do desenvolvimento não substituem o executável
instalado para a validação de uma release. Consulte [publicação](RELEASE.md)
antes de distribuir os pacotes.
