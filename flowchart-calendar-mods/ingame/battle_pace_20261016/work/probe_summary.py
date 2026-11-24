# -*- coding: utf-8 -*-
"""Summarize the isolated native probes of the battle-pace candidate against the installed Mods-tab AIN (before / after, run
back to back with mods_effects_20261016/probe_effects.py --layer mods|pace) -> 증거/probe_pace.json + 증거/그림/*.png.
Reads the probe run records only."""
import json, re, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import bplib as L

RUNS = HERE.parent / 'mods_effects_20261016' / '증거' / 'runs'
SHOTS = HERE.parent / 'mods_effects_20261016' / '증거' / 'shots'
OUT = HERE / '증거'
FIG = OUT / '그림'
SINCE = '20261016_08'          # the back-to-back pairs of 10-16 morning (before = installed Mods-tab AIN, after = candidate)


def latest(layer, scen):
    pre = scen if layer == 'mods' else 'pace_' + scen
    cands = [p for p in RUNS.glob(pre + '_2026*.json') if re.fullmatch(re.escape(pre) + r'_\d{8}_\d{6}', p.stem)]
    cands = [p for p in cands if p.stem[-15:] >= SINCE]
    return json.loads(max(cands).read_text('utf8')) | {'_run': max(cands).stem} if cands else None


def battles(log):
    out = []
    dec = {}
    cyc = []
    for l in log:
        if l.startswith('BATTLE') and ' BEGIN ' in l:
            dec = {}
            cyc = []
        m = re.match(r'SMART call=\d+ ms=(\d+) r=\d actor=(\d+)', l)
        if m:
            t, a = int(m[1]), int(m[2])
            if a in dec:
                cyc.append(t - dec[a])
            dec[a] = t
        m = re.match(r'BATTLE (\d+) END ms=(\d+) .* quickActive=(\d) rate=(\d+) .* sumTime=(\d+) sumScaled=(\d+) transitions=(\d+) transitionMs=(\d+)', l)
        if m:
            out.append(dict(battle=int(m[1]), ms=int(m[2]), quick=int(m[3]), rate=int(m[4]), scaled_over_real=round(int(m[6]) / max(1, int(m[5])), 2),
                            transitions=int(m[7]), transition_ms=int(m[8]), cycles_ms=cyc))
    return out


def group(r):
    b = battles(r['log'])
    cyc = [c for x in b for c in x['cycles_ms']]
    tr = sum(x['transitions'] for x in b)
    trms = sum(x['transition_ms'] for x in b)
    return dict(run=r['_run'], candidate_ain=r.get('candidate_ain'), battles=b, battle_ms_total=sum(x['ms'] for x in b),
                transition_ms_total=trms, transitions_total=tr, ms_per_transition=round(trms / tr, 1) if tr else None,
                transition_share=round(trms / max(1, sum(x['ms'] for x in b)), 2),
                cycle_ms_mean=round(statistics.mean(cyc)) if cyc else None, cycle_n=len(cyc))


def clean(r):
    lg = r.get('log') or []
    return bool(r.get('user_save_folder_unchanged') and not r.get('vm_error') and not r.get('events') and not r.get('timeout')
                and not r.get('fails') and 'END code=0' in lg)


def red_pixels(png):
    from PIL import Image
    im = Image.open(png).convert('RGB').crop((530, 415, 815, 700))
    return sum(1 for p in im.getdata() if p[0] > 200 and p[1] < 80 and p[2] < 80)


def shots_dir(run):
    return SHOTS / run


def story_trans(r):
    return [int(m[1]) for l in r['log'] for m in [re.match(r'TRANS outside battle ms=(-?\d+)', l)] if m]


def main():
    cand = L.sha(HERE / 'candidate' / 'NightRemaster.ain')
    res = dict(candidate_ain=cand, base_ain=L.BASE_AIN_SHA, author=L.AUTHOR, runs_folder=str(RUNS), problems=[])
    allpace = []
    for scen in ['speed1', 'speed5', 'quick']:
        b, a = latest('mods', scen), latest('pace', scen)
        if not (b and a):
            res['problems'].append('missing pair ' + scen)
            continue
        allpace.append(a)
        if b.get('candidate_ain') != L.BASE_AIN_SHA or a.get('candidate_ain') != cand:
            res['problems'].append('pair for another AIN: ' + scen)
        res[scen] = dict(before=group(b), after=group(a), before_clean=clean(b), after_clean=clean(a))
    s1, s5, q = res.get('speed1'), res.get('speed5'), res.get('quick')
    checks = {}
    if s1:
        checks['speed1_transition_time_unchanged'] = s1['before']['ms_per_transition'] == s1['after']['ms_per_transition'] or \
            abs((s1['before']['ms_per_transition'] or 0) - (s1['after']['ms_per_transition'] or 0)) <= 15
    if s5:
        checks['speed5_transitions_divided'] = bool(s5['after']['ms_per_transition'] and s5['before']['ms_per_transition'] and
                                                    s5['after']['ms_per_transition'] <= s5['before']['ms_per_transition'] / 4)
    if q:
        checks['quick_no_transition_wait'] = all(x['transition_ms'] == 0 for x in q['after']['battles']) and len(q['after']['battles']) == 3
    rb, ra = latest('mods', 'routestale'), latest('pace', 'routestale')
    if rb and ra:
        allpace.append(ra)
        px = {}
        for tag, r in [('before', rb), ('after', ra)]:
            d = shots_dir(r['_run'])
            px[tag] = {n: red_pixels(d / (n + '.png')) for n in ['pe_routestale_start', 'pe_routestale_step', 'pe_routestale_step2']}
        res['route_stale'] = dict(before=rb['_run'], after=ra['_run'], red_pixels_in_minimap=px)
        checks['route_line_gone_after_load'] = all(v > 40 for v in px['before'].values()) and all(v == 0 for v in px['after'].values())
    rt = latest('pace', 'routetoggle')
    if rt:
        allpace.append(rt)
        d = shots_dir(rt['_run'])
        px = {n: red_pixels(d / (n + '.png')) for n in ['pe_rt_on_1', 'pe_rt_on_2', 'pe_rt_off_1', 'pe_rt_off_2', 'pe_rt_on_3']}
        res['route_toggle_after'] = dict(run=rt['_run'], red_pixels_in_minimap=px)
        checks['route_on_off_on_still_works'] = px['pe_rt_on_1'] > 40 and px['pe_rt_on_2'] > 40 and px['pe_rt_off_1'] == 0 and \
            px['pe_rt_off_2'] == 0 and px['pe_rt_on_3'] > 40
    sb, sa = latest('mods', 'story'), latest('pace', 'story')
    if sb and sa:
        tb, ta = story_trans(sb), story_trans(sa)
        res['story'] = dict(before=sb['_run'], after=sa['_run'], transitions_before=tb, transitions_after=ta,
                            save=sa.get('save'), vm_error_before=sb.get('vm_error'), vm_error_after=sa.get('vm_error'),
                            user_save_folder_unchanged=bool(sb.get('user_save_folder_unchanged') and sa.get('user_save_folder_unchanged')),
                            note='screen transitions outside battles while a dungeon story event plays (no screenshots). The save was '
                                 'taken inside a message click-wait; the probe ends that resumed wait once (input is cut off). Both runs '
                                 'then stop at the same VM error near the end of the event, with the installed AIN as with the candidate: '
                                 'a probe-condition stop, not this change; the transitions up to it are compared.')
        checks['story_transitions_identical'] = bool(tb) and tb == ta and sb.get('vm_error') == sa.get('vm_error')
    res['checks'] = checks
    res['user_save_folder_unchanged_all'] = all(r.get('user_save_folder_unchanged') for r in allpace)
    res['after_runs_clean'] = all(clean(r) for r in allpace)
    res['passed'] = bool(checks) and all(checks.values()) and res['after_runs_clean'] and not res['problems']
    OUT.mkdir(parents=True, exist_ok=True)
    L.writej(OUT / 'probe_pace.json', res)
    print(json.dumps({k: v for k, v in res.items() if k in ('checks', 'passed', 'problems', 'user_save_folder_unchanged_all', 'after_runs_clean')}, ensure_ascii=False, indent=1))
    for scen in ['speed1', 'speed5', 'quick']:
        if scen in res:
            g = res[scen]
            print(scen, 'before', {k: g['before'][k] for k in ('battle_ms_total', 'transition_ms_total', 'ms_per_transition', 'transition_share', 'cycle_ms_mean', 'cycle_n')})
            print(scen, 'after ', {k: g['after'][k] for k in ('battle_ms_total', 'transition_ms_total', 'ms_per_transition', 'transition_share', 'cycle_ms_mean', 'cycle_n')})
    if 'route_stale' in res:
        print('route', res['route_stale']['red_pixels_in_minimap'])
    if 'route_toggle_after' in res:
        print('toggle', res['route_toggle_after']['red_pixels_in_minimap'])
    if 'story' in res:
        print('story', res['story']['transitions_before'][:20], res['story']['transitions_after'][:20])


if __name__ == '__main__':
    main()
