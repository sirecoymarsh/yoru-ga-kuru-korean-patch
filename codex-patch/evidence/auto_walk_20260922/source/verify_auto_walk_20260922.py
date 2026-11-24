"""Execute actual candidate JAM; OS input and drawing are explicit fixture boundaries."""
from pathlib import Path
import ast,copy,json,re,random,struct
import verify_route_puzzle_20260916 as P
from cheat_support_20260915 import R,read_meta,cmd,sha,savej
from build_route_perf_20260915 import symbol
from build_remaster_multiplier_20260915 import ex
O=R/'staging/auto_walk_20260922';M=read_meta(O/'candidate_meta.json');MARK=2026092203
s=P.s
s=s.replace("elif op=='NOT':", "elif op=='INV':st.append(i32(-st.pop()))\n   elif op=='NOT':")
s=s.replace("elif op=='PUSHLOCALPAGE':st.append(loc)","elif op=='S_PUSH':st.append(ast.literal_eval(a))\n   elif op=='PUSHLOCALPAGE':st.append(loc)")
s=s.replace("if a=='Delegate Numof 0':", "if a=='Array Empty 2':st.append(int(not st.pop()))\n    elif a=='Array Free 2':st.pop().clear()\n    elif a=='Delegate Numof 0':")
s=s.replace('st.append(n)','st.append(n-1 if getattr(self,"copy_failure",False) else n)')
env=dict(P.ns);env.update(O=O,read_meta=lambda p:M,ast=ast)
exec(compile(s,'<candidate auto-walk JAM>','exec'),env)
P.L.ns['VM'].run=env['VM'].run
P.L.ns.update(O=O,read_meta=lambda p:M)

class VM(P.VM):
 def __init__(self,mp=None,pos=(1,1)):
  super().__init__();self.pos=pos;self.labels={};self.notices=[];self.plans=0;self.annihilated=False;self.this=None
  mp=mp or P.L.Map(data={(x,1):(0,0) for x in range(1,8)}|{(8,1):(2,1)})
  if mp.map_id in [401,403,405]:self.bind(mp,P.Node())
  else:self.mp=mp;self.view=P.Node();self.dv=P.Node({3:self.view});self.scene=P.Node({2:self.dv,6:mp})
  self.scene[7]=[];self.scene_id=mp.map_id
 def retain(self,z):
  if z==-1:return
  assert isinstance(z,(P.Node,P.L.Map));self.refs[id(z)]+=1
 def delete(self,z):
  if isinstance(z,P.L.Map):self.refs[id(z)]-=1;assert self.refs[id(z)]>=0
  elif isinstance(z,list):z.clear()
  else:super().delete(z)
 def run(self,n,args=(),**kw):
  if n=='L_Party::IsAnnihilated':return int(self.annihilated)
  if n in ['KR_WalkVisible','KR_WalkShowStart','KR_WalkShowStop']:self.labels[n]=bool(args[1]);return
  if n=='KR_NoticeShow':self.notices.append(args[0]);return
  if n=='KR_WalkPlan':self.plans+=1
  return super().run(n,args,**kw)
 def method(self,mid,obj,args):
  if mid==28622:return self.scene_id
  if mid==28647:self.count[mid]+=1;return int(P.L.walk(obj[6],tuple(args)))
  if mid in [28659,28658]:
   old=self.this;oldrefs=getattr(self,'structrefs',{});self.this=obj
   self.structrefs={'C_SceneDungeon m_AutoMoveList':obj[7],'C_SceneDungeon m_DungeonView':obj[2]}
   try:return self.run(symbol(M,mid),args)
   finally:self.this=old;self.structrefs=oldrefs
  if mid==28768:obj[3]['drawn']=copy.deepcopy(args[0]);return
  if mid==28769:obj['no-route-warning']=bool(args[0]);return
  return super().method(mid,obj,args)
 def start(self):return self.run('KR_WalkStart',[self.scene])
 def guard(self):return self.run('KR_WalkGuard',[self.scene])
 def stop(self):return self.run('KR_WalkStop',[self.scene])
 def valid(self,route):return self.run('KR_WalkPathValid',[self.scene,route])
 def check_refs(self):assert not self.owned and not any(self.refs.values()),(self.owned,self.refs)

def prepare():
 names=['KR_Flag','KR_Poke','KR_InitOptions','KR_GetRoute','KR_SweepActive','KR_RouteAppendLinear','KR_RouteCellLinear','KR_PuzzleReadState','KR_PuzzleCell']
 names +=[symbol(M,i) for i in [28658,28639,28677]+list(range(31639,31652))]
 for n in names:cmd('ain','dump','--function',n,'-o',O/f"built_{next(f['index'] for f in M['functions'] if f['name']==n)}.jam",O/'NightRemaster.ain')

def canonical(s):
 lines=[x.strip() for x in s.splitlines() if x.strip() and not x.lstrip().startswith((';','EOF','ENDFUNC'))]
 labels={x[:-1]:f'L{i}' for i,x in enumerate(lines) if x.endswith(':')}
 return [re.sub(r'0x[0-9a-f]+',lambda m:labels.get(m[0],m[0]),x) for x in lines]

def main():
 r={};ev=json.loads((O/'build_evidence.json').read_text());assert all(sha(O/n)==h for n,h in ev['files'].items())
 v=VM();before=copy.deepcopy(v.mp);assert v.start();assert v.scene[7]==[(x,1) for x in range(2,9)]
 assert v.flags[71]==MARK and not v.flags[93] and v.pos==(1,1) and v.mp==before and v.saved==[]
 assert v.labels['KR_WalkShowStart']==False and v.labels['KR_WalkShowStop']==True;v.check_refs()
 r['real_planner_commit_detached_queue_route_option_off_no_save_no_teleport']=True
 vfail=VM();vfail.copy_failure=True;assert not vfail.start() and not vfail.scene[7] and vfail.flags[71]==0;vfail.check_refs()
 r['short_array_copy_fail_closed']=True
 # No whole-map reads or re-planning during idle/valid-head frames.
 scans=v.count[27082];plans=v.plans
 for _ in range(1000):v.guard()
 assert v.count[27082]==scans==900 and v.plans==plans==1
 v.stop();v.stop();assert not v.scene[7] and v.flags[71]==0 and v.labels['KR_WalkShowStart']
 v.scene[7][:]=[(4,4)];before=copy.deepcopy(v.scene[7]);v.flags[71]=0
 for _ in range(1000):v.guard()
 v.stop();assert v.scene[7]==before and v.plans==1
 r['thousand_active_and_inactive_ticks_no_BFS_and_unowned_queue_preserved']=True
 # Native Clear must clear ownership even for an empty queue, including the final-step path.
 v.flags[71]=MARK;v.scene[7].clear();v.method(28659,v.scene,[]);assert v.flags[71]==0
 v=VM();v.start();v.scene[7][:]=[(2,1)];v.method(28658,v.scene,[]);assert v.flags[71]==0 and v.scene[7]==[]
 v=VM();v.start();v.run('KR_WalkPause');assert v.flags[71]==-MARK;v.guard();assert v.flags[71]==0 and not v.scene[7]
 v=VM();v.start();v.run('KR_ResetTransient');assert v.flags[71]==0
 r['native_clear_empty_final_step_pause_and_load_reset']=True
 for field,bad in [(6,-1),(2,-1)]:
  v=VM();v.scene[field]=bad;assert not v.start() and not v.scene[7]
 for field,bad in [('scene_id',202),('annihilated',True),('pos',(-1,0)),('pos',(30,2))]:
  v=VM();setattr(v,field,bad);assert not v.start() and not v.scene[7]
 for route in [[],[(3,1)],[(1,1)],[(2,1),None],[(-1,1)],[(30,1)],[(2,1)]*901]:
  v=VM();rr=[-1 if x is None else x for x in route];assert not v.valid(rr)
 for route in [[],[(3,1)],[(30,1)],[-1],[(2,1)]*901]:
  v=VM();v.start();v.scene[7][:]=route;v.guard();assert v.flags[71]==0 and not v.scene[7]
 r['invalid_context_coordinates_nonadjacent_corrupt_and_oversized_queue_fail_closed']=True
 v=VM();v.start();v.mp[2,1]=(1,0);v.mp.update({(x,2):(0,0) for x in range(1,4)});v.guard()
 assert v.plans==2 and v.flags[71]==MARK and v.scene[7][0]==(1,2);v.check_refs()
 v=VM();v.start();v.mp[2,1]=(1,0);v.guard();assert v.plans==2 and not v.scene[7] and v.flags[71]==0
 for _ in range(100):v.guard()
 assert v.plans==2;r['blocked_next_step_one_replan_then_stop_if_no_path']=True
 for obj in range(9):
  v=VM();v.start();v.run('KR_WalkCellGate',[v.scene,dict(object=obj)]);assert (v.flags[71]==0)==(obj>=2)
 r['native_interaction_gate_stops_remaining_route']=True
 # Independent graph-distance oracle against exact candidate planning/commit.
 cases=[];rng=random.Random(20260922)
 for i in range(60):
  mid=[1001,202,203,204][i%4];mp=P.L.Map(mid)
  for y in range(12):
   for x in range(12):mp[x,y]=(1,0) if rng.random()<.2 else (0,0)
  for _ in range(5):mp[rng.randrange(12),rng.randrange(12)]=(7,rng.randrange(5)) if mid<1000 else (2,1)
  pos=(rng.randrange(12),rng.randrange(12));v=VM(mp,pos);before=copy.deepcopy(mp);d,goal=P.L.expected(mp,pos);ok=v.start();path=list(v.scene[7])
  assert ok==bool(d) and len(path)==d and (path[-1] if path else None)==goal,(i,d,goal,path)
  assert v.mp==before and v.pos==pos;v.check_refs();cases.append(dict(mode=mid,start=pos,length=d,goal=goal))
 r['independent_ordinary_distance_oracle_cases']=cases
 # Shipped puzzle map data; compare existing guide and new planner for current state only.
 rt=Path(ev['source_pointer']['runtime']);root=ex.decode_ex(rt/'NightRemasterEX.ex').blocks[2].payload;puzzles=[]
 for mid,positions in [(401,[(15,2),(5,5),(19,27)]),(403,[(3,3),(18,11)]),(405,[(22,12),(6,13)])]:
  part=next(t for t in root.children if t.name.value==f'{mid:04d}'.encode());data={c.name.value.decode('cp932'):[struct.unpack('<i',i.value.payload.raw)[0] for i in c.leaf_value.payload.items] for c in part.children};mp=P.L.Map(mid,P.L.native_map(data['地面データ'],data['置物データ'],mid))
  for pos in positions:
   v=VM(copy.deepcopy(mp),pos);v.flags[93]=0
   if mid==401 and pos==(5,5):v.inner[2][:4]=[1]*4
   if mid==403 and pos==(18,11):
    v.event[4][:]=[1]*6
    for column in range(6):P.rock(v,column,True)
   before=copy.deepcopy((dict(v.mp),v.inner[2],v.event[3],v.event[4]));route=[];v.run('KR_WalkPlan',[v.scene,route]);v.check_refs()
   # Old planner is unchanged; enable only its display for the expected path.
   v.flags[93]=1;v.run('KR_DrawPuzzleRoute',[v.mp,v.view,*pos,mid]);expected=list(v.view.get('drawn',[]));assert route==expected,(mid,pos,route,expected)
   assert v.valid(route),(mid,pos,'invalid path',route);v.flags[93]=0;ok=v.start();assert ok and v.scene[7]==route and v.plans==2,(mid,pos,ok,v.scene[7],route,v.plans,v.notices)
   assert before==(dict(v.mp),v.inner[2],v.event[3],v.event[4]);v.check_refs();puzzles.append(dict(mode=mid,start=pos,goal=route[-1],length=len(route)))
 r['shipped_puzzle_current_segments_no_event_writes']=puzzles
 # Embedded original lambdas relocate with Init but their exact instructions remain identical.
 original=(O/'original_28731.jam').read_text(encoding='utf8');nested=[]
 for fid in range(31639,31652):
  start=original.index(f'FUNC {fid}\n');end=original.index('\nENDFUNC ',start);old=original[start:end]
  built=(O/f'built_{fid}.jam').read_text(encoding='utf8');built=built[:built.index('\nENDFUNC ')] if '\nENDFUNC ' in built else built
  assert canonical(old)==canonical(built),fid;nested.append(fid)
 r['relocated_original_lambdas_instruction_exact']=nested
 b=lambda fid:(O/f'built_{fid}.jam').read_text(encoding='utf8')
 assert b(28642).index('CALLFUNC KR_WalkGuard')<b(28642).index('CALLHLL Array Empty 2')
 assert 'CALLMETHOD 0' in b(28639) and 'PUSH 28659' in b(28639)
 assert b(28664).index('CALLFUNC KR_NoticeInstant')<b(28664).index('CALLFUNC KR_WalkCellGate')
 assert b(28664).index('CALLFUNC KR_GetTrap')<b(28664).index('CALLFUNC KR_WalkCellGate')
 assert 'CALLFUNC KR_WalkPause' in b(28739) and 'CALLFUNC KR_WalkStop' in b(28665) and 'CALLFUNC KR_WalkStop' in b(28641)
 base=read_meta(R/'staging/auto_items_20260922/candidate_meta.json')
 for fid in [28638,28639,28643,28644,28645,28647,28649,28650,28658,28677,29240,29242]:assert M['functions'][fid]==base['functions'][fid]
 r['original_step_damage_event_time_and_battle_effect_methods_unchanged']=True
 savej(O/'verification.json',dict(status='AUTO_WALK_COMPILED_PASS',files=ev['files'],tests=r,native_gameplay_verified=False,boundaries='Actual candidate JAM planners/controller/commit/clear and existing puzzle-state query. Native scene getters, cell access, step passability, UI visibility/drawing, notices and input are fixtures. Full native movement and rendered gameplay require in-game retest.'))
 print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in r.items()},indent=2))

if __name__=='__main__':
 prepare()
 for n in ['KR_DrawPuzzleRoute']:
  f=next(f for f in M['functions'] if f['name']==n);cmd('ain','dump','--function',n,'-o',O/f"built_{f['index']}.jam",O/'NightRemaster.ain')
 main()
