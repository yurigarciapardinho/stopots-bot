"""Validação do wheel instalado fora do fonte, incluindo recursos e interface."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import zipfile
import stopots_v2

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('STOPOTS_BUILD_ROOT', ROOT / '.runtime')).resolve()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dist', type=Path, default=BUILD / 'dist')
    parser.add_argument('--report', type=Path, default=BUILD / 'validation/installed.json')
    parser.add_argument('--skip-frozen', action='store_true')
    args = parser.parse_args()
    installed = Path(stopots_v2.__file__).resolve().parent
    source = ROOT / 'src/stopots_v2'
    assert 'site-packages' in installed.parts and installed != source, 'Exige wheel instalado em venv separado'
    wheel = args.dist / f'stopots_bot-{stopots_v2.__version__}-py3-none-any.whl'
    hashes = {}
    with zipfile.ZipFile(wheel) as archive:
        for path in sorted(source.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            rel = path.relative_to(source).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert hashlib.sha256((installed / rel).read_bytes()).hexdigest() == digest, rel
            assert hashlib.sha256(archive.read('stopots_v2/' + rel)).hexdigest() == digest, rel
            hashes[rel] = digest
        metadata = archive.read(next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))).decode()
        assert 'Yuri Garcia Pardinho' in metadata and 'LicenseRef-YGP-NoResale-1.0 AND MIT' in metadata
        assert any(n.endswith('/licenses/LICENSE') for n in archive.namelist())
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.update(STOPOTS_RUNTIME=str(BUILD / 'wheel-ui'), QT_QPA_PLATFORM='offscreen')
    BUILD.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([sys.executable, '-m', 'stopots_v2.desktop', '--verificar-ui'], cwd=BUILD, env=env,
                            text=True, capture_output=True, timeout=45)
    assert result.returncode == 0, result.stdout + '\n' + result.stderr
    if not args.skip_frozen:
        assets = args.dist / 'portable/StopotsAssistente/_internal/stopots_v2'
        for rel, digest in hashes.items():
            if Path(rel).suffix != '.py':
                assert hashlib.sha256((assets / rel).read_bytes()).hexdigest() == digest, rel
    report = {'version': stopots_v2.__version__, 'installed_wheel': True, 'runtime_files_matched': len(hashes),
              'runtime_source_sha256': hashes, 'frozen_assets_match': None if args.skip_frozen else True,
              'installed_gui_exit': result.returncode, 'playwright': importlib.metadata.version('playwright'),
              'pyside6_essentials': importlib.metadata.version('PySide6_Essentials'), 'subject': 'installed-wheel-and-ui-offline'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != 'runtime_source_sha256'}), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
