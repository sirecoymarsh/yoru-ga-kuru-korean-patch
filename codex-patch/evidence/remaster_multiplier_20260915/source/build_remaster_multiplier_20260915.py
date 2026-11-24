"""Stage four independent native sliders without changing serialized globals."""
from pathlib import Path
import copy, datetime, hashlib, json, re, struct, subprocess
from audit_dynamic_ui_20260915 import R, ex, encode, decode
from integrate_ui_opening_20260913 import read_meta
from repair_ui_runtime_weapon_text_20260913 import unpack, pack, strings
from build_afa3_cumulative_20260912 import read_afa3, rebuild
from publish_training_fix_20260915 import read, write, sha

O=Path('remaster_multiplier_20260915')
A=Path('P:/AI/Codex/projects/YoruGaKuru_KR_rebuild_20260830_compat_v2/tools/alice-tools-0.13.0/alice.exe')
ROWS=[('EX','경험치',201,29860,26361,'EX'),('Training','훈련치',203,29863,26363,'Trainging'),
      ('Money','월편',202,29866,26362,'Money'),('PairTraining','동료 특훈치',204,29869,26364,'PairTraining')]
OLD_PARTS=['SYS_２倍／経験値','SYS_２倍／訓練値','SYS_２倍／月片','SYS_２倍／仲間特訓値']

def cmd(*args):
    q=subprocess.run([str(A),*map(str,args)],capture_output=True,timeout=45)
    assert q.returncode==0,(args,q.stdout.decode('utf8','replace'),q.stderr.decode('utf8','replace'))
    return q

def cp(s):return s.encode('cp932')
def f32(f):return struct.unpack('<I',struct.pack('<f',f))[0]
def child(t,k):return next(c for c in t.children if c.name.value.decode('cp932')==k)
def maybe(t,k):return next((c for c in t.children if c.name.value.decode('cp932')==k),None)
def val(t,k):return child(t,k).leaf_value.payload
def allparts(t):
    if maybe(t,'座標') is not None:yield t
    kids=maybe(t,'子パーツ')
    if kids:
        for c in kids.children:yield from allparts(c)
def part(doc,name):return next(t for t in allparts(doc.blocks[2].payload.children[0]) if t.name.value.decode('cp932')==name)
def si(t,k,x):n=val(t,k);assert isinstance(n,ex.ScalarNode);n.raw=struct.pack('<f' if n.type_id==2 else '<i',x)
def ss(t,k,s,korean=False):val(t,k).replacement=encode(s) if korean else cp(s)
def setlist(t,k,vs):
    n=val(t,k);assert len(n.items)==len(vs)
    for i,v in zip(n.items,vs):
        p=i.value.payload
        if isinstance(p,ex.ScalarNode):p.raw=struct.pack('<f' if p.type_id==2 else '<i',v)
        else:p.replacement=cp(v)
def rename(t,s):t.name.replacement=cp(s);ss(t,'コメント',s)
def txt_info(t):return child(child(t,'種類別情報'),'通常状態')

def build_pact(rt):
    src=rt/'NightRemasterPact.afa';arc=read_afa3(src)
    for i in [120,125]:
        e=arc.entries[i]
        with src.open('rb') as f:f.seek(e.absolute_offset);b=f.read(e.size)
        (O/f'pact_{i}.pactex').write_bytes(b)
    sound=ex.decode_ex(O/'pact_120.pactex');doc=ex.decode_ex(O/'pact_125.pactex')
    original=ex.decode_ex(O/'pact_125.pactex')
    group=part(doc,'レイアウト_カジュアル');og=part(original,'レイアウト_カジュアル')
    kids=child(group,'子パーツ');order=val(group,'子パーツリスト')
    slider_template=part(sound,'SYS_音声女性スライダ')
    label_template=copy.deepcopy(child(kids,'テキストパーツ_000:0'))
    template_order=copy.deepcopy(order.items[0])
    # Native bar/cursor assets are reused verbatim; no raster image is edited.
    for j,(key,label,gi,_,__,___) in enumerate(ROWS):
        old=child(kids,OLD_PARTS[j]);ix=kids.children.index(old)
        sl=copy.deepcopy(slider_template);name='KR_Multiplier_'+key;rename(sl,name)
        x=(j%2)*360; y=82+(j//2)*68
        setlist(sl,'座標',[x,y,3+j]);si(sl,'原点座標モード',1)
        info=child(sl,'種類別情報')
        si(info,'長さ',324);si(info,'幅',42);si(info,'全体スクロール量',20)
        si(info,'表示量',1);si(info,'スクロール位置',1);si(info,'スクロールレート',1/19)
        si(info,'ボタンクリック移動量',1)
        kids.children[ix]=sl
        next(i.value.payload for i in order.items if i.value.payload.value.decode('cp932')==OLD_PARTS[j]).replacement=cp(name)
        for suffix,text,dx in [('Label',label,0),('Value','2배',268)]:
            tx=copy.deepcopy(label_template);tn='KR_Multiplier_'+suffix+'_'+key;rename(tx,tn)
            setlist(tx,'座標',[x+dx,58+(j//2)*68,20+j*2+(suffix=='Value')])
            ti=txt_info(tx);ss(ti,'テキスト',text,True)
            decor=child(ti,'テキスト装飾');si(decor,'フォントサイズ',22);si(decor,'行間隔',0)
            kids.children.append(tx);oi=copy.deepcopy(template_order);oi.value.payload.replacement=cp(tn);order.items.append(oi)
    # Split the old multi-line text so control geometry does not depend on blank lines.
    heading=child(kids,'テキストパーツ_000:0')
    ss(txt_info(heading),'テキスト','항목별 보상 배율 (1~20배)',True)
    si(child(txt_info(heading),'テキスト装飾'),'フォントサイズ',20)
    hint=copy.deepcopy(label_template);rename(hint,'KR_Multiplier_VisibilityHeading')
    setlist(hint,'座標',[0,202,40]);ss(txt_info(hint),'テキスト','숨겨진 배치물 강제 표시(틈새 진입 시 처음부터 표시)',True)
    si(child(txt_info(hint),'テキスト装飾'),'フォントサイズ',20)
    kids.children.append(hint);oi=copy.deepcopy(template_order);oi.value.payload.replacement=cp('KR_Multiplier_VisibilityHeading');order.items.append(oi)
    for name,x in [('SYS_敵強制表示',51),('SYS_罠強制表示',239),('SYS_宝箱強制表示',427)]:
        t=child(kids,name);z=struct.unpack('<i',val(t,'座標').items[2].value.payload.raw)[0];setlist(t,'座標',[x,230,z])
    setlist(child(kids,'SYS_アイテム所持数増加'),'座標',[1,278,7])
    # Everything outside the precisely owned casual-settings subtree remains exact.
    changed=group.serialize();saved=copy.deepcopy(group)
    group.__dict__.update(copy.deepcopy(og.__dict__))
    assert doc.serialize_payload()==original.raw_payload
    group.__dict__.update(saved.__dict__)
    target=O/'pact_125_sliders.pactex';target.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()))
    reopened=ex.decode_ex(target);assert reopened.serialize_payload()==doc.serialize_payload()
    for key,*_ in ROWS:
        q=part(reopened,'KR_Multiplier_'+key);assert val(child(q,'種類別情報'),'パーツタイプ').value.decode('cp932')=='横スクロールバー'
        assert struct.unpack('<i',val(child(q,'種類別情報'),'全体スクロール量').raw)[0]==20
    # Other remaster options, wallpaper controls, CG/FNL, sound page, and tabs are unmodified.
    rebuild(src,O/'NightRemasterPact.afa',{125:target})
    result=read_afa3(O/'NightRemasterPact.afa');changed_entries=[]
    with src.open('rb') as a,(O/'NightRemasterPact.afa').open('rb') as b:
        for old,new in zip(arc.entries,result.entries):
            assert (old.no,old.name,old.unknown0,old.unknown1)==(new.no,new.name,new.unknown0,new.unknown1)
            a.seek(old.absolute_offset);b.seek(new.absolute_offset)
            if a.read(old.size)!=b.read(new.size):changed_entries.append(old.no)
    assert changed_entries==[125]
    cmd('ex','dump','-o',O/'pact_125_sliders.x',target)
    return dict(changed_entries=changed_entries,unmodified_entries=184,owned_subtree='レイアウト_リマスター/レイアウト_カジュアル',outside_owned_subtree_byte_exact=True,new_native_sliders=4,new_labels=9,source_bar_assets='Native sound-page bar/cursor, unchanged raster bytes',range=[1,20],integer_step=1)

def dumpfun(src,name,file):
    path=O/file;cmd('ain','dump','--function',name,'-o',path,src)
    s=path.read_text(encoding='utf8');assert s.strip(),name
    return s
def fn(fid,name,body):return f'FUNC {fid}\n'+body.rstrip()+f'\nENDFUNC {name}\n\n'

def build_ain(rt):
    src=rt/'NightRemaster.ain';old=unpack(src.read_bytes())
    cmd('ain','dump','-j','-o',O/'current_meta.json',src);meta=read_meta(O/'current_meta.json')
    stubs=''.join(f'float KR_MultiplierGet{k}() {{ return 0.0; }}\nvoid KR_MultiplierSet{k}(float rate) {{ return; }}\n' for k,*_ in ROWS)
    stubs+='int KR_MultiplierCalc(int src, int percent) { return 0; }\n'
    (O/'callback_stubs.jaf').write_text(stubs,encoding='utf8');stage=O/'callbacks_declared.ain'
    cmd('ain','edit','--jaf',O/'callback_stubs.jaf','-o',stage,src)
    cmd('ain','dump','-j','-o',O/'declared_meta.json',stage);decl=read_meta(O/'declared_meta.json')
    assert len(decl['functions'])==len(meta['functions'])+9
    assert [i for i,(a,b) in enumerate(zip(meta['functions'],decl['functions'])) if a!=b]==[0]
    for k in meta:
        if k!='functions':assert meta[k]==decl[k],k
    raw=bytearray(unpack(stage.read_bytes()));oldlen=struct.unpack_from('<I',old,12)[0];newlen=struct.unpack_from('<I',raw,12)[0]
    assert raw[16:16+oldlen]==old[16:16+oldlen]
    at=16+newlen;assert raw[at:at+4]==b'FUNC' and struct.unpack_from('<I',raw,at+4)[0]==len(decl['functions'])
    assert struct.unpack_from('<I',raw,at+8)[0]==decl['functions'][0]['address']
    # JAF emits an empty NULL stub. Keep the historical NULL entry/address exactly.
    struct.pack_into('<I',raw,at+8,meta['functions'][0]['address']);stage.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
    ids={f['name']:f['index'] for f in decl['functions'] if f['index']>=len(meta['functions'])}
    out=[]
    for ix,(key,label,gi,setold,calc,ratekey) in enumerate(ROWS):
        g='L_CasualMode::Rate'+ratekey;getname='KR_MultiplierGet'+key;setname='KR_MultiplierSet'+key
        lo=0x7fe00000+ix*0x100;hi=lo+1
        getter=f'''\t.GLOBALREF {g}
\tPUSH 100
\tLTE
\tIFNZ 0x{lo:x}
\t.GLOBALREF {g}
\tPUSH 2000
\tGTE
\tIFNZ 0x{hi:x}
\t.GLOBALREF {g}
\tPUSH 100
\tSUB
\tITOF
\tPUSH {f32(1900)}
\tF_DIV
\tRETURN
0x{lo:x}:
\tPUSH 0
\tRETURN
0x{hi:x}:
\tPUSH {f32(1)}
\tRETURN
'''
        def assign(v):return f'\tPUSHGLOBALPAGE\n\tPUSH {gi}\n\tPUSH {v}\n\tX_ASSIGN 1\n\tPOP\n\tRETURN\n'
        lo+=0x10;hi+=0x10
        setter=f'''\t.LOCALREF rate
\tPUSH 0
\tF_GTE
\tIFZ 0x{lo:x}
\t.LOCALREF rate
\tPUSH {f32(1)}
\tF_GTE
\tIFNZ 0x{hi:x}
\tPUSHGLOBALPAGE
\tPUSH {gi}
\t.LOCALREF rate
\tPUSH {f32(19)}
\tF_MUL
\tPUSH {f32(.5)}
\tF_ADD
\tFTOI
\tPUSH 1
\tADD
\tPUSH 100
\tMUL
\tX_ASSIGN 1
\tPOP
\tRETURN
0x{lo:x}:
'''+assign(100)+f'0x{hi:x}:\n'+assign(2000)
        out += [fn(ids[getname],getname,getter),fn(ids[setname],setname,setter)]
        name=meta['functions'][calc]['name']
        out.append(fn(calc,name,f'\t.LOCALREF src\n\t.GLOBALREF {g}\n\tCALLFUNC KR_MultiplierCalc\n\tRETURN\n'))
    # Preserve legacy non-integer debug percentages. Integer1..20 gains avoid
    # the unnecessary src*2000 intermediate overflow and saturate at int limits.
    calc='''\t.LOCALREF percent
\tPUSH 100
\tLT
\tIFNZ 0x7fe01000
\t.LOCALREF percent
\tPUSH 2000
\tGT
\tIFNZ 0x7fe01000
\t.LOCALREF percent
\tPUSH 100
\tMOD
\tIFNZ 0x7fe01000
\t.LOCALREF src
\tPUSH 2147483647
\t.LOCALREF percent
\tPUSH 100
\tDIV
\tDIV
\tGT
\tIFNZ 0x7fe01010
\t.LOCALREF src
\tPUSH -2147483648
\t.LOCALREF percent
\tPUSH 100
\tDIV
\tDIV
\tLT
\tIFNZ 0x7fe01020
\t.LOCALREF src
\t.LOCALREF percent
\tPUSH 100
\tDIV
\tMUL
\tRETURN
0x7fe01000:
\t.LOCALREF src
\t.LOCALREF percent
\tMUL
\tPUSH 100
\tDIV
\tRETURN
0x7fe01010:
\tPUSH 2147483647
\tRETURN
0x7fe01020:
\tPUSH -2147483648
\tRETURN
'''
    out.append(fn(ids['KR_MultiplierCalc'],'KR_MultiplierCalc',calc))
    for fid,oldmethod,newmethod,mode in [(29817,29827,29825,'Get'),(29818,29828,29826,'Set')]:
        name=meta['functions'][fid]['name'];s=dumpfun(src,name,f'original_{fid}.jam')
        for ix,(key,_,__,setold,___,ratekey) in enumerate(ROWS):
            oldcb=setold+1 if mode=='Get' else setold;newcb=ids['KR_Multiplier'+mode+key]
            needle=f'\tPUSH {oldmethod}\n\tS_PUSH "{OLD_PARTS[ix]}"\n\tPUSH -1\n\tPUSH {oldcb}\n'
            assert s.count(needle)==1
            s=s.replace(needle,f'\tPUSH {newmethod}\n\tS_PUSH "KR_Multiplier_{key}"\n\tPUSH -1\n\tPUSH {newcb}\n')
        values=''
        for ix,(key,_,__,___,____,ratekey) in enumerate(ROWS):
            done=0x7fe02000+(fid-29817)*0x100+ix
            values+=f'''\t.STRUCTREF C_ConfigView m_ActName
\tA_REF
\tS_PUSH "KR_Multiplier_Value_{key}"
\tCALLFUNC AFL_Activity_IsExistPartsByName
\tIFZ 0x{done:x}
\t.STRUCTREF C_ConfigView m_ActName
\tA_REF
\tS_PUSH "KR_Multiplier_Value_{key}"
\tCALLFUNC AFL_Activity_GetPartsNumber
\tS_PUSH "%d{encode('배').decode('cp932')}"
\t.GLOBALREF L_CasualMode::Rate{ratekey}
\tPUSH 100
\tDIV
\tS_MOD 2
\tPUSH 1
\tCALLFUNC Ｐ＿テキスト設定
0x{done:x}:
'''
        pos=s.rfind('\tRETURN');assert pos>=0
        s=s[:pos]+values+s[pos:];s=re.sub(r'^EOF .*\n?','',s,flags=re.M)
        if 'ENDFUNC ' not in s:s+=f'ENDFUNC {name}\n'
        out.append(s+'\n')
    patch=O/'multiplier_patch.jam';patch.write_text('\n'.join(out),encoding='utf8')
    dest=O/'NightRemaster.ain';cmd('ain','edit','--jam',patch,'-o',dest,stage)
    cmd('ain','dump','-j','-o',O/'candidate_meta.json',dest);nm=read_meta(O/'candidate_meta.json')
    patched=sorted([29817,29818,26361,26362,26363,26364])
    assert len(nm['functions'])==len(meta['functions'])+9
    changes=[]
    for i,(a,b) in enumerate(zip(meta['functions'],nm['functions'])):
        if a!=b:
            aa=dict(a);bb=dict(b);aa.pop('address');bb.pop('address');assert aa==bb,i;changes.append(i)
    assert changes==patched,changes
    for k in meta:
        if k not in ['functions','strings','code']:assert meta[k]==nm[k],k
    newer=unpack(dest.read_bytes());ns=strings(newer)[2];os_=strings(old)[2]
    assert ns[:len(os_)]==os_ and newer[16:16+oldlen]==old[16:16+oldlen]
    assert newer[newer.index(b'MSG1'):newer.index(b'STR0')]==old[old.index(b'MSG1'):old.index(b'STR0')]
    for f in nm['functions'][len(meta['functions']):]:dumpfun(dest,f['name'],f"built_{f['index']}.jam")
    for i in patched:dumpfun(dest,nm['functions'][i]['name'],f'built_{i}.jam')
    return dict(patched_existing_function_ids=patched,added_function_ids=ids,
        existing_function_signatures_exact=True,all331_globals_and804_structures_exact=True,
        original_CODE_prefix_exact=True,original_STR0_entries_exact=True,MSG1_all_100944_exact=True,
        unrelated_metadata_exact=True,added_STR0_entries=len(ns)-len(os_),
        range=[1,20],step=1,stored_percentages=[100,2000],save_structure_unchanged=True,
        legacy_bool_callbacks_unchanged_and_not_bound_to_new_sliders=True,
        scalar_math='Integer1..20 multiply directly with signed-int saturation; legacy noninteger/out-of-range percent math unchanged.')

def main():
    O.mkdir(exist_ok=True);p=read(R/'ui_cumulative/current.json');assert p==read(O/'source_pointer.json')
    rt=Path(p['runtime']);assert sha(Path(p['manifest']))==p['manifest_sha256']
    pact=build_pact(rt);ain=build_ain(rt)
    evidence=dict(status='STAGED_REVIEW_PENDING',time=datetime.datetime.now().astimezone().isoformat(),
        source_pointer=p,translator_model='Codex internal',request='Four independent integer1..20 reward sliders',
        PACT=pact,AIN=ain,files={n:sha(O/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},
        no_game_or_save_modified=True,native_verified=False)
    write(O/'build_evidence.json',evidence);print(json.dumps(evidence,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
