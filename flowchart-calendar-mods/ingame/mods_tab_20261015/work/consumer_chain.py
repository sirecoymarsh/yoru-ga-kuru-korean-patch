# -*- coding: utf-8 -*-
"""Read only (10-15): for each Mods setting's reader, follow callers upward (live code, CALLFUNC / method PUSH) until an original
game function (not KR_*) is reached, so a setting that is read only by an unreachable helper shows up."""
import sys, re, json, collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mdlib as L

bp = L.base_paths()
m = L.read_meta(bp['meta'])
vers = L.versions(bp['raw'])
names = {f['index']: L.raw_symbol(m, f['index']) for f in m['functions']}
callers = collections.defaultdict(set)
for fid, vs in vers.items():
    for v in vs:
        if v['start'] != m['functions'][fid]['address']:
            continue
        for ad, op in v['ops']:
            z = re.match(r'(CALLFUNC|PUSH) 0x([0-9a-f]+)$', op)
            if z:
                t = int(z[2], 16)
                if z[1] == 'CALLFUNC' or (20000 < t < len(names)):
                    callers[t].add(fid)
audit = json.loads((Path(__file__).resolve().parent / 'consumer_audit.json').read_text('utf8'))
by_name = collections.defaultdict(list)
for i, n in names.items():
    by_name[n].append(i)


def chain(name, depth=0, seen=None):
    seen = seen or set()
    out = []
    for fid in by_name.get(name, []):
        for c in sorted(callers.get(fid, ())):
            cn = names[c]
            if cn in seen:
                continue
            seen.add(cn)
            if cn.startswith('KR_') and depth < 4:
                sub = chain(cn, depth + 1, seen)
                out.append((cn, sub))
            else:
                out.append((cn, None))
    return out


def originals(tree):
    res = set()
    for n, sub in tree:
        if sub is None:
            if not n.startswith('KR_'):
                res.add(n)
        else:
            res |= originals(sub)
    return res


report = {}
for label, v in audit.items():
    readers = v.get('callers') or v.get('readers') or {}
    tops = {}
    for r in readers:
        if r.startswith('KR_'):
            tops[r] = sorted(originals(chain(r)))
        else:
            tops[r] = ['(original game function)']
    report[label] = tops
(Path(__file__).resolve().parent / 'consumer_chain.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), 'utf8')
for label, tops in report.items():
    print('==', label)
    for r, o in tops.items():
        print('   ', r, '<-', ', '.join(o)[:300] if o else 'NO ORIGINAL CALLER FOUND')
