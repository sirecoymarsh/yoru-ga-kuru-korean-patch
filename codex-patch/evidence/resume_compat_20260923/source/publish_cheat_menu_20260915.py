"""Hash-bound two-file live revision, external backup, no save writes or new runtime."""
from pathlib import Path
import copy,datetime,hashlib,os,shutil,sys,tempfile
from publish_remaster_multiplier_20260915 import put,js,replace_checked,processes,read,sha

W=Path(__file__).resolve().parent
O=W/'cheat_menu_20260915'; C=W/'consume_saved_display_20260915'
R=Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908')
E=R/'evidence/cheat_menu_20260915'
RT=R/'ui_cumulative/enemyscope_fbca7f090e72/runtime'
SAVE=Path('C:/Users/CadriacLord/OneDrive/문서/AliceSoft/밤이 온다! -Square of the MOON- Remastered/SaveData_KR_UI_Integrated_20260913')
FILES=['NightRemaster.ain','NightRemasterPact.afa']
CONTRACTS=['required_item_skill_names.json','required_dynamic_ui_text_fix.json','required_map_marker_axis_fix.json','required_location_card_aura_fix.json','required_build_retention.json','required_remaster_multiplier.json','required_saved_display_refresh.json']
NEWCONTRACTS=['required_consumable_display_fix.json','required_cheat_menu.json']
STATUS='CHEAT_MENU_AND_CONSUMABLE_STATIC_PASS_NATIVE_PENDING'

def active_target(rows,rt):
    exe=(rt/'NightRemaster.exe').resolve()
    # Unknown executable path is fail-closed; a known different install is not blocked.
    return [x for x in rows if not x.get('ExecutablePath') or Path(x['ExecutablePath']).resolve()==exe]

def stopped(rt):
    return not active_target(processes(),rt)

def exact_tree(rt,rows):
    assert rt==rt.resolve(),('redirected runtime',rt)
    for parent in [rt,*rt.parents]:
        assert not getattr(parent.stat(),'st_file_attributes',0)&0x400,('reparse ancestor',parent)
    expected={r['path'] for r in rows}
    assert {p.relative_to(rt).as_posix() for p in rt.rglob('*') if p.is_file()}==expected
    for r in rows:
        p=(rt/r['path']).resolve();assert p.is_relative_to(rt)
        assert p.stat().st_size==r['size'] and sha(p)==r['sha256'],p

def snapshot_saves():
    assert SAVE.is_dir(),SAVE
    return {p.relative_to(SAVE).as_posix():sha(p) for p in SAVE.rglob('*') if p.is_file()}

def pair_apply(src,backup,live,before,after,fail_after=0):
    # Validate every source and backup before writing any destination.
    for n in FILES:
        assert sha(src/n)==after[n],('payload',n)
        assert sha(backup/n)==before[n],('backup',n)
        assert sha(live/n)==before[n],('baseline',n)
    attempted=[]
    try:
        for n in FILES:
            attempted.append(n);replace_checked(src/n,live/n,after[n])
            if len(attempted)==fail_after:raise RuntimeError('fixture injected replacement failure')
    except BaseException:
        for n in reversed(attempted):replace_checked(backup/n,live/n,before[n])
        raise

def pair_restore(backup,live,before,after):
    for n in FILES:
        assert sha(backup/n)==before[n],('tampered backup',n)
        assert sha(live/n) in [before[n],after[n]],('unknown live state',n)
    # These two names are created only by replace_checked and were absent from
    # the exact pre-install runtime. Preserve interrupted copies outside it.
    for n in FILES:
        tmp=live/(n+'.multiplier-copy.tmp')
        if tmp.exists():
            assert tmp.resolve().parent==live.resolve() and tmp.is_file()
            assert not getattr(tmp.stat(),'st_file_attributes',0)&0x400
            quarantine=backup.parent/'interrupted_incoming';quarantine.mkdir(exist_ok=True)
            assert not quarantine.resolve().is_relative_to(live.resolve())
            dest=quarantine/(tmp.name+'.'+sha(tmp)[:12]+'.'+str(datetime.datetime.now().timestamp()))
            tmp.replace(dest)
    for n in FILES:
        if sha(live/n)!=before[n]:replace_checked(backup/n,live/n,before[n])

def fixture():
    f=Path(tempfile.mkdtemp(prefix='복구 검증 ',dir=O));b=f/'backup';s=f/'payload';l=f/'live'
    for p in [b,s,l]:p.mkdir()
    for i,n in enumerate(FILES):
        (b/n).write_bytes(('old '+n).encode());shutil.copy2(O/n,s/n);shutil.copy2(b/n,l/n)
    before={n:sha(b/n) for n in FILES};after={n:sha(s/n) for n in FILES}
    pair_apply(s,b,l,before,after);assert all(sha(l/n)==after[n] for n in FILES)
    pair_restore(b,l,before,after);pair_restore(b,l,before,after)
    try:pair_apply(s,b,l,before,after,fail_after=1)
    except RuntimeError:pass
    else:raise AssertionError('failure not injected')
    assert all(sha(l/n)==before[n] for n in FILES)
    # Simulated interruption after first atomic replacement: reconstruct from hashes.
    replace_checked(s/FILES[0],l/FILES[0],after[FILES[0]]);pair_restore(b,l,before,after)
    # Simulated interruption during incoming copy, both before and after install.
    for installed in [False,True]:
        if installed:pair_apply(s,b,l,before,after)
        (l/(FILES[0]+'.multiplier-copy.tmp')).write_bytes(b'partial interrupted copy')
        pair_restore(b,l,before,after)
        assert all(sha(l/n)==before[n] for n in FILES) and not list(l.glob('*.tmp'))
    for kind,folder,op in [('payload',s,lambda:pair_apply(s,b,l,before,after)),('baseline',l,lambda:pair_apply(s,b,l,before,after)),('backup',b,lambda:pair_restore(b,l,before,after))]:
        n=FILES[-1];saved=(folder/n).read_bytes();(folder/n).write_bytes(b'tampered')
        state={name:sha(l/name) for name in FILES}
        try:op()
        except AssertionError:pass
        else:raise AssertionError('tampering accepted: '+kind)
        assert state=={name:sha(l/name) for name in FILES};(folder/n).write_bytes(saved)
    assert not active_target([dict(ExecutablePath=str(f/'elsewhere/NightRemaster.exe'))],l)
    assert active_target([dict(ExecutablePath=str(l/'NightRemaster.exe'))],l)
    assert not list(l.glob('*.tmp'))
    metadata_interruption_fixture(f,s,b,l,before,after)
    result=dict(status='TRANSACTION_FIXTURE_PASS',fixture=str(f),payload=after,install_restore=True,idempotent_restore=True,known_mixed_and_interruption_restore=True,partial_incoming_copy_recovered=True,interrupted_metadata_restoration_resumable=True,nth_replacement_rollback=True,tampered_payload_baseline_backup_rejected=True,exact_process_path_filter=True,unicode_spaces_path=True,no_incoming_residue=True,zip='not applicable: live data-only installation; no archive emitted')
    put(O/'transaction_verification.json',js(result));return result

def restore():
    j=read(E/'journal.json');rt=Path(j['runtime']).resolve();assert rt==RT.resolve() and stopped(rt)
    if j['status']=='RESTORED':
        assert all(sha(rt/n)==j['before'][n] for n in FILES);print('ALREADY_RESTORED');return
    assert j['status'] in ['COMMITTED','PREPARED','ROLLBACK_INCOMPLETE','RESTORING']
    ptr=R/'ui_cumulative/current.json'
    # Validate every current metadata file against a known before/after state.
    # A RESTORING journal stays retryable even after current.json was restored.
    for row in j['metadata']:
        path=Path(row['path']);assert path.resolve().is_relative_to(R.resolve())
        if row['existed']:assert sha(E/'before'/row['name'])==row['sha256']
        current=sha(path) if path.exists() else None
        allowed={row['sha256'],j.get('metadata_after',{}).get(str(path),row['sha256'])}
        assert current in allowed,('A newer or unknown metadata state exists',str(path))
    j['status']='RESTORING';put(E/'journal.json',js(j))
    pair_restore(E/'before',rt,j['before'],j['after'])
    for row in j['metadata']:
        path=Path(row['path']);assert path.resolve().is_relative_to(R.resolve())
        if row['existed']:put(path,(E/'before'/row['name']).read_bytes())
        elif path.exists():path.unlink()
    assert all(sha(rt/n)==j['before'][n] for n in FILES)
    j['status']='RESTORED';put(E/'journal.json',js(j));print('RESTORED EXACT PRE-PATCH STATE')

def metadata_interruption_fixture(f,s,b,l,before,after):
    """Exercise the actual restorer against a disposable fake project/journal."""
    global R,E,RT,stopped,put
    saved_globals=(R,E,RT,stopped,put);real_put=put
    try:
        R=f;E=f/'restore_evidence';RT=l;stopped=lambda rt:True
        (E/'before').mkdir(parents=True);(f/'ui_cumulative').mkdir()
        ptr=f/'ui_cumulative/current.json';note=f/'progress.md';meta=[];newhash={}
        for p in [ptr,note]:
            old=b'old metadata '+p.name.encode();new=b'new metadata '+p.name.encode()
            (E/'before'/p.name).write_bytes(old);p.write_bytes(new)
            meta.append(dict(path=str(p),name=p.name,existed=True,sha256=sha(E/'before'/p.name)));newhash[str(p)]=sha(p)
        for n in FILES:shutil.copy2(b/n,E/'before'/n)
        pair_apply(s,b,l,before,after)
        real_put(E/'journal.json',js(dict(status='COMMITTED',runtime=str(l),before=before,after=after,metadata=meta,metadata_after=newhash,committed_pointer_sha256=sha(ptr))))
        def interrupted_put(p,data):
            real_put(p,data)
            if p==ptr:raise RuntimeError('fixture interrupted after restoring pointer')
        put=interrupted_put
        try:restore()
        except RuntimeError:pass
        else:raise AssertionError('metadata interruption not injected')
        put=real_put;assert read(E/'journal.json')['status']=='RESTORING'
        restore();restore()
        assert read(E/'journal.json')['status']=='RESTORED'
        assert all(sha(Path(x['path']))==x['sha256'] for x in meta)
        assert all(sha(l/n)==before[n] for n in FILES)
    finally:R,E,RT,stopped,put=saved_globals

def main():
    ev=read(O/'build_evidence.json');qa=read(O/'verification.json')
    assert qa['status']=='STATIC_COMPILED_HELPERS_AND_LAYOUT_PASS'
    for name,status in [('independent_review.json','STATIC_REVIEW_PASS'),('visual_review.json','STATIC_FONT_GEOMETRY_VISUAL_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        x=read(O/name);assert x['status']==status and x['files']==ev['files']
    after=ev['files'];assert qa['files']==after and all(sha(O/n)==after[n] for n in FILES)
    ce=read(C/'build_evidence.json');cq=read(C/'verification.json');cr=read(C/'independent_review.json')
    assert cq['status']=='CONSUMABLE_COMPILED_VM_AND_CONSUMER_CLOSURE_PASS' and cr['status']=='STATIC_REVIEW_PASS'
    assert ce['files']==cq['files']==cr['files'] and sha(C/'NightRemaster.ain')==ev['source_ain']==ce['files']['NightRemaster.ain']
    if E.exists():
        j=read(E/'journal.json')
        if j['status']=='COMMITTED' and all(sha(RT/n)==after[n] for n in FILES):
            assert sha(R/'ui_cumulative/current.json')==j['committed_pointer_sha256'];print('ALREADY_INSTALLED');return
        raise AssertionError('Inspect existing transaction; never overwrite recovery evidence')
    ptr=R/'ui_cumulative/current.json';p=read(ptr);assert p==ev['source_pointer']==ce['source_pointer']
    mp=Path(p['manifest']);assert sha(mp)==p['manifest_sha256'];m=read(mp);rt=Path(p['runtime']).resolve();assert rt==RT.resolve()
    if not stopped(rt):
        print(js(dict(status='READY_WAITING_FOR_GAME_EXIT',runtime=str(rt),live_modified=False)).decode('utf8'));return
    fx=fixture();exact_tree(rt,m['files']);assert len(m['files'])==98
    before={n:next(r['sha256'] for r in m['files'] if r['path']==n) for n in FILES}
    assert before['NightRemaster.ain']==ce['source_files']['NightRemaster.ain']
    keep=read(R/'required_build_retention.json');rec=Path(keep['recovery_runtime']).resolve();rm=Path(keep['recovery_manifest']);assert rec!=rt and sha(rm)==keep['recovery_manifest_sha256']
    rh={n:sha(rec/n) for n in FILES};recrows={r['path']:r['sha256'] for r in read(rm)['files']}
    assert all(rh[n]==recrows[n] for n in FILES)
    assert len(list((R/'ui_cumulative').glob('*/runtime')))==2
    saved=snapshot_saves()
    E.mkdir(parents=True);assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for name in ['before','candidate','source','source/consumable']:(E/name).mkdir()
    paths=[mp,ptr,R/'progress.md']+[R/n for n in CONTRACTS+NEWCONTRACTS]
    snapshots={path:path.read_bytes() if path.exists() else None for path in paths}
    assert all(snapshots[R/n] is None for n in NEWCONTRACTS)
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=sha(path) if data is not None else None))
    for n in FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
        assert sha(E/'before'/n)==before[n] and sha(E/'candidate'/n)==after[n]
    # Freeze sources/reviews, not scan/fixture directories or another full runtime.
    for source,target in [(O,E/'source'),(C,E/'source/consumable')]:
        for f in source.iterdir():
            if f.is_file() and f.suffix in ['.json','.jam','.jaf','.pactex','.x','.png']:shutil.copy2(f,target/f.name)
    for name in ['cheat_support_20260915.py','build_cheat_menu_20260915.py','verify_cheat_menu_20260915.py','render_cheat_menu_proof_20260915.py','publish_cheat_menu_20260915.py','scan_cheat_payload_20260915.ps1','build_consume_saved_display_20260915.py','verify_consume_saved_display_20260915.py','publish_remaster_multiplier_20260915.py']:
        shutil.copy2(W/name,E/'source'/name)
    put(E/'save_hashes_before.json',js(saved))
    journal=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fx)
    put(E/'journal.json',js(journal))
    def metadata_put(path,data):
        assert path in snapshots
        journal.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest()
        # Journal each intended metadata hash BEFORE its atomic replacement.
        put(E/'journal.json',js(journal));put(path,data)
    put(E/'frozen_index.json',js([dict(path=f.relative_to(E).as_posix(),sha256=sha(f),size=f.stat().st_size) for f in E.rglob('*') if f.is_file() and f.name!='journal.json']))
    attempted=False
    try:
        assert stopped(rt),'Game reopened: no runtime changes'
        assert read(ptr)==p and sha(mp)==p['manifest_sha256']
        attempted=True;pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat();nm=copy.deepcopy(m)
        rev=dict(status=STATUS,time=now,runtime=str(rt),evidence=str(E),previous_manifest=str(E/'before/manifest.json'),previous_manifest_sha256=p['manifest_sha256'],files=after,
            native_verified=False,translator_model='Codex internal',features=['instant ordinary trap disarm','integer battle speed1..5 slider','actual auto-battle calculation with hidden presentation and original results','next-floor shortest walkable route overlay'],
            defaults='all toggles off, battle speed1',quick_battle='not forced victory; exclude first tutorial/event battle; right-click or15s watchdog restores presentation',
            route='separate path buffer, no fog/seen/search/auto-move-queue writes',changed_existing_functions=ev['AIN']['patched_existing'],added_functions=ev['AIN']['added_functions'],changed_PACT_entries=[123],
            save_schema_unchanged=True,original_reward_sliders_and_display_getters_preserved=True,source_consumable_ain=ev['source_ain'])
        consume=dict(status=STATUS,time=now,evidence=str(E/'source/consumable'),source_reviewed_ain=ev['source_ain'],integrated_ain=after['NightRemaster.ain'],patched_function_ids=ce['patched_function_ids'],consumable_ids=[1,2,3,4,5],
            approved_name_catalog_coverage=cq['approved_name_catalog_coverage'],unknown_id_keeps_original_field=True,inventory_and_save_data_unchanged=True,native_verified=False,translator_model='Codex internal')
        nm.update(status=STATUS,time=now,runtime_verified=False,cheat_menu_revision=rev,consumable_saved_display_fix=consume)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],cheat_menu_overlay=str(E/'source/build_evidence.json'),consumable_display_fix=str(E/'source/consumable/build_evidence.json'),
            inherited_evidence_scope='Historical evidence remains bound to its revision. This cumulative AIN includes the pending8-function consumable display fix,14 existing cheat hook overrides and25 new helper functions. Original messages/code prefix and serialized structure/global schema retained; current files manifest is authoritative.')
        nm['cheat_pact_overlay']=dict(entry=123,sha256=after['NightRemasterPact.afa'],other184_entries_exact=True,evidence=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Native test on existing save: Settings > Game settings, speed1..5, three toggles, save/reload, normal/event battle, quick cancel/results, trap and route. No new game required; full dialogue-polish audit is not complete.'
        metadata_put(mp,js(nm));mh=sha(mp)
        for n in CONTRACTS:
            path=R/n;c=read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:assert c[k]==p['manifest_sha256'];c[k]=mh
            for name in FILES:
                if name in c.get('required_files',{}):c['required_files'][name]=after[name]
            c['cheat_menu_overlay']=str(E/'source/build_evidence.json');c['consumable_display_fix_overlay']=str(E/'source/consumable/build_evidence.json');metadata_put(path,js(c))
        metadata_put(R/NEWCONTRACTS[0],js(dict(consume,manifest=str(mp),manifest_sha256=mh,required_files={'NightRemaster.ain':after['NightRemaster.ain']},instruction='Preserve all6 ID1..5 consumable getters and2 material-description literals independently of stale save fields. Do not reset inventory, quantities, stats or saves. No new game required.')))
        metadata_put(R/NEWCONTRACTS[1],js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Rebase future changes from current.json. Preserve native Game settings controls and all4 cheat features. Keep original auto battle AI/rewards/defeat; never force a win. Event and first tutorial stay visible. Keep1..20 reward sliders and Korean display fixes. Scratch87/88/89/94/97/98 are reset at load, preferences90..93 persist in existing sysFlag array; no serialized schema changes. Native verification pending.')))
        metadata_put(ptr,js(dict(p,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now[:10]} Native cheat controls + consumable cache fix integrated\n- Latest runtime remains {rt}; no extra full build. AIN {after[FILES[0]]}, PACT {after[FILES[1]]}. Manifest {mh}.\n- Four requested controls on Game settings(123): ordinary trap instant disarm plus explicit relief fast path; integer battle speed1..5; result-only real auto battle(not forced victory); next-floor shortest route in a separate overlay buffer. All defaults OFF/speed1. Event battles and first tutorial remain original; cancel/right-click or15s watchdog restores battle presentation. Scaled-frame clamp means measured quick-battle performance is NOT established yet. No save schema/stat/inventory rewriting; normal AI and reward/defeat processing remain original.\n- Pending consumable fix is included:6 getters IDs26668/26669/26671/26672/26680/26681 and2 literals31454/31481, five names 반달 환약/달의 물방울/달빛 수정/보름달 환약/카샤의 영약. Existing-save getters, not save migration; no new game required. Source reviewed AIN {ev["source_ain"]}.\n- Compiled VM7071calls,500slider roundtrips,24quick cases,72trap cases,6route fixtures; bounds/cancel/clock wrap tests PASS. Independent final AIN and PACT reviews PASS. Actual FNL glyph/geometry proof viewed; not a game capture. Defender disposable-payload scan and two-file rollback/tamper/interruption fixture PASS. Only PACT123 changed; other184 entries including reward-slider125 exact; original UI raster/font/fog/opening and all100944MSG1 retained.\n- The earlier1782 candidate was rejected for extra POP after void setters; final e103 fixes all known instances. No native gameplay/control/save-reload test claimed. Evidence/backups: {E}.\n- Next executable step: launch latest runtime, load existing save, open Game settings and test each option individually, then quick normalbattle results/defeat/cancel and route in fog/no-exit maps. Confirm the5 consumable names. Full dialogue polish remains408/686packets; do not call whole localization audit complete.\n'
        metadata_put(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        exact_tree(rt,nm['files']);assert saved==snapshot_saves(),'Save data changed during publication'
        assert sha(rm)==keep['recovery_manifest_sha256'] and all(sha(rec/n)==rh[n] for n in FILES)
        assert len(list((R/'ui_cumulative').glob('*/runtime')))==2 and sha(mp)==read(ptr)['manifest_sha256']
        journal.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=sha(ptr));put(E/'journal.json',js(journal))
    except BaseException as err:
        failures=[]
        if attempted:
            try:pair_restore(E/'before',rt,before,after)
            except BaseException as x:failures.append(repr(x))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:put(path,data)
                elif path.exists():path.unlink()
            except BaseException as x:failures.append(repr(x))
        journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(err),rollback_errors=failures);put(E/'journal.json',js(journal));raise
    report=dict(status=STATUS,runtime=str(rt),manifest_sha256=mh,files=after,all98_runtime_files_verified=True,unchanged_runtime_files_exact=96,save_files_hashes_unchanged=len(saved),recovery_build_unchanged=True,new_game_required=False,native_verified=False,evidence=str(E))
    put(E/'publish_report.json',js(report));put(O/'publish_report.json',js(report));print(js(report).decode('utf8'))

if __name__=='__main__':
    if '--fixture' in sys.argv:print(js(fixture()).decode('utf8'))
    elif '--restore' in sys.argv:restore()
    else:main()
