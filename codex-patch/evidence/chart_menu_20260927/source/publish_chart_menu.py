"""Claude Fable 5.1 (2026-09-27): install / restore of the chart-menu hook (modelled on publish_calendar_r17.py).

  python publish_chart_menu.py --stage      copy the release DLL and the chart into candidate/ and record their hashes
  python publish_chart_menu.py --contract   write the Codex contract draft required_chart_menu_20260927.json (draft)
  python publish_chart_menu.py --verify     read-only readiness check
  python publish_chart_menu.py --install    INSTALL (only with the user's permission, game closed, Codex not installing)
  python publish_chart_menu.py --restore    undo the install exactly (journal-driven, idempotent)

Payload (2 files, runtime-relative):
  winmm.dll                          replaced: the Korean-patch IME hook rebuilt from hook_chartmenu/src with a
                                     「도움말 → 이벤트 플로우 차트(&E)」 menu item (same proxy table, same 4 exports)
  Manual/chart/yoru_flowchart_v2.html  added: the reviewer flowchart the menu item opens in the default browser
No AIN / PACT / EX / FNL change. Metadata touched only by --install / --restore: runtime manifest.json, current.json,
every required_*.json (chart_menu_preserved_by), new required_chart_menu_20260927.json, ui_hangul_input_fix.json,
latest_worked_translation.json (manifest hash only), progress.md note, evidence/chart_menu_20260927/.
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
E = R / 'evidence' / 'chart_menu_20260927'
NEW = 'required_chart_menu_20260927.json'
DRAFT = HERE / NEW
AUTHOR = 'Claude Fable 5.1 (claude-fable-5-1)'
STATUS = 'CHART_MENU_INSTALLED_NATIVE_PASS'
READY = 'CHART_MENU_READY_NOT_INSTALLED'
DLL = 'winmm.dll'
CHART = 'Manual/chart/yoru_flowchart_v2.html'
FILES = [DLL, CHART]
SOURCES = {DLL: HERE / 'build_release' / 'winmm.dll', CHART: HERE.parent / 'chart' / 'yoru_flowchart_v2.html'}
BASE_DLL_SHA = 'e81cfca5e7a84841affaf55cdcac3912a5b471c4073b2114e8c503dad41d0ed4'   # hangul_name_v4 release hook
HEADER_SHA = '757865b39d9991d3'                                                     # proxy table header prefix (2,364 rows)
INSTRUCTION = (
    'Claude chart menu (2026-09-27): the runtime winmm.dll is now built from hook_chartmenu/src (a copy of the hangul_name_v4 '
    'IME hook, P:/AI/Codex/projects/YoruGaKuru_KR_rebuild_20260830_hangul_name_v4/hook, plus one feature): on the first WM_INITMENU '
    'of the game window it inserts 「이벤트 플로우 차트(&E)」 after 「플레이 매뉴얼(&M)」 in the 「도움말(&H)」 menu, choosing a free '
    'command id in 0x7E10..0x7EFF, and on that WM_COMMAND opens <exe folder>/Manual/chart/yoru_flowchart_v2.html with ShellExecuteW '
    '(default browser). The item is not added when the menu bar does not have the shipped shape or the chart file is missing. '
    'Everything else in the hook is unchanged: same 4 exports, same IAT hooks, same 2,364-row proxy table (generated header '
    'sha256 757865b3…, identical to the shipped build), same IME behaviour; the DLL additionally imports SHELL32/ole32. '
    'Build: hook_chartmenu/build_all.cmd 2364 (VS 2022 Build Tools x86, /W4 /WX, static CRT); release profile ships, diagnostic '
    'profile writes hangul_ime_hook.log. ui_hangul_input_fix.json now points to this DLL: any rebuild of the runtime must copy '
    'this winmm.dll (not the hangul_name_v4 one) and keep Manual/chart/yoru_flowchart_v2.html; when the chart is rebuilt '
    '(chart/build_chart_v2.py) copy the new HTML to the same path and update its manifest row. If the IME hook itself changes, '
    'rebuild from hook_chartmenu/src (merge the change there) so the menu item survives. No AIN/PACT/EX/FNL change; no save '
    'schema change. Every earlier contract stays in force.')


def js(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.chartmenu-', suffix='.tmp', delete=False) as f:
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
    tmp = dest.with_name(dest.name + '.chartmenu-copy.tmp')
    assert not tmp.exists(), str(tmp)
    try:
        shutil.copy2(src, tmp)
        assert L.sha(tmp) == expected
        os.replace(tmp, dest)
        assert L.sha(dest) == expected
    finally:
        if tmp.exists():
            tmp.unlink()


def remove_file(path):
    if path.exists():
        path.unlink()
    parent = path.parent
    if parent.name == 'chart' and parent.exists() and not any(parent.iterdir()):
        parent.rmdir()


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
    expected = {r['path'] for r in rows}
    actual = {p.relative_to(rt).as_posix() for p in rt.rglob('*') if p.is_file()}
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
    man = dict(schema='chart-menu-hook.candidate.v1', author=AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
               files=rec, base_dll_sha256=BASE_DLL_SHA, proxy_header_sha256=L.sha(header), proxy_header_rows=header.read_bytes().count(b'static_cast<wchar_t>'),
               source_sha256={f.name: L.sha(f) for f in (HERE / 'src').glob('*') if f.is_file()},
               build_log_sha256=L.sha(build) if build.exists() else None)
    assert man['proxy_header_sha256'].startswith(HEADER_SHA), 'proxy table header differs from the shipped build'
    put(O / 'manifest.json', js(man))
    print(js(man).decode('utf8'))


def after_hashes():
    man = read(O / 'manifest.json')
    return {n: man['files'][n]['sha256'] for n in FILES}


def draft_contract():
    man = read(O / 'manifest.json')
    probe = read(HERE / 'probe_result.json')
    scan = read(HERE / 'scan_report.json')
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    return dict(status='CHART_MENU_DRAFT_NOT_INSTALLED', author=AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
                required_files=after_hashes(), replaced_files={DLL: dict(before=BASE_DLL_SHA, after=man['files'][DLL]['sha256'])},
                added_files=[CHART], ain_changed=False, pact_changed=False, ex_changed=False, fnl_changed=False,
                hook=dict(source=str(HERE / 'src'), build='hook_chartmenu/build_all.cmd 2364', proxy_header_sha256=man['proxy_header_sha256'],
                          proxy_header_rows=man['proxy_header_rows'], exports=['timeGetDevCaps', 'timeGetTime', 'timeBeginPeriod', 'timeEndPeriod'],
                          new_imports=['SHELL32.dll', 'ole32.dll'], menu=dict(top='도움말(&H)', position=1, text='이벤트 플로우 차트(&E)',
                          command_id_range='0x7E10..0x7EFF (first free)', opens=CHART, hidden_when='chart file missing or menu shape differs')),
                verification=dict(unit_harness='PASS table=2364 (build log)', native_probe=probe, defender=scan.get('status')),
                preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='chart_menu_preserved_by',
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
        issues.append('runtime winmm.dll is not the hangul_name_v4 release hook (someone changed it): rebuild from that source')
    if (rt / CHART).exists():
        issues.append('runtime already has ' + CHART)
    if cur['manifest_sha256'] != L.sha(mp):
        issues.append('current.json / runtime manifest hash mismatch')
    try:
        exact_tree(rt, read(mp)['files'])
    except AssertionError as ex:
        issues.append('runtime tree differs from its manifest: ' + str(ex)[:200])
    scan = read(HERE / 'scan_report.json') if (HERE / 'scan_report.json').exists() else {}
    if scan.get('status') != 'SCANNED_NO_TARGET_DETECTIONS' or scan.get('sha256') != after[DLL]:
        issues.append('Defender scan missing or not for this DLL')
    probe = read(HERE / 'probe_result.json') if (HERE / 'probe_result.json').exists() else {}
    if not (probe.get('menu_item_added') and probe.get('chart_opened') and probe.get('iat_hooks_installed')):
        issues.append('native probe missing or failing')
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
        issues.append('ui_hangul_input_fix.json does not point to the base hook')
    if E.exists():
        issues.append('evidence/chart_menu_20260927 already exists: inspect the earlier transaction')
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
    for n in FILES:
        dest = E / 'candidate' / n
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(O / n, dest)
        assert L.sha(dest) == after[n]
    for f in list(HERE.glob('*.py')) + list(HERE.glob('*.json')) + list(HERE.glob('*.md')) + list(HERE.glob('*.cmd')) + list((HERE / 'src').glob('*')):
        if f.is_file():
            shutil.copy2(f, E / 'source' / f.name)
    for f in (HERE / 'build_release').glob('build*.log'):
        shutil.copy2(f, E / 'source' / f.name)
    put(E / 'save_hashes_before.json', js(saves))
    j = dict(status='PREPARED', runtime=str(rt), before=before, after=after, added=[CHART], metadata=metadata)
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
        copy_checked(O / CHART, rt / CHART, after[CHART])
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, author=AUTHOR, files=after, source_files=before, added_files=[CHART], evidence=str(E),
                   native_probe_verified=True, screen_verified=False, ain_changed=False, pact_changed=False, ex_changed=False, fnl_changed=False,
                   save_schema_changes=0, save_writes=0, translator_model=AUTHOR)
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now, chart_menu_revision=rev)
        rows = [r for r in nm['files'] if r['path'] not in after]
        for n in FILES:
            rows.append(dict(path=n, size=(rt / n).stat().st_size, sha256=after[n]))
        nm['files'] = sorted(rows, key=lambda r: r['path'])
        nm['next'] = 'User screen check: 게임 창 상단 도움말(H) 메뉴에 「이벤트 플로우 차트(E)」 → 기본 브라우저로 차트가 열리는지; 한글 이름 입력이 전과 같은지.'
        write(mp, js(nm))
        mh = L.sha(mp)
        for n in contracts:
            c = read(R / n)
            for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if k in c:
                    c[k] = mh
            c['chart_menu_preserved_by'] = str(E)
            write(R / n, js(c))
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, evidence=str(E), preserves_contracts=sorted(contracts))
        write(R / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, chart_menu_revision=rev)
        write(PTR, js(nc))
        fix = read(R / 'ui_hangul_input_fix.json')
        fix['files']['winmm.dll'] = dict(source=str(HERE / 'build_release' / 'winmm.dll'), sha256=after[DLL],
                                         base_source='P:\\AI\\Codex\\projects\\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4\\hook\\build_release\\winmm.dll',
                                         base_sha256=BASE_DLL_SHA, note='chart_menu_20260927: same IME hook + 도움말 menu item; rebuild from hook_chartmenu/src')
        write(R / 'ui_hangul_input_fix.json', js(fix))
        latest = read(R / 'latest_worked_translation.json')
        latest.update(manifest_sha256=mh, chart_menu_evidence=str(E))
        write(R / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} 도움말 메뉴 「이벤트 플로우 차트」 설치 (Claude Fable 5.1)\n"
                "- 실행본 winmm.dll(한글 IME 후크)을 같은 소스에 메뉴 항목 하나를 더해 다시 빌드: 게임 창 도움말(H) → 「이벤트 플로우 차트(E)」 → Manual/chart/yoru_flowchart_v2.html 을 기본 브라우저로 연다. 표·IME 동작·내보내기 4개 동일, SHELL32/ole32 가져오기 추가. 차트 파일이 없으면 항목을 넣지 않는다.\n"
                f"- winmm.dll {after[DLL]}; chart {after[CHART]}; manifest {mh}; evidence {E}; 되돌리기 publish_chart_menu.py --restore. ui_hangul_input_fix.json 이 새 DLL 을 가리킨다.\n")
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
                remove_file(rt / CHART)
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
        assert L.sha(rt / DLL) == j['before'][DLL] and not (rt / CHART).exists()
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
    remove_file(rt / CHART)
    for row in j['metadata']:
        path = Path(row['path'])
        if row['existed']:
            put(path, (E / 'before' / row['name']).read_bytes())
        elif path.exists():
            path.unlink()
    assert L.sha(rt / DLL) == j['before'][DLL] and not (rt / CHART).exists()
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
