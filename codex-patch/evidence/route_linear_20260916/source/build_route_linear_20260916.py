"""Bounded linear route preview, leaving native gameplay and save schemas intact."""
from pathlib import Path
import json,re,struct,shutil
from cheat_support_20260915 import R,cmd,read_meta,sha,savej
from build_route_perf_20260915 import symbol,RESET
from build_instant_loot_20260915 import clean
from repair_ui_runtime_weapon_text_20260913 import unpack,pack
from audit_sys43_native_opcodes_20260915 import native_lower,audit

S=Path(__file__).resolve().parent
O=R/'staging/route_linear_20260916'
EXPECTED='edf32d46d6ee1baa1c2101c6fca39a74aaa53f5e91033c9f03c3f3ee2a5e50b5'
IDS=[27007,27010,27025,27031,31860]
def lr(n):return f'\t.LOCALREF {n}\n'
def push(n):return f'\tPUSH {n}\n'
def cm(obj,i,args='',argc=0):return obj+push(i)+args+f'\tCALLMETHOD {argc}\n'
def assign(i,e):return '\tPUSHLOCALPAGE\n'+push(i)+e+'\tX_ASSIGN 1\n\tPOP\n'

def main():
 O.mkdir(parents=True,exist_ok=True);p=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime']);src=rt/'NightRemaster.ain';assert sha(src)==EXPECTED
 cmd('ain','dump','-j','-o',O/'source_meta.json',src);m=read_meta(O/'source_meta.json');names={};seen={}
 for f in m['functions']:
  n=symbol(m,f['index']);c=seen.get(n,0);seen[n]=c+1;names[f['index']]=n+(f'#{c}' if c else '')
 jaf=S/'route_linear_helpers_20260916.jaf';shutil.copy2(jaf,O/jaf.name);decl=O/'declared.ain';cmd('ain','edit','--jaf',jaf,'-o',decl,src)
 # ain edit's declaration pass resets function0's address; retain the active source.
 old=unpack(src.read_bytes());raw=bytearray(unpack(decl.read_bytes()));size=struct.unpack_from('<I',old,12)[0];ns=struct.unpack_from('<I',raw,12)[0]
 assert raw[16:16+size]==old[16:16+size];struct.pack_into('<I',raw,24+ns,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');new={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};assert set(new)=={'KR_RouteAppendLinear','KR_RouteCellLinear','KR_DrawRouteLinear'}
 patches=[]
 for fid in IDS:
  path=O/f'original_{fid}.jam';cmd('ain','dump','--function',names[fid],'-o',path,src);s=clean(path.read_text(encoding='utf8'),names[fid])
  if fid==31860:
   guard='\tCALLFUNC KR_GetRoute\n\tIFZ route_linear_miss\n'+push(89)+'\tCALLFUNC KR_Flag\n'+push(1)+'\tNOTE\n\tIFNZ route_linear_miss\n'
   for slot,xy in [(85,'x'),(86,'y')]:guard+=push(slot)+'\tCALLFUNC KR_Flag\n'+lr(xy)+'\tNOTE\n\tIFNZ route_linear_miss\n'
   guard+='\tRETURN\nroute_linear_miss:\n'
   s=f'FUNC {fid}\n'+guard+''.join(lr(v) for v in ['map','view','x','y'])+cm(lr('map'),27042)+'\tCALLFUNC KR_DrawRouteLinear\n\tRETURN\nENDFUNC KR_DrawRoute\n'
  else:
   fld={27007:3,27010:4,27025:9,27031:11}[fid];assert s.count(RESET)==1
   guard='\tPUSHSTRUCTPAGE\n'+push(fld)+'\tX_REF 1\n'+lr('value')+'\tEQUALE\n\tIFNZ route_same_value\n'
   s=s.replace(RESET,(guard+RESET+'route_same_value:\n').replace('route_same_value',f'route_same_value_{fid}'))
  patches.append(s)
 cell=dm['functions'][new['KR_RouteCellLinear']];assert [v['name'] for v in cell['variables']]==['cell','code','sub']
 b=assign(4,cm(lr('map'),27082,lr('x')+lr('y'),2))+lr('cell')+push(-1)+'\tEQUALE\n\tIFNZ cell_null\n'
 b+=assign(5,cm(lr('cell'),27039))
 b+=lr('mode')+push(202)+'\tEQUALE\n\tIFNZ event_goal\n'+lr('mode')+push(203)+'\tEQUALE\n\tIFNZ event_goal\n'+lr('mode')+push(204)+'\tEQUALE\n\tIFNZ event_goal\n'
 b+=cm(lr('cell'),27005)+push(2)+'\tNOTE\n\tIFNZ cell_done\n'+cm(lr('cell'),27008)+push(1)+'\tNOTE\n\tIFNZ cell_done\n'+assign(5,lr('code')+push(2)+'\tADD\n')+'\tJUMP cell_done\n'
 b+='event_goal:\n'+cm(lr('cell'),27005)+push(7)+'\tNOTE\n\tIFNZ cell_done\n'+cm(lr('cell'),27023)+'\tIFNZ cell_done\n'+assign(6,cm(lr('cell'),27008))
 b+=lr('sub')+push(0)+'\tLT\n\tIFNZ cell_done\n'+lr('sub')+push(4)+'\tGT\n\tIFNZ cell_done\n'+lr('mode')+push(203)+'\tEQUALE\n\tIFNZ event_tag\n'+lr('sub')+'\tIFNZ cell_done\nevent_tag:\n'
 b+=assign(5,lr('code')+lr('sub')+push(1)+'\tADD\n'+push(2)+'\tMUL\n\tADD\n')
 b+='cell_done:\n\t.LOCALDELETE cell\n'+lr('code')+'\tRETURN\ncell_null:\n'+push(0)+'\tRETURN\n'
 patches.append(f"FUNC {new['KR_RouteCellLinear']}\n"+b+'ENDFUNC KR_RouteCellLinear\n')
 patches.append(f"FUNC {new['KR_RouteAppendLinear']}\n"+lr('route')+lr('x')+lr('y')+'\tNEW CASPos 20851\n\tCALLHLL Array PushBack 2\n\tRETURN\nENDFUNC KR_RouteAppendLinear\n')
 fid=new['KR_DrawRouteLinear'];cmd('ain','dump','--function','KR_DrawRouteLinear','-o',O/'declared_route.jam',decl)
 patches.append(native_lower(clean((O/'declared_route.jam').read_text(encoding='utf8'),'KR_DrawRouteLinear')))
 (O/'route_linear_patch.jam').write_text('\n'.join(patches),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'route_linear_patch.jam','-o',out,decl)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  a=dict(a);z=dict(z);aa=a.pop('address');zz=z.pop('address');assert a==z
  if aa!=zz:changed.append(a['index'])
 assert changed==IDS
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 after=unpack(out.read_bytes());assert old[16:16+size]==after[16:16+size];assert old[old.index(b'MSG1'):]==after[after.index(b'MSG1'):]
 # Dump exact candidate consumers and preserved route hooks for compiled fixtures.
 extra=[31838,31839,31846,31850,31856,28638,28669,28673,28677,28754,27039,27041,27082]
 for fid in sorted(set(IDS+extra+list(new.values()))):
  name=names.get(fid,nm['functions'][fid]['name']);cmd('ain','dump','--function',name,'-o',O/f'built_{fid}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);native=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert native['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',native)
 ev=dict(status='ROUTE_LINEAR_STAGED',source_pointer=p,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},patched_function_ids=IDS,added_functions=new,
 unchanged_files={n:sha(rt/n) for n in ['NightRemasterPact.afa','NightRemasterEX.ex','NightRemaster.exe','NightRemasterFont.fnl']},serialized_metadata_exact=True,old_CODE_MSG1_STR0_exact=True,
 route_algorithm='One900cell scalar grid pass and one bounded four-direction BFS; row-major equal-distance goal selection; start excluded; native passability; department event priority unchanged',
 invalidations='Retain every map/rebuild/load/option hook; skip topology setter invalidation only when value unchanged',native_gameplay_verified=False,native_performance_measured=False)
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,indent=2))
if __name__=='__main__':main()
