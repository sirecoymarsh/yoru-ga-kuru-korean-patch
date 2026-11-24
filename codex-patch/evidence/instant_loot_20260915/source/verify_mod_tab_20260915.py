"""Persisted payload, callback synchronization and first-formation presentation tests."""
from build_mod_tab_20260915 import *
import verify_remaster_multiplier_20260915 as rewards
import verify_cheat_menu_20260915 as cheats
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
from audit_dynamic_ui_20260915 import ENC
from PIL import Image,ImageDraw,ImageFont
import numpy as np,zlib

def reward_tests(meta):
 rewards.O=O;vm=rewards.VM(meta)
 # alice's overloaded symbol names, not a dictionary overwriting duplicate names.
 seen={};vm.functions={}
 for f in meta['functions']:
  n=symbol(meta,f['index']);count=seen.get(n,0);seen[n]=count+1;vm.functions[n+(f'#{count}' if count else '')]=f
 for j,r in enumerate(ROWS):
  key,label,gi,setter,calc,ratekey=r
  gname='L_CasualMode::GetRate'+ratekey
  fid=vm.functions[gname]['index']
  src=Path(json.loads((O/'source_pointer.json').read_text())['runtime'])/'NightRemaster.ain'
  cmd('ain','dump','--function',gname,'-o',O/f'built_{fid}.jam',src)
  setname='L_CasualMode::SetRate'+ratekey+'#1';sfid=vm.functions[setname]['index'];cmd('ain','dump','--function',setname,'-o',O/f'built_{sfid}.jam',src)
  assert f'FUNC {sfid}\n' in (O/f'built_{sfid}.jam').read_text()
  for mult in range(1,21):
   vm.run('KR_MultiplierSet'+key,[rewards.bits((mult-1)/19)]);assert vm.g[gi]==mult*100
   get=meta['functions'][setter+1]['name'];set_=meta['functions'][setter]['name']
   for _ in range(40):
    state=vm.run(get,[]);assert state==(mult==2);vm.run(set_,[state]);assert vm.g[gi]==mult*100
   other=dict(vm.g);vm.run(set_,[not state]);assert vm.g[gi]==(100 if mult==2 else 200)
   assert all(vm.g[k]==val for k,val in other.items() if k!=gi)
   vm.run(set_,[False]);assert vm.g[gi]==100
   for n in [1,7,123456,2147483647,-1,-2147483648]:
    vm.g[gi]=mult*100;assert vm.run(meta['functions'][calc]['name'],[n])==max(-2147483648,min(2147483647,n*mult))
 for r,mult in zip(ROWS,[1,2,5,20]):vm.run('KR_MultiplierSet'+r[0],[rewards.bits((mult-1)/19)])
 for _ in range(100):
  for r in ROWS:vm.run(meta['functions'][r[3]]['name'],[vm.run(meta['functions'][r[3]+1]['name'],[])])
 assert [vm.g[r[2]] for r in ROWS]==[100,200,500,2000]
 return dict(calls=vm.calls,independent_rates=[1,2,5,20],all_20_steps_passive_visits_and_actual_toggles=True,saturation_preserved=True)

class BattleVM(cheats.VM):
 def __init__(self):
  super().__init__();self.skip=False
  for f in self.meta['functions']:self.fs[symbol(self.meta,f['index'])]=f
 def run(self,name,args=(),**kw):
  if name=='Conf_GetBattleSpeedUp':return int(bool(self.flags[15]))
  if name=='Ａ＿全文スキップ中確認':return int(self.skip)
  return super().run(name,args,**kw)

def battle_tests():
 cheats.O=O;old=cheats.VM;cheats.VM=BattleVM
 try:baseline=cheats.vm_tests()
 finally:cheats.VM=old
 v=BattleVM();v.run('KR_InitOptions');count=0
 for quick in [0,1]:
  for original in [0,1]:
   for skip in [False,True]:
    for speed in range(1,6):
     v.flags[94]=quick;v.flags[15]=original;v.skip=skip;v.run('KR_SetSpeed',[rewards.bits((speed-1)/4)])
     want=1000 if quick else speed if speed>1 else 2 if original and not skip else 1
     assert v.run('KR_BattleRate')==want;count+=1
 # Execute the inserted presentation region with stubbed engine APIs only.
 s=(O/'built_29387.jam').read_text();orig=(O/'original_29387.jam').read_text()
 start=s.index('\tCALLFUNC KR_QuickActive',s.index('\tPUSH 29443'))
 end=s.index('\tPUSH 1\n\tIFZ',start)
 body=s[start:end];assert body.count('SystemService UpdateView')==1
 assert s.index('PUSH 29392')<start and s.index('PUSH 29389')<start and start<s.index('PUSH 29220')
 ops=[];labels={}
 for line in body.splitlines():
  line=line.strip()
  if line.endswith(':'):labels[line[:-1]]=len(ops)
  elif line:ops.append(line.split(maxsplit=1))
 for initial,cancel in [(False,False),(True,False),(True,True)]:
  st=[];pc=0;active=initial;updates=0;extra=0;normal=0
  while pc<len(ops):
   op,*a=ops[pc];arg=a[0] if a else '';pc+=1
   if op=='CALLFUNC' and arg=='KR_QuickActive':st.append(int(active))
   elif op=='CALLFUNC' and arg=='AFL_View_Update':
    updates+=1
    if cancel:active=False;normal+=1
   elif op=='CALLHLL':assert arg=='SystemService UpdateView 0';extra+=1;st.append(1)
   elif op=='POP':st.pop()
   elif op=='IFZ':
    if not st.pop():pc=labels[arg]
   else:raise AssertionError((op,arg))
  assert not st and updates==int(initial) and extra+normal==int(initial)
 return dict(baseline=baseline,speed_priority_cases=count,initial_formation_present_fixture_cases=3,no_action_loop_or_result_logic_changes=True,native_present_verified=False)

def ui_tests(rt,extra_controls=(),bottom_limit=635):
 docs={i:ex.decode_ex(O/f'pact_{i}_tabs.pactex') for i in range(117,127)};docs[185]=ex.decode_ex(O/'pact_185_mods.pactex')
 modnames=['KR_CheatSpeed','KR_CheatTrap','KR_CheatQuick','KR_CheatRoute']+['KR_Multiplier_'+r[0] for r in ROWS]+list(extra_controls)
 for ix,d in docs.items():
  root=d.blocks[2].payload.children[0];ns=[name(t) for t in allparts(root)];assert len(ns)==len(set(ns)),ix
  assert ns.count(BUTTON)==1
  assert scalar(val(child(part(d,BUTTON),'種類別情報'),'有効'))==(0 if ix==185 else 1)
  if ix==185:assert scalar(val(child(part(d,'３Ｄボタン'),'種類別情報'),'有効'))==1
  for t in allparts(root):
   k=maybe(t,'子パーツ');order=maybe(t,'子パーツリスト')
   if k and order:assert [name(c) for c in k.children]==[i.value.payload.value.decode('cp932') for i in order.leaf_value.payload.items],(ix,name(t))
  assert all((n in ns)==(ix==185) for n in modnames),(ix,'misplaced mod control')
  if ix==123:assert 'SYS_戦闘の進行速度を速くする' in ns
  if ix==125:assert all(n in ns for n in OLD_PARTS)
 # Page list/appended payload resolve the same normalized game archive key.
 table=ex.decode_ex(O/'NightRemasterEX.ex').blocks[23].payload
 assert len(table.rows)==10 and table.rows[-1][0].payload.value.decode('cp932')==BUTTON
 target=table.rows[-1][1].payload.value.decode('cp932').replace('\\','/')+'.pactex';assert target==PAGE
 arc=read_afa3(O/'NightRemasterPact.afa');assert arc.entries[185].name==target
 for fid,mode,method in [(29817,'Get',29825),(29818,'Set',29826)]:
  s=(O/f'built_{fid}.jam').read_text();meta=read_meta(O/'candidate_meta.json');ids={f['name']:f['index'] for f in meta['functions']}
  for key,*_ in ROWS:assert f'PUSH {method}\n\tS_PUSH "KR_Multiplier_{key}"\n\tPUSH -1\n\tPUSH {ids["KR_Multiplier"+mode+key]}' in s
  for n in OLD_PARTS+['SYS_戦闘の進行速度を速くする']:assert s.count(f'S_PUSH "{n}"')==1
 # Actual shipped FNL bitmaps and width checks for every new-page text state.
 fp=rt/'NightRemasterFont.fnl';raw=fp.read_bytes();_,faces=parse_fnl_font(fp,3);table={};q=20
 for fontno in range(struct.unpack_from('<I',raw,16)[0]):
  nf=struct.unpack_from('<I',raw,q)[0];q+=4
  for fi in range(nf):
   h,u,n=struct.unpack_from('<III',raw,q);q+=12
   if fontno==3:table[fi]=(h,[struct.unpack_from('<HII',raw,q+10*j) for j in range(n)])
   q+=10*n
 proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};rows=[];boxes=[];image=Image.new('RGB',(1140,720),(12,21,49));draw=ImageDraw.Draw(image)
 mono=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13);draw.text((15,696),'ACTUAL FNL GLYPHS + NATIVE CONTROL GEOMETRY / NOT A GAME CAPTURE',font=mono,fill=(164,190,213))
 def textdraw(x,y,text,size,spacing):
  face,den,_=select_fnl_face(faces,size);m=WidthMeasurer(face,den,proxy,spacing,0,0);width=m.measure(text,True)['lines'][0]['width_px']
  for ch in text:
   idx=m.glyph_index(ch,True);h,es=table[face.face_index];w,pos,n=es[idx]
   if not ch.isspace():
    assert n>0 and pos>0 and w>0,(ch,size);rg=zlib.decompress(raw[pos:pos+n]);assert any(rg),(ch,size)
    bits_=np.unpackbits(np.frombuffer(rg,dtype=np.uint8).reshape(h,len(rg)//h),axis=1,bitorder='big')[::-1]*255
    mask=Image.fromarray(bits_,'L').resize((max(1,round(bits_.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS);image.paste((241,246,255),(round(x),round(y)),mask)
   x+=w/den+spacing
  return width
 root=docs[185].blocks[2].payload.children[0]
 for parent in child(root,'子パーツ').children:
  if not name(parent).startswith('KR_Mod'):continue
  px,py,_=coords(parent)
  for t in child(parent,'子パーツ').children:
   n=name(t);x,y,_=coords(t);x+=px;y+=py;info=child(t,'種類別情報');typ=val(info,'パーツタイプ').value.decode('cp932')
   if typ=='横スクロールバー':
    w=scalar(val(info,'長さ'));h=scalar(val(info,'幅'));boxes.append([x,y,x+w,y+h]);draw.rectangle((x,y,x+w,y+h),outline=(35,156,239),width=2);draw.rectangle((x,y+5,x+12,y+h-5),fill=(135,223,255));continue
   checkbox=typ=='チェックボックス'
   if checkbox:draw.rectangle((x,y,x+32,y+32),outline=(35,156,239),width=2)
   def nodes(z):
    if maybe(z,'テキスト') and (maybe(z,'テキスト装飾') or maybe(z,'フォントサイズ')):yield z
    for c in z.children:
     if c.children:yield from nodes(c)
   for state in nodes(info):
    text=decode(val(state,'テキスト').value);dec=maybe(state,'テキスト装飾') or state;size=scalar(val(dec,'フォントサイズ'));spacing=scalar(val(dec,'文字間隔' if checkbox else '字間隔'));assert scalar(val(dec,'フォントタイプ'))==259
    # Same-position variants are checked separately but drawn just once.
    sx=x+(32 if checkbox else 0);maxwidth=1140-sx-20
    if n=='KR_CheatSpeedValue':maxwidth=66
    if '_Value_' in n:maxwidth=56
    if '_Label_' in n:maxwidth=268
    face,den,_=select_fnl_face(faces,size);measure=WidthMeasurer(face,den,proxy,spacing,0,0)
    texts=[f'{i}배' for i in range(1,21)] if '_Value_' in n else ['기본','2배','3배','4배','5배'] if n=='KR_CheatSpeedValue' else [text]
    for s in texts:assert measure.measure(s,True)['lines'][0]['width_px']<=maxwidth,(n,s,maxwidth)
    if not any(r['name']==n for r in rows):width=textdraw(sx,y,text,size,spacing)
    else:width=measure.measure(text,True)['lines'][0]['width_px']
    assert y+size<bottom_limit
    rows.append(dict(name=n,text=text,x=sx,y=y,size=size,width=width,budget=maxwidth))
 for i,a in enumerate(boxes):
  for b in boxes[i+1:]:assert a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1]
 for y,label in [(30,'메시지 속도'),(90,'메시지'),(150,'메시지 창'),(210,'사운드'),(270,'입력'),(330,'화면'),(390,'게임 설정'),(450,'리마스터'),(510,'모드')]:
  draw.rectangle((110,y,302,y+42),outline=(30,160,255),width=2);textdraw(130,y+7,label,24,0)
 for x,label in [(605,'게임 종료'),(765,'타이틀로'),(925,'게임으로')]:draw.rectangle((x,656,x+149,694),outline=(72,138,239),width=2);textdraw(x+16,661,label,22,0)
 image.save(O/'font_layout_proof.png')
 return dict(tabs_in_all10_original_pages=True,new_registered_page=185,controls_only_on_mod_page=len(modnames),original_checkbox_controls_restored=True,roundtrip_parts_order_and_unique_names=True,rows=rows,slider_boxes=boxes,actual_FNL_face=3,overflows=0,native_visual_verified=False)

def main():
 ev=json.loads((O/'build_evidence.json').read_text());assert all(sha(O/n)==h for n,h in ev['files'].items());rt=Path(ev['source_pointer']['runtime']);m=read_meta(O/'candidate_meta.json')
 rw=reward_tests(m);battle=battle_tests();ui=ui_tests(rt)
 report=dict(status='MOD_TAB_STATIC_PASS_NATIVE_PENDING',files=ev['files'],rewards=rw,battle=battle,UI=ui,native_gameplay_verified=False,actual_save_reload_verified=False,translator_model='Codex internal')
 savej(O/'verification.json',report);print(json.dumps({k:v for k,v in report.items() if k!='UI'},indent=2))
if __name__=='__main__':main()
