# -*- coding: utf-8 -*-
"""Make publish_overview.py from calendar_redesign_20261017/publish_home.py (read only): the same journaled install / restore
transaction, fixture and readiness, with the overview payload (NightRemaster.ain only), evidence checks, contract and notes.
Stage 2 of the calendar / completion-rate redesign (2026-10-18)."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'calendar_redesign_20261017' / 'publish_home.py').read_text('utf8')


def func(text, name, new):
    """Replace a top-level def (up to the next top-level def / class / section comment)."""
    m = re.search(r'\ndef %s\(.*?(?=\n\n\n(?:def |class |# -))' % re.escape(name), text, re.S)
    assert m, name
    return text[:m.start()] + '\n' + new.strip('\n') + text[m.end():]


def once(text, a, b):
    assert text.count(a) == 1, a[:80]
    return text.replace(a, b)


DOC = '''"""Claude Opus 5.5 (2026-10-18): install / restore of the event-calendar overview, stage 2 of the calendar / completion-rate
redesign (user, 10-17: the calendar does not feel like an overview of the whole story, too many pages, cells say little, no
per-character view; mockup approved 「왜 이리 멋져? 좋아 가자」; 10-18 「개선된 이벤트 캘린더도 적용됐어?」), made from
publish_home.py (same journaled transaction, same KRMenu scratch rule).

  python publish_overview.py --stage      check candidate/manifest.json against the built AIN (the payload is the AIN only)
  python publish_overview.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_overview.py --contract   write the Codex contract draft required_calendar_overview_20261018.json
  python publish_overview.py --fixture    transaction fixture on disposable files under calendar_overview_20261018/work (no runtime)
  python publish_overview.py --verify     read-only readiness check (hashes, native probes, scan, fixture, saved stacks, contracts)
  python publish_overview.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_overview.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_XV* layer). PACT/EX/FNL, the Manual chart and winmm.dll untouched. One journaled transaction as
publish_home.py: PREPARED -> atomic hash-checked replacement -> runtime manifest + current.json + every required_*.json present at
install time (calendar_overview_20261018_preserved_by) + new required_calendar_overview_20261018.json +
latest_worked_translation.json + progress.md note -> exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure
rolls back; --restore returns the exact pre-install state.
"""'''
src = DOC + src[src.index('\nfrom pathlib import Path'):]
src = once(src, 'import hvlib as L', 'import ovlib as L')
for a, b in [('home_panel_20261017', 'calendar_overview_20261018'), ('HOME_PANEL_20261017', 'CALENDAR_OVERVIEW_20261018'),
             ('.home-', '.overview-'), ('home-copy.tmp', 'overview-copy.tmp'), ('publish_home', 'publish_overview')]:
    src = src.replace(a, b)
src = once(src, "FILES = ['NightRemaster.ain', 'NightRemasterPact.afa']\nPACT_SRC = HERE / 'candidate' / 'NightRemasterPact.afa'\nPACT_EVID = HERE / 'work' / 'pact' / 'build_evidence.json'\n",
           "FILES = ['NightRemaster.ain']\nPROBES = ['probe_overview.json', 'probe_overview_NightR16.json', 'probe_overview_TITLE.json']\n")
a = src.index("NO_RESTORE = ('Codex must never run")
b = src.index('\n\n\ndef js(')
src = src[:a] + '''NO_RESTORE = ('Codex must never run publish_overview*.py --restore or otherwise remove the calendar-overview layer: KR_XV* '
              'functions; KR_CDo calls KR_XVChart where it called KR_CChart (the title and home chart requests open the month x row '
              'overview board first; a month head or a cell opens the month view KR_CChart on that month and closing it returns to '
              'the board); KR_C24Chart calls KR_XVWait where it called KR_CWait (right after a jump from the board the month view '
              'answers its first wait with that month\\'s tab button, then waits as before). The board is drawn on parts '
              '2026101800-2026102440 above every AddArea part (as KR_F28ChartFrame does). Companion rows follow the home panel '
              'rule (KR_T20Joined at home; on the title screen a companion shows once any of their scenes was read in some save). '
              'It is user-requested: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry '
              'it forward; restore is reserved for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_overview*.py --restore 를 실행하거나 캘린더 한눈에 보기 층(KR_XV* 함수; KR_CDo 의 KR_CChart 호출 → '
                 'KR_XVChart(타이틀 · 본거지의 캘린더 요청이 먼저 달 × 줄 판을 연다; 달 머리나 칸을 누르면 그 달의 달별 화면 KR_CChart, 닫으면 '
                 '판으로 돌아옴); KR_C24Chart 의 KR_CWait 호출 → KR_XVWait(판에서 넘어온 직후 첫 대기만 그 달 탭 단추로 답함))을 지우지 '
                 '않는다. 판의 부품 번호는 2026101800~2026102440, Z 는 AddArea 부품 위(KR_F28ChartFrame 과 같은 방식). 동료 줄은 본거지 '
                 '패널 규칙(본거지는 KR_T20Joined, 타이틀은 어느 세이브에서든 그 동료의 장면을 읽었으면). 사용자가 요청한 것이다: 깨끗한 '
                 '기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude event-calendar overview layer (2026-10-18, stage 2 of the user-requested calendar / completion-rate redesign). '
    + NO_RESTORE + ' Payload: NightRemaster.ain only. KR_XV* functions appended; no original function relocated; no new global '
    '/ struct member; 2 same-length CALLFUNC operand swaps. Row of every event baked as KR_XVLaneNo (schedule.json lanes), looked '
    'up by KR_CCellEv, so later calendar layers may reorder cells. The auto-nav pins stay (index, address and every code byte): '
    + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE + ' Every earlier contract stays in force.')''' + src[b:]
src = func(src, 'stage', '''
def stage():
    man = read(O / 'manifest.json')
    want = man['files']['NightRemaster.ain']['sha256']
    assert L.sha(O / 'NightRemaster.ain') == want, 'candidate AIN differs from its manifest: rebuild'
    assert man['pact_changed'] is False and set(man['files']) == set(FILES), man['files'].keys()
    return {n: man['files'][n]['sha256'] for n in FILES}
''')
src = func(src, 'probe_home_ok', '''
def probe_overview_ok(p):
    lg = p.get('log') or []
    return bool(lg and 'END' in lg and 'FAILS 0' in lg and p.get('user_save_folder_unchanged') and not p.get('vm_error')
                and not p.get('events') and not p.get('timeout') and not p.get('fails') and p.get('oks', 0) >= 5)


def probes_ok(after):
    out = {}
    for n in PROBES:
        p = read(L.EVID / n) if (L.EVID / n).exists() else {}
        out[n] = bool(p.get('candidate_ain') == after['NightRemaster.ain'] and probe_overview_ok(p))
    return out
''')
src = func(src, 'draft_contract', '''
def draft_contract():
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    pk = probes_ok(after)
    assert all(pk.values()), ('rerun the probes for this candidate', pk)
    scan_ = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    rc = read(L.WORK / 'resume_offset_check.json')
    assert rc['candidate_ain'] == after['NightRemaster.ain'] and not rc['problems'], 'rerun work/resume_offset_check.py'
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, code=man['pinned_functions'].get(name))
    still = {}
    for name in PINNED_NEW:
        fid = L.fid_of(nm, name)
        still[name] = dict(index=fid, address=nm['functions'][fid]['address'], code=man['pinned_functions'].get(name))
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    probes = {}
    for n in PROBES:
        p = read(L.EVID / n)
        probes[n] = dict(passed=pk[n], oks=p.get('oks'), fails=p.get('fails'), seconds=p.get('seconds'), save=p.get('save'),
                         shots=[Path(x).name for x in p.get('shots', [])])
    return dict(
        status='CALENDAR_OVERVIEW_20261018_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files=after, candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False,
        ex_changed=False, fnl_changed=False, chart_changed=False, hook_changed=False,
        no_restore_rule=NO_RESTORE, added_functions=len(ids), added_function_names=sorted(ids),
        same_length_sites=man['same_length_sites'], message_box_sites=[], relocated_original_functions=[],
        pinned_addresses=pinned, pinned_from_now_on=still, baked=man.get('baked'),
        saved_stacks=dict(resume_saves=rc['stats']['resume_saves'], frames=rc['stats']['frames'],
                          frames_in_changed_functions=rc['stats'].get('frames_in_changed_functions', 0), problems=len(rc['problems']),
                          changed_functions_on_stacks=sorted({h['fn'] for h in rc['frames_in_changed_functions']}),
                          check=str(L.WORK / 'resume_offset_check.json'), check_sha256=L.sha(L.WORK / 'resume_offset_check.json'),
                          note='read-only check of the user\\'s saves: every saved frame keeps its crc (the AIN function table is '
                               'unchanged), no original function moved, no frame resumes at or inside a swapped instruction'),
        verification=dict(probes=probes, defender=scan_.get('status'), transaction_fixture=fx['status'] if fx else 'NOT_RUN',
                          not_played_natively='real mouse clicks on the board (the probes end the wait with the part number a '
                                              'click returns); the cell replay paths are the month view\\'s own, unchanged'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_overview_20261018_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)
''')
src = once(src, "self.note_title = note_title or '본거지 달성률 패널 새 모양 (Claude Opus 5.5; 전투 템포 설치본 위)'",
           "self.note_title = note_title or '이벤트 캘린더 한눈에 보기 (Claude Opus 5.5; 본거지 달성률 패널 설치본 위)'")
src = once(src, '''        for n in ['probe_home.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        for f in (L.WORK / 'pact').glob('*.pactex'):
            shutil.copy2(f, ev / 'source' / f.name)
        shutil.copy2(PACT_EVID, ev / 'source' / 'pact_build_evidence.json')''', '''        for n in PROBES:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        for f in L.EVID.glob('probe_*.png'):
            shutil.copy2(f, ev / 'source' / 'probe' / f.name)''')
src = once(src, '''        nm['next'] = ('User screen check: 본거지 왼쪽 달성률 패널(얼굴 · 막대, 「이 세이브」 · 「모든 세이브 합산」 구역); 인물 단추에 마우스를 '
                      '올리면 금색 테두리가 되는지; 인물 단추를 누르면 그 인물의 남은 이벤트 창, 「이벤트 캘린더」 단추를 누르면 캘린더가 '
                      '열리는지; 던전 등 본거지 밖(달성률 항상 표시)에서는 캘린더 단추 없이 숫자만 보이는지.')''',
           '''        nm['next'] = ('User screen check: 캘린더를 열면 한눈에 보기(달 × 줄 판)가 먼저 뜨는지; 달이나 칸을 누르면 그 달 화면, 닫으면 판으로 '
                      '돌아오는지; 「이 세이브 / 모든 세이브」 전환; 합류 전 동료 줄이 안 보이는지; 타이틀의 모드 메뉴로 열어도 같은지.')''')
a = src.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = src.index("        write(root / 'progress.md'")
src = src[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 이벤트 캘린더 한눈에 보기(사용자 10-17 캘린더 불편 · 시안 승인, 10-18 「개선된 이벤트 캘린더도 적용됐어?」): 캘린더를 열면 "
                "달(4~11월) × 줄(본편 · 합류한 동료 · 던전 동행) 판이 먼저 뜬다. 칸마다 본 수/전체와 막대(본 · 놓침 · 남음 · 아직), "
                "「이 세이브 / 모든 세이브」 전환, 회상 · 그 밖 단추. 달 머리나 칸을 누르면 그 달의 달별 화면, 닫으면 판으로 돌아온다.\\n"
                "- KR_CDo 의 KR_CChart → KR_XVChart, KR_C24Chart 의 KR_CWait → KR_XVWait(같은 길이 CALLFUNC 피연산자 2곳). AIN 만, 원본 함수 "
                "이전 0, 새 전역 · 구조체 필드 0. 고정 함수(r18~r23 · 오토 내비 " + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) publish_overview.py --restore.\\n")
''' + src[b:]
# fixture: one payload file (as battle_pace_20261016/work/make_publish.py did)
src = once(src, '''    os.unlink(l / FILES[1])
    shared = f / 'shared_copy.afa'
    shutil.copy2(b / FILES[1], shared)
    os.link(shared, l / FILES[1])
    pair_apply(s, b, l, before, after)
    assert L.sha(shared) == before[FILES[1]], 'the swap wrote through a hard link\'''', '''    os.unlink(l / FILES[-1])
    shared = f / 'shared_copy.ain'
    shutil.copy2(b / FILES[-1], shared)
    os.link(shared, l / FILES[-1])
    pair_apply(s, b, l, before, after)
    assert L.sha(shared) == before[FILES[-1]], 'the swap wrote through a hard link\'''')
src = once(src, '''    ctx, rt, rec = fake_project(f, 'proj_pact_missing_in_recovery', FILES, recovery_has={'NightRemaster.ain'})
    tree0 = snapshot_folder(ctx.root)
    rep = transact(ctx)
    j = read(ctx.evidence / 'journal.json')
    assert j['status'] == 'COMMITTED' and rep['recovery_lacks'] == ['NightRemasterPact.afa'] and rep['recovery_hashed'] == ['NightRemaster.ain']''',
           '''    ctx, rt, rec = fake_project(f, 'proj_ain_only', FILES, recovery_has={'NightRemaster.ain'})
    tree0 = snapshot_folder(ctx.root)
    rep = transact(ctx)
    j = read(ctx.evidence / 'journal.json')
    assert j['status'] == 'COMMITTED' and rep['recovery_lacks'] == [] and rep['recovery_hashed'] == ['NightRemaster.ain']''')
# readiness: no PACT in the payload; the three probes
src = once(src, '''    man = read(O / 'manifest.json')
    if 'NightRemasterPact.afa' not in man['files']:
        return False, dict(status='NOT_READY', issues=['the PACT is not staged into candidate/ (run --stage)'])
    after = {n: man['files'][n]['sha256'] for n in FILES}''', '''    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}''')
src = once(src, '''    if L.sha(PACT_SRC) != after['NightRemasterPact.afa']:
        issues.append('NightRemasterPact.afa differs from the staged PACT: rerun --stage')
''', '')
src = once(src, '''    pm = read(L.EVID / 'probe_home.json') if (L.EVID / 'probe_home.json').exists() else {}
    if pm.get('candidate_ain') != after['NightRemaster.ain'] or pm.get('candidate_pact') != after['NightRemasterPact.afa'] or not probe_home_ok(pm):
        issues.append('native probe (probe_home.py) missing, failing or for another candidate')''', '''    pk = probes_ok(after)
    if not all(pk.values()):
        issues.append('native probes (probe_overview.py: NightR47, NightR16, TITLE) missing, failing or for another candidate: ' + str(pk))''')
src = once(src, "str(HERE.parent / 'autonav_20261015' / 'scan_autonav.ps1')", "str(HERE / 'scan_overview.ps1')")
assert 'probe_home' not in src and 'PACT_SRC' not in src and 'PACT_EVID' not in src and 'hvlib' not in src, 'leftover stage-1 checks'
(HERE / 'publish_overview.py').write_text(src, 'utf8')
print('ok', len(src.splitlines()), 'lines')
