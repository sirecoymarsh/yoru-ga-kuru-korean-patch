"""Native UI-family extension; immutable original chrome, appended assets and save-safe hooks."""
from pathlib import Path
import copy, json, struct, re, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import build_auto_explore_segment_fix_20260923 as previous
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,si,ss,setlist,txt_info
from build_mod_tab_20260915 import coords
from audit_dynamic_ui_20260915 import encode,decode
from repair_ui_chrome_preserving_20260912 import fixed_ink,interior40,target_layer
from repair_ui_adjacent_preserving_20260912 import translate,measured_face,source_reference_ink,bounds

R=previous.R; HERE=previous.HERE; b=previous.b; p=previous.p; q=previous.q
O=R/'staging/mod_native_style_20260923'; BASE=previous.O
FILES=['NightRemaster.ain','NightRemasterPact.afa','NightRemasterCG.afa']
EXPECTED='e6d47c4356d5d12118e8424b002ebe07dbc5cc38591a4bcb5907a544e5c21250'
def save(name,value): (O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
def h(path): return b.a.sha(path)

def graphics(rt):
    assets=[]; append=[]
    chrome={r['id']:r for r in b.a.readj(R/'ui_chrome_repair/manifest.json')['records']}
    weapon={r['id']:r for r in b.a.readj(R/'ui_weapon_style_repair/manifest.json')['records']}
    for key,text,base in [('sweep','자동 소탕',990000),('walk','자동 탐색',990010),('stop','탐색 중지',990020),('stone','요소석 추천',990030)]:
        if key=='stone':
            normal=weapon[1871]; oldink=np.array(Image.open(normal['canonical_ink']).convert('L'))
            ns=np.array(Image.open(normal['source_png']).convert('RGBA')); nc=np.array(Image.open(normal['clean_plate']).convert('RGBA'))
            sm=np.any(ns!=nc,axis=2); field,_,_=measured_face(ns,nc,sm,'x'); sourceink=source_reference_ink(ns,nc,sm,field)
            ys,xs=np.where(oldink>0); cy=(int(ys.min())+int(ys.max())+1)/2
            font=ImageFont.truetype(r'C:\Windows\Fonts\NotoSerifKR-VF.ttf',24);font.set_variation_by_axes([600])
            mask=Image.new('L',(172,70)); d=ImageDraw.Draw(mask); bb=d.textbbox((0,0),text,font=font)
            d.text((round(91-(bb[2]-bb[0])/2)-bb[0],round(cy-(bb[3]-bb[1])/2)-bb[1]),text,font=font,fill=255)
            assert mask.getbbox()[0]>=26 and mask.getbbox()[2]<=158,mask.getbbox()
            source_ids=[1871,1867,1868]
        else:
            mask=fixed_ink((120,40),text,22); assert mask.getbbox()[0]>=9 and mask.getbbox()[2]<=111
            source_ids=[1675,1672,1673]
        for state,idx in enumerate(source_ids):
            if key=='stone':
                r=weapon[idx]; plate=Image.open(r['clean_plate']).convert('RGBA'); a=np.array(plate)
                protected=(a[:,:,:3].min(2)==255)&(a[:,:,3]==255)
                ink=Image.fromarray(translate(np.array(mask),1 if state==2 else 0))
                layer=Image.new('RGBA',plate.size)
                # Reuse the native material's measured distance-dependent optical profile.
                if state:
                    import cv2
                    info=r['glow_profile']; distance=cv2.distanceTransform((np.array(ink)<77).astype('uint8'),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
                    bins=np.array(info['distance_bins']); colors=np.array(info['source_glow_colors'])
                    alpha=np.interp(distance,bins,info['source_opacity']);alpha[protected]=0
                    rgb=np.stack([np.interp(distance,bins,colors[:,c]) for c in range(3)],axis=2)
                    layer=Image.fromarray(np.dstack([rgb.round().astype('uint8'),(alpha*255).round().astype('uint8')]))
                sb=bounds(translate(sourceink,1 if state==2 else 0)>.1);tb=ink.getbbox();coef=np.array(r['face_ramp_coefficients'])
                pos=sb[0]+(np.arange(172)-tb[0])*(sb[2]-sb[0])/(tb[2]-tb[0])
                rgb=np.broadcast_to(np.clip(pos[:,None]*coef[0]+coef[1],0,255)[None,:,:],(70,172,3))
                face=Image.fromarray(np.dstack([rgb.round().astype('uint8'),np.array(ink)]));layer=Image.alpha_composite(layer,face)
                fontdesc='NotoSerifKR-VF weight600 size24'
            else:
                plate=Image.open(R/f'ui_chrome_repair/{idx}_clean.png').convert('RGBA');protected=~interior40(120)
                ink=mask;layer=target_layer(ink,chrome[idx]['face_color'],state!=0,~protected);fontdesc='NotoSerifKR-VF weight500 size22'
            assert not np.any((np.array(layer)[:,:,3]>0)&protected)
            final=Image.alpha_composite(plate,layer); assert np.array_equal(np.array(final)[protected],np.array(plate)[protected])
            name=f'CG{base+state}'; png=O/(name+'.png'); payload=O/(name+'.qnt');final.save(png)
            b.cmd('cg','convert',png,payload);opened=O/(name+'_reopened.png');b.cmd('cg','convert',payload,opened)
            assert np.array_equal(np.array(final),np.array(Image.open(opened).convert('RGBA')))
            append.append((name+'.qnt',payload));assets.append(dict(key=key,text=text,state=state,source_id=idx,name=name,font=fontdesc,canvas=list(final.size),ink_bounds=ink.getbbox(),protected_pixel_changes=0,roundtrip='PASS',png=str(png),payload_sha256=h(payload),translator_model='Codex internal'))
    cg=rebuild(rt/'NightRemasterCG.afa',O/'NightRemasterCG.afa',{},append)
    sheet=Image.new('RGBA',(660,340),(10,16,35,255)); d=ImageDraw.Draw(sheet)
    for j,(key,label) in enumerate([('sweep','RETURN FAMILY / SWEEP'),('walk','EXPLORE'),('stop','STOP'),('stone','SYNTHESIS FAMILY / RECOMMEND')]):
        y=j*80;d.text((5,y),label,fill='white')
        for r in [a for a in assets if a['key']==key]: sheet.alpha_composite(Image.open(r['png']).convert('RGBA'),(15+r['state']*205,y+15))
    sheet.save(O/'button_states.png')
    return cg,assets

def pact(rt):
    arc=read_afa3(rt/'NightRemasterPact.afa');repl={};records=[]
    for idx in [154,161]:
        entry=arc.entries[idx];src=O/f'original_{idx}.pactex'
        with (rt/'NightRemasterPact.afa').open('rb') as stream:stream.seek(entry.absolute_offset);src.write_bytes(stream.read(entry.size))
        doc=ex.decode_ex(src);frozen=copy.deepcopy(doc)
        rows=[('KR_AutoStoneRoot','KR_AutoStoneButton',990030,(948,435,40),(172,70),['KR_AutoStoneButtonLabel'])] if idx==154 else [
            ('KR_SweepRoot','KR_SweepButton',990000,(1145,388,40),(120,40),['KR_SweepButtonLabel']),
            ('KR_WalkRoot','KR_WalkButton',990010,(1145,443,41),(120,40),['KR_WalkStartLabel','KR_WalkStopLabel'])]
        owned=[]
        for rootname,buttonname,base,xyz,size,labels in rows:
            root=part(doc,rootname);button=part(doc,buttonname);setlist(root,'座標',xyz);info=txt_info(root);w,ht=size
            for name,xy in [('右上',[w,0]),('左下',[0,ht]),('右下',[w,ht])]:setlist(info,name,xy)
            setlist(button,'拡大縮小',[1,1]);setlist(button,'座標',[0,0,1]);bi=child(button,'種類別情報')
            for state,name in enumerate(['通常状態','オンカーソル状態','キーダウン状態']):ss(child(bi,name),'ＣＧ名',f'CG{base+state}')
            for name in labels:
                lab=part(doc,name);si(lab,'表示',0);ss(txt_info(lab),'テキスト','')
            # All input, callback, order and generic part identities are preserved.
            assert val(button,'クリック許可').raw==val(part(frozen,buttonname),'クリック許可').raw
            owned.append((rootname,copy.deepcopy(root)))
            records.append(dict(entry=idx,root=rootname,button=buttonname,xyz=list(xyz),size=list(size),scale=[1,1],hidden_legacy_labels=labels))
        for name,_ in owned:part(doc,name).__dict__.update(copy.deepcopy(part(frozen,name).__dict__))
        assert doc.serialize_payload()==frozen.raw_payload
        for name,new in owned:part(doc,name).__dict__.update(new.__dict__)
        out=O/f'pact_{idx}.pactex';out.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()));assert ex.decode_ex(out).serialize_payload()==doc.serialize_payload();repl[idx]=out
    result=rebuild(rt/'NightRemasterPact.afa',O/'NightRemasterPact.afa',repl)
    return dict(archive=result,buttons=records,outside_mod_roots_exact=True)

def ain(rt):
    src=rt/'NightRemaster.ain';m=b.read_meta(BASE/'candidate_meta.json');decl=O/'declared.ain'
    b.cmd('ain','edit','--jaf',HERE/'mod_native_style_20260923.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added}
    patch=[]
    for f in added:
        path=O/f"jaf_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl)
        body=b.clean(b.native_lower(path.read_text('utf8')),f['name'])
        if f['name']=='KR_ModStonePart':
            path=O/'stone_part_template.jam';b.cmd('ain','dump','--function','KR_AutoStoneVisible','-o',path,src)
            t=b.clean(path.read_text('utf8'),'KR_AutoStoneVisible').split('FUNC 31919\n',1)[1].split('ENDFUNC ',1)[0]
            t=t.replace('S_PUSH "KR_AutoStoneRoot"','.LOCALREF key').replace('\tPUSH 60\n','\tPUSH 31\n')
            t=t.replace('\t.LOCALREF show\n\tCALLMETHOD 1\n','\tCALLMETHOD 0\n\tPUSHLOCALPAGE\n\tPUSH 2\n\tX_MOV 3 2\n\tX_ASSIGN 1\n\tPOP\n').replace('\tRETURN\n','\t.LOCALREF number\n\tRETURN\n')
            t=re.sub(r'0x[0-9a-fA-F]+',lambda match:'mod_stone_part_'+match[0],t)
            body=f"FUNC {f['index']}\n"+t+'ENDFUNC KR_ModStonePart\n'
        patch.append(body)
    patch.append('FUNC 32033\n\t.LOCALREF scene\n\t.LOCALREF active\n\tCALLFUNC KR_ModWalkGraphics\n\tRETURN\nENDFUNC KR_WalkLabels\n')
    for fid,name,arg,hook in [(31890,'KR_SweepVisible','scene','KR_ModSweepGraphics'),(31919,'KR_AutoStoneVisible','view','KR_ModStoneGraphics')]:
        path=O/f'original_{fid}.jam';b.cmd('ain','dump','--function',name,'-o',path,src)
        body=b.clean(path.read_text('utf8'),name);head=f'FUNC {fid}\n';assert body.count(head)==1
        patch.append(body.replace(head,head+f'\t.LOCALREF {arg}\n\t.LOCALREF show\n\tCALLFUNC {hook}\n'))
    (O/'patch.jam').write_text('\n'.join(patch),'utf8');out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    old=b.unpack(src.read_bytes());raw=bytearray(b.unpack(out.read_bytes()));oldn=struct.unpack_from('<I',old,12)[0];newn=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+newn,m['functions'][0]['address'])
    assert raw[16:16+oldn]==old[16:16+oldn]
    # PUSH and CALLFUNC are both six bytes. No addresses, jumps, locals or saved return offsets move.
    def push(v):return struct.pack('<Hi',0,v)
    callop=0x30 # CALLFUNC, cross-checked against raw instruction stream below.
    changes=[]
    for fid,pattern,pos,helper in [
        (31922,push(2)+struct.pack('<Hi',callop,31920),0,'KR_ModConfirmColumns'),
        (31892,push(1)+push(0)+struct.pack('<Hi',callop,27873),0,'KR_ModConfirmCancelable'),
        (27928,push(27935)+push(0)+struct.pack('<Hi',0x5c,1),6,'KR_ModDefaultIndex')]:
        start=m['functions'][fid]['address'];end=min([f['address'] for f in m['functions'] if f['address']>start]+[oldn]);body=old[16+start:16+end]
        assert body.count(pattern)==1,(fid,pattern.hex(),body[:32].hex())
        addr=start+body.index(pattern)+pos;new=struct.pack('<Hi',callop,ids[helper]);raw[16+addr:16+addr+6]=new
        changes.append(dict(fid=fid,address=addr,before=old[16+addr:16+addr+6].hex(),after=new.hex(),helper=helper))
    start,end,strings=b.strings(raw);renamed=[]
    for i,s in enumerate(strings):
        if encode('자동 이동') in s:
            target=s.replace(encode('자동 이동'),encode('자동 탐색'));strings[i]=target;renamed.append(dict(index=i,before=decode(s),after=decode(target)))
    assert [r['index'] for r in renamed]==[11514,11515,11516,11517,15381]
    raw[start:end]=b'STR0'+struct.pack('<I',len(strings))+b''.join(s+b'\0' for s in strings)
    out.write_bytes(b.pack(raw,src.read_bytes()[:8]));assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    for f,g in zip(m['functions'],nm['functions']):
        z=dict(f)
        if f['index'] in [31890,31919,32033]:z['address']=g['address']
        assert z==g,f['index']
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    report=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',report);assert report['all_active_opcodes_supported']
    return dict(added_functions=ids,in_place_instructions=changes,relocated=[31890,31919,32033],renamed_strings=renamed,MSG1_exact=True,save_schema_changes=0,translator_model='Codex internal')

def main():
    O.mkdir(exist_ok=True);ptr=b.a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime'])
    assert h(rt/'NightRemaster.ain')==EXPECTED and h(Path(ptr['manifest']))==ptr['manifest_sha256']
    p.exact_tree(rt,b.a.readj(Path(ptr['manifest']))['files']);save('source_pointer.json',ptr);save('save_hashes_before_build.json',p.snapshot_saves())
    shutil.copy2(rt/'NightRemaster.ain',O/'baseline_NightRemaster.ain')
    code=ain(rt);cg,assets=graphics(rt);pa=pact(rt)
    save('build_evidence.json',dict(status='MOD_NATIVE_STYLE_STAGED',source_pointer=ptr,source_files={n:h(rt/n) for n in FILES},files={n:h(O/n) for n in FILES},AIN=code,CG=cg,assets=assets,PACT=pa,save_schema_changes=0,save_writes=0,translator_model='Codex internal'))
    print('STAGED',O)
if __name__=='__main__':main()
