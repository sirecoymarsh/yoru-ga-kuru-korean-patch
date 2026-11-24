"""Hash-bound two-file installation; journalled metadata and tested rollback."""
from pathlib import Path
from types import SimpleNamespace
import sys, copy, shutil, datetime, hashlib
sys.dont_write_bytecode = True
C = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0, str(C))
import r24lib as L
import publish_chart_r24 as P
R = L.CODEX
O = R/'staging/claude_fixes_20260928'
E = R/'evidence/claude_fixes_20260928'
HERE = Path(__file__).resolve().parent
FILES = ['NightRemaster.ain', 'winmm.dll']
NEW = R/'required_claude_fixes_20260928.json'
STATUS = 'CLAUDE_FIXES_20260928_INSTALLED_NATIVE_PASS'

def preflight():
    qa = L.readj(O/'verification.json')
    man = L.readj(O/'candidate/manifest.json')
    after = {n: L.sha(O/'candidate'/n) for n in FILES}
    before = {n: L.sha(O/'source'/n) for n in FILES}
    assert qa['status'] == 'STATIC_NATIVE_PASS' and qa['files'] == after
    assert after == {n: man['files'][n]['sha256'] for n in FILES}
    for path, status in [(O/'candidate/scan_report.json', 'SCANNED_NO_TARGET_DETECTIONS'),
                         (O/'evidence/transaction_verification.json', 'TRANSACTION_FIXTURE_PASS')]:
        result = L.readj(path)
        assert result['status'] == status and result.get('payload', result.get('files')) == after
    normal = L.readj(O/'evidence/normal_save/probe_chart_r24.json')['home']
    assert normal['candidate_sha256'] == after['NightRemaster.ain'] and normal['exit_code'] == 0
    assert not normal.get('vm_error') and not normal.get('message') and not normal['events']
    assert 'NORMAL SAVE 88 PRESENT' in normal['log'] and any(x.startswith('PASS normal native') for x in normal['log'])
    qa['ordinary_save_load_native'] = True
    qa['ordinary_save_load_evidence'] = str(O/'evidence/normal_save/probe_chart_r24.json')
    current = L.readj(L.CURRENT)
    assert current == L.readj(O/'source_pointer.json'), 'Live build changed since staging'
    rt, mp = Path(current['runtime']), Path(current['manifest'])
    assert L.sha(mp) == current['manifest_sha256'] and P.stopped(rt), 'Game running or manifest changed'
    manifest = L.readj(mp)
    P.exact_tree(rt, manifest['files'])
    assert all(L.sha(rt/n) == h for n, h in before.items())
    latest = L.readj(R/'latest_worked_translation.json')
    assert latest['manifest_sha256'] == current['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    return qa, man, after, before, current, rt, mp, manifest, latest

def main(check=False):
    qa, man, after, before, current, rt, mp, manifest, latest = preflight()
    if check:
        print('PREFLIGHT_PASS', after)
        return
    assert not E.exists() and not NEW.exists(), 'Inspect existing journal rather than overwriting'
    contracts = sorted(R.glob('required_*.json'))
    paths = [mp, L.CURRENT, R/'progress.md', R/'latest_worked_translation.json', R/'ui_hangul_input_fix.json', NEW] + contracts
    assert len({x.name for x in paths}) == len(paths)
    snapshots = {x: x.read_bytes() if x.exists() else None for x in paths}
    for folder in ['before', 'candidate', 'source', 'screenshots']:
        (E/folder).mkdir(parents=True)
    metadata = []
    for path, data in snapshots.items():
        if data is not None:
            P.put(E/'before'/path.name, data)
        metadata.append(dict(path=str(path), name=path.name, existed=data is not None,
                             sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    for n in FILES:
        shutil.copy2(rt/n, E/'before'/n)
        shutil.copy2(O/'candidate'/n, E/'candidate'/n)
    for n in ['source_pointer.json', 'source_hashes.json']:
        shutil.copy2(O/n, E/'source'/n)
    for name, path in {
        'candidate_manifest.json': O/'candidate/manifest.json',
        'scan_report.json': O/'candidate/scan_report.json',
        'r24_manifest.json': C/'candidate/manifest.json',
        'save_frames.json': O/'evidence/save_frames.json',
        'transaction_verification.json': O/'evidence/transaction_verification.json',
        'chart_native.json': O/'evidence/probe_chart_r24.json',
        'replay_safety.json': O/'evidence/replay_safety.json',
        'replay_state_comparison.json': O/'evidence/replay_state_comparison.json',
        'normal_save_native.json': O/'evidence/normal_save/probe_chart_r24.json',
        'startup_recovery_native.json': O/'evidence/startup_wrapper/result.json',
        'maintenance_summary.json': O/'evidence/maintenance/summary.json',
        'maintenance_reset.json': O/'evidence/maintenance/reset.json',
        'maintenance_restore.json': O/'evidence/maintenance/restore.json',
    }.items():
        shutil.copy2(path, E/'source'/name)
    P.put(E/'source/verification.json', P.js(qa))
    P.put(O/'verification.json', P.js(qa))
    for path in HERE.glob('*20260928.*'):
        if path.name.endswith(('.py', '.jaf', '.h', '.cpp', '.ps1')) and any(s in path.name for s in ['claude_fixes', 'maintenance', 'replay_safety', 'normal_save']):
            shutil.copy2(path, E/'source'/path.name)
    shutil.copytree(O/'hook', E/'source/hook', ignore=shutil.ignore_patterns('*.dll', '*.obj', '*.lib', '*.exp', '*.exe'))
    for img in (O/'evidence/probe').glob('*.png'):
        shutil.copy2(img, E/'screenshots'/img.name)
    saves = P.snapshot_folder(L.SAVES)
    menu = P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None
    P.put(E/'save_hashes_before.json', P.js(saves))
    P.put(E/'menu_hashes_before.json', P.js(menu))
    full = L.readj(Path(latest['translation_map']))
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full['claude_fixes_20260928'] = dict(evidence=str(E), semantic_dialogue_changes=0, translator_model='Codex internal')
    translation = E/'source/installed_translation_map.json'
    P.put(translation, P.js(full))
    j = dict(status='PREPARED', runtime=str(rt), files=FILES, before=before, after=after, metadata=metadata)
    P.put(E/'journal.json', P.js(j))
    def write(path, data):
        assert path in snapshots
        j.setdefault('metadata_after', {})[str(path)] = hashlib.sha256(data).hexdigest()
        P.put(E/'journal.json', P.js(j))
        P.put(path, data)
    attempted = False
    try:
        assert P.stopped(rt) and L.readj(L.CURRENT) == current and P.snapshot_folder(L.SAVES) == saves
        assert all((path.read_bytes() if path.exists() else None) == data for path, data in snapshots.items())
        attempted = True
        P.pair_apply(E/'candidate', E/'before', rt, before, after, files=FILES)
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, files=after, source_files=before, evidence=str(E),
                   claude_r24_source_sha256=man['base'], existing_saves_checked=qa['existing_resume_saves'],
                   saved_frames_checked=qa['saved_return_frames'], schema_changes=0, translator_model='Codex internal',
                   limitations=qa['limitations'])
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now, claude_fixes_20260928_revision=rev)
        nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], claude_fixes=str(E/'source/candidate_manifest.json'))
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt/row['path']).stat().st_size)
        nm['next'] = 'User continuous-play check remains. Replay saves are blocked; unsafe legacy replay saves return to title. Ordinary saves are preserved. r24 chart is integrated with native home-layer repair.'
        write(mp, P.js(nm))
        mh = L.sha(mp)
        for path in contracts:
            co = L.readj(path)
            for key in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if key in co:
                    co[key] = mh
            for n, h in after.items():
                if n in co.get('required_files', {}):
                    co['required_files'][n] = h
            co['claude_fixes_20260928_preserved_by'] = str(E)
            if 'calendar' in path.name or 'chart' in path.name:
                co['active_replay_save_policy_20260928'] = 'New user saves during replay blocked; legacy replay user saves rejected before resumed events; internal sandbox snapshots still restore. Pinned sandbox bytes/addresses preserved.'
            write(path, P.js(co))
        write(NEW, P.js({**rev, 'manifest': str(mp), 'manifest_sha256': mh, 'required_files': after,
            'added_functions': man['added_functions'], 'metadata_forwarders': qa['metadata_forwarders'],
            'same_length_sites': man['same_length_sites'], 'pinned_exact': man['pinned_exact'],
            'r24_contract': L.readj(C/'candidate/manifest.json'),
            'instruction': 'Preserve KR_C24* chart and KR_F28* replay/save/layer guards, the seven-file journalled native maintenance protocol, and all earlier contracts. Ordinary save schema, saved addresses and the six pinned frames are unchanged. Never enable replay-mid-save without self-contained snapshot support. Do not replace the latest native DLL with the older hook_modmenu build.',
            'verification': qa}))
        hook = L.readj(R/'ui_hangul_input_fix.json')
        hook['files']['winmm.dll'].update(source=str(E/'candidate/winmm.dll'), sha256=after['winmm.dll'],
            note='Same IME table and native mod menu; Codex journalled reset/restore. Source: '+str(E/'source/hook'))
        hook['maintenance_revision'] = rev
        write(R/'ui_hangul_input_fix.json', P.js(hook))
        nc = copy.deepcopy(current)
        nc.update(status=STATUS, manifest_sha256=mh, claude_fixes_20260928_revision=rev)
        write(L.CURRENT, P.js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation), claude_fixes_20260928_evidence=str(E))
        write(R/'latest_worked_translation.json', P.js(latest))
        note = f'\n\n### {now} Claude 인계 수정 F01–F04 완료 — Codex internal\n- F01/F04: 초기화·복원 7개 전역 기록을 SHA-256 검증·원복·중단 복구 트랜잭션으로 교체. 미완료 백업 제외. 복구 실패 시 혼합 상태로 시작하지 않음.\n- F02: 재생 중 저장/자동 저장/빠른 저장 차단, 과거 재생 도중 저장은 타이틀로 안전 복귀. 정상 저장·로드 및 달력/차트 재생의 원상복귀를 native 무음 사본에서 확인.\n- F03: r24 통합 및 본거지 차트 가림 해결. 재생 후 같은 페이지 복귀 확인.\n- 검증: 실패/강제 중단 338건, 실제 DLL 시작 복구, IME 2364행, {qa["existing_resume_saves"]}개 저장/{qa["saved_return_frames"]}개 복귀 주소 검사. 사용자 파일 {len(saves)}개 설치 전후 무변경.\n- 전체 915장면·엔딩의 재생 및 장시간 플레이는 이번 검증 범위 밖. 사용자 연속 플레이 확인이 다음 단계.\n- 최신 빌드 {rt}; 증거/백업 {E}; 복구 publish_claude_fixes_20260928.py --restore (해시 확인).\n'
        write(R/'progress.md', snapshots[R/'progress.md']+note.encode('utf8'))
        P.exact_tree(rt, nm['files'])
        assert P.snapshot_folder(L.SAVES) == saves
        assert (P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None) == menu
        for path in contracts+[NEW]:
            co = L.readj(path)
            for key in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if key in co:
                    assert co[key] == mh
        j.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=L.sha(L.CURRENT))
        P.put(E/'journal.json', P.js(j))
    except BaseException as error:
        failures = []
        if attempted:
            try:
                P.pair_restore(E/'before', rt, before, after, files=FILES)
            except BaseException as er:
                failures.append(repr(er))
        for path, data in reversed(list(snapshots.items())):
            try:
                if data is not None:
                    P.put(path, data)
                elif path.exists():
                    assert path == NEW
                    path.unlink()
            except BaseException as er:
                failures.append(repr(er))
        j.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK', error=repr(error), rollback_errors=failures)
        P.put(E/'journal.json', P.js(j))
        raise
    report = dict(status=STATUS, files=after, manifest_sha256=mh, runtime=str(rt),
                  user_save_files_unchanged=len(saves), prior_contracts_preserved=len(contracts), backup=str(E/'before'))
    P.put(E/'publish_report.json', P.js(report))
    P.put(O/'publish_report.json', P.js(report))
    readme = f'# Claude 인계 수정 설치 완료\n\n- 전역 기록 초기화·복원: 실패 원복과 중단 후 복구, 불완전 백업 제외.\n- 재생 중 저장 차단 및 과거 문제 저장의 타이틀 복귀. 일반 저장·불러오기 정상 확인.\n- r24 차트 통합, 본거지 가림 해결, 재생 후 같은 페이지 복귀.\n- 338개 실패/중단 조건과 무음 native 실행 검증 완료. 기존 사용자 저장 {len(saves)}개 파일 무변경.\n\n전체 이벤트·장시간 플레이까지 검증한 것은 아닙니다. 다음 확인은 실제 연속 플레이입니다.\n\n실행 폴더: `{rt}`\n\n설치 기록: `publish_report.json` / 복구 원본: `before` / 소스·검증: `source` / 화면: `screenshots`\n'
    P.put(E/'README.md', readme.encode('utf8'))
    print(P.js(report).decode())

if __name__ == '__main__':
    if '--restore' in sys.argv:
        P.restore_ctx(SimpleNamespace(root=R, evidence=E, pointer=L.CURRENT, stop_check=P.stopped))
    else:
        main('--check' in sys.argv)
