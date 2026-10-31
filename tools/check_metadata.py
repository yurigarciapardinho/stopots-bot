"""Integridade dos metadados e configuração de publicação."""
from pathlib import Path
import ast
import json
import re
import tomllib
ROOT = Path(__file__).resolve().parents[1]

def main():
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
    tree = ast.parse((ROOT / 'src/stopots_v2/__init__.py').read_text())
    version = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets))
    assert version == project['version'] and re.fullmatch(r'\d+\.\d+\.\d+', version)
    assert project['authors'][0]['name'] == 'Yuri Garcia Pardinho'
    assert project['license'] == 'LicenseRef-YGP-NoResale-1.0 AND MIT'
    assert not (ROOT / '.github/workflows/python-publish.yml').exists()
    assert not (ROOT / 'setup.py').exists()
    for name in ('LICENSE', 'LICENSES/MIT.txt', 'LICENSES/LicenseRef-YGP-NoResale-1.0.txt',
                 'LICENSES/LGPL-3.0-only.txt', 'LICENSES/GPL-3.0-only.txt', 'AUTHORS.md', 'CREDITS.md',
                 'THIRD_PARTY_NOTICES.md', 'docs/PROCEDENCIA.md', 'uv.lock'):
        assert (ROOT / name).is_file(), name
    assert 'Copyright (c) 2019 Lucas8x' in (ROOT / 'LICENSES/MIT.txt').read_text()
    count = 0
    for file in (ROOT / '.github/workflows').glob('*.yml'):
        text = file.read_text()
        for action in re.findall(r'uses:\s*([^\s#]+)', text):
            if not action.startswith('./'):
                assert re.fullmatch(r'[^@]+@[a-f0-9]{40}', action), (file.name, action)
            count += 1
        assert 'pull_request_target:' not in text and 'TWINE_PASSWORD' not in text
    assert count > 0
    print(json.dumps({'version': version, 'metadata_passed': True, 'pinned_actions': count}))

if __name__ == '__main__':
    main()
