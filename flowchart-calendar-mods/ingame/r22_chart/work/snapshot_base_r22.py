"""r22: the base snapshot (runtime AIN copy + meta.json + raw_code.jam) the build and the verifier read (after r21
work/snapshot_base_r21.py). Needed only after a rebase.

While the base AIN is the r21 candidate (same hash as r22lib BASE_AIN_SHA) nothing is copied: r22lib.base_paths() reads the r21
candidate files (read only). After a rebase (Codex moved the runtime, r22lib BASE_* updated first) the runtime AIN is copied into
r22 work/base and dumped once (ain dump -j / --raw-code --no-macros, the same commands the build uses for the candidate).
Records work/base_snapshot.json either way. Nothing outside r22_chart is written; the runtime is only read.
"""
import sys, shutil
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r22lib as L

free = shutil.disk_usage('P:/').free
assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
ptr, rt = L.runtime()
src = rt / 'NightRemaster.ain'
h = L.sha(src)
print('runtime', rt)
print('AIN', h, src.stat().st_size, ptr['status'])
assert h == L.BASE_AIN_SHA and ptr['status'] == L.BASE_STATUS, 'runtime moved: update r22lib BASE_* first'
assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'] == L.BASE_MANIFEST_SHA
try:
    found = L.base_paths()
except AssertionError:
    found = None
if found is None:
    base = L.WORK / 'base'
    base.mkdir(exist_ok=True)
    dst = base / 'NightRemaster.ain'
    if not dst.exists() or L.sha(dst) != h:
        shutil.copy2(src, dst)
    assert L.sha(dst) == h
    if not (base / 'meta.json').exists():
        L.cmd('ain', 'dump', '-j', '-o', base / 'meta.json', dst)
    if not (base / 'raw_code.jam').exists():
        L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', base / 'raw_code.jam', dst, timeout=900)
    found = L.base_paths()
    assert found['ain'] == dst, found
reused = found['ain'].resolve() != (L.WORK / 'base' / 'NightRemaster.ain').resolve()
m = L.read_meta(found['meta'])
print('base', found['ain'], 'reused (read only)' if reused else 'own copy', 'functions', len(m['functions']))
L.writej(L.WORK / 'base_snapshot.json', dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'],
                                             status=ptr['status'], ain_sha256=h, ain_size=src.stat().st_size, functions=len(m['functions']),
                                             base_ain=str(found['ain']), base_meta=str(found['meta']), base_raw=str(found['raw']),
                                             reused_snapshot=reused, pact_sha256=L.sha(rt / 'NightRemasterPact.afa'),
                                             ex_sha256=L.sha(rt / 'NightRemasterEX.ex'), exe_sha256=L.sha(rt / 'NightRemaster.exe')))
