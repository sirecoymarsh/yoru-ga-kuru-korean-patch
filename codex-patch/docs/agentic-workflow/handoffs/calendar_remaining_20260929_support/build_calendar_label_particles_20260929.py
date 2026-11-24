"""Correct only audited, standalone person-name labels; retain every prior UI override."""
from pathlib import Path
import sys,json,re,struct,shutil
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
R=L.CODEX;PRE=R/'staging/calendar_april_adaptive_minis_20260929'
O=R/'staging/calendar_label_particles_20260929_r2';W=O/'work/build';L.TMP=O/'work/tmp'
BASE='7579a581f60e989d07f9abca13e4bc620aa6f65952974bbddbf0fa99e5f107d3'
SPEC=[('ev_short','KR_T19EvShort','KR_N29Short','no'),('ev_head','KR_T19EvHead','KR_N29Head','no'),
      ('heads','KR_T19CardHead','KR_N29CardHead','k'),('tails','KR_T19CardTail','KR_N29CardTail','k')]
cur=L.readj(L.CURRENT);rt=Path(cur['runtime'])
assert L.sha(rt/'NightRemaster.ain')==L.sha(PRE/'candidate/NightRemaster.ain')==BASE
if not O.exists():
    for d in ['source','design','work/build','work/tmp','candidate','evidence','probe']:(O/d).mkdir(parents=True)
    for n in ['NightRemaster.ain','winmm.dll']:shutil.copy2(rt/n,O/'source'/n)
    for n in ['candidate_meta.json','candidate_raw_code.jam']:shutil.copy2(PRE/'work/build'/n,O/'source'/n)
    L.writej(O/'source_pointer.json',cur)
assert L.readj(O/'source_pointer.json')==cur
m=L.read_meta(O/'source/candidate_meta.json');src=O/'source/NightRemaster.ain'
assert L.sha(src)==BASE and not any(f['name'].startswith('KR_N29') for f in m['functions'])
t=L.readj(R/'staging/calendar_april_summary_20260929/design/r19_tables.json')
overridden=set()
for stage in ['calendar_choices_20260929','calendar_choice_context_20260929']:
    old=L.readj(R/'staging'/stage/'design/label_patch.json')
    for key in ['ev_head','ev_short']:
        t[key].update(old['patch'][key]);overridden.update(old['patch'][key])
# Authored rule applies ONLY to these known names at the end of UI labels (or before a numeric suffix).
# Phrases with a following action, e.g. 이즈미와 촬영 / 쿄카와 동행, are explicitly excluded.
pat=re.compile(r'(이즈미|쿄카|마나미|마코토|호시카와|신카이|모모세)와(?=$| [0-9]+$)')
patch={key:{n:dict(before=s,after=pat.sub(r'\1',s)) for n,s in t[key].items() if pat.search(s)} for key,_,_,_ in SPEC}
assert all(n not in overridden for key in ['ev_short','ev_head'] for n in patch[key])
assert [patch['ev_short'][str(n)]['after'] for n in range(4,8)]==[f'{n-3}. 이즈미' for n in range(4,8)]
design=dict(translator_model='Codex internal',author='Codex root',source_sha256=BASE,
    quality_sha256=L.sha(Path('P:/AI/Codex/skills/contextual-game-localization/references/translation-quality.md')),
    scope='Standalone character-name labels in shared achievement/calendar scene lists and their headings; no dialogue or action-phrase edits.',
    patch=patch,counts={k:len(v) for k,v in patch.items()},preserved_action_examples={n:t['ev_short'][n] for n in ['323','324','60201','30153']})
L.writej(O/'design/label_patch.json',design)
L.writej(O/'design/expected_tables.json',{k:t[k] for k,_,_,_ in SPEC})
jaf=[]
for key,old,new,arg in SPEC:
    jaf.append(f'string {new}Base(int {arg}) {{ return ""; }}')
    body=[f'    string text={new}Base({arg});']
    for n,row in patch[key].items():
        body.append(f'    if({arg}=={n} && text=={json.dumps(row["before"],ensure_ascii=False)}) return {json.dumps(row["after"],ensure_ascii=False)};')
    body.append('    return text;')
    jaf.append(f'string {new}(int {arg}) {{\n'+'\n'.join(body)+'\n}')
jaf='\n\n'.join(jaf)+'\n'
(W/'helpers_readable.jaf').write_text(jaf,'utf8');(W/'helpers.jaf').write_text(L.jaf_literal_encode(jaf),'utf8')
decl=W/'declared.ain';out=O/'candidate/NightRemaster.ain'
L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl);dm=L.read_meta(W/'declared_meta.json')
added={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};assert len(added)==8
jams=[]
for key,old,new,arg in SPEC:
    clone=new+'Base';p=W/(old+'_original.jam');L.cmd('ain','dump','--function',old,'-o',p,src)
    a=m['functions'][L.fid_of(m,old)];b=dm['functions'][added[clone]]
    assert all(a[k]==b[k] for k in ['arguments','variables','return-type'])
    jam=L.clean(p.read_text('utf8'),old)
    jam=re.sub(r'(?m)^FUNC .*$',f'FUNC {added[clone]}',jam);jam=re.sub(r'(?m)^ENDFUNC .*$',f'ENDFUNC {clone}',jam)
    jams.append(jam)
    p=W/(new+'.jam');L.cmd('ain','dump','--function',new,'-o',p,decl)
    jams.append(L.clean(L.native_lower(p.read_text('utf8')),new))
    jams.append(f'FUNC {a["index"]}\n\t.LOCALREF {arg}\n\tCALLFUNC {new}\n\tRETURN\nENDFUNC {old}\n')
(W/'patch.jam').write_text('\n'.join(jams),'utf8');L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
base=L.unpack(src.read_bytes());raw=bytearray(L.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out);nm=L.read_meta(W/'candidate_meta.json')
changed=[L.fid_of(m,old) for _,old,_,_ in SPEC]
assert [i for i,(a,b) in enumerate(zip(m['functions'],nm['functions'])) if a!=b]==sorted(changed)
for i in changed:assert {k:v for k,v in m['functions'][i].items() if k!='address'}=={k:v for k,v in nm['functions'][i].items() if k!='address'}
for k in m:
    if k!='functions':assert m[k]==nm[k],k
oldn=struct.unpack_from('<I',base,12)[0];assert raw[16:16+oldn]==base[16:16+oldn]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert L.raw_messages(out.read_bytes())[3]==L.raw_messages(src.read_bytes())[3]
L.cmd('ain','dump','--raw-code','--no-macros','-o',W/'candidate_raw_code.jam',out)
audit=L.audit(out,W/'candidate_meta.json',W/'candidate_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported']
L.writej(W/'native_opcode_audit.json',audit);shutil.copy2(O/'source/winmm.dll',O/'candidate/winmm.dll')
L.writej(O/'candidate/manifest.json',dict(status='LABEL_PARTICLES_STAGED_NATIVE_PENDING',source_sha256=BASE,live_sha256=BASE,
    files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ['NightRemaster.ain','winmm.dll']},counts=design['counts'],
    changed_functions=[s[1] for s in SPEC],added_functions=added,original_code_prefix_exact=True,original_strings_prefix_exact=True,
    messages_exact=True,serialized_schema_changes=0,installed=False,translator_model='Codex internal'))
print(json.dumps(dict(candidate=str(out),sha256=L.sha(out),counts=design['counts']),ensure_ascii=False))
