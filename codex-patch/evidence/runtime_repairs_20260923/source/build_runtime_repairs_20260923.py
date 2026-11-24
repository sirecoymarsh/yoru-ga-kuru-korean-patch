from pathlib import Path
import json,struct,re,copy,shutil,collections
import build_mod_native_style_20260923 as previous
from build_dungeon_sweep_20260916 import lr,cf,push
from audit_dynamic_ui_20260915 import ENC
R=previous.R;HERE=previous.HERE;b=previous.b;p=previous.p;q=previous.q
BASE=previous.O;O=R/'staging/runtime_repairs_20260923'
EXPECTED='bdcd8c8c8d1c2f606ee39f4180a3f377ea1db82818ba6a99f420bf518cdd6758'
FILES=['NightRemaster.ain','NightRemasterPact.afa']
def h(path):return b.a.sha(path)
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
    O.mkdir(exist_ok=True);ptr=b.a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
    assert h(src)==EXPECTED and h(Path(ptr['manifest']))==ptr['manifest_sha256'];p.exact_tree(rt,b.a.readj(Path(ptr['manifest']))['files'])
    save('source_pointer.json',ptr);save('save_hashes_before_build.json',p.snapshot_saves());shutil.copy2(src,O/'baseline_NightRemaster.ain')
    m=b.read_meta(BASE/'candidate_meta.json');jaf=(HERE/'runtime_repairs_20260923.jaf').read_text('utf8')
    groups=collections.defaultdict(list)
    for c,v in ENC.items():
        if len(c)==1 and '\uac00'<=c<='\ud7a3':
            code=c.encode('cp949');groups[code[0]].append((int.from_bytes(code,'big'),c))
    table=''
    for high,rows in sorted(groups.items()):
        table+=f'if(code/256=={high}) {{\n'+''.join(f'if(code=={v}) return {json.dumps(c,ensure_ascii=False)};\n' for v,c in sorted(rows))+'return "";\n}\n'
    jaf=jaf.replace('/*INPUT_TABLE*/',table)
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(previous.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('\uac00'<=c<='\ud7a3' for c in z[0]) else z[0],jaf)
    (O/'helpers.jaf').write_text(jaf,'utf8');decl=O/'declared.ain';b.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[]
    for f in added:
        path=O/f"jaf_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl);body=b.clean(b.native_lower(path.read_text('utf8')),f['name'])
        if f['name']=='KR_KoreanInputChar':body=f"FUNC {f['index']}\n"+lr('text')+lr('index')+'\tC_REF\n\tRETURN\nENDFUNC KR_KoreanInputChar\n'
        patch.append(body)
    relocated=[32062,32064,32195,32205]
    patch.append('FUNC 32062\n'+lr('path')+'\tA_REF\n'+push(1)+cf('KR_TermReadSafe')+'\tRETURN\nENDFUNC KR_TermLoadFile\n')
    patch.append('FUNC 32064\n'+cf('KR_TermSaveSafe')+'\tRETURN\nENDFUNC KR_TermSave\n')
    for fid in [32195,32205]:
        name=b.symbol(m,fid);path=O/f'original_{fid}.jam';b.cmd('ain','dump','--function',name,'-o',path,src);body=b.clean(path.read_text('utf8'),name)
        needle=lr('key')+'\tCALLMETHOD 1\n';assert body.count(needle)==1
        patch.append(body.replace(needle,lr('key')+'\tA_REF\n\tCALLMETHOD 1\n'))
    # Only the short mod helper changes; persistent dungeon frames are untouched.
    fid=next(f['index'] for f in m['functions'] if f['name']=='KR_ExploreBattleEnter');name=b.symbol(m,fid);path=O/f'original_{fid}.jam';b.cmd('ain','dump','--function',name,'-o',path,src)
    body=b.clean(path.read_text('utf8'),name);head=f'FUNC {fid}\n';body=body.replace(head,head+'\tS_PUSH "YoruKR.Explore.ResultStarted"\n\tS_PUSH ""\n\tCALLHLL SystemService SystemVariable_Set 0\n');patch.append(body);relocated.append(fid)
    (O/'patch.jam').write_text('\n'.join(patch),'utf8');out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    old=b.unpack(src.read_bytes());raw=bytearray(b.unpack(out.read_bytes()));oldn=struct.unpack_from('<I',old,12)[0];newn=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+newn,m['functions'][0]['address']);assert raw[16:16+oldn]==old[16:16+oldn]
    sites=[]
    versions=q.versions(BASE/'native_raw_code.jam')
    enter=next(f['index'] for f in m['functions'] if f['name']=='C_UserInputManager::IsClickEnter')
    for fid,oldfid,helper in [(32168,27756,'KR_KoreanInputDialog'),(32160,27756,'KR_KoreanInputDialog'),(29271,enter,'KR_ExploreResultEnter'),(27302,27750,'KR_ExploreLevelDialog'),(27776,enter,'KR_ExploreLevelEnter')]:
        start=m['functions'][fid]['address'];version=next(v for v in versions[fid] if v['start']==start);end=version['ops'][-1][0]+6
        pattern=struct.pack('<Hi',0x30,oldfid);body=old[16+start:16+end];assert body.count(pattern)==1,(fid,body.count(pattern))
        addr=start+body.index(pattern);change=struct.pack('<Hi',0x30,ids[helper]);raw[16+addr:16+addr+6]=change;sites.append(dict(fid=fid,address=addr,before=pattern.hex(),after=change.hex(),helper=helper))
    out.write_bytes(b.pack(raw,src.read_bytes()[:8]));b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    for f,g in zip(m['functions'],nm['functions']):
        test=dict(f)
        if f['index'] in relocated:test['address']=g['address']
        assert test==g,f['index']
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(raw)[2][:len(b.strings(old)[2])]==b.strings(old)[2]
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',audit);assert audit['all_active_opcodes_supported']
    # Korean two-syllable values fit between unchanged native baked labels.
    doc=previous.ex.decode_ex(BASE/'pact_154.pactex');frozen=copy.deepcopy(doc);records=[]
    for prefix in ['テキスト_武器_','テキスト_新武器_']:
        for field,x in [('属性',64),('範囲',156),('射程',269)]:
            node=previous.part(doc,prefix+field);xyz=previous.coords(node);new=[x,xyz[1],xyz[2]];previous.setlist(node,'座標',new);previous.si(previous.child(previous.txt_info(node),'テキスト装飾'),'フォントサイズ',20)
            records.append(dict(name=prefix+field,before=list(xyz),after=new,font_size=20))
    pact=O/'pact_154.pactex';pact.write_bytes(previous.ex.encode_ex(doc.header,doc.serialize_payload()));assert previous.ex.decode_ex(pact).serialize_payload()==doc.serialize_payload()
    for r in records:previous.part(doc,r['name']).__dict__.update(copy.deepcopy(previous.part(frozen,r['name']).__dict__))
    assert doc.serialize_payload()==frozen.raw_payload
    archive=previous.rebuild(rt/'NightRemasterPact.afa',O/'NightRemasterPact.afa',{154:pact})
    save('build_evidence.json',dict(status='RUNTIME_REPAIRS_STAGED',source_pointer=ptr,source_files={n:h(rt/n) for n in FILES},files={n:h(O/n) for n in FILES},added_functions=ids,relocated=sorted(relocated),same_length_sites=sites,input_syllables=sum(map(len,groups.values())),PACT=archive,layout=records,MSG1_exact=True,STR0_prefix_exact=True,serialized_schema_changes=0,translator_model='Codex internal'))
    print('STAGED',O)
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print(str(ex)[-3000:]);raise SystemExit(1)
