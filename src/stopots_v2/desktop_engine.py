# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
from __future__ import annotations

import asyncio
from dataclasses import asdict
from pathlib import Path
import threading
import time
import queue

from .application import Controller, EventLog
from .adapters.chrome_session import ChromeSession
from .adapters.invitation import EntryError, enter_invitation
from .adapters.web import StopotsWeb
from .domain import Phase
from .vocabulary import Vocabulary


class DesktopEngine:
    """Executor serial; a janela conversa por comandos, sem acessar Playwright."""

    def __init__(self, directory: Path, policy, emit, headless=False):
        self.directory, self.policy, self.emit = directory, policy, emit
        self.chrome = ChromeSession(directory, headless=headless)
        self.stop = threading.Event()
        self.active = threading.Event()
        self.driver_ready = threading.Event()
        self.loop = self.task = self.entry_task = None
        self.queue = queue.SimpleQueue()
        self.entry_cancelled = threading.Event()
        self.port = self.controller = None
        self.vocabulary = None
        self.revision = 0
        self.final_seen = set()
        self.last_phase = None
        self.unknown_since = None
        self.state = {'connected': False, 'active': False, 'busy': False, 'phase': '',
                      'message': 'Pronto para começar', 'detail': 'Escolha sua ajuda e abra o jogo.',
                      'filled': 0, 'total': 0, 'letter': '—', 'round': '—', 'pending': [],
                      'revision': 0, 'error_code': '', 'in_room': False, 'ranking': [], 'ranking_scope': ''}

    def publish(self, **values):
        ready=values.pop('ready',False)
        self.state.update(values)
        self.state['active'] = self.active.is_set()
        self.emit({**self.state, **({'ready': True} if ready else {})})

    def submit(self, command, payload=None):
        if command == 'invite':
            self.entry_cancelled.clear()
        if command in ('pause', 'cancel', 'quit', 'close_game'):
            self.active.clear()
            self.entry_cancelled.set()
            if self.entry_task and self.loop:
                self.loop.call_soon_threadsafe(self.entry_task.cancel)
        if command == 'quit':
            self.stop.set()
        self.queue.put((command, payload))
        if command == 'quit' and self.task and self.loop:
            self.loop.call_soon_threadsafe(self.task.cancel)

    async def ensure(self, pw):
        if self.chrome.browser and self.chrome.browser.is_connected() and self.chrome.page and not self.chrome.page.is_closed():
            return
        if self.port:
            await self.port.close()
        page = await self.chrome.connect(pw)
        self.port = StopotsWeb(page)
        self.controller = Controller(self.port, self.vocabulary, self.policy,
                                     EventLog(self.directory / 'events.jsonl'))
        self.controller.paused = lambda: not self.active.is_set()
        self.publish(connected=True)

    async def handle(self, pw, command, payload):
        if command == 'policy':
            self.policy, self.revision = payload
            if self.controller:
                self.controller.planner.policy = self.policy
            self.publish(revision=self.revision)
        elif command in ('pause', 'cancel'):
            self.active.clear()
            self.publish(message='Ajuda pausada', detail='Você continua no controle do jogo.')
        elif command in ('start', 'resume', 'open'):
            self.publish(busy=True, error_code='', message='Conectando ao jogo…')
            await self.ensure(pw)
            if self.chrome.page.url == 'about:blank':
                await self.chrome.page.goto('https://stopots.com/pt', wait_until='domcontentloaded', timeout=30000)
            if command != 'open':
                self.active.set()
            await self.chrome.page.bring_to_front()
            self.publish(busy=False, ready=command != 'open', message='Ajuda ativa' if self.active.is_set() else 'Ajuda pausada')
        elif command == 'invite':
            request, allow_replace = payload
            try:
                request.validate()
                if self.state['in_room'] and not allow_replace:
                    raise EntryError('Confirme a saída da sala atual antes de entrar em outro convite.')
                self.active.clear()
                self.publish(busy=True, error_code='', message='Entrando na sala…', detail='Conferindo o convite e a entrada no jogo.')
                await self.ensure(pw)
                self.entry_task = asyncio.create_task(enter_invitation(self.chrome.page, request, self.port,
                    lambda: self.stop.is_set() or self.entry_cancelled.is_set()))
                await self.entry_task
                self.active.set()
                self.publish(busy=False, ready=True, message='Entrada confirmada', detail='A ajuda começa quando a fase permitir.')
            except asyncio.CancelledError:
                if self.stop.is_set():
                    raise
                self.publish(busy=False, message='Entrada cancelada', detail='O Chrome permanece aberto.')
            finally:
                self.entry_task = None
                request.password = ''
        elif command == 'close_game':
            await self.chrome.close_game()
            self.stop.set()
        elif command == 'quit':
            self.stop.set()

    async def tick(self):
        from playwright.async_api import Error
        if not self.controller:
            return
        try:
            obs, result = await self.controller.step()
        except (Error, OSError, TimeoutError):
            self.active.clear()
            self.publish(connected=False, busy=False, message='Conexão interrompida',
                         detail='A ajuda está suspensa. Confira o Chrome e use Retomar ajuda.')
            return
        self.last_phase = obs.phase
        if obs.phase == Phase.CLOSED:
            self.active.clear()
            self.publish(connected=False, message='Chrome fechado', detail='Use Abrir jogo para começar novamente.', in_room=False)
            return
        if not obs.connected:
            self.active.clear()
        if obs.phase == Phase.UNKNOWN:
            self.unknown_since = self.unknown_since or time.monotonic()
            if time.monotonic() - self.unknown_since > 45:
                self.active.clear()
        else:
            self.unknown_since = None
        key = (obs.context.session_id, obs.context.room_epoch, obs.context.match_epoch)
        if obs.phase == Phase.FINAL_RESULT and key not in self.final_seen:
            self.final_seen.add(key)
            self.active.clear()
        pending = []
        if obs.phase == Phase.WRITING and obs.fields_stable:
            for f in obs.fields:
                if not f.value.strip() and not self.vocabulary.choose(f.label, obs.letter, f.max_length, self.policy.seed):
                    pending.append(f.label)
        message, detail = self.message(obs)
        ranking = [{'player': p, 'points': score} for p, score in obs.ranking.rows] if obs.ranking else []
        if self.state.get('error_code'):
            message, detail = self.state['message'], self.state['detail']
        self.publish(connected=obs.connected, phase=str(obs.phase),
                     message=message, detail=detail, filled=sum(bool(f.value.strip()) for f in obs.fields),
                     total=len(obs.fields), letter=obs.letter or '—',
                     round=f'{obs.context.round_index}/{obs.total_rounds}' if obs.context.round_index and obs.total_rounds else '—',
                     pending=pending, in_room=obs.phase not in (Phase.HOME, Phase.ENTERING, Phase.UNKNOWN, Phase.CLOSED),
                     ranking=ranking, ranking_scope=obs.ranking.scope if obs.ranking else '',
                     last_action=str(result.status) if result else self.state.get('last_action', ''))

    def message(self, obs):
        if not obs.connected:
            return 'Conexão interrompida', 'Confira o Chrome antes de retomar a ajuda.'
        if obs.phase == Phase.FINAL_RESULT and not self.active.is_set():
            return 'Partida encerrada · Ajuda pausada', 'Chrome permanece aberto. Retome a ajuda quando quiser.'
        if not self.active.is_set():
            return 'Ajuda pausada', 'Você pode continuar jogando manualmente.'
        if obs.notice:
            return 'Confira o aviso no jogo', 'A ajuda aguarda a resolução do aviso.'
        if obs.phase == Phase.REVIEW and not self.policy.confirm_review:
            return 'Sua vez de avaliar', 'Avalie as respostas e confirme pelo jogo.'
        if obs.phase == Phase.ROUND_RESULT and not self.policy.continue_results:
            return 'Resultado da rodada', 'Continue pelo jogo quando estiver pronto.'
        if obs.phase == Phase.WRITING:
            return ('Preenchendo campos vazios' if self.policy.fill_blanks and not self.policy.observe_only else 'Acompanhando a rodada',
                    'Suas respostas e edições são preservadas.')
        if obs.phase == Phase.UNKNOWN:
            return 'Aguardando a interface', 'Ações dependem de uma tela reconhecida do jogo.'
        return 'Aguardando partida', 'Escolha ou inicie uma partida pelo Chrome.'

    async def main(self):
        from playwright.async_api import async_playwright, Error
        self.loop, self.task = asyncio.get_running_loop(), asyncio.current_task()
        self.vocabulary = Vocabulary.bundled()
        try:
            async with async_playwright() as pw:
                self.driver_ready.set()
                if not self.stop.is_set() and await asyncio.to_thread(self.chrome.endpoint):
                    await self.ensure(pw)  # reabertura observa, mas não retoma silenciosamente
                while not self.stop.is_set():
                    try:
                        command, payload = self.queue.get_nowait()
                    except queue.Empty:
                        await asyncio.sleep(.15)
                        command = None
                    if command:
                        try:
                            await self.handle(pw, command, payload)
                        except (EntryError, ValueError, FileNotFoundError) as exc:
                            self.active.clear()
                            self.publish(busy=False, message=str(exc), detail='Confira os dados e tente novamente.',
                                         error_code=getattr(exc, 'code', 'INPUT_ERROR'))
                        except (Error, OSError, TimeoutError):
                            self.active.clear()
                            self.publish(busy=False, message='Não consegui concluir a conexão',
                                         detail='Confira o Chrome e tente novamente.', error_code='CONNECTION_ERROR')
                    if not self.stop.is_set() and self.queue.empty():
                        await self.tick()
        except asyncio.CancelledError:
            pass
        finally:
            self.active.clear()
            self.driver_ready.clear()
            if self.port:
                await self.port.close()
            # Não chama context.close/browser.close: Chrome pertence à sessão do usuário.
