"""Append-only detail-board correction on the installed portrait build."""
from pathlib import Path
import sys,json,struct,re,shutil
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
O=L.CODEX/'staging/calendar_detail_layout_20260929';W=O/'work/build';W.mkdir(parents=True,exist_ok=True)
L.TMP=O/'work/tmp';L.TMP.mkdir(exist_ok=True)
src=O/'source/NightRemaster.ain';out=O/'candidate/NightRemaster.ain'
assert L.sha(src)=='5f9b4cb43e393f6a9a9f269c3ac71e32e9262497f4495a034bbc2d50fe27d459'
m=L.read_meta(O/'source/candidate_meta.json');fid=lambda n:L.fid_of(m,n)
cards={}
for row in L.readj(O/'design/cells.json'):
    if row['ref']<100000:continue
    k=row['ref']-100000
    assert row['no'] not in cards or cards[row['no']]==k
    cards[row['no']]=k
table='int KR_B29Card(int no) {\n'+''.join(f'    if (no=={no}) return {k};\n' for no,k in sorted(cards.items()))+'    return -1;\n}\n'
jaf=table+(HERE/'calendar_detail_layout_20260929.jaf').read_text('utf8')
(W/'helpers_readable.jaf').write_text(jaf,'utf8');(W/'helpers.jaf').write_text(L.jaf_literal_encode(L.strip_comments(jaf)),'utf8')
decl=W/'declared.ain';L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl);dm=L.read_meta(W/'declared_meta.json')
added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[]
for f in added:
    n=f['name'];p=W/(n+'.jam');L.cmd('ain','dump','--function',n,'-o',p,decl);jam=p.read_text('utf8')
    jam=re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',lambda z:'\t.LOCALASSIGN '+z[1]+' '+str(struct.unpack('<i',struct.pack('<f',float(z[2])))[0]),jam)
    patch.append(L.clean(L.native_lower(jam).replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),n))
forward={'KR_P29Board':'KR_B29Board','KR_P29Buttons':'KR_B29Buttons'}
for old,new in forward.items():
    f=m['functions'][fid(old)];g=dm['functions'][ids[new]]
    assert f['return-type']==g['return-type'] and [a['type'] for a in f['arguments']]==[a['type'] for a in g['arguments']]
    args=''.join(f"\t.LOCALREF {a['name']}\n"+('\tA_REF\n' if a['type'][0]==12 else '') for a in f['arguments'])
    patch.append(f'FUNC {fid(old)}\n{args}\tCALLFUNC {new}\n\tRETURN\nENDFUNC {old}\n')
(W/'patch.jam').write_text('\n'.join(patch),'utf8');L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
base=L.unpack(src.read_bytes());raw=bytearray(L.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out);nm=L.read_meta(W/'candidate_meta.json')
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
L.writej(O/'candidate/manifest.json',dict(status='STAGED_NATIVE_PENDING',files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ['NightRemaster.ain','winmm.dll']},source_sha256=L.sha(src),forwarded=forward,added_functions=ids,new_globals=0,serialized_schema_changes=0,old_code_prefix_exact=True,messages_exact=True,dll_unchanged=True,mini_size=[32,40],detail_size=[104,130],summary_events=[11],restored_fields=['when','who','read_state','read_stages/total_stages','conditions','no_replay_reason'],translator_model='Codex internal'))
print('BUILT',L.sha(out),len(added),'helpers; DLL unchanged')
