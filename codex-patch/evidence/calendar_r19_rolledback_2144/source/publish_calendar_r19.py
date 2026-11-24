"""Claude Opus 5.5 (2026-09-27) r19: install / restore of the calendar r19 candidate (copy of publish_calendar_r18.py).
r19 = the r18 install + names instead of the internal event numbers on every calendar page + the affinity conditions
(rule 11); the regenerated PC chart v2 (same names) goes to the help-menu chart path as the chart-menu contract asks.

  python publish_calendar_r19.py --contract   write the Codex contract draft r19_calendar/required_calendar_r19.json
  python publish_calendar_r19.py --fixture    transaction fixture on disposable files under r19_calendar/work (no runtime)
  python publish_calendar_r19.py --verify     read-only readiness check (hashes, VM, self-test, probe, native compare, scan,
                                              fixture, contract list, pointer)
  python publish_calendar_r19.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_calendar_r19.py --restore    undo an install exactly (journal-driven, resumable, idempotent): the runtime
                                              goes back to the pre-install files (= the r18 install)

Payload: NightRemaster.ain + Manual/chart/yoru_flowchart_v2.html (PACT/EX untouched). One journaled transaction, as in r4~r18:
  PREPARED (evidence/calendar_r19: before/candidate copies, metadata snapshots) -> atomic hash-checked replacement of the two
  files -> runtime manifest + current.json + every required_*.json present at install time (calendar_r19_preserved_by; their
  required_files rows for the two files follow) + new required_calendar_r19.json + latest_worked_translation.json + progress.md
  note -> exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure rolls back files and metadata; --restore
  returns the exact pre-install state.
Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
"""
from pathlib import Path
import copy, datetime, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r19lib as L

R = L.CODEX
O = HERE / 'candidate'
E = R / 'evidence' / 'calendar_r19'                   # created only by --install
PTR = L.CURRENT
CHART = 'Manual/chart/yoru_flowchart_v2.html'
FILES = ['NightRemaster.ain', CHART]
NEW = 'required_calendar_r19.json'
DRAFT = HERE / NEW
STATUS = 'CALENDAR_R19_INSTALLED_NATIVE_PASS'
READY = 'CALENDAR_R19_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'
DEFECTS = 31
PINNED = {
    'KR_T9HomeCasual': 'on saved stacks during a calendar replay: C_SceneHomebase@Run > CheckGameSysButtons (return after the '
                       'casual call site) > KR_T9HomeCasual (return after the RunEvent call site, offset 198) > KR_T18RunSandboxed > '
                       'RunEvent > event. Keep index, address and code bytes in every later build. r18 changed exactly one thing in '
                       'it: the 4-byte operand of that call (LSys3xScript::RunEvent -> KR_T18RunSandboxed, same signature, same '
                       'length); every other byte equals the r15 candidate. r19: byte-identical to r18.',
    'KR_T9HomeConfig': 'the settings screen opened from the home base runs inside it (no save is possible there as far as known); '
                       'keep it in place as a precaution (r15 contract; r18 and r19 byte-identical).',
    'C_SceneHomebase@CheckGameSysButtons': 'already on saved stacks (save/load screens) and below KR_T9HomeCasual. Keep in place; '
                                           'its casual and config call sites must keep calling KR_T9HomeCasual / KR_T9HomeConfig.',
    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15, r17, r18 and r19 (called from KR_T18RunSandboxed).',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15, r17, r18 and r19.',
    'KR_T18RunSandboxed': 'r18, pinned (r19 byte-identical): on saved stacks when the player saves during a sandboxed replay '
                          '(KR_T9HomeCasual > KR_T18RunSandboxed (return after its RunEvent call) > RunEvent) and inside the '
                          'sandbox\'s own temporary resume image (return after its gamesave::detail::セーブ実行 call, offset 174). '
                          'Keep index, address and code bytes in every later build.',
}
FORWARDED = {           # r19's five one-call forwarders (r18's eight KR_T9 -> KR_T18 forwarders stay as they are)
    'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
    'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage',
}
R18_FORWARDED = ['KR_T9MonthPage', 'KR_T9MemPage', 'KR_T9LaneTitle', 'KR_T9CardRow', 'KR_T9ChipRow', 'KR_T9MonthChips',
                 'KR_T9CardPage', 'KR_T9EventPage']
NO_RESTORE = ('Codex must never run publish_calendar_*.py --restore or otherwise remove the calendar overlay (KR_T9*/KR_T17*/KR_T18*/KR_T19* '
              'functions, the nine r15 same-length operands, the RunEvent operand swap in KR_T9HomeCasual). The calendar is a permanent '
              'user-requested feature: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry '
              'the calendar functions forward; restore is reserved for the user\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_calendar_*.py --restore 를 실행하거나 달력 오버레이(KR_T9*/KR_T17*/KR_T18*/KR_T19* 함수, r15 의 같은 길이 '
                 '피연산자 9곳, KR_T9HomeCasual 의 RunEvent 피연산자 교체)를 지우지 않는다. 달력은 사용자가 요청한 영구 기능이다: 깨끗한 '
                 '기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 달력 함수를 이어 싣는다. 되돌리기는 사용자가 명시적으로 '
                 '요청할 때만 한다.')
INSTRUCTION = (
    'Claude r19 (2026-09-27): in-game event calendar = the r18 install + human-readable names instead of the internal event '
    'numbers (E#####) on every calendar page + affinity conditions on the 「언제」 lines (design ingame/설계_v3_글메뉴판.md, 「r19 요구」 '
    'rules 1-11). ' + NO_RESTORE + ' Payload: NightRemaster.ain and Manual/chart/yoru_flowchart_v2.html (the PC chart v2 rebuilt by '
    'chart/build_chart_v2.py with the same names in a side-panel field; required_chart_menu_20260927.json asks exactly this when the chart '
    'is rebuilt); PACT/EX untouched. KR_T19* functions appended (tables: card names / tails / lane-row conditions, scene names / list '
    'lines, the 「언제」 lines that differ from r15\'s table, the drawer display order, list columns); no original function relocated. '
    'Five existing functions keep index and arguments but their body is a one-call forwarder at a new address: KR_T18CardRow -> '
    'KR_T19CardRow (name tails on the lane rows whose card names collide, e.g. 「10/22 밤 ● 이즈미와 1」), KR_T18CardTitle -> '
    'KR_T19CardTitle and KR_T18EventTitle -> KR_T19EventTitle (first line 「<언제> · <유형> · <이름>」, 「언제」 with names and affinity), '
    'KR_T9StagePage -> KR_T19StagePage (「2. 갈래 1 쿄카와 ○」) and KR_T9ChipPage -> KR_T19ChipPage (「마코토와 3번째 ●」). These page '
    'functions are never on a saved stack. r18\'s eight KR_T9 -> KR_T18 forwarders stay. No same-length operand changes: r15\'s nine and '
    'r18\'s KR_T9HomeCasual RunEvent -> KR_T18RunSandboxed operand stay applied. Pinned (index, address and every code byte identical): '
    'KR_T9HomeCasual, KR_T9HomeConfig, C_SceneHomebase@CheckGameSysButtons, C_SceneHomebase@Run, LSys3xScript::RunEvent, '
    'KR_T18RunSandboxed. The names are computed by chart/build_chart_v2.py (event_names) from graph/schedule.json / labels.json / '
    'groups.json; graph/schedule.json triggers gained `feeling_gate` (scratch/extract.py: ConditionalCall nFeeling, '
    'GetAfterTrainingEvent GetFeeling() >= n, L_EventCall::E30152 GetFeeling() < 50 branches, L_EventCall::E10501 highest affinity '
    'when no route is set). Rebuild the calendar when the chart data changes. State: SystemService variables YoruKR.T9.* / YoruKR.T18.* '
    'only; no globals, structs or save schema change. Every earlier contract stays in force.')


def js(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def put(path, data):
    """publish_remaster_multiplier_20260915.put: atomic write through a temporary file in the same folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.calendar-', suffix='.tmp', delete=False) as f:
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
    tmp = dest.with_name(dest.name + '.calendar-copy.tmp')
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
    assert rt == rt.resolve(), ('redirected runtime', rt)
    expected = {r['path'] for r in rows}
    assert {p.relative_to(rt).as_posix() for p in rt.rglob('*') if p.is_file()} == expected
    for r in rows:
        p = (rt / r['path']).resolve()
        assert p.is_relative_to(rt)
        assert p.stat().st_size == r['size'] and L.sha(p) == r['sha256'], p


def snapshot_saves():
    assert L.SAVES.is_dir(), L.SAVES
    return {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}


def pair_apply(src, backup, live, before, after, fail_after=0):
    for n in FILES:
        assert L.sha(src / n) == after[n], ('payload', n)
        assert L.sha(backup / n) == before[n], ('backup', n)
        assert L.sha(live / n) == before[n], ('baseline', n)
    attempted = []
    try:
        for n in FILES:
            attempted.append(n)
            replace_checked(src / n, live / n, after[n])
            if len(attempted) == fail_after:
                raise RuntimeError('fixture injected replacement failure')
    except BaseException:
        for n in reversed(attempted):
            replace_checked(backup / n, live / n, before[n])
        raise


def pair_restore(backup, live, before, after):
    for n in FILES:
        assert L.sha(backup / n) == before[n], ('tampered backup', n)
        assert L.sha(live / n) in [before[n], after[n]], ('unknown live state', n)
    for n in FILES:
        tmp = live / (n + '.calendar-copy.tmp')
        if tmp.exists():
            assert tmp.resolve().parent == (live / n).resolve().parent and tmp.resolve().is_relative_to(live.resolve()) and tmp.is_file()
            quarantine = backup.parent / 'interrupted_incoming'
            quarantine.mkdir(exist_ok=True)
            dest = quarantine / (tmp.name + '.' + L.sha(tmp)[:12] + '.' + str(datetime.datetime.now().timestamp()))
            tmp.replace(dest)
    for n in FILES:
        if L.sha(live / n) != before[n]:
            replace_checked(backup / n, live / n, before[n])


def contracts_now():
    return sorted(p.name for p in R.glob('required_*.json') if p.name != NEW)


def draft_contract():
    man = read(O / 'manifest.json')
    vm = read(L.WORK / 'build' / 'vm_verification.json')
    st = read(L.WORK / 'build' / 'vm_verification_selftest.json')
    probe = read(L.EVID / 'probe_result.json')
    native = read(L.WORK / 'build' / 'native_compare.json')
    scan = read(L.WORK / 'scan_report.json')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why,
                            code=man['pinned_functions'][name])
    forwarded = {}
    for name, target in FORWARDED.items():
        fid = L.fid_of(nm, name)
        forwarded[name] = dict(index=fid, address=nm['functions'][fid]['address'], base_address=man['forwarded_functions'][name]['base_address'],
                               body='one CALLFUNC ' + target, target_index=ids[target])
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    ok_probe = probe_ok(probe)
    return dict(
        status='CALENDAR_R19_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files={n: man['files'][n]['sha256'] for n in FILES},
        candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False, ex_changed=False,
        no_restore_rule=NO_RESTORE, based_on_r18_install=True,
        added_functions=len(ids), added_function_names=sorted(ids), forwarded_functions=forwarded, r18_forwarders_kept=R18_FORWARDED,
        same_length_sites=[], same_length_sites_kept=man['same_length_sites_kept'],
        names=dict(man['names'], computed_by='chart/build_chart_v2.py event_names (the PC chart v2 shows the same names)',
                   chart_file=CHART, chart_sha256=man['files'][CHART]['sha256'], chart_builder_sha256=man['chart']['builder_sha256'],
                   schedule_sha256=man['chart']['schedule_sha256']),
        sandbox_replay_unchanged_since_r18=dict(verified_natively=dict(probe['sandbox'], files_at_end=None) if probe.get('sandbox') else None,
                                                session_variables_restored_by_resumeload=(probe.get('sandbox') or {}).get('session_variables_restored_by_resumeload')),
        relocated_original_functions=[], pinned_addresses=pinned,
        never_on_saved_stack=['C_SceneHomebase@RunHome (r13/r15 rule: the replay runs after RunHome has returned)',
                              'every KR_T9 / KR_T18 / KR_T19 page and table function, incl. the r18 and r19 forwarders (S4: no saved frame in them)'],
        panel_outside='unchanged since r18 (KR_T18Out, derived from KR_PlayerEventCount at the r18 build; r19 adds no count)',
        affinity=dict(rule='「<인물> 친밀도 v 이상 / 미만」 (C_Ability@GetFeeling() units = what the status window affinity page draws, 60 a heart); '
                           'lane rows full or 「쿄카 30+」', events=man['names'].get('affinity_events'),
                      source='graph/schedule.json triggers[].feeling_gate (scratch/extract.py, r19)'),
        session_variables=man['session_variables'], serialized_schema_changes=0,
        verification=dict(vm=vm['counts'], vm_steps=vm['vm_steps'], planted_defects_caught=sum(p['caught'] for p in st['planted_defects']),
                          planted_defects=len(st['planted_defects']), saves_checked=vm['saves_checked'], frames_checked=vm['frames_checked'],
                          native_probe=dict(passed=bool(ok_probe), seconds=probe.get('seconds'), save=probe.get('save'),
                                            screenshots=[Path(s).name for s in probe['screenshots']],
                                            home_before_after_differing_pixels=probe.get('home_before_after', {}).get('differing_pixels'),
                                            month_before_after_summary_differing_pixels=probe.get('month_before_after_summary', {}).get('differing_pixels')),
                          native_blocks_equal_vm=native['counts']['N_blocks_identical'], native_panel=native['blocks'].get('panel_same_save'),
                          native_sandbox=native['blocks'].get('sandbox'),
                          real_saves_summary_equals_panel=vm['counts'].get('V14_native_panel_equal'),
                          panel=vm['panel'] and {k: v for k, v in vm['panel'].items() if k != 'states'},
                          chart_dom=read(L.EVID / 'chart_dom_diff.json')['dom'] if (L.EVID / 'chart_dom_diff.json').exists() else None,
                          defender=scan['status'], transaction_fixture=fx['status'] if fx else 'NOT_RUN'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_r19_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)


def probe_ok(probe):
    """r17's conditions + the sandbox: home before = home after the replay (pixels and every logged state key outside the allow
    list), temp file present during the replay and gone after, the mid-replay load keeps the replay (no temp file). The user's
    folder may change only while the user's own game runs (the probe logs its own save folder inside run/)."""
    sb = probe.get('sandbox') or {}
    user_ok = probe['user_save_folder_unchanged'] or bool((probe.get('user_game_running') or {}).get('before') or (probe.get('user_game_running') or {}).get('after'))
    return bool(probe.get('exit_code') == 0 and probe['log'] and probe['log'][-1] == 'END' and user_ok and probe.get('probe_save_folder_inside_run')
                and not probe.get('vm_error') and not probe.get('message') and not probe.get('events')
                and probe.get('home_before_after', {}).get('differing_pixels') == 0
                and probe.get('month_before_after_summary', {}).get('differing_pixels') == 0
                and set(sb.get('states', [])) >= {'HOME', 'PREPLAY', 'MIDREPLAY', 'AFTER', 'MIDLOAD'}
                and sb.get('home_vs_after') == {} and sb.get('home_vs_preplay') == {}
                and sb.get('after_temp_files') == ['0', '0'] and sb.get('midreplay_temp_files') == ['1', '1']
                and sb.get('midload_temp_files') == ['0', '0'] and not sb.get('temp_file_on_disk_at_end'))


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
            (l / (n + '.calendar-copy.tmp')).write_bytes(b'partial interrupted copy')
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
    metadata_fixture(f, s, b, l, before, after)
    result = dict(status='TRANSACTION_FIXTURE_PASS', fixture=str(f), payload=after, install_restore=True, idempotent_restore=True,
                  injected_failure_rollback=True, known_mixed_and_interruption_restore=True, partial_incoming_copy_recovered=True,
                  tampered_payload_baseline_backup_rejected=True, exact_process_path_filter=True, unicode_spaces_path=True,
                  interrupted_metadata_restoration_resumable=True, no_incoming_residue=not list(l.rglob('*.tmp')), files=FILES)
    put(L.WORK / 'transaction_verification.json', js(result))
    return result


def metadata_fixture(f, s, b, l, before, after):
    """The real restore() against a disposable project/journal, interrupted after restoring the pointer, then resumed."""
    global R, E, PTR, stopped, put
    saved = (R, E, PTR, stopped, put)
    real_put = put
    try:
        R = f
        E = f / 'restore_evidence'
        PTR = f / 'ui_cumulative' / 'current.json'
        stopped = lambda rt: True
        (E / 'before').mkdir(parents=True)
        PTR.parent.mkdir()
        note = f / 'progress.md'
        meta = []
        newhash = {}
        for p in [PTR, note]:
            old = b'old metadata ' + p.name.encode()
            new = b'new metadata ' + p.name.encode()
            (E / 'before' / p.name).write_bytes(old)
            p.write_bytes(new)
            meta.append(dict(path=str(p), name=p.name, existed=True, sha256=L.sha(E / 'before' / p.name)))
            newhash[str(p)] = L.sha(p)
        for n in FILES:
            (E / 'before' / n).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(b / n, E / 'before' / n)
        pair_apply(s, b, l, before, after)
        real_put(E / 'journal.json', js(dict(status='COMMITTED', runtime=str(l), before=before, after=after, metadata=meta,
                                             metadata_after=newhash, committed_pointer_sha256=L.sha(PTR))))

        def interrupted_put(p, data):
            real_put(p, data)
            if p == PTR:
                raise RuntimeError('fixture interrupted after restoring the pointer')
        put = interrupted_put
        try:
            restore(runtime_override=l)
        except RuntimeError:
            pass
        else:
            raise AssertionError('metadata interruption not injected')
        put = real_put
        assert read(E / 'journal.json')['status'] == 'RESTORING'
        restore(runtime_override=l)
        restore(runtime_override=l)
        assert read(E / 'journal.json')['status'] == 'RESTORED'
        assert all(L.sha(Path(x['path'])) == x['sha256'] for x in meta)
        assert all(L.sha(l / n) == before[n] for n in FILES)
    finally:
        R, E, PTR, stopped, put = saved


def restore(runtime_override=None):
    j = read(E / 'journal.json')
    rt = Path(j['runtime']).resolve()
    if runtime_override is None:
        assert rt == L.runtime()[1].resolve()
    else:
        assert rt == Path(runtime_override).resolve()
    assert stopped(rt), 'close the game first'
    if j['status'] == 'RESTORED':
        assert all(L.sha(rt / n) == j['before'][n] for n in FILES)
        print('ALREADY_RESTORED')
        return
    assert j['status'] in ['COMMITTED', 'PREPARED', 'ROLLBACK_INCOMPLETE', 'RESTORING']
    for row in j['metadata']:
        path = Path(row['path'])
        assert path.resolve().is_relative_to(R.resolve())
        if row['existed']:
            assert L.sha(E / 'before' / row['name']) == row['sha256']
        current = L.sha(path) if path.exists() else None
        allowed = {row['sha256'], j.get('metadata_after', {}).get(str(path), row['sha256'])}
        assert current in allowed, ('A newer or unknown metadata state exists — inspect before restoring', str(path))
    j['status'] = 'RESTORING'
    put(E / 'journal.json', js(j))
    pair_restore(E / 'before', rt, j['before'], j['after'])
    for row in j['metadata']:
        path = Path(row['path'])
        if row['existed']:
            put(path, (E / 'before' / row['name']).read_bytes())
        elif path.exists():
            path.unlink()
    assert all(L.sha(rt / n) == j['before'][n] for n in FILES)
    j['status'] = 'RESTORED'
    put(E / 'journal.json', js(j))
    print('RESTORED EXACT PRE-INSTALL STATE')


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
        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r19 on the new runtime')
    if L.sha(rt / 'NightRemasterPact.afa') != base['pact_sha256'] or L.sha(rt / 'NightRemasterEX.ex') != base['ex_sha256']:
        issues.append('runtime PACT/EX moved since the build')
    if cur['manifest_sha256'] != base['manifest_sha256'] or L.sha(Path(cur['manifest'])) != cur['manifest_sha256']:
        issues.append('current.json / runtime manifest moved since the build')
    if cur.get('status') != base['status']:
        issues.append('current.json status moved since the build')
    if L.sha(rt / CHART) != man['chart_runtime_before_sha256']:
        issues.append('the runtime help-menu chart moved since the build (another chart installed?)')
    vm = read(L.WORK / 'build' / 'vm_verification.json')
    if vm['candidate_sha256'] != after['NightRemaster.ain']:
        issues.append('VM verification is for another candidate')
    elif vm['counts'].get('V14_saves', 0) < 1 or vm['counts'].get('V14_native_panel_equal') != vm['counts'].get('V14_saves'):
        issues.append('real-save summary = panel check missing')
    st = read(L.WORK / 'build' / 'vm_verification_selftest.json')
    if st['candidate_sha256'] != after['NightRemaster.ain'] or len(st['planted_defects']) != DEFECTS or not all(p['caught'] for p in st['planted_defects']):
        issues.append('planted-defect self-test missing or failing (%d defects expected)' % DEFECTS)
    probe = read(L.EVID / 'probe_result.json')
    if probe.get('candidate_sha256') != after['NightRemaster.ain'] or not probe_ok(probe):
        issues.append('native probe missing or failing')
    native = read(L.WORK / 'build' / 'native_compare.json') if (L.WORK / 'build' / 'native_compare.json').exists() else {}
    if native.get('candidate_sha256') != after['NightRemaster.ain'] or not native.get('counts', {}).get('N_blocks_identical') \
            or 'panel_same_save' not in native.get('blocks', {}) or not native.get('counts', {}).get('N_sandbox_state_equal'):
        issues.append('native titles / rows / lists / panel / sandbox not compared with the VM (verify_calendar_r19.py --native)')
    dom = read(L.EVID / 'chart_dom_diff.json') if (L.EVID / 'chart_dom_diff.json').exists() else {}
    if not dom.get('dom_identical_except_name_field_and_rule11') or L.sha(Path(dom.get('new', ''))) != after[CHART] if dom.get('new') else True:
        issues.append('PC chart DOM identity (work/chart_dom_diff_r19.py) missing, failing or for another chart')
    regs = read(L.EVID / 'probe_regs.json') if (L.EVID / 'probe_regs.json').exists() else {}
    if not regs.get('saves') or any(s.get('candidate_sha256') != after['NightRemaster.ain'] for s in regs['saves']):
        issues.append('real save states (probe --regs) missing or from another candidate')
    scan = read(L.WORK / 'scan_report.json')
    if scan['status'] != 'SCANNED_NO_TARGET_DETECTIONS' or scan['files'] != after:
        issues.append('Defender scan missing or not for this candidate')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else {}
    if fx.get('status') != 'TRANSACTION_FIXTURE_PASS' or fx.get('payload') != after:
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
        issues.append('evidence/calendar_r19 already exists: inspect the earlier transaction')
    j18 = read(R / 'evidence' / 'calendar_r18' / 'journal.json') if (R / 'evidence' / 'calendar_r18' / 'journal.json').exists() else {}
    if j18.get('status') != 'COMMITTED' or not (R / 'required_calendar_r18.json').exists():
        issues.append('r18 is not installed as the base expects (evidence/calendar_r18 journal not COMMITTED or required_calendar_r18.json missing): rebuild')
    running = active_target(processes(), rt)
    report = dict(status=READY if not issues else 'NOT_READY', candidate=after, runtime=str(rt), base=base, issues=issues,
                  game_running=bool(running), contracts_now=len(contracts_now()),
                  install_command=f'python "{Path(__file__)}" --install',
                  restore_command=f'python "{Path(__file__)}" --restore', checked=datetime.datetime.now().astimezone().isoformat())
    return not issues, report


def install():
    ok, report = readiness()
    assert ok, report['issues']
    cur = read(PTR)
    rt = Path(cur['runtime']).resolve()
    mp = Path(cur['manifest'])
    if not stopped(rt):
        print('READY_WAITING_FOR_GAME_EXIT')
        return
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    before = {n: L.sha(rt / n) for n in FILES}
    manifest = read(mp)
    exact_tree(rt, manifest['files'])
    saves = snapshot_saves()
    keep = read(R / 'required_build_retention.json')
    rec = Path(keep['recovery_runtime'])
    rm = Path(keep['recovery_manifest'])
    assert L.sha(rm) == keep['recovery_manifest_sha256']
    rh = {n: L.sha(rec / n) for n in FILES if (rec / n).exists()}
    contracts = contracts_now()
    paths = [mp, PTR, R / 'progress.md', R / 'latest_worked_translation.json'] + [R / n for n in contracts + [NEW]]
    assert len(paths) == len(set(x.name for x in paths))
    snapshots = {x: x.read_bytes() if x.exists() else None for x in paths}
    assert snapshots[R / NEW] is None
    E.mkdir(parents=True)
    assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for folder in ['before', 'candidate', 'source', 'source/probe']:
        (E / folder).mkdir()
    metadata = []
    for path, data in snapshots.items():
        if data is not None:
            put(E / 'before' / path.name, data)
        metadata.append(dict(path=str(path), name=path.name, existed=data is not None, sha256=L.sha(path) if data is not None else None))
    for n in FILES:
        for d in ('before', 'candidate'):
            (E / d / n).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rt / n, E / 'before' / n)
        shutil.copy2(O / n, E / 'candidate' / n)
        assert L.sha(E / 'before' / n) == before[n] and L.sha(E / 'candidate' / n) == after[n]
    for f in HERE.iterdir():
        if f.is_file() and f.suffix in ('.py', '.jaf', '.json', '.md', '.ps1'):
            shutil.copy2(f, E / 'source' / f.name)
    for f in (L.EVID / 'probe').glob('*.png'):
        shutil.copy2(f, E / 'source' / 'probe' / f.name)
    for n in ['vm_verification.json', 'vm_verification_selftest.json', 'native_opcode_audit.json', 'native_compare.json']:
        shutil.copy2(L.WORK / 'build' / n, E / 'source' / n)
    for n in ['scan_report.json', 'transaction_verification.json']:
        shutil.copy2(L.WORK / n, E / 'source' / n)
    for n in ['probe_result.json', 'probe_regs.json', 'page_stats.json']:
        shutil.copy2(L.EVID / n, E / 'source' / n)
    latest = read(R / 'latest_worked_translation.json')
    assert latest['manifest_sha256'] == cur['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    full = read(Path(latest['translation_map']))
    sequence = full['target_text_sequence_sha256']
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full['calendar_r19_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)
    translation = E / 'source' / 'installed_translation_map.json'
    put(translation, js(full))
    assert read(translation)['target_text_sequence_sha256'] == sequence
    put(E / 'save_hashes_before.json', js(saves))
    j = dict(status='PREPARED', runtime=str(rt), before=before, after=after, metadata=metadata)
    put(E / 'journal.json', js(j))
    draft = read(DRAFT)

    def write(path, data):
        assert path in snapshots
        j.setdefault('metadata_after', {})[str(path)] = hashlib.sha256(data).hexdigest()
        put(E / 'journal.json', js(j))
        put(path, data)
    attempted = False
    try:
        assert stopped(rt) and read(PTR) == cur and L.sha(mp) == cur['manifest_sha256'] and saves == snapshot_saves()
        attempted = True
        pair_apply(E / 'candidate', E / 'before', rt, before, after)
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, author=L.AUTHOR, files=after, source_files=before, evidence=str(E), native_probe_verified=True,
                   screen_verified=False, persistent_return_offsets_exact=True, MSG1_exact=True, save_schema_changes=0, save_writes=0,
                   existing_saves_checked=draft['verification']['saves_checked'], frames_checked=draft['verification']['frames_checked'],
                   forwarded_functions=draft['forwarded_functions'], pinned_addresses=draft['pinned_addresses'], translator_model=L.AUTHOR)
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now, calendar_r19_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_r19_overlay=str(E / 'source' / 'manifest.json'))
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = 'User screen check: 이벤트 달력 r19 — 카드 쪽 · 장면 쪽 첫 줄과 단계 목록 · 서랍 장면 목록에 E번호 대신 이름(「특훈 뒤 대화 3번째」「마코토와 3번째」「2. 갈래 1 쿄카와」), 친밀도 조건(「쿄카 친밀도 30 이상」), 도움말 메뉴 차트의 「게임 안 이름」.'
        write(mp, js(nm))
        mh = L.sha(mp)
        for n in contracts:
            c = read(R / n)
            for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if k in c:
                    c[k] = mh
            for file, h in after.items():
                if file in c.get('required_files', {}):
                    c['required_files'][file] = h
            c['calendar_r19_preserved_by'] = str(E)
            write(R / n, js(c))
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, required_files=after, evidence=str(E),
                     preserves_contracts=sorted(contracts))
        write(R / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, calendar_r19_revision=rev)
        write(PTR, js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation), calendar_r19_evidence=str(E))
        write(R / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} 인게임 이벤트 달력 r19 설치 (Claude Opus 5.5; r18 설치본 위)\n"
                "- 달력의 모든 쪽에서 E번호 대신 이름(카드 · 장면 쪽 첫 줄 「<언제> · <유형> · <이름>」, 단계 목록 「2. 갈래 1 쿄카와」, 서랍 장면 목록 「마코토와 3번째」, 겹치는 레인 줄 꼬리 「이즈미와 1」) + 「언제」 줄의 친밀도 조건(「쿄카 친밀도 30 이상」). 이름은 chart/build_chart_v2.py 가 계산하고 PC 차트 v2(도움말 메뉴 차트)에도 같은 이름을 넣었다.\n"
                "- AIN 과 Manual/chart/yoru_flowchart_v2.html 두 파일, 원본 함수 이전 0, 기존 함수 5개는 번호 그대로 한 줄 전달(KR_T18CardRow · KR_T18CardTitle · KR_T18EventTitle · KR_T9StagePage · KR_T9ChipPage), 같은 길이 교체 없음(r15 의 9곳 · r18 의 1곳 그대로), 주소 유지 함수 6개 바이트 동일.\n"
                "- " + NO_RESTORE_KO + "\n"
                f"- AIN {after['NightRemaster.ain']}; chart {after[CHART]}; manifest {mh}; evidence {E}; 되돌리기(사용자 요청 때만) publish_calendar_r19.py --restore.\n")
        write(R / 'progress.md', (snapshots[R / 'progress.md'] or b'') + note.encode('utf8'))
        exact_tree(rt, nm['files'])
        assert saves == snapshot_saves()
        assert L.sha(rm) == keep['recovery_manifest_sha256'] and rh == {x: L.sha(rec / x) for x in FILES}
        j.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=L.sha(PTR))
        put(E / 'journal.json', js(j))
    except BaseException as error:
        errors = []
        if attempted:
            try:
                pair_restore(E / 'before', rt, before, after)
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
        put(E / 'journal.json', js(j))
        raise
    report = dict(status=STATUS, files=after, manifest_sha256=mh, runtime=str(rt), unchanged_save_files=len(saves), recovery_unchanged=True,
                  evidence=str(E), author=L.AUTHOR)
    put(E / 'publish_report.json', js(report))
    print(js(report).decode('utf8'))


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
