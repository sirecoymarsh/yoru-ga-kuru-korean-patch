"""Claude Opus 5.5 (2026-09-28) r22: install / restore of the chart r22 candidate (the event flow chart screen of the menu-bar
「모드」 menu, stage 2), after publish_modmenu_r21.py (same transaction, same KRMenu scratch rule).
r22 = the r21 install + the chart: the 「chart」 request opens a save-independent event flow chart (KR_C*) on the title screen (new
same-length poll / serve sites in C_SceneTitle@Update / @Run) and in the home menu (KR_MDo forwarded); unlock = the game's global
records (first-message read marks, recollection unlocks) or 「전체 개방」; a click opens the calendar's card / scene page (chart
branch) and 이 장면 재생 replays through the game's memory-mode path (the recollection mode's own code).

  python publish_chart_r22.py --contract   write the Codex contract draft r22_chart/required_chart_r22.json
  python publish_chart_r22.py --fixture    transaction fixture on disposable files under r22_chart/work (no runtime): pair
                                           apply/restore, injected failures, tampering, interrupted restore, a whole install
                                           transaction in a disposable project (recovery runtime lacking a payload file, a
                                           KRMenu\\ request folder in the runtime)
  python publish_chart_r22.py --verify     read-only readiness check (hashes, VM, self-test, probes, native compare, scan,
                                           fixture, contract list, pointer)
  python publish_chart_r22.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_chart_r22.py --restore    undo an install exactly (journal-driven, resumable, idempotent): the runtime goes
                                           back to the pre-install AIN (= the r21 install)

Payload: NightRemaster.ain only (PACT/EX/FNL, the Manual chart and winmm.dll untouched). One journaled transaction, as in r4~r21:
PREPARED (evidence/chart_r22: before/candidate copies, metadata snapshots) -> atomic hash-checked replacement -> runtime manifest +
current.json + every required_*.json present at install time (chart_r22_preserved_by; their required_files row for the AIN
follows) + new required_chart_r22.json + latest_worked_translation.json + progress.md note -> exact tree (the runtime's KRMenu\\
folder excluded) / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back files and metadata; --restore returns
the exact pre-install state. Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
"""
from pathlib import Path
import copy, datetime, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r22lib as L

R = L.CODEX
O = HERE / 'candidate'
E = R / 'evidence' / 'chart_r22'                    # created only by --install
PTR = L.CURRENT
FILES = ['NightRemaster.ain']
NEW = 'required_chart_r22.json'
DRAFT = HERE / NEW
STATUS = 'CHART_R22_INSTALLED_NATIVE_PASS'
READY = 'CHART_R22_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'
DEFECTS = 48
RUNTIME_SCRATCH = 'KRMenu'           # <runtime>\KRMenu\: request / result / .req files the hook and the game write at run time
KRMENU_FILES = ['request.txt', 'last_result.txt', 'reset.req', 'restore.req']
KRMENU_RULE = ('<runtime>/KRMenu/ is the temporary exchange-file folder of the mod-menu hook and the game script (request.txt, '
               'last_result.txt, reset.req, restore.req): never put it in a manifest, ignore it in every tree check, and never delete '
               'it (a pending reset.req / restore.req or an unread last_result.txt may be waiting there).')
KRMENU_RULE_KO = ('<실행본>/KRMenu 는 후크 · 스크립트의 일시 교환 파일 폴더(request.txt · last_result.txt · reset.req · restore.req)이며 '
                  'manifest 에 넣지 않고 트리 검사에서 무시한다; 지우지 말 것(처리 대기 중인 reset.req / restore.req 나 아직 안 본 '
                  'last_result.txt 가 있을 수 있다).')
PINNED = {
    'KR_T9HomeCasual': 'on saved stacks during a calendar replay: C_SceneHomebase@Run > CheckGameSysButtons (return after the '
                       'casual call site) > KR_T9HomeCasual (return after the RunEvent call site, offset 198) > KR_T18RunSandboxed > '
                       'RunEvent > event. Keep index, address and code bytes in every later build. r18 changed exactly one thing in '
                       'it: the 4-byte operand of that call (LSys3xScript::RunEvent -> KR_T18RunSandboxed, same signature, same '
                       'length); every other byte equals the r15 candidate. r19, r20, r21 and r22: byte-identical to r18.',
    'KR_T9HomeConfig': 'the settings screen opened from the home base runs inside it (no save is possible there as far as known); '
                       'keep it in place as a precaution (r15 contract; r18, r19, r20, r21 and r22 byte-identical).',
    'C_SceneHomebase@CheckGameSysButtons': 'already on saved stacks (save/load screens) and below KR_T9HomeCasual. Keep in place; '
                                           'its casual and config call sites must keep calling KR_T9HomeCasual / KR_T9HomeConfig.',
    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15, r17, r18, r19, r20, r21 and r22 (called from KR_T18RunSandboxed and, in r22, from KR_CReplayRun as in the recollection mode).',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15, r17, r18, r19, r20, r21 and r22.',
    'KR_T18RunSandboxed': 'r18, pinned (r19, r20, r21 and r22 byte-identical): on saved stacks when the player saves during a sandboxed replay '
                          '(KR_T9HomeCasual > KR_T18RunSandboxed (return after its RunEvent call) > RunEvent) and inside the '
                          'sandbox\'s own temporary resume image (return after its gamesave::detail::セーブ実行 call, offset 174). '
                          'Keep index, address and code bytes in every later build.',
}
R19_FORWARDED = ['KR_T18CardRow', 'KR_T18CardTitle', 'KR_T18EventTitle', 'KR_T9StagePage', 'KR_T9ChipPage']
R18_FORWARDED = ['KR_T9MonthPage', 'KR_T9MemPage', 'KR_T9LaneTitle', 'KR_T9CardRow', 'KR_T9ChipRow', 'KR_T9MonthChips',
                 'KR_T9CardPage', 'KR_T9EventPage']
R22_FORWARDED = {'KR_MDo': 'KR_CDoHome', 'KR_T9Seen': 'KR_CSeen', 'KR_T9State': 'KR_CState', 'KR_T9Legend': 'KR_CLegend',
                 'KR_T18CardPage': 'KR_CCardPage', 'KR_T18EventPage': 'KR_CEventPage'}
NO_RESTORE = ('Codex must never run publish_calendar_*.py --restore, publish_modmenu_*.py --restore or publish_chart_*.py --restore or '
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


def js(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def put(path, data):
    """publish_remaster_multiplier_20260915.put: atomic write through a temporary file in the same folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.chart22-', suffix='.tmp', delete=False) as f:
        tmp = Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def replace_checked(src, dest, expected):
    assert L.sha(src) == expected, ('source mismatch', str(src))
    assert dest.parent.is_dir(), ('target folder missing', str(dest.parent))
    tmp = dest.with_name(dest.name + '.chart22-copy.tmp')
    assert not tmp.exists(), str(tmp)
    try:
        shutil.copy2(src, tmp)
        assert L.sha(tmp) == expected
        os.replace(tmp, dest)
        assert L.sha(dest) == expected
    finally:
        if tmp.exists():
            tmp.unlink()


def processes():
    cmd = ("$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process -Filter \"Name = 'NightRemaster.exe'\" | "
           "Select-Object ProcessId,ExecutablePath) | ConvertTo-Json -Compress")
    p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, timeout=60, env=L.env())
    assert p.returncode == 0, ('process preflight failed', p.stderr.decode('utf8', 'replace'))
    s = p.stdout.decode('utf-8-sig').strip()
    result = json.loads(s) if s else []
    return result if isinstance(result, list) else [result]


def active_target(rows, rt):
    exe = (rt / 'NightRemaster.exe').resolve()
    return [x for x in rows if not x.get('ExecutablePath') or Path(x['ExecutablePath']).resolve() == exe]


def stopped(rt):
    return not active_target(processes(), rt)


def exact_tree(rt, rows):
    """The runtime holds exactly the manifest's files; <runtime>/KRMenu/ (request / result / .req files the native hook and the game
    write while the game runs) is scratch, not part of any build."""
    assert rt == rt.resolve(), ('redirected runtime', rt)
    expected = {r['path'] for r in rows}
    assert not any(r['path'].split('/')[0] == RUNTIME_SCRATCH for r in rows), 'a build file inside the KRMenu scratch folder'
    assert {p.relative_to(rt).as_posix() for p in rt.rglob('*') if p.is_file() and p.relative_to(rt).parts[0] != RUNTIME_SCRATCH} == expected
    for r in rows:
        p = (rt / r['path']).resolve()
        assert p.is_relative_to(rt)
        assert p.stat().st_size == r['size'] and L.sha(p) == r['sha256'], p


def snapshot_folder(folder):
    assert folder.is_dir(), folder
    return {p.relative_to(folder).as_posix(): L.sha(p) for p in folder.rglob('*') if p.is_file()}


def recovery_hashes(rec, files):
    """The payload files the recovery runtime HAS (the r19 21:44 fix): the same set is hashed before and after the swap, so a
    payload file the recovery runtime lacks (e.g. a help-menu chart newer than the recovery build) neither fails nor hides a change."""
    return {n: L.sha(rec / n) for n in files if (rec / n).exists()}


def pair_apply(src, backup, live, before, after, fail_after=0, files=None):
    files = files or FILES
    for n in files:
        assert L.sha(src / n) == after[n], ('payload', n)
        assert L.sha(backup / n) == before[n], ('backup', n)
        assert L.sha(live / n) == before[n], ('baseline', n)
    attempted = []
    try:
        for n in files:
            attempted.append(n)
            replace_checked(src / n, live / n, after[n])
            if len(attempted) == fail_after:
                raise RuntimeError('fixture injected replacement failure')
    except BaseException:
        for n in reversed(attempted):
            replace_checked(backup / n, live / n, before[n])
        raise


def pair_restore(backup, live, before, after, files=None):
    files = files or FILES
    for n in files:
        assert L.sha(backup / n) == before[n], ('tampered backup', n)
        assert L.sha(live / n) in [before[n], after[n]], ('unknown live state', n)
    for n in files:
        tmp = live / (n + '.chart22-copy.tmp')
        if tmp.exists():
            assert tmp.resolve().parent == (live / n).resolve().parent and tmp.resolve().is_relative_to(live.resolve()) and tmp.is_file()
            quarantine = backup.parent / 'interrupted_incoming'
            quarantine.mkdir(exist_ok=True)
            dest = quarantine / (tmp.name + '.' + L.sha(tmp)[:12] + '.' + str(datetime.datetime.now().timestamp()))
            tmp.replace(dest)
    for n in files:
        if L.sha(live / n) != before[n]:
            replace_checked(backup / n, live / n, before[n])


def contracts_now(root=None):
    root = root or R
    return sorted(p.name for p in root.glob('required_*.json') if p.name != NEW)


# ------------------------------------------------------------------ the contract draft
def draft_contract():
    man = read(O / 'manifest.json')
    vm = read(L.WORK / 'build' / 'vm_verification.json')
    st = read(L.WORK / 'build' / 'vm_verification_selftest.json')
    probe = read(L.EVID / 'probe_result.json')
    p22 = read(L.EVID / 'probe_r22.json')
    kinds = read(L.EVID / 'replay_kinds.json')
    native = read(L.WORK / 'build' / 'native_compare.json')
    scan = read(L.WORK / 'scan_report.json')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    cg = read(L.FLOW / 'graph' / 'event_cg.json')
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, code=man['pinned_functions'][name])
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    r22n = native.get('r22') or {}
    return dict(
        status='CHART_R22_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files={n: man['files'][n]['sha256'] for n in FILES},
        candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False, ex_changed=False, fnl_changed=False, chart_changed=False,
        hook_changed=False, no_restore_rule=NO_RESTORE, based_on_r21_install=True,
        added_functions=len(ids), added_function_names=sorted(ids), jam_bodies=man['jam_bodies'],
        forwarded_functions=man['forwarded_functions'], r19_forwarders_kept=R19_FORWARDED, r18_forwarders_kept=R18_FORWARDED,
        same_length_sites=man['same_length_sites'], earlier_same_length_sites_kept=man['earlier_same_length_sites_kept'],
        relocated_original_functions=[], pinned_addresses=pinned,
        never_on_saved_stack=['every KR_C function except, by construction, inside the game\'s own memory-mode resume image '
                              '(NightRMemoryMode.asd, the recollection mode\'s temporary file: made by AFL_MemoryModeEvent_Begin inside '
                              'KR_CReplayRun and deleted by _Cleanup right after it is loaded back) and an engine-made SystemSuspend / '
                              'Reload image taken while the chart or a replay runs (like RunHome, KR_T9HomeMenuRun and KR_MHomeRun, not '
                              'pinned); no slot save is possible in the chart (no save UI) and the recollection mode refuses save / load '
                              'while _g_回想中 (C_SysButton@IsAbleSave / IsAbleLoad). None of the user saves has a KR_C frame or a frame in '
                              'the six forwarded functions or the two title sites (S4).'],
        chart=dict(cells=man['data']['cells'], per_tab=man['data']['per_tab'], thumbnail_cells=man['data']['thumbnail_cells'],
                   small_cells=man['data']['small_cells'], order=man['data']['cell_order'], parts=man['parts'], root_z=man['root_z'],
                   event_cg=dict(sha256=L.sha(L.FLOW / 'graph' / 'event_cg.json'), gates={k: v['ok'] for k, v in cg['gates'].items()}),
                   unlock='first-message MsgSkip read mark or N_ModeScene::CheckEnabelScenario (the game\'s recollection unlock), or 「전체 '
                          '개방」 (YoruKR_Chart.dat 1, read once when the chart opens); never IsRegisteredEvent while the chart is open',
                   replay='KR_CReplayRun = C_SceneModeScene@ExecScene from AFL_MemoryModeEvent_Begin on (S8 compares the ops)',
                   replay_kinds=kinds['verdicts'], not_playable_events=man['data']['not_playable_events']),
        protocol=dict(title_poll='C_SceneTitle@Update: KR_CTitleTick in place of C_UserInputManager::IsClickConfig (two FileOperation.ExistFile '
                                 'a title frame; a waiting request / result ends the title wait with KR_CCode 2026092802 and answers false)',
                      title_serve='C_SceneTitle@Run: KR_CTitleServe in place of ■方向キー処理／削除 (the original call, then the result and the request)',
                      home='r21 unchanged (KR_MHomeRun / KR_MTick); KR_MDo forwarded to KR_CDoHome',
                      runtime_scratch_folder=RUNTIME_SCRATCH),
        runtime_exchange_folder=dict(path='<runtime>/KRMenu', files=KRMENU_FILES, rule=KRMENU_RULE, rule_ko=KRMENU_RULE_KO,
                                     in_manifest=False, tree_checks='ignore', delete=False),
        session_variables_new=man['session_variables_new'], new_globals=0, new_struct_members=0, serialized_schema_changes=0,
        verification=dict(vm=vm['counts'], vm_steps=vm['vm_steps'], planted_defects_caught=sum(p['caught'] for p in st['planted_defects']),
                          planted_defects=len(st['planted_defects']), saves_checked=vm['saves_checked'], frames_checked=vm['frames_checked'],
                          calendar_tour_on_r22=dict(passed=probe_ok(probe), seconds=probe.get('seconds'), save=probe.get('save'),
                                                    screenshots=[Path(x).name for x in probe['screenshots']],
                                                    home_before_after_differing_pixels=probe.get('home_before_after', {}).get('differing_pixels')),
                          chart_tours=dict(passed=probe22_ok(p22), title=dict(seconds=p22['title'].get('seconds'), shots=p22['title'].get('shots')),
                                           home=dict(seconds=(p22.get('home') or {}).get('seconds'), shots=(p22.get('home') or {}).get('shots')),
                                           native_compare=r22n),
                          replay_kinds=kinds['verdicts'],
                          native_blocks_equal_vm=native['counts'].get('N_blocks_identical'), native_r20_blocks_equal_vm=native['counts'].get('N_r20_blocks_identical'),
                          native_chart_pages_equal_vm=native['counts'].get('R22N_pages_equal_vm'),
                          defender=scan['status'], transaction_fixture=fx['status'] if fx else 'NOT_RUN',
                          fixture_recovery_runtime_lacking_a_payload_file=(fx or {}).get('install_with_recovery_lacking_payload_file')),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='chart_r22_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)


def probe_ok(probe):
    """The r20 calendar tour run on the r22 candidate (probe_calendar_tour_r22.py full): r19's conditions (sandbox, home pixels) +
    r20's (the member screen returns to a pixel-identical home, the partner run ended cleanly, our parts are gone after every exit)."""
    sb = probe.get('sandbox') or {}
    user_ok = probe['user_save_folder_unchanged'] or bool((probe.get('user_game_running') or {}).get('before') or (probe.get('user_game_running') or {}).get('after'))
    r20 = probe.get('r20') or {}
    st = r20.get('status') or {}
    pt = r20.get('partner') or {}
    pr = probe.get('partner_run') or {}
    return bool(probe.get('exit_code') == 0 and probe['log'] and probe['log'][-1] == 'END' and user_ok and probe.get('probe_save_folder_inside_run')
                and not probe.get('vm_error') and not probe.get('message') and not probe.get('events')
                and probe.get('home_before_after', {}).get('differing_pixels') == 0
                and probe.get('home_before_after_member', {}).get('differing_pixels') == 0
                and probe.get('month_before_after_summary', {}).get('differing_pixels') == 0
                and set(sb.get('states', [])) >= {'HOME', 'PREPLAY', 'MIDREPLAY', 'AFTER', 'MIDLOAD'}
                and sb.get('home_vs_after') == {} and sb.get('home_vs_preplay') == {}
                and sb.get('after_temp_files') == ['0', '0'] and sb.get('midreplay_temp_files') == ['1', '1']
                and sb.get('midload_temp_files') == ['0', '0'] and not sb.get('temp_file_on_disk_at_end')
                and st.get('after_exit1', {}).get('ours') == 0 and st.get('after_exit2', {}).get('ours') == 0
                and st.get('page4', {}).get('ours') == 2 and st.get('second_entry_page4', {}).get('ours') == 2
                and pt.get('first', {}).get('ours') == pt.get('again', {}).get('ours') and pt.get('after_screen', {}).get('ours') == 0
                and pr.get('exit_code') == 0 and pr.get('log') and pr['log'][-1] == 'END' and not pr.get('vm_error') and not pr.get('message')
                and not pr.get('events'))


def probe22_ok(p22):
    """The chart tours (probe_chart_r22.py --title / --home): ended with END, exit 0, no engine error / message box, the replay ran in
    memory mode with the chart closed and came back."""
    ok = True
    for mode in ('title', 'home'):
        r = p22.get(mode)
        if not r:
            return False
        lg = r.get('log') or []
        ok = ok and r.get('exit_code') == 0 and not r.get('vm_error') and not r.get('message') and not r.get('timeout') and lg and lg[-1] == 'END' \
            and any(x.startswith('REPLAY first message memory=1') and 'ours=0' in x for x in lg) and any(x.startswith('RETURNED') and 'ours=0' in x for x in lg)
    return bool(ok)


# ------------------------------------------------------------------ the transaction (real paths or a disposable project)
class Ctx:
    """Every path the install transaction touches. The real one points at the Codex project; the fixture builds a disposable one."""
    def __init__(self, root, evidence, pointer, candidate, files, saves, stop_check, sources=None, note_title=None):
        self.root, self.evidence, self.pointer, self.candidate, self.files, self.saves = root, evidence, pointer, candidate, files, saves
        self.stop_check = stop_check
        self.sources = sources            # folder whose scripts/evidence are copied into evidence/source (None in the fixture)
        self.note_title = note_title or '메뉴바 「모드」 메뉴 r22(2단계, 이벤트 플로우 차트 화면) 설치 (Claude Opus 5.5; r21 설치본 위)'


def real_ctx():
    return Ctx(R, E, PTR, O, FILES, L.SAVES, stopped, sources=HERE)


def transact(ctx, fail_at=None):
    """The install transaction (r4~r19 shape). fail_at: fixture hook ('after_files', 'after_contracts', 'recovery_changed') that
    injects a failure at that point - the transaction must roll everything back."""
    root, ev, ptr_path, cand, files = ctx.root, ctx.evidence, ctx.pointer, ctx.candidate, ctx.files
    cur = read(ptr_path)
    rt = Path(cur['runtime']).resolve()
    mp = Path(cur['manifest'])
    man = read(cand / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in files}
    before = {n: L.sha(rt / n) for n in files}
    manifest = read(mp)
    exact_tree(rt, manifest['files'])
    saves = snapshot_folder(ctx.saves)
    keep = read(root / 'required_build_retention.json')
    rec = Path(keep['recovery_runtime'])
    rm = Path(keep['recovery_manifest'])
    assert L.sha(rm) == keep['recovery_manifest_sha256']
    rh = recovery_hashes(rec, files)
    contracts = contracts_now(root)
    paths = [mp, ptr_path, root / 'progress.md', root / 'latest_worked_translation.json'] + [root / n for n in contracts + [NEW]]
    assert len(paths) == len(set(x.name for x in paths))
    snapshots = {x: x.read_bytes() if x.exists() else None for x in paths}
    assert snapshots[root / NEW] is None
    ev.mkdir(parents=True)
    assert ev.resolve().is_relative_to(root.resolve()) and not ev.resolve().is_relative_to(rt)
    for folder in ['before', 'candidate', 'source', 'source/probe']:
        (ev / folder).mkdir()
    metadata = []
    for path, data in snapshots.items():
        if data is not None:
            put(ev / 'before' / path.name, data)
        metadata.append(dict(path=str(path), name=path.name, existed=data is not None, sha256=L.sha(path) if data is not None else None))
    for n in files:
        for d in ('before', 'candidate'):
            (ev / d / n).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rt / n, ev / 'before' / n)
        shutil.copy2(cand / n, ev / 'candidate' / n)
        assert L.sha(ev / 'before' / n) == before[n] and L.sha(ev / 'candidate' / n) == after[n]
    if ctx.sources is not None:
        for f in ctx.sources.iterdir():
            if f.is_file() and f.suffix in ('.py', '.jaf', '.json', '.md', '.ps1'):
                shutil.copy2(f, ev / 'source' / f.name)
        for f in (L.EVID / 'probe').glob('*.png'):
            shutil.copy2(f, ev / 'source' / 'probe' / f.name)
        for n in ['vm_verification.json', 'vm_verification_selftest.json', 'native_opcode_audit.json', 'native_compare.json']:
            shutil.copy2(L.WORK / 'build' / n, ev / 'source' / n)
        for n in ['scan_report.json', 'transaction_verification.json']:
            shutil.copy2(L.WORK / n, ev / 'source' / n)
        for n in ['probe_result.json', 'probe_regs.json', 'probe_r22.json', 'probe_kinds.json', 'replay_kinds.json', 'event_cg_gate.json',
                  'verify.json', 'verify_selftest.json']:
            if (L.EVID / n).exists():
                shutil.copy2(L.EVID / n, ev / 'source' / n)
        for sub in ('probe_kinds', 'probe_zoom'):
            if (L.EVID / sub).exists():
                shutil.copytree(L.EVID / sub, ev / 'source' / sub)
        shutil.copy2(L.FLOW / 'graph' / 'event_cg.json', ev / 'source' / 'event_cg.json')
    shutil.copy2(cand / 'manifest.json', ev / 'source' / 'manifest.json')
    latest = read(root / 'latest_worked_translation.json')
    assert latest['manifest_sha256'] == cur['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    full = read(Path(latest['translation_map']))
    sequence = full['target_text_sequence_sha256']
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full['chart_r22_overlay'] = dict(evidence=str(ev), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)
    translation = ev / 'source' / 'installed_translation_map.json'
    put(translation, js(full))
    assert read(translation)['target_text_sequence_sha256'] == sequence
    put(ev / 'save_hashes_before.json', js(saves))
    put(ev / 'recovery_hashes_before.json', js(dict(recovery_runtime=str(rec), hashed=rh, not_in_recovery=[n for n in files if n not in rh])))
    j = dict(status='PREPARED', runtime=str(rt), before=before, after=after, metadata=metadata, files=files)
    put(ev / 'journal.json', js(j))
    draft = read(cand / NEW) if (cand / NEW).exists() else read(DRAFT)

    def write(path, data):
        assert path in snapshots
        j.setdefault('metadata_after', {})[str(path)] = hashlib.sha256(data).hexdigest()
        put(ev / 'journal.json', js(j))
        put(path, data)
    attempted = False
    try:
        assert ctx.stop_check(rt) and read(ptr_path) == cur and L.sha(mp) == cur['manifest_sha256'] and saves == snapshot_folder(ctx.saves)
        attempted = True
        pair_apply(ev / 'candidate', ev / 'before', rt, before, after, files=files)
        if fail_at == 'after_files':
            raise RuntimeError('fixture: injected failure after the file swap')
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, author=L.AUTHOR, files=after, source_files=before, evidence=str(ev), native_probe_verified=True,
                   screen_verified=False, persistent_return_offsets_exact=True, MSG1_exact=True, save_schema_changes=0, save_writes=0,
                   existing_saves_checked=draft['verification']['saves_checked'], frames_checked=draft['verification']['frames_checked'],
                   same_length_sites=[dict(function=s['function'], kind=s['kind'], original=s['original'], replacement=s['replacement'], site=s['site'])
                                      for s in draft['same_length_sites']],
                   pinned_addresses=draft['pinned_addresses'], protocol=draft.get('protocol'), translator_model=L.AUTHOR)
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now, chart_r22_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], chart_r22_overlay=str(ev / 'source' / 'manifest.json'))
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = ('User screen check: 이벤트 플로우 차트 r22 — 타이틀 화면과 본거지 첫 메뉴에서 메뉴바 「모드 → 이벤트 플로우 차트」: 달 탭 · '
                      '썸네일 칸 · 작은 칸 · 잠긴 칸(누르면 안내), 전체 개방 뒤 같은 칸 열림, 칸 → 카드 쪽 / 장면 쪽 → 이 장면 재생(회상 모드처럼, '
                      '끝나면 차트를 연 화면으로), 전체 개방 되돌리기 뒤 다시 잠김(재생한 장면은 읽음 표시가 남아 열린 채).')
        write(mp, js(nm))
        mh = L.sha(mp)
        for n in contracts:
            c = read(root / n)
            for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if k in c:
                    c[k] = mh
            for file, h in after.items():
                if file in c.get('required_files', {}):
                    c['required_files'][file] = h
            c['chart_r22_preserved_by'] = str(ev)
            write(root / n, js(c))
        if fail_at == 'after_contracts':
            raise RuntimeError('fixture: injected failure after the contracts')
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, required_files=after, evidence=str(ev),
                     preserves_contracts=sorted(contracts))
        write(root / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, chart_r22_revision=rev)
        write(ptr_path, js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation), chart_r22_evidence=str(ev))
        write(root / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} {ctx.note_title}\n"
                "- 이벤트 플로우 차트(2단계): 메뉴바 「모드 → 이벤트 플로우 차트」 요청을 타이틀 화면(새로: C_SceneTitle@Update 의 IsClickConfig "
                "자리 → KR_CTitleTick, C_SceneTitle@Run 의 ■方向キー処理／削除 자리 → KR_CTitleServe; 5개 명령 전부)과 본거지 첫 메뉴(r21 그대로, "
                "KR_MDo 한 줄 전달)에서 받아 차트 화면(KR_C*, 파츠 2026092200~2026092311)을 연다. 저장과 무관한 전체 지도: 해금 = 게임 전역 "
                "기록(첫 메시지 읽음 표시 · 회상 해금) 또는 전체 개방(YoruKR_Chart.dat 1). 칸 → 달력의 카드 쪽 / 장면 쪽(차트 가지) → 이 장면 "
                "재생 = 게임 회상 모드 경로(KR_CReplayRun = C_SceneModeScene@ExecScene 의 명령).\n"
                "- AIN 한 파일, 원본 함수 이전 0, 한 줄 전달 6개(KR_MDo · KR_T9Seen · KR_T9State · KR_T9Legend · KR_T18CardPage · KR_T18EventPage: "
                "차트 밖에서는 r15 · r18 몸체 그대로), 같은 길이 피연산자 2곳(C_SceneTitle@Update · @Run), 주소 유지 함수 6개 바이트 동일, "
                "새 전역 · 구조체 필드 0, 세션 변수 YoruKR.C.* 만.\n"
                "- " + KRMENU_RULE_KO + "\n"
                "- " + NO_RESTORE_KO + "\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) publish_chart_r22.py --restore.\n")
        write(root / 'progress.md', (snapshots[root / 'progress.md'] or b'') + note.encode('utf8'))
        exact_tree(rt, nm['files'])
        assert saves == snapshot_folder(ctx.saves)
        if fail_at == 'recovery_changed':
            (rec / next(iter(rh))).write_bytes(b'changed by the fixture')
        assert L.sha(rm) == keep['recovery_manifest_sha256'] and rh == recovery_hashes(rec, files), 'the recovery runtime changed during the install'
        j.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=L.sha(ptr_path))
        put(ev / 'journal.json', js(j))
    except BaseException as error:
        errors = []
        if attempted:
            try:
                pair_restore(ev / 'before', rt, before, after, files=files)
            except BaseException as failure:
                errors.append(repr(failure))
        for path, data in reversed(list(snapshots.items())):
            try:
                if data is not None:
                    put(path, data)
                elif path.exists():
                    path.unlink()
            except BaseException as failure:
                errors.append(repr(failure))
        j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK', error=repr(error), rollback_errors=errors)
        put(ev / 'journal.json', js(j))
        raise
    report = dict(status=STATUS, files=after, manifest_sha256=mh, runtime=str(rt), unchanged_save_files=len(saves), recovery_unchanged=True,
                  recovery_hashed=sorted(rh), recovery_lacks=[n for n in files if n not in rh], evidence=str(ev), author=L.AUTHOR)
    put(ev / 'publish_report.json', js(report))
    return report


def restore_ctx(ctx, runtime_override=None):
    ev = ctx.evidence
    j = read(ev / 'journal.json')
    rt = Path(j['runtime']).resolve()
    files = j.get('files') or FILES
    if runtime_override is None:
        assert rt == Path(read(ctx.pointer)['runtime']).resolve() or j['status'] in ('RESTORING', 'RESTORED')
    else:
        assert rt == Path(runtime_override).resolve()
    assert ctx.stop_check(rt), 'close the game first'
    if j['status'] == 'RESTORED':
        assert all(L.sha(rt / n) == j['before'][n] for n in files)
        print('ALREADY_RESTORED')
        return
    assert j['status'] in ['COMMITTED', 'PREPARED', 'ROLLBACK_INCOMPLETE', 'RESTORING']
    for row in j['metadata']:
        path = Path(row['path'])
        assert path.resolve().is_relative_to(ctx.root.resolve())
        if row['existed']:
            assert L.sha(ev / 'before' / row['name']) == row['sha256']
        current = L.sha(path) if path.exists() else None
        allowed = {row['sha256'], j.get('metadata_after', {}).get(str(path), row['sha256'])}
        assert current in allowed, ('A newer or unknown metadata state exists — inspect before restoring', str(path))
    j['status'] = 'RESTORING'
    put(ev / 'journal.json', js(j))
    pair_restore(ev / 'before', rt, j['before'], j['after'], files=files)
    for row in j['metadata']:
        path = Path(row['path'])
        if row['existed']:
            put(path, (ev / 'before' / row['name']).read_bytes())
        elif path.exists():
            path.unlink()
    assert all(L.sha(rt / n) == j['before'][n] for n in files)
    j['status'] = 'RESTORED'
    put(ev / 'journal.json', js(j))
    print('RESTORED EXACT PRE-INSTALL STATE')


def restore(runtime_override=None):
    restore_ctx(real_ctx(), runtime_override)


# ------------------------------------------------------------------ fixture
def fixture():
    root = L.WORK / ('fixture_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    f = Path(tempfile.mkdtemp(prefix='복구 검증 ', dir=root.parent if root.parent.exists() else L.WORK))
    b, s, l = f / 'backup', f / 'payload', f / 'live'
    for p in [b, s, l]:
        p.mkdir()
    for n in FILES:
        for d in (b, s, l):
            (d / n).parent.mkdir(parents=True, exist_ok=True)
        (b / n).write_bytes(('old ' + n).encode())
        shutil.copy2(O / n, s / n)
        shutil.copy2(b / n, l / n)
    before = {n: L.sha(b / n) for n in FILES}
    after = {n: L.sha(s / n) for n in FILES}
    pair_apply(s, b, l, before, after)
    assert all(L.sha(l / n) == after[n] for n in FILES)
    pair_restore(b, l, before, after)
    pair_restore(b, l, before, after)
    try:
        pair_apply(s, b, l, before, after, fail_after=1)
    except RuntimeError:
        pass
    else:
        raise AssertionError('failure not injected')
    assert all(L.sha(l / n) == before[n] for n in FILES)
    replace_checked(s / FILES[0], l / FILES[0], after[FILES[0]])
    pair_restore(b, l, before, after)
    for installed in [False, True]:
        if installed:
            pair_apply(s, b, l, before, after)
        for n in FILES:
            (l / (n + '.chart22-copy.tmp')).write_bytes(b'partial interrupted copy')
        pair_restore(b, l, before, after)
        assert all(L.sha(l / n) == before[n] for n in FILES) and not list(l.rglob('*.tmp'))
    for kind, folder, op in [('payload', s, lambda: pair_apply(s, b, l, before, after)), ('baseline', l, lambda: pair_apply(s, b, l, before, after)),
                             ('backup', b, lambda: pair_restore(b, l, before, after))]:
        n = FILES[-1]
        saved = (folder / n).read_bytes()
        (folder / n).write_bytes(b'tampered')
        state = {name: L.sha(l / name) for name in FILES}
        try:
            op()
        except AssertionError:
            pass
        else:
            raise AssertionError('tampering accepted: ' + kind)
        assert state == {name: L.sha(l / name) for name in FILES}
        (folder / n).write_bytes(saved)
    assert not active_target([dict(ExecutablePath=str(f / 'elsewhere/NightRemaster.exe'))], l)
    assert active_target([dict(ExecutablePath=str(l / 'NightRemaster.exe'))], l)
    whole = install_fixture(f)
    result = dict(status='TRANSACTION_FIXTURE_PASS', fixture=str(f), payload=after, install_restore=True, idempotent_restore=True,
                  runtime_scratch_folder_ignored=whole['scratch_folder_ignored'],
                  injected_failure_rollback=True, known_mixed_and_interruption_restore=True, partial_incoming_copy_recovered=True,
                  tampered_payload_baseline_backup_rejected=True, exact_process_path_filter=True, unicode_spaces_path=True,
                  interrupted_metadata_restoration_resumable=whole['interrupted_restore_resumable'],
                  install_with_recovery_lacking_payload_file=whole, no_incoming_residue=not list(l.rglob('*.tmp')), files=FILES)
    put(L.WORK / 'transaction_verification.json', js(result))
    return result


def fake_project(f, name, payload_files, recovery_has):
    """A disposable Codex-like project: runtime (+ manifest), recovery runtime holding only `recovery_has`, pointer, contracts,
    translation map, retention contract, saves, and a candidate folder with a manifest and a contract draft."""
    root = f / name
    rt = root / 'ui_cumulative' / 'latest' / 'runtime'
    rec = root / 'ui_cumulative' / 'recovery' / 'runtime'
    cand = root / 'candidate'
    saves = root / 'saves'
    for d in (rt, rec, cand, saves):
        d.mkdir(parents=True)
    (saves / 'NightR01.asd').write_bytes(b'a save that must not change')
    rows = []
    for n in payload_files + ['NightRemaster.exe', 'Data/Shader.slk']:
        (rt / n).parent.mkdir(parents=True, exist_ok=True)
        (rt / n).write_bytes(('runtime ' + n).encode())
        rows.append(dict(path=n, size=(rt / n).stat().st_size, sha256=L.sha(rt / n)))
        if n in recovery_has or n not in payload_files:
            (rec / n).parent.mkdir(parents=True, exist_ok=True)
            (rec / n).write_bytes(('recovery ' + n).encode())
    mp = root / 'ui_cumulative' / 'latest' / 'manifest.json'
    put(mp, js(dict(status='BASE', files=rows, ain=dict(status='BASE'))))
    (rt / RUNTIME_SCRATCH).mkdir()                                   # the hook's request folder, as a user's runtime may hold it
    (rt / RUNTIME_SCRATCH / 'request.txt').write_bytes(b'chart\r\n1\r\n2026-09-28 03:30:00\r\n')
    rmp = root / 'ui_cumulative' / 'recovery' / 'manifest.json'
    put(rmp, js(dict(status='RECOVERY')))
    ptr = root / 'ui_cumulative' / 'current.json'
    put(ptr, js(dict(runtime=str(rt), manifest=str(mp), manifest_sha256=L.sha(mp), status='BASE')))
    tmap = root / 'evidence' / 'old' / 'installed_translation_map.json'
    put(tmap, js(dict(target_text_sequence_sha256='seq', installed_ain_sha256=L.sha(rt / 'NightRemaster.ain'))))
    put(root / 'latest_worked_translation.json', js(dict(manifest_sha256=L.sha(mp), ain_sha256=L.sha(rt / 'NightRemaster.ain'),
                                                         translation_map=str(tmap), translation_map_sha256=L.sha(tmap))))
    put(root / 'required_build_retention.json', js(dict(recovery_runtime=str(rec), recovery_manifest=str(rmp), recovery_manifest_sha256=L.sha(rmp))))
    put(root / 'required_example_a.json', js(dict(status='A', required_files={'NightRemaster.ain': L.sha(rt / 'NightRemaster.ain')}, manifest_sha256=L.sha(mp))))
    put(root / 'required_example_b.json', js(dict(status='B', instruction='keep')))
    put(root / 'progress.md', 'progress\n'.encode('utf8'))
    files = {}
    for n in payload_files:
        (cand / n).parent.mkdir(parents=True, exist_ok=True)
        (cand / n).write_bytes(('candidate ' + n).encode() if n != 'NightRemaster.ain' else (O / n).read_bytes())
        files[n] = dict(sha256=L.sha(cand / n), size=(cand / n).stat().st_size)
    put(cand / 'manifest.json', js(dict(files=files)))
    put(cand / NEW, js(dict(verification=dict(saves_checked=1, frames_checked=1), same_length_sites=[], pinned_addresses={}, runtime_parts={})))
    ctx = Ctx(root, root / 'evidence' / 'chart_r22', ptr, cand, payload_files, saves, lambda rt_: True, sources=None,
              note_title='fixture')
    return ctx, rt, rec


def install_fixture(f):
    """The whole transaction in disposable projects, including the r19 21:44 case: a payload file that the recovery runtime
    does not have. The recovery check hashes the same subset before and after -> COMMITTED; --restore -> exact; a recovery
    file changed during the install -> ROLLED_BACK; injected failures -> ROLLED_BACK; the pre-fix check (hash every payload file
    in the recovery runtime) fails on the same project."""
    out = {}
    two = ['NightRemaster.ain', 'Manual/chart/yoru_flowchart_v2.html']
    # 1. commit + restore with a payload file missing from the recovery runtime
    ctx, rt, rec = fake_project(f, 'proj_missing_in_recovery', two, recovery_has={'NightRemaster.ain'})
    tree0 = snapshot_folder(ctx.root)
    try:
        {n: L.sha(rec / n) for n in two}
        old_check = 'passed'
    except (FileNotFoundError, OSError) as ex:
        old_check = 'fails: ' + type(ex).__name__
    assert old_check.startswith('fails'), 'the fixture must reproduce the 21:44 failure of the pre-fix check'
    rep = transact(ctx)
    j = read(ctx.evidence / 'journal.json')
    assert j['status'] == 'COMMITTED' and rep['recovery_lacks'] == ['Manual/chart/yoru_flowchart_v2.html'] and rep['recovery_hashed'] == ['NightRemaster.ain']
    assert all(L.sha(rt / n) == L.sha(ctx.candidate / n) for n in two)
    c = read(ctx.root / 'required_example_a.json')
    assert c['required_files']['NightRemaster.ain'] == L.sha(ctx.candidate / 'NightRemaster.ain') and c['chart_r22_preserved_by'] == str(ctx.evidence)
    assert read(ctx.pointer)['status'] == STATUS and (ctx.root / NEW).exists()
    restore_ctx(ctx, runtime_override=rt)
    restore_ctx(ctx, runtime_override=rt)
    tree1 = snapshot_folder(ctx.root)
    changed = sorted(k for k in set(tree0) | set(tree1) if tree0.get(k) != tree1.get(k) and not k.startswith('evidence/chart_r22/'))
    assert not changed, ('restore did not return the disposable project to its pre-install bytes', changed[:6])
    assert (rt / RUNTIME_SCRATCH / 'request.txt').exists(), 'the transaction touched the KRMenu scratch folder'
    out.update(old_check_on_missing_recovery_file=old_check, committed=True, recovery_hashed=rep['recovery_hashed'], recovery_lacks=rep['recovery_lacks'],
               restored_exact=True, restore_idempotent=True, scratch_folder_ignored=True)
    # 2. the same project shape, one payload file (the real r21 payload), recovery has it
    ctx2, rt2, rec2 = fake_project(f, 'proj_ain_only', FILES, recovery_has=set(FILES))
    rep2 = transact(ctx2)
    assert read(ctx2.evidence / 'journal.json')['status'] == 'COMMITTED' and rep2['recovery_lacks'] == []
    restore_ctx(ctx2, runtime_override=rt2)
    out['single_file_payload_committed_and_restored'] = True
    # 3. injected failures roll back to the exact bytes (files and metadata)
    for where in ('after_files', 'after_contracts', 'recovery_changed'):
        ctx3, rt3, rec3 = fake_project(f, 'proj_fail_' + where, two, recovery_has={'NightRemaster.ain'})
        t0 = snapshot_folder(ctx3.root)
        try:
            transact(ctx3, fail_at=where)
        except (RuntimeError, AssertionError):
            pass
        else:
            raise AssertionError('failure not injected: ' + where)
        assert read(ctx3.evidence / 'journal.json')['status'] == 'ROLLED_BACK', where
        t1 = snapshot_folder(ctx3.root)
        diff = sorted(k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k) and not k.startswith('evidence/chart_r22/')
                      and not (where == 'recovery_changed' and k.startswith('ui_cumulative/recovery/')))
        assert not diff, ('rollback left changes', where, diff[:6])
        out['rolled_back_' + where] = True
    # 4. an interrupted restore resumes (the pointer written, then a crash)
    ctx4, rt4, rec4 = fake_project(f, 'proj_interrupted_restore', FILES, recovery_has=set(FILES))
    transact(ctx4)
    global put
    real_put = put

    def interrupted_put(p, data):
        real_put(p, data)
        if p == ctx4.pointer:
            raise RuntimeError('fixture interrupted after restoring the pointer')
    put = interrupted_put
    try:
        try:
            restore_ctx(ctx4, runtime_override=rt4)
        except RuntimeError:
            pass
        else:
            raise AssertionError('metadata interruption not injected')
    finally:
        put = real_put
    assert read(ctx4.evidence / 'journal.json')['status'] == 'RESTORING'
    restore_ctx(ctx4, runtime_override=rt4)
    assert read(ctx4.evidence / 'journal.json')['status'] == 'RESTORED'
    out['interrupted_restore_resumable'] = True
    return out


# ------------------------------------------------------------------ readiness and install
def readiness():
    """Everything the install needs, read only. Returns (ready, report)."""
    issues = []
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    cur = read(PTR)
    rt = Path(cur['runtime']).resolve()
    if any(L.sha(O / n) != after[n] for n in FILES):
        issues.append('candidate files differ from their manifest')
    base = man['base']
    if L.sha(rt / 'NightRemaster.ain') != base['ain_sha256']:
        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r22 on the new runtime')
    if L.sha(rt / 'NightRemasterPact.afa') != base['pact_sha256'] or L.sha(rt / 'NightRemasterEX.ex') != base['ex_sha256']:
        issues.append('runtime PACT/EX moved since the build')
    if cur['manifest_sha256'] != base['manifest_sha256'] or L.sha(Path(cur['manifest'])) != cur['manifest_sha256']:
        issues.append('current.json / runtime manifest moved since the build')
    if cur.get('status') != base['status']:
        issues.append('current.json status moved since the build')
    if L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') != base['chart_sha256']:
        issues.append('the runtime Manual chart moved since the build')
    if L.sha(rt / 'winmm.dll') != base['winmm_sha256']:
        issues.append('the runtime winmm.dll (mod-menu hook) moved since the build: re-check the hook contract, rebuild if needed')
    vm = read(L.WORK / 'build' / 'vm_verification.json')
    c = vm.get('counts', {})
    if vm['candidate_sha256'] != after['NightRemaster.ain']:
        issues.append('VM verification is for another candidate')
    elif c.get('V14_saves', 0) < 1 or c.get('V14_native_panel_equal') != c.get('V14_saves'):
        issues.append('real-save summary = panel check missing')
    elif not c.get('V27_real_saves') or not c.get('V30_status_page_steps') or not c.get('V31_parts_per_entry'):
        issues.append('r20 VM checks (V27 real saves, V30, V31) missing')
    elif c.get('V34_commands', 0) < 10 or not c.get('V35_flag_saved_and_reloaded') or not c.get('V36_yes_schedules_and_exits') \
            or not c.get('V37_exit_path_equals_game_exit_tail') or not c.get('V38_results_shown') \
            or not c.get('V39_dialogs_outside_home_not_polled') or not c.get('V40_r21_windows_checked'):
        issues.append('r21 VM checks (V34-V40) missing')
    elif not c.get('V41_cells') or not c.get('V42_pages') or c.get('V43_states', 0) < 4 or not c.get('V43_registration_ignored') \
            or not c.get('V44_replays_ctx1') or not c.get('V44_replays_ctx2') or not c.get('V44_card_stage_paths') \
            or not c.get('V45_calendar_equal_r21') or not c.get('V45_calendar_equal_r21_stale_flag') or not c.get('V46_ways_out') \
            or c.get('V47_title_commands', 0) < 5 or not c.get('V48_page_and_request') or not c.get('S8_replay_ops_equal_ExecScene'):
        issues.append('r22 VM checks (V41-V48, S8 replay) missing')
    st = read(L.WORK / 'build' / 'vm_verification_selftest.json')
    if st['candidate_sha256'] != after['NightRemaster.ain'] or len(st['planted_defects']) != DEFECTS or not all(p['caught'] for p in st['planted_defects']):
        issues.append('planted-defect self-test missing or failing (%d defects expected)' % DEFECTS)
    probe = read(L.EVID / 'probe_result.json') if (L.EVID / 'probe_result.json').exists() else {}
    if probe.get('candidate_sha256') != after['NightRemaster.ain'] or not probe_ok(probe):
        issues.append('native calendar tour on the r22 candidate (probe_calendar_tour_r22.py) missing or failing')
    regs = read(L.EVID / 'probe_regs.json') if (L.EVID / 'probe_regs.json').exists() else {}
    if not regs.get('saves') or any(s_.get('candidate_sha256') != after['NightRemaster.ain'] for s_ in regs['saves']):
        issues.append('real save states (probe_calendar_tour_r22.py --regs) missing or from another candidate')
    p22 = read(L.EVID / 'probe_r22.json') if (L.EVID / 'probe_r22.json').exists() else {}
    if any((p22.get(k) or {}).get('candidate_sha256') != after['NightRemaster.ain'] for k in ('title', 'home')) or not probe22_ok(p22):
        issues.append('native chart tours (probe_chart_r22.py --title / --home) missing, failing or for another candidate')
    kinds = read(L.EVID / 'replay_kinds.json') if (L.EVID / 'replay_kinds.json').exists() else {}
    if kinds.get('candidate_sha256') != after['NightRemaster.ain'] or any(e.get('candidate_sha256') != after['NightRemaster.ain'] for e in kinds.get('events', {}).values()) \
            or not kinds.get('events'):
        issues.append('per-kind replay probes (probe_chart_r22.py --kinds) missing or for another candidate')
    native = read(L.WORK / 'build' / 'native_compare.json') if (L.WORK / 'build' / 'native_compare.json').exists() else {}
    nc = native.get('counts', {})
    if native.get('candidate_sha256') != after['NightRemaster.ain'] or not nc.get('N_blocks_identical') or 'panel_same_save' not in native.get('blocks', {}) \
            or not nc.get('N_sandbox_state_equal') or not nc.get('N_r20_blocks_identical') or not nc.get('R22N_pages_equal_vm') \
            or not nc.get('R22N_title_tour') or not nc.get('R22N_title_reset_no') or not nc.get('R22N_home_tour') or not nc.get('R22N_kinds'):
        issues.append('native calendar / chart pages not compared with the VM (verify_chart_r22.py --native)')
    scan = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    if scan.get('status') != 'SCANNED_NO_TARGET_DETECTIONS' or scan.get('files') != after:
        issues.append('Defender scan missing or not for this candidate')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else {}
    if fx.get('status') != 'TRANSACTION_FIXTURE_PASS' or fx.get('payload') != after or not (fx.get('install_with_recovery_lacking_payload_file') or {}).get('committed'):
        issues.append('transaction fixture missing (run --fixture)')
    if not DRAFT.exists():
        issues.append('contract draft missing (run --contract)')
    else:
        d = read(DRAFT)
        if sorted(d['preserves_contracts']) != contracts_now():
            issues.append('required_*.json list changed since the contract draft: rerun --contract')
        if d['required_files'] != after:
            issues.append('contract draft is for another candidate')
    latest = read(R / 'latest_worked_translation.json')
    if latest.get('manifest_sha256') != cur['manifest_sha256'] or latest.get('ain_sha256') != base['ain_sha256'] \
            or L.sha(Path(latest['translation_map'])) != latest.get('translation_map_sha256'):
        issues.append('latest_worked_translation.json does not match the runtime')
    keep = read(R / 'required_build_retention.json')
    if L.sha(Path(keep['recovery_manifest'])) != keep['recovery_manifest_sha256']:
        issues.append('recovery runtime manifest moved')
    try:
        exact_tree(rt, read(Path(cur['manifest']))['files'])
    except AssertionError as ex:
        issues.append('runtime tree differs from its manifest: ' + str(ex)[:200])
    if E.exists():
        issues.append('evidence/chart_r22 already exists: inspect the earlier transaction')
    j21 = read(L.R21_JOURNAL) if L.R21_JOURNAL.exists() else {}
    if j21.get('status') != 'COMMITTED' or j21.get('after', {}).get('NightRemaster.ain') != L.BASE_AIN_SHA or not (R / 'required_modmenu_r21.json').exists():
        issues.append('r21 is not installed as the base expects (evidence/modmenu_r21 journal not COMMITTED or required_modmenu_r21.json missing): rebuild')
    jh = read(L.HOOK_JOURNAL) if L.HOOK_JOURNAL.exists() else {}
    if jh.get('status') != 'COMMITTED' or jh.get('after', {}).get('winmm.dll') != L.BASE_WINMM_SHA:
        issues.append('the mod-menu hook is not installed as the base expects (evidence/mod_menu_20260928 journal)')
    running = active_target(processes(), rt)
    rec = Path(keep['recovery_runtime'])
    report = dict(status=READY if not issues else 'NOT_READY', candidate=after, runtime=str(rt), base=base, issues=issues,
                  game_running=bool(running), contracts_now=len(contracts_now()),
                  recovery_runtime=str(rec), recovery_has=sorted(recovery_hashes(rec, FILES)),
                  install_command=f'python "{Path(__file__)}" --install',
                  restore_command=f'python "{Path(__file__)}" --restore', checked=datetime.datetime.now().astimezone().isoformat())
    return not issues, report


def install():
    ok, report = readiness()
    assert ok, report['issues']
    cur = read(PTR)
    rt = Path(cur['runtime']).resolve()
    if not stopped(rt):
        print('READY_WAITING_FOR_GAME_EXIT')
        return
    rep = transact(real_ctx())
    print(js(rep).decode('utf8'))


if __name__ == '__main__':
    if '--restore' in sys.argv:
        restore()
    elif '--fixture' in sys.argv:
        print(js(fixture()).decode('utf8'))
    elif '--contract' in sys.argv:
        put(DRAFT, js(draft_contract()))
        print('DRAFT', DRAFT, L.sha(DRAFT))
    elif '--verify' in sys.argv:
        ok, rep = readiness()
        put(L.EVID / 'readiness.json', js(rep))
        print(js(rep).decode('utf8'))
    elif '--install' in sys.argv:
        install()
    else:
        print(__doc__)
