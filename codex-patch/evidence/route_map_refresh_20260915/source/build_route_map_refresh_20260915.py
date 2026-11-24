"""Close next-floor post-event and minimap-rebuild refresh gaps, without per-frame search."""
from pathlib import Path
import json,struct,re,shutil
from cheat_support_20260915 import cmd,read_meta,R,sha,savej
from repair_ui_runtime_weapon_text_20260913 import unpack
from audit_sys43_native_opcodes_20260915 import audit
from build_route_perf_20260915 import symbol,RESET

O=Path('route_map_refresh_20260915');BASE=Path('route_perf_20260915')
IDS=[28638,28754]
def refresh(i):
 label=f'kr_refresh_done_{i}'
 if i==28638:
  mapref='\t.STRUCTREF C_SceneDungeon m_MapInfo\n'
  view='\t.STRUCTREF C_SceneDungeon m_DungeonView\n\tPUSH 3\n\tX_REF 1\n'
 else:
  mapref='\t.STRUCTREF C_SceneDungeonView m_MapInfo\n'
  view='\t.STRUCTREF C_SceneDungeonView m_MiniMapView\n'
 return ('\tCALLFUNC KR_GetRoute\n\tIFZ '+label+'\n'+mapref+'\tPUSH -1\n\tEQUALE\n\tIFNZ '+label+'\n'+
   RESET+mapref+view+'\t.GLOBALREF Flags\n\tPUSH 26559\n\tCALLMETHOD 0\n\t.GLOBALREF Flags\n\tPUSH 26562\n\tCALLMETHOD 0\n\tCALLFUNC KR_DrawRoute\n'+label+':\n')
def main():
 O.mkdir(exist_ok=True);p=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)=='39c55a8c8c5fadb77a235116a80c10798482313e72bfda50df5ea07d3766bf0e'
 m=read_meta(BASE/'candidate_meta.json');patch=[]
 assert next(s for s in m['structures'] if s['name']=='C_SceneDungeonView')['members'][3]['name']=='m_MiniMapView'
 for i in IDS:
  f=O/f'original_{i}.jam';cmd('ain','dump','--function',symbol(m,i),'-o',f,src);s=f.read_text(encoding='utf8')
  if 'ENDFUNC ' not in s:s=re.sub(r'^EOF .*\n?','',s,flags=re.M)+f'\nENDFUNC {symbol(m,i)}\n'
  if i==28638:
   needle='\tPUSH 28639\n\t.LOCALREF nextId\n\tPUSH 0\n\tCALLMETHOD 2\n';assert s.count(needle)==1
   s=s.replace(needle,needle+refresh(i))
  else:
   assert s.count('\tRETURN')==1;s=s.replace('\tRETURN',refresh(i)+'\tRETURN')
  patch.append(s)
 (O/'route_map_refresh_patch.jam').write_text('\n'.join(patch),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'route_map_refresh_patch.jam','-o',out,src)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,b in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y
  if aa!=bb:changed.append(a['index'])
 assert changed==IDS and len(m['functions'])==len(nm['functions'])
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 a=unpack(src.read_bytes());b=unpack(out.read_bytes());size=struct.unpack_from('<I',a,12)[0]
 assert a[16:16+size]==b[16:16+size] and a[a.index(b'MSG1'):]==b[b.index(b'MSG1'):]
 for f in BASE.glob('built_*.jam'):shutil.copy2(f,O/f.name)
 for i in IDS:cmd('ain','dump','--function',symbol(nm,i),'-o',O/f'built_{i}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 native=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert native['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',native)
 ev=dict(status='ROUTE_MAP_REFRESH_STAGED',source_pointer=p,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},patched_function_ids=IDS,
  changes=['Refresh after next-floor SetMapId returns, after native arrival coordinates and entrance events','Refresh at end of full minimap rebuild; invalidate cached result first only when route enabled'],
  old_CODE_MSG1_STR0_and_other_metadata_exact=True,search_and_goal_rules_unchanged=True,save_schema_and_other_game_files_unchanged=True,native_gameplay_verified=False,
  root_cause_status='Rebuild lifecycle gap demonstrated statically; exact user next-floor symptom not reproduced in native runtime')
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,indent=2))
if __name__=='__main__':main()
