import sys, time, collections, json
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import verify_calendar_r18 as V
import r18lib as L
t0 = time.time()
nm = L.read_meta(V.W / 'candidate_meta.json')
X = V.expectations()
vm = V.VM(V.O / 'NightRemaster.ain', nm)
counts = collections.Counter()
which = sys.argv[1:] or ['sandbox', 'lock']
if 'sandbox' in which:
    out = V.sandbox_checks(vm, X, counts)
    print(json.dumps(out, ensure_ascii=False, default=str)[:3000])
    print('sandbox ok', round(time.time() - t0, 1))
if 'lock' in which:
    V.lock_checks(vm, X, counts)
    print('lock ok', round(time.time() - t0, 1))
print(dict(counts))
