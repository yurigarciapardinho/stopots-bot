from __future__ import annotations

import asyncio
from dataclasses import asdict
from importlib.resources import files
import os
from pathlib import Path
import signal
import sys
import threading

from .desktop_model import Invitation, Preferences
from .desktop_engine import DesktopEngine


def main(argv=None, on_ready=None):
    os.environ.setdefault('QT_QUICK_BACKEND', 'software')
    try:
        from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl, QTimer, QLockFile, Qt
        from PySide6.QtGui import QGuiApplication, QIcon
        from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
        from PySide6.QtQuickControls2 import QQuickStyle
    except ImportError:
        print('Instale o pacote com a opção desktop: pip install "stopots-bot[desktop]"', file=sys.stderr)
        return 2
    arguments = argv or sys.argv
    probe = '--verificar-ui' in arguments
    if os.environ.get('STOPOTS_RUNTIME'):
        data_root = Path(os.environ['STOPOTS_RUNTIME']).resolve()
    elif sys.platform == 'win32':
        data_root = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'StopotsAssistente'
    elif sys.platform == 'darwin':
        data_root = Path.home() / 'Library/Application Support/StopotsAssistente'
    else:
        data_root = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state'))) / 'stopots-assistente'
    directory = data_root / ('ui-probe/desktop' if probe else 'desktop')
    directory.mkdir(parents=True, exist_ok=True)
    if os.name != 'nt':
        directory.chmod(0o700)
    lock = QLockFile(str(directory / 'application.lock'))
    lock.setStaleLockTime(0)
    app = QGuiApplication(arguments)
    app.setApplicationName('StopotS Assistente')
    app.setOrganizationName('StopotsLocal')
    app.setDesktopFileName('stopots-assistente')
    if not lock.tryLock(100):
        print('O assistente já está aberto para esta sessão.', file=sys.stderr)
        if probe:
            return 3
        notice = QQmlApplicationEngine()
        notice.quit.connect(app.quit)
        notice.loadData('''import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ApplicationWindow {
 visible:true;width:440;height:220;title:"StopotS já aberto"
 ColumnLayout {
  anchors.fill:parent;anchors.margins:24;spacing:16
  Label {text:"O assistente já está aberto para esta sessão. Use a janela existente para controlar sua ajuda.";wrapMode:Text.WordWrap;Layout.fillWidth:true;font.pixelSize:16}
  Button {text:"Fechar aviso";Layout.fillWidth:true;onClicked:Qt.quit()}
 }
}'''.encode('utf-8'))
        return app.exec() if notice.rootObjects() else 3
    QQuickStyle.setStyle('Basic')
    from .ui_surface import OrganicSurface
    qmlRegisterType(OrganicSurface, 'Stopots.UI', 1, 0, 'OrganicSurface')
    diagnostic = None
    if probe and not on_ready:
        from .desktop_diagnostics import UiDiagnostic
        diagnostic = UiDiagnostic(directory.parent)
        on_ready = diagnostic.ready

    class Bridge(QObject):
        changed = Signal()
        incoming = Signal(dict)
        finished = Signal()
        sessionReady = Signal()

        def __init__(self):
            super().__init__()
            self.prefs = Preferences(directory / 'preferences.json')
            self.engine = DesktopEngine(directory, self.prefs.policy, self.incoming.emit)
            self._state = dict(self.engine.state)
            self._revision = 0
            self._closing = False
            self._can_exit = False
            self._activity = []
            self.incoming.connect(self.receive)
            self.finished.connect(self.workerFinished)
            self.thread = threading.Thread(target=self.work, daemon=True, name='stopots-session')
            self.thread.start()

        def work(self):
            try:
                asyncio.run(self.engine.main())
            except Exception:
                self.incoming.emit({'message': 'A ajuda foi encerrada por um erro', 'active': False,
                                    'detail': 'O Chrome permanece aberto. Reabra o assistente para retomar.'})
            finally:
                self.finished.emit()

        @Slot()
        def workerFinished(self):
            if self._closing:
                self._can_exit = True
                self.changed.emit()
                app.quit()
            else:
                self._state.update(active=False, busy=False, message='A ajuda foi interrompida',
                                   detail='Use Retomar ajuda para reconectar ao Chrome.')
                self.changed.emit()

        def ensureWorker(self):
            if not self.thread.is_alive():
                self.engine = DesktopEngine(directory, self.prefs.policy, self.incoming.emit)
                self.thread = threading.Thread(target=self.work, daemon=True, name='stopots-session')
                self.thread.start()
                self.engine.submit('policy', (self.prefs.policy, self._revision))

        @Slot(dict)
        def receive(self, state):
            ready = state.pop('ready', False)
            previous = self._state.get('message')
            self._state.update(state)
            if self._state.get('message') != previous:
                self._activity = ([self._state.get('message', '')] + self._activity)[:30]
            self.changed.emit()
            if ready:
                self.sessionReady.emit()

        @Property('QVariantMap', notify=changed)
        def state(self):
            return {**self._state, 'closing': self._closing, 'can_exit': self._can_exit,
                    'applying': self._state.get('revision', 0) < self._revision,
                    'activity': self._activity}

        @Property('QVariantMap', notify=changed)
        def preferences(self):
            return {'theme': self.prefs.theme, 'nickname': self.prefs.nickname,
                    'profile': self.prefs.profile, 'policy': asdict(self.prefs.policy),
                    'reduced_motion': self.prefs.reduced_motion}

        @Property(bool, notify=changed)
        def systemDark(self):
            return app.styleHints().colorScheme() == Qt.ColorScheme.Dark

        def policy(self):
            self.ensureWorker()
            self._revision += 1
            self.engine.submit('policy', (self.prefs.policy, self._revision))
            self.changed.emit()

        @Slot(str)
        def setProfile(self, name):
            if name != 'Personalizado':
                self.prefs.preset(name)
                self.policy()

        @Slot(str, bool)
        def setAction(self, name, enabled):
            self.prefs.action(name, enabled)
            self.policy()

        @Slot(str)
        def setTheme(self, theme):
            if theme in ('sistema', 'claro', 'escuro'):
                self.prefs.theme = theme
                self.prefs.save()
                self.changed.emit()

        @Slot(bool)
        def setReducedMotion(self, value):
            self.prefs.reduced_motion = value
            self.prefs.save()
            self.changed.emit()

        @Slot(str)
        def command(self, command):
            if command in ('pause', 'cancel') or (command in ('start', 'resume', 'open') and not self._state.get('busy')):
                self.ensureWorker()
                self.engine.submit(command)

        @Slot(str, str, bool, str, bool)
        def invite(self, url, nickname, has_password, password, replace_room):
            if self._state.get('busy'):
                return
            try:
                request = Invitation(url, nickname, has_password, password).validate()
                self.prefs.nickname = nickname
                self.prefs.save()
                self.ensureWorker()
                self._state.update(busy=True, message='Entrando na sala…', error_code='')
                self.changed.emit()
                self.engine.submit('invite', (request, replace_room))
            except ValueError as exc:
                self._state.update(message=str(exc), detail='Confira o formulário.', error_code='INPUT_ERROR')
                self.changed.emit()

        @Slot(bool)
        def shutdown(self, close_game=False):
            if self._closing:
                return
            self._closing = True
            self._state.update(message='Encerrando a ajuda…', active=False)
            self.changed.emit()
            if self.thread.is_alive():
                self.engine.submit('close_game' if close_game else 'quit')
            else:
                self.workerFinished()

    bridge = Bridge()
    app.styleHints().colorSchemeChanged.connect(lambda *_: bridge.changed.emit())
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('backend', bridge)
    assets = files('stopots_v2').joinpath('ui')
    app.setWindowIcon(QIcon(str(assets.joinpath('icon.svg'))))
    engine.load(QUrl.fromLocalFile(str(assets.joinpath('Main.qml'))))
    if not engine.rootObjects():
        bridge.shutdown(False)
        bridge.thread.join(5)
        return 2
    if on_ready:
        QTimer.singleShot(200, lambda: on_ready(app, bridge, engine.rootObjects()[0]))
    timer = QTimer(); timer.start(300); timer.timeout.connect(lambda: None)
    signal.signal(signal.SIGINT, lambda *_: bridge.shutdown(False))
    result = app.exec()
    bridge.engine.stop.set()
    bridge.engine.active.clear()
    bridge.thread.join(5)
    lock.unlock()
    return result or (1 if diagnostic and not diagnostic.passed else 0)


if __name__ == '__main__':
    raise SystemExit(main())
