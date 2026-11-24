"""Inactive-runtime transaction for pinned daily/weekly auto-save cards."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import build_pinned_autosave_20260926 as build
import publish_save_page_restore_20260926 as prior
p=build.p;R=build.R;O=build.O;E=R/'evidence/pinned_autosave_20260926'
FILES=['NightRemaster.ain','NightRemasterPact.afa'];p.O=O;p.E=E;p.FILES=FILES
CONTRACTS=prior.CONTRACTS+[prior.NEW];NEW='required_pinned_autosave_20260926.json'
STATUS='PINNED_AUTOSAVE_INSTALLED_NATIVE_PASS'

def main():
    ev=p.read(O/'build_evidence.json');after=ev['files'];before={n:p.sha(build.S/n) for n in FILES}
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);rt=Path(current['runtime']).resolve();mp=Path(current['manifest'])
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(rt/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'] and rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    qa=p.read(O/'verification.json');assert qa['status']=='PINNED_AUTOSAVE_STATIC_NATIVE_PASS' and qa['files']==after
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
    for name in ['build_evidence.json','verification.json','visual_review.json','patch.jam','layout.json','native_opcode_audit.json','scan_report.json','transaction_verification.json','save_frames.json']:
        shutil.copy2(O/name,E/'source'/name)
    for name in ['build_pinned_autosave_20260926.py','probe_pinned_autosave_20260926.py','verify_pinned_autosave_20260926.py','publish_pinned_autosave_20260926.py']:
        shutil.copy2(build.HERE/name,E/'source'/name)
    for mode,path in qa['native_probes'].items():
        root=Path(path).parent;shutil.copy2(path,E/'source'/('native_'+mode+'.json'))
        for img in root.glob('*.png'):shutil.copy2(img,E/'screenshots'/(mode+'_'+img.name))
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full['pinned_autosave_overlay']={'evidence':str(E),'semantic_dialogue_changes':0,'translator_model':'Codex internal'}
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full))
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat();rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),native_page_verified=True,
            OS_mouse_hit_test=False,MSG1_exact=True,serialized_schema_changes=0,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],relocated=ev['relocated'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,pinned_autosave_revision=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],pinned_autosave_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Restart normally. Daily/weekly auto-save cards stay pinned above manual saves on every page. Latest manual-save page and original ten page buttons are preserved.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for name in CONTRACTS:
            co=p.read(R/name)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for file,hash in after.items():
                if file in co.get('required_files',{}):co['required_files'][file]=hash
            co['pinned_autosave_preserved_by']=str(E);write(R/name,p.js(co))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,
            'instruction':'Keep daily999 and weekly998 fixed at y0/y72 on all ten pages. Page0 has six rows, others seven; manual IDs1..49 keep their original pages. Row pitch72/card height70; PACT168/169 compact geometry. Auto cards say 오토세이브, remain read-only in save mode and loadable only when present. Preserve Init Update(pageNo,false), latest-manual page policy, saved schema and original save writers.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,pinned_autosave_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),pinned_autosave_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 오토세이브 상단 고정 — Codex internal\n- 일간999/주간998 슬롯을 모든 페이지의 y0/y72에 고정하고 오토세이브로 표기. 수동1..49만 페이지에 따라 변경. 원래 10페이지와 마지막 수동 저장 페이지 열기는 유지.\n- 실제 엔진 무음 사본에서 저장/불러오기 총22회 화면 갱신, 10개 페이지, 셀 위치와 키보드 선택 가능 여부 확인. 6장 화면 검수; 사용자 세이브 변경 없음. OS 마우스 좌표 클릭은 별도 미검증.\n- {qa["existing_resume_saves"]}개 저장/{qa["saved_return_frames"]}개 복귀주소 검사 PASS. 기존 CODE·메시지·스키마·EX 불변. 기존 문자열 접두 유지 및 오토세이브만 추가. PACT168/169의 높이·위치만 변경. 경화기/중화기와 모든 누적 수정 유지.\n- 증거 {E}; 복구 publish_pinned_autosave_20260926.py --restore.\n'
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
