"""Build WI-007 from the frozen installed AIN; no live installation."""
from pathlib import Path
import sys, re, struct, shutil, json
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
F = Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0, str(F))
import r24lib as L
R = L.CODEX
O = R/'staging/calendar_april_readability_20260929'
W = O/'work/build'
L.TMP = O/'work/tmp'
BASE = '1a7bd3352132f123f2dd1cf8491b8faf16391b7361a57d6f76585843b4757542'
cur = L.readj(L.CURRENT)
rt = Path(cur['runtime'])
assert L.sha(rt/'NightRemaster.ain') == BASE
first = not O.exists()
for d in ('source', 'design', 'work/build', 'work/tmp', 'candidate', 'evidence', 'probe'):
    (O/d).mkdir(parents=True, exist_ok=True)
pre = R/'staging/calendar_choice_context_20260929'
fields = R/'staging/calendar_april_fields_20260929'
if first:
    for n in ('NightRemaster.ain', 'winmm.dll'):
        shutil.copy2(rt/n, O/'source'/n)
    for n in ('candidate_meta.json', 'candidate_raw_code.jam'):
        shutil.copy2(pre/'work/build'/n, O/'source'/n)
    for n in ('cells.json', 'cast_evidence.json', 'r15_tables.json'):
        shutil.copy2(pre/'design'/n, O/'design'/n)
    shutil.copy2(fields/'work/build/helpers_readable.jaf', O/'source/fields_helpers.jaf')
    shutil.copy2(R/'staging/calendar_map_20260929/design/r19_tables.json', O/'design/r19_tables.json')
    L.writej(O/'source_pointer.json', cur)
assert L.sha(O/'source/NightRemaster.ain') == BASE
assert L.readj(O/'source_pointer.json') == cur

def function(text, name):
    start = re.search(r'^(?:void|int|string|bool) '+re.escape(name)+r'\(', text, re.M).start()
    pos = text.index('{', start)+1
    depth = 1
    while depth:
        depth += (text[pos]=='{')-(text[pos]=='}')
        pos += 1
    return text[start:pos]

cells = L.readj(O/'design/cells.json')
cards = L.readj(O/'design/r15_tables.json')['cards']
ids = sorted({c['no'] for c in cells if c['tab']==0} | {n for c in cards if c['month']==4 for n in c['stages']})
assert len(ids)==146
assert [(c['k'],c['stages']) for c in cards if c['month']==4 and c['size']>1] == [(6,[4,5,6,7])]
assert not set(ids)&{int(n) for n in L.readj(pre/'design/label_patch.json')['dates']}
old = (O/'source/fields_helpers.jaf').read_text('utf-8')
field = function(old,'KR_L29Field').replace('KR_L29','KR_U29')
board = function(old,'KR_L29Board').replace('KR_L29','KR_U29')
board = board.replace('string title=head;', 'string title=KR_U29Head(no,head,stages);')
board = board.replace('"미열람 이벤트"','"아직 보지 않은 장면"').replace('"열람 후 표시됩니다"','"감상 후 표시됩니다"')
extra = (H/'calendar_april_readability_20260929.jaf').read_text('utf-8')
pred = ' || '.join(f'no=={n}' for n in ids)
heads = L.readj(O/'design/r19_tables.json')['ev_head']
newheads = {str(n): heads[str(n)].replace(f'{n-3}단계', f'장면 {n-3}') for n in [4,5,6,7]}
q = lambda s: json.dumps(s, ensure_ascii=False)
headfun = 'string KR_U29Head(int no,string head,int stages) {\n'
headfun += '    if(no==4 && stages>1)return "4월 중 · 던전 · 공원 · 사건 1 · 장면 4개";\n'
for n,t in newheads.items():
    headfun += f'    if(no=={n})return {q(t)};\n'
headfun += '    return head;\n}\n'
router = f'''bool KR_U29April(int no) {{ return {pred}; }}
void KR_U29Router(int no,string head,int stages,bool canplay) {{
    if(KR_U29April(no))KR_U29Board(no,head,stages,canplay);
    else KR_B29Board(no,head,stages,canplay);
}}
'''
jaf = field+'\n'+headfun+'\n'+extra+'\n'+board+'\n'+router
(W/'helpers_readable.jaf').write_text(jaf,'utf-8')
(W/'helpers.jaf').write_text(L.jaf_literal_encode(jaf),'utf-8')
src = O/'source/NightRemaster.ain'
decl = W/'declared.ain'
out = O/'candidate/NightRemaster.ain'
m = L.read_meta(O/'source/candidate_meta.json')
L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl)
dm = L.read_meta(W/'declared_meta.json')
added = {f['name']:f['index'] for f in dm['functions'][len(m['functions']):]}
assert all(n.startswith('KR_U29') for n in added)
patch=[]
for n in added:
    p=W/(n+'.jam')
    L.cmd('ain','dump','--function',n,'-o',p,decl)
    jam=L.native_lower(p.read_text('utf-8'))
    jam=re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',lambda z:'\t.LOCALASSIGN '+z[1]+' '+str(struct.unpack('<i',struct.pack('<f',float(z[2])))[0]),jam)
    patch.append(L.clean(jam.replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),n))
routes={'KR_P29Board':('KR_B29Board','KR_U29Router'),
        'KR_P29Buttons':('KR_B29Buttons','KR_U29Buttons'),
        'KR_CDraw':('KR_C24Draw','KR_U29Draw'),
        'KR_T9StagePage':('KR_T19StagePage','KR_U29Stages')}
for name,(oldtarget,newtarget) in routes.items():
    p=W/(name+'_original.jam')
    L.cmd('ain','dump','--function',name,'-o',p,src)
    body=L.clean(p.read_text('utf-8'),name)
    assert body.count('CALLFUNC '+oldtarget)==1
    patch.append(body.replace('CALLFUNC '+oldtarget,'CALLFUNC '+newtarget))
(W/'patch.jam').write_text('\n'.join(patch),'utf-8')
L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
base=L.unpack(src.read_bytes())
raw=bytearray(L.unpack(out.read_bytes()))
size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out)
nm=L.read_meta(W/'candidate_meta.json')
changed=[L.fid_of(m,n) for n in routes]
assert [i for i,(a,b) in enumerate(zip(m['functions'],nm['functions'])) if a!=b]==sorted(changed)
for i in changed:
    assert {k:v for k,v in m['functions'][i].items() if k!='address'}=={k:v for k,v in nm['functions'][i].items() if k!='address'}
for k in m:
    if k!='functions': assert m[k]==nm[k],k
oldn=struct.unpack_from('<I',base,12)[0]
assert raw[16:16+oldn]==base[16:16+oldn]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert L.raw_messages(out.read_bytes())[3]==L.raw_messages(src.read_bytes())[3]
L.cmd('ain','dump','--raw-code','--no-macros','-o',W/'candidate_raw_code.jam',out)
audit=L.audit(out,W/'candidate_meta.json',W/'candidate_raw_code.jam',rt/'NightRemaster.exe')
assert audit['all_active_opcodes_supported']
L.writej(W/'native_opcode_audit.json',audit)
shutil.copy2(O/'source/winmm.dll',O/'candidate/winmm.dll')
L.writej(O/'design/scope.json',dict(april_event_ids=ids,april_cells=143,scope='April list, detail, park scene selection only',other_months_unchanged=True,installed=False,
    labels=['언제','인물','열람 상태','재생','장면 묶음','조건'],head_revisions=newheads,translator_model='Codex internal',author='/root',
    preserves=['E identifiers','protagonist','portraits','date and condition values','original replay eligibility','read flags','save schema','scenario'],
    existing_summary_ids=[11],new_summaries=[]))
L.writej(O/'candidate/manifest.json',dict(status='APRIL_READABILITY_PREVIEW_NATIVE_PENDING',source_sha256=BASE,
    files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ('NightRemaster.ain','winmm.dll')},changed_functions=list(routes),added_functions=added,
    original_code_prefix_exact=True,original_strings_prefix_exact=True,messages_exact=True,serialized_schema_changes=0,translator_model='Codex internal',installed=False))
print(json.dumps({'candidate':str(out),'sha256':L.sha(out),'april_events':len(ids),'helpers':len(added)},ensure_ascii=False))
