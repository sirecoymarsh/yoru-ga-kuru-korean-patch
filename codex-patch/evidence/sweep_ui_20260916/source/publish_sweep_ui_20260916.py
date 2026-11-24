"""Sweep-only dialog correction; retain all current reward/gameplay data."""
from pathlib import Path
import json,copy,datetime,shutil,sys,hashlib
import publish_dungeon_sweep_20260916 as prior
import publish_cheat_menu_20260915 as p
S=Path(__file__).resolve().parent;R=p.R;O=R/'staging/sweep_ui_20260916';E=R/'evidence/sweep_ui_20260916';NEW='required_sweep_ui_fix.json'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']
STATUS='SWEEP_UI_STATIC_PASS_NATIVE_PENDING'
def main():
 ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
 for f,s in [('verification.json',STATUS),('independent_review.json','STATIC_REVIEW_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
  x=p.read(O/f);assert x['status']==s and x['files']==after,f
 assert all(p.sha(O/n)==h for n,h in after.items())
 if E.exists():
  j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256'];print('ALREADY_INSTALLED');return
 assert current==ev['source_pointer'];rt=Path(current['runtime']).resolve();mp=Path(current['manifest']);assert p.sha(mp)==current['manifest_sha256'];m=p.read(mp)
 if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
 fx=p.fixture();p.exact_tree(rt,m['files']);assert all(p.sha(rt/n)==h for n,h in before.items());assert all(p.sha(rt/n)==h for n,h in ev['unchanged_files'].items())
 saves=p.snapshot_saves();keep=p.read(R/'required_build_retention.json');recovery=Path(keep['recovery_runtime']);rh=p.sha(recovery/'NightRemaster.ain');rm=Path(keep['recovery_manifest']);assert p.sha(rm)==keep['recovery_manifest_sha256']
 contracts=prior.CONTRACTS+['required_dungeon_sweep.json','required_sweep_infinite_fix.json'];paths=[mp,ptr,R/'progress.md']+[R/n for n in contracts+[NEW]];snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
 for n in contracts:
  c=p.read(R/n)
  for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
   if k in c:assert c[k]==current['manifest_sha256'],n
 E.mkdir(parents=True)
 for n in ['before','candidate','source']:(E/n).mkdir()
 metadata=[]
 for x,data in snapshots.items():
  if data is not None:p.put(E/'before'/x.name,data)
  metadata.append(dict(path=str(x),name=x.name,existed=data is not None,sha256=p.sha(x) if data is not None else None))
 for n in p.FILES:shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
 for f in O.iterdir():
  if f.is_file() and f.suffix in ['.json','.jam','.png'] and f.name!='native_raw_code.jam':shutil.copy2(f,E/'source'/f.name)
 for n in ['repair_sweep_ui_20260916.py','verify_sweep_ui_20260916.py','publish_sweep_ui_20260916.py','scan_sweep_ui_20260916.ps1']:shutil.copy2(S/n,E/'source'/n)
 p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fx);p.put(E/'journal.json',p.js(j))
 def write(path,data):
  assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
 attempted=False
 try:
  assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
  now=datetime.datetime.now().astimezone().isoformat();rev=dict(status=STATUS,time=now,files=after,evidence=str(E),changed_function_ids=[31892,27936],reward_logic_unchanged=True,native_gameplay_verified=False)
  nm=copy.deepcopy(m);nm.update(status=STATUS,time=now,runtime_verified=False,sweep_ui_revision=rev)
  nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],sweep_ui_overlay=str(E/'source/build_evidence.json'))
  for row in nm['files']:
   if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
  nm['next']='Verify navy sweep confirmation, four-line text padding, remaining-time/count display and Cancel/Execute in game. Reward/day/story code unchanged; prior build story progression confirmed by user.'
  write(mp,p.js(nm));mh=p.sha(mp)
  for n in contracts:
   path=R/n;c=p.read(path)
   for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
    if k in c:c[k]=mh
   if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
   c['sweep_ui_overlay']=str(E/'source/build_evidence.json')
   write(path,p.js(c))
  write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Navy sweep confirmation only: functions31892/27936, type2026091602. Keep82dungeon scope, payout/traps/multipliers/date functions, PACT, translations and save schema unchanged.')))
  write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
  note=f'\n\n### {now} 소탕 확인창 색상·영역 수정\n- 소탕 전용 type2026091602에만 네이비 색상 적용. 24px 글자, 4행, 줄간격8, 제목여백48. 시간과 전투/상자 환산횟수 표시. 취소 우선 유지.\n- AIN31892/27936만 변경. 원래 CODE/STR0/MSG1, 다른 함수, PACT/EX/EXE/FNL 불변. 80개 compiled confirm fixture 및 shippedfont55glyph/폭664이하 확인. 실제 창 렌더 검증은 남음.\n- 사용자가 이전5429AIN으로 소탕 후 메인 스토리 정상 진입을 직접 확인했다고 보고. 전체 보상/저장/재독해 검증과 구분.\n- {len(saves)}개 세이브와 복구용 보존. evidence/rollback: {E}. manifest {mh}.\n'
  write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'));p.exact_tree(rt,nm['files']);assert p.snapshot_saves()==saves;assert p.sha(recovery/'NightRemaster.ain')==rh and p.sha(rm)==keep['recovery_manifest_sha256'];assert len(list((R/'ui_cumulative').glob('*/runtime')))==2
  j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(j))
 except BaseException as error:
  errors=[]
  if attempted:
   try:p.pair_restore(E/'before',rt,before,after)
   except BaseException as x:errors.append(repr(x))
  for x,data in reversed(list(snapshots.items())):
   try:
    if data is None:
     if x.exists():x.unlink()
    else:p.put(x,data)
   except BaseException as x:errors.append(repr(x))
  j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);p.put(E/'journal.json',p.js(j));raise
 report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),changed_function_ids=[31892,27936],unchanged_other_runtime_files=97,unchanged_save_files=len(saves),recovery_unchanged=True,native_gameplay_verified=False,evidence=str(E));p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
 if '--restore' in sys.argv:p.restore()
 elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
 else:main()
