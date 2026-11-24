"""development: plant only the defects whose label contains one of the given substrings (python work/dev_defects.py legend Thumb)."""
import sys, collections, time
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import verify_chart_r22 as V
import r22lib as L

t0 = time.time()
man = L.readj(V.O / 'manifest.json')
cand = V.O / 'NightRemaster.ain'
nm = L.read_meta(V.W / 'candidate_meta.json')
X = V.expectations()
vm = V.VM(cand, nm)
regs = V.seen_checks(vm, X, collections.Counter())
C = V.chart_expect(X, vm)
groups = dict(pages=lambda v: V.pages_all(v, X, collections.Counter(), 'partial'),
              r22_pages=lambda v: V.chart_page_checks(V.chart_vm(cand, nm, X, mutate=v.mutate), X, C, collections.Counter()))
want = sys.argv[1:]
for label, group, mutation in V.DEFECTS + V.r22_defects(C):
    if not any(w in label for w in want):
        continue
    v2 = V.VM(cand, nm, mutate=mutation)
    v2.registered = regs
    try:
        groups[group](v2)
        print('NOT CAUGHT', label)
    except (AssertionError, V.Stop, V.VMExit) as ex:
        print('CAUGHT', label, str(ex)[:200])
    except RuntimeError as ex:
        print('NOT PLANTED', label, str(ex)[:200])
print(round(time.time() - t0, 1), 's')
