"""WI-009 r2 home-context native probe (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29; review F-05).

probe_chart_r24's --home mode on the candidate: the copied home save NightR44.asd (10/14; a read-only savecopy of the user's slot,
copied into the private save folder) is resumed, the home menu requests the chart, and the calendar opens in the home context
(ctx 2). Tour (probe_calendar_home_20260929.jaf): lists as opened and under the mixed read fixture (current month, 회상 p1 and
8월 p1 = the pages whose footer note moved into the bottom bar, 5월 p2 with the two-line names), group card 21 (card page ->
장면 고르기 -> back), E01101 (a short pool talk) -> 다시 보기 = memory-mode replay (messages clicked through) -> the chart opens again
on the same tab / page -> closed -> home menu, no calendar parts left. Every list page drawn is checked with the all-tabs probe's
KR_W29PList. Uses probe/tour_readable.jaf written by probe_calendar_all_tabs_20260929.py (same candidate).
Results: evidence/native_home_probe.json, evidence/native_home/*.png. Muted, private save folder; the user's saves are hashed only.
"""
from pathlib import Path
import sys, json, datetime
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import w29common as C
import w29probe as WP
L = C.L
O = C.O
T = C.tables()
cells = T['cells']
first = {}
for i, c in enumerate(cells):
    first.setdefault(c['tab'], i)


def where(no):
    i = next(j for j, c in enumerate(cells) if c['no'] == no and (c['card'] or True))
    c = cells[i]
    return c['tab'], (i - first[c['tab']]) // 12, (i - first[c['tab']]) % 12, i


t41, p41, s41, i41 = where(41)
t1101, p1101, s1101, i1101 = where(1101)
assert t41 == 1 and p41 == 1 and cells[i41]['card'] and cells[i41]['ref'] == 100021
assert t1101 == 0 and p1101 == 0 and not cells[i1101]['card'] and not cells[i1101]['thumb']
man = L.readj(O / 'candidate/manifest.json')
assert L.sha(O / 'candidate/NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
tour = O / 'probe/tour_readable.jaf'
allp = L.readj(O / 'evidence/native_all_tabs_probe.json')
assert allp['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256'], 'run the all-tabs probe on this candidate first'
home = (H / 'probe_calendar_home_20260929.jaf').read_text('utf-8')
for k, v in {'@@PAGE41@@': p41, '@@PAGE41P1@@': p41 + 1, '@@SLOT41@@': s41, '@@PAGE1101@@': p1101, '@@PAGE1101P1@@': p1101 + 1,
             '@@SLOT1101@@': s1101, '@@I1101@@': i1101}.items():
    home = home.replace(k, str(v))
assert '@@' not in home
jaf = tour.read_text('utf-8') + '\n' + home
(O / 'probe_home').mkdir(parents=True, exist_ok=True)
(O / 'probe_home/tour_home_readable.jaf').write_text(jaf, 'utf-8')
P = WP.configure(O / 'probe_home', O / 'candidate', O / 'work', jaf, '', '    if (KR_W29PDialog(ph, title)) return;')
a1 = '    KR_P22SetN("Step", step + 1);\n    if (ph == "kchart") {'
assert P.PROBE_JAF.count(a1) == 1
P.PROBE_JAF = P.PROBE_JAF.replace(a1, '    KR_P22SetN("Step", step + 1);\n    if (KR_W29PHomeChart(ph)) return;\n    if (ph == "kchart") {')
a2 = '''        if (ph == "home_after") {
            KR_P22Shot("chart_home_after");
            KR_P22Log("END");
            system.Exit(0);
        }'''
assert P.PROBE_JAF.count(a2) == 1
P.PROBE_JAF = P.PROBE_JAF.replace(a2, '''        if (ph == "home_after") {
            KR_P22Shot("chart_home_after");
            KR_W29PHomeEnd();
        }''')
before = P.user_state()
playing = P.user_game_running()
P.setup_folder()
key = L.save_records(L.save_path(P.HOME_SAVE))['key']
info = P.build_probe('home', key=key)
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
r = P.one_run('home', stamp, save=P.HOME_SAVE, copy_save=True, timeout=900)
r['probe'] = info
dest = O / 'evidence/native_home'
if dest.exists():
    import shutil
    shutil.rmtree(dest)
r['shots'] = P.collect_shots('native_home')
r['candidate_sha256'] = L.sha(P.O / 'NightRemaster.ain')
after = P.user_state()
r['user_files_changed'] = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
r['user_game_running'] = bool(playing or P.user_game_running())
r['home_save'] = dict(name=P.HOME_SAVE, source=str(L.save_path(P.HOME_SAVE)), sha256=L.sha(L.save_path(P.HOME_SAVE)))
log = r['log']
r['fail_lines'] = [l for l in log if l.startswith('FAIL')]
r['summary'] = [l for l in log if l.startswith(('W29', 'HOME', 'RESUMED', 'RETURNED', 'REPLAY', 'CHOICE', 'PICKER', 'END', 'UNEXPECTED', 'STUCK'))]
r['time'] = stamp
r['pass'] = (r.get('exit_code') == 0 and 'END' in log and not r['fail_lines'] and not any(k in r for k in ('vm_error', 'message', 'timeout'))
             and not r['user_files_changed'] and any(l.startswith('RETURNED') for l in log) and any(l.startswith('W29 RESUMED') for l in log))
r['author'] = C.AUTHOR
L.writej(O / 'evidence/native_home_probe.json', r)
print(json.dumps({k: v for k, v in r.items() if k not in ('events', 'probe', 'log')}, ensure_ascii=False, indent=1)[:5000])
