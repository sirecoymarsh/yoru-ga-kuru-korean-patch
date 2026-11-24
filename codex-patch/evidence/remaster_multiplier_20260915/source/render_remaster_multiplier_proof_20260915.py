"""Render actual shipped FNL glyphs at the patched control coordinates, not game capture."""
import math,struct,zlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
from verify_remaster_multiplier_20260915 import O,R,ex,part,child,val,value,read,sha,ENC
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index

def main():
    p=read(O/'source_pointer.json');fp=Path(p['runtime'])/'NightRemasterFont.fnl';raw=fp.read_bytes()
    _,faces=parse_fnl_font(fp,3);table={};q=20
    for fn in range(struct.unpack_from('<I',raw,16)[0]):
        nf=struct.unpack_from('<I',raw,q)[0];q+=4
        for f in range(nf):
            h,u,n=struct.unpack_from('<III',raw,q);q+=12
            if fn==3:table[f]=(h,[struct.unpack_from('<HII',raw,q+10*i) for i in range(n)])
            q+=10*n
    proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()}
    im=Image.new('RGB',(734,310),(12,21,49));d=ImageDraw.Draw(im)
    d.text((12,6),'FNL + CONTROL GEOMETRY PROOF / NOT A GAME CAPTURE',font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13),fill=(170,187,210))
    def text(x,y,s,size):
        face,den,_=select_fnl_face(faces,size);m=WidthMeasurer(face,den,proxy,0,0,0)
        for c in s:
            idx=m.glyph_index(c,True);h,es=table[face.face_index];w,pos,n=es[idx]
            if not c.isspace():
                rawg=zlib.decompress(raw[pos:pos+n]);stride=len(rawg)//h
                bits=np.unpackbits(np.frombuffer(rawg,dtype=np.uint8).reshape(h,stride),axis=1,bitorder='big')[::-1]*255
                mask=Image.fromarray(bits,'L').resize((max(1,round(bits.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS)
                im.paste((244,247,255),(round(x),round(y)),mask)
            x+=w/den
    doc=ex.decode_ex(O/'pact_125_sliders.pactex');cas=part(doc,'レイアウト_カジュアル');kids=child(cas,'子パーツ')
    for t in kids.children:
        name=t.name.value.decode('cp932')
        if name.startswith('KR_Multiplier_') or name=='テキストパーツ_000:0':
            info=child(t,'種類別情報');x,y,z=value(val(t,'座標'));x+=20;y+=28
            normal=next((c for c in info.children if c.name.value.decode('cp932')=='通常状態'),None)
            if normal is not None:
                s=value(val(normal,'テキスト'));size=value(val(child(normal,'テキスト装飾'),'フォントサイズ'))
                if '_Value_' in name:s=str({'EX':1,'Training':2,'Money':5,'PairTraining':20}[name.split('_')[-1]])+'배'
                text(x,y,s,size)
            elif name in ['KR_Multiplier_EX','KR_Multiplier_Training','KR_Multiplier_Money','KR_Multiplier_PairTraining']:
                w,h=value(val(info,'長さ')),value(val(info,'幅'));d.rectangle((x,y,x+w,y+h),outline=(74,116,166))
                d.text((x+10,y+12),'NATIVE SLIDER BOUNDS',font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12),fill=(124,151,185))
    text(20,274,'1배   2배   5배   10배   19배   20배',22)
    im.save(O/'font_layout_proof.png')
    print(O/'font_layout_proof.png')

if __name__=='__main__':main()
