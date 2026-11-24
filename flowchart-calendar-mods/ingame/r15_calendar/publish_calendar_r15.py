"""Claude Opus 5.5 (2026-09-27) r15: install / restore of the in-game event calendar candidate (after the 09-24 r14 publisher).

  python publish_calendar_r15.py --contract   write the Codex contract draft r15_calendar/required_calendar_r15.json
  python publish_calendar_r15.py --fixture    transaction fixture on disposable files under r15_calendar/work (no runtime)
  python publish_calendar_r15.py --verify     read-only readiness check (hashes, VM, self-test, probe, scan, fixture, pointer)
  python publish_calendar_r15.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_calendar_r15.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain only (PACT/EX untouched). The install is one journaled transaction, as in r4~r14:
  PREPARED (evidence/calendar_r15: before/candidate copies, metadata snapshots) -> atomic hash-checked replacement of the
  AIN -> runtime manifest + current.json + every required_*.json (calendar_r15_preserved_by) + new required_calendar_r15.json
  + latest_worked_translation.json + progress.md note -> exact tree / saves / recovery runtime re-checked -> COMMITTED.
  Any failure rolls back files and metadata; --restore returns the exact pre-install state from the journal.
Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
"""
from pathlib import Path
import copy, datetime, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r15lib as L

R = L.CODEX
O = HERE / 'candidate'
E = R / 'evidence' / 'calendar_r15'                   # created only by --install
PTR = L.CURRENT
FILES = ['NightRemaster.ain']
NEW = 'required_calendar_r15.json'
DRAFT = HERE / NEW
STATUS = 'CALENDAR_R15_INSTALLED_NATIVE_PASS'
READY = 'CALENDAR_R15_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'
PINNED = {
    'KR_T9HomeCasual': 'on saved stacks during a calendar replay: C_SceneHomebase@Run > CheckGameSysButtons (return after the '
                       'casual call site) > KR_T9HomeCasual (return after LSys3xScript::RunEvent) > RunEvent > event. Keep index, '
                       'address and code bytes in every later build.',
    'KR_T9HomeConfig': 'the settings screen opened from the home base runs inside it (no save is possible there as far as known); '
                       'keep it in place as a precaution.',
    'C_SceneHomebase@CheckGameSysButtons': 'already on saved stacks (save/load screens); now also below KR_T9HomeCasual. Keep in place; '
                                           'its casual and config call sites must keep calling KR_T9HomeCasual / KR_T9HomeConfig.',
    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15.',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15.',
}
INSTRUCTION = (
    'Claude r15 (2026-09-27): in-game event calendar (text menu board, design ingame/설계_v3_글메뉴판.md). Payload AIN only '
    '(PACT/EX untouched); KR_T9* functions appended; no original function relocated; nine same-length CALLFUNC operand swaps: '
    'C_SceneHomebase@RunHome ■選択ダイアログ／実行 -> KR_T9HomeMenuRun (a queued replay returns 3 without showing the menu, '
    'otherwise the original run; the r13 pick code marks context P); C_SceneHomebase@CheckGameSysButtons ■カジュアルモード設定呼び出し -> '
    'KR_T9HomeCasual (replays the queued event with the game\'s own path LSys3xScript::Prepare(name) + RunEvent + ■ＡＤＶ消し(true, 0), '
    'otherwise the original casual call) and ▲コンフィグ実行 -> KR_T9HomeConfig (context C while the settings opened from the home base '
    'run; a reservation made inside is armed only after they return); KR_T8CharMissingMenu ■選択ダイアログ／タイトル設定 -> '
    'KR_T9CharMenuTitle (adds item 1 이벤트 달력), ■選択ダイアログ／実行 -> KR_T9CharMenuRun, KR_T8CharMissingPage -> KR_T9CharMenuPage; '
    'KR_T8CharMissingPage the 2nd ■選択ダイアログ／選択肢追加 -> KR_T9CharPageAdd (adds item 3 달력으로 보기), ■選択ダイアログ／実行 -> '
    'KR_T9CharPageRun, KR_T8CharDatePage -> KR_T9CharDate. Names and addresses of KR_T8* and Codex functions are unchanged. '
    'Saved stacks: a save made during a calendar replay holds C_SceneHomebase@Run > CheckGameSysButtons > KR_T9HomeCasual > '
    'LSys3xScript::RunEvent > event: keep KR_T9HomeCasual (index, address, code) and CheckGameSysButtons in place in every later build, '
    'and KR_T9HomeConfig as a precaution; such a save cannot be loaded by a runtime without KR_T9HomeCasual. State lives only in '
    'SystemService variables YoruKR.T9.* (never saved); no globals, structs or save schema change. Tables are baked from '
    'chart/build_chart_v2.py (155 cards, 760 drawer scenes, 1,164 events): rebuild r15 when the chart data changes. A later rebuild of '
    'RunHome, CheckGameSysButtons, KR_T8CharMissingMenu or KR_T8CharMissingPage must keep these calls. Every earlier contract stays in force.')


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
            assert tmp.resolve().parent == live.resolve() and tmp.is_file()
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
    scan = read(L.WORK / 'scan_report.json')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = ids[name] if name in ids else L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, new=name in ids)
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    ok_probe = probe.get('exit_code') == 0 and probe['log'] and probe['log'][-1] == 'END' and probe['user_save_folder_unchanged'] and not probe['c_drive_alicesoft_changes']
    return dict(
        status='CALENDAR_R15_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], files=man['files'] and {n: man['files'][n]['sha256'] for n in FILES}, required_files={n: man['files'][n]['sha256'] for n in FILES},
        candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False, ex_changed=False,
        added_functions=len(ids), same_length_sites=[{k: s[k] for k in ('function', 'site', 'site_offset', 'original', 'replacement')} for s in man['same_length_sites']],
        relocated_original_functions=[], pinned_addresses=pinned,
        never_on_saved_stack=['C_SceneHomebase@RunHome (unchanged r13 rule: the replay runs after RunHome has returned)', 'every other KR_T9* page and table function'],
        session_variables=man['session_variables'], serialized_schema_changes=0,
        verification=dict(vm=vm['counts'], vm_steps=vm['vm_steps'], planted_defects_caught=sum(p['caught'] for p in st['planted_defects']),
                          planted_defects=len(st['planted_defects']), saves_checked=vm['saves_checked'], frames_checked=vm['frames_checked'],
                          native_probe=dict(passed=bool(ok_probe), seconds=probe.get('seconds'), screenshots=[Path(s).name for s in probe['screenshots']]),
                          defender=scan['status'], transaction_fixture=fx['status'] if fx else 'NOT_RUN'),
        preserves_contracts=prev, preserved_by_key='calendar_r15_preserved_by', instruction=INSTRUCTION, translator_model=L.AUTHOR)


def fixture():
    root = L.WORK / ('fixture_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    f = Path(tempfile.mkdtemp(prefix='복구 검증 ', dir=root.parent if root.parent.exists() else L.WORK))
    b, s, l = f / 'backup', f / 'payload', f / 'live'
    for p in [b, s, l]:
        p.mkdir()
    for n in FILES:
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
        (l / (FILES[0] + '.calendar-copy.tmp')).write_bytes(b'partial interrupted copy')
        pair_restore(b, l, before, after)
        assert all(L.sha(l / n) == before[n] for n in FILES) and not list(l.glob('*.tmp'))
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
                  interrupted_metadata_restoration_resumable=True, no_incoming_residue=not list(l.glob('*.tmp')))
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
    if L.sha(O / 'NightRemaster.ain') != after['NightRemaster.ain']:
        issues.append('candidate AIN differs from its manifest')
    base = man['base']
    if L.sha(rt / 'NightRemaster.ain') != base['ain_sha256']:
        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r15 on the new runtime')
    if L.sha(rt / 'NightRemasterPact.afa') != base['pact_sha256'] or L.sha(rt / 'NightRemasterEX.ex') != base['ex_sha256']:
        issues.append('runtime PACT/EX moved since the build')
    if cur['manifest_sha256'] != base['manifest_sha256'] or L.sha(Path(cur['manifest'])) != cur['manifest_sha256']:
        issues.append('current.json / runtime manifest moved since the build')
    vm = read(L.WORK / 'build' / 'vm_verification.json')
    if vm['candidate_sha256'] != after['NightRemaster.ain']:
        issues.append('VM verification is for another candidate')
    st = read(L.WORK / 'build' / 'vm_verification_selftest.json')
    if st['candidate_sha256'] != after['NightRemaster.ain'] or not all(p['caught'] for p in st['planted_defects']):
        issues.append('planted-defect self-test missing or failing')
    probe = read(L.EVID / 'probe_result.json')
    if probe.get('candidate_sha256') != after['NightRemaster.ain'] or probe.get('exit_code') != 0 or probe['log'][-1:] != ['END'] \
            or probe.get('vm_error') or probe.get('message') or probe.get('events') or not probe['user_save_folder_unchanged']:
        issues.append('native probe missing or failing')
    scan = read(L.WORK / 'scan_report.json')
    if scan['status'] != 'SCANNED_NO_TARGET_DETECTIONS' or scan['files'] != after:
        issues.append('Defender scan missing or not for this candidate')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else {}
    if fx.get('status') != 'TRANSACTION_FIXTURE_PASS' or fx.get('payload') != after:
        issues.append('transaction fixture missing (run --fixture)')
    if not DRAFT.exists():
        issues.append('contract draft missing (run --contract)')
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
        issues.append('evidence/calendar_r15 already exists: inspect the earlier transaction')
    running = active_target(processes(), rt)
    report = dict(status=READY if not issues else 'NOT_READY', candidate=after, runtime=str(rt), base=base, issues=issues,
                  game_running=bool(running), install_command=f'python "{Path(__file__)}" --install',
                  restore_command=f'python "{Path(__file__)}" --restore')
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
    rh = {n: L.sha(rec / n) for n in FILES}
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
        shutil.copy2(rt / n, E / 'before' / n)
        shutil.copy2(O / n, E / 'candidate' / n)
        assert L.sha(E / 'before' / n) == before[n] and L.sha(E / 'candidate' / n) == after[n]
    for f in HERE.iterdir():
        if f.is_file() and f.suffix in ('.py', '.jaf', '.json', '.md', '.ps1'):
            shutil.copy2(f, E / 'source' / f.name)
    for f in (L.EVID / 'probe').glob('*.png'):
        shutil.copy2(f, E / 'source' / 'probe' / f.name)
    for n in ['vm_verification.json', 'vm_verification_selftest.json', 'native_opcode_audit.json']:
        shutil.copy2(L.WORK / 'build' / n, E / 'source' / n)
    for n in ['scan_report.json', 'transaction_verification.json']:
        shutil.copy2(L.WORK / n, E / 'source' / n)
    shutil.copy2(L.EVID / 'probe_result.json', E / 'source' / 'probe_result.json')
    latest = read(R / 'latest_worked_translation.json')
    assert latest['manifest_sha256'] == cur['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    full = read(Path(latest['translation_map']))
    sequence = full['target_text_sequence_sha256']
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full['calendar_r15_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)
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
                   same_length_sites=draft['same_length_sites'], pinned_addresses=draft['pinned_addresses'], translator_model=L.AUTHOR)
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now, calendar_r15_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_r15_overlay=str(E / 'source' / 'manifest.json'))
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = 'User screen check: 플레이 정보 > 캐릭터별 남은 이벤트 > 이벤트 달력; 본거지 패널 캐릭터 > 달력으로 보기; 카드 쪽 이 장면 재생 (검수용 저장에서).'
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
            c['calendar_r15_preserved_by'] = str(E)
            write(R / n, js(c))
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, required_files=after, evidence=str(E),
                     preserves_contracts=sorted(contracts))
        write(R / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, calendar_r15_revision=rev)
        write(PTR, js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation), calendar_r15_evidence=str(E))
        write(R / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} 인게임 이벤트 달력 r15 설치 (Claude Opus 5.5)\n"
                "- 플레이 정보 → 캐릭터별 남은 이벤트 첫 칸 「이벤트 달력」, 본거지 패널 캐릭터 창 「달력으로 보기」. 달 쪽(글자 달력·레인·이달의 서랍) → 레인 쪽 → 카드 쪽(언제·누구·유형·조건·본 것) → 「이 장면 재생」(본거지 첫 메뉴로 돌아간 뒤 캐주얼 버튼 자리에서 게임 자신의 이벤트 경로로 재생).\n"
                "- AIN 한 파일, 원본 함수 이전 0, 같은 길이 호출 교체 9곳, KR_T9HomeCasual 은 재생 중 저장 스택에 오른다(주소 유지).\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {E}; 되돌리기 publish_calendar_r15.py --restore.\n")
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
