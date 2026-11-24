"""Install the whole-page MSG-only reflow with hash-bound rollback."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import polish_translation_20260917 as t
import publish_polish_lineflow_20260917 as prior
import publish_cheat_menu_20260915 as p
R=t.ROOT;W=t.WORK/'page_lineflow_v2';O=W/'install_payload';E=R/'evidence/page_lineflow_v2_20260917'
CONTRACTS=prior.CONTRACTS+[prior.NEW];NEW='required_page_lineflow_v2.json'
STATUS='PAGE_LINEFLOW_V2_INSTALLED_STATIC_PASS_NATIVE_PENDING'
p.R=R;p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);mp=Path(current['manifest']);rt=Path(current['runtime']).resolve()
    assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    ev=p.read(W/'build_evidence.json');before={'NightRemaster.ain':ev['baseline_sha256']};after={'NightRemaster.ain':ev['ain_sha256']}
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert p.sha(rt/'NightRemaster.ain')==after['NightRemaster.ain'];print('ALREADY_INSTALLED');return
    assert current==p.read(W/'source_pointer.json')
    assert p.stopped(rt),'Target game is running; preserve unsaved play and exit before applying'
    scan=p.read(W/'defender_scan.json');assert scan['completed'] and scan['status']=='SCANNED_NO_TARGET_DETECTIONS' and not scan['after']
    assert scan['files']==after and p.sha(W/'scan_copy/NightRemaster.ain')==p.sha(W/'output/NightRemaster.ain')==after['NightRemaster.ain']
    native=p.read(W/'native_review.json');review=p.read(W/'independent_review.json')
    assert native['production_ain_sha256']==review['ain_sha256']==after['NightRemaster.ain']
    assert native['status']=='USER_TOOK_OVER_TEST_WINDOW' and review['status']=='PASS'
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    assert p.sha(rt/'NightRemaster.ain')==before['NightRemaster.ain']
    old,os,oe,oldraw=t.raw_messages((rt/'NightRemaster.ain').read_bytes());new,ns,ne,newraw=t.raw_messages((W/'output/NightRemaster.ain').read_bytes())
    assert old[:os+12]==new[:ns+12] and old[oe:]==new[ne:] and len(oldraw)==len(newraw)==100944
    assert sum(a!=b for a,b in zip(oldraw,newraw))==ev['changed_fields_from_installed']
    O.mkdir(exist_ok=True);shutil.copy2(W/'output/NightRemaster.ain',O/'NightRemaster.ain')
    fixture=p.fixture();saves=p.snapshot_saves()
    keep=p.read(R/'required_build_retention.json');recovery=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
    rh=p.sha(recovery/'NightRemaster.ain');assert p.sha(rm)==keep['recovery_manifest_sha256']
    paths=[mp,ptr,R/'progress.md',t.WORK/'progress.json',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len({x.name for x in paths})==len(paths)
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for n in CONTRACTS:
        c=p.read(R/n)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in c:assert c[key]==current['manifest_sha256'],n
    E.mkdir(parents=True)
    for name in ['before','candidate','source']:(E/name).mkdir()
    assert not E.resolve().is_relative_to(rt) and not E.resolve().is_relative_to((W/'output').resolve())
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append({'path':str(path),'name':path.name,'existed':data is not None,'sha256':p.sha(path) if data is not None else None})
    for n in p.FILES:shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
    # User explicitly requested save protection: retain the full exact save tree,
    # although this transaction never writes or restores any user save file.
    save_backup=E/'before/saves';save_backup.mkdir()
    for name,h in saves.items():
        src=p.SAVE/name;dst=save_backup/name;dst.parent.mkdir(parents=True,exist_ok=True)
        assert p.sha(src)==h;shutil.copy2(src,dst);assert p.sha(dst)==h
    assert p.snapshot_saves()==saves
    for name in ['build_evidence.json','layout_map.json','layout_records.json','held_pages.json','reported_examples.json','native_review.json','independent_review.json','defender_scan.json','검증결과.md']:
        shutil.copy2(W/name,E/'source'/name)
    for source in (W/'qa').glob('*.png'):shutil.copy2(source,E/'source'/source.name)
    shutil.copy2(W/'qa/fixture.json',E/'source/qa_fixture.json')
    for name in ['publish_page_lineflow_v2_20260917.py','build_page_lineflow_v2_20260917.py','stage_page_lineflow_v2_qa_20260917.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py','scan_page_lineflow_v2_20260917.ps1']:
        shutil.copy2(t.HERE/name,E/'source'/name)
    latest=p.read(R/'latest_worked_translation.json');full=p.read(Path(latest['translation_map']))
    proxy=p.read(t.INPUT/'proxy.json');rev={x['proxy_character']:x['unicode_character'] for x in proxy['mapping']}
    final_text=[''.join(rev.get(c,c) for c in b.decode('cp932')) for b in newraw]
    jp=[b.decode('cp932') for b in t.raw_messages((t.INPUT/'jp.ain').read_bytes())[3]]
    existing={x['numeric_id']:x for x in full['entries']};layout=p.read(W/'layout_map.json')
    for i,(a,b) in enumerate(zip(oldraw,newraw)):
        if a!=b and i not in existing:
            row={'stable_id':f'NightRemaster.ain::m[{i}]','kind':'message','numeric_id':i,'source':jp[i],'source_sha256':hashlib.sha256(jp[i].encode()).hexdigest(),'translation_required':True};full['entries'].append(row);existing[i]=row
    for i,row in existing.items():
        target=final_text[i]
        if row.get('target')!=target:
            row['target']=target;row['target_snapshot_provenance']='Exact installed MSG1; historical provider fields describe original draft only'
        # Prior comma-layout claims must not survive for pages now held intact.
        prior_layout=row.pop('layout_provenance',None)
        if prior_layout or target:row.pop('empty_target_reason',None)
        if str(i) in layout:
            row['layout_provenance']='Codex deterministic whole-page reflow v2; page text except whitespace exact'
            if not target:row['empty_target_reason']='Trailing physical MSG field; text retained earlier in the same unchanged MSG/R/A page'
    full['entries'].sort(key=lambda x:x['numeric_id']);h=hashlib.sha256()
    for row in full['entries']:h.update(row['stable_id'].encode());h.update(b'\0');h.update(row['target'].encode());h.update(b'\0')
    full.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),entry_count=len(full['entries']),target_character_count=sum(len(x['target']) for x in full['entries']),target_text_sequence_sha256=h.hexdigest(),installed_ain_sha256=after['NightRemaster.ain'],current_revision={'translator_model':'Codex internal','operation':'Existing semantic polish retained; deterministic whole-page layout only','native_status':'Isolated test launched; user took over and explicitly stopped automated UI control. Target dialogue, empty-tail and backlog visual verification incomplete.'})
    fullpath=E/'source/installed_translation_map.json';p.put(fullpath,p.js(full));p.put(E/'save_hashes_before.json',p.js(saves))
    journal={'status':'PREPARED','runtime':str(rt),'before':before,'after':after,'metadata':metadata,'fixture':fixture};p.put(E/'journal.json',p.js(journal))
    def write(path,data):
        assert path in snapshots
        journal.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(journal));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256']
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        revision={'status':STATUS,'time':now,'files':after,'evidence':str(E),'layout_pages':ev['counts']['changed_pages'],'layout_fields_from_semantic_polish':ev['layout_fields_from_polish'],'changed_fields_from_installed':ev['changed_fields_from_installed'],'message_count':100944,'outside_MSG1_exact':True,'page_content_except_whitespace_exact':True,'native_review':native,'save_files_unchanged':len(saves),'translator_model':'Codex internal','final_translation_map':str(fullpath),'final_translation_map_sha256':p.sha(fullpath)}
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,page_lineflow_v2_revision=revision,runtime_verified=False)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],page_lineflow_v2_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Whole-page reflow active. Special and ambiguous pages retained. User took over test window; target dialogue and empty-tail/backlog native verification remains pending.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in c:c[key]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
            c['page_lineflow_v2_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
        write(R/NEW,p.js(dict(revision,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Preserve installed MSG1 snapshot, including whole-page lineflow v2 and semantic polish. Rebuild from latest_worked_translation, never older per-line translation packets. CODE and all other runtime files retained.')))
        latest.update(runtime=str(rt),manifest=str(mp),manifest_sha256=mh,translation_map=str(fullpath),translation_map_sha256=p.sha(fullpath),ain_sha256=after['NightRemaster.ain'],instruction='Preserve installed MSG1, whole-page layout v2 and semantic polish; use this exact complete target snapshot for later builds.')
        write(R/'latest_worked_translation.json',p.js(latest));write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 전역 줄 배치 v2 기존 플레이 빌드 적용\n- 쉼표 기준 대신 일반 페이지 전체를 실제 글꼴 폭으로 재배치: {ev["counts"]["changed_pages"]:,}페이지. 의미·문자 순서 보존. 모호 경계·특수 서식 유지.\n- AIN {after["NightRemaster.ain"]}. MSG1 밖 바이트, 다른97개 파일, 세이브{len(saves)}개 보존. 독립검수·구조·폭·Defender·설치복구 fixture PASS.\n- 격리 테스트 실행 후 사용자가 직접 조작하며 자동 UI 조작 중단 지시. 제보 문장·빈 끝줄·백로그 최종 실기는 미확인. 모든 대상은 실제 폰트 폭 정적검증 통과.\n- 전체 번역지도와 유지계약 갱신. 복구: {E}.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf-8'))
        progress=p.read(t.WORK/'progress.json');progress.update(stage='installed_whole_page_lineflow_v2',live_install=True,installed_runtime=str(rt),installed_sha256=after['NightRemaster.ain'],backup=str(E/'before/NightRemaster.ain'));progress['page_lineflow_v2'].update(stage='installed_static_pass_native_pending',evidence=str(E),next='User controls isolated test; target dialogue and empty-tail/backlog visual check pending. Preserve installed snapshot for later builds.');write(t.WORK/'progress.json',p.js(progress))
        p.exact_tree(rt,nm['files']);assert p.snapshot_saves()==saves
        assert p.sha(recovery/'NightRemaster.ain')==rh and p.sha(rm)==keep['recovery_manifest_sha256']
        journal.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(journal))
    except BaseException as error:
        errors=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as x:errors.append(repr(x))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is None:
                    if path.exists():path.unlink()
                else:p.put(path,data)
            except BaseException as x:errors.append(repr(x))
        journal.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);p.put(E/'journal.json',p.js(journal));raise
    report={'status':STATUS,'runtime':str(rt),'files':after,'manifest_sha256':mh,'backup':str(E/'before/NightRemaster.ain'),'save_backup':str(save_backup),'unchanged_other_runtime_files':97,'unchanged_save_files':len(saves),'code_and_non_MSG1_exact':True,'native_dialogue_verified':False,'native_backlog_verified':False,'native_face_window_verified':False,'existing_save_load_verified':False,'fixture':fixture['status']}
    p.put(E/'publish_report.json',p.js(report));p.put(W/'publish_report.json',p.js(report))
    print(p.js(report).decode('utf-8'))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
