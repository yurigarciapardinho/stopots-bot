# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
from __future__ import annotations

import asyncio
from importlib.resources import files
import time
import re

from ..domain import Phase
from ..normalization import utf16_length

ENTRY_SNAPSHOT = files('stopots_v2').joinpath('adapters/entry.js').read_text(encoding='utf-8')


class EntryError(ValueError):
    def __init__(self, message, code='ENTRY_ERROR'):
        super().__init__(message)
        self.code = code


async def enter_invitation(page, request, port, cancelled=lambda: False, timeout=50):
    """Entrada pela UI. O segredo não integra estado público nem eventos."""
    end = time.monotonic() + timeout
    try:
        request.validate()
        if cancelled():
            raise asyncio.CancelledError
        await page.goto('https://stopots.com/pt', wait_until='domcontentloaded', timeout=25000)
        nickname = page.locator('input[maxlength="15"]').filter(visible=True)
        await nickname.wait_for(state='visible', timeout=15000)
        if cancelled():
            raise asyncio.CancelledError
        await nickname.fill(request.nickname, timeout=3000)
        await page.goto(request.url, wait_until='domcontentloaded', timeout=25000)
        submitted = set()
        nickname_done = False
        while time.monotonic() < end:
            if cancelled():
                raise asyncio.CancelledError
            if not re.fullmatch(r'https://stopots\.com/pt(?:/(?:[0-9]+|game))?/?',page.url):
                raise EntryError('O convite abriu outra página. Confira o Chrome antes de continuar.')
            obs = await port.observe()
            if obs.connected and obs.phase in (Phase.ROOM, Phase.COUNTDOWN, Phase.WRITING,
                                                Phase.REVIEW, Phase.ROUND_RESULT, Phase.FINAL_RESULT):
                return obs
            state = await page.evaluate(ENTRY_SNAPSHOT)
            code = state.get('error')
            if code:
                messages = {'PASSWORD_REJECTED': 'A senha não foi aceita. Confira e tente novamente.',
                            'ROOM_UNAVAILABLE': 'A sala não está disponível ou está cheia.',
                            'UNKNOWN_NOTICE': 'O jogo mostrou um aviso. Confira o Chrome antes de continuar.'}
                raise EntryError(messages[code], code)
            if state.get('button') and not nickname_done:
                current_name=page.locator('input[maxlength="15"]').filter(visible=True)
                if await current_name.count()==1:
                    await current_name.fill(request.nickname,timeout=3000)
                    if await current_name.input_value()!=request.nickname:
                        raise EntryError('O jogo modificou o apelido. Confira o formato aceito.')
                    nickname_done=True
                    state=await page.evaluate(ENTRY_SNAPSHOT)
            password = state.get('password')
            if password and not request.has_password:
                raise EntryError('Esta sala pede senha. Informe a senha para entrar.', 'PASSWORD_REQUIRED')
            signature = ('password' if password else 'invitation', state.get('button'))
            if state.get('button') and signature not in submitted:
                if password:
                    maximum = state.get('max_length', -1)
                    if maximum >= 0 and utf16_length(request.password) > maximum:
                        raise EntryError(f'A senha excede o limite de {maximum} caracteres do jogo.')
                    target = page.locator(password)
                    await target.fill(request.password, timeout=3000)
                    if await target.input_value() != request.password:
                        raise EntryError('O jogo modificou a senha digitada. Confira o formato aceito.')
                button = page.locator(state['button'])
                if await button.count() != 1 or not await button.is_enabled():
                    await asyncio.sleep(.15)
                    continue
                submitted.add(signature)
                await button.click(timeout=4000)
            await asyncio.sleep(.2)
        raise EntryError('A entrada não foi confirmada. Confira o jogo e tente novamente.', 'ENTRY_TIMEOUT')
    finally:
        request.password = ''
