"""Hash-bound inactive-runtime update with rollback; no save-file writes."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import build_event_navigation_20260926 as build
import publish_story_progress_20260926 as prior
p=build.p;R=build.R;O=build.O;E=R/'evidence/event_navigation_20260926'
FILES=['NightRemaster.ain','NightRemasterPact.afa'];p.O=O;p.E=E;p.FILES=FILES
NEW='required_event_navigation_20260926.json';CONTRACTS=prior.CONTRACTS+[prior.NEW]
STATUS='EVENT_NAVIGATION_INSTALLED_NATIVE_PASS'
def main():
    ev=p.read(O/'build_evidence.json');after=ev['files'];before={n:p.sha(build.S/n) for n in FILES}
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);rt=Path(current['runtime']).resolve();mp=Path(current['manifest'])
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(rt/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'] and rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    qa=p.read(O/'verification.json');assert qa['status']=='EVENT_NAVIGATION_STATIC_NATIVE_PASS' and qa['files']==after
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
    for name in ['build_evidence.json','verification.json','map_checks.json','helpers_readable.jaf','helpers.jaf','patch.jam','native_opcode_audit.json','scan_report.json','transaction_verification.json','save_frames.json']:
        shutil.copy2(O/name,E/'source'/name)
    for name in ['build_event_navigation_20260926.py','probe_event_navigation_20260926.py','verify_event_navigation_20260926.py','publish_event_navigation_20260926.py','review_navigation_20260926.py']:
        shutil.copy2(build.HERE/name,E/'source'/name)
    for save,path in qa['native_probes'].items():
        root=Path(path).parent;shutil.copy2(path,E/'source'/('native_'+save+'.json'))
        for image in root.glob('*.png'):
            shutil.copy2(image,E/'screenshots'/(save.removesuffix('.asd')+'_'+image.name))
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain'];full['event_navigation_overlay']={'evidence':str(E),'semantic_dialogue_changes':0,'translator_model':'Codex internal'}
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full))
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat();rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),native_render_verified=True,OS_mouse_hit_test=False,MSG1_exact=True,serialized_schema_changes=0,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],relocated=ev['relocated'],translator_model='Codex internal')
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,event_navigation_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],event_navigation_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Restart and resume existing saves; six verified event-goal maps now guide and explore toward native progress events. Story and party choices are unchanged.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for name in CONTRACTS:
            co=p.read(R/name)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for file,hash in after.items():
                if file in co.get('required_files',{}):co['required_files'][file]=hash
            co['event_navigation_preserved_by']=str(E);write(R/name,p.js(co))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':'Preserve event-goal mapping 101/102/303/503/605/803. Native event6/sub0 is goal; active B1 precedes R1 on101/605. Draw and movement planners must match. Preserve native story/party controls, ordinary/puzzle goals, bounded scan caching, and all save frames. Do not blindly route to every event or bypass events.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,event_navigation_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),event_navigation_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 이벤트 맵 경로/자동 탐색 수정 설치 — Codex internal\n- NAV-001/002: 101·102·303·503·605·803의 계단 대신 진행 이벤트 목표를 지원. 101/605는 원작 B1 이벤트 완료 후 R1 안내. 스토리/파티 선택/퍼즐/수동 중지 코드는 유지; 알 수 없는 기믹을 무작정 배회하지 않음.\n- 마지막 던전 저장45/map605 안내2칸+탐색시작+원작 이벤트까지 실제이동 무음 사본 PASS. 일반저장36 다음층+새층3칸 탐색 PASS. 전체 40개 맵/상태의 실제컴파일코드 경로/목표/참조/캐시 검사 PASS. 다른5맵은 코드/실제맵 fixture 검증이며 스토리전체 플레이 완료 검증은 아님.\n- {qa["existing_resume_saves"]}개 세이브/{qa["saved_return_frames"]}복귀주소 호환, 기존 CODE/스키마/PACT/EX/대사 불변. Defender/설치복구fixture PASS. 실제 세이브 변경 없음.\n- evidence {E}; AIN {after["NightRemaster.ain"]}; manifest {mh}; 복구 publish_event_navigation_20260926.py --restore. 908/909 등 다른 미검수 기믹과 장시간 자동탐색 종료는 이번 범위 밖.\n'
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
    p.put(E/'README.md',('# 이벤트 맵 경로와 자동 탐색 수정\n\n- 확인된 6개 맵에서 계단 대신 원작 진행 이벤트를 안내합니다.\n- 서양관 내부 틈새5는 파티 관련 이벤트를 먼저 거친 다음 보스 진행 지점으로 안내합니다. 스토리와 파티 선택은 건너뛰지 않습니다.\n- 마지막 던전 저장45에서 경로 표시와 실제 자동 이동을 무음 사본으로 확인했습니다. 일반 던전의 다음 층 이동 후 탐색 재개도 확인했습니다.\n- 기존 세이브를 그대로 불러오면 됩니다. 사용자 저장 파일은 변경하지 않았습니다.\n- 나머지 대상 맵은 실제 맵/컴파일 코드 검증이며 모든 스토리를 새로 플레이한 것은 아닙니다.\n- 복구: '+str(build.HERE/'publish_event_navigation_20260926.py')+' --restore\n').encode('utf8'))
    print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
    else:main()
