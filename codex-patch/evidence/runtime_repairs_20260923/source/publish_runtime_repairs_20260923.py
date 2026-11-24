"""Install data-only UI extension with hash-bound rollback and prior contracts retained."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_mod_native_style_20260923 as previous
import publish_cheat_menu_20260915 as p
import build_runtime_repairs_20260923 as build
R=build.R;O=build.O;E=R/'evidence/runtime_repairs_20260923';HERE=build.HERE
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_runtime_repairs_20260923.json'
STATUS='RUNTIME_REPAIRS_INSTALLED_NATIVE_REGRESSION_PASS'
p.O=O;p.E=E;p.FILES=build.FILES

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for name,status in [('verification.json','RUNTIME_REPAIRS_STATIC_AND_NATIVE_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/name);assert check['status']==status and check['files']==after
    qa=p.read(O/'verification.json');assert qa['existing_save_local_offsets_exact'] and qa['old_CODE_allowlist_exact'] and qa['native_checks_passed']
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
    saves=p.snapshot_saves();assert saves==p.read(O/'save_hashes_before_validation.json')
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
        if file.is_file() and file.suffix in ['.json','.txt','.jaf','.jam','.png','.qnt','.pactex'] and file.name!='native_raw_code.jam':shutil.copy2(file,E/'source'/file.name)
    shutil.copytree(O/'native',E/'source/native')
    for n in ['runtime_repairs_20260923.jaf','build_runtime_repairs_20260923.py','verify_runtime_repairs_20260923.py','weapon_cancel_probe_20260923.jaf','build_weapon_cancel_probe_20260923.py','build_walk_segment_probe_20260923.py','walk_segment_probe_20260923.jaf','battle_walk_fixture_20260923.jaf','diagnostic_audio_20260923.py','verify_assign_diagnostic_20260923.py','run_runtime_repairs_checks_20260923.py','trace_native_error_20260923.py','publish_runtime_repairs_20260923.py','scan_runtime_repairs_20260923.ps1']:
        shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['runtime_repairs_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model='Codex internal')
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),native_render_verified=True,os_mouse_hit_test_verified=False,persistent_return_offsets_exact=True,MSG1_exact=True,save_schema_changes=0,save_writes=0,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],changed_PACT=[154],old_CODE_allowlist=ev['same_length_sites'],relocated_helpers=ev['relocated'],translator_model='Codex internal')
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,runtime_repairs_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],runtime_repairs_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User restart: test name entry Ryo via Korean IME, terminology changes, original save/next-day flow and manual right-click. Isolated original-engine tests pass; OS input and full next-day scenario remain user runtime checks.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['runtime_repairs_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':'Preserve short-helper string A_REF lifetime fixes; preferences must not use native VSFile singleton. Keep CP949 input conversion before proxy validation, same-length persistent CALLFUNC patches, native save layouts, and battle-result auto-close only while exploration owns an enemy encounter. Do not overwrite user saves.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,runtime_repairs_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),runtime_repairs_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f"\n\n### {now} 런타임 회귀 수정 설치\n- 상마도 우클릭 취소: KR_ModStonePart/ExploreButtonNumber의 동적 key 참조 증가 누락 수정. 추천→원작확인 취소→상마도 우클릭 반환과 두 뷰 소멸을 실제 엔진에서 확인.\n- 용어설정: VSFile에 절대 경로를 전달한 쓰기 실패가 singleton 종료 상태를 붙잡아 다음 저장도 실패함을 재현. 독립 TextFile 핸들/CRLF 검증/보관본 복구로 교체. 설정 변경 및 새 프로세스 재독해, 실패한 쓰기 이후 VSFile 정상 저장 통과. 원본 자동저장 덮어쓰지 않음.\n- 이름 입력: CP949를 게임 proxy 문자로 변환한 뒤 기존 1~5글자 검증. 지원 문자·경계 조합2372건 네이티브 변환 통과. 실제 OS IME 타이핑은 사용자 재검증 필요.\n- 자동 탐색 소유권+적조우 Pending3인 결과창만 800ms 뒤 닫기. 일반/관련없는 결과창은 수동 유지. 상세 네이티브 전투·탐색 결과: {qa['native_summary']}.\n- 무기 비교창 속성/범위/사거리 6값의 좌표/글자 크기만 수정, PACT154 외 모든 자산 동일. 캡처 검토 증거 보관.\n- {qa['existing_resume_saves']}저장/{qa['saved_return_frames']}복귀 위치 exact; MSG1/STR0기존접두부/저장스키마 동일. Defender 및 설치/복구 fixture PASS. AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {E}.\n"
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
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
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=96,unchanged_save_files=len(saves),recovery_unchanged=True,native_render_verified=True,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
    else:main()
