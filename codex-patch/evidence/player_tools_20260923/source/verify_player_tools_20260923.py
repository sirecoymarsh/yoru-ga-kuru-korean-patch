"""Bounded execution of the actual compiled JAM. Native HLL I/O is modeled, not a game test."""
from pathlib import Path
import collections,copy,json,re,itertools,struct
import build_term_switch_20260923 as b
from probe_player_tools_20260923 import O,R,save
def proxy(s):return b.encode(s).decode('cp932')
def ko(s):return b.decode(s.encode('cp932'))
class VM:
 def __init__(self):
  self.meta=b.read_meta(O/'candidate_meta.json');self.fs={b.raw_symbol(self.meta,f['index']):f for f in self.meta['functions']};self.code={};self.cache={};self.files={};self.fail=set();self.dialog=[];self.steps=0;self.selection_active=False;self.selection_initializations=0; self.ready=True; self.replay=False; self.scene={0:[28170]}; self.retains=0; self.registry=[]; self.player={"name":proxy("기이월"),"hp":671,"lv":57,"difficulty":2,"date":819}; self.replacements={}; self.refreshes=0; self.banned=[]; self.inputs=[]; self.titles=[]; self.notices=[]; self.lookups=0
 def run(self,name,args=()):
  f=self.fs[name];fid=f['index'];vs=f['arguments']+f['variables'];li={x['name']:i for i,x in enumerate(vs)};loc={i:'' if v['type'][0]==12 else -1 if v['type'][0] in (21,89) else 0 for i,v in enumerate(vs)};loc.update(enumerate(args));st=[]
  if fid not in self.code:
   path=O/f'built_{fid}.jam';ops=[];labels={}
   for line in path.read_text('utf8').splitlines():
    l=line.strip()
    if not l or l.startswith((';','FUNC ','ENDFUNC ','EOF ')):continue
    if l.endswith(':'):labels[l[:-1]]=len(ops)
    else:ops.append(l.split(maxsplit=1))
   self.code[fid]=(ops,labels)
  ops,labels=self.code[fid];pc=0;steps=0
  while pc<len(ops):
   op,*rest=ops[pc];arg=rest[0] if rest else '';pc+=1;steps+=1;self.steps+=1;assert steps<150000,(name,pc)
   if op=='PUSH':st.append(int(arg,0))
   elif op=='S_PUSH':st.append(json.loads(arg))
   elif op=='.S_LOCALASSIGN':v,x=arg.split(' ',1);loc[li[v]]=json.loads(x)
   elif op=='.LOCALASSIGN':v,x=arg.rsplit(' ',1);loc[li[v]]=int(x,0)
   elif op=='.LOCALREF':st.append(loc[li[arg]])
   elif op in ['.LOCALINC2','.LOCALINC3','.LOCALINC']:loc[li[arg]]+=1
   elif op=='.LOCALDEC2':loc[li[arg]]-=1
   elif op=='.LOCALPLUSA':v,x=arg.rsplit(' ',1);loc[li[v]]+=int(x)
   elif op=='.LOCALMINUSA':v,x=arg.rsplit(' ',1);loc[li[v]]-=int(x)
   elif op=='.LOCALDELETE':
    value=loc[li[arg]]
    if isinstance(value,dict):self.retains-=1
    loc[li[arg]]=-1
   elif op=='.GLOBALREF':
    if arg=='Flags':st.append('flags')
    elif arg=='GetActiveScene':st.append('active_scene_delegate')
    elif arg=='N_ScenarioRegister::detail::_EV_TABLE':st.append(self.registry)
    else:raise AssertionError(arg)
   elif op=='CALLMETHOD':
    assert arg=='0' and st.pop()==26485 and st.pop()=='flags';st.append(int(self.ready))
   elif op=='DG_CALLBEGIN':assert st.pop()=='active_scene_delegate'
   elif op=='DG_CALL':
    assert arg.startswith('"DG_Func<ref I_Scene>" ')
    st += [self.scene,0]
    if isinstance(self.scene,dict):self.retains+=1
    pc=labels[arg.rsplit(' ',1)[1]]
   elif op=='PUSHLOCALPAGE':st.append(loc)
   elif op=='A_REF':assert isinstance(st[-1],str),(name,st[-1])
   elif op in ['S_ASSIGN','X_ASSIGN']:
    assert op=='S_ASSIGN' or arg=='1';v=st.pop();i=st.pop();p=st.pop();p[i]=v;st.append(v)
   elif op=='X_REF':
    assert arg=='1';i=st.pop();p=st.pop();st.append(p[i])
   elif op=='X_DUP':st+=st[-int(arg):]
   elif op in ['DELETE','POP']:st.pop()
   elif op=='NOT':st.append(int(not st.pop()))
   elif op in ['ADD','SUB','S_ADD','LT','LTE','GT','GTE','EQUALE','NOTE','S_EQUALE','S_NOTE','MUL','DIV','MOD']:
    z=st.pop();x=st.pop()
    if op in ['ADD','S_ADD']:v=x+z
    elif op=='SUB':v=x-z
    elif op=='MUL':v=x*z
    elif op=='DIV':v=x//z
    elif op=='MOD':v=x%z
    elif op=='LT':v=int(x<z)
    elif op=='LTE':v=int(x<=z)
    elif op=='GT':v=int(x>z)
    elif op=='GTE':v=int(x>=z)
    elif op in ['EQUALE','S_EQUALE']:v=int(x==z)
    else:v=int(x!=z)
    st.append(v)
   elif op=='S_MOD':v=st.pop();s=st.pop();assert arg=='2';st.append(s%v)
   elif op in ['IFZ','IFNZ']:
    if bool(st.pop())==(op=='IFNZ'):pc=labels[arg]
   elif op=='JUMP':pc=labels[arg]
   elif op=='CALLFUNC':
    ff=self.fs[arg];n=len(ff['arguments']);aa=st[-n:] if n else [];st=st[:-n] if n else st
    if arg=='SYS_AddPunct':out=aa[0] if aa[0].endswith('\\') else aa[0]+'\\'
    elif arg=='Ａ＿回想モード実行中確認':out=int(self.replay)
    elif arg=='LAbility::GetPlayerName':out=self.player['name']
    elif arg=='LAbility::SetPlayerName':self.player['name']=aa[0];out=None
    elif arg=='Ａ＿メッセージ置換設定':self.replacements[aa[0]]=aa[1];out=None
    elif arg=='L_StatusFace::UpdateAll':self.refreshes+=1;out=None
    elif arg=='EX_Width':assert aa==['禁止テキスト.主人公名',0];out=len(self.banned)
    elif arg=='EX_AString':assert aa[0]=='禁止テキスト.主人公名' and aa[2:]==['',0];out=self.banned[aa[1]]
    elif arg=='■文字列入力ダイアログ':
     out,text=self.inputs.pop(0)
     assert name=='KR_PlayerRename' and aa[3]==loc[li['candidate']]
     loc[li['candidate']]=text
    elif arg.startswith('■'):
     out=self.dialog.pop(0) if '実行' in arg else 0
     if arg=='■選択ダイアログ／存在確認':out=int(self.selection_active)
     if arg=='■選択ダイアログ／初期化':self.selection_initializations+=1
     if arg=='■選択ダイアログ／タイトル設定':self.titles.append(aa[0])
     if arg=='■シンプルダイアログ':self.notices.append(aa[0])
    else:out=self.run(arg,aa)
    if ff['return-type'][0]!=0:st.append(out)
   elif op=='CALLHLL':
    lib,method,_=arg.split()
    if lib=='system' and method=='GetSaveFolderName':st.append('SaveData_Test')
    elif lib=='SystemService':
     if method=='SystemVariable_Get':st.append(self.cache.get(st.pop(),''))
     elif method=='SystemVariable_Set':v=st.pop();key=st.pop();self.cache[key]=v
     else:raise AssertionError(method)
    elif lib=='Array':
     if method=='Numof':st.append(len(st.pop()))
     elif method=='Find#1':
      self.lookups+=1;key=st.pop();end=st.pop();start=st.pop();array=st.pop()
      try:out=array.index(key,start,end)
      except ValueError:out=-1
      st.append(out)
     else:raise AssertionError(method)
    elif lib=='String':
     if method=='Length':st.append(len(st.pop()))
     elif method=='LengthByte':st.append(len(st.pop().encode('cp932')))
     elif method=='Find':key=st.pop();text=st.pop();st.append(text.find(key))
     elif method=='StartsWith':key=st.pop();text=st.pop();st.append(int(text.startswith(key)))
     elif method=='GetPart':idx=st.pop();text=st.pop();assert idx>=0;st.append(text[idx:])
     elif method=='GetPart#1':count=st.pop();idx=st.pop();text=st.pop();assert min(idx,count)>=0;st.append(text[idx:idx+count])
     elif method=='Replace':new=st.pop();old=st.pop();text=st.pop();st.append(text.replace(old,new))
     elif method=='Trim':st.append(st.pop().strip())
     elif method=='TrimStart':st.append(st.pop().lstrip())
     else:raise AssertionError((name,method))
    elif lib=='VSFile':
     if method in ['OpenForWrite','OpenForRead']:
      path=st.pop();ok=method not in self.fail and (method=='OpenForWrite' or path in self.files);st.append(int(ok))
      if ok:
       self.handle=path;self.cursor=0
       if method=='OpenForWrite':self.files[path]=[]
     elif method in ['WriteInt','WriteString']:
      v=st.pop();ok=method not in self.fail
      if ok:self.files[self.handle].append(v)
      st.append(int(ok))
     elif method in ['ReadInt','ReadString']:
      if method=='ReadInt':idx=st.pop();page=st.pop()
      else:st.pop();assert ops[pc-2][0]=='.LOCALREF';page=loc;idx=li[ops[pc-2][1]]
      ok=self.cursor<len(self.files[self.handle]) and method not in self.fail
      if ok:page[idx]=self.files[self.handle][self.cursor];self.cursor+=1
      st.append(int(ok))
     elif method=='Close':st.append(int(method not in self.fail))
     else:raise AssertionError(method)
    elif lib=='FileOperation':
     if method=='ExistFile':st.append(int(st.pop() in self.files))
     elif method=='CopyFile':
      src=st.pop();dst=st.pop();ok=src in self.files and (method,dst) not in self.fail
      if ok:self.files[dst]=copy.deepcopy(self.files[src])
      st.append(int(ok))
     elif method=='DeleteFile':p=st.pop();self.files.pop(p,None);st.append(1)
     else:raise AssertionError(method)
    else:raise AssertionError((name,lib,method))
   elif op=='RETURN':
    assert len(st)==int(f['return-type'][0]!=0),(name,st)
    return st[0] if st else None
   else:raise AssertionError((name,op,arg))
  raise AssertionError(('no return',name))

def main():
 ev=b.a.readj(O/'build_evidence.json');assert all(b.a.sha(O/n)==h for n,h in ev['files'].items())
 v=VM();counts=collections.Counter();cat=b.a.readj(O/'event_catalog.json');events=cat['events'];keys=[e['fn'] for e in events]
 call=lambda n,*args:v.run(n,[proxy(x) if isinstance(x,str) else x for x in args])
 # Execute native registration lookup bytecode, with only Array HLL modeled.
 for fid in [26435,26438,31952]:assert (O/f'built_{fid}.jam').exists()
 for ready,replay,scene,want in [(True,False,{0:[28170]},1),(False,False,{0:[28170]},0),(True,True,{0:[28170]},0),(True,False,-1,0),(True,False,{0:[29512]},0)]:
  v.ready=ready;v.replay=replay;v.scene=scene
  for _ in range(5):assert call('KR_PlayerReady')==want and v.retains==0
  counts['ready_guard_lifetime']+=5
  if not want:
   before=copy.deepcopy(v.player);assert not call('KR_PlayerApplyName','하늘');assert v.player==before
   counts['wrong_scene_no_mutation']+=1
 v.ready=True;v.replay=False;v.scene={0:[28170]}
 alphabet=''.join(x['unicode_character'] for x in b.a.readj(b.a.PROXY)['mapping'] if '\uac00'<=x['unicode_character']<='\ud7a3');assert len(alphabet)==2364 and len(set(alphabet))==2364
 for c in alphabet:assert call('KR_PlayerNameValid',c);counts['supported_hangul']+=1
 for text in ['A','a','01234','한 글','기이월','가나다라마','Ab1한글']:
  assert call('KR_PlayerNameValid',text);counts['valid_names']+=1
 for text in ['', ' ', ' 이름','이름 ','가나다라마바','이\n름','A\tB','%s','a{b','a\\b']:
  assert not call('KR_PlayerNameValid',text);counts['invalid_names']+=1
 for raw in ['ㄱ','ᄀ','힣','💛','a\x00b']:
  assert not v.run('KR_PlayerNameValid',[raw]);counts['unsupported_names']+=1
 v.banned=[proxy('금지')];assert not call('KR_PlayerNameValid','금지');counts['native_ban_list']+=1
 # Candidate string is a native ref string; fixture mutates that local on native dialog return.
 for result,text in [(0,'하늘'),(1,'기이월'),(1,'가나다라마바'),(1,'금지')]:
  before=copy.deepcopy(v.player);v.inputs=[(result,proxy(text))];v.run('KR_PlayerRename')
  assert v.player==before and not v.inputs and v.refreshes==0 and not v.replacements;counts['cancel_invalid_unchanged']+=1
 before=copy.deepcopy(v.player);v.inputs=[(1,proxy('하늘'))];v.run('KR_PlayerRename');before['name']=proxy('하늘')
 assert v.player==before and v.refreshes==1 and v.replacements=={proxy('료　　　　'):proxy('하늘')} and v.retains==0;counts['rename_only_name_replacement_refresh']+=1
 doc=b.ex.decode_ex(O/'baseline_NightRemasterEX.ex');bans=next(x.payload for x in doc.blocks if x.name.value.decode('cp932')=='禁止テキスト')
 v.banned=[x.value.payload.value.decode('cp932') for x in b.val(bans,'主人公名').items]
 for text in v.banned:assert not v.run('KR_PlayerNameValid',[text]);counts['original_banned_entries']+=1
 for text in ['하늘','한별','기이월','Ab1한글']:assert call('KR_PlayerNameValid',text)
 # None/all/partial, repeated calls, repeated recorded IDs, excluded keys, and nonstandard01707 alias.
 sets=[[],keys,keys[::7],['ＥＶ／元／01707'],['ＥＶ／元／E01707'],keys[::17]*2+['ＥＶ／元／E05000','ＥＶ／元／E00996','ＥＶ／回想／E00001']]
 for registered in sets:
  v.registry=list(registered);snapshot=list(v.registry)
  for _ in range(2):
   for g in range(4):
    want=sum(e['fn'] in registered for e in events if e['group']==g)
    assert call('KR_PlayerEventCount',g)==want;counts['event_group_cases']+=1
  assert v.registry==snapshot
 for g in [-1,4,100]:assert call('KR_PlayerEventCount',g)==0
 for total in [1043,398,362,42,241]:
  for seen in [0,1,total//2,total]:
   rate=seen*1000//total;expected=f'{seen} / {total}  ({rate//10}.{rate%10}%)'
   assert call('KR_PlayerRate',seen,total)==expected;counts['rates']+=1
 v.registry=keys[::7];v.dialog=[0];before=copy.deepcopy(v.player);v.run('KR_PlayerInfoMenu');assert v.player==before and not v.dialog;counts['menu_cancel_no_write']+=1
 expected=sum(e['fn'] in v.registry for e in events);assert f'{expected} / 1043' in ko(v.titles[-1])
 initial=v.selection_initializations;v.selection_active=True;v.run('KR_PlayerInfoMenu');assert v.selection_initializations==initial;v.selection_active=False;counts['active_choice_preserved']+=1
 v.dialog=[1,0];v.inputs=[(1,proxy('한별'))];nlookups=v.lookups;v.run('KR_PlayerInfoMenu')
 assert not v.inputs and not v.dialog and '주인공 : 한별' in ko(v.titles[-1]);assert v.lookups-nlookups==1043;counts['rename_menu_refresh_count_once']+=1
 assert v.retains==0 and not v.files and not v.cache
 # The new helpers' mutable native boundary is limited to these three operations.
 calls=set()
 for fid in ev['added_functions'].values():
  calls.update(re.findall(r'^\s*CALLFUNC (.+)$',(O/f'built_{fid}.jam').read_text('utf8'),re.M))
 assert not any('Save' in x or 'RegisterEvent' in x or 'SetEventFlag' in x or 'ClearAll' in x for x in calls)
 menu=(O/f'built_{ev["added_functions"]["KR_PlayerInfoMenu"]}.jam').read_text('utf8');assert 'CALLFUNC ■選択ダイアログ／タイプ設定' in menu
 save('verification.json',dict(status='PLAYER_TOOLS_COMPILED_PASS',files=ev['files'],counts=dict(counts),steps=v.steps,examples=[ko(x) for x in v.titles[-2:]],native_verified=False,boundaries='Actual compiled helper and registry lookup JAM executed. Native scene callback, String/Array HLL, input GUI, name setter and redraw modeled; IME and normal-save restart not observed.'))
 print(dict(counts=counts,steps=v.steps))

if __name__=='__main__':main()
