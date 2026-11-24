# -*- coding: utf-8 -*-
"""Print the live body of a function (by name or index) from the base raw code dump with call targets and strings resolved.
usage: python show_live.py <name-or-fid> [grep]"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import anlib as L

bp = L.base_paths()
m = L.read_meta(bp['meta'])
key = sys.argv[1]
fid = int(key) if key.isdigit() else L.fid_of(m, key)
pat = sys.argv[2] if len(sys.argv) > 2 else None
strs = L.strings(L.unpack(bp['ain'].read_bytes()))[2]
names = {f['index']: L.raw_symbol(m, f['index']) for f in m['functions']}
ops = L.region_ops(bp['raw'], m, fid)
print('==', names[fid], fid, 'address', m['functions'][fid]['address'], 'ops', len(ops))
for ad, op in ops:
    z = re.match(r'(CALLFUNC|PUSH|S_PUSH|CALLMETHOD|DG_NEW_FROM_METHOD) 0x([0-9a-f]+)$', op)
    note = ''
    if z:
        v = int(z[2], 16)
        if z[1] == 'CALLFUNC' or (z[1] == 'PUSH' and 20000 < v < len(names)):
            note = names.get(v, '')
        elif z[1] == 'S_PUSH' and v < len(strs):
            note = repr(strs[v].decode('cp932', 'replace'))
    line = '%s %s %s' % (hex(ad), op, ('; ' + note) if note else '')
    if pat is None or re.search(pat, line):
        print(line)
