"""Rebase term preferences on the installed translation; display-only, additive native code."""
from pathlib import Path
import collections,copy,functools,json,re,struct,shutil
from build_remaster_multiplier_20260915 import cmd,ex,read_afa3,rebuild,part,child,val,si,ss,setlist,rename,txt_info,encode,decode
from build_mod_tab_20260915 import add,remove
from integrate_ui_opening_20260913 import read_meta
from build_route_perf_20260915 import symbol as raw_symbol
from build_instant_loot_20260915 import clean,begin
from build_dungeon_sweep_20260916 import S,push,cf,lr
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from polish_translation_20260917 import raw_messages
from audit_sys43_native_opcodes_20260915 import native_lower,audit
import review_claude_handoff_20260923 as a
R=a.R;O=R/'staging/term_switch_20260923';HERE=Path(__file__).resolve().parent
EXPECTED='baef6ec000683bc9fdb3660ebbca2a5a841b3f487c05780febeb3efe90fcacf4'
TERMS=[('히카리',['히카리','광수','빛잡이'],108),('카샤',['카샤','화자','불지기'],108),('치로',['치로','쉭쉭이'],108),('틈새',['틈새','하자마','틈'],108),('얼어붙은 밤',['얼어붙은 밤','토야','동야'],192),('참된 달',['참된 달','진월','참달'],120),('참된 밤',['참된 밤','진야','참밤'],120)]
RAW_GETTERS=[(26155,'KR_TermRawMonster','C_Monster'),(26810,'KR_TermRawWeapon','C_Weapon'),(26668,'KR_TermRawItem','C_ConsumeItem')]
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def symbol(m,i):
 n=raw_symbol(m,i);prior=sum(f['name']==m['functions'][i]['name'] for f in m['functions'][:i])
 return n+(f'#{prior}' if prior else '')
def width(s):return sum(12 if c==' ' else 36 for c in s)
def quote(s):return json.dumps(s,ensure_ascii=False)
def coda(s):return (ord(s[-1])-0xac00)%28 if s and '\uac00'<=s[-1]<='\ud7a3' else 0
# Only complete attested suffix units; never rewrite unrelated following words.
PAIRS=[('였','이었',False),('여서','이어서',False),('여야','이어야',False),('예요','이에요',False),('래','이래',False),('란','이란',False),('랄','이랄',False),('라','이라',False),('나','이나',False),('랑','이랑',False),('든','이든',False),('야','이야',False),('다','이다',False),('지','이지',False),('잖','이잖',False),('냐','이냐',False),('군','이군',False),('네','이네',False),('니까','이니까',False),('거든','이거든',False),('니','이니',False),('고','이고',False),('로군','이로군',False),('로','으로',True),('는','은',False),('가','이',False),('를','을',False),('와','과',False)]
def suffix(t,i):
 close=''
 while t and t[0] in '」』】”\"':close+=t[0];t=t[1:]
 base=TERMS[i][0];co=coda(base)
 for vo,ca,rieul in PAIRS:
  src=vo if co==0 or (rieul and co==8) else ca
  if not t.startswith(src):continue
  rest=t[len(src):]
  # Restrict short ambiguous particles/copulas to valid endings or boundaries.
  word=re.split(r'[\s\W]',rest,1)[0]
  ok=True
  if vo in ['는','가','를','와','로']:ok=word in ['', '는','도','만','의','서','서는','서도','서의','써','써는','부터','커녕']
  if vo=='나':ok=word in ['','마','마도']
  if vo=='야':ok=word in ['','말로','만','도']
  if vo in ['다','지','냐','군','네']:ok=word in ['','고','는','만','요','요만','만요']
  if vo=='라':ok=word.startswith(('고','는','면','서','도','니','서야','며','든')) or word==''
  if not ok:continue
  return close,vo,ca,rieul,rest
 return close,None,None,False,t
def tokens(text):
 out=[];cursor=0
 pat='|'.join(re.escape(t[0]) for t in TERMS)
 for mt in re.finditer(pat,text):
  if mt.start()<cursor:continue
  if mt.start()>0 and '\uac00'<=text[mt.start()-1]<='\ud7a3':continue
  i=next(i for i,t in enumerate(TERMS) if t[0]==mt[0])
  if mt.start()>cursor:out.append(('s',text[cursor:mt.start()]))
  out.append(('t',i));close,vo,ca,rieul,rest=suffix(text[mt.end():],i)
  if close:out.append(('s',close))
  if vo:out.append(('p',(i,vo,ca,rieul)))
  cursor=len(text)-len(rest)
 if cursor<len(text):out.append(('s',text[cursor:]))
 return out
def render(ts,values=None,worst=False):
 s=''
 for k,v in ts:
  if k=='s':s+=v
  elif k=='t':s+=('가'*(TERMS[v][2]//36)+' '*(TERMS[v][2]%36//12)) if worst else (values or [x[0] for x in TERMS])[v]
  else:
   i,vo,ca,rieul=v;n=(values or [x[0] for x in TERMS])[i]
   s+=(vo if i<4 else max([vo,ca],key=width)) if worst else vo if coda(n)==0 or (rieul and coda(n)==8) else ca
 return s
def expr(ts):
 parts=[]
 for k,v in ts:
  if k=='s':parts.append(quote(v))
  elif k=='t':parts.append(f'KR_TermGet({v})')
  else:
   i,vo,ca,rieul=v;parts.append(f'KR_TermParticle({i}, {quote(vo)}, {quote(ca)}, '+str(rieul).lower()+')')
 return ' + '.join(parts) or '""'
def wrap(text,budget,quoted):
 lines=[]
 while text:
  indent='　' if quoted and lines else '';limit=budget-width(indent)
  if width(text)<=limit:lines.append(indent+text);break
  positions=[i for i,c in enumerate(text) if c==' ' and i>0 and width(text[:i])<=limit]
  if not positions:positions=[i for i in range(1,len(text)+1) if width(text[:i])<=limit]
  if not positions:return None
  cut=max(positions);lines.append(indent+text[:cut]);text=text[cut:].lstrip(' ')
 return lines
def prepare_tables():
 src=O/'baseline_NightRemaster.ain';raw=raw_messages(src.read_bytes())[3];msgs=[decode(x) for x in raw]
 entries={i:tokens(t) for i,t in enumerate(msgs) if any(k=='t' for k,v in tokens(t))}
 assert all(render(t)==msgs[i] for i,t in entries.items()),'default must roundtrip exactly'
 pages=a.readj(a.HERE/'message_page_groups.json')['pages'];dynamic={};records=[];fail=[]
 classification={r['message_id']:r for r in a.readj(a.HERE/'message_window_classification.json')['rows']}
 for pg in pages:
  ids=pg['body_message_ids'];hit=[i for i in ids if i in entries]
  if not hit:continue
  budget=716 if pg['window_type']=='Face' else 932
  if all(width(render(entries.get(i,[('s',msgs[i])]),worst=True))<=budget for i in ids):continue
  assert pg['complete'] and pg['font_command']==0 and pg['window_type'] in ['Face','Text','All']
  nonempty=[msgs[i] for i in ids if msgs[i].strip()];quoted=nonempty[0].startswith(('「','（'))
  full=' '.join(t.strip('　 ') for t in nonempty);full=re.sub(r' (?=[」』）】!?！？.,、。])','',full)
  ts=tokens(full);worst=render(ts,worst=True);lines=wrap(worst,budget,quoted)
  if lines is None or len(lines)>len(ids):fail.append(dict(ids=ids,budget=budget,text=full,lines=lines));continue
  for pos,i in enumerate(ids):dynamic[i]=f'KR_TermWrapLine({expr(ts)}, {budget}, {pos}, {str(quoted).lower()})'
  records.append(dict(ids=ids,budget=budget,worst=lines,quoted=quoted,source=full))
 save('layout_failures.json',fail);save('dynamic_pages.json',records)
 if fail:raise AssertionError(('term page capacity',len(fail)))
 bodies=collections.defaultdict(list);coverage=[]
 for i in sorted(set(entries)|set(dynamic)):
  expression=dynamic.get(i,expr(entries[i]) if i in entries else quote(msgs[i]))
  bodies[i//1000].append(f'if (id == {i} && text == {quote(msgs[i])}) return {expression};')
  coverage.append(dict(id=i,source=msgs[i],tokens=entries.get(i),dynamic_page=i in dynamic))
 code=[]
 for group,body in bodies.items():code.append(f'string KR_TermMsg{group}(int id, string text) {{\n'+ '\n'.join(body)+'\nreturn text;\n}')
 code.append('string KR_TermMessage(int id, string text) {\nif (SystemService.SystemVariable_Get("YoruKR.Term.Active") != "1") return text;\n'+ '\n'.join(f'if (id >= {g*1000} && id < {(g+1)*1000}) return KR_TermMsg{g}(id, text);' for g in bodies)+'\nreturn text;\n}')
 # STR0 only by exact displayed value; EX names are separately whitelisted at getters.
 st=[decode(b) for b in strings(unpack(src.read_bytes()))[2]]
 displays=set(t for t in st if any(k=='t' for k,v in tokens(t)) and not any(c in t for c in ['\\','/','%','{','}']))
 # EX display names are collected from known display getter backing fields below, not generic EX hooks.
 d=ex.decode_ex(O/'baseline_NightRemasterEX.ex')
 def walk(n):
  if isinstance(n,ex.StringNode):
   try:yield decode(n.value)
   except (UnicodeError,KeyError):pass
  for attr in ['blocks','rows','items','children']:
   arr=getattr(n,attr,None)
   if arr:
    for v in arr:
     if isinstance(v,list):
      for x in v:yield from walk(x)
     else:yield from walk(v)
  for attr in ['payload','leaf_value','value']:
   v=getattr(n,attr,None)
   if v is not None and not isinstance(v,(str,bytes,int,float)):yield from walk(v)
 for t in walk(d):
  if any(k in t for k in ['카샤','틈','치로','히카리']):displays.add(t)
 display_rows=[]
 for text in sorted(displays):
  ts=tokens(text)
  # This exact EX dungeon-name family uses a shorter localized label.
  if re.fullmatch(r'수수께끼의 틈[ 0-9①-⑳]*',text):ts=[('s','수수께끼의 '),('t',3),('s',text.split('틈',1)[1])]
  if not any(k=='t' for k,v in ts):continue
  display_rows.append(dict(source=text,tokens=ts))
 code.append('string KR_TermDisplay(string text) {\nif (SystemService.SystemVariable_Get("YoruKR.Term.Active") != "1") return text;\n'+'\n'.join(f'if (text == {quote(r["source"])}) return {expr(r["tokens"])};' for r in display_rows)+'\nreturn text;\n}')
 save('term_coverage.json',coverage);save('display_terms.json',display_rows)
 return '\n'.join(code)

def assets():
 src=O/'baseline_NightRemasterPact.afa';arc=read_afa3(src);entry=arc.entries[185]
 with src.open('rb') as f:f.seek(entry.absolute_offset);raw=f.read(entry.size)
 (O/'original_185.pactex').write_bytes(raw);d=ex.decode_ex(O/'original_185.pactex');root=d.blocks[2].payload.children[0]
 b=copy.deepcopy(part(d,'KR_ItemConfigButton'));rename(b,'KR_TermConfigButton');setlist(b,'座標',[580,622,260]);add(root,b)
 from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
 from audit_dynamic_ui_20260915 import ENC
 fp=Path(a.readj(O/'source_pointer.json')['runtime'])/'NightRemasterFont.fnl'
 _,faces=parse_fnl_font(fp,3);face,den,_=select_fnl_face(faces,20)
 tw=WidthMeasurer(face,den,{c:sjis_bytes_to_fnl_index(v) for c,v in ENC.items()},0,0,0).measure('용어 표기 설정',True)['lines'][0]['width_px'];assert tw<=180
 label=copy.deepcopy(part(d,'KR_ItemConfigLabel'));rename(label,'KR_TermConfigLabel');setlist(label,'座標',[580+(192-tw)/2,627,261]);ss(txt_info(label),'テキスト','용어 표기 설정',True);add(root,label)
 path=O/'pact_185_terms.pactex';path.write_bytes(ex.encode_ex(d.header,d.serialize_payload()))
 reverse=ex.decode_ex(path);rr=reverse.blocks[2].payload.children[0];remove(rr,'KR_TermConfigButton');remove(rr,'KR_TermConfigLabel');assert reverse.serialize_payload()==d.raw_payload
 ar=rebuild(src,O/'NightRemasterPact.afa',{185:path})
 return dict(changed_entries=[185],reverse_exact=True,archive=ar,button=[580,622,192,30],font_color=[255,230,80])

def main():
 ptr=a.readj(O/'source_pointer.json');rt=Path(ptr['runtime']);src=O/'baseline_NightRemaster.ain'
 assert a.sha(src)==a.sha(rt/'NightRemaster.ain')==EXPECTED and a.readj(R/'ui_cumulative/current.json')==ptr
 m=read_meta(O/'baseline_meta.json');render_code=prepare_tables()
 jaf=(HERE/'term_switch_helpers_20260923.jaf').read_text('utf8')
 jaf=jaf.replace('/*DEFAULTS*/',' '.join(f'if (i == {i}) return {quote(t[0])};' for i,t in enumerate(TERMS)))
 jaf=jaf.replace('/*CAPS*/',' '.join(f'if (i == {i}) return {t[2]};' for i,t in enumerate(TERMS)))
 jaf=jaf.replace('/*PRESETS*/',' '.join(f'if (i == {i} && n == {j}) return {quote(s)};' for i,t in enumerate(TERMS) for j,s in enumerate(t[1])))
 jaf=jaf.replace('for (int j = 0; j < 3; j++)','for (int j = 0; j < 3; j++)').replace('■選択ダイアログ／選択肢追加(j + 1, KR_TermPreset(item, j), "", false);','{ if (item != 2 || j < 2) ■選択ダイアログ／選択肢追加(j + 1, KR_TermPreset(item, j), "", false); }')
 proxy=a.readj(a.PROXY);alphabet=''.join(x['unicode_character'] for x in proxy['mapping'] if '\uac00'<=x['unicode_character']<='\ud7a3')+' '
 jaf=jaf.replace('@@ALPHABET@@',alphabet).replace('/*RENDER_TABLES*/',render_code)
 jaf+='\n'+'\n'.join(f'string {n}(ref {c} self) {{ return ""; }}' for _,n,c in RAW_GETTERS)
 (O/'helpers_readable.jaf').write_text(jaf,'utf8');save('term_definitions.json',[dict(default=t[0],choices=t[1],max_width=t[2],translator_model='Codex internal') for t in TERMS])
 jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False),jaf)
 (O/'helpers_proxy.jaf').write_text(jaf,'utf8');decl=O/'declared.ain';cmd('ain','edit','--jaf',O/'helpers_proxy.jaf','-o',decl,src)
 raw=bytearray(unpack(decl.read_bytes()));n=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+n,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};patches={};edits=[]
 for name,fid in ids.items():
  path=O/f'jaf_{fid}.jam';cmd('ain','dump','--function',name,'-o',path,decl);patches[fid]=clean(native_lower(path.read_text('utf8')),name)
 def get(fid):
  path=O/f'original_{fid}.jam'
  if not path.exists() or not re.search(r'^FUNC '+str(fid)+r'$',path.read_text('utf8'),re.M):cmd('ain','dump','--function',symbol(m,fid),'-o',path,src)
  return clean(path.read_text('utf8'),symbol(m,fid))
 def hook(fid,after):
  before=get(fid);assert before!=after;patches[fid]=after;edits.append(dict(fid=fid,before=before,after=after))
 s=get(6971);hook(6971,begin(s,'\tPUSHLOCALPAGE\n\tPUSH 2\n'+lr('nMsgNum')+lr('szText')+'\tA_REF\n'+cf('KR_TermMessage')+'\tS_ASSIGN\n\tDELETE\n'))
 for fid in [28133,29665]:hook(fid,begin(get(fid),cf('KR_TermLoad')))
 s=get(29556);hook(29556,s.replace('\tRETURN\n',cf('KR_TermLoad')+'\tRETURN\n'))
 for fid,arg in [(6484,'テキスト'),(27778,'txt')]:
  s=get(fid);needle=lr(arg)+'\tA_REF\n';assert needle in s;hook(fid,s.replace(needle,needle+cf('KR_TermDisplay'),1))
 # Display getters, never broad EX reader hooks. Non-display identifiers stay byte-exact.
 for fid in [26155,26156,26668,26669,26756,26757,26786,26787,26810,26811,26954,26955]:
  s=get(fid);s=s.replace('\tRETURN\n',cf('KR_TermDisplay')+'\tRETURN\n');hook(fid,s)
 # Object copies must not write selected display names back into gameplay state.
 for oldid,n,c in RAW_GETTERS:
  fid=ids[n];s=get(oldid);s=re.sub(r'^FUNC \d+',f'FUNC {fid}',s,flags=re.M);s=re.sub(r'ENDFUNC [^\n]+',f'ENDFUNC {n}',s)
  members={x['name']:i for i,x in enumerate(next(x for x in m['structures'] if x['name']==c)['members'])}
  s=re.sub(r'\t\.STRUCTREF '+c+r' (.+)\n',lambda mt:lr('self')+push(members[mt[1]])+'\tX_REF 1\n',s)
  assert '.STRUCTREF' not in s and 'PUSHSTRUCTPAGE' not in s
  s=re.sub(r'0x([0-9a-f]+)',lambda mt:f'raw_{fid}_{mt[1]}',s)
  patches[fid]=s
 for caller,getter,rawname,expected in [(26216,26155,'KR_TermRawMonster',1),(26894,26810,'KR_TermRawWeapon',1),(26687,26668,'KR_TermRawItem',5)]:
  s=get(caller);needle=push(getter)+'\tCALLMETHOD 0\n';assert s.count(needle)==expected,(caller,s.count(needle));hook(caller,s.replace(needle,cf(rawname)))
 s=get(29815);hook(29815,begin(s,'\tPUSHSTRUCTPAGE\n'+push(29822)+lr('ActivityName')+'\tA_REF\n'+S('KR_TermConfigButton')+'\tCALLMETHOD 2\n'))
 s=get(29823);pfx='\tPUSHSTRUCTPAGE\n'+push(29824)+lr('number')+S('KR_TermConfigButton')+push(-1)+push(ids['KR_TermMenu'])+'\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 3\n';hook(29823,begin(s,pfx))
 jam=O/'patch.jam';jam.write_text('\n'.join(patches.values()),'utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,decl)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json')
 changed=[]
 for x,y in zip(m['functions'],nm['functions']):
  xx=copy.deepcopy(x);xx['address']=y['address'];assert xx==y,x['index']
  if x['address']!=y['address']:changed.append(x['index'])
 assert sorted(changed)==sorted(x['fid'] for x in edits)
 switch_changes=[]
 assert len(m['switches'])==len(nm['switches'])
 for si0,(x,y) in enumerate(zip(m['switches'],nm['switches'])):
  if x==y:continue
  assert x['case-type']==y['case-type'] and [c['value'] for c in x['cases']]==[c['value'] for c in y['cases']]
  def owner(meta,address):
   starts=sorted((f['address'],f['index']) for f in meta['functions'] if f['address']<=address)
   return starts[-1][1]
  for xx,yy in zip(x['cases'],y['cases']):assert owner(m,xx['address'])==owner(nm,yy['address']) in changed
  if x['default-address']!=-1:assert owner(m,x['default-address'])==owner(nm,y['default-address']) in changed
  else:assert y['default-address']==-1
  switch_changes.append(si0)
 for k in m:
  if k not in ['functions','switches']:assert m[k]==nm[k],k
 old=unpack(src.read_bytes());new=unpack(out.read_bytes());size=struct.unpack_from('<I',old,12)[0];assert old[16:16+size]==new[16:16+size]
 assert raw_messages(src.read_bytes())[3]==raw_messages(out.read_bytes())[3]
 assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
 for fid in patches:cmd('ain','dump','--function',symbol(nm,fid),'-o',O/f'built_{fid}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);na=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',na);assert na['all_active_opcodes_supported']
 art=assets();files=['NightRemaster.ain','NightRemasterPact.afa'];save('reversible_hook_edits.json',edits)
 ev=dict(status='TERM_SWITCH_STAGED',source_pointer=ptr,source_files={n:a.sha(rt/n) for n in files},files={n:a.sha(O/n) for n in files},patched_existing=changed,added_functions=ids,PACT=art,relocated_switches=switch_changes,MSG1_exact=True,old_CODE_prefix_exact=True,old_STR0_exact=True,globals_structures_exact=True,save_schema_changes=0,native_verified=False,translator_model='Codex internal')
 save('build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
