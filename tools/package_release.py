"""Build por plataforma com inventário e avisos de redistribuição."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from stopots_v2 import __version__

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('STOPOTS_BUILD_ROOT', ROOT / '.runtime')).resolve()

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=BUILD / 'dist')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if not (BUILD / 'dist/THIRD_PARTY_SOURCES.json').is_file():
        raise RuntimeError('Execute tools/third_party_sources.py antes de distribuir bibliotecas Qt')
    BUILD.mkdir(parents=True, exist_ok=True)
    spec = BUILD / 'StopotsAssistente.spec'
    spec.write_text(
        'import sys\nfrom PyInstaller.utils.hooks import collect_data_files, copy_metadata\n'
        "datas = collect_data_files('stopots_v2') + collect_data_files('playwright')\n"
        "for name in ('stopots-bot','PySide6_Essentials','shiboken6','playwright'): datas += copy_metadata(name)\n"
        f'a = Analysis([{str(ROOT / "tools/desktop_entry.py")!r}], pathex=[{str(ROOT / "src")!r}], '
        f'binaries=[], datas=datas, hiddenimports=["PySide6.QtQuickControls2"], hookspath=[{str(ROOT / "build_hooks")!r}], '
        'hooksconfig={}, runtime_hooks=[], excludes=["tkinter","readline"], noarchive=False)\n'
        'if sys.platform.startswith("linux"): a.exclude_system_libraries()\n'
        'pyz = PYZ(a.pure)\n'
        'exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="StopotsAssistente", '
        'debug=False, strip=False, upx=False, console=False)\n'
        'coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="StopotsAssistente")\n'
    )
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
               '--distpath', str(output / 'portable'), '--workpath', str(BUILD / 'pyinstaller'), str(spec)]
    with (output / 'build.log').open('w') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print((output / 'build.log').read_text()[-10000:])
        return result.returncode
    app = output / 'portable/StopotsAssistente'
    legal = app / 'legal'
    legal.mkdir(exist_ok=True)
    for name in ('LICENSE', 'AUTHORS.md', 'CREDITS.md', 'THIRD_PARTY_NOTICES.md'):
        shutil.copy2(ROOT / name, legal / name)
    shutil.copytree(ROOT / 'LICENSES', legal / 'LICENSES', dirs_exist_ok=True)
    shutil.copy2(ROOT / 'docs/LICENCIAMENTO.md', legal / 'LICENCIAMENTO.md')
    shutil.copy2(BUILD / 'dist/THIRD_PARTY_SOURCES.json', legal / 'THIRD_PARTY_SOURCES.json')
    shutil.copytree(BUILD / 'third-party-notices', legal / 'qt-source-notices', dirs_exist_ok=True)
    if sys.platform.startswith('linux'):
        for package in ('python3.12','libpython3.12-stdlib','libpython3.12-minimal','libpython3.12t64'):
            source = Path('/usr/share/doc') / package / 'copyright'
            if source.is_file():
                target = legal / 'dependencies' / package / 'copyright'
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,target)
    for name in ('playwright', 'greenlet', 'pyee', 'typing_extensions', 'shiboken6', 'PySide6_Essentials', 'PyInstaller'):
        dist = importlib.metadata.distribution(name)
        for item in dist.files or []:
            if any(term in item.name.lower() for term in ('license', 'copying', 'copyright', 'notice')):
                source = Path(dist.locate_file(item))
                if source.is_file():
                    target = legal / 'dependencies' / name / str(item)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    import PyInstaller
    for source in (Path(PyInstaller.__file__).parent / 'COPYING.txt', Path(sys.base_prefix) / 'LICENSE.txt'):
        if source.is_file():
            shutil.copy2(source, legal / ('PyInstaller-COPYING.txt' if 'PyInstaller' in str(source) else 'Python-LICENSE.txt'))
    forbidden = ('Qt6Charts', 'Qt6Graphs', 'Qt6DataVisualization', 'Qt6VirtualKeyboard', 'Qt6WebEngine')
    bad = [p.name for p in app.rglob('*') if p.is_file() and any(x in p.name for x in forbidden)]
    if bad:
        raise RuntimeError('Módulos Qt fora do conjunto aprovado: ' + ', '.join(bad))
    inventory = {str(p.relative_to(app)): {'bytes': p.stat().st_size, 'sha256': digest(p)}
                 for p in sorted(app.rglob('*')) if p.is_file() and not p.is_symlink()}
    (legal / 'FILES.json').write_text(json.dumps(inventory, indent=2) + '\n')
    arch = 'x86_64' if platform.machine().lower() in ('amd64', 'x86_64') else platform.machine().lower()
    if sys.platform == 'win32':
        archive = Path(shutil.make_archive(str(output / f'stopots-assistente-{__version__}-windows-{arch}'), 'zip', app.parent, app.name))
    elif sys.platform.startswith('linux'):
        archive = output / f'stopots-assistente-{__version__}-linux-{arch}.tar.gz'
        with tarfile.open(archive, 'w:gz', compresslevel=6) as stream:
            stream.add(app, arcname=app.name)
    else:
        raise RuntimeError('Empacotamento desta plataforma ainda não validado')
    artifacts = [archive]
    if sys.platform.startswith('linux') and shutil.which('dpkg-deb'):
        if arch != 'x86_64':
            raise RuntimeError('Pacote deb atualmente limitado a amd64')
        stage = BUILD / 'deb'
        if stage.exists():
            shutil.rmtree(stage)
        (stage / 'DEBIAN').mkdir(parents=True)
        deps = 'libegl1, libgl1, libfontconfig1, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render-util0, libxcb-shape0, libxcb-sync1, libxcb-xfixes0, libxcb-xinerama0, libxcb-xkb1, libdbus-1-3, libglib2.0-0t64, libstdc++6, libgcc-s1, zlib1g, libexpat1, libbz2-1.0, liblzma5, libffi8, libssl3t64, libsqlite3-0, libuuid1'
        (stage / 'DEBIAN/control').write_text(f'Package: stopots-assistente\nVersion: {__version__}\nArchitecture: amd64\nMaintainer: Yuri Garcia Pardinho\nHomepage: https://github.com/yurigarciapardinho/stopots-bot\nDepends: {deps}\nDescription: Assistente local do StopotS em portugues\n')
        shutil.copytree(app, stage / 'opt/stopots-assistente', symlinks=True)
        launch = stage / 'usr/bin/stopots-assistente'
        launch.parent.mkdir(parents=True)
        launch.write_text('#!/bin/sh\nexec /opt/stopots-assistente/StopotsAssistente "$@"\n')
        launch.chmod(0o755)
        icon = stage / 'usr/share/icons/hicolor/scalable/apps/stopots-assistente.svg'
        icon.parent.mkdir(parents=True)
        shutil.copy2(ROOT / 'src/stopots_v2/ui/icon.svg', icon)
        desktop = stage / 'usr/share/applications/stopots-assistente.desktop'
        desktop.parent.mkdir(parents=True)
        desktop.write_text('[Desktop Entry]\nType=Application\nName=StopotS Assistente\nComment=Sua ajuda, do seu jeito\nExec=stopots-assistente\nIcon=stopots-assistente\nTerminal=false\nCategories=Game;\nStartupWMClass=StopotS Assistente\n')
        shutil.copytree(legal, stage / 'usr/share/doc/stopots-assistente')
        deb = output / f'stopots-assistente_{__version__}_amd64.deb'
        subprocess.run(['dpkg-deb', '--root-owner-group', '-Zgzip', '-z6', '--build', str(stage), str(deb)], check=True)
        artifacts.append(deb)
    manifest = {'version': __version__, 'platform': sys.platform, 'architecture': arch,
                'files': {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size} for p in artifacts},
                'qt_policy': 'PySide6-Essentials, QML permitido, bibliotecas dinamicas'}
    (output / 'DESKTOP_MANIFESTO.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest, ensure_ascii=False), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
