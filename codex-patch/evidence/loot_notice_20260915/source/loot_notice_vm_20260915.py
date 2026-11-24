from pathlib import Path
import json,collections
from build_remaster_multiplier_20260915 import read_meta
from build_route_perf_20260915 import symbol
from verify_remaster_multiplier_20260915 import i32
O=Path('loot_notice_20260915')
class VM:
 cached=None
 def __init__(self):
  if VM.cached is None:
   m=read_meta(O/'candidate_meta.json');fs={};counts={}
   for f in m['functions']:
    n=symbol(m,f['index']);c=counts.get(n,0);counts[n]=c+1;fs[n+(f'#{c}' if c else '')]=f
   VM.cached=m,fs
  self.meta,self.fs=VM.cached;self.code={};self.flags=[0]*101;self.first=False;self.saved=[];self.calls=0
  self.party=[{'movable':True} for _ in range(3)];self.persons=3;self.monsters={i:dict(id=i,level=7+i,exp=9+i,training=11+i,money=13+i) for i in range(1,10)};self.ids=[1,2,1,0,0,0,0,0,0];self.placement=True;self.gamelevel=1;self.random=True;self.incomes=[];self.paid=[];self.settle_ok=True;self.updated=0;self.refs=collections.Counter();self.trace=[];self.lookups=0;self.fail_lookup_at=0
 def own(self,obj):
  if obj!=-1:self.refs[id(obj)]+=1
  return obj
 def delete(self,obj):
  if isinstance(obj,dict):self.refs[id(obj)]-=1;assert self.refs[id(obj)]>=0
 def run(self,name,args=()):
  self.calls+=1
  if name=='SystemFlagManager::Get':return self.flags[args[0]] if 0<=args[0]<len(self.flags) else 0
  if name=='SystemFlagManager::Save':self.saved.append(list(self.flags));return
  if name=='N_Tutorial::IsRunFirstTime':assert list(args)==[3];return int(self.first)
  if name=='L_Party::GetNumberOfPersons':return self.persons
  if name=='L_Party::AbilityAt':return self.own(self.party[args[0]] if self.party[args[0]] is not None else -1)
  if name=='L_MonsterManager::At':
   self.lookups+=1;return self.own(self.monsters.get(args[0],-1) if self.lookups!=self.fail_lookup_at else -1)
  if name=='L_DungeonInfo::GetBattleMonsterPlacement':assert len(args[2])==9;args[2][:]=self.ids;self.trace.append('placement');return int(self.placement)
  if name=='L_GameLevel::Get':return self.gamelevel
  if name=='N_Map::IsRandomDungeon':return int(self.random)
  if name=='L_BattleIncome::Clear':self.incomes=[];return 1
  if name=='L_BattleIncome::AddIncome':self.incomes.append(tuple(args));return 1
  if name=='L_BattleIncome::Settle':assert self.run('KR_IsSilentLoot',args);self.paid.append((args[0],list(self.incomes)));self.trace.append('settle');return int(self.settle_ok)
  if name=='L_StatusFace::UpdateAll':self.updated+=1;return
  if name=='AFL_Activity_IsExistPartsByName':return int(args[1] in self.widgets)
  if name=='AFL_Activity_GetPartsNumber':assert args[1] in self.widgets;return args[1]
  if name=='Ｐ＿チェックボックス＿チェック状態取得':return self.widgets[args[0]]
  if name=='Ｐ＿チェックボックス＿チェック状態設定':self.widgets[args[0]]=args[1];return
  f=self.fs[name];fid=f['index'];vs=f['arguments']+f['variables'];li={v['name']:i for i,v in enumerate(vs)};loc={i:0 for i in range(len(vs))};loc.update(enumerate(args));st=[]
  if fid not in self.code:
   ops=[];labs={}
   source=(O/f'built_{fid}.jam').read_text(encoding='utf8')
   if fid==29818:source=source[:source.index('\tPUSHSTRUCTPAGE\n')]+'\tRETURN\n'
   for line in source.splitlines():
    l=line.strip()
    if not l or l.startswith((';','FUNC','ENDFUNC','EOF')):continue
    if l.endswith(':'):labs[l[:-1]]=len(ops)
    else:ops.append(l.split(maxsplit=1))
   self.code[fid]=ops,labs
  ops,labs=self.code[fid];pc=0;steps=0
  while pc<len(ops):
   steps+=1;assert steps<100000,(name,pc);op,*ar=ops[pc];a=ar[0] if ar else '';pc+=1
   if op=='PUSH':st.append(i32(int(a,0)))
   elif op=='S_PUSH':st.append(json.loads(a))
   elif op=='A_REF':pass
   elif op=='.STRUCTREF':assert a=='C_ConfigView m_ActName';st.append('mods')
   elif op=='PUSHLOCALPAGE':st.append(loc)
   elif op=='.LOCALREF':st.append(loc[li[a]])
   elif op in ['.LOCALASSIGN','.LOCALPLUSA']:
    n,v=a.rsplit(' ',1);loc[li[n]]=i32(int(v)+(loc[li[n]] if op=='.LOCALPLUSA' else 0))
   elif op in ['.LOCALINC2','.LOCALINC3']:loc[li[a]]=i32(loc[li[a]]+1)
   elif op=='.GLOBALREF':assert a=='g_sysFlagList';st.append(self.flags)
   elif op=='X_DUP':st.extend(st[-int(a):])
   elif op=='X_MOV':assert a=='2 1';st[-2:]=st[-2:][::-1]
   elif op=='X_REF':assert a=='1';ix=st.pop();obj=st.pop();st.append(obj[ix])
   elif op in ['X_ASSIGN','S_ASSIGN']:
    if op=='X_ASSIGN':assert a=='1'
    v=st.pop();ix=st.pop();obj=st.pop();obj[ix]=v;st.append(v)
   elif op=='X_A_INIT':assert a=='0' and st.pop()==0;ix=st.pop();obj=st.pop();obj[ix]=[];st.append(obj[ix])
   elif op in ['POP','DELETE']:
    v=st.pop()
    if op=='DELETE':self.delete(v)
   elif op=='DG_NEW_FROM_METHOD':
    fid=st.pop();owner=st.pop();st.append((owner,fid))
   elif op=='S_MOD':
    v=st.pop();fmt=st.pop();assert a=='2';st.append(fmt % v)
   elif op=='.S_LOCALASSIGN':
    n,v=a.split(' ',1);loc[li[n]]=json.loads(v)
   elif op in ['PLUSA','MINUSA']:
    v=st.pop();ix=st.pop();obj=st.pop();obj[ix]=i32(obj[ix]+v if op=='PLUSA' else obj[ix]-v);st.append(obj[ix])
   elif op=='NOT':st.append(int(not st.pop()))
   elif op in ['IFZ','IFNZ']:
    if bool(st.pop())==(op=='IFNZ'):pc=labs[a]
   elif op=='JUMP':pc=labs[a]
   elif op=='CALLFUNC':
    ff=self.fs[a];n=len(ff['arguments']);aa=st[-n:] if n else []
    if n:del st[-n:]
    v=self.run(a,aa)
    if ff['return-type'][0]!=0:st.append(v)
   elif op=='CALLMETHOD':
    n=int(a);aa=st[-n:] if n else []
    if n:del st[-n:]
    mid=st.pop();obj=st.pop();v=self.method(mid,obj,aa)
    if self.meta['functions'][mid]['return-type'][0]!=0:st.append(v)
   elif op=='CALLHLL':
    if a=='Array Numof 1':st.append(len(st.pop()))
    elif a=='Array Alloc 1':n=st.pop();arr=st.pop();arr[:]=[0]*n
    elif a=='String ToInt 0':st.append(int(st.pop()))
    else:raise AssertionError(a)
   elif op in ['ADD','SUB','MUL','DIV','LTE','GTE','LT','GT','NOTE','EQUALE','S_ADD','S_NOTE']:
    b=st.pop();v=st.pop()
    if op=='S_ADD':z=v+b
    elif op=='S_NOTE':z=int(v!=b)
    elif op=='MUL':z=i32(v*b)
    elif op=='DIV':z=i32(int(v/b))
    elif op=='ADD':z=i32(v+b)
    elif op=='SUB':z=i32(v-b)
    elif op=='LTE':z=int(v<=b)
    elif op=='GTE':z=int(v>=b)
    elif op=='LT':z=int(v<b)
    elif op=='GT':z=int(v>b)
    elif op=='NOTE':z=int(v!=b)
    else:z=int(v==b)
    st.append(z)
   elif op=='RETURN':
    if f['return-type'][0]==0:assert not st,(name,st);return
    assert len(st)==1,(name,st);return st.pop()
   else:raise AssertionError((name,op,a))
  raise AssertionError('No return')
 def method(self,mid,obj,args):
  keys={27005:'object',27008:'sub',27023:'removed',27301:'movable',26149:'id',26158:'level',26173:'exp',26176:'training',26179:'money'}
  if mid in keys:return obj[keys[mid]]
  if mid==27025:obj['removed']=bool(args[0]);self.trace.append('removed');return
  raise AssertionError(mid)
