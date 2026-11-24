"""Append-only display getter overrides; scenario and save bytes are preserved."""
from pathlib import Path
import sys,json,struct,re,shutil
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
O=L.CODEX/'staging/calendar_choice_context_20260929';W=O/'work/build';L.TMP=O/'work/tmp'
src=O/'source/NightRemaster.ain';out=O/'candidate/NightRemaster.ain'
assert L.sha(src)=='6681bc33dc97a99eb59a3280a3b53e505f09fb8aac7e8a1d84c0b64e0c9b08ac'
m=L.read_meta(O/'source/candidate_meta.json');fid=lambda n:L.fid_of(m,n)
spec=[('ev_head','KR_T19EvHead','KR_S29Head','no','string'),('ev_short','KR_T19EvShort','KR_S29Short','no','string'),
      ('when_fix','KR_T19WhenFix','KR_S29When','no','string')]
labels=L.readj(O/'design/label_patch.json');jaf=[]
for key,old,new,arg,ret in spec:
    fallback=new+'Base';default='""' if ret=='string' else '0'
    jaf.append(f'{ret} {fallback}(int {arg}) {{ return {default}; }}')
    body=[]
    for no,value in sorted(labels['patch'][key].items(),key=lambda x:int(x[0])):
        val=json.dumps(value,ensure_ascii=False) if ret=='string' else str(value)
        if key in labels['unread']:
            hidden=json.dumps(labels['unread'][key][no],ensure_ascii=False)
            seen=f'KR_P29Read({arg})' if arg=='no' else f'KR_P29Read(KR_T9CardEntry({arg}))'
            body.append(f'    if ({arg}=={no}) {{ if (!{seen}) return {hidden}; return {val}; }}')
        else:body.append(f'    if ({arg}=={no}) return {val};')
    jaf.append(f'{ret} {new}(int {arg}) {{\n'+ '\n'.join(body)+f'\n    return {fallback}({arg});\n}}')

# Only the 20 context-rich details gain an explicit choice field; other boards use an exact fallback.
info=(HERE/'calendar_detail_layout_20260929.jaf').read_text('utf8').split('string KR_B29Info(',1)[1].split('void KR_B29Buttons()',1)[0]
baseinfo='string KR_S29InfoBase('+info
info='string KR_S29Info('+info
info=info.replace('    bool read = KR_P29Read(no);','    string date="";\n'+''.join('    if(no==%s) date=%s;\n'%(n,json.dumps(v,ensure_ascii=False)) for n,v in labels['dates'].items())+'    if(date=="") return KR_S29InfoBase(no,stages,width);\n    bool read = KR_P29Read(no);\n    if(!read) date=KR_T19EvWhen(no);')
info=info.replace('string t = KR_B29Field("언제",KR_T19EvWhen(no),width);','string t = KR_B29Field("언제",date,width);\n    if(read) t=t+KR_B29Field("선택",KR_T19WhenFix(no),width);\n    else t=t+KR_B29Field("선택","열람 후 표시됩니다",width);')
jaf.append(baseinfo)
jaf.append(info)

jaf='\n\n'.join(jaf)+'\n';(W/'helpers_readable.jaf').write_text(jaf,'utf8');(W/'helpers.jaf').write_text(L.jaf_literal_encode(jaf),'utf8')
decl=W/'declared.ain';L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl);dm=L.read_meta(W/'declared_meta.json')
added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[];clones={}
for key,old,new,arg,ret in spec:
    p=W/(old+'_original.jam');L.cmd('ain','dump','--function',old,'-o',p,src)
    jam=L.clean(p.read_text('utf8'),old);clone=new+'Base'
    jam=re.sub(r'(?m)^FUNC .*$',f'FUNC {ids[clone]}',jam);jam=re.sub(r'(?m)^ENDFUNC .*$',f'ENDFUNC {clone}',jam)
    patch.append(jam);clones[clone]=old
    p=W/(new+'.jam');L.cmd('ain','dump','--function',new,'-o',p,decl)
    patch.append(L.clean(L.native_lower(p.read_text('utf8')),new))
    f=m['functions'][fid(old)];g=dm['functions'][ids[new]]
    assert f['return-type']==g['return-type'] and [a['type'] for a in f['arguments']]==[a['type'] for a in g['arguments']]
    oldarg=f['arguments'][0]['name']
    patch.append(f'FUNC {fid(old)}\n\t.LOCALREF {oldarg}\n\tCALLFUNC {new}\n\tRETURN\nENDFUNC {old}\n')

old='KR_B29Info';new='KR_S29Info';clone=new+'Base'
assert all(m['functions'][fid(old)][k]==dm['functions'][ids[clone]][k] for k in ['arguments','variables','return-type'])
p=W/(old+'_original.jam');L.cmd('ain','dump','--function',old,'-o',p,src)
jam=L.clean(p.read_text('utf8'),old)
jam=re.sub(r'(?m)^FUNC .*$',f'FUNC {ids[clone]}',jam);jam=re.sub(r'(?m)^ENDFUNC .*$',f'ENDFUNC {clone}',jam)
patch.append(jam);clones[clone]=old
p=W/(new+'.jam');L.cmd('ain','dump','--function',new,'-o',p,decl)
patch.append(L.clean(L.native_lower(p.read_text('utf8')),new))
patch.append(f'FUNC {fid(old)}\n\t.LOCALREF no\n\t.LOCALREF stages\n\t.LOCALREF width\n\t.CALLFUNC {new}\n\tRETURN\nENDFUNC {old}\n'.replace('.CALLFUNC','CALLFUNC'))

(W/'patch.jam').write_text('\n'.join(patch),'utf8');L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
base=L.unpack(src.read_bytes());raw=bytearray(L.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out);nm=L.read_meta(W/'candidate_meta.json')
forward={old:new for _,old,new,_,_ in spec};forward['KR_B29Info']='KR_S29Info'
assert [i for i,(a,b) in enumerate(zip(m['functions'],nm['functions'])) if a!=b]==sorted(fid(n) for n in forward)
for k in m:
    if k!='functions':assert m[k]==nm[k],k
oldn=struct.unpack_from('<I',base,12)[0];assert raw[16:16+oldn]==base[16:16+oldn]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert L.raw_messages(out.read_bytes())[3]==L.raw_messages(src.read_bytes())[3]
L.cmd('ain','dump','--raw-code','--no-macros','-o',W/'candidate_raw_code.jam',out)
rt=Path(L.readj(O/'source_pointer.json')['runtime']);audit=L.audit(out,W/'candidate_meta.json',W/'candidate_raw_code.jam',rt/'NightRemaster.exe')
L.writej(W/'native_opcode_audit.json',audit);assert audit['all_active_opcodes_supported']
shutil.copy2(O/'source/winmm.dll',O/'candidate/winmm.dll')
L.writej(O/'candidate/manifest.json',dict(status='STAGED_NATIVE_PENDING',files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ['NightRemaster.ain','winmm.dll']},source_sha256=L.sha(src),forwarded=forward,added_functions=ids,cloned_getters=clones,
    new_globals=0,serialized_schema_changes=0,old_code_prefix_exact=True,messages_exact=True,dll_unchanged=True,choice_label_sha256=L.sha(O/'design/label_patch.json'),changed_counts={k:len(v) for k,v in labels['patch'].items()},translator_model='Codex internal'))
print('BUILT',L.sha(out),len(added),'helpers; unchanged DLL and original scenario code')
