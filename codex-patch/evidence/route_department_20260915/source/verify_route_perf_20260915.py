from pathlib import Path
import json,collections
import verify_cheat_menu_20260915 as v

O=Path('route_perf_20260915')
class Meter(v.VM):
 def __init__(self,fresh=False):super().__init__();self.count=collections.Counter();self.fresh=fresh
 def method(self,mid,obj,args):
  self.count[mid]+=1
  if mid==30019 and self.fresh:
   assert not obj.get('already_used',False),'Reused AStar mutable search state';obj['already_used']=True
   assert not args[5],'Native TraceRoute output must be cleared before each candidate'
  return super().method(mid,obj,args)

def run(path,fresh):
 v.O=Path(path);x=Meter(fresh);x.run('KR_SetRoute',[1]);mp={(i,1):(0,0) for i in range(1,8)};mp[7,1]=(2,1);view={}
 for _ in range(20):x.run('KR_DrawRoute',[mp,view,1,1])
 result=dict(cost_map_builds=x.count[27081],searches=x.count[30019],route_draws=x.count[28677],VM_calls=x.calls)
 return x,mp,view,result

def main():
 old,mp,ov,before=run('cheat_opcode64_fix_20260915',False);new,mp,nv,after=run(O,True)
 assert before['cost_map_builds']==20 and before['searches']==40 and before['route_draws']==20
 assert after['cost_map_builds']==after['searches']==after['route_draws']==1
 assert set(ov['drawn'])==set(nv['drawn']) and nv['drawn'][0]==(2,1) and nv['drawn'][-1]==(7,1)
 # A move re-plans exactly once; facing-only/same-tile update is cached.
 new.run('KR_DrawRoute',[mp,nv,2,1]);new.run('KR_DrawRoute',[mp,nv,2,1]);assert new.count[30019]==2
 # A same-coordinate new map/rebuild is not allowed to hit the previous cache.
 new.run('KR_Poke',[85,-1]);new.run('KR_Poke',[86,-1]);new.run('KR_DrawRoute',[mp,nv,2,1]);assert new.count[30019]==3
 # Switching OFF clears an old path even when the coordinates did not change.
 new.run('KR_SetRoute',[0]);new.run('KR_DrawRoute',[mp,nv,2,1]);assert nv['drawn']==[]
 new.run('KR_SetRoute',[1]);new.run('KR_DrawRoute',[mp,nv,2,1]);assert new.count[30019]==4
 # An exitless floor is cached as a miss, not scanned on every update.
 new.run('KR_Poke',[85,-1]);new.run('KR_Poke',[86,-1]);mp[7,1]=(0,0);n=new.count[27081]
 for _ in range(20):new.run('KR_DrawRoute',[mp,nv,2,1])
 assert new.count[27081]==n+1 and nv['drawn']==[]
 # Real load-reset helper invalidates both cache coordinates.
 new.run('KR_ResetTransient');assert new.flags[85]==new.flags[86]==-1
 # Enumeration sees the farther exit first; a later, shorter route must win.
 far=Meter(True);far.run('KR_SetRoute',[1]);two={(i,1):(0,0) for i in range(1,9)}
 two[1,1]=two[8,1]=(2,1);fv={};far.run('KR_DrawRoute',[two,fv,6,1])
 assert far.count[30019]==2 and fv['drawn']==[(7,1),(8,1)]
 v.O=O;baseline=v.vm_tests()
 e=json.loads((O/'build_evidence.json').read_text());native=json.loads((O/'native_opcode_audit.json').read_text())
 r=dict(status='ROUTE_CACHE_COMPILED_BEHAVIOR_PASS',files=e['files'],VM=baseline,identical_position_20_updates=dict(before=before,after=after),movement_floor_toggle_load_and_no_route_cases_pass=True,
       nearest_route_and_original_draw_style_preserved=True,farther_exit_enumerated_first_regression=True,fresh_search_and_empty_output_per_candidate=True,all_active_native_opcodes_supported=native['all_active_opcodes_supported'],native_active_functions=native['active_functions'],native_instruction_sites=native['instruction_sites'],native_performance_measured=False)
 v.savej(O/'verification.json',r);print(json.dumps(r,indent=2))
if __name__=='__main__':main()
