"""Pair the settle-path multiplier inputs (CALC lines) with the party gains that follow, per battle / instant kill / sweep."""
import json, glob, re, os, sys
from pathlib import Path

EVID = Path(__file__).resolve().parent.parent / '증거' / 'runs'


def party(line):
    out = {}
    for m in re.finditer(r'p(\d) id=(\d+) lv=(\d+) hp=(\d+)/(\d+) exp=(\d+) tr=(\d+) money=(\d+)', line):
        out[int(m[1])] = dict(lv=int(m[3]), exp=int(m[6]), tr=int(m[7]), money=int(m[8]))
    return out


def main(pattern='*'):
    for p in sorted(EVID.glob(pattern + '.json')):
        d = json.loads(p.read_text('utf8'))
        log = d['log']
        if not any(l.startswith('CALC') for l in log):
            continue
        print('=====', p.name)
        prev = None
        calcs = []
        battle = False
        for l in log:
            if l.startswith('BATTLE') and ' BEGIN ' in l:
                battle = True
            if l.startswith('CALC'):
                calcs.append(l)
            if l.startswith('PARTY ') or l.startswith('SWEEP END') or l.startswith('SWEEP BEGIN'):
                cur = party(l)
                tag = l.split()[1] if l.startswith('PARTY ') else l.split()[0] + '_' + l.split()[1]
                if prev is not None and calcs:
                    get = lambda k, f: [int(re.search(f + r'=(\d+)', c)[1]) for c in calcs if c.startswith('CALC ' + k)]
                    rate = re.search(r'rate=(\d+)', calcs[0])[1]
                    dm = {k: cur[k]['money'] - prev[k]['money'] for k in cur if k in prev}
                    de = {k: cur[k]['exp'] - prev[k]['exp'] for k in cur if k in prev}
                    dt = {k: cur[k]['tr'] - prev[k]['tr'] for k in cur if k in prev}
                    kind = 'battle' if battle else 'instant/sweep'
                    print(f'{tag:26s} {kind:13s} rate={rate} incomes={len(get("money", "src"))} money src={get("money", "src")[:8]}'
                          f' -> +money {dm} +exp {de} +tr {dt}')
                prev = cur
                calcs = []
                battle = False


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '*')
