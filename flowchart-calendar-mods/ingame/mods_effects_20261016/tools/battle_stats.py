"""Battle timing per setting from the run logs: engine scaled/real time ratio, same-actor decision cycle, transition share."""
import json, re, statistics
from pathlib import Path

EVID = Path(__file__).resolve().parent.parent / '증거' / 'runs'
GROUP = {'speedraw': 'x1 (native speed-up off, slider 1)', 'speed1': 'x2 (native speed-up, slider 1)', 'off': 'x2 (native speed-up, slider 1)',
         'smart': 'x2 (native speed-up, slider 1)', 'items': 'x2 (native speed-up, slider 1)', 'speed5': 'x5 (slider 5)',
         'quick': 'quick (effects hidden, rate 1000)', 'rates20battle': 'quick (effects hidden, rate 1000)'}


def main():
    rows = {}
    for p in sorted(EVID.glob('*.json')):
        scen = p.stem.rsplit('_', 2)[0]
        if scen not in GROUP:
            continue
        log = json.loads(p.read_text('utf8'))['log']
        g = rows.setdefault(GROUP[scen], dict(ratio=[], cycle=[], battles=0, ms=[], trans_share=[], runs=set()))
        g['runs'].add(p.stem)
        dec = {}
        for l in log:
            if ' BEGIN ' in l and l.startswith('BATTLE'):
                dec = {}
            m = re.match(r'SMART call=\d+ ms=(\d+) r=\d actor=(\d+)', l)
            if m:
                t, a = int(m[1]), int(m[2])
                if a in dec:
                    g['cycle'].append(t - dec[a])
                dec[a] = t
            m = re.match(r'BATTLE \d+ END ms=(\d+) .* sumTime=(\d+) sumScaled=(\d+)(?: transitions=\d+ transitionMs=(\d+))?', l)
            if m:
                g['battles'] += 1
                g['ms'].append(int(m[1]))
                if int(m[2]) > 0:
                    g['ratio'].append(int(m[3]) / int(m[2]))
                if m[4] is not None and int(m[1]) > 0:
                    g['trans_share'].append(int(m[4]) / int(m[1]))
    out = {}
    for k, g in rows.items():
        out[k] = dict(runs=sorted(g['runs']), battles=g['battles'],
                      scaled_over_real=round(statistics.mean(g['ratio']), 2) if g['ratio'] else None,
                      cycle_ms_mean=round(statistics.mean(g['cycle'])) if g['cycle'] else None,
                      cycle_ms_n=len(g['cycle']), cycle_ms=sorted(g['cycle']),
                      transition_share_mean=round(statistics.mean(g['trans_share']), 2) if g['trans_share'] else None,
                      transition_share_n=len(g['trans_share']))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


if __name__ == '__main__':
    main()
