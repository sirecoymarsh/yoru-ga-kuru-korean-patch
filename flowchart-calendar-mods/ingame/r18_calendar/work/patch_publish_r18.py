"""One-off: turn the copied r17 publish script into publish_calendar_r18.py (exact block replacements, each asserted)."""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / 'publish_calendar_r18.py'
t = P.read_text('utf8')


def rep(old, new, count=1):
    global t
    assert t.count(old) == count, (t.count(old), old[:90])
    t = t.replace(old, new)


i = t.index('"""', 3)
t = '''"""Claude Opus 5.5 (2026-09-27) r18: install / restore of the calendar r18 candidate (copy of publish_calendar_r17.py).
r18 = r17's screens (renamed KR_T18*) + replay lock + replay sandbox. r17 was installed 07:24 and restored 14:11 (journal
RESTORED); r18 replaces the r17 candidate and installs straight onto the base (r15 + Codex's later work, 18:03 chart menu).

  python publish_calendar_r18.py --contract   write the Codex contract draft r18_calendar/required_calendar_r18.json
  python publish_calendar_r18.py --fixture    transaction fixture on disposable files under r18_calendar/work (no runtime)
  python publish_calendar_r18.py --verify     read-only readiness check (hashes, VM, self-test, probe, native compare, scan,
                                              fixture, contract list, pointer)
  python publish_calendar_r18.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_calendar_r18.py --restore    undo an install exactly (journal-driven, resumable, idempotent): the runtime
                                              goes back to the pre-install AIN (= the base, r15 and Codex's later work inside)

Payload: NightRemaster.ain only (PACT/EX untouched). The install is one journaled transaction, as in r4~r17:
  PREPARED (evidence/calendar_r18: before/candidate copies, metadata snapshots) -> atomic hash-checked replacement of the
  AIN -> runtime manifest + current.json + every required_*.json present at install time (calendar_r18_preserved_by) +
  new required_calendar_r18.json + latest_worked_translation.json + progress.md note -> exact tree / saves / recovery
  runtime re-checked -> COMMITTED. Any failure rolls back files and metadata; --restore returns the exact pre-install state.
Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
''' + t[i:]

rep('import r17lib as L', 'import r18lib as L')
rep("E = R / 'evidence' / 'calendar_r17'                   # created only by --install",
    "E = R / 'evidence' / 'calendar_r18'                   # created only by --install")
rep("NEW = 'required_calendar_r17.json'", "NEW = 'required_calendar_r18.json'")
rep("STATUS = 'CALENDAR_R17_INSTALLED_NATIVE_PASS'", "STATUS = 'CALENDAR_R18_INSTALLED_NATIVE_PASS'")
rep("READY = 'CALENDAR_R17_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'", "READY = 'CALENDAR_R18_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'")
rep("DEFECTS = 22", "DEFECTS = 27")

a = t.index('PINNED = {')
b = t.index('def js(data):')
t = t[:a] + '''PINNED = {
    'KR_T9HomeCasual': 'on saved stacks during a calendar replay: C_SceneHomebase@Run > CheckGameSysButtons (return after the '
                       'casual call site) > KR_T9HomeCasual (return after the RunEvent call site, offset 198) > KR_T18RunSandboxed > '
                       'RunEvent > event. Keep index, address and code bytes in every later build. r18 changed exactly one thing in '
                       'it: the 4-byte operand of that call (LSys3xScript::RunEvent -> KR_T18RunSandboxed, same signature, same '
                       'length); every other byte equals the r15 candidate.',
    'KR_T9HomeConfig': 'the settings screen opened from the home base runs inside it (no save is possible there as far as known); '
                       'keep it in place as a precaution (r15 contract; r18 byte-identical).',
    'C_SceneHomebase@CheckGameSysButtons': 'already on saved stacks (save/load screens) and below KR_T9HomeCasual. Keep in place; '
                                           'its casual and config call sites must keep calling KR_T9HomeCasual / KR_T9HomeConfig.',
    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15, r17 and r18 (now called from KR_T18RunSandboxed).',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15, r17 and r18.',
    'KR_T18RunSandboxed': 'NEW in r18 and pinned from now on: on saved stacks when the player saves during a sandboxed replay '
                          '(KR_T9HomeCasual > KR_T18RunSandboxed (return after its RunEvent call) > RunEvent) and inside the '
                          'sandbox\\'s own temporary resume image (return after its gamesave::detail::セーブ実行 call, offset 174). '
                          'Keep index, address and code bytes in every later build.',
}
FORWARDED = {
    'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage',
    'KR_T9LaneTitle': 'KR_T18LaneTitle', 'KR_T9CardRow': 'KR_T18CardRow',
    'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
    'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage',
}
NO_RESTORE = ('Codex must never run publish_calendar_*.py --restore or otherwise remove the calendar overlay (KR_T9*/KR_T17*/KR_T18* '
              'functions, the nine r15 same-length operands, the RunEvent operand swap in KR_T9HomeCasual). The calendar is a permanent '
              'user-requested feature: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry '
              'the calendar functions forward; restore is reserved for the user\\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_calendar_*.py --restore 를 실행하거나 달력 오버레이(KR_T9*/KR_T17*/KR_T18* 함수, r15 의 같은 길이 '
                 '피연산자 9곳, KR_T9HomeCasual 의 RunEvent 피연산자 교체)를 지우지 않는다. 달력은 사용자가 요청한 영구 기능이다: 깨끗한 '
                 '기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 달력 함수를 이어 싣는다. 되돌리기는 사용자가 명시적으로 '
                 '요청할 때만 한다.')
INSTRUCTION = (
    'Claude r18 (2026-09-27): in-game event calendar = r17 screens + replay lock + replay sandbox (design ingame/설계_v3_글메뉴판.md, '
    'r16/r17/r18 요구). ' + NO_RESTORE + ' r17 was installed 07:24 and restored 14:11 (evidence/calendar_r17 journal RESTORED); r18 '
    'replaces the r17 candidate and carries its screens itself, every r17 function renamed KR_T18* (no KR_T16*/KR_T17* exists in the '
    'runtime). Payload AIN only (PACT/EX untouched). KR_T18* functions appended; no original function relocated. Eight r15 functions '
    'keep their index and arguments but their body is a one-call forwarder at a new address: KR_T9MonthPage/MemPage/LaneTitle/CardRow/'
    'ChipRow/MonthChips -> KR_T18* (r17 achievement bars, day cells ▲●○ without ★, 10-cell month bar, summary page lowered to y 186 '
    'with ■選択ダイアログ／上座標制限値, drawer rows 「이름 k/n □□□□□」, E-number tails on the 26 colliding rows; counts on the home panel '
    'set Σ KR_PlayerEventCount(0..3)/1043, the 121 calendar events outside it listed but counted only on 「패널 밖 n/121」), '
    'KR_T9CardPage -> KR_T18CardPage and KR_T9EventPage -> KR_T18EventPage (replay lock: 「이 장면 재생」 only for a scene registered '
    'in this save (N_ScenarioRegister::IsRegisteredEvent, ○); ● unseen and △ read only in another save show a lock line instead; bundle '
    'stages judged one by one; r15 context lock kept). These page functions are never on a saved stack. ONE same-length operand: in '
    'KR_T9HomeCasual the CALLFUNC LSys3xScript::RunEvent now calls KR_T18RunSandboxed (bool, no arguments, like RunEvent). '
    'KR_T18RunSandboxed = the game\\'s own recollection-mode method (game::detail::MemoryModeEvent_Begin/_End/_Cleanup): it deletes and '
    'writes the temporary resume save <EX Ｅ＿セーブファイル名＿接頭語>KRReplay.asd (+ .vsf) with gamesave::detail::セーブ実行(file, "", "", '
    'false); true = fresh path -> RunEvent -> gamesave::detail::ロード実行(file) (ResumeLoad, does not return); false = resumed path -> '
    'delete the temp file, put back LSys3xScript::m_FuncName / m_IsSysScenario recorded at the request (YoruKR.T18.Prev*), return. '
    'No temp file after the event (a save made during the replay loaded later) = no restore; the resume save failing (no .asd/.vsf) '
    '= no replay, notice. The temp file name never collides with user slots (<prefix>%02d.asd incl. the pinned autosaves 998/999) or '
    'the game\\'s own temporary files (QC, TempSelect, BackSelect1/2, MemoryMode, SystemSuspend, Reload). Pinned: KR_T9HomeCasual '
    '(code identical to r15 except that operand), KR_T9HomeConfig, C_SceneHomebase@CheckGameSysButtons, C_SceneHomebase@Run, '
    'LSys3xScript::RunEvent and now KR_T18RunSandboxed keep index, address and code bytes; r15\\'s nine same-length CALLFUNC operands '
    'stay applied. Panel code (KR_T8*, KR_Rate*, KR_PlayerEventCount) untouched; the calendar\\'s panel-outside table (KR_T18Out) is '
    'derived from KR_PlayerEventCount at build time: if Codex changes the panel set, rebuild the calendar. State: SystemService '
    'variables YoruKR.T9.* and YoruKR.T18.* (not part of resume images: verified natively); no globals, structs or save schema change. '
    'Tables stay r15\\'s (chart/build_chart_v2.py) plus the r16 tail table and the r17 panel-outside table: rebuild when the chart data '
    'changes. Every earlier contract stays in force.')


''' + t[b:]

rep("        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, r17_byte_identical_to_r15=True)",
    "        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why,\n"
    "                            code=man['pinned_functions'].get(name, dict(new_in_r18=True)))")
rep("""        status='CALENDAR_R17_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),""",
    """        status='CALENDAR_R18_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),""")
rep("""        replaces=dict(r16_candidate_ain_sha256=L.R16_AIN_SHA, r16_installed=False,
                      function_names='new functions are all KR_T17*; KR_T16* (r16) never shipped and are not in this candidate'),
        added_functions=len(ids), added_function_names=sorted(ids), forwarded_functions=forwarded, same_length_sites=[],""",
    """        replaces=man['replaces'], no_restore_rule=NO_RESTORE,
        added_functions=len(ids), added_function_names=sorted(ids), forwarded_functions=forwarded, same_length_sites=man['same_length_sites'],
        sandbox=dict(man['sandbox'], verified_natively=dict(probe['sandbox'], files_at_end=None) if probe.get('sandbox') else None,
                     session_variables_restored_by_resumeload=(probe.get('sandbox') or {}).get('session_variables_restored_by_resumeload')),
        replay_lock=dict(rule='「이 장면 재생」 only when the scene is registered in this save (IsRegisteredEvent, ○); ● / △ -> one lock line',
                         pages=['KR_T9CardPage -> KR_T18CardPage', 'KR_T9EventPage -> KR_T18EventPage'],
                         second_check='KR_T18Request (state 2 + context) and KR_T18RunSandboxed (IsRegisteredEvent of the prepared name)'),""")
rep("""                              'every KR_T9 / KR_T17 page and table function, incl. the six forwarded ones (S4: no saved frame in them)'],""",
    """                              'every KR_T9 / KR_T18 page and table function, incl. the eight forwarded ones (S4: no saved frame in them)'],""")
rep("""                          native_blocks_equal_vm=native['counts']['N_blocks_identical'], native_panel=native['blocks'].get('panel_same_save'),""",
    """                          native_blocks_equal_vm=native['counts']['N_blocks_identical'], native_panel=native['blocks'].get('panel_same_save'),
                          native_sandbox=native['blocks'].get('sandbox'),""")
rep("""        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_r17_preserved_by',""",
    """        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_r18_preserved_by',""")
rep("""def probe_ok(probe):
    return bool(probe.get('exit_code') == 0 and probe['log'] and probe['log'][-1] == 'END' and probe['user_save_folder_unchanged']
                and not probe['c_drive_alicesoft_changes'] and not probe.get('vm_error') and not probe.get('message') and not probe.get('events')
                and probe.get('home_before_after', {}).get('differing_pixels') == 0
                and probe.get('month_before_after_summary', {}).get('differing_pixels') == 0)""",
    """def probe_ok(probe):
    \"\"\"r17's conditions + the sandbox: home before = home after the replay (pixels and every logged state key outside the allow
    list), temp file present during the replay and gone after, the mid-replay load keeps the replay (no temp file). The user's
    folder may change only while the user's own game runs (the probe logs its own save folder inside run/).\"\"\"
    sb = probe.get('sandbox') or {}
    user_ok = probe['user_save_folder_unchanged'] or bool((probe.get('user_game_running') or {}).get('before') or (probe.get('user_game_running') or {}).get('after'))
    return bool(probe.get('exit_code') == 0 and probe['log'] and probe['log'][-1] == 'END' and user_ok and probe.get('probe_save_folder_inside_run')
                and not probe.get('vm_error') and not probe.get('message') and not probe.get('events')
                and probe.get('home_before_after', {}).get('differing_pixels') == 0
                and probe.get('month_before_after_summary', {}).get('differing_pixels') == 0
                and set(sb.get('states', [])) >= {'HOME', 'PREPLAY', 'MIDREPLAY', 'AFTER', 'MIDLOAD'}
                and sb.get('home_vs_after') == {} and sb.get('home_vs_preplay') == {}
                and sb.get('after_temp_files') == ['0', '0'] and sb.get('midreplay_temp_files') == ['1', '1']
                and sb.get('midload_temp_files') == ['0', '0'] and not sb.get('temp_file_on_disk_at_end'))""")
rep("""        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r17 on the new runtime')""",
    """        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r18 on the new runtime')""")
rep("""        issues.append('native titles / rows / panel not compared with the VM (verify_calendar_r17.py --native)')""",
    """        issues.append('native titles / rows / panel / sandbox not compared with the VM (verify_calendar_r18.py --native)')""")
rep("""            or 'panel_same_save' not in native.get('blocks', {}):""",
    """            or 'panel_same_save' not in native.get('blocks', {}) or not native.get('counts', {}).get('N_sandbox_state_equal'):""")
rep("""        issues.append('evidence/calendar_r17 already exists: inspect the earlier transaction')
    if (R / 'evidence' / 'calendar_r16').exists() or (R / 'required_calendar_r16.json').exists():
        issues.append('r16 appears installed after all (evidence/calendar_r16 or required_calendar_r16.json): r17 was built to replace an uninstalled r16 — inspect first')""",
    """        issues.append('evidence/calendar_r18 already exists: inspect the earlier transaction')
    if (R / 'evidence' / 'calendar_r16').exists() or (R / 'required_calendar_r16.json').exists():
        issues.append('r16 appears installed after all (evidence/calendar_r16 or required_calendar_r16.json) - inspect first')
    j17 = read(L.R17_JOURNAL) if L.R17_JOURNAL.exists() else {}
    if j17.get('status') != 'RESTORED' or (R / 'required_calendar_r17.json').exists():
        issues.append('r17 is installed again (evidence/calendar_r17 journal not RESTORED or required_calendar_r17.json present): r18 was built on the base without r17 - rebuild')""")
rep("""    full['calendar_r17_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)""",
    """    full['calendar_r18_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)""")
rep("""        nm.update(status=STATUS, time=now, calendar_r17_revision=rev)""", """        nm.update(status=STATUS, time=now, calendar_r18_revision=rev)""")
rep("""            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_r17_overlay=str(E / 'source' / 'manifest.json'))""",
    """            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_r18_overlay=str(E / 'source' / 'manifest.json'))""")
rep("""            c['calendar_r17_preserved_by'] = str(E)""", """            c['calendar_r18_preserved_by'] = str(E)""")
rep("""        nc.update(status=STATUS, manifest_sha256=mh, calendar_r17_revision=rev)""", """        nc.update(status=STATUS, manifest_sha256=mh, calendar_r18_revision=rev)""")
rep("""                      translation_map_sha256=L.sha(translation), calendar_r17_evidence=str(E))""",
    """                      translation_map_sha256=L.sha(translation), calendar_r18_evidence=str(E))""")
a = t.index('        note = (f"\\n\\n### {now} 인게임 이벤트 달력 r17 설치')
b = t.index("        write(R / 'progress.md'", a)
t = t[:a] + '''        note = (f"\\n\\n### {now} 인게임 이벤트 달력 r18 설치 (Claude Opus 5.5; 14:11 에 되돌려진 r17 을 대신함)\\n"
                "- r17 화면(달성도 막대 · 요약 쪽 · 서랍 줄, 함수 이름 KR_T18*) + 재생 잠금(이 저장에서 본 장면 ○ 만 「이 장면 재생」, ● · △ 는 잠금 줄) + 재생 뒤 되돌리기(KR_T18RunSandboxed: 게임 회상 모드와 같은 임시 이어하기 저장 <접두어>KRReplay.asd → RunEvent → ロード実行).\\n"
                "- AIN 한 파일, 원본 함수 이전 0, r15 함수 8개는 번호 그대로 한 줄 전달, 같은 길이 교체는 KR_T9HomeCasual 의 RunEvent 피연산자 4바이트 하나(→ KR_T18RunSandboxed), 주소 유지 함수 6개(KR_T18RunSandboxed 포함).\\n"
                "- " + NO_RESTORE_KO + "\\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {E}; 되돌리기(사용자 요청 때만) publish_calendar_r18.py --restore.\\n")
''' + t[b:]
rep("""        nm['next'] = 'User screen check: 이벤트 달력 달 쪽(막대 반올림·▲●○, ★ 없음·9월 3열), 달성도 보기(왼쪽 패널 전체 %와 같은 값), 레인 쪽 서랍 줄 「이름 k/n □□□□□」, 회상 · 그 밖 (패널 밖), 10월 마나미 E번호 꼬리.'""",
    """        nm['next'] = 'User screen check: 이벤트 달력 r17 화면(막대·▲●○·달성도 보기·서랍 줄) + r18: ● · △ 카드는 「이 장면 재생」 대신 잠금 줄, ○ 장면 재생 뒤 본거지 달성률 · 친밀도 · 날짜가 재생 전과 같음.'""")
left = [(i, l[:160]) for i, l in enumerate(t.splitlines(), 1)
        if 'r17lib' in l or "'calendar_r17_" in l or 'KR_T17' in l.replace('KR_T9*/KR_T17*/KR_T18*', '').replace('KR_T16*/KR_T17*', '')]
print('left:', left)
assert not left
P.write_text(t, 'utf8')
import ast
ast.parse(t)
print('patched', P)
