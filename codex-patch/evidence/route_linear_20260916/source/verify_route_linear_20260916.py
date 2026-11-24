"""Execute exact compiled helpers; native rendering/time remains a separate check."""
from pathlib import Path
import json,copy,inspect,collections,random,struct
import verify_cheat_menu_20260915 as v
from cheat_support_20260915 import R,cmd,sha,savej
from build_route_perf_20260915 import symbol
from build_remaster_multiplier_20260915 import ex
from verify_route_department_20260915 import native_map

O=R/'staging/route_linear_20260916'

# Extend the existing explicit opcode interpreter, never substitute the BFS body.
src=inspect.getsource(v.VM)
def change(old,new):
 global src
 assert old in src,old;src=src.replace(old,new)
change('steps<150000','steps<1000000')
change('steps+=1;', 'steps+=1;self.steps+=1;')
change("elif op=='PUSHLOCALPAGE':st.append(loc)","elif op=='PUSHLOCALPAGE':st.append(loc)\n   elif op=='PUSHSTRUCTPAGE':st.append(self.this)")
change("elif op=='.LOCALCREATE':", "elif op=='.LOCALDEC2':loc[li[a]]=i32(loc[li[a]]-1)\n   elif op=='.LOCALDELETE':self.delete(loc[li[a]]);loc[li[a]]=-1\n   elif op=='NEW':\n    assert a=='CASPos 20851';y=st.pop();x=st.pop();st.append((x,y))\n   elif op=='.LOCALCREATE':")
change("obj[index])", "obj[index])")
change("obj[ix]=v;st.append(v)","\n    if isinstance(obj,list):assert 0<=ix<len(obj),(name,ix,len(obj))\n    obj[ix]=v;st.append(v)")
change("elif a=='Array Realloc 2':", "elif a in ['Array Realloc 1','Array Realloc 2']:")
change("elif a=='Array Copy#3 2':", "elif a=='Array PushBack 2':\n     value=st.pop();target=st.pop();target.append(copy.deepcopy(value))\n    elif a=='Array Copy#3 2':")
change("['ADD','SUB','MUL','DIV','LTE'", "['MOD','ADD','SUB','MUL','DIV','LTE'")
change("if k=='ADD':v=aa+b", "if k=='MOD':v=aa-trunc(aa,b)*b\n    elif k=='ADD':v=aa+b")
ns=dict(vars(v));ns['O']=O
META=v.read_meta(O/'candidate_meta.json');ns['read_meta']=lambda path:META
exec(compile(src,'<extended exact-opcode interpreter>','exec'),ns)

class Cell(dict):pass
class Map(dict):
 def __init__(self,mid=1001,data=None,event=None):
  super().__init__(data or {});self.map_id=mid;self.event=mid<1000 if event is None else event;self.removed=set()

def walk(mp,p):
 if p not in mp:return False
 obj=mp[p][0]
 return obj!=1 if not mp.event else obj not in [-1,1] or p in mp.removed

class VM(ns['VM']):
 def __init__(self):super().__init__();self.steps=0;self.count=collections.Counter();self.owned={};self.this=None
 def run(self,name,args=(),**kw):
  if name=='KR_SaveOptions':return
  return super().run(name,args,**kw)
 def delete(self,z):
  if isinstance(z,Cell):assert self.owned.pop(id(z),None) is z,'unbalanced owned cell release'
 def method(self,mid,obj,a):
  self.count[mid]+=1
  if mid==27082:
   p=tuple(a)
   if p not in obj:return -1
   c=Cell(object=obj[p][0],sub=obj[p][1],event=obj.event,removed=p in obj.removed)
   self.owned[id(c)]=c;return c
  if mid==27039:
   if not obj['event']:return int(obj['object']!=1)
   return int(obj['object'] not in [-1,1] or obj['removed'])
  assert mid not in [27081,30019], 'Old cost-map or AStar must never run in new preview'
  return super().method(mid,obj,a)

def expected(mp,start):
 # Independent graph-distance oracle; priority chosen before reachability.
 if mp.map_id in [202,204]:obj,sub=7,0
 elif mp.map_id==203:
  obj=7;sub=min([c[1] for p,c in mp.items() if c[0]==7 and p not in mp.removed and 0<=c[1]<4]+[4])
 else:obj,sub=2,1
 targets={p for p,c in mp.items() if c==(obj,sub) and (obj!=7 or p not in mp.removed)}
 q=collections.deque([start]);dist={start:0}
 while q:
  p=q.popleft()
  for n in [(p[0]-1,p[1]),(p[0],p[1]-1),(p[0]+1,p[1]),(p[0],p[1]+1)]:
   if 0<=n[0]<30 and 0<=n[1]<30 and n not in dist and walk(mp,n):dist[n]=dist[p]+1;q.append(n)
 candidates=[(dist[p],p[1]*30+p[0],p) for p in targets if p in dist and dist[p]>0]
 if not candidates:return 0,None
 d,_,goal=min(candidates);return d,goal

def check(mp,start,label):
 vm=VM();vm.flags[84]=20260915;vm.flags[93]=1;view={};before=copy.deepcopy(mp);saved=list(vm.flags)
 vm.run('KR_DrawRoute',[mp,view,*start]);path=view['drawn'];d,goal=expected(mp,start)
 assert len(path)==d and (path[-1] if path else None)==goal,(label,d,goal,path)
 last=start
 for p in path:assert abs(p[0]-last[0])+abs(p[1]-last[1])==1 and walk(mp,p),(label,p);last=p
 assert mp==before and mp.removed==before.removed and not vm.owned
 assert all(vm.flags[i]==saved[i] for i in range(101) if i not in [85,86,89])
 assert vm.flags[87]==vm.flags[88]==0 and vm.count[27082]==900 and vm.count[28677]==1
 return dict(case=label,length=d,goal=goal,compiled_instructions=vm.steps,cells=vm.count[27082]),vm,view

def main():
 ev=json.loads((O/'build_evidence.json').read_text());assert sha(O/'NightRemaster.ain')==ev['files']['NightRemaster.ain']
 m=v.read_meta(O/'candidate_meta.json')
 for n in ['KR_Flag','KR_Poke','KR_InitOptions','KR_GetRoute','KR_SetRoute','KR_ResetTransient','KR_SweepActive']:
  f=next(f for f in m['functions'] if f['name']==n);cmd('ain','dump','--function',n,'-o',O/f"built_{f['index']}.jam",O/'NightRemaster.ain')
 rows=[]
 def go(mp,p,n):
  row,vm,view=check(mp,p,n);rows.append(row);return vm,view
 corridor={(x,1):(0,0) for x in range(1,9)};corridor[8,1]=(2,1)
 basic=Map(data=corridor);vm,view=go(basic,(1,1),'ordinary corridor')
 initial=vm.count.copy()
 for _ in range(1000):vm.run('KR_DrawRoute',[basic,view,1,1])
 assert vm.count[27082]==initial[27082] and vm.count[28677]==1
 vm.run('KR_DrawRoute',[basic,view,2,1]);assert vm.count[27082]==1800
 vm.run('KR_SetRoute',[0]);vm.run('KR_DrawRoute',[basic,view,2,1]);assert view['drawn']==[] and vm.flags[89]==0
 vm.run('KR_SetRoute',[1]);vm.run('KR_DrawRoute',[basic,view,2,1]);assert view['drawn']
 vm.run('KR_ResetTransient');assert vm.flags[85]==vm.flags[86]==-1
 replacement=Map(data={(2,1):(0,0),(2,2):(0,0),(2,3):(2,1)});vm.run('KR_DrawRoute',[replacement,view,2,1]);assert view['drawn']==[(2,2),(2,3)]
 # Execute actual conditional setter code with exact fields, not a replacement model.
 setters=[]
 for fid,field in [(27007,3),(27010,4),(27025,9),(27031,11)]:
  for value in [0,1,4]:
   for same in [True,False]:
    vm.this={field:value if same else value+1};member={3:'ObjectId',4:'ObjectSubId',9:'IsRemoved',11:'IsEventDungeon'}[field]
    vm.structrefs={f'C_MapCellInfo <{member}>':vm.this[field]};vm.flags[85:87]=[2,3];vm.run(symbol(m,fid),[value]);assert vm.this[field]==value
    assert vm.flags[85:87]==([2,3] if same else [-1,-1]);setters.append((fid,value,same))
 for mode in [1001,202,203,204]:
  a=Map(mode,{(x,y):(0,0) for y in range(5) for x in range(5)})
  a[2,0]=(7,0) if mode in [202,203,204] else (2,1);a[0,2]=a[2,0]
  go(a,(2,2),f'equal distance row-major goal {mode}')
  a[2,2]=a[2,0];go(a,(2,2),f'exclude start goal {mode}')
  a[2,2]=(1,0);go(a,(2,2),f'blocked start seed {mode}')
  a.removed.update([p for p,c in a.items() if c[0]==7]);go(a,(2,2),f'removed goals {mode}')
 a=Map(203,{(1,1):(0,0),(2,1):(7,1),(10,10):(7,0),(3,1):(7,4)});go(a,(1,1),'blocked priority does not advance')
 a.removed.add((10,10));go(a,(1,1),'advance to next event group after removal')
 a.removed.add((2,1));go(a,(1,1),'sub4 fallback only after0..3 removed')
 a=Map(202,{(1,1):(0,0),(2,1):(1,0),(3,1):(7,0)});go(a,(1,1),'wall blocks');a.removed.add((2,1));go(a,(1,1),'story removed wall passes')
 a=Map(data={(1,1):(0,0),(2,1):(1,0),(3,1):(2,1)});a.removed.add((2,1));go(a,(1,1),'ordinary wall stays blocked')
 go(Map(data={(1,1):(0,0)}),(1,1),'no goal')
 a=Map(data={(x,y):(0,0) for y in range(30) for x in range(30)});a[29,29]=(2,1);go(a,(0,0),'full900open worst distance')
 a=Map(data={(x,y):(1,0) for y in range(30) for x in range(30)})
 for y in range(0,30,2):
  for x in range(30):a[x,y]=(0,0)
  if y<28:a[29 if y%4==0 else 0,y+1]=(0,0)
 a[29,28]=(2,1);go(a,(0,0),'long snake path')
 # Actual shipped department EX layouts, all ordered203stages, varied positions.
 rt=Path(ev['source_pointer']['runtime']);assert sha(rt/'NightRemasterEX.ex')==ev['unchanged_files']['NightRemasterEX.ex']
 root=ex.decode_ex(rt/'NightRemasterEX.ex').blocks[2].payload
 for mid in [201,202,203,204]:
  part=next(t for t in root.children if t.name.value==f'{mid:04d}'.encode())
  data={c.name.value.decode('cp932'):[struct.unpack('<i',i.value.payload.raw)[0] for i in c.leaf_value.payload.items] for c in part.children}
  mp=Map(mid,native_map(data['地面データ'],data['置物データ'],mid))
  starts=[p for p,c in mp.items() if c==(2,2)]+[p for p in mp if walk(mp,p)][::80]
  for p in starts:go(mp,p,f'native department{mid} at{p}')
  if mid==203:
   for sub in range(5):
    go(mp,(14,3),f'native203 event phase{sub}')
    mp.removed.update(p for p,c in mp.items() if c==(7,sub))
 rng=random.Random(20260916)
 for n in range(100):
  mid=[1001,202,203,204][n%4];mp=Map(mid)
  for y in range(15):
   for x in range(15):
    if rng.random()<.06:continue
    mp[x,y]=(1,0) if rng.random()<.25 else (0,0)
    if rng.random()<.04:mp.removed.add((x,y))
  for _ in range(8):mp[rng.randrange(15),rng.randrange(15)]=(7,rng.randrange(6)) if mid<1000 else (2,rng.randrange(3))
  go(mp,(rng.randrange(15),rng.randrange(15)),f'random{n}')
 # Existing transition methods must remain active at their exact old addresses.
 old=v.read_meta(O/'source_meta.json')
 for fid in [28638,28669,28673,28677,28754,31850,31856]:assert old['functions'][fid]==m['functions'][fid]
 r=dict(status='ROUTE_LINEAR_STATIC_PASS_NATIVE_PENDING',files=ev['files'],compiled_cases=len(rows),cases=rows,compiled_setter_cases=len(setters),same_position_1000_updates_additional_scans=0,
 linear_cost_map_builds=0,linear_native_AStar_calls=0,per_replan_cell_reads=900,owned_cell_refs_balanced=True,queue_bounds_checked=True,actual_department_EX_tested=True,
 existing_transition_load_toggle_hooks_exact=True,save_schema_exact=True,native_performance_measured=False,native_gameplay_verified=False,
 verification_scope='Exact compiled new helper instructions with native accessor/draw fixtures, independent shortest-distance oracle, actual shipped department maps. Not a native frame-time benchmark.')
 savej(O/'verification.json',r);print(json.dumps({k:z for k,z in r.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
