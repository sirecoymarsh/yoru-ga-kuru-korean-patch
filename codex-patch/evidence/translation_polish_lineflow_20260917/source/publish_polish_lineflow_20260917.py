"""User-authorized in-place MSG1 update with exact backup and project retention."""
from pathlib import Path
import collections,copy,datetime,hashlib,shutil,sys
import polish_translation_20260917 as t
import publish_mod_menu_style_20260917 as previous
import publish_cheat_menu_20260915 as p

R=t.ROOT;TRIAL=t.WORK/'global_lineflow_trial';O=TRIAL/'install_payload'
E=R/'evidence/translation_polish_lineflow_20260917'
CONTRACTS=previous.CONTRACTS+['required_mod_menu_style.json']
NEW='required_translation_polish_lineflow.json'
STATUS='TRANSLATION_POLISH_LINEFLOW_INSTALLED_NATIVE_PARTIAL'
p.R=R;p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);mp=Path(current['manifest']);rt=Path(current['runtime']).resolve()
    assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    tm=p.read(TRIAL/'manifest.json');before={'NightRemaster.ain':tm['baseline_sha256']};after={'NightRemaster.ain':tm['ain_sha256']}
    if E.exists():
        journal=p.read(E/'journal.json')
        assert journal['status']=='COMMITTED' and p.sha(ptr)==journal['committed_pointer_sha256']
        assert p.sha(rt/'NightRemaster.ain')==after['NightRemaster.ain']
        print('ALREADY_INSTALLED');return
    assert p.stopped(rt),'Exact target game is running; exit without losing unsaved play before applying'
    scan=p.read(TRIAL/'defender_scan.json');assert scan['completed']
    assert not [x for x in scan['after'] if any('global_lineflow_trial' in str(s) for s in x.get('Resources',[]))]
    for n,h in p.read(TRIAL/'output_inventory.json')['files'].items():assert p.sha(TRIAL/'output'/n)==p.sha(TRIAL/'scan_copy'/n)==h
    assert p.sha(TRIAL/'output/NightRemaster.ain')==after['NightRemaster.ain']
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    assert p.sha(rt/'NightRemaster.ain')==before['NightRemaster.ain']
    oldbytes=(rt/'NightRemaster.ain').read_bytes();newbytes=(TRIAL/'output/NightRemaster.ain').read_bytes()
    old,os,oe,oldraw=t.raw_messages(oldbytes);new,ns,ne,newraw=t.raw_messages(newbytes)
    assert old[:os+12]==new[:ns+12] and old[oe:]==new[ne:] and len(oldraw)==len(newraw)==100944
    assert sum(a!=b for a,b in zip(oldraw,newraw))==13671
    O.mkdir(exist_ok=True);shutil.copy2(TRIAL/'output/NightRemaster.ain',O/'NightRemaster.ain')
    fixture=p.fixture();saves=p.snapshot_saves()
    keep=p.read(R/'required_build_retention.json');recovery=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
    recovery_hash=p.sha(recovery/'NightRemaster.ain');assert p.sha(rm)==keep['recovery_manifest_sha256']
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for n in CONTRACTS:
        c=p.read(R/n)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in c:assert c[key]==current['manifest_sha256'],n
    E.mkdir(parents=True)
    for name in ['before','candidate','source']:(E/name).mkdir()
    assert not E.resolve().is_relative_to(rt) and not E.resolve().is_relative_to((TRIAL/'output').resolve())
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append({'path':str(path),'name':path.name,'existed':data is not None,'sha256':p.sha(path) if data is not None else None})
    for n in p.FILES:shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
    for source in [TRIAL/'manifest.json',TRIAL/'검증결과.md',TRIAL/'native_2247.png',TRIAL/'defender_scan.json',t.WORK/'global_lineflow_dry_run.json',t.WORK/'global_lineflow_dry_run_map.json',t.WORK/'build_manifest.json',t.WORK/'final_map.json',t.WORK/'changes.tsv',t.WORK/'reported_linebreak_audit.json']:
        shutil.copy2(source,E/'source'/source.name)
    for name in ['publish_polish_lineflow_20260917.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py','probe_global_lineflow_20260917.py','build_global_lineflow_trial_20260917.py']:
        shutil.copy2(t.HERE/name,E/'source'/name)
    # Preserve a compatible full translation map for later UI/gameplay rebuilds.
    latest=p.read(R/'latest_worked_translation.json');full=p.read(Path(latest['translation_map']))
    proxy=p.read(t.INPUT/'proxy.json');rev={x['proxy_character']:x['unicode_character'] for x in proxy['mapping']}
    final_text=[''.join(rev.get(c,c) for c in b.decode('cp932')) for b in newraw]
    jp=[b.decode('cp932') for b in t.raw_messages((t.INPUT/'jp.ain').read_bytes())[3]]
    existing={x['numeric_id']:x for x in full['entries']}
    corrections=p.read(t.WORK/'codex_corrections.json');proposals=p.read(t.WORK/'final_map.json');layout=p.read(t.WORK/'global_lineflow_dry_run_map.json')
    for i,(a,b) in enumerate(zip(oldraw,newraw)):
        if a==b:continue
        if i not in existing:
            entry={'stable_id':f'NightRemaster.ain::m[{i}]','kind':'message','numeric_id':i,'source':jp[i],'source_sha256':hashlib.sha256(jp[i].encode()).hexdigest(),'translation_required':True};full['entries'].append(entry);existing[i]=entry
    for i,entry in existing.items():
        target=final_text[i]
        if entry['target']!=target:
            entry['target']=target;entry['target_snapshot_provenance']='Exact installed MSG1; historical provider fields describe original draft only'
        if str(i) in proposals:entry['polish_provenance']='Codex internal' if str(i) in corrections else 'Existing user-provided Claude/Fable proposal'
        if str(i) in layout:
            entry['layout_provenance']='Codex deterministic comma-continuation reflow; page text except whitespace exact'
            if not target:entry['empty_target_reason']='Approved trailing physical field; its content is preserved earlier in the same MSG/R/A page'
    full['entries'].sort(key=lambda x:x['numeric_id'])
    h=hashlib.sha256()
    for entry in full['entries']:h.update(entry['stable_id'].encode());h.update(b'\0');h.update(entry['target'].encode());h.update(b'\0')
    full.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),entry_count=len(full['entries']),target_character_count=sum(len(x['target']) for x in full['entries']),target_text_sequence_sha256=h.hexdigest(),installed_ain_sha256=after['NightRemaster.ain'],current_revision={'translator_model':'Codex internal','retained_external_proposals':'User-provided Claude/Fable proposal fields are individually marked','operation':'Reviewed polish plus common-rule layout','native_status':'representative dialogue passed; backlog pending'})
    fullpath=E/'source/installed_translation_map.json';p.put(fullpath,p.js(full))
    p.put(E/'save_hashes_before.json',p.js(saves))
    journal={'status':'PREPARED','runtime':str(rt),'before':before,'after':after,'metadata':metadata,'fixture':fixture}
    p.put(E/'journal.json',p.js(journal))
    def write(path,data):
        assert path in snapshots
        journal.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(journal));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256']
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        revision={'status':STATUS,'time':now,'files':after,'evidence':str(E),'semantic_polish_fields':3076,'layout_pages':5463,'layout_fields':11387,'total_changed_fields':13671,'message_count':100944,'outside_MSG1_exact':True,'page_content_except_whitespace_exact_for_layout':True,'native_dialogue_observed_ids':[2247,2248],'native_backlog_verified':False,'save_files_unchanged':len(saves),'translator_model':'Codex internal','final_translation_map':str(fullpath),'final_translation_map_sha256':p.sha(fullpath)}
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,translation_polish_lineflow_revision=revision,runtime_verified=False)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],translation_polish_lineflow_overlay=str(E/'source/manifest.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Continue from existing saves; verify empty-tail paragraph and backlog during ordinary play. Full native game verification is not claimed.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in c:c[key]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
            c['translation_polish_lineflow_overlay']=str(E/'source/manifest.json')
            write(R/n,p.js(c))
        write(R/NEW,p.js(dict(revision,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Preserve the exact MSG1 polish and common-rule lineflow snapshot in subsequent builds. Game CODE, all non-MSG1 data and 97 other runtime files were retained. Do not restore older field splits from translation packets.')))
        latest.update(runtime=str(rt),manifest=str(mp),manifest_sha256=mh,translation_map=str(fullpath),translation_map_sha256=p.sha(fullpath),ain_sha256=after['NightRemaster.ain'],instruction='Preserve this installed MSG1 snapshot including Codex polish and common-rule layout; historical external drafting provenance is retained per entry.')
        write(R/'latest_worked_translation.json',p.js(latest))
        write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 번역 교정·전역 줄 배치 기존 플레이 빌드 적용\n- 사용자 명시 승인으로 AIN 한 파일 적용. {after["NightRemaster.ain"]}. 기존 교정3,076항목 및 공통 재배치5,463페이지/11,387필드 포함; 기존 기준본 대비13,671필드 차이.\n- MSG1 밖 원본 바이트와 다른97개 파일 및 세이브{len(saves)}개 해시 보존. 구조/폭/인코딩·Defender·설치복구fixture PASS. 대사2247–2248 실기 확인, 빈 끝줄·백로그 실기는 미완료.\n- 전체 번역지도와 latest_worked_translation, current 및 유지계약 갱신. 복구: {E}.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf-8'))
        p.exact_tree(rt,nm['files']);assert p.snapshot_saves()==saves
        assert p.sha(recovery/'NightRemaster.ain')==recovery_hash and p.sha(rm)==keep['recovery_manifest_sha256']
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
    report={'status':STATUS,'runtime':str(rt),'files':after,'manifest_sha256':mh,'backup':str(E/'before/NightRemaster.ain'),'unchanged_other_runtime_files':97,'unchanged_save_files':len(saves),'code_and_non_MSG1_exact':True,'native_backlog_verified':False,'fixture':fixture['status']}
    p.put(E/'publish_report.json',p.js(report));p.put(TRIAL/'publish_report.json',p.js(report))
    progress=p.read(t.WORK/'progress.json');progress.update(stage='installed_polish_and_global_lineflow',live_install=True,installed_runtime=str(rt),installed_sha256=after['NightRemaster.ain'],backup=str(E/'before/NightRemaster.ain'));progress['global_lineflow']['live_installed']=True;p.put(t.WORK/'progress.json',p.js(progress))
    print(p.js(report).decode('utf-8'))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
