"""Install native-style mod dialogs and yellow labels as a reversible data pair."""
from pathlib import Path
import copy, datetime, hashlib, shutil, sys
import publish_autoequip_20260917 as prior
import publish_cheat_menu_20260915 as p

W = Path(__file__).resolve().parent
R = p.R
O = R / 'staging/mod_menu_style_20260917'
E = R / 'evidence/mod_menu_style_20260917'
CONTRACTS = prior.CONTRACTS + ['required_autoequip.json']
NEW = 'required_mod_menu_style.json'
STATUS = 'MOD_MENU_STYLE_STATIC_PASS_NATIVE_PENDING'
p.O = O
p.E = E
p.FILES = ['NightRemaster.ain', 'NightRemasterPact.afa']


def main():
    ev = p.read(O / 'build_evidence.json')
    after, before = ev['files'], ev['source_files']
    for name, status in [
        ('verification.json', 'MOD_MENU_STYLE_FIXTURES_PASS'),
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
        if f.is_file() and f.suffix in ['.json', '.jam', '.pactex', '.jaf', '.png'] and f.name != 'native_raw_code.jam':
            shutil.copy2(f, E / 'source' / f.name)
    for name in [
        'build_mod_menu_style_20260917.py',
        'verify_mod_menu_style_20260917.py', 'check_mod_menu_style_release_20260917.py',
        'publish_mod_menu_style_20260917.py', 'scan_mod_menu_style_20260917.ps1',
        'publish_autoequip_20260917.py', 'publish_dungeon_sweep_20260916.py', 'publish_loot_notice_20260915.py',
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
                   AIN=dict(changed_function_ids=ev['changed_function_ids'], added_functions=0), PACT=ev['PACT'], native_gameplay_verified=False,
                   save_schema_unchanged=True, translator_model='Codex internal')
        updated = copy.deepcopy(manifest)
        updated.update(status=STATUS, time=now, runtime_verified=False, mod_menu_style_revision=rev)
        updated['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'],
                              mod_menu_style_overlay=str(E / 'source/build_evidence.json'))
        for row in updated['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        updated['next'] = 'Native UI check: yellow mod launch labels and native blue framed sweep/autoequip/stone menus; hover/disabled/cancel and normal dialogs unchanged. Native screenshot evidence pending.'
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
            contract['mod_menu_style_overlay'] = str(E / 'source/build_evidence.json')
            write(path, p.js(contract))
        instruction = ('Style only: Type2026091602 renderer27936 uses existing CG1840 and text-free strips of CG1500. '
                       'Native selection labels yellow255/224/96, hover255/250/180; disabled preserved; title color restored. '
                       'Every root48px, row pitch and backgroundheight agree; commands precede native Build. '
                       'Other dialog branches exact; all reward/equip/inventory/choice-code/callback functions unchanged. '
                       'PACT153/154/161 change only added mod label FontColor. No raster/font/EX/exe/save schema changes. '
                       'Actual native UI validation pending.')
        write(R / NEW, p.js(dict(rev, manifest=str(mp), manifest_sha256=mh,
                               required_files=after, instruction=instruction)))
        write(ptr, p.js(dict(current, status=STATUS, manifest_sha256=mh, runtime_verified=False)))
        note = (f'\n\n### {now} 모드 메뉴 원작형 버튼·노란 글자 — 적용, 게임 화면 확인 대기\n'
                '- 소탕 확인 및 자동 장착·요소석 추천 메뉴: 원작 CG1840 발광 프레임,CG1500 텍스트 없는 양끝과1px 배경으로 독립 버튼 구성. 래스터 수정 없음.\n'
                '- 모드 글자 노랑255/224/96,hover 밝은 노랑255/250/180,비활성 원본 유지. 제목 일시 색상 적용 후 원상 복원. 진입 버튼3개도 노랑으로 구분.\n'
                '- AIN27936만 변경,PACT153/154/161의 모드 글자색만 변경. 보상·장착·재고·선택코드·입력·콜백 변경 없음.\n'
                '- 컴파일 렌더러60fixture(다른타입4종/선택개수/행간격), 모든 클릭영역48px·중앙·배경높이 일치, 구축완료 전 합성,글리프 및 native CG 재구성 시각검사 통과. 실제 게임 캡처 아님.\n'
                f'- 다른96runtime파일, {len(saves)}개 세이브 및 복구빌드 보존. Evidence/rollback: {E}. Manifest {mh}.\n'
                '- 남음: 실제게임 소탕/장비/가공 메뉴와 hover·취소 확인.\n')
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
