"""Auditoria de dependências, segredos e workflows com saída sanitizada."""
from pathlib import Path
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ.get('STOPOTS_BUILD_ROOT', ROOT / '.runtime')).resolve()

def tool(name):
    data = json.loads((ROOT / 'tools/security-tools.json').read_text(encoding="utf-8"))[name]
    target = BUILD / 'security-tools' / data['executable']
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with urllib.request.urlopen(data['url'], timeout=60) as response:
            body = response.read()
        assert hashlib.sha256(body).hexdigest() == data['sha256'], 'Checksum de ferramenta divergente'
        with tarfile.open(fileobj=io.BytesIO(body), mode='r:gz') as archive:
            member = next(m for m in archive.getmembers() if Path(m.name).name == data['executable'] and m.isfile())
            target.write_bytes(archive.extractfile(member).read())
        target.chmod(0o755)
    return target

def main():
    out = BUILD / 'security'
    out.mkdir(parents=True, exist_ok=True)
    results = []
    results.append(subprocess.run([str(tool('rhysd/actionlint')), '-color=false'], cwd=ROOT).returncode)
    gitleaks = str(tool('gitleaks/gitleaks'))
    results.append(subprocess.run([gitleaks, 'git', '--no-banner', '--redact=100', '--log-opts=--all',
                                   '--report-format=json', '--report-path='+str(out/'history.json')], cwd=ROOT).returncode)
    tree = out / 'working-tree'
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir()
    files = subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    for name in files:
        source = ROOT / name
        if not name or not source.is_file() or source.is_symlink():
            continue
        target = tree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    results.append(subprocess.run([gitleaks,'dir',str(tree),'--no-banner','--redact=100',
                                   '--report-format=json','--report-path='+str(out/'tree.json')],cwd=ROOT).returncode)
    requirements = out / 'runtime-requirements.txt'
    with requirements.open('w') as stream:
        subprocess.run(['uv','export','--frozen','--no-dev','--extra','desktop','--group','build','--no-emit-project'],cwd=ROOT,stdout=stream,check=True)
    results.append(subprocess.run(['pip-audit','--requirement',str(requirements),'--no-deps','--disable-pip',
                                   '--progress-spinner','off','--format','json','--output',str(out/'dependencies.json')],cwd=ROOT).returncode)
    shutil.rmtree(tree)
    (out/'summary.json').write_text(json.dumps({'actionlint':results[0],'gitleaks_history':results[1],
                                              'gitleaks_tree':results[2],'runtime_and_build_audit':results[3]},indent=2)+'\n', encoding="utf-8")
    return 0 if not any(results) else 1

if __name__ == '__main__':
    raise SystemExit(main())
