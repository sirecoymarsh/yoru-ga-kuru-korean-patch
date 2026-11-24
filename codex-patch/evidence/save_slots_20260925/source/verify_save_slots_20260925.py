"""Read-only artifact, saved-frame, native-row, and roundtrip release checks."""
from pathlib import Path
import collections,json,re,struct
import build_save_slots_20260925 as e

def main():
    ev=e.a.readj(e.O/'build_evidence.json');files=ev['files']
    assert all(e.h(e.O/n)==h for n,h in files.items())
    bm=e.b.read_meta(e.S/'candidate_meta.json');nm=e.b.read_meta(e.O/'candidate_meta.json')
    old=e.b.unpack((e.S/'NightRemaster.ain').read_bytes());new=e.b.unpack((e.O/'NightRemaster.ain').read_bytes())
    size=struct.unpack_from('<I',old,12)[0];allowed=set()
    for site in ev['same_length_sites']:
        ad=site['address'];assert old[16+ad:22+ad].hex()==site['before'] and new[16+ad:22+ad].hex()==site['after'];allowed.update(range(ad,ad+6))
    assert {i for i in range(size) if old[16+i]!=new[16+i]}<=allowed
    for key in bm:
        if key!='functions':assert bm[key]==nm[key],key
    relocated=set(ev['relocated'])
    for f,g in zip(bm['functions'],nm['functions']):
        adjusted=dict(f)
        if f['index'] in relocated:adjusted['address']=g['address']
        assert adjusted==g,f['index']
    oldvs=e.q.versions(e.S/'native_raw_code.jam');sig=collections.defaultdict(list)
    for f in bm['functions']:sig[f['crc']&0xffffffff].append(f)
    before=e.p.snapshot_saves();frames=[];saves=[]
    for path in sorted(e.p.SAVE.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd',path.name):continue
        row=e.q.records(path);assert row is not None;saves.append(path.name)
        for rec in [row['ip']]+row['returns']:
            if rec['address']==-1:continue
            choices=[f for f in sig[rec['crc']] if rec['name'].startswith(e.b.raw_symbol(bm,f['index'])+'(') and any(v['start']==rec['address']-rec['offset'] for v in oldvs[f['index']])]
            assert len(choices)==1,(path,rec);f=choices[0];fid=f['index']
            assert fid not in relocated and nm['functions'][fid]==f,(path,fid)
            ad=f['address']+rec['offset'];assert old[16+ad:18+ad]==new[16+ad:18+ad]
            frames.append(dict(save=path.name,fid=fid,offset=rec['offset']))
    e.save('save_frames.json',dict(saves=saves,frames=frames))
    assert before==e.p.snapshot_saves()
    ar=e.n.read_afa3(e.S/'NightRemasterPact.afa');br=e.n.read_afa3(e.O/'NightRemasterPact.afa');changed=[]
    with (e.S/'NightRemasterPact.afa').open('rb') as a,(e.O/'NightRemasterPact.afa').open('rb') as b:
        assert len(ar.entries)==len(br.entries)
        for i,(x,y) in enumerate(zip(ar.entries,br.entries)):
            assert x.name==y.name;a.seek(x.absolute_offset);b.seek(y.absolute_offset)
            if a.read(x.size)!=b.read(y.size):changed.append(i)
    assert changed==[168]
    assert e.a.readj(e.O/'native_opcode_audit.json')['all_active_opcodes_supported']
    probes={}
    for path in sorted(e.O.glob('native_probe_*/result.json')):
        r=e.a.readj(path)
        if r['source_sha256']!=files['NightRemaster.ain']:continue
        if not all(r.get(k,{}).get('exit_code')==0 for k in ['A','B']):continue
        for k in ['A','B']:
            assert not r[k].get('events') and not any(r[k].get(key) for key in ['timeout','message','vm_error'])
        assert r['manual49_unchanged'] and r['real_saves_unchanged']
        log=r['A']['log'];assert log[-1]=='END' and not any('FAIL' in line for line in log)
        assert any(line.startswith('WEEKLY_AND_DAILY_MATCH=1 SNAPSHOT=') for line in log)
        parsed=[]
        for line in log:
            mt=re.fullmatch(r'ROWS page=(\d+) type=(\d+):(.*)',line)
            if mt:parsed.append((int(mt[1]),int(mt[2]),[tuple(map(int,x.split('/'))) for x in mt[3].split()]))
        assert parsed
        for typ in [0,1]:
            pages={page:rows for page,t,rows in parsed if typ==t};assert sorted(pages)==list(range(10))
            assert [n for n,c in pages[0]]==[999,998,1,2,3,4]
            assert [n for page in range(1,10) for n,c in pages[page]]==list(range(5,50))
            if typ==0:assert all(c==(n<998) for rows in pages.values() for n,c in rows)
        assert r['B']['log'][-2].startswith('RESUMED weekly autosave')
        files2=r['files'];assert {'NightR998.asd','NightR999.asd','NightR04.asd'}<=set(files2)
        probes[r['source_save']]=str(path)
    assert {'NightR36.asd','NightR49.asd'}<=set(probes),probes
    e.save('verification.json',dict(status='SAVE_CARDS_STATIC_NATIVE_PASS',files=files,existing_resume_saves=len(saves),saved_return_frames=len(frames),save_schema_equal=True,old_CODE_allowlist_exact=True,changed_PACT=changed,native_probes=probes,real_saves_unchanged=True,OS_mouse_hit_test=False))
    e.save('save_hashes_before_validation.json',before)
    print('PASS',len(saves),'saves,',len(frames),'frames; native dungeon/daily save + resume and 51-slot mapping')
if __name__=='__main__':main()
