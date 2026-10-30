from pathlib import Path
import json
import sys
import time
from PySide6.QtCore import QTimer, qInstallMessageHandler


class UiDiagnostic:
    """Autoverificação das telas distribuídas, sem entrar em jogo ou abrir Chrome."""
    def __init__(self, directory):
        self.directory=Path(directory)
        self.errors=[];self.frames=[];self.passed=False
        qInstallMessageHandler(self.message)

    def message(self, kind, context, text):
        print(text,file=sys.stderr,flush=True)
        if any(x in text for x in ['ReferenceError','TypeError','Binding loop','Cannot assign','Unable to assign','is not a type','Invalid property','failed to load']):
            self.errors.append(text)

    def ready(self, app, bridge, window):
        started=time.monotonic()
        bridge.receive({'error_code':'PASSWORD_REJECTED','message':'Senha recusada — cenário local'})
        window.setProperty('tab',1)
        bridge.receive({'error_code':'PASSWORD_REJECTED'})
        if window.property('tab')!=1:self.errors.append('Erro de entrada impede navegar nos ajustes')
        bridge.receive({'error_code':'','message':'Pronto para começar'})
        steps=[('claro',False,0),('escuro',False,1),('escuro',True,1),('claro',False,2)]
        def step(i):
            if i==len(steps):
                driver_ready=bridge.engine.driver_ready.is_set()
                if not driver_ready and time.monotonic()-started<15:
                    QTimer.singleShot(150,lambda:step(i));return
                self.passed=not self.errors and len(self.frames)==4 and driver_ready
                report={'passed':self.passed,'frames':self.frames,'qml_errors':self.errors,'driver_ready':driver_ready,'online':False}
                self.directory.mkdir(parents=True,exist_ok=True)
                (self.directory/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
                print(json.dumps(report,ensure_ascii=False),flush=True)
                bridge.shutdown(False);return
            theme,compact,tab=steps[i]
            bridge.setTheme(theme);window.setProperty('compact',compact);window.setProperty('tab',tab)
            window.setProperty('entryMode',1);window.setProperty('passwordChoice',1)
            def check():
                try:
                    image=window.grabWindow()
                    assert not image.isNull(),'Janela sem renderização'
                    assert window.height()<=760,'Janela excedeu a altura lógica planejada'
                    assert window.property('accentInk').name()==('#163136' if theme=='escuro' else '#ffffff'),'Cor do texto primário incorreta'
                    accent=(121,209,214) if theme=='escuro' else (23,102,120)
                    matches=0
                    for y in range(0,image.height(),4):
                        for x in range(0,image.width(),4):
                            color=image.pixelColor(x,y)
                            if sum(abs(a-b) for a,b in zip(accent,(color.red(),color.green(),color.blue())))<9:matches+=1
                    assert matches>300,'As ações principais perderam a cor de destaque'
                    self.frames.append({'theme':theme,'compact':compact,'width':image.width(),'height':image.height(),'logical_height':window.height(),'dpr':image.devicePixelRatio()})
                except Exception as exc:self.errors.append(str(exc))
                QTimer.singleShot(50,lambda:step(i+1))
            QTimer.singleShot(250,check)
        step(0)
