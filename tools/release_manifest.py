"""Manifesto, SBOM e hashes do conjunto exato de arquivos a distribuir."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
from stopots_v2 import __version__

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('STOPOTS_BUILD_ROOT', ROOT / '.runtime')).resolve()

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-dirty', action='store_true')
    args = parser.parse_args()
    out = BUILD / 'dist'
    sha = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty = bool(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).strip())
    if dirty and not args.allow_dirty:
        raise RuntimeError('Finalize o commit antes de produzir o manifesto de publicação')
    python = BUILD / 'installed' / ('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    assert python.is_file(), 'Instalação isolada deve ser verificada antes do manifesto'
    subprocess.run(['cyclonedx-py','environment',str(python),'--spec-version','1.6','--output-format','JSON',
                    '--output-file',str(out/'SBOM.cdx.json')],check=True)
    extensions = ('.whl','.tar.gz','.deb','.zip')
    files = {p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir())
             if p.is_file() and (p.name.endswith(extensions) or p.name in ('SBOM.cdx.json','THIRD_PARTY_SOURCES.json','DESKTOP_MANIFESTO.json','INSTALLED_VALIDATION.json'))}
    assert any(n.endswith('.whl') for n in files)
    assert any(n.endswith('.deb') for n in files) if os.name!='nt' else True
    report = {'schema_version':1,'version':__version__,'source_commit':sha,'source_dirty':dirty,
              'created_at':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
              'python':platform.python_version(),'playwright':importlib.metadata.version('playwright'),
              'pyside6_essentials':importlib.metadata.version('PySide6_Essentials'),
              'pyinstaller':importlib.metadata.version('PyInstaller'),'files':files}
    manifest = out/'MANIFESTO.json'
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n', encoding="utf-8")
    checksums = {**files,'MANIFESTO.json':{'sha256':digest(manifest)}}
    (out/'SHA256SUMS').write_text(''.join(v['sha256']+'  '+n+'\n' for n,v in sorted(checksums.items())), encoding="utf-8")
    print(json.dumps({'version':__version__,'source_commit':sha,'files':len(files),'source_dirty':dirty}))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
