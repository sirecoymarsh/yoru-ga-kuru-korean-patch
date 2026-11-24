"""Connect copied read-only planners to native one-step movement, not teleportation."""
from pathlib import Path
import copy,json,re,struct,shutil
from cheat_support_20260915 import R,sha,savej,read_meta,cmd
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,si,ss,setlist,rename,txt_info,encode,decode,allparts
from build_mod_tab_20260915 import add,remove,coords,name,scalar
from build_route_perf_20260915 import symbol
from build_instant_loot_20260915 import clean,begin
from build_dungeon_sweep_20260916 import S,push,cf,lr,cm,assign,field
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit
O=R/'staging/auto_walk_20260922';HERE=Path(__file__).resolve().parent
BASE=R/'staging/auto_items_20260922';EXPECTED='9fc891f423e216e906c01cf7b5e2deed9b0ad13a06bf73f369d311349a280ee4'
MARK=2026092203

def planners():
 a=(HERE/'route_linear_helpers_20260916.jaf').read_text(encoding='utf8');a=a[a.index('void KR_DrawRouteLinear'):]
 a=a.replace('KR_DrawRouteLinear(ref C_MapInfo map, ref C_SceneDungeonMiniMapView view, int x, int y, int mode)','KR_WalkPlanLinear(ref C_MapInfo map, ref C_SceneDungeonMiniMapView view, int x, int y, int mode, ref array<CASPos> route)')
 a=a.replace('    array<CASPos> route;\n','');start=a.index('    if (!KR_GetRoute())');end=a.index('    if (x < 0',start);a=a[:start]+a[end:]
 a=a[:a.index('    KR_Poke(88, 1);')]+'}\n'
 b=(HERE/'route_puzzle_helpers_20260916.jaf').read_text(encoding='utf8');b=b[b.index('void KR_DrawPuzzleRoute'):]
 b=b.replace('KR_DrawPuzzleRoute(ref C_MapInfo map, ref C_SceneDungeonMiniMapView view, int x, int y, int mode)','KR_WalkPlanPuzzle(ref C_MapInfo map, ref C_SceneDungeonMiniMapView view, int x, int y, int mode, ref array<CASPos> route)')
 b=b.replace('    array<CASPos> route;\n','').replace('!KR_GetRoute() || ','');b=b[:b.index('    KR_Poke(88,')]+ '}\n'
 assert 'DrawAutoMoveLines' not in a+b and 'KR_Poke' not in a+b
 return a+'\n'+b

def assets(rt):
 src=rt/'NightRemasterPact.afa';ar=read_afa3(src);e=ar.entries[161]
 with src.open('rb') as f:f.seek(e.absolute_offset);raw=f.read(e.size)
 (O/'original_161.pactex').write_bytes(raw);d=ex.decode_ex(O/'original_161.pactex');assert d.serialize_payload()==d.raw_payload
 root=copy.deepcopy(part(d,'KR_SweepRoot'));rename(root,'KR_WalkRoot');setlist(root,'座標',[1142,436,41]);si(root,'表示',0)
 kids=child(root,'子パーツ');button=next(t for t in kids.children if name(t)=='KR_SweepButton');label=next(t for t in kids.children if name(t)=='KR_SweepButtonLabel')
 rename(button,'KR_WalkButton');rename(label,'KR_WalkStartLabel')
 for item in val(root,'子パーツリスト').items:
  n=item.value.payload.value.decode('cp932');item.value.payload.replacement={'KR_SweepButton':'KR_WalkButton','KR_SweepButtonLabel':'KR_WalkStartLabel'}[n].encode('cp932')
 from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
 from audit_dynamic_ui_20260915 import ENC
 _,faces=parse_fnl_font(rt/'NightRemasterFont.fnl',3)
 def label_text(t,s):
  tx=txt_info(t);ss(tx,'テキスト',s,True);dec=child(tx,'テキスト装飾');size=scalar(val(dec,'フォントサイズ'))
  face,den,_=select_fnl_face(faces,size);width=WidthMeasurer(face,den,{c:sjis_bytes_to_fnl_index(v) for c,v in ENC.items()},scalar(val(dec,'字間隔')),0,0).measure(s,True)['lines'][0]['width_px']
  assert width<=104;xyz=coords(t);setlist(t,'座標',[(116-width)/2,xyz[1],xyz[2]])
 label_text(label,'자동 이동');stop=copy.deepcopy(label);rename(stop,'KR_WalkStopLabel');label_text(stop,'이동 중지');si(stop,'表示',0);add(root,stop)
 add(part(d,'矩形_000'),root)
 out=O/'pact_161_auto_walk.pactex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()))
 rev=ex.decode_ex(out);remove(part(rev,'矩形_000'),'KR_WalkRoot');assert rev.serialize_payload()==d.raw_payload
 archive=rebuild(src,O/'NightRemasterPact.afa',{161:out})
 return dict(changed_entries=[161],archive=archive,reverse_original_payload_exact=True,button_rect=[1142,436,116,55],native_sweep_button_states_exact=True,unscaled_yellow_labels=True)

def main():
 O.mkdir(parents=True,exist_ok=True);ptr=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)==EXPECTED and sha(Path(ptr['manifest']))==ptr['manifest_sha256'];savej(O/'source_pointer.json',ptr)
 m=read_meta(BASE/'candidate_meta.json');names={};seen={}
 for f in m['functions']:
  n=symbol(m,f['index']);c=seen.get(n,0);seen[n]=c+1;names[f['index']]=n+(f'#{c}' if c else '')
 def get(fid):
  p=O/f'original_{fid}.jam';cmd('ain','dump','--function',names[fid],'-o',p,src);return clean(p.read_text(encoding='utf8'),names[fid])
 jaf=planners()+'\n'+(HERE/'auto_walk_helpers_20260922.jaf').read_text(encoding='utf8')
 for k,s in dict(WALK_UNAVAILABLE='지금은 자동 이동을 시작할 수 없습니다.',WALK_NO_ROUTE='자동 이동\n안내할 경로를 찾지 못했습니다.',WALK_STOP='자동 이동을 중지했습니다.',WALK_START='자동 이동을 시작했습니다.\n수동 이동이나 버튼으로 중지할 수 있습니다.').items():jaf=jaf.replace('"'+k+'"',json.dumps(encode(s).decode('cp932'),ensure_ascii=False))
 (O/'helpers.jaf').write_text(jaf,encoding='utf8');decl=O/'declared.ain';cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
 old=unpack(src.read_bytes());raw=bytearray(unpack(decl.read_bytes()));size=struct.unpack_from('<I',old,12)[0];nsize=struct.unpack_from('<I',raw,12)[0]
 assert old[16:16+size]==raw[16:16+size];struct.pack_into('<I',raw,24+nsize,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};bridges={};patches={}
 def bind(func,local,expr):
  f=dm['functions'][ids[func]];vs=f['arguments']+f['variables'];return assign(next(i for i,v in enumerate(vs) if v['name']==local),expr)
 scene=lr('scene');mp=field(scene,6);dv=field(scene,2);vw=field(dv,3);queue=field(scene,7)
 template=get(31890)
 for n,key in [('KR_WalkVisible','KR_WalkRoot'),('KR_WalkShowStart','KR_WalkStartLabel'),('KR_WalkShowStop','KR_WalkStopLabel')]:
  bridges[n]=template.split('FUNC 31890\n',1)[1].split('ENDFUNC ',1)[0].replace('KR_SweepRoot',key)
 bridges['KR_WalkX']=cm('\t.GLOBALREF Flags\n',26559)+'\tRETURN\n';bridges['KR_WalkY']=cm('\t.GLOBALREF Flags\n',26562)+'\tRETURN\n'
 b=''
 for obj in [scene,mp,dv,vw]:b+=obj+push(-1)+'\tEQUALE\n\tIFNZ invalid_context\n'
 b+=cm(scene,28622)+cm(mp,27042)+'\tNOTE\n\tIFNZ invalid_context\n'+cf('L_Party::IsAnnihilated')+'\tIFNZ invalid_context\n'
 for n in ['KR_WalkX','KR_WalkY']:b+=cf(n)+push(0)+'\tLT\n\tIFNZ invalid_context\n'+cf(n)+push(30)+'\tGTE\n\tIFNZ invalid_context\n'
 bridges['KR_WalkValid']=b+push(1)+'\tRETURN\ninvalid_context:\n'+push(0)+'\tRETURN\n'
 bridges['KR_WalkCount']=queue+'\tCALLHLL Array Numof 2\n\tRETURN\n'
 bridges['KR_WalkRouteCount']=lr('route')+'\tCALLHLL Array Numof 2\n\tRETURN\n'
 bridges['KR_WalkObject']=cm(lr('cell'),27005)+'\tRETURN\n'
 bridges['KR_WalkPoint']=lr('route')+lr('index')+'\tX_REF 1\n\tX_DUP 1\n'+push(-1)+'\tEQUALE\n\tIFNZ null_point\n'+lr('field')+'\tX_REF 1\n\tRETURN\nnull_point:\n\tPOP\n'+push(-1)+'\tRETURN\n'
 bridges['KR_WalkHead']=queue+push(0)+lr('field')+cf('KR_WalkPoint')+'\tRETURN\n'
 n='KR_WalkPlan';b=bind(n,'map',mp)+'\t.LOCALREF map\n\tSP_INC\n'+bind(n,'view',vw)+'\t.LOCALREF view\n\tSP_INC\n'+bind(n,'mode',cm(lr('map'),27042))
 for mode in [401,403,405]:b+=lr('mode')+push(mode)+'\tEQUALE\n\tIFNZ plan_puzzle\n'
 args=lr('map')+lr('view')+cf('KR_WalkX')+cf('KR_WalkY')+lr('mode')+lr('route')
 b+=args+cf('KR_WalkPlanLinear')+'\tJUMP plan_done\nplan_puzzle:\n'+args+cf('KR_WalkPlanPuzzle')+'plan_done:\n\t.LOCALDELETE view\n\t.LOCALDELETE map\n\tRETURN\n';bridges[n]=b
 n='KR_WalkCommit';b=bind(n,'n',lr('route')+'\tCALLHLL Array Numof 2\n')
 b+=queue+lr('n')+'\tCALLHLL Array Realloc 2\n'+queue+push(0)+lr('route')+push(0)+lr('n')+'\tCALLHLL Array Copy#3 2\n'+lr('n')+'\tNOTE\n\tIFNZ copy_failed\n'
 b+=cm(dv,28769,push(0),1)+push(88)+push(1)+cf('KR_Poke')+cm(dv,28768,queue,1)+push(88)+push(0)+cf('KR_Poke')+push(1)+'\tRETURN\ncopy_failed:\n'+cm(scene,28659)+push(0)+'\tRETURN\n';bridges[n]=b
 for n,fid in ids.items():
  p=O/f'jaf_{fid}.jam';cmd('ain','dump','--function',n,'-o',p,decl);s=clean(native_lower(p.read_text(encoding='utf8')),n)
  if n in bridges:
   body=bridges[n]
   for label in re.findall(r'^([^\s:]+):$',body,re.M):body=re.sub(r'(?<![\w])'+re.escape(label)+r'(?![\w])',f'walk_{fid}_{label}',body)
   s=f'FUNC {fid}\n'+body+f'ENDFUNC {n}\n'
  patches[fid]=s
 # Every inserted hook is reversible; keep original method bodies in order.
 s=get(28637);wait='\tPUSHLOCALPAGE\n\tPUSH 1\n\tPUSHSTRUCTPAGE\n\tPUSH 28642\n';assert s.count(wait)==1
 s=s.replace(wait,'\tPUSHSTRUCTPAGE\n'+push(1)+cf('KR_WalkVisible')+wait)
 needle='\tPUSHSTRUCTPAGE\n\tPUSH 0\n\tCALLFUNC KR_SweepVisible\n';assert s.count(needle)==1
 top=re.search(r'(0x[0-9a-f]+):\n\tPUSH 1\n\tIFZ',s)[1]
 body='\tPUSHSTRUCTPAGE\n'+push(0)+cf('KR_WalkVisible')+lr('clickType')+push(MARK)+'\tNOTE\n\tIFNZ walk_other_click\n\tPUSHSTRUCTPAGE\n'+cf('KR_WalkToggle')+f'\tJUMP {top}\nwalk_other_click:\n\tPUSHSTRUCTPAGE\n'+cf('KR_WalkStop')
 patches[28637]=s.replace(needle,body+needle)
 s=get(28642);needle='\t.STRUCTREF C_SceneDungeon m_AutoMoveList\n\tCALLHLL Array Empty 2\n';assert s.count(needle)==1
 s=s.replace(needle,'\tPUSHSTRUCTPAGE\n'+cf('KR_WalkGuard')+needle)
 for call in ['■バックログ起動監視','■バックシーン起動監視']:
  pat=r'(\tCALLFUNC '+call+r'\n\tIFNZ (0x[0-9a-f]+)\n\tJUMP 0x[0-9a-f]+\n\2:\n)(\tRETURN\n)'
  s,n=re.subn(pat,lambda z:z[1]+'\tPUSHSTRUCTPAGE\n'+cf('KR_WalkStop')+z[3],s);assert n==1,(call,n)
 patches[28642]=s
 patches[28659]=begin(get(28659),'\tPUSHSTRUCTPAGE\n'+cf('KR_WalkReset'))
 s=get(28664);needle='\tPUSHLOCALPAGE\n\tPUSH 14\n\t.LOCALREF cell\n\tPUSH 27005\n';assert s.count(needle)==2
 s=s.replace(needle,'\tPUSHSTRUCTPAGE\n'+lr('cell')+cf('KR_WalkCellGate')+needle,1);patches[28664]=s
 s=get(28641);needle='\t.STRUCTREF C_SceneDungeon m_DungeonView\n';at=s.index(needle);patches[28641]=s[:at]+'\tPUSHSTRUCTPAGE\n'+cf('KR_WalkStop')+s[at:]
 patches[28665]=begin(get(28665),'\tPUSHSTRUCTPAGE\n'+cf('KR_WalkStop'))
 patches[28739]=begin(get(28739),cf('KR_WalkPause'))
 patches[31856]=begin(get(31856),push(71)+push(0)+cf('KR_Poke'))
 s=get(28731);at=s.index('\tS_PUSH "KR_SweepButton"');start=s.rfind('\tPUSHSTRUCTPAGE\n\tPUSH 0\n',0,at);end=s.index('\t.LOCALDELETE ',at);end=s.index('\n',end)+1
 block=s[start:end].replace('"KR_SweepButton"','"KR_WalkButton"').replace(push(31891)+ '\tDG_NEW_FROM_METHOD',push(ids['KR_WalkClick'])+'\tDG_NEW_FROM_METHOD')
 assert cf('KR_WalkClick') not in block and push(ids['KR_WalkClick']) in block
 pos=s.rfind('\tRETURN');patches[28731]=s[:pos]+block+s[pos:]
 jam=O/'auto_walk_patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,decl)
 # Match original DrawAutoMoveLines' ref array<CASPos> metadata (owned struct elements).
 data=bytearray(unpack(out.read_bytes()));abi=[]
 for n,fid in ids.items():
  args=dm['functions'][fid]['arguments']+dm['functions'][fid]['variables']
  routes=[v for v in args if v['name']=='route' and v['type'][0] in [79,80]]
  if not routes:continue
  assert len(routes)==1;typ=routes[0]['type'][0]
  start=data.index(n.encode()+b'\0');offset=data.index(b'route\0\0',start)+7;assert struct.unpack_from('<7i',data,offset)==(typ,13,1,13,514,0,0)
  struct.pack_into('<7i',data,offset,typ,514,1,13,514,0,0);abi.append(dict(function=n,offset=offset,type=typ))
 out.write_bytes(pack(bytes(data),src.read_bytes()[:8]));savej(O/'array_abi_normalization.json',abi)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(z);aa=x.pop('address');zz=y.pop('address');assert x==y,a['index']
  if aa!=zz:changed.append(a['index'])
 nested=list(range(31639,31652))
 assert changed==sorted([fid for fid in patches if fid<len(m['functions'])]+nested),(changed,nested)
 switches=[]
 for i,(a,z) in enumerate(zip(m['switches'],nm['switches'])):
  if a==z:continue
  assert i in [450,451] and a['case-type']==z['case-type'] and a['default-address']==z['default-address']==-1
  assert [c['value'] for c in a['cases']]==[c['value'] for c in z['cases']]
  for table,meta in [(a,m),(z,nm)]:
   lo=meta['functions'][28664]['address'];hi=min(f['address'] for f in meta['functions'] if f['address']>lo);assert all(lo<=c['address']<hi for c in table['cases'])
  switches.append(i)
 assert switches==[450,451]
 for k in m:
  if k not in ['functions','switches']:assert m[k]==nm[k],k
 new=unpack(out.read_bytes());assert old[16:16+size]==new[16:16+size] and strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
 assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
 for fid in patches:cmd('ain','dump','--function',names.get(fid,nm['functions'][fid]['name']),'-o',O/f'built_{fid}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);report=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');savej(O/'native_opcode_audit.json',report);assert report['all_active_opcodes_supported']
 art=assets(rt);files=['NightRemaster.ain','NightRemasterPact.afa']
 ev=dict(status='AUTO_WALK_STAGED_UNVERIFIED',source_pointer=ptr,source_files={n:sha(rt/n) for n in files},files={n:sha(O/n) for n in files},patched_existing=changed,added_functions=ids,PACT=art,old_CODE_STR0_MSG1_exact=True,existing_metadata_exact_except_function_and_switch_addresses=True,relocated_native_switches=switches,translator_model='Codex internal',native_verified=False,transient=dict(slot=71,marker=MARK,saved_configuration=False,new_serialized_fields=False),runtime=dict(native_movement=True,no_teleport=True,planning='explicit button; one replan on actual blocked next step',no_per_frame_BFS=True,puzzle_segment_scope=[401,403,405],stop_on_native_interactions=True,instant_enemy_trap_short_circuits_preserved=True,default_running=False))
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
