"""Append one display menu: rename current protagonist and count registered events."""
import copy,json,re,struct,collections
from pathlib import Path
import build_term_switch_20260923 as b
from probe_player_tools_20260923 import O,R,EXPECTED,save
from build_mod_tab_20260915 import coords,scalar
HERE=Path(__file__).resolve().parent

def catalog(m):
 source=R.parent/'YoruGaKuru_flowchart_20260922/graph/schedule.json';doc=b.a.readj(source)
 jp=R/'translation_polish_20260917/input/jp.ain';assert b.a.sha(jp)==doc['game']['ain_sha256_original']
 b.cmd('ain','dump','-j','-o',O/'original_jp_meta.json',jp);jm=b.read_meta(O/'original_jp_meta.json')
 oldjam=O/'original_jp_raw.jam'
 if not oldjam.exists():b.cmd('ain','dump','--raw-code','--no-macros','-o',oldjam,jp)
 def event_ops(path,meta):
  out={};last=0;active=None
  for line in path.read_text('utf8').splitlines():
   if line.startswith('FUNC '):
    fid=int(line.split()[1]);f=meta['functions'][fid];active=fid if f['address']==last+6 and b.raw_symbol(meta,fid).startswith('ＥＶ／元／') else None
    if active is not None:out[active]=[]
    continue
   z=re.match(r'^0x([0-9a-fA-F]+):\s*(.*)',line)
   if not z:continue
   last=int(z[1],16)
   if active is None:continue
   ins=z[2].strip();op=ins.split(' ',1)[0]
   if op in ['FUNC','EOF','ENDFUNC']:continue
   if op in ['JUMP','IFZ','IFNZ']:ins=re.sub(r'0x[0-9a-fA-F]+',lambda mt:str(int(mt[0],16)-meta['functions'][active]['address']),ins)
   out[active].append(ins)
  return out
 oldops=event_ops(oldjam,jm);newops=event_ops(b.O/'native_raw_code.jam',m)
 lookup={b.raw_symbol(m,f['index']):f for f in m['functions']};picked=[];excluded=[]
 groups={'main':0,'after_training':1,'after_training_priority':1,'training_invite':2,'dungeon_walk':3}
 for e in doc['events']:
  if e['category'] not in groups or not e['triggers'] or not e['messages']['count']:
   excluded.append(dict(id=e['id'],category=e['category'],no_trigger=not e['triggers'],message_count=e['messages']['count']));continue
  f=lookup[e['fn']];assert newops[f['index']]==oldops[f['index']],('event gameplay changed',e['id'])
  if not e['registers_self']:assert all(t['kind']=='chained' for t in e['triggers']),e['id']
  picked.append(dict(id=e['id'],key=e['fn'].removeprefix('ＥＶ／元／'),fn=e['fn'],fid=f['index'],group=groups[e['category']],messages=e['messages']['count'],registers_self=e['registers_self'],triggers=e['triggers']))
 assert len(picked)==1043 and len({r['key'] for r in picked})==len(picked)
 save('event_catalog.json',dict(source=str(source),source_sha256=b.a.sha(source),original_ain_sha256=b.a.sha(jp),events=picked,excluded=excluded,group_counts=dict(collections.Counter(x['group'] for x in picked)),event_instructions_exact_with_relative_branch_targets=True,count_basis='Current save registered event IDs; all reachable dialogue events; replay, unknown/unreachable, system and zero-message trampolines excluded. Registration means entered, not fully read.'))
 code='int KR_PlayerEventCount(int group) { int count = 0;\n'
 for group in range(4):
  code+=f'if (group == {group}) {{\n'+''.join(f'if (N_ScenarioRegister::IsRegisteredEvent("{r["fn"]}")) count++;\n' for r in picked if r['group']==group)+'}\n'
 code+='return count;\n}'
 return code,collections.Counter(r['group'] for r in picked)

def assets(rt):
 d=b.ex.decode_ex(O/'original_185.pactex');root=d.blocks[2].payload.children[0]
 p=copy.deepcopy(b.part(d,'KR_TermConfigButton'));b.rename(p,'KR_PlayerInfoButton');b.setlist(p,'座標',[797,622,260]);b.add(root,p)
 from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
 from audit_dynamic_ui_20260915 import ENC
 _,faces=parse_fnl_font(rt/'NightRemasterFont.fnl',3);face,den,_=select_fnl_face(faces,20);w=WidthMeasurer(face,den,{c:sjis_bytes_to_fnl_index(v) for c,v in ENC.items()},0,0,0).measure('플레이 정보',True)['lines'][0]['width_px']
 p=copy.deepcopy(b.part(d,'KR_TermConfigLabel'));b.rename(p,'KR_PlayerInfoLabel');b.setlist(p,'座標',[797+(192-w)/2,627,261]);b.ss(b.txt_info(p),'テキ스트' if False else 'テキスト','플레이 정보',True);b.add(root,p)
 out=O/'pact_185_player_tools.pactex';out.write_bytes(b.ex.encode_ex(d.header,d.serialize_payload()));rev=b.ex.decode_ex(out);rr=rev.blocks[2].payload.children[0];b.remove(rr,'KR_PlayerInfoButton');b.remove(rr,'KR_PlayerInfoLabel');assert rev.serialize_payload()==d.raw_payload
 ar=b.rebuild(O/'baseline_NightRemasterPact.afa',O/'NightRemasterPact.afa',{185:out});return dict(changed_entries=[185],reverse_exact=True,archive=ar,button=[797,622,192,30],label_width=w)

def main():
 ptr=b.a.readj(O/'source_pointer.json');rt=Path(ptr['runtime']);src=O/'baseline_NightRemaster.ain';assert b.a.sha(src)==b.a.sha(rt/'NightRemaster.ain')==EXPECTED and ptr==b.a.readj(R/'ui_cumulative/current.json')
 m=b.read_meta(O/'baseline_meta.json');code,counts=catalog(m);jaf=(HERE/'player_tools_helpers_20260923.jaf').read_text('utf8')
 alphabet=''.join(x['unicode_character'] for x in b.a.readj(b.a.PROXY)['mapping'] if '\uac00'<=x['unicode_character']<='\ud7a3')
 jaf=jaf.replace('@@ALPHABET@@',alphabet).replace('/*EVENT_FUNCTIONS*/',code)
 for k,v in dict(TOTAL=sum(counts.values()),STORY=counts[0],TRAINING=counts[1],INVITE=counts[2],WALK=counts[3]).items():jaf=jaf.replace('@@'+k+'@@',str(v))
 (O/'helpers_readable.jaf').write_text(jaf,'utf8');jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(b.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False),jaf);(O/'helpers_proxy.jaf').write_text(jaf,'utf8')
 declared=O/'declared.ain';b.cmd('ain','edit','--jaf',O/'helpers_proxy.jaf','-o',declared,src)
 data=bytearray(b.unpack(declared.read_bytes()));size=struct.unpack_from('<I',data,12)[0];struct.pack_into('<I',data,24+size,m['functions'][0]['address']);declared.write_bytes(b.pack(data,src.read_bytes()[:8]))
 b.cmd('ain','dump','-j','-o',O/'declared_meta.json',declared);dm=b.read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};patches={};edits=[]
 for name,i in ids.items():
  p=O/f'jaf_{i}.jam';b.cmd('ain','dump','--function',name,'-o',p,declared);patches[i]=b.clean(b.native_lower(p.read_text('utf8')),name)
 i=ids['KR_PlayerReadyFlag'];patches[i]=f'FUNC {i}\n\t.GLOBALREF Flags\n\tPUSH 26485\n\tCALLMETHOD 0\n\tRETURN\nENDFUNC KR_PlayerReadyFlag\n'
 i=ids['KR_PlayerReady'];assert dm['functions'][i]['variables'][0]['name']=='scene';delegate=json.dumps(m['delegates'][1251]['name'],ensure_ascii=False);assert b.raw_symbol(m,28170)=='C_SceneGame@GetSceneType'
 patches[i]=f'''FUNC {i}
\tCALLFUNC KR_PlayerReadyFlag
\tIFZ rename_not_ready
\tCALLFUNC Ａ＿回想モード実行中確認
\tIFNZ rename_not_ready
\tPUSHLOCALPAGE
\tPUSH 0
\t.GLOBALREF GetActiveScene
\tDG_CALLBEGIN {delegate}
rename_get_scene:
\tDG_CALL {delegate} rename_got_scene
\tJUMP rename_get_scene
rename_got_scene:
\tPOP
\tX_ASSIGN 1
\tPOP
\t.LOCALREF scene
\tPUSH -1
\tEQUALE
\tIFNZ rename_not_ready
\t.LOCALREF scene
\tPUSH 0
\tX_REF 1
\tPUSH 0
\tX_REF 1
\tPUSH 28170
\tEQUALE
\t.LOCALDELETE scene
\tRETURN
rename_not_ready:
\t.LOCALDELETE scene
\tPUSH 0
\tRETURN
ENDFUNC KR_PlayerReady
'''
 for i in [29815,29823]:
  before=b.clean((O/f'original_{i}.jam').read_text('utf8'),b.symbol(m,i))
  if i==29815:pfx='\tPUSHSTRUCTPAGE\n'+b.push(29822)+b.lr('ActivityName')+'\tA_REF\n'+b.S('KR_PlayerInfoButton')+'\tCALLMETHOD 2\n'
  else:pfx='\tPUSHSTRUCTPAGE\n'+b.push(29824)+b.lr('number')+b.S('KR_PlayerInfoButton')+b.push(-1)+b.push(ids['KR_PlayerInfoMenu'])+'\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 3\n'
  patches[i]=b.begin(before,pfx);edits.append(dict(fid=i,before=before,after=patches[i]))
 (O/'patch.jam').write_text('\n'.join(patches.values()),'utf8');out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,declared);b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 for i,f in enumerate(m['functions']):
  expected=copy.deepcopy(f)
  if i in [29815,29823]:expected['address']=nm['functions'][i]['address']
  assert expected==nm['functions'][i],i
 old=b.unpack(src.read_bytes());new=b.unpack(out.read_bytes());n=struct.unpack_from('<I',old,12)[0];assert old[16:16+n]==new[16:16+n]
 assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3] and b.strings(new)[2][:len(b.strings(old)[2])]==b.strings(old)[2]
 for i in patches:b.cmd('ain','dump','--function',b.symbol(nm,i),'-o',O/f'built_{i}.jam',out)
 b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported'];save('native_opcode_audit.json',audit)
 art=assets(rt);save('reversible_hook_edits.json',edits);save('build_evidence.json',dict(status='PLAYER_TOOLS_STAGED',source_pointer=ptr,source_files={n:b.a.sha(rt/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},files={n:b.a.sha(O/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},patched_existing=[29815,29823],added_functions=ids,PACT=art,MSG1_exact=True,old_CODE_prefix_exact=True,old_STR0_exact=True,globals_structures_exact=True,save_schema_changes=0,native_verified=False,translator_model='Codex internal',event_count=sum(counts.values())))
 print(b.a.readj(O/'build_evidence.json'))
if __name__=='__main__':main()
