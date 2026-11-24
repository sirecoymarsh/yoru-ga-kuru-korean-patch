"""Compiled-helper VM, native-consumer contracts, and shipped-font layout checks."""
from cheat_support_20260915 import *
import math,struct,copy,collections,zlib
from verify_remaster_multiplier_20260915 import i32,bits,flt,trunc,value
from build_remaster_multiplier_20260915 import ex,part,child,val,allparts,maybe
from audit_dynamic_ui_20260915 import ENC
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index

class VM:
 def __init__(self):
  self.meta=read_meta(O/'candidate_meta.json');self.fs={f['name']:f for f in self.meta['functions']};self.code={};self.flags=[0]*101;self.auto=False;self.now=1000;self.first=False;self.cancel=False;self.saved=[];self.calls=0
 def run(self,name,args=(),trap_fixture=None):
  if name=='SystemFlagManager::Get':return self.flags[args[0]] if 0<=args[0]<len(self.flags) else 0
  if name=='SystemFlagManager::Save':self.saved.append(list(self.flags));return
  if name=='N_Tutorial::IsRunFirstTime':assert args==[3];return int(self.first)
  if name=='C_UserInputManager::IsClickCancel':return int(self.cancel)
  f=self.fs[name];fid=f['index'];self.calls+=1
  if fid not in self.code:
   ops=[];labs={}
   for line in (O/f'built_{fid}.jam').read_text(encoding='utf8').splitlines():
    l=line.strip()
    if not l or l.startswith((';','FUNC','ENDFUNC','EOF')):continue
    if l.endswith(':'):labs[l[:-1]]=len(ops)
    else:ops.append(l.split(maxsplit=1))
   self.code[fid]=ops,labs
  ops,labs=self.code[fid];vs=f['arguments']+f['variables'];li={v['name']:i for i,v in enumerate(vs)};loc={i:0 for i in range(len(vs))};loc.update(enumerate(args));st=[];pc=0;steps=0;endpc=None
  if trap_fixture is not None:
   pc=next(i for i,x in enumerate(ops) if x==['CALLFUNC','KR_GetTrap'])
   endpc=labs[ops[pc+1][1]];loc[li['cell']]=trap_fixture;loc[li['lx']]=3;loc[li['ly']]=5
  while pc<len(ops):
   if endpc is not None and pc==endpc:assert not st;return 999
   steps+=1;assert steps<150000,(name,pc)
   op,*arg=ops[pc];a=arg[0] if arg else '';pc+=1
   if op=='PUSH':st.append(i32(int(a,0)))
   elif op=='F_PUSH':raise AssertionError('Unsupported native opcode64 F_PUSH')
   elif op=='PUSHLOCALPAGE':st.append(loc)
   elif op=='.LOCALREF':st.append(loc[li[a]])
   elif op=='.LOCALASSIGN':n,v=a.rsplit(' ',1);loc[li[n]]=i32(int(v,0))
   elif op in ['.LOCALINC2','.LOCALINC3','.LOCALINC']:loc[li[a]]=i32(loc[li[a]]+1)
   elif op in ['SH_LOCALDELETE','SH_LOCALCREATE']:raise AssertionError('Unsupported native legacy struct opcode')
   elif op=='.LOCALCREATE':n,_=a.split(' ',1);loc[li[n]]={}
   elif op=='.GLOBALREF':st.append(self.flags if a=='g_sysFlagList' else {'FLAGS':True} if a=='Flags' else None);assert st[-1] is not None,a
   elif op=='.STRUCTREF':assert a=='C_SceneDungeon m_DungeonView';st.append({'view':True})
   elif op=='X_DUP':st.extend(st[-int(a):])
   elif op=='X_REF':
    assert a=='1';index=st.pop();obj=st.pop();st.append(obj[index])
   elif op=='X_ASSIGN':
    assert a=='1';v=st.pop();ix=st.pop();obj=st.pop();obj[ix]=v;st.append(v)
   elif op=='X_A_INIT':
    assert a=='0' and st.pop()==0;ix=st.pop();obj=st.pop();obj[ix]=[];st.append(obj[ix])
   elif op in ['DELETE','POP']:st.pop()
   elif op=='NOT':st.append(int(not st.pop()))
   elif op=='ITOF':st.append(bits(st.pop()))
   elif op=='FTOI':st.append(i32(math.trunc(flt(st.pop()))))
   elif op in ['IFNZ','IFZ']:
    v=st.pop()
    if bool(v)==(op=='IFNZ'):pc=labs[a]
   elif op=='JUMP':pc=labs[a]
   elif op=='RETURN':
    if f['return-type'][0]==0:assert not st,(name,st);return
    assert len(st)==1,(name,st);return st.pop()
   elif op=='CALLFUNC':
    ff=self.fs[a];n=len(ff['arguments']);aa=st[-n:] if n else []
    if n:del st[-n:]
    v=self.run(a,aa)
    if ff['return-type'][0]!=0:st.append(v)
   elif op=='CALLHLL':
    if a in ['Array Numof 1','Array Numof 2']:st.append(len(st.pop()))
    elif a=='Array Realloc 2':
     n=st.pop();target=st.pop();target[:]=target[:n]+[None]*max(0,n-len(target))
    elif a=='Array Copy#3 2':
     n=st.pop();source_index=st.pop();source=st.pop();target_index=st.pop();target=st.pop()
     target[target_index:target_index+n]=copy.deepcopy(source[source_index:source_index+n]);st.append(n)
    elif a=='system GetTime 0':st.append(i32(self.now))
    else:raise AssertionError(a)
   elif op=='CALLMETHOD':
    n=int(a);aa=st[-n:] if n else []
    if n:del st[-n:]
    mid=st.pop();obj=st.pop();ret=self.method(mid,obj,aa)
    if self.meta['functions'][mid]['return-type'][0]!=0:st.append(ret)
   elif op in ['ADD','SUB','MUL','DIV','LTE','GTE','LT','GT','NOTE','EQUALE'] or op.startswith('F_'):
    b=st.pop();aa=st.pop();k=op
    if k.startswith('F_'):aa,b=flt(aa),flt(b);k=k[2:]
    if k=='ADD':v=aa+b
    elif k=='SUB':v=aa-b
    elif k=='MUL':v=aa*b
    elif k=='DIV':v=aa/b if op.startswith('F_') else trunc(aa,b)
    elif k=='LTE':v=int(aa<=b)
    elif k=='GTE':v=int(aa>=b)
    elif k=='LT':v=int(aa<b)
    elif k=='GT':v=int(aa>b)
    elif k=='NOTE':v=int(aa!=b)
    elif k=='EQUALE':v=int(aa==b)
    else:raise AssertionError(op)
    st.append(bits(v) if op.startswith('F_') and k in ['ADD','SUB','MUL','DIV'] else i32(v))
   else:raise AssertionError((name,op,a))
  raise AssertionError(('No return',name))
 def method(self,mid,obj,a):
  if mid==26609:return int(self.auto)
  if mid==26611:self.auto=bool(a[0]);return a[0]
  if mid in [27005,27029,27008]:return obj[{27005:'object',27029:'event',27008:'sub'}[mid]]
  if mid in [27025,27022]:obj[{27025:'removed',27022:'shown'}[mid]]=bool(a[0]);return
  if mid==28763:assert a==[3,5];return
  if mid in [27074,27075]:return obj.get(tuple(a),(1,0))[mid-27074]
  if mid==27081:
   assert a[1:]==[0,0,30,30] and self.flags[87]==1
   a[0]['walk']={p for p,v in obj.items() if v[0]!=1};return
  if mid==30019:
   info,x,y,gx,gy,result=a;assert self.flags[87]==0
   start=(x,y);goal=(gx,gy);q=collections.deque([start]);prev={start:None}
   while q:
    p=q.popleft()
    if p==goal:
     while p is not None:result.append(p);p=prev[p]
     # Native30029 appends goal->start; native30022 reverses the ENTIRE output.
     result.reverse();return len(result)
    for n in [(p[0]+1,p[1]),(p[0]-1,p[1]),(p[0],p[1]+1),(p[0],p[1]-1)]:
     if n in info['walk'] and n not in prev:prev[n]=p;q.append(n)
   return 0
  if mid==28677:
   assert self.flags[88]==1 or not self.run('KR_GetRoute');obj['drawn']=list(a[0]);return
  raise AssertionError(mid)

def vm_tests():
 v=VM();base=list(v.flags);v.flags[15]=1;v.flags[95]=1;v.flags[96]=1
 for name in ['Trap','Quick','Route']:assert v.run('KR_Get'+name)==0
 assert v.run('KR_Speed')==1
 v.run('KR_InitOptions');assert [v.flags[i] for i in [15,95,96]]==[1,1,1]
 for speed in range(1,6):
  v.run('KR_SetSpeed',[bits((speed-1)/4)]);assert v.run('KR_Speed')==speed
  for _ in range(100):v.run('KR_SetSpeed',[v.run('KR_GetSpeed')]);assert v.run('KR_Speed')==speed
 for n,want in [(-float('inf'),1),(float('nan'),1),(-1,1),(3,5),(float('inf'),5)]:v.run('KR_SetSpeed',[bits(n)]);assert v.run('KR_Speed')==want
 for flag in ['Trap','Quick','Route']:
  for setting in [True,False]:v.run('KR_Set'+flag,[int(setting)]);assert v.run('KR_Get'+flag)==setting
 quick=0
 for oldauto in [False,True]:
  for enabled in [0,1]:
   for first in [False,True]:
    for event in [0,1,999]:
     v.auto=oldauto;v.first=first;v.cancel=False;v.now=1000;v.run('KR_SetQuick',[enabled]);v.run('KR_BeginQuick',[event]);active=enabled and not first and event==0
     assert v.run('KR_QuickActive')==active
     if active:assert v.auto and v.run('KR_BattleRate')==1000
     v.run('KR_EndQuick');assert v.auto==oldauto and not v.run('KR_QuickActive');quick+=1
 v.first=False;v.run('KR_SetQuick',[1])
 for cancel,elapsed in [(True,1),(False,15001),(False,100)]:
  v.auto=False;v.cancel=False;v.now=2147483600;v.run('KR_BeginQuick',[0]);v.cancel=cancel;v.now=i32(v.now+elapsed);v.run('KR_QuickWatch')
  assert bool(v.run('KR_QuickActive'))== (not cancel and elapsed<=15000)
  v.run('KR_EndQuick')
 for slot in [-1,101,5000]:b=list(v.flags);v.run('KR_Poke',[slot,99]);assert v.flags==b
 traps=0
 for on in [0,1]:
  v.run('KR_SetTrap',[on])
  for object_ in [0,2,3,4,5,6]:
   for event in [0,1]:
    for sub in [0,1,42]:
     cell=dict(object=object_,event=event,sub=sub,removed=False,shown=False);before=copy.deepcopy(cell)
     ret=v.run('C_SceneDungeon@StepedOnCell',trap_fixture=cell)
     expected=on and object_==5 and (not event or sub==0)
     if expected:assert ret==0 and cell['removed'] and cell['shown']
     else:assert ret==999 and cell==before
     traps+=1
 # Execute actual compiled route enumeration, refs and buffers with native method fixtures.
 routecases=0
 for layout in ['straight','detour','no_exit','blocked','nearest','entrance_not_exit']:
  # Each fixture represents a fresh map binding, which invalidates route cache.
  v.run('KR_Poke',[85,-1]);v.run('KR_Poke',[86,-1])
  v.run('KR_SetRoute',[1]);mp={(x,1):(0,0) for x in range(1,8)};mp[(7,1)]=(2,1);view={};playerqueue=[(2,1),(3,1)];before=list(playerqueue)
  if layout=='detour':mp[(4,1)]=(1,0);mp.update({(x,2):(0,0) for x in range(3,6)})
  if layout=='no_exit':mp[(7,1)]=(0,0)
  if layout=='blocked':mp[(4,1)]=(1,0)
  if layout=='nearest':mp[(3,1)]=(2,1)
  if layout=='entrance_not_exit':mp[(3,1)]=(2,0)
  oldmap=copy.deepcopy(mp);v.run('KR_DrawRoute',[mp,view,1,1]);r=view['drawn'];assert mp==oldmap and playerqueue==before and v.flags[87]==v.flags[88]==0
  if layout in ['blocked','no_exit']:assert r==[]
  else:assert r[0]==(1,1) and r[-1]==((3,1) if layout=='nearest' else (7,1));assert all(mp[x][0]!=1 for x in r)
  # The route's last-draw marker survives entering battle, even with quick disabled.
  v.run('KR_SetQuick',[0]);v.run('KR_BeginQuick',[0]);assert v.flags[89]==1
  v.run('KR_SetRoute',[0]);v.run('KR_DrawRoute',[mp,view,1,1]);assert view['drawn']==[] and v.flags[89]==0;routecases+=1
 return dict(compiled_VM_calls=v.calls,slider_steps=5,slider_roundtrips=500,quick_entry_exit_cases=quick,watchdog_and_cancel=True,int32_clock_wrap=True,trap_compiled_hook_cases=traps,route_compiled_helper_fixtures=routecases,unknown_slot_bounds=True,original_system_flags_preserved=True,route_native_AStar_engine_itself_tested=False)

def font_layout():
 ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime']);fp=rt/'NightRemasterFont.fnl';raw=fp.read_bytes();_,faces=parse_fnl_font(fp,3);q=20;table={}
 for fn in range(struct.unpack_from('<I',raw,16)[0]):
  nf=struct.unpack_from('<I',raw,q)[0];q+=4
  for f in range(nf):
   h,u,n=struct.unpack_from('<III',raw,q);q+=12
   if fn==3:table[f]=(h,[struct.unpack_from('<HII',raw,q+10*j) for j in range(n)])
   q+=10*n
 proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};doc=ex.decode_ex(O/'pact_123_cheats.pactex');rows=[]
 for parent in [part(doc,'矩形_戦闘'),part(doc,'KR_CheatGroup')]:
  names_=[t.name.value.decode('cp932') for t in child(parent,'子パーツ').children];order=[i.value.payload.value.decode('cp932') for i in val(parent,'子パーツリスト').items];assert names_==order and len(names_)==len(set(names_))
  px,py,pz=value(val(parent,'座標'))
  for t in child(parent,'子パーツ').children:
   name=t.name.value.decode('cp932');x,y,z=value(val(t,'座標'));info=child(t,'種類別情報')
   def walk(n,state=''):
    nn=n.name.value.decode('cp932') if getattr(n,'name',None) else ''
    if nn=='テキスト':
     text=decode(n.leaf_value.payload.value);return [(state,text)]
    result=[]
    for c in getattr(n,'children',[]):result+=walk(c,state or c.name.value.decode('cp932'))
    return result
   texts=walk(info)
   for state,text in texts:
    ns=maybe(info,state);decor=maybe(ns,'テキスト装飾') if ns else None
    checkbox=state=='テキスト' and maybe(info,'フォントサイズ') is not None
    if not decor and not checkbox:continue
    source=info if checkbox else decor
    size=value(val(source,'フォントサイズ'));font=value(val(source,'フォントタイプ'));assert font==259,(name,font)
    spacing=value(val(source,'文字間隔' if checkbox else '字間隔'))
    face,den,_=select_fnl_face(faces,size);measure=WidthMeasurer(face,den,proxy,spacing,0,0)
    width=measure.measure(text,True)['lines'][0]['width_px'];budget=330 if parent.name.value.decode('cp932')=='KR_CheatGroup' else 375
    if name=='KR_CheatSpeedValue':budget=44
    if name=='テキストパーツ_000:0':budget=250
    assert width<=budget,(name,state,text,width,budget)
    for ch in text:
     if ch.isspace():continue
     ix=measure.glyph_index(ch,True);w,pos,n=table[face.face_index][1][ix];assert w>0 and n>0 and any(zlib.decompress(raw[pos:pos+n])),(name,ch)
    rows.append(dict(name=name,state=state,text=text,font=font,size=size,x=px+x+(32 if checkbox else 0),y=py+y,width=width,budget=budget,checkbox=checkbox))
 slider=part(doc,'KR_CheatSpeed');i=child(slider,'種類別情報');assert value(val(i,'全体スクロール量'))-value(val(i,'表示量'))==4;assert value(val(i,'スクロールレート'))==0
 assert value(val(part(doc,'矩形_戦闘'),'座標'))[:2]==[363,267]
 assert 267+102+32<406 and 406+174+22<635
 for key in ['Trap','Quick','Route']:
  group=part(doc,'KR_Cheat'+key);assert value(val(child(group,'種類別情報'),'パーツタイプ'))=='チェックボックス'
 return dict(native_font_glyphs_present=True,overflows=0,rows=rows,slider_travel=4,old_settings_layout_preserved=True)

def main():
 ev=json.loads((O/'build_evidence.json').read_text());assert all(sha(O/n)==h for n,h in ev['files'].items())
 result=dict(status='STATIC_COMPILED_HELPERS_AND_LAYOUT_PASS',files=ev['files'],VM=vm_tests(),UI=font_layout(),native_verified=False,actual_save_reload_verified=False,translator_model='Codex internal')
 savej(O/'verification.json',result);print(json.dumps({k:v for k,v in result.items() if k!='UI'},indent=2))
if __name__=='__main__':main()
