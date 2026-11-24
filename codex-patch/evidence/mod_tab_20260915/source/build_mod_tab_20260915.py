"""Separate native mod page; restore Korean original config surfaces in latest build."""
from pathlib import Path
import copy,json,struct,shutil,re
from build_remaster_multiplier_20260915 import (R,cmd,ex,read_meta,read_afa3,rebuild,part,child,maybe,val,allparts,si,ss,setlist,rename,txt_info,ROWS,OLD_PARTS,encode,decode,fn)
from repair_ui_runtime_weapon_text_20260913 import unpack,strings
from cheat_support_20260915 import sha,savej
from audit_sys43_native_opcodes_20260915 import audit
from build_route_perf_20260915 import symbol

O=Path('mod_tab_20260915');BASE=Path('route_department_20260915')
PAGE='Asra/Mods.pactex';BUTTON='KR_ModTab'
FILES=['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']

def name(t):return (t.name.replacement or t.name.value).decode('cp932')
def scalar(n):return struct.unpack('<f' if n.type_id==2 else '<i',n.raw)[0]
def coords(t):return [scalar(i.value.payload) for i in val(t,'座標').items]
def add(parent,t):
 order=val(parent,'子パーツリスト');oi=copy.deepcopy(order.items[0]) if order.items else copy.deepcopy(ORDER)
 oi.value.payload.replacement=(t.name.replacement or t.name.value)
 child(parent,'子パーツ').children.append(t);order.items.append(oi)
def remove(parent,n):
 kids=child(parent,'子パーツ');kids.children[:]=[t for t in kids.children if name(t)!=n]
 order=val(parent,'子パーツリスト');order.items[:]=[i for i in order.items if (i.value.payload.replacement or i.value.payload.value).decode('cp932')!=n]
def clean_group(t,n,x,y):
 g=copy.deepcopy(t);rename(g,n);setlist(g,'座標',[x,y,40]);child(g,'子パーツ').children=[];val(g,'子パーツリスト').items=[]
 return g

def build_pact(rt):
 global ORDER
 src=rt/'NightRemasterPact.afa';arc=read_afa3(src);docs={}
 for i in range(117,127):
  e=arc.entries[i]
  with src.open('rb') as f:f.seek(e.absolute_offset);(O/f'original_pact_{i}.pactex').write_bytes(f.read(e.size))
  docs[i]=ex.decode_ex(O/f'original_pact_{i}.pactex')
 # Frozen Korean pre-mod surfaces. Restore subtrees, never an old entire runtime.
 donor123=Path('cheat_menu_20260915/pact_123.pactex');donor125=Path('remaster_multiplier_20260915/pact_125.pactex')
 game=ex.decode_ex(donor123);remaster=ex.decode_ex(donor125)
 assert game.serialize_payload()==ex.decode_ex(Path('remaster_multiplier_20260915/pact_123.pactex')).raw_payload
 root=docs[123].blocks[2].payload.children[0]
 battle=part(docs[123],'矩形_戦闘');battle.__dict__.update(copy.deepcopy(part(game,'矩形_戦闘').__dict__))
 remove(root,'KR_CheatGroup');assert docs[123].serialize_payload()==game.raw_payload
 casual=part(docs[125],'レイアウト_カジュアル');casual.__dict__.update(copy.deepcopy(part(remaster,'レイアウト_カジュアル').__dict__))
 assert docs[125].serialize_payload()==remaster.raw_payload
 ORDER=copy.deepcopy(val(root,'子パーツリスト').items[0])
 # All original page payloads receive the same native tab and original CG states.
 tab_template=copy.deepcopy(part(docs[117],'３Ｄボタン'))
 for ix,doc in docs.items():
  buttons=part(doc,'タブ／ボタン類');t=copy.deepcopy(tab_template);rename(t,BUTTON);setlist(t,'座標',[110,510,13]);si(child(t,'種類別情報'),'有効',1);add(buttons,t)
  debug=part(doc,'デバッグボタン');p=coords(debug);setlist(debug,'座標',[p[0],583,p[2]])
  try:
   labels=part(doc,'レイアウト_タブテキスト');tx=copy.deepcopy(part(doc,'テキスト_リマスター'));rename(tx,'KR_ModTabLabel');setlist(tx,'座標',[91,480,9]);ss(txt_info(tx),'テキスト','모드',True);add(labels,tx)
  except StopIteration:
   # Hidden debug page has no separate label group. Use native button text.
   ss(child(t,'種類別情報'),'テキスト','모드',True)
 # New page inherits only unchanged native background, particles, tabs and footer.
 doc=copy.deepcopy(docs[125]);root=doc.blocks[2].payload.children[0];remove(root,'レイアウト_リマスター')
 si(child(part(doc,'３Ｄボタン'),'種類別情報'),'有効',1);si(child(next(t for t in allparts(root) if name(t)==BUTTON),'種類別情報'),'有効',0)
 source123=ex.decode_ex(O/'original_pact_123.pactex');source125=ex.decode_ex(O/'original_pact_125.pactex')
 template=part(game,'矩形_訓練');text_template=copy.deepcopy(child(child(part(game,'矩形_戦闘'),'子パーツ'),'テキストパーツ_000:0'))
 def tx(n,text,x,y,size=22):
  t=copy.deepcopy(text_template);rename(t,n);setlist(t,'座標',[x,y,30]);ss(txt_info(t),'テキスト',text,True)
  si(child(txt_info(t),'テキスト装飾'),'フォントサイズ',size);si(child(txt_info(t),'テキスト装飾'),'行間隔',0)
  return t
 header=clean_group(template,'KR_ModHeader',363,40)
 add(header,tx('KR_ModTitle','모드 설정',0,0,26))
 add(header,tx('KR_ModScope','보상 배율은 저장 데이터별 · 전투와 던전 편의 기능은 공통 적용',0,48,18));add(root,header)
 rewards=clean_group(template,'KR_ModRewards',363,122)
 add(rewards,tx('KR_ModRewardsTitle','보상 배율 (1~20배)',0,0,23))
 for j,(key,label,*_) in enumerate(ROWS):
  x=(j%2)*360;y=42+(j//2)*96
  for suffix,text,dx in [('Label',label,0),('Value','2배',268)]:
   t=copy.deepcopy(part(source125,'KR_Multiplier_'+suffix+'_'+key));setlist(t,'座標',[x+dx,y,32+j]);add(rewards,t)
  sl=copy.deepcopy(part(source125,'KR_Multiplier_'+key));setlist(sl,'座標',[x,y+30,2+j]);add(rewards,sl)
 add(rewards,tx('KR_ModRewardHint','리마스터의 2배 체크를 바꾸면 해당 항목을 1배 또는 2배로 설정합니다.',0,219,16));add(root,rewards)
 speed=clean_group(template,'KR_ModBattle',363,400)
 add(speed,tx('KR_ModSpeedTitle','전투 속도',0,0,23));add(speed,tx('KR_CheatSpeedValue','기본',260,0,22))
 sl=copy.deepcopy(part(source123,'KR_CheatSpeed'));setlist(sl,'座標',[0,42,2]);add(speed,sl)
 add(speed,tx('KR_ModSpeedHint','기본 / 2배 / 3배 / 4배 / 5배',0,94,17))
 add(speed,tx('KR_ModSpeedDefaultHint','기본: 게임 설정의 전투 가속을 따릅니다.',0,124,16));add(root,speed)
 convenience=clean_group(template,'KR_ModDungeon',783,396)
 for key,y in [('Trap',12),('Quick',60),('Route',108)]:
  t=copy.deepcopy(part(source123,'KR_Cheat'+key));setlist(t,'座標',[0,y,2+y]);add(convenience,t)
  label=next((t for t in allparts(source123.blocks[2].payload.children[0]) if name(t)=='KR_CheatLabel'+key),None)
  if label is not None:
   t=copy.deepcopy(label);setlist(t,'座標',[44,y+3,40+y]);add(convenience,t)
 add(convenience,tx('KR_ModQuickHint','결과만 보기: 일반 전투에 적용',0,161,15))
 add(convenience,tx('KR_ModQuickCancel','우클릭하면 전투 화면으로 돌아옵니다.',0,186,15));add(root,convenience)
 target=O/'pact_185_mods.pactex';target.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()));assert ex.decode_ex(target).serialize_payload()==doc.serialize_payload()
 replacements={}
 for ix,d in docs.items():
  out=O/f'pact_{ix}_tabs.pactex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));assert ex.decode_ex(out).serialize_payload()==d.serialize_payload();replacements[ix]=out
 archive=rebuild(src,O/'NightRemasterPact.afa',replacements,[(PAGE,target)])
 return dict(archive=archive,restored_pre_mod_donors={str(donor123):sha(donor123),str(donor125):sha(donor125)},original_options_restored_exact_before_tab_addition=True,mode_only_controls=8,all_raster_font_assets_unchanged=True)

def build_ex(rt):
 src=rt/'NightRemasterEX.ex';d=ex.decode_ex(src);original=[b.serialize() for b in d.blocks];b=d.blocks[23];assert b.name.value.decode('cp932')=='Ｅ＿コンフィグファイル名'
 t=b.payload;assert len(t.rows)==9;before=[r.copy() for r in t.rows];row=copy.deepcopy(t.rows[-1])
 row[0].payload.replacement=BUTTON.encode('cp932');row[1].payload.replacement=b'Asra\\Mods';t.rows.append(row);assert t.dimensions==(9,2);t.dimensions=(10,2)
 out=O/'NightRemasterEX.ex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));new=ex.decode_ex(out)
 assert len(new.blocks[23].payload.rows)==10
 assert [i for i,(a,z) in enumerate(zip(original,new.blocks)) if a!=z.serialize()]==[23]
 assert [c.serialize() for r in before for c in r]==[c.serialize() for r in new.blocks[23].payload.rows[:9] for c in r]
 return dict(changed_block_ids=[23],appended_row_index=9,button=BUTTON,page='Asra\\Mods',other_blocks_and_original_rows_exact=True)

def build_ain(rt):
 src=rt/'NightRemaster.ain';m=read_meta(BASE/'candidate_meta.json');names={};seen={}
 for f in m['functions']:
  n=symbol(m,f['index']);count=seen.get(n,0);seen[n]=count+1;names[f['index']]=n+(f'#{count}' if count else '')
 def get(i):
  out=O/f'original_{i}.jam'
  cmd('ain','dump','--function',names[i],'-o',out,src);s=out.read_text(encoding='utf8');assert s.strip()
  if 'ENDFUNC ' not in s:s+='\nENDFUNC '+names[i]+'\n'
  return s
 def begin(s,x):return re.sub(r'(^FUNC \d+\n)',lambda q:q[0]+x,s,count=1,flags=re.M)
 patches={}
 # Keep mod callbacks, and restore legacy callbacks. Parts only exist on their owner page.
 for fid,mode in [(29817,'Get'),(29818,'Set')]:
  s=get(fid);method=29827 if mode=='Get' else 29828
  bindings=[('SYS_戦闘の進行速度を速くする',29853 if mode=='Get' else 29852)]+[(OLD_PARTS[j],r[3]+(1 if mode=='Get' else 0)) for j,r in enumerate(ROWS)]
  body=''.join(f'\tPUSHSTRUCTPAGE\n\tPUSH {method}\n\tS_PUSH "{key}"\n\tPUSH -1\n\tPUSH {cb}\n\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n' for key,cb in bindings)
  s=begin(s,body)
  old=f'\tS_PUSH "%d{encode("배").decode("cp932")}"\n\tCALLFUNC KR_Speed\n\tS_MOD 2\n'
  assert s.count(old)==1
  lbl='kr_speed_label_'+mode
  new=f'\tCALLFUNC KR_Speed\n\tPUSH 1\n\tNOTE\n\tIFNZ {lbl}\n\tS_PUSH "{encode("기본").decode("cp932")}"\n\tJUMP {lbl}_done\n{lbl}:\n'+old+f'{lbl}_done:\n'
  patches[fid]=s.replace(old,new)
 # Preserve non-2x mod values through passive per-frame checkbox synchronization.
 for j,r in enumerate(ROWS):
  setter=r[3];getter=setter+1;s=get(getter);assert s.count('\tPUSH 100\n\tGT\n')==1
  patches[getter]=s.replace('\tPUSH 100\n\tGT\n','\tPUSH 200\n\tEQUALE\n')
  s=get(setter);patches[setter]=begin(s,f'\t.LOCALREF bCheck\n\tCALLFUNC {names[getter]}\n\tNOTE\n\tIFNZ kr_toggle_{setter}\n\tRETURN\nkr_toggle_{setter}:\n')
 # Default slider notch honors vanilla battle-speed flag; explicit mod/quick take priority.
 patches[31859]=fn(31859,'KR_BattleRate','''\tCALLFUNC KR_QuickActive
\tIFZ kr_rate_normal
\tPUSH 1000
\tRETURN
kr_rate_normal:
\tCALLFUNC KR_Speed
\tPUSH 1
\tLTE
\tIFNZ kr_rate_vanilla
\tCALLFUNC KR_Speed
\tRETURN
kr_rate_vanilla:
\tCALLFUNC Conf_GetBattleSpeedUp
\tIFZ kr_rate_one
\tCALLFUNC Ａ＿全文スキップ中確認
\tIFNZ kr_rate_one
\tPUSH 2
\tRETURN
kr_rate_one:
\tPUSH 1
\tRETURN''')
 # Show the fully assembled starting formation once, before the action loop.
 # View_Update still performs native updates/rendering in quick mode; only its
 # final presentation is suppressed, so present that completed initial frame.
 s=get(29387);needle='\tPUSH 29443\n\tPUSH 1\n\tX_DUP 1\n\tX_MOV 4 1\n\tCALLMETHOD 1\n\tPOP\n';assert s.count(needle)==1
 preview='\tCALLFUNC KR_QuickActive\n\tIFZ kr_initial_preview_done\n\tCALLFUNC AFL_View_Update\n\tCALLFUNC KR_QuickActive\n\tIFZ kr_initial_preview_done\n\tCALLHLL SystemService UpdateView 0\n\tPOP\nkr_initial_preview_done:\n'
 patches[29387]=s.replace(needle,needle+preview)
 patch=O/'mod_tab_patch.jam';patch.write_text('\n'.join(patches.values()),encoding='utf8')
 out=O/'NightRemaster.ain';cmd('ain','edit','--jam',patch,'-o',out,src);cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json')
 changes=[]
 for a,b in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y
  if aa!=bb:changes.append(a['index'])
 assert changes==sorted(patches) and len(m['functions'])==len(nm['functions'])
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 a=unpack(src.read_bytes());b=unpack(out.read_bytes());size=struct.unpack_from('<I',a,12)[0]
 assert a[16:16+size]==b[16:16+size]
 assert strings(b)[2][:len(strings(a)[2])]==strings(a)[2]
 assert a[a.index(b'MSG1'):a.index(b'STR0')]==b[b.index(b'MSG1'):b.index(b'STR0')]
 for f in BASE.glob('built_*.jam'):shutil.copy2(f,O/f.name)
 for f in Path('remaster_multiplier_20260915').glob('built_*.jam'):
  if not (O/f.name).exists():shutil.copy2(f,O/f.name)
 for i in sorted(set(patches)|{26335,26338,26341,26344}):cmd('ain','dump','--function',names[i],'-o',O/f'built_{i}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 nat=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert nat['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',nat)
 return dict(patched_functions=changes,all_other_functions_and_metadata_exact=True,original_CODE_and_strings_prefix_and_MSG1_exact=True,save_schema_unchanged=True,speed_precedence='quick > explicit2..5x > original speed option at default notch',reward_sync='Exact2x checkbox; unchanged input is no-op, explicit toggle sets1x/2x',quick_preview='Once after DispEffect/enemy formation/gauges/control setup, before first action; original results unchanged')

def main():
 O.mkdir(exist_ok=True);p=json.loads((O/'source_pointer.json').read_text());assert p==json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime'])
 assert sha(rt/'NightRemaster.ain')=='532f09ba127c2bdb8dbca3b41d6eb9615806a98ef326766f1d950c79d04f3ad0'
 before={n:sha(rt/n) for n in FILES};pact=build_pact(rt);ee=build_ex(rt);ain=build_ain(rt)
 ev=dict(status='MOD_TAB_STAGED',source_pointer=p,source_files=before,files={n:sha(O/n) for n in FILES},PACT=pact,EX=ee,AIN=ain,translator_model='Codex internal',native_gameplay_verified=False,department_route_user_confirmed=True)
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
