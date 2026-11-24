"""r18: the base snapshot (runtime AIN copy + meta.json + raw_code.jam) the build and the verifier read (copy of r17
work/snapshot_base_r17.py).

When r16_calendar\\work\\base already holds the base AIN (same hash as r18lib BASE_AIN_SHA) nothing is copied: r18lib.base_dir()
reads it there (read only; saves 81 MB). After a rebase (Codex moved the runtime, r18lib BASE_* updated) the runtime AIN is
copied into r18 work\\base and dumped once. Records work\\base_snapshot.json either way. Nothing outside r18_calendar is written.
"""
import sys, shutil
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r18lib as L

free = shutil.disk_usage('P:\\').free
assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
ptr, rt = L.runtime()
src = rt / 'NightRemaster.ain'
h = L.sha(src)
print('runtime', rt)
print('AIN', h, src.stat().st_size, ptr['status'])
assert h == L.BASE_AIN_SHA and ptr['status'] == L.BASE_STATUS, 'runtime moved: update r18lib BASE_* first'
assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'] == L.BASE_MANIFEST_SHA
r16 = L.R16 / 'work' / 'base'
if (r16 / 'NightRemaster.ain').exists() and (r16 / 'meta.json').exists() and (r16 / 'raw_code.jam').exists() \
        and L.sha(r16 / 'NightRemaster.ain') == h:
    where, reused = r16, True
else:
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
    where, reused = base, False
assert L.base_dir() == where, (L.base_dir(), where)
m = L.read_meta(where / 'meta.json')
print('base folder', where, 'reused from r16' if reused else 'own copy', 'functions', len(m['functions']))
L.writej(L.WORK / 'base_snapshot.json', dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'],
                                             status=ptr['status'], ain_sha256=h, ain_size=src.stat().st_size, functions=len(m['functions']),
                                             base_folder=str(where), reused_r16_snapshot=reused,
                                             pact_sha256=L.sha(rt / 'NightRemasterPact.afa'), ex_sha256=L.sha(rt / 'NightRemasterEX.ex'),
                                             exe_sha256=L.sha(rt / 'NightRemaster.exe')))
