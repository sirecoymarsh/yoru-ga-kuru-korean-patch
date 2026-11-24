"""r16: copy the current runtime AIN (read-only source) into work/base and dump what the build/verify need (meta + raw code).

The runtime copy and its metadata made by the 05:15 base check (work/base_moved_check) are moved here when their hash is
the base hash (saves a second 17 MB dump). Nothing outside r16_calendar is written.
"""
import sys, shutil
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r16lib as L

ptr, rt = L.runtime()
src = rt / 'NightRemaster.ain'
h = L.sha(src)
print('runtime', rt)
print('AIN', h, src.stat().st_size, ptr['status'])
assert h == L.BASE_AIN_SHA and ptr['status'] == L.BASE_STATUS, 'runtime moved: update r16lib BASE_* first'
assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'] == L.BASE_MANIFEST_SHA
base = L.WORK / 'base'
base.mkdir(exist_ok=True)
dst = base / 'NightRemaster.ain'
chk = L.WORK / 'base_moved_check'
if (not dst.exists() or L.sha(dst) != h) and (chk / 'runtime_now.ain').exists() and L.sha(chk / 'runtime_now.ain') == h:
    shutil.move(str(chk / 'runtime_now.ain'), str(dst))
    if (chk / 'runtime_now_meta.json').exists() and not (base / 'meta.json').exists():
        shutil.move(str(chk / 'runtime_now_meta.json'), str(base / 'meta.json'))
if not dst.exists() or L.sha(dst) != h:
    shutil.copy2(src, dst)
assert L.sha(dst) == h
for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex', 'NightRemaster.exe']:
    print(n, L.sha(rt / n))
if not (base / 'meta.json').exists():
    L.cmd('ain', 'dump', '-j', '-o', base / 'meta.json', dst)
if not (base / 'raw_code.jam').exists():
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', base / 'raw_code.jam', dst, timeout=900)
m = L.read_meta(base / 'meta.json')
print('functions', len(m['functions']))
L.writej(base / 'snapshot.json', dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                                      ain_sha256=h, ain_size=src.stat().st_size, functions=len(m['functions']),
                                      pact_sha256=L.sha(rt / 'NightRemasterPact.afa'), ex_sha256=L.sha(rt / 'NightRemasterEX.ex'),
                                      exe_sha256=L.sha(rt / 'NightRemaster.exe')))
