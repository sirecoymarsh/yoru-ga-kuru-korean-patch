"""Exact write-set, saved-offset, native-bridge and Korean font checks."""
import json,re,struct,collections
import build_auto_explore_20260923 as e
b=e.b;p=e.p;q=e.q;O=e.O
def main():
 ev=b.a.readj(O/'build_evidence.json');src=O/'baseline_NightRemaster.ain';out=O/'NightRemaster.ain'
 assert b.a.sha(src)==e.EXPECTED and ev['files']=={'NightRemaster.ain':b.a.sha(out)}
 bm=b.read_meta(e.BASE/'candidate_meta.json');nm=b.read_meta(O/'candidate_meta.json');oldvs=q.versions(e.BASE/'native_raw_code.jam');newvs=q.versions(O/'native_raw_code.jam')
 old=b.unpack(src.read_bytes());new=b.unpack(out.read_bytes());size=struct.unpack_from('<I',old,12)[0];prefix=bytearray(new[16:16+size]);sites=b.a.readj(O/'same_length_sites.json')
 for r in sites:
  ad=r['address'];bb=bytes.fromhex(r['before']);aa=bytes.fromhex(r['after']);assert len(bb)==len(aa) and bytes(prefix[ad:ad+len(aa)])==aa
  assert old[16+ad:16+ad+len(bb)]==bb;prefix[ad:ad+len(bb)]=bb
 assert bytes(prefix)==old[16:16+size] and len(sites)==7
 for f,g in zip(bm['functions'],nm['functions']):
  z=dict(f)
  if f['index'] in e.WRAPPERS:z['address']=g['address']
  assert z==g
 for k in bm:
  if k!='functions':assert bm[k]==nm[k],k
 assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
 assert b.strings(new)[2][:len(b.strings(old)[2])]==b.strings(old)[2]
 # Read every current save. No historical fixed save count; no writes.
 signatures=collections.defaultdict(list)
 for f in bm['functions']:signatures[f['crc']&0xffffffff].append(f)
 records=[];frames=[];allold={ad:op for vv in oldvs.values() for v in vv for ad,op in v['ops']};allnew={ad:op for vv in newvs.values() for v in vv for ad,op in v['ops']}
 for path in sorted(p.SAVE.glob('NightR*.asd')):
  if not re.fullmatch(r'NightR\d+\.asd',path.name):continue
  row=q.records(path);assert row is not None;records.append(row)
  for rr in [row['ip']]+row['returns']:
   if rr['address']==-1:continue
   choices=[f for f in signatures[rr['crc']] if rr['name'].startswith(b.raw_symbol(bm,f['index'])+'(') and any(v['start']==rr['address']-rr['offset'] for v in oldvs[f['index']])]
   assert len(choices)==1,(path.name,rr,choices);f=choices[0];fid=f['index'];assert fid not in e.WRAPPERS
   assert nm['functions'][fid]==f
   before=next(v for v in oldvs[fid] if v['start']==f['address']);after=next(v for v in newvs[fid] if v['start']==f['address']);ad=f['address']+rr['offset'];ob=dict(before['ops']);nb=dict(after['ops'])
   assert ad in ob and ad in nb and ob[ad]==nb[ad],(path.name,fid,hex(ad))
   # Follow existing compatibility shims without changing their entry or target.
   if ob[ad].startswith('JUMP '):target=int(ob[ad].split()[1],16);assert allold[target]==allnew[target]
   frames.append(dict(file=path.name,fid=fid,offset=rr['offset'],opcode=nb[ad]))
 # Semantic bridge bounds and key calls on the actual assembled code.
 ids=ev['added_functions'];j=lambda n:(O/f'built_{ids[n]}.jam').read_text('utf8')
 cell=j('KR_ExploreCell');seen=cell.index('PUSH 27017');stepped=cell.index('PUSH 27014');physical=cell.index('PUSH 27039');obj=cell.index('PUSH 27005')
 assert stepped<seen<physical<obj and 'PUSH 27020' in cell and 'PUSH 27023' in cell
 assert all(s not in cell for s in ['PUSH 27025','KR_GetRoute','IsEventDungeon'])
 guided=j('KR_ExploreGuidedPlan');assert 'CALLFUNC KR_WalkPlanLinear' in guided and 'CALLFUNC KR_WalkPlanPuzzle' in guided
 planner=j('KR_ExplorePlan');assert 'CALLFUNC KR_GetRoute' in planner and 'CALLFUNC KR_ExploreGuidedPlan' in planner and 'CALLFUNC KR_ExploreCell' in planner
 assert 'CALLFUNC KR_ExploreClear' in j('KR_ExploreTripBegin') and 'CALLFUNC KR_ExploreClear' in j('KR_ExploreAfterLoad')
 for n in ['KR_ExplorePlan','KR_ExploreGuard','KR_ExploreFloorDialog']:
  assert not any(x in j(n) for x in ['VSFile','SaveFile','GetExperience','Money','SetLevel'])
 from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
 from audit_dynamic_ui_20260915 import ENC
 rt=e.Path(ev['source_pointer']['runtime']);_,faces=parse_fnl_font(rt/'NightRemasterFont.fnl',3);face,den,_=select_fnl_face(faces,36)
 text='이번 탐색은 묻지 않고 이동';width=WidthMeasurer(face,den,{c:sjis_bytes_to_fnl_index(v) for c,v in ENC.items()},0,0,0).measure(text,True)['lines'][0]['width_px'];assert width<720
 assert b.decode(b.encode(text))==text
 assert p.snapshot_saves()==b.a.readj(O/'save_hashes_before_build.json')
 e.save('save_resume_check.json',dict(saves=len(records),frames=frames))
 report=dict(status='AUTO_EXPLORE_STATIC_PASS',files=ev['files'],existing_resume_saves=len(records),saved_return_frames=len(frames),save_files_unchanged=len(p.snapshot_saves()),same_length_sites=len(sites),existing_save_local_offsets_exact=True,MSG1_exact=True,STR0_prefix_exact=True,hidden_topology_not_read=True,new_choice=dict(text=text,columns=1,width_at_36px=width),native_gameplay_verified=False)
 e.save('verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
