"""One-file compatibility hotfix using the already interruption-tested publisher primitives."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_cheat_menu_20260915 as p

W=Path(__file__).resolve().parent;O=W/'route_map_refresh_20260915'
R=p.R;E=R/'evidence/route_map_refresh_20260915';RT=p.RT
CONTRACTS=p.CONTRACTS+p.NEWCONTRACTS+['required_native_opcode_fix.json','required_route_cache_fix.json']
NEW='required_route_map_refresh.json';STATUS='ROUTE_MAP_REFRESH_STATIC_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ev=p.read(O/'build_evidence.json');qa=p.read(O/'verification.json');review=p.read(O/'independent_review.json');scan=p.read(O/'scan_report.json')
    assert qa['status']=='ROUTE_MAP_REFRESH_COMPILED_PASS' and review['status']=='STATIC_REVIEW_PASS' and scan['status']=='SCANNED_NO_TARGET_DETECTIONS'
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
        if f.is_file() and (f.name in ['build_evidence.json','candidate_meta.json','native_opcode_audit.json','verification.json','independent_review.json','scan_report.json','transaction_verification.json'] or f.name=='route_map_refresh_patch.jam' or f.name.startswith(('built_','original_'))):shutil.copy2(f,E/'source'/f.name)
    for n in ['build_route_map_refresh_20260915.py','publish_route_map_refresh_20260915.py','scan_route_map_refresh_20260915.ps1','audit_sys43_native_opcodes_20260915.py','build_cheat_menu_20260915.py','verify_cheat_menu_20260915.py','verify_route_map_refresh_20260915.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
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
            changed_functions=ev['patched_function_ids'],refresh_after_next_floor_events=True,refresh_after_full_rebuild=True,existing_same_tile_cache_preserved=True,root_cause_status=ev['root_cause_status'],active_native_opcode_audit=dict(functions=qa['native_active_functions'],instruction_sites=qa['native_instruction_sites'],unsupported=0),native_gameplay_verified=False,translation_UI_and_save_schema_unchanged=True)
        nm.update(status=STATUS,time=now,runtime_verified=False,route_map_refresh=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],route_map_refresh=str(E/'source/build_evidence.json'),inherited_evidence_scope='Historical reviews remain bound to their own frozen revision. This revision adds route refresh only after ToNextFloor28638 finishes SetMapId28639 (including entrance events) and after UpdateAll28754 finishes rebuilding the minimap. The cached route helper, goal rules, movement and event functions are unchanged. Existing CODE prefix, messages, string tables, serialized schemas and every other function signature/body remain unchanged.')
        for row in nm['files']:
            if row['path']=='NightRemaster.ain':row.update(sha256=after['NightRemaster.ain'],size=(rt/'NightRemaster.ain').stat().st_size)
        nm['next']='Relaunch latest runtime; enable route display, enter the next floor and verify dots without moving. Test a full map rebuild and normal movement. Native regression reproduction and verification remain pending.'
        meta_put(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            path=R/n;c=p.read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
            c['route_map_refresh_overlay']=str(E/'source/build_evidence.json');meta_put(path,p.js(c))
        meta_put(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Preserve post-SetMapId route refresh in ToNextFloor28638 and post-rebuild refresh in UpdateAll28754. Refresh only with route enabled and a non-null current map, invalidate85/86 and use current Flags XY and current minimap. Do not move the next-floor refresh before entry events or reuse previous floor coordinates. Keep route helper31860, eligibility and same-tile caching; all prior translations/UI/cheats/save schema remain unchanged. Native user regression is not yet reproduced or verified.')))
        meta_put(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now[:10]} Next-floor and full-rebuild route refresh closure\n- User reports route disappears on entering the next floor after39c55 cache revision. Static flow: SetMapId28639 invokes both player refreshes BEFORE entrance events; UpdateAll28754 rebinds and invalidates cache but does not redraw route. Ordinary map changes do call player refresh; exact user symptom/root cause is not yet reproduced in native runtime.\n- Patched ONLY28638 ToNextFloor: after SetMapId returns, and28754 UpdateAll: after full rebuild. Both skip when route OFF or map absent, invalidate85/86, then invoke unchanged KR_DrawRoute using current map/minimap/current Flags coordinates. No per-frame hook; same-tile cache and goal/walkability rules unchanged. Metadata exact except2function addresses; oldCODEprefix andMSG1onward exact.\n- Compiled inserted-region fixtures16combinations (ON/OFF,nullmap,exit/noexit), post-event changedXY and20repeat cache checks PASS. Existing500slider/24quick/72trap/6route fixtures and active-native-opcode audit PASS. Native AStar fixture corrected to exclude start tile, matching TraceRoute; native map transition still pending.\n- InstalledAIN {after["NightRemaster.ain"]};97other runtime files exact;{len(saved)}save hashes unchanged, recovery build unchanged. Manifest {mh}; evidence/backups {E}.\n- Next: confirm route appears on next-floor arrival without moving; if absent obtain exact dungeon/floor and distinguish absent/unreachable exit from display refresh. Do not claim native symptom resolved before confirmation.\n'
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
