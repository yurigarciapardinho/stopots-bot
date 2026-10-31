"""Criar venv limpo e testar o wheel, sem instalação editável."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('STOPOTS_BUILD_ROOT', ROOT / '.runtime')).resolve()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    target = BUILD / 'installed'
    subprocess.run(['uv', 'venv', '--clear', '--python', sys.executable, str(target)], check=True)
    python = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    wheels = list((BUILD / 'dist').glob('*.whl'))
    assert len(wheels) == 1, 'Esperado exatamente um wheel'
    subprocess.run(['uv', 'pip', 'install', '--python', str(python), str(wheels[0]) + '[desktop]'], check=True)
    command = [str(python), str(ROOT / 'tools/check_installed_desktop.py')]
    if not args.frozen:
        command.append('--skip-frozen')
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    return subprocess.run(command, cwd=BUILD, env=env).returncode

if __name__ == '__main__':
    raise SystemExit(main())
