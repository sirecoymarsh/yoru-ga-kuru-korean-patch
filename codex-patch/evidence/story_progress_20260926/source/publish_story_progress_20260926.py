"""Hash-bound inactive-runtime update with rollback; no save-file writes."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import build_story_progress_20260926 as build
import publish_save_slots_20260925 as prior
p=build.p;R=build.R;O=build.O;E=R/'evidence/story_progress_20260926'
FILES=['NightRemaster.ain','NightRemasterPact.afa'];p.O=O;p.E=E;p.FILES=FILES
NEW='required_story_progress_20260926.json';CONTRACTS=prior.CONTRACTS+[prior.NEW]
STATUS='STORY_PROGRESS_INSTALLED_NATIVE_PASS'
def main():
    ev=p.read(O/'build_evidence.json');after=ev['files'];before={n:p.sha(build.S/n) for n in FILES}
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);rt=Path(current['runtime']).resolve();mp=Path(current['manifest'])
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(rt/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'] and rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    qa=p.read(O/'verification.json');assert qa['status']=='STORY_PROGRESS_STATIC_NATIVE_PASS' and qa['files']==after
    assert qa['save_schema_equal'] and qa['old_CODE_allowlist_exact'] and qa['changed_PACT']==[]
    for name,status in [('scan_report.json','SCANNED_NO_TARGET_DETECTIONS'),('transaction_verification.json','TRANSACTION_FIXTURE_PASS')]:
        check=p.read(O/name);assert check['status']==status and check.get('files',check.get('payload'))==after
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);saves=p.snapshot_saves()
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths));snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for name in CONTRACTS:
        co=p.read(R/name)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in co:assert co[key]==current['manifest_sha256'],name
    E.mkdir(parents=True)
    for folder in ['before','candidate','source','screenshots']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for name in FILES:shutil.copy2(rt/name,E/'before'/name);shutil.copy2(O/name,E/'candidate'/name)
    for name in ['build_evidence.json','verification.json','story_catalog.json','helpers_readable.jaf','helpers.jaf','patch.jam','native_opcode_audit.json','scan_report.json','transaction_verification.json','save_frames.json']:
        shutil.copy2(O/name,E/'source'/name)
    for name in ['inspect_story_progress_20260926.py','build_story_progress_20260926.py','probe_story_progress_20260926.py','verify_story_progress_20260926.py','publish_story_progress_20260926.py']:
        shutil.copy2(build.HERE/name,E/'source'/name)
    for save,path in qa['native_probes'].items():
        root=Path(path).parent;shutil.copy2(path,E/'source'/('native_'+save+'.json'))
        for image in ['auto_probe_load_page0.png','auto_probe_save_page0.png','auto_probe_load_page9.png','story_info.png','story_detail.png','story_home.png']:
            if (root/image).exists():shutil.copy2(root/image,E/'screenshots'/(save.removesuffix('.asd')+'_'+image))
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain'];full['story_progress_overlay']={'evidence':str(E),'semantic_dialogue_changes':0,'translator_model':'Codex internal'}
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full))
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat();rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),native_render_verified=True,OS_mouse_hit_test=False,MSG1_exact=True,serialized_schema_changes=0,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],relocated=ev['relocated'],translator_model='Codex internal')
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,story_progress_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],story_progress_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Restart; save again to record main-story checkpoint independently from per-save all-branch event collection.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for name in CONTRACTS:
            co=p.read(R/name)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for file,hash in after.items():
                if file in co.get('required_files',{}):co['required_files'][file]=hash
            co['story_progress_preserved_by']=str(E);write(R/name,p.js(co))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':'Main story is a current-save event checkpoint label, never all-branch percentage/calendar interpolation. Entire-event collection remains current save entered/1043 and separate from global gallery/read data. Preserve KR_SAVE2 28 fields plus optional KR_MAIN1,stage fields; unknown legacy main progress is explicit. Home character click rows remain 7..13. No persistent frame/schema change.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,story_progress_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),story_progress_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 본편 진행 단계 / 전체 이벤트 달성률 분리 설치 — Codex internal\n- 저장 목록·플레이 정보·거점 패널을 분리 표기. 본편은 실제 등록된 주요 사건 단계, 전체는 해당 저장의 전체 분기1043개 진입률. 날짜 보간/가짜 본편 퍼센트/전역 CG 달성률 혼합 없음.\n- KR_SAVE2 뒤 KR_MAIN1,단계 숫자를 추가. 옛 저장은 본편 미기록/재저장 안내; 현재 플레이 값을 다른 슬롯에 대입하지 않음. 세이브/자동 저장 파일 직접 변경 없음.\n- {qa["existing_resume_saves"]}개 저장/{qa["saved_return_frames"]}개 복귀주소 정적호환, 기존 CODE/스키마/PACT/대사 완전동일. 던전·거점 무음 격리 저장/재로딩·화면 확인, 모든 사건별 별칭·개인이벤트 분리·캐릭터 클릭줄 검증 통과. 진단 중 거점의 기존 선택창과 중첩 호출한 초기 시도는 제외하고 표면별 분리 검증.\n- evidence {E}; AIN {after["NightRemaster.ain"]}; manifest {mh}; 복구 publish_story_progress_20260926.py --restore. 본편 전체를 새로 플레이한 검증은 아니며 기존 CT-RATE-004/장시간 자동탐색 종료는 이번 범위 밖.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves()
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(j))
    except BaseException as error:
        failures=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as er:failures.append(repr(er))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:p.put(path,data)
                elif path.exists():path.unlink()
            except BaseException as er:failures.append(repr(er))
        j.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(error),rollback_errors=failures);p.put(E/'journal.json',p.js(j));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,existing_save_files_unchanged=len(saves),evidence=str(E),runtime=str(rt))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report))
    p.put(E/'README.md',('# 본편 진행과 전체 이벤트 달성률\n\n- 본편: 해당 저장의 실제 이벤트 기록에 따른 도달 단계. 본편 완료 퍼센트가 아닙니다.\n- 전체 달성률: 해당 저장에서 진입한 이벤트 / 전체 분기1043개. 대사 완독·CG·회상은 별도입니다.\n- 저장 목록, 플레이 정보, 거점 패널에 분리 표기했습니다. 구형 저장은 다시 저장하면 본편 단계가 나타납니다.\n- 기존 저장 파일은 변경하지 않았습니다. 실제 던전/거점 사본의 저장·재로딩과 화면을 무음 검증했습니다.\n- 복구: '+str(build.HERE/'publish_story_progress_20260926.py')+' --restore\n').encode('utf8'))
    print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
    else:main()
