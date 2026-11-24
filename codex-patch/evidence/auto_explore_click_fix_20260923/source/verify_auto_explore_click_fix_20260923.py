"""Verify exact code boundary, saved frames, and native callback/movement evidence."""
import collections,re,struct,json
import build_auto_explore_click_fix_20260923 as e
b=e.b;p=e.p;q=e.q;O=e.O

def main():
    ev=b.a.readj(O/'build_evidence.json');src=O/'baseline_NightRemaster.ain';out=O/'NightRemaster.ain'
    assert b.a.sha(src)==e.EXPECTED and ev['files']=={'NightRemaster.ain':b.a.sha(out)}
    bm=b.read_meta(e.BASE/'candidate_meta.json');nm=b.read_meta(O/'candidate_meta.json')
    before=b.unpack(src.read_bytes());after=b.unpack(out.read_bytes());n=struct.unpack_from('<I',before,12)[0]
    assert after[16:16+n]==before[16:16+n]
    assert len(nm['functions'])==len(bm['functions'])+3
    for f,g in zip(bm['functions'],nm['functions']):
        test=dict(f)
        if f['index']==32030:test['address']=g['address']
        assert test==g,f['index']
    for k in bm:
        if k!='functions':assert bm[k]==nm[k],k
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(after)[2][:len(b.strings(before)[2])]==b.strings(before)[2]
    oldvs=q.versions(e.BASE/'native_raw_code.jam');sig=collections.defaultdict(list)
    for f in bm['functions']:sig[f['crc']&0xffffffff].append(f)
    records=[];frames=[]
    for path in sorted(p.SAVE.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd',path.name):continue
        row=q.records(path);assert row is not None;records.append(row)
        for rr in [row['ip']]+row['returns']:
            if rr['address']==-1:continue
            choices=[f for f in sig[rr['crc']] if rr['name'].startswith(b.raw_symbol(bm,f['index'])+'(') and any(v['start']==rr['address']-rr['offset'] for v in oldvs[f['index']])]
            assert len(choices)==1,(path.name,rr);f=choices[0];fid=f['index'];assert fid!=32030 and nm['functions'][fid]==f
            addr=f['address']+rr['offset'];ops=next(v['ops'] for v in oldvs[fid] if v['start']==f['address']);op=dict(ops)[addr]
            assert before[16+addr:16+addr+2]==after[16+addr:16+addr+2]
            frames.append(dict(file=path.name,fid=fid,offset=rr['offset'],opcode=op))
    bound=(O/'built_32197.jam').read_text('utf-8');bind=(O/'built_32196.jam').read_text('utf-8')
    assert bound.index('.LOCALREF show')<bound.index('CALLFUNC KR_ExploreBindClick')<bound.index('CALLFUNC KR_ExploreVisible')
    assert bind.count('DG_NEW_FROM_METHOD')==2 and bind.count('PUSH 32037')==2
    assert bind.index('EraseMouseLClickEvent')<bind.index('AddMouseLClickEvent')
    assert 'KR_SweepClick' not in bind and 'Clear' not in bind
    baseline=(O/'native_before_fix.txt').read_text('utf-8')
    assert 'walk=1000010566 delegate=423 handlers=0' in baseline and 'clickResult=0' in baseline
    native=[]
    for mode in ['off','on']:
        log=(O/f'native_route_{mode}.txt').read_text('utf-8');capture=b.a.readj(O/f'native_route_{mode}_capture.json')
        assert capture.get('exit_code')==0 and not capture['events'] and 'message' not in capture
        assert 'repeat-visible handlers=1' in log and 'clickResult=2026092203' in log
        assert 'native Run started queue=' in log and f'guide={int(mode=="on")}' in log
        assert 'MOVED 21,6 -> ' in log and 'STOPPED through second click' in log
        native.append(dict(mode=mode,pid=capture['pid'],probe_sha256=capture['ain_sha256'],log=log))
    assert b.a.readj(O/'native_route_on_manifest.json')['source_sha256']==ev['files']['NightRemaster.ain']
    assert p.snapshot_saves()==b.a.readj(O/'save_hashes_before_build.json')
    e.save('save_resume_check.json',dict(saves=len(records),frames=frames))
    report=dict(status='CLICK_FIX_STATIC_AND_NATIVE_DISPATCH_PASS',files=ev['files'],existing_resume_saves=len(records),saved_return_frames=len(frames),existing_save_local_offsets_exact=True,old_CODE_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native=native,scope='real copied dungeon save; actual part delegate dispatch, wait-loop, route ON/OFF movement, second-click stop, idempotent visible rebind',not_verified=['OS cursor hit testing','all dungeon/combat/stair transitions'],save_files_unchanged=len(p.snapshot_saves()))
    e.save('verification.json',report);print(json.dumps({k:v for k,v in report.items() if k!='native'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
