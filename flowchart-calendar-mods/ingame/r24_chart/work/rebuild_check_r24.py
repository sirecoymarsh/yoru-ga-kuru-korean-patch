"""r24: build again from the same sources into tmp/rebuild_check (copies of r24lib.py, build_chart_r24.py, claude_chart_r24.jaf;
the copy's paths to r15-r23 and the flowchart folder anchored on the real ingame folder) and compare the AIN hash with the candidate.
Writes work/rebuild_determinism.log. Nothing outside r24_chart is written."""
import sys, shutil, subprocess, os
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import r24lib as L

import datetime
dst = L.TMP / ('rebuild_check_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
if dst.exists():
    raise SystemExit('the rebuild folder exists: inspect it first (not overwritten)')
dst.mkdir(parents=True)
lib = (HERE / 'r24lib.py').read_text('utf8')
anchor = "HERE = Path(__file__).resolve().parent                     # ...\\ingame\\r24_chart\n"
assert lib.count(anchor) == 1
lib = lib.replace(anchor, anchor + "INGAME = Path(r'%s')                   # the rebuild copy lives in r24_chart\\tmp\\rebuild_check\n" % HERE.parent)
assert lib.count("FLOW = HERE.parent.parent") == 1
lib = lib.replace("FLOW = HERE.parent.parent", "FLOW = INGAME.parent")
n = lib.count("HERE.parent / 'r")
assert n >= 9, n
lib = lib.replace("HERE.parent / 'r", "INGAME / 'r")
(dst / 'r24lib.py').write_text(lib, 'utf8')
for f in ('build_chart_r24.py', 'claude_chart_r24.jaf'):
    shutil.copy2(HERE / f, dst / f)
env = dict(os.environ, TEMP=str(L.TMP), TMP=str(L.TMP), PYTHONIOENCODING='utf-8', PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
q = subprocess.run([sys.executable, '-B', str(dst / 'build_chart_r24.py')], capture_output=True, env=env, cwd=str(dst))
out = q.stdout.decode('utf8', 'replace') + q.stderr.decode('utf8', 'replace')
a = L.sha(HERE / 'candidate' / 'NightRemaster.ain')
b = L.sha(dst / 'candidate' / 'NightRemaster.ain') if (dst / 'candidate' / 'NightRemaster.ain').exists() else None
out += '\ncandidate %s\nrebuilt   %s\n%s\n' % (a, b, 'SAME' if a == b else 'DIFFERENT')
(L.WORK / 'rebuild_determinism.log').write_text(out, 'utf8')
print(out[-1500:])
raise SystemExit(0 if a == b else 1)
