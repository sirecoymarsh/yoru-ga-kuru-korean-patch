"""Run actual candidate JAM, with explicit native data/animation boundary fixtures.
No game process, RNG, saves or native runtime benchmark is claimed by these tests.
"""
from pathlib import Path
import copy,json,re,random
import verify_autoequip_20260917 as old
from cheat_support_20260915 import R,sha,read_meta,savej,cmd
from build_route_perf_20260915 import symbol
from build_remaster_multiplier_20260915 import ex,part,child,ss,setlist,read_afa3
from build_mod_tab_20260915 import remove,coords
O=R/'staging/smart_auto_20260922';M=read_meta(O/'candidate_meta.json');FS={};seen={}
for f in M['functions']:
 for v in f['arguments']+f['variables']:
  if any(0xdc80<=ord(c)<=0xdcff for c in v['name']):v['name']=v['name'].encode('utf8','surrogateescape').decode('cp932')
for f in M['functions']:
 n=symbol(M,f['index']);j=seen.get(n,0);seen[n]=j+1;FS[n+(f'#{j}' if j else '')]=f
GLOBALS={g['name']:i for i,g in enumerate(M['globals'])}
src=old.src.replace("Path('autoequip_probe_20260917')/f'{f[\"index\"]}.jam'","O/f'original_{f[\"index\"]}.jam'")
src=src.replace("elif op=='AND':b=st.pop();st.append(st.pop() & b)","elif op=='AND':b=st.pop();st.append(st.pop() & b)\n  elif op=='INV':st.append(-st.pop())")
ns=dict(vars(old.base),O=O,M=M,FS=FS,GLOBALS=GLOBALS);exec(compile(src,'<smart auto compiled JAM fixture>','exec'),ns);execute=ns['run']

def weapon(ident=0,power=30,attribute=4,area=1,cost=0,repeat=1,delay=3,physical=False):
 w=[0]*28;w[0]=ident;w[1]='fixture';w[11]=1 if ident>0 else 0;w[12]=power;w[13]=100;w[17]=area;w[18]=3;w[19]=repeat;w[20]=cost;w[21]=w[22]=delay;w[23]=0 if physical else 1;w[25]=attribute;w[26]=[0]*5;w[27]=[];return w
def enemy(pos=0,hp=500):
 m=[0]*22;m[3]=10;m[4]=hp;m[5]=100;m[13:17]=[3]*4;m[17]=1
 e=[0]*15;e[0]=m;e[1]=pos%3;e[2]=pos//3;e[3]=hp;e[14]=900+pos;return e

class VM(old.VM):
 def __init__(self):
  super().__init__();self.codes={};self.g[229][79]=20260922;self.g[229][82]=1
  self.weapons={0:weapon()};self.crafted={};self.techniques=[];self.commits=[];self.bars=[];self.queries=0;self.fail_commit=False
  self.areas={1:[int(i==12) for i in range(25)],2:[1]*25}
  self.pa=self.g[250][1];self.pa[25]=[0]*100;self.pa[13:17]=[0]*4;self.pa[1]=10;self.pa[2]=100;self.pa[3]=100
  self.pf=[0]*10;self.battle=[0]*10;self.enemies=[enemy()]+[-1]*8
 def run(self,n,args=(),obj=None):
  if n=='L_Weapon::At':return self.weapons.get(args[0],-1)
  if n=='LAbility::GetTechnique':assert args[1]==self.pa[0];args[0][:]=self.techniques;return
  if n=='L_TargetArea::At':return [self.areas[args[0]]] if args[0] in self.areas else -1
  return execute(self,n,args,obj)
 def create(self,typ):
  st=next(s for s in M['structures'] if s['name']==typ)
  x=[[] if v['type'][0] in [79,80] else '' if v['type'][0]==12 else -1 if v['type'][0] in [13,21,89] else 0 for v in st['members']]
  if typ=='C_Weapon':x[26]=[0]*5
  return x
 def method(self,mid,owner,args):
  if mid in [27332,27335,27336,27358]:return owner[{27332:0,27335:1,27336:3,27358:23}[mid]]
  if mid==27359:return 0
  if mid==27316:return owner[25][args[0]] if 0<=args[0]<len(owner[25]) else 0
  if mid==27338:return owner[2]*(100+10*self.method(27316,owner,[35]))//100
  if mid==26894:owner[:]=copy.deepcopy(args[0]);return
  if mid==26481:return self.crafted
  if mid==26723:return owner.get(args[0],-1)
  if mid==26708:args[0][:]=copy.deepcopy(owner);return 1
  if mid==29236:
   if self.fail_commit:return 0
   self.commits.append(args[0]);self.weapons[0]=copy.deepcopy(self.crafted[args[0]]);owner[8]=1;return 1
  if mid==29469:return owner[1]+owner[2]*3
  if mid in [29470,29471]:self.bars.append((mid,args[0]));return
  if mid==29483:
   attribute,monster=args;kind=monster[{0:16,1:13,2:14,3:15}[attribute]] if attribute in [0,1,2,3] else 3
   return {1:400,2:150,3:100,4:50,5:0}.get(kind,100)
  if mid==29486:
   w,m=args;effects=[w[26][ix] for bit,ix in [(1,1),(2,2),(4,3),(8,4),(16,0)] if m[17]&bit]
   return 150 if 1 in effects else 50 if 2 in effects else 100
  if mid in [27350,27352,27353,27354,27355,27356,27357]:return self.run(symbol(M,mid),args,owner)
  raise AssertionError(('unexpected native call',mid,owner,args))
 def decide(self):return self.run('KR_SmartRun',[self.battle,self.pa,self.pf,self.enemies])
 def evaluate(self,key):
  probe=self.create('C_Ability');self.run('KR_AutoCopyAbility',[probe,self.pa]);best=[0,-1,-1,0,0]
  before=copy.deepcopy((self.pa,self.weapons,self.enemies,self.crafted))
  self.run('KR_SmartEvaluate',[self.pa,probe,self.weapons[0],key,self.enemies,best]);assert before==(self.pa,self.weapons,self.enemies,self.crafted)
  return best

def prepare():
 rt=Path(json.loads((O/'source_pointer.json').read_text())['runtime'])
 names=['KR_AutoCount','KR_AutoValidAbility','KR_AutoCopyAbility','KR_AutoBound','KR_AutoWeaponSkill','KR_AutoW']
 names += [symbol(M,i) for i in [27350,27352,27353,27354,27355,27356,27357,27297]]
 for name in names:cmd('ain','dump','--function',name,'-o',O/f'original_{FS[name]["index"]}.jam',rt/'NightRemaster.ain')

def test():
 results={};v=VM();v.g[229][79]=0;flags=copy.deepcopy(v.g[229]);before=copy.deepcopy((v.pa,v.pf,v.weapons));assert not v.decide();assert before==(v.pa,v.pf,v.weapons)
 v.run('KR_SetSmartAuto',[True]);assert v.g[229][79]==20260922 and v.saves==1;v.run('KR_SetSmartAuto',[True]);assert v.saves==1
 v.run('KR_SetSmartAuto',[False]);assert v.saves==2 and v.g[229]==flags;results['default_off_toggle_idempotent_story82_preserved']=True
 v=VM();assert v.decide();assert v.pf[3]==0 and v.pf[6]==0 and v.pf[9]==900 and len(v.bars)==2
 for typ in [2,3]:
  v=VM();v.battle[5]=typ;before=copy.deepcopy(v.pf);assert not v.decide() and v.pf==before
 results['vanilla_fallback_special_event_types']=True
 v=VM();v.weapons[251]=weapon(251,40,1);v.weapons[252]=weapon(252,40,2);v.techniques=[251,252];v.enemies[0][0][13]=5;v.enemies[0][0][14]=2
 assert v.decide() and v.pf[3:5]==[1,252];results['weakness_immunity_selection']=True
 v=VM();v.weapons[251]=weapon(251,800,cost=81);v.techniques=[251];assert v.decide() and v.pf[3]==0
 v=VM();v.weapons[251]=weapon(251,800,cost=50);v.pa[3]=70;v.techniques=[251];assert v.decide() and v.pf[4]==251
 v=VM();v.weapons[0]=weapon(cost=11,repeat=2);v.pa[3]=40;assert v.evaluate(-1)[2]==-1
 v=VM();v.weapons[251]=weapon(251,100,cost=30);v.weapons[251][9]=10;v.pa[3]=50;assert v.evaluate(251)[2]==-1
 v=VM();v.pa[3]=1;assert v.decide();results['HP_floor_and_basic_repeat_EX_scaling']=True
 v=VM();v.enemies=[enemy(i) for i in range(9)];v.weapons[251]=weapon(251,20,area=2);v.techniques=[251];assert v.decide() and v.pf[4]==251;results['AOE_coverage']=True
 v=VM();v.enemies=[enemy(0,30),enemy(1,500)]+[-1]*7;assert v.decide() and v.pf[6]==0
 v=VM();v.enemies=[enemy(0,500),enemy(1,30)]+[-1]*7;assert v.decide() and v.pf[6]==1;results['finish_and_no_first_index_bias']=True
 v=VM();v.enemies=[enemy(8)]+[-1]*8;v.weapons[0][18]=2;assert not v.decide();v.weapons[0][18]=3;assert v.decide() and v.pf[6]==0 and v.pf[9]==908
 v=VM();v.enemies=[-1,enemy(1),enemy(2)]+[-1]*6;v.enemies[1][12]=1;assert v.decide() and v.pf[6]==2
 results['range_dead_null_array_index_fixedID']=True
 v=VM();v.weapons[251]=weapon(251,100,delay=8);v.weapons[252]=weapon(252,80,delay=1);v.techniques=[251,252];assert v.decide() and v.pf[4]==252
 v=VM();v.weapons[251]=weapon(251,100);v.weapons[251][11]=2;v.techniques=[251];assert v.decide() and v.pf[3]==0;results['speed_and_no_heal_buff_consumption']=True
 # Real crafted object, rather than base template; preview skill tables stay detached.
 v=VM();v.pa[0]=1;v.pa[25]=[0]*20;v.crafted[103]=weapon(0,20);v.crafted[103][27]=[41]*20+[76,78,92];v.techniques=[103]
 b=v.evaluate(103);assert b[2]==0 and len(v.pa[25])==20 and v.weapons[0][12]==30
 assert v.decide() and v.commits==[103] and v.pf[3]==0 and v.battle[8]==1 and v.pf[1]==1
 v=VM();v.pa[0]=1;v.crafted[3]=weapon(0,200);v.techniques=[3];v.fail_commit=True;before=copy.deepcopy((v.pa,v.pf,v.weapons));assert not v.decide() and before==(v.pa,v.pf,v.weapons)
 results['crafted_stats_passives_last_commit_failure']=True
 v=VM();v.techniques=list(range(50));assert not v.decide();v=VM();v.enemies=[];assert not v.decide();v=VM();v.weapons[0][17]=999;assert not v.decide()
 results['candidate_array_mask_bounds']=True
 # Formula known-vector: 100 power + 20 ability, +20% attack =144, not140.
 v=VM();v.pa[13]=v.pa[16]=100;v.pa[25][41]=2;w=weapon(power=100);assert v.run('KR_SmartDamage',[v.pa,w,v.enemies[0][0]])==144
 v=VM();w=weapon(power=1,physical=True);assert v.run('KR_SmartDamage',[v.pa,w,v.enemies[0][0]])==1
 v.weapons[0]=w;v.enemies=[enemy(0,500),enemy(1,1)]+[-1]*7;assert v.decide() and v.pf[6]==1
 # Native hit-grade distribution is integrated analytically without advancing RNG.
 rng=random.Random(20260922);cases=0
 for _ in range(100):
  v=VM();w=weapon(power=rng.randint(1,120),physical=True);w[13]=rng.randint(0,400);e=enemy();e[0][5]=rng.randint(1,300);e[0][6]=rng.randint(0,80)
  result=v.run('KR_SmartDamage',[v.pa,w,e[0]]);alpha=min(800,max(0,w[13]*100//e[0][5]));prob=1.0;expected=0
  for grade in range(6):
   nxt=prob*min(alpha,100)/100 if grade<5 else 0
   de=e[0][6];de=de*90//100 if grade==2 else de//2 if grade==3 else 0 if grade>=4 else de
   dmg=0 if grade==0 else max(1,w[12]*(2 if grade==5 else 1)-de)
   expected+=dmg*(prob-nxt);prob=nxt;alpha//=2
  assert abs(result-expected)<=1.5,(result,expected);cases+=1
 results['damage_distribution_known_vectors']=cases+3
 # Reverse allowed PACT edits must recover the exact source payload.
 d=ex.decode_ex(O/'pact_185_smart_auto.pactex');before=ex.decode_ex(O/'original_185.pactex');remove(d.blocks[2].payload.children[0],'KR_SmartAutoToggle')
 for name in ['KR_CheatQuick','KR_CheatRoute','KR_CheatLoot','KR_CheatSweep']:setlist(part(d,name),'座標',coords(part(before,name)))
 assert d.serialize_payload()==before.serialize_payload();results['PACT_reverse_exact']=True
 # Original automatic fallback and getter/setter bodies survive exactly after prefixes.
 from build_instant_loot_20260915 import clean
 for fid in [29242,29817,29818]:
  original=clean((O/f'original_{fid}.jam').read_text(encoding='utf8'),symbol(M,fid))
  patch=(O/'smart_auto_patch.jam').read_text(encoding='utf8');body=original.split(f'FUNC {fid}\n',1)[1]
  assert body in patch,fid
 results['original_hook_bodies_exact']=True
 ev=json.loads((O/'build_evidence.json').read_text());assert all(sha(O/n)==h for n,h in ev['files'].items())
 report=dict(status='SMART_AUTO_COMPILED_PASS',files=ev['files'],tests=results,native_gameplay_verified=False,boundaries='Native table lookup, Copy, crafted RestoreWeapon, attribute/shape query, ChangePlayerWeapon, display bars; compiled decision/formula/control/bridges executed')
 savej(O/'verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':prepare();test()
