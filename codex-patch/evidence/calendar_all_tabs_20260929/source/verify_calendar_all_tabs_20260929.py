"""WI-009 install preflight (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29): cumulative, native and reversible-install gates
for the all-tabs calendar candidate, in the form of verify_calendar_label_particles_20260929.py.

  - pointer / live build unchanged since staging; candidate hashes = manifest = the probed AIN
  - native probe (evidence/native_all_tabs_probe.json) passed on this very candidate: 4,575 list cells, 2,638 boards + extras,
    35 x 2 pickers, 3 in-game pickers, the real waits, title / list pixels back, the user's saves untouched
  - April regression (evidence/april_regression.json): installed vs candidate, only the expected differences
  - r2: home-context probe (evidence/native_home_probe.json: calendar opened from the home menu, lists incl. the moved-footer
    pages, card page / picker, a representative replay and the return to the same tab / page, no parts on the home menu) and the
    r1 -> r2 screenshot comparison (evidence/r1_vs_r2_screens.json)
  - static: original CODE prefix, STR0 prefix, MSG1 identical; metadata identical except the three forwarders (address only);
    the six pinned functions identical; every active opcode supported by NightRemaster.exe; winmm.dll = the live one
  - saves: every resume image of the user's save folder (read only): each saved IP / return frame points at identical 6 code bytes
  - transaction fixture (publish_chart_r24.fixture: apply / restore / injected failure / tampering / interruption / whole
    disposable install) on this payload
  - wording map (design/wording_map.json) + its review (evidence/semantic_qa.json)
  - Microsoft Defender scan of the payload (scan_calendar_all_tabs_20260929.ps1 -> candidate/scan_report.json)
Writes evidence/install_preflight.json (status ALL_TABS_PREFLIGHT_PASS). Reads the runtime / saves only; installs nothing.
"""
from pathlib import Path
import sys, struct, json, re, subprocess, datetime
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import w29common as C
L = C.L
import publish_chart_r24 as P
O, R = C.O, C.R
E = O / 'evidence'
L.TMP = O / 'work/tmp'
now = datetime.datetime.now().astimezone().isoformat()

cur = L.readj(L.CURRENT)
rt = Path(cur['runtime'])
man = L.readj(O / 'candidate/manifest.json')
assert cur == L.readj(O / 'source_pointer.json'), 'current.json moved since staging: rebase'
assert L.sha(rt / 'NightRemaster.ain') == man['live_sha256'] == C.BASE_AIN, 'live AIN moved since staging'
files = {n: L.sha(O / 'candidate' / n) for n in ['NightRemaster.ain', 'winmm.dll']}
assert files == {n: v['sha256'] for n, v in man['files'].items()}

# ---- native probe on this candidate
p = L.readj(E / 'native_all_tabs_probe.json')
assert p['pass'] and p['candidate_sha256'] == files['NightRemaster.ain'], 'native probe not passed on this candidate'
assert not p['user_files_changed'] and not p['fail_lines'] and 'END' in p['log']
lists = [l for l in p['log'] if l.startswith('LISTS')]
assert len(lists) == 5 and ' cells=4575 ' in lists[-1] and lists[-1].endswith(' fails=0'), lists
details = [l for l in p['log'] if l.startswith('DETAILS read=')]
assert len(details) == 2 and all(' events=1164 ' in l for l in details), details
pickers = [l for l in p['log'] if l.startswith('PICKERS')]
assert len(pickers) == 2 and all(' cards=35 ' in l for l in pickers), pickers
assert all(v == 0 for v in p['pixel_compare'].values()), p['pixel_compare']
picker_pages = [l for l in p['log'] if l.startswith('PICKER ')]
minis = {int(k): v for k, v in p['minis_all_read'].items()}
assert len(minis) == 915
joined = [int(l.split(' joined_conditions=')[1].split()[0]) for l in lists]
# ---- r2: home context + replay (review F-05)
hp = L.readj(E / 'native_home_probe.json')
assert hp['pass'] and hp['candidate_sha256'] == files['NightRemaster.ain'] and not hp['user_files_changed'] and not hp['fail_lines']
# ---- r2: which screenshots changed since r1 (same probe shot names)
from PIL import Image, ImageChops
R1 = E / 'r1/evidence/native_all_tabs'
N2 = E / 'native_all_tabs'
screens = {}
for png in sorted(N2.glob('*.png')):
    old = R1 / png.name
    if not old.exists():
        screens[png.stem] = 'new in r2'
        continue
    box = ImageChops.difference(Image.open(old).convert('RGB'), Image.open(png).convert('RGB')).getbbox()
    screens[png.stem] = list(box) if box else 0
for png in sorted(R1.glob('*.png')):
    if not (N2 / png.name).exists():
        screens[png.stem] = 'only in r1'
L.writej(E / 'r1_vs_r2_screens.json', dict(author=C.AUTHOR, r1_candidate='3808a9c408375c78a7e3fe078fa36d9dd13d5e40ef2356cf7e69c5ba66ddb4b7',
                                           r2_candidate=files['NightRemaster.ain'], shots=len(screens),
                                           identical=sorted(k for k, v in screens.items() if v == 0),
                                           changed={k: v for k, v in screens.items() if v != 0}))
# ---- April regression
a = L.readj(E / 'april_regression.json')
assert a['status'] == 'APRIL_REGRESSION_PASS', a['status']
assert a['candidate_sha256'] == files['NightRemaster.ain'] and a['installed_sha256'] == C.BASE_AIN

# ---- static
base = L.unpack((O / 'source/NightRemaster.ain').read_bytes())
raw = L.unpack((O / 'candidate/NightRemaster.ain').read_bytes())
oldn = struct.unpack_from('<I', base, 12)[0]
assert raw[16:16 + oldn] == base[16:16 + oldn], 'original CODE prefix changed'
m = L.read_meta(O / 'source/candidate_meta.json')
nm = L.read_meta(O / 'work/build/candidate_meta.json')
changed = []
for f, g in zip(m['functions'], nm['functions']):
    if f != g:
        assert L.raw_symbol(m, f['index']) in C.ROUTES, f['name']
        assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}
        changed.append(L.raw_symbol(m, f['index']))
assert sorted(changed) == sorted(C.ROUTES)
added = [L.raw_symbol(nm, f['index']) for f in nm['functions'][len(m['functions']):]]
assert set(added) == C.ADDED and len(added) == len(C.ADDED)
for k in m:
    if k != 'functions':
        assert m[k] == nm[k], k
for n in L.PINNED_ALL:
    assert m['functions'][L.fid_of(m, n)] == nm['functions'][L.fid_of(nm, n)], n
assert L.strings(raw)[2][:len(L.strings(base)[2])] == L.strings(base)[2], 'STR0 prefix changed'
assert L.raw_messages((O / 'source/NightRemaster.ain').read_bytes())[3] == L.raw_messages((O / 'candidate/NightRemaster.ain').read_bytes())[3]
assert (rt / 'winmm.dll').read_bytes() == (O / 'candidate/winmm.dll').read_bytes(), 'winmm.dll differs from the live one'
audit = L.audit(O / 'candidate/NightRemaster.ain', O / 'work/build/candidate_meta.json', O / 'work/build/candidate_raw_code.jam', rt / 'NightRemaster.exe')
assert audit['all_active_opcodes_supported'] and audit['ain_sha256'] == files['NightRemaster.ain']

# ---- saves (read only): saved IPs / return frames point at unchanged code
saves, frames, other = [], [], []
for path in sorted(L.SAVES.glob('NightR*.asd')):
    if not path.stem[6:].isdigit():
        continue
    r = L.save_records(path)
    if r is None:
        other.append(path.name)
        continue
    saves.append(path.name)
    for fr in [r['ip']] + r['returns']:
        ad = fr['address']
        if ad < 0:
            continue
        assert base[16 + ad:22 + ad] == raw[16 + ad:22 + ad], (path.name, fr)
        frames.append(dict(save=path.name, **fr))
L.writej(E / 'save_frames.json', dict(time=now, saves=saves, non_resume_slots=other, frames=frames))

# ---- transaction fixture on this payload
P.FILES = list(files)
P.O = O / 'candidate'
L.WORK = O / 'work'
tx = P.fixture()
assert tx['status'] == 'TRANSACTION_FIXTURE_PASS' and tx['payload'] == files
L.writej(E / 'transaction_verification.json', tx)

# ---- wording map and its review
T = C.tables()
wm = C.wording_map(T)
wm_path = O / 'design/wording_map.json'
L.writej(wm_path, dict(author=C.AUTHOR, translator_model=C.AUTHOR, rule='N단계 -> 장면 N (card / group heads: 장면 N개); group list names '
                       'lose the stage-count tail; a picker title over 37 characters loses its trailing 장면 N개', **wm))
issues = []
for part in ('list_conditions', 'card_heads', 'scene_heads', 'when', 'card_conditions'):
    for key, row in wm[part].items():
        src = C.clean(row['before']) if part == 'when' else row['before']
        if C.norm(row['after']) != C.norm(src) or C.plain(src, part == 'card_heads' and row.get('size', 1) > 1) != row['after']:
            issues.append((part, key))
        if any(ch in row['after'] for ch in '†‡¶〓'):
            issues.append((part, key, 'colour mark left'))
        if '단계' in row['after']:
            issues.append((part, key, 'still 단계'))
for key, row in wm['list_names'].items():
    tail = row['before'][len(row['after']):]
    if not row['before'].startswith(row['after']) or not re.fullmatch(r'(?: · |\n| )\d+단계', tail):
        issues.append(('list_names', key))
for key, row in wm['picker_titles'].items():
    if not row['before'].startswith(row['after']) or not re.fullmatch(r' · 장면 \d+개', row['before'][len(row['after']):]):
        issues.append(('picker_titles', key))
qa = dict(status='PASS' if not issues else 'FAIL', translator_model=C.AUTHOR, reviewer=C.AUTHOR, time=now,
          translation_map=str(wm_path), translation_map_sha256=L.sha(wm_path), reviewed_fields=sum(wm['counts'].values()),
          counts=wm['counts'], unresolved=issues,
          checks=['Every changed display string equals the rule applied to its r19 / chart source, and both reduce to the same text when '
                  'every stage number spelling (N단계 / 장면 N / 장면 N개) is reduced to N: no other character changes.',
                  '언제 only: the r19 dialog-title continuation 「\\n† + full-width indent」 (23 events, 46 read / unread strings) becomes '
                  '「 · 」 (KR_W29Clean); no colour mark († ‡ ¶ 〓) is left in any changed string.',
                  'No 단계 left in any changed string; digits preserved.',
                  'Group list names lose exactly the stage-count tail (" · N단계" / "\\nN단계"); the count is on the state line.',
                  'r2 (review F-04): every generic picker title (34 groups; card 6 keeps the approved April picker) loses exactly its '
                  'trailing 「 · 장면 N개」 (the count is on the second title line).',
                  'r2 (review F-01): list conditions keep every character - a two-line-name cell shows the short condition joined on one '
                  'line at 13 px instead of its first line (native probe: whole-condition comparison on 4,575 cells).',
                  'Unread masks of KR_R29 / KR_S29 / KR_N29 untouched (no 단계 in them); choice wording, dates and join descriptions '
                  'reach the board through the existing getters (native probe: 20 choice scenes read / unread).',
                  'The full wording map was read by the author: readable Korean; 「보스 장면 16 본 뒤」 style conditions keep the source order.'],
          review_scope='Automated inverse-rule review of every changed field + the author\'s full read; the native probe verified every '
                       'rendered cell / board / picker. No independent reviewer (the task forbade sub-agents).')
L.writej(E / 'semantic_qa.json', qa)
assert qa['status'] == 'PASS', issues[:10]

# ---- Defender scan of this payload
scan = O / 'candidate/scan_report.json'
if not (scan.exists() and L.readj(scan).get('files') == files):
    q = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
                        str(H / 'scan_calendar_all_tabs_20260929.ps1')], capture_output=True, timeout=1800, env=L.env())
    assert q.returncode == 0, q.stderr.decode('utf-8', 'replace')[-2000:]
sc = L.readj(scan)
assert sc['status'] == 'SCANNED_NO_TARGET_DETECTIONS' and sc['files'] == files, sc

report = dict(status='ALL_TABS_PREFLIGHT_PASS', time=now, files=files, source_sha256=C.BASE_AIN, source_manifest_sha256=C.BASE_MANIFEST,
              original_code_prefix_exact=True, original_messages_exact=True, original_strings_prefix_exact=True, serialized_schema_changes=0,
              pinned_functions_unchanged=L.PINNED_ALL, changed_forwarders={n: C.ROUTES[n][1] for n in sorted(changed)},
              added_functions=added, native_opcodes_supported=True, existing_resume_saves=len(saves), non_resume_slots=len(other),
              saved_return_frames=len(frames), dll_unchanged=True, transaction_fixture_pass=True, defender=sc['status'],
              native_probe=dict(pid=p.get('pid'), seconds=p.get('seconds'), list_cells_checked=4575, list_fixtures=5,
                                detail_boards=int(details[-1].split(' boards=')[1].split()[0]), events_per_state=1164,
                                picker_pages=len(picker_pages), pickers_per_pass=35, achievement_pickers=3,
                                real_wait_flows=['list -> scene page -> 돌아가기', 'list -> card page -> 장면 고르기 -> scene -> 돌아가기 -> '
                                                 'picker -> 돌아가기 -> card page -> 돌아가기'],
                                pixel_compare=p['pixel_compare'], cells_more_than_3_portraits=sum(1 for v in minis.values() if v['shown'] > 3),
                                max_portraits=max(v['shown'] for v in minis.values()),
                                overflow_badges=sum(1 for v in minis.values() if v['cast'] > v['shown']), shots=len(p['shots'])),
              april_regression=dict(status=a['status'], identical=len(a['identical']), differing=sorted(a['differing']),
                                    unexpected=a['unexpected_differences']),
              revision=man.get('revision'), previous_candidate=man.get('previous_candidate'),
              joined_conditions_per_list_pass=joined,
              home_probe=dict(pid=hp.get('pid'), seconds=hp.get('seconds'), shots=len(hp['shots']), home_save=hp['home_save'],
                              summary=[l for l in hp['summary'] if l.startswith(('W29', 'RESUMED', 'RETURNED', 'REPLAY', 'END'))]),
              r1_vs_r2_screens=str(E / 'r1_vs_r2_screens.json'),
              review_fixes={'F-01': 'fixed: joined one-line condition at 13 px before any cut; probe compares the whole condition',
                            'F-02': 'partly: whole-condition comparison, every picker page visited, exact picker first line; board titles '
                                    'still structural',
                            'F-03': 'kept (intended defect fix, E10001 언제), recorded in 인계_WI009.md',
                            'F-04': 'fixed: 「 · 장면 N개」 dropped from every generic picker title (card 6 = April picker unchanged)',
                            'F-05': 'added: home-context native probe with a representative replay (evidence/native_home_probe.json)',
                            'F-06': 'fixed: install only on --install, usage otherwise; --check confirms every source copy',
                            'F-07': 'recorded only (narrow value column wraps inside words on 6-column boards)'},
              wording=dict(map=str(wm_path), counts=wm['counts'], qa=qa['status']),
              translator_model=C.AUTHOR, author=C.AUTHOR, designer=C.DESIGNER,
              limitations=['Display-only: list / detail / scene-picker layers of the event calendar (chart context). No scenario, choice '
                           'outcome, read-record or save-layout edits.',
                           'The in-game calendar / achievement dialogs (KR_CActive() false) keep their r18 / r19 bodies (user 09-28); only '
                           'their opening, names and cancel were probed.',
                           'Native diagnostics used a muted private copy with scripted read fixtures and modal answers, not an all-route '
                           'gameplay test; one representative replay (E01101 from the home context) was run, not every kind.',
                           'Narrow value columns of 6-column boards (8+ portraits) still wrap inside words (review F-07, recorded).'])
L.writej(E / 'install_preflight.json', report)
man['status'] = 'ALL_TABS_PREFLIGHT_PASS_NOT_INSTALLED'
man['preflight_sha256'] = L.sha(E / 'install_preflight.json')
L.writej(O / 'candidate/manifest.json', man)
print(json.dumps({k: v for k, v in report.items() if k != 'added_functions'}, ensure_ascii=False, indent=1))
