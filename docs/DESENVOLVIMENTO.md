# Desenvolvimento

Requisitos: Python 3.12, `uv` 0.11.16 e Chrome local. Na raiz:

```bash
uv sync --frozen --extra desktop --extra test --group build --group audit
uv run --frozen --no-sync python tools/check_metadata.py
uv run --frozen --no-sync pytest -q
uv run --frozen --no-sync stopots-assistente --verificar-ui
uv build --out-dir .runtime/dist
uv run --frozen --no-sync python tools/ci_install_wheel.py
uv run --frozen --no-sync python tools/third_party_sources.py
uv run --frozen --no-sync python tools/package_desktop.py
```

Após o sync completo, `--no-sync` preserva os extras e grupos já instalados.

O lock resolve dependências de runtime, desktop, build e auditoria. Atualizações
entram por PR com novo lock e verificações. `pip install '.[desktop]'` continua
disponível para usuários; o fluxo de desenvolvimento usa o lock.

Testes de navegador usam DOMs locais/roteados. Testes reais não fazem parte do
pytest automático. `tools/validate_desktop_live.py` cria cenário privado
controlado; execute somente quando houver objetivo de validação definido.
Para prova do wheel, invoque-o pelo Python de `.runtime/installed`, sem
PYTHONPATH e com `STOPOTS_EXPECT_INSTALLED=1`. O relatório identifica a origem e fica em `.runtime/validation/`.
No CI Linux, `tools/setup_ci_linux.sh` prepara as bibliotecas gráficas do runner;
o script é restrito ao GitHub Actions. Para uso comum no Ubuntu, o `.deb`
resolve essas dependências pelo gerenciador de pacotes.

`STOPOTS_BUILD_ROOT` direciona saídas. Os comandos em scripts/ são conveniência
de desenvolvimento; atalhos de usuário devem apontar ao pacote instalado.
O legado em stopots_bot/ e legacy/ não integra o wheel atual.
