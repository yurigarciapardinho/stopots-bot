# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request


def chrome_executable():
    for name in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'):
        if found := shutil.which(name):
            return found
    candidates = [Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')]
    for key in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
        if os.environ.get(key):
            candidates.append(Path(os.environ[key]) / 'Google/Chrome/Application/chrome.exe')
    for p in candidates:
        if p.is_file():
            return str(p)
    raise FileNotFoundError('Instale o Google Chrome para abrir o jogo.')


class ChromeSession:
    """Chrome dedicado independente da UI; parar Playwright apenas desanexa."""

    def __init__(self, directory: Path, headless=False):
        self.directory = directory.resolve()
        self.profile = self.directory / 'chrome-profile'
        self.headless = headless
        self.browser = self.page = None
        self.process = None

    def endpoint(self):
        try:
            lines = (self.profile / 'DevToolsActivePort').read_text().splitlines()
            port = int(lines[0])
            if not 0 < port < 65536 or not lines[1].startswith('/devtools/browser/'):
                return None
            endpoint = f'http://127.0.0.1:{port}'
            with urllib.request.urlopen(endpoint + '/json/version', timeout=.5) as response:
                data = json.load(response)
            if not data.get('webSocketDebuggerUrl', '').endswith(lines[1]):
                return None
            return endpoint
        except (OSError, ValueError, IndexError):
            return None

    async def connect(self, playwright):
        self.profile.mkdir(parents=True, exist_ok=True)
        if os.name != 'nt':
            self.directory.chmod(0o700)
            self.profile.chmod(0o700)
        endpoint = await asyncio.to_thread(self.endpoint)
        if not endpoint:
            # Perfil próprio: nenhum processo externo é anexado por descoberta global.
            args = [chrome_executable(), '--user-data-dir=' + str(self.profile),
                    '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
                    '--no-first-run', '--no-default-browser-check']
            if self.headless:
                args.append('--headless=new')
            args.append('about:blank')
            env = os.environ.copy()
            temporary = Path(env.get('TMPDIR', str(self.directory / 'tmp')))
            temporary.mkdir(parents=True, exist_ok=True)
            env['TMPDIR'] = str(temporary)
            with (self.directory / 'chrome.log').open('ab') as output:
                self.process = subprocess.Popen(args, stdout=output, stderr=output, env=env,
                                                start_new_session=os.name != 'nt')
            for _ in range(100):
                endpoint = await asyncio.to_thread(self.endpoint)
                if endpoint:
                    break
                if self.process.poll() is not None:
                    raise OSError('O Chrome não abriu. Confira se este perfil já está em uso.')
                await asyncio.sleep(.1)
            else:
                raise TimeoutError('Não consegui conectar ao Chrome dedicado.')
        self.browser = await playwright.chromium.connect_over_cdp(endpoint, timeout=10000, no_defaults=True)
        pages = [p for c in self.browser.contexts for p in c.pages if not p.url.startswith('devtools:')]
        matches = [p for p in pages if p.url.startswith('https://stopots.com/pt')]
        if len(matches) > 1:
            raise ValueError('Há várias abas do StopotS neste Chrome. Deixe apenas a que deseja usar.')
        blank = next((p for p in pages if p.url == 'about:blank'), None)
        self.page = matches[0] if matches else (blank or await self.browser.contexts[0].new_page())
        return self.page

    async def close_game(self):
        if self.browser and self.browser.is_connected():
            from playwright.async_api import Error
            try:
                cdp = await self.browser.new_browser_cdp_session()
                await cdp.send('Browser.close')
            except Error:
                pass  # o alvo pode fechar antes da resposta
        self.browser = self.page = None
