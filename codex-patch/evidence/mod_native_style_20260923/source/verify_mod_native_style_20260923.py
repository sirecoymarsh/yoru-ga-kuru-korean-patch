"""Verify exact instruction allowlist, save return frames, archive identity, and engine captures."""
import collections,re,struct,json,shutil
from PIL import Image
import numpy as np
import build_mod_native_style_20260923 as e
from build_mod_style_probe_20260923 import D
b=e.b;p=e.p;q=e.q;O=e.O

def main():
    ev=b.a.readj(O/'build_evidence.json');src=O/'baseline_NightRemaster.ain';out=O/'NightRemaster.ain'
    assert e.h(src)==e.EXPECTED and ev['files']=={n:e.h(O/n) for n in e.FILES}
    bm=b.read_meta(e.BASE/'candidate_meta.json');nm=b.read_meta(O/'candidate_meta.json')
    before=b.unpack(src.read_bytes());after=b.unpack(out.read_bytes());n=struct.unpack_from('<I',before,12)[0]
    reverted=bytearray(after[16:16+n])
    for change in ev['AIN']['in_place_instructions']:
        a=change['address'];assert reverted[a:a+6].hex()==change['after'];reverted[a:a+6]=bytes.fromhex(change['before'])
    assert reverted==before[16:16+n]
    for f,g in zip(bm['functions'],nm['functions']):
        test=dict(f)
        if f['index'] in ev['AIN']['relocated']:test['address']=g['address']
        assert test==g,f['index']
    for k in bm:
        if k!='functions':assert bm[k]==nm[k],k
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    oldstr=b.strings(before)[2];newstr=b.strings(after)[2]
    assert [i for i,(a,z) in enumerate(zip(oldstr,newstr)) if a!=z]==[r['index'] for r in ev['AIN']['renamed_strings']]
    oldvs=q.versions(e.BASE/'native_raw_code.jam');sig=collections.defaultdict(list)
    for f in bm['functions']:sig[f['crc']&0xffffffff].append(f)
    records=[];frames=[]
    for path in sorted(p.SAVE.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd',path.name):continue
        row=q.records(path);assert row is not None;records.append(row)
        for rr in [row['ip']]+row['returns']:
            if rr['address']==-1:continue
            choices=[f for f in sig[rr['crc']] if rr['name'].startswith(b.raw_symbol(bm,f['index'])+'(') and any(v['start']==rr['address']-rr['offset'] for v in oldvs[f['index']])]
            assert len(choices)==1,(path.name,rr);f=choices[0];fid=f['index'];assert fid not in ev['AIN']['relocated'] and nm['functions'][fid]==f
            addr=f['address']+rr['offset'];assert before[16+addr:16+addr+2]==after[16+addr:16+addr+2]
            frames.append(dict(file=path.name,fid=fid,offset=rr['offset']))
    assert ev['CG']['replaced_ids']==[] and len(ev['CG']['appended'])==12
    assert ev['PACT']['archive']['replaced_ids']==[154,161] and ev['PACT']['outside_mod_roots_exact']
    for r in ev['assets']:assert r['protected_pixel_changes']==0 and r['roundtrip']=='PASS'
    capture_path=O/'native/capture.json'
    if not capture_path.exists():capture_path=e.HERE/'native_error_capture_20260923.json'
    cap=b.a.readj(capture_path);pm=b.a.readj(O/'native_probe_manifest.json')
    assert cap.get('exit_code')==0 and not cap['events'] and 'message' not in cap and 'timeout' not in cap
    assert cap['ain_sha256']==pm['probe_sha256'] and pm['candidate_files']==ev['files']
    log=(D/'style_probe.txt').read_text('utf8');assert 'FAIL' not in log and 'PASS affirmative/cancel and one-shot focus isolation' in log
    assert log.count('DEFAULT 1')==4 and log.count('DEFAULT 0')==1
    evidence=O/'native';evidence.mkdir(exist_ok=True)
    shutil.copy2(D/'style_probe.txt',evidence/'style_probe.txt')
    if capture_path!=evidence/'capture.json':shutil.copy2(capture_path,evidence/'capture.json')
    shots={}
    for name in ['dungeon_1','dungeon_2','dungeon_3','dungeon_stop','weapon_1','weapon_2','weapon_3','sweep_confirm','recommend_confirm','ordinary_dialog']:
        path=D/(name+'.bmp');im=Image.open(path).convert('RGB');assert im.size==(1280,720)
        out=evidence/(name+'.png');im.save(out);shots[name]=dict(path=str(out),sha256=e.h(out))
    # Native capture must actually contain the correct asset, not just open successfully.
    matches=[]
    # Weapon activity has a native +160px centered-layout parent translation.
    for name,key,state,xy in [('dungeon_1','walk',0,(1145,443)),('dungeon_1','sweep',0,(1145,388)),('dungeon_stop','stop',0,(1145,443)),('weapon_1','stone',0,(1108,435))]:
        r=next(a for a in ev['assets'] if a['key']==key and a['state']==state);art=np.array(Image.open(r['png']).convert('RGBA'));screen=np.array(Image.open(shots[name]['path']).convert('RGB'))
        x,y=xy;crop=screen[y:y+art.shape[0],x:x+art.shape[1]];opaque=art[:,:,3]==255
        fraction=float(np.mean(np.max(np.abs(crop.astype('int16')-art[:,:,:3].astype('int16')),axis=2)[opaque]<=1))
        assert fraction>.995,(name,key,fraction)
        matches.append(dict(screenshot=name,key=key,opaque_pixel_match=fraction))
    assert p.snapshot_saves()==b.a.readj(O/'save_hashes_before_build.json')
    e.save('save_resume_check.json',dict(saves=len(records),frames=frames))
    report=dict(status='MOD_NATIVE_STYLE_STATIC_AND_ENGINE_PASS',files=ev['files'],existing_resume_saves=len(records),saved_return_frames=len(frames),existing_save_local_offsets_exact=True,old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_changes=ev['AIN']['renamed_strings'],save_schema_changes=0,native=cap,shots=shots,render_matches=matches,choice_scope='Affirmative is initial cursor index 1 only for mod confirmations; cancel and accept IDs tested without executing gameplay operations; ordinary menus remain index0. Native craft confirmation is already OK-first and unchanged.',state_scope='All three source state textures and bindings statically verified. Native screenshots prove normal/start/stop only; SetInputState did not force a hover transition. Weapon activity instantiated over copied dungeon solely to exercise its native loader and parts, not a full scene transition.',not_verified=['OS mouse hit testing','hover/down input transition','full gameplay sweep or synthesis execution'],save_files_unchanged=len(p.snapshot_saves()),translator_model='Codex internal')
    e.save('verification.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['shots','native','STR0_changes']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
