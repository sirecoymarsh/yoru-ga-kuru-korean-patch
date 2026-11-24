"""Exact compiled puzzle helpers, bounded native access/event fixtures, no game control."""
from pathlib import Path
import json,copy,collections,struct
import verify_route_linear_20260916 as L
from cheat_support_20260915 import R,read_meta,sha,savej
from build_remaster_multiplier_20260915 import ex

O=R/'staging/route_puzzle_20260916'
META=read_meta(O/'candidate_meta.json')
s=L.src
def change(a,b):
 global s
 assert a in s,a;s=s.replace(a,b)
change("li={v['name']:i for i,v in enumerate(vs)};loc=", "li={};seen={}\n  for i,v in enumerate(vs):\n   n=v['name'];j=seen.get(n,0);seen[n]=j+1;li[n+(f'#{j}' if j else '')]=i\n  loc=")
change("elif op=='X_MOV':assert a=='2 1';st[-2:]=st[-2:][::-1]", "elif op=='X_MOV':\n    n,k=map(int,a.split());z=st[-n:];st[-n:]=z[-k:]+z[:-k]")
change("assert a=='1';index=st.pop();obj=st.pop();st.append(obj[index])", "n=int(a);index=st.pop();obj=st.pop();st.extend(obj[index+i] for i in range(n))")
change("elif op=='NOT':", "elif op=='INC':\n    ix=st.pop();obj=st.pop();obj[ix]+=1\n   elif op=='SP_INC':self.retain(st.pop())\n   elif op=='DG_CALLBEGIN':\n    assert a=='\"DG_Func<ref I_Scene>\"';assert st.pop() is self.delegate;dg_done=False\n   elif op=='DG_CALL':\n    typ,label=a.rsplit(' ',1);assert typ=='\"DG_Func<ref I_Scene>\"'\n    if dg_done:pc=labs[label]\n    else:self.retain(self.outer);st.extend([self.outer,0]);dg_done=True\n   elif op=='NOT':")
change("else None);assert st[-1] is not None,a", "else self.delegate if a=='GetActiveScene' else None);assert st[-1] is not None,a")
change("if a in ['Array Numof 1','Array Numof 2']:", "if a=='Delegate Numof 0':assert st.pop() is self.delegate;st.append(self.delegate_count)\n    elif a in ['Array Numof 1','Array Numof 2']:")
# Existing ordinary tests are replayed against the candidate, not the baseline.
L.O=O;L.META=META;L.ns.update(O=O,read_meta=lambda p:META)
ns=dict(L.ns);exec(compile(s,'<exact puzzle helper instructions>','exec'),ns)
L.ns['VM'].run=ns['VM'].run

class Node(dict):
 def __eq__(self,o):return self is o
 def __ne__(self,o):return self is not o

class VM(L.VM):
 def __init__(self):
  super().__init__();self.refs=collections.Counter();self.delegate=object();self.delegate_count=1;self.outer=-1;self.pos=(0,0);self.events=[];self.on_event=None
 def retain(self,z):
  if z==-1:return
  assert isinstance(z,Node);self.refs[id(z)]+=1
 def delete(self,z):
  if isinstance(z,Node):
   self.refs[id(z)]-=1;assert self.refs[id(z)]>=0
  else:super().delete(z)
 def method(self,mid,obj,a):
  if mid in [26559,26562]:return self.pos[mid-26559==3]
  if mid in [28949,28952,28981,28982,29008,29009]:
   self.events.append((mid,a[0]));self.on_event(mid,a[0]);return
  return super().method(mid,obj,a)
 def bind(self,mp,view):
  self.mp=mp;self.view=view;self.dv=Node({3:view});self.inner=Node({0:mp,1:self.dv,2:[0]*8,3:[0]*8})
  prepare={401:28951,403:28985,405:29012}[mp.map_id]
  rr,bb={401:(28949,28952),403:(28981,28982),405:(29008,29009)}[mp.map_id]
  vt=[prepare,0,0,0,rr,bb,0,0,0,0]
  self.event=Node({0:vt,1:mp,2:self.inner,3:0,4:[0]*6})
  self.scene=Node({0:[28634,0,0,0],2:self.dv,4:self.event,5:0,6:mp})
  self.outer=Node({0:[28170,0,0],3:self.scene,4:0})
  self.flags[84]=20260915;self.flags[93]=1;self.flags[85:87]=[-1,-1]
 def draw(self,p):
  self.pos=p;before=(copy.deepcopy(dict(self.mp)),set(self.mp.removed),list(self.inner[2]),list(self.event[4]),self.event[3]);flags=list(self.flags)
  self.run('KR_DrawRoute',[self.mp,self.view,*p]);assert not self.owned and not any(self.refs.values())
  assert before==(dict(self.mp),self.mp.removed,self.inner[2],self.event[4],self.event[3]),'solver modified native puzzle state'
  assert all(self.flags[i]==flags[i] for i in range(101) if i not in [85,86,89]);assert self.flags[87]==self.flags[88]==0
  path=self.view.get('drawn',[]);last=p
  for z in path:assert abs(z[0]-last[0])+abs(z[1]-last[1])==1 and L.walk(self.mp,z),(p,z,path);last=z
  return list(path)
 def stepped(self,p):
  self.pos=p;obj,sub=self.mp[p]
  if obj not in [6,7] or p in self.mp.removed:return False
  old=self.this;self.this=self.inner
  self.structrefs={'C_InnerEventDungeon m_nSteppedOnEventB':self.inner[2],'C_InnerEventDungeon m_nSteppedOnEventR':self.inner[3]}
  self.run('C_InnerEventDungeon@SteppedOnEvent',[int(obj==6),sub,self.event,0]);self.this=old
  assert not any(self.refs.values()) and not self.owned
  return True

def maps():
 ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime'])
 assert sha(rt/'NightRemasterEX.ex')==ev['unchanged_files']['NightRemasterEX.ex']
 root=ex.decode_ex(rt/'NightRemasterEX.ex').blocks[2].payload;out={}
 for mid in [401,403,405]:
  part=next(t for t in root.children if t.name.value==f'{mid:04d}'.encode())
  data={c.name.value.decode('cp932'):[struct.unpack('<i',i.value.payload.raw)[0] for i in c.leaf_value.payload.items] for c in part.children}
  out[mid]=L.Map(mid,L.native_map(data['地面データ'],data['置物データ'],mid))
 return out

def rock(vm,c,close):
 for y in [3,11,19,27]:
  gate=(6+c*2,y);choice=(7+c*2,y)
  if close:vm.mp[gate]=(1,3);vm.mp.removed.discard(gate);vm.mp.removed.add(choice)
  else:vm.mp.removed.add(gate);vm.mp[choice]=(7,c);vm.mp.removed.discard(choice)

def native_event(vm,mid,eid):
 """Bounded event effects independently transcribed from original native event scripts."""
 mp=vm.mp;mode=mp.map_id;p=vm.pos
 if mode==401 and mid==28952 and eid==5 and all(vm.inner[2][:4]) and sum(vm.inner[2][:4])>=12:
  mp.removed.update(p for p,c in mp.items() if c[0]==7 and c[1]<4)
  for p,c in list(mp.items()):
   if c==(1,4):mp[p]=(0,0)
 elif mode==403:
  if mid==28982 and 1<=eid<=6:
   c=eid-1;vm.event[4][c]=int(p==(7+2*c,[11,27,27,19,11,11][c]));rock(vm,c,True)
  elif mid==28982 and eid==7 and all(vm.event[4]):mp.removed.update([(20,1),(24,19)])
  elif mid==28981 and eid==8:
   vm.pos=(3,3)
   for c in range(6):rock(vm,c,False)
 elif mode==405:
  if mid==29009 and eid==1:vm.pos=(6,13)
  if mid==29008 and eid==1:vm.event[3]=1

def setup(mp):
 vm=VM();vm.bind(copy.deepcopy(mp),Node());vm.on_event=lambda m,e:native_event(vm,m,e);return vm

def play(vm,start,label,max_segments=50):
 p=start;trace=[];allsteps=0
 for _ in range(max_segments):
  path=vm.draw(p);assert path,(label,p,'no guide',trace,vm.inner[2],vm.event[4])
  trace.append({'from':p,'goal':path[-1],'length':len(path)})
  for z in path:
   obj,sub=vm.mp[z]
   if vm.mp.map_id==405:assert (obj,sub)!=(7,0) or z in vm.mp.removed,'warp trap crossed'
   oldstate=list(vm.event[4]);oldremoved=set(vm.mp.removed);allsteps+=1;p=z
   if (obj,sub)==(2,1):return dict(case=label,segments=trace,walking_steps=allsteps,completed=True)
   if vm.stepped(p):
    p=vm.pos
    if vm.mp.map_id==405 and vm.event[3]:return dict(case=label,segments=trace,walking_steps=allsteps,reached_native_boss=True)
    # Native hints do not change movement or answers; no need to rescan fixture after them.
    if vm.mp.map_id==401 or oldstate!=vm.event[4] or oldremoved!=vm.mp.removed or p!=z:break
  else:raise AssertionError((label,'goal is not a trigger/exit',p))
 raise AssertionError((label,'too many segments',trace))

def main():
 ev=json.loads((O/'build_evidence.json').read_text());assert sha(O/'NightRemaster.ain')==ev['files']['NightRemaster.ain']
 L.main();ordinary=json.loads((O/'verification.json').read_text());layouts=maps();rows=[]
 # Entire physical puzzle route, including the exact compiled post-event hook.
 for counts,start in [([0,0,0,0],(15,2)),([1,0,2,0],(19,27)),([1,1,1,1],(5,5)),([3,3,3,2],(25,5)),([3,3,3,3],(15,22))]:
  vm=setup(layouts[401]);vm.inner[2][:4]=counts
  if start==(15,22):vm.stepped(start)
  rows.append(play(vm,start,f'401 partial counts {counts}'))
 vm=setup(layouts[401])
 for p,c in list(vm.mp.items()):
  if c==(1,4):vm.mp[p]=(0,0)
 rows.append(play(vm,(19,27),'401 manually inspected wall already open'))
 vm=setup(layouts[403]);rows.append(play(vm,(3,3),'403 six correct branches'))
 for badcol in [0,2,5]:
  vm=setup(layouts[403])
  for c in range(badcol):vm.event[4][c]=1;rock(vm,c,True)
  vm.stepped((7+2*badcol,3));rows.append(play(vm,vm.pos,f'403 wrong branch {badcol}, reset then solve'))
 vm=setup(layouts[403]);vm.event[4][:]=[1]*6
 for c in range(6):rock(vm,c,False)
 rows.append(play(vm,(3,3),'403 reset retains old true answers but choices reopened'))
 vm=setup(layouts[403]);vm.event[4][:]=[1]*6
 for c in range(6):rock(vm,c,True)
 rows.append(play(vm,(18,11),'403 all answers complete awaiting B7'))
 for p in [(22,12),(6,13)]:rows.append(play(setup(layouts[405]),p,f'405 avoid warp traps from {p}'))
 vm=setup(layouts[405]);vm.event[3]=1;assert vm.draw((7,28))==[]
 # Unknown/bad scene must fail closed, release all acquired refs, and NOT cache failure.
 failures=[]
 variants=[('empty delegate',lambda v:setattr(v,'delegate_count',0)),('multiple delegates',lambda v:setattr(v,'delegate_count',2)),('null outer',lambda v:setattr(v,'outer',-1)),('wrong outer',lambda v:v.outer[0].__setitem__(0,0)),('null scene',lambda v:v.outer.__setitem__(3,-1)),('wrong scene',lambda v:v.scene[0].__setitem__(0,0)),('scene map mismatch',lambda v:v.scene.__setitem__(6,-1)),('view mismatch',lambda v:v.dv.__setitem__(3,Node())),('null event',lambda v:v.scene.__setitem__(4,-1)),('wrong event',lambda v:v.event[0].__setitem__(0,0)),('event map mismatch',lambda v:v.event.__setitem__(1,-1)),('null inner',lambda v:v.event.__setitem__(2,-1)),('inner map mismatch',lambda v:v.inner.__setitem__(0,-1)),('inner view mismatch',lambda v:v.inner.__setitem__(1,-1)),('short counters',lambda v:v.inner.__setitem__(2,[0])),('bad counter',lambda v:v.inner[2].__setitem__(0,-1))]
 for name,edit in variants:
  vm=setup(layouts[401]);edit(vm);vm.draw((15,2));assert vm.flags[85:87]==[-1,-1] and vm.count[27082]==0
  failures.append(name)
 # Same-position frames do not query native state or scan cells again.
 vm=setup(layouts[401]);vm.draw((15,2));calls=vm.calls;reads=vm.count[27082]
 for _ in range(1000):vm.draw((15,2))
 assert vm.count[27082]==reads==900
 vm.run('KR_SetRoute',[0]);vm.draw((15,2));assert vm.view['drawn']==[]
 vm.run('KR_SetRoute',[1]);vm.draw((15,2));assert vm.view['drawn']
 # A failed prepare-frame query retries successfully at the very same coordinate.
 vm=setup(layouts[401]);vm.delegate_count=0;vm.draw((15,2));vm.delegate_count=1;assert vm.draw((15,2))
 result=dict(status='PUZZLE_ROUTE_STATIC_PASS_NATIVE_PENDING',files=ev['files'],scope=[401,403,405],ordinary_compiled_cases=ordinary['compiled_cases'],ordinary_setter_cases=ordinary['compiled_setter_cases'],puzzle_cases=rows,state_query_fail_closed_cases=failures,reference_lifetimes_balanced=True,compiled_post_event_refresh_tested=True,failed_query_not_cached=True,same_position_1000_updates_additional_scans=0,game_state_unchanged_by_solver=True,save_schema_exact=True,native_gameplay_verified=False,native_performance_measured=False,verification_scope='Exact compiled new helpers and SteppedOnEvent hook. Native scene-delegate/getter/draw and original event effects are fixtures, not native playthrough.')
 savej(O/'verification.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
