"""Execute compiled JAM in a strict stack fixture. Not native gameplay evidence.
Native reward/GUI/HLL boundaries are explicit fixtures; snapshot, scope, RNG,
transaction order, EXP arithmetic and control flow execute the built instructions.
"""
from pathlib import Path
import copy,json,re,random
from build_remaster_multiplier_20260915 import read_meta,encode,decode
from build_route_perf_20260915 import symbol
from cheat_support_20260915 import savej,sha
O=Path('dungeon_skip_20260916')
M=read_meta(O/'candidate_meta.json'); FS={}; SEEN={}
for f in M['functions']:
 n=symbol(M,f['index']); c=SEEN.get(n,0);SEEN[n]=c+1;FS[n+(f'#{c}' if c else '')]=f
GLOBALS={g['name']:i for i,g in enumerate(M['globals'])}
def eq(a,b):return a is b if isinstance(a,(dict,list)) or isinstance(b,(dict,list)) else a==b
def i32(n):return ((n+2**31)%2**32)-2**31
class VM:
 def __init__(self):
  self.g={};self.g[229]=[0]*101;self.g[229][84]=20260915;self.g[229][99]=20260916
  self.g.update({201:2,202:2,203:2,204:2,206:1,253:[1,2,3],198:[]})
  self.g[250]=[]
  for i in range(8):
   a=[0]*28;a[0]=i+1;a[1]=10 if i<3 else 0;a[2]=100;a[3]=80;a[4]=20;a[5]=200;a[6]=300;a[13]=20;a[16]=15;a[21]=[-1]*21;a[22]=[0]*4;a[25]=[0]*30;self.g[250].append(a)
  self.g[230]=[[i,encode('아이템'+str(i)).decode('cp932'),'',0,0] for i in range(6)]
  self.g[231]=[[i,i%7+1,encode('장비'+str(i)).decode('cp932'),0,0] for i in range(28)]
  self.g[236]=[[[[0,0] for j in range(10)] for i in range(4)]];self.g[196]=[0,[0]*99]
  self.g[GLOBALS['Flags']]=dict(month=4,day=29,lock=False);self.g[GLOBALS['Flags']][52]={1:0}
  self.scene={2:{4:{0:{},1:0}},4:-1,5:-1,6:[[],1001,0,'',0,0],7:[],11:0}
  self.map=1001;self.start=1001;self.base=1000;self.rem=1000;self.training=True;self.living=True;self.confirm=True;self.modal=lambda:None;self.trace=[];self.report=[];self.saves=0;self.settles=0;self.chests=0;self.fail=0;self.gamelevel=1;self.codes={};self.refs=0;self.clock=100;self.partshow=[]
 def run(self,n,args=(),obj=None):
  # Explicit external boundaries. No test calls the real game or modifies saves.
  if n=='KR_Flag':return self.g[229][args[0]]
  if n=='KR_Poke':self.g[229][args[0]]=args[1];return
  if n=='KR_InitOptions':return
  if n=='KR_SaveOptions':self.saves+=1;return
  if n=='L_Party::GetNumberOfPersons':return len(self.g[253])
  if n=='KR_LootHasLivingParty':return int(self.living)
  if n=='L_DungeonManager::GetStartDungeonId':return self.start
  if n=='L_DungeonManager::GetDungeonBaseId':return self.base
  if n=='L_Calendar::GetRemainTime':return self.rem
  if n=='L_GameLevel::Get':return self.gamelevel
  if n=='KR_SweepConfirm' and not getattr(self,'real_dialog',False):self.modal();return int(self.confirm)
  if n=='KR_SweepReport' and not getattr(self,'real_dialog',False):self.report.append(args[0]);return
  if getattr(self,'real_dialog',False):
   if n in ['■選択ダイアログ／タイトル設定','■選択ダイアログ／横項目数','■選択ダイアログ／選択肢追加','■選択ダイアログ／クリック制限／全体']:
    assert self.g[GLOBALS['Flags']]['lock'];self.trace.append((n,args));return
   if n=='■選択ダイアログ／実行':assert self.g[GLOBALS['Flags']]['lock'];return self.choice
   if n=='AFL_Parts_GetActiveLayer':return 3
   if n=='AFL_Parts_AddLayer':self.trace.append('new_layer');return 6
   if n=='AFL_Parts_SetActiveLayer':assert args==[3];self.trace.append('restore_layer');return 1
   if n=='AFL_Parts_EraseLayer':assert args==[6];self.trace.append('erase_layer');return
   if n=='Ａ＿全表示':return
   if n in ['C_UserInputManager::IsClickCancel','C_UserInputManager::IsClickEnter']:return 0
   if n=='AFL_View_Update':assert self.g[GLOBALS['Flags']]['lock'];self.clock+=100;return
  if n=='KR_Time':return self.clock
  if n=='KR_NoticeStat':return self.g[250][self.g[253][args[0]]-1][[1,4,5,6][args[1]]] if args[0]<len(self.g[253]) else 0
  if n=='KR_NoticeName':return encode(['이즈미','쿄카','마나미'][args[0]]).decode('cp932')
  if n=='KR_NoticeTotal':return sum(5*(i+1)*(i+2) for i in range(1,args[0]))+args[1]
  if n=='L_StatusFace::UpdateAll':self.trace.append('update');return
  if n=='AFL_Parts_EndWaitForClick':self.trace.append(('click',args[0]));return
  if n=='L_BattleIncome::Clear':self.g[198].clear();return 1
  if n=='L_DungeonInfo::GetBattleMonsterPlacement':
   self.trace.append('placement');args[2][:]=[self.run('KR_SweepRand',[9]) for _ in range(3)]+[0]*6;return 1
  if n=='KR_LootMonsterById':
   if args[2]:self.g[198].append(args[0])
   return 1
  if n=='L_BattleIncome::Settle':
   assert self.run('KR_SweepActive') and args[0]==2026091500
   self.settles+=1;self.trace.append('settle');self.g[196][1][self.settles%99]=1
   for id in self.g[253]:
    a=self.g[250][id-1]
    if a[1]<99:self.run('KR_SweepAddExp',[a,900])
    a[5]=min(99999,a[5]+50);a[6]=min(999999,a[6]+100)
   return int(self.settles!=self.fail)
  if n=='L_TreasureBox::Open':
   assert self.run('KR_SweepActive');self.chests+=1;self.trace.append('chest')
   self.g[250][0][6]=min(999999,self.g[250][0][6]+70)
   self.g[230][1][3]=1;self.g[230][1][4]=min(99,self.g[230][1][4]+1)
   e=self.run('KR_SweepEquip',[2]);e[3]=1;e[4]=min(99,e[4]+1)
   self.g[236][0][2][3][:]=[1,min(99,self.g[236][0][2][3][1]+1)];return
  f=FS[n];vs=f['arguments']+f['variables'];li={v['name']:i for i,v in enumerate(vs)}
  def ix(s):return li[json.loads(s) if s.startswith('"') else s]
  loc={i:([] if v['type'][0] in (79,80) else '' if v['type'][0]==12 else -1 if v['type'][0] in(13,21) else 0) for i,v in enumerate(vs)};loc.update(enumerate(args));st=[]
  if f['index'] not in self.codes:
   p=O/f'built_{f["index"]}.jam'
   if not p.exists():p=O/f'original_{f["index"]}.jam'
   ops=[];labels={}
   for line in p.read_text(encoding='utf8').splitlines():
    l=line.strip()
    if not l or l.startswith((';','FUNC','ENDFUNC','EOF')):continue
    if l.endswith(':'):labels[l[:-1]]=len(ops)
    else:ops.append(l.split(maxsplit=1))
   self.codes[f['index']]=(ops,labels)
  ops,labels=self.codes[f['index']];pc=steps=0
  while pc<len(ops):
   steps+=1;assert steps<2000000,(n,pc);op,*a=ops[pc];a=a[0] if a else '';pc+=1
   if op=='PUSH':st.append(int(a,0))
   elif op=='PUSHLOCALPAGE':st.append(loc)
   elif op=='PUSHGLOBALPAGE':st.append(self.g)
   elif op=='PUSHSTRUCTPAGE':assert obj is not None;st.append(obj)
   elif op=='.LOCALREF':st.append(loc[ix(a)])
   elif op=='.GLOBALREF':st.append(self.g[GLOBALS[a]])
   elif op=='.STRUCTREF':
    struct,member=a.split(' ',1);members=next(s for s in M['structures'] if s['name']==struct)['members'];st.append(obj[next(i for i,m in enumerate(members) if m['name']==member)])
   elif op=='.STRUCTASSIGN':
    struct,member,v=a.split(' ');members=next(s for s in M['structures'] if s['name']==struct)['members'];obj[next(i for i,m in enumerate(members) if m['name']==member)]=int(v)
   elif op in ('.LOCALASSIGN','.LOCALPLUSA'):
    k,v=a.rsplit(' ',1);loc[ix(k)]=(loc[ix(k)] if op.endswith('PLUSA') else 0)+int(v)
   elif op in ('.LOCALINC2','.LOCALINC3','.LOCALDEC2'):
    loc[ix(a)]+=(-1 if op=='.LOCALDEC2' else 1)
   elif op=='.LOCALCREATE':k,typ=a.split(' ',1);assert typ=='C_MessageDialog';loc[ix(k)]={0:-1,1:0,2:-1,3:0}
   elif op=='S_PUSH':st.append(json.loads(a))
   elif op=='.S_LOCALASSIGN':k,v=a.split(' ',1);loc[ix(k)]=json.loads(v)
   elif op=='A_REF':st[-1]=copy.deepcopy(st[-1]) if isinstance(st[-1],list) else st[-1]
   elif op=='X_DUP':st.extend(st[-int(a):])
   elif op=='X_MOV':
    x,y=map(int,a.split());st[-x:]=st[-x:][-y:]+st[-x:][:-y]
   elif op=='X_REF':
    k=st.pop();p=st.pop();st.extend(p[k+i] for i in range(int(a)))
   elif op in ('X_ASSIGN','S_ASSIGN'):
    size=int(a or 1);vals=st[-size:];del st[-size:];k=st.pop();p=st.pop()
    for i,v in enumerate(vals):p[k+i]=v
    st.extend(vals)
   elif op=='X_A_INIT':
    count=st.pop();k=st.pop();p=st.pop();p[k]=[0]*count;st.append(p[k])
   elif op=='X_A_SIZE':st.append(len(st.pop()))
   elif op in ('PLUSA','MINUSA'):
    v=st.pop();k=st.pop();p=st.pop();p[k]=i32(p[k]+(v if op=='PLUSA' else -v));st.append(p[k])
   elif op in ('POP','DELETE','SP_INC'):st.pop()
   elif op=='S_MOD':
    v=st.pop();s=st.pop();z=re.search('%[sd]',s);assert z;st.append(s[:z.start()]+str(v)+s[z.end():])
   elif op=='NOT':st.append(int(not st.pop()))
   elif op in ('IFZ','IFNZ'):
    if bool(st.pop())==(op=='IFNZ'):pc=labels[a]
   elif op=='JUMP':pc=labels[a]
   elif op=='CALLFUNC':
    ff=FS[a];c=len(ff['arguments']);aa=st[-c:] if c else []
    if c:del st[-c:]
    v=self.run(a,aa)
    if ff['return-type'][0]!=0:st.append(v)
   elif op=='CALLMETHOD':
    c=int(a);aa=st[-c:] if c else []
    if c:del st[-c:]
    mid=st.pop();owner=st.pop();v=self.method(mid,owner,aa)
    if M['functions'][mid]['return-type'][0]!=0:st.append(v)
   elif op=='CALLHLL':
    lib,call,typ=a.split();assert lib=='Array',a
    if call=='Numof':st.append(len(st.pop()))
    elif call in ('Alloc','Realloc'):size=st.pop();arr=st.pop();arr[:]=[0]*size
    elif call=='PushBack':v=st.pop();arr=st.pop();arr.append(v)
    else:raise AssertionError(a)
   elif op in ['ADD','SUB','MUL','DIV','MOD','LT','LTE','GT','GTE','NOTE','EQUALE','S_ADD']:
    b=st.pop();v=st.pop()
    if op=='EQUALE':z=int(eq(v,b))
    elif op=='NOTE':z=int(not eq(v,b))
    elif op=='S_ADD':z=v+b
    else:z={'ADD':lambda:v+b,'SUB':lambda:v-b,'MUL':lambda:v*b,'DIV':lambda:int(v/b),'MOD':lambda:v%b,'LT':lambda:int(v<b),'LTE':lambda:int(v<=b),'GT':lambda:int(v>b),'GTE':lambda:int(v>=b)}[op]();z=i32(z)
    st.append(z)
   elif op=='RETURN':
    expected=int(f['return-type'][0]!=0);assert len(st)==expected,(n,'unbalanced',st);return st.pop() if expected else None
   else:raise AssertionError((n,pc,op,a))
  raise AssertionError(('no return',n))
 def method(self,mid,obj,args):
  if mid==28622:return self.map
  if mid==27042:return obj[1]
  if mid==26518:return int(self.training)
  if mid==26512:return int(obj['lock'])
  if mid==26514:obj['lock']=bool(args[0]);return
  if mid==27778:self.report.append(args[0]);return
  if mid==26479:return obj
  if mid==26450:return obj['month']
  if mid==26453:return obj['day']
  if mid==28650:
   assert args==[self.rem] and obj is self.scene;self.rem=0;self.trace.append('consume');return 1
  if mid in [26668,26756]:return obj[1 if mid==26668 else 2]
  if mid in [27303,27334]:return self.run(next(n for n,f in FS.items() if f['index']==mid),args,obj)
  if mid==27407:return # native equipment formula is outside this fixture
  raise AssertionError(('method',mid,args))

def main():
 results={};v=VM();allowed=[i for i in range(-1,10001) if v.run('KR_SweepAllowed',[i])];assert len(allowed)==80
 results['scope_ids_checked']=10002;results['allowed_ids']=allowed
 for i in [-1,0,1,999,1000,1011,1111,1201,1999,2511,2601,9999]:assert not v.run('KR_SweepAllowed',[i])
 for count in [1,2,3]:
  v=VM();v.g[253]=list(range(1,count+1));assert v.run('KR_SweepSceneOK',[v.scene]);assert v.run('KR_SweepPreflight',[1001])
 cases=[lambda v:setattr(v,'training',False),lambda v:setattr(v,'rem',0),lambda v:setattr(v,'rem',1001),lambda v:setattr(v,'start',401),lambda v:setattr(v,'base',2000),lambda v:setattr(v,'map',1201),lambda v:v.scene.update({4:{}}),lambda v:v.scene.update({6:-1}),lambda v:v.scene[7].append(1),lambda v:v.g[198].append(1),lambda v:setattr(v,'living',False)]
 for mutate in cases:v=VM();mutate(v);assert not v.run('KR_SweepSceneOK',[v.scene])
 results['scope_negative_fixtures']=len(cases)
 for mutate in [lambda v:v.g[250].pop(),lambda v:v.g[250][0].__setitem__(1,0),lambda v:v.g[230].pop(),lambda v:v.g[231].clear(),lambda v:v.g[236][0][2].pop(),lambda v:v.g[250][0].__setitem__(4,2000000000)]:
  v=VM();mutate(v);assert not v.run('KR_SweepPreflight',[1001])
 results['preflight_negative_fixtures']=6
 v=VM();before=copy.deepcopy(v.g);data=[];assert v.run('KR_SweepState',[data,0]);assert len(data)>600
 # Change every covered scalar, including all nonparty characters and disclosure flags.
 for i in range(5):v.g[[201,202,203,204,206][i]]+=1
 v.g[253].reverse()
 for a in v.g[250]:
  for i,x in enumerate(a):
   if isinstance(x,list):a[i][:]=[777]*len(x)
   else:a[i]+=10
 for g in [230,231]:
  for a in v.g[g]:a[3]=1;a[4]=99
 for row in v.g[236][0]:
  for a in row:a[:]=[1,99]
 v.g[196][1][:]=[1]*99
 assert v.run('KR_SweepState',[data,1]) and v.g==before;results['snapshot_roundtrip_scalars']=len(data)
 for seed in [0,1,100,32767]:
  v=VM();v.g[229][99]=-seed-1;expected=seed
  for i in range(1000):expected=(expected*25173+13849)%32768;assert v.run('KR_SweepRand',[17])==expected%17+1
 results['private_rng_steps']=4000
 for lv in [1,2,10,40,98,99]:
  for amount in [0,1,59,100,10000,1000000]:
   v=VM();a=v.g[250][0];a[1]=lv;ex=a[4]+amount;end=lv
   while end<99 and ex>=5*(end+1)*(end+2):ex-=5*(end+1)*(end+2);end+=1
   v.run('KR_SweepAddExp',[a,amount]);assert (a[1],a[4])==(end,ex)
 results['native_exp_boundary_fixtures']=36
 for r in [1,39,40,41,199,200,201,399,400,999,1000]:
  v=VM();v.rem=r;assert v.run('KR_SweepExecute',[v.scene]);assert v.settles==r//40 and v.chests==r//200 and v.rem==0 and v.saves==0 and v.g[229][99]==20260916
  assert len(v.report)==1 and '소탕 결과' in decode(v.report[0].encode('cp932'));assert v.trace.count('consume')==1
  assert not v.run('KR_SweepExecute',[v.scene])
 results['successful_budget_boundaries']=11;results['duplicate_payout_blocked']=11
 for failure in [1,2,5,6,10,20,25]:
  v=VM();v.fail=failure;before=copy.deepcopy(v.g);assert not v.run('KR_SweepExecute',[v.scene]);assert v.g==before and v.rem==1000 and v.saves==0
 results['midpayout_rollback_fixtures']=7
 v=VM();v.confirm=False;before=copy.deepcopy(v.g);assert not v.run('KR_SweepExecute',[v.scene]);assert v.g==before and not v.trace and v.rem==1000
 results['cancel_zero_side_effect']=True
 for mutation in [lambda v:setattr(v,'map',1002),lambda v:setattr(v,'rem',999),lambda v:v.scene.update({6:copy.deepcopy(v.scene[6])}),lambda v:v.g[250][0].__setitem__(4,100),lambda v:v.g[229].__setitem__(99,0),lambda v:v.g[GLOBALS['Flags']].__setitem__('day',30)]:
  v=VM();v.modal=lambda:mutation(v);assert not v.run('KR_SweepExecute',[v.scene]);assert v.settles==0 and v.saves==0
 results['postmodal_stale_guards']=6
 for lock in [False,True]:
  for choice in [-1,12,11,503,2026091601]:
   v=VM();v.real_dialog=True;v.choice=choice;v.g[GLOBALS['Flags']]['lock']=lock
   assert v.run('KR_SweepConfirm',[1000])==int(choice==11);assert v.g[GLOBALS['Flags']]['lock']==lock
  v=VM();v.real_dialog=True;v.g[GLOBALS['Flags']]['lock']=lock;v.run('KR_SweepReport',['fixture'])
  assert v.clock==6100 and v.g[GLOBALS['Flags']]['lock']==lock and v.trace==['new_layer','restore_layer','erase_layer']
 results['modal_lock_restore_cases']=10;results['timed_dialog_cleanup_cases']=2
 ev=json.loads((O/'build_evidence.json').read_text());assert all(sha(O/n)==h for n,h in ev['files'].items())
 savej(O/'verification.json',dict(status='SWEEP_STATIC_PASS_NATIVE_PENDING',files=ev['files'],compiled_fixture_results=results,native_gameplay_verified=False,fixture_boundaries='Native reward settlement, chest tables, UI and HLL are mocked. Quiet EXP executes original need/level JAM, equipment cap update is an explicit stub. Snapshot/scope/private RNG/control flow are actual compiled instructions.'))
 print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
