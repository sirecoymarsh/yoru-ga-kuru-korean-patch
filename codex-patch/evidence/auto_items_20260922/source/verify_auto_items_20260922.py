"""Execute candidate auto-item JAM against explicit native object/UI boundaries."""
from pathlib import Path
import copy,json,re,struct
from cheat_support_20260915 import R,read_meta,savej,sha,cmd
from build_route_perf_20260915 import symbol
HERE=Path(__file__).resolve().parent;O=R/'staging/auto_items_20260922'
s=(HERE/'verify_smart_auto_20260922.py').read_text(encoding='utf8').replace("O=R/'staging/smart_auto_20260922'","O=R/'staging/auto_items_20260922'")
ns={'__name__':'auto_items_fixture','__file__':str(HERE/'verify_smart_auto_20260922.py')};exec(compile(s,ns['__file__'],'exec'),ns)
M=ns['M'];FS=ns['FS'];Base=ns['VM']
src=ns['src'].replace("elif op=='PUSHLOCALPAGE':st.append(loc)","elif op=='F_PUSH':st.append(float(a))\n  elif op=='FTOI':st.append(int(st.pop()))\n  elif op=='ITOF':st.append(float(st.pop()))\n  elif op in ['F_ADD','F_SUB','F_MUL','F_DIV']:\n   b=st.pop();v=st.pop();st.append({'F_ADD':lambda:v+b,'F_SUB':lambda:v-b,'F_MUL':lambda:v*b,'F_DIV':lambda:v/b}[op]())\n  elif op=='PUSHLOCALPAGE':st.append(loc)")
src=src.replace("int(st.pop())","int(as_float(st.pop()))").replace("b=st.pop();v=st.pop();st.append({'F_ADD'", "b=as_float(st.pop());v=as_float(st.pop());st.append({'F_ADD'")
ns['ns']['as_float']=lambda x:x if isinstance(x,float) else struct.unpack('<f',struct.pack('<I',x&0xffffffff))[0]
exec(compile(src,'<auto items candidate JAM>','exec'),ns['ns']);ns['execute']=ns['ns']['run']

class VM(Base):
 def __init__(self):
  super().__init__();self.party=self.g[250][:3];self.pa=self.party[0]
  for a in self.party:a[25]=[0]*100;a[2]=a[3]=100
  self.friends=[[i,0,0,-1,0,0,0,0,0,-1] for i in range(3)];self.pf=self.friends[0]
  self.items={i:[i,'','',1,8] for i in range(1,6)};self.stock_writes=[]
 def run(self,n,args=(),obj=None):
  if n=='L_ConsumeItem::At':return self.items.get(args[0],-1)
  if n=='L_Party::AbilityAt':return self.party[args[0]] if 0<=args[0]<len(self.party) else -1
  return super().run(n,args,obj)
 def method(self,mid,owner,args):
  if mid in [27301,27381,27382,27383,27384,27385,27386]:return self.run(symbol(M,mid),args,owner)
  if mid==26677:return owner[4]
  if mid==26679:self.stock_writes.append((owner[0],owner[4],args[0]));owner[4]=args[0];return
  return super().method(mid,owner,args)
 def enable(self):self.run('KR_ItemsSetEnabled',[True]);return self
 def attempt(self,actor=0):return self.run('KR_ItemsTry',[self.battle,self.party[actor],self.friends[actor],self.friends])
 def pending(self,target,item):return self.run('KR_ItemsPending',[self.friends,target,item])
 def need(self,target,item):return self.run('KR_ItemsNeed',[target,item])

def prepare():
 names=['KR_AutoValidAbility','KR_AutoBound','KR_AutoW','KR_SmartType']+[symbol(M,i) for i in [27301,27381,27382,27383,27384,27385,27386]]
 for name in names:cmd('ain','dump','--function',name,'-o',O/f'original_{FS[name]["index"]}.jam',O/'NightRemaster.ain')

def tests():
 r={};v=VM();before=copy.deepcopy((v.g,v.items,v.friends));assert not v.attempt();assert before==(v.g,v.items,v.friends)
 assert v.run('KR_ItemsMain')==30 and v.run('KR_ItemsGetThreshold')==.25
 for i in range(1,6):assert v.run('KR_ItemsAllowed',[i]) and v.run('KR_ItemsReserve',[i])==3
 assert v.saves==0;r['default_off_readonly']=True
 v.enable();assert v.saves==1;v.run('KR_ItemsSetEnabled',[True]);assert v.saves==1
 old=copy.deepcopy(v.g[229]);v.run('KR_ItemsSetThreshold',[2.0]);assert v.run('KR_ItemsMain')==190
 v.run('KR_ItemsSetThreshold',[-1.0]);assert v.run('KR_ItemsMain')==110
 v.run('KR_ItemsSetThreshold',[.25]);assert v.run('KR_ItemsMain')==130
 for i in range(1,6):
  v.run(f'KR_ItemsSetAllow{i}',[False]);assert not v.run(f'KR_ItemsGetAllow{i}')
  v.run(f'KR_ItemsSetReserve{i}',[2.0]);assert v.run('KR_ItemsReserve',[i])==99
  v.run(f'KR_ItemsSetReserve{i}',[-1.0]);assert v.run('KR_ItemsReserve',[i])==0
  v.run(f'KR_ItemsSetReserve{i}',[3/99]);assert v.run('KR_ItemsReserve',[i])==3
  v.run(f'KR_ItemsSetAllow{i}',[True]);assert v.run(f'KR_ItemsGetAllow{i}')
 assert all(a==b for i,(a,b) in enumerate(zip(old,v.g[229])) if i not in range(72,79))
 count=v.saves;v.run('KR_ItemsSetReserve',[1,3/99]);v.run('KR_ItemsSetThreshold',[.25]);assert v.saves==count
 v.run('KR_ItemsSetEnabled',[False]);assert v.run('KR_ItemsMain')==30;r['independent_settings_clamps_idempotence_story82_preserved']=True
 v=VM().enable();v.pa[3]=31;assert not v.attempt();v.pa[3]=30;assert v.attempt()
 assert v.pf[1:7]==[2,1,4,0,1,0] and v.pf[9]==2026092202 and v.items[1][4]==7 and v.pa[3]==30
 assert v.bars==[(29471,2),(29470,4)] and len(v.stock_writes)==1
 r['threshold_inclusive_native_reservation_no_effect_yet']=True
 v=VM().enable();v.pa[3]=20;v.items[1][4]=3;v.items[4][4]=3;assert not v.attempt()
 v.items[1][4]=4;assert v.attempt() and v.items[1][4]==3
 assert not v.attempt(1) and not v.attempt(2);r['reserve_floor_same_frame_no_duplicate']=True
 v=VM().enable();v.pa[3]=10;v.run('KR_ItemsSetAllowed',[1,False]);assert v.attempt() and v.pf[5]==4
 v=VM().enable();v.pa[25][81]=1;v.pa[3]=10;assert v.attempt() and v.bars==[(29471,1),(29470,2)]
 r['full_heal_fallback_and_native_item_speed_skill']=True
 for item,status in [(2,8),(3,9),(5,7)]:
  v=VM().enable();v.party[1][status]=1
  if item==5:v.party[1][3]=0
  assert v.attempt() and v.pf[5:7]==[item,1],(item,v.pf)
 r['poison_paralysis_revive_party_slot_not_character_id']=True
 v=VM().enable();v.pa[3]=10;v.party[1][7]=1;v.party[1][3]=0;assert v.attempt() and v.pf[5:7]==[5,1]
 for target_status in [9,10,11]:
  v=VM().enable();v.party[1][target_status]=1;v.party[1][3]=10;assert v.attempt() and v.pf[5:7]==[1,1]
 r['revive_priority_immovable_targets_healable']=True
 cases=0
 for typ in [-1,0,1,2,3,4,5]:
  v=VM().enable();v.pa[3]=10;v.battle[5]=typ;before=copy.deepcopy(v.items);ok=v.attempt();assert bool(ok)==(typ in [-1,0]);cases+=1
  if not ok:assert v.items==before
 for status in [7,9,10,11,12]:
  v=VM().enable();v.pa[status]=1;v.party[1][3]=10;assert not v.attempt();cases+=1
 for mutate in [lambda v:v.friends.pop(),lambda v:v.pa.__setitem__(3,0),lambda v:v.pf.__setitem__(2,1),lambda v:v.pf.__setitem__(1,1),lambda v:v.items.clear()]:
  v=VM().enable();v.pa[3]=10;mutate(v);before=copy.deepcopy(v.items);assert not v.attempt() and v.items==before;cases+=1
 r['scripted_battles_invalid_actor_and_stock_guards']=cases
 for wait in [0,1,2]:
  for item in [1,4,5]:
   v=VM().enable();v.pa[3]=10;v.friends[1][1:7]=[wait,1,4,0,item,0];assert v.pending(0,1) and v.pending(0,4)
 for kind in [2,3]:
  v=VM().enable();v.weapons[777]=ns['weapon'](777);v.weapons[777][11]=kind;v.friends[1][1:7]=[0,1,1,777,0,0]
  assert v.pending(0,1) and not v.pending(1,1) and not v.pending(0,5)
  assert bool(v.pending(2,1))==(kind==3)
 v.friends[1][2]=0;assert not v.pending(0,1)
 r['pending_wait_zero_items_single_all_ally_EX_no_false_revive_block']=True
 v=VM().enable();v.pa[3]=10;v.attempt();v.run('KR_ItemsSetEnabled',[False]);assert v.items[1][4]==7 and v.pf[3]==4
 v.run('KR_ItemsCancelDown',[v.pf]);assert v.items[1][4]==8 and v.pf[3]==-1
 v.run('KR_ItemsCancelDown',[v.pf]);assert v.items[1][4]==8
 for index,value in [(3,-1),(2,0),(9,0),(5,0),(5,6)]:
  v=VM().enable();v.pa[3]=10;v.attempt();v.pf[index]=value;v.run('KR_ItemsCancelDown',[v.pf]);assert v.items[1][4]==7
 r['down_refund_owned_once_manual_completed_untouched_toggle_keeps_queue']=True
 # Every original byte including native effect, execution and battle-end refund remains.
 before=read_meta(R/'staging/smart_auto_fix_20260922/candidate_meta.json');after=read_meta(O/'candidate_meta.json')
 for fid in [26694,26695,29229,29240,29242,29393,29475,31979,31981]:assert before['functions'][fid]==after['functions'][fid]
 r['native_effect_inventory_manual_refund_and_smart_fix_metadata_unchanged']=True
 ev=json.loads((O/'build_evidence.json').read_text());assert all(sha(O/n)==h for n,h in ev['files'].items())
 savej(O/'verification.json',dict(status='AUTO_ITEMS_COMPILED_PASS',files=ev['files'],tests=r,native_gameplay_verified=False,boundaries='Candidate JAM executed. Native item lookup/count access, party lookup, ability HP properties, weapon lookup, animation bars and common flag persistence emulated; native movement/status checks execute unmodified original JAM. No native gameplay claim.'))
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':prepare();tests()
