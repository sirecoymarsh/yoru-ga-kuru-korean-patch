"""Claude Opus 5.5 (2026-10-15): install / restore of the auto-nav candidate (오토 내비게이션; design 설계.md, spoilers inside),
after publish_feeling_r23.py (same journaled transaction, same KRMenu scratch rule).

  python publish_autonav.py --stage      put the PACT candidate (pact/NightRemasterPact.afa) into candidate/ and record it in
                                         candidate/manifest.json (rerun after every build_autonav.py run)
  python publish_autonav.py --scan       Defender custom scan of a copy of the payload (scan_autonav.ps1) -> work/scan_report.json
  python publish_autonav.py --contract   write the Codex contract draft autonav_20261015/required_autonav_20261015.json
  python publish_autonav.py --fixture    transaction fixture on disposable files under autonav_20261015/work (no runtime)
  python publish_autonav.py --verify     read-only readiness check (hashes, VM + self-test, native probes, scan, fixture, contracts)
  python publish_autonav.py --install    INSTALL (only with the user's permission, Codex stopped, game closed)
  python publish_autonav.py --restore    undo an install exactly (journal-driven, resumable, idempotent)

Payload: NightRemaster.ain + NightRemasterPact.afa (entry 185 Asra/Mods only: the 오토 내비게이션 row). EX/FNL, the Manual chart
and winmm.dll untouched. One journaled transaction: PREPARED (evidence/autonav_20261015: before/candidate copies, metadata
snapshots) -> atomic hash-checked replacement (new files; hard links are broken, never written through) -> runtime manifest +
current.json + every required_*.json present at install time (autonav_20261015_preserved_by; their required_files rows follow)
+ new required_autonav_20261015.json + latest_worked_translation.json + progress.md note -> exact tree (KRMenu\\ excluded) / saves
/ recovery runtime re-checked -> COMMITTED. Any failure rolls back files and metadata; --restore returns the exact pre-install
state. Nothing is written to the runtime, the save folder or the Codex root except by --install / --restore.
"""
from pathlib import Path
import copy, datetime, hashlib, json, os, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import anlib as L

R = L.CODEX
O = HERE / 'candidate'
E = R / 'evidence' / 'autonav_20261015'                 # created only by --install
PTR = L.CURRENT
FILES = ['NightRemaster.ain', 'NightRemasterPact.afa']
PACT_SRC = HERE / 'pact' / 'NightRemasterPact.afa'
NEW = 'required_autonav_20261015.json'
DRAFT = HERE / NEW
STATUS = 'AUTONAV_20261015_INSTALLED_NATIVE_PASS'
READY = 'AUTONAV_20261015_STATIC_VM_NATIVE_PASS_NOT_INSTALLED'
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
# new in this layer: functions that sit on saved stacks when the player saves while a choice / the partner confirm / the
# new-game question is open (system menu): later builds keep their index, address and every code byte
PINNED_NEW = (['KR_AN_E%05d' % e for e in EVENTS] + ['KR_ANSelect', 'KR_ANSelFrame', 'KR_ANTrainConfirm', 'KR_ANOpeningQ', 'KR_ANNewGame'])
NO_RESTORE = ('Codex must never run publish_autonav*.py --restore or otherwise remove the auto navigation (KR_AN* functions, its 27 '
              'same-length operands - the 19 choice events call KR_AN_E<no> where they called ■選択メッセージ／実行, '
              'C_SelectMessage@CreateParts calls KR_ANInfoCreate where it called C_SelectMessInfo@CreateParts, C_SelectMessage@Update '
              'calls KR_ANSelFrame where it called ■バックログ起動監視, C_SceneTraining@_UpdateInputPartner calls KR_ANTrainFrame where it '
              'called C_UserInputManager::IsClickCancelOtherMouse, C_SceneTraining@RunSelectPartner calls KR_ANTrainConfirm where it called '
              '■選択ダイアログ／実行, L_EventCall::Check asks KR_ANDateGet where it asked C_GameFlags@Date::get (first of two), '
              'C_SceneGame@Run asks KR_ANOpeningQ where it asked C_GameFlags@IsPlayOpening::get, C_ConfigView@EventConfAsraDataForParts '
              '/ EventConfPartsDataForAsra call KR_ANCfgSeenToParts / KR_ANCfgSeenToAsra at their last existence check - and the seven '
              'KR_Nav* parts of PACT entry 185 Asra/Mods). It is a permanent user-requested feature: when a rebuild needs a clean base, '
              'rebase on the runtime that current.json points to and carry the auto navigation forward; restore is reserved for the '
              'user\'s explicit request.')
NO_RESTORE_KO = ('Codex 는 publish_autonav*.py --restore 를 실행하거나 오토 내비게이션(KR_AN* 함수, 같은 길이 피연산자 27곳 — 선택지 이벤트 19곳의 '
                 '■選択メッセージ／実行 → KR_AN_E<번호>, C_SelectMessage@CreateParts 의 C_SelectMessInfo@CreateParts → KR_ANInfoCreate, '
                 'C_SelectMessage@Update 의 ■バックログ起動監視 → KR_ANSelFrame, C_SceneTraining@_UpdateInputPartner 의 '
                 'IsClickCancelOtherMouse → KR_ANTrainFrame, C_SceneTraining@RunSelectPartner 의 ■選択ダイアログ／実行 → KR_ANTrainConfirm, '
                 'L_EventCall::Check 의 첫 C_GameFlags@Date::get → KR_ANDateGet, C_SceneGame@Run 의 IsPlayOpening::get → KR_ANOpeningQ, '
                 '옵션 동기화 두 함수의 마지막 존재 확인 → KR_ANCfgSeenToParts / KR_ANCfgSeenToAsra — 와 PACT 185 Asra/Mods 의 KR_Nav* '
                 '부품 7개)을 지우지 않는다. 사용자가 요청한 영구 기능이다: 깨끗한 기준이 필요하면 current.json 이 가리키는 실행본 위에서 '
                 '다시 만들고 이어 싣는다. 되돌리기는 사용자가 명시적으로 요청할 때만 한다.')
INSTRUCTION = (
    'Claude auto navigation (2026-10-15, user request: a chosen heroine\'s route; the choice for her shimmers and is picked after 20 s). '
    + NO_RESTORE + ' Payload: NightRemaster.ain + NightRemasterPact.afa (entry 185 only). KR_AN* functions appended; no original '
    'function relocated; no new global / struct member; the per-save target is one name KR_AUTONAV_<2..5> in '
    'N_ScenarioRegister::detail::_EV_TABLE (set and cleared with N_ScenarioRegister::SetEventFlag, never LEventFlag::Set), session '
    'variables YoruKR.AN.* (not in saves). The options\' Mods page shows five radio boxes (KR_NavOff, KR_NavIzumi, KR_NavKyouka, '
    'KR_NavManami, KR_NavMakoto), locked and empty outside a game (no C_SceneGame@Run on the stack). The affinity top-up '
    '(KR_ANTopUp) raises only the chosen heroine and only up to what that day needs (the per-day table KR_ANNeed comes from '
    'graph/schedule.json; the numbers are in 설계.md under its spoiler warning - the user is playing, keep them out of chat and '
    'notes); calendar / chart / recollection replays are left alone (KR_F28Replay, '
    'Ａ＿回想モード実行中確認). Pinned for every later build (index, address and every code byte): ' + ', '.join(PINNED_NEW) +
    ' - they are on saved stacks when the player saves with a choice, the partner confirm or the new-game question open. ' +
    KRMENU_RULE + ' Every earlier contract stays in force.')


def js(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + '.autonav-', suffix='.tmp', delete=False) as f:
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
    tmp = dest.with_name(dest.name + '.autonav-copy.tmp')
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
        tmp = live / (n + '.autonav-copy.tmp')
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
    want = L.sha(PACT_SRC)
    pe = read(HERE / 'pact' / 'build_evidence.json')
    arc = pe['archive']
    assert arc['source_sha256'] == man['base']['pact_sha256'], 'the PACT row was built on another PACT than the AIN base'
    assert arc['candidate_sha256'] == want == pe['outputs']['NightRemasterPact.afa'], 'pact/NightRemasterPact.afa is not the one the evidence describes'
    assert pe['changed_entries'] == [185] and arc['replaced_ids'] == [185] and not arc['appended'], 'more than entry 185 changed'
    assert pe['round_trip_exact'] and pe['inverse_exact'] and pe['alice_ar_extract_all_entries']['differing'] == ['Asra/Mods.pactex']
    dest = O / 'NightRemasterPact.afa'
    if not dest.exists() or L.sha(dest) != want:
        shutil.copy2(PACT_SRC, dest)
    assert L.sha(dest) == want
    man['files']['NightRemasterPact.afa'] = dict(sha256=want, size=dest.stat().st_size, built_by='pact/build_pact_autonav.py',
                                                 source_sha256=arc['source_sha256'], changed_entries=[185],
                                                 evidence_sha256=L.sha(HERE / 'pact' / 'build_evidence.json'),
                                                 note='entry 185 Asra/Mods: the 오토 내비게이션 row (KR_Nav* parts)')
    man['pact_changed'] = True
    put(O / 'manifest.json', js(man))
    return {n: man['files'][n]['sha256'] for n in FILES}


def scan():
    target = L.WORK / ('scan_payload_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    out = L.WORK / 'scan_report.json'
    p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(HERE / 'scan_autonav.ps1'),
                        '-Candidate', str(O), '-Target', str(target), '-Out', str(out)], capture_output=True, timeout=900, env=L.env())
    print(p.stdout.decode('utf-8', 'replace')[-2000:], p.stderr.decode('utf-8', 'replace')[-2000:])
    assert p.returncode == 0, 'scan failed'
    return read(out)


# ------------------------------------------------------------------ evidence checks
def probe_home_ok(p):
    lg = p.get('log') or []
    text = '\n'.join(lg)
    return bool(p.get('exit_code') == 0 and lg and lg[-1] == 'END' and p.get('user_save_folder_unchanged') and not p.get('vm_error')
                and not p.get('message') and not p.get('events') and not p.get('timeout')
                and 'AUTO PICK 1 after' in text and 'AUTO PICK 2 after' in text and 'MANUAL PICK 1' in text
                and 'fn=E00805' in text and 'fn=E00806' in text and 'NEWGAME RETURNED target=4' in text
                and 'CONFIG page act=Asra\\Mods mods=1 ingame=1' in text
                and 'CFG BEFORE target=4 boxes=0/1 0/1 0/1 1/1 0/1' in text and 'CFG AFTER_MAKOTO target=5 boxes=0/1 0/1 0/1 0/1 1/1' in text
                and 'CFG AFTER_RECLICK target=5 boxes=0/1 0/1 0/1 0/1 1/1' in text and 'CFG AFTER_OFF target=0 boxes=1/1 0/1 0/1 0/1 0/1' in text
                and any(x.startswith('ROW n=2 ') and 'glow=2026101503:p' in x for x in lg)
                and any(x.startswith('ROW n=0 ') and 'glow=2026101503:none' in x for x in lg))


def probe_train_ok(p):
    lg = p.get('log') or []
    text = '\n'.join(lg)
    return bool(p.get('exit_code') == 0 and lg and lg[-1] == 'END' and p.get('user_save_folder_unchanged') and not p.get('vm_error')
                and not p.get('message') and not p.get('events') and not p.get('timeout')
                and 'AUTO PARTNER ' in text and 'AFTER CONFIRM trfired=2 trcg=0' in text and any(x.startswith('TRAIN cg=') and ':mul255,' in x for x in lg))


def draft_contract():
    man = read(O / 'manifest.json')
    after = {n: man['files'][n]['sha256'] for n in FILES}
    vf = read(L.EVID / 'verify.json')
    home = read(L.EVID / 'probe_home.json')
    train = read(L.EVID / 'probe_train.json')
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
    pinned_new = {}
    for name in PINNED_NEW:
        fid = ids[name]
        pinned_new[name] = dict(index=fid, address=nm['functions'][fid]['address'])
    prev = {}
    for n in contracts_now():
        c = read(R / n)
        prev[n] = dict(sha256=L.sha(R / n), status=c.get('status'), instruction_present=bool(c.get('instruction')))
    return dict(
        status='AUTONAV_20261015_DRAFT_NOT_INSTALLED', author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(),
        base=man['base'], required_files=after, candidate_manifest_sha256=L.sha(O / 'manifest.json'), pact_changed=True,
        pact_changed_entries=[185], ex_changed=False, fnl_changed=False, chart_changed=False, hook_changed=False,
        no_restore_rule=NO_RESTORE, added_functions=len(ids), added_function_names=sorted(ids), jam_bodies=man['jam_bodies'],
        same_length_sites=man['same_length_sites'], relocated_original_functions=[], pinned_addresses=pinned,
        pinned_from_now_on=pinned_new,
        saved_stacks=dict(resume_saves=rc['stats']['resume_saves'], frames=rc['stats']['frames'],
                          frames_in_changed_functions=rc['stats']['frames_in_changed_functions'], problems=len(rc['problems']),
                          changed_functions_on_stacks=sorted({h['fn'] for h in rc['frames_in_changed_functions']}),
                          saved_with_a_choice_open=[dict(save=h['save'], event=h['fn'], resumes_after_swapped_call_bytes=h['to_sites'])
                                                    for h in rc['frames_in_changed_functions'] if h['fn'].startswith('ＥＶ')],
                          check=str(L.WORK / 'resume_offset_check.json'), check_sha256=L.sha(L.WORK / 'resume_offset_check.json'),
                          note='read-only check of the user\'s saves (work/resume_offset_check.py): every saved frame keeps its crc (the '
                               'AIN function table is unchanged), no original function moved, no frame resumes at or inside a swapped '
                               'instruction; a save made with a choice open resumes inside the original ■選択メッセージ／実行 (its event '
                               'frame resumes right after the swapped call) and shows that one choice without the shimmer'),
        storage=man['data']['storage'], session_variables=man['data']['session_variables'],
        verification=dict(vm=vf['counts'], selftest=vf.get('selftest'), probe_home=dict(passed=probe_home_ok(home), seconds=home.get('seconds'),
                                                                                       save=home.get('save'), shots=[Path(x).name for x in home.get('shots', [])]),
                          probe_train=dict(passed=probe_train_ok(train), seconds=train.get('seconds'), save=train.get('save'),
                                           shots=[Path(x).name for x in train.get('shots', [])]),
                          defender=scan_.get('status'), transaction_fixture=fx['status'] if fx else 'NOT_RUN'),
        preserves_contracts=prev, preserves_contracts_count=len(prev), preserved_by_key='autonav_20261015_preserved_by',
        instruction=INSTRUCTION, translator_model=L.AUTHOR)


# ------------------------------------------------------------------ the transaction (real paths or a disposable project)
class Ctx:
    def __init__(self, root, evidence, pointer, candidate, files, saves, stop_check, sources=None, note_title=None):
        self.root, self.evidence, self.pointer, self.candidate, self.files, self.saves = root, evidence, pointer, candidate, files, saves
        self.stop_check = stop_check
        self.sources = sources
        self.note_title = note_title or '오토 내비게이션 설치 (Claude Opus 5.5; claude_text_20261001 설치본 위)'


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
        for n in ['verify.json', 'probe_home.json', 'probe_train.json']:
            shutil.copy2(L.EVID / n, ev / 'source' / n)
        for n in ['scan_report.json', 'transaction_verification.json', 'resume_offset_check.json', 'build/native_opcode_audit.json']:
            if (L.WORK / n).exists():
                shutil.copy2(L.WORK / n, ev / 'source' / Path(n).name)
        (ev / 'source' / 'pact').mkdir()
        for f in (ctx.sources / 'pact').iterdir():
            if f.is_file() and f.suffix in ('.py', '.json', '.png'):
                shutil.copy2(f, ev / 'source' / 'pact' / f.name)
    shutil.copy2(cand / 'manifest.json', ev / 'source' / 'manifest.json')
    latest = read(root / 'latest_worked_translation.json')
    assert latest['manifest_sha256'] == cur['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    full = read(Path(latest['translation_map']))
    sequence = full['target_text_sequence_sha256']
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full['autonav_20261015_overlay'] = dict(evidence=str(ev), semantic_dialogue_changes=0, MSG1_exact=True, translator_model=L.AUTHOR)
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
        nm.update(status=STATUS, time=now, autonav_20261015_revision=rev)
        if isinstance(nm.get('ain'), dict):
            nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], autonav_20261015_overlay=str(ev / 'source' / 'manifest.json'))
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = ('User screen check: 오토 내비게이션 — 새 게임 시작 때 대상 고르기 창; 옵션 → 모드 탭의 「오토 내비게이션」 다섯 칸(게임 중에만); '
                      '선택지가 뜨면 고른 인물 쪽 답이 금빛으로 반짝이고 20초 뒤 자동으로 골라짐(직접 골라도 됨); 이야기가 있는 토요일엔 특훈 상대 '
                      '화면에서 대상 초상이 반짝이고 20초 뒤 자동 선택 · 확인.')
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
            c['autonav_20261015_preserved_by'] = str(ev)
            write(root / n, js(c))
        if fail_at == 'after_contracts':
            raise RuntimeError('fixture: injected failure after the contracts')
        final = dict(draft, status=STATUS, time=now, manifest=str(mp), manifest_sha256=mh, required_files=after, evidence=str(ev),
                     preserves_contracts=sorted(contracts))
        write(root / NEW, js(final))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh, autonav_20261015_revision=rev)
        write(ptr_path, js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation), autonav_20261015_evidence=str(ev))
        write(root / 'latest_worked_translation.json', js(latest))
        note = (f"\n\n### {now} {ctx.note_title}\n"
                "- 오토 내비게이션(사용자 요청 10-15): 새 게임 시작 때 대상(이즈미 · 쿄카 · 마나미 · 마코토 · 쓰지 않음)을 고르고 옵션 「모드」 탭에서 "
                "바꾼다(세이브마다, 게임 중에만). 대사 선택지 19곳에서 대상 쪽 답 줄이 금빛으로 반짝이고 20초 뒤 자동 선택(직접 고르면 그 답). "
                "대상의 특훈 뒤 이야기가 있는 토요일에만 특훈 상대 화면에서 대상 초상이 반짝이고 20초 뒤 자동 선택 · 확인. 대상의 친밀도가 그날 "
                "조건에 못 미칠 때만 채운다(원래 규칙 밖 보정, 대상만). 회상 · 달력 · 차트 재생에서는 동작하지 않는다.\n"
                "- AIN + PACT(185 Asra/Mods 만), 원본 함수 이전 0, 같은 길이 피연산자 27곳, 새 전역 · 구조체 필드 0, 저장 이름 KR_AUTONAV_<2..5>"
                "(N_ScenarioRegister 표), 세션 변수 YoruKR.AN.*. 이후 빌드는 " + ', '.join(PINNED_NEW[:3]) + " 등 "
                + str(len(PINNED_NEW)) + "개 함수의 주소 · 바이트를 유지할 것(선택지 · 특훈 확인 · 새 게임 창이 열린 채 저장한 세이브의 스택).\n"
                "- " + KRMENU_RULE_KO + "\n"
                "- " + NO_RESTORE_KO + "\n"
                f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}; manifest {mh}; evidence {ev}; 되돌리기(사용자 요청 때만) "
                "publish_autonav.py --restore.\n")
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
    os.unlink(l / FILES[1])
    shared = f / 'shared_copy.afa'
    shutil.copy2(b / FILES[1], shared)
    os.link(shared, l / FILES[1])
    pair_apply(s, b, l, before, after)
    assert L.sha(shared) == before[FILES[1]], 'the swap wrote through a hard link'
    pair_restore(b, l, before, after)
    for installed in [False, True]:
        if installed:
            pair_apply(s, b, l, before, after)
        for n in FILES:
            (l / (n + '.autonav-copy.tmp')).write_bytes(b'partial interrupted copy')
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
    ctx = Ctx(root, root / 'evidence' / 'autonav_20261015', ptr, cand, payload_files, saves, lambda rt_: True, sources=None, note_title='fixture')
    return ctx, rt, rec


def install_fixture(f):
    out = {}
    ctx, rt, rec = fake_project(f, 'proj_pact_missing_in_recovery', FILES, recovery_has={'NightRemaster.ain'})
    tree0 = snapshot_folder(ctx.root)
    rep = transact(ctx)
    j = read(ctx.evidence / 'journal.json')
    assert j['status'] == 'COMMITTED' and rep['recovery_lacks'] == ['NightRemasterPact.afa'] and rep['recovery_hashed'] == ['NightRemaster.ain']
    assert all(L.sha(rt / n) == L.sha(ctx.candidate / n) for n in FILES)
    c = read(ctx.root / 'required_example_a.json')
    assert c['required_files']['NightRemaster.ain'] == L.sha(ctx.candidate / 'NightRemaster.ain') and c['autonav_20261015_preserved_by'] == str(ctx.evidence)
    assert read(ctx.pointer)['status'] == STATUS and (ctx.root / NEW).exists()
    restore_ctx(ctx, runtime_override=rt)
    restore_ctx(ctx, runtime_override=rt)
    tree1 = snapshot_folder(ctx.root)
    changed = sorted(k for k in set(tree0) | set(tree1) if tree0.get(k) != tree1.get(k) and not k.startswith('evidence/autonav_20261015/'))
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
        diff = sorted(k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k) and not k.startswith('evidence/autonav_20261015/')
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
    if 'NightRemasterPact.afa' not in man['files']:
        return False, dict(status='NOT_READY', issues=['the PACT is not staged into candidate/ (run --stage)'])
    after = {n: man['files'][n]['sha256'] for n in FILES}
    cur = read(PTR)
    rt = Path(cur['runtime']).resolve()
    if any(L.sha(O / n) != after[n] for n in FILES):
        issues.append('candidate files differ from their manifest')
    if L.sha(PACT_SRC) != after['NightRemasterPact.afa']:
        issues.append('pact/NightRemasterPact.afa differs from the staged PACT: rerun --stage')
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
    vf = read(L.EVID / 'verify.json') if (L.EVID / 'verify.json').exists() else {}
    c = vf.get('counts', {})
    if vf.get('candidate') != after['NightRemaster.ain']:
        issues.append('VM verification (verify_autonav.py --selftest) is for another candidate')
    elif c.get('A1') != 76 or c.get('A4') != 76 or c.get('A8', 0) < 7000 or c.get('A9', 0) < 27 or c.get('S1') != 27 or c.get('A7', 0) < 8:
        issues.append('VM checks incomplete')
    elif (vf.get('selftest') or {}).get('planted') != DEFECTS or (vf.get('selftest') or {}).get('caught') != DEFECTS:
        issues.append('planted-defect self-test missing or failing (%d expected)' % DEFECTS)
    home = read(L.EVID / 'probe_home.json') if (L.EVID / 'probe_home.json').exists() else {}
    train = read(L.EVID / 'probe_train.json') if (L.EVID / 'probe_train.json').exists() else {}
    for label, p, ok in (('home', home, probe_home_ok), ('train', train, probe_train_ok)):
        if p.get('candidate_ain') != after['NightRemaster.ain'] or p.get('candidate_pact') != after['NightRemasterPact.afa'] or not ok(p):
            issues.append('native probe %s missing, failing or for another candidate' % label)
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
        issues.append('evidence/autonav_20261015 already exists: inspect the earlier transaction')
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
