from pathlib import Path
import json,re
import verify_cheat_menu_20260915 as v
from verify_route_perf_20260915 import Meter
from cheat_support_20260915 import savej

O=Path('route_map_refresh_20260915')
class Lifecycle(Meter):
 def __init__(self):super().__init__(True);self.xy=(1,1);self.structrefs={}
 def method(self,mid,obj,args):
  if mid in [26559,26562]:return self.xy[mid==26562]
  return super().method(mid,obj,args)
def main():
 v.O=O;cases=[]
 for fid,fn,cls in [(28638,'C_SceneDungeon@ToNextFloor','C_SceneDungeon'),(28754,'C_SceneDungeonView@UpdateAll','C_SceneDungeonView')]:
  s=(O/f'built_{fid}.jam').read_text(encoding='utf8')
  i=s.index('\tCALLFUNC KR_GetRoute');assert 'CALLFUNC KR_DrawRoute' in s[i:]
  if fid==28638:assert s.index('\tPUSH 28639')<i and '\tCALLMETHOD 2\n\tCALLFUNC KR_GetRoute' in s
  else:assert s.index('\tPUSH 28671')<i and '\tCALLMETHOD 0\n\tCALLFUNC KR_GetRoute' in s
  for on in [False,True]:
   for present in [False,True]:
    for exit_exists in [False,True]:
     x=Lifecycle();x.run('KR_SetRoute',[int(on)]);mp={(i,1):(0,0) for i in range(1,8)}
     if exit_exists:mp[7,1]=(2,1)
     view={'drawn':[(29,29)]};x.flags[85]=1;x.flags[86]=1;x.flags[89]=1
     x.structrefs={cls+' m_MapInfo':mp if present else -1,cls+' m_DungeonView':{3:view},cls+' m_MiniMapView':view}
     assert x.run(fn,region_fixture=True)==999
     if not on or not present:assert view['drawn']==[(29,29)] and x.count[27081]==0
     else:
      assert x.count[27081]==1 and view['drawn']==([(i,1) for i in range(2,8)] if exit_exists else [])
      for _ in range(20):x.run('KR_DrawRoute',[mp,view,1,1])
      assert x.count[27081]==1,'Lifecycle fix reintroduced duplicate work'
     cases.append(dict(function=fid,enabled=on,map_present=present,exit_exists=exit_exists))
 # Simulate entry events changing arrival position before the compiled post-transition hook.
 x=Lifecycle();x.run('KR_SetRoute',[1]);x.xy=(5,1);mp={(i,1):(0,0) for i in range(1,8)};mp[7,1]=(2,1);view={}
 x.structrefs={'C_SceneDungeon m_MapInfo':mp,'C_SceneDungeon m_DungeonView':{3:view}}
 x.run('C_SceneDungeon@ToNextFloor',region_fixture=True);assert view['drawn']==[(6,1),(7,1)]
 baseline=v.vm_tests();ev=json.loads((O/'build_evidence.json').read_text());native=json.loads((O/'native_opcode_audit.json').read_text())
 r=dict(status='ROUTE_MAP_REFRESH_COMPILED_PASS',files=ev['files'],compiled_inserted_regions_tested=cases,current_post_event_coordinates=True,same_tile_cache_preserved=True,
  VM=baseline,native_active_functions=native['active_functions'],native_instruction_sites=native['instruction_sites'],all_active_native_opcodes_supported=native['all_active_opcodes_supported'],
  native_gameplay_verified=False,root_cause_status=ev['root_cause_status'],verification_scope='Actual compiled inserted regions and unchanged route helper with native-method fixtures; native map transition NOT executed')
 savej(O/'verification.json',r);print(json.dumps({k:z for k,z in r.items() if k!='compiled_inserted_regions_tested'},indent=2))
if __name__=='__main__':main()
