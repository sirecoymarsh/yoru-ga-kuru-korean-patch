"""Department-store scripted progression goals; no change to gameplay or save schemas."""
from pathlib import Path
import json,struct,shutil
from cheat_support_20260915 import cmd,read_meta,R,sha,savej
from repair_ui_runtime_weapon_text_20260913 import unpack
from audit_sys43_native_opcodes_20260915 import audit
from build_route_perf_20260915 import symbol

O=Path('route_department_20260915');BASE=Path('route_map_refresh_20260915')
def mapid():return '\t.LOCALREF map\n\tPUSH 27042\n\tCALLMETHOD 0\n'
def cellcall(mid):return f'\t.LOCALREF map\n\tPUSH {mid}\n\t.LOCALREF gx\n\t.LOCALREF gy\n\tCALLMETHOD 2\n'
def removed():
 #27082 returns SP_INC-owned reference; keep it across the borrowed getter,
 # then release it without losing the returned bool.
 return cellcall(27082)+'\tX_DUP 1\n\tPUSH 27023\n\tCALLMETHOD 0\n\tX_MOV 2 1\n\tDELETE\n'
def selector():
 s='\t.LOCALASSIGN bestX 2\n\t.LOCALASSIGN bestY 1\n'
 for mid in [202,204]:s+=mapid()+f'\tPUSH {mid}\n\tEQUALE\n\tIFNZ kr_department_exit\n'
 s+=mapid()+'\tPUSH 203\n\tNOTE\n\tIFNZ kr_goal_ready\n'
 # The four event groups remove themselves in plot order. Do not target an
 # arbitrary nearest event or a later gate while an earlier group remains.
 s+='\t.LOCALASSIGN bestX 7\n\t.LOCALASSIGN bestY 4\n\t.LOCALASSIGN gy 0\nkr_priority_y:\n\t.LOCALREF gy\n\tPUSH 30\n\tGTE\n\tIFNZ kr_goal_ready\n\t.LOCALASSIGN gx 0\nkr_priority_x:\n\t.LOCALREF gx\n\tPUSH 30\n\tGTE\n\tIFNZ kr_priority_next_y\n'
 s+=cellcall(27074)+'\tPUSH 7\n\tNOTE\n\tIFNZ kr_priority_next_x\n'+removed()+'\tIFNZ kr_priority_next_x\n'
 s+='\tPUSHLOCALPAGE\n\tPUSH 13\n'+cellcall(27075)+'\tX_ASSIGN 1\n\tPOP\n\t.LOCALREF n\n\tPUSH 0\n\tLT\n\tIFNZ kr_priority_next_x\n\t.LOCALREF n\n\t.LOCALREF bestY\n\tGTE\n\tIFNZ kr_priority_next_x\n\tPUSHLOCALPAGE\n\tPUSH 10\n\t.LOCALREF n\n\tX_ASSIGN 1\n\tPOP\n'
 s+='kr_priority_next_x:\n\t.LOCALINC2 gx\n\tJUMP kr_priority_x\nkr_priority_next_y:\n\t.LOCALINC2 gy\n\tJUMP kr_priority_y\nkr_department_exit:\n\t.LOCALASSIGN bestX 7\n\t.LOCALASSIGN bestY 0\nkr_goal_ready:\n'
 return s
def main():
 O.mkdir(exist_ok=True);p=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)=='552332f5dc6da24c07dd2f4a00531de2b3c0fb1fc1f39c8995baa464f61848f1'
 m=read_meta(BASE/'candidate_meta.json');f=O/'original_31860.jam';cmd('ain','dump','--function','KR_DrawRoute','-o',f,src);s=f.read_text(encoding='utf8')
 old='\t.LOCALASSIGN bestX -1\n\t.LOCALASSIGN bestY -1\n';assert s.count(old)==1;s=s.replace(old,'')
 pos=s.index('\t.LOCALASSIGN gy 0\n');s=s[:pos]+selector()+s[pos:]
 # Replace only the old stair predicate. Existing scan loop and search stay.
 start=s.index(cellcall(27074),s.index('kr_goal_ready:\n'))
 end=s.index('\t.LOCALREF route\n\tPUSH 0\n\tCALLHLL Array Realloc 2\n',start)
 pred=cellcall(27074)+'\t.LOCALREF bestX\n\tNOTE\n\tIFNZ 0x94d9ae\n'+cellcall(27075)+'\t.LOCALREF bestY\n\tNOTE\n\tIFNZ 0x94d9ae\n'
 pred+='\t.LOCALREF bestX\n\tPUSH 7\n\tNOTE\n\tIFNZ kr_candidate_ready\n'+removed()+'\tIFNZ 0x94d9ae\nkr_candidate_ready:\n'
 s=s[:start]+pred+s[end:]
 # bestX/bestY were unused stored coordinates; now selector locals throughout.
 old='\tPUSHLOCALPAGE\n\tPUSH 9\n\t.LOCALREF gx\n\tX_ASSIGN 1\n\tPOP\n\tPUSHLOCALPAGE\n\tPUSH 10\n\t.LOCALREF gy\n\tX_ASSIGN 1\n\tPOP\n'
 assert s.count(old)==1;s=s.replace(old,'')
 (O/'route_department_patch.jam').write_text(s,encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'route_department_patch.jam','-o',out,src)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,b in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y
  if aa!=bb:changed.append(a['index'])
 assert changed==[31860] and len(m['functions'])==len(nm['functions'])
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 a=unpack(src.read_bytes());b=unpack(out.read_bytes());size=struct.unpack_from('<I',a,12)[0]
 assert a[16:16+size]==b[16:16+size] and a[a.index(b'MSG1'):]==b[b.index(b'MSG1'):]
 for f in BASE.glob('built_*.jam'):shutil.copy2(f,O/f.name)
 cmd('ain','dump','--function','KR_DrawRoute','-o',O/'built_31860.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 native=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert native['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',native)
 ev=dict(status='DEPARTMENT_EVENT_ROUTE_STAGED',source_pointer=p,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},patched_function_ids=[31860],
  source_ex_sha256=sha(rt/'NightRemasterEX.ex'),target_rules={'default':'stair ObjectId2 SubId1 unchanged','202':'unremoved event ObjectId7 SubId0','203':'smallest unremoved SubId0..3 for ObjectId7, then nearest in that group','204':'unremoved escape event ObjectId7 SubId0'},
  source_function_evidence=[27070,28865,28879,28880,28881,28882,28896,29171],old_CODE_MSG1_STR0_and_other_metadata_exact=True,UI_gameplay_events_save_schemas_unchanged=True,
  cache_and_post_transition_hooks_preserved=True,native_gameplay_verified=False)
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,indent=2))
if __name__=='__main__':main()
