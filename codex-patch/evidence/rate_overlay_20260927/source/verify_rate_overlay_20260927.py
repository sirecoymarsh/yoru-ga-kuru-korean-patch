"""Independent persisted-output checks and bounded HUD runtime matrix."""
import sys,struct,shutil,json
from pathlib import Path
import build_rate_overlay_20260927 as b
l=b.l;p=b.p;O=b.O;S=b.S
def main():
    ev=l.readj(O/'build_evidence.json');files={n:l.sha(O/n) for n in b.FILES};assert files==ev['files']
    old=l.unpack((S/'NightRemaster.ain').read_bytes());new=l.unpack((O/'NightRemaster.ain').read_bytes());count=struct.unpack_from('<I',old,12)[0]
    code=bytearray(new[16:16+count])
    for site in ev['same_length_sites']:
        i=site['site'];assert code[i:i+6]==bytes.fromhex(site['after']);code[i:i+6]=bytes.fromhex(site['before'])
    assert code==old[16:16+count]
    m=l.read_meta(S/'candidate_meta.json');nm=l.read_meta(O/'candidate_meta.json')
    assert m['functions']==nm['functions'][:len(m['functions'])]
    for k in m:
        if k!='functions':assert m[k]==nm[k]
    assert l.strings(old)[2]==l.strings(new)[2][:len(l.strings(old)[2])]
    assert l.raw_messages((S/'NightRemaster.ain').read_bytes())[3]==l.raw_messages((O/'NightRemaster.ain').read_bytes())[3]
    # Calendar's pinned functions remain byte-exact, not merely at unchanged addresses.
    contract=l.readj(b.R/'required_calendar_r15.json');vs=l.versions(S/'candidate_raw_code.jam')
    for name,pin in contract['pinned_addresses'].items():
        ops=l.live_version(m,vs,pin['index'])['ops'];start=pin['address'];end=ops[-1][0]+2
        assert old[16+start:16+end]==new[16+start:16+end],name
    import build_remaster_multiplier_20260915 as n
    a=n.read_afa3(S/'NightRemasterPact.afa');z=n.read_afa3(O/'NightRemasterPact.afa');assert len(a.entries)==len(z.entries)
    changed=[]
    with (S/'NightRemasterPact.afa').open('rb') as x,(O/'NightRemasterPact.afa').open('rb') as y:
        for i,(e,f) in enumerate(zip(a.entries,z.entries)):
            assert e.name==f.name;x.seek(e.absolute_offset);y.seek(f.absolute_offset)
            if x.read(e.size)!=y.read(f.size):changed.append(i)
    assert changed==[185]
    results={}
    for mode in ['home','dungeon','dialogue','battle']:
        root=O/('native_'+mode);r=l.readj(root/'result.json')
        assert r['source_sha256']==files['NightRemaster.ain'] and r['pact_sha256']==files['NightRemasterPact.afa']
        assert r['probe_sha256']==l.sha(root/'run/NightRemaster.ain')
        assert r.get('exit_code')==0 and r['real_saves_unchanged'] and not r.get('events') and not r.get('vm_error') and not r.get('message')
        assert r['log'][-1]=='END' and 'CACHE 50 updates no rescan' in r['log']
        assert 'LOAD INVALIDATION rebuilt' in r['log'] and 'EVENT INVALIDATION rebuilt' in r['log']
        if mode=='battle':assert 'ACTUAL EVENT BATTLE 7' in r['log']
        results[mode]=str(root/'result.json')
    vis=l.readj(O/'visual_review.json');assert vis['files']==files and vis['status']=='PASS'
    frames=l.readj(O/'save_frames.json')
    result=dict(status='RATE_OVERLAY_STATIC_NATIVE_PASS',files=files,existing_resume_saves=len(frames['saves']),saved_return_frames=len(frames['frames']),
        native_probes=results,calendar_pinned_bytes_exact=True,all_original_function_metadata_exact=True,old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_prefix_exact=True,serialized_schema_changes=0,
        changed_PACT=changed,save_writes=0,cache_test='50 forced visibility updates without rescanning in home, dungeon, dialogue and actual event-battle entry',
        limitations=['Event-battle entry/layout tested, not an entire combat-to-result playthrough.','Native function callbacks tested; physical mouse hit testing not performed.'])
    l.writej(O/'verification.json',result)
    p.O=O;p.FILES=b.FILES;l.WORK=O
    l.writej(O/'transaction_verification.json',p.fixture())
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
