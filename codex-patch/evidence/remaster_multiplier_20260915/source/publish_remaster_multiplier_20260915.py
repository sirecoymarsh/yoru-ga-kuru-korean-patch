"""Transactional two-file revision of the inactive latest build; no new full runtime."""
from pathlib import Path
import copy,datetime,hashlib,json,os,shutil,subprocess,tempfile
from publish_training_fix_20260915 import read,sha

W=Path(__file__).resolve().parent
O=W/'remaster_multiplier_20260915'
R=Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908')
E=R/'evidence/remaster_multiplier_20260915'
STATUS='REMASTER_MULTIPLIERS_STATIC_PASS_NATIVE_PENDING'
CONTRACTS=['required_item_skill_names.json','required_dynamic_ui_text_fix.json','required_map_marker_axis_fix.json','required_location_card_aura_fix.json','required_build_retention.json']

def js(data):return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix=path.name+'.multiplier-',suffix='.tmp',delete=False) as f:
        tmp=Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
    try:os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()

def replace_checked(src,dest,expected):
    assert sha(src)==expected,('source mismatch',str(src))
    tmp=dest.with_name(dest.name+'.multiplier-copy.tmp');assert not tmp.exists(),str(tmp)
    try:
        shutil.copy2(src,tmp);assert sha(tmp)==expected
        os.replace(tmp,dest);assert sha(dest)==expected
    finally:
        if tmp.exists():tmp.unlink()

def fixture():
    f=Path(tempfile.mkdtemp(prefix='transaction-fixture-',dir=O))
    old,new,live=f/'old',f/'new',f/'live'
    old.write_bytes(b'old');new.write_bytes(b'new');live.write_bytes(b'old')
    replace_checked(new,live,sha(new));assert live.read_bytes()==b'new'
    replace_checked(old,live,sha(old));assert live.read_bytes()==b'old'
    # Package and backup tampering must fail before replacing the live file.
    for src in [old,new]:
        try:replace_checked(src,live,'0'*64)
        except AssertionError:pass
        else:raise AssertionError('tamper accepted')
        assert live.read_bytes()==b'old'
    a,b=f/'a',f/'b';a.write_bytes(b'old');b.write_bytes(b'old')
    replace_checked(new,a,sha(new))
    for dest in [a,b]:replace_checked(old,dest,sha(old))
    assert a.read_bytes()==b.read_bytes()==b'old'
    return dict(install=True,restore=True,mixed_state_recovery=True,tampered_package_rejected=True,tampered_backup_rejected=True,path=str(f))

def processes():
    cmd="$ErrorActionPreference='Stop'; @(Get-CimInstance Win32_Process -Filter \"Name = 'NightRemaster.exe'\" | Select-Object ProcessId,ExecutablePath) | ConvertTo-Json -Compress"
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],capture_output=True,timeout=60)
    assert p.returncode==0,('process preflight failed',p.stderr.decode('utf8','replace'))
    s=p.stdout.decode('utf8-sig').strip();result=json.loads(s) if s else []
    return result if isinstance(result,list) else [result]

def main():
    ev=read(O/'build_evidence.json');qa=read(O/'verification.json');review=read(O/'independent_review.json');visual=read(O/'visual_review.json')
    assert qa['status']=='STATIC_VM_LAYOUT_PASS_NATIVE_PENDING' and review['status']=='STATIC_REVIEW_PASS' and visual['status']=='STATIC_FONT_GEOMETRY_VISUAL_PASS'
    assert ev['files']==qa['files']==review['files']==visual['files']
    for n,h in ev['files'].items():assert sha(O/n)==h
    fx=fixture();pointer=R/'ui_cumulative/current.json';p=read(pointer);assert p==ev['source_pointer']
    mp=Path(p['manifest']);assert sha(mp)==p['manifest_sha256'];m=read(mp);rt=Path(p['runtime']).resolve()
    assert rt==Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908/ui_cumulative/enemyscope_fbca7f090e72/runtime').resolve()
    retention=read(R/'required_build_retention.json');recovery=Path(retention['recovery_runtime']).resolve();assert rt!=recovery
    assert sha(Path(retention['recovery_manifest']))==retention['recovery_manifest_sha256']
    recovery_files={row['path']:row['sha256'] for row in read(Path(retention['recovery_manifest']))['files']}
    for n in ev['files']:assert sha(recovery/n)==recovery_files[n]
    files={row['path']:row for row in m['files']};assert len(files)==98
    assert {f.relative_to(rt).as_posix() for f in rt.rglob('*') if f.is_file()}==set(files)
    for n,row in files.items():
        fp=(rt/n).resolve();assert fp.is_relative_to(rt) and fp.stat().st_size==row['size'] and sha(fp)==row['sha256'],n
    print('Source 98-file manifest PASS',flush=True)
    assert not E.exists(),'Evidence target already exists; inspect journal instead of rerunning'
    E.mkdir(parents=True);(E/'before').mkdir();(E/'candidate').mkdir();(E/'source').mkdir()
    snapshots={mp:mp.read_bytes(),pointer:pointer.read_bytes(),R/'progress.md':(R/'progress.md').read_bytes()}
    for n in CONTRACTS:snapshots[R/n]=(R/n).read_bytes()
    for path,data in snapshots.items():put(E/'before'/path.name,data)
    for n,h in ev['files'].items():
        shutil.copy2(rt/n,E/'before'/n);assert sha(E/'before'/n)==files[n]['sha256']
        shutil.copy2(O/n,E/'candidate'/n);assert sha(E/'candidate'/n)==h
    evidence_names=['build_evidence.json','verification.json','independent_review.json','visual_review.json','source_pointer.json','multiplier_patch.jam','callback_stubs.jaf','pact_125_sliders.pactex','pact_125.pactex','font_layout_proof.png','current_meta.json','candidate_meta.json']
    evidence_names += [f'built_{i}.jam' for i in ev['AIN']['patched_existing_function_ids']+list(ev['AIN']['added_function_ids'].values())]
    for n in evidence_names:shutil.copy2(O/n,E/'source'/n)
    for n in ['build_remaster_multiplier_20260915.py','verify_remaster_multiplier_20260915.py','render_remaster_multiplier_proof_20260915.py','publish_remaster_multiplier_20260915.py']:shutil.copy2(W/n,E/'source'/n)
    index=[dict(path=str(f.relative_to(E)),sha256=sha(f),size=f.stat().st_size) for f in E.rglob('*') if f.is_file()]
    put(E/'frozen_index.json',js(index))
    now=datetime.datetime.now().astimezone().isoformat()
    journal=dict(status='PREPARED',time=now,runtime=str(rt),backups=str(E/'before'),candidate=ev['files'],fixture=fx)
    put(E/'journal.json',js(journal))
    before_proc=processes();assert not before_proc,('Game is running; staged only, no files replaced',before_proc)
    assert read(pointer)==p and sha(mp)==p['manifest_sha256']
    replaced=[];changed_metadata=[];newcontract=R/'required_remaster_multiplier.json';assert not newcontract.exists()
    try:
        for n,h in ev['files'].items():
            assert sha(rt/n)==files[n]['sha256']
            replaced.append(n);replace_checked(E/'candidate'/n,rt/n,h)
            journal.update(status='REPLACING',replaced=replaced);put(E/'journal.json',js(journal))
        newm=copy.deepcopy(m);newm.update(status=STATUS,time=now,runtime_verified=False,whole_ui_complete=False)
        for row in newm['files']:
            if row['path'] in ev['files']:row.update(size=(rt/row['path']).stat().st_size,sha256=ev['files'][row['path']])
        revision=dict(status=STATUS,time=now,runtime=str(rt),previous_manifest=str(E/'before/manifest.json'),previous_manifest_sha256=p['manifest_sha256'],files=ev['files'],
            categories=['경험치','훈련치','월편','동료 특훈치'],range=[1,20],integer_step=1,independent_rates=True,existing_1x_2x_values_preserved=True,
            save_global_and_structure_schema_unchanged=True,changed_existing_functions=ev['AIN']['patched_existing_function_ids'],added_functions=ev['AIN']['added_function_ids'],
            changed_PACT_entries=[125],unaffected_runtime_files_exact=96,original_code_prefix_and_existing_messages_strings_exact=True,
            evidence=str(E),source_build=ev['source_pointer'],native_verified=False,save_file_roundtrip_verified=False,translator_model='Codex internal')
        newm['remaster_multiplier_revision']=revision
        newm['ain'].update(candidate_sha256=ev['files']['NightRemaster.ain'],status=STATUS,remaster_multiplier_overlay=str(E/'source/build_evidence.json'),
            inherited_evidence_scope='Preceding fields and reviews describe their own historical revisions, retained in before/manifest.json. This feature appends nine functions and repoints only six existing functions; original globals, structures, CODE prefix, messages and existing strings are exact. Current files and remaster_multiplier_revision are authoritative.')
        newm['pact_display_overlay'].update(candidate_sha256=ev['files']['NightRemasterPact.afa'],remaster_multiplier_overlay=str(E/'source/build_evidence.json'))
        newm['next']='Native verification: four independent sliders, real reward payment, save and reload. Launch only current.json runtime in normal user context.'
        for row in newm['files']:assert sha(rt/row['path'])==row['sha256'],row['path']
        put(mp,js(newm));changed_metadata.append(mp);newhash=sha(mp)
        for n in CONTRACTS:
            path=R/n;c=read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:assert c[k]==p['manifest_sha256'];c[k]=newhash
            for fn,h in ev['files'].items():
                if fn in c.get('required_files',{}):c['required_files'][fn]=h
            c['remaster_multiplier_overlay']=str(E/'source/build_evidence.json')
            if n=='required_dynamic_ui_text_fix.json':
                c['remaster_multiplier_scope']='Only Remaster casual settings subtree125 is replaced by independent native sliders; preceding display words and internal keys outside the feature remain exact. name_revision_scope describes the earlier enemy-only revision.'
            put(path,js(c));changed_metadata.append(path)
        contract=copy.deepcopy(revision);contract.update(manifest=str(mp),manifest_sha256=newhash,required_files=ev['files'],
            instruction='Preserve all four independent integer1..20 native reward sliders and overflow-safe Calc wrappers. Rebase from current.json. Globals201/202/203/204 store integer percentages100..2000; never rebind them to legacy bool callbacks. Do not add serialized fields or regress prior localization/crash fixes. Native slider operation and actual save/reload remain pending.')
        put(newcontract,js(contract));changed_metadata.append(newcontract)
        np=copy.deepcopy(p);np.update(manifest_sha256=newhash,status=STATUS,runtime_verified=False);put(pointer,js(np));changed_metadata.append(pointer)
        note=f'\n\n### {now[:10]} Independent Remaster reward multipliers\n- User requested separate1..20 sliders for EXP, training, moon pieces and partner training. Reused native sound slider bar/cursor; PACT125 casual-settings subtree only. No raster panels or font changes. Four saved percent globals and all804 structure schemas unchanged; existing1x/2x values retain their values.\n- Added9 callbacks/helper; repointed only existing26361..26364,29817,29818. Original CODE prefix,100944 messages and existingSTR0 exact. Signed-int saturation prevents new20x intermediate overflow. All prior translations, names, opening/UI and crash fixes preserved.\n- Actual compiled disassembly VM:17894 calls,80 category steps,8000 float roundtrips, mixed1/2/5/20 and bounds PASS. Native FNL glyphs/widths, geometry proof and independent read-only code/PACT review PASS. No native input/reward or actual save/reload test.\n- Transactionally replaced only AIN and PACT in {rt}. Full98-file manifest PASS;96 other files exact. Only latest and recovery full runtime folders retained; original game and user saves untouched.\n- Evidence and two-file rollback: {E}. Current manifest SHA256 {newhash}. Next: launch current.json runtime, open Remaster settings, test independent sliders/rewards and save/reload.\n'
        put(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'));changed_metadata.append(R/'progress.md')
        assert sha(mp)==read(pointer)['manifest_sha256']
        for row in newm['files']:assert sha(rt/row['path'])==row['sha256']
        assert len(list((R/'ui_cumulative').glob('*/runtime')))==2
        assert sha(Path(retention['recovery_manifest']))==retention['recovery_manifest_sha256']
        for n in ev['files']:assert sha(recovery/n)==recovery_files[n]
        report=dict(status=STATUS,runtime=str(rt),manifest_sha256=newhash,changed_files=ev['files'],unchanged_files_exact=96,all_runtime_files_verified=98,full_runtime_count=2,
            original_game_modified=False,saves_modified=False,game_running_at_publish=False,game_launched=False,native_verified=False,save_file_roundtrip_verified=False,
            evidence=str(E),fixture=fx)
        put(E/'publish_report.json',js(report));put(O/'publish_report.json',js(report));journal.update(status='COMMITTED',manifest_sha256=newhash);put(E/'journal.json',js(journal))
        print(json.dumps(report,ensure_ascii=False,indent=2))
    except BaseException as err:
        failures=[]
        for n in reversed(replaced):
            try:replace_checked(E/'before'/n,rt/n,files[n]['sha256'])
            except BaseException as rollback:failures.append(str(rollback))
        for path in reversed(list(snapshots)+[newcontract]):
            try:
                if path in snapshots:put(path,snapshots[path])
                elif path==newcontract and path.exists():path.unlink()
            except BaseException as rollback:failures.append(str(rollback))
        journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(err),rollback_errors=failures);put(E/'journal.json',js(journal))
        raise

if __name__=='__main__':main()
