"""Install a one-file save-independent display fix in the stopped latest runtime."""
from pathlib import Path
import copy,datetime,json,shutil
from publish_remaster_multiplier_20260915 import put,js,replace_checked,processes
from publish_training_fix_20260915 import read,sha

W=Path(__file__).resolve().parent;O=W/'saved_name_refresh_20260915'
R=Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908');E=R/'evidence/saved_name_refresh_20260915'
STATUS='SAVED_DISPLAY_REFRESH_STATIC_PASS_NATIVE_PENDING'
CONTRACTS=['required_item_skill_names.json','required_dynamic_ui_text_fix.json','required_map_marker_axis_fix.json','required_location_card_aura_fix.json','required_build_retention.json','required_remaster_multiplier.json']

def main():
    ev=read(O/'build_evidence.json');qa=read(O/'verification.json');review=read(O/'independent_review.json')
    assert qa['status']=='COMPILED_GETTER_VM_PASS_NATIVE_PENDING' and review['status']=='STATIC_REVIEW_PASS'
    assert ev['files']==qa['files']==review['files'];new_ain=ev['files']['NightRemaster.ain'];assert sha(O/'NightRemaster.ain')==new_ain
    pointer=R/'ui_cumulative/current.json';p=read(pointer);assert p==ev['source_pointer'];mp=Path(p['manifest']);assert sha(mp)==p['manifest_sha256']
    m=read(mp);rt=Path(p['runtime']).resolve();assert rt==Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908/ui_cumulative/enemyscope_fbca7f090e72/runtime').resolve()
    keep=read(R/'required_build_retention.json');recovery=Path(keep['recovery_runtime']).resolve();assert recovery!=rt
    rm=Path(keep['recovery_manifest']);assert sha(rm)==keep['recovery_manifest_sha256'];rh=next(x['sha256'] for x in read(rm)['files'] if x['path']=='NightRemaster.ain');assert sha(recovery/'NightRemaster.ain')==rh
    oldfiles={x['path']:x for x in m['files']};assert len(oldfiles)==98
    assert {x.relative_to(rt).as_posix() for x in rt.rglob('*') if x.is_file()}==set(oldfiles)
    for n,row in oldfiles.items():assert sha(rt/n)==row['sha256'] and (rt/n).stat().st_size==row['size'],n
    assert oldfiles['NightRemaster.ain']['sha256']==ev['source_files']['NightRemaster.ain']
    assert not processes(),'Game still running: nothing applied'
    assert not E.exists(),'Existing evidence/journal must be inspected before retry'
    E.mkdir(parents=True);(E/'before').mkdir();(E/'candidate').mkdir();(E/'source').mkdir()
    snapshots={mp:mp.read_bytes(),pointer:pointer.read_bytes(),R/'progress.md':(R/'progress.md').read_bytes()}
    for n in CONTRACTS:snapshots[R/n]=(R/n).read_bytes()
    for path,data in snapshots.items():put(E/'before'/path.name,data)
    shutil.copy2(rt/'NightRemaster.ain',E/'before/NightRemaster.ain');assert sha(E/'before/NightRemaster.ain')==ev['source_files']['NightRemaster.ain']
    shutil.copy2(O/'NightRemaster.ain',E/'candidate/NightRemaster.ain');assert sha(E/'candidate/NightRemaster.ain')==new_ain
    names=['source_pointer.json','build_evidence.json','verification.json','independent_review.json','refresh_patch.jam','name_getter_call_sites.json','source.ex']
    names += [f'{kind}_{fid}.jam' for fid in ev['patched_function_ids'] for kind in ['original','built']]
    for n in names:shutil.copy2(O/n,E/'source'/n)
    for n in ['build_saved_name_refresh_20260915.py','verify_saved_name_refresh_20260915.py','publish_saved_name_refresh_20260915.py','publish_remaster_multiplier_20260915.py']:shutil.copy2(W/n,E/'source'/n)
    shutil.copy2(W/'translation_applied_check_20260915.json',E/'source/translation_applied_check_20260915.json')
    # Private save snapshots are analysis-only: keep just their hashes and finding.
    save_proof=dict(snapshot_asd_sha256=sha(O/'NightR07.snapshot.asd'),decoded_sha256=sha(O/'NightR07.snapshot.raw'),
        cached_old_name='아카나메',old_count=1,current_translation='때핥이',new_count=0,user_saves_modified=False)
    put(E/'source/resume_cache_finding.json',js(save_proof))
    frozen=[dict(path=str(f.relative_to(E)),sha256=sha(f),size=f.stat().st_size) for f in E.rglob('*') if f.is_file()];put(E/'frozen_index.json',js(frozen))
    journal=dict(status='PREPARED',runtime=str(rt),candidate_ain_sha256=new_ain,source_ain_sha256=ev['source_files']['NightRemaster.ain']);put(E/'journal.json',js(journal))
    assert not processes(),'Game reopened: prepared only'
    assert read(pointer)==p and sha(mp)==p['manifest_sha256']
    newcontract=R/'required_saved_display_refresh.json';assert not newcontract.exists();attempted=False
    try:
        attempted=True;replace_checked(E/'candidate/NightRemaster.ain',rt/'NightRemaster.ain',new_ain)
        now=datetime.datetime.now().astimezone().isoformat();nm=copy.deepcopy(m)
        revision=dict(status=STATUS,time=now,runtime=str(rt),source_ain_sha256=ev['source_files']['NightRemaster.ain'],candidate_ain_sha256=new_ain,
            previous_manifest=str(E/'before/manifest.json'),previous_manifest_sha256=p['manifest_sha256'],evidence=str(E),patched_function_ids=ev['patched_function_ids'],
            cached_name_root_cause=save_proof,EX_name_rows=512,compiled_getter_cases=qa['total_compiled_table_cases'],fallback_cases=qa['negative_missing_id_and_missing_field_fallback_cases'],
            description_only_reload_rows=qa['weapon_comment_rows'],existing_save_schema_and_gameplay_fields_preserved=True,
            all_100944_MSG1_and_reviewed10882_dialogue_corrections_preserved=True,remaster_multipliers_and_all_prior_fixes_preserved=True,
            native_verified=False,save_file_reloaded_in_native_engine=False,translator_model='Codex internal')
        nm.update(status=STATUS,time=now,runtime_verified=False,saved_display_refresh=revision)
        nm['ain'].update(candidate_sha256=new_ain,status=STATUS,saved_display_refresh=str(E/'source/build_evidence.json'),
            inherited_evidence_scope='Historical reviews remain bound to their frozen revisions. Current files are authoritative. This revision changes17 existing display/save-resume function addresses only; all globals, structures, original CODE bytes, MSG1 and pre-existing STR0 are retained.')
        for row in nm['files']:
            if row['path']=='NightRemaster.ain':row.update(sha256=new_ain,size=(rt/'NightRemaster.ain').stat().st_size)
        nm['next']='Load an existing save and confirm enemy 때핥이 plus current item/skill names and descriptions; independent multipliers remain preserved. Native save/display confirmation pending.'
        for row in nm['files']:assert sha(rt/row['path'])==row['sha256']
        put(mp,js(nm));mh=sha(mp)
        for n in CONTRACTS:
            path=R/n;c=read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:assert c[k]==p['manifest_sha256'];c[k]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=new_ain
            c['saved_display_refresh_overlay']=str(E/'source/build_evidence.json');put(path,js(c))
        contract=copy.deepcopy(revision);contract.update(manifest=str(mp),manifest_sha256=mh,required_files={'NightRemaster.ain':new_ain,'NightRemasterEX.ex':ev['source_files']['NightRemasterEX.ex']},
            instruction='Old resume saves retain translated names and descriptions in heap objects. Preserve the16 ID-bound current-EX display getters and existing after-load weapon-comment refresh. Do not reset gameplay data, inventory, known flags, structs or saved reward percentages. Keep latest translations and all previous fixes. Never validate only the EX file and claim old-save display is proven.')
        put(newcontract,js(contract));np=dict(p,status=STATUS,manifest_sha256=mh,runtime_verified=False);put(pointer,js(np))
        note=f'\n\n### {now[:10]} Old-save display name cache fix\n- User screenshot from latest runtime still showed 아카나메. Actual NightR07 resume snapshot contains old 아카나메 once and 때핥이 zero times; serialized C_Monster/weapon/skill objects retain old text. This contradicts earlier file-only assumption of native name application. Current EX512 names and all100944 MSG1 already matched approved data.\n- Repointed16 existing monster/weapon/equipment/skill display getters (including skill short text/descriptions) to current native EX fields by stable ID, with negative/missing-ID/field fallback to original member. Existing ExecAfterLoad additionally invokes original weapon-comment loader for143 rows; no LoadData, inventory/stat/known-flag reset. Existing global/structure/function signatures preserved; no new functions,1STR0 added, originalCODE/MSG1/STR0 prefix exact.\n- Compiled VM1560 table cases and78 fallback cases PASS; old-save stale 아카나메 fixture returns 때핥이 without mutating stored stats. Independent persisted-code review PASS. Native save/load/display still pending; no user-save writes or computer-use operations.\n- Existing 9/14 dialogue improvement10882 edits present; quality review remains408/686 packets (278/27655 body entries unreviewed), not a stale-dialogue-file regression. Do not claim full wording improvement complete.\n- Installed AIN only into {rt}; all98 runtime files verified,97 other files exact, latest/recovery only2 full runtimes remain. Four independent1..20 multipliers and all prior fixes retained. Evidence/backups: {E}. Manifest SHA256 {mh}.\n- Next: normal-context launch current.json, load existing save, verify battle label 때핥이 and weapon/skill names.\n'
        put(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        assert sha(recovery/'NightRemaster.ain')==rh and sha(rm)==keep['recovery_manifest_sha256']
        assert len(list((R/'ui_cumulative').glob('*/runtime')))==2
        assert read(pointer)['manifest_sha256']==sha(mp)
        for row in nm['files']:assert sha(rt/row['path'])==row['sha256']
        report=dict(status=STATUS,runtime=str(rt),manifest_sha256=mh,ain_sha256=new_ain,all98_files_verified=True,unchanged_files_exact=97,
            recovery_preserved=True,no_user_save_changes=True,no_new_full_build=True,native_verified=False,evidence=str(E))
        put(E/'publish_report.json',js(report));put(O/'publish_report.json',js(report));journal.update(status='COMMITTED',manifest_sha256=mh);put(E/'journal.json',js(journal));print(json.dumps(report,ensure_ascii=False,indent=2))
    except BaseException as e:
        failures=[]
        if attempted:
            try:replace_checked(E/'before/NightRemaster.ain',rt/'NightRemaster.ain',ev['source_files']['NightRemaster.ain'])
            except BaseException as x:failures.append(str(x))
        for path in reversed(list(snapshots)+[newcontract]):
            try:
                if path in snapshots:put(path,snapshots[path])
                elif path.exists():path.unlink()
            except BaseException as x:failures.append(str(x))
        journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(e),rollback_errors=failures);put(E/'journal.json',js(journal));raise

if __name__=='__main__':main()
