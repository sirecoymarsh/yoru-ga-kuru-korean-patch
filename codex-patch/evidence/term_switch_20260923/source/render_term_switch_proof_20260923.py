"""Static native button geometry and shipped FNL proof, not a runtime capture."""
import copy,json,re
from pathlib import Path
from PIL import Image,ImageDraw
import build_term_switch_20260923 as b
from build_mod_tab_20260915 import coords,scalar
from verify_mod_menu_style_20260917 import Font
O=b.O

def main():
 ev=b.a.readj(O/'build_evidence.json');rt=Path(ev['source_pointer']['runtime']);d=b.ex.decode_ex(O/'pact_185_terms.pactex');font=Font(rt/'NightRemasterFont.fnl')
 button=b.part(d,'KR_TermConfigButton');label=b.part(d,'KR_TermConfigLabel');old=b.part(d,'KR_ItemConfigButton')
 rev=copy.deepcopy(button);b.rename(rev,'KR_ItemConfigButton');b.setlist(rev,'座標',coords(old));assert rev.serialize()==old.serialize()
 ti=b.txt_info(label);dec=b.child(ti,'テキスト装飾');text=b.decode(b.val(ti,'テキスト').value);size=scalar(b.val(dec,'フォントサイズ'));w,h=font.metrics(text,size);x,y,z=coords(label)
 assert coords(button)==[580,622,260] and abs(x-580-(192-w)/2)<0.001 and y==627 and h<=20 and w<=180
 assert scalar(b.val(label,'オンカーソル透過'))==1
 rect=[580,622,192,30];assert 363+192<rect[0] and rect[1]+rect[3]<670
 info=b.child(button,'種類別情報');prefix=b.val(info,'ＣＧ名').value.decode('cp932');ar=b.read_afa3(rt/'NightRemasterCG.afa')
 im=Image.new('RGBA',(600,170),(8,15,34,255));draw=ImageDraw.Draw(im);draw.text((12,8),'NATIVE TAB + SHIPPED FNL / NOT A GAME CAPTURE',fill='white')
 for i,state in enumerate(['通常','オン']):
  cg=prefix+'／'+state+'.qnt';entry=next(e for e in ar.entries if e.name in [cg,cg.encode('cp932')]);qnt=O/f'native_tab_{i}.qnt';png=O/f'native_tab_{i}.png'
  with (rt/'NightRemasterCG.afa').open('rb') as stream:stream.seek(entry.absolute_offset);qnt.write_bytes(stream.read(entry.size))
  b.cmd('cg','convert',qnt,png);plate=Image.open(png).convert('RGBA');assert plate.size==(192,42),plate.size
  tile=plate.resize((192,30),Image.Resampling.LANCZOS);px=20+i*290;py=58
  im.alpha_composite(tile,(px,py));font.text(im,text,px+(192-w)/2,py+5,size,(255,230,80,255))
  draw.text((px,100),'TERM SETTINGS BUTTON',fill='white')
 strings=[json.loads(m[0]) for m in re.finditer(r'"(?:[^"\\]|\\.)*"',(O/'helpers_readable.jaf').read_text('utf8'))]
 for s in strings:
  for c in set(s):
   if '\uac00'<=c<='\ud7a3':assert c in font.proxy,c
 im.save(O/'button_proof.png')
 b.save('visual_review.json',dict(status='STATIC_FONT_GEOMETRY_PASS',files=ev['files'],button=rect,label=dict(text=text,x=x,y=y,width=w,height=h),original_blue_chrome=True,yellow_color=[255,230,80],original_button_properties_exact_except_name_and_position=True,atlas_size=list(plate.size),font_sha256=b.a.sha(rt/'NightRemasterFont.fnl'),native_capture=False))
 print(O/'button_proof.png')
if __name__=='__main__':main()
