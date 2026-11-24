"""Install the approved recommendation mod as a hash-bound, reversible data pair."""
from pathlib import Path
import copy, datetime, hashlib, shutil, sys
import publish_dungeon_sweep_20260916 as prior
import publish_cheat_menu_20260915 as p

W = Path(__file__).resolve().parent
R = p.R
O = R / 'staging/autoequip_20260917'
E = R / 'evidence/autoequip_20260917'
CONTRACTS = prior.CONTRACTS + [
    'required_dungeon_sweep.json', 'required_sweep_infinite_fix.json',
    'required_sweep_ui_fix.json', 'required_route_linear_fix.json',
    'required_route_puzzle_guide.json',
]
NEW = 'required_autoequip.json'
STATUS = 'AUTOEQUIP_STATIC_PASS_NATIVE_PENDING'
p.O = O
p.E = E
p.FILES = ['NightRemaster.ain', 'NightRemasterPact.afa']


def main():
    ev = p.read(O / 'build_evidence.json')
    after, before = ev['files'], ev['source_files']
    for name, status in [
        ('verification.json', 'COMPILED_FIXTURES_PASS'),
        ('release_checks.json', 'RELEASE_STATIC_PASS'),
        ('independent_review.json', 'STATIC_REVIEW_PASS'),
        ('scan_report.json', 'SCANNED_NO_TARGET_DETECTIONS'),
    ]:
        check = p.read(O / name)
        assert check['status'] == status and check['files'] == after, name
    assert set(after) == set(before) == set(p.FILES)
    assert all(p.sha(O / n) == after[n] for n in p.FILES)
    ptr = R / 'ui_cumulative/current.json'
    current = p.read(ptr)
    if E.exists():
        j = p.read(E / 'journal.json')
        assert j['status'] == 'COMMITTED' and p.sha(ptr) == j['committed_pointer_sha256']
        assert all(p.sha(p.RT / n) == after[n] for n in p.FILES)
        print('ALREADY_INSTALLED')
        return
    assert current == ev['source_pointer']
    mp = Path(current['manifest'])
    assert p.sha(mp) == current['manifest_sha256']
    manifest = p.read(mp)
    rt = Path(current['runtime']).resolve()
    assert rt == p.RT.resolve()
    if not p.stopped(rt):
        print('READY_WAITING_FOR_GAME_EXIT')
        return
    fixture = p.fixture()
    p.exact_tree(rt, manifest['files'])
    assert len(manifest['files']) == 98
    assert all(p.sha(rt / n) == h for n, h in before.items())
    assert all(p.sha(rt / n) == h for n, h in ev['unchanged_files'].items())
    keep = p.read(R / 'required_build_retention.json')
    rm, recovery = Path(keep['recovery_manifest']), Path(keep['recovery_runtime'])
    assert p.sha(rm) == keep['recovery_manifest_sha256']
    rh = {n: p.sha(recovery / n) for n in p.FILES}
    saves = p.snapshot_saves()
    paths = [mp, ptr, R / 'progress.md'] + [R / n for n in CONTRACTS + [NEW]]
    snapshots = {x: x.read_bytes() if x.exists() else None for x in paths}
    assert snapshots[R / NEW] is None
    for name in CONTRACTS:
        contract = p.read(R / name)
        for key in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
            if key in contract:
                assert contract[key] == current['manifest_sha256'], name
    E.mkdir(parents=True)
    assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for name in ['before', 'candidate', 'source']:
        (E / name).mkdir()
    metadata = []
    for path, data in snapshots.items():
        if data is not None:
            p.put(E / 'before' / path.name, data)
        metadata.append(dict(path=str(path), name=path.name, existed=data is not None,
                             sha256=p.sha(path) if data is not None else None))
    for name in p.FILES:
        shutil.copy2(rt / name, E / 'before' / name)
        shutil.copy2(O / name, E / 'candidate' / name)
        assert p.sha(E / 'before' / name) == before[name]
        assert p.sha(E / 'candidate' / name) == after[name]
    for f in O.iterdir():
        if f.is_file() and f.suffix in ['.json', '.jam', '.pactex', '.jaf'] and f.name != 'native_raw_code.jam':
            shutil.copy2(f, E / 'source' / f.name)
    for name in [
        'build_autoequip_20260917.py', 'autoequip_helpers_20260917.jaf',
        'verify_autoequip_20260917.py', 'check_autoequip_release_20260917.py',
        'publish_autoequip_20260917.py', 'scan_autoequip_20260917.ps1',
        'publish_dungeon_sweep_20260916.py', 'publish_loot_notice_20260915.py',
        'publish_cheat_menu_20260915.py', 'publish_remaster_multiplier_20260915.py',
        'audit_sys43_native_opcodes_20260915.py',
    ]:
        shutil.copy2(W / name, E / 'source' / name)
    p.put(E / 'save_hashes_before.json', p.js(saves))
    j = dict(status='PREPARED', runtime=str(rt), before=before, after=after,
             metadata=metadata, fixture=fixture)
    p.put(E / 'journal.json', p.js(j))

    def write(path, data):
        assert path in snapshots
        j.setdefault('metadata_after', {})[str(path)] = hashlib.sha256(data).hexdigest()
        p.put(E / 'journal.json', p.js(j))
        p.put(path, data)

    attempted = False
    try:
        assert p.stopped(rt) and p.read(ptr) == current and p.sha(mp) == current['manifest_sha256']
        attempted = True
        p.pair_apply(E / 'candidate', E / 'before', rt, before, after)
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, files=after, source_files=before,
                   evidence=str(E), previous_manifest_sha256=current['manifest_sha256'],
                   AIN=ev['AIN'], PACT=ev['PACT'], native_gameplay_verified=False,
                   save_schema_unchanged=True, translator_model='Codex internal')
        updated = copy.deepcopy(manifest)
        updated.update(status=STATUS, time=now, runtime_verified=False, autoequip_revision=rev)
        updated['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'],
                              autoequip_overlay=str(E / 'source/build_evidence.json'))
        for row in updated['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        updated['next'] = ('Native check: Mods > 자동 장착·요소석 추천 (default OFF); equipment and crafting buttons; '
                           'four profiles, locked slots, preview/cancel, native craft confirm/cost/inventory, '
                           'save/reload and responsiveness. Compiled fixtures are not native gameplay evidence.')
        write(mp, p.js(updated))
        mh = p.sha(mp)
        for name in CONTRACTS:
            path = R / name
            contract = p.read(path)
            for key in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if key in contract:
                    contract[key] = mh
            for file, h in after.items():
                if file in contract.get('required_files', {}):
                    contract['required_files'][file] = h
            contract['autoequip_overlay'] = str(E / 'source/build_evidence.json')
            write(path, p.js(contract))
        instruction = ('Flag83 tag20260917 default OFF, native enum/consumers audited. Button-triggered only. '
                       'Balanced/attack/survival/utility heuristic profiles, operation-local slot locks and preview. '
                       'Never steal other characters equipment, purchase or synthesize. Deep private candidate copies; '
                       'native equip setter with controlled rollback; original craft validation and confirmation; '
                       'partial stone reservation restored on cancel, native99 cap. Tutorial excluded. '
                       'No new serialized globals/structs. Preserve all earlier translations, graphics and mods. '
                       'Native gameplay/UI/performance/save-load still pending.')
        write(R / NEW, p.js(dict(rev, manifest=str(mp), manifest_sha256=mh,
                               required_files=after, instruction=instruction)))
        write(ptr, p.js(dict(current, status=STATUS, manifest_sha256=mh, runtime_verified=False)))
        note = (f'\n\n### {now} 장비·요소석 추천 — 적용, 실제 게임 검증 대기\n'
                '- 모드 탭 자동 장착·요소석 추천(default OFF), 장비/무기 가공 화면 버튼. 균형·공격·생존·유틸리티 4기준, 슬롯 유지, 미리보기 후 확인.\n'
                '- 유틸리티: 함정 해제·감지, 휴식/보행 회복, 보물 탐색 등 원작 스킬 기준. 함정 즉시 해제·경로 모드와 중복되는 효용은 감점. 전역 최적해가 아닌 제한된 추천.\n'
                '- 다른 캐릭터 장비·구매·합성 사용 안 함. 취소 시 재고/장비 보존. 요소석은 원작 가공 확인창으로 연결, 비용/능력/99개 한도/부분 예약 검증.\n'
                '- 최종 pair compiled fixtures, 기존 콜백17개, PACT 3entry, FNL 글리프·중앙정렬, opcode, 독립 검토, Defender 및 설치복구 fixture 통과. GUI/native craft boundaries는 모의 경계이며 실제 플레이 증거가 아님.\n'
                f'- 다른96개 runtime파일, {len(saves)}개 세이브, 복구용 빌드 보존. Evidence/rollback: {E}. Manifest {mh}.\n'
                '- 남음: 실제 버튼/4기준/유지 슬롯/취소/가공 확인/재고·비용/성능/세이브 재로드. 전 게임 한국어화 완료 주장 없음.\n')
        write(R / 'progress.md', snapshots[R / 'progress.md'] + note.encode('utf8'))
        p.exact_tree(rt, updated['files'])
        assert saves == p.snapshot_saves()
        assert p.sha(rm) == keep['recovery_manifest_sha256']
        assert rh == {n: p.sha(recovery / n) for n in p.FILES}
        assert len(list((R / 'ui_cumulative').glob('*/runtime'))) == 2
        j.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=p.sha(ptr))
        p.put(E / 'journal.json', p.js(j))
    except BaseException as error:
        errors = []
        if attempted:
            try:
                p.pair_restore(E / 'before', rt, before, after)
            except BaseException as failure:
                errors.append(repr(failure))
        for path, data in reversed(list(snapshots.items())):
            try:
                if data is not None:
                    p.put(path, data)
                elif path.exists():
                    path.unlink()
            except BaseException as failure:
                errors.append(repr(failure))
        j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',
                 error=repr(error), rollback_errors=errors)
        p.put(E / 'journal.json', p.js(j))
        raise
    report = dict(status=STATUS, runtime=str(rt), manifest_sha256=mh, files=after,
                  unchanged_other_runtime_files=96, save_files_hashes_unchanged=len(saves),
                  recovery_build_unchanged=True, native_gameplay_verified=False, evidence=str(E))
    p.put(E / 'publish_report.json', p.js(report))
    p.put(O / 'publish_report.json', p.js(report))
    print(p.js(report).decode('utf8'))


if __name__ == '__main__':
    if '--restore' in sys.argv:
        p.restore()
    elif '--fixture' in sys.argv:
        print(p.js(p.fixture()).decode('utf8'))
    else:
        main()
