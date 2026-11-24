"""Check compiled compatibility entrypoints and every recorded save resume frame.
This is a static bytecode/return-record test, NOT a native game load test.
"""
import collections,struct,re,json
import resume_compat_20260923 as q
import publish_cheat_menu_20260915 as p
b=q.b;O=q.O

def main():
 ev=b.a.readj(O/'build_evidence.json');assert ev['files']=={'NightRemaster.ain':b.a.sha(O/'NightRemaster.ain')}
 bm=b.read_meta(q.BASE/'candidate_meta.json');nm=b.read_meta(O/'candidate_meta.json')
 oldvs=q.versions(q.BASE/'native_raw_code.jam');newvs=q.versions(O/'native_raw_code.jam')
 layouts={x['fid']:x for x in b.a.readj(O/'shim_layout.json')}
 oldraw=b.unpack((O/'baseline_NightRemaster.ain').read_bytes());newraw=b.unpack((O/'NightRemaster.ain').read_bytes())
 old=oldraw[16:16+struct.unpack_from('<I',oldraw,12)[0]];new=newraw[16:16+struct.unpack_from('<I',newraw,12)[0]]
 assert old==new[:len(old)]
 current={};proof=[];jumps=[]
 for fid,row in layouts.items():
  before=next(v for v in oldvs[fid] if v['start']==bm['functions'][fid]['address'])
  after=next(v for v in newvs[fid] if v['start']==nm['functions'][fid]['address']);current[fid]=after
  start=after['start'];body=start+row['body_offset'];delta=body-before['start'];adict=dict(after['ops'])
  assert adict[start]==f'JUMP 0x{body:x}'
  # Body bytes must be identical except absolute control-flow destinations.
  size=before['ops'][-1][0]+6-before['start'];expected=bytearray(old[before['start']:before['start']+size]);branches=0
  for a,op in before['ops']:
   if op.split()[0] in ['JUMP','IFZ','IFNZ']:
    target=struct.unpack_from('<i',old,a+2)[0]
    assert before['start']<=target<before['start']+size,(fid,hex(a),hex(target))
    struct.pack_into('<i',expected,a-before['start']+2,target+delta);branches+=1
  assert new[body:body+size]==expected,('body changed beyond branch relocation',fid)
  aliases={int(k):v for k,v in row['aliases'].items()}
  occupied=set(range(0,6,2))
  for offset,target in aliases.items():
   pc=start+offset;destination=body+target
   assert adict[pc]==f'JUMP 0x{destination:x}' and destination in adict
   assert struct.unpack_from('<H',new,pc)[0]==0x2c and struct.unpack_from('<I',new,pc+2)[0]==destination
   assert destination>=body and not (occupied & set(range(offset,offset+6,2)))
   occupied.update(range(offset,offset+6,2));jumps.append(dict(fid=fid,offset=offset,destination=destination,opcode=adict[destination]))
  for off in range(0,row['body_offset'],2):
   if off not in occupied:assert adict[start+off]=='RETURN'
  proof.append(dict(fid=fid,bytes_verified=size,branches_relocated=branches,normal_entry_jump=True,body_offset=row['body_offset'],return_aliases=len(aliases)))
 # Re-read the immutable save bytes rather than trust only the generated site table.
 inventory=b.a.readj(O/'save_inventory.json');records=[]
 for row in inventory:
  reread=q.records(p.SAVE/row['file']);assert reread==row
  records += [(row['file'],rec) for rec in [row['ip']]+row['returns'] if rec['address']!=-1]
 sites=b.a.readj(O/'resume_sites.json');assert len(records)==len(sites)==950
 moved=[];future=[]
 for (filename,rec),site in zip(records,sites):
  fid=site['fid'];f=nm['functions'][fid]
  assert filename==site['save'] and rec['name']==site['name'] and rec['address']==site['saved_address'] and rec['offset']==site['saved_offset']
  assert f['crc']&0xffffffff==rec['crc']
  actual=f['address']+rec['offset']
  if fid in layouts:
   row=layouts[fid];ops=dict(current[fid]['ops']);target=int(ops[actual].split()[1],16)
   assert ops[actual].startswith('JUMP ') and target==f['address']+row['body_offset']+site['target_offset']
   assert ops[target]==site['opcode'] or q.norm(ops[target])==q.norm(site['opcode'])
   moved.append(dict(save=filename,fid=fid,saved_offset=rec['offset'],loaded_alias=actual,resume_destination=target,opcode=ops[target]))
   # A save made at the repaired live return location roundtrips without the old alias.
   newlocal=target-f['address'];assert newlocal>=row['body_offset'] and f['address']+newlocal==target
   future.append(dict(fid=fid,local_offset=newlocal,target=target))
  else:
   assert actual==site['target'] and bm['functions'][fid]==f
 # Concrete reproduction oracle for user's SetMotionWaitInForceStop failure.
 bad=next(x for x in sites if x['save']=='NightR36.asd' and x['fid']==28637)
 oldfunc=next(v for v in oldvs[28637] if v['start']==bad['current_start'])
 wrong=dict(oldfunc['ops'])[bad['current_start']+bad['saved_offset']]
 assert wrong=='PUSH 0x6fec' and bad['opcode']=='POP'
 repaired=next(x for x in moved if x['save']=='NightR36.asd' and x['fid']==28637);assert repaired['opcode']=='POP'
 # All existing metadata except four entry addresses and two relocatable switch tables.
 assert len(bm['functions'])==len(nm['functions'])
 for i,(a,z) in enumerate(zip(bm['functions'],nm['functions'])):
  expected=dict(a)
  if i in layouts:expected['address']=z['address']
  assert expected==z,i
 for k in bm:
  if k not in ['functions','switches']:assert bm[k]==nm[k],k
 for i,(a,z) in enumerate(zip(bm['switches'],nm['switches'])):
  if i not in [450,451]:assert a==z,i
 assert b.strings(oldraw)[2]==b.strings(newraw)[2]
 assert b.raw_messages((O/'baseline_NightRemaster.ain').read_bytes())[3]==b.raw_messages((O/'NightRemaster.ain').read_bytes())[3]
 assert b.a.readj(O/'save_hashes_before_build.json')==p.snapshot_saves()
 q.save('verification.json',dict(status='RESUME_COMPAT_STATIC_PASS',files=ev['files'],existing_resume_saves=len(inventory),saved_return_frames=len(records),redirected_frames=len(moved),shim_entry_count=len(jumps),gameplay_body_byte_proofs=proof,resume_redirects=moved,future_relative_returns=future,cause=dict(save='NightR36.asd',before_wrong_instruction=wrong,after_correct_instruction='POP',failed_method='C_SceneDungeon@SetMotionWaitInForceStop()'),save_files_unchanged=len(p.snapshot_saves()),MSG1_STR0_exact=True,native_verified=False))
 print('PASS: 37 saves / 950 saved resume sites; '+str(len(moved))+' frames redirected, 9 shim entries. Native load test pending.')

if __name__=='__main__':main()
