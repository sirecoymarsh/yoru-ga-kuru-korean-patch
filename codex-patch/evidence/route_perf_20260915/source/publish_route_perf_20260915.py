"""One-file compatibility hotfix using the already interruption-tested publisher primitives."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_cheat_menu_20260915 as p

W=Path(__file__).resolve().parent;O=W/'route_perf_20260915'
R=p.R;E=R/'evidence/route_perf_20260915';RT=p.RT
CONTRACTS=p.CONTRACTS+p.NEWCONTRACTS+['required_native_opcode_fix.json']
NEW='required_route_cache_fix.json';STATUS='ROUTE_CACHE_STATIC_PASS_NATIVE_PERFORMANCE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ev=p.read(O/'build_evidence.json');qa=p.read(O/'verification.json');review=p.read(O/'independent_review.json');scan=p.read(O/'scan_report.json')
    assert qa['status']=='ROUTE_CACHE_COMPILED_BEHAVIOR_PASS' and review['status']=='STATIC_REVIEW_PASS' and scan['status']=='SCANNED_NO_TARGET_DETECTIONS'
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
        if f.is_file() and (f.suffix=='.json' or f.name=='route_perf_patch.jam' or f.name.startswith(('built_','original_'))):shutil.copy2(f,E/'source'/f.name)
    for n in ['build_route_perf_20260915.py','publish_route_perf_20260915.py','scan_route_perf_20260915.ps1','audit_sys43_native_opcodes_20260915.py','build_cheat_menu_20260915.py','verify_cheat_menu_20260915.py','verify_route_perf_20260915.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
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
            changed_functions=ev['patched_function_ids'],cache_slots=[85,86],same_position_results_cached=True,duplicate_AStar_search_removed=True,active_native_opcode_audit=dict(functions=qa['native_active_functions'],instruction_sites=qa['native_instruction_sites'],unsupported=0),native_gameplay_verified=False,translation_UI_and_save_schema_unchanged=True)
        nm.update(status=STATUS,time=now,runtime_verified=False,route_cache_fix=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],route_cache_fix=str(E/'source/build_evidence.json'),inherited_evidence_scope='Historical reviews remain bound to their own frozen revision. This hotfix only adds route cache invalidation to four topology setters, map binding, option changes and load; the route helper skips repeated coordinates, creates a fresh AStar per candidate and preserves the best route instead of rerunning the search. Existing CODE prefix, messages, string tables, serialized schemas and every other function signature/body remain unchanged.')
        for row in nm['files']:
            if row['path']=='NightRemaster.ain':row.update(sha256=after['NightRemaster.ain'],size=(rt/'NightRemaster.ain').stat().st_size)
        nm['next']='Relaunch latest runtime, keep route enabled, compare idle and movement responsiveness; test new floor, repeated coordinates, settings toggle and load. Native performance measurement remains pending.'
        meta_put(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            path=R/n;c=p.read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
            c['route_cache_fix_overlay']=str(E/'source/build_evidence.json');meta_put(path,p.js(c))
        meta_put(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Preserve route helper31860 coordinate cache85/86(-1 invalid), invalidation hooks27007/27010/27025/27031/28669/31850/31856, and best-path copy with fresh AStar per candidate. Same-position/no-route results must be cached; do not skip player facing updates. Do not reuse mutable AStar state or redraw/recalculate on an identical tile. Keep native-opcode compatibility, all cheats, translations, UI, saved-name getters and reward sliders.')))
        meta_put(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now[:10]} Route cache and duplicate search cost reduced\n- User confirmed red route dots appear after entering a new floor, but dungeon play became very slow. Inspection: both28758 UpdatePlayer and28759 FinishMoved call minimap28673; old route helper rebuilt900-cell cost map, searched once perexit then searched again on the same mutable AStar object, and redrew even at identical coordinates. Native Exec does not clear its open/closed sets between these calls.\n- Repointed8 functions:27007/27010/27025/27031 invalidate on map topology setter calls;28669 on map bind/rebuild;31850 only on route option changes;31856 on load;31860 caches successful AND no-route results with85/86xy(-1 invalid) plus89 draw marker. Player position/facing function itself unchanged. Fresh AStar percandidate, structured-array copy of shortest result using original9164 native Realloc2/Copy#3 2 recipe, no second search. No new functions/fields/global/save schema, no fog flags/auto-move queue changes.\n- Compiled fixture20identical updates: cost-map builds20→1, AStar calls40→1, route draws20→1; same path. Native FPS not measured. Movement, floor/reset/toggle/no-exit cache cases plus500slider roundtrips/24quick/72trap/6route layouts PASS. Independent persisted candidate review and full native dispatch coverage PASS.\n- AIN {after["NightRemaster.ain"]};97other runtime files exact, {len(saved)}save hashes unchanged, recovery build unchanged. Manifest {mh}; evidence/backups {E}.\n- Next: user native performance check with route enabled, idle then move and change floors; confirm no missing/stale route after toggles or topology change. No full localization/runtime completion claim.\n'
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
