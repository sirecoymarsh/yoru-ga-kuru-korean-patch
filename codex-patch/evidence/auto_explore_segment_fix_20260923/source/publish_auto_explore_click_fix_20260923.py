"""Hash-bound callback repair; reuse existing atomic install and rollback machinery."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_auto_explore_20260923 as previous
import publish_cheat_menu_20260915 as p
R=p.R;O=R/'staging/auto_explore_click_fix_20260923';E=R/'evidence/auto_explore_click_fix_20260923';HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_auto_explore_click_fix_20260923.json'
STATUS='AUTO_EXPLORE_CALLBACK_FIX_INSTALLED_NATIVE_DISPATCH_PASS'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for name,status in [('verification.json','CLICK_FIX_STATIC_AND_NATIVE_DISPATCH_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/name);assert check['status']==status and check['files']==after
    qa=p.read(O/'verification.json');assert qa['existing_save_local_offsets_exact'] and qa['old_CODE_exact'] and len(qa['native'])==2
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
    saves=p.snapshot_saves();assert saves==p.read(O/'save_hashes_before_build.json')
    keep=p.read(R/'required_build_retention.json');rec=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
    assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths));snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for n in CONTRACTS:
        c=p.read(R/n)
        for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if k in c:assert c[k]==current['manifest_sha256'],n
    E.mkdir(parents=True);assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for folder in ['before','candidate','source']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
        assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
    for file in O.iterdir():
        if file.is_file() and file.suffix in ['.json','.txt','.jam'] and file.name!='native_raw_code.jam':shutil.copy2(file,E/'source'/file.name)
    for n in ['auto_explore_click_fix_20260923.jaf','build_auto_explore_click_fix_20260923.py','verify_auto_explore_click_fix_20260923.py','walk_click_probe_20260923.jaf','build_walk_click_probe_20260923.py','trace_native_error_20260923.py','publish_auto_explore_click_fix_20260923.py','publish_auto_explore_20260923.py','publish_resume_compat_20260923.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
        shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['auto_explore_click_fix_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,STR0_prefix_exact=True)
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),patched_existing=[32030],added_helpers=3,old_CODE_exact=True,persistent_return_offsets_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,save_writes=0,native_dispatch_verified=True,os_mouse_hit_test_verified=False,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,auto_explore_click_fix_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],auto_explore_click_fix_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User mouse retest of automatic exploration after loading an existing dungeon save. Native part-event dispatch, actual one-step movement and second-click stop verified in both route modes. Button styling/rename, calendar and wall localization remain separate pending requests.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['auto_explore_click_fix_preserved_by']=str(E);write(R/n,p.js(c))
        contract={**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':'Keep KR_WalkVisible -> KR_ExploreVisibleBound. On show, resolve current WalkButton and erase/add only KR_WalkClick before original visibility/floor-resume behavior. Preserve callback idempotence, existing other handlers, old persistent code/metadata and save offsets. Do not rewrite saves. Native copied-save dispatch ON/OFF start/move/stop passed; OS mouse hit test still requires user retest.'}
        write(R/NEW,p.js(contract))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,auto_explore_click_fix_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),auto_explore_click_fix_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 자동 탐색 버튼 저장 로드 후 무반응 수정 설치\n- 기존 던전 저장에서 자동탐색 버튼 clickable/input=1이지만 handlers=0, 실제 버튼 이벤트 전달 후 clickResult=0 재현. 소탕은 handlers=1. 새 자산의 버튼이 저장 로드로 복원되어도 Init에만 있던 클릭 연결은 빠지는 문제.\n- 던전 자동탐색 버튼 표시 시 현재 파트 번호를 조회하고 KR_WalkClick만 제거/재등록. 다른 버튼/핸들러 보존; 중복 표시3회 후 handlers=1. 기존 KR_ExploreVisible의 층 재개 처리 유지.\n- 실제 복사 NightR36 저장/네이티브 CPartsFunctionSet 클릭 이벤트 → 원래 WaitForClick/Run → 경로OFF4칸 계획 및21,6→20,6 이동, 경로ON21칸 계획 및21,6→22,6 이동, 두 번째 클릭으로 중지. PID32396/63876 모두exit0. OS 마우스 좌표 hit test는 도구 연결 불가로 직접 확인하지 못함. 전체 던전/전투/층전환 회귀를 전량 확인한 것은 아님.\n- 기존 CODE 전량·MSG1·STR0접두부 동일, helper32030 진입만 변경/3helper추가. {qa["existing_resume_saves"]}저장/{qa["saved_return_frames"]}복귀 위치 exact. 설치복구/중단/tamper fixture 및 Defender PASS. 다른97runtime파일/{len(saves)}원본저장파일/복구빌드 해시 보존.\n- AIN {after["NightRemaster.ain"]}; manifest {mh}; evidence/rollback {E}. 모드 버튼 원작 스타일/표시명 자동 탐색 변경, 달력9월 배치, 부실 벽 이미지는 아직 별도 미완료.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf-8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves();assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={n:p.sha(rec/n) for n in p.FILES}
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(j))
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
        j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);p.put(E/'journal.json',p.js(j));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=97,unchanged_save_files=len(saves),recovery_unchanged=True,native_dispatch_verified=True,os_mouse_hit_test_verified=False,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf-8'))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf-8'))
    else:main()
