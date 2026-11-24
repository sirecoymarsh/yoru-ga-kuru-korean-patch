"""Stage native game-settings cheats on top of the pending consume-name repair."""
from cheat_support_20260915 import *
import copy,struct,datetime
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit
from build_remaster_multiplier_20260915 import (read_afa3,rebuild,ex,child,maybe,val,part,allparts,si,ss,setlist,rename,txt_info)

def clean(s,fid):
 s=re.sub(r'^EOF .*\n?','',s,flags=re.M)
 if 'ENDFUNC ' not in s:s+='\nENDFUNC '+names[fid]+'\n'
 return s
def begin(s,body):return re.sub(r'(^FUNC \d+\n)',lambda m:m[0]+body,s,count=1,flags=re.M)
def end(s,body):
 p=s.rfind('\tRETURN');assert p>=0;return s[:p]+body+s[p:]
def label():
 label.i+=1;return '0x'+hex(0x7ed00000+label.i)[2:]
label.i=0
def callmethod(fid):return f'\tPUSH {fid}\n\tCALLMETHOD 0\n'

def build_ain():
 stage=O/'helpers_declared.ain';cmd('ain','edit','--jaf',O/'helpers.jaf','-o',stage,SRC)
 cmd('ain','dump','-j','-o',O/'declared_meta.json',stage);decl=read_meta(O/'declared_meta.json')
 ids={f['name']:f['index'] for f in decl['functions'][len(M['functions']):]}
 old=unpack(SRC.read_bytes());raw=bytearray(unpack(stage.read_bytes()));oldlen=struct.unpack_from('<I',old,12)[0];newlen=struct.unpack_from('<I',raw,12)[0]
 assert raw[16:16+oldlen]==old[16:16+oldlen]
 assert raw[16+newlen:20+newlen]==b'FUNC'
 struct.pack_into('<I',raw,24+newlen,M['functions'][0]['address']);stage.write_bytes(pack(bytes(raw),SRC.read_bytes()[:8]))
 patches={};bridges={}
 bridges['KR_Flag']='\t.LOCALREF slot\n\tPUSH 0\n\tLT\n\tIFNZ 0x7ed00001\n\t.LOCALREF slot\n\tCALLFUNC SystemFlagManager::Get\n\tRETURN\n0x7ed00001:\n\tPUSH 0\n\tRETURN\n'
 bridges['KR_Poke']='\t.LOCALREF slot\n\tPUSH 0\n\tLT\n\tIFNZ 0x7ed00002\n\t.GLOBALREF g_sysFlagList\n\tCALLHLL Array Numof 1\n\t.LOCALREF slot\n\tLTE\n\tIFNZ 0x7ed00002\n\t.GLOBALREF g_sysFlagList\n\t.LOCALREF slot\n\t.LOCALREF value\n\tX_ASSIGN 1\n\tPOP\n0x7ed00002:\n\tRETURN\n'
 label.i=100
 bridges['KR_SaveOptions']='\tCALLFUNC SystemFlagManager::Save\n\tRETURN\n'
 bridges['KR_GetAuto']='\t.GLOBALREF Flags\n'+callmethod(26609)+'\tRETURN\n'
 bridges['KR_SetAuto']='\t.GLOBALREF Flags\n\tPUSH 26611\n\t.LOCALREF enabled\n\tCALLMETHOD 1\n\tRETURN\n'
 bridges['KR_FirstBattleTutorial']='\tPUSH 3\n\tCALLFUNC N_Tutorial::IsRunFirstTime\n\tRETURN\n'
 bridges['KR_Time']='\tCALLHLL system GetTime 0\n\tRETURN\n'
 bridges['KR_CancelPressed']='\tCALLFUNC C_UserInputManager::IsClickCancel\n\tRETURN\n'
 # Native slider + checkbox event bindings, preserving all existing options.
 for fid,method,mode in [(29817,29825,'Get'),(29818,29826,'Set')]:
  s=dump(fid);oldmethod=29827 if mode=='Get' else 29828;oldcb=29853 if mode=='Get' else 29852
  needle=f'\tPUSH {oldmethod}\n\tS_PUSH "SYS_戦闘の進行速度を速くする"\n\tPUSH -1\n\tPUSH {oldcb}\n'
  assert s.count(needle)==1
  s=s.replace(needle,f'\tPUSH {method}\n\tS_PUSH "KR_CheatSpeed"\n\tPUSH -1\n\tPUSH {ids["KR_"+mode+"Speed"]}\n')
  extra=''
  for key in ['Trap','Quick','Route']:
   extra+=f'\tPUSHSTRUCTPAGE\n\tPUSH {oldmethod}\n\tS_PUSH "KR_Cheat{key}"\n\tPUSH -1\n\tPUSH {ids["KR_"+mode+key]}\n\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n'
  done=label()
  extra+=f'''\t.STRUCTREF C_ConfigView m_ActName
\tA_REF
\tS_PUSH "KR_CheatSpeedValue"
\tCALLFUNC AFL_Activity_IsExistPartsByName
\tIFZ {done}
\t.STRUCTREF C_ConfigView m_ActName
\tA_REF
\tS_PUSH "KR_CheatSpeedValue"
\tCALLFUNC AFL_Activity_GetPartsNumber
\tS_PUSH "%d{encode('배').decode('cp932')}"
\tCALLFUNC KR_Speed
\tS_MOD 2
\tPUSH 1
\tCALLFUNC Ｐ＿テキスト設定
{done}:
'''
  patches[fid]=end(s,extra)
 # One owner for normal1..5x and quick simulation's scaled timers.
 same=label();patches[29388]=fn(29388,names[29388],f'''\tCALLFUNC KR_QuickWatch
\t.STRUCTREF C_SceneBattle m_BattleSpeed
\tCALLFUNC KR_BattleRate
\tEQUALE
\tIFNZ {same}
\tCALLFUNC CASTimer::EraseRate
\tS_PUSH ""
\tCALLFUNC KR_BattleRate
\tITOF
\tCALLFUNC CASTimer::AddRate
\tPUSHSTRUCTPAGE
\tPUSH 12
\tCALLFUNC KR_BattleRate
\tX_ASSIGN 1
\tPOP
{same}:
\tRETURN''')
 # Keep state/event/audio/sprite updates. Only the final screen presentation is gated.
 s=dump(21031);needle='\tCALLHLL SystemService UpdateView 0\n\tPOP\n';assert s.count(needle)==1;done=label()
 patches[21031]=begin(s.replace(needle,f'\tCALLFUNC KR_QuickActive\n\tIFNZ {done}\n'+needle+done+':\n'),'\tCALLFUNC KR_QuickWatch\n')
 # Both wait functions still pump a complete update once in quick mode.
 for fid in [30084,30085]:
  normal=label();patches[fid]=begin(dump(fid),f'\tCALLFUNC KR_QuickActive\n\tIFZ {normal}\n\tCALLFUNC AFL_View_Update\n\tPUSH 0\n\tRETURN\n{normal}:\n')
 s=dump(29387);needle='\tPUSHSTRUCTPAGE\n\tPUSH 29392\n\tCALLMETHOD 0\n';assert s.count(needle)==1
 s=s.replace(needle,'\t.STRUCTREF C_SceneBattle m_EventBattleInfo\n\tPUSH 0\n\tX_REF 1\n\tCALLFUNC KR_BeginQuick\n'+needle)
 needle='\t.LOCALASSIGN pnResult 0\n';assert s.count(needle)==1;s=s.replace(needle,'\tCALLFUNC KR_EndQuick\n'+needle)
 patches[29387]=s
 # Restore resumed transient auto mode BEFORE original common-settings load.
 patches[29556]=begin(dump(29556),'\tCALLFUNC KR_EndQuick\n')
 patches[26656]=end(dump(26656),'\tCALLFUNC KR_ResetTransient\n')
 # Trap removal is a normal visited-cell removal, not a dungeon-wide data reset.
 s=dump(28664);needle='0x6180b4:\n';assert s.count(needle)==1;normal=label()
 body=f'''\tCALLFUNC KR_GetTrap
\tIFZ {normal}
\t.LOCALREF cell
\tPUSH 27005
\tCALLMETHOD 0
\tPUSH 5
\tNOTE
\tIFNZ {normal}
\t.LOCALREF cell
\tPUSH 27029
\tCALLMETHOD 0
\tIFZ 0x7ed03001
\t.LOCALREF cell
\tPUSH 27008
\tCALLMETHOD 0
\tPUSH 0
\tNOTE
\tIFNZ {normal}
0x7ed03001:
\t.LOCALREF cell
\tPUSH 27025
\tPUSH 1
\tCALLMETHOD 1
\t.LOCALREF cell
\tPUSH 27022
\tPUSH 1
\tCALLMETHOD 1
\t.STRUCTREF C_SceneDungeon m_DungeonView
\tPUSH 28763
\t.LOCALREF lx
\t.LOCALREF ly
\tCALLMETHOD 2
\tPUSH 0
\tRETURN
{normal}:
'''
 patches[28664]=s.replace(needle,needle+body)
 # The explicit disarm action also succeeds immediately without the character
 # selector; its caller retains the original removal and map-update handling.
 normal=label()
 patches[27143]=begin(dump(27143),f'\tCALLFUNC KR_GetTrap\n\tIFZ {normal}\n\tPUSH 1\n\tRETURN\n{normal}:\n')
 # Fog-independent path cost applies only during our synchronous AStar snapshot.
 normal=label();blocked=label()
 patches[27041]=begin(dump(27041),f'''\tPUSH 87
\tCALLFUNC KR_Flag
\tPUSH 1
\tNOTE
\tIFNZ {normal}
\tPUSHSTRUCTPAGE
\tPUSH 27039
\tCALLMETHOD 0
\tIFZ {blocked}
\tPUSH 0
\tRETURN
{blocked}:
\tPUSH 2147483647
\tRETURN
{normal}:
''')
 # A route preview uses its own local array; never replaces auto-move destinations.
 normal=label();patches[28677]=begin(dump(28677),f'''\tCALLFUNC KR_GetRoute
\tIFZ {normal}
\tPUSH 88
\tCALLFUNC KR_Flag
\tPUSH 1
\tEQUALE
\tIFNZ {normal}
\tRETURN
{normal}:
''')
 done=label();patches[28673]=end(dump(28673),f'''\t.STRUCTREF C_SceneDungeonMiniMapView m_MapInfo
\tPUSH -1
\tEQUALE
\tIFNZ {done}
\t.STRUCTREF C_SceneDungeonMiniMapView m_MapInfo
\tPUSHSTRUCTPAGE
\t.LOCALREF x
\t.LOCALREF y
\tCALLFUNC KR_DrawRoute
{done}:
''')
 out=[fn(ids[n],n,b) for n,b in bridges.items()]+[clean(s,i) for i,s in patches.items()]
 # JAF's legacy F_PUSH/SH_LOCALCREATE instructions are unsupported by this
 # shipped engine. Lower only added helpers to its native v14 instruction forms.
 for n,i in ids.items():
  if n in bridges:continue
  helper_file=O/f'jaf_helper_{i}.jam';cmd('ain','dump','--function',n,'-o',helper_file,stage)
  raw_helper=helper_file.read_text(encoding='utf8');fixed_helper=native_lower(raw_helper)
  if fixed_helper!=raw_helper:out.append(fixed_helper)
 (O/'cheat_patch.jam').write_text('\n'.join(out),encoding='utf8')
 dest=O/'NightRemaster.ain';cmd('ain','edit','--jam',O/'cheat_patch.jam','-o',dest,stage)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',dest);nm=read_meta(O/'candidate_meta.json')
 changed=[]
 for i,(a,b) in enumerate(zip(M['functions'],nm['functions'])):
  if a!=b:
   aa=dict(a);bb=dict(b);aa.pop('address');bb.pop('address');assert aa==bb,i;changed.append(i)
 assert sorted(patches)==changed,(sorted(patches),changed)
 for k in M:
  if k not in ['functions','switches']:assert M[k]==nm[k],k
 assert len(M['switches'])==len(nm['switches'])
 schanged=[]
 for i,(a,b) in enumerate(zip(M['switches'],nm['switches'])):
  if a!=b:
   assert a['case-type']==b['case-type'] and a['default-address']==b['default-address']
   assert [x['value'] for x in a['cases']]==[x['value'] for x in b['cases']]
   assert len({y['address']-x['address'] for x,y in zip(a['cases'],b['cases'])})==1
   schanged.append(i)
 assert schanged==[450,451,452],schanged
 new=unpack(dest.read_bytes());assert new[16:16+oldlen]==old[16:16+oldlen]
 assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
 assert new[new.index(b'MSG1'):new.index(b'SWI0')]==old[old.index(b'MSG1'):old.index(b'SWI0')]
 assert new[new.index(b'GVER'):new.index(b'STR0')]==old[old.index(b'GVER'):old.index(b'STR0')]
 for i in sorted(patches):cmd('ain','dump','--function',names[i],'-o',O/f'built_{i}.jam',dest)
 for name,i in ids.items():cmd('ain','dump','--function',name,'-o',O/f'built_{i}.jam',dest)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',dest)
 runtime=Path(json.loads((R/'ui_cumulative/current.json').read_text())['runtime'])
 native=audit(dest,O/'candidate_meta.json',O/'native_raw_code.jam',runtime/'NightRemaster.exe')
 assert native['all_active_opcodes_supported'],native['unsupported']
 savej(O/'native_opcode_audit.json',native)
 return dict(patched_existing=changed,added_functions=ids,relocated_switches=schanged,all_original_metadata_except_addresses_exact=True,original_CODE_STR0_MSG1_exact=True,save_schema_unchanged=True)

def build_pact():
 p=json.loads((R/'ui_cumulative/current.json').read_text());src=Path(p['runtime'])/'NightRemasterPact.afa';arc=read_afa3(src)
 for i in [120,123]:
  e=arc.entries[i]
  with src.open('rb') as f:f.seek(e.absolute_offset);(O/f'pact_{i}.pactex').write_bytes(f.read(e.size))
 original=ex.decode_ex(O/'pact_123.pactex');doc=ex.decode_ex(O/'pact_123.pactex');sound=ex.decode_ex(O/'pact_120.pactex')
 battle=part(doc,'矩形_戦闘');kids=child(battle,'子パーツ');order=val(battle,'子パーツリスト')
 tx=copy.deepcopy(child(kids,'テキストパーツ_000:0'));order_template=copy.deepcopy(order.items[0])
 def add(parent,t):
  child(parent,'子パーツ').children.append(t);oi=copy.deepcopy(order_template);oi.value.payload.replacement=t.name.replacement or t.name.value;val(parent,'子パーツリスト').items.append(oi)
 def textpart(name,text,x,y,size=22):
  t=copy.deepcopy(tx);rename(t,name);setlist(t,'座標',[x,y,20]);ss(txt_info(t),'テキスト',text,True);si(child(txt_info(t),'テキスト装飾'),'フォントサイズ',size);return t
 old=child(kids,'SYS_戦闘の進行速度を速くする');ix=kids.children.index(old)
 slider=copy.deepcopy(part(sound,'SYS_音声女性スライダ'));rename(slider,'KR_CheatSpeed');setlist(slider,'座標',[0,50,2]);si(slider,'原点座標モード',1)
 info=child(slider,'種類別情報')
 for k,v in [('長さ',320),('幅',38),('全体スクロール量',5),('表示量',1),('スクロール位置',0),('スクロールレート',0),('ボタンクリック移動量',1)]:si(info,k,v)
 kids.children[ix]=slider
 next(i.value.payload for i in order.items if i.value.payload.value.decode('cp932')=='SYS_戦闘の進行速度を速くする').replacement=b'KR_CheatSpeed'
 ss(txt_info(child(kids,'テキストパーツ_000:0')),'テキスト','전투 속도 (1~5배)',True)
 add(battle,textpart('KR_CheatSpeedValue','1배',276,8,22))
 setlist(child(kids,'SYS_戦闘が終わってもオート戦闘継続'),'座標',[0,102,3])
 # New native group in the free right-hand column; original confirmations,
 # training, NSFW option, chrome, remaster reward sliders and wallpapers retained.
 donor=part(doc,'矩形_訓練');group=copy.deepcopy(donor);rename(group,'KR_CheatGroup');setlist(group,'座標',[783,406,45])
 child(group,'子パーツ').children=[];val(group,'子パーツリスト').items=[]
 add(group,textpart('KR_CheatHeading','치트 / 편의 기능',14,0,22))
 checkbox=part(doc,'SYS_訓練演出の簡略化')
 labels={}
 for key,title,y in [('Trap','함정 즉시 해체',45),('Quick','자동 전투 결과만 보기',85),('Route','다음 층 경로 표시',125)]:
  c=copy.deepcopy(checkbox);rename(c,'KR_Cheat'+key);setlist(c,'座標',[0,y,2+y]);
  # Native checkbox labels are children/low-level text, not replacement raster plates.
  ci=child(c,'種類別情報');labels[key]=title
  # Inspect and replace only the existing label text nodes in every checkbox state.
  changed=0
  def walk(n):
   nonlocal changed
   if getattr(n,'name',None) and n.name.value.decode('cp932')=='テキスト' and getattr(n,'leaf_value',None):
    oldtext=decode(n.leaf_value.payload.value);pad=oldtext[:len(oldtext)-len(oldtext.lstrip())]
    n.leaf_value.payload.replacement=encode(pad+title);changed+=1
   for z in getattr(n,'children',[]):walk(z)
  walk(ci)
  if changed==0:
   # Native checkbox sprite has no label: reuse separate native text to its right.
   add(group,textpart('KR_CheatLabel'+key,title,44,y+3,20))
  add(group,c)
 add(group,textpart('KR_CheatHint','일반 전투만 / 우클릭으로 연출 복귀',0,174,15))
 root=doc.blocks[2].payload.children[0];add(root,group)
 # Exact inverse proves only battle subtree + new group changed.
 saved=copy.deepcopy(battle);battle.__dict__.update(copy.deepcopy(part(original,'矩形_戦闘').__dict__))
 rk=child(root,'子パーツ');rk.children.remove(group);ro=val(root,'子パーツリスト');go=ro.items.pop()
 assert doc.serialize_payload()==original.raw_payload
 battle.__dict__.update(saved.__dict__);rk.children.append(group);ro.items.append(go)
 target=O/'pact_123_cheats.pactex';target.write_bytes(ex.encode_ex(doc.header,doc.serialize_payload()))
 assert ex.decode_ex(target).serialize_payload()==doc.serialize_payload()
 rebuild(src,O/'NightRemasterPact.afa',{123:target})
 result=read_afa3(O/'NightRemasterPact.afa');changed=[]
 with src.open('rb') as a,(O/'NightRemasterPact.afa').open('rb') as b:
  for x,y in zip(arc.entries,result.entries):
   assert (x.no,x.name,x.unknown0,x.unknown1)==(y.no,y.name,y.unknown0,y.unknown1)
   a.seek(x.absolute_offset);b.seek(y.absolute_offset)
   if a.read(x.size)!=b.read(y.size):changed.append(x.no)
 assert changed==[123]
 cmd('ex','dump','-o',O/'pact_123_cheats.x',target)
 return dict(changed_entries=changed,other184_entries_exact=True,native_slider_range=[1,5],raster_bytes_unchanged=True,labels=labels)

def main():
 assert sha(SRC)=='e144757005642031e155c08c8ab9d6c51582868f86b513a6f45d83438266c931'
 p=json.loads((R/'ui_cumulative/current.json').read_text());savej(O/'source_pointer.json',p)
 ain=build_ain();pact=build_pact();savej(O/'build_evidence.json',dict(status='STAGED_REVIEW_PENDING',time=datetime.datetime.now().astimezone().isoformat(),source_pointer=p,source_ain=sha(SRC),included_pending_consumable_fix=True,AIN=ain,PACT=pact,files={n:sha(O/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},translator_model='Codex internal',native_verified=False,no_live_or_save_files_modified=True))
 print((O/'build_evidence.json').read_text(encoding='utf8'))
if __name__=='__main__':main()
