"""Cache identical minimap updates and eliminate duplicate mutable AStar searches."""
from pathlib import Path
import json,struct,re,shutil
from cheat_support_20260915 import cmd,read_meta,R,sha,savej
from repair_ui_runtime_weapon_text_20260913 import unpack
from audit_sys43_native_opcodes_20260915 import audit

O=Path('route_perf_20260915');BASE=Path('cheat_opcode64_fix_20260915')
IDS=[27007,27010,27025,27031,28669,31850,31856,31860]
RESET='\tPUSH 85\n\tPUSH -1\n\tCALLFUNC KR_Poke\n\tPUSH 86\n\tPUSH -1\n\tCALLFUNC KR_Poke\n'
def symbol(m,i):
 n=m['functions'][i]['name'];return n.encode('utf8','surrogateescape').decode('cp932') if any(0xdc80<=ord(c)<=0xdcff for c in n) else n
def main():
 O.mkdir(exist_ok=True);p=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)=='537a684b60828bdf3b19252e3e6b32c3ebffb8812de70b323805b479fea05e2a'
 m=read_meta(BASE/'candidate_meta.json');patch=[];savej(O/'source_pointer.json',p)
 for i in IDS:
  f=O/f'original_{i}.jam';cmd('ain','dump','--function',symbol(m,i),'-o',f,src);s=f.read_text(encoding='utf8')
  if 'ENDFUNC ' not in s:s=re.sub(r'^EOF .*\n?','',s,flags=re.M)+f'\nENDFUNC {symbol(m,i)}\n'
  if i in [27007,27010,27025,27031,28669,31856]:
   s=re.sub(r'(^FUNC \d+\n)',lambda z:z[0]+RESET,s,count=1,flags=re.M)
  elif i==31850:
   body='\t.LOCALREF value\n\tCALLFUNC KR_GetRoute\n\tEQUALE\n\tIFNZ 0x7ef00001\n'+RESET+'0x7ef00001:\n'
   s=re.sub(r'(^FUNC \d+\n)',lambda z:z[0]+body,s,count=1,flags=re.M)
  else:
   guard='\tCALLFUNC KR_GetRoute\n\tIFZ 0x7ef00002\n\tPUSH 89\n\tCALLFUNC KR_Flag\n\tPUSH 1\n\tNOTE\n\tIFNZ 0x7ef00002\n'
   for slot,xy in [(85,'x'),(86,'y')]:guard+=f'\tPUSH {slot}\n\tCALLFUNC KR_Flag\n\t.LOCALREF {xy}\n\tNOTE\n\tIFNZ 0x7ef00002\n'
   guard+='\tRETURN\n0x7ef00002:\n';s=re.sub(r'(^FUNC \d+\n)',lambda z:z[0]+guard,s,count=1,flags=re.M)
   create='\t.LOCALCREATE search NS_AStar::AStarExecuteLoop\n';assert s.count(create)==1;s=s.replace(create,'')
   needle='\tPUSHLOCALPAGE\n\tPUSH 13\n\t.LOCALREF search\n';assert s.count(needle)==1
   # Native TraceRoute appends then reverses; it never clears caller output.
   s=s.replace(needle,'\t.LOCALREF route\n\tPUSH 0\n\tCALLHLL Array Realloc 2\n'+create+needle)
   # Native structured-array copy recipe from parts::detail::CallPartsUpdateEvent9164.
   copy='\t.LOCALREF empty\n\t.LOCALREF n\n\tCALLHLL Array Realloc 2\n\t.LOCALREF empty\n\tPUSH 0\n\t.LOCALREF route\n\tPUSH 0\n\t.LOCALREF n\n\tCALLHLL Array Copy#3 2\n\tPOP\n'
   needle='\tPUSHLOCALPAGE\n\tPUSH 8\n\t.LOCALREF n\n';assert s.count(needle)==1;s=s.replace(needle,copy+needle)
   # Already retain the best route; never re-run Exec on an uncleared search object.
   start=s.index('\t.LOCALREF bestX\n\tPUSH 0\n\tGTE\n');stop=s.index('\tPUSH 88\n\tPUSH 0\n',start)
   s=s[:start]+'\t.LOCALREF view\n\tPUSH 28677\n\t.LOCALREF empty\n\tCALLMETHOD 1\n'+s[stop:]
   pos=s.rfind('\tRETURN');s=s[:pos]+'\tPUSH 85\n\t.LOCALREF x\n\tCALLFUNC KR_Poke\n\tPUSH 86\n\t.LOCALREF y\n\tCALLFUNC KR_Poke\n'+s[pos:]
  patch.append(s)
 (O/'route_perf_patch.jam').write_text('\n'.join(patch),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'route_perf_patch.jam','-o',out,src)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,b in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y
  if aa!=bb:changed.append(a['index'])
 assert changed==IDS and len(m['functions'])==len(nm['functions'])
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 a=unpack(src.read_bytes());b=unpack(out.read_bytes());size=struct.unpack_from('<I',a,12)[0];assert a[16:16+size]==b[16:16+size] and a[a.index(b'MSG1'):]==b[b.index(b'MSG1'):]
 for f in BASE.glob('built_*.jam'):shutil.copy2(f,O/f.name)
 for i in IDS:cmd('ain','dump','--function',symbol(nm,i),'-o',O/f'built_{i}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 native=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert native['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',native)
 ev=dict(status='ROUTE_PERFORMANCE_STAGED',source_pointer=p,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},patched_function_ids=IDS,
  changes=['cache route and no-route at same x/y','invalidate on map binding/rebuild, topology setters, settings change and load','fresh search per exit candidate','copy best path once, remove final repeated search'],
  reused_unused_int_slots=[85,86],serialized_schemas_and_all_other_metadata_exact=True,all_existing_CODE_prefix_MSG1_STR0_exact=True,UI_and_gameplay_inputs_unchanged=True,native_performance_measured=False)
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,indent=2))
if __name__=='__main__':main()
