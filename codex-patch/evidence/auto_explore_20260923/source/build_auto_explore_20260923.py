"""Session exploration; old persistent methods receive only same-size operand edits."""
from pathlib import Path
import json,re,struct,shutil
import build_term_switch_20260923 as b
import resume_compat_20260923 as q
import publish_cheat_menu_20260915 as p
from build_dungeon_sweep_20260916 import push,cf,lr,cm,assign,field
R=b.R;O=R/'staging/auto_explore_20260923';BASE=R/'staging/load_error_20260923';HERE=Path(__file__).resolve().parent
EXPECTED='f39c448723a1139673ae443da3cc10a27ccec5422df5fe0fa3258d580f09b635'
WRAPPERS={32030:'KR_ExploreVisible',32036:'KR_ExploreStop',32046:'KR_ExplorePlan',32049:'KR_ExploreStart',32051:'KR_ExploreGuard',32052:'KR_ExploreGate'}
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 O.mkdir(exist_ok=True);ptr=b.a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
 assert b.a.sha(src)==EXPECTED and b.a.sha(Path(ptr['manifest']))==ptr['manifest_sha256'];p.exact_tree(rt,b.a.readj(Path(ptr['manifest']))['files'])
 save('source_pointer.json',ptr);save('save_hashes_before_build.json',p.snapshot_saves());shutil.copy2(src,O/'baseline_NightRemaster.ain')
 m=b.read_meta(BASE/'candidate_meta.json');vs=q.versions(BASE/'native_raw_code.jam')
 def get(fid):
  path=O/f'original_{fid}.jam';b.cmd('ain','dump','--function',b.symbol(m,fid),'-o',path,src);return b.clean(path.read_text('utf8'),b.symbol(m,fid))
 jaf=(HERE/'auto_explore_helpers_20260923.jaf').read_text('utf8')
 jaf=re.sub(r'"([^"\n]*(?:[가-힣])[^"\n]*)"',lambda x:json.dumps(b.encode(json.loads(x[0])).decode('cp932'),ensure_ascii=False),jaf)
 (O/'helpers.jaf').write_text(jaf,'utf8');decl=O/'declared.ain';b.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
 old=b.unpack(src.read_bytes());raw=bytearray(b.unpack(decl.read_bytes()));n=struct.unpack_from('<I',old,12)[0];nn=struct.unpack_from('<I',raw,12)[0]
 assert old[16:16+n]==raw[16:16+n];struct.pack_into('<I',raw,24+nn,m['functions'][0]['address']);decl.write_bytes(b.pack(raw,src.read_bytes()[:8]))
 b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json');ids={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]}
 scene=lr('scene');mp=field(scene,6);cell=lr('cell');bridges={};patches={}
 bridges['KR_ExploreMap']=cm(scene,28622)+'\tRETURN\n'
 bridges['KR_ExploreFloor']=cm(scene,28628)+'\tRETURN\n'
 bridges['KR_ExploreSubId']=cm(cell,27008)+'\tRETURN\n'
 def bind(func,name,expr):
  f=dm['functions'][ids[func]];return assign(next(i for i,v in enumerate(f['arguments']+f['variables']) if v['name']==name),expr)
 # Query visibility before any object/passability getter. Unknown cells return zero.
 fn='KR_ExploreCell';s=bind(fn,'cell',cm(mp,27082,lr('x')+lr('y'),2))+cell+'\tSP_INC\n'
 s+=cell+push(-1)+'\tEQUALE\n\tIFNZ cell_zero\n'
 s+=cm(cell,27014)+'\tIFNZ cell_known\n'+cm(cell,27017)+'\tIFZ cell_zero\ncell_known:\n'
 s+=cm(cell,27039)+'\tIFZ cell_zero\n'+bind(fn,'code',push(1))
 s+=cm(cell,27014)+'\tIFNZ cell_seen\n'+bind(fn,'code',lr('code')+push(2)+'\tADD\n')+'cell_seen:\n'
 s+=cm(cell,27023)+'\tIFNZ cell_done\n'+cm(cell,27020)+'\tIFZ cell_done\n'+bind(fn,'obj',cm(cell,27005))
 s+=lr('obj')+push(2)+'\tNOTE\n\tIFNZ cell_loot\n'+cm(cell,27008)+push(1)+'\tNOTE\n\tIFNZ cell_done\n'+bind(fn,'code',lr('code')+push(8)+'\tADD\n')+'\tJUMP cell_done\ncell_loot:\n'
 s+=lr('obj')+push(3)+'\tLT\n\tIFNZ cell_done\n'+lr('obj')+push(5)+'\tGT\n\tIFNZ cell_done\n'+bind(fn,'code',lr('code')+push(4)+'\tADD\n')
 s+='cell_done:\n\t.LOCALDELETE cell\n'+lr('code')+'\tRETURN\ncell_zero:\n\t.LOCALDELETE cell\n'+push(0)+'\tRETURN\n';bridges[fn]=s
 fn='KR_ExploreRemoved';s=bind(fn,'cell',cm(mp,27082,lr('x')+lr('y'),2))+cell+'\tSP_INC\n'+cell+push(-1)+'\tEQUALE\n\tIFNZ cell_zero\n'+cm(cell,27023)+'\t.LOCALDELETE cell\n\tRETURN\ncell_zero:\n\t.LOCALDELETE cell\n'+push(0)+'\tRETURN\n';bridges[fn]=s
 for name,fid in [('KR_ExploreGuidedPlan',32046),('KR_ExploreRawVisible',32030)]:bridges[name]=get(fid).split(f'FUNC {fid}\n',1)[1].split('ENDFUNC ',1)[0]
 for name,fid in ids.items():
  path=O/f'jaf_{fid}.jam';b.cmd('ain','dump','--function',name,'-o',path,decl);s=b.clean(b.native_lower(path.read_text('utf8')),name)
  if name in bridges:
   body=bridges[name]
   for label in re.findall(r'^([^\s:]+):$',body,re.M):body=re.sub(r'(?<![\w])'+re.escape(label)+r'(?![\w])',f'explore_{fid}_{label}',body)
   s=f'FUNC {fid}\n'+body+f'ENDFUNC {name}\n'
  patches[fid]=s
 for fid,target in WRAPPERS.items():
  args=''.join(lr(a['name']) for a in m['functions'][fid]['arguments']);patches[fid]=f'FUNC {fid}\n'+args+cf(target)+'\tRETURN\n'+f'ENDFUNC {b.symbol(m,fid)}\n'
 jam=O/'native_patch.jam';jam.write_text('\n'.join(patches.values()),'utf8');out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',jam,'-o',out,decl)
 data=bytearray(b.unpack(out.read_bytes()));abi=[]
 for name,fid in ids.items():
  for v in dm['functions'][fid]['arguments']+dm['functions'][fid]['variables']:
   if v['name']=='route' and v['type'][0] in [79,80]:
    typ=v['type'][0];start=data.index(name.encode()+b'\0');off=data.index(b'route\0\0',start)+7
    assert struct.unpack_from('<7i',data,off)==(typ,13,1,13,514,0,0);struct.pack_into('<7i',data,off,typ,514,1,13,514,0,0);abi.append(dict(function=name,offset=off))
 # Resolve patch sites from the exact baseline disassembly, never an edited dump.
 def ops(fid):return next(v['ops'] for v in vs[fid] if v['start']==m['functions'][fid]['address'])
 def findid(name):return next(f['index'] for f in m['functions'] if b.raw_symbol(m,f['index'])==name)
 sites=[]
 def replace_at(fid,ad,before,after,why):
  assert len(before)==len(after) and bytes(data[16+ad:16+ad+len(before)])==before==old[16+ad:16+ad+len(before)]
  assert not any(ad<r['address']+len(bytes.fromhex(r['before'])) and r['address']<ad+len(before) for r in sites)
  data[16+ad:16+ad+len(after)]=after;sites.append(dict(fid=fid,address=ad,before=before.hex(),after=after.hex(),reason=why))
 callcode=None
 def callpatch(fid,oldfid,target,lo=0,hi=2**31):
  rows=[(a,o) for a,o in ops(fid) if o==f'CALLFUNC {oldfid:#x}' and lo<=a<hi];assert len(rows)==1,(fid,oldfid,rows)
  ad=rows[0][0];before=old[16+ad:16+ad+6];replace_at(fid,ad,before,before[:2]+struct.pack('<i',ids[target]),target)
  return before[:2]
 callcode=callpatch(28637,findid('C_SysVoice::PlayVoiceEnterRandomDungeon'),'KR_ExploreTripBegin')
 callpatch(28637,32036,'KR_ExploreAfterClick');callpatch(28665,32036,'KR_ExploreBattleEnter');callpatch(29556,32063,'KR_ExploreAfterLoad')
 cases=m['switches'][451]['cases'];lo=next(c['address'] for c in cases if c['value']==1);hi=min([c['address'] for c in cases if c['address']>lo]+[2**31])
 callpatch(28664,findid('■選択ダイアログ／実行'),'KR_ExploreFloorDialog',lo,hi)
 oo=ops(27159);seq=['PUSHLOCALPAGE','PUSH 0x8','PUSH 0x0','X_ASSIGN 0x1','POP']
 matches=[i for i in range(len(oo)-len(seq)) if [v[1] for v in oo[i:i+len(seq)]]==seq];assert len(matches)==1
 ad=oo[matches[0]+2][0];replace_at(27159,ad,old[16+ad:16+ad+6],callcode+struct.pack('<i',ids['KR_ExploreTrapAuto']),'native auto trap selector only during our pending trap')
 seq=['PUSHLOCALPAGE','PUSH 0x2','X_REF 0x2','X_REF 0x1','GT'];matches=[i for i in range(len(oo)-len(seq)) if [v[1] for v in oo[i:i+len(seq)]]==seq];assert len(matches)==1
 ad=oo[matches[0]+4][0];gte=next(a for vv in vs.values() for v in vv for a,o in v['ops'] if o=='GTE');replace_at(27159,ad,old[16+ad:16+ad+2],old[16+gte:16+gte+2],'select living party member even when all native chances are zero')
 # Every byte changed in old CODE must belong to one explicit instruction write.
 prefix=bytearray(data[16:16+n])
 for r in sites:prefix[r['address']:r['address']+len(bytes.fromhex(r['before']))]=bytes.fromhex(r['before'])
 assert bytes(prefix)==old[16:16+n]
 out.write_bytes(b.pack(bytes(data),src.read_bytes()[:8]));save('same_length_sites.json',sites);save('array_abi_normalization.json',abi)
 b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json');changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  aa=dict(a);zz=dict(z);ad=aa.pop('address');zd=zz.pop('address');assert aa==zz,a['index']
  if ad!=zd:changed.append(a['index'])
 assert changed==sorted(WRAPPERS),changed
 for k in m:
  if k!='functions':assert m[k]==nm[k],k
 assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
 assert b.strings(bytes(data))[2][:len(b.strings(old)[2])]==b.strings(old)[2]
 b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 for fid in patches:b.cmd('ain','dump','--function',b.symbol(nm,fid),'-o',O/f'built_{fid}.jam',out)
 report=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',report);assert report['all_active_opcodes_supported']
 assert p.snapshot_saves()==b.a.readj(O/'save_hashes_before_build.json')
 ev=dict(status='AUTO_EXPLORE_STAGED',source_pointer=ptr,source_files={'NightRemaster.ain':EXPECTED},files={'NightRemaster.ain':b.a.sha(out)},patched_existing=changed,in_place_functions=sorted(set(s['fid'] for s in sites)),same_length_instruction_sites=len(sites),added_functions=ids,MSG1_exact=True,STR0_prefix_exact=True,existing_metadata_exact_except_six_helper_addresses=True,serialized_fields_added=0,save_writes=0,translator_model='Codex internal',native_verified=False)
 save('build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
