"""One-off: r22 specifics in publish_chart_r22.py (a copy of publish_modmenu_r21.py with the tokens already renamed)."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'publish_chart_r22.py'
s = p.read_text('utf8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:100])
    s = s.replace(a, b)


# ---- docstring
a = s.index('"""')
b = s.index('"""', a + 3) + 3
s = s[:a] + '''"""Claude Opus 5.5 (2026-09-28) r22: install / restore of the chart r22 candidate (the event flow chart screen of the menu-bar
「모드」 menu, stage 2), after publish_modmenu_r21.py (same transaction, same KRMenu scratch rule).
r22 = the r21 install + the chart: the 「chart」 request opens a save-independent event flow chart (KR_C*) on the title screen (new
same-length poll / serve sites in C_SceneTitle@Update / @Run) and in the home menu (KR_MDo forwarded); unlock = the game's global
records (first-message read marks, recollection unlocks) or 「전체 개방」; a click opens the calendar's card / scene page (chart
branch) and 이 장면 재생 replays through the game's memory-mode path (the recollection mode's own code).

  python publish_chart_r22.py --contract   write the Codex contract draft r22_chart/required_chart_r22.json
  python publish_chart_r22.py --fixture    transaction fixture on disposable files under r22_chart/work (no runtime): pair
                                           apply/restore, injected failures, tampering, interrupted restore, a whole install
                                           transaction in a disposable project (recovery runtime lacking a payload file, a
                                           KRMenu\\\\ request folder in the runtime)
  python publish_chart_r22.py --verify     read-only readiness check (hashes, VM, self-test, probes, native compare, scan,
                                           fixture, contract list, pointer)
  python publish_chart_r22.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_chart_r22.py --restore    undo an install exactly (journal-driven, resumable, idempotent): the runtime goes
                                           back to the pre-install AIN (= the r21 install)

Payload: NightRemaster.ain only (PACT/EX/FNL, the Manual chart and winmm.dll untouched). One journaled transaction, as in r4~r21:
PREPARED (evidence/chart_r22: before/candidate copies, metadata snapshots) -> atomic hash-checked replacement -> runtime manifest +
current.json + every required_*.json present at install time (chart_r22_preserved_by; their required_files row for the AIN
follows) + new required_chart_r22.json + latest_worked_translation.json + progress.md note -> exact tree (the runtime's KRMenu\\\\
folder excluded) / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back files and metadata; --restore returns
the exact pre-install state. Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
"""''' + s[b:]

rep("""                       'length); every other byte equals the r15 candidate. r19, r20 and r21: byte-identical to r18.',""",
    """                       'length); every other byte equals the r15 candidate. r19, r20, r21 and r22: byte-identical to r18.',""")
rep("""                       'keep it in place as a precaution (r15 contract; r18, r19, r20 and r21 byte-identical).',""",
    """                       'keep it in place as a precaution (r15 contract; r18, r19, r20, r21 and r22 byte-identical).',""")
rep("""    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15, r17, r18, r19, r20 and r21 (called from KR_T18RunSandboxed).',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15, r17, r18, r19, r20 and r21.',
    'KR_T18RunSandboxed': 'r18, pinned (r19, r20 and r21 byte-identical): on saved stacks when the player saves during a sandboxed replay '""",
    """    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15, r17, r18, r19, r20, r21 and r22 (called from KR_T18RunSandboxed and, in r22, from KR_CReplayRun as in the recollection mode).',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15, r17, r18, r19, r20, r21 and r22.',
    'KR_T18RunSandboxed': 'r18, pinned (r19, r20, r21 and r22 byte-identical): on saved stacks when the player saves during a sandboxed replay '""")
rep("""R18_FORWARDED = ['KR_T9MonthPage', 'KR_T9MemPage', 'KR_T9LaneTitle', 'KR_T9CardRow', 'KR_T9ChipRow', 'KR_T9MonthChips',
                 'KR_T9CardPage', 'KR_T9EventPage']""", """R18_FORWARDED = ['KR_T9MonthPage', 'KR_T9MemPage', 'KR_T9LaneTitle', 'KR_T9CardRow', 'KR_T9ChipRow', 'KR_T9MonthChips',
                 'KR_T9CardPage', 'KR_T9EventPage']
R22_FORWARDED = {'KR_MDo': 'KR_CDoHome', 'KR_T9Seen': 'KR_CSeen', 'KR_T9State': 'KR_CState', 'KR_T9Legend': 'KR_CLegend',
                 'KR_T18CardPage': 'KR_CCardPage', 'KR_T18EventPage': 'KR_CEventPage'}""")

# ---- no-restore rule and instruction
a = s.index('NO_RESTORE = (')
b = s.index('def js(data):')
s = s[:a] + r'''NO_RESTORE = ('Codex must never run publish_calendar_*.py --restore, publish_modmenu_*.py --restore or publish_chart_*.py --restore or '
              'otherwise remove the calendar overlay (KR_T9*/KR_T17*/KR_T18*/KR_T19*/KR_T20* functions, the nine r15 same-length operands, '
              'the RunEvent operand swap in KR_T9HomeCasual, the seven r20 same-length operands in C_Status::RunStatus, '
              'C_HomeStatusView@SetInfo, C_SceneTraining@RunSelectPartner and C_SceneTraining@_UpdateInputPartner), the mod-menu request '
              'consumer (KR_M* functions and the two r21 same-length operands: KR_T9HomeMenuRun calls KR_MHomeRun where it called '
              '■選択ダイアログ／実行, C_SelectDialog@_Update calls KR_MTick where it called C_UserInputManager::IsClickEnterOtherMouse) or the '
              'event flow chart (KR_C* functions, the six r22 one-call forwarders KR_MDo -> KR_CDoHome, KR_T9Seen -> KR_CSeen, KR_T9State -> '
              'KR_CState, KR_T9Legend -> KR_CLegend, KR_T18CardPage -> KR_CCardPage, KR_T18EventPage -> KR_CEventPage, and the two r22 '
              'same-length operands: C_SceneTitle@Update calls KR_CTitleTick where it called C_UserInputManager::IsClickConfig, '
              'C_SceneTitle@Run calls KR_CTitleServe where it called ■方向キー処理／削除). The calendar, the mod menu and the chart are '
              'permanent user-requested features: when a rebuild needs a clean base, rebase on the runtime that current.json points to and '
              'carry the calendar, mod-menu and chart functions forward; restore is reserved for the user\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_calendar_*.py · publish_modmenu_*.py · publish_chart_*.py --restore 를 실행하거나 달력 오버레이(KR_T9*/KR_T17*/'
                 'KR_T18*/KR_T19*/KR_T20* 함수, r15 의 같은 길이 피연산자 9곳, KR_T9HomeCasual 의 RunEvent 피연산자 교체, r20 의 같은 길이 피연산자 7곳), '
                 '모드 메뉴 요청 소비(KR_M* 함수, r21 의 같은 길이 피연산자 2곳 — KR_T9HomeMenuRun → KR_MHomeRun, C_SelectDialog@_Update → '
                 'KR_MTick)나 이벤트 플로우 차트(KR_C* 함수, r22 의 한 줄 전달 6개 — KR_MDo · KR_T9Seen · KR_T9State · KR_T9Legend · '
                 'KR_T18CardPage · KR_T18EventPage, 같은 길이 피연산자 2곳 — C_SceneTitle@Update 의 IsClickConfig → KR_CTitleTick, '
                 'C_SceneTitle@Run 의 ■方向キー処理／削除 → KR_CTitleServe)를 지우지 않는다. 달력 · 모드 메뉴 · 차트는 사용자가 요청한 영구 '
                 '기능이다: 깨끗한 기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 '
                 '요청할 때만 한다.')
INSTRUCTION = (
    'Claude r22 (2026-09-28): the event flow chart screen of the menu-bar 「모드」 menu, stage 2 (design ingame/설계_v4_메뉴바차트.md 「C」 '
    'and 「정정(09-28 06시)」: a save-independent whole map, openable on the title screen like the recollection mode). ' + NO_RESTORE +
    ' Payload: NightRemaster.ain only; PACT/EX/FNL, the Manual chart and winmm.dll untouched. KR_C* functions appended (tables baked: the '
    'chart\'s 915 cells in 10 tabs, names / conditions from the r19 texts, thumbnails from graph/event_cg.json = the CG gallery '
    'thumbnails, recollection cells, not-playable scenes); no original function relocated; no new global / struct member; no save '
    'schema change; session variables YoruKR.C.Open / Ctx / All / Play / TitleReq only. Six one-call forwarders (same index, arguments '
    'and return type): KR_MDo -> KR_CDoHome (the home menu\'s 「chart」 opens the chart; the other four commands are r21\'s code), '
    'KR_T9Seen -> KR_CSeen, KR_T9State -> KR_CState, KR_T9Legend -> KR_CLegend, KR_T18CardPage -> KR_CCardPage, KR_T18EventPage -> '
    'KR_CEventPage: while the chart is open (YoruKR.C.Open = 1 AND the chart root part 2026092200 exists) they use the global records '
    '(first-message MsgSkip read mark or N_ModeScene::CheckEnabelScenario; 「전체 개방」 = YoruKR_Chart.dat 1) and replay through '
    'KR_CReplayRun; otherwise they run exactly r15 / r18\'s bodies (the in-game calendar: per-save ○ △ ●, the r18 lock, the sandbox). '
    'Two same-length CALLFUNC operand swaps on the title: C_SceneTitle@Update C_UserInputManager::IsClickConfig -> KR_CTitleTick (every '
    'title frame: two FileOperation.ExistFile calls; a waiting request / result ends the title\'s wait with KR_CCode 2026092802), '
    'C_SceneTitle@Run ■方向キー処理／削除 -> KR_CTitleServe (the original call, then the result and the request: all five commands). '
    'KR_CReplayRun is C_SceneModeScene@ExecScene\'s memory-mode path (AFL_MemoryModeEvent_Begin, IsExecNameEntry saved / 0, new '
    'C_SceneGame, LSys3xScript::Prepare + RunEvent, delete, IsExecNameEntry restored, AFL_MemoryModeEvent_End, _Cleanup) with the '
    'event name from LSys3xScript::GetLabelName(no); it runs after the chart closed (every chart part released) where the chart was '
    'opened (the title: its root hidden around the replay; the home menu: rebuilt after it). The chart\'s parts are fixed numbers '
    '2026092200-2026092311 (root Z 5000), all released on every way out. ' + KRMENU_RULE + ' Pinned (index, address and every code '
    'byte identical): KR_T9HomeCasual, KR_T9HomeConfig, C_SceneHomebase@CheckGameSysButtons, C_SceneHomebase@Run, LSys3xScript::RunEvent, '
    'KR_T18RunSandboxed. r15\'s nine, r18\'s one, r20\'s seven and r21\'s two same-length sites and r18\'s eight / r19\'s five forwarders '
    'stay. Every earlier contract stays in force.')


''' + s[b:]

# ---- the note title and sources copied into the evidence
rep("""        self.note_title = note_title or '메뉴바 「모드」 메뉴 r21(1단계, 게임 스크립트 쪽) 설치 (Claude Opus 5.5; r20 설치본 위)'""",
    """        self.note_title = note_title or '메뉴바 「모드」 메뉴 r22(2단계, 이벤트 플로우 차트 화면) 설치 (Claude Opus 5.5; r21 설치본 위)'""")
rep("""        for n in ['probe_result.json', 'probe_regs.json', 'probe_r21.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        if (L.EVID / 'integrated').exists():
            shutil.copytree(L.EVID / 'integrated', ev / 'source' / 'integrated')""",
    """        for n in ['probe_result.json', 'probe_regs.json', 'probe_r22.json', 'probe_kinds.json', 'replay_kinds.json', 'event_cg_gate.json',
                  'verify.json', 'verify_selftest.json']:
            if (L.EVID / n).exists():
                shutil.copy2(L.EVID / n, ev / 'source' / n)
        for sub in ('probe_kinds', 'probe_zoom'):
            if (L.EVID / sub).exists():
                shutil.copytree(L.EVID / sub, ev / 'source' / sub)
        shutil.copy2(L.FLOW / 'graph' / 'event_cg.json', ev / 'source' / 'event_cg.json')""")
rep("""        nm['next'] = ('User screen check: 모드 메뉴 r21(1단계) — 본거지 첫 메뉴에서 메뉴바 「모드」의 각 항목(후크 설치 뒤): 차트 안내 창, 전체 개방 / '
                      '되돌리기 안내 창, 전체 리셋 · 되돌리기 확인 창(아니요 = 그대로, 예 = 게임 종료, 다음 실행에서 후크가 처리하고 결과 창).')""",
    """        nm['next'] = ('User screen check: 이벤트 플로우 차트 r22 — 타이틀 화면과 본거지 첫 메뉴에서 메뉴바 「모드 → 이벤트 플로우 차트」: 달 탭 · '
                      '썸네일 칸 · 작은 칸 · 잠긴 칸(누르면 안내), 전체 개방 뒤 같은 칸 열림, 칸 → 카드 쪽 / 장면 쪽 → 이 장면 재생(회상 모드처럼, '
                      '끝나면 차트를 연 화면으로), 전체 개방 되돌리기 뒤 다시 잠김(재생한 장면은 읽음 표시가 남아 열린 채).')""")
a = s.index('        note = (f"\\n\\n### {now} {ctx.note_title}\\n"')
b = s.index("        write(root / 'progress.md',")
s = s[:a] + '''        note = (f"\\n\\n### {now} {ctx.note_title}\\n"
                "- 이벤트 플로우 차트(2단계): 메뉴바 「모드 → 이벤트 플로우 차트」 요청을 타이틀 화면(새로: C_SceneTitle@Update 의 IsClickConfig "
                "자리 → KR_CTitleTick, C_SceneTitle@Run 의 ■方向キー処理／削除 자리 → KR_CTitleServe; 5개 명령 전부)과 본거지 첫 메뉴(r21 그대로, "
                "KR_MDo 한 줄 전달)에서 받아 차트 화면(KR_C*, 파츠 2026092200~2026092311)을 연다. 저장과 무관한 전체 지도: 해금 = 게임 전역 "
                "기록(첫 메시지 읽음 표시 · 회상 해금) 또는 전체 개방(YoruKR_Chart.dat 1). 칸 → 달력의 카드 쪽 / 장면 쪽(차트 가지) → 이 장면 "
                "재생 = 게임 회상 모드 경로(KR_CReplayRun = C_SceneModeScene@ExecScene 의 명령).\\n"
                "- AIN 한 파일, 원본 함수 이전 0, 한 줄 전달 6개(KR_MDo · KR_T9Seen · KR_T9State · KR_T9Legend · KR_T18CardPage · KR_T18EventPage: "
                "차트 밖에서는 r15 · r18 몸체 그대로), 같은 길이 피연산자 2곳(C_SceneTitle@Update · @Run), 주소 유지 함수 6개 바이트 동일, "
                "새 전역 · 구조체 필드 0, 세션 변수 YoruKR.C.* 만.\\n"
                "- " + KRMENU_RULE_KO + "\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) publish_chart_r22.py --restore.\\n")
''' + s[b:]
p.write_text(s, 'utf8')
print('publish: docstring / rules / note done')
