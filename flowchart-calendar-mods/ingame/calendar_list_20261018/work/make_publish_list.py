# -*- coding: utf-8 -*-
"""Make publish_list.py from calendar_overview_20261018/publish_overview.py (read only): the same journaled install / restore
transaction, fixture and readiness, with the scene-list payload (NightRemaster.ain only), its probes, contract and notes.
Stage 3 of the calendar / completion-rate redesign (2026-10-18). Also scan_list.ps1 (copy of scan_overview.ps1)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OV = HERE.parent / 'calendar_overview_20261018'
src = (OV / 'publish_overview.py').read_text('utf8')


def once(text, a, b):
    assert text.count(a) == 1, (a[:90], text.count(a))
    return text.replace(a, b)


def between(text, a, b, new):
    """Replace text from the start of a up to (not including) b."""
    i = text.index(a)
    j = text.index(b, i)
    return text[:i] + new + text[j:]


DOC = '''"""Claude Opus 5.5 (2026-10-18): install / restore of the event-calendar scene list, stage 3 of the calendar / completion-rate
redesign (user, 10-17: a cell says little, no per-character view; mockup approved 「왜 이리 멋져? 좋아 가자」; 10-18 「3단계 목록도
이어서 만들어 줘.」), made from publish_overview.py (same journaled transaction, same KRMenu scratch rule).

  python publish_list.py --stage      check candidate/manifest.json against the built AIN (the payload is the AIN only)
  python publish_list.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_list.py --contract   write the Codex contract draft required_calendar_list_20261018.json
  python publish_list.py --fixture    transaction fixture on disposable files under calendar_list_20261018/work (no runtime)
  python publish_list.py --verify     read-only readiness check (hashes, native probes, scan, fixture, saved stacks, contracts)
  python publish_list.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_list.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_LV* layer). PACT/EX/FNL, the Manual chart and winmm.dll untouched. One journaled transaction as
publish_overview.py: PREPARED -> atomic hash-checked replacement -> runtime manifest + current.json + every required_*.json present
at install time (calendar_list_20261018_preserved_by) + new required_calendar_list_20261018.json + latest_worked_translation.json
+ progress.md note -> exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back; --restore returns the
exact pre-install state.
"""'''
src = DOC + src[src.index('\nfrom pathlib import Path'):]
src = once(src, 'import ovlib as L', 'import lvlib as L')
for a, b in [('calendar_overview_20261018', 'calendar_list_20261018'), ('CALENDAR_OVERVIEW_20261018', 'CALENDAR_LIST_20261018'),
             ('.overview-', '.list-'), ('overview-copy.tmp', 'list-copy.tmp'), ('publish_overview', 'publish_list'),
             ('scan_overview.ps1', 'scan_list.ps1'), ('probe_overview_ok', 'probe_list_ok'), ('probe_overview.py', 'probe_list.py')]:
    src = src.replace(a, b)
src = once(src, "PROBES = ['probe_overview.json', 'probe_overview_NightR16.json', 'probe_overview_TITLE.json']",
           "PROBES = ['probe_list.json', 'probe_list_NightR16.json', 'probe_list_TITLE.json']")
src = between(src, "NO_RESTORE = ('Codex must never run", "\n\n\ndef js(", '''NO_RESTORE = ('Codex must never run publish_list*.py --restore or otherwise remove the calendar scene-list layer: KR_LV* functions; '
              'KR_CDo calls KR_LVChart where it called KR_XVChart (the board is still KR_XVDraw; a cell, a row name or a month head '
              'now opens the scene list filtered to that month / row; 회상 and 그 밖 keep the month view KR_CChart); KR_HVPick calls '
              'KR_LVPerson where it called KR_T8CharMissingPage (the home panel\\'s companion buttons open that companion\\'s list). '
              'The list is drawn on the chart root KR_CRoot with the chart session open (Open = 1) and parts 2026102500-2026102830, '
              'above every AddArea part; 다시 보기 uses the month view\\'s replay path (KR_CRequest -> unwind -> KR_CReplay) and '
              '자세히 its detail board (KR_CClick). Rows follow the board (본편, joined / met companions, 던전 동행). The cast, the '
              'summary, 다시 보기 and 자세히 open only for a scene the player has seen (home: registered in this save, because the '
              'user\\'s save folder holds later saves than the current play; title: read in any save; everywhere with 전체 개방); a row '
              'naming a companion outside the rows shows ？？？ until then. '
              'It is user-requested: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry '
              'it forward; restore is reserved for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_list*.py --restore 를 실행하거나 캘린더 장면 목록 층(KR_LV* 함수; KR_CDo 의 KR_XVChart 호출 → '
                 'KR_LVChart(판은 그대로 KR_XVDraw, 칸 · 줄 이름 · 달 머리를 누르면 그 달 · 그 줄로 거른 장면 목록; 회상 · 그 밖은 달별 화면); '
                 'KR_HVPick 의 KR_T8CharMissingPage 호출 → KR_LVPerson(본거지 패널 인물 단추가 그 인물의 목록을 연다))을 지우지 않는다. '
                 '목록은 차트 뿌리 KR_CRoot 위에 차트 세션(Open = 1)을 열고 부품 2026102500~2026102830 으로 그리며 Z 는 AddArea 부품 위. '
                 '다시 보기는 달별 화면의 재생 경로(KR_CRequest → 되감기 → KR_CReplay), 자세히는 그 상세 창(KR_CClick). 줄은 판과 같다'
                 '(본편 · 합류한/만난 동료 · 던전 동행). 등장인물 · 줄거리 · 다시 보기 · 자세히는 본 장면만 연다(본거지는 이 세이브에서 본 '
                 '장면 — 세이브 폴더에 지금 진도보다 앞선 세이브가 있다; 타이틀은 어느 세이브에서든 읽은 장면; 전체 개방이면 모두). 합류 전 '
                 '동료 이름이 든 줄은 그때까지 ？？？. '
                 '사용자가 요청한 것이다: 깨끗한 기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 이어 싣는다. 되돌리기는 '
                 '사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude event-calendar scene-list layer (2026-10-18, stage 3 of the user-requested calendar / completion-rate redesign). '
    + NO_RESTORE + ' Payload: NightRemaster.ain only. KR_LV* functions appended; no original function relocated; no new global '
    '/ struct member; 2 same-length CALLFUNC operand swaps (KR_CDo, KR_HVPick). The stage-2 board functions (KR_XV*) stay and are '
    'called by KR_LVChart. The auto-nav pins stay (index, address and every code byte): '
    + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE + ' Every earlier contract stays in force.')''')
src = once(src, "self.note_title = note_title or '이벤트 캘린더 한눈에 보기 (Claude Opus 5.5; 본거지 달성률 패널 설치본 위)'",
           "self.note_title = note_title or '이벤트 캘린더 장면 목록 (Claude Opus 5.5; 한눈에 보기 설치본 위)'")
src = between(src, "        nm['next'] = (", "        write(mp, js(nm))", '''        nm['next'] = ('User screen check: 판의 칸 · 인물 이름 · 달을 누르면 장면 목록이 뜨는지; 줄을 누르면 오른쪽 미리보기(얼굴 · 줄거리)가 바뀌는지; '
                      '「다시 보기」 뒤 목록으로 돌아오는지; 「자세히」가 상세 창을 여는지; 본거지 패널의 인물 단추가 그 인물 목록을 여는지; '
                      '합류 전 동료가 칩 · 줄 이름에 안 보이는지.')
''')
a = src.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = src.index("        write(root / 'progress.md'")
src = src[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 이벤트 캘린더 장면 목록(사용자 10-17 시안 승인, 10-18 「3단계 목록도 이어서 만들어 줘.」): 한눈에 보기 판의 칸 · 줄 이름 · 달 "
                "머리를 누르면 그 달 · 그 줄로 거른 장면 목록이 열린다(한 쪽 14줄: 상태 ● · ▲ · ○, 언제, 장면, 함께, 줄거리 첫 줄). 오른쪽 "
                "미리보기(얼굴 · 언제 · 조건 · 함께 · 상태 · 다시 보기 · 줄거리)와 「다시 보기」 「자세히」, 위에 달 · 줄 칩, 「달 화면으로」 "
                "「한눈에 보기로」. 본거지 패널의 인물 단추는 그 인물의 목록을 연다(예전 글자 창 대신).\\n"
                "- KR_CDo 의 KR_XVChart → KR_LVChart, KR_HVPick 의 KR_T8CharMissingPage → KR_LVPerson(같은 길이 CALLFUNC 피연산자 2곳). AIN 만, "
                "원본 함수 이전 0, 새 전역 · 구조체 필드 0. 고정 함수(r18~r23 · 오토 내비 " + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) publish_list.py --restore.\\n")
''' + src[b:]
src = between(src, "                          not_played_natively=", "),\n", '''                          not_played_natively='real mouse clicks (the probes end the waits with the part number a click '
                                              'returns); the stage-only card pages of the detail board (단계 고르기) are the month '
                                              'view\\'s own, unchanged\'''')
for bad in ['probe_overview', 'KR_XVLaneNo (schedule', 'ovlib', 'overview layer', 'publish_overview', 'scan_overview']:
    assert bad not in src, bad
(HERE / 'publish_list.py').write_text(src, 'utf8')
ps = (OV / 'scan_overview.ps1').read_text('utf8')
(HERE / 'scan_list.ps1').write_bytes(ps.encode('ascii'))
print('ok', len(src.splitlines()), 'lines')
