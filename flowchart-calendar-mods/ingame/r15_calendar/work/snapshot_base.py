"""r15: copy the current runtime AIN (read only source) into work/base and dump it for study."""
import sys, shutil, json
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r15lib as L

ptr, rt = L.runtime()
src = rt / 'NightRemaster.ain'
h = L.sha(src)
print('runtime', rt)
print('AIN', h, src.stat().st_size)
assert h == L.BASE_AIN_SHA, 'runtime AIN moved since 09-27 00:00'
assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256']
base = L.WORK / 'base'
base.mkdir(exist_ok=True)
dst = base / 'NightRemaster.ain'
if not dst.exists() or L.sha(dst) != h:
    shutil.copy2(src, dst)
assert L.sha(dst) == h
for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex', 'NightRemaster.exe']:
    print(n, L.sha(rt / n))
L.cmd('ain', 'dump', '-j', '-o', base / 'meta.json', dst)
L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', base / 'raw_code.jam', dst)
L.cmd('ain', 'dump', '-c', '-o', base / 'code.jam', dst)
L.cmd('ain', 'dump', '-f', '-o', base / 'functions.txt', dst)
L.cmd('ain', 'dump', '-g', '-o', base / 'globals.txt', dst)
L.cmd('ain', 'dump', '-S', '-o', base / 'structs.txt', dst)
m = L.read_meta(base / 'meta.json')
print('meta keys', list(m.keys()))
print('functions', len(m['functions']))
L.writej(base / 'snapshot.json', dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                                      ain_sha256=h, ain_size=src.stat().st_size,
                                      pact_sha256=L.sha(rt / 'NightRemasterPact.afa'), ex_sha256=L.sha(rt / 'NightRemasterEX.ex')))
