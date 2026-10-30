"""Reprodução visual local, sem conectar ao jogo. Imagens ficam no runtime."""
from pathlib import Path
import os
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('STOPOTS_UI_TEST_RUNTIME', ROOT.parent / '.runtime/ui-check'))
os.environ['STOPOTS_RUNTIME'] = str(RUNTIME)
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
sys.path.insert(0, str(ROOT / 'src'))

from PySide6.QtCore import QTimer, QObject, qInstallMessageHandler
from stopots_v2.desktop import main

errors = []
frames = []


def message(kind, context, text):
    if any(term in text for term in ('ReferenceError', 'TypeError', 'Cannot assign', 'Unable to assign', 'is not a type', 'failed to load', 'Binding loop')):
        errors.append(text)
    print(text, flush=True)


def ready(app, bridge, window):
    steps = [('claro', False, 0), ('escuro', False, 1), ('escuro', True, 1), ('claro', False, 2)]

    def step(index):
        if index == len(steps):
            result = {'frames': frames, 'qml_errors': errors, 'local_simulation': True,
                      'online_game_started': False}
            RUNTIME.mkdir(parents=True, exist_ok=True)
            (RUNTIME / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
            bridge.shutdown(False)
            return
        theme, compact, tab = steps[index]
        bridge.setTheme(theme)
        window.setProperty('compact', compact)
        window.setProperty('tab', tab)
        window.setProperty('entryMode', 1)
        window.setProperty('passwordChoice', 1)

        def capture():
            try:
                image = window.grabWindow()
                assert not image.isNull(), 'A janela não foi renderizada'
                RUNTIME.mkdir(parents=True, exist_ok=True)
                target = RUNTIME / f'frame-{index}.png'
                assert image.save(str(target))
                if index==0:
                    def inspect(item):
                        if item.property('text') in ('S','Retomar ajuda','Entrar por convite'):
                            color=item.property('color')
                            if color is not None:print('LABEL_COLOR',item.property('text'),color.name(),flush=True)
                        for child in item.childItems():inspect(child)
                    print('ACCENT_INK',window.property('accentInk').name(),flush=True)
                    inspect(window.contentItem())
                frames.append({'theme': theme, 'compact': compact, 'tab': tab,
                               'width': image.width(), 'height': image.height()})
                QTimer.singleShot(100, lambda: step(index + 1))
            except Exception as exc:
                errors.append(type(exc).__name__+': '+str(exc))
                print(errors[-1],flush=True)
                bridge.shutdown(False)
        QTimer.singleShot(350, capture)
    step(0)


if __name__ == '__main__':
    qInstallMessageHandler(message)
    code = main(['stopots-ui-check'], on_ready=ready)
    raise SystemExit(code or bool(errors) or len(frames) != 4)
