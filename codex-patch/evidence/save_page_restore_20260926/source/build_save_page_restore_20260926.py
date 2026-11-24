"""Restore native last-manual-save page selection; retain independent autosave rows."""
from pathlib import Path
import collections,json,re,shutil,struct
import build_event_navigation_20260926 as base
b=base.b;p=base.p;q=base.q;a=base.a;n=base.n;R=base.R;HERE=Path(__file__).parent
O=R/'staging/save_page_restore_20260926';S=O/'source';AUTHOR='Codex internal'
h=base.h;clean=base.clean;textdump=base.textdump;wrapper=base.wrapper
EXPECTED='c1014763926f31c79b161a70f55cdd6b24a5dde24ba79d1a73a56996d7f65bee'

def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
    assert not O.exists(),'Do not overwrite the frozen baseline'
    ptr=p.read(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);assert h(rt/'NightRemaster.ain')==EXPECTED
    assert h(Path(ptr['manifest']))==ptr['manifest_sha256'];S.mkdir(parents=True)
    for name in ['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']:shutil.copy2(rt/name,S/name)
    save('source_pointer.json',ptr)
    for name in ['candidate_meta.json','native_raw_code.jam']:shutil.copy2(R/'staging/event_navigation_20260926'/name,S/name)
    m=b.read_meta(S/'candidate_meta.json');src=S/'NightRemaster.ain'
    body=clean(m,29571,src)
    old='\tPUSH 29577\n\tPUSH 0\n\tPUSH 0\n\tCALLMETHOD 2\n\tPUSHSTRUCTPAGE\n\tPUSH 29567\n'
    new=old.replace('\tPUSH 29577\n\tPUSH 0\n','\tPUSH 29577\n\t.LOCALREF pageNo\n',1)
    assert body.count(old)==1
    assert '\tPUSH 29582\n\tPUSH -1\n\tPUSH 0\n\tPUSH 0\n\tCALLMETHOD 3\n' in body
    (O/'before_init.jam').write_text(body,'utf8');body=body.replace(old,new)
    (O/'patch.jam').write_text(body,'utf8');out=O/'NightRemaster.ain'
    b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,src)
    raw=bytearray(b.unpack(out.read_bytes()));oldraw=b.unpack(src.read_bytes());size=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(b.pack(raw,src.read_bytes()[:8]))
    oldsize=struct.unpack_from('<I',oldraw,12)[0];assert raw[16:16+oldsize]==oldraw[16:16+oldsize]
    b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    relocated=[29571,*range(31683,31694)]
    assert len(m['functions'])==len(nm['functions'])
    for f,g in zip(m['functions'],nm['functions']):
        expect=dict(f)
        if f['index'] in relocated:expect['address']=g['address']
        assert expect==g,f['index']
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(raw)[2]==b.strings(oldraw)[2]
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported']
    save('native_opcode_audit.json',audit)
    for name in ['NightRemasterPact.afa','NightRemasterEX.ex']:shutil.copy2(S/name,O/name)
    # Saved runtime frames and all serialized declarations must remain compatible.
    vs=q.versions(S/'native_raw_code.jam');sig=collections.defaultdict(list)
    for f in m['functions']:sig[f['crc']&0xffffffff].append(f)
    before=p.snapshot_saves();frames=[];saves=[]
    for path in sorted(p.SAVE.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd',path.name):continue
        recs=q.records(path);assert recs is not None;saves.append(path.name)
        for rec in [recs['ip']]+recs['returns']:
            if rec['address']==-1:continue
            choices=[f for f in sig[rec['crc']] if rec['name'].startswith(b.raw_symbol(m,f['index'])+'(') and any(v['start']==rec['address']-rec['offset'] for v in vs[f['index']])]
            assert len(choices)==1,(path,rec);f=choices[0];fid=f['index'];assert fid not in relocated
            ad=f['address']+rec['offset'];assert oldraw[16+ad:18+ad]==raw[16+ad:18+ad]
            frames.append(dict(save=path.name,fid=fid,offset=rec['offset']))
    assert before==p.snapshot_saves();save('save_frames.json',dict(saves=saves,frames=frames))
    save('build_evidence.json',dict(status='STAGED_NATIVE_PENDING',source_pointer=ptr,files={name:h(O/name) for name in ['NightRemaster.ain','NightRemasterPact.afa']},relocated=relocated,
         old_CODE_exact=True,serialized_schema_changes=0,MSG1_exact=True,STR0_exact=True,changed_PACT=[],existing_resume_saves=len(saves),saved_return_frames=len(frames),
         cause='Init computed pageNo from latest manual save, then discarded it by Update(0,false). Restore Update(pageNo,false); existing clamp and updated slot mapper remain.',translator_model=AUTHOR))
    print('BUILT',len(saves),'save schemas;',len(frames),'compatible saved frames')

if __name__=='__main__':main()
