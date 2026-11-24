"""Append-only offensive auto-selection; exact newest runtime only. Never installs."""
from pathlib import Path
import copy,json,re,struct,shutil
from cheat_support_20260915 import R,sha,savej,read_meta,cmd
from build_remaster_multiplier_20260915 import ex,read_afa3,rebuild,part,child,val,si,ss,setlist,rename,txt_info
from build_mod_tab_20260915 import add,coords
from build_route_perf_20260915 import symbol
from build_instant_loot_20260915 import clean,begin
from build_dungeon_sweep_20260916 import S,push,cf,lr,cm,assign,field
from repair_ui_runtime_weapon_text_20260913 import unpack,pack,strings
from audit_sys43_native_opcodes_20260915 import native_lower,audit

O=R/'staging/smart_auto_20260922';HERE=Path(__file__).resolve().parent
EXPECTED='0cefd6c20f120903773f71469aa6669fb1b3a5b5b5b6e3f0da9423b5778a7295'

def pact(rt):
 src=rt/'NightRemasterPact.afa';arc=read_afa3(src);entry=arc.entries[185]
 with src.open('rb') as f:f.seek(entry.absolute_offset);raw=f.read(entry.size)
 original=O/'original_185.pactex';original.write_bytes(raw);d=ex.decode_ex(original)
 for name,y in [('KR_CheatQuick',38),('KR_CheatRoute',76),('KR_CheatLoot',114),('KR_CheatSweep',152)]:
  p=part(d,name);xyz=coords(p);setlist(p,'座標',[xyz[0],y,xyz[2]])
 root=d.blocks[2].payload.children[0];toggle=copy.deepcopy(part(d,'KR_AutoEquipToggle'))
 rename(toggle,'KR_SmartAutoToggle');setlist(toggle,'座標',[783,590,251]);ss(child(toggle,'種類別情報'),'テキスト','    강화 자동 전투',True);add(root,toggle)
 out=O/'pact_185_smart_auto.pactex';out.write_bytes(ex.encode_ex(d.header,d.serialize_payload()))
 assert ex.decode_ex(out).serialize_payload()==d.serialize_payload()
 return dict(changed_entries=[185],archive=rebuild(src,O/'NightRemasterPact.afa',{185:out}),new_toggle='KR_SmartAutoToggle',default=False)

def main():
 O.mkdir(parents=True,exist_ok=True);ptr=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)==EXPECTED and sha(Path(ptr['manifest']))==ptr['manifest_sha256'];savej(O/'source_pointer.json',ptr)
 m=read_meta(R/'staging/notice_repair_20260917/candidate_meta.json');names={};seen={}
 for f in m['functions']:
  n=symbol(m,f['index']);j=seen.get(n,0);seen[n]=j+1;names[f['index']]=n+(f'#{j}' if j else '')
 def get(fid):
  out=O/f'original_{fid}.jam';cmd('ain','dump','--function',names[fid],'-o',out,src);return clean(out.read_text(encoding='utf8'),names[fid])
 jaf=O/'helpers.jaf';shutil.copy2(HERE/'smart_auto_helpers_20260922.jaf',jaf)
 decl=O/'declared.ain';cmd('ain','edit','--jaf',jaf,'-o',decl,src)
 old=unpack(src.read_bytes());raw=bytearray(unpack(decl.read_bytes()));oldsize=struct.unpack_from('<I',old,12)[0];newsize=struct.unpack_from('<I',raw,12)[0]
 assert old[16:16+oldsize]==raw[16:16+oldsize];struct.pack_into('<I',raw,24+newsize,m['functions'][0]['address']);decl.write_bytes(pack(bytes(raw),src.read_bytes()[:8]))
 cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]};bridges={}
 # Owned returned refs are kept once and released exactly once on all branches.
 f=dm['functions'][ids['KR_SmartLoad']];vs=f['arguments']+f['variables'];ix={v['name']:i for i,v in enumerate(vs)}
 def own(name,expr):return assign(ix[name],expr)
 cleanup=''.join('\t.LOCALDELETE '+name+'\n' for name in ['info','list','source'])
 b=lr('key')+push(-1)+'\tLT\n\tIFNZ load_fail\n'+lr('key')+push(0)+'\tLT\n\tIFNZ load_current\n'
 b+=cm(lr('pa'),27332)+push(1)+'\tNOTE\n\tIFNZ load_technique\n'
 b+=own('list',cm('\t.GLOBALREF Flags\n',26481))+lr('list')+push(-1)+'\tEQUALE\n\tIFNZ load_fail\n'
 b+=own('info',cm(lr('list'),26723,lr('key'),1))+lr('info')+push(-1)+'\tEQUALE\n\tIFNZ load_fail\n'
 b+=cm(lr('info'),26708,lr('weapon'),1)+cleanup+'\tRETURN\n'
 b+='load_current:\n'+own('source',cm(lr('pa'),27359)+cf('L_Weapon::At'))+'\tJUMP load_copy\n'
 b+='load_technique:\n'+own('source',lr('key')+cf('L_Weapon::At'))
 b+='load_copy:\n'+lr('source')+push(-1)+'\tEQUALE\n\tIFNZ load_fail\n'+cm(lr('weapon'),26894,lr('source'),1)+cleanup+push(1)+'\tRETURN\nload_fail:\n'+cleanup+push(0)+'\tRETURN\n'
 bridges['KR_SmartLoad']=b
 # Validated, copied target mask; no allocation/lookup in the target-pair loop.
 f=dm['functions'][ids['KR_SmartArea']];vs=f['arguments']+f['variables'];aix=next(i for i,v in enumerate(vs) if v['name']=='area')
 b=assign(aix,lr('id')+cf('L_TargetArea::At'))+lr('area')+push(-1)+'\tEQUALE\n\tIFNZ area_fail\n'
 b+=field(lr('area'),0)+'\tCALLHLL Array Numof 1\n'+push(25)+'\tNOTE\n\tIFNZ area_fail\n'
 b+='\t.LOCALASSIGN i 0\narea_loop:\n'+lr('i')+push(25)+'\tGTE\n\tIFNZ area_done\n'
 b+=lr('mask')+lr('i')+field(lr('area'),0)+lr('i')+'\tX_REF 1\n\tX_ASSIGN 1\n\tPOP\n\t.LOCALINC2 i\n\tJUMP area_loop\narea_done:\n\t.LOCALDELETE area\n'+push(1)+'\tRETURN\narea_fail:\n\t.LOCALDELETE area\n'+push(0)+'\tRETURN\n'
 bridges['KR_SmartArea']=b
 b=lr('enemy')+push(-1)+'\tEQUALE\n\tIFNZ dead\n'+field(lr('enemy'),0)+push(-1)+'\tEQUALE\n\tIFNZ dead\n'
 b+=field(lr('enemy'),12)+'\tIFNZ dead\n'+field(lr('enemy'),3)+push(0)+'\tLTE\n\tIFNZ dead\n'
 for fld in [1,2]:b+=field(lr('enemy'),fld)+push(0)+'\tLT\n\tIFNZ dead\n'+field(lr('enemy'),fld)+push(2)+'\tGT\n\tIFNZ dead\n'
 bridges['KR_SmartAlive']=b+push(1)+'\tRETURN\ndead:\n'+push(0)+'\tRETURN\n'
 bridges['KR_SmartM']=lr('monster')+lr('field')+'\tX_REF 1\n\tRETURN\n'
 bridges['KR_SmartType']=field(lr('battle'),5)+'\tRETURN\n'
 bridges['KR_SmartCount']=lr('enemies')+'\tCALLHLL Array Numof 65538\n\tRETURN\n'
 patches={}
 for name,fid in ids.items():
  out=O/f'jaf_{fid}.jam';cmd('ain','dump','--function',name,'-o',out,decl);s=clean(native_lower(out.read_text(encoding='utf8')),name)
  if name in bridges:s=f'FUNC {fid}\n'+bridges[name]+f'ENDFUNC {name}\n'
  patches[fid]=s
 # Only the decision hook changes; damage, HP, rewards, manual commands stay native.
 prefix='\tPUSHSTRUCTPAGE\n'+lr('pa')+lr('pf')+lr('enemies')+cf('KR_SmartRun')+'\tIFZ smart_original\n\tPUSHLOCALPAGE\n'+push(0)+'\tX_REF 2\n'+push(1)+'\tX_ASSIGN 1\n\tPOP\n'+push(1)+'\tRETURN\nsmart_original:\n'
 patches[29242]=begin(get(29242),prefix)
 for fid,method,callback in [(29817,29827,'KR_GetSmartAuto'),(29818,29828,'KR_SetSmartAuto')]:
  patches[fid]=begin(get(fid),'\tPUSHSTRUCTPAGE\n'+push(method)+S('KR_SmartAutoToggle')+push(-1)+push(ids[callback])+'\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n')
 jam=O/'smart_auto_patch.jam';jam.write_text('\n'.join(patches.values()),encoding='utf8');out=O/'NightRemaster.ain';cmd('ain','edit','--jam',jam,'-o',out,decl)
 # JAF cannot spell array<ref T>. Its flat placeholder emits correct pointer
 # accesses, but its serialized signature must be restored to the native ABI.
 data=bytearray(unpack(out.read_bytes()));abi=[]
 for name in ['KR_SmartCount','KR_SmartEvaluate','KR_SmartRun']:
  marker=name.encode()+b'\0';assert data.count(marker)==1
  start=data.index(marker);offset=data.index(b'enemies\0\0',start)+9
  assert struct.unpack_from('<7i',data,offset)==(80,13,1,13,746,0,0)
  struct.pack_into('<7i',data,offset,80,746,1,21,746,0,0);abi.append(dict(function=name,offset=offset))
 out.write_bytes(pack(bytes(data),src.read_bytes()[:8]));savej(O/'array_abi_normalization.json',abi)
 cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=read_meta(O/'candidate_meta.json');changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  x=dict(a);y=dict(z);aa=x.pop('address');zz=y.pop('address');assert x==y,a['index']
  if aa!=zz:changed.append(a['index'])
 assert set(changed)=={29242,29817,29818},changed
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 native_enemy_type=m['functions'][29242]['arguments'][4]['type']
 for name in ['KR_SmartCount','KR_SmartEvaluate','KR_SmartRun']:
  assert next(a for a in nm['functions'][ids[name]]['arguments'] if a['name']=='enemies')['type']==native_enemy_type
 after=unpack(out.read_bytes());assert old[16:16+oldsize]==after[16:16+oldsize]
 assert strings(after)[2][:len(strings(old)[2])]==strings(old)[2]
 assert old[old.index(b'MSG1'):old.index(b'SWI0')]==after[after.index(b'MSG1'):after.index(b'SWI0')]
 for fid in patches:cmd('ain','dump','--function',names.get(fid,nm['functions'][fid]['name']),'-o',O/f'built_{fid}.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 na=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');savej(O/'native_opcode_audit.json',na);assert na['all_active_opcodes_supported']
 pe=pact(rt)
 ev=dict(status='SMART_AUTO_STAGED_UNVERIFIED',source_pointer=ptr,source_files={n:sha(rt/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},files={n:sha(O/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']},
  unchanged_CG=sha(rt/'NightRemasterCG.afa'),patched_existing=changed,added_functions=ids,serialized_metadata_exact=True,old_CODE_STR0_MSG1_exact=True,PACT=pe,translator_model='Codex internal',native_verified=False,
  option=dict(slot=79,on_value=20260922,default=False,original_story_flag82_preserved=True),algorithm=dict(learned_offensive_only=True,max_candidates=50,max_enemies=9,decision_only=True,HP_cost_floor_percent=20,HP_floor_scope='decision time, not guaranteed after incoming damage',RNG_reads=0,preview_live_writes=0))
 savej(O/'build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
