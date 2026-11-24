"""Re-read final bytes: native opcode, append-only metadata, saved offsets and tests."""
import sys,struct,json
from pathlib import Path
import build_story_explore_20260927 as b
l=b.l;p=b.p;O=b.O;S=b.S
def main():
    ev=l.readj(O/'build_evidence.json');files={n:l.sha(O/n) for n in b.FILES};assert files==ev['files']
    old=l.unpack((S/'NightRemaster.ain').read_bytes());new=l.unpack((O/'NightRemaster.ain').read_bytes());count=struct.unpack_from('<I',old,12)[0]
    code=bytearray(new[16:16+count]);occupied=set()
    for site in ev['same_length_sites']:
        i=site['site'];assert not occupied.intersection(range(i,i+6));occupied.update(range(i,i+6))
        assert code[i:i+6]==bytes.fromhex(site['after']);code[i:i+6]=bytes.fromhex(site['before'])
    assert code==old[16:16+count]
    m=l.read_meta(S/'candidate_meta.json');nm=l.read_meta(O/'candidate_meta.json')
    assert m['functions']==nm['functions'][:len(m['functions'])]
    for k in m:
        if k!='functions':assert m[k]==nm[k]
    assert l.strings(old)[2]==l.strings(new)[2][:len(l.strings(old)[2])]
    assert l.raw_messages((S/'NightRemaster.ain').read_bytes())[3]==l.raw_messages((O/'NightRemaster.ain').read_bytes())[3]
    vs=l.versions(S/'candidate_raw_code.jam');contract=l.readj(b.R/'required_calendar_r15.json')
    for name,pin in contract['pinned_addresses'].items():
        ops=l.live_version(m,vs,pin['index'])['ops'];a=pin['address'];z=ops[-1][0]+2;assert old[16+a:16+z]==new[16+a:16+z],name
    # All existing saved instruction and return addresses still address unchanged instructions.
    frames=[];saves=[]
    for path in sorted(l.SAVES.glob('NightR*.asd')):
        if not path.stem[6:].isdigit():continue
        rec=l.save_records(path);assert rec;saves.append(path.name)
        for r in [rec['ip']]+rec['returns']:
            ad=r['address']
            if ad<0:continue
            assert old[16+ad:22+ad]==new[16+ad:22+ad],(path,ad)
            frames.append(dict(save=path.name,**r))
    l.writej(O/'save_frames.json',dict(saves=saves,frames=frames,all_existing_function_metadata_exact=True))
    results={}
    for mode in ['story','story_return','rest','normal','story_floor']:
        root=O/('native_'+mode);r=l.readj(root/'result.json')
        assert r['source_sha256']==files['NightRemaster.ain'] and r['probe_sha256']==l.sha(root/'run/NightRemaster.ain')
        assert r.get('exit_code')==0 and r['real_saves_unchanged'] and not r.get('events') and not r.get('vm_error') and not r.get('message'),mode
        assert r['log'][-1]=='END' and any(x.startswith('PASS ') for x in r['log'])
        assert not any(x.startswith(('FAIL ','STOPPED ','UNEXPECTED ')) for x in r['log']),mode
        results[mode]=str(root/'result.json')
    result=dict(status='STORY_EXPLORE_STATIC_NATIVE_PASS',files=files,existing_resume_saves=len(saves),saved_return_frames=len(frames),native_probes=results,
        calendar_pinned_bytes_exact=True,all_original_function_metadata_exact=True,old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_prefix_exact=True,serialized_schema_changes=0,save_writes=0,
        limitations=['Representative native cases, not every story dungeon completed.','Story test runs 13 original dialogue lines into the original manual party prompt. The separate continuation test retains the preselected party in the private fixture only. Its three logged positions include the event tile and two subsequent movements.','Rest fixture places a native rest tile one step away and damages the copied party; native recovery itself is unmodified.','Story-floor fixture uses native map creation and supplies the 501 completion signal to test transition handling without changing story flags.','Story-owned result timer and level notification were tested natively; full story-boss combat not completed in this matrix.','Native choices remain manual; no forced story flags, rewards or battle outcomes in the installed patch.'])
    l.writej(O/'verification.json',result);p.O=O;p.FILES=b.FILES;l.WORK=O;l.writej(O/'transaction_verification.json',p.fixture());print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
