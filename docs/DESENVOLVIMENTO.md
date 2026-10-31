# Desenvolvimento

Requisitos: Python 3.12, `uv` 0.11.16 e Chrome local. Na raiz:

```bash
uv sync --frozen --extra desktop --extra test --group build --group audit
uv run --frozen python tools/check_metadata.py
uv run --frozen pytest -q
uv run --frozen --extra desktop stopots-assistente --verificar-ui
uv build --out-dir .runtime/dist
uv run --frozen --extra desktop --group build python tools/ci_install_wheel.py
uv run --frozen --extra desktop python tools/third_party_sources.py
uv run --frozen --extra desktop --group build python tools/package_desktop.py
```

O lock resolve dependências de runtime, desktop, build e auditoria. Atualizações
entram por PR com novo lock e verificações. `pip install '.[desktop]'` continua
disponível para usuários; o fluxo de desenvolvimento usa o lock.

Testes de navegador usam DOMs locais/roteados. Testes reais não fazem parte do
pytest automático. `tools/validate_desktop_live.py` cria cenário privado
controlado; execute somente quando houver objetivo de validação definido.
Para prova do wheel, invoque-o pelo Python de `.runtime/installed`, sem
PYTHONPATH e com `STOPOTS_EXPECT_INSTALLED=1`. O relatório identifica a origem.

`STOPOTS_BUILD_ROOT` direciona saídas. Os comandos em scripts/ são conveniência
de desenvolvimento; atalhos de usuário devem apontar ao pacote instalado.
O legado em stopots_bot/ e legacy/ não integra o wheel atual.
