"""Claude Fable 5.1 (2026-09-28): install / restore of the mod-menu hook (replaces the chart-menu hook DLL).

  python publish_mod_menu.py --stage      copy the release DLL into candidate/ and record its hash
  python publish_mod_menu.py --contract   write the Codex contract draft required_mod_menu_20260928.json
  python publish_mod_menu.py --verify     read-only readiness check
  python publish_mod_menu.py --install    INSTALL (only with the user's permission, game closed, Codex not installing)
  python publish_mod_menu.py --restore    undo the install exactly (journal-driven, idempotent)

Payload (1 file): winmm.dll — the Korean-patch IME hook rebuilt from hook_modmenu/src. Compared with the chart-menu
build (378a7834…) the Help item is gone; a 「모드」 popup (이벤트 플로우 차트 / 전체 개방 / 전체 개방 되돌리기 / 전체 리셋 /
전체 리셋 되돌리기) writes KRMenu\\request.txt for the game script, and a pending KRMenu\\reset.req / restore.req is
executed at the next start (global record files backed up to <save>\\Backup\\KR_reset_<time>\\ or restored from there).
Manual/chart/yoru_flowchart_v2.html stays in place (its contract row is untouched). No AIN / PACT / EX / FNL change.
"""
from pathlib import Path
import copy, datetime, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R17 = HERE.parent / 'ingame' / 'r17_calendar'
sys.path.insert(0, str(R17))
import r17lib as L                                   # read-only helpers: CODEX, CURRENT, SAVES, env, sha

R = L.CODEX
PTR = L.CURRENT
O = HERE / 'candidate'
E = R / 'evidence' / 'mod_menu_r2_20260928'
NEW = 'required_mod_menu_r2_20260928.json'
DRAFT = HERE / NEW
AUTHOR = 'Claude Fable 5.1 (claude-fable-5-1)'
STATUS = 'MOD_MENU_R2_INSTALLED_NATIVE_PASS'
READY = 'MOD_MENU_R2_READY_NOT_INSTALLED'
DLL = 'winmm.dll'
CHART = 'Manual/chart/yoru_flowchart_v2.html'
FILES = [DLL]
SOURCES = {DLL: HERE / 'build_release' / 'winmm.dll'}
BASE_DLL_SHA = 'a4dd91102fbea2e1a7992974e53d45ffbeec8e79dc9981c5cc7c5201a01ab053'   # mod-menu hook r1 (2026-09-28 05:5x)
HEADER_SHA = '757865b39d9991d3'
INSTRUCTION = (
    'Claude mod menu r2 (2026-09-28 06h; r2 = the Mod popup is inserted as soon as the window shows (WM_SHOWWINDOW/ACTIVATE/PAINT, WM_INITMENU fallback), a native notice appears when request.txt is not consumed within 2.5 s, and YoruKR_HomeRate.dat (achievement-panel setting) is excluded from reset): the runtime winmm.dll is built from hook_modmenu/src (chart-menu hook + one feature set). '
    'On the first WM_INITMENU it inserts a 「모드(&M)」 popup between 「시스템」 and 「도움말」 with 이벤트 플로우 차트(&E) / 전체 개방(&U) / '
    '전체 개방 되돌리기(&R) / — / 전체 리셋(&Z) / 전체 리셋 되돌리기(&B) (command ids = first free in 0x7E10..0x7EFF); the Help item of '
    'the chart-menu build is gone. Each item writes <exe>/KRMenu/request.txt (3 lines: cmd, seq, time; cmd in chart, unlock_all, '
    'unlock_revert, reset_all, reset_restore) which the game script consumes in its home loop (calendar r21+); the two reset items '
    'first ask through a native MessageBox. At the next start (first timer call, before the engine reads its global record files) '
    'a pending KRMenu/reset.req or restore.req is executed only when the save folder also holds YoruKR_reset.marker with the '
    'matching word: NightRAFInfo/CGMode/MemMode/BGMMode/Common .asd, NightRMsgSkip.msk, CommonGameData.asd and YoruKR_HomeRate.dat '
    'are copied to <save>/Backup/KR_reset_<time>/ (manifest.txt) and deleted (reset), or copied back from the newest such folder '
    'with the current files kept in Backup/KR_before_restore_<time>/ (restore); save slots, config files, YoruKR_Terms.dat and '
    'YoruKR_Chart.dat are never touched; the outcome is written to KRMenu/last_result.txt (ASCII). Save folder resolution: '
    'AliceStart.ini SaveFolder + InstallInfo/SaveFolderSetting.ini (type 2 = exe-relative, else Documents/AliceSoft/<GameName>/). '
    'Everything else is unchanged: same 4 exports, same IAT hooks, same 2,364-row proxy table (header sha256 757865b3…), same IME '
    'behaviour; imports add SHELL32/ole32. Build: hook_modmenu/build_all.cmd 2364. ui_hangul_input_fix.json points to this DLL: '
    'any runtime rebuild must copy it; if the IME hook changes, rebuild from hook_modmenu/src. Manual/chart/yoru_flowchart_v2.html '
    'stays as required by required_chart_menu_20260927.json until the in-game chart replaces it. No AIN/PACT/EX/FNL change.')


def js(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.modmenu-', suffix='.tmp', delete=False) as f:
        tmp = Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    try:
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def copy_checked(src, dest, expected):
    assert L.sha(src) == expected, ('source mismatch', str(src))
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + '.modmenu-copy.tmp')
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


def stopped(rt):
    exe = (rt / 'NightRemaster.exe').resolve()
    return not [x for x in processes() if not x.get('ExecutablePath') or Path(x['ExecutablePath']).resolve() == exe]


def exact_tree(rt, rows):
    # <runtime>/KRMenu holds transient exchange files written by the hook and the game script (request.txt,
    # last_result.txt, reset.req, restore.req); it is never part of the manifest and is ignored here.
    expected = {r['path'] for r in rows}
    actual = {p.relative_to(rt).as_posix() for p in rt.rglob('*') if p.is_file() and p.relative_to(rt).parts[0] != 'KRMenu'}
    assert actual == expected, ('runtime tree differs from manifest', sorted(actual ^ expected)[:10])
    for r in rows:
        p = rt / r['path']
        assert p.stat().st_size == r['size'] and L.sha(p) == r['sha256'], r['path']


def snapshot_saves():
    assert L.SAVES.is_dir(), L.SAVES
    return {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}


def contracts_now():
    return sorted(p.name for p in R.glob('required_*.json') if p.name != NEW)


def stage():
    O.mkdir(exist_ok=True)
    rec = {}
    for n in FILES:
        src = SOURCES[n]
        assert src.is_file(), src
        dest = O / n
        copy_checked(src, dest, L.sha(src))
        rec[n] = dict(source=str(src), sha256=L.sha(dest), size=dest.stat().st_size)
    header = HERE / 'src' / 'hangul_proxy_table.generated.h'
    build = HERE / 'build_release' / 'build.log'
    man = dict(schema='mod-menu-hook.candidate.v1', author=AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
               files=rec, base_dll_sha256=BASE_DLL_SHA, proxy_header_sha256=L.sha(header),
               proxy_header_rows=header.read_bytes().count(b'static_cast<wchar_t>'),
               source_sha256={f.name: L.sha(f) for f in (HERE / 'src').glob('*') if f.is_file()},
               build_log_sha256=L.sha(build) if build.exists() else None)
    assert man['proxy_header_sha256'].startswith(HEADER_SHA), 'proxy table header differs from the shipped build'
    put(O / 'manifest.json', js(man))
    print(js(man).decode('utf8'))


def after_hashes():
    man = read(O / 'manifest.json')
    return {n: man['files'][n]['sha256'] for n in FILES}


def probe_summary():
    full = read(HERE / 'probe_result.json')
    run1 = read(HERE / 'probe_result_run1.json')

    def text(v):
        return (v.get('value') if isinstance(v, dict) else v) or ''
    ok = dict(
        menu_installed=run1.get('mod_index', -1) >= 0 and len(run1.get('command_ids') or []) == 5 and run1.get('help_items') == 3,
        requests_written=all(text(run1.get(k)).startswith(c) for k, c in [('req_chart', 'chart'), ('req_unlock', 'unlock_all'),
                                                                            ('req_revert', 'unlock_revert'), ('req_after_reset_yes', 'reset_all')]),
        reset_cancel_respected=text(run1.get('req_after_reset_no')).startswith('unlock_revert') and bool(run1.get('reset_box_found')),
        startup_reset=text(full.get('reset_result')).startswith('reset ok') and
                      set(full.get('global_files_after_reset') or []) <= {'YoruKR_HomeRate.dat'} and
                      len(full.get('backup_files') or []) >= 8 and 'YoruKR_HomeRate.dat' not in (full.get('backup_files') or []) and
                      not full.get('marker_left') and not full.get('req_left'),
        startup_restore=text(full.get('restore_result')).startswith('restore ok') and
                        sorted(full.get('global_files_after_restore') or []) == sorted(full.get('global_files_before') or []) and
                        not full.get('marker_left_after_restore'))
    return dict(ok, all=all(ok.values()), mod_items=run1.get('mod_items'), reset_result=text(full.get('reset_result')).strip(),
                restore_result=text(full.get('restore_result')).strip())


def draft_contract():
    man = read(O / 'manifest.json')
    scan = read(HERE / 'scan_report.json')
    probe = probe_summary()
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    return dict(status='MOD_MENU_R2_DRAFT_NOT_INSTALLED', author=AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
                required_files=after_hashes(), replaced_files={DLL: dict(before=BASE_DLL_SHA, after=man['files'][DLL]['sha256'])},
                kept_files=[CHART], ain_changed=False, pact_changed=False, ex_changed=False, fnl_changed=False,
                hook=dict(source=str(HERE / 'src'), build='hook_modmenu/build_all.cmd 2364', proxy_header_sha256=man['proxy_header_sha256'],
                          proxy_header_rows=man['proxy_header_rows'], exports=['timeGetDevCaps', 'timeGetTime', 'timeBeginPeriod', 'timeEndPeriod'],
                          menu=dict(top='모드(&M) between 시스템 and 도움말', items=['이벤트 플로우 차트(&E)', '전체 개방(&U)', '전체 개방 되돌리기(&R)',
                                    '전체 리셋(&Z)', '전체 리셋 되돌리기(&B)'], command_id_range='0x7E10..0x7EFF (first free)'),
                          request_file='<exe>/KRMenu/request.txt (cmd, seq, time)',
                          startup_maintenance='KRMenu/reset.req or restore.req + <save>/YoruKR_reset.marker -> Backup/KR_reset_<time>',
                          global_record_files=['NightRAFInfo.asd', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd',
                                               'NightRAFCommon.asd', 'NightRMsgSkip.msk', 'CommonGameData.asd', 'YoruKR_HomeRate.dat']),
                verification=dict(unit_harness='PASS table=2364 (build log)', native_probe=probe, defender=scan.get('status')),
                preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='mod_menu_r2_preserved_by',
                instruction=INSTRUCTION, translator_model=AUTHOR)


def readiness():
    issues = []
    cur = read(PTR)
    rt = Path(cur['runtime']).resolve()
    mp = Path(cur['manifest'])
    if not (O / 'manifest.json').exists():
        return False, dict(status='NOT_READY', issues=['run --stage first'])
    after = after_hashes()
    for n in FILES:
        if L.sha(O / n) != after[n]:
            issues.append('candidate file differs from its manifest: ' + n)
    if L.sha(rt / DLL) != BASE_DLL_SHA:
        issues.append('runtime winmm.dll is not the mod-menu r1 hook build: rebase this build on the DLL that is installed')
    if not (rt / CHART).exists():
        issues.append('runtime lacks ' + CHART + ' (required_chart_menu contract): inspect')
    if cur['manifest_sha256'] != L.sha(mp):
        issues.append('current.json / runtime manifest hash mismatch')
    try:
        exact_tree(rt, read(mp)['files'])
    except AssertionError as ex:
        issues.append('runtime tree differs from its manifest: ' + str(ex)[:200])
    scan = read(HERE / 'scan_report.json') if (HERE / 'scan_report.json').exists() else {}
    if scan.get('status') != 'SCANNED_NO_TARGET_DETECTIONS' or scan.get('sha256') != after[DLL]:
        issues.append('Defender scan missing or not for this DLL')
    try:
        probe = probe_summary()
        if not probe['all']:
            issues.append('native probe failing: ' + json.dumps({k: v for k, v in probe.items() if v is False}))
    except Exception as ex:
        issues.append('native probe missing: ' + repr(ex))
    if not DRAFT.exists():
        issues.append('contract draft missing (run --contract)')
    else:
        d = read(DRAFT)
        if sorted(d['preserves_contracts']) != contracts_now():
            issues.append('required_*.json list changed since the contract draft: rerun --contract')
        if d['required_files'] != after:
            issues.append('contract draft is for another candidate')
    fix = read(R / 'ui_hangul_input_fix.json')
    if fix['files']['winmm.dll']['sha256'] != BASE_DLL_SHA:
        issues.append('ui_hangul_input_fix.json does not point to the mod-menu r1 hook')
    if E.exists():
        issues.append('evidence/mod_menu_20260928 already exists: inspect the earlier transaction')
    running = not stopped(rt)
    report = dict(status=READY if not issues else 'NOT_READY', candidate=after, runtime=str(rt), issues=issues, game_running=running,
                  contracts_now=len(contracts_now()), install_command=f'python "{Path(__file__)}" --install',
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
    after = after_hashes()
    before = {DLL: L.sha(rt / DLL)}
    manifest = read(mp)
    exact_tree(rt, manifest['files'])
    saves = snapshot_saves()
    contracts = contracts_now()
    paths = [mp, PTR, R / 'progress.md', R / 'ui_hangul_input_fix.json', R / 'latest_worked_translation.json'] + [R / n for n in contracts + [NEW]]
    assert len(paths) == len(set(x.name for x in paths))
    snapshots = {x: x.read_bytes() if x.exists() else None for x in paths}
    assert snapshots[R / NEW] is None
    E.mkdir(parents=True)
    for folder in ['before', 'candidate', 'source']:
        (E / folder).mkdir()
    metadata = []
    for path, data in snapshots.items():
        if data is not None:
            put(E / 'before' / path.name, data)
        metadata.append(dict(path=str(path), name=path.name, existed=data is not None, sha256=L.sha(path) if data is not None else None))
    shutil.copy2(rt / DLL, E / 'before' / DLL)
    shutil.copy2(O / DLL, E / 'candidate' / DLL)
    assert L.sha(E / 'candidate' / DLL) == after[DLL]
    for f in list(HERE.glob('*.py')) + list(HERE.glob('*.json')) + list(HERE.glob('*.md')) + list(HERE.glob('*.cmd')) + list(HERE.glob('*.ps1')) + list((HERE / 'src').glob('*')):
        if f.is_file():
            shutil.copy2(f, E / 'source' / f.name)
    for f in (HERE / 'build_release').glob('build*.log'):
        shutil.copy2(f, E / 'source' / f.name)
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
        copy_checked(O / DLL, rt / DLL, after[DLL])
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, author=AUTHOR, files=after, source_files=before, evidence=str(E), native_probe_verified=True,
                   screen_verified=False, ain_changed=False, pact_changed=False, ex_changed=False, fnl_changed=False,
                   save_schema_changes=0, save_writes=0, translator_model=AUTHOR)
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now, mod_menu_r2_revision=rev)
        for row in nm['files']:
            if row['path'] == DLL:
                row.update(sha256=after[DLL], size=(rt / DLL).stat().st_size)
        nm['next'] = 'User screen check: 게임 창 메뉴바 「모드(M)」 → 다섯 항목; 「전체 리셋」은 확인 창 뒤 다음 실행에서 초기화(백업 Backup/KR_reset_*).'
        write(mp, js(nm))
        mh = L.sha(mp)
        for n in contracts:
            c = read(R / n)
            for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if k in c:
                    c[k] = mh
            c['mod_menu_r2_preserved_by'] = str(E)
            write(R / n, js(c))
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, evidence=str(E), preserves_contracts=sorted(contracts))
        write(R / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, mod_menu_r2_revision=rev)
        write(PTR, js(nc))
        fix = read(R / 'ui_hangul_input_fix.json')
        fix['files']['winmm.dll'] = dict(source=str(HERE / 'build_release' / 'winmm.dll'), sha256=after[DLL],
                                         base_source='P:\\AI\\Codex\\projects\\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4\\hook\\build_release\\winmm.dll',
                                         base_sha256='e81cfca5e7a84841affaf55cdcac3912a5b471c4073b2114e8c503dad41d0ed4',
                                         note='mod_menu_20260928: same IME hook + 모드 menu (request file, startup reset/restore); rebuild from hook_modmenu/src')
        write(R / 'ui_hangul_input_fix.json', js(fix))
        latest = read(R / 'latest_worked_translation.json')
        latest.update(manifest_sha256=mh, mod_menu_r2_evidence=str(E))
        write(R / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} 메뉴바 「모드」 메뉴 후크 설치 (Claude Fable 5.1)\n"
                "- winmm.dll(한글 IME 후크)을 다시 빌드: 게임 창 메뉴바에 「모드(M)」 = 이벤트 플로우 차트 / 전체 개방 / 전체 개방 되돌리기 / 전체 리셋 / 전체 리셋 되돌리기. 항목은 KRMenu/request.txt 를 쓰고 게임 스크립트(달력 r21+)가 본거지에서 읽는다. 도움말의 차트 항목은 제거(차트 HTML 파일은 계약대로 유지). 전체 리셋/되돌리기는 다음 실행 때 후크가 전역 기록 파일을 Backup/KR_reset_<시각>에 백업·삭제 / 복원한다(세이브·설정·용어 파일은 손대지 않음).\n"
                f"- 표·IME 동작·내보내기 4개 동일. winmm.dll {after[DLL]}; manifest {mh}; evidence {E}; 되돌리기 publish_mod_menu.py --restore. ui_hangul_input_fix.json 이 새 DLL 을 가리킨다.\n")
        write(R / 'progress.md', (snapshots[R / 'progress.md'] or b'') + note.encode('utf8'))
        exact_tree(rt, nm['files'])
        assert saves == snapshot_saves()
        j.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=L.sha(PTR))
        put(E / 'journal.json', js(j))
    except BaseException as error:
        errors = []
        if attempted:
            try:
                copy_checked(E / 'before' / DLL, rt / DLL, before[DLL])
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
    report = dict(status=STATUS, files=after, manifest_sha256=mh, runtime=str(rt), unchanged_save_files=len(saves), evidence=str(E), author=AUTHOR)
    put(E / 'publish_report.json', js(report))
    print(js(report).decode('utf8'))


def restore():
    j = read(E / 'journal.json')
    rt = Path(j['runtime']).resolve()
    assert stopped(rt), 'close the game first'
    if j['status'] == 'RESTORED':
        assert L.sha(rt / DLL) == j['before'][DLL]
        print('ALREADY_RESTORED')
        return
    assert j['status'] in ['COMMITTED', 'PREPARED', 'ROLLBACK_INCOMPLETE', 'RESTORING']
    for row in j['metadata']:
        path = Path(row['path'])
        assert path.resolve().is_relative_to(R.resolve())
        current = L.sha(path) if path.exists() else None
        allowed = {row['sha256'], j.get('metadata_after', {}).get(str(path), row['sha256'])}
        assert current in allowed, ('A newer or unknown metadata state exists: inspect before restoring', str(path))
    j['status'] = 'RESTORING'
    put(E / 'journal.json', js(j))
    if L.sha(rt / DLL) != j['before'][DLL]:
        copy_checked(E / 'before' / DLL, rt / DLL, j['before'][DLL])
    for row in j['metadata']:
        path = Path(row['path'])
        if row['existed']:
            put(path, (E / 'before' / row['name']).read_bytes())
        elif path.exists():
            path.unlink()
    assert L.sha(rt / DLL) == j['before'][DLL]
    j['status'] = 'RESTORED'
    put(E / 'journal.json', js(j))
    print('RESTORED EXACT PRE-INSTALL STATE')


if __name__ == '__main__':
    if '--stage' in sys.argv:
        stage()
    elif '--contract' in sys.argv:
        put(DRAFT, js(draft_contract()))
        print('DRAFT', DRAFT, L.sha(DRAFT))
    elif '--verify' in sys.argv:
        ok, rep = readiness()
        put(HERE / 'readiness.json', js(rep))
        print(js(rep).decode('utf8'))
    elif '--install' in sys.argv:
        install()
    elif '--restore' in sys.argv:
        restore()
    else:
        print(__doc__)
