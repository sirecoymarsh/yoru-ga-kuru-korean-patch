"""Install data-only UI extension with hash-bound rollback and prior contracts retained."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_auto_explore_segment_fix_20260923 as previous
import publish_cheat_menu_20260915 as p
import build_mod_native_style_20260923 as build
R=build.R;O=build.O;E=R/'evidence/mod_native_style_20260923';HERE=build.HERE
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_mod_native_style_20260923.json'
STATUS='MOD_NATIVE_STYLE_INSTALLED_ENGINE_RENDER_PASS'
p.O=O;p.E=E;p.FILES=build.FILES

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for name,status in [('verification.json','MOD_NATIVE_STYLE_STATIC_AND_ENGINE_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/name);assert check['status']==status and check['files']==after
    qa=p.read(O/'verification.json');assert qa['existing_save_local_offsets_exact'] and qa['old_CODE_allowlist_exact'] and len(qa['render_matches'])==4
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
        if file.is_file() and file.suffix in ['.json','.txt','.jaf','.jam','.png','.qnt','.pactex'] and file.name!='native_raw_code.jam':shutil.copy2(file,E/'source'/file.name)
    shutil.copytree(O/'native',E/'source/native')
    for n in ['mod_native_style_20260923.jaf','build_mod_native_style_20260923.py','verify_mod_native_style_20260923.py','mod_style_probe_20260923.jaf','build_mod_style_probe_20260923.py','trace_native_error_20260923.py','publish_mod_native_style_20260923.py','publish_auto_explore_segment_fix_20260923.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py','scan_mod_native_style_20260923.ps1']:
        shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['mod_native_style_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,mod_string_renames=ev['AIN']['renamed_strings'],translator_model='Codex internal')
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),native_render_verified=True,os_mouse_hit_test_verified=False,persistent_return_offsets_exact=True,MSG1_exact=True,save_schema_changes=0,save_writes=0,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],changed_PACT=[154,161],appended_CG=12,old_CODE_allowlist=ev['AIN']['in_place_instructions'],relocated_helpers=ev['AIN']['relocated'],translator_model='Codex internal')
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,mod_native_style_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],mod_native_style_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User restart: inspect Sweep/Explore and Element Recommendation in original serif/color/chrome. Native saved-scene engine captures and focus/cancel branches passed; OS mouse click and full sweep/crafting execution not claimed. All exploration behavior fixes retained.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['mod_native_style_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':'Keep original return 120x40 family and weapon 172x70 family, original font/color (no yellow mod distinction), unscaled textures and legacy saved-part refresh. Low-level texture states are 1,2,3. Preserve generic part keys and input callbacks. Mod affirmative focus is one-shot; ordinary choices and cancellation remain unchanged. Rename display to automatic exploration; do not alter save schemas.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,mod_native_style_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),mod_native_style_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 모드 버튼 원작 스타일 및 확인 기본 선택 설치\n- 자동 소탕/자동 탐색/탐색 중지: 거점 복귀와 동일120x40 프레임, NotoSerifKR500 22px. 요소석 추천: 요소석 합성과 동일172x70 캔버스/24px600. 사용자 최신 결정에 따라 노란 구분 폐기, 원작 상태별 글씨색/광원 재사용. 원본2824CG 보존,12자산추가,PACT154/161 모드root만 변경.\n- 기존 저장이 예전 그래픽까지 복원함을 실제 엔진에서 확인. 가시성/시작중지 helper에 한정해 새CG·좌표·배율/옛라벨숨김 갱신. 상태번호1/2/3 검증, 반복 텍스처 로드 없음.\n- 소탕/추천 확인은 실행 쪽으로 커서 이동. 실제 확인 입력은 유지, 취소/실행 반환 및 일반선택으로 전염하지 않는 것 검증. 원작 합성의 후속확인은 이미OK먼저라 그대로 둠.\n- 복사NightR36 엔진 렌더, 기본/중지 및 요소석 패널 실측. hover/down 자산과 연결은 정적검증, 실제 마우스전환 미검증. 최종PNG 픽셀 대조4종 PASS. Native diagnostic PID {qa["native"]["pid"]}, 오류0. OS마우스클릭/실제보상·합성실행 전체 검사는 별도.\n- CODE3명령만 같은길이교체, 단기helper3개재배치, 추가helper8개; MSG1보존, 모드자동이동문구5개만 자동탐색으로변경. {qa["existing_resume_saves"]}저장/{qa["saved_return_frames"]}복귀위치검사 PASS. 저장스키마/원본저장/복구빌드 보존. Defender/설치복구fixture PASS.\n- AIN {after["NightRemaster.ain"]}; manifest {mh}; evidence/rollback {E}. 기존 자동탐색 구간/클릭 수정 유지. 최종 후보에서 native 버튼콜백 8걸음/두 경계통과/재클릭중지 회귀검사PASS(PID53992). 벽이미지 작업 별도.\n'
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
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=95,unchanged_save_files=len(saves),recovery_unchanged=True,native_render_verified=True,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
    else:main()
