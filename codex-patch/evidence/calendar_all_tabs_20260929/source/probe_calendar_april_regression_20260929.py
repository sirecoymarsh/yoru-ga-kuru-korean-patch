"""WI-009 April regression (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29): the approved April tour (KR_A29Tour of
probe_calendar_april_adaptive_minis_20260929.jaf, the WI-008 probe) run under the same conditions on
  installed  = the live AIN b74ebc26... (the copy in source/, its meta / raw dump copied to work/regress_installed/build)
  candidate  = this batch's candidate
then every screenshot compared pixel by pixel.

The tour is used as it is except its two May-only assertions ("extras cleared outside April", "April status removed outside
April"): they assert that May still has the OLD layout, which this batch replaces on purpose; the May screenshots are kept and
reported as the intended change. Same muted private run, same April read fixture (KR_A29Global / KR_A29Read).

  python probe_calendar_april_regression_20260929.py installed
  python probe_calendar_april_regression_20260929.py candidate
  python probe_calendar_april_regression_20260929.py compare      -> evidence/april_regression.json
"""
from pathlib import Path
import sys, json, shutil
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import w29common as C
L = C.L
O = C.O
SUPPORT = C.R / 'docs/agentic-workflow/handoffs/calendar_remaining_20260929_support'
TOUR = SUPPORT / 'probe_calendar_april_adaptive_minis_20260929.jaf'
MAY_ONLY = ['    for(int s=0;s<12;s++)for(int j=0;j<20;j++)KR_A29Ensure(!PartsEngine.IsExist(KR_AM29Mini(s,j)),"extras cleared outside April");\n',
            '    for(int s=0;s<12;s++)KR_A29Ensure(!PartsEngine.IsExist(KR_P29Mini(s,4)),"April status removed outside April");\n']
HOOK = '''
    if(ph=="april_stage") {
        string items=KR_P22Get("Items");
        KR_A29Ensure(items.Find("E00004")>=0 && items.Find("E00007")>=0,"picker E numbers retained");
        KR_A29Ensure(items.Find("감상 완료")>=0 && items.Find("아직 보지 않음")>=0,"picker mixed state");
        KR_A29Ensure(items.Find("△")<0 && items.Find("●")<0 && title.Find("단계")<0,"picker plain wording");
        KR_P22Shot("april_scene_picker");KR_P22SetPhase("april_continue");AFL_Parts_EndWaitForClick(0);return;
    }
'''
EXPECTED_DIFF = {'april_detail_group_scene3': 'E00006 read: title from the shared KR_T19EvHead (「이즈미」) instead of the '
                                              'hand-written KR_U29Head (「이즈미와」) - the 09-29 particle correction',
                 'april_detail_e10001': 'E10001 read: 언제 without the stray r19 title mark 「†」 + indent (KR_W29Clean: 「… 6/16 까지 · '
                                        '이즈미 친밀도 5 이상」)',
                 'may_list_unchanged': 'May list: the April list UI now covers May (intended WI-009 change)',
                 'may_detail_unchanged': 'May E00011 card page: the April detail board now covers May (intended WI-009 change)',
                 'may_list_after_april': 'May list: the April list UI now covers May (intended WI-009 change)'}


def tour():
    jaf = TOUR.read_text('utf-8')
    for line in MAY_ONLY:
        assert jaf.count(line) == 1, line
        jaf = jaf.replace(line, '')
    return jaf


def run(which):
    import w29probe as WP
    if which == 'installed':
        ain_dir = O / 'source'
        work = O / 'work/regress_installed'
        (work / 'build').mkdir(parents=True, exist_ok=True)
        for n in ('candidate_meta.json', 'candidate_raw_code.jam'):
            if not (work / 'build' / n).exists():
                shutil.copy2(O / 'source' / n, work / 'build' / n)
            assert L.sha(work / 'build' / n) == L.sha(O / 'source' / n)
        assert L.sha(ain_dir / 'NightRemaster.ain') == C.BASE_AIN
    else:
        ain_dir = O / 'candidate'
        work = O / 'work'
        man = L.readj(O / 'candidate/manifest.json')
        assert L.sha(ain_dir / 'NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    P = WP.configure(O / ('probe_regress_' + which), ain_dir, work, tour(), 'KR_A29Tour();', HOOK,
                     fixture=('KR_A29Global', 'KR_A29Read'), frame_prefix=None)
    tag = 'april_regression/' + which
    dest = O / 'evidence' / tag
    if dest.exists():
        shutil.rmtree(dest)
    r = WP.run(P, tag, timeout=600)
    r['pass'] = (r.get('exit_code') == 0 and 'END' in r['log'] and not any(l.startswith('FAIL') for l in r['log'])
                 and not any(k in r for k in ('vm_error', 'message', 'timeout')) and not r['user_files_changed'])
    L.writej(O / 'evidence' / f'april_regression_{which}.json', r)
    print(json.dumps({k: v for k, v in r.items() if k not in ('events', 'probe', 'log')}, ensure_ascii=False, indent=1)[:3000])
    print('\n'.join(l for l in r['log'] if l.startswith(('FAIL', 'PASS', 'END', 'SUMMARY E0000'))))


def compare():
    import w29probe as WP
    a = L.readj(O / 'evidence/april_regression_installed.json')
    b = L.readj(O / 'evidence/april_regression_candidate.json')
    A, B = O / 'evidence/april_regression/installed', O / 'evidence/april_regression/candidate'
    names = sorted({p.stem for p in A.glob('*.png')} | {p.stem for p in B.glob('*.png')})
    rows = {}
    for n in names:
        pa, pb = A / (n + '.png'), B / (n + '.png')
        if not (pa.exists() and pb.exists()):
            rows[n] = dict(pixels='missing on one side')
            continue
        px = WP.P.diff_pixels(pa, pb)
        from PIL import Image, ImageChops
        box = ImageChops.difference(Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')).getbbox()
        rows[n] = dict(pixels=px, bbox=list(box) if box else None, expected=EXPECTED_DIFF.get(n))
    unexpected = {n: v for n, v in rows.items() if v.get('pixels') != 0 and n not in EXPECTED_DIFF}
    missing_expected = [n for n in EXPECTED_DIFF if rows.get(n, {}).get('pixels') == 0]
    april_same = sorted(n for n, v in rows.items() if v.get('pixels') == 0)
    same_within = {}
    for which, S in (('installed', A), ('candidate', B)):
        same_within[which] = dict(
            title_return=WP.P.diff_pixels(S / 'chart_title_before.png', S / 'april_title_after.png'),
            list_return=WP.P.diff_pixels(S / 'april_list_readable.png', S / 'april_list_return.png'))
    report = dict(author=C.AUTHOR, installed_sha256=a['candidate_sha256'], candidate_sha256=b['candidate_sha256'],
                  installed_pass=a['pass'], candidate_pass=b['pass'], pids=dict(installed=a.get('pid'), candidate=b.get('pid')),
                  shots=len(rows), identical=april_same, differing={n: v for n, v in rows.items() if v.get('pixels') != 0},
                  unexpected_differences=unexpected, expected_but_identical=missing_expected, within_run=same_within,
                  user_files_changed=dict(installed=a['user_files_changed'], candidate=b['user_files_changed']),
                  tour='KR_A29Tour of ' + str(TOUR) + ' minus its two May-only assertions (they assert the old May layout)',
                  status='APRIL_REGRESSION_PASS' if (a['pass'] and b['pass'] and not unexpected and not missing_expected
                                                     and all(v == 0 for w in same_within.values() for v in w.values()))
                  else 'APRIL_REGRESSION_DIFFERENCES')
    L.writej(O / 'evidence/april_regression.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'identical'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else ''
    if arg in ('installed', 'candidate'):
        run(arg)
    elif arg == 'compare':
        compare()
    else:
        raise SystemExit(__doc__)
