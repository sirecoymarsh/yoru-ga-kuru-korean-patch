"""Live function bodies of the candidate AIN (the version whose start address == meta address), from the raw-code dump.
usage: python live.py NAME [NAME ...]    (re:REGEX allowed)
Writes nothing; prints ops with addresses. CALLFUNC 0x.. operands are resolved to names."""
import re, sys, json, collections, pickle
from pathlib import Path
MT = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\mods_tab_20261015')
sys.path.insert(0, str(MT)); sys.dont_write_bytecode = True
import mdlib as L
RAW = MT / 'work' / 'build' / 'candidate_raw_code.jam'
META = MT / 'work' / 'build' / 'candidate_meta.json'
CACHE = Path(__file__).resolve().parent.parent / 'ref' / 'live_cache.pkl'
def load():
    if CACHE.exists():
        return pickle.loads(CACHE.read_bytes())
    m = L.read_meta(META)
    names = [L.raw_symbol(m, f['index']) for f in m['functions']]
    addr = [f['address'] for f in m['functions']]
    vers = L.versions(RAW)
    live = {}
    for fid, vs in vers.items():
        for v in vs:
            if v['start'] == addr[fid]:
                live[fid] = v['ops']
    gl = [L.fix_name(g['name']) for g in m['globals']]
    st = {}
    for si, s in enumerate(m['structures']):
        st[si] = L.fix_name(s['name'])
    data = dict(names=names, live=live, globals=gl, structs=st, args={f['index']: [(a['name'], a.get('type')) for a in f.get('arguments', [])] + [('VAR', a['name']) for a in f.get('variables', [])[len(f.get('arguments', [])):]] for f in m['functions']}, ret={f['index']: f.get('return-type') for f in m['functions']})
    CACHE.write_bytes(pickle.dumps(data))
    return data
def show(d, fid):
    out = [f'## {fid} {d["names"][fid]}  args={[a[0] if a[0]!="VAR" else "var:"+a[1] for a in d["args"].get(fid,[])]}']
    prev = None
    for ad, op in d['live'].get(fid, []):
        z = re.match(r'CALLFUNC 0x([0-9a-fA-F]+)', op)
        if z:
            op = 'CALLFUNC ' + d['names'][int(z[1], 16)]
        if op.startswith('CALLMETHOD') and prev:
            z = re.match(r'PUSH 0x([0-9a-fA-F]+)$', prev)
            if z and int(z[1], 16) < len(d['names']):
                op = op + '   ; ' + d['names'][int(z[1], 16)]
        z = re.match(r'(\.?GLOBALREF|\.GLOBALREF) (\w+)', op)
        out.append(f'  {ad:#x}: {op}')
        prev = op
    return '\n'.join(out)
if __name__ == '__main__':
    d = load()
    idx = collections.defaultdict(list)
    for i, n in enumerate(d['names']):
        idx[n].append(i)
    for a in sys.argv[1:]:
        if a.startswith('re:'):
            r = re.compile(a[3:])
            for n, ids in idx.items():
                if r.search(n):
                    for i in ids: print(show(d, i))
        else:
            for i in idx.get(a, []):
                print(show(d, i))
            if a not in idx: print('?? ' + a)
