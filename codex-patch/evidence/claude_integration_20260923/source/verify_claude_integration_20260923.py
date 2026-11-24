"""Independent byte/leaf/glyph checks and actual FNL representative render."""
from pathlib import Path
import json,struct,zlib,re,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import review_claude_handoff_20260923 as a
from integrate_claude_revision_20260923 import O,BASE

def main():
    ev=a.readj(O/'build_evidence.json');assert a.sha(O/'NightRemaster.ain')==ev['files']['NightRemaster.ain']
    assert a.sha(O/'baseline.ain')==BASE and not a.readj(O/'layout_failures.json') and not a.readj(O/'unresolved_width.json')
    p,s,e,old=a.raw_messages((O/'baseline.ain').read_bytes());q,t,u,new=a.raw_messages((O/'NightRemaster.ain').read_bytes())
    assert len(old)==len(new)==100944 and p[:s+12]==q[:t+12] and p[e:]==q[u:]
    proxy=a.readj(a.PROXY);dec={x['proxy_character']:x['unicode_character'] for x in proxy['mapping']}
    decode=lambda b:''.join(dec.get(c,c) for c in b.decode('cp932'))
    texts=[decode(b) for b in new];edits=a.readj(O/'final_edits.json');ids={int(i) for i in edits}
    assert {i for i,(x,y) in enumerate(zip(old,new)) if x!=y}==ids and all(texts[int(i)]==v for i,v in edits.items())
    fp=Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl';font=fp.read_bytes()
    _,faces=a.parse_fnl_font(fp,0);face,den,_=a.select_fnl_face(faces,60)
    indices,_=a.load_proxy_indices(proxy,len(face.widths));meter=a.WidthMeasurer(face,den,indices,-2,2,0)
    classes={x['message_id']:x for x in a.readj(a.HERE/'message_window_classification.json')['rows']}
    widths=[]
    for i in sorted(ids):
        c=classes[i];assert not c['ambiguous'] and c['message_roles']==['Body'] and c['font_commands']==[0]
        limit=668 if c['window_types']==['Face'] else 884;w=meter.measure(texts[i],True)['max_width_px'];assert w<=limit,(i,w,limit)
        assert re.findall(r'[\x00-\x1f\x7f]|료　　　　',decode(old[i]))==re.findall(r'[\x00-\x1f\x7f]|료　　　　',texts[i])
        widths.append(dict(m_id=i,width_px=w,budget_px=limit))
    # Parse the physical glyph directory and decompress every non-space glyph used by the patch.
    cursor=20;table={}
    for fn in range(struct.unpack_from('<I',font,16)[0]):
        nfaces=struct.unpack_from('<I',font,cursor)[0];cursor+=4
        for fi in range(nfaces):
            h,unknown,n=struct.unpack_from('<III',font,cursor);cursor+=12
            if fn==0:table[fi]=(h,[struct.unpack_from('<HII',font,cursor+10*i) for i in range(n)])
            cursor+=10*n
    h,entries=table[face.face_index];masks={}
    for c in set(''.join(edits.values())):
        if c.isspace():continue
        gi=meter.glyph_index(c,True);w,pos,n=entries[gi];assert pos and n and w,(c,gi)
        bits=zlib.decompress(font[pos:pos+n]);assert len(bits)%h==0
        arr=np.unpackbits(np.frombuffer(bits,dtype=np.uint8).reshape(h,-1),axis=1,bitorder='big')[::-1]*255
        assert arr.any(),('empty glyph',c,gi)
        masks[c]=Image.fromarray(arr).resize((max(1,round(arr.shape[1]/den)),round(h/den)),Image.Resampling.LANCZOS)
    examples=[5123,5717,33021,33022,65344,62912,72313,72314]
    im=Image.new('RGB',(960,90+len(examples)*110),(12,21,49));d=ImageDraw.Draw(im);mono=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14)
    d.text((24,14),'SHIPPED FNL / FINAL MSG1 / NOT A GAME CAPTURE',font=mono,fill=(168,199,222))
    for row,i in enumerate(examples):
        y=62+row*110;limit=668 if classes[i]['window_types']==['Face'] else 884
        d.text((24,y),f'MSG {i} / {meter.measure(texts[i],True)["max_width_px"]:.0f} <= {limit}px',font=mono,fill=(168,199,222))
        d.rectangle((24,y+22,24+limit,y+90),outline=(79,108,153));x=24.
        for c in texts[i]:
            gi=meter.glyph_index(c,True);w,_,_=entries[gi]
            if not c.isspace():
                mask=masks.get(c)
                if mask is None: # The example may deliberately retain a baseline glyph.
                    raise AssertionError(('proof glyph not included',c))
                im.paste((240,246,255),(round(x+2),y+26),mask)
            x+=w/den+2
    im.save(O/'font_layout_proof.png')
    # Alice-tools successfully parsed this exact final candidate (generated immediately before this check).
    assert (O/'candidate_meta.json').stat().st_size>100000
    json.loads((O/'candidate_meta.json').read_text(encoding='utf8',errors='surrogateescape'))
    report=dict(status='MSG1_STRUCTURE_FONT_LAYOUT_PASS',files=ev['files'],changed_fields=len(ids),
                message_count=100944,outside_MSG1_exact=True,width_overflow=0,glyphs_nonempty=len(masks),
                metadata_sha256=a.sha(O/'candidate_meta.json'),font_sha256=a.sha(fp),native_tested=False,
                proof='font_layout_proof.png',widths=widths)
    (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='widths'},ensure_ascii=False))

if __name__=='__main__':main()
