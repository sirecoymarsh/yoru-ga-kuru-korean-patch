"""Correct only the sweep whitelist, on the latest already-installed sweep build."""
from pathlib import Path
import json,struct,copy,re
from build_remaster_multiplier_20260915 import cmd,read_meta
from build_instant_loot_20260915 import begin,clean
from repair_ui_runtime_weapon_text_20260913 import unpack
from cheat_support_20260915 import R,sha,savej
from audit_sys43_native_opcodes_20260915 import audit
import verify_dungeon_sweep_20260916 as test
O=Path('sweep_infinite_20260916');O.mkdir(exist_ok=True)
NAME='KR_SweepAllowed';FID=31888
def main():
 ptr=json.loads((R/'ui_cumulative/current.json').read_text());rt=Path(ptr['runtime']);src=rt/'NightRemaster.ain'
 assert sha(src)=='b58ba53d8920f0e1c2553d7bfecf84f61aafed0887c549d272b77d83610cf650'
 cmd('ain','dump','-j','-o',O/'source_meta.json',src);oldm=read_meta(O/'source_meta.json')
 cmd('ain','dump','--function',NAME,'-o',O/'original_31888.jam',src)
 s=clean((O/'original_31888.jam').read_text(encoding='utf8'),NAME)
 prefix='\t.LOCALREF id\n\tPUSH 1201\n\tEQUALE\n\tIFNZ infinite_allowed\n\t.LOCALREF id\n\tPUSH 2601\n\tEQUALE\n\tIFZ infinite_others\ninfinite_allowed:\n\tPUSH 1\n\tRETURN\ninfinite_others:\n'
 patch=O/'patch.jam';patch.write_text(begin(s,prefix),encoding='utf8');out=O/'NightRemaster.ain'
 cmd('ain','edit','--jam',patch,'-o',out,src);cmd('ain','dump','-j','-o',O/'candidate_meta.json',out)
 nm=read_meta(O/'candidate_meta.json');expected=copy.deepcopy(oldm);expected['functions'][FID]['address']=nm['functions'][FID]['address'];assert expected==nm
 old=unpack(src.read_bytes());new=unpack(out.read_bytes());ns=struct.unpack_from('<I',new,12)[0];os=struct.unpack_from('<I',old,12)[0]
 assert new[16:16+os]==old[16:16+os]
 # Every non-CODE section byte is exact except the one function entry address.
 offset=oldm['functions'][FID]['address'];newaddr=nm['functions'][FID]['address']
 tailold=old[16+os:];tailnew=new[16+ns:];assert len(tailold)==len(tailnew)
 differences=[i for i,(a,b) in enumerate(zip(tailold,tailnew)) if a!=b];assert len(differences)<=4
 lo=min(differences);positions=[i for i in range(max(0,lo-3),lo+1) if tailold[i:i+4]==struct.pack('<I',offset) and tailnew[i:i+4]==struct.pack('<I',newaddr)]
 assert len(positions)==1;at=positions[0];assert tailold[:at]+tailold[at+4:]==tailnew[:at]+tailnew[at+4:]
 cmd('ain','dump','--function',NAME,'-o',O/'built_31888.jam',out)
 cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
 na=audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe',ids=[FID]);savej(O/'native_opcode_audit.json',na);assert na['all_active_opcodes_supported']
 ops=[];labels={}
 for line in (O/'built_31888.jam').read_text(encoding='utf8').splitlines():
  l=line.strip()
  if not l or l.startswith((';','FUNC','ENDFUNC','EOF')):continue
  if l.endswith(':'):labels[l[:-1]]=len(ops)
  else:ops.append(l.split(maxsplit=1))
 def vm():
  v=test.VM();v.codes[FID]=(ops,labels);return v
 previous=test.VM();v=vm();changed=[]
 for i in range(-1,10001):
  a=previous.run(NAME,[i]);b=v.run(NAME,[i])
  if a!=b:changed.append(i);assert not a and b
 assert changed==[1201,2601]
 cases=0
 for mapid,start in [(1201,1001),(1201,1101),(1201,1201),(2601,2001),(2601,2501),(2601,2601)]:
  for persons in [1,2,3]:
   v=vm();v.map=mapid;v.scene[6][1]=mapid;v.start=start;v.base=(mapid//1000)*1000;v.g[253]=list(range(1,persons+1))
   assert v.run('KR_SweepSceneOK',[v.scene]);assert v.run('KR_SweepPreflight',[mapid])
   v.confirm=False;before=copy.deepcopy(v.g);assert not v.run('KR_SweepExecute',[v.scene]);assert v.g==before and v.rem==1000
   v.confirm=True;assert v.run('KR_SweepExecute',[v.scene]);assert v.rem==0 and v.settles==25 and v.chests==5
   assert not v.run('KR_SweepExecute',[v.scene]);cases+=1
 for mapid in [1201,2601]:
  for kind in ['off','event','not_sunday','story_start','wrong_family','zero_time']:
   v=vm();v.map=mapid;v.scene[6][1]=mapid;v.start=mapid;v.base=(mapid//1000)*1000
   if kind=='off':v.g[229][99]=0
   if kind=='event':v.scene[4]={}
   if kind=='not_sunday':v.training=False
   if kind=='story_start':v.start=405
   if kind=='wrong_family':v.base=3000
   if kind=='zero_time':v.rem=0
   assert not v.run('KR_SweepSceneOK',[v.scene])
  v=vm();v.map=mapid;v.scene[6][1]=mapid;v.start=mapid;v.base=(mapid//1000)*1000;v.fail=6;before=copy.deepcopy(v.g)
  assert not v.run('KR_SweepExecute',[v.scene]);assert v.g==before and v.rem==1000
 rows=json.loads(Path('dungeon_skip_20260916/dungeon_table.json').read_text());rows=[r for r in rows if r['id'] in changed]
 for r in rows:
  assert r['id']>=1000 and r['id']==r['nextId'] and r['map']==0 and r['level']>0
  assert sum(r[f'mons{i}Rate'] for i in range(1,9))==100
 evidence=dict(status='SWEEP_INFINITE_STATIC_PASS_NATIVE_PENDING',source_pointer=ptr,source_files={'NightRemaster.ain':sha(src)},files={'NightRemaster.ain':sha(out)},unchanged_files={n:sha(rt/n) for n in ['NightRemasterPact.afa','NightRemasterEX.ex','NightRemaster.exe']},AIN=dict(patched_existing=[FID],new_functions=0,old_CODE_exact=True,all_other_sections_exact_except_one_address=True,save_schema_unchanged=True),allowed_count=82,added_ids=changed,table_rows=rows,reason='Self-loop is ordinary infinite exploration, not a story/boss flag. User confirms1201; native26986/26988,27068/27069 share ordinary branch for both. Chest27183 uses dungeon.level, not zero layout ranks; weighted native monster table valid.',native_gameplay_verified=False)
 savej(O/'build_evidence.json',evidence)
 savej(O/'verification.json',dict(status=evidence['status'],files=evidence['files'],predicate_ids_checked=10002,only_newly_allowed=changed,party_and_start_cases=cases,negative_context_cases=12,rollback_after_chest_cases=2,native_opcodes_supported=True,native_gameplay_verified=False,scope='Actual compiled whitelist and existing compiled scene/control logic in fixture; native reward/HLL boundaries mocked. Only original31888metadataentry changes.'))
 print(json.dumps(evidence,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
