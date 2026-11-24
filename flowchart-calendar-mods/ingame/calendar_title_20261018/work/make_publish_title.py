# -*- coding: utf-8 -*-
"""Make publish_title.py from calendar_list_20261018/publish_list.py (read only): the same journaled install / restore
transaction, fixture and readiness, with the title-layer payload (NightRemaster.ain only), probes, contract and notes.
Also scan_title.ps1 (copy of scan_list.ps1) and work/resume_offset_check.py."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
LV = HERE.parent / 'calendar_list_20261018'
src = (LV / 'publish_list.py').read_text('utf8')


def once(text, a, b):
    assert text.count(a) == 1, (a[:90], text.count(a))
    return text.replace(a, b)


def between(text, a, b, new):
    i = text.index(a)
    j = text.index(b, i)
    return text[:i] + new + text[j:]


DOC = '''"""Claude Opus 5.5 (2026-10-18): install / restore of the title-calendar spoiler layer (user, 10-18: 「타이틀에서 연 캘린더도 처음부터
있는 동료만 보이고 줄거리·얼굴은 닫히게 바꿔 줘.」), made from publish_list.py (same journaled transaction, same KRMenu scratch rule).

  python publish_title.py --stage      check candidate/manifest.json against the built AIN (the payload is the AIN only)
  python publish_title.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_title.py --contract   write the Codex contract draft required_calendar_title_20261018.json
  python publish_title.py --fixture    transaction fixture on disposable files under calendar_title_20261018/work (no runtime)
  python publish_title.py --verify     read-only readiness check (hashes, native probes, scan, fixture, saved stacks, contracts)
  python publish_title.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_title.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_LT* layer). PACT/EX/FNL, the Manual chart and winmm.dll untouched.
"""'''
src = DOC + src[src.index('\nfrom pathlib import Path'):]
src = once(src, 'import lvlib as L', 'import ltlib as L')
for a, b in [('calendar_list_20261018', 'calendar_title_20261018'), ('CALENDAR_LIST_20261018', 'CALENDAR_TITLE_20261018'),
             ('.list-', '.title-'), ('list-copy.tmp', 'title-copy.tmp'), ('publish_list', 'publish_title'),
             ('scan_list.ps1', 'scan_title.ps1'), ('probe_list_ok', 'probe_title_ok'), ('probe_list.py', 'probe_title.py')]:
    src = src.replace(a, b)
src = once(src, "PROBES = ['probe_list.json', 'probe_list_NightR16.json', 'probe_list_TITLE.json']",
           "PROBES = ['probe_title.json', 'probe_title_NightR16.json', 'probe_title_TITLE.json']")
src = between(src, "NO_RESTORE = ('Codex must never run", "\n\n\ndef js(", '''NO_RESTORE = ('Codex must never run publish_title*.py --restore or otherwise remove the title-calendar spoiler layer: KR_LT* '
              'functions and 9 CALLFUNC operand swaps - KR_XVRows and KR_LVLanes call KR_LTStart where they called KR_XVMet (on the '
              'title the board rows and the list chips are 본편, the companions present from the start (KR_T20JoinDay <= 0) and 던전 '
              '동행); KR_LVReveal calls KR_LTRead where it called KR_P29Read (on the title the cast, summaries, 다시 보기 and 자세히 '
              'stay closed unless 전체 개방); KR_LVRow calls KR_LTNote, KR_LVDraw calls KR_LTPreview and KR_LTLine (the title wording, '
              '달 화면으로 off); KR_LVChart calls KR_LTBoardExtras and KR_LTMonth, KR_LVRun calls KR_LTMonth (회상 · 그 밖 and the month '
              'view are not opened from the title calendar). Home is unchanged. It is user-requested: when a rebuild needs a clean '
              'base, rebase on the runtime that current.json points to and carry it forward; restore is reserved for the user\\'s '
              'explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_title*.py --restore 를 실행하거나 타이틀 캘린더 가림 층(KR_LT* 함수와 같은 길이 CALLFUNC 피연산자 '
                 '9곳: KR_XVRows · KR_LVLanes 의 KR_XVMet → KR_LTStart(타이틀에서는 본편 · 처음부터 있는 동료 · 던전 동행만), '
                 'KR_LVReveal 의 KR_P29Read → KR_LTRead(타이틀에서는 등장인물 · 줄거리 · 다시 보기 · 자세히를 닫음, 전체 개방이면 '
                 '열림), KR_LVRow · KR_LVDraw 의 문구와 달 화면으로 끄기, KR_LVChart · KR_LVRun 의 회상 · 그 밖 · 달 화면 막기)을 '
                 '지우지 않는다. 본거지 동작은 그대로다. 사용자가 요청한 것이다: 깨끗한 기준이 필요하면 current.json 이 가리키는 '
                 '실행본 위에서 다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude title-calendar spoiler layer (2026-10-18, user-requested). '
    + NO_RESTORE + ' Payload: NightRemaster.ain only. KR_LT* functions appended; no original function relocated; no new global '
    '/ struct member. The auto-nav pins stay (index, address and every code byte): '
    + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE + ' Every earlier contract stays in force.')''')
src = once(src, "self.note_title = note_title or '이벤트 캘린더 장면 목록 (Claude Opus 5.5; 한눈에 보기 설치본 위)'",
           "self.note_title = note_title or '타이틀 캘린더 가림 (Claude Opus 5.5; 장면 목록 설치본 위)'")
src = between(src, "        nm['next'] = (", "        write(mp, js(nm))", '''        nm['next'] = ('User screen check: 타이틀의 모드 메뉴로 연 캘린더에 처음부터 있는 동료만 보이는지; 목록의 줄거리 · 얼굴 · 다시 보기 · '
                      '자세히가 닫혀 있는지; 본거지에서 연 캘린더는 그대로인지.')
''')
a = src.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = src.index("        write(root / 'progress.md'")
src = src[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 타이틀 캘린더 가림(사용자 10-18 「타이틀에서 연 캘린더도 처음부터 있는 동료만 보이고 줄거리·얼굴은 닫히게 바꿔 줘.」): "
                "타이틀의 모드 메뉴로 연 캘린더는 본편 · 처음부터 있는 동료 · 던전 동행만 보이고, 등장인물 · 줄거리 · 다시 보기 · 자세히 · "
                "회상 · 달 화면을 닫는다(전체 개방이면 열림). 본거지 동작은 그대로.\\n"
                "- KR_LT* 함수, 같은 길이 CALLFUNC 피연산자 9곳. AIN 만, 원본 함수 이전 0, 새 전역 · 구조체 필드 0. 고정 함수(r18~r23 · 오토 내비 "
                + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) publish_title.py --restore.\\n")
''' + src[b:]
src = between(src, "                          not_played_natively=", "),\n", '''                          not_played_natively='real mouse clicks (the probes end the waits with the part number a click '
                                              'returns)\'''')
for bad in ['probe_list', 'publish_list', 'scan_list', 'lvlib', 'scene-list layer: KR_LV']:
    assert bad not in src, bad
(HERE / 'publish_title.py').write_text(src, 'utf8')
(HERE / 'scan_title.ps1').write_bytes((LV / 'scan_list.ps1').read_bytes())
rc = (LV / 'work' / 'resume_offset_check.py').read_text('utf8').replace('import lvlib as L', 'import ltlib as L')
rc = rc.replace('against the calendar scene-list candidate (copied from calendar_overview_20261018/work)',
                'against the title-calendar candidate (copied from calendar_list_20261018/work)')
(HERE / 'work' / 'resume_offset_check.py').write_text(rc, 'utf8')
print('ok', len(src.splitlines()), 'lines')
