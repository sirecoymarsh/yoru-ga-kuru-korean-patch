"""Claude Opus 5.5 (2026-09-27) r17: install / restore of the calendar r17 candidate (copy of publish_calendar_r16.py).
r17 replaces the r16 candidate, which was never installed: installing r17 goes straight onto the base (r15 + Codex's later work).

  python publish_calendar_r17.py --contract   write the Codex contract draft r17_calendar/required_calendar_r17.json
  python publish_calendar_r17.py --fixture    transaction fixture on disposable files under r17_calendar/work (no runtime)
  python publish_calendar_r17.py --verify     read-only readiness check (hashes, VM, self-test, probe, native compare, scan,
                                              fixture, contract list, pointer)
  python publish_calendar_r17.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_calendar_r17.py --restore    undo an install exactly (journal-driven, resumable, idempotent): the runtime
                                              goes back to the pre-install AIN (= the base, r15 and Codex's later work inside)

Payload: NightRemaster.ain only (PACT/EX untouched). The install is one journaled transaction, as in r4~r16:
  PREPARED (evidence/calendar_r17: before/candidate copies, metadata snapshots) -> atomic hash-checked replacement of the
  AIN -> runtime manifest + current.json + every required_*.json present at install time (calendar_r17_preserved_by) +
  new required_calendar_r17.json + latest_worked_translation.json + progress.md note -> exact tree / saves / recovery
  runtime re-checked -> COMMITTED. Any failure rolls back files and metadata; --restore returns the exact pre-install state.
Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
"""
from pathlib import Path
import copy, datetime, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r17lib as L

R = L.CODEX
O = HERE / 'candidate'
E = R / 'evidence' / 'calendar_r17'                   # created only by --install
PTR = L.CURRENT
FILES = ['NightRemaster.ain']
NEW = 'required_calendar_r17.json'
DRAFT = HERE / NEW
STATUS = 'CALENDAR_R17_INSTALLED_NATIVE_PASS'
READY = 'CALENDAR_R17_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'
DEFECTS = 22
PINNED = {
    'KR_T9HomeCasual': 'on saved stacks during a calendar replay: C_SceneHomebase@Run > CheckGameSysButtons (return after the '
                       'casual call site) > KR_T9HomeCasual (return after LSys3xScript::RunEvent) > RunEvent > event. Keep index, '
                       'address and code bytes in every later build (r15 contract; r17 leaves it byte-identical).',
    'KR_T9HomeConfig': 'the settings screen opened from the home base runs inside it (no save is possible there as far as known); '
                       'keep it in place as a precaution (r15 contract; r17 byte-identical).',
    'C_SceneHomebase@CheckGameSysButtons': 'already on saved stacks (save/load screens) and below KR_T9HomeCasual. Keep in place; '
                                           'its casual and config call sites must keep calling KR_T9HomeCasual / KR_T9HomeConfig.',
    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract); unchanged by r15 and r17.',
    'C_SceneHomebase@Run': 'already on saved stacks; unchanged by r15 and r17.',
}
FORWARDED = {
    'KR_T9MonthPage': 'KR_T17MonthPage', 'KR_T9MemPage': 'KR_T17MemPage',
    'KR_T9LaneTitle': 'KR_T17LaneTitle', 'KR_T9CardRow': 'KR_T17CardRow',
    'KR_T9ChipRow': 'KR_T17ChipRow', 'KR_T9MonthChips': 'KR_T17MonthChips',
}
INSTRUCTION = (
    'Claude r17 (2026-09-27): calendar achievement bars and summary page on top of r15 (design ingame/설계_v3_글메뉴판.md, r16 요구 '
    '+ r17 요구). r17 replaces the r16 candidate, which was never installed; every new function is named KR_T17* (no KR_T16* exists '
    'in the runtime). Payload AIN only (PACT/EX untouched). KR_T17* functions appended; no original function relocated; no new '
    'same-length swap. Six r15 screen functions keep their index and arguments but their body is now a one-call forwarder at a new '
    'address: KR_T9MonthPage -> KR_T17MonthPage (title: 10-cell bar k/n (p%), legend 「▲놓침 ●앞으로 ○다 봄 금색=오늘」, day cells '
    '놓침 ▲ / 앞으로 ● / 다 봄 ○ (no ★); menu rows name k/n + 5-cell bar; 달성도 보기 -> KR_T17SummaryPage, whose dialog top is '
    'lowered to y 186 with ■選択ダイアログ／上座標制限値 so the home panel 전체 row stays visible; 3 columns where 2 would exceed '
    '704 px, i.e. September), KR_T9MemPage -> KR_T17MemPage (title 「회상 · 그 밖 (패널 밖)」 + bar line, 113 = all of its own '
    'scenes, all outside the panel), KR_T9LaneTitle -> KR_T17LaneTitle (bar line), KR_T9CardRow -> KR_T17CardRow (E-number tail '
    'on the 26 rows that collided), KR_T9ChipRow -> KR_T17ChipRow (drawer rows 「이름 k/n □□□□□」), KR_T9MonthChips -> '
    'KR_T17MonthChips (이달의 서랍 title counted on the panel set). These screen functions are never on a saved stack. Bars: nearest '
    'cell (.5 up), never the last cell before everything is seen. Counts: in months 4-11 every numerator/denominator counts only '
    'the home achievement panel set (r9 KR_T8: Σ KR_PlayerEventCount(0..3) / 1043); the 121 calendar events outside it (85 회상 '
    'replays, 28 events the game never calls, 8 dungeon-lane events: E00996 E05000 E06001 E10523 E20523 E30523 E40523 E50007) stay '
    'listed and playable but are not counted, and appear only in the summary line 「패널 밖 n/121」 and the 회상 · 그 밖 page. The '
    'summary first line 「전체 k/1043 (x%)」 prints the panel value with the panel\'s own KR_T8Pct. r15 rules stay: KR_T9HomeCasual, '
    'KR_T9HomeConfig, C_SceneHomebase@CheckGameSysButtons, C_SceneHomebase@Run and LSys3xScript::RunEvent keep index, address and '
    'code bytes (r17 verified them byte-identical to the r15 candidate); r15\'s nine same-length CALLFUNC operands stay applied. '
    'Panel code (KR_T8*, KR_Rate*, KR_PlayerEventCount) untouched; the calendar\'s panel-outside table (KR_T17Out) is derived from '
    'KR_PlayerEventCount at build time: if Codex changes the panel set, rebuild the calendar. State lives only in SystemService '
    'variables YoruKR.T9.* (never saved); no globals, structs or save schema change. Tables stay r15\'s (chart/build_chart_v2.py) '
    'plus the r16 tail table and the r17 panel-outside table: rebuild when the chart data changes. Every earlier contract stays in force.')


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
    native = read(L.WORK / 'build' / 'native_compare.json')
    scan = read(L.WORK / 'scan_report.json')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, r17_byte_identical_to_r15=True)
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
        status='CALENDAR_R17_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files={n: man['files'][n]['sha256'] for n in FILES},
        candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False, ex_changed=False,
        replaces=dict(r16_candidate_ain_sha256=L.R16_AIN_SHA, r16_installed=False,
                      function_names='new functions are all KR_T17*; KR_T16* (r16) never shipped and are not in this candidate'),
        added_functions=len(ids), added_function_names=sorted(ids), forwarded_functions=forwarded, same_length_sites=[],
        r15_same_length_sites_kept=man['r15_same_length_sites_kept'], relocated_original_functions=[], pinned_addresses=pinned,
        never_on_saved_stack=['C_SceneHomebase@RunHome (r13/r15 rule: the replay runs after RunHome has returned)',
                              'every KR_T9 / KR_T17 page and table function, incl. the six forwarded ones (S4: no saved frame in them)'],
        panel_outside=dict(count=man['panel']['outside'], memory_page=man['panel']['memory_page'],
                           dungeon_lane=man['panel']['dungeon_lane'], derived_from='KR_PlayerEventCount (base AIN) at build time',
                           panel_code_sha256=man['panel']['panel_code_sha256']),
        summary_dialog_top=186,
        session_variables=man['session_variables'], serialized_schema_changes=0,
        verification=dict(vm=vm['counts'], vm_steps=vm['vm_steps'], planted_defects_caught=sum(p['caught'] for p in st['planted_defects']),
                          planted_defects=len(st['planted_defects']), saves_checked=vm['saves_checked'], frames_checked=vm['frames_checked'],
                          native_probe=dict(passed=bool(ok_probe), seconds=probe.get('seconds'), save=probe.get('save'),
                                            screenshots=[Path(s).name for s in probe['screenshots']],
                                            home_before_after_differing_pixels=probe.get('home_before_after', {}).get('differing_pixels'),
                                            month_before_after_summary_differing_pixels=probe.get('month_before_after_summary', {}).get('differing_pixels')),
                          native_blocks_equal_vm=native['counts']['N_blocks_identical'], native_panel=native['blocks'].get('panel_same_save'),
                          real_saves_summary_equals_panel=vm['counts'].get('V14_native_panel_equal'),
                          panel=vm['panel'] and {k: v for k, v in vm['panel'].items() if k != 'states'},
                          defender=scan['status'], transaction_fixture=fx['status'] if fx else 'NOT_RUN'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_r17_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)


def probe_ok(probe):
    return bool(probe.get('exit_code') == 0 and probe['log'] and probe['log'][-1] == 'END' and probe['user_save_folder_unchanged']
                and not probe['c_drive_alicesoft_changes'] and not probe.get('vm_error') and not probe.get('message') and not probe.get('events')
                and probe.get('home_before_after', {}).get('differing_pixels') == 0
                and probe.get('month_before_after_summary', {}).get('differing_pixels') == 0)


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
        issues.append('runtime AIN moved since the build (Codex installed something): rebuild r17 on the new runtime')
    if L.sha(rt / 'NightRemasterPact.afa') != base['pact_sha256'] or L.sha(rt / 'NightRemasterEX.ex') != base['ex_sha256']:
        issues.append('runtime PACT/EX moved since the build')
    if cur['manifest_sha256'] != base['manifest_sha256'] or L.sha(Path(cur['manifest'])) != cur['manifest_sha256']:
        issues.append('current.json / runtime manifest moved since the build')
    if cur.get('status') != base['status']:
        issues.append('current.json status moved since the build')
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
            or 'panel_same_save' not in native.get('blocks', {}):
        issues.append('native titles / rows / panel not compared with the VM (verify_calendar_r17.py --native)')
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
        issues.append('evidence/calendar_r17 already exists: inspect the earlier transaction')
    if (R / 'evidence' / 'calendar_r16').exists() or (R / 'required_calendar_r16.json').exists():
        issues.append('r16 appears installed after all (evidence/calendar_r16 or required_calendar_r16.json): r17 was built to replace an uninstalled r16 — inspect first')
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
    full['calendar_r17_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)
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
        nm.update(status=STATUS, time=now, calendar_r17_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_r17_overlay=str(E / 'source' / 'manifest.json'))
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = 'User screen check: 이벤트 달력 달 쪽(막대 반올림·▲●○, ★ 없음·9월 3열), 달성도 보기(왼쪽 패널 전체 %와 같은 값), 레인 쪽 서랍 줄 「이름 k/n □□□□□」, 회상 · 그 밖 (패널 밖), 10월 마나미 E번호 꼬리.'
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
            c['calendar_r17_preserved_by'] = str(E)
            write(R / n, js(c))
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, required_files=after, evidence=str(E),
                     preserves_contracts=sorted(contracts))
        write(R / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, calendar_r17_revision=rev)
        write(PTR, js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation), calendar_r17_evidence=str(E))
        write(R / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} 인게임 이벤트 달력 r17 설치 (Claude Opus 5.5; 설치되지 않은 r16 후보를 대신함)\n"
                "- 달 쪽 제목 첫 줄 달성도 막대·비율, 달력 칸 놓침 ▲·앞으로 ●·다 봄 ○(★ 없음), 메뉴 줄·서랍 줄 「이름 본 것/장면 □□□□□」, 「달성도 보기」 요약 쪽(첫 줄 = 왼쪽 패널 전체 값, 패널 밖 n/121 한 줄), 레인 쪽 제목 막대, 겹치던 레인 줄 26개에 E번호 꼬리. 막대는 가장 가까운 칸, 다 보기 전 마지막 칸 없음. 셈은 패널과 같은 1,043. 9월(6주)은 메뉴 3열.\n"
                "- AIN 한 파일, 원본 함수 이전 0, 새 같은 길이 교체 0(r15 의 9곳 유지), r15 화면 함수 6개는 번호 그대로 한 줄 전달(새 함수 KR_T17*), 주소 유지 함수 5개 바이트 동일.\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {E}; 되돌리기 publish_calendar_r17.py --restore.\n")
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
