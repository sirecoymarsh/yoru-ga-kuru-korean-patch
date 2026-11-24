"""Static native button geometry and shipped FNL proof, not a runtime capture."""
import copy,json,re
from pathlib import Path
from PIL import Image,ImageDraw
import build_term_switch_20260923 as b
from build_mod_tab_20260915 import coords,scalar
from verify_mod_menu_style_20260917 import Font
from probe_player_tools_20260923 import O,save

def main():
 ev=b.a.readj(O/'build_evidence.json');rt=Path(ev['source_pointer']['runtime']);d=b.ex.decode_ex(O/'pact_185_player_tools.pactex');font=Font(rt/'NightRemasterFont.fnl')
 button=b.part(d,'KR_PlayerInfoButton');label=b.part(d,'KR_PlayerInfoLabel');old=b.part(d,'KR_TermConfigButton')
 rev=copy.deepcopy(button);b.rename(rev,'KR_TermConfigButton');b.setlist(rev,'座標',coords(old));assert rev.serialize()==old.serialize()
 ti=b.txt_info(label);dec=b.child(ti,'テキスト装飾');text=b.decode(b.val(ti,'テキスト').value);size=scalar(b.val(dec,'フォントサイズ'));w,h=font.metrics(text,size);x,y,z=coords(label)
 assert coords(button)==[797,622,260] and abs(x-797-(192-w)/2)<0.001 and y==627 and h<=20 and w<=180
 assert scalar(b.val(label,'オンカーソル透過'))==1
 rect=[797,622,192,30];assert 580+192<rect[0] and rect[1]+rect[3]<670
 info=b.child(button,'種類別情報');prefix=b.val(info,'ＣＧ名').value.decode('cp932');ar=b.read_afa3(rt/'NightRemasterCG.afa')
 im=Image.new('RGBA',(600,170),(8,15,34,255));draw=ImageDraw.Draw(im);draw.text((12,8),'NATIVE TAB + SHIPPED FNL / NOT A GAME CAPTURE',fill='white')
 for i,state in enumerate(['通常','オン']):
  cg=prefix+'／'+state+'.qnt';entry=next(e for e in ar.entries if e.name in [cg,cg.encode('cp932')]);qnt=O/f'native_tab_{i}.qnt';png=O/f'native_tab_{i}.png'
  with (rt/'NightRemasterCG.afa').open('rb') as stream:stream.seek(entry.absolute_offset);qnt.write_bytes(stream.read(entry.size))
  b.cmd('cg','convert',qnt,png);plate=Image.open(png).convert('RGBA');assert plate.size==(192,42),plate.size
  tile=plate.resize((192,30),Image.Resampling.LANCZOS);px=20+i*290;py=58
  im.alpha_composite(tile,(px,py));font.text(im,text,px+(192-w)/2,py+5,size,(255,230,80,255))
  draw.text((px,100),'PLAYER INFO BUTTON',fill='white')
 strings=[json.loads(m[0]) for m in re.finditer(r'"(?:[^"\\]|\\.)*"',(O/'helpers_readable.jaf').read_text('utf8'))]
 for s in strings:
  for c in set(s):
   if '\uac00'<=c<='\ud7a3':assert c in font.proxy,c
 im.save(O/'button_proof.png')
 import verify_mod_menu_style_20260917 as native
 native.FONT=font
 samples=b.a.readj(O/'verification.json')['examples']
 modal=[]
 for i,title in enumerate(samples):
  vm=native.VM(O/'built_27936.jam',native.TYPE,title,['주인공 이름 변경','닫기'],size=30,gap=0)
  vm.obj[7][1]=32;vm.obj[10]=1
  vm.run()
  width,height=vm.locals[19],vm.locals[20]
  assert width<=1280 and height<=720,(width,height)
  # The current fixed renderer uses solid native fills, not the old CG-copy commands.
  panel=Image.new('RGBA',(width,height));draw_panel=ImageDraw.Draw(panel)
  for name,args in vm.commands:
   if name=='CASConstructionProcess::Create':assert args==[width,height]
   elif name=='CASConstructionProcess::Fill#4':assert args==[0]
   elif name=='CASConstructionProcess::Fill#3':
    px,py,pw,ph,r,g,blue,alpha=args
    assert min(px,py)>=0 and pw>0 and ph>0 and px+pw<=width and py+ph<=height
    draw_panel.rectangle((px,py,px+pw-1,py+ph-1),fill=(r,g,blue,alpha))
   elif name=='Ｐ＿構築手順＿テキストアルファブレンド':
    _,px,py,txt,f,cs,ls,state=args
    for row,line in enumerate(txt.splitlines()):
     tw,th=font.metrics(line,f[1]);assert px+tw<=width and py+row*(f[1]+ls)+th<=height
     font.text(panel,line,px,py+row*(f[1]+ls),f[1],f[2])
   else:raise AssertionError(('unrendered native command',name))
  for info,root in zip(vm.obj[4],vm.roots):
   cx=width/2+root['pos'][0];cy=height/2+root['pos'][1];tw,gh=font.metrics(info[2],32)
   assert tw+20<=info['width'] and gh+2<=48
   font.text(panel,info[2],cx-tw/2,cy-gh/2,32,info[0][0])
  panel.save(O/f'menu_proof_{i}.png')
  modal.append(dict(width=width,height=height,title_lines=len(title.splitlines())))
 save('visual_review.json',dict(status='STATIC_FONT_GEOMETRY_PASS',files=ev['files'],button=rect,label=dict(text=text,x=x,y=y,width=w,height=h),original_blue_chrome=True,yellow_color=[255,230,80],original_button_properties_exact_except_name_and_position=True,atlas_size=list(plate.size),font_sha256=b.a.sha(rt/'NightRemasterFont.fnl'),native_capture=False,modal=modal))
 print(O/'button_proof.png')
if __name__=='__main__':main()
