"""Two-body append-only correction against the exact installed smart-auto build."""
from pathlib import Path
import json,shutil,struct
from cheat_support_20260915 import R,sha,savej,read_meta,cmd
from build_instant_loot_20260915 import clean
from build_dungeon_sweep_20260916 import lr,push,cf,cm,assign
from build_route_perf_20260915 import symbol
from repair_ui_runtime_weapon_text_20260913 import unpack,strings
from audit_sys43_native_opcodes_20260915 import audit

O=R/'staging/smart_auto_fix_20260922';BASE=R/'staging/smart_auto_20260922';HERE=Path(__file__).resolve().parent
EXPECTED='f331f7303175e9d7c9fbbcd3e032973717654e223d2ab2f9969638900b08022c'

def main():
 O.mkdir(parents=True,exist_ok=True)
 ptr=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)==EXPECTED and sha(Path(ptr['manifest']))==ptr['manifest_sha256']
 savej(O/'source_pointer.json',ptr);m=read_meta(BASE/'candidate_meta.json')
 # Historical regression fixtures are copied, never rewritten in installed evidence.
 for f in BASE.iterdir():
  if f.is_file() and (f.name.startswith(('built_','original_')) and f.suffix=='.jam' or f.name in ['smart_auto_patch.jam','pact_185_smart_auto.pactex','original_185.pactex']):shutil.copy2(f,O/f.name)
 patches={}
 for fid in [31979,31981]:
  f=O/f'original_{fid}.jam';cmd('ain','dump','--function',symbol(m,fid),'-o',f,src)
  patches[fid]=clean(f.read_text(encoding='utf8'),symbol(m,fid))
 needle=lr('weapon')+push(11)+cf('KR_AutoW')+push(0)+'\tNOTE\n'
 body=lr('weapon')+push(11)+cf('KR_AutoW')+'\tIFNZ type0_done\n'
 body+=cm(lr('pa'),27332)+push(1)+'\tEQUALE\n\tIFNZ type0_done\n'
 body+=assign(6,lr('pa')+push(0)+cf('KR_AutoCombatValue'))+assign(7,lr('pa')+push(1)+cf('KR_AutoCombatValue'))+'type0_done:\n'
 assert patches[31979].count(needle)==1;patches[31979]=patches[31979].replace(needle,body+needle)
 bad='\t.LOCALREF normal\n\tNOT\n\tIFZ 0x996b94\n\t.LOCALREF action\n\tPUSH 1\n\tNOTE\n\tIFZ 0x996b94\n\tPUSH 1\n\tJUMP 0x996b9a\n0x996b94:\n\tPUSH 0\n0x996b9a:\n\tIFNZ 0x996ba6\n\tJUMP 0x996ba8\n0x996ba6:\n\tRETURN\n0x996ba8:\n'
 assert patches[31981].count(bad)==1;patches[31981]=patches[31981].replace(bad,'')
 jam=O/'type0_fix.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8')
 out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,src)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 assert len(m['functions'])==len(nm['functions'])
 for a,b in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y,a['index']
  if aa!=bb:changed.append(a['index'])
 assert changed==[31979,31981],changed
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 old=unpack(src.read_bytes());new=unpack(out.read_bytes());size=struct.unpack_from('<I',old,12)[0]
 assert old[16:16+size]==new[16:16+size]
 assert strings(old)[2]==strings(new)[2]
 assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
 for fid in changed:cmd('ain','dump','--function',symbol(nm,fid),'-o',O/f'built_{fid}.jam',out)
 for fid in [27320,27321,27325,27326,27290,27293,27296,27297,26843,26844,26876,31942]:
  cmd('ain','dump','--function',symbol(nm,fid),'-o',O/f'original_{fid}.jam',src)
 shutil.copy2(HERE/'smart_auto_helpers_20260922.jaf',O/'helpers.jaf')
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 na=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');savej(O/'native_opcode_audit.json',na);assert na['all_active_opcodes_supported']
 ev=dict(status='SMART_AUTO_FIX_STAGED_UNVERIFIED',source_pointer=ptr,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},patched_existing=changed,added_functions={},PACT='unchanged',serialized_metadata_exact=True,old_CODE_STR0_MSG1_exact=True,native_verified=False,translator_model='Codex internal',fix='Allow companion type-0 EX with native current-weapon attack/hit; keep EX action, HP cost, repeat, range, timing and technique effects')
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
