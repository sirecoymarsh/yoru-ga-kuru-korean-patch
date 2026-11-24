"""Adaptive April list minis on the frozen, verified summary candidate."""
from pathlib import Path
import sys,re,struct,shutil,json
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
R=L.CODEX;PRE=R/'staging/calendar_april_summary_20260929';O=R/'staging/calendar_april_adaptive_minis_20260929'
W=O/'work/build';L.TMP=O/'work/tmp'
BASE='928c52bb738d57ffddce3abeeac640a18a1e686b3782c6f6308156f31fcaff38'
LIVE='1a7bd3352132f123f2dd1cf8491b8faf16391b7361a57d6f76585843b4757542'
cur=L.readj(L.CURRENT);rt=Path(cur['runtime'])
assert L.sha(PRE/'candidate/NightRemaster.ain')==BASE and L.sha(rt/'NightRemaster.ain')==LIVE
if not O.exists():
    for d in ('source','design','work/build','work/tmp','candidate','evidence','probe'):(O/d).mkdir(parents=True)
    for n in ('NightRemaster.ain','winmm.dll'):shutil.copy2(PRE/'candidate'/n,O/'source'/n)
    for n in ('candidate_meta.json','candidate_raw_code.jam'):shutil.copy2(PRE/'work/build'/n,O/'source'/n)
    for n in ('cells.json','cast_evidence.json','scope.json'):shutil.copy2(PRE/'design'/n,O/'design'/n)
    L.writej(O/'source_pointer.json',cur)
assert cur==L.readj(O/'source_pointer.json')
src=O/'source/NightRemaster.ain';assert L.sha(src)==BASE
oldraw=(O/'source/candidate_raw_code.jam').read_text('utf-8',errors='replace')
assert not any('PUSH '+str(i) in oldraw for i in range(2026095000,2026095240))
jaf=(H/'calendar_april_adaptive_minis_20260929.jaf').read_text('utf-8')
(W/'helpers_readable.jaf').write_text(jaf,'utf-8');(W/'helpers.jaf').write_text(L.jaf_literal_encode(jaf),'utf-8')
decl=W/'declared.ain';out=O/'candidate/NightRemaster.ain';m=L.read_meta(O/'source/candidate_meta.json')
L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl);dm=L.read_meta(W/'declared_meta.json')
added={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]}
assert len(added)==5 and all(n.startswith('KR_AM29') for n in added)
patch=[]
for n in added:
    p=W/(n+'.jam');L.cmd('ain','dump','--function',n,'-o',p,decl)
    jam=L.native_lower(p.read_text('utf-8'))
    jam=re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',lambda z:'\t.LOCALASSIGN '+z[1]+' '+str(struct.unpack('<i',struct.pack('<f',float(z[2])))[0]),jam)
    patch.append(L.clean(jam.replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),n))
routes={'KR_CDraw':'KR_AM29Draw','KR_P29DropMinis':'KR_AM29Drop'}
for name,target in routes.items():
    f=m['functions'][L.fid_of(m,name)]
    patch.append('FUNC '+str(f['index'])+'\n'+''.join('\t.LOCALREF '+a['name']+'\n' for a in f['arguments'])+'\tCALLFUNC '+target+'\n\tRETURN\nENDFUNC '+name+'\n')
(W/'patch.jam').write_text('\n'.join(patch),'utf-8');L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
base=L.unpack(src.read_bytes());raw=bytearray(L.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out);nm=L.read_meta(W/'candidate_meta.json');changed=[L.fid_of(m,n) for n in routes]
assert [i for i,(a,b) in enumerate(zip(m['functions'],nm['functions'])) if a!=b]==sorted(changed)
for i in changed:
    assert {k:v for k,v in m['functions'][i].items() if k!='address'}=={k:v for k,v in nm['functions'][i].items() if k!='address'}
for k in m:
    if k!='functions':assert m[k]==nm[k],k
oldn=struct.unpack_from('<I',base,12)[0];assert raw[16:16+oldn]==base[16:16+oldn]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert L.raw_messages(out.read_bytes())[3]==L.raw_messages(src.read_bytes())[3]
L.cmd('ain','dump','--raw-code','--no-macros','-o',W/'candidate_raw_code.jam',out)
audit=L.audit(out,W/'candidate_meta.json',W/'candidate_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported']
L.writej(W/'native_opcode_audit.json',audit);shutil.copy2(O/'source/winmm.dll',O/'candidate/winmm.dll')
L.writej(O/'candidate/manifest.json',dict(status='APRIL_ADAPTIVE_MINIS_NATIVE_PENDING',source_sha256=BASE,live_sha256=LIVE,
    files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ('NightRemaster.ain','winmm.dll')},changed_functions=list(routes),added_functions=added,
    original_code_prefix_exact=True,original_strings_prefix_exact=True,messages_exact=True,serialized_schema_changes=0,installed=False,
    scope='April list only; preserve summaries, details, other months and user session',portrait_size=[32,40],max_capacity=8))
print(json.dumps({'candidate':str(out),'sha256':L.sha(out),'helpers':len(added)},ensure_ascii=False))
