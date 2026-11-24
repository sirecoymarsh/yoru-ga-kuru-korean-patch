"""WI-009 native probe (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29): one muted private run of the candidate.

  (a) all 10 tabs, every page, 915 cells x 5 fixtures (all / none / mixed read under 전체 개방, mixed / none locked):
      E number, no △●○, state wording, no 단계, names (group tails trimmed), conditions kept, text inside the cell, no
      overlapping lines, adaptive 32x40 portraits (bounds, maximal count, exact +N, unread hidden), clean empty slots, header
  (b) 1,164 events as scene pages + 155 cards as card pages, read and unread (+ 35 groups mixed, 155 cards locked): E number,
      labels, two columns (gap 18, same line), board <= 680, fields inside, centred captions, unread masking (title, people,
      portraits, summary, choice, no quotes), 선택 only on the 20 choice scenes, summaries only April + E00011, replay button =
      KR_CCanPlay, button labels
  (c) the pickers of all 35 groups (chart context), mixed + locked: items, E numbers, unread 「장면 N」, no 단계, title lines,
      height, next page once then cancel
  (d) the in-game calendar picker (KR_CActive() false) on 3 cards: r19 dialog, names kept, cancel returns
  (e) real waits: list -> scene page -> 돌아가기; card page -> 장면 고르기 -> scene -> 돌아가기 -> picker -> 돌아가기 -> card page ->
      돌아가기; pixels of the list before / after; no parts after closing; title pixels before / after
Results: evidence/native_all_tabs_probe.json, evidence/native_all_tabs/*.png. Nothing is installed; the user's saves are hashed only.
"""
from pathlib import Path
import sys, json, re
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import w29common as C
import w29probe as WP
L = C.L
O = C.O
T = C.tables()
cells, t15 = T['cells'], T['t15']
cards = {c['k']: c for c in t15['cards']}
multi = sorted(k for k, c in cards.items() if c['size'] > 1)
first = {}
for i, c in enumerate(cells):
    first.setdefault(c['tab'], i)


def where(no):
    i = next(j for j, c in enumerate(cells) if c['no'] == no)
    c = cells[i]
    return c['tab'], (i - first[c['tab']]) // 12, i


q = lambda s: json.dumps(s, ensure_ascii=False)


def tree(ret, name, var, pairs, default):
    body = [f'{ret} {name}(int {var}) {{']
    for k, v in pairs:
        body.append(f'    if ({var} == {k}) return {v};')
    body.append(f'    return {default};\n}}')
    return '\n'.join(body)


tables = []
names = {i: C.plain(C.trim(c['name']), False) for i, c in enumerate(cells) if C.plain(C.trim(c['name']), False) != c['name']}
tables.append(tree('string', 'KR_W29PName', 'i', [(i, q(v)) for i, v in sorted(names.items())], '""'))
conds = {i: C.plain(c['cond'], False) for i, c in enumerate(cells) if C.plain(c['cond'], False) != c['cond']}
tables.append(tree('string', 'KR_W29PCondPlain', 'i', [(i, q(v)) for i, v in sorted(conds.items())], '""'))
dates = T['context']['dates']
tables.append(tree('bool', 'KR_W29PChoice', 'no', [(int(k), 'true') for k in sorted(dates, key=int)], 'false'))
tables.append(tree('string', 'KR_W29PDate', 'no', [(int(k), q(v)) for k, v in sorted(dates.items(), key=lambda x: int(x[0]))], '""'))
tables.append('int KR_W29PMultiN() { return %d; }' % len(multi))
tables.append(tree('int', 'KR_W29PMultiK', 'j', [(j, k) for j, k in enumerate(multi)], -1))
tables.append(tree('int', 'KR_W29PMultiM', 'j', [(j, cards[k]['month']) for j, k in enumerate(multi)], 4))
pick_heads = {k: '〓' + C.title_fit(C.plain(C.effective(T, 'heads', k, True), True)) for k in multi if k != 6}
assert all(C.effective(T, 'heads', k, True) == C.effective(T, 'heads', k, False) for k in multi)
tables.append(tree('string', 'KR_W29PPickHead', 'k', [(k, q(v)) for k, v in sorted(pick_heads.items())], '""'))
tabtags = ['t0_apr', 't1_may', 't2_jun', 't3_jul', 't4_aug', 't5_sep', 't6_oct', 't7_nov', 't8_memory', 't9_other']
tables.append(tree('string', 'KR_W29PTabTag', 't', [(t, q(v)) for t, v in enumerate(tabtags)], '"t"'))
SHOT_MIXED = [6, 49, 81, 101, 115, 151]
SHOT_LOCKED = [49, 81]
tables.append('int KR_W29PShotPicker(int k) {\n    string tag = KR_P22Get("PTag");\n    if (tag == "mixed") {\n'
              + ''.join(f'        if (k == {k}) return 1;\n' for k in SHOT_MIXED) + '    }\n    if (tag == "locked") {\n'
              + ''.join(f'        if (k == {k}) return 1;\n' for k in SHOT_LOCKED) + '    }\n    return 0;\n}')
jaf = (H / 'probe_calendar_all_tabs_20260929.jaf').read_text('utf-8').replace('/*TABLES*/', '\n\n'.join(tables))

# list shots: two-line names (May p2, Oct p4, Jun p16), locked, thumbnail group cells (Nov p1 / p2), recollection cast
shots = []
for no, tagname in [(30, 'may_twoline'), (512, 'oct_twoline'), (2410, 'jun_twoline')]:
    tab, page, _ = where(no)
    for mode in ('mixed', 'all'):
        shots.append(f'KR_W29PShotList({tab}, {page}, "{mode}", "1", "w29_list_{tagname}_p{page + 1}_{mode}");')
tab, page, _ = where(30)
shots.append(f'KR_W29PShotList({tab}, {page}, "mixed", "0", "w29_list_may_twoline_p{page + 1}_locked");')
for no, tagname in [(602, 'nov_cg_group_a'), (658, 'nov_cg_group_b')]:
    tab, page, _ = where(no)
    shots.append(f'KR_W29PShotList({tab}, {page}, "none", "0", "w29_list_{tagname}_p{page + 1}_locked");')
    shots.append(f'KR_W29PShotList({tab}, {page}, "all", "1", "w29_list_{tagname}_p{page + 1}_all");')
tab, page, _ = where(60205)
shots.append(f'KR_W29PShotList({tab}, {page}, "all", "1", "w29_list_memory_p{page + 1}_all");')
shots.append('KR_W29PShotList(9, 0, "none", "0", "w29_list_t9_other_locked");')
jaf = jaf.replace('    /*SHOTS_LIST*/', '\n'.join('    ' + s for s in shots))
boards = [
    ('97', 'KR_T19EvHead(97)', 1, 'all', '1', 'w29_detail_cast12_e00097'),
    ('328', 'KR_T19EvHead(328)', 1, 'all', '1', 'w29_detail_join_e00328'),
    ('323', 'KR_T19EvHead(323)', 1, 'all', '1', 'w29_detail_choice_read_e00323'),
    ('323', 'KR_T19EvHead(323)', 1, 'none', '1', 'w29_detail_choice_unread_e00323'),
    ('323', 'KR_T19EvHead(323)', 1, 'none', '0', 'w29_detail_choice_unread_locked_e00323'),
    ('KR_T9CardEntry(21)', 'KR_T19CardHead(21)', 21, 'mixed', '1', 'w29_detail_group21_mixed'),
    ('KR_T9CardEntry(81)', 'KR_T19CardHead(81)', 6, 'mixed', '1', 'w29_detail_group81_mixed'),
    ('11', 'KR_T19CardHead(7)', 1, 'all', '1', 'w29_detail_e00011_summary'),
    ('50205', 'KR_T19EvHead(50205)', 1, 'all', '1', 'w29_detail_memory_e50205'),
    ('1', 'KR_T19CardHead(1)', 1, 'all', '1', 'w29_detail_april_e00001'),
    ('10021', 'KR_T19EvHead(10021)', 1, 'all', '1', 'w29_detail_when_mark_cleaned_e10021'),
    ('10001', 'KR_T19EvHead(10001)', 1, 'all', '1', 'w29_detail_when_mark_cleaned_april_e10001'),
]
other = next(c['no'] for c in cells if c['tab'] == 9 and not c['card'])
boards.append((str(other), f'KR_T19EvHead({other})', 1, 'all', '1', f'w29_detail_other_e{other:05d}'))
assert cards[21]['size'] == 21 and cards[81]['size'] == 6 and cards[7]['entry'] == 11 and cards[1]['entry'] == 1
jaf = jaf.replace('    /*SHOTS_BOARD*/', '\n'.join(f'    KR_W29PShotBoard({a}, {b}, {c}, "{d}", "{e}", "{f}");' for a, b, c, d, e, f in boards))
ach = []
for k in (21, 81, 6):
    ach.append(f'    KR_P22SetN("PK", {k});\n    KR_P22SetPhase("w29_ach");\n    KR_T9StagePage({k}, {cards[k]["month"]});\n'
               f'    KR_W29PWhere("achievement picker card {k} return");\n    KR_W29PEnsure(KR_P22Phase() == "w29_ach_done", "achievement picker cancel returned");')
jaf = jaf.replace('    /*ACHIEVEMENT*/', '\n'.join(ach))
# flows: a non-card cell of May page 1 (scene page), the group card 81 (card page with 장면 고르기)
fl_i = next(i for i, c in enumerate(cells) if c['tab'] == 1 and not c['card'] and not c['thumb'])
fl_page = (fl_i - first[1]) // 12
fl_no = cells[fl_i]['no']
c81 = next(i for i, c in enumerate(cells) if c['card'] and c['ref'] == 100081)
tab81, page81 = cells[c81]['tab'], (c81 - first[cells[c81]['tab']]) // 12
flows = f'''    KR_CSet("ProbeRead", "mixed");
    KR_CSet("All", "1");
    KR_CShow(true);
    KR_W29PList(1, {fl_page});
    KR_P22Shot("w29_flow_list_before_detail");
    KR_P22SetPhase("w29_detail");
    KR_CClick(1, {fl_i});
    KR_W29PWhere("flow scene page E{fl_no:05d}");
    KR_W29PEnsure(KR_P22Phase() == "w29_detail_done", "scene page 돌아가기 returned");
    KR_W29PEnsure(KR_W29PNoBoard(), "board cleared after the scene page");
    KR_P22Shot("w29_flow_list_after_detail");
    KR_W29PList({tab81}, {page81});
    KR_P22Shot("w29_flow_list_before_card");
    KR_P22SetN("PK", 81);
    KR_P22SetPhase("w29_card1");
    KR_CClick({tab81}, {c81});
    KR_W29PWhere("flow card page 81");
    KR_W29PEnsure(KR_P22Phase() == "w29_card_done", "card page 돌아가기 returned");
    KR_W29PEnsure(KR_W29PNoBoard(), "board cleared after the card page");
    KR_P22Shot("w29_flow_list_after_card");'''
jaf = jaf.replace('    /*FLOWS*/', flows)
assert '/*' not in L.strip_comments(jaf) and '@@' not in jaf
(O / 'probe').mkdir(parents=True, exist_ok=True)
(O / 'probe/tour_readable.jaf').write_text(jaf, 'utf-8')
hook = '    if (KR_W29PDialog(ph, title)) return;'
P = WP.configure(O / 'probe', O / 'candidate', O / 'work', jaf, 'KR_W29PTour();', hook)
man = L.readj(O / 'candidate/manifest.json')
assert L.sha(O / 'candidate/NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
r = WP.run(P, 'native_all_tabs', timeout=2400)
log = r['log']
fails = [l for l in log if l.startswith('FAIL')]
r['fail_lines'] = fails
r['summary'] = [l for l in log if l.startswith(('DRAW', 'LISTS', 'DETAILS', 'PICKERS', 'CAST', 'END', 'PICKER '))]
minis = {}
for line in log:
    z = re.match(r'MINIS E(\d+) count=(\d+) shown=(\d+) left=(\d+)', line)
    if z:
        minis[int(z[1])] = dict(cast=int(z[2]), shown=int(z[3]), left=int(z[4]))
r['minis_all_read'] = minis
S = O / 'evidence/native_all_tabs'
pix = {}
for a, b in [('chart_title_before', 'w29_title_after'), ('w29_flow_list_before_detail', 'w29_flow_list_after_detail'),
             ('w29_flow_list_before_card', 'w29_flow_list_after_card')]:
    pa, pb = S / (a + '.png'), S / (b + '.png')
    pix[f'{a} vs {b}'] = WP.P.diff_pixels(pa, pb) if pa.exists() and pb.exists() else 'missing'
r['pixel_compare'] = pix
r['pass'] = (r.get('exit_code') == 0 and 'END' in log and not fails and not any(k in r for k in ('vm_error', 'message', 'timeout'))
             and not r['user_files_changed'] and all(v == 0 for v in pix.values()))
r['author'] = C.AUTHOR
L.writej(O / 'evidence/native_all_tabs_probe.json', r)
print(json.dumps({k: v for k, v in r.items() if k not in ('events', 'probe', 'log', 'minis_all_read')}, ensure_ascii=False, indent=1)[:6000])
