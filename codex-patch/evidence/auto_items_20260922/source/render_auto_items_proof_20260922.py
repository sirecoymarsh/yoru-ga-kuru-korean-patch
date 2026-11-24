"""Actual shipped glyphs and candidate geometry. This is not a game capture."""
import json,struct,zlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from cheat_support_20260915 import R,sha,savej
from build_remaster_multiplier_20260915 import ex,part,child,txt_info,val,decode
from build_mod_tab_20260915 import name,coords,scalar
from audit_dynamic_ui_20260915 import ENC
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
O=R/'staging/auto_items_20260922'

def main():
 ev=json.loads((O/'build_evidence.json').read_text());fp=Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl';raw=fp.read_bytes()
 _,faces=parse_fnl_font(fp,3);table={};q=20
 for fn in range(struct.unpack_from('<I',raw,16)[0]):
  nf=struct.unpack_from('<I',raw,q)[0];q+=4
  for f in range(nf):
   h,u,n=struct.unpack_from('<III',raw,q);q+=12
   if fn==3:table[f]=(h,[struct.unpack_from('<HII',raw,q+10*i) for i in range(n)])
   q+=10*n
 proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};rows=[]
 im=Image.new('RGB',(820,680),(12,21,49));d=ImageDraw.Draw(im);mono=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
 ox=-340;oy=18
 d.text((12,6),'SHIPPED FNL + CANDIDATE GEOMETRY / NOT A GAME CAPTURE',font=mono,fill=(174,189,211))
 def text(x,y,s,size,spacing=0):
  face,den,_=select_fnl_face(faces,size);m=WidthMeasurer(face,den,proxy,spacing,0,0);width=m.measure(s,True)['lines'][0]['width_px']
  assert x+width<=1120 and y+face.height/den<=653,(s,x,y,width)
  rows.append(dict(text=s,x=x,y=y,size=size,width=width))
  for c in s:
   idx=m.glyph_index(c,True);h,es=table[face.face_index];w,pos,n=es[idx]
   if not c.isspace():
    assert pos and n,(s,c);rawg=zlib.decompress(raw[pos:pos+n]);stride=len(rawg)//h
    bits=np.unpackbits(np.frombuffer(rawg,dtype=np.uint8).reshape(h,stride),axis=1,bitorder='big')[::-1]*255
    mask=Image.fromarray(bits).resize((max(1,round(bits.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS)
    im.paste((241,246,255),(round(x+ox),round(y+oy)),mask)
   x+=w/den+spacing
 p=ex.decode_ex(O/'pact_187_auto_items.pactex');sliders=[]
 for t in child(p.blocks[2].payload.children[0],'子パーツ').children:
  nm=name(t)
  if not nm.startswith('KR_Items'):continue
  x,y,z=coords(t);info=child(t,'種類別情報');typ=val(info,'パーツタイプ').value.decode('cp932')
  if typ=='横スクロールバー':
   scale=[scalar(i.value.payload) for i in val(t,'拡大縮小').items];total=scalar(val(info,'全体スクロール量'));assert total==(81 if nm=='KR_ItemsThreshold' else 100)
   assert scalar(val(info,'表示量'))==1 and scalar(val(info,'ボタンクリック移動量'))==1
   height=42*scale[1];width=320*scale[0];assert height<31
   if nm=='KR_ItemsThreshold':assert y+height<247
   else:assert y+height<283+int(nm[-1])*64
   d.rectangle((x+ox,y+oy,x+ox+width,y+oy+height),outline=(75,112,155));d.text((x+ox+10,y+oy+9),f'NATIVE SLIDER / {total-1} STEPS',font=mono,fill=(170,187,210));sliders.append(nm)
  elif typ=='チェックボックス':
   d.rectangle((x+ox,y+oy,x+ox+32,y+oy+32),outline=(75,112,155))
   text(x+32,y+3,decode(val(info,'テキスト').value),scalar(val(info,'フォントサイズ')),scalar(val(info,'文字間隔')))
  else:
   ti=txt_info(t);deco=child(ti,'テキスト装飾');s=decode(val(ti,'テキスト').value)
   if 'ReserveValue' in nm:s='99개'
   if nm=='KR_ItemsThresholdValue':s='90% 이하'
   text(x,y,s,scalar(val(deco,'フォントサイズ')),scalar(val(deco,'字間隔')))
 assert len(sliders)==6
 im.save(O/'font_layout_proof.png')
 savej(O/'visual_review.json',dict(status='STATIC_FONT_GEOMETRY_PASS',files=ev['files'],rows=rows,slider_steps=[80,99,99,99,99,99],native_slider_graphic_height=30,unchanged_native_CG=True,native_capture=False,font_sha256=sha(fp)))
 print(O/'font_layout_proof.png')
if __name__=='__main__':main()
