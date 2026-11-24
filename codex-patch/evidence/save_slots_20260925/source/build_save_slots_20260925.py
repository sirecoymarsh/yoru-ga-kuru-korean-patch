"""Save-compatible independent autosaves and original-family native save cards."""
from pathlib import Path
import copy,json,re,shutil,struct
import inspect_save_slots_20260925 as source
import build_mod_native_style_20260923 as n
from build_remaster_multiplier_20260915 import allparts,rename,cp
from audit_dynamic_ui_20260915 import encode
e=source.e;b=e.b;p=e.p;q=e.q;a=e.a
R=e.R;O=source.O;S=source.S;HERE=Path(__file__).parent
AUTHOR='Codex internal'
def h(path):return e.h(path)
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
def korean(jaf):
    return re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False),jaf)
def textdump(m,fid,src):return b.cmd('ain','dump','--function',b.symbol(m,fid),src).stdout.decode('utf8')
def clean(m,fid,src):return b.clean(textdump(m,fid,src),b.symbol(m,fid))
def once(text,old,new):
    assert text.count(old)==1,(old,text.count(old))
    return text.replace(old,new)
def wrapper(m,fid,ops):return f'FUNC {fid}\n{ops}\tRETURN\nENDFUNC {b.raw_symbol(m,fid)}\n'
def pact():
    doc=n.ex.decode_ex(O/'pact_168.pactex');original=copy.deepcopy(doc)
    root=n.part(doc,'矩形_000');children=n.child(root,'子パーツ');order=n.val(root,'子パーツリスト');oi=copy.deepcopy(order.items[0])
    text=copy.deepcopy(n.part(doc,'テキスト_NODATA'))
    # Keep original input rectangle/callback identities. Hide only legacy drawing.
    for part in children.children:n.si(part,'表示',0)
    def add(part,name,xyz):
        rename(part,name);n.setlist(part,'座標',xyz);n.si(part,'表示',1);children.children.append(part)
        it=copy.deepcopy(oi);it.value.payload.replacement=cp(name);order.items.append(it)
    bg=copy.deepcopy(n.part(original,'ＣＧ_NODATA'))
    n.child(bg,'子パーツ').children=[];n.val(bg,'子パーツリスト').items=[]
    add(bg,'KR_SaveBackground',[0,0,80])
    layout=[('Label',20,16,28),('Kind',16,51,14),('Headline',118,6,20),('Party',118,32,17),
            ('Progress',584,32,16),('Stamp',118,58,14),('Detail',584,58,14)]
    for key,x,y,size in layout:
        part=copy.deepcopy(text);info=n.txt_info(part)
        n.ss(info,'テキスト','');n.si(info,'テキスト位置',0)
        decor=n.child(info,'テキスト装飾');n.si(decor,'フォントサイズ',size)
        n.setlist(decor,'フォント色',[245,239,255] if key not in ['Kind','Stamp','Detail'] else [196,195,233])
        add(part,'KR_Save'+key,[x,y,81])
    target=O/'new_pact_168.pactex';target.write_bytes(n.ex.encode_ex(doc.header,doc.serialize_payload()))
    assert n.ex.decode_ex(target).serialize_payload()==doc.serialize_payload()
    # The page count and native page buttons remain unchanged; two auto rows + 1..4 on page 1.
    result=n.rebuild(S/'NightRemasterPact.afa',O/'NightRemasterPact.afa',{168:target})
    return dict(archive=result,layout=layout,frame='Original empty-slot chrome; no CG archive change')
def main():
    ptr=a.readj(S/'current.json');rt=Path(ptr['runtime'])
    assert h(rt/'NightRemaster.ain')==source.EXPECTED,'Live build changed'
    p.exact_tree(rt,a.readj(Path(ptr['manifest']))['files'])
    save('source_pointer.json',ptr);save('save_hashes_before_build.json',p.snapshot_saves())
    src=S/'NightRemaster.ain';m=b.read_meta(S/'candidate_meta.json')
    jaf=(HERE/'save_slots_20260925.jaf').read_text('utf8')
    doc=n.ex.decode_ex(O/'pact_168.pactex')
    oldparts=[x.name.value.decode('cp932') for x in n.child(n.part(doc,'矩形_000'),'子パーツ').children]
    jaf=jaf.replace('/*HIDE_LEGACY_PARTS*/','\n'.join('PartsEngine.SetComponentShow(KR_SaveCellPart(view,'+json.dumps(key,ensure_ascii=False)+'),false);' for key in oldparts))
    jaf=korean(jaf)
    (O/'helpers.jaf').write_text(jaf,'utf8');decl=O/'declared.ain'
    b.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[];relocated=[]
    for f in added:
        body=b.clean(b.native_lower(textdump(dm,f['index'],decl)),f['name'])
        if f['name']=='KR_SaveMap':body=wrapper(dm,f['index'],'\t.GLOBALREF Flags\n\tPUSH 26556\n\tCALLMETHOD 0\n')
        if f['name']=='KR_SaveCellSlot':body=wrapper(dm,f['index'],'\t.LOCALREF view\n\tPUSH 29588\n\tCALLMETHOD 0\n')
        if f['name']=='KR_SaveLegacy':body=wrapper(dm,f['index'],'\t.LOCALCREATE info S_SaveCellInfo\n\t.LOCALREF info\n\tPUSH 29657\n\tCALLMETHOD 0\n\tA_REF\n')
        if f['name']=='KR_SaveScene':
            ops='''\t.GLOBALREF GetGameView
\tDG_CALLBEGIN "DG_Func<ref C_SceneGameView>"
saveview_loop:
\tDG_CALL "DG_Func<ref C_SceneGameView>" saveview_end
\tJUMP saveview_loop
saveview_end:
\t.LOCALREF view
\tDELETE
\tPUSHLOCALPAGE
\tPUSH 0
\tX_MOV 3 2
\tX_ASSIGN 1
\tPOP
\t.LOCALREF view
\tPUSH -1
\tEQUALE
\tIFNZ svk_none
'''
            for field,kind in [(8,13),(6,11),(5,10),(4,9)]:
                ops+=f'\t.LOCALREF view\n\tPUSH {field}\n\tX_REF 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ svk_next{field}\n\tPUSH {kind}\n\tRETURN\nsvk_next{field}:\n'
            body=wrapper(dm,f['index'],ops+'svk_none:\n\tPUSH 0\n')
        if f['name']=='KR_SaveGameView':
            body=f'''FUNC {f['index']}
\t.GLOBALREF GetGameView
\tDG_CALLBEGIN "DG_Func<ref C_SceneGameView>"
saveview_loop:
\tDG_CALL "DG_Func<ref C_SceneGameView>" saveview_end
\tJUMP saveview_loop
saveview_end:
\tRETURN
ENDFUNC KR_SaveGameView
'''
        if f['name']=='KR_SaveCellPart':
            body=clean(m,32205,src).replace('FUNC 32205\n',f"FUNC {f['index']}\n").replace('ENDFUNC KR_ModStonePart','ENDFUNC KR_SaveCellPart')
            body=re.sub(r'0x[0-9a-fA-F]+',lambda z:'savepart_'+z[0],body)
        patch.append(body)
    def replacefn(fid,body):patch.append(body);relocated.append(fid)
    names={f['name']:f['index'] for f in m['functions']}
    for name,helper in [('KR_T8WeeklySlot','KR_SaveWeekly'),('KR_T8AutoSaveSlot','KR_SaveMorningSlot')]:
        fid=names[name];replacefn(fid,wrapper(m,fid,f'\tCALLFUNC {helper}\n'))
    replacefn(29574,wrapper(m,29574,'\t.LOCALREF saveNo\n\tCALLFUNC KR_SaveSnapshot\n'))
    replacefn(29648,wrapper(m,29648,'\tPUSHLOCALPAGE\n\tPUSH 0\n\tX_REF 2\n\tPUSHLOCALPAGE\n\tPUSH 2\n\tX_REF 2\n\t.LOCALREF bAuto\n\tCALLFUNC KR_SaveNewest\n'))
    body=clean(m,29582,src)
    body=once(body,'\t.LOCALREF dataNo\n\tPUSH 5\n\tMOD\n','\t.LOCALREF dataNo\n\tCALLFUNC KR_SaveRow\n')
    replacefn(29582,body)
    # Direct index conversion; caller already knows this is a visible cell.
    replacefn(29581,wrapper(m,29581,'\t.LOCALREF saveNo\n\tCALLFUNC KR_SaveRow\n'))
    body=clean(m,29577,src)
    page='\tPUSHSTRUCTPAGE\n\tPUSH 29562\n\tCALLMETHOD 0\n'
    body=once(body,'\t.LOCALREF i#1\n\tPUSH 5\n\tLT\n','\t.LOCALREF i#1\n'+page+'\tCALLFUNC KR_SaveRows\n\tLT\n')
    body=once(body,page+'\tPUSH 5\n\tMUL\n\t.LOCALREF i#1\n\tADD\n',page+'\t.LOCALREF i#1\n\tCALLFUNC KR_SaveSlot\n')
    # New badges depended on the original 5-row indexing; new cards intentionally omit them.
    body=body.split('\t.LOCALASSIGN newIdx 0\n',1)[0]+'\tRETURN\nENDFUNC C_SceneSaveLoadView@Update\n'
    body=once(body,'\tPUSH 101\n\t.LOCALREF i#1\n\tMUL\n',page+'\tCALLFUNC KR_SavePitch\n\t.LOCALREF i#1\n\tMUL\n')
    replacefn(29577,body)
    body=clean(m,29583,src);body=once(body,'\tPUSH 1\n\tPUSH 5\n\tPUSH 0\n', '\tPUSH 1\n'+page+'\tCALLFUNC KR_SaveRows\n\tPUSH 0\n')
    replacefn(29583,body)
    body=clean(m,29600,src).replace('S_PUSH "ＣＧ_データ土台"','S_PUSH "KR_SaveBackground"').replace('S_PUSH "ＣＧ_NODATA"','S_PUSH "KR_SaveBackground"')
    replacefn(29600,body)
    body=clean(m,29584,src)
    guard='\t.STRUCTREF C_SceneSaveLoadView m_Cells\n\t.LOCALREF idx\n\tX_REF 1\n\tPUSH 29595\n\tCALLMETHOD 0\n\tIFNZ save_idx_enabled\n\tPUSH -1\n\tRETURN\nsave_idx_enabled:\n'
    body=once(body,'\t.LOCALREF bNeedExist\n',guard+'\t.LOCALREF bNeedExist\n')
    replacefn(29584,body)
    body=clean(m,29571,src)
    body=once(body,'\tPUSH 29577\n\t.LOCALREF pageNo\n\tPUSH 0\n\tCALLMETHOD 2\n','\tPUSH 29577\n\tPUSH 0\n\tPUSH 0\n\tCALLMETHOD 2\n')
    replacefn(29571,body);relocated.extend(range(31683,31694))
    body=clean(m,29601,src)
    pos=body.rfind('\tRETURN\n');assert pos>0
    body=body[:pos]+'\tPUSHSTRUCTPAGE\n\t.LOCALREF type\n\tCALLFUNC KR_SavePaint\n'+body[pos:]
    replacefn(29601,body);relocated.extend([31695,31696,31697])
    (O/'patch.jam').write_text('\n'.join(patch),'utf8');out=O/'NightRemaster.ain'
    b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    old=b.unpack(src.read_bytes());raw=bytearray(b.unpack(out.read_bytes()));oldn=struct.unpack_from('<I',old,12)[0];newn=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+newn,m['functions'][0]['address'])
    assert raw[16:16+oldn]==old[16:16+oldn]
    # Exactly one same-length hook, after the existing native save has completed.
    version=next(v for v in q.versions(S/'native_raw_code.jam')[29555] if v['start']==m['functions'][29555]['address'])
    ad=version['ops'][-5][0] # selected by the exact suffix below, not assumed opcode index
    ops=version['ops'];tail=[(i,op) for i,op in ops if op=='PUSH 0x1']
    ad=tail[-1][0]
    assert old[16+ad:16+ad+8]==struct.pack('<HiH',0,1,0x2f),(hex(ad),old[16+ad:16+ad+8].hex())
    raw[16+ad:16+ad+6]=struct.pack('<Hi',0x30,ids['KR_SaveCommitted'])
    out.write_bytes(b.pack(raw,src.read_bytes()[:8]))
    b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    for f,g in zip(m['functions'],nm['functions']):
        test=dict(f)
        if f['index'] in relocated:test['address']=g['address']
        assert test==g,f['index']
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(raw)[2][:len(b.strings(old)[2])]==b.strings(old)[2]
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',audit);assert audit['all_active_opcodes_supported']
    pa=pact()
    shutil.copy2(rt/'NightRemasterEX.ex',O/'NightRemasterEX.ex')
    save('build_evidence.json',dict(status='STAGED_UNVERIFIED',files={x:h(O/x) for x in ['NightRemaster.ain','NightRemasterPact.afa']},source_pointer=ptr,added_functions=ids,relocated=relocated,same_length_sites=[dict(address=ad,before=old[16+ad:16+ad+6].hex(),after=raw[16+ad:16+ad+6].hex())],PACT=pa,serialized_schema_changes=0,MSG1_exact=True,STR0_prefix_exact=True,translator_model=AUTHOR))
    print('STAGED',O)
if __name__=='__main__':main()
