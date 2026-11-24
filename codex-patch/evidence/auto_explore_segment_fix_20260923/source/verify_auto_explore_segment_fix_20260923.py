"""Verify exact code boundary, saved frames, and native callback/movement evidence."""
import collections,re,struct,json
import build_auto_explore_segment_fix_20260923 as e
b=e.b;p=e.p;q=e.q;O=e.O

def main():
    ev=b.a.readj(O/'build_evidence.json');src=O/'baseline_NightRemaster.ain';out=O/'NightRemaster.ain'
    assert b.a.sha(src)==e.EXPECTED and ev['files']=={'NightRemaster.ain':b.a.sha(out)}
    bm=b.read_meta(e.BASE/'candidate_meta.json');nm=b.read_meta(O/'candidate_meta.json')
    before=b.unpack(src.read_bytes());after=b.unpack(out.read_bytes());n=struct.unpack_from('<I',before,12)[0]
    assert after[16:16+n]==before[16:16+n]
    assert len(nm['functions'])==len(bm['functions'])+1
    for f,g in zip(bm['functions'],nm['functions']):
        test=dict(f)
        if f['index']==28658:test['address']=g['address']
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
            assert len(choices)==1,(path.name,rr);f=choices[0];fid=f['index'];assert fid!=28658 and nm['functions'][fid]==f
            addr=f['address']+rr['offset'];ops=next(v['ops'] for v in oldvs[fid] if v['start']==f['address']);op=dict(ops)[addr]
            assert before[16+addr:16+addr+2]==after[16+addr:16+addr+2]
            frames.append(dict(file=path.name,fid=fid,offset=rr['offset'],opcode=op))
    pop=(O/'built_28658.jam').read_text('utf8');end=(O/'built_32198.jam').read_text('utf8')
    assert pop.count('CALLFUNC KR_ExploreSegmentEnd')==1 and 'CALLHLL Array Erase' in pop
    assert 'KR_ExplorePlan' not in pop and 'KR_ExploreStart' not in pop
    assert 'PUSH 28659' in end and 'PUSH 2026092203' in end and 'S_PUSH "Pending"' in end
    # All other existing entrypoints, including ClearAutoMove, remain exact.
    assert nm['functions'][28659]==bm['functions'][28659]
    baseline=(O/'native_before_fix.txt').read_text('utf8')
    cap=b.a.readj(O/'native_before_fix_capture.json')
    assert cap['exit_code']==0 and not cap['events']
    assert 'STEP 4 at 17,6 queue=0 flag=0' in baseline and 'STOPPED EARLY moves=4 availableRoute=4' in baseline
    native=[]
    for mode in ['off','on']:
        log=(O/f'native_route_{mode}.txt').read_text('utf8');capture=b.a.readj(O/f'native_route_{mode}_capture.json')
        assert capture.get('exit_code')==0 and not capture['events'] and 'message' not in capture
        assert 'repeat-visible handlers=1' in log and 'clickResult=2026092203' in log
        assert f'STEP {8 if mode=="off" else 1} at ' in log and 'STOPPED through second click' in log
        assert 'STOPPED EARLY' not in log and 'FAIL' not in log
        assert log.count('PASS ')==5
        assert b.a.readj(O/f'native_route_{mode}_manifest.json')['source_sha256']==ev['files']['NightRemaster.ain']
        if mode=='off':assert 'STEP 4 at 17,6 queue=4 flag=2026092203' in log
        native.append(dict(mode=mode,pid=capture['pid'],probe_sha256=capture['ain_sha256'],log=log))
    assert p.snapshot_saves()==b.a.readj(O/'save_hashes_before_build.json')
    e.save('save_resume_check.json',dict(saves=len(records),frames=frames))
    report=dict(status='SEGMENT_FIX_STATIC_AND_NATIVE_DISPATCH_PASS',files=ev['files'],existing_resume_saves=len(records),saved_return_frames=len(frames),existing_save_local_offsets_exact=True,old_CODE_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native=native,scope='real copied dungeon save; native click/movement through two 4-step segment boundaries (8 steps OFF); guide ON one-step movement; second-click stop; natural/manual/pending/paused/native-only ownership boundaries',not_verified=['OS cursor hit testing','all dungeon/combat/stair transitions'],save_files_unchanged=len(p.snapshot_saves()))
    e.save('verification.json',report);print(json.dumps({k:v for k,v in report.items() if k!='native'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
