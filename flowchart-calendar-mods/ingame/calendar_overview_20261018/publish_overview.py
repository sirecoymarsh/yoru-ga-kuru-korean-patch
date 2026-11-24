"""Claude Opus 5.5 (2026-10-18): install / restore of the event-calendar overview, stage 2 of the calendar / completion-rate
redesign (user, 10-17: the calendar does not feel like an overview of the whole story, too many pages, cells say little, no
per-character view; mockup approved 「왜 이리 멋져? 좋아 가자」; 10-18 「개선된 이벤트 캘린더도 적용됐어?」), made from
publish_overview.py (same journaled transaction, same KRMenu scratch rule).

  python publish_overview.py --stage      check candidate/manifest.json against the built AIN (the payload is the AIN only)
  python publish_overview.py --scan       Defender custom scan of a copy of the payload -> work/scan_report.json
  python publish_overview.py --contract   write the Codex contract draft required_calendar_overview_20261018.json
  python publish_overview.py --fixture    transaction fixture on disposable files under calendar_overview_20261018/work (no runtime)
  python publish_overview.py --verify     read-only readiness check (hashes, native probes, scan, fixture, saved stacks, contracts)
  python publish_overview.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_overview.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain (KR_XV* layer). PACT/EX/FNL, the Manual chart and winmm.dll untouched. One journaled transaction as
publish_overview.py: PREPARED -> atomic hash-checked replacement -> runtime manifest + current.json + every required_*.json present at
install time (calendar_overview_20261018_preserved_by) + new required_calendar_overview_20261018.json +
latest_worked_translation.json + progress.md note -> exact tree / saves / recovery runtime re-checked -> COMMITTED. Any failure
rolls back; --restore returns the exact pre-install state.
"""
from pathlib import Path
import copy, datetime, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ovlib as L

R = L.CODEX
O = HERE / 'candidate'
E = R / 'evidence' / 'calendar_overview_20261018'                 # created only by --install
PTR = L.CURRENT
FILES = ['NightRemaster.ain']
PROBES = ['probe_overview.json', 'probe_overview_NightR16.json', 'probe_overview_TITLE.json']
NEW = 'required_calendar_overview_20261018.json'
DRAFT = HERE / NEW
STATUS = 'CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS'
READY = 'CALENDAR_OVERVIEW_20261018_STATIC_NATIVE_PASS_NOT_INSTALLED'
DEFECTS = 12
RUNTIME_SCRATCH = 'KRMenu'
KRMENU_FILES = ['request.txt', 'last_result.txt', 'reset.req', 'restore.req']
KRMENU_RULE = ('<runtime>/KRMenu/ is the temporary exchange-file folder of the mod-menu hook and the game script (request.txt, '
               'last_result.txt, reset.req, restore.req): never put it in a manifest, ignore it in every tree check, and never delete '
               'it (a pending reset.req / restore.req or an unread last_result.txt may be waiting there).')
KRMENU_RULE_KO = ('<실행본>/KRMenu 는 후크 · 스크립트의 일시 교환 파일 폴더(request.txt · last_result.txt · reset.req · restore.req)이며 '
                  'manifest 에 넣지 않고 트리 검사에서 무시한다; 지우지 말 것.')
EVENTS = [58, 63, 69, 104, 258, 260, 322, 611, 10021, 20041, 20081, 20164, 30001, 30021, 30152, 40021, 40041, 40043, 40061]
PINNED = {
    'KR_T9HomeCasual': 'r18 contract: on saved stacks during a calendar replay; keep index, address and code bytes.',
    'KR_T9HomeConfig': 'r15 contract: keep in place.',
    'C_SceneHomebase@CheckGameSysButtons': 'already on saved stacks (save/load screens); keep in place.',
    'LSys3xScript::RunEvent': 'already on saved stacks (r12 contract).',
    'C_SceneHomebase@Run': 'already on saved stacks.',
    'KR_T18RunSandboxed': 'r18 contract: on saved stacks during a sandboxed replay.',
    'KR_CReplayRun': 'r22: the chart replay (memory mode) runs inside it.',
}
# auto-nav pins (10-15, still in force): on saved stacks when the player saves while a choice / the partner confirm / the
# new-game question is open; this layer keeps them byte-identical (build_mods_ain.py invariance) and so must every later build
PINNED_NEW = (['KR_AN_E%05d' % e for e in EVENTS] + ['KR_ANSelect', 'KR_ANSelFrame', 'KR_ANTrainConfirm', 'KR_ANOpeningQ', 'KR_ANNewGame'])
NO_RESTORE = ('Codex must never run publish_overview*.py --restore or otherwise remove the calendar-overview layer: KR_XV* '
              'functions; KR_CDo calls KR_XVChart where it called KR_CChart (the title and home chart requests open the month x row '
              'overview board first; a month head or a cell opens the month view KR_CChart on that month and closing it returns to '
              'the board); KR_C24Chart calls KR_XVWait where it called KR_CWait (right after a jump from the board the month view '
              'answers its first wait with that month\'s tab button, then waits as before). The board is drawn on parts '
              '2026101800-2026102440 above every AddArea part (as KR_F28ChartFrame does). Companion rows follow the home panel '
              'rule (KR_T20Joined at home; on the title screen a companion shows once any of their scenes was read in some save). '
              'It is user-requested: when a rebuild needs a clean base, rebase on the runtime that current.json points to and carry '
              'it forward; restore is reserved for the user\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_overview*.py --restore 를 실행하거나 캘린더 한눈에 보기 층(KR_XV* 함수; KR_CDo 의 KR_CChart 호출 → '
                 'KR_XVChart(타이틀 · 본거지의 캘린더 요청이 먼저 달 × 줄 판을 연다; 달 머리나 칸을 누르면 그 달의 달별 화면 KR_CChart, 닫으면 '
                 '판으로 돌아옴); KR_C24Chart 의 KR_CWait 호출 → KR_XVWait(판에서 넘어온 직후 첫 대기만 그 달 탭 단추로 답함))을 지우지 '
                 '않는다. 판의 부품 번호는 2026101800~2026102440, Z 는 AddArea 부품 위(KR_F28ChartFrame 과 같은 방식). 동료 줄은 본거지 '
                 '패널 규칙(본거지는 KR_T20Joined, 타이틀은 어느 세이브에서든 그 동료의 장면을 읽었으면). 사용자가 요청한 것이다: 깨끗한 '
                 '기준이 필요하면 current.json 이 가리키는 실행본 위에서 다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude event-calendar overview layer (2026-10-18, stage 2 of the user-requested calendar / completion-rate redesign). '
    + NO_RESTORE + ' Payload: NightRemaster.ain only. KR_XV* functions appended; no original function relocated; no new global '
    '/ struct member; 2 same-length CALLFUNC operand swaps. Row of every event baked as KR_XVLaneNo (schedule.json lanes), looked '
    'up by KR_CCellEv, so later calendar layers may reorder cells. The auto-nav pins stay (index, address and every code byte): '
    + ', '.join(PINNED_NEW) + '. ' + KRMENU_RULE + ' Every earlier contract stays in force.')


def js(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.overview-', suffix='.tmp', delete=False) as f:
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
    tmp = dest.with_name(dest.name + '.overview-copy.tmp')
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
        tmp = live / (n + '.overview-copy.tmp')
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


# ------------------------------------------------------------------ staging, scan
def stage():
    man = read(O / 'manifest.json')
    want = man['files']['NightRemaster.ain']['sha256']
    assert L.sha(O / 'NightRemaster.ain') == want, 'candidate AIN differs from its manifest: rebuild'
    assert man['pact_changed'] is False and set(man['files']) == set(FILES), man['files'].keys()
    return {n: man['files'][n]['sha256'] for n in FILES}


def scan():
    target = L.WORK / ('scan_payload_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    out = L.WORK / 'scan_report.json'
    p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(HERE / 'scan_overview.ps1'),
                        '-Candidate', str(O), '-Target', str(target), '-Out', str(out)], capture_output=True, timeout=900, env=L.env())
    print(p.stdout.decode('utf-8', 'replace')[-2000:], p.stderr.decode('utf-8', 'replace')[-2000:])
    assert p.returncode == 0, 'scan failed'
    return read(out)


# ------------------------------------------------------------------ evidence checks
def probe_overview_ok(p):
    lg = p.get('log') or []
    return bool(lg and 'END' in lg and 'FAILS 0' in lg and p.get('user_save_folder_unchanged') and not p.get('vm_error')
                and not p.get('events') and not p.get('timeout') and not p.get('fails') and p.get('oks', 0) >= 5)


def probes_ok(after):
    out = {}
    for n in PROBES:
        p = read(L.EVID / n) if (L.EVID / n).exists() else {}
        out[n] = bool(p.get('candidate_ain') == after['NightRemaster.ain'] and probe_overview_ok(p))
    return out


def draft_contract():
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    pk = probes_ok(after)
    assert all(pk.values()), ('rerun the probes for this candidate', pk)
    scan_ = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else None
    rc = read(L.WORK / 'resume_offset_check.json')
    assert rc['candidate_ain'] == after['NightRemaster.ain'] and not rc['problems'], 'rerun work/resume_offset_check.py'
    nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    ids = man['added_functions']
    pinned = {}
    for name, why in PINNED.items():
        fid = L.fid_of(nm, name)
        pinned[name] = dict(index=fid, address=nm['functions'][fid]['address'], why=why, code=man['pinned_functions'].get(name))
    still = {}
    for name in PINNED_NEW:
        fid = L.fid_of(nm, name)
        still[name] = dict(index=fid, address=nm['functions'][fid]['address'], code=man['pinned_functions'].get(name))
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    probes = {}
    for n in PROBES:
        p = read(L.EVID / n)
        probes[n] = dict(passed=pk[n], oks=p.get('oks'), fails=p.get('fails'), seconds=p.get('seconds'), save=p.get('save'),
                         shots=[Path(x).name for x in p.get('shots', [])])
    return dict(
        status='CALENDAR_OVERVIEW_20261018_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files=after, candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=False,
        ex_changed=False, fnl_changed=False, chart_changed=False, hook_changed=False,
        no_restore_rule=NO_RESTORE, added_functions=len(ids), added_function_names=sorted(ids),
        same_length_sites=man['same_length_sites'], message_box_sites=[], relocated_original_functions=[],
        pinned_addresses=pinned, pinned_from_now_on=still, baked=man.get('baked'),
        saved_stacks=dict(resume_saves=rc['stats']['resume_saves'], frames=rc['stats']['frames'],
                          frames_in_changed_functions=rc['stats'].get('frames_in_changed_functions', 0), problems=len(rc['problems']),
                          changed_functions_on_stacks=sorted({h['fn'] for h in rc['frames_in_changed_functions']}),
                          check=str(L.WORK / 'resume_offset_check.json'), check_sha256=L.sha(L.WORK / 'resume_offset_check.json'),
                          note='read-only check of the user\'s saves: every saved frame keeps its crc (the AIN function table is '
                               'unchanged), no original function moved, no frame resumes at or inside a swapped instruction'),
        verification=dict(probes=probes, defender=scan_.get('status'), transaction_fixture=fx['status'] if fx else 'NOT_RUN',
                          not_played_natively='real mouse clicks on the board (the probes end the wait with the part number a '
                                              'click returns); the cell replay paths are the month view\'s own, unchanged'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='calendar_overview_20261018_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)


# ------------------------------------------------------------------ the transaction (real paths or a disposable project)
class Ctx:
    def __init__(self, root, evidence, pointer, candidate, files, saves, stop_check, sources=None, note_title=None):
        self.root, self.evidence, self.pointer, self.candidate, self.files, self.saves = root, evidence, pointer, candidate, files, saves
        self.stop_check = stop_check
        self.sources = sources
        self.note_title = note_title or '이벤트 캘린더 한눈에 보기 (Claude Opus 5.5; 본거지 달성률 패널 설치본 위)'


def real_ctx():
    return Ctx(R, E, PTR, O, FILES, L.SAVES, stopped, sources=HERE)


def transact(ctx, fail_at=None):
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
        for n in PROBES:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        for f in L.EVID.glob('probe_*.png'):
            shutil.copy2(f, ev / 'source' / 'probe' / f.name)
        for n in ['scan_report.json', 'transaction_verification.json', 'resume_offset_check.json', 'consumer_audit.json',
                  'consumer_chain.json', 'build/native_opcode_audit.json']:
            if (L.WORK / n).exists():
                shutil.copy2(L.WORK / n, ev / 'source' / Path(n).name)
    shutil.copy2(cand / 'manifest.json', ev / 'source' / 'manifest.json')
    latest = read(root / 'latest_worked_translation.json')
    assert latest['manifest_sha256'] == cur['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    full = read(Path(latest['translation_map']))
    sequence = full['target_text_sequence_sha256']
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full['calendar_overview_20261018_overlay'] = dict(evidence=str(ev), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)
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
                   same_length_sites=[dict(function=s['function'], kind=s['kind'], original=s['original'], replacement=s['replacement'], site=s['site'])
                                      for s in draft.get('same_length_sites', [])],
                   pinned_from_now_on=sorted(draft.get('pinned_from_now_on', {})), translator_model=L.AUTHOR)
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now, calendar_overview_20261018_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], calendar_overview_20261018_overlay=str(ev / 'source' / 'manifest.json'))
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = ('User screen check: 캘린더를 열면 한눈에 보기(달 × 줄 판)가 먼저 뜨는지; 달이나 칸을 누르면 그 달 화면, 닫으면 판으로 '
                      '돌아오는지; 「이 세이브 / 모든 세이브」 전환; 합류 전 동료 줄이 안 보이는지; 타이틀의 모드 메뉴로 열어도 같은지.')
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
            c['calendar_overview_20261018_preserved_by'] = str(ev)
            write(root / n, js(c))
        if fail_at == 'after_contracts':
            raise RuntimeError('fixture: injected failure after the contracts')
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, required_files=after, evidence=str(ev),
                     preserves_contracts=sorted(contracts))
        write(root / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, calendar_overview_20261018_revision=rev)
        write(ptr_path, js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation), calendar_overview_20261018_evidence=str(ev))
        write(root / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} {ctx.note_title}\n"
                "- 이벤트 캘린더 한눈에 보기(사용자 10-17 캘린더 불편 · 시안 승인, 10-18 「개선된 이벤트 캘린더도 적용됐어?」): 캘린더를 열면 "
                "달(4~11월) × 줄(본편 · 합류한 동료 · 던전 동행) 판이 먼저 뜬다. 칸마다 본 수/전체와 막대(본 · 놓침 · 남음 · 아직), "
                "「이 세이브 / 모든 세이브」 전환, 회상 · 그 밖 단추. 달 머리나 칸을 누르면 그 달의 달별 화면, 닫으면 판으로 돌아온다.\n"
                "- KR_CDo 의 KR_CChart → KR_XVChart, KR_C24Chart 의 KR_CWait → KR_XVWait(같은 길이 CALLFUNC 피연산자 2곳). AIN 만, 원본 함수 "
                "이전 0, 새 전역 · 구조체 필드 0. 고정 함수(r18~r23 · 오토 내비 " + str(len(PINNED_NEW)) + "개)는 바이트 그대로.\n"
                "- " + KRMENU_RULE_KO + "\n"
                "- " + NO_RESTORE_KO + "\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) publish_overview.py --restore.\n")
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
    f = Path(tempfile.mkdtemp(prefix='복구 검증 ', dir=L.WORK))
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
    # a hard-linked live file (another copy of the runtime may share the inode): the swap must break the link, never write through
    os.unlink(l / FILES[-1])
    shared = f / 'shared_copy.ain'
    shutil.copy2(b / FILES[-1], shared)
    os.link(shared, l / FILES[-1])
    pair_apply(s, b, l, before, after)
    assert L.sha(shared) == before[FILES[-1]], 'the swap wrote through a hard link'
    pair_restore(b, l, before, after)
    for installed in [False, True]:
        if installed:
            pair_apply(s, b, l, before, after)
        for n in FILES:
            (l / (n + '.overview-copy.tmp')).write_bytes(b'partial interrupted copy')
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
                  hard_link_not_written_through=True, runtime_scratch_folder_ignored=whole['scratch_folder_ignored'],
                  injected_failure_rollback=True, known_mixed_and_interruption_restore=True, partial_incoming_copy_recovered=True,
                  tampered_payload_baseline_backup_rejected=True, exact_process_path_filter=True, unicode_spaces_path=True,
                  interrupted_metadata_restoration_resumable=whole['interrupted_restore_resumable'], whole_transaction=whole,
                  no_incoming_residue=not list(l.rglob('*.tmp')), files=FILES)
    put(L.WORK / 'transaction_verification.json', js(result))
    return result


def fake_project(f, name, payload_files, recovery_has):
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
    (rt / RUNTIME_SCRATCH).mkdir()
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
        (cand / n).write_bytes((O / n).read_bytes() if (O / n).exists() else ('candidate ' + n).encode())
        files[n] = dict(sha256=L.sha(cand / n), size=(cand / n).stat().st_size)
    put(cand / 'manifest.json', js(dict(files=files)))
    put(cand / NEW, js(dict(same_length_sites=[], pinned_from_now_on={})))
    ctx = Ctx(root, root / 'evidence' / 'calendar_overview_20261018', ptr, cand, payload_files, saves, lambda rt_: True, sources=None, note_title='fixture')
    return ctx, rt, rec


def install_fixture(f):
    out = {}
    ctx, rt, rec = fake_project(f, 'proj_ain_only', FILES, recovery_has={'NightRemaster.ain'})
    tree0 = snapshot_folder(ctx.root)
    rep = transact(ctx)
    j = read(ctx.evidence / 'journal.json')
    assert j['status'] == 'COMMITTED' and rep['recovery_lacks'] == [] and rep['recovery_hashed'] == ['NightRemaster.ain']
    assert all(L.sha(rt / n) == L.sha(ctx.candidate / n) for n in FILES)
    c = read(ctx.root / 'required_example_a.json')
    assert c['required_files']['NightRemaster.ain'] == L.sha(ctx.candidate / 'NightRemaster.ain') and c['calendar_overview_20261018_preserved_by'] == str(ctx.evidence)
    assert read(ctx.pointer)['status'] == STATUS and (ctx.root / NEW).exists()
    restore_ctx(ctx, runtime_override=rt)
    restore_ctx(ctx, runtime_override=rt)
    tree1 = snapshot_folder(ctx.root)
    changed = sorted(k for k in set(tree0) | set(tree1) if tree0.get(k) != tree1.get(k) and not k.startswith('evidence/calendar_overview_20261018/'))
    assert not changed, ('restore did not return the disposable project to its pre-install bytes', changed[:6])
    assert (rt / RUNTIME_SCRATCH / 'request.txt').exists(), 'the transaction touched the KRMenu scratch folder'
    out.update(committed=True, recovery_hashed=rep['recovery_hashed'], recovery_lacks=rep['recovery_lacks'], restored_exact=True,
               restore_idempotent=True, scratch_folder_ignored=True)
    for where in ('after_files', 'after_contracts', 'recovery_changed'):
        ctx3, rt3, rec3 = fake_project(f, 'proj_fail_' + where, FILES, recovery_has={'NightRemaster.ain'})
        t0 = snapshot_folder(ctx3.root)
        try:
            transact(ctx3, fail_at=where)
        except (RuntimeError, AssertionError):
            pass
        else:
            raise AssertionError('failure not injected: ' + where)
        assert read(ctx3.evidence / 'journal.json')['status'] == 'ROLLED_BACK', where
        t1 = snapshot_folder(ctx3.root)
        diff = sorted(k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k) and not k.startswith('evidence/calendar_overview_20261018/')
                      and not (where == 'recovery_changed' and k.startswith('ui_cumulative/recovery/')))
        assert not diff, ('rollback left changes', where, diff[:6])
        out['rolled_back_' + where] = True
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
    issues = []
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    cur = read(PTR)
    rt = Path(cur['runtime']).resolve()
    if any(L.sha(O / n) != after[n] for n in FILES):
        issues.append('candidate files differ from their manifest')
    base = man['base']
    if L.sha(rt / 'NightRemaster.ain') != base['ain_sha256']:
        issues.append('runtime AIN moved since the build (Codex installed something): rebuild on the new runtime')
    if L.sha(rt / 'NightRemasterPact.afa') != base['pact_sha256'] or L.sha(rt / 'NightRemasterEX.ex') != base['ex_sha256']:
        issues.append('runtime PACT/EX moved since the build: rebuild (the PACT row is built on the runtime PACT)')
    if cur['manifest_sha256'] != base['manifest_sha256'] or L.sha(Path(cur['manifest'])) != cur['manifest_sha256']:
        issues.append('current.json / runtime manifest moved since the build')
    if cur.get('status') != base['status']:
        issues.append('current.json status moved since the build')
    if L.sha(rt / 'winmm.dll') != base['winmm_sha256']:
        issues.append('the runtime winmm.dll moved since the build')
    pk = probes_ok(after)
    if not all(pk.values()):
        issues.append('native probes (probe_overview.py: NightR47, NightR16, TITLE) missing, failing or for another candidate: ' + str(pk))
    scan_ = read(L.WORK / 'scan_report.json') if (L.WORK / 'scan_report.json').exists() else {}
    if scan_.get('status') != 'SCANNED_NO_TARGET_DETECTIONS' or scan_.get('files') != after:
        issues.append('Defender scan missing or not for this candidate (run --scan)')
    fx = read(L.WORK / 'transaction_verification.json') if (L.WORK / 'transaction_verification.json').exists() else {}
    if fx.get('status') != 'TRANSACTION_FIXTURE_PASS' or fx.get('payload') != after:
        issues.append('transaction fixture missing (run --fixture)')
    rc = read(L.WORK / 'resume_offset_check.json') if (L.WORK / 'resume_offset_check.json').exists() else {}
    if rc.get('candidate_ain') != after['NightRemaster.ain'] or rc.get('problems') != [] or not rc.get('stats', {}).get('resume_saves'):
        issues.append('saved-stack check missing, failing or for another candidate (run work/resume_offset_check.py)')
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
        issues.append('evidence/calendar_overview_20261018 already exists: inspect the earlier transaction')
    running = active_target(processes(), rt)
    rec = Path(keep['recovery_runtime'])
    report = dict(status=READY if not issues else 'NOT_READY', candidate=after, runtime=str(rt), base=base, issues=issues,
                  game_running=bool(running), contracts_now=len(contracts_now()), recovery_runtime=str(rec),
                  recovery_has=sorted(recovery_hashes(rec, FILES)), install_command=f'python "{Path(__file__)}" --install',
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
    elif '--stage' in sys.argv:
        print(stage())
    elif '--scan' in sys.argv:
        print(scan())
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
