"""Build an ordinary-dungeon-only sweep candidate against the current exact runtime."""
from pathlib import Path
import copy,json,re,struct,shutil
from build_remaster_multiplier_20260915 import cmd,read_meta,ex,read_afa3,rebuild,part,child,val,allparts,rename,setlist,ss,si,txt_info,encode,decode,fn
from build_mod_tab_20260915 import add,remove,name,coords
from build_route_perf_20260915 import symbol
from build_instant_loot_20260915 import clean,begin
from cheat_support_20260915 import R,sha,savej
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit

O=Path('dungeon_skip_20260916'); FILES=['NightRemaster.ain','NightRemasterPact.afa']
M=read_meta(Path('loot_notice_20260915/candidate_meta.json'))
NAMES={}; seen={}
for f in M['functions']:
 n=symbol(M,f['index']); c=seen.get(n,0); seen[n]=c+1; NAMES[f['index']]=n+(f'#{c}' if c else '')
def S(t):return '\tS_PUSH '+json.dumps(encode(t).decode('cp932'),ensure_ascii=False)+'\n'
def lr(n):return f'\t.LOCALREF {n}\n'
def push(n):return f'\tPUSH {n}\n'
def cf(n):return f'\tCALLFUNC {n}\n'
def field(obj,i):return obj+push(i)+'\tX_REF 1\n'
def glob(i):return '\tPUSHGLOBALPAGE\n'+push(i)+'\tX_REF 1\n'
def meth(obj,i,args=''):return obj+push(i)+args+f'\tCALLMETHOD {len(args.splitlines()) if False else 0}\n'
def cm(obj,i,args='',argc=0):return obj+push(i)+args+f'\tCALLMETHOD {argc}\n'
def assign(index,expr):return '\tPUSHLOCALPAGE\n'+push(index)+expr+'\tX_ASSIGN 1\n\tPOP\n'

def build_pact(rt):
 src=rt/'NightRemasterPact.afa'; arc=read_afa3(src); docs={}
 for i in [161,185]:
  e=arc.entries[i]
  with src.open('rb') as f:f.seek(e.absolute_offset); raw=f.read(e.size)
  p=O/f'original_pact_{i}.pactex'; p.write_bytes(raw); docs[i]=ex.decode_ex(p)
 d=docs[185]; group=part(d,'KR_ModDungeon'); t=copy.deepcopy(part(d,'KR_CheatTrap'))
 rename(t,'KR_CheatSweep'); setlist(t,'座標',[0,188,198]); ss(child(t,'種類別情報'),'テキスト','    소탕',True); add(group,t)
 for n,y in [('KR_CheatTrap',0),('KR_CheatQuick',44),('KR_CheatRoute',88),('KR_CheatLoot',132)]:
  p=part(d,n);c=coords(p);setlist(p,'座標',[c[0],y,c[2]])
 for n,text,y in [('KR_ModQuickHint','일반 던전에 자동 소탕 버튼을 표시합니다.',544),('KR_ModQuickCancel','소탕: 남은 시간 정산 후 다음 날로 진행',568)]:
  p=part(d,n); remove(group,n);setlist(p,'座標',[363,y,40]);ss(txt_info(p),'テキスト',text,True);si(child(txt_info(p),'テキスト装飾'),'フォントサイズ',14);add(d.blocks[2].payload.children[0],p)
 d=docs[161]; parent=part(d,'矩形_000'); t=copy.deepcopy(part(d,'ボタン_アイテム'))
 rename(t,'KR_SweepButton');setlist(t,'座標',[0,0,1]);si(t,'表示',1)
 ci=child(t,'種類別情報');ss(ci,'ＣＧ名','シス／コンフィグ／タブ');ss(ci,'テキスト','')
 si(ci,'フォントタイプ',259);si(ci,'フォントサイズ',24);setlist(ci,'サイズ',[192,42])
 # Native CG is 192px regardless of Size. Scale only its background, not Hangul.
 setlist(t,'拡大縮小',[138/192,1])
 label=copy.deepcopy(part(docs[185],'KR_ModQuickHint'));rename(label,'KR_SweepButtonLabel')
 setlist(label,'座標',[26.666667,9,2]);setlist(label,'拡大縮小',[1,1]);si(label,'オンカーソル透過',1)
 ti=txt_info(label);ss(ti,'テキスト','자동 소탕',True);deco=child(ti,'テキスト装飾');si(deco,'フォントサイズ',24);si(deco,'字間隔',0)
 import build_mod_tab_20260915 as modtab
 modtab.ORDER=copy.deepcopy(val(parent,'子パーツリスト').items[0])
 root=modtab.clean_group(part(docs[185],'KR_ModDungeon'),'KR_SweepRoot',1130,386);si(root,'表示',0)
 si(root,'オンカーソル透過',1)
 rectangle=child(child(root,'種類別情報'),'通常状態')
 for key,point in [('左上',[0,0]),('右上',[138,0]),('左下',[0,42]),('右下',[138,42])]:setlist(rectangle,key,point)
 add(root,t);add(root,label);add(parent,root)
 # Result is a timed native message dialog, not a new external activity file.
 replacements={}
 for i,d in docs.items():
  out=O/f'pact_{i}_sweep.pactex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));assert ex.decode_ex(out).serialize_payload()==d.serialize_payload();replacements[i]=out
 report=rebuild(src,O/'NightRemasterPact.afa',replacements)
 return dict(changed_entries=[161,185],archive=report,all_raster_font_assets_unchanged=True)

def build_ain(rt):
 src=rt/'NightRemaster.ain'; stage=O/'helpers_declared.ain'
 jaf=(O/'sweep_helpers.jaf').read_text(encoding='utf8')
 jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda m:json.dumps(encode(json.loads(m[0])).decode('cp932'),ensure_ascii=False) if any('\uac00'<=c<='\ud7a3' for c in m[0]) else m[0],jaf)
 (O/'helpers_proxy.jaf').write_text(jaf,encoding='utf8');cmd('ain','edit','--jaf',O/'helpers_proxy.jaf','-o',stage,src)
 old=unpack(src.read_bytes());raw=bytearray(unpack(stage.read_bytes()));size=struct.unpack_from('<I',old,12)[0];ns=struct.unpack_from('<I',raw,12)[0]
 assert raw[16:16+size]==old[16:16+size];struct.pack_into('<I',raw,24+ns,M['functions'][0]['address']);stage.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',stage);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(M['functions']):]}
 def get(i):
  p=O/f'original_{i}.jam'
  if not p.exists():cmd('ain','dump','--function',NAMES[i],'-o',p,src)
  return clean(p.read_text(encoding='utf8'),NAMES[i])
 patches={}; bridges={}
 scene=lr('scene');mp=field(scene,6)
 bridges['KR_SweepCurrent']=cm(scene,28622)+'\tRETURN\n'
 bridges['KR_SweepMapIdentity']=mp+'\tRETURN\n'
 # Date key uses the native serialized date fields, no clock-based reward reroll.
 date=cm(glob(228),26479) if False else ''
 # C_GameFlags is accessed by symbol because its global index is not assumed.
 date=cm('\t.GLOBALREF Flags\n',26479)
 bridges['KR_SweepDate']=date+'\tX_DUP 1\n'+push(26450)+'\tCALLMETHOD 0\n'+push(100)+'\tMUL\n\tX_MOV 2 1\n\tX_DUP 1\n'+push(26453)+'\tCALLMETHOD 0\n\tX_MOV 2 1\n\tDELETE\n\tADD\n\tRETURN\n'
 # Replace with direct C_GameDate getter wrapper below after verified metadata.
 bridges['KR_SweepConsume']=cm(scene,28650,lr('remaining'),1)+'\tPOP\n\tRETURN\n'
 b=cf('KR_GetSweep')+'\tIFZ sweep_no\n'+scene+push(-1)+'\tEQUALE\n\tIFNZ sweep_no\n'
 b+=assign(1,cm(scene,28622))+lr('id')+cf('KR_SweepAllowed')+'\tIFZ sweep_no\n'
 b+=assign(2,cf('L_DungeonManager::GetStartDungeonId'))+lr('start')+cf('KR_SweepAllowed')+'\tIFZ sweep_no\n'
 b+=lr('id')+push(1000)+'\tDIV\n'+lr('start')+push(1000)+'\tDIV\n\tNOTE\n\tIFNZ sweep_no\n'
 b+=lr('id')+push(1000)+'\tDIV\n'+push(1000)+'\tMUL\n'+cf('L_DungeonManager::GetDungeonBaseId')+'\tNOTE\n\tIFNZ sweep_no\n'
 b+=cm('\t.GLOBALREF Flags\n',26518)+'\tIFZ sweep_no\n'
 b+=scene+push(4)+'\tX_REF 2\n\tPOP\n'+push(-1)+'\tNOTE\n\tIFNZ sweep_no\n'
 b+=mp+push(-1)+'\tEQUALE\n\tIFNZ sweep_no\n'+cm(mp,27042)+lr('id')+'\tNOTE\n\tIFNZ sweep_no\n'
 b+=field(scene,7)+'\tCALLHLL Array Numof 2\n\tIFNZ sweep_no\n'
 b+=cf('L_Calendar::GetRemainTime')+push(0)+'\tLTE\n\tIFNZ sweep_no\n'+cf('L_Calendar::GetRemainTime')+push(1000)+'\tGT\n\tIFNZ sweep_no\n'
 b+=assign(3,cf('L_Party::GetNumberOfPersons'))+lr('persons')+push(1)+'\tLT\n\tIFNZ sweep_no\n'+lr('persons')+push(3)+'\tGT\n\tIFNZ sweep_no\n'+cf('KR_LootHasLivingParty')+'\tIFZ sweep_no\n'
 b+=glob(198)+'\tCALLHLL Array Numof 65538\n\tIFNZ sweep_no\n'+push(1)+'\tRETURN\nsweep_no:\n'+push(0)+'\tRETURN\n'
 bridges['KR_SweepSceneOK']=b
 # Reuse the native IParts wrapper retrieval/release sequence (m_Act -> part).
 def parts_seq(owner,variable='p'):
  return owner+push(0)+'\tX_REF 2\n\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n'+push(0)+'\tX_REF 1\n\tX_MOV 2 1\n'+push(7)+'\tADD\n\tX_REF 1\n'+S('KR_SweepRoot')+'\tCALLMETHOD 1\n'
 owner=field(field(scene,2),4)
 b=''
 for obj in [scene,field(scene,2),owner]:b+=obj+push(-1)+'\tEQUALE\n\tIFNZ visible_done\n'
 b+=owner+push(0)+'\tX_REF 2\n\tPOP\n'+push(-1)+'\tEQUALE\n\tIFNZ visible_done\n'
 b+=parts_seq(owner)+'\tX_DUP 2\n\tPOP\n'+push(-1)+'\tEQUALE\n\tIFNZ visible_release\n\tX_DUP 2\n'
 b+='\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n'+push(0)+'\tX_REF 1\n\tX_MOV 2 1\n'+push(60)+'\tADD\n\tX_REF 1\n'+lr('show')+'\tCALLMETHOD 1\nvisible_release:\n\tPOP\n\tDELETE\nvisible_done:\n\tRETURN\n'
 bridges['KR_SweepVisible']=b
 # Native dialog, cancel is first and the only success code is 11.
 bridges['KR_SweepConfirm']=S('자동 소탕\n남은 탐색 시간을 모두 사용하고 다음 날로 진행합니다.\n보상은 현재 층 기준의 대체 보상입니다.\n스토리 던전에는 적용되지 않습니다.\n계속하시겠습니까?')+cf(NAMES[27863])+push(2)+cf(NAMES[27864])+push(12)+S('취소')+S('')+push(0)+cf(NAMES[27865])+push(11)+S('소탕 실행')+S('')+push(0)+cf(NAMES[27865])+cf(NAMES[27872])+push(1)+push(0)+cf(NAMES[27873])+push(11)+'\tEQUALE\n\tRETURN\n'
 flags='\t.GLOBALREF Flags\n'
 confirm=bridges['KR_SweepConfirm'].removesuffix(push(11)+'\tEQUALE\n\tRETURN\n')
 bridges['KR_SweepConfirm']=assign(1,cm(flags,26512))+cm(flags,26514,push(1),1)+assign(2,confirm)+cm(flags,26514,lr('previousLock'),1)+lr('result')+push(11)+'\tEQUALE\n\tRETURN\n'
 # Quiet equivalent of native AddExp: same need table, levelup, HP and equipment limit.
 pa=lr('pa'); b=pa+push(4)+lr('amount')+'\tPLUSA\n\tPOP\nexp_loop:\n'+field(pa,1)+push(99)+'\tGTE\n\tIFNZ exp_end\n'
 b+=assign(2,cm(pa,27334))+lr('need')+push(0)+'\tLTE\n\tIFNZ exp_end\n'+field(pa,4)+lr('need')+'\tLT\n\tIFNZ exp_end\n'
 b+=cm(pa,27303,push(1),1)+pa+push(4)+lr('need')+'\tMINUSA\n\tPOP\n\tJUMP exp_loop\nexp_end:\n\tRETURN\n';bridges['KR_SweepAddExp']=b
 # Scalar snapshot generator: writes no references; shape cannot change in payout.
 serial=0
 def label(stem):
  nonlocal serial;serial+=1;return f'{stem}_{serial}'
 def loop(var,limit,body):
  a=label('loop');z=label('end');return f'\t.LOCALASSIGN {var} 0\n{a}:\n'+lr(var)+limit+f'\tGTE\n\tIFNZ {z}\n'+body+f'\t.LOCALINC2 {var}\n\tJUMP {a}\n{z}:\n'
 def transfer(address,restore=True):
  a=label('read');z=label('done')
  w=lr('restore')+f'\tIFZ {a}\n'+address+lr('data')+lr('cursor')+'\tX_REF 1\n\tX_ASSIGN 1\n\tPOP\n'+f'\tJUMP {z}\n{a}:\n'+lr('data')+address+'\tX_REF 1\n\tCALLHLL Array PushBack 1\n'+f'{z}:\n\t.LOCALINC2 cursor\n'
  return w
 def array_values(arr,var):return loop(var,arr+'\tCALLHLL Array Numof 1\n',transfer(arr+lr(var)))
 def object_loop(gid,fields):
  arr=glob(gid);obj=field(arr,'i') if False else arr+lr('i')+'\tX_REF 1\n';end=label('skipnull')
  body=obj+push(-1)+f'\tEQUALE\n\tIFNZ {end}\n'
  for f in fields:
   if f in [21,22,25] and gid==250:body+=array_values(field(obj,f),'j')
   else:body+=transfer(obj+push(f))
  body+=end+':\n';return loop('i',arr+'\tCALLHLL Array Numof 65538\n',body)
 # Snapshot input fingerprint includes party, reward rates and inventory-cap option.
 b='\t.LOCALASSIGN cursor 0\n'+lr('restore')+'\tIFNZ state_restore\n'+lr('data')+push(0)+'\tCALLHLL Array Realloc 1\nstate_restore:\n'
 for g in [201,202,203,204,206]:b+=transfer('\tPUSHGLOBALPAGE\n'+push(g))
 b+=array_values(glob(253),'i')
 b+=object_loop(250,list(range(28)))+object_loop(230,[3,4])+object_loop(231,[3,4])
 stone=glob(236)+push(0)+'\tX_REF 1\n'+lr('i')+'\tX_REF 1\n'+lr('j')+'\tX_REF 1\n'
 b+=loop('i',push(4),loop('j',push(10),transfer(stone+push(0))+transfer(stone+push(1))))
 b+=array_values(field(glob(196),1),'i')+push(1)+'\tRETURN\n';bridges['KR_SweepState']=b
 # Data validation before the exclusive payout section, no RNG used.
 b=lr('mapId')+cf('KR_SweepAllowed')+'\tIFZ preflight_no\n'+glob(198)+'\tCALLHLL Array Numof 65538\n\tIFNZ preflight_no\n'
 b+=glob(250)+'\tCALLHLL Array Numof 65538\n'+push(8)+'\tNOTE\n\tIFNZ preflight_no\n'
 obj=glob(250)+lr('i')+'\tX_REF 1\n'
 body=obj+push(-1)+'\tEQUALE\n\tIFNZ preflight_no\n'
 # Unrecruited characters legitimately have level zero; only payout party must be >=1.
 for fld,maximum in [(1,99),(4,100000000),(5,99999),(6,999999)]:
  body+=field(obj,fld)+push(0)+'\tLT\n\tIFNZ preflight_no\n'+field(obj,fld)+push(maximum)+'\tGT\n\tIFNZ preflight_no\n'
 for fld in [21,22,25]:
  body+=field(obj,fld)+push(-1)+'\tEQUALE\n\tIFNZ preflight_no\n'
 b+=loop('i',glob(250)+'\tCALLHLL Array Numof 65538\n',body)
 b+=loop('i',cf('L_Party::GetNumberOfPersons'),lr('i')+push(0)+cf('KR_NoticeStat')+push(1)+'\tLT\n\tIFNZ preflight_no\n')
 b+=glob(230)+'\tCALLHLL Array Numof 65538\n'+push(6)+'\tLT\n\tIFNZ preflight_no\n'+field(glob(196),1)+'\tCALLHLL Array Numof 1\n'+push(99)+'\tLT\n\tIFNZ preflight_no\n'
 b+=loop('i',push(6),glob(230)+lr('i')+'\tX_REF 1\n'+push(-1)+'\tEQUALE\n\tIFNZ preflight_no\n')
 arr=field(glob(236),0)
 b+=arr+'\tX_A_SIZE\n'+push(4)+'\tLT\n\tIFNZ preflight_no\n'
 row=arr+lr('i')+'\tX_REF 1\n'
 b+=loop('i',push(4),row+'\tX_A_SIZE\n'+push(10)+'\tLT\n\tIFNZ preflight_no\n'+loop('j',push(10),row+lr('j')+'\tX_REF 1\n'+push(-1)+'\tEQUALE\n\tIFNZ preflight_no\n'))
 b+=loop('rank',push(7),'\t.LOCALASSIGN count 0\n'+loop('i',glob(231)+'\tCALLHLL Array Numof 65538\n',glob(231)+lr('i')+'\tX_REF 1\n'+push(-1)+'\tEQUALE\n\tIFNZ preflight_no\n'+field(glob(231)+lr('i')+'\tX_REF 1\n',1)+lr('rank')+push(1)+'\tADD\n\tNOTE\n\tIFNZ equip_other\n\t.LOCALINC2 count\nequip_other:\n')+lr('count')+'\tIFZ preflight_no\n')
 b+=push(1)+'\tRETURN\npreflight_no:\n'+push(0)+'\tRETURN\n';bridges['KR_SweepPreflight']=b
 # Native Array.Shuffle uses an HLL RNG, so replace only the sweep-scoped selection.
 obj=glob(231)+lr('i')+'\tX_REF 1\n'
 match=field(obj,1)+lr('rank')+'\tNOTE\n'
 b='\t.LOCALASSIGN count 0\n'+loop('i',glob(231)+'\tCALLHLL Array Numof 65538\n',match+'\tIFNZ equip_count_next\n\t.LOCALINC2 count\nequip_count_next:\n')
 b+=lr('count')+'\tIFZ equip_none\n'+assign(3,lr('count')+cf('KR_SweepRand'))
 b+=loop('i',glob(231)+'\tCALLHLL Array Numof 65538\n',match+'\tIFNZ equip_pick_next\n\t.LOCALDEC2 pick\n'+lr('pick')+'\tIFNZ equip_pick_next\n'+obj+'\tX_DUP 1\n\tSP_INC\n\tRETURN\nequip_pick_next:\n')
 b+='equip_none:\n'+push(-1)+'\tRETURN\n';bridges['KR_SweepEquip']=b
 # Walk the same scalar layout to report actual money/item deltas, not expected rewards.
 def text_append(expr):return '\tPUSHLOCALPAGE\n'+push(5)+lr('text')+'\tA_REF\n'+expr+'\tS_ADD\n\tS_ASSIGN\n\tPOP\n'
 b='\t.S_LOCALASSIGN text ""\n\t.LOCALASSIGN total 0\n'+assign(3,push(5)+glob(253)+'\tCALLHLL Array Numof 1\n\tADD\n')
 obj=glob(250)+lr('i')+'\tX_REF 1\n';body=obj+push(-1)+'\tEQUALE\n\tIFNZ report_ability_next\n'
 for fld in range(28):
  if fld in [21,22,25]:body+='\tPUSHLOCALPAGE\n'+push(3)+field(obj,fld)+'\tCALLHLL Array Numof 1\n\tPLUSA\n\tPOP\n'
  else:
   if fld==6:body+='\tPUSHLOCALPAGE\n'+push(6)+field(obj,6)+lr('before')+lr('cursor')+'\tX_REF 1\n\tSUB\n\tPLUSA\n\tPOP\n'
   body+='\t.LOCALINC2 cursor\n'
 body+='report_ability_next:\n';b+=loop('i',glob(250)+'\tCALLHLL Array Numof 65538\n',body)
 b+=text_append(S('달조각 +%d\n')+lr('total')+'\tS_MOD 2\n')
 for domain,gid in [(0,230),(1,231)]:
  obj=glob(gid)+lr('i')+'\tX_REF 1\n';nxt=label('report_next')
  body=obj+push(-1)+f'\tEQUALE\n\tIFNZ {nxt}\n'+assign(4,field(obj,4)+lr('before')+lr('cursor')+push(1)+'\tADD\n\tX_REF 1\n\tSUB\n')+'\t.LOCALPLUSA cursor 2\n'+lr('delta')+push(0)+f'\tLTE\n\tIFNZ {nxt}\n'
  body+=text_append(S('%s +%d\n')+push(domain)+lr('i')+cf('KR_SweepItemName')+'\tS_MOD 4\n'+lr('delta')+'\tS_MOD 2\n')+nxt+':\n'
  b+=loop('i',glob(gid)+'\tCALLHLL Array Numof 65538\n',body)
 stone=glob(236)+push(0)+'\tX_REF 1\n'+lr('i')+'\tX_REF 1\n'+lr('j')+'\tX_REF 1\n'
 body=assign(4,field(stone,1)+lr('before')+lr('cursor')+push(1)+'\tADD\n\tX_REF 1\n\tSUB\n')+'\t.LOCALPLUSA cursor 2\n'+lr('delta')+push(0)+'\tLTE\n\tIFNZ report_stone_next\n'
 body+=text_append(S('%s +%d\n')+push(2)+lr('i')+push(10)+'\tMUL\n'+lr('j')+'\tADD\n'+cf('KR_SweepItemName')+'\tS_MOD 4\n'+lr('delta')+'\tS_MOD 2\n')+'report_stone_next:\n'
 b+=loop('i',push(4),loop('j',push(10),body))+text_append(S('소지 한도를 넘은 보상은 제외됩니다.'))+lr('text')+'\tA_REF\n\tRETURN\n';bridges['KR_SweepItems']=b
 b=lr('domain')+'\tIFNZ name_not_consume\n'+cm(glob(230)+lr('index')+'\tX_REF 1\n',26668)+'\tRETURN\nname_not_consume:\n'+lr('domain')+push(1)+'\tNOTE\n\tIFNZ name_stone\n'+cm(glob(231)+lr('index')+'\tX_REF 1\n',26756)+'\tRETURN\nname_stone:\n'
 for color,t in enumerate(['적색','청색','백색','흑색']):
  b+=lr('index')+push(10)+'\tDIV\n'+push(color)+f'\tNOTE\n\tIFNZ name_color_{color}\n'+S(f'{t} 요소석(%d등급)')+lr('index')+push(10)+'\tMOD\n'+push(1)+'\tADD\n\tS_MOD 2\n\tRETURN\n'+f'name_color_{color}:\n'
 b+=S('요소석')+'\tRETURN\n';bridges['KR_SweepItemName']=b
 # Timed original message dialog. The exclusive transaction has ended before this runs.
 native=get(27776);body=native[native.index('\n',native.index('FUNC 27776'))+1:];body=re.sub(r'^ENDFUNC .*\n?','',body,flags=re.M)
 body=re.sub(r'PUSHLOCALPAGE\n\tPUSH (\d+)',lambda m:'PUSHLOCALPAGE\n\tPUSH '+str(int(m[1])+1),body)
 body=body.replace('PUSHSTRUCTPAGE','\t.LOCALREF dlg'.strip())
 body=assign(6,cf('KR_Time'))+body
 needle='0x5944fa:\n';assert needle in body
 body=body.replace(needle,needle+cf('KR_Time')+lr('started')+'\tSUB\n'+push(6000)+'\tGTE\n\tIFNZ 0x5945b4\n')
 bridges['KR_SweepTimedRun']=body
 bridges['KR_SweepReport']=assign(2,cm(flags,26512))+cm(flags,26514,push(1),1)+'\t.LOCALCREATE dlg C_MessageDialog\n'+lr('dlg')+lr('txt')+'\tA_REF\n'+push(150)+push(0)+cf('KR_SweepTimedRun')+cm(flags,26514,lr('previousLock'),1)+'\tRETURN\n'
 for n,i in ids.items():
  p=O/f'jaf_{i}.jam';cmd('ain','dump','--function',n,'-o',p,stage)
  s=clean(native_lower(p.read_text(encoding='utf8')),n)
  s=s.replace('\tI_STRING\n','\tS_PUSH "%d"\n\tX_MOV 2 1\n\tS_MOD 2\n')
  if n in bridges:s=fn(i,n,bridges[n])
  patches[i]=s
 # Only these original paths receive scope-gated hooks.
 patches[6462]=begin(get(6462),cf('KR_SweepActive')+'\tIFZ rng_native\n'+lr('最大値')+cf('KR_SweepRand')+'\tRETURN\nrng_native:\n')
 patches[27302]=begin(get(27302),cf('KR_SweepActive')+'\tIFZ exp_native\n\tPUSHSTRUCTPAGE\n'+lr('nExpAdd')+cf('KR_SweepAddExp')+'\tRETURN\nexp_native:\n')
 patches[27194]=begin(get(27194),cf('KR_SweepActive')+'\tIFZ treasure_native\n\tRETURN\ntreasure_native:\n')
 patches[26780]=begin(get(26780),cf('KR_SweepActive')+'\tIFZ equip_native\n'+lr('nRank')+cf('KR_SweepEquip')+'\tRETURN\nequip_native:\n')
 # Active RNG is transient, cannot survive native load/reset.
 patches[31856]=begin(get(31856),cf('KR_SweepActive')+'\tIFZ sweep_reset_done\n'+push(99)+push(20260916)+cf('KR_Poke')+'sweep_reset_done:\n')
 for i,mid,cb in [(29817,29827,'KR_GetSweep'),(29818,29828,'KR_SetSweep')]:
  patches[i]=begin(get(i),'\tPUSHSTRUCTPAGE\n'+push(mid)+S('KR_CheatSweep')+push(-1)+push(ids[cb])+'\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n')
 # Bind the new native button using an existing, verified IParts callback sequence.
 s=get(28731);at=s.index('\tS_PUSH "ボタン_アイテム"',s.index('\tS_PUSH "ボタン_アイテム"')+1);start=s.rfind('\tPUSHSTRUCTPAGE\n\tPUSH 0\n',0,at)
 end=s.index('\t.LOCALDELETE ',at);end=s.index('\n',end)+1
 block=s[start:end];assert 'DG_NEW_FROM_METHOD' in block,block
 block=block.replace('"ボタン_アイテム"','"KR_SweepButton"')
 block=re.sub(r'\tPUSHSTRUCTPAGE\n\tPUSH (316\d+)\n\tDG_NEW_FROM_METHOD',lambda m:push(-1)+push(ids['KR_SweepClick'])+'\tDG_NEW_FROM_METHOD',block)
 pos=s.rfind('\tRETURN');patches[28731]=s[:pos]+block+s[pos:]
 patches[28642]=begin(get(28642),'\tPUSHSTRUCTPAGE\n\tPUSHSTRUCTPAGE\n'+cf('KR_SweepSceneOK')+cf('KR_SweepVisible'))
 s=get(28637);needle='\t.LOCALREF clickType\n\tPUSH 10000\n';assert s.count(needle)==1
 branch='\tPUSHSTRUCTPAGE\n'+push(0)+cf('KR_SweepVisible')+lr('clickType')+push(2026091601)+'\tNOTE\n\tIFNZ sweep_regular_click\n\tPUSHSTRUCTPAGE\n'+cf('KR_SweepExecute')+'\tIFNZ 0x60faa4\n\tJUMP 0x60fa9e\nsweep_regular_click:\n'
 patches[28637]=s.replace(needle,branch+needle)
 jam=O/'sweep_patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain'
 cmd('ain','edit','--jam',jam,'-o',out,stage);cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json')
 changed=[]
 for a,b in zip(M['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y,a['index']
  if aa!=bb:changed.append(a['index'])
 nested={int(i) for fid in patches if fid<len(M['functions']) for i in re.findall(r'^FUNC (\d+)',get(fid),re.M)}
 assert set(changed)=={i for i in patches if i<len(M['functions'])}|nested,changed
 for k in M:
  if k!='functions':assert M[k]==nm[k],k
 new=unpack(out.read_bytes());assert old[16:16+size]==new[16:16+size]
 assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
 assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
 for i in patches:cmd('ain','dump','--function',NAMES.get(i) or next(n for n,ix in ids.items() if ix==i),'-o',O/f'built_{i}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_sweep_raw_code.jam',out)
 nat=audit(out,O/'candidate_meta.json',O/'native_sweep_raw_code.jam',rt/'NightRemaster.exe');savej(O/'native_opcode_audit.json',nat);assert nat['all_active_opcodes_supported']
 return dict(patched_existing=changed,added_functions=ids,original_CODE_STR0_MSG1_preserved=True,save_schema_unchanged=True)

def main():
 ptr=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(ptr['runtime'])
 assert sha(rt/'NightRemaster.ain')=='f3a82e856b75cbb10b455cf3575f10964c0a7218ef86c1a601c3da66404fd538'
 savej(O/'source_pointer.json',ptr);before={n:sha(rt/n) for n in FILES}
 pa=build_pact(rt);ain=build_ain(rt)
 savej(O/'build_evidence.json',dict(status='SWEEP_STAGED_NOT_VERIFIED',source_pointer=ptr,source_files=before,files={n:sha(O/n) for n in FILES},AIN=ain,PACT=pa,EX_unchanged_sha256=sha(rt/'NightRemasterEX.ex'),translator_model='Codex internal',native_gameplay_verified=False))
 print('SWEEP CANDIDATE BUILT')
if __name__=='__main__':main()
