"""Executes candidate JAM control/transaction logic with explicit native/GUI fixtures.
Not native gameplay or a performance measurement. Does not launch/touch the game.
"""
from pathlib import Path
import copy,inspect,json,re,textwrap,collections
import verify_dungeon_sweep_20260916 as base
from cheat_support_20260915 import R,sha,read_meta,savej
from build_route_perf_20260915 import symbol
from build_remaster_multiplier_20260915 import encode
O=R/'staging/autoequip_20260917';M=read_meta(O/'candidate_meta.json');FS={};seen={}
for f in M['functions']:
 for v in f['arguments']+f['variables']:
  if any(0xdc80<=ord(c)<=0xdcff for c in v['name']):v['name']=v['name'].encode('utf8','surrogateescape').decode('cp932')
for f in M['functions']:
 n=symbol(M,f['index']);j=seen.get(n,0);seen[n]=j+1;FS[n+(f'#{j}' if j else '')]=f
GLOBALS={g['name']:i for i,g in enumerate(M['globals'])}
src=textwrap.dedent(inspect.getsource(base.VM.run))
def change(a,b):
 global src
 assert a in src,a;src=src.replace(a,b)
change("li={v['name']:i for i,v in enumerate(vs)}", "li={};seen={}\n for i,v in enumerate(vs):\n  key=v['name'];j=seen.get(key,0);seen[key]=j+1;li[key+(f'#{j}' if j else '')]=i")
change("if not p.exists():p=O/f'original_{f[\"index\"]}.jam'", "if not p.exists():p=Path('autoequip_probe_20260917')/f'{f[\"index\"]}.jam'")
change("elif op=='.LOCALCREATE':k,typ=a.split(' ',1);assert typ=='C_MessageDialog';loc[ix(k)]={0:-1,1:0,2:-1,3:0}", "elif op=='.LOCALCREATE':\n   k,typ=a.split(' ',1);loc[ix(k)]=self.create(typ)\n  elif op=='.LOCALDELETE':loc[ix(a)]=-1")
change("elif op in ('POP','DELETE','SP_INC'):st.pop()", "elif op in ('POP','DELETE','SP_INC'):st.pop()\n  elif op in ('INC','DEC'):\n   k=st.pop();p=st.pop();p[k]+=(1 if op=='INC' else -1)\n  elif op=='AND':b=st.pop();st.append(st.pop() & b)")
ns=dict(vars(base),O=O,M=M,FS=FS,GLOBALS=GLOBALS);exec(compile(src,'<exact autoequip candidate JAM interpreter>','exec'),ns)
execute=ns['run']
def proxy(s):return encode(s).decode('cp932')

class VM(base.VM):
 def __init__(self):
  super().__init__();self.codes={};self.g[229][83]=20260917
  self.g[231]=[[101+i,1,proxy(name),1,1,skills] for i,(name,skills) in enumerate([('공격 장비',[41]),('방어 장비',[44]),('함정 도구',[10]),('회복 장비',[12]),('보물 장비',[13]),('민첩 장비',[76])])]
  self.g[231].append([999,0,proxy('고정 장비'),1,0,[35]])
  self.weapon=[0]*28;self.weapon[1]=proxy('현재 무기');self.weapon[12]=5;self.weapon[13]=20;self.weapon[19]=1;self.weapon[21]=4;self.weapon[22]=4;self.weapon[26]=[];self.weapon[27]=[]
  self.menu=[];self.menus=[];self.trap=False;self.route=False;self.full=False;self.confirm_kind='accept';self.native_confirm_calls=0;self.creations=0;self.fail_equip_at=0;self.equips=0;self.preview_mutation=None;self.allow_cost=True
  self.scene={};self.view={};self.info=[];self.g[250][0][6]=500
 def create(self,typ):
  st=next(s for s in M['structures'] if s['name']==typ);x=[]
  for v in st['members']:
   t=v['type'][0];x.append([] if t in [79,80] else '' if t==12 else -1 if t in [13,21,89] else 0)
  if typ=='fire_amulet_t':x[0]=[[False,-1,-1] for _ in range(3)]
  return x
 def state(self):return copy.deepcopy({k:self.g[k] for k in [229,250,231,236]})
 def snapshot(self):
  out=[]
  def flat(x):
   if isinstance(x,(list,tuple)):
    out.append(-987654);out.append(len(x))
    for v in x:flat(v)
   elif isinstance(x,int):out.append(x)
  for k in [229,250,231,236]:flat(self.g[k])
  return out
 def skill(self,owner,k):return owner[25][k] if k<len(owner[25]) else 0
 def run(self,n,args=(),obj=None):
  if n=='KR_GetTrap':return self.trap
  if n=='KR_GetRoute':return self.route
  if n=='KR_SweepState':assert not args[1];args[0][:]=self.snapshot();return 1
  if n=='KR_SweepItemName':return proxy(f'요소석{args[1]}')
  if n=='KR_AutoMenu':
   self.menus.append((args[0],list(args[1])));assert self.menu,(n,self.menus)
   result=self.menu.pop(0)
   if len(args[1])==2 and self.preview_mutation:self.preview_mutation(self)
   return result
  if n=='LAbility::At':return self.g[250][args[0]-1] if 1<=args[0]<=8 else -1
  if n=='L_EquipItem::At':return next((x for x in self.g[231] if x[0]==args[0]),-1)
  if n=='L_EquipItem::Numof':return len(self.g[231])
  if n=='L_Weapon::At':return self.weapon
  if n=='L_ElementStone::AddStone':
   c,r,delta=args;assert 0<=c<4 and 0<=r<10
   self.g[236][0][c][r][1]+=delta;assert self.g[236][0][c][r][1]>=0;return
  if n=='L_Weapon::CreateNewWeapon':
   self.creations+=1;amulet,weapon=args;assert all(h[0] for h in amulet[0]);slots=[h[1]*10+h[2] if h[1]>=0 else 99 for h in amulet[0]]
   weapon[:]=copy.deepcopy(self.weapon);weapon[1]=proxy('추천 무기');weapon[10]=10
   # Explicit native-query fixture: different base/side profiles, no live writes.
   weapon[12]=10+(10 if slots[0]==0 else 3 if slots[0]==10 else 0)+sum(3 for s in slots[1:] if s==0)
   weapon[14]=15 if slots[0]==10 else 0;weapon[27]=[10] if 20 in slots else [];return 1
  if n=='L_EquipItem::EquipItem':
   self.equips+=1
   if self.fail_equip_at and self.equips==self.fail_equip_at:return 0
  return execute(self,n,args,obj)
 def method(self,mid,owner,args):
  if mid==26481:return [self.full]
  if mid==26717:return owner[0]
  if mid in [26750,26753,26756,26762,26810]:return owner[{26750:0,26753:1,26756:2,26762:4,26810:1}[mid]]
  if mid==26764:owner[4]=args[0];return
  if mid==27361:return owner[22][args[0]]
  if mid==27363:old=owner[22][args[0]];owner[22][args[0]]=args[1];return old
  if mid==27315:
   owner[25]=[0]*100
   for ident in owner[22]:
    item=self.run('L_EquipItem::At',[ident])
    if item!=-1:
     for k in item[5]:owner[25][k]+=1
   return 1
  if mid==27316:return self.skill(owner,args[0])
  if mid==27359:return 0
  if mid in [27356,27357]:return max(1,args[0]-(self.skill(owner,76) if mid==27356 else 0))
  if mid==27338:return owner[2]*(100+10*self.skill(owner,35))//100
  if mid in [27325,27326,27327,27328,27329]:
   field={27325:41,27326:42,27327:43,27328:44,27329:45}[mid];return [10,0,10*self.skill(owner,field)]
  if mid==27297:return sum(owner)
  if mid==26895:
   args[0][:]=[self.allow_cost and owner[10]<=self.g[250][0][6]]+[True]*4;return all(args[0])
  if mid==28587:
   reserved,pos=args
   for i in range(3):
    if reserved[i]>=0 and (pos<0 or pos==i):
     if reserved[i]!=99:self.run('L_ElementStone::AddStone',[reserved[i]//10,reserved[i]%10,1])
     reserved[i]=-1
   return
  if mid in [28527,28526,28514]:return
  if mid==28586:
   reserved,box,index,tutorial=args;assert not tutorial;self.native_confirm_calls+=1
   if self.confirm_kind=='early':return 0
   if self.confirm_kind=='accept':self.g[250][0][6]-=10
   self.method(28587,owner,[reserved,-1]);box[index]=0
   return int(self.confirm_kind=='accept')
  return super().method(mid,owner,args)

def test():
 results={};v=VM();before=v.state();v.run('KR_SetAutoEquip',[False]);assert v.g[229][83]==0
 assert all(v.g[229][i]==before[229][i] for i in range(101) if i!=83);v.run('KR_SetAutoEquip',[True]);assert v.g[229][83]==20260917;results['option_scope']=True
 v=VM();clone=v.create('C_Ability');v.run('KR_AutoCopyAbility',[clone,v.g[250][0]]);assert clone==v.g[250][0]
 for ix in [21,22,25]:assert clone[ix] is not v.g[250][0][ix];clone[ix][0]=123;assert clone[ix]!=v.g[250][0][ix]
 results['deep_copy_arrays']=3
 for profile in range(4):
  v=VM();before=v.state();v.menu=[profile+1,2];assert v.run('KR_AutoGearRun',[1]);assert v.equips>0
  assert v.g[250][1:]==before[250][1:]
  for x,y in zip(v.g[231],before[231]):assert x[4]+v.g[250][0][22].count(x[0])==y[4]+before[250][0][22].count(x[0])
  if profile==3:assert 103 in v.g[250][0][22]
 results['four_profiles_equip']=True
 for choices in [[9],[1,1]]:
  v=VM();before=v.state();v.menu=choices;assert not v.run('KR_AutoGearRun',[1]);assert v.state()==before and v.equips==0
 v=VM();v.g[250][0][22][0]=999;v.menu=[5,4,2];assert v.run('KR_AutoGearRun',[1]);assert v.g[250][0][22][0]==999
 v=VM();v.g[250][0][22][0]=101;v.g[231][0][4]=0;v.menu=[5,4,2];assert v.run('KR_AutoGearRun',[1]);assert v.g[250][0][22][0]==101
 v=VM();v.menu=[1,2,1];v.fail_equip_at=3;before=v.state();assert not v.run('KR_AutoGearRun',[1]);assert v.state()==before
 v=VM();v.menu=[1,2,1];v.preview_mutation=lambda vv:vv.g[231][0].__setitem__(4,0);assert not v.run('KR_AutoGearRun',[1]);assert v.equips==0 and v.g[231][0][4]==0
 v=VM();v.menu=[1,1]
 for it in v.g[231]:it[4]=0
 before=v.state();assert not v.run('KR_AutoGearRun',[1]);assert v.state()==before
 results['gear_cancel_lock_fixed_rollback_stale_empty']=True
 # A real native26781 swap, including stock=0 at start: all changed slots released first.
 v=VM();v.g[250][0][22]=[101,102,0,0];v.g[231][0][4]=v.g[231][1][4]=0
 backup=copy.deepcopy(v.g[250][0]);ids=[x[0] for x in v.g[231]];stock=[x[4] for x in v.g[231]]
 assert v.run('KR_AutoGearApply',[1,[102,101,0,0],[101,102,0,0],ids,stock,backup]);assert [x[4] for x in v.g[231]]==stock
 skills=[0]*100;skills[10]=1;v=VM();normal=v.run('KR_AutoUtility',[skills]);v.trap=True;assert v.run('KR_AutoUtility',[skills])<normal
 skills=[0]*100;skills[17]=1;normal=v.run('KR_AutoUtility',[skills]);v.route=True;assert v.run('KR_AutoUtility',[skills])<normal
 results['swap_and_redundant_utility']=True
 for profile in range(4):
  for kind in ['accept','cancel','early']:
   v=VM();v.confirm_kind=kind;v.menu=[profile+1,2];v.g[236][0][0][0][1]=3;v.g[236][0][1][0][1]=2;v.g[236][0][2][0][1]=1
   before=v.state();reserved=[-1]*3;pos=[0];result=v.run('KR_AutoStoneRun',[v.scene,v.view,reserved,pos,0])
   assert result==(kind=='accept');assert v.native_confirm_calls==1 and reserved==[-1]*3 and pos==[0]
   assert v.g[236]==before[236];assert v.g[250][0][6]==before[250][0][6]-(10 if kind=='accept' else 0)
   assert v.creations<=4000,v.creations
 results['stone_profiles_normal_cancel_early']=12
 for confirm in [False,True]:
  v=VM();v.g[236][0][0][0][1]=2;v.g[236][0][1][0][1]=1;reserved=[0,-1,-1];pos=[1];before=v.state();v.menu=[1,2 if confirm else 1]
  result=v.run('KR_AutoStoneRun',[v.scene,v.view,reserved,pos,0]);assert result==confirm
  if confirm:assert v.g[236][0][0][0][1]==before[236][0][0][0][1]+1 and pos==[0]
  else:assert v.state()==before and reserved==[0,-1,-1] and pos==[1]
 results['partial_reservation_cancel_apply']=True
 for reason in ['stock','money','capacity','off']:
  v=VM();v.menu=[1,1];v.g[236][0][0][0][1]=1
  if reason=='stock':v.g[236][0][0][0][1]=0;v.weapon[12]=1000
  if reason=='money':v.allow_cost=False
  if reason=='capacity':v.full=True;v.menu=[1]
  if reason=='off':v.g[229][83]=0;v.menu=[]
  before=v.state();reserved=[-1]*3;pos=[0];assert not v.run('KR_AutoStoneRun',[v.scene,v.view,reserved,pos,0]);assert v.native_confirm_calls==0 and v.state()==before
 results['negative_stone_conditions']=4
 for held,reserved,pos in [(100,[-1,-1,-1],0),(99,[0,-1,-1],1)]:
  v=VM();v.g[236][0][0][0][1]=held;before=v.state();box=[pos]
  assert not v.run('KR_AutoStoneRun',[v.scene,v.view,reserved,box,0]);assert v.state()==before and v.native_confirm_calls==0
 results['native_99_cap_rejections']=2
 ev=json.loads((O/'build_evidence.json').read_text());assert sha(O/'NightRemaster.ain')==ev['files']['NightRemaster.ain']
 output=dict(status='COMPILED_FIXTURES_PASS',results=results,files=ev['files'],native_boundary_fixtures=['GUI selection','native derived ability/query formulas','native craft confirmation','read-only snapshot'],native_equip_26781_executed=True,native_gameplay_verified=False)
 print(json.dumps(output,ensure_ascii=False,indent=2));savej(O/'verification.json',output)
if __name__=='__main__':test()
