"""Technical proof of shipped FNL glyphs and control coordinates; not game capture."""
import json,struct,zlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
from verify_remaster_multiplier_20260915 import ENC

O=Path('cheat_menu_20260915')
def main():
    qa=json.loads((O/'verification.json').read_text(encoding='utf8'))
    ev=json.loads((O/'build_evidence.json').read_text(encoding='utf8'))
    fp=Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl'; raw=fp.read_bytes()
    _,faces=parse_fnl_font(fp,3);table={};q=20
    for fn in range(struct.unpack_from('<I',raw,16)[0]):
        nf=struct.unpack_from('<I',raw,q)[0];q+=4
        for f in range(nf):
            h,u,n=struct.unpack_from('<III',raw,q);q+=12
            if fn==3:table[f]=(h,[struct.unpack_from('<HII',raw,q+10*i) for i in range(n)])
            q+=10*n
    proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()}
    im=Image.new('RGB',(830,460),(12,21,49));d=ImageDraw.Draw(im)
    mono=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
    d.text((14,8),'ACTUAL FNL GLYPHS + CONTROL GEOMETRY / NOT A GAME CAPTURE',font=mono,fill=(174,189,211))
    ox,oy=-340,-220
    def rect(x,y,w,h):
        d.rectangle((x+ox,y+oy,x+ox+w,y+oy+h),outline=(75,112,155))
    for x,y in [(363,369),(783,451),(783,491),(783,531)]:rect(x,y,32,32)
    rect(363,317,320,38)
    d.text((373+ox,328+oy),'NATIVE SLIDER: 1 / 2 / 3 / 4 / 5',font=mono,fill=(128,157,189))
    rect(783,656,330,38)
    d.text((792+ox,666+oy),'EXISTING BOTTOM BUTTON ROW',font=mono,fill=(128,157,189))
    def draw_text(x,y,s,size,spacing):
        face,den,_=select_fnl_face(faces,size);m=WidthMeasurer(face,den,proxy,spacing,0,0)
        for c in s:
            idx=m.glyph_index(c,True);h,es=table[face.face_index];w,pos,n=es[idx]
            if not c.isspace():
                rawg=zlib.decompress(raw[pos:pos+n]);stride=len(rawg)//h
                bits=np.unpackbits(np.frombuffer(rawg,dtype=np.uint8).reshape(h,stride),axis=1,bitorder='big')[::-1]*255
                mask=Image.fromarray(bits,'L').resize((max(1,round(bits.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS)
                im.paste((241,246,255),(round(x+ox),round(y+oy)),mask)
            x+=w/den+spacing
    for row in qa['UI']['rows']:
        draw_text(row['x'],row['y'],row['text'],row['size'],-2 if row['checkbox'] else 0)
    im.save(O/'font_layout_proof.png')
    print(O/'font_layout_proof.png')
if __name__=='__main__':main()
