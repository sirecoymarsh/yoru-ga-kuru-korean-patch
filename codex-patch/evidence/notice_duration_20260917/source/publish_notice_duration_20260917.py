"""One-file, hash-bound notice lifetime adjustment; rewards and saves unchanged."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_notice_depth_20260917 as previous
import publish_cheat_menu_20260915 as p

R=p.R;O=R/'staging/notice_duration_20260917';E=R/'evidence/notice_duration_20260917'
HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_notice_duration.json'
STATUS='NOTICE_DURATION_INSTALLED_STATIC_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files']
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);rt=Path(current['runtime']).resolve();mp=Path(current['manifest'])
    assert rt==p.RT.resolve()
    if E.exists():
        journal=p.read(E/'journal.json')
        assert journal['status']=='COMMITTED' and p.sha(ptr)==journal['committed_pointer_sha256']
        assert all(p.sha(rt/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'] and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for name,status in [('verification.json','NOTICE_DURATION_STATIC_PASS'),('independent_review.json','STATIC_REVIEW_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        report=p.read(O/name);assert report['status']==status and report['files']==after
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    assert p.sha(rt/'NightRemasterPact.afa')==ev['unchanged_PACT'] and p.sha(rt/'NightRemasterCG.afa')==ev['unchanged_CG']
    fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
    saves=p.snapshot_saves();retention=p.read(R/'required_build_retention.json');recovery=Path(retention['recovery_runtime']);rm=Path(retention['recovery_manifest'])
    assert p.sha(rm)==retention['recovery_manifest_sha256'];recovery_hash=p.sha(recovery/p.FILES[0])
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths))
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for name in CONTRACTS:
        contract=p.read(R/name)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in contract:assert contract[key]==current['manifest_sha256'],name
    latest=p.read(R/'latest_worked_translation.json')
    assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    E.mkdir(parents=True)
    assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for folder in ['before','candidate','source']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for name in p.FILES:
        shutil.copy2(rt/name,E/'before'/name);shutil.copy2(O/name,E/'candidate'/name)
        assert p.sha(E/'before'/name)==before[name] and p.sha(E/'candidate'/name)==after[name]
    for path in O.iterdir():
        if path.is_file() and path.suffix in ['.json','.jam','.pactex','.png']:shutil.copy2(path,E/'source'/path.name)
    for name in ['build_notice_duration_20260917.py','publish_notice_duration_20260917.py','scan_notice_duration_20260917.ps1','verify_notice_duration_20260917.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
        shutil.copy2(HERE/name,E/'source'/name)
    full=p.read(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full['notice_duration_overlay']=dict(evidence=str(E),semantic_text_changes=0,MSG1_exact=True)
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full))
    p.put(E/'save_hashes_before.json',p.js(saves))
    journal=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture)
    p.put(E/'journal.json',p.js(journal))
    def write(path,data):
        assert path in snapshots
        journal.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest()
        p.put(E/'journal.json',p.js(journal));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256']
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        revision=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),changes=ev['changes'],durations_ms=ev['durations_ms'],
            patched_functions=[31880,31967,31968],unchanged_PACT=ev['unchanged_PACT'],six_operand_reverse_exact=True,unchanged_CG=ev['unchanged_CG'],
            semantic_text_changes=0,save_schema_changes=0,native_verified=False)
        updated=copy.deepcopy(manifest);updated.update(status=STATUS,time=now,notice_duration_revision=revision,runtime_verified=False)
        updated['ain'].update(candidate_sha256=after['NightRemaster.ain'],notice_duration_overlay=str(E/'source/build_evidence.json'))
        for row in updated['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        updated['next']='Native check: chest notice expires after2s, instant loot after3s, final500ms fade. New messages refresh timer. Only six existing duration operands changed; translations, rewards, saves, buttons and depth fix unchanged.'
        write(mp,p.js(updated));mh=p.sha(mp)
        for name in CONTRACTS:
            contract=p.read(R/name)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in contract:contract[key]=mh
            for file,h in after.items():
                if file in contract.get('required_files',{}):contract['required_files'][file]=h
            contract['notice_duration_overlay']=str(E/'source/build_evidence.json');write(R/name,p.js(contract))
        write(R/NEW,p.js(dict(revision,manifest=str(mp),manifest_sha256=mh,required_files=after,
            instruction='Chest lifetime2000ms/fade start1500ms; loot lifetime3000ms/fade500ms. ChestShow resets stale lines after2000ms too. Only six PUSH operands, no code relocation or metadata changes. Preserve depth repair, rewards, buttons and translations. Native retest pending.')))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),notice_duration_overlay=str(E/'source/build_evidence.json'));write(R/'latest_worked_translation.json',p.js(latest))
        write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 보상 알림 표시 시간 단축\n- 사용자 요청: 오래 떠있는 알림을 빨리 숨김. 상자4.5→2초, 전투6→3초, 마지막0.5초fade 유지. 신규알림마다 타이머갱신/최근3줄정리 기준 일치.\n- AIN31880/31967/31968 내부 PUSH 피연산자6개만 변경. 복원하면 전체unpacked AIN exact. 함수주소·메타데이터·MSG1·STR0·보상·세이브·PACT/CG 및 지형앞표시 수정 불변.\n- 실제후보 JAM 만료/페이드/갱신/잘못된시간/알림교대 검증, 독립검토·Defender·설치복구fixture 통과. 네이티브시간 확인은 남음.\n- 다른97파일·세이브{len(saves)}개 해시보존. Manifest {mh}; evidence {E}.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,updated['files']);assert saves==p.snapshot_saves()
        assert p.sha(rm)==retention['recovery_manifest_sha256'] and p.sha(recovery/p.FILES[0])==recovery_hash
        journal.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(journal))
    except BaseException as error:
        errors=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as failure:errors.append(repr(failure))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:p.put(path,data)
                elif path.exists():path.unlink()
            except BaseException as failure:errors.append(repr(failure))
        journal.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors)
        p.put(E/'journal.json',p.js(journal));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,unchanged_other_runtime_files=97,
        unchanged_save_files=len(saves),recovery_unchanged=True,native_verified=False,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
    else:main()
