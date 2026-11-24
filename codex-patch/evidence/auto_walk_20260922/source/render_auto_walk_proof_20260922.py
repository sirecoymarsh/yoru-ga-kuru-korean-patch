"""Native CG and shipped glyphs; static UI proof, not a game capture."""
import copy,json
from pathlib import Path
from PIL import Image,ImageDraw
from cheat_support_20260915 import R,sha,savej,cmd
from build_remaster_multiplier_20260915 import ex,part,child,val,txt_info,decode,read_afa3,rename
from build_mod_tab_20260915 import name,coords,scalar,remove
from verify_mod_menu_style_20260917 import Font
O=R/'staging/auto_walk_20260922'

def main():
 ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime']);d=ex.decode_ex(O/'pact_161_auto_walk.pactex');font=Font(rt/'NightRemasterFont.fnl')
 root=part(d,'KR_WalkRoot');assert coords(root)==[1142,436,41];assert scalar(val(root,'表示'))==0
 b=part(d,'KR_WalkButton');old=part(d,'KR_SweepButton');ren=copy.deepcopy(b);rename(ren,'KR_SweepButton');assert ren.serialize()==old.serialize()
 im=Image.new('RGBA',(520,260),(7,12,24,255));dr=ImageDraw.Draw(im);dr.text((12,7),'NATIVE CG + SHIPPED FONT / NOT A GAME CAPTURE',fill='white')
 ar=read_afa3(rt/'NightRemasterCG.afa');rows=[]
 for j,state in enumerate(['通常状態','オンカーソル状態','キーダウン状態']):
  cg=val(child(child(b,'種類別情報'),state),'ＣＧ名').value.decode('cp932')+'.qnt'
  entry=next(e for e in ar.entries if e.name==cg or e.name==cg.encode('cp932'))
  qnt=O/f'button_{j}.qnt';png=O/f'button_{j}.png'
  with (rt/'NightRemasterCG.afa').open('rb') as stream:stream.seek(entry.absolute_offset);qnt.write_bytes(stream.read(entry.size))
  cmd('cg','convert',qnt,png);plate=Image.open(png).convert('RGBA');assert plate.size==(116,55)
  dr.text((16+j*170,35),['NORMAL','HOVER','PRESSED'][j],fill='white')
  for k,n in enumerate(['KR_WalkStartLabel','KR_WalkStopLabel']):
   t=part(d,n);ti=txt_info(t);dc=child(ti,'テキスト装飾');text=decode(val(ti,'テキスト').value);size=scalar(val(dc,'フォントサイズ'));x,y,z=coords(t);w,h=font.metrics(text,size)
   assert abs(x-(116-w)/2)<.0001 and abs(y-(55-h)/2)<.0001
   assert scalar(val(t,'表示'))==1-k
   im.alpha_composite(plate,(16+j*170,60+k*90));font.text(im,text,16+j*170+x,60+k*90+y,size,(255,224,96,255))
   rows.append(dict(state=state,label=text,width=w,height=h,x=x,y=y))
 remove(part(d,'矩形_000'),'KR_WalkRoot');assert d.serialize_payload()==ex.decode_ex(O/'original_161.pactex').raw_payload
 im.save(O/'button_proof.png')
 savej(O/'visual_review.json',dict(status='STATIC_FONT_GEOMETRY_PASS',files=ev['files'],button_canvas=[116,55],button_rect=[1142,436,116,55],native_CG_states_byte_exact=True,only_added_group=True,labels=rows,font_sha256=sha(rt/'NightRemasterFont.fnl'),native_capture=False))
 print(O/'button_proof.png')
if __name__=='__main__':main()
