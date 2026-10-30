"""Gera distribuição Ubuntu e pasta portátil sem modificar instalação do sistema."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT.parent/'.runtime'
OUTPUT=RUNTIME/'dist-desktop'


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed',
             '--name','StopotsAssistente','--paths',str(ROOT/'src'),
             '--collect-data','stopots_v2','--collect-data','playwright',
             '--copy-metadata','stopots-bot','--copy-metadata','PySide6','--copy-metadata','PySide6_Essentials',
             '--copy-metadata','PySide6_Addons','--copy-metadata','shiboken6','--copy-metadata','playwright',
             '--hidden-import','PySide6.QtQuickControls2',
             '--distpath',str(OUTPUT/'portable'),'--workpath',str(RUNTIME/'build-desktop'),
             '--specpath',str(RUNTIME/'desktop-spec'),str(ROOT/'tools/desktop_entry.py')]
    log=OUTPUT/'build.log'
    with log.open('w') as stream:
        result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text()[-12000:]);return result.returncode
    app=OUTPUT/'portable/StopotsAssistente'
    from stopots_v2 import __version__
    archive=OUTPUT/f'stopots-assistente-{__version__}-linux-x86_64.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
        tar.add(app,arcname='StopotsAssistente')
    artifacts=[archive]
    if sys.platform.startswith('linux') and shutil.which('dpkg-deb'):
        staging=RUNTIME/'deb-desktop'
        if staging.exists():shutil.rmtree(staging)
        (staging/'DEBIAN').mkdir(parents=True)
        deps='libegl1, libgl1, libfontconfig1, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render-util0, libxcb-xinerama0, libxcb-xkb1, libdbus-1-3'
        (staging/'DEBIAN/control').write_text(f'Package: stopots-assistente\nVersion: {__version__}\nArchitecture: amd64\nMaintainer: Stopots Local\nDepends: {deps}\nDescription: Assistente local do StopotS em portugues\n')
        shutil.copytree(app,staging/'opt/stopots-assistente',symlinks=True)
        launch=staging/'usr/bin/stopots-assistente';launch.parent.mkdir(parents=True)
        launch.write_text('#!/bin/sh\nexec /opt/stopots-assistente/StopotsAssistente "$@"\n');launch.chmod(0o755)
        icon=staging/'usr/share/icons/hicolor/scalable/apps/stopots-assistente.svg';icon.parent.mkdir(parents=True)
        shutil.copy2(ROOT/'src/stopots_v2/ui/icon.svg',icon)
        desktop=staging/'usr/share/applications/stopots-assistente.desktop';desktop.parent.mkdir(parents=True)
        desktop.write_text('[Desktop Entry]\nType=Application\nName=StopotS Assistente\nComment=Sua ajuda, do seu jeito\nExec=stopots-assistente\nIcon=stopots-assistente\nTerminal=false\nCategories=Game;\nStartupWMClass=StopotS Assistente\n')
        license_path=staging/'usr/share/doc/stopots-assistente/copyright';license_path.parent.mkdir(parents=True)
        if (ROOT/'LICENSE').exists():shutil.copy2(ROOT/'LICENSE',license_path)
        deb=OUTPUT/f'stopots-assistente_{__version__}_amd64.deb'
        subprocess.run(['dpkg-deb','--root-owner-group','-Zgzip','-z1','--build',str(staging),str(deb)],check=True)
        artifacts.append(deb)
    manifest={'version':__version__,'files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in artifacts}}
    (OUTPUT/'MANIFESTO.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
