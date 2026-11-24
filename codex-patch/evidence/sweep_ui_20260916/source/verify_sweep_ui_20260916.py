"""Compiled confirmation fixture and shipped-font layout proof (not a game capture)."""
from pathlib import Path
import json,struct,zlib,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from repair_sweep_ui_20260916 import O,TYPE,STATUS
from verify_dungeon_sweep_20260916 import VM,GLOBALS
from build_remaster_multiplier_20260915 import decode
from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
from audit_dynamic_ui_20260915 import ENC
from cheat_support_20260915 import sha,savej

def ops(path):
    code=[];labels={}
    for line in path.read_text(encoding='utf8').splitlines():
        line=line.strip()
        if not line or line.startswith((';','FUNC','ENDFUNC','EOF')):continue
        if line.endswith(':'):labels[line[:-1]]=len(code)
        else:code.append(line.split(maxsplit=1))
    return code,labels

class ConfirmVM(VM):
    def __init__(self):
        super().__init__();self.real_dialog=True;self.codes[31892]=ops(O/'built_31892.jam');self.g[268]={6:[259,30,None,0,1073741824],7:[259,32,None,0,1073741824],8:[0,0],11:0};self.choices=[]
    def run(self,n,args=(),obj=None):
        if n=='■選択ダイアログ／タイトル設定':self.title=decode(args[0].encode('cp932'));assert self.g[GLOBALS['Flags']]['lock'];return
        if n=='■選択ダイアログ／タイプ設定':self.g[268][11]=args[0];return
        if n=='■選択ダイアログ／選択肢追加':self.choices.append((args[0],decode(args[1].encode('cp932'))));return
        if n=='■選択ダイアログ／実行':
            assert self.g[GLOBALS['Flags']]['lock'];assert self.g[268][11]==TYPE
            assert self.g[268][6][1:2]==[24] and self.g[268][7][1:2]==[24]
            assert self.g[268][6][4]==1065353216 and self.g[268][8][1]==1090519040
            assert self.choices==[(12,'취소'),(11,'소탕 실행')];return self.choice
        return super().run(n,args,obj)

def main():
    ev=json.loads((O/'build_evidence.json').read_text());rt=Path(ev['source_pointer']['runtime']);cases=0;samples=[]
    for rem in [1,39,40,199,200,944,999,1000]:
        for lock in [False,True]:
            for choice in [-1,0,1,11,12]:
                v=ConfirmVM();v.choice=choice;v.g[GLOBALS['Flags']]['lock']=lock;before=copy.deepcopy(v.g)
                assert v.run('KR_SweepConfirm',[rem])==(choice==11)
                assert v.g[GLOBALS['Flags']]['lock']==lock
                for k in before:
                    if k!=268:assert v.g[k]==before[k]
                assert str(rem) in v.title and f'전투 {rem//40}회 / 보물상자 {rem//200}개' in v.title
                cases+=1
        samples.append(v.title)
    fp=rt/'NightRemasterFont.fnl';raw=fp.read_bytes();_,faces=parse_fnl_font(fp,3);table={};q=20
    for fontno in range(struct.unpack_from('<I',raw,16)[0]):
        nf=struct.unpack_from('<I',raw,q)[0];q+=4
        for fi in range(nf):
            h,u,n=struct.unpack_from('<III',raw,q);q+=12
            if fontno==3:table[fi]=(h,[struct.unpack_from('<HII',raw,q+10*j) for j in range(n)])
            q+=10*n
    proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};face,den,_=select_fnl_face(faces,24);measure=WidthMeasurer(face,den,proxy,0,0,0)
    h,es=table[face.face_index];checked=set();bounds=[]
    def width(s):return measure.measure(s,True)['lines'][0]['width_px']
    def draw_text(im,text,x,y):
        for c in text:
            idx=measure.glyph_index(c,True);w,pos,n=es[idx]
            if not c.isspace():
                assert pos and n and w,(c,idx);rg=zlib.decompress(raw[pos:pos+n]);assert any(rg)
                bits=np.unpackbits(np.frombuffer(rg,dtype=np.uint8).reshape(h,len(rg)//h),axis=1,bitorder='big')[::-1]*255
                mask=Image.fromarray(bits,'L').resize((max(1,round(bits.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS)
                edge=mask.filter(ImageFilter.MaxFilter(3));im.paste((2,5,15),(round(x),round(y)),edge);im.paste((244,248,255),(round(x),round(y)),mask);checked.add(c)
            x+=w/den
    for text in samples:
        lines=('　'+text+'　').splitlines();bw=max(map(len,lines))*24+4;th=4*24+3*8+48
        assert bw+12<900
        for i,line in enumerate(lines):
            assert 8+width(line)+2<bw-8,(line,width(line),bw)
            assert 8+i*32+h/den+2<th-6,(i,h/den,th)
        bounds.append(dict(width=bw+12,title_height=th,max_text_width=max(map(width,lines)),glyph_height=h/den))
    # Reconstruct only the panel from its existing primitive layout and native FNL.
    lines=('　'+samples[5]+'　').splitlines();bw=bounds[5]['width']-12;th=168;sh=52;fw=bw+12;fh=th+sh+10
    im=Image.new('RGB',(fw+40,fh+68),(13,18,38));d=ImageDraw.Draw(im);ox=20;oy=20
    def rect(x,y,w,h,c):d.rectangle((ox+x,oy+y,ox+x+w-1,oy+y+h-1),fill=c)
    border=(139,180,244);dark=(8,16,42)
    rect(6,6,bw-6,th-6,border);rect(0,0,bw-6,th-6,border);rect(7,7,bw-8,th-8,dark);rect(1,1,bw-8,th-8,(18,32,64))
    rect(18,th-1,bw-24,sh,border);rect(19,th-1,bw-26,sh-1,dark);rect(12,th-1,bw-24,sh-6,border);rect(15,th-1,bw-30,sh-9,(12,24,52));rect(bw//2,th-1,2,sh-9,border)
    for i,line in enumerate(lines):draw_text(im,line,ox+8,oy+8+i*32)
    for x,label in [(bw/4,'취소'),(bw*3/4,'소탕 실행')]:draw_text(im,label,ox+x-width(label)/2,oy+th+4)
    d.text((20,fh+35),'SHIPPED FONT / LAYOUT RECONSTRUCTION / NOT A GAME CAPTURE',font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12),fill=(150,180,210));im.save(O/'confirmation_layout_proof.png')
    savej(O/'verification.json',dict(status=STATUS,files=ev['files'],compiled_confirm_cases=cases,cancel_and_success_codes_verified=True,config_lock_restored=True,no_reward_changes=True,font_sha256=sha(fp),glyphs_checked=len(checked),samples=bounds,native_gameplay_verified=False))
    print('PASS',cases,'confirm fixtures; max width',max(x['width'] for x in bounds),'glyphs',len(checked))

if __name__=='__main__':main()
