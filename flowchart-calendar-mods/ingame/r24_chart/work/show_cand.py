"""r24 reading aid: the live body of candidate functions (work/build/candidate_raw_code.jam + candidate_meta.json), ops with
CALLFUNC / PUSH-of-function targets named. Read only.
  python show_cand.py NAME [NAME...]
"""
import sys, re
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r24lib as L

sys.stdout.reconfigure(encoding='utf-8')
W = L.WORK / 'build'
nm = L.read_meta(W / 'candidate_meta.json')
cv = L.versions(W / 'candidate_raw_code.jam')
for name in sys.argv[1:]:
    fid = L.fid_of(nm, name)
    f = nm['functions'][fid]
    v = L.live_version(nm, cv, fid)
    print('=' * 10, name, 'fid', fid, 'address', f['address'], 'args', [(a['name'], a['type'][0]) for a in f['arguments']],
          'vars', [(a['name'], a['type'][0]) for a in f['variables']], 'ret', f['return-type'][0])
    for ad, op in v['ops']:
        z = re.match(r'(CALLFUNC|PUSH) 0x([0-9a-f]+)$', op)
        extra = ''
        if z and z.group(1) == 'CALLFUNC':
            extra = '   ; ' + L.raw_symbol(nm, int(z.group(2), 16))
        print('  %8d  %s%s' % (ad, op, extra))
