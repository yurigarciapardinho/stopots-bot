"""CLI distribuída anexada a uma página local simulada; sem jogo na rede."""
import asyncio
import socket

import pytest

from stopots_v2.cli import execute, parser

pytestmark = pytest.mark.browser


def test_cli_attaches_to_unique_page_and_preserves_browser(tmp_path, monkeypatch):
    monkeypatch.setenv('STOPOTS_RUNTIME', str(tmp_path))
    async def scenario():
        from playwright.async_api import async_playwright
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(channel='chrome', headless=True, args=[f'--remote-debugging-port={port}'])
            try:
                page = await browser.new_page()
                await page.route('**/*', lambda route: route.fulfill(content_type='text/html', body='<section class="ranking"><h2>RANKING FINAL</h2><div class="userRkg"><span class="nick">Jogador sintético</span><span class="points">260</span></div></section>'))
                url = 'https://stopots.com/pt/1234567'
                await page.goto(url)
                args = parser().parse_args(['executar', '--cdp', f'http://127.0.0.1:{port}', '--url', url, '--tempo-limite', '5'])
                result = await execute(args)
                assert result['status'] == 'concluido' and result['final_result_verified']
                assert not page.is_closed() and browser.is_connected()
            finally:
                await browser.close()
    asyncio.run(scenario())
