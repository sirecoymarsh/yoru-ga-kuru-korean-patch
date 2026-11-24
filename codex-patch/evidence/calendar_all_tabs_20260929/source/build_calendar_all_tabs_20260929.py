"""WI-009 build (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29; design Claude Fable 5.1): the approved April event-calendar UI on
every tab of the chart context, as an append-only candidate over the installed AIN b74ebc26... (label particles r2).

  1. baseline: live AIN / DLL / manifest / current.json = the frozen handoff values (else stop: rebase is the user's call)
  2. source/: copies of the live AIN + DLL and of the matching meta / raw-code dump; source_pointer.json = current.json
  3. design/: the design tables (cells, r15 / r19 tables, the three label patches) copied read-only; static gates on the Python
     twins of the display rules (w29common): no 「단계」 left, picker title lines <= 38 characters, items <= 38 units,
     dialog height <= 704, the 35 group names trimmed, the 20 choice dates
  4. helpers: design/calendar_all_tabs_20260929.jaf + the generated KR_W29Date + KR_W29Board derived from the approved
     KR_AS29Board text (title / fields / summary getter only)
  5. `ain edit --jaf` (declare) -> each KR_W29 body dumped, lowered to native opcodes -> `ain edit --jam` with the three
     forwarders (the current forwarder body dumped, its one CALLFUNC re-pointed: index, arguments, A_REF and return kept)
  6. gates: only those three metadata entries changed (address only), every other metadata key identical, original CODE prefix /
     STR0 prefix / MSG1 identical, the six pinned functions identical, every active opcode supported by the engine, no new part
     number literal, winmm.dll unchanged
Nothing is written outside staging/calendar_all_tabs_20260929.
"""
from pathlib import Path
import sys, re, json, struct, shutil, datetime
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import w29common as C
L = C.L
O, PRE, R = C.O, C.PRE, C.R
W = O / 'work/build'
L.TMP = O / 'work/tmp'

# ---- 1. baseline
cur = L.readj(L.CURRENT)
rt = Path(cur['runtime'])
assert L.sha(rt / 'NightRemaster.ain') == L.sha(PRE / 'candidate/NightRemaster.ain') == C.BASE_AIN, 'live build moved: rebase first'
assert L.sha(rt / 'winmm.dll') == C.BASE_DLL, 'live winmm.dll moved'
assert cur['manifest_sha256'] == C.BASE_MANIFEST and L.sha(Path(cur['manifest'])) == C.BASE_MANIFEST, 'live manifest moved'
for d in ('source', 'design', 'work/build', 'work/tmp', 'candidate', 'evidence', 'probe'):
    (O / d).mkdir(parents=True, exist_ok=True)
# ---- 2. source copies (once)
if not (O / 'source/NightRemaster.ain').exists():
    for n in ('NightRemaster.ain', 'winmm.dll'):
        shutil.copy2(rt / n, O / 'source' / n)
    for n in ('candidate_meta.json', 'candidate_raw_code.jam'):
        shutil.copy2(PRE / 'work/build' / n, O / 'source' / n)
    L.writej(O / 'source_pointer.json', cur)
assert L.readj(O / 'source_pointer.json') == cur, 'current.json changed since the source copy'
src = O / 'source/NightRemaster.ain'
assert L.sha(src) == C.BASE_AIN and L.sha(O / 'source/winmm.dll') == C.BASE_DLL
m = L.read_meta(O / 'source/candidate_meta.json')
names = [L.raw_symbol(m, f['index']) for f in m['functions']]
assert not any(n.startswith('KR_W29') for n in names), 'KR_W29 prefix already taken'
for n in ('KR_AM29Draw', 'KR_AS29Router', 'KR_U29Stages', 'KR_AS29Board', 'KR_AS29Story', 'KR_P29Story', 'KR_U29Field',
          'KR_U29State', 'KR_U29Seen', 'KR_U29Group', 'KR_AM29Render', 'KR_T19StagePage', 'KR_C24Draw'):
    assert names.count(n) == 1, n

# ---- 3. design tables (read-only copies) and static gates
copies = {'cells.json': R / 'staging/calendar_april_adaptive_minis_20260929/design/cells.json',
          'cast_evidence.json': R / 'staging/calendar_april_adaptive_minis_20260929/design/cast_evidence.json',
          'r15_tables.json': R / 'staging/calendar_april_summary_20260929/design/r15_tables.json',
          'r19_tables.json': R / 'staging/calendar_april_summary_20260929/design/r19_tables.json',
          'choices_label_patch.json': R / 'staging/calendar_choices_20260929/design/label_patch.json',
          'choice_context_label_patch.json': R / 'staging/calendar_choice_context_20260929/design/label_patch.json',
          'label_particles_patch.json': PRE / 'design/label_patch.json'}
for n, p in copies.items():
    if not (O / 'design' / n).exists():
        shutil.copy2(p, O / 'design' / n)
    assert L.sha(O / 'design' / n) == L.sha(p), n
T = C.tables()
cells, t15, t19 = T['cells'], T['t15'], T['t19']
cards = {c['k']: c for c in t15['cards']}
events = sorted(int(n) for n in t15['events'])
assert len(cells) == 915 and len(cards) == 155 and len(events) == 1164
multi = {k: c for k, c in cards.items() if c['size'] > 1}
assert len(multi) == 35
stage_events = {n for c in cards.values() for n in c['stages']}
cell_events = {c['no'] for c in cells if not c['card']}
assert stage_events | cell_events == set(events) and not stage_events & cell_events
dates = T['context']['dates']
assert len(dates) == 20 and all(re.fullmatch(r'\d+', k) for k in dates)
gates = {}
# list cells: names without the stage tail, no 단계 in name / when / condition after the rules
trimmed = {}
for c in cells:
    shown = C.plain(C.trim(c['name']), False)
    assert '단계' not in shown and '단계' not in C.plain(c['when'], False) and '단계' not in C.plain(c['cond'], False), c['no']
    if shown != c['name']:
        trimmed[c['no']] = shown
group_cells = [c for c in cells if c['card'] and cards[c['ref'] - 100000]['size'] > 1]
assert len(group_cells) == 35 and set(trimmed) == {c['no'] for c in group_cells}
assert trimmed[4] == '던전 · 공원 · 사건 1', trimmed[4]
two_line = sorted(c['no'] for c in cells if '\n' in c['name'])
two_line_after = sorted(no for no in two_line if '\n' in trimmed.get(no, next(c['name'] for c in cells if c['no'] == no)))
assert len(two_line) == 16 and not any(c['thumb'] for c in cells if '\n' in c['name'])
gates['list'] = dict(cells=len(cells), group_cells=len(group_cells), trimmed_names=trimmed, two_line_names=two_line,
                     two_line_names_after_trim=two_line_after, thumbnail_group_cells=sorted(c['no'] for c in group_cells if c['thumb']))
# detail titles / 언제 / 조건: no 단계 after the rule, both read states
for n in events:
    for read in (True, False):
        assert '단계' not in C.plain(C.effective(T, 'ev_head', n, read), False), n
        assert '단계' not in C.plain(C.when(T, n, read), False), n
        assert '단계' not in C.plain(C.effective(T, 'ev_short', n, read), False), n
for k in cards:
    for read in (True, False):
        assert '단계' not in C.plain(C.effective(T, 'heads', k, read), True), k
        assert '단계' not in C.plain(C.effective(T, 'conds', k, read), False), k
# no r19 title colour mark reaches the board's 언제 after KR_W29Clean
marked = sorted({n for n in events for read in (True, False) if any(ch in C.when(T, n, read) for ch in '†‡¶〓')})
for n in events:
    for read in (True, False):
        assert not any(ch in C.plain(C.clean(C.when(T, n, read)), False) for ch in '†‡¶〓'), n
gates['when_marks_cleaned'] = marked
# unread detail values never carry a quoted choice (「 / 『) through 언제 / 조건
for n in events:
    assert '「' not in C.when(T, n, False) and '『' not in C.when(T, n, False), n
for k in cards:
    v = C.effective(T, 'conds', k, False)
    assert '「' not in v and '『' not in v, k
# scene pickers (card 6 keeps the approved April picker; the rest use the generic one)
pickers = {}
for k, c in sorted(multi.items()):
    n = c['size']
    per, pages = C.picker_layout(n)
    worst = None
    for read in (True, False):
        head = C.title_fit(C.plain(C.effective(T, 'heads', k, read), True))
        second = f'†장면 고르기 · 전체 {n}개 중 {n}개 감상' + C.page_tag(pages - 1, pages)
        tl = ('〓' + head).split('\n') + [second]          # KR_W29Title marks every continuation line itself
        assert all(len(x) <= C.TITLE_LIMIT for x in tl), (k, tl)
        items = min(per, n) + (2 if pages > 1 else 0) + 1
        height = 64 + 34 * len(tl) + 48 * items
        assert height <= C.DIALOG_MAX, (k, height)
        if worst is None or height > worst['height']:
            worst = dict(title_lines=tl, items=items, height=height)
    widest = 0
    for j, no in enumerate(c['stages']):
        read_item = C.plain(C.effective(T, 'ev_short', no, True), False) + f' · E{no:05d} · 감상 완료'
        unread_item = f'장면 {j + 1} · E{no:05d} · 아직 보지 않음 · 잠김'
        widest = max(widest, C.units(read_item), C.units(unread_item))
    assert widest <= C.ITEM_CAP, (k, widest)
    pickers[k] = dict(size=n, per_page=per, pages=pages, widest_item_units=widest, generic=k != 6, **worst)
gates['pickers'] = pickers
# detail titles longer than the board's 34-character line break at " · " (never inside 「장면 N」 or a name)
wrapped = {}
for label, pairs in (('scene', [(n, C.plain(C.effective(T, 'ev_head', n, True), False)) for n in events]),
                     ('card', [(k, C.plain(C.effective(T, 'heads', k, True), cards[k]['size'] > 1)) for k in cards])):
    for key, title in pairs:
        if len(title) > 34:
            w = C.head_wrap(title)
            assert w is not None and all(len(x) <= 34 for x in w.split('\n')), (label, key, title)
            wrapped[f'{label}:{key}'] = w
april_ids = {n for c in cells if c['tab'] == 0 for n in (cards[c['ref'] - 100000]['stages'] if c['card'] else [c['no']])}
assert not any(k.startswith('scene:') and int(k[6:]) in april_ids for k in wrapped), 'an April title would change its wrap'
gates['detail_titles_rewrapped'] = wrapped
# bottom-row thumbnail cells in slot 8 / 9 move the footer note into the bottom bar (never on an April page)
first_of = {}
for i, c in enumerate(cells):
    first_of.setdefault(c['tab'], i)
low_pages = sorted({(c['tab'], (i - first_of[c['tab']]) // 12) for i, c in enumerate(cells) if c['thumb'] and (i - first_of[c['tab']]) % 12 in (8, 9)})
assert not any(t == 0 for t, _ in low_pages)
gates['footer_moved_pages'] = [dict(tab=t, page=p + 1) for t, p in low_pages]
gates['picker_first_lines'] = {k: C.title_fit(C.plain(C.effective(T, 'heads', k, True), True)) for k in multi if k != 6}
assert all(not re.search(r' · 장면 \d+개$', v) and len(v) <= 37 for v in gates['picker_first_lines'].values())
# two-line name cells: the short condition joined on one line (review F-01) keeps every character of the source
sc_short = {}
for c in cells:
    if c['no'] in two_line_after:
        sc_short[c['no']] = c['cond']
gates['two_line_cells_conditions'] = sc_short

# ---- 4. helpers JAF
def function(text, name):
    start = re.search(r'^(?:void|int|string|bool) ' + re.escape(name) + r'\(', text, re.M).start()
    pos = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[pos] == '{') - (text[pos] == '}')
        pos += 1
    return text[start:pos]


as29 = (R / 'staging/calendar_april_summary_20260929/work/build/helpers_readable.jaf').read_text('utf-8')
board = function(as29, 'KR_AS29Board')
for a, b in [('void KR_AS29Board(', 'void KR_W29Board('),
             ('    string title=KR_U29Head(no,head,stages);\n', '    string title=KR_W29Plain(head,stages>1);\n'),
             ('    int infoH=0; int infoW=0;\n', '    string story="";\n    if (read) story=KR_W29Story(no);\n    int infoH=0; int infoW=0;\n'),
             ('        string text=KR_AS29Info(no,stages,valueWidth,false);\n', '        string text=KR_W29Info(no,stages,valueWidth,false);\n'),
             ('        string labels=KR_AS29Info(no,stages,valueWidth,true);\n', '        string labels=KR_W29Info(no,stages,valueWidth,true);\n'),
             ('        if (read) {\n            string heading="줄거리";', '        if (story!="") {\n            string heading="줄거리";'),
             ('KR_B29Wrap(KR_AS29Story(no),storyWidth)', 'KR_B29Wrap(story,storyWidth)'),
             ('KR_CTint(KR_B29Wrap(title,34),KR_CGold())', 'KR_CTint(KR_W29HeadWrap(title),KR_CGold())')]:
    assert board.count(a) == 1, a
    board = board.replace(a, b)
assert 'KR_AS29' not in board and 'KR_U29Head' not in board
q = lambda s: json.dumps(s, ensure_ascii=False)
datefn = 'string KR_W29Date(int no) {\n' + ''.join(f'    if (no == {int(k)}) return {q(dates[k])};\n' for k in sorted(dates, key=int)) + '    return "";\n}\n'
jaf = (O / 'design/calendar_all_tabs_20260929.jaf').read_text('utf-8')
assert jaf.count('/*DATES*/') == 1 and jaf.count('/*BOARD*/') == 1
jaf = jaf.replace('/*DATES*/', datefn).replace('/*BOARD*/', board)
code = L.strip_comments(jaf)
bare = re.sub(r'"(?:[^"\\]|\\.)*"', '""', code)                  # string literals out: numbers in code only
assert not re.search(r'\b\d{9,}\b', bare), 'a raw part number literal in the new code'
assert not re.search(r'\b(?:SetGlobal|G_|system\.)', bare)
(W / 'helpers_readable.jaf').write_text(jaf, 'utf-8')
(W / 'helpers.jaf').write_text(L.jaf_literal_encode(code), 'utf-8')

# ---- 5. declare, lower, append, forward
decl = W / 'declared.ain'
out = O / 'candidate/NightRemaster.ain'
L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, src)
L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl)
dm = L.read_meta(W / 'declared_meta.json')
added = {f['name']: f['index'] for f in dm['functions'][len(m['functions']):]}
assert set(added) == C.ADDED, set(added) ^ C.ADDED
patch = []
for n in added:
    p = W / (n + '.jam')
    L.cmd('ain', 'dump', '--function', n, '-o', p, decl)
    jam = L.native_lower(p.read_text('utf-8'))
    jam = re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',
                 lambda z: '\t.LOCALASSIGN ' + z[1] + ' ' + str(struct.unpack('<i', struct.pack('<f', float(z[2])))[0]), jam)
    patch.append(L.clean(jam.replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), n))
for name, (old, new) in C.ROUTES.items():
    p = W / (name + '_original.jam')
    L.cmd('ain', 'dump', '--function', name, '-o', p, src)
    body = L.clean(p.read_text('utf-8'), name)
    assert body.count('\tCALLFUNC ') == 1 and body.count('\tCALLFUNC ' + old + '\n') == 1, (name, body)
    f = m['functions'][L.fid_of(m, name)]
    g = dm['functions'][added[new]]
    assert [a['type'] for a in f['arguments']] == [a['type'] for a in g['arguments']], (name, new)
    assert f['return-type'] == g['return-type'], (name, new)
    patch.append(body.replace('\tCALLFUNC ' + old + '\n', '\tCALLFUNC ' + new + '\n'))
(W / 'patch.jam').write_text('\n'.join(patch), 'utf-8')
L.cmd('ain', 'edit', '--jam', W / 'patch.jam', '-o', out, decl)
base = L.unpack(src.read_bytes())
raw = bytearray(L.unpack(out.read_bytes()))
size = struct.unpack_from('<I', raw, 12)[0]
struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))

# ---- 6. gates
L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', out)
nm = L.read_meta(W / 'candidate_meta.json')
changed = sorted(L.fid_of(m, n) for n in C.ROUTES)
assert [i for i, (a, b) in enumerate(zip(m['functions'], nm['functions'])) if a != b] == changed
for i in changed:
    assert {k: v for k, v in m['functions'][i].items() if k != 'address'} == {k: v for k, v in nm['functions'][i].items() if k != 'address'}
for k in m:
    if k != 'functions':
        assert m[k] == nm[k], k
assert len(nm['functions']) == len(m['functions']) + len(added)
for n in L.PINNED_ALL:
    assert m['functions'][L.fid_of(m, n)] == nm['functions'][L.fid_of(nm, n)], n
oldn = struct.unpack_from('<I', base, 12)[0]
raw = L.unpack(out.read_bytes())
assert raw[16:16 + oldn] == base[16:16 + oldn], 'original CODE prefix changed'
assert L.strings(raw)[2][:len(L.strings(base)[2])] == L.strings(base)[2], 'STR0 prefix changed'
assert L.raw_messages(out.read_bytes())[3] == L.raw_messages(src.read_bytes())[3], 'MSG1 changed'
L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out)
audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
L.writej(W / 'native_opcode_audit.json', audit)
# the three forwarders now call the KR_W29 targets (checked in the candidate's own dump)
for name, (old, new) in C.ROUTES.items():
    p = W / (name + '_candidate.jam')
    L.cmd('ain', 'dump', '--function', name, '-o', p, out)
    body = p.read_text('utf-8')
    assert body.count('\tCALLFUNC ' + new + '\n') == 1 and '\tCALLFUNC ' + old + '\n' not in body, name
shutil.copy2(O / 'source/winmm.dll', O / 'candidate/winmm.dll')
assert L.sha(O / 'candidate/winmm.dll') == C.BASE_DLL
now = datetime.datetime.now().astimezone().isoformat()
L.writej(O / 'design/static_gates.json', dict(author=C.AUTHOR, time=now, **gates))
L.writej(O / 'design/scope.json', dict(
    work_item='WI-009', author=C.AUTHOR, translator_model=C.AUTHOR, designer=C.DESIGNER, time=now,
    scope='The approved April list / detail / scene-picker UI on every tab (4..11월, 회상, 그 밖) of the event calendar (chart '
          'context, KR_CActive() true). The in-game calendar / achievement dialogs (KR_CActive() false) keep the r18 / r19 bodies '
          '(user 09-28: leave the in-game achievement chart as it is); only their integrity is probed.',
    tabs=list(range(10)), cells=len(cells), events=len(events), multi_stage_cards=sorted(multi),
    choice_context_dates=sorted(int(k) for k in dates), two_line_name_cells=two_line, two_line_after_trim=two_line_after,
    trimmed_group_names={str(k): v for k, v in trimmed.items()},
    stage_word_rule='N단계 -> 장면 N in titles / 언제 / 조건 / list conditions (card and group heads: 장면 N개); group names lose the '
                    'stage-count tail on the list, the count is on the state line 「전체 N개 중 M개 감상」',
    picker_rule='one column, 10 scenes on a single page, 8 per page with paging; unread scene = 「장면 N」; card 6 keeps the approved '
                'April picker (KR_U29Stages) unchanged; r2 (review F-04): every generic picker title drops the trailing 「 · 장면 N개」 of '
                'the card head (the count stands on the second line 「장면 고르기 · 전체 N개 중 M개 감상」)',
    condition_rule='r2 (review F-01): a list condition that does not fit is tried at 13 px, then joined on one line at 13 px (short '
                   'condition glue "", card condition glue " · "), and only then cut to its first line + 「…」',
    revision='r2', previous_candidate='3808a9c408375c78a7e3fe078fa36d9dd13d5e40ef2356cf7e69c5ba66ddb4b7 (evidence/r1)',
    review=str(C.R / 'staging/calendar_all_tabs_review_20260929/review.md'),
    new_functions=sorted(added), rerouted={k: v[1] for k, v in C.ROUTES.items()},
    previous_targets={k: v[0] for k, v in C.ROUTES.items()},
    preserves=['E identifiers', 'protagonist', 'portraits and cast masks', 'date and condition values', 'choice labels and the unread '
               'masking of KR_R29 / KR_S29 / KR_N29', 'replay eligibility', 'read flags', 'save schema', 'scenario messages',
               'April summaries and E00011', 'the approved April picker of card 6', 'the in-game calendar dialogs'],
    april_difference='detail titles of E00004..E00007 come from the shared KR_T19EvHead (「이즈미」) instead of the hand-written KR_U29Head '
                     '(「이즈미와」): the 09-29 particle correction reaches the April titles too; E10001 언제 loses the stray r19 title mark '
                     '「†」 + indent (KR_W29Clean, review F-03: kept as an intended defect fix)',
    installed=False))
L.writej(O / 'candidate/manifest.json', dict(
    status='ALL_TABS_STAGED_NATIVE_PENDING', revision='r2', previous_candidate='3808a9c408375c78a7e3fe078fa36d9dd13d5e40ef2356cf7e69c5ba66ddb4b7',
    source_sha256=C.BASE_AIN, live_sha256=C.BASE_AIN, source_manifest_sha256=C.BASE_MANIFEST,
    files={n: dict(sha256=L.sha(O / 'candidate' / n), size=(O / 'candidate' / n).stat().st_size) for n in ('NightRemaster.ain', 'winmm.dll')},
    changed_functions=list(C.ROUTES), rerouted={k: v[1] for k, v in C.ROUTES.items()}, added_functions=added,
    original_code_prefix_exact=True, original_strings_prefix_exact=True, messages_exact=True, serialized_schema_changes=0,
    pinned_functions_unchanged=L.PINNED_ALL, native_opcodes_supported=True, installed=False,
    translator_model=C.AUTHOR, author=C.AUTHOR, designer=C.DESIGNER))
print(json.dumps(dict(candidate=str(out), sha256=L.sha(out), helpers=len(added), changed=list(C.ROUTES),
                      picker_first_lines=len(gates['picker_first_lines']), two_line_after_trim=two_line_after), ensure_ascii=False))
