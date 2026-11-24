"""Append stable resume entrances. Existing saves and gameplay bodies are untouched.

Each old local return offset contains only JUMP to its matched live instruction.
Normal function calls jump over the compatibility table to the unmodified body.
"""
from pathlib import Path
import copy,json,re,shutil,struct
import resume_compat_20260923 as q
import publish_cheat_menu_20260915 as p
b=q.b;R=q.R;O=q.O;BASE=q.BASE

def main():
 ptr=b.a.readj(O/'source_pointer.json');rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
 assert b.a.sha(src)==q.EXPECTED and ptr==b.a.readj(R/'ui_cumulative/current.json')
 p.exact_tree(rt,b.a.readj(Path(ptr['manifest']))['files'])
 q.save('save_hashes_before_build.json',p.snapshot_saves())
 shutil.copy2(src,O/'baseline_NightRemaster.ain')
 m=b.read_meta(BASE/'candidate_meta.json');vs=q.versions(BASE/'native_raw_code.jam')
 aliases={int(i):{int(k):v for k,v in rows.items()} for i,rows in b.a.readj(O/'resume_aliases.json').items()}
 patches=[];shims=[]
 for fid,entries in aliases.items():
  v=next(v for v in vs[fid] if v['start']==m['functions'][fid]['address'])
  lines=(O/f'original_{fid}.jam').read_text('utf8').splitlines()
  ops=[line for line in lines if line.startswith('\t')]
  assert len(ops)+1==len(v['ops']) and v['ops'][-1][1].startswith('ENDFUNC ')
  assert [x.strip().split()[0] for x in ops]==[x[1].split()[0] for x in v['ops'][:-1]]
  labels={off:f'resume_{fid}_to_{off:x}' for off in set(entries.values())}
  shim=[f'\tJUMP resume_{fid}_body'];pc=6
  for offset,target in sorted(entries.items()):
   assert offset>=pc and (offset-pc)%2==0
   shim+=['\tRETURN']*((offset-pc)//2)
   shim += [f'resume_{fid}_old_{offset:x}:',f'\tJUMP {labels[target]}'];pc=offset+6
  shim.append(f'resume_{fid}_body:')
  body=[];index=0
  for line in lines:
   if line.startswith('FUNC '):
    assert line==f'FUNC {fid}';body += [line,*shim];continue
   if line.startswith('\t'):
    off=v['ops'][index][0]-v['start'];index+=1
    if off in labels:body.append(labels[off]+':')
   body.append(line)
  assert index==len(ops)
  text=b.clean('\n'.join(body)+'\n',b.symbol(m,fid));patches.append(text)
  shims.append(dict(fid=fid,name=b.raw_symbol(m,fid),body_offset=pc,baseline_start=v['start'],aliases=entries,body_instructions=len(ops)))
 jam=O/'resume_compat_patch.jam';jam.write_text('\n'.join(patches),'utf8')
 out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',jam,'-o',out,src)
 b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
 assert len(m['functions'])==len(nm['functions']);changed=[]
 for a,z in zip(m['functions'],nm['functions']):
  aa=dict(a);zz=dict(z);ad=aa.pop('address');zd=zz.pop('address');assert aa==zz,a['index']
  if ad!=zd:changed.append(a['index'])
 assert sorted(aliases)==changed,changed
 for k in m:
  if k not in ['functions','switches']:assert m[k]==nm[k],k
 switches=[]
 step=next(row for row in shims if row['fid']==28664)
 delta=nm['functions'][28664]['address']+step['body_offset']-step['baseline_start']
 for i,(a,z) in enumerate(zip(m['switches'],nm['switches'])):
  if a==z:continue
  assert i in (450,451);expected=copy.deepcopy(a)
  for case in expected['cases']:case['address']+=delta
  assert expected==z,(i,expected,z);switches.append(i)
 assert switches==[450,451]
 old=b.unpack(src.read_bytes());new=b.unpack(out.read_bytes());n=struct.unpack_from('<I',old,12)[0]
 assert old[16:16+n]==new[16:16+n]
 assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
 assert b.strings(old)[2]==b.strings(new)[2]
 b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 for fid in aliases:b.cmd('ain','dump','--no-macros','--function',b.symbol(nm,fid),'-o',O/f'built_{fid}.jam',out)
 report=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe')
 assert report['all_active_opcodes_supported'];q.save('native_opcode_audit.json',report)
 assert b.a.readj(O/'save_hashes_before_build.json')==p.snapshot_saves()
 q.save('shim_layout.json',shims)
 ev=dict(status='RESUME_COMPAT_STAGED',source_pointer=ptr,source_files={'NightRemaster.ain':q.EXPECTED},files={'NightRemaster.ain':b.a.sha(out)},patched_existing=changed,added_functions={},relocated_switches=switches,MSG1_exact=True,STR0_exact=True,old_CODE_prefix_exact=True,save_schema_changes=0,save_writes=0,native_verified=False,supported_existing_resume_saves=37,mapped_saved_frames=950,scope='Only recorded return offsets from the current 37 saves; not a universal external-save converter.')
 q.save('build_evidence.json',ev);print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
