"""Hash-bound cumulative install; external full save backup, exact rollback."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import polish_translation_20260917 as t
import publish_page_lineflow_v2_20260917 as previous
import publish_cheat_menu_20260915 as p
R=t.ROOT;W=R/'staging/name_particles_20260917';O=W/'install_payload';E=R/'evidence/name_particles_20260917'
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_name_particles.json'
STATUS='NAME_PARTICLES_INSTALLED_COMPILED_PASS_NATIVE_PENDING'
p.R=R;p.O=O;p.E=E;p.FILES=['NightRemaster.ain']
def main():
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);mp=Path(current['manifest']);rt=Path(current['runtime']).resolve()
    ev=p.read(W/'build_evidence.json');before={'NightRemaster.ain':ev['source_ain_sha256']};after={'NightRemaster.ain':ev['ain_sha256']}
    assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert p.sha(rt/'NightRemaster.ain')==after['NightRemaster.ain'];print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(W/'source_pointer.json')
    assert p.stopped(rt),'Target game is running; exit normally before installation'
    qa=p.read(W/'verification.json');review=p.read(W/'independent_review.json');scan=p.read(W/'defender_scan.json')
    assert qa['status']=='COMPILED_JAM_AND_CORPUS_PASS' and review['status']=='PASS'
    assert qa['ain_sha256']==review['ain_sha256']==ev['ain_sha256']
    assert scan['status']=='SCANNED_NO_TARGET_DETECTIONS' and scan['files']==after and not scan['after']
    assert p.sha(W/'output/NightRemaster.ain')==p.sha(W/'scan_copy/NightRemaster.ain')==ev['ain_sha256']
    assert ev['all_MSG1_100944_exact'] and ev['old_CODE_prefix_exact'] and ev['globals_and_structures_exact'] and ev['save_schema_changes']==0
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98 and p.sha(rt/'NightRemaster.ain')==before['NightRemaster.ain']
    assert t.raw_messages((rt/'NightRemaster.ain').read_bytes())[3]==t.raw_messages((W/'output/NightRemaster.ain').read_bytes())[3]
    O.mkdir(exist_ok=True);shutil.copy2(W/'output/NightRemaster.ain',O/'NightRemaster.ain');fixture=p.fixture();saves=p.snapshot_saves()
    keep=p.read(R/'required_build_retention.json');recovery=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest']);rh=p.sha(recovery/'NightRemaster.ain');assert p.sha(rm)==keep['recovery_manifest_sha256']
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
    save_backup=E/'before/saves';save_backup.mkdir()
    for name,h in saves.items():
        src=p.SAVE/name;dst=save_backup/name;dst.parent.mkdir(parents=True,exist_ok=True);assert p.sha(src)==h;shutil.copy2(src,dst);assert p.sha(dst)==h
    assert p.snapshot_saves()==saves
    for name in ['build_evidence.json','verification.json','independent_review.json','defender_scan.json','format_changes.json','format_consumers.json','name_entry_scalars.json','native_opcode_audit.json','reversible_hook_edits.json','helpers_readable.jaf','helpers_proxy.jaf','patch.jam','검증결과.md']:
        shutil.copy2(W/name,E/'source'/name)
    for name in ['publish_name_particles_20260917.py','build_name_particles_20260917.py','verify_name_particles_20260917.py','name_particles_helpers_20260917.jaf','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py','scan_name_particles_20260917.ps1']:
        shutil.copy2(t.HERE/name,E/'source'/name)
    # Keep the complete semantic/layout snapshot identical; only bind its runtime provenance.
    latest=p.read(R/'latest_worked_translation.json');full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256']
    full['installed_ain_sha256']=ev['ain_sha256'];full['runtime_particle_revision']={'translator_model':'Codex internal','operation':'Runtime particle selection only; all MSG targets and semantic/layout provenance retained','evidence':str(E),'format_changes':str(E/'source/format_changes.json'),'new_save_schema_fields':0,'native_verified':False}
    fullpath=E/'source/installed_translation_map.json';p.put(fullpath,p.js(full));assert p.read(fullpath)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));journal={'status':'PREPARED','runtime':str(rt),'before':before,'after':after,'metadata':metadata,'fixture':fixture};p.put(E/'journal.json',p.js(journal))
    def write(path,data):
        assert path in snapshots
        journal.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(journal));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        revision={'status':STATUS,'time':now,'files':after,'evidence':str(E),'patched_existing_function_ids':ev['patched_existing_function_ids'],'helper_function_ids':ev['helper_function_ids'],'format_string_count':ev['format_string_count'],'all_MSG1_100944_exact':True,'old_CODE_prefix_exact':True,'save_schema_changes':0,'supported_hangul_syllables':ev['supported_hangul_syllables'],'verification_counts':qa['counts'],'save_files_unchanged':len(saves),'save_backup':str(save_backup),'translator_model':'Codex internal','native_verified':False,'existing_save_load_verified':False}
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,name_particles_revision=revision,runtime_verified=False);nm['ain'].update(status=STATUS,candidate_sha256=ev['ain_sha256'],name_particles_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Player/monster Korean particles selected at display time. Existing saves retained; native rendering and actual save load remain user verification items.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in c:c[key]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=ev['ain_sha256']
            c['name_particles_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
        write(R/NEW,p.js(dict(revision,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Preserve runtime josa hooks, appended helpers and marked STR0 formats together. Start future builds from this AIN; never apply marked formats without their resolver. Preserve all prior MSG1 polish/lineflow and original save schema.')))
        latest.update(runtime=str(rt),manifest=str(mp),manifest_sha256=mh,translation_map=str(fullpath),translation_map_sha256=p.sha(fullpath),ain_sha256=ev['ain_sha256'],name_particles_overlay=str(E/'source/build_evidence.json'),instruction='Preserve complete MSG1 snapshot and runtime name-particle CODE/STR0 overlay. Always rebuild from latest cumulative AIN and its required contracts.')
        write(R/'latest_worked_translation.json',p.js(latest));write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 주인공·몬스터 이름 조사 선택 적용\n- 현재 한글2364음절 받침/ㄹ 판정, 기존 이름 치환1함수 및 표시2함수에 연결. 표시형식19개, 신규 순수도우미8개.\n- MSG1 100,944개·기존 CODE 원본 구간·전역/구조체/기존 함수서명 보존. 세이브{len(saves)}개 전체 외부 백업 및 전후 해시 동일. 다른97개파일 보존.\n- 실제 빌드 JAM 실행, 모든 한글·몬스터85종·현재 이름치환·독립검수·Defender·설치복구 fixture 통과. 네이티브 화면/실제 세이브 로드 미검증.\n- AIN {ev["ain_sha256"]}. 복구/검증: {E}.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf-8'));progress=p.read(t.WORK/'progress.json');progress.update(stage='installed_name_particles',installed_runtime=str(rt),installed_sha256=ev['ain_sha256'],backup=str(E/'before/NightRemaster.ain'));progress['name_particles']={'stage':'installed_compiled_pass_native_pending','work':str(W),'evidence':str(E),'next':'User checks names with/without 받침 in existing save and battle; no automated UI control performed in this task.'};write(t.WORK/'progress.json',p.js(progress))
        p.exact_tree(rt,nm['files']);assert p.snapshot_saves()==saves;assert p.sha(recovery/'NightRemaster.ain')==rh and p.sha(rm)==keep['recovery_manifest_sha256']
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
    report={'status':STATUS,'runtime':str(rt),'files':after,'manifest_sha256':mh,'backup':str(E/'before/NightRemaster.ain'),'save_backup':str(save_backup),'unchanged_other_runtime_files':97,'unchanged_save_files':len(saves),'MSG1_exact':True,'save_schema_changes':0,'native_verified':False,'existing_save_load_verified':False,'fixture':fixture['status']};p.put(E/'publish_report.json',p.js(report));p.put(W/'publish_report.json',p.js(report));print(p.js(report).decode('utf-8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
