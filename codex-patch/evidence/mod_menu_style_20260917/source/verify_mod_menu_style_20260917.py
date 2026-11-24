"""Execute final renderer JAM with explicit native drawing/layout boundaries.
Captures commands, then renders native CG+FNL proof; this is not a game screenshot.
"""
from pathlib import Path
import copy,json,math,re,struct,zlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from build_mod_menu_style_20260917 import O,TYPE,PANEL,BUTTON,YELLOW,HOVER,CF,BLEND
from cheat_support_20260915 import sha,savej,read_meta
from build_route_perf_20260915 import symbol
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
from audit_dynamic_ui_20260915 import ENC

M=read_meta(O/'candidate_meta.json');FS={};seen={}
for f in M['functions']:
 n=symbol(M,f['index']);j=seen.get(n,0);seen[n]=j+1;FS[n+(f'#{j}' if j else '')]=f
def fval(x):return struct.unpack('<f',struct.pack('<I',x&0xffffffff))[0]
def fbits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def slots(t):return 2 if t[0] in (89,100) or t[0]==82 and t[3][0]==100 else int(t[0]!=0)
def normalize(s):
 labels={m.group(1):f'L{j}' for j,m in enumerate(re.finditer(r'^(0x[0-9a-f]+):',s,re.M))}
 return re.sub(r'0x[0-9a-f]+',lambda m:labels.get(m[0],m[0]),s)

class Font:
 def __init__(self,path):
  self.raw=path.read_bytes();_,self.faces=parse_fnl_font(path,3);q=20;self.tables={};self.checked=set()
  for fn in range(struct.unpack_from('<I',self.raw,16)[0]):
   nf=struct.unpack_from('<I',self.raw,q)[0];q+=4
   for fi in range(nf):
    h,u,n=struct.unpack_from('<III',self.raw,q);q+=12
    if fn==3:self.tables[fi]=(h,[struct.unpack_from('<HII',self.raw,q+10*j) for j in range(n)])
    q+=10*n
  self.proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()}
 def metrics(self,text,size):
  face,den,_=select_fnl_face(self.faces,size);measure=WidthMeasurer(face,den,self.proxy,0,0,0)
  return measure.measure(text,True)['lines'][0]['width_px'],self.tables[face.face_index][0]/den
 def text(self,im,text,x,y,size,color):
  face,den,_=select_fnl_face(self.faces,size);m=WidthMeasurer(face,den,self.proxy,0,0,0);h,es=self.tables[face.face_index]
  for c in text:
   w,p,n=es[m.glyph_index(c,True)]
   if not c.isspace():
    assert p and n and w,(c,size);raw=zlib.decompress(self.raw[p:p+n]);assert any(raw)
    bits=np.unpackbits(np.frombuffer(raw,dtype=np.uint8).reshape(h,len(raw)//h),axis=1,bitorder='big')[::-1]*255
    mask=Image.fromarray(bits,'L').resize((max(1,round(bits.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS)
    im.paste((2,5,15,255),(round(x),round(y)),mask.filter(ImageFilter.MaxFilter(3)))
    im.paste(tuple(color),(round(x),round(y)),mask);self.checked.add((c,size))
   x+=w/den

class VM:
 def __init__(self,path,tag,title,choices,size=20,gap=0):
  self.ops=[];self.labels={};self.commands=[];self.roots=[];self.finalized=False;self.font=FONT
  for line in path.read_text(encoding='utf8').splitlines():
   line=line.strip()
   if not line or line.startswith((';','FUNC','ENDFUNC','EOF')):continue
   if line.endswith(':'):self.labels[line[:-1]]=len(self.ops)
   else:self.ops.append(line.split(maxsplit=1))
  self.root=self.makepart('rect');self.counter=0
  self.obj={0:self.root[0],1:0,2:-1,3:0,4:[],5:title,6:[259,size,[244,248,255,255],0,fbits(1),[0,0,0,255]],7:[259,size,[255]*4,0,fbits(1),[0,0,0,255]],8:[0,fbits(8)],9:[0,fbits(gap)],10:2 if len(choices)>1 else 1,11:tag,12:0}
  self.original_color=copy.deepcopy(self.obj[6][2])
  for i,text in enumerate(choices):
   root=self.makepart('rect');self.roots.append(root[0])
   self.obj[4].append({0:[[255]*4,[255,255,0,255],[100,100,100,255]],1:i+1,2:text,6:root[0],7:0,'width':0,'height':0})
 def makepart(self,kind):
  # Mock vtable entries retain actual interface stack width but no native graphics.
  p={0:[('v',kind,i) for i in range(300)],'kind':kind,'id':len(getattr(self,'roots',[]))+300,'pos':[0,0]}
  return [p,0]
 def method(self,mid,obj,args):
  if isinstance(mid,tuple):
   _,kind,slot=mid
   if (kind,slot) in [('construction',13),('rect',5)]:
    if 'core' not in obj:obj['core']=self.makepart('core')[0];obj['core']['parent']=obj
    return [obj['core'],0],2
   if kind=='construction':
    if slot==4:self.commands=[];return None,0
    if slot==0:self.commands.append(args[0]);return None,0
    if slot==5:self.finalized=True;return None,0
   if kind=='core':
    if slot==31:return 777,1
    if slot==37:return [fbits(v) for v in obj['parent']['pos']],1
    if slot==38:obj['parent']['pos']=[fval(v) for v in args[0]];return None,0
    if slot in [50,57,171,226]:return None,0
   raise AssertionError((mid,args))
  if mid in [27905,27908,27911]:return obj[{27905:10,27908:11,27911:12}[mid]],1
  if mid==27904:
   w,h=self.font.metrics(obj[2],args[0][1]);obj['width']=math.ceil(w);obj['height']=math.ceil(h);return None,0
  if mid in [27895,27898]:return obj['width' if mid==27895 else 'height'],1
  if mid in [27897,27900]:obj['width' if mid==27897 else 'height']=args[0];return None,0
  if mid==27889:return [obj[6],obj[7]],2
  if mid==20822:return obj[1],1
  if mid in [20930,20933]:return obj[0 if mid==20930 else 1],1
  if mid in [20871,20877]:return obj[0 if mid==20871 else 2],1
  raise AssertionError(('method',mid,args))
 def call(self,n,args):
  if n=='AFL_Parts_CreateConstruction':return self.makepart('construction'),2
  if n.startswith('CASConstructionProcess::'):return (n,args),1
  if n=='AFL_View_GetHeight':return 720,1
  if n=='AFL_View_GetWidth':return 1280,1
  if n.startswith('Ｐ＿構築手順＿'):
   assert not self.finalized,('command after Build',n)
   self.commands.append((n,copy.deepcopy(args)));return None,0
  raise AssertionError(('call',n))
 def run(self):
  f=M['functions'][27936];vs=f['arguments']+f['variables'];li={};seen={};loc={i:-1 if slots(v['type']) else 0 for i,v in enumerate(vs)}
  for i,v in enumerate(vs):
   n=v['name'];n=n.encode('utf8','surrogateescape').decode('cp932') if any(0xdc80<=c<=0xdcff for c in map(ord,n)) else n
   j=seen.get(n,0);seen[n]=j+1;li[n+(f'#{j}' if j else '')]=i
  def ix(a):return li[json.loads(a) if a.startswith('"') else a]
  st=[];pc=0;steps=0
  while pc<len(self.ops):
   steps+=1;assert steps<100000;op,*args=self.ops[pc];a=args[0] if args else '';pc+=1
   if op=='PUSH':st.append(int(a,0))
   elif op=='PUSHLOCALPAGE':st.append(loc)
   elif op=='PUSHSTRUCTPAGE':st.append(self.obj)
   elif op=='.LOCALREF':
    # JAM .LOCALREF is the scalar SH_LOCALREF macro. Interface pairs use X_REF2.
    st.append(loc[ix(a)])
   elif op=='.LOCALDELETE':
    k=ix(a)
    for j in range(slots(vs[k]['type'])):loc[k+j]=-1
   elif op=='.LOCALASSIGN':k,v=a.rsplit(' ',1);loc[ix(k)]=int(v)
   elif op in ['.LOCALINC2','.LOCALINC3']:loc[ix(a)]+=1
   elif op=='.STRUCTREF':
    _,member=a.split(' ',1);fields=next(s for s in M['structures'] if s['name']=='C_SelectDialog')['members'];st.append(self.obj[next(i for i,v in enumerate(fields) if v['name']==member)])
   elif op=='S_PUSH':st.append(json.loads(a))
   elif op=='X_DUP':st.extend(st[-int(a):])
   elif op=='X_MOV':x,y=map(int,a.split());st[-x:]=st[-x:][-y:]+st[-x:][:-y]
   elif op=='X_REF':k=st.pop();p=st.pop();st.extend(p[k+j] for j in range(int(a)))
   elif op=='X_ASSIGN':
    size=int(a);vals=st[-size:];del st[-size:];k=st.pop();p=st.pop()
    assert isinstance(p,(dict,list)),('assign',pc,self.ops[max(0,pc-8):pc],type(p),k)
    for j,v in enumerate(vals):p[k+j]=v
    st.extend(vals)
   elif op=='A_REF':st[-1]=copy.deepcopy(st[-1])
   elif op in ['POP','DELETE','SP_INC']:st.pop()
   elif op=='PLUSA':v=st.pop();k=st.pop();p=st.pop();p[k]+=v;st.append(p[k])
   elif op in ['ADD','SUB','MUL','DIV','MOD','LT','LTE','GT','GTE','EQUALE']:
    b=st.pop();v=st.pop();st.append({'ADD':lambda:v+b,'SUB':lambda:v-b,'MUL':lambda:v*b,'DIV':lambda:int(v/b),'MOD':lambda:v%b,'LT':lambda:int(v<b),'LTE':lambda:int(v<=b),'GT':lambda:int(v>b),'GTE':lambda:int(v>=b),'EQUALE':lambda:int(v==b)}[op]())
   elif op in ['ITOF','FTOI']:st.append(fbits(st.pop()) if op=='ITOF' else int(fval(st.pop())))
   elif op in ['F_ADD','F_SUB','F_MUL']:
    b=fval(st.pop());v=fval(st.pop());st.append(fbits({'F_ADD':lambda:v+b,'F_SUB':lambda:v-b,'F_MUL':lambda:v*b}[op]()))
   elif op in ['IFZ','IFNZ']:
    if bool(st.pop())==(op=='IFNZ'):pc=self.labels[a]
   elif op=='JUMP':pc=self.labels[a]
   elif op=='CALLHLL':
    lib,n,_=a.split()
    if (lib,n)==('Array','Numof'):st.append(len(st.pop()))
    elif (lib,n)==('String','Length'):st.append(len(st.pop()))
    elif (lib,n)==('String','Split'):st.pop();sep=st.pop();s=st.pop();st.append(s.split(sep))
    elif (lib,n)==('Math','Max'):b=st.pop();v=st.pop();st.append(max(v,b))
    else:raise AssertionError(a)
   elif op in ['CALLFUNC','CALLMETHOD','NEW']:
    if op=='CALLFUNC':n=len(FS[a]['arguments']);aa=st[-n:] if n else [];del st[len(st)-n:];v,width=self.call(a,aa)
    elif op=='CALLMETHOD':
     n=int(a);aa=st[-n:] if n else [];del st[len(st)-n:];mid=st.pop();owner=st.pop();v,width=self.method(mid,owner,aa)
    else:
     typ,mid=a.rsplit(' ',1);n=len(M['functions'][int(mid)]['arguments']);v=st[-n:];del st[-n:];width=1
    if width==2:st.extend(v)
    elif width==1:st.append(v)
   elif op=='RETURN':assert not st,('stack',st);self.locals=loc;return
   else:raise AssertionError((op,a,pc))
  raise AssertionError('no return')

def render(v,path):
 w,h=v.locals[19],v.locals[20];im=Image.new('RGBA',(w,h))
 sources={PANEL:Image.open(O/'cg_1840.png').convert('RGBA'),BUTTON:Image.open(O/'cg_1500.png').convert('RGBA')}
 copies=[];titles=[]
 for n,a in v.commands:
  if n in [CF,BLEND]:
   _,cg,x,y,ww,hh,sx,sy,sw,sh,interp,state=a;source=sources[cg]
   assert min(x,y,sx,sy)>=0 and min(ww,hh,sw,sh)>0
   assert sx+sw<=source.width and sy+sh<=source.height and x+ww<=w and y+hh<=h
   tile=source.crop((sx,sy,sx+sw,sy+sh)).resize((ww,hh),Image.Resampling.NEAREST)
   if n==BLEND:im.alpha_composite(tile,(x,y))
   else:im.paste(tile,(x,y))
   copies.append(a)
  elif n.endswith('テキストアルファブレンド'):
   _,x,y,text,font,charspace,linespace,state=a
   for j,line in enumerate(text.splitlines()):FONT.text(im,line,x,y+j*(font[1]+linespace),font[1],font[2])
   titles.append(a)
 for info,root in zip(v.obj[4],v.roots):
  cx=w/2+root['pos'][0];cy=h/2+root['pos'][1];tw,gh=FONT.metrics(info[2],v.obj[7][1])
  assert tw+20<=info['width'] and gh+2<=40,(info[2],tw,info['width'],gh)
  FONT.text(im,info[2],cx-tw/2,cy-gh/2,v.obj[7][1],info[0][0])
 im.save(path)
 return copies,titles

def main():
 global FONT
 ev=json.loads((O/'build_evidence.json').read_text(encoding='utf8'));rt=Path(ev['source_pointer']['runtime']);FONT=Font(rt/'NightRemasterFont.fnl')
 tests=0
 for tag in [0,1,2,999,TYPE]:
  for n in [1,2,8,9]:
   for gap in [0,4,8]:
    choices=['유틸리티 추천']*n;v=VM(O/'built_27936.jam',tag,'자동 장착\n유지할 슬롯과 기준을 선택하세요.',choices,gap=gap);v.run()
    assert v.obj[6][2]==v.original_color
    if tag!=TYPE:
     old=VM(O/'original_27936.jam',tag,'자동 장착\n유지할 슬롯과 기준을 선택하세요.',choices,gap=gap);old.run()
     assert v.commands==old.commands
     for a,b in zip(v.obj[4],old.obj[4]):
      assert (a[0],a[1],a[2],a['width'],a['height'],a[6]['pos'])==(b[0],b[1],b[2],b['width'],b['height'],b[6]['pos'])
     assert [v.locals[k] for k in range(21)]==[old.locals[k] for k in range(21)]
    else:
     copies=[a for name,a in v.commands if name in [CF,BLEND]];assert len(copies)==9+3*n
     assert all(i['height']==48 and i[0][0]==list(YELLOW) and i[0][1]==list(HOVER) and i[0][2]==[100,100,100,255] for i in v.obj[4])
     for i,(info,root) in enumerate(zip(v.obj[4],v.roots)):
      cell=copies[9+3*i];_,_,x,y,*_=cell
      assert abs((v.locals[19]/2+root['pos'][0])-(x+(info['width']-8)/2))<=1
      assert abs((v.locals[20]/2+root['pos'][1])-(y+20))<=1
    tests+=1
 # Reversibility includes every byte in untouched branches; runtime helper entry
 # points, callbacks and rewards have unchanged addresses and original CODE bytes.
 edits=json.loads((O/'reversible_edits.json').read_text(encoding='utf8'));s=(O/'patch.jam').read_text(encoding='utf8')
 from build_instant_loot_20260915 import clean
 for x in reversed(edits):assert s.count(x['new'])==1;s=s.replace(x['new'],x['old'])
 assert s==clean((O/'original_27936.jam').read_text(encoding='utf8'),'C_SelectDialog@CreateParts')
 proofs=[]
 for key,title,labels,size in [
  ('sweep','자동 소탕 · 남은 탐색 시간 944\n　현재 층 기준: 전투 23회 / 보물상자 4개\n　보상 배율 적용 · 전투/함정 피해 없음\n　남은 시간을 모두 쓰고 다음 날로 진행할까요?',['취소','소탕 실행'],24),
  ('gear','자동 장착 · 현재 캐릭터의 장비만 추천\n　유지할 슬롯을 선택한 뒤 추천 기준을 고르세요.',['균형 추천','공격 추천','생존 추천','유틸리티 추천','1번 [변경] 함정 도구','2번 [유지] 회복 장비','3번 [변경] 없음','4번 [고정] 고정 장비','취소'],20),
  ('stone','요소석 추천 · 원작 가공 확인 후 적용',['균형 추천','공격 추천','생존 추천','유틸리티 추천','1번 [유지] 불의 요소석','2번 [변경] 없음','3번 [변경] 없음','취소'],20),
 ]:
  v=VM(O/'built_27936.jam',TYPE,title,labels,size=size,gap=8);v.run();copies,titles=render(v,O/f'{key}_proof.png')
  assert all(a[4][2]==list(YELLOW) for a in titles)
  proofs.append(dict(name=key,size=[v.locals[19],v.locals[20]],path=str(O/f'{key}_proof.png')))
 sheet=Image.new('RGB',(1100,sum(Image.open(p['path']).height+38 for p in proofs)+30),(12,18,36));d=ImageDraw.Draw(sheet);y=12
 mono=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
 for p in proofs:
  d.text((18,y),p['name'].upper()+' / NATIVE CG + FNL / NOT GAME CAPTURE',font=mono,fill=(145,165,195));im=Image.open(p['path']);sheet.paste(im,(18,y+22),im);y+=im.height+38
 sheet.save(O/'menu_style_proof.png')
 result=dict(status='MOD_MENU_STYLE_FIXTURES_PASS',files=ev['files'],renderer_cases=tests,unrelated_dialog_types_exact=True,
             all_cells_hitbox48=True,margin_and_root_centers_agree=True,commands_before_Build=True,title_color_restored=True,
             disabled_and_callbacks_unchanged=True,native_glyph_states_checked=len(FONT.checked),proofs=proofs,
             native_gameplay_verified=False,boundaries='Native Parts/CG commands and font metrics are fixture boundaries; exact compiled renderer branches execute. Proofs are reconstructions, not game screenshots.')
 savej(O/'verification.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
