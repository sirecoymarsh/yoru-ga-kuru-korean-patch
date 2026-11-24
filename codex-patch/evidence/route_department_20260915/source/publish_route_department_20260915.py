"""One-file compatibility hotfix using the already interruption-tested publisher primitives."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_cheat_menu_20260915 as p

W=Path(__file__).resolve().parent;O=W/'route_department_20260915'
R=p.R;E=R/'evidence/route_department_20260915';RT=p.RT
CONTRACTS=p.CONTRACTS+p.NEWCONTRACTS+['required_native_opcode_fix.json','required_route_cache_fix.json','required_route_map_refresh.json']
NEW='required_department_route.json';STATUS='DEPARTMENT_ROUTE_STATIC_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ev=p.read(O/'build_evidence.json');qa=p.read(O/'verification.json');review=p.read(O/'independent_review.json');scan=p.read(O/'scan_report.json')
    assert qa['status']=='DEPARTMENT_ROUTE_COMPILED_MAP_FIXTURES_PASS' and review['status']=='STATIC_REVIEW_PASS' and scan['status']=='SCANNED_NO_TARGET_DETECTIONS'
    after=ev['files'];before=ev['source_files'];assert after==qa['files']==review['files']==scan['files']
    assert p.sha(O/'NightRemaster.ain')==after['NightRemaster.ain']
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert p.sha(RT/'NightRemaster.ain')==after['NightRemaster.ain'];print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'];mp=Path(current['manifest']);assert p.sha(mp)==current['manifest_sha256'];m=p.read(mp);rt=Path(current['runtime']).resolve();assert rt==RT.resolve()
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    fx=p.fixture();p.exact_tree(rt,m['files']);assert p.sha(rt/'NightRemaster.ain')==before['NightRemaster.ain']
    keep=p.read(R/'required_build_retention.json');rm=Path(keep['recovery_manifest']);rec=Path(keep['recovery_runtime']);assert p.sha(rm)==keep['recovery_manifest_sha256'];rh=p.sha(rec/'NightRemaster.ain')
    saved=p.snapshot_saves();snapshots={path:path.read_bytes() if path.exists() else None for path in [mp,ptr,R/'progress.md']+[R/n for n in CONTRACTS+[NEW]]}
    assert snapshots[R/NEW] is None
    for n in CONTRACTS:
        c=p.read(R/n)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in c:assert c[key]==current['manifest_sha256']
    E.mkdir(parents=True)
    for d in ['before','candidate','source']:(E/d).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
        assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
    for f in O.iterdir():
        if f.is_file() and (f.name in ['build_evidence.json','candidate_meta.json','native_opcode_audit.json','verification.json','independent_review.json','scan_report.json','transaction_verification.json','map_arrays.json','map_201_native_cells.json','map_202_native_cells.json','map_203_native_cells.json','map_204_native_cells.json'] or f.name=='route_department_patch.jam' or f.name.startswith(('built_','original_'))):shutil.copy2(f,E/'source'/f.name)
    for n in ['build_route_department_20260915.py','publish_route_department_20260915.py','scan_route_department_20260915.ps1','audit_sys43_native_opcodes_20260915.py','build_cheat_menu_20260915.py','verify_cheat_menu_20260915.py','verify_route_department_20260915.py','verify_route_perf_20260915.py','build_route_perf_20260915.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
        shutil.copy2(W/n,E/'source'/n)
    p.put(E/'save_hashes_before.json',p.js(saved));journal=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fx)
    p.put(E/'journal.json',p.js(journal))
    def meta_put(path,data):
        assert path in snapshots;journal.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest()
        p.put(E/'journal.json',p.js(journal));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256']
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat();nm=copy.deepcopy(m)
        rev=dict(status=STATUS,time=now,source_ain_sha256=before['NightRemaster.ain'],candidate_ain_sha256=after['NightRemaster.ain'],evidence=str(E),previous_manifest=str(E/'before/manifest.json'),previous_manifest_sha256=current['manifest_sha256'],
            changed_functions=ev['patched_function_ids'],target_rules=ev['target_rules'],root_cause=qa['root_cause'],scope=qa['scope'],existing_same_tile_cache_preserved=True,active_native_opcode_audit=dict(functions=qa['native_active_functions'],instruction_sites=qa['native_instruction_sites'],unsupported=0),native_gameplay_verified=False,translation_UI_and_save_schema_unchanged=True)
        nm.update(status=STATUS,time=now,runtime_verified=False,department_route=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],department_route=str(E/'source/build_evidence.json'),inherited_evidence_scope='Historical reviews remain bound to their own frozen revision. This revision changes only route helper31860 goal selection for department maps202/203/204, following original scripted completion events rather than inaccessible or absent stairs. Cached search, prior refresh hooks, player movement and event scripts are unchanged. Existing CODE prefix, messages, string tables, serialized schemas and every other function signature/body remain unchanged.')
        for row in nm['files']:
            if row['path']=='NightRemaster.ain':row.update(sha256=after['NightRemaster.ain'],size=(rt/'NightRemaster.ain').stat().st_size)
        nm['next']='Relaunch latest runtime; enable route display and verify department204 escape route,202 event exit and203 ordered event targets. Native display verification remains pending; this is not universal event-dungeon coverage.'
        meta_put(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            path=R/n;c=p.read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
            c['department_route_overlay']=str(E/'source/build_evidence.json');meta_put(path,p.js(c))
        meta_put(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Preserve department route target rules in31860:202/204 target unremoved7/0;203 lowest unremoved7 subtype0..3, then shortest route to that group. Keep default stair2/1 elsewhere, same-tile cache, native-compatible instructions and post-transition refresh hooks. Never modify event completion, walls, inventory, saves or move the player for this display feature. Other event maps require separately verified target rules.')))
        meta_put(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now[:10]} Department-store scripted route targets corrected\n- User screenshot identified burning department west2F map204. Exact current EX geometry: entrance14,3; only2/1 stair13,1 is enclosed by wall/fire(ground34/35), so previous routehelper correctly found no path to the WRONG target. True exit event7/0 at6,22..24 invokes28896→m_bNext. Map202 has no2/1 stair; exit7/0 at28,22..24 invokes28865→m_bExit. Previous refresh-only patch did not fix this selector error.\n- Changed ONLY31860; map202/204 target unremoved7/0.203 follows smallest unremoved7 subtype0→1→2→3; native scripts removecompletedgroups via29171. ReusedunusedbestX/bestY locals; default2/1 elsewhere; no gameplay/event/wall mutation. Existing cached search and refresh hooks preserved. OldCODEprefix/MSG1tail/signatures/allothermetadata exact except1function address.\n- Compiled helper tested against4 actual EX maps with nativeLoadMapData27070 and passability rules, BFS method fixture:202/204 previously no path now valid escape paths;201 path exact;203 all4removal stages ordered. Existing500slider/24quick/72trap/6generic route fixtures and full nativeopcodeaudit PASS. Native renderer and AStar execution NOT tested.\n- InstalledAIN {after["NightRemaster.ain"]};97other runtimefiles exact,{len(saved)}save hashes unchanged,recovery unchanged. Manifest {mh}; evidence/backups {E}.\n- Scope limit from source review:101/102/303 target6/0;405/503/605 use scriptedflags;700/800/900 mixedevent/stair semantics. These are NOT changed or verified by this department patch. Next: native204 path display confirmation, then separately audit other event targets if requested.\n'
        meta_put(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saved==p.snapshot_saves()
        assert p.sha(rm)==keep['recovery_manifest_sha256'] and p.sha(rec/'NightRemaster.ain')==rh and len(list((R/'ui_cumulative').glob('*/runtime')))==2
        journal.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(journal))
    except BaseException as err:
        failures=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as x:failures.append(repr(x))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:p.put(path,data)
                elif path.exists():path.unlink()
            except BaseException as x:failures.append(repr(x))
        journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(err),rollback_errors=failures);p.put(E/'journal.json',p.js(journal));raise
    report=dict(status=STATUS,runtime=str(rt),manifest_sha256=mh,files=after,unchanged_other_runtime_files=97,save_files_hashes_unchanged=len(saved),recovery_build_unchanged=True,native_gameplay_verified=False,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
    else:main()
