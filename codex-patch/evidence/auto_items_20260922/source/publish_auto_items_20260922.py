"""Install reviewed auto-item logic and native UI, preserving translations and saves."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_smart_auto_fix_20260922 as previous
import publish_cheat_menu_20260915 as p
R=p.R;O=R/'staging/auto_items_20260922';E=R/'evidence/auto_items_20260922';HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_auto_items.json'
STATUS='AUTO_ITEMS_INSTALLED_COMPILED_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for filename,status in [('verification.json','AUTO_ITEMS_COMPILED_PASS'),('visual_review.json','STATIC_FONT_GEOMETRY_PASS'),('independent_review.json','STATIC_REVIEW_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/filename);assert check['status']==status and check['files']==after
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
    saves=p.snapshot_saves();keep=p.read(R/'required_build_retention.json');rec=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
    assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths))
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for n in CONTRACTS:
        c=p.read(R/n)
        for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if k in c:assert c[k]==current['manifest_sha256'],n
    E.mkdir(parents=True)
    assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for folder in ['before','candidate','source']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
        assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
    assert saves==p.snapshot_saves()
    for f in O.iterdir():
        if f.is_file() and f.suffix in ['.json','.jam','.pactex','.jaf','.png'] and f.name!='raw.jam':shutil.copy2(f,E/'source'/f.name)
    for n in ['build_auto_items_20260922.py','verify_auto_items_20260922.py','render_auto_items_proof_20260922.py','publish_auto_items_20260922.py','scan_auto_items_20260922.ps1','auto_items_helpers_20260922.jaf','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['auto_items_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,UI_text_changes='auto recovery subpage and effects option rename')
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),patched_existing=ev['patched_existing'],added_functions=ev['added_functions'],PACT=ev['PACT'],old_CODE_STR0_MSG1_exact=True,save_schema_changes=0,native_verified=False)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,auto_items_revision=rev,runtime_verified=False);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],auto_items_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Native retest: Mods > auto recovery settings. Default OFF, HP threshold30%, per-item reserve3. Enable then native auto in ordinary battle: reservation, item effect, no double healing, stock floor, existing saves. Settings common across saves; no new game needed.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['auto_items_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
        write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,options=ev['options'],instruction='Auto recovery native config page, defaultOFF, threshold30%, each stock reserve3. Shared flag slots72..78. Only ordinary battle types-1/0, normal item action4. Native effects and timing. Deduct once on reservation; pending recovery dedup; refund only auto-owned down cancellation. Latest translation, smart auto fix, saves and native options preserved. Native retest pending.')))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),auto_items_overlay=str(E/'source/build_evidence.json'));write(R/'latest_worked_translation.json',p.js(latest))
        write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 자동 회복 아이템 설정 추가\n- 모드 탭의 자동 회복 설정: 사용 기본 OFF, 영력 기준30%(10~90%), 회복/해독/마비해제/부활5종별 허용 및 최소보유3개(0~99). 공통 설정72~78, 기존 세이브 호환.\n- 원작 자동 행동 선택 직전에만 적용; 일반전투-1/0, 중복회복 예약 제외, 예약시1개 차감, 원작 효과/시간 유지. 자동예약 행동자가 쓰러지면 미사용 아이템1회 반환. 수동/이벤트전투·기존 강화 자동 전투는 보존.\n- 모드 옵션명을 전투 이펙트 보지 않기로 변경. 이전 별도 label 후보는 이 통합 후보로 대체(그 후보는 설치하지 않음). 원작 옵션 화면 수정 없음.\n- 컴파일된 후보 실행검사, UI 글꼴/배치 검사, 독립검토, Defender, 설치/복구검증 통과. 게임화면 재검증은 남음.\n- 변경 AIN+PACT185및187신설+EX라우팅1행. MSG1번역·기존 저장스키마 불변. 다른95파일·세이브{len(saves)}개·복구빌드 보존.\n- Manifest {mh}; evidence/rollback {E}. 다음: 기존 세이브에서 설정 저장/아이템 회복과 보존량 확인.\n'
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
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=95,unchanged_save_files=len(saves),save_preservation='hash-only: installer never writes saves',recovery_unchanged=True,native_verified=False,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
