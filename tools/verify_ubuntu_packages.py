"""Instala o .deb em containers descartáveis; não instala no sistema do usuário."""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=Path(os.environ.get('STOPOTS_BUILD_ROOT',ROOT/'.runtime')).resolve()
DIST=RUNTIME/'dist'

SCRIPT=r'''
from pathlib import Path
import os,subprocess,json,sys
base=os.environ.copy();steps=[]
def run(name,args,extra=None):
 env=base.copy();env.update(extra or {})
 result=subprocess.run(args,env=env,text=True,capture_output=True,timeout=180)
 steps.append({'step':name,'exit':result.returncode,'output':result.stdout[-2200:],'stderr':result.stderr[-1200:]})
 print(name,result.returncode,flush=True)
 if result.returncode:
  print(result.stdout[-6000:],result.stderr[-3000:],flush=True)
  raise RuntimeError(name)
try:
 deb=next(Path('/release').glob('stopots-assistente_*_amd64.deb'))
 run('install_deb',['dpkg','-i',str(deb)])
 run('installed_offscreen',['/usr/bin/stopots-assistente','--verificar-ui'])
 run('installed_xcb',['xvfb-run','-a','-s','-screen 0 1366x768x24','/usr/bin/stopots-assistente','--verificar-ui'],{'QT_QPA_PLATFORM':'xcb'})
 for scale in ['1.25','1.5']:
  run('installed_scale_'+scale,['/usr/bin/stopots-assistente','--verificar-ui'],{'QT_SCALE_FACTOR':scale})
 if os.environ['TEST_UBUNTU']=='24.04':
  Path('/runtime/tmp').mkdir(exist_ok=True)
  # O host retoma a posse do bind mount após cada teste; subprocessos do Chrome
  # podem descartar capabilities. Usar permissões de diretório temporário Unix.
  Path('/runtime/tmp').chmod(0o1777)
  wrapper=Path('/usr/local/bin/google-chrome')
  wrapper.write_text('#!/bin/sh\nexec /opt/google/chrome/chrome --no-sandbox --disable-dev-shm-usage "$@"\n');wrapper.chmod(0o755)
  os.chdir('/src')
  run('source_contracts',['/venv/bin/python','-m','pytest','-x','-vv','-s','--tb=short','-p','no:cacheprovider','--basetemp','/runtime/pytest','tests'],{'PYTHONPATH':'/src/src','TMPDIR':'/runtime/tmp'})
 passed=True
except Exception as e:
 passed=False;steps.append({'failure':type(e).__name__})
finally:
 report={'ubuntu':os.environ['TEST_UBUNTU'],'passed':passed,'steps':steps,'scope':'isolated_userspace_offscreen_xvfb_no_online_match'}
 Path('/runtime/package-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 subprocess.run(['chown','-R',os.environ['HOST_UID']+':'+os.environ['HOST_GID'],'/runtime'])
sys.exit(0 if passed else 1)
'''


def main():
    versions=sys.argv[1:] or ['24.04','26.04']
    out=ROOT/'evidence/releases/2.0.0/ubuntu.json'
    reports=[r for r in json.loads(out.read_text(encoding="utf-8")).get('platforms',[]) if r['ubuntu'] not in versions] if out.exists() else []
    for version in versions:
        target=RUNTIME/('ubuntu-package-'+version);target.mkdir(exist_ok=True)
        command=['docker','run','--rm','--network','none','--shm-size=512m',
                 '-e','TEST_UBUNTU='+version,'-e','HOST_UID='+str(os.getuid()),'-e','HOST_GID='+str(os.getgid()),
                 '-v',str(DIST)+':/release:ro','-v',str(target)+':/runtime',
                 '-v',str(ROOT)+':/src:ro','-v',str(Path(sys.prefix))+':/venv:ro',
                 '-v','/opt/google/chrome:/opt/google/chrome:ro','stopots-ui-test:'+version,'python3','-u','-c',SCRIPT]
        result=subprocess.run(command,text=True,capture_output=True,timeout=360)
        print('UBUNTU',version,'EXIT',result.returncode,flush=True)
        print(result.stdout[-6000:],result.stderr[-2500:],flush=True)
        reports.append(json.loads((target/'package-result.json').read_text(encoding="utf-8")))
    out.write_text(json.dumps({'platforms':reports},ensure_ascii=False,indent=2)+'\n', encoding="utf-8")
    return 0 if all(r['passed'] for r in reports) else 1


if __name__=='__main__':raise SystemExit(main())
