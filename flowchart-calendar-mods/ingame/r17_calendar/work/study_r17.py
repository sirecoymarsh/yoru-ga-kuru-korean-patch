"""r17 study helper (copy of r16 work/study.py): python study_r17.py [--cand] NAME [NAME...] -> live body of each function
(alice --function) from the base AIN (or the r17 candidate with --cand), saved under work/study; proxy strings decoded for
reading. `--grep REGEX` lists matching function names. Read only outside r17_calendar."""
import sys, re, json
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r17lib as L

args = sys.argv[1:]
cand = '--cand' in args
args = [a for a in args if a != '--cand']
if cand:
    ain = L.HERE / 'candidate' / 'NightRemaster.ain'
    meta = L.WORK / 'build' / 'candidate_meta.json'
    out = L.WORK / 'study' / 'cand'
else:
    bd = L.base_dir()
    ain = bd / 'NightRemaster.ain'
    meta = bd / 'meta.json'
    out = L.WORK / 'study'
out.mkdir(parents=True, exist_ok=True)
m = L.read_meta(meta)
names = {}
for f in m['functions']:
    names.setdefault(L.raw_symbol(m, f['index']), []).append(f['index'])


def dec(z):
    try:
        s = json.loads(z.group(0))
        return json.dumps(L.decode(s.encode('cp932')), ensure_ascii=False)
    except Exception:
        return z.group(0)


if args and args[0] == '--grep':
    pat = re.compile(args[1])
    for n, ids in sorted(names.items()):
        if pat.search(n):
            for i in ids:
                f = m['functions'][i]
                print(i, n, 'addr=0x%x' % f['address'] if f['address'] != 0xffffffff else 'noaddr',
                      'args=' + ','.join('%s:%s' % (a['name'], a['type'][0]) for a in f['arguments']), 'ret=%s' % (f['return-type'][0],))
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
        if not p.exists():
            L.cmd('ain', 'dump', '--function', sym, '-o', p, ain)
        f = m['functions'][i]
        print('=' * 20, i, sym, 'addr=0x%x' % f['address'], 'args=', [(a['name'], a['type'][0]) for a in f['arguments']], 'ret=', f['return-type'][0])
        print(re.sub(r'"(?:[^"\\]|\\.)*"', dec, p.read_text('utf8')))
