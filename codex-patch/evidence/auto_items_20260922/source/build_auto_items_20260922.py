"""Stage native auto-item reservations and a native configuration subpage."""
from pathlib import Path
import copy,json,re,struct,shutil
from cheat_support_20260915 import R,sha,savej,read_meta,cmd
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,si,ss,setlist,rename,txt_info,encode,decode
from build_mod_tab_20260915 import add,remove,coords,scalar
from build_route_perf_20260915 import symbol
from build_instant_loot_20260915 import clean,begin
from build_dungeon_sweep_20260916 import S,push,cf,lr,cm,assign,field
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit

O=R/'staging/auto_items_20260922';HERE=Path(__file__).resolve().parent
BASE=R/'staging/smart_auto_fix_20260922'
EXPECTED='b86f6f5ff17cf2d08c0eb7a1015d05136819d5daf8803b6bca00b2c5d6cb08ea'
NAMES=['반달 환약','달의 물방울','달빛 수정','보름달 환약','카샤의 영약']
EFFECTS=['영력 50% 회복','독 해제','마비 해제','영력 모두 회복','부활 · 영력 50% 회복']

def assets(rt):
 src=rt/'NightRemasterPact.afa';ar=read_afa3(src);e=ar.entries[185]
 with src.open('rb') as f:f.seek(e.absolute_offset);raw=f.read(e.size)
 (O/'original_185.pactex').write_bytes(raw);mods=ex.decode_ex(O/'original_185.pactex')
 assert mods.serialize_payload()==mods.raw_payload
 info=child(part(mods,'KR_CheatQuick'),'種類別情報');assert decode(val(info,'テキスト').value)=='\u3000자동 전투 결과만 보기'
 ss(info,'テキスト','\u3000전투 이펙트 보지 않기',True)
 root=mods.blocks[2].payload.children[0]
 page=copy.deepcopy(mods);pr=page.blocks[2].payload.children[0]
 for n in ['KR_ModHeader','KR_ModRewards','KR_ModBattle','KR_ModDungeon','KR_ModQuickHint','KR_ModQuickCancel','KR_AutoEquipToggle','KR_SmartAutoToggle']:remove(pr,n)
 si(child(part(page,'KR_ModTab'),'種類別情報'),'有効',1)
 b=copy.deepcopy(part(mods,'KR_ModTab'));rename(b,'KR_ItemConfigButton');setlist(b,'座標',[363,622,260])
 bi=child(b,'種類別情報');si(bi,'有効',1);ss(bi,'テキスト','');si(bi,'フォントタイプ',259);si(bi,'フォントサイズ',20)
 ss(bi,'ＣＧ名','シス／コンフィグ／タブ');setlist(bi,'サイズ',[192,42]);setlist(b,'拡大縮小',[1,0.7142857])
 # Mod-owned buttons use yellow lettering, native blue chrome.
 setlist(bi,'フォント色',[255,230,80]);add(root,b)
 from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
 from audit_dynamic_ui_20260915 import ENC
 _,faces=parse_fnl_font(rt/'NightRemasterFont.fnl',3);face,den,_=select_fnl_face(faces,20)
 width=WidthMeasurer(face,den,{c:sjis_bytes_to_fnl_index(v) for c,v in ENC.items()},0,0,0).measure('자동 회복 설정',True)['lines'][0]['width_px'];assert width<=180
 label=copy.deepcopy(part(mods,'KR_ModSpeedTitle'));rename(label,'KR_ItemConfigLabel');setlist(label,'座標',[363+(192-width)/2,627,261]);si(label,'オンカーソル透過',1)
 ti=txt_info(label);ss(ti,'テキスト','자동 회복 설정',True);dec=child(ti,'テキスト装飾');si(dec,'フォントサイズ',20);si(dec,'字間隔',0);setlist(dec,'フォント色',[255,230,80]);add(root,label)
 def text(n,t,x,y,size=20):
  p=copy.deepcopy(part(mods,'KR_ModSpeedTitle'));rename(p,n);setlist(p,'座標',[x,y,80]);ti=txt_info(p);ss(ti,'テキスト',t,True);si(child(ti,'テキスト装飾'),'フォントサイズ',size);si(child(ti,'テキスト装飾'),'字間隔',0);add(pr,p);return p
 def toggle(n,t,x,y):
  p=copy.deepcopy(part(mods,'KR_CheatTrap'));rename(p,n);setlist(p,'座標',[x,y,90]);ss(child(p,'種類別情報'),'テキスト','\u3000'+t,True);add(pr,p)
 def slider(n,x,y):
  p=copy.deepcopy(part(mods,'KR_CheatSpeed'));rename(p,n);setlist(p,'座標',[x,y,50]);setlist(p,'拡大縮小',[1,0.7142857]);si(child(p,'種類別情報'),'全体スクロール量',81 if n=='KR_ItemsThreshold' else 100);add(pr,p)
 text('KR_ItemsTitle','자동 회복 설정',363,40,26)
 text('KR_ItemsScope','자동 전투 중에만 사용 · 설정은 모든 저장 데이터에 공통 적용',363,88,18)
 toggle('KR_ItemsEnabled','회복 아이템 자동 사용',363,128)
 text('KR_ItemsThresholdLabel','영력 회복 기준',363,182,23);text('KR_ItemsThresholdValue','30% 이하',1010,182)
 slider('KR_ItemsThreshold',783,213)
 text('KR_ItemsAllowHeader','사용 허용 / 아이템 효과',363,247,18);text('KR_ItemsReserveHeader','최소 보유 개수 (0~99개)',783,247,18)
 for i,(name,effect) in enumerate(zip(NAMES,EFFECTS),1):
  y=283+(i-1)*64
  toggle(f'KR_ItemsAllow{i}',name,363,y)
  text(f'KR_ItemsEffect{i}',effect,409,y+30,16)
  slider(f'KR_ItemsReserve{i}',783,y+27)
  text(f'KR_ItemsReserveValue{i}','3개',1060,y)
 text('KR_ItemsHint','보유량이 지정 개수보다 많을 때만 사용합니다. 모드 탭으로 돌아갈 수 있습니다.',363,617,16)
 replacements={185:O/'pact_185_auto_items.pactex'}
 for doc,path in [(mods,replacements[185]),(page,O/'pact_187_auto_items.pactex')]:
  path.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()));assert ex.decode_ex(path).serialize_payload()==doc.serialize_payload()
 # Exact old-page recovery after removing the new button and reversing its label.
 rev=ex.decode_ex(replacements[185]);remove(rev.blocks[2].payload.children[0],'KR_ItemConfigButton');remove(rev.blocks[2].payload.children[0],'KR_ItemConfigLabel');ss(child(part(rev,'KR_CheatQuick'),'種類別情報'),'テキスト','\u3000자동 전투 결과만 보기',True)
 assert rev.serialize_payload()==mods.raw_payload
 archive=rebuild(src,O/'NightRemasterPact.afa',replacements,[('Asra/AutoItems.pactex',O/'pact_187_auto_items.pactex')])
 d=ex.decode_ex(rt/'NightRemasterEX.ex');old=[b.serialize() for b in d.blocks];t=d.blocks[23].payload;before=copy.deepcopy(t.rows)
 assert len(t.rows)==10 and t.dimensions==(10,2)
 row=copy.deepcopy(t.rows[-1]);row[0].payload.replacement=b'KR_ItemConfigButton';row[1].payload.replacement=b'Asra\\AutoItems';t.rows.append(row);t.dimensions=(11,2)
 p=O/'NightRemasterEX.ex';p.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));new=ex.decode_ex(p)
 assert [i for i,(a,b) in enumerate(zip(old,new.blocks)) if a!=b.serialize()]==[23]
 assert [c.serialize() for r in before for c in r]==[c.serialize() for r in new.blocks[23].payload.rows[:10] for c in r]
 return dict(archive=archive,changed_entries=[185],added_entry=187,route_row=10,other_EX_blocks_and_original_rows_exact=True,old_page_reverse_exact=True,original_font_chrome=True)

def main():
 O.mkdir(parents=True,exist_ok=True);ptr=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)==EXPECTED and sha(Path(ptr['manifest']))==ptr['manifest_sha256'];savej(O/'source_pointer.json',ptr)
 m=read_meta(BASE/'candidate_meta.json');names={};seen={}
 for f in m['functions']:
  n=symbol(m,f['index']);c=seen.get(n,0);seen[n]=c+1;names[f['index']]=n+(f'#{c}' if c else '')
 def get(fid):
  p=O/f'original_{fid}.jam';cmd('ain','dump','--function',names[fid],'-o',p,src);return clean(p.read_text(encoding='utf8'),names[fid])
 jaf=(HERE/'auto_items_helpers_20260922.jaf').read_text(encoding='utf8')
 for i in range(1,6):
  jaf+=f'\nbool KR_ItemsGetAllow{i}() {{ return KR_ItemsAllowed({i}); }}\nvoid KR_ItemsSetAllow{i}(bool v) {{ KR_ItemsSetAllowed({i},v); }}\nfloat KR_ItemsGetReserve{i}() {{ return KR_ItemsGetReserve({i}); }}\nvoid KR_ItemsSetReserve{i}(float v) {{ KR_ItemsSetReserve({i},v); }}\n'
 (O/'helpers.jaf').write_text(jaf,encoding='utf8');decl=O/'declared.ain';cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
 old=unpack(src.read_bytes());raw=bytearray(unpack(decl.read_bytes()));size=struct.unpack_from('<I',old,12)[0];nsize=struct.unpack_from('<I',raw,12)[0]
 assert old[16:16+size]==raw[16:16+size];struct.pack_into('<I',raw,24+nsize,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};bridges={}
 def bind(func,local,expr):
  f=dm['functions'][ids[func]];vs=f['arguments']+f['variables'];return assign(next(i for i,v in enumerate(vs) if v['name']==local),expr)
 name='KR_ItemsStock';b=bind(name,'item',lr('id')+cf('L_ConsumeItem::At'))
 bridges[name]=b+lr('item')+push(-1)+'\tEQUALE\n\tIFNZ no_stock\n'+cm(lr('item'),26677)+'\t.LOCALDELETE item\n\tRETURN\nno_stock:\n\t.LOCALDELETE item\n'+push(0)+'\tRETURN\n'
 name='KR_ItemsTake';b=bind(name,'item',lr('id')+cf('L_ConsumeItem::At'))+lr('item')+push(-1)+'\tEQUALE\n\tIFNZ no_take\n'
 b+=bind(name,'count',cm(lr('item'),26677))+lr('count')+lr('reserve')+'\tLTE\n\tIFNZ no_take\n'+cm(lr('item'),26679,lr('count')+push(1)+'\tSUB\n',1)
 bridges[name]=b+'\t.LOCALDELETE item\n'+push(1)+'\tRETURN\nno_take:\n\t.LOCALDELETE item\n'+push(0)+'\tRETURN\n'
 name='KR_ItemsReturn';b=bind(name,'item',lr('id')+cf('L_ConsumeItem::At'))+lr('item')+push(-1)+'\tEQUALE\n\tIFNZ return_end\n'+cm(lr('item'),26679,cm(lr('item'),26677)+push(1)+'\tADD\n',1)
 bridges[name]=b+'return_end:\n\t.LOCALDELETE item\n\tRETURN\n'
 bridges['KR_ItemsFriendCount']=lr('friends')+'\tCALLHLL Array Numof 65538\n\tRETURN\n'
 b=lr('friends')+lr('i')+'\tX_REF 1\n'+push(-1)+'\tEQUALE\n\tIFNZ no_friend\n'+lr('friends')+lr('i')+'\tX_REF 1\n'+lr('field')+'\tX_REF 1\n\tRETURN\nno_friend:\n'+push(-1)+'\tRETURN\n';bridges['KR_ItemsFriend']=b
 name='KR_ItemsActionType';bridges[name]=bind(name,'weapon',lr('id')+cf('L_Weapon::At'))+lr('weapon')+push(11)+cf('KR_AutoW')+'\t.LOCALDELETE weapon\n\tRETURN\n'
 name='KR_ItemsNeed';bridges[name]=bind(name,'pa',lr('target')+cf('L_Party::AbilityAt'))+lr('pa')+lr('item')+cf('KR_ItemsNeedAbility')+'\t.LOCALDELETE pa\n\tRETURN\n'
 patches={}
 for name,fid in ids.items():
  p=O/f'jaf_{fid}.jam';cmd('ain','dump','--function',name,'-o',p,decl);s=clean(native_lower(p.read_text(encoding='utf8')),name)
  if name in bridges:s=f'FUNC {fid}\n'+bridges[name]+f'ENDFUNC {name}\n'
  patches[fid]=s
 # Existing readiness/confusion/manual branching and original attack fallback remain exact.
 s=get(29221);oldcall='\tPUSHSTRUCTPAGE\n'+push(29242)+'\tPUSHLOCALPAGE\n'+push(6)+lr('pa')+lr('pf')+lr('enemies')+'\tCALLMETHOD 5\n\tPOP\n'
 assert s.count(oldcall)==2
 for n in range(2):
  body='\tPUSHSTRUCTPAGE\n'+lr('pa')+lr('pf')+lr('friends')+cf('KR_ItemsTry')+f'\tIFZ item_original_{n}\n\t.LOCALASSIGN bSet 1\n\tJUMP item_done_{n}\nitem_original_{n}:\n'+oldcall+f'item_done_{n}:\n'
  # Avoid replacing the copy of oldcall just inserted.
  pos=s.find(oldcall,0 if n==0 else s.index('item_done_0:\n')+len('item_done_0:\n'));s=s[:pos]+body+s[pos+len(oldcall):]
 patches[29221]=s
 s=get(29222);needle='\tX_REF 1\n'+push(29475)+'\tCALLMETHOD 0\n';assert s.count(needle)==1
 patches[29222]=s.replace(needle,'\tX_REF 1\n\tX_DUP 1\n'+cf('KR_ItemsCancelDown')+push(29475)+'\tCALLMETHOD 0\n')
 for fid,mode in [(29817,'Get'),(29818,'Set')]:
  b='';check=29827 if mode=='Get' else 29828;slide=29825 if mode=='Get' else 29826
  bindings=[('KR_ItemsEnabled',check,'KR_ItemsEnabled' if mode=='Get' else 'KR_ItemsSetEnabled'),('KR_ItemsThreshold',slide,'KR_Items'+mode+'Threshold')]
  for i in range(1,6):bindings += [(f'KR_ItemsAllow{i}',check,f'KR_Items{mode}Allow{i}'),(f'KR_ItemsReserve{i}',slide,f'KR_Items{mode}Reserve{i}')]
  for partname,method,callback in bindings:b+='\tPUSHSTRUCTPAGE\n'+push(method)+S(partname)+push(-1)+push(ids[callback])+'\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n'
  for i in range(6):
   key='KR_ItemsThresholdValue' if i==0 else f'KR_ItemsReserveValue{i}';act='\t.STRUCTREF C_ConfigView m_ActName\n\tA_REF\n'
   expr=cf('KR_ItemsMain')+push(100)+'\tMOD\n' if i==0 else push(i)+cf('KR_ItemsReserve')
   fmt='%d' if i==0 else '%d개'
   suffix=S('% 이하')+'\tS_ADD\n' if i==0 else ''
   b+=act+S(key)+cf('AFL_Activity_IsExistPartsByName')+f'\tIFZ item_label_{fid}_{i}\n'+act+S(key)+cf('AFL_Activity_GetPartsNumber')+S(fmt)+expr+'\tS_MOD 2\n'+suffix+push(1)+cf('Ｐ＿テキスト設定')+f'item_label_{fid}_{i}:\n'
  patches[fid]=begin(get(fid),b)
 jam=O/'auto_items_patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,decl)
 data=bytearray(unpack(out.read_bytes()));abi=[]
 typ=m['functions'][29221]['arguments'][0]['type'];structid=typ[1]
 for name in ['KR_ItemsFriendCount','KR_ItemsFriend','KR_ItemsPending','KR_ItemsTry']:
  start=data.index(name.encode()+b'\0');offset=data.index(b'friends\0\0',start)+9
  assert struct.unpack_from('<7i',data,offset)==(80,13,1,13,structid,0,0)
  struct.pack_into('<7i',data,offset,80,structid,1,21,structid,0,0);abi.append(dict(function=name,offset=offset))
 out.write_bytes(pack(bytes(data),src.read_bytes()[:8]));savej(O/'array_abi_normalization.json',abi)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(z);aa=x.pop('address');zz=y.pop('address');assert x==y,a['index']
  if aa!=zz:changed.append(a['index'])
 assert changed==[29221,29222,29817,29818],changed
 switch_changes=[]
 assert len(m['switches'])==len(nm['switches'])
 for i,(a,z) in enumerate(zip(m['switches'],nm['switches'])):
  if a==z:continue
  assert i in [511,512] and a['case-type']==z['case-type'] and a['default-address']==z['default-address']==-1
  assert [c['value'] for c in a['cases']]==[c['value'] for c in z['cases']]
  fid=29221
  for table,meta in [(a,m),(z,nm)]:
   start=meta['functions'][fid]['address'];end=min(f['address'] for f in meta['functions'] if f['address']>start)
   assert all(start<=c['address']<end for c in table['cases'])
  switch_changes.append(i)
 assert switch_changes==[511,512]
 for k in m:
  if k not in ['functions','switches']:assert m[k]==nm[k],k
 new=unpack(out.read_bytes());assert old[16:16+size]==new[16:16+size]
 assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
 assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
 for fid in patches:cmd('ain','dump','--function',names.get(fid,nm['functions'][fid]['name']),'-o',O/f'built_{fid}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);report=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');savej(O/'native_opcode_audit.json',report);assert report['all_active_opcodes_supported']
 art=assets(rt);files=['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']
 ev=dict(status='AUTO_ITEMS_STAGED_UNVERIFIED',source_pointer=ptr,source_files={n:sha(rt/n) for n in files},files={n:sha(O/n) for n in files},patched_existing=changed,added_functions=ids,PACT=art,old_CODE_STR0_MSG1_exact=True,existing_metadata_exact_except_function_and_switch_addresses=True,relocated_native_switches=switch_changes,translator_model='Codex internal',native_verified=False,options=dict(slots=list(range(72,79)),marker=2026092202,default_enabled=False,default_threshold=30,default_reserve=3),runtime=dict(allowed_battle_types=[-1,0],native_items=True,queued_stock_deduct_once=True,auto_owned_down_refund=True,no_new_serialized_fields=True))
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
