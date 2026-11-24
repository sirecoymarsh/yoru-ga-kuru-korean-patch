from pathlib import Path
import json,struct,collections,copy
from audit_dynamic_ui_20260915 import ex,R
from cheat_support_20260915 import sha,savej
import verify_cheat_menu_20260915 as v
from verify_route_perf_20260915 import Meter as BaseMeter

O=Path('route_department_20260915');BASE=Path('route_map_refresh_20260915')
class OwnedCell(dict):pass
class Meter(BaseMeter):
 def __init__(self,fresh):super().__init__(fresh);self.owned={}
 def method(self,mid,obj,a):
  z=super().method(mid,obj,a)
  if mid==27082:z=OwnedCell(z);self.owned[id(z)]=z
  return z
 def delete(self,z):
  if isinstance(z,OwnedCell):assert self.owned.pop(id(z),None) is z,'Double release'
class Map(dict):
 def __init__(self,mid):super().__init__();self.map_id=mid;self.removed=set()
def native_map(g,o,mid):
 cells=Map(mid)
 for i,(gr,ob) in enumerate(zip(g,o)):
  obj,sub=0,0
  if gr==0:obj=-1
  elif 8<=gr<16:obj,sub=1,gr-8
  elif 24<=gr<27:obj,sub=2,gr-24
  elif 32<=gr<40:obj,sub=1,gr-24
  if gr!=0:
   if ob in [40,41]:obj,sub=3,ob-40
   elif ob in [48,49]:obj,sub=4,ob-48
   elif ob in [56,57]:obj,sub=5,ob-56
   elif 64<=ob<72:obj,sub=6,ob-64
   elif 72<=ob<80:obj,sub=7,ob-72
   elif ob==80:obj,sub=8,0
  cells[i%30,i//30]=(obj,sub)
 return cells
def main():
 ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime']);assert sha(rt/'NightRemasterEX.ex')==ev['source_ex_sha256']
 t=ex.decode_ex(rt/'NightRemasterEX.ex').blocks[2].payload;maps={};rows=[]
 for mid in [201,202,203,204]:
  m=next(t for t in t.children if t.name.value==f'{mid:04d}'.encode())
  a={c.name.value.decode('cp932'):[struct.unpack('<i',i.value.payload.raw)[0] for i in c.leaf_value.payload.items] for c in m.children}
  cells=native_map(a['地面データ'],a['置物データ'],mid);maps[mid]=cells
  start=next(p for p,c in cells.items() if c==(2,2));rr=[]
  for source in [BASE,O]:
   v.O=source;x=Meter(source==O);x.run('KR_SetRoute',[1]);view={};before=copy.deepcopy(cells)
   x.run('KR_DrawRoute',[cells,view,*start]);path=view['drawn'];assert cells==before and not cells.removed and not x.owned,'Owned cell reference leaked'
   prev=start
   for p in path:assert abs(p[0]-prev[0])+abs(p[1]-prev[1])==1 and cells[p][0] not in [-1,1];prev=p
   n=x.count[30019]
   for _ in range(20):x.run('KR_DrawRoute',[cells,view,*start])
   assert n==x.count[30019] and x.count[27081]==1
   rr.append(dict(length=len(path),goal=path[-1] if path else None,searches=n,path=path))
  if mid in [202,204]:assert rr[0]['length']==0 and rr[1]['length']>0 and cells[tuple(rr[1]['goal'])]==(7,0)
  elif mid==201:assert rr[0]['path']==rr[1]['path']
  else:assert cells[tuple(rr[1]['goal'])]==(7,0)
  rows.append(dict(map_id=mid,entrance=start,before=rr[0],after=rr[1]))
 # The real203 event groups are removed together by native29171. Check all
 # four selector stages, even from a position nearer to a later event group.
 v.O=O;mp=maps[203];start=(14,3);x=Meter(True);x.run('KR_SetRoute',[1]);progress=[]
 for sub in range(4):
  x.run('KR_Poke',[85,-1]);x.run('KR_Poke',[86,-1]);view={};x.run('KR_DrawRoute',[mp,view,*start]);p=view['drawn'];assert p and mp[p[-1]]==(7,sub) and not x.owned
  progress.append(dict(sub=sub,goal=p[-1],length=len(p)))
  mp.removed.update(p for p,c in mp.items() if c==(7,sub))
 x.run('KR_Poke',[85,-1]);x.run('KR_Poke',[86,-1]);x.run('KR_DrawRoute',[mp,view,*start]);assert view['drawn']==[]
 baseline=v.vm_tests();native=json.loads((O/'native_opcode_audit.json').read_text())
 r=dict(status='DEPARTMENT_ROUTE_COMPILED_MAP_FIXTURES_PASS',files=ev['files'],source_ex_sha256=ev['source_ex_sha256'],department_maps=rows,ordered_203_events=progress,VM=baseline,
  native_active_functions=native['active_functions'],native_instruction_sites=native['instruction_sites'],all_active_native_opcodes_supported=native['all_active_opcodes_supported'],
  root_cause='204 native map stair at13,1 is enclosed by wall/fire; actual escape is event7/0.202 has no2/1 stair and advances at7/0.',
  scope='Department202/203/204 only; other scripted dungeons require separately verified target rules',owned_cell_reference_fixture_balanced=True,native_gameplay_verified=False,
  verification_scope='Compiled route helper on actual EX-derived maps using native-load/passability rules and BFS method fixture; native AStar/rendering not executed')
 savej(O/'verification.json',r);print(json.dumps({k:z for k,z in r.items() if k not in ['department_maps']},indent=2));print([(z['map_id'],z['before']['length'],z['after']['length'],z['after']['goal']) for z in rows])
if __name__=='__main__':main()
