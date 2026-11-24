# -*- coding: utf-8 -*-
"""Make publish_deadline.py from calendar_redesign_20261017/publish_home.py (read only; it carries the PACT handling: staging
checks, the panel evidence, the two-file fixture), with the deadline-layer names, contract and notes, and the three probes (as
the later stages). Also scan_deadline.ps1 (both payload files) and work/resume_offset_check.py."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
HV = HERE.parent / 'calendar_redesign_20261017'
src = (HV / 'publish_home.py').read_text('utf8')


def once(text, a, b):
    assert text.count(a) == 1, (a[:90], text.count(a))
    return text.replace(a, b)


def between(text, a, b, new):
    i = text.index(a)
    j = text.index(b, i)
    return text[:i] + new + text[j:]


DOC = '''"""Claude Opus 5.5 (2026-10-18): install / restore of the deadline alert (user, 10-18: 「2번은 괜찮네 시간 제한 있는 이벤트
알려주기」, then 「…기한 알림은 시안대로 만들어 줘.」), made from publish_home.py (same journaled transaction, same KRMenu scratch rule).

  python publish_deadline.py --stage      check candidate/manifest.json against the built AIN and PACT (both built into candidate/)
  python publish_deadline.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_deadline.py --contract   write the Codex contract draft required_calendar_deadline_20261018.json
  python publish_deadline.py --fixture    transaction fixture on disposable files under calendar_deadline_20261018/work (no runtime)
  python publish_deadline.py --verify     read-only readiness check (hashes, native probes, scan, fixture, saved stacks, contracts)
  python publish_deadline.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_deadline.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_DL* layer) + NightRemasterPact.afa (entry 177 Game/Scenes/Common/AddArea.pactex: the KR_HomeRate
group gets the KR_DL_* parts of the right-margin panel). EX/FNL, the Manual chart and winmm.dll untouched. One journaled transaction
as publish_home.py: PREPARED -> atomic hash-checked replacement -> runtime manifest + current.json + every required_*.json present at
install time (calendar_deadline_20261018_preserved_by) + new required_calendar_deadline_20261018.json + latest_worked_translation.json
+ progress.md note -> exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back; --restore returns the
exact pre-install state.
"""'''
src = DOC + src[src.index('\nfrom pathlib import Path'):]
src = once(src, 'import hvlib as L', 'import dllib as L')
for a, b in [('home_panel_20261017', 'calendar_deadline_20261018'), ('HOME_PANEL_20261017', 'CALENDAR_DEADLINE_20261018'),
             ('.home-', '.deadline-'), ('home-copy.tmp', 'deadline-copy.tmp'), ('publish_home', 'publish_deadline'), ('probe_home', 'probe_deadline')]:
    src = src.replace(a, b)
src = once(src, "PACT_EVID = HERE / 'work' / 'pact' / 'build_evidence.json'\n",
           "PACT_EVID = HERE / 'work' / 'pact' / 'build_evidence.json'\nPROBES = ['probe_deadline.json', 'probe_deadline_NightR16.json', 'probe_deadline_TITLE.json']\n")
src = between(src, "NO_RESTORE = ('Codex must never run", "\n\n\ndef js(", '''NO_RESTORE = ('Codex must never run publish_deadline*.py --restore or otherwise remove the deadline-alert layer: KR_DL* functions '
              'and 5 CALLFUNC operand swaps - KR_T8HomeMenuOpen and KR_T8HomeMenuClose call KR_DLClickable where they called '
              'KR_HVClickable (the left panel as before, then the right-margin deadline panel is filled and shown while the home top '
              'menu waits and hidden when it closes); KR_HVPick calls KR_DLPick where it called KR_LVPerson (the panel\\'s 「목록에서 '
              '보기」 opens the list on 기한); KR_LVChart and KR_LVPerson call KR_DLRun where they called KR_LVRun (the list loop with the '
              '기한 chip, a copy of KR_LVRun / KR_LVDraw with the title layer\\'s KR_LTLine / KR_LTPreview / KR_LTMonth). KR_DLBindClick '
              'has a hand-written body (EraseMouseLClickEvent / AddMouseLClickEvent with the KR_DLClick delegate). PACT 177 '
              'Game/Scenes/Common/AddArea.pactex: the KR_HomeRate group gets KR_DL_Box, KR_DL_Title, KR_DL_Face0-7, KR_DL_Text0-7, '
              'KR_DL_Num0-7, KR_DL_BtnBox, KR_DL_BtnText (all hidden at start, x 1124-1276). Deadlines are baked from schedule.json '
              '(monthly 특훈 뒤 대화 by their pool months, 우선 대화 by their IsTodayOrAfter / IsTodayOrBefore window and the earlier '
              '우선 대화 they need); pending = open today, unseen in this save, the companion joined. It is user-requested: when a '
              'rebuild needs a clean base, rebase on the runtime that current.json points to and carry it forward; restore is reserved '
              'for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_deadline*.py --restore 를 실행하거나 기한 있는 장면 알림 층(KR_DL* 함수와 같은 길이 CALLFUNC 피연산자 '
                 '5곳: KR_T8HomeMenuOpen · Close 의 KR_HVClickable → KR_DLClickable(본거지 첫 메뉴가 떠 있는 동안 오른쪽 여백 기한 패널), '
                 'KR_HVPick 의 KR_LVPerson → KR_DLPick(패널의 「목록에서 보기」), KR_LVChart · KR_LVPerson 의 KR_LVRun → KR_DLRun(목록의 '
                 '「기한」 칩); KR_DLBindClick 은 손으로 쓴 jam 몸체; PACT 177 AddArea 의 KR_HomeRate 묶음에 KR_DL_* 부품 28개)을 지우지 '
                 '않는다. 기한은 schedule.json 에서 굽는다(특훈 뒤 대화는 묶음 달, 우선 대화는 날짜 창과 앞 대화). 사용자가 요청한 것이다: '
                 '깨끗한 기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 '
                 '요청할 때만 한다.')
INSTRUCTION = (
    'Claude deadline-alert layer (2026-10-18, user-requested). '
    + NO_RESTORE + ' Payload: NightRemaster.ain + NightRemasterPact.afa (entry 177 only). KR_DL* functions appended; no original '
    'function relocated; no new global / struct member. The auto-nav pins stay (index, address and every code byte): '
    + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE + ' Every earlier contract stays in force.')''')
src = once(src, "str(HERE.parent / 'autonav_20261015' / 'scan_autonav.ps1')", "str(HERE / 'scan_deadline.ps1')")
src = between(src, "def probe_deadline_ok(p):", "\n\n\ndef draft_contract(", '''def probe_deadline_ok(p):
    lg = p.get('log') or []
    return bool(lg and 'END' in lg and 'FAILS 0' in lg and p.get('user_save_folder_unchanged') and not p.get('vm_error')
                and not p.get('events') and not p.get('timeout') and not p.get('fails') and p.get('oks', 0) >= 5)


def probes_ok(after):
    out = {}
    for n in PROBES:
        p = read(L.EVID / n) if (L.EVID / n).exists() else {}
        out[n] = bool(p.get('candidate_ain') == after['NightRemaster.ain'] and p.get('candidate_pact') == after['NightRemasterPact.afa']
                      and probe_deadline_ok(p))
    return out''')
src = once(src, '''    pm = read(L.EVID / 'probe_deadline.json')
    assert pm.get('candidate_ain') == after['NightRemaster.ain'] and pm.get('candidate_pact') == after['NightRemasterPact.afa'], 'rerun probe_deadline.py\'''',
           '''    pk = probes_ok(after)
    assert all(pk.values()), ('rerun the probes for this candidate', pk)
    probes = {}
    for n in PROBES:
        p = read(L.EVID / n)
        probes[n] = dict(passed=pk[n], oks=p.get('oks'), fails=p.get('fails'), seconds=p.get('seconds'), save=p.get('save'),
                         shots=[Path(x).name for x in p.get('shots', [])])''')
src = once(src, '''        verification=dict(probe=dict(passed=probe_deadline_ok(pm), oks=pm.get('oks'), fails=pm.get('fails'), seconds=pm.get('seconds'),
                                     save=pm.get('save'), shots=[Path(x).name for x in pm.get('shots', [])]),''',
           '''        baked=man.get('baked'),
        verification=dict(probes=probes,''')
src = once(src, "self.note_title = note_title or '본거지 달성률 패널 새 모양 (Claude Opus 5.5; 전투 템포 설치본 위)'",
           "self.note_title = note_title or '기한 있는 장면 알림 (Claude Opus 5.5; 타이틀 가림 설치본 위)'")
src = once(src, '''        for n in ['probe_deadline.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)''', '''        for n in PROBES:
            shutil.copy2(L.EVID / n, ev / 'source' / n)''')
src = between(src, "        nm['next'] = (", "        write(mp, js(nm))", '''        nm['next'] = ('User screen check: 본거지 첫 메뉴 오른쪽 여백에 「기한 있는 장면」 패널(기한별 묶음, 7일 안 주황)이 뜨는지; '
                      '「목록에서 보기」를 누르면 목록의 「기한」이 열리는지; 목록의 「기한」 칩; 본거지 밖과 옵션 창에서는 패널이 안 보이는지.')
''')
a = src.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = src.index("        write(root / 'progress.md'")
src = src[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 기한 있는 장면 알림(사용자 10-18 「시간 제한 있는 이벤트 알려주기」, 시안 승인): 본거지 첫 메뉴가 떠 있는 동안 오른쪽 "
                "여백에 「기한 있는 장면」 패널 — 아직 이 세이브에서 안 본 장면을 기한별로 묶어(7일 안은 주황) 동료별 특훈 뒤 대화 수와 "
                "우선 대화를 보이고, 「목록에서 보기」는 목록의 「기한」(기한 · 장면 · 조건 열)을 연다. 목록에는 본거지에서 「기한」 칩.\\n"
                "- PACT 177 AddArea 의 KR_HomeRate 묶음에 KR_DL_* 부품 28개(처음엔 숨김). AIN 은 KR_DL* 함수, 원본 함수 이전 0, 같은 길이 "
                "CALLFUNC 피연산자 5곳, 새 전역 · 구조체 필드 0. 고정 함수(r18~r23 · 오토 내비 " + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) "
                "publish_deadline.py --restore.\\n")
''' + src[b:]
src = once(src, '''    pm = read(L.EVID / 'probe_deadline.json') if (L.EVID / 'probe_deadline.json').exists() else {}
    if pm.get('candidate_ain') != after['NightRemaster.ain'] or pm.get('candidate_pact') != after['NightRemasterPact.afa'] or not probe_deadline_ok(pm):
        issues.append('native probe (probe_deadline.py) missing, failing or for another candidate')''',
           '''    pk = probes_ok(after)
    if not all(pk.values()):
        issues.append('native probes (probe_deadline.py: NightR47, NightR16, TITLE) missing, failing or for another candidate: ' + str(pk))''')
src = once(src, "                          not_played_natively='real mouse hit-testing and the cursor-over (state 2) look of the buttons: the probe '\n"
                "                                              'cuts input off and calls the click handler with each button\\'s coordinates'),",
           "                          not_played_natively='real mouse hit-testing and the cursor-over (state 2) look of the 목록에서 보기 button: '\n"
           "                                              'the probe cuts input off and calls KR_DLClick'),")
for bad in ['probe_home', 'hvlib', 'scan_autonav']:
    assert bad not in src, bad
(HERE / 'publish_deadline.py').write_text(src, 'utf8')
ps = (HERE.parent / 'calendar_title_20261018' / 'scan_title.ps1').read_text('utf8')
ps2 = ps.replace("$files=@('NightRemaster.ain')", "$files=@('NightRemaster.ain','NightRemasterPact.afa')")
assert ps2 != ps
(HERE / 'scan_deadline.ps1').write_bytes(ps2.encode('ascii'))
rc = (HERE.parent / 'calendar_title_20261018' / 'work' / 'resume_offset_check.py').read_text('utf8').replace('import ltlib as L', 'import dllib as L')
rc = rc.replace('against the title-calendar candidate (copied from calendar_list_20261018/work)', 'against the deadline-alert candidate (copied from calendar_title_20261018/work)')
(HERE / 'work' / 'resume_offset_check.py').write_text(rc, 'utf8')
print('ok', len(src.splitlines()), 'lines')
