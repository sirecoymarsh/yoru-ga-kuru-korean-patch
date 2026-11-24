"""Keep exploration ownership on natural route-segment completion only."""
from pathlib import Path
import json,re,struct,shutil
import build_auto_explore_click_fix_20260923 as e
from build_dungeon_sweep_20260916 import push,cf,lr
R=e.R;O=R/'staging/auto_explore_segment_fix_20260923';BASE=e.O;HERE=e.HERE;b=e.b;p=e.p;q=e.q
EXPECTED='2c1b0174ddefda36b00ab864146eefe070971e9c6cc914df6ef14a2e560dfc86'

def save(name,obj):(O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    O.mkdir(exist_ok=True);ptr=b.a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
    assert b.a.sha(src)==EXPECTED and b.a.sha(Path(ptr['manifest']))==ptr['manifest_sha256']
    p.exact_tree(rt,b.a.readj(Path(ptr['manifest']))['files']);save('source_pointer.json',ptr);save('save_hashes_before_build.json',p.snapshot_saves());shutil.copy2(src,O/'baseline_NightRemaster.ain')
    m=b.read_meta(BASE/'candidate_meta.json');decl=O/'declared.ain';b.cmd('ain','edit','--jaf',HERE/'auto_explore_segment_fix_20260923.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added}
    patch=[]
    for f in added:
        n=f['name'];fid=f['index'];path=O/f'jaf_{fid}.jam';b.cmd('ain','dump','--function',n,'-o',path,decl)
        body=b.clean(b.native_lower(path.read_text('utf-8')),n)
        patch.append(body)
    tmp=O/'pop_template.jam';b.cmd('ain','dump','--function',b.symbol(m,28658),'-o',tmp,src)
    t=b.clean(tmp.read_text('utf8'),b.symbol(m,28658))
    oldcall='\tPUSHSTRUCTPAGE\n\tPUSH 28659\n\tCALLMETHOD 0\n'
    assert t.count(oldcall)==1
    t=t.replace(oldcall,'\tPUSHSTRUCTPAGE\n'+cf('KR_ExploreSegmentEnd'))
    # Existing labels resolve against the appended body; no old CODE writes.
    patch.append(t)
    (O/'patch.jam').write_text('\n'.join(patch),'utf-8');out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    raw=bytearray(b.unpack(out.read_bytes()));old=b.unpack(src.read_bytes());n=struct.unpack_from('<I',raw,12)[0];oldn=struct.unpack_from('<I',old,12)[0];struct.pack_into('<I',raw,24+n,m['functions'][0]['address']);out.write_bytes(b.pack(raw,src.read_bytes()[:8]))
    assert raw[16:16+oldn]==old[16:16+oldn]
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(raw)[2][:len(b.strings(old)[2])]==b.strings(old)[2]
    b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    for i,(x,y) in enumerate(zip(m['functions'],nm['functions'])):
        z=dict(x)
        if i==28658:z['address']=y['address']
        assert z==y,i
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    for fid in [28658]+list(ids.values()):b.cmd('ain','dump','--function',b.raw_symbol(nm,fid),'-o',O/f'built_{fid}.jam',out)
    report=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',report);assert report['all_active_opcodes_supported']
    ev=dict(status='SEGMENT_FIX_STAGED',source_pointer=ptr,source_files={'NightRemaster.ain':EXPECTED},files={'NightRemaster.ain':b.a.sha(out)},patched_existing=[28658],added_functions=ids,old_CODE_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,save_writes=0)
    save('build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
