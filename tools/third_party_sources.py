"""Espelhar fontes Qt/PySide e avisos para acompanhar a distribuição LGPL."""
from pathlib import Path, PurePosixPath
import hashlib
import importlib.metadata
import json
import os
import tarfile
import urllib.request
from PySide6.QtCore import qVersion

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('STOPOTS_BUILD_ROOT', ROOT / '.runtime')).resolve()

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()

def main():
    version = qVersion()
    pyside = importlib.metadata.version('PySide6_Essentials')
    assert version == pyside, 'Conferir mapeamento de fontes de versões diferentes'
    major_minor = '.'.join(version.split('.')[:2])
    source_dir = BUILD / 'third-party-sources'
    source_dir.mkdir(parents=True, exist_ok=True)
    legal = BUILD / 'third-party-notices'
    legal.mkdir(parents=True, exist_ok=True)
    urls = {name: f'https://download.qt.io/archive/qt/{major_minor}/{version}/submodules/{name}-everywhere-src-{version}.tar.xz'
            for name in ('qtbase','qtdeclarative','qtshadertools','qtsvg','qtwayland','qtimageformats','qttranslations','qtlanguageserver')}
    urls['pyside-setup'] = f'https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-{pyside}-src/pyside-setup-everywhere-src-{pyside}.tar.xz'
    records = []
    for name, url in urls.items():
        path = source_dir / url.rsplit('/',1)[1]
        if not path.exists():
            temp = path.with_suffix(path.suffix+'.part')
            with urllib.request.urlopen(url, timeout=90) as response, temp.open('wb') as target:
                while block := response.read(1024*1024):
                    target.write(block)
            temp.replace(path)
        with tarfile.open(path, 'r:*') as archive:
            for member in archive:
                label = PurePosixPath(member.name).name.lower()
                if not member.isfile() or member.size > 2_000_000:
                    continue
                license_directory = any(p.lower() in ('licenses', 'licences') for p in PurePosixPath(member.name).parts[:-1])
                if not license_directory and not any(term in label for term in ('license','licence','copying','copyright','qt_attribution')):
                    continue
                parts = PurePosixPath(member.name).parts
                if '..' in parts or member.name.startswith('/'):
                    raise ValueError('Caminho inseguro no arquivo de terceiros')
                target = legal / name / Path(*parts)
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
        records.append({'component':name,'version':version,'url':url,'archive':path.name,
                        'bytes':path.stat().st_size,'sha256':digest(path),'modified_by_project':False})
        print('SOURCE_READY',name,path.stat().st_size,flush=True)
    out = BUILD / 'dist'
    out.mkdir(parents=True,exist_ok=True)
    manifest = {'qt_version':version,'pyside_version':pyside,'sources':records,
                'notice':'Fontes independentes mantêm suas próprias licenças; não estão sob YGP NoResale.'}
    (source_dir/'SOURCES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (out/'THIRD_PARTY_SOURCES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    bundle=out/f'third-party-sources-qt-{version}.tar.gz'
    with tarfile.open(bundle,'w:gz',compresslevel=1) as archive:
        for path in sorted(source_dir.iterdir()):
            if path.is_file() and not path.name.endswith('.part'):
                archive.add(path,arcname='third-party-sources/'+path.name)
    print('SOURCE_BUNDLE_READY',bundle.name,digest(bundle),flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
