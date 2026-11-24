import collections,json,re,struct
import build_runtime_repairs_20260923 as e
b=e.b;p=e.p;q=e.q;O=e.O
def main():
    ev=b.a.readj(O/'build_evidence.json');src=O/'baseline_NightRemaster.ain';out=O/'NightRemaster.ain'
    assert e.h(src)==e.EXPECTED and ev['files']=={n:e.h(O/n) for n in e.FILES}
    assert p.stopped(p.RT),'Game must be closed for the final save snapshot'
    saves=p.snapshot_saves();e.save('save_hashes_before_validation.json',saves)
    bm=b.read_meta(e.BASE/'candidate_meta.json');nm=b.read_meta(O/'candidate_meta.json')
    before=b.unpack(src.read_bytes());after=b.unpack(out.read_bytes());n=struct.unpack_from('<I',before,12)[0]
    reverted=bytearray(after[16:16+n])
    for change in ev['same_length_sites']:
        a=change['address'];assert reverted[a:a+6].hex()==change['after'];reverted[a:a+6]=bytes.fromhex(change['before'])
        old_id=struct.unpack_from('<i',bytes.fromhex(change['before']),2)[0];new_id=struct.unpack_from('<i',bytes.fromhex(change['after']),2)[0]
        assert bm['functions'][old_id]['return-type']==nm['functions'][new_id]['return-type']
        assert [v['type'] for v in bm['functions'][old_id]['arguments']]==[v['type'] for v in nm['functions'][new_id]['arguments']]
    assert reverted==before[16:16+n]
    for f,g in zip(bm['functions'],nm['functions']):
        test=dict(f)
        if f['index'] in ev['relocated']:test['address']=g['address']
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
            assert len(choices)==1,(path.name,rr);f=choices[0];fid=f['index'];assert fid not in ev['relocated'] and nm['functions'][fid]==f
            addr=f['address']+rr['offset'];assert before[16+addr:16+addr+2]==after[16+addr:16+addr+2]
            frames.append(dict(file=path.name,fid=fid,offset=rr['offset']))
    assert ev['PACT']['replaced_ids']==[154] and len(ev['layout'])==6
    assert b.a.readj(O/'native_opcode_audit.json')['all_active_opcodes_supported']
    required={
      'prefs_domain':['PASS native input conversion 2372 cases','PASS native one-character name commit and restore','PASS changed preference roundtrip','PASS rejected preference write preserves main','PASS damaged preference uses valid backup','NEXT_OPEN true','NEXT_CLOSE true'],
      'prefs_reload':['PASS preference reloaded in fresh native process'],
      'result':['PASS manual and unrelated results remain manual','PASS native result Run/Clearup','PASS native levelup auto-close and ordinary dialog scope'],
      'weapon':['destroy_weapon_view','destroy_memory_view','RETURN weapon controller 0','END'],
      'battle_walk':['RESULT flag=','RESULT_CLEAR','PASS moved after native battle result'],
      'walk_regression':['STEP 8','STOPPED through second click']}
    native={}
    for name,keys in required.items():
        cap=b.a.readj(O/'native'/f'{name}_capture.json');man=b.a.readj(O/'native'/f'{name}_manifest.json');log=(O/'native'/f'{name}_log.txt').read_bytes().decode('cp932',errors='replace')
        assert cap.get('exit_code')==0 and not cap.get('message') and not cap.get('vm_error') and not cap['events'],(name,cap)
        assert cap['ain_sha256']==man['probe_sha256'] and man['source_sha256']==e.h(out)
        assert 'FAIL ' not in log and all(k in log for k in keys),(name,log)
        native[name]=dict(pid=cap['pid'],probe_sha256=cap['ain_sha256'],log_sha256=e.h(O/'native'/f'{name}_log.txt'))
    images={n:e.h(O/'native'/n) for n in ['weapon_dialog_2.png','weapon_memory_before_cancel.png','weapon_returned_home.png']}
    e.save('native/visual_review.json',dict(reviewer='Codex internal',images=images,comparison='Six blue/pink attribute/range/distance values fit inside their original black cells; SP cost remains separated from its label.',cancellation='Both native view destructors execute, and their old panels disappear. Diagnostic home background is not initialized; residual copied dungeon party HUD is not a claim about normal home rendering.'))
    assert saves==p.snapshot_saves()
    e.save('save_resume_check.json',dict(saves=len(records),frames=frames))
    e.save('verification.json',dict(status='RUNTIME_REPAIRS_STATIC_AND_NATIVE_PASS',files=ev['files'],existing_resume_saves=len(records),saved_return_frames=len(frames),existing_save_local_offsets_exact=True,old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native_checks_passed=True,native=native,native_summary='Owned encounter result closes after 800 ms, native enemy battle returns to dungeon, automatic movement resumes; manual and unrelated results remain manual.',not_verified=['Physical Korean IME typing and mouse hit testing','Full next-day scenario on the user save; isolated native summary writer passed after both successful and rejected preference writes'],images=images,original_save_files_unchanged=len(saves),translator_model='Codex internal'))
    print('PASS',len(records),'saves',len(frames),'frames',native)
if __name__=='__main__':main()
