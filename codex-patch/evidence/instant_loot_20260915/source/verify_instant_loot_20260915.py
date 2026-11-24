"""Execute actual compiled contact/option helpers with explicit engine fixtures."""
from pathlib import Path
import json,re,shutil,collections
from cheat_support_20260915 import sha,savej
from build_remaster_multiplier_20260915 import read_meta
from build_route_perf_20260915 import symbol
from verify_remaster_multiplier_20260915 import i32
import verify_mod_tab_20260915 as oldqa

O=Path('instant_loot_20260915');BASE=Path('mod_tab_20260915')
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
   elif op=='X_ASSIGN':assert a=='1';v=st.pop();ix=st.pop();obj=st.pop();obj[ix]=v;st.append(v)
   elif op=='X_A_INIT':assert a=='0' and st.pop()==0;ix=st.pop();obj=st.pop();obj[ix]=[];st.append(obj[ix])
   elif op in ['POP','DELETE']:
    v=st.pop()
    if op=='DELETE':self.delete(v)
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
    else:raise AssertionError(a)
   elif op in ['ADD','SUB','LTE','GTE','LT','GT','NOTE','EQUALE']:
    b=st.pop();v=st.pop()
    if op=='ADD':z=i32(v+b)
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

def tests():
 v=VM();v.run('KR_InitOptions');option_cases=0
 for initial in [0,1,2]:
  v.flags[92]=initial
  for _ in range(100):
   v.run('KR_SetBattleMode',[v.run('KR_GetQuick'),v.run('KR_GetLoot')])
   assert v.flags[92]==initial;option_cases+=1
 # One clicked checkbox alongside the OTHER widget's stale pre-click state.
 mode_cases=0
 for old,quick,loot,want in [(1,1,1,2),(2,1,1,1),(0,1,0,1),(0,0,1,2),(1,0,0,0),(2,0,0,0),(1,1,0,1),(2,0,1,2),(0,0,0,0)]:
  v.flags[92]=old;v.widgets={'KR_CheatQuick':quick,'KR_CheatLoot':loot}
  for _ in range(20):
   v.run('C_ConfigView@EventConfPartsDataForAsra',[0,0,'mods']);assert v.flags[92]==want,(old,quick,loot,v.flags[92])
   assert v.widgets=={'KR_CheatQuick':int(want==1),'KR_CheatLoot':int(want==2)}
  mode_cases+=1
 for widgets in [{},{'KR_CheatQuick':1},{'KR_CheatLoot':1}]:
  v.flags[92]=2;v.widgets=dict(widgets);v.run('C_ConfigView@EventConfPartsDataForAsra',[0,0,'other']);assert v.flags[92]==2 and v.widgets==widgets
 for kind,num in [('Loot',2),('Quick',1),('Loot',2)]:v.run('KR_Set'+kind,[1]);assert v.flags[92]==num
 v.run('KR_SetLoot',[0]);assert v.flags[92]==0
 for n in [-1,0,1,2,2026091499,2026091500,2026091501,2026091502,2147483647]:assert v.run('KR_IsSilentLoot',[n])==(n in [2026091500,2026091501])
 guards=0
 for enabled in [0,1,2]:
  for first in [False,True]:
   for obj in range(9):
    for sub in [-1,0,1,2,7]:
     for removed in [False,True]:
      v.flags[92]=enabled;v.first=first;c=dict(object=obj,sub=sub,removed=removed)
      assert v.run('KR_LootEligible',[c])==bool(enabled==2 and not first and obj==3 and sub in [0,1] and not removed);guards+=1
 v.flags[92]=2;v.first=False;assert not v.run('KR_LootEligible',[-1])
 cases=0
 for game in [0,1,2,3]:
  for random in [False,True]:
   for persons in [1,2,3]:
    for count in [1,3,9]:
     v=VM();v.run('KR_InitOptions');v.flags[92]=2;v.gamelevel=game;v.random=random;v.persons=persons;v.ids=list(range(1,count+1))+[0]*(9-count)
     cell=dict(object=3,sub=0,removed=False);assert v.run('KR_TryInstantLoot',[cell,204])==1
     assert v.trace==['placement','settle','removed'] and v.updated==1 and not v.incomes and not any(v.refs.values())
     kind,rows=v.paid[0];assert kind==2026091500+int(not random)
     delta=[0,0,0,0] if game<2 else [30,30,20,40] if game==2 else [60,50,30,60]
     expected=[tuple([i]+[v.monsters[i][key]+d for key,d in zip(['level','exp','training','money'],delta)]) for i in range(1,count+1)]
     assert rows==expected
     assert not v.run('KR_TryInstantLoot',[cell,204]) and len(v.paid)==1;cases+=1
 failures=0
 for mode in ['no_movable','missing','placement','empty','persons0','persons4','second_lookup','settle']:
  v=VM();v.run('KR_InitOptions');v.flags[92]=2;cell=dict(object=3,sub=1,removed=False)
  if mode=='no_movable':v.party=[None,{'movable':False},{'movable':False}]
  if mode=='missing':v.ids[0]=999
  if mode=='placement':v.placement=False
  if mode=='empty':v.ids=[0]*9
  if mode=='persons0':v.persons=0
  if mode=='persons4':v.persons=4
  if mode=='second_lookup':v.fail_lookup_at=5
  if mode=='settle':v.settle_ok=False
  assert not v.run('KR_TryInstantLoot',[cell,204]) and not cell['removed'] and not v.updated and not v.incomes and not any(v.refs.values()),mode
  if mode!='settle':assert not v.paid
  failures+=1
 return dict(passive_option_roundtrips=option_cases,stale_checkbox_transition_cases=mode_cases,eligibility_cases=guards,compiled_encounter_reward_cases=cases,failure_cases=failures,reference_ownership_balanced=True,repeat_contact_no_duplicate_reward=True,native_settle_math_executed=False)

def normalize(s):
 rows=[];labels={}
 for line in s.splitlines():
  l=line.strip()
  if not l or l.startswith((';','FUNC','ENDFUNC','EOF')):continue
  if l.endswith(':'):labels[l[:-1]]=len(rows)
  else:rows.append(l)
 for i,l in enumerate(rows):
  if l.startswith(('IFZ ','IFNZ ','JUMP ')):op,target=l.split();rows[i]=op+' @'+str(labels[target])
 return rows

def closure():
 # Invert exactly the three new Settle modifications; all original arithmetic,
 # property writes and control-flow destinations must remain identical.
 s=(O/'built_26258.jam').read_text();old=(O/'original_26258.jam').read_text()
 s=re.sub(r'\t.LOCALREF nDungeonType\n\tPUSH 2026091501\n\tEQUALE\n\tIFNZ [^\n]+\n','',s,count=1)
 s=re.sub(r'\t.LOCALREF nDungeonType\n\tCALLFUNC KR_IsSilentLoot\n\tIFNZ [^\n]+\n','',s,count=1)
 s=s.replace('\t.LOCALREF nDungeonType\n\tCALLFUNC KR_IsSilentLoot\n\tNOT\n','\tPUSH 1\n');assert normalize(s)==normalize(old)
 s=(O/'built_28664.jam').read_text();old=(O/'original_28664.jam').read_text()
 start=s.index('\t.LOCALREF cell\n\t.GLOBALREF Flags\n\tPUSH 26556\n');end=s.index('\tCALLFUNC KR_GetTrap\n',start);region=s[start:end]
 assert 'CALLFUNC KR_TryInstantLoot' in region and 'PUSH 28763' in region and region.count('RETURN')==1
 assert normalize(s[:start]+s[end:])==normalize(old)
 m=read_meta(O/'candidate_meta.json');a=read_meta(BASE/'candidate_meta.json')
 for sw,owner in [(361,26258),(450,28664),(451,28664)]:
  addresses=[x['address'] for x in m['switches'][sw]['cases']];lo=m['functions'][owner]['address'];others=[f['address'] for f in m['functions'] if f['address']>lo];hi=min(others)
  assert all(lo<=x<hi for x in addresses)
  assert len({y['address']-x['address'] for x,y in zip(a['switches'][sw]['cases'],m['switches'][sw]['cases'])})==1
 return dict(native_reward_math_and_old_0_1_control_flow_exact=True,collision_hook_only_change=True,all_three_switches_target_relocated_owners=True,normal_quick_preview_and_route_preserved=True)

def main():
 ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime']);assert all(sha(O/n)==h for n,h in ev['files'].items())
 vm=tests();cl=closure()
 # Reuse font/native geometry validator on the final payload, not a mock font.
 for f in BASE.glob('pact_*_tabs.pactex'):shutil.copy2(f,O/f.name)
 shutil.copy2(O/'pact_185_loot.pactex',O/'pact_185_mods.pactex');shutil.copy2(rt/'NightRemasterEX.ex',O/'NightRemasterEX.ex')
 oldqa.O=O;ui=oldqa.ui_tests(rt,extra_controls=['KR_CheatLoot'],bottom_limit=646)
 q=dict(status='INSTANT_LOOT_STATIC_PASS_NATIVE_PENDING',files=ev['files'],compiled_helpers=vm,preservation=cl,UI=ui,native_gameplay_verified=False,actual_save_reload_verified=False,translator_model='Codex internal')
 savej(O/'verification.json',q);print(json.dumps({k:v for k,v in q.items() if k!='UI'},indent=2))
if __name__=='__main__':main()
