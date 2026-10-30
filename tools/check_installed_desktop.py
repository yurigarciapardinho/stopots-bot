"""Invocar pelo Python do wheel instalado, fora do diretório do projeto."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import zipfile

import stopots_v2

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT.parent/'.runtime'
DIST=RUNTIME/'dist-desktop'


def main():
    installed=Path(stopots_v2.__file__).resolve().parent
    source=ROOT/'src/stopots_v2'
    assert 'site-packages' in installed.parts and installed!=source
    wheel=DIST/'stopots_bot-2.1.0-py3-none-any.whl'
    hashes={}
    with zipfile.ZipFile(wheel) as archive:
        for p in source.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix not in ('.py','.js','.json','.qml','.svg'):continue
            rel=p.relative_to(source)
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            assert hashlib.sha256((installed/rel).read_bytes()).hexdigest()==digest,str(rel)
            assert hashlib.sha256(archive.read('stopots_v2/'+rel.as_posix())).hexdigest()==digest,str(rel)
            hashes[rel.as_posix()]=digest
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    env.update(STOPOTS_RUNTIME=str(RUNTIME/'wheel-ui-test'),QT_QPA_PLATFORM='offscreen')
    c=subprocess.run([sys.executable,'-m','stopots_v2.desktop','--verificar-ui'],cwd=RUNTIME,env=env,text=True,capture_output=True,timeout=40)
    assert c.returncode==0,c.stdout+'\n'+c.stderr
    assets=DIST/'portable/StopotsAssistente/_internal/stopots_v2'
    for rel,digest in hashes.items():
        if Path(rel).suffix!='.py':assert hashlib.sha256((assets/rel).read_bytes()).hexdigest()==digest,rel
    report={'version':stopots_v2.__version__,'installed_wheel':True,'runtime_files_matched':len(hashes),
            'runtime_source_sha256':hashes,'frozen_assets_match':True,'installed_gui_exit':c.returncode,
            'playwright':importlib.metadata.version('playwright'),'pyside6':importlib.metadata.version('PySide6'),
            'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in DIST.iterdir() if p.suffix in ('.deb','.whl') or p.name.endswith('.tar.gz')}}
    (ROOT/'evidence/v2/DESKTOP_PACOTE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='runtime_source_sha256'}),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
