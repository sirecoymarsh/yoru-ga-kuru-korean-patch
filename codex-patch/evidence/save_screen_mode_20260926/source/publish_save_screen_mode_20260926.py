"""Inactive-runtime transaction for selectable original/alternative save screens."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import build_save_screen_mode_20260926 as build
import publish_pinned_autosave_20260926 as prior
p=build.p;R=build.R;O=build.O;E=R/'evidence/save_screen_mode_20260926'
FILES=['NightRemaster.ain','NightRemasterPact.afa'];p.O=O;p.E=E;p.FILES=FILES
CONTRACTS=prior.CONTRACTS+[prior.NEW];NEW='required_save_screen_mode_20260926.json'
STATUS='SAVE_SCREEN_MODE_INSTALLED_NATIVE_PASS'

def main():
    ev=p.read(O/'build_evidence.json');after=ev['files'];before={n:p.sha(build.S/n) for n in FILES}
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);rt=Path(current['runtime']).resolve();mp=Path(current['manifest'])
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(rt/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'] and rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    qa=p.read(O/'verification.json');assert qa['status']=='SAVE_SCREEN_MODE_STATIC_NATIVE_PASS' and qa['files']==after
    for name,status in [('scan_report.json','SCANNED_NO_TARGET_DETECTIONS'),('transaction_verification.json','TRANSACTION_FIXTURE_PASS')]:
        check=p.read(O/name);assert check['status']==status and check.get('files',check.get('payload'))==after
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);saves=p.snapshot_saves()
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for name in CONTRACTS:
        co=p.read(R/name)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in co:assert co[key]==current['manifest_sha256'],name
    for folder in ['before','candidate','source','screenshots']:(E/folder).mkdir(parents=True,exist_ok=True)
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for name in FILES:shutil.copy2(rt/name,E/'before'/name);shutil.copy2(O/name,E/'candidate'/name)
    for name in ['build_evidence.json','verification.json','visual_review.json','patch.jam','helpers.jaf','layout.json','native_opcode_audit.json','scan_report.json','transaction_verification.json','save_frames.json']:
        shutil.copy2(O/name,E/'source'/name)
    for name in ['build_save_screen_mode_20260926.py','save_screen_mode_20260926.jaf','probe_save_screen_mode_20260926.py','verify_save_screen_mode_20260926.py','publish_save_screen_mode_20260926.py']:
        shutil.copy2(build.HERE/name,E/'source'/name)
    for mode,path in qa['native_probes'].items():
        root=Path(path).parent;shutil.copy2(path,E/'source'/('native_'+mode+'.json'))
        for img in root.glob('*.png'):shutil.copy2(img,E/'screenshots'/(mode+'_'+img.name))
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full['save_screen_mode_overlay']={'evidence':str(E),'semantic_dialogue_changes':0,'translator_model':'Codex internal'}
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full))
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat();rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),native_page_verified=True,native_config_dispatch=True,restart_preference=True,cross_mode_resume=True,default_mode="alternative",
            OS_mouse_hit_test=False,MSG1_exact=True,serialized_schema_changes=0,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],relocated=ev['relocated'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,save_screen_mode_revision=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],save_screen_mode_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Restart normally. Mods > 저장 화면 설정 selects original stat cards or alternative progress cards with pinned daily/weekly autosaves. Default stays alternative. Both layouts use the same save data; choice persists across restart.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for name in CONTRACTS:
            co=p.read(R/name)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for file,hash in after.items():
                if file in co.get('required_files',{}):co['required_files'][file]=hash
            co['save_screen_mode_preserved_by']=str(E)
            if any(part in name for part in ['save_slots','story_progress','pinned_autosave']):co['save_screen_mode_scope']='Save-card progress and pinned daily/weekly layout requirements apply to alternative mode. Original mode intentionally restores five stat cards and daily slot on page1. Save files/writers and latest-manual page are common.'
            write(R/name,p.js(co))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,
            'instruction':'Preserve Mods KR_SaveStyleButton/label and native ClickEvent binding. Missing YoruKR_OriginalSaveScreen.dat means alternative; marker present means original. Keep preference outside saved globals; capture style when opening each view. Original uses appended original PACT cell/scene assets and five rows (daily999 + manual1..4 on page0). Alternative keeps pinned daily999/weekly998 and progress cards. Preserve manual1..49, latest-manual page, existing save metadata/writers, all unrelated translations and mods.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,save_screen_mode_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),save_screen_mode_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 원본/대체 저장 화면 선택 모드 설치 — Codex internal\n- 모드 탭 저장 화면 설정: 원본 능력치5행 / 대체 진행 정보+일간·주간 상단 고정 선택. 기본값은 현재 대체 화면 유지. 원본 모드는 첫 페이지 일간999, 수동1..49; 주간998은 대체 화면에서 표시한다고 선택창에 안내.\n- 선택은 SaveFolder의 YoruKR_OriginalSaveScreen.dat 존재로 보존. 원본 선택=create, 대체 선택=delete, 내용 해석 없음. 사용자 게임 저장·스키마·다른 모드 설정과 분리. 화면을 열 때 렌더링 모드 고정.\n- 무음 사본: 실제 모드 버튼 ClickEvent→선택창→원본/대체·취소, 10페이지 양방향·셀 위치·키보드 선택, 총50회 native 화면 갱신. 원본 모드 저장47→프로세스 재실행→실제47 재개→대체 화면에서 동일47 표시 PASS. 원본/대체 카드·모드 버튼·선택창 실화면 검수. OS 실제 마우스 좌표 클릭은 별도 미검증.\n- {qa["existing_resume_saves"]}개 저장/{qa["saved_return_frames"]}개 복귀주소 호환 PASS. 기존 CODE·메시지·스키마·EX·기존문자열 접두 불변. 기존 PACT185에 버튼/라벨2개만 추가, 과거 원본 계열 한국어 저장 자산168/169는 별도 경로로 무변경 복사; 대체 PACT168/169 바이트 유지. 세이브 파일은 공용이며 사용자의397개 파일은 변경 없음.\n- 증거 {E}; 복구 publish_save_screen_mode_20260926.py --restore. 기본값 확인·재실행은 새 빌드에서 계속.\n'
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
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode())

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
