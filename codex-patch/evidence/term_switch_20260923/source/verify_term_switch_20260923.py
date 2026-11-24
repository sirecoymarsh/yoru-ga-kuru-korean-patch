"""Bounded execution of the actual compiled JAM. Native HLL I/O is modeled, not a game test."""
from pathlib import Path
import collections,copy,json,re,itertools,struct
import build_term_switch_20260923 as b
O=b.O;R=b.R
def proxy(s):return b.encode(s).decode('cp932')
def ko(s):return b.decode(s.encode('cp932'))
class VM:
 def __init__(self):
  self.meta=b.read_meta(O/'candidate_meta.json');self.fs={b.raw_symbol(self.meta,f['index']):f for f in self.meta['functions']};self.code={};self.cache={};self.files={};self.fail=set();self.dialog=[];self.steps=0;self.selection_active=False;self.selection_initializations=0
 def run(self,name,args=()):
  f=self.fs[name];fid=f['index'];vs=f['arguments']+f['variables'];li={x['name']:i for i,x in enumerate(vs)};loc={i:'' if v['type'][0]==12 else 0 for i,v in enumerate(vs)};loc.update(enumerate(args));st=[]
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
    elif arg.startswith('■'):
     out=self.dialog.pop(0) if '実行' in arg else 0
     if arg=='■選択ダイアログ／存在確認':out=int(self.selection_active)
     if arg=='■選択ダイアログ／初期化':self.selection_initializations+=1
    else:out=self.run(arg,aa)
    if ff['return-type'][0]!=0:st.append(out)
   elif op=='CALLHLL':
    lib,method,_=arg.split()
    if lib=='system' and method=='GetSaveFolderName':st.append('SaveData_Test')
    elif lib=='SystemService':
     if method=='SystemVariable_Get':st.append(self.cache.get(st.pop(),''))
     elif method=='SystemVariable_Set':v=st.pop();key=st.pop();self.cache[key]=v
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
 for fid in [31952,31953]:b.cmd('ain','dump','--function',b.symbol(b.read_meta(O/'candidate_meta.json'),fid),'-o',O/f'built_{fid}.jam',O/'NightRemaster.ain')
 v=VM();counts=collections.Counter();raw=[b.decode(x) for x in b.raw_messages((O/'baseline_NightRemaster.ain').read_bytes())[3]];rows=b.a.readj(O/'term_coverage.json')
 call=lambda n,*args:v.run(n,[proxy(x) if isinstance(x,str) else x for x in args])
 def settings(values):
  for i,t in enumerate(values):v.cache[f'YoruKR.Term.v1.{i}']=proxy(t)
  v.run('KR_TermRefresh')
 defaults=[t[0] for t in b.TERMS]
 for i,s in enumerate(raw):assert ko(call('KR_TermMessage',i,s))==s;counts['default_all_MSG1']+=1
 from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer
 _,faces=parse_fnl_font(Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl',0);face,den,_=select_fnl_face(faces,60);indices,_=b.a.load_proxy_indices(b.a.readj(b.a.PROXY),len(face.widths));meter=WidthMeasurer(face,den,indices,-2,2,0)
 classes={r['message_id']:r for r in b.a.readj(b.a.HERE/'message_window_classification.json')['rows']}
 scenarios=[['광수','화자','쉭쉭이','하자마','토야','진월','진야'],['빛잡이','불지기','쉭쉭이','틈','동야','참달','참밤'],['광군','화군','하늘','공간','차디찬 겨울','푸른 별','깊은 밤']]
 examples=[]
 for values in scenarios:
  assert all(call('KR_TermValid',i,x) for i,x in enumerate(values)),values;settings(values)
  for row in rows:
   i=row['id'];out=ko(call('KR_TermMessage',i,row['source']));c=classes[i]
   if c['message_roles']==['Body']:
    budget=716 if c['window_types']==['Face'] else 932
    assert meter.measure(out,True)['max_width_px']<=budget,(i,out,budget,meter.measure(out,True))
   if not row['dynamic_page']:assert out==b.render(row['tokens'],values),(i,out,b.render(row['tokens'],values))
   counts['compiled_term_rows']+=1
  # Dynamic pages retain every visible character except spaces, with no truncation.
  for page in b.a.readj(O/'dynamic_pages.json'):
   joined=''.join(ko(call('KR_TermMessage',i,raw[i])) for i in page['ids']);want=b.render(b.tokens(page['source']),values)
   assert re.sub(r'\s','',joined)==re.sub(r'\s','',want),(page['ids'],joined,want);counts['complete_dynamic_pages']+=1
  examples.append(dict(settings=values,examples={str(i):ko(call('KR_TermMessage',i,raw[i])) for i in [10455,25440,33021,33022,51101,51102]}))
 settings(scenarios[2])
 golden=[(10455,'공간' if False else '토야')]
 # Independent particle expectations, not generated by the production suffix rules.
 settings(['광군','화군','하늘','공간','토야','진월','진야'])
 assert '토야나' in ko(call('KR_TermMessage',10455,raw[10455]))
 assert '광군이었던' in ko(call('KR_TermMessage',25440,raw[25440]))
 for i in [18448,93821]:assert ko(call('KR_TermMessage',i,raw[i]))==raw[i]
 for s in ['발치로','입부하자마자','말을 하자마자','마코토야','호무라 신사','顔CG変換テーブル.cgName']:
  assert ko(call('KR_TermDisplay',s))==s;counts['false_positive_unchanged']+=1
 for bad in ['', ' ', ' 가','가 ', '가\n나','{키}','%s','abc','123','가가가가가가가가가','가각각']:
  assert not call('KR_TermValid',0,bad);counts['invalid_custom_rejected']+=1
 for i in range(7):
  for j,s in enumerate(defaults):
   if i!=j:assert not call('KR_TermValid',i,s);counts['cross_term_collision_rejected']+=1
 for n in ['빛','하늘','가가가','밥','별']:
  assert call('KR_TermValid',0,n);counts['valid_custom']+=1
 for values in scenarios:
  settings(values)
  for row in b.a.readj(O/'display_terms.json'):
   once=call('KR_TermDisplay',row['source']);assert v.run('KR_TermDisplay',[once])==once;counts['display_idempotent']+=1
 dat='SaveData_Test\\YoruKR_Terms.dat';backup='SaveData_Test\\YoruKR_Terms.backup'
 settings(scenarios[0]);assert v.run('KR_TermSave');saved=copy.deepcopy(v.files);v.cache={};v.run('KR_TermLoad');assert [ko(call('KR_TermGet',i)) for i in range(7)]==scenarios[0];counts['save_reload']+=1
 settings(scenarios[1]);v.fail={'WriteString'};assert not v.run('KR_TermSave');assert v.files[dat]==saved[dat];v.run('KR_TermLoad');assert [ko(call('KR_TermGet',i)) for i in range(7)]==scenarios[0];v.fail=set();counts['failed_write_preserves_previous']+=1
 settings(scenarios[1]);assert v.run('KR_TermSave');v.files[dat]=[20260923,'bad'];v.cache={};v.run('KR_TermLoad');assert [ko(call('KR_TermGet',i)) for i in range(7)]==scenarios[0];counts['corrupt_primary_backup_restore']+=1
 oldbackup=copy.deepcopy(v.files[backup]);settings(scenarios[2]);v.fail={('CopyFile',dat)};assert not v.run('KR_TermSave');assert v.files[backup]==oldbackup;v.run('KR_TermLoad');assert [ko(call('KR_TermGet',i)) for i in range(7)]==scenarios[0];v.fail=set();counts['invalid_main_never_overwrites_valid_backup']+=1
 assert all(p.startswith('SaveData_Test\\') for p in v.files);counts['preferences_in_engine_save_folder']+=1
 # Menu immediate cancel and submenu cancel do not touch settings or files.
 for queue in [[0],[1,0,0]]:
  v.dialog=list(queue);before=copy.deepcopy(v.files);v.run('KR_TermMenu');assert v.files==before and not v.dialog;counts['menu_cancel_no_write']+=1
 v.dialog=[1,3,0];v.run('KR_TermMenu');assert ko(call('KR_TermGet',0))=='빛잡이' and not v.dialog;v.cache={};v.run('KR_TermLoad');assert ko(call('KR_TermGet',0))=='빛잡이';counts['menu_preset_saved_reloaded']+=1
 v.dialog=[20,0];v.run('KR_TermMenu');assert [ko(call('KR_TermGet',i)) for i in range(7)]==defaults and not v.dialog;counts['menu_restore_defaults']+=1
 v.selection_active=True;before=copy.deepcopy(v.files);initializations=v.selection_initializations;v.run('KR_TermMenu');assert v.files==before and v.selection_initializations==initializations;counts['active_native_choice_not_deleted']+=1
 b.save('verification.json',dict(status='TERM_SWITCH_COMPILED_PASS',files=ev['files'],counts=dict(counts),steps=v.steps,native_verified=False,examples=examples,limits='Actual compiled bytecode executed in bounded VM; native String/VSFile/GUI methods modeled. Native modal input and persistence not yet observed.'))
 print(dict(counts=counts,steps=v.steps))
if __name__=='__main__':main()
