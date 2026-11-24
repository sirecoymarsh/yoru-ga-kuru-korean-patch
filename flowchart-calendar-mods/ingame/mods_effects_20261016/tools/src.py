"""Structured (names resolved) live body from base code.jam: picks the FUNC copy whose jump labels lie inside the live
address range (live.py data). usage: python src.py NAME [NAME...] [> file]"""
import re, sys
import funcs, live
def live_range(d, fid):
    ops = d['live'].get(fid)
    if not ops: return None
    return ops[0][0], ops[-1][0]
def pick(name):
    d = live.load()
    ids = [i for i, n in enumerate(d['names']) if n == name]
    out = []
    vs = funcs.blocks().get(name, [])
    for fid in ids:
        r = live_range(d, fid)
        best = None
        for v in vs:
            if f'FUNC {fid}\n' not in v: continue
            labs = [int(x, 16) for x in re.findall(r'(?m)^0x([0-9a-f]+):', v)]
            if r and labs and all(r[0] - 8 <= a <= r[1] + 8 for a in labs):
                best = v
        if best is None:
            cand = [v for v in vs if f'FUNC {fid}\n' in v]
            best = (cand[-1] + '\n;; (no-label pick: last copy)') if cand else f';; ?? {name} {fid}'
        out.append(best)
    return out
if __name__ == '__main__':
    for a in sys.argv[1:]:
        for x in pick(a): print(x)
