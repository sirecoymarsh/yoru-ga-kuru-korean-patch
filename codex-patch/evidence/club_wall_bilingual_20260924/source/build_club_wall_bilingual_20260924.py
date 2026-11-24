"""Source-bound graphics-only repair; preserve the latest code, saves and English captions."""
from pathlib import Path
import json, hashlib, struct, shutil, copy
import numpy as np
import cv2
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, binary_dilation
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
import repair_ui_banners_20260913 as banners
from ui_container_tools_20260912 import R, source_archive, encode, run, read_afa3
from build_remaster_multiplier_20260915 import rebuild

O=R/'staging/club_wall_bilingual_20260924'
S=Path('P:/AI/Codex/game_localization/YoruGaKuru_Remastered_KO_Project/extracted/images/NightRemasterCG_png')
IDS=[485,981,1004,1318,1319]
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def bounds(mask):
    y,x=np.where(mask);return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None
def png(path,a):Image.fromarray(a.astype('uint8')*255 if a.dtype==bool else a).save(path)

def banner(n):
    source=banners.get(n)
    old=copy.deepcopy(banners.SPEC[n]);banners.SPEC[n]=old[:1]
    try: primary=banners.repaired(n)[2]
    finally:banners.SPEC[n]=old
    split={485:183,981:173,1004:224}[n]
    face=(source[:,:,:3].min(2)>235)&(source[:,:,3]>200)
    english=face.copy();english[:split]=False
    japanese=face.copy();japanese[split:]=False
    de=distance_transform_edt(~english);dj=distance_transform_edt(~japanese)
    profile,_=banners.glow_profile(n)
    def glow(distance):
        p=np.stack([np.interp(distance*2,np.arange(len(profile)),profile[:,j],right=0) for j in range(4)],2)
        out=np.zeros_like(source);out[:,:,3]=np.uint8(p[:,:,3].round());nz=out[:,:,3]>0
        out[nz,:3]=np.uint8(np.clip(p[nz,:3]*255/p[nz,3,None],0,255).round());return out
    # The shared halo cannot be sliced along its ownership boundary: that makes
    # angular seams. Reconstruct only that halo from the original distance profile,
    # retaining the original Latin glyphs/AA and near glow byte-for-byte.
    clean=glow(de);exact=(de<=3)&(dj>2);clean[exact]=source[exact]
    oldface=banners.face_layer((source.shape[1],source.shape[0]),*old[0][1:])
    dp=distance_transform_edt(oldface<128)
    final=glow(np.minimum(dp,de))
    # Reuse complete already-localized primary face and its AA, not regenerated Latin.
    primary_owned=dp<=3;final[primary_owned]=primary[primary_owned]
    final[exact]=source[exact]
    assert np.array_equal(final[english],source[english])
    assert not ((clean[:,:,:3].min(2)>235)&(clean[:,:,3]>200)&japanese).any()
    erase=np.any(clean!=source,axis=2);target=np.any(final!=clean,axis=2)
    return source,clean,final,erase,target,dict(source=old[0][0],target=old[0][1],english=old[1][0],english_near_face_pixel_identity=True,
        english_exact_pixels=int(exact.sum()),split_y=split,mask_method='Erase complete Japanese glyph system. Reconstruct shared halo using original distance profile; original English faces, AA and near halo copied byte-exact, not retypeset.',target_slot=[0,0,source.shape[1],source.shape[0]])

def wall(n):
    source=np.array(Image.open(S/('CG1541.qnt.png' if n==1318 else 'CG1542.qnt.png')).convert('RGBA'))
    rgb=source[:,:,:3].astype(float); yy,xx=np.indices(source.shape[:2])
    area=(xx>=14)&(xx<=53)&(yy>=141)&(yy<=298)
    # All brush ink is darker and less blue than the smooth blue paper.
    # Day/night share the exact sign/glyph geometry, but the night colour grade
    # changes the ink hue. Derive both masks from the day original, never from target ink.
    mask_rgb=np.array(Image.open(S/'CG1541.qnt.png').convert('RGBA'))[:,:,:3].astype(float)
    core=area&((mask_rgb[:,:,2]-mask_rgb[:,:,1])<8)&(mask_rgb[:,:,2]<145)
    erase=binary_dilation(core,iterations=2)&area
    # Harmonic restoration uses only adjacent original paper boundary samples.
    # No rectangle replacement and no changes to the paper edge/stars/wall.
    ys,xs=np.where(erase);index=np.full(erase.shape,-1);index[erase]=np.arange(len(ys))
    mat=lil_matrix((len(ys),len(ys)));rhs=np.zeros((len(ys),3))
    for i,(y,x) in enumerate(zip(ys,xs)):
        mat[i,i]=4
        for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
            y1,x1=y+dy,x+dx;j=index[y1,x1]
            if j>=0:mat[i,j]=-1
            else:rhs[i]+=rgb[y1,x1]
    clean=source.copy();clean[erase,:3]=np.uint8(np.clip(spsolve(mat.tocsr(),rhs),0,255).round())
    ink=Image.open(O/'korean_brush_generated.png').convert('RGBA')
    # Alpha<=8 outside this evidenced ink column consists of generator background noise.
    ink=ink.crop((427,60,736,1378)).resize((34,149),Image.Resampling.LANCZOS)
    layer=Image.new('RGBA',Image.fromarray(source).size);layer.paste(ink,(18,145))
    final=np.array(Image.alpha_composite(Image.fromarray(clean),layer));target=np.array(layer)[:,:,3]>0
    assert np.array_equal(source[~(erase|target)],final[~(erase|target)])
    return source,clean,final,erase,target,dict(source='我は王なり',target='나는 왕이다',source_slot=[14,141,54,299],target_slot=[18,145,52,294],
        mask_method='Source charcoal blue-green<8 and blue<145 inside source ink slot, expanded 2px for original antialias; original paper boundary-driven harmonic fill restricted to glyph mask.',
        generated_source=str(O/'korean_brush_generated.png'),generated_sha256=h(O/'korean_brush_generated.png'),tool='built-in image_gen',generated_crop=[427,60,736,1378])

def qnt_header(source,new):
    if source[:4]!=b'QNT\0':return new
    v,z=struct.unpack_from('<II',source,4);nv,nz=struct.unpack_from('<II',new,4)
    assert source[12:36]==new[12:36]
    head=bytearray(source[:z]);head[36:44]=new[36:44]
    return bytes(head)+new[nz:]

def main():
    O.mkdir(exist_ok=True);ptr=json.loads((R/'ui_cumulative/current.json').read_text('utf8'));rt=Path(ptr['runtime'])
    assert h(ptr['manifest'])==ptr['manifest_sha256'];js(O/'source_pointer.json',ptr)
    source_files={n:h(rt/n) for n in ['NightRemaster.ain','NightRemasterPact.afa','NightRemasterCG.afa']}
    _,raw=source_archive();arc=read_afa3(rt/'NightRemasterCG.afa');data=(rt/'NightRemasterCG.afa').read_bytes()
    replacements={};records=[]
    for n in IDS:
        source,clean,final,erase,target,meta=banner(n) if n in [485,981,1004] else wall(n)
        paths={k:O/f'{n}_{k}.png' for k in ['source','clean','final','erase','target','protected']}
        for k,a in [('source',source),('clean',clean),('final',final),('erase',erase),('target',target),('protected',~(erase|target))]:png(paths[k],a)
        assert np.array_equal(source[~(erase|target)],final[~(erase|target)])
        payload=O/f'{n}.payload';encode(raw[n],paths['final'],payload);payload.write_bytes(qnt_header(raw[n],payload.read_bytes()))
        reopen=O/f'{n}_reopened.png';run(['cg','convert',payload,reopen]);assert np.array_equal(np.array(Image.open(reopen).convert('RGBA')),final)
        old=arc.entries[n];old_bytes=data[old.absolute_offset:old.absolute_offset+old.size];(O/f'{n}_installed_before.payload').write_bytes(old_bytes)
        rec=dict(id=n,archive_name=old.name,canvas=[source.shape[1],source.shape[0]],original_sha256=hashlib.sha256(raw[n]).hexdigest(),
            installed_before_sha256=hashlib.sha256(old_bytes).hexdigest(),payload=str(payload),payload_sha256=h(payload),source_png_sha256=h(paths['source']),
            final_png_sha256=h(paths['final']),roundtrip='PASS',protected_pixel_changes=0,erase_bounds=bounds(erase),target_ink_bounds=bounds(target),
            translator_model='Codex internal',task='/root',**meta,artifacts={k:str(v) for k,v in paths.items()})
        records.append(rec);replacements[n]=payload
    audit=rebuild(rt/'NightRemasterCG.afa',O/'NightRemasterCG.afa',replacements)
    # Re-read candidate archive independently, checking exact logical membership/payloads.
    out=read_afa3(O/'NightRemasterCG.afa');candidate=(O/'NightRemasterCG.afa').read_bytes();changed=[]
    assert len(arc.entries)==len(out.entries)
    for a,b in zip(arc.entries,out.entries):
        assert a.no==b.no and a.name==b.name
        aa=data[a.absolute_offset:a.absolute_offset+a.size];bb=candidate[b.absolute_offset:b.absolute_offset+b.size]
        if aa!=bb:changed.append(a.no)
    assert changed==IDS
    js(O/'build_evidence.json',dict(status='BUILT_VISUAL_NATIVE_PENDING',source_pointer=ptr,source_files=source_files,
        files={'NightRemasterCG.afa':h(O/'NightRemasterCG.afa')},unchanged_code={k:v for k,v in source_files.items() if k!='NightRemasterCG.afa'},records=records,
        changed_entries=changed,entry_count=len(out.entries),archive_audit=audit,translator_model='Codex internal',builder_sha256=h(__file__)))
    # Persisted native-size previews, padding belongs to the evidence only.
    sheet=Image.new('RGB',(1520,975),(13,20,32));d=ImageDraw.Draw(sheet)
    y=0
    for n in [485,981,1004]:
        for c,k in enumerate(['source','reopened']):
            im=Image.open(O/f'{n}_{k}.png').convert('RGBA');d.text((c*760+6,y+4),f'{n} / {k.upper()}',fill='white');sheet.paste(im,(c*760,y+24),im)
        y+={485:287,981:287,1004:401}[n]
    sheet.save(O/'bilingual_comparison.png')
    sheet=Image.new('RGB',(576,1032),(20,25,34));d=ImageDraw.Draw(sheet)
    for c,k in enumerate(['source','clean','reopened']):
        im=Image.open(O/f'1318_{k}.png').crop((0,133,64,302)).resize((192,507),Image.Resampling.NEAREST)
        sheet.paste(im,(c*192,24));d.text((c*192+4,4),k,fill='white')
    whole=Image.open(O/'1318_reopened.png').convert('RGB');whole.thumbnail((576,480));sheet.paste(whole,(0,540));sheet.save(O/'wall_comparison.png')
    print(json.dumps(dict(changed=changed,files={'NightRemasterCG.afa':h(O/'NightRemasterCG.afa')})))

if __name__=='__main__':main()
