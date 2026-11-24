"""Append state-aware guidance for MysteryRift401/403/405 only."""
from pathlib import Path
import json,struct,shutil
from cheat_support_20260915 import R,cmd,read_meta,sha,savej
from build_route_perf_20260915 import symbol
from build_route_linear_20260916 import lr,push,cm,assign
from build_instant_loot_20260915 import clean
from repair_ui_runtime_weapon_text_20260913 import unpack,pack
from audit_sys43_native_opcodes_20260915 import native_lower,audit

S=Path(__file__).resolve().parent;O=R/'staging/route_puzzle_20260916'
EXPECTED='0130135eff6c1b156a76f2fa9505addae18d5b2bdbaedc27ab711a54e368ad39'
IDS=[29176,31860]
def fld(obj,i):return obj+push(i)+'\tX_REF 1\n'
def borrowed(index,e):return '\tPUSHLOCALPAGE\n'+push(index)+e+'\tX_ASSIGN 1\n\tSP_INC\n'
def cf(n):return f'\tCALLFUNC {n}\n'
def state_body():
 fail='puzzle_state_fail';done='puzzle_state_done'
 outer=lr('outer');scene=lr('scene');event=lr('event');inner=lr('inner')
 b=''.join(f'\t.LOCALASSIGN {n} -1\n' for n in ['outer','scene','event','inner'])
 b+=lr('state')+'\tCALLHLL Array Numof 1\n'+push(10)+f'\tNOTE\n\tIFNZ {fail}\n'
 b+=cm(lr('map'),27042)+lr('mode')+f'\tNOTE\n\tIFNZ {fail}\n'
 b+='\t.LOCALASSIGN expected 0\n'
 for mode,prepare in [(401,28951),(403,28985),(405,29012)]:
  b+=lr('mode')+push(mode)+f'\tNOTE\n\tIFNZ state_not_{mode}\n\t.LOCALASSIGN expected {prepare}\nstate_not_{mode}:\n'
 b+=lr('expected')+f'\tIFZ {fail}\n'
 b+='\t.GLOBALREF GetActiveScene\n\tCALLHLL Delegate Numof 0\n'+push(1)+f'\tNOTE\n\tIFNZ {fail}\n'
 # GetActiveScene owns the returned object reference; discard only interface offset.
 dg='\t.GLOBALREF GetActiveScene\n\tDG_CALLBEGIN "DG_Func<ref I_Scene>"\nstate_delegate_loop:\n\tDG_CALL "DG_Func<ref I_Scene>" state_delegate_done\n\tJUMP state_delegate_loop\nstate_delegate_done:\n\tPOP\n'
 b+=assign(4,dg)
 def notnull(o):return o+push(-1)+f'\tEQUALE\n\tIFNZ {fail}\n'
 def vtable(o,n,fnexpr):
  a=fld(o,0)
  return notnull(o)+notnull(a)+a+'\tCALLHLL Array Numof 1\n'+push(n)+f'\tLT\n\tIFNZ {fail}\n'+fld(a,0)+fnexpr+f'\tNOTE\n\tIFNZ {fail}\n'
 b+=vtable(outer,3,push(28170))
 b+=borrowed(5,outer+push(3)+'\tX_REF 2\n\tPOP\n')+vtable(scene,4,push(28634))
 b+=fld(scene,6)+lr('map')+f'\tNOTE\n\tIFNZ {fail}\n'
 dv=fld(scene,2);b+=notnull(dv)+fld(dv,3)+lr('view')+f'\tNOTE\n\tIFNZ {fail}\n'
 b+=borrowed(6,scene+push(4)+'\tX_REF 2\n\tPOP\n')+vtable(event,10,lr('expected'))
 b+=fld(event,1)+lr('map')+f'\tNOTE\n\tIFNZ {fail}\n'
 b+=borrowed(7,fld(event,2))+notnull(inner)
 b+=fld(inner,0)+lr('map')+f'\tNOTE\n\tIFNZ {fail}\n'+fld(inner,1)+dv+f'\tNOTE\n\tIFNZ {fail}\n'
 b+=lr('mode')+push(401)+'\tNOTE\n\tIFNZ state_not_counts\n'
 counts=fld(inner,2);b+=notnull(counts)+counts+'\tCALLHLL Array Numof 1\n'+push(4)+f'\tLT\n\tIFNZ {fail}\n'
 for i in range(4):
  # Corrupt or unexpected counters fail closed instead of selecting a false goal.
  b+=fld(counts,i)+push(0)+f'\tLT\n\tIFNZ {fail}\n'+fld(counts,i)+push(1000000)+f'\tGT\n\tIFNZ {fail}\n'
  b+=lr('state')+push(i)+fld(counts,i)+'\tX_ASSIGN 1\n\tPOP\n'
 b+=f'\tJUMP {done}\nstate_not_counts:\n'+lr('mode')+push(403)+'\tNOTE\n\tIFNZ state_not_answers\n'
 answers=fld(event,4);b+=notnull(answers)+answers+'\tCALLHLL Array Numof 1\n'+push(6)+f'\tLT\n\tIFNZ {fail}\n'
 for i in range(6):b+=lr('state')+push(i)+fld(answers,i)+'\tX_ASSIGN 1\n\tPOP\n'
 b+=f'\tJUMP {done}\nstate_not_answers:\n'+lr('state')+push(0)+fld(event,3)+'\tX_ASSIGN 1\n\tPOP\n'
 release=''.join(f'\t.LOCALDELETE {n}\n' for n in ['inner','event','scene','outer'])
 b+=done+':\n'+release+push(1)+'\tRETURN\n'+fail+':\n'+release+push(0)+'\tRETURN\n'
 return b

def cell_body():
 b=assign(3,cm(lr('map'),27082,lr('x')+lr('y'),2))+lr('cell')+push(-1)+'\tEQUALE\n\tIFNZ puzzle_cell_null\n'
 b+=assign(5,cm(lr('cell'),27005))+assign(6,cm(lr('cell'),27008))
 for n,lo,hi in [('obj',-1,8),('sub',0,7)]:
  b+=lr(n)+push(lo)+'\tLT\n\tIFNZ puzzle_cell_bad\n'+lr(n)+push(hi)+'\tGT\n\tIFNZ puzzle_cell_bad\n'
 b+=assign(4,cm(lr('cell'),27039)+cm(lr('cell'),27023)+push(2)+'\tMUL\n\tADD\n'+lr('obj')+push(1)+'\tADD\n'+push(32)+'\tMUL\n\tADD\n'+lr('sub')+push(4)+'\tMUL\n\tADD\n')
 b+='\t.LOCALDELETE cell\n'+lr('code')+'\tRETURN\npuzzle_cell_bad:\n\t.LOCALDELETE cell\npuzzle_cell_null:\n'+push(0)+'\tRETURN\n';return b

def refresh_body():
 mp=fld(lr('inner'),0);dv=fld(lr('inner'),1);vw=fld(dv,3)
 b=cf('KR_GetRoute')+'\tIFZ puzzle_refresh_end\n'
 for obj in [lr('inner'),mp,dv,vw]:b+=obj+push(-1)+'\tEQUALE\n\tIFNZ puzzle_refresh_end\n'
 for mid in [401,403,405]:b+=cm(mp,27042)+push(mid)+'\tEQUALE\n\tIFNZ puzzle_refresh_scope\n'
 b+='\tRETURN\npuzzle_refresh_scope:\n'+push(85)+push(-1)+cf('KR_Poke')+push(86)+push(-1)+cf('KR_Poke')
 b+=mp+vw+cm('\t.GLOBALREF Flags\n',26559)+cm('\t.GLOBALREF Flags\n',26562)+cf('KR_DrawRoute')+'puzzle_refresh_end:\n\tRETURN\n';return b

def main():
 O.mkdir(parents=True,exist_ok=True);p=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime']);src=rt/'NightRemaster.ain';assert sha(src)==EXPECTED
 cmd('ain','dump','-j','-o',O/'source_meta.json',src);m=read_meta(O/'source_meta.json');names={};seen={}
 for f in m['functions']:
  n=symbol(m,f['index']);count=seen.get(n,0);seen[n]=count+1;names[f['index']]=n+(f'#{count}' if count else '')
 jaf=S/'route_puzzle_helpers_20260916.jaf';shutil.copy2(jaf,O/jaf.name);decl=O/'declared.ain';cmd('ain','edit','--jaf',jaf,'-o',decl,src)
 old=unpack(src.read_bytes());raw=bytearray(unpack(decl.read_bytes()));size=struct.unpack_from('<I',old,12)[0];ns=struct.unpack_from('<I',raw,12)[0];assert raw[16:16+size]==old[16:16+size];struct.pack_into('<I',raw,24+ns,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');new={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};assert set(new)=={'KR_PuzzleReadState','KR_PuzzleCell','KR_PuzzleRefresh','KR_DrawPuzzleRoute'}
 patches=[]
 for fid in IDS:
  out=O/f'original_{fid}.jam';cmd('ain','dump','--function',names[fid],'-o',out,src);s=clean(out.read_text(encoding='utf8'),names[fid])
  if fid==31860:
   pos=s.rfind('\t.LOCALREF map\n\t.LOCALREF view\n\t.LOCALREF x\n\t.LOCALREF y\n');assert pos>0
   branch=''
   for mid in [401,403,405]:branch+=cm(lr('map'),27042)+push(mid)+'\tEQUALE\n\tIFNZ puzzle_route_dispatch\n'
   # OFF must still call the existing clear-path consumer, not the puzzle solver.
   branch=cf('KR_GetRoute')+'\tIFZ puzzle_route_regular\n'+branch+'\tJUMP puzzle_route_regular\npuzzle_route_dispatch:\n'+''.join(lr(n) for n in ['map','view','x','y'])+cm(lr('map'),27042)+cf('KR_DrawPuzzleRoute')+'\tRETURN\npuzzle_route_regular:\n'
   s=s[:pos]+branch+s[pos:]
  else:
   pos=s.rfind('\tRETURN');s=s[:pos]+'\tPUSHSTRUCTPAGE\n'+cf('KR_PuzzleRefresh')+s[pos:]
  patches.append(s)
 for name,body in [('KR_PuzzleReadState',state_body()),('KR_PuzzleCell',cell_body()),('KR_PuzzleRefresh',refresh_body())]:patches.append(f'FUNC {new[name]}\n'+body+f'ENDFUNC {name}\n')
 cmd('ain','dump','--function','KR_DrawPuzzleRoute','-o',O/'declared_route.jam',decl);patches.append(native_lower(clean((O/'declared_route.jam').read_text(encoding='utf8'),'KR_DrawPuzzleRoute')))
 (O/'route_puzzle_patch.jam').write_text('\n'.join(patches),encoding='utf8');candidate=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'route_puzzle_patch.jam','-o',candidate,decl)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',candidate);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  a=dict(a);z=dict(z);aa=a.pop('address');zz=z.pop('address');assert a==z
  if aa!=zz:changed.append(a['index'])
 assert changed==IDS
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 after=unpack(candidate.read_bytes());assert old[16:16+size]==after[16:16+size] and old[old.index(b'MSG1'):]==after[after.index(b'MSG1'):]
 # Exact consumers for fixtures; keep the already-verified ordinary helpers.
 for f in (R/'staging/route_linear_20260916').glob('built_*.jam'):shutil.copy2(f,O/f.name)
 for fid in IDS+list(new.values()):cmd('ain','dump','--function',names.get(fid,nm['functions'][fid]['name']),'-o',O/f'built_{fid}.jam',candidate)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',candidate);native=audit(candidate,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert native['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',native)
 ev=dict(status='PUZZLE_ROUTE_STAGED',source_pointer=p,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(candidate)},patched_function_ids=IDS,added_functions=new,
 unchanged_files={n:sha(rt/n) for n in ['NightRemasterPact.afa','NightRemasterEX.ex','NightRemaster.exe','NightRemasterFont.fnl']},serialized_metadata_exact=True,old_CODE_MSG1_STR0_exact=True,scope=[401,403,405],ordinary_maps_402_404_unchanged=True,
 native_state_read_only=True,forced_events_or_puzzle_completion=False,per_frame_full_scan=False,native_gameplay_verified=False,native_performance_measured=False)
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,indent=2))
if __name__=='__main__':main()
