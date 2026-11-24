"""r16 study helper (copy of r15 work/study.py): python study.py NAME [NAME...]  -> live body of each function (alice --function), saved under work/study."""
import sys, re
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r16lib as L

base = L.WORK / 'base'
out = L.WORK / 'study'
out.mkdir(exist_ok=True)
m = L.read_meta(base / 'meta.json')
names = {}
for f in m['functions']:
    names.setdefault(L.raw_symbol(m, f['index']), []).append(f['index'])
args = sys.argv[1:]
if args and args[0] == '--grep':
    pat = re.compile(args[1])
    for n, ids in sorted(names.items()):
        if pat.search(n):
            for i in ids:
                f = m['functions'][i]
                print(i, n, 'addr=0x%x' % f['address'] if f['address'] != 0xffffffff else 'noaddr',
                      'args=' + ','.join(a['name'] for a in f['arguments']), 'ret=%s' % (f['return-type'],))
    sys.exit(0)
for n in args:
    ids = names.get(n)
    if not ids and n.isdigit():
        ids = [int(n)]
        n = L.symbol(m, ids[0])
    assert ids, n
    for i in ids:
        sym = L.symbol(m, i)
        p = out / f'{i}.jam'
        L.cmd('ain', 'dump', '--function', sym, '-o', p, base / 'NightRemaster.ain')
        f = m['functions'][i]
        print('=' * 20, i, sym, 'addr=0x%x' % f['address'], 'args=', [(a['name'], a['type']) for a in f['arguments']], 'ret=', f['return-type'],
              'vars=', [(v['name']) for v in f.get('vars', [])][:40])
        print(p.read_text('utf8'))
