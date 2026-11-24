"""Recognize verified event-exit maps without changing native events or save frames."""
from pathlib import Path
import json,shutil,struct
import build_story_progress_20260926 as base
import review_navigation_20260926 as review
b=base.b;p=base.p;q=base.q;a=base.a;n=base.n;R=base.R;HERE=Path(__file__).parent
O=R/'staging/event_navigation_20260926';S=review.O
h=base.h;clean=base.clean;textdump=base.textdump;wrapper=base.wrapper;AUTHOR='Codex internal'
MAPS=[101,102,303,503,605,803]
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
    review.prepare();O.mkdir(exist_ok=True)
    source=S/'NightRemaster.ain';m=b.read_meta(S/'candidate_meta.json');ptr=a.readj(S/'source_pointer.json')
    rt=Path(ptr['runtime']);assert h(source)==review.EXPECTED
    # Object 6/sub0 is the native progress event for these six maps.
    # 101/605 require the active B1 story/party trigger first; removal by native code advances the target.
    jaf='''bool KR_EventRouteOrdered(int mode) { return mode==203 || mode==101 || mode==605; }
int KR_EventRouteTag(int mode,int obj,int sub,bool removed) {
    if(removed || sub!=0) return 0;
    if(obj==7 && (mode==101 || mode==605)) return 1;
    if(obj==6) { if(mode==101 || mode==605) return 2; return 1; }
    return 0;
}
'''
    (O/'helpers_readable.jaf').write_text(jaf,'utf8');(O/'helpers.jaf').write_text(jaf,'utf8')
    declared=O/'declared.ain';b.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',declared,source)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',declared);dm=b.read_meta(O/'declared_meta.json')
    added=dm['functions'][len(m['functions']):];patches=[b.clean(b.native_lower(textdump(dm,f['index'],declared)),f['name']) for f in added]
    names={f['name']:f['index'] for f in m['functions']};relocated=[]
    # Reuse exact bounded BFS and only broaden its verified ordered-target classifier.
    needle='\t.LOCALREF mode\n\tPUSH 203\n\tEQUALE\n'
    for name in ['KR_DrawRouteLinear','KR_WalkPlanLinear']:
        fid=names[name];body=clean(m,fid,source);assert body.count(needle)==2
        body=body.replace(needle,'\t.LOCALREF mode\n\tCALLFUNC KR_EventRouteOrdered\n')
        patches.append(body);relocated.append(fid)
    fid=names['KR_RouteCellLinear'];body=clean(m,fid,source)
    # Unknown and previously supported maps execute the prior accessor byte-for-byte body.
    guard=''.join(f'\t.LOCALREF mode\n\tPUSH {mid}\n\tEQUALE\n\tIFNZ event_route_cell\n' for mid in MAPS)
    body=body.replace(f'FUNC {fid}\n',f'FUNC {fid}\n'+guard,1)
    code='''event_route_cell:
	PUSHLOCALPAGE
	PUSH 4
	.LOCALREF map
	PUSH 27082
	.LOCALREF x
	.LOCALREF y
	CALLMETHOD 2
	X_ASSIGN 1
	POP
	.LOCALREF cell
	PUSH -1
	EQUALE
	IFNZ event_route_null
	PUSHLOCALPAGE
	PUSH 5
	.LOCALREF cell
	PUSH 27039
	CALLMETHOD 0
	.LOCALREF mode
	.LOCALREF cell
	PUSH 27005
	CALLMETHOD 0
	.LOCALREF cell
	PUSH 27008
	CALLMETHOD 0
	.LOCALREF cell
	PUSH 27023
	CALLMETHOD 0
	CALLFUNC KR_EventRouteTag
	PUSH 2
	MUL
	ADD
	X_ASSIGN 1
	POP
	.LOCALDELETE cell
	.LOCALREF code
	RETURN
event_route_null:
	PUSH 0
	RETURN
'''
    assert [v['name'] for v in m['functions'][fid]['arguments']+m['functions'][fid]['variables']]==['map','x','y','mode','cell','code','sub']
    body=body.replace('ENDFUNC KR_RouteCellLinear\n',code+'ENDFUNC KR_RouteCellLinear\n')
    patches.append(body);relocated.append(fid)
    (O/'patch.jam').write_text('\n'.join(patches),'utf8');out=O/'NightRemaster.ain'
    b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,declared)
    old=b.unpack(source.read_bytes());raw=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',old,12)[0];ns=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+ns,m['functions'][0]['address']);assert raw[16:16+size]==old[16:16+size]
    out.write_bytes(b.pack(raw,source.read_bytes()[:8]));b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out)
    nm=b.read_meta(O/'candidate_meta.json')
    for f,g in zip(m['functions'],nm['functions']):
        compare=dict(f)
        if f['index'] in relocated:compare['address']=g['address']
        assert compare==g,f['index']
    for key in m:
        if key!='functions':assert m[key]==nm[key],key
    assert b.raw_messages(source.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(raw)[2][:len(b.strings(old)[2])]==b.strings(old)[2]
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported'];save('native_opcode_audit.json',audit)
    for name in ['NightRemasterPact.afa','NightRemasterEX.ex']:shutil.copy2(S/name,O/name)
    save('source_pointer.json',ptr)
    save('build_evidence.json',dict(status='STAGED_UNVERIFIED',files={name:h(O/name) for name in ['NightRemaster.ain','NightRemasterPact.afa']},source_pointer=ptr,relocated=sorted(relocated),added_functions={f['name']:f['index'] for f in added},same_length_sites=[],PACT={'changed_entries':[]},serialized_schema_changes=0,MSG1_exact=True,STR0_prefix_exact=True,maps=MAPS,ordered_B1_then_R1=[101,605],native_events_unchanged=True,blind_fallback=False,translator_model=AUTHOR))
    print('STAGED',O,h(out),flush=True)
if __name__=='__main__':main()
