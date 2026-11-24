"""Native recommendation UI; append-only candidate, never installs or starts the game."""
from pathlib import Path
import copy,json,re,struct,shutil
from cheat_support_20260915 import R,sha,savej,read_meta,cmd
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,si,ss,setlist,rename,txt_info,encode
from build_mod_tab_20260915 import add,coords
from build_route_perf_20260915 import symbol
from build_instant_loot_20260915 import clean,begin
from build_dungeon_sweep_20260916 import S,push,cf,lr,cm,assign,field
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit

O=R/'staging/autoequip_20260917'; HERE=Path(__file__).resolve().parent
EXPECTED='75d721bc318296fa1e2f4d1e4a86bd220c5d1c7977d753473bf12962b4711b07'
def globalref(n):return f'\t.GLOBALREF {n}\n'
def loop(var,limit,body,tag):
 return f'\t.LOCALASSIGN {var} 0\n{tag}_loop:\n'+lr(var)+limit+f'\tGTE\n\tIFNZ {tag}_end\n'+body+f'\t.LOCALINC2 {var}\n\tJUMP {tag}_loop\n{tag}_end:\n'
def writefield(obj,ix,expr):return obj+push(ix)+expr+'\tX_ASSIGN 1\n\tPOP\n'
def visibility(owner,slot,button):
 b=owner+push(-1)+'\tEQUALE\n\tIFNZ visible_done\n'
 b+=owner+push(slot)+'\tX_REF 2\n\tPOP\n'+push(-1)+'\tEQUALE\n\tIFNZ visible_done\n'
 b+=owner+push(slot)+'\tX_REF 2\n\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n'+push(0)+'\tX_REF 1\n\tX_MOV 2 1\n'+push(7)+'\tADD\n\tX_REF 1\n'+S(button)+'\tCALLMETHOD 1\n'
 b+='\tX_DUP 2\n\tPOP\n'+push(-1)+'\tEQUALE\n\tIFNZ visible_release\n\tX_DUP 2\n\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n'+push(0)+'\tX_REF 1\n\tX_MOV 2 1\n'+push(60)+'\tADD\n\tX_REF 1\n'+lr('show')+'\tCALLMETHOD 1\nvisible_release:\n\tPOP\n\tDELETE\nvisible_done:\n\tRETURN\n'
 return b.replace('visible_',button+'_visible_')

def pact(rt):
 source=rt/'NightRemasterPact.afa';arc=read_afa3(source);docs={}
 for i in [153,154,185]:
  e=arc.entries[i]
  with source.open('rb') as f:f.seek(e.absolute_offset);raw=f.read(e.size)
  out=O/f'original_pact_{i}.pactex';out.write_bytes(raw);docs[i]=ex.decode_ex(out)
 d=docs[185];root=d.blocks[2].payload.children[0];toggle=copy.deepcopy(part(d,'KR_CheatTrap'));rename(toggle,'KR_AutoEquipToggle')
 setlist(toggle,'座標',[363,590,250]);ss(child(toggle,'種類別情報'),'テキスト','    자동 장착·요소석 추천',True);add(root,toggle)
 import build_mod_tab_20260915 as mt
 mt.ORDER=copy.deepcopy(val(root,'子パーツリスト').items[0])
 def button(doc,parent,rootname,buttonname,label,x,y,width):
  group=mt.clean_group(part(d,'KR_ModBattle'),rootname,x,y);si(group,'表示',0);si(group,'オンカーソル透過',1)
  rect=child(child(group,'種類別情報'),'通常状態')
  for n,p in [('左上',[0,0]),('右上',[width,0]),('左下',[0,42]),('右下',[width,42])]:setlist(rect,n,p)
  template=copy.deepcopy(part(d,'KR_ModTab'));rename(template,buttonname);setlist(template,'座標',[0,0,1]);si(template,'表示',1)
  ci=child(template,'種類別情報');ss(ci,'ＣＧ名','シス／コンフィグ／タブ');ss(ci,'テキスト','');si(ci,'有効',1);setlist(template,'拡大縮小',[width/192,1]);setlist(ci,'サイズ',[192,42])
  from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
  from audit_dynamic_ui_20260915 import ENC
  _,faces=parse_fnl_font(rt/'NightRemasterFont.fnl',3);face,den,_=select_fnl_face(faces,21)
  measure=WidthMeasurer(face,den,{c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()},0,0,0)
  labelwidth=measure.measure(label,True)['lines'][0]['width_px'];assert labelwidth<=width-12
  text=copy.deepcopy(part(d,'KR_ModSpeedTitle'));rename(text,buttonname+'Label');setlist(text,'座標',[(width-labelwidth)/2,9,2]);si(text,'オンカーソル透過',1)
  tx=txt_info(text);ss(tx,'テキスト',label,True);deco=child(tx,'テキスト装飾');si(deco,'フォントサイズ',21);si(deco,'字間隔',0)
  add(group,template);add(group,text);add(parent,group)
 button(docs[153],part(docs[153],'矩形_アイテム'),'KR_AutoEquipRoot','KR_AutoEquipButton','자동 장착',440,677,192)
 button(docs[154],part(docs[154],'矩形_追加より上'),'KR_AutoStoneRoot','KR_AutoStoneButton','요소석 추천',948,435,138)
 replacements={}
 for i,d in docs.items():
  out=O/f'pact_{i}_autoequip.pactex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));assert ex.decode_ex(out).serialize_payload()==d.serialize_payload();replacements[i]=out
 return dict(changed_entries=[153,154,185],archive=rebuild(source,O/'NightRemasterPact.afa',replacements),raster_font_unchanged=True)

def main():
 O.mkdir(parents=True,exist_ok=True);ptr=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain';assert sha(src)==EXPECTED
 assert sha(Path(ptr['manifest']))==ptr['manifest_sha256'];savej(O/'source_pointer.json',ptr)
 m=read_meta(R/'staging/route_puzzle_20260916/candidate_meta.json');names={};seen={}
 for f in m['functions']:
  n=symbol(m,f['index']);j=seen.get(n,0);seen[n]=j+1;names[f['index']]=n+(f'#{j}' if j else '')
 def get(fid):
  out=O/f'original_{fid}.jam';cmd('ain','dump','--function',names[fid],'-o',out,src);return clean(out.read_text(encoding='utf8'),names[fid])
 # Korean text authored here; only reversible legacy encoding is automated.
 jaf=(HERE/'autoequip_helpers_20260917.jaf').read_text(encoding='utf8');shutil.copy2(HERE/'autoequip_helpers_20260917.jaf',O/'helpers.jaf')
 jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('\uac00'<=c<='\ud7a3' for c in z[0]) else z[0],jaf)
 (O/'helpers_proxy.jaf').write_text(jaf,encoding='utf8');decl=O/'declared.ain';cmd('ain','edit','--jaf',O/'helpers_proxy.jaf','-o',decl,src)
 old=unpack(src.read_bytes());raw=bytearray(unpack(decl.read_bytes()));oldsize=struct.unpack_from('<I',old,12)[0];newsize=struct.unpack_from('<I',raw,12)[0]
 assert old[16:16+oldsize]==raw[16:16+oldsize];struct.pack_into('<I',raw,24+newsize,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};bridges={}
 bridges['KR_AutoCount']=lr('data')+'\tCALLHLL Array Numof 1\n\tRETURN\n'
 bridges['KR_AutoEquipVisible']=visibility(lr('view'),1,'KR_AutoEquipRoot')
 bridges['KR_AutoStoneVisible']=visibility(lr('view'),0,'KR_AutoStoneRoot')
 flags=globalref('Flags');select=globalref('g_MainSelect')
 b=assign(4,cm(flags,26512))+cm(flags,26514,push(1),1)+lr('title')+'\tA_REF\n'+cf('■選択ダイアログ／タイトル設定')+push(2026091602)+cf('■選択ダイアログ／タイプ設定')
 for fld in [6,7]:
  b+=writefield(field(select,fld),1,push(20))+writefield(field(select,fld),4,push(1065353216))
 b+=writefield(field(select,8),1,push(1090519040))+lr('columns')+cf('■選択ダイアログ／横項目数')
 b+=loop('i',lr('options')+'\tCALLHLL Array Numof 12\n',lr('i')+push(1)+'\tADD\n'+lr('options')+lr('i')+'\tX_REF 1\n\tA_REF\n'+S('')+push(0)+cf('■選択ダイアログ／選択肢追加'),'options')
 b+=cf('■選択ダイアログ／クリック制限／全体')+assign(5,push(1)+push(0)+cf('■選択ダイアログ／実行'))+cm(flags,26514,lr('previousLock'),1)+lr('result')+'\tRETURN\n';bridges['KR_AutoMenu']=b
 # Every array gets fresh storage. Neither ref assignment nor shallow SR_ASSIGN is used.
 b=''
 for ix in range(28):
  dst=lr('dst');source=lr('src')
  if ix in [21,22,25]:
   b+=dst+push(ix)+'\tX_DUP 2\n\tX_REF 1\n\tDELETE\n'+field(source,ix)+'\tCALLHLL Array Numof 1\n\tX_A_INIT 0\n\tPOP\n'
   b+=loop('i',field(source,ix)+'\tCALLHLL Array Numof 1\n',field(dst,ix)+lr('i')+field(source,ix)+lr('i')+'\tX_REF 1\n\tX_ASSIGN 1\n\tPOP\n',f'copy_{ix}')
  else:b+=writefield(dst,ix,field(source,ix))
 bridges['KR_AutoCopyAbility']=b+'\tRETURN\n'
 b=lr('pa')+push(-1)+'\tEQUALE\n\tIFNZ invalid\n'
 for ix,minimum in [(21,21),(22,4),(25,0)]:
  b+=field(lr('pa'),ix)+push(-1)+'\tEQUALE\n\tIFNZ invalid\n'+field(lr('pa'),ix)+'\tCALLHLL Array Numof 1\n'+push(minimum)+'\tLT\n\tIFNZ invalid\n'
 b+=field(lr('pa'),22)+'\tCALLHLL Array Numof 1\n'+push(4)+'\tNOTE\n\tIFNZ invalid\n'+push(1)+'\tRETURN\ninvalid:\n'+push(0)+'\tRETURN\n';bridges['KR_AutoValidAbility']=b
 equip=globalref('L_EquipItem::m_data');item=lr('item')
 bridges['KR_AutoItemId']=equip+lr('index')+'\tX_REF 1\n'+push(0)+'\tX_REF 1\n\tRETURN\n'
 b=assign(2,lr('id')+cf('L_EquipItem::At'))+item+push(-1)+'\tEQUALE\n\tIFNZ no_item\n'+item+lr('field')+'\tX_REF 1\n\t.LOCALDELETE item\n\tRETURN\nno_item:\n'+push(-1)+'\tRETURN\n';bridges['KR_AutoItemField']=b
 bridges['KR_AutoItemCount']=assign(2,lr('id')+cf('L_EquipItem::At'))+item+push(-1)+'\tEQUALE\n\tIFNZ count_end\n'+writefield(item,4,lr('count'))+'count_end:\n\t.LOCALDELETE item\n\tRETURN\n'
 bridges['KR_AutoItemName']=lr('id')+'\tIFZ empty_name\n'+assign(1,lr('id')+cf('L_EquipItem::At'))+item+push(-1)+'\tEQUALE\n\tIFNZ empty_name\n'+cm(item,26756)+'\t.LOCALDELETE item\n\tRETURN\nempty_name:\n\t.LOCALDELETE item\n'+S('없음')+'\tRETURN\n'
 bridges['KR_AutoW']=lr('weapon')+push(-1)+'\tEQUALE\n\tIFNZ no_weapon\n'+lr('weapon')+lr('field')+'\tX_REF 1\n\tRETURN\nno_weapon:\n'+push(0)+'\tRETURN\n'
 bridges['KR_AutoWName']=cm(lr('weapon'),26810)+'\tRETURN\n'
 stone=field(globalref('L_ElementStone::m_data'),0)+lr('stone')+push(10)+'\tDIV\n\tX_REF 1\n'+lr('stone')+push(10)+'\tMOD\n\tX_REF 1\n'
 bridges['KR_AutoStock']=field(stone,1)+'\tRETURN\n'
 bridges['KR_AutoCraftRoom']=assign(0,cm(flags,26481))+cm(lr('list'),26717)+'\tNOT\n\t.LOCALDELETE list\n\tRETURN\n'
 a=field(lr('weapon'),27)
 bridges['KR_AutoWeaponSkill']='\t.LOCALASSIGN count 0\n'+loop('i',a+'\tCALLHLL Array Numof 1\n',a+lr('i')+'\tX_REF 1\n'+lr('id')+'\tNOTE\n\tIFNZ skill_next\n\t.LOCALINC2 count\nskill_next:\n','wskills')+lr('count')+'\tRETURN\n'
 b=''
 for kind,method in enumerate([27325,27326,27328,27327,27329]):
  b+=lr('kind')+push(kind)+f'\tNOTE\n\tIFNZ combat_next_{kind}\n'+assign(2,cm(lr('probe'),method))+cm(lr('value'),27297)+'\t.LOCALDELETE value\n\tRETURN\n'+f'combat_next_{kind}:\n'
 bridges['KR_AutoCombatValue']=b+push(0)+'\tRETURN\n'
 patches={}
 for name,fid in ids.items():
  out=O/f'jaf_{fid}.jam';cmd('ain','dump','--function',name,'-o',out,decl);s=clean(native_lower(out.read_text(encoding='utf8')),name)
  if name in bridges:s=f'FUNC {fid}\n'+bridges[name]+f'ENDFUNC {name}\n'
  else:
   # The compiler cannot bind a returned ref initializer. Replace explicit markers by
   # an owned native result assignment; its normal local teardown releases it once.
   ff=dm['functions'][fid];variables=ff['arguments']+ff['variables']
   for marker,native,local in [('KR_AutoBindAbilityMarker','LAbility::At','live'),('KR_AutoBindWeaponMarker','L_Weapon::At','current' if name=='KR_AutoStoneRun' else 'weapon')]:
    needle=cf(marker)
    if needle not in s:continue
    ix=next(i for i,v in enumerate(variables) if v['name']==local)
    s=s.replace(needle,cf(native)+'\tPUSHLOCALPAGE\n'+push(ix)+'\tX_MOV 3 2\n\tX_ASSIGN 1\n\tPOP\n')
   if name=='KR_AutoStoneRun':
    # JAF counts ref int as one source argument, but Sys43's ABI needs two words.
    pat=r'(\tPUSH 28586\n(?:(?!\tCALLMETHOD).)*?)\tCALLMETHOD 3\n'
    s,count=re.subn(pat,r'\1\tCALLMETHOD 4\n',s,flags=re.S);assert count==1
  patches[fid]=s
 # Getter/setter native mod-tab delegates.
 for fid,method,callback in [(29817,29827,'KR_GetAutoEquip'),(29818,29828,'KR_SetAutoEquip')]:
  patches[fid]=begin(get(fid),'\tPUSHSTRUCTPAGE\n'+push(method)+S('KR_AutoEquipToggle')+push(-1)+push(ids[callback])+'\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n')
 def bind(fid,original_button,new_button,callback,slot):
  s=get(fid);needle=S(original_button);at=0;block=None
  while True:
   at=s.find(needle,at)
   if at<0:break
   start=s.rfind('\tPUSHSTRUCTPAGE\n'+push(slot)+'\tX_REF 2\n',0,at)
   end=s.index('\t.LOCALDELETE ',at);end=s.index('\n',end)+1
   candidate=s[start:end]
   if '\tPUSH 258\n' in candidate and 'DG_NEW_FROM_METHOD' in candidate:block=candidate;break
   at+=len(needle)
  assert block,fid
  block=block.replace(needle,S(new_button));block=re.sub(r'\tPUSHSTRUCTPAGE\n\tPUSH (\d+)\n\tDG_NEW_FROM_METHOD',lambda z:push(-1)+push(ids[callback])+'\tDG_NEW_FROM_METHOD',block)
  at=s.rfind('\tRETURN');patches[fid]=s[:at]+block+s[at:]
 bind(28430,'構築_ページ切り替え前','KR_AutoEquipButton','KR_AutoEquipClick',1)
 bind(28504,'ボタン_武器加工','KR_AutoStoneButton','KR_AutoStoneClick',0)
 s=get(28003);needle='0x5ac23c:\n';assert s.count(needle)==1;s=s.replace(needle,needle+lr('statusView')+cf('KR_GetAutoEquip')+cf('KR_AutoEquipVisible'))
 needle=lr('clickType')+push(0)+'\tLTE\n';assert s.count(needle)==1
 branch=lr('clickType')+push(2026091701)+'\tNOTE\n\tIFNZ autoequip_regular\n'+lr('charaNo')+cf('KR_AutoGearRun')+'\tIFZ autoequip_done\n'+lr('statusView')+lr('charaNo')+lr('isDungeon')+cf('C_Status::UpdateViewAfterEquip')+'autoequip_done:\n\tJUMP 0x5ac23c\nautoequip_regular:\n'
 patches[28003]=s.replace(needle,branch+needle)
 s=get(28585);needle='0x6079aa:\n';assert s.count(needle)==1
 view='\t.STRUCTREF C_SceneSubWeapon m_WeaponView\n'
 s=s.replace(needle,needle+view+cf('KR_GetAutoEquip')+lr('bTutorial')+'\tNOT\n\tAND\n'+cf('KR_AutoStoneVisible'))
 needle='\tPUSHSTRUCTPAGE\n'+push(28584)+lr('clickType')+'\tCALLMETHOD 1\n';assert s.count(needle)==1
 b=view+push(0)+cf('KR_AutoStoneVisible')+lr('clickType')+push(701)+'\tNOTE\n\tIFNZ autostone_regular\n'+lr('bTutorial')+'\tIFNZ 0x6079aa\n'
 b+='\tPUSHSTRUCTPAGE\n'+view+lr('stoneSetList')+'\tPUSHLOCALPAGE\n'+push(1)+cf('KR_AutoStoneRun')+'\tIFNZ 0x608056\n\tJUMP 0x6079aa\nautostone_regular:\n'
 patches[28585]=s.replace(needle,b+needle)
 jam=O/'autoequip_patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,decl)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(z);aa=x.pop('address');zz=y.pop('address');assert x==y,a['index']
  if aa!=zz:changed.append(a['index'])
 nested={int(i) for fid in patches if fid<len(m['functions']) for i in re.findall(r'^FUNC (\d+)',get(fid),re.M)}
 assert set(changed)=={i for i in patches if i<len(m['functions'])}|nested,changed
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 after=unpack(out.read_bytes());assert old[16:16+oldsize]==after[16:16+oldsize];assert strings(after)[2][:len(strings(old)[2])]==strings(old)[2];assert old[old.index(b'MSG1'):old.index(b'SWI0')]==after[after.index(b'MSG1'):after.index(b'SWI0')]
 for fid in patches:cmd('ain','dump','--function',names.get(fid,nm['functions'][fid]['name']),'-o',O/f'built_{fid}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);na=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');savej(O/'native_opcode_audit.json',na);assert na['all_active_opcodes_supported']
 pe=pact(rt)
 ev=dict(status='AUTOEQUIP_STAGED_UNVERIFIED',source_pointer=ptr,source_files={n:sha(rt/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},files={n:sha(O/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},
  unchanged_files={n:sha(rt/n) for n in ['NightRemasterEX.ex','NightRemaster.exe','NightRemasterFont.fnl']},AIN=dict(patched_existing=changed,added_functions=ids,serialized_metadata_exact=True,old_CODE_STR0_MSG1_exact=True),PACT=pe,
  translator_model='Codex internal',native_gameplay_verified=False,profiles=['균형','공격','생존','유틸리티'],live_state_mutated_during_search=False,slot_locks_scope='current operation',stock_scope='unassigned inventory plus this character/selection only')
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
