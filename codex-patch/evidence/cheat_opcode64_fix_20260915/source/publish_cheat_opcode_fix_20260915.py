"""One-file compatibility hotfix using the already interruption-tested publisher primitives."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_cheat_menu_20260915 as p

W=Path(__file__).resolve().parent;O=W/'cheat_opcode64_fix_20260915'
R=p.R;E=R/'evidence/cheat_opcode64_fix_20260915';RT=p.RT
CONTRACTS=p.CONTRACTS+p.NEWCONTRACTS
NEW='required_native_opcode_fix.json';STATUS='CHEAT_NATIVE_OPCODE_FIX_STATIC_PASS_RUNTIME_RETEST_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ev=p.read(O/'build_evidence.json');qa=p.read(O/'verification.json');review=p.read(O/'independent_review.json');scan=p.read(O/'scan_report.json')
    assert qa['status']=='COMPILED_BEHAVIOR_AND_NATIVE_OPCODE_PASS' and review['status']=='STATIC_REVIEW_PASS' and scan['status']=='SCANNED_NO_TARGET_DETECTIONS'
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
        if f.is_file() and (f.suffix=='.json' or f.name=='opcode_fix.jam' or f.name.startswith(('built_31852','built_31853','built_31860','original_'))):shutil.copy2(f,E/'source'/f.name)
    for n in ['build_cheat_opcode_fix_20260915.py','publish_cheat_opcode_fix_20260915.py','audit_sys43_native_opcodes_20260915.py','build_cheat_menu_20260915.py','verify_cheat_menu_20260915.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
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
            changed_functions=ev['patched_function_ids'],rejected_native_opcodes=[64,129,130],active_native_opcode_audit=dict(functions=qa['native_active_functions'],instruction_sites=qa['native_instruction_sites'],unsupported=0),native_gameplay_verified=False,translation_UI_and_save_schema_unchanged=True)
        nm.update(status=STATUS,time=now,runtime_verified=False,native_opcode_fix=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],native_opcode_fix=str(E/'source/build_evidence.json'),inherited_evidence_scope='Historical reviews remain bound to their own frozen revision. This hotfix only replaces three helper implementations with native-supported equivalent instructions. Existing CODE prefix, messages, string tables, serialized schemas and every other function signature/body remain unchanged.')
        for row in nm['files']:
            if row['path']=='NightRemaster.ain':row.update(sha256=after['NightRemaster.ain'],size=(rt/'NightRemaster.ain').stat().st_size)
        nm['next']='Relaunch latest runtime. Retest opening Game settings and moving1..5 battle speed slider; then toggle next-floor route on an existing dungeon save. Native execution confirmation remains pending.'
        meta_put(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            path=R/n;c=p.read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
            c['native_opcode_fix_overlay']=str(E/'source/build_evidence.json');meta_put(path,p.js(c))
        meta_put(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='This engine rejects F_PUSH64 and SH_LOCALCREATE129/SH_LOCALDELETE130. Emit PUSH with unchanged IEEE754 literal bits; use native .LOCALCREATE sequence for route locals. Audit the persisted active code against the exact runtime dispatcher; a mocked VM accepting old opcodes is not native compatibility proof. Preserve three fixed helper implementations31852/31853/31860 and all other cumulative fixes.')))
        meta_put(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now[:10]} Native cheat settings opcode64 crash repaired\n- User native screenshot reports 未定義命令コード【64】; actual unchanged NightRemaster.exe default handler0x66888d rejects F_PUSH64. Cause is our JAF helper output, not user save corruption. Previous mocked VM incorrectly accepted64,129,130 and therefore was not engine compatibility verification.\n- Repointed ONLY31852/31853/31860:6 float literal F_PUSH operations become native PUSH with identical IEEE754 bits;2 route local SH_LOCALDELETE/SH_LOCALCREATE pairs become native .LOCALCREATE (same delete/NEW sequence as original dungeon AStar). Engine rejects129/130 too; fixed before their next native trigger. Existing helper declarations, oldCODE prefix, allMSG1/STR0 and all postMSG1 metadata exact; UI/PACT untouched.\n- Actual engine dispatch map/table audit:29,974 active functions,1,803,538 instruction sites,0 unsupported opcodes after patch. Re-executed compiledVM7071calls,500slider roundtrips,24quick cases,72trap cases,6route fixtures PASS. Independent persisted-code review PASS; not a native gameplay pass. Future builder now lowers unsupported JAF instructions, mocked verifier rejects them rather than emulating them.\n- Installed AIN {after["NightRemaster.ain"]};97other runtime files exact,106save file hashes unchanged, recovery build unchanged. Manifest {mh}; evidence/previousAIN outside runtime: {E}.\n- Next: relaunch current runtime and retest Game settings/slider, then dungeon route. Do not mark native gameplay or full translation review complete before user confirmation.\n'
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
