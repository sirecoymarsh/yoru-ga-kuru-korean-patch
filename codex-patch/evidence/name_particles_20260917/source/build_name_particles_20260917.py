"""Append display helpers and narrowly hook existing name/text writers."""
import copy,json,re,struct,shutil,sys
from pathlib import Path
from audit_name_particles_20260917 import O,cmd,read_meta,t,decode
from audit_dynamic_ui_20260915 import encode
from trace_name_particles_20260917 import symbol
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit
from build_instant_loot_20260915 import clean
sys.stdout.reconfigure(encoding='utf-8')
# Every placeholder below is a displayed actor/monster/weapon/item name.
FORMATS={
3404:'%s{KJ:n} 히카리의 기척을 감지했다',3405:'%s{KJ:n} 함정의 기척을 감지했다',3406:'%s{KJ:n} 보물의 기척을 감지했다',3407:'%s{KJ:g} 함정을 해제하는 중',3410:'%s{KJ:n} 독으로 쓰러졌다',
3440:'%s{KJ:n} 회피했다',3444:'%s{KJ:n} 독에 걸렸다',3445:'%s{KJ:n} 마비됐다',3446:'%s{KJ:n} 다운됐다',
3486:'회복 아이템「%s」{KJ:O} 손에 넣었다',3491:'장비 아이템「%s」{KJ:O} 손에 넣었다',
4144:'%s{KJ:w} 함께 싸울 멤버를',4268:'%s{KJ:n} 벽을 만져 보았다.',
4425:'%s{KJ:g} %s{KJ:r} %s{KJ:q} 공격',4426:'%s{KJ:g} %s{KJ:r} 공격',4429:'%s{KJ:n} 방어 중',
4446:'%s{KJ:n} %s',4449:'%s{KJ:g} %s%s',4450:'%s{KJ:g} %s',
}
FALLBACK=dict(n='는',N='은',g='가',G='이',o='를',O='을',q='을(를)',w='와',W='과',r='로',R='으로')
MARKER='{YORU_KR_JOSA:'
FORMATS={k:v.replace('{KJ:',MARKER) for k,v in FORMATS.items()}
HOOKS=[7184,27778,29214]
def main():
    src=O/'source.ain';m=read_meta(O/'source_meta.json');original=src.read_bytes()
    assert t.sha(original)=='e775f61d6caf2fdec00623d69cd3241f3034881488981bc07744253d108602ed'
    old=unpack(original);a,b,ss=strings(old);changed=list(ss);format_records=[]
    for sid,new in FORMATS.items():
        before=decode(ss[sid]);fallback=re.sub(re.escape(MARKER)+r'(.)\}',lambda z:FALLBACK[z[1]],new)
        assert before==fallback,(sid,before,fallback)
        assert re.findall(r'%[-+0-9.]*s',before)==re.findall(r'%[-+0-9.]*s',new)
        changed[sid]=encode(new);format_records.append(dict(id=sid,before=before,after=new))
    # strings() returns the tag start and end; preserve count, order and other sections.
    payload=old[:a+8]+b''.join(x+b'\0' for x in changed)+old[b:]
    seeded=O/'annotated.ain';seeded.write_bytes(pack(payload,original[:8]))
    proxy=t.readj(t.INPUT/'proxy.json')['mapping'];alphabet=''.join(x['unicode_character'] for x in proxy if '\uac00'<=x['unicode_character']<='\ud7a3')
    classes=''.join('0' if (ord(c)-0xac00)%28==0 else '2' if (ord(c)-0xac00)%28==8 else '1' for c in alphabet)
    assert len(alphabet)>=2350 and len(set(alphabet))==len(alphabet)
    limits=[r for r in t.readj(O/'name_entry_scalars.json') if r['path'].endswith('テキストボックス_名前/種類別情報/最大文字数')]
    assert len(limits)==1 and limits[0]['value']==5
    assert len(MARKER)>limits[0]['value']*2 and MARKER.encode() not in old
    jaf=(t.HERE/'name_particles_helpers_20260917.jaf').read_text(encoding='utf-8')
    for placeholder,cls in [('VOWELS','0'),('RIEULS','2'),('CODAS','1')]:jaf=jaf.replace('@@'+placeholder+'@@',''.join(c for c,k in zip(alphabet,classes) if k==cls))
    rules=[]
    # The only two live sentinel+야 sites (m2631, m2967) are self-introduction
    # copulas: JP ends だよ, not vocatives. Preserve that source distinction.
    jp=t.raw_messages((t.INPUT/'jp.ain').read_bytes())[3];kr=t.raw_messages(original)[3]
    ya_ids=[i for i,b in enumerate(kr) if '료　　　　야' in decode(b)]
    assert ya_ids==[2631,2967]
    assert all(jp[i].decode('cp932').rsplit('亮　　　　',1)[1].startswith('だよ') for i in ya_ids)
    for root in ['라고','잖아','다','냐','야']:
        for prefix in ['이','']:
            form=prefix+root
            # Predicate endings must occupy a whole following segment, not begin another word.
            rules.append('if (tail.StartsWith('+json.dumps(form,ensure_ascii=False)+') && KR_JosaBoundary(tail, '+str(len(form))+')) return KR_JosaSelect(name, "i", '+json.dumps(prefix)+') + tail.GetPart('+str(len(prefix))+');')
    for form,kind in [('으로','R'),('로','r'),('은','N'),('는','n'),('을','O'),('를','o'),('과','W'),('와','w'),('가','g'),('이','G')]:
        rules.append('if (tail.StartsWith('+json.dumps(form,ensure_ascii=False)+') && KR_JosaBoundary(tail, '+str(len(form))+')) return KR_JosaSelect(name, "'+kind+'", '+json.dumps(form,ensure_ascii=False)+') + tail.GetPart('+str(len(form))+');')
    jaf=jaf.replace('/*PLAYER_RULES*/','\n    '.join(rules));(O/'helpers_readable.jaf').write_text(jaf,encoding='utf-8')
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False),jaf)
    (O/'helpers_proxy.jaf').write_text(jaf,encoding='utf-8');decl=O/'declared.ain';cmd('ain','edit','--jaf',O/'helpers_proxy.jaf','-o',decl,seeded)
    # JAF repoints NULL: restore its exact old entry address, preserving save metadata.
    raw=bytearray(unpack(decl.read_bytes()));n=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+n,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),original[:8]))
    cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};patches={}
    for name,fid in ids.items():
        path=O/f'jaf_{fid}.jam';cmd('ain','dump','--function',name,'-o',path,decl);s=clean(native_lower(path.read_text(encoding='utf-8')),name)
        if name=='KR_JosaSlice':s=f'FUNC {fid}\n\t.LOCALREF text\n\t.LOCALREF index\n\t.LOCALREF count\n\tCALLHLL String GetPart#1 0\n\tRETURN\nENDFUNC {name}\n'
        patches[fid]=s
    edits=[]
    for fid in HOOKS:
        name=symbol(m,fid);s=clean((O/f'original_{fid}.jam').read_text(encoding='utf-8'),name);before=s
        if fid==7184:
            needle='\t.LOCALREF baseText\n\tPUSHLOCALPAGE\n';assert s.count(needle)==1;s=s.replace(needle,'\t.LOCALREF baseText\n\tA_REF\n\tPUSHLOCALPAGE\n')
            needle='\tCALLHLL String Replace 0\n';assert s.count(needle)==1;s=s.replace(needle,'\tCALLFUNC KR_ReplacePlayerJosa\n')
        else:
            prefix='\tPUSHLOCALPAGE\n\tPUSH 0\n\t.LOCALREF txt\n\tA_REF\n\tCALLFUNC KR_ResolveJosa\n\tS_ASSIGN\n\tDELETE\n'
            s=s.replace(f'FUNC {fid}\n',f'FUNC {fid}\n'+prefix,1)
        patches[fid]=s;edits.append(dict(fid=fid,before=before,after=s))
    jam=O/'patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf-8');out=O/'output';out.mkdir(exist_ok=True);candidate=out/'NightRemaster.ain'
    cmd('ain','edit','--jam',jam,'-o',candidate,decl);cmd('ain','dump','-j','-o',O/'candidate_meta.json',candidate);nm=read_meta(O/'candidate_meta.json')
    for key in m:
        if key!='functions':assert m[key]==nm[key],key
    for fid,fn in enumerate(m['functions']):
        expected=copy.deepcopy(fn)
        if fid in HOOKS:expected['address']=nm['functions'][fid]['address']
        assert expected==nm['functions'][fid],fid
    assert len(nm['functions'])==len(m['functions'])+len(ids)
    final=unpack(candidate.read_bytes());oldsize=struct.unpack_from('<I',old,12)[0];assert final[16:16+oldsize]==old[16:16+oldsize]
    ssnew=strings(final)[2];assert ssnew[:len(ss)]==changed
    assert t.raw_messages(original)[3]==t.raw_messages(candidate.read_bytes())[3]
    for fid in patches:cmd('ain','dump','--function',symbol(nm,fid),'-o',O/f'built_{fid}.jam',candidate)
    cmd('ain','dump','--raw-code','--no-macros','-o',O/'candidate_raw.jam',candidate)
    ptr=t.readj(O/'source_pointer.json');na=audit(candidate,O/'candidate_meta.json',O/'candidate_raw.jam',Path(ptr['runtime'])/'NightRemaster.exe',ids=list(patches));assert na['all_active_opcodes_supported'];t.writej(O/'native_opcode_audit.json',na)
    t.writej(O/'format_changes.json',format_records);t.writej(O/'reversible_hook_edits.json',edits)
    evidence={'status':'BUILT_STATIC_PASS_VERIFICATION_PENDING','translator_model':'Codex internal','source_pointer':ptr,'source_ain_sha256':t.sha(original),'ain_sha256':t.sha(candidate.read_bytes()),'patched_existing_function_ids':HOOKS,'helper_function_ids':ids,'format_string_count':len(FORMATS),'all_MSG1_100944_exact':True,'old_CODE_prefix_exact':True,'old_function_signatures_exact':True,'globals_and_structures_exact':True,'save_schema_changes':0,'native_verified':False,'supported_hangul_syllables':len(alphabet),'unknown_name_policy':'Keep the original particle for unsupported/ambiguous non-Hangul endings','player_ya_source_review':{'ids':ya_ids,'japanese_ending':'だよ','role':'self-introduction copula: 야/이야, not vocative 야/아'}}
    t.writej(O/'build_evidence.json',evidence);print(json.dumps(evidence,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
