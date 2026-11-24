"""Optional ordinary-enemy contact rewards. Stage only; never edit a live runtime."""
from pathlib import Path
import json,re,copy,struct,shutil
from build_remaster_multiplier_20260915 import cmd,read_meta,fn,ex,read_afa3,rebuild,part,child,val,allparts,rename,setlist,ss,si,txt_info
from build_mod_tab_20260915 import add,name,coords
from build_route_perf_20260915 import symbol
from cheat_support_20260915 import R,sha,savej
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit

O=Path('instant_loot_20260915');BASE=Path('mod_tab_20260915');FILES=['NightRemaster.ain','NightRemasterPact.afa']
SILENT=(2026091500,2026091501)
def begin(s,x):return re.sub(r'(^FUNC \d+\n)',lambda m:m[0]+x,s,count=1,flags=re.M)
def mc(local,mid):return f'\t.LOCALREF {local}\n\tPUSH {mid}\n\tCALLMETHOD 0\n'
def clean(s,n):
 s=re.sub(r'^EOF .*\n?','',s,flags=re.M)
 if 'ENDFUNC ' not in s:s+='\nENDFUNC '+n+'\n'
 return s

def build_ain(rt):
 src=rt/'NightRemaster.ain';m=read_meta(BASE/'candidate_meta.json');seen={};names={}
 for f in m['functions']:
  n=symbol(m,f['index']);c=seen.get(n,0);seen[n]=c+1;names[f['index']]=n+(f'#{c}' if c else '')
 def get(i):
  p=O/f'original_{i}.jam';cmd('ain','dump','--function',names[i],'-o',p,src);return clean(p.read_text(encoding='utf8'),names[i])
 stage=O/'helpers_declared.ain';cmd('ain','edit','--jaf',O/'helpers.jaf','-o',stage,src)
 cmd('ain','dump','-j','-o',O/'declared_meta.json',stage);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]}
 # Alice JAF writer repoints NULL: retain its cumulative original entry address.
 old=unpack(src.read_bytes());raw=bytearray(unpack(stage.read_bytes()));size=struct.unpack_from('<I',old,12)[0];nsize=struct.unpack_from('<I',raw,12)[0]
 assert raw[16:16+size]==old[16:16+size] and raw[16+nsize:20+nsize]==b'FUNC'
 struct.pack_into('<I',raw,24+nsize,m['functions'][0]['address']);stage.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 patches={};bridge={}
 bridge['KR_LootEligible']='\tCALLFUNC KR_GetLoot\n\tIFZ loot_ineligible\n\t.LOCALREF cell\n\tPUSH -1\n\tEQUALE\n\tIFNZ loot_ineligible\n\tCALLFUNC KR_FirstBattleTutorial\n\tIFNZ loot_ineligible\n'+mc('cell',27005)+'\tPUSH 3\n\tNOTE\n\tIFNZ loot_ineligible\n'+mc('cell',27023)+'\tIFNZ loot_ineligible\n'+mc('cell',27008)+'\tPUSH 0\n\tEQUALE\n\tIFNZ loot_eligible\n'+mc('cell',27008)+'\tPUSH 1\n\tNOTE\n\tIFNZ loot_ineligible\nloot_eligible:\n\tPUSH 1\n\tRETURN\nloot_ineligible:\n\tPUSH 0\n\tRETURN\n'
 bridge['KR_LootRemove']='\t.LOCALREF cell\n\tPUSH 27025\n\tPUSH 1\n\tCALLMETHOD 1\n\tRETURN\n'
 # At/AbilityAt return owned references. Borrow for methods, DELETE exactly once.
 bridge['KR_LootMonsterById']='\t.LOCALREF id\n\tCALLFUNC L_MonsterManager::At\n\tX_DUP 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ loot_missing_monster\n\t.LOCALREF add\n\tIFZ loot_monster_done\n\tX_DUP 1\n\t.LOCALREF gameLevel\n\tCALLFUNC KR_AddLootMonster\nloot_monster_done:\n\tDELETE\n\tPUSH 1\n\tRETURN\nloot_missing_monster:\n\tDELETE\n\tPUSH 0\n\tRETURN\n'
 bridge['KR_LootHasLivingParty']='\t.LOCALASSIGN i 0\nloot_party_loop:\n\t.LOCALREF i\n\tPUSH 3\n\tGTE\n\tIFNZ loot_party_none\n\t.LOCALREF i\n\tCALLFUNC L_Party::AbilityAt\n\tX_DUP 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ loot_party_null\n\tX_DUP 1\n\tPUSH 27301\n\tCALLMETHOD 0\n\tX_MOV 2 1\n\tDELETE\n\tIFNZ loot_party_yes\n\tJUMP loot_party_next\nloot_party_null:\n\tDELETE\nloot_party_next:\n\t.LOCALINC2 i\n\tJUMP loot_party_loop\nloot_party_yes:\n\tPUSH 1\n\tRETURN\nloot_party_none:\n\tPUSH 0\n\tRETURN\n'
 # Retain compiled difficulty branches, initialize fields from native getters.
 for n,i in ids.items():
  p=O/f'jaf_{i}.jam';cmd('ain','dump','--function',n,'-o',p,stage);s=clean(native_lower(p.read_text(encoding='utf8')),n)
  if n=='KR_AddLootMonster':
   # JAF initializes these four locals to0 before the difficulty branches.
   for var,ix,mid in [('level',2,26158),('exp',3,26173),('training',4,26176),('money',5,26179)]:
    needle=f'\t.LOCALASSIGN {var} 0\n';assert s.count(needle)==1,(var,s)
    s=s.replace(needle,f'\tPUSHLOCALPAGE\n\tPUSH {ix}\n'+mc('pm',mid)+'\tX_ASSIGN 1\n\tPOP\n')
   pos=s.rfind('\tRETURN');assert pos>=0
   s=s[:pos]+mc('pm',26149)+''.join(f'\t.LOCALREF {v}\n' for v in ['level','exp','training','money'])+'\tCALLFUNC L_BattleIncome::AddIncome\n\tPOP\n'+s[pos:]
  if n in bridge:s=fn(i,n,bridge[n])
  patches[i]=s
 # Configuration callback belongs only to native Mods page185.
 for i,mode,mid in [(29817,'Get',29827),(29818,'Set',29828)]:
  s=get(i)
  if mode=='Get':
   body=f'\tPUSHSTRUCTPAGE\n\tPUSH {mid}\n\tS_PUSH "KR_CheatLoot"\n\tPUSH -1\n\tPUSH {ids["KR_GetLoot"]}\n\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n'
  else:
   qid=next(ix for ix,n in names.items() if n=='KR_SetQuick')
   binding=f'\tPUSHSTRUCTPAGE\n\tPUSH 29828\n\tS_PUSH "KR_CheatQuick"\n\tPUSH -1\n\tPUSH {qid}\n\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n';assert s.count(binding)==1;s=s.replace(binding,'')
   body=''
   for key in ['KR_CheatQuick','KR_CheatLoot']:
    body+='\t.STRUCTREF C_ConfigView m_ActName\n\tA_REF\n'+f'\tS_PUSH "{key}"\n\tCALLFUNC AFL_Activity_IsExistPartsByName\n\tIFZ loot_pair_missing\n'
   for key in ['KR_CheatQuick','KR_CheatLoot']:
    body+='\t.STRUCTREF C_ConfigView m_ActName\n\tA_REF\n'+f'\tS_PUSH "{key}"\n\tCALLFUNC AFL_Activity_GetPartsNumber\n\tCALLFUNC Ｐ＿チェックボックス＿チェック状態取得\n'
   body+='\tCALLFUNC KR_SetBattleMode\n'
   # Synchronize both widgets immediately; do not depend on callback order or
   # allow a second pass to interpret the stale two-checked state as another click.
   for key,getter in [('KR_CheatQuick','KR_GetQuick'),('KR_CheatLoot','KR_GetLoot')]:
    body+='\t.STRUCTREF C_ConfigView m_ActName\n\tA_REF\n'+f'\tS_PUSH "{key}"\n\tCALLFUNC AFL_Activity_GetPartsNumber\n\tCALLFUNC {getter}\n\tCALLFUNC Ｐ＿チェックボックス＿チェック状態設定\n'
   body+='loot_pair_missing:\n'
  patches[i]=begin(s,body)
 # Passive checkbox synchronization must not erase flag92=2 when Quick is false.
 qid=next(i for i,n in names.items() if n=='KR_SetQuick');patches[qid]=begin(get(qid),'\t.LOCALREF value\n\tCALLFUNC KR_GetQuick\n\tEQUALE\n\tIFZ loot_quick_changed\n\tRETURN\nloot_quick_changed:\n')
 # Own collision hook: after native seen/nonremoved checks, before danger avoidance.
 s=get(28664);needle='\tCALLFUNC KR_GetTrap\n';assert s.count(needle)==1
 body='\t.LOCALREF cell\n\t.GLOBALREF Flags\n\tPUSH 26556\n\tCALLMETHOD 0\n\tCALLFUNC KR_TryInstantLoot\n\tIFZ loot_contact_continue\n\t.STRUCTREF C_SceneDungeon m_DungeonView\n\tPUSH 28763\n\t.LOCALREF lx\n\t.LOCALREF ly\n\tCALLMETHOD 2\n\tPUSH 0\n\tRETURN\nloot_contact_continue:\n'
 patches[28664]=s.replace(needle,body+needle)
 # Native reward arithmetic is unchanged. Exact sentinel only suppresses UI.
 s=get(26258);needle='\t.LOCALREF nDungeonType\n\tPUSH 1\n\tEQUALE\n\tIFNZ 0x5335f8\n';assert s.count(needle)==1
 s=s.replace(needle,needle+'\t.LOCALREF nDungeonType\n\tPUSH 2026091501\n\tEQUALE\n\tIFNZ 0x5335f8\n')
 start=s.index('\tPUSHLOCALPAGE\n\tPUSH 25\n\tNEW C_BattleResultView');end=s.index('\t.LOCALASSIGN i#7 0\n',start)
 block=s[start:end];(O/'native_resultview_region.jam').write_text(block,encoding='utf8')
 s=s[:start]+'\t.LOCALREF nDungeonType\n\tCALLFUNC KR_IsSilentLoot\n\tIFNZ loot_skip_result_view\n'+block+'loot_skip_result_view:\n'+s[end:]
 needle='\tPUSH 0\n\tX_REF 1\n\tPUSH 1\n\tCALLMETHOD 2\n';assert s.count(needle)==1
 s=s.replace(needle,'\tPUSH 0\n\tX_REF 1\n\t.LOCALREF nDungeonType\n\tCALLFUNC KR_IsSilentLoot\n\tNOT\n\tCALLMETHOD 2\n');patches[26258]=s
 jam=O/'instant_loot_patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain'
 cmd('ain','edit','--jam',jam,'-o',out,stage);cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json')
 changed=[]
 for a,b in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(b);aa=x.pop('address');bb=y.pop('address');assert x==y,a['index']
  if aa!=bb:changed.append(a['index'])
 assert changed==sorted(i for i in patches if i<len(m['functions']))
 for k in m:
  if k not in ['functions','switches']:assert m[k]==nm[k],k
 sw=[]
 for i,(a,b) in enumerate(zip(m['switches'],nm['switches'])):
  if a!=b:
   sw.append(i);assert a['case-type']==b['case-type'] and a['default-address']==b['default-address'];assert [c['value'] for c in a['cases']]==[c['value'] for c in b['cases']]
 assert sw==[361,450,451],sw
 new=unpack(out.read_bytes());assert old[16:16+size]==new[16:16+size]
 assert strings(new)[2][:len(strings(old)[2])]==strings(old)[2]
 assert old[old.index(b'MSG1'):old.index(b'SWI0')]==new[new.index(b'MSG1'):new.index(b'SWI0')]
 for f in BASE.glob('built_*.jam'):shutil.copy2(f,O/f.name)
 for i in patches:cmd('ain','dump','--function',names.get(i) or next(n for n,ix in ids.items() if ix==i),'-o',O/f'built_{i}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 nat=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');assert nat['all_active_opcodes_supported'];savej(O/'native_opcode_audit.json',nat)
 return dict(patched_existing=changed,added_functions=ids,relocated_switches=sw,original_CODE_STR0_MSG1_preserved=True,save_schema_unchanged=True,option='owned flag92: off0, quick1, instant2; passive no-op setters',quiet_settle_sentinels=SILENT)

def build_pact(rt):
 src=rt/'NightRemasterPact.afa';arc=read_afa3(src);e=arc.entries[185]
 with src.open('rb') as f:f.seek(e.absolute_offset);raw=f.read(e.size)
 source=O/'original_pact_185.pactex';source.write_bytes(raw);d=ex.decode_ex(source)
 g=part(d,'KR_ModDungeon');checkbox=copy.deepcopy(part(d,'KR_CheatTrap'));rename(checkbox,'KR_CheatLoot');setlist(checkbox,'座標',[0,156,158])
 ci=child(checkbox,'種類別情報');oldtext=val(ci,'テキスト').value
 from build_remaster_multiplier_20260915 import decode
 pad=decode(oldtext);pad=pad[:len(pad)-len(pad.lstrip())];ss(ci,'テキスト',pad+'일반 적 즉시 처치',True);add(g,checkbox)
 for n,text,y in [('KR_ModQuickHint','즉시 처치와 결과만 보기는 함께 켤 수 없습니다.',204),('KR_ModQuickCancel','결과만 보기: 우클릭으로 전투 화면 복귀',230)]:
  t=part(d,n);setlist(t,'座標',[0,y,40]);ss(txt_info(t),'テキスト',text,True);si(child(txt_info(t),'テキスト装飾'),'フォントサイズ',14)
 out=O/'pact_185_loot.pactex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()));assert ex.decode_ex(out).serialize_payload()==d.serialize_payload()
 # Exact inverse checks the unchanged native layout outside these three nodes.
 original=ex.decode_ex(source);from build_mod_tab_20260915 import remove
 remove(g,'KR_CheatLoot')
 for n in ['KR_ModQuickHint','KR_ModQuickCancel']:part(d,n).__dict__.update(copy.deepcopy(part(original,n).__dict__))
 assert d.serialize_payload()==original.raw_payload
 report=rebuild(src,O/'NightRemasterPact.afa',{185:out});return dict(archive=report,changed_entries=[185],new_control='KR_CheatLoot',label='일반 적 즉시 처치',raster_and_fonts_unchanged=True)

def main():
 p=json.loads((O/'source_pointer.json').read_text());assert p==json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(p['runtime'])
 assert sha(rt/'NightRemaster.ain')=='28b837397fc79edb89de826819cd8e9a8de077e1c21a7513b748be13fe5a7412'
 before={n:sha(rt/n) for n in FILES};pa=build_pact(rt);ain=build_ain(rt)
 ev=dict(status='INSTANT_LOOT_STAGED',source_pointer=p,source_files=before,files={n:sha(O/n) for n in FILES},AIN=ain,PACT=pa,EX_unchanged_sha256=sha(rt/'NightRemasterEX.ex'),translator_model='Codex internal',native_gameplay_verified=False)
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
