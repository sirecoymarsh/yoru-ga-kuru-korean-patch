"""Linear route preview only; retain all current sweep/UI/reward/gameplay data."""
from pathlib import Path
import json,copy,datetime,shutil,sys,hashlib
import publish_dungeon_sweep_20260916 as prior
import publish_cheat_menu_20260915 as p
S=Path(__file__).resolve().parent;R=p.R;O=R/'staging/route_linear_20260916';E=R/'evidence/route_linear_20260916';NEW='required_route_linear_fix.json'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']
STATUS='ROUTE_LINEAR_STATIC_PASS_NATIVE_PENDING'
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
 contracts=prior.CONTRACTS+['required_dungeon_sweep.json','required_sweep_infinite_fix.json','required_sweep_ui_fix.json'];paths=[mp,ptr,R/'progress.md']+[R/n for n in contracts+[NEW]];snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
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
 for n in ['build_route_linear_20260916.py','route_linear_helpers_20260916.jaf','verify_route_linear_20260916.py','publish_route_linear_20260916.py','scan_route_linear_20260916.ps1']:shutil.copy2(S/n,E/'source'/n)
 p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fx);p.put(E/'journal.json',p.js(j))
 def write(path,data):
  assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
 attempted=False
 try:
  assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
  now=datetime.datetime.now().astimezone().isoformat();rev=dict(status=STATUS,time=now,files=after,evidence=str(E),changed_function_ids=ev['patched_function_ids'],added_functions=ev['added_functions'],reward_logic_unchanged=True,native_gameplay_verified=False)
  nm=copy.deepcopy(m);nm.update(status=STATUS,time=now,runtime_verified=False,route_linear_revision=rev)
  nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],route_linear_overlay=str(E/'source/build_evidence.json'))
  for row in nm['files']:
   if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
  nm['next']='Verify route ON movement smoothness, idle, ordinary/departments maps, next floor and reload. Native frame-time improvement remains unmeasured. Sweep UI/rewards/translations unchanged.'
  write(mp,p.js(nm));mh=p.sha(mp)
  for n in contracts:
   path=R/n;c=p.read(path)
   for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
    if k in c:c[k]=mh
   if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
   c['route_linear_overlay']=str(E/'source/build_evidence.json')
   write(path,p.js(c))
  write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Route preview only: five modified functions and three appended helpers. Preserve native passability, row-major nearest goal and department event priorities; retain map/load invalidation. No save schema or reward/UI/translation change.')))
  write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
  note=f'\n\n### {now} 경로 표시 끊김 최적화\n- 이동마다900셀 객체형 비용지도와 출구별AStar를 만들던 경로 표시를 단일 정수배열 BFS로 교체. 같은 좌표에서는 새 배열/탐색함수 진입도 생략. 같은값 setter가 캐시를 지우지 않도록 수정.\n- 일반 계단/백화점202·203·204 목표 우선순위, native통행판정, 층전환/맵갱신/로드 무효화 유지. 글로벌/세이브 스키마 및 원본 CODE/문자열 보존.\n- compiled fixture와 독립 검토, native opcode, 설치/복구 fixture, Defender 통과. 실제 이동 프레임 시간과 체감 개선은 실게임 확인 필요.\n- {len(saves)}개 세이브와 복구용 보존. evidence/rollback: {E}. manifest {mh}.\n'
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
 report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),changed_function_ids=ev['patched_function_ids'],added_functions=ev['added_functions'],unchanged_other_runtime_files=97,unchanged_save_files=len(saves),recovery_unchanged=True,native_gameplay_verified=False,evidence=str(E));p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
 if '--restore' in sys.argv:p.restore()
 elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
 else:main()
