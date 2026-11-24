"""Apply two hash-bound data files only, with verified rollback and save protection."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys,json
import publish_cheat_menu_20260915 as p
import publish_loot_notice_20260915 as old
W=Path(__file__).resolve().parent;O=W/'dungeon_skip_20260916';R=p.R;RT=p.RT;E=R/'evidence/dungeon_sweep_20260916'
CONTRACTS=old.CONTRACTS+['required_loot_notice.json'];NEW='required_dungeon_sweep.json';STATUS='SWEEP_STATIC_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain','NightRemasterPact.afa']
def main():
 ev=p.read(O/'build_evidence.json');after=ev['files'];before=ev['source_files']
 for file,status in [('verification.json',STATUS),('release_checks.json','RELEASE_STATIC_PASS'),('independent_review.json','STATIC_REVIEW_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
  v=p.read(O/file);assert v['status']==status and v['files']==after,file
 assert all(p.sha(O/n)==after[n] for n in p.FILES)
 ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
 if E.exists():
  j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256'];assert all(p.sha(RT/n)==after[n] for n in p.FILES);print('ALREADY_INSTALLED');return
 assert current==ev['source_pointer'];mp=Path(current['manifest']);assert p.sha(mp)==current['manifest_sha256'];m=p.read(mp);rt=Path(current['runtime']).resolve();assert rt==RT.resolve()
 if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
 fx=p.fixture();p.exact_tree(rt,m['files']);assert all(p.sha(rt/n)==before[n] for n in p.FILES);assert p.sha(rt/'NightRemasterEX.ex')==ev['EX_unchanged_sha256']
 keep=p.read(R/'required_build_retention.json');rm=Path(keep['recovery_manifest']);rec=Path(keep['recovery_runtime']);assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
 saved=p.snapshot_saves();paths=[mp,ptr,R/'progress.md']+[R/n for n in CONTRACTS+[NEW]];snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
 for n in CONTRACTS:
  c=p.read(R/n)
  for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
   if key in c:assert c[key]==current['manifest_sha256'],n
 E.mkdir(parents=True)
 for n in ['before','candidate','source']:(E/n).mkdir()
 metadata=[]
 for x,data in snapshots.items():
  if data is not None:p.put(E/'before'/x.name,data)
  metadata.append(dict(path=str(x),name=x.name,existed=data is not None,sha256=p.sha(x) if data is not None else None))
 for n in p.FILES:
  shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n);assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
 for f in O.iterdir():
  if f.is_file() and f.suffix in ['.json','.jam','.pactex','.png','.jaf'] and f.name!='native_sweep_raw_code.jam':shutil.copy2(f,E/'source'/f.name)
 for n in ['build_dungeon_sweep_20260916.py','verify_dungeon_sweep_20260916.py','sweep_release_checks_20260916.py','publish_dungeon_sweep_20260916.py','scan_dungeon_sweep_final_20260916.ps1','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py','audit_sys43_native_opcodes_20260915.py']:
  shutil.copy2(W/n,E/'source'/n)
 p.put(E/'save_hashes_before.json',p.js(saved));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fx);p.put(E/'journal.json',p.js(j))
 def write(x,data):
  assert x in snapshots;j.setdefault('metadata_after',{})[str(x)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(x,data)
 attempted=False
 try:
  assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
  now=datetime.datetime.now().astimezone().isoformat();nm=copy.deepcopy(m)
  rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),previous_manifest_sha256=current['manifest_sha256'],AIN=ev['AIN'],PACT=ev['PACT'],native_gameplay_verified=False,save_schema_unchanged=True,translator_model='Codex internal')
  nm.update(status=STATUS,time=now,runtime_verified=False,dungeon_sweep_revision=rev)
  nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],dungeon_sweep_overlay=str(E/'source/build_evidence.json'),inherited_evidence_scope='Latest baseline preserved, exact original CODE/STR0/MSG1/switches/serialized metadata retained. Scope-gated existing function hooks and new sweep helpers only. Native gameplay and save/reload pending.')
  for row in nm['files']:
   if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
  nm['next']='Options > Mods > 소탕 (default OFF). In ordinary dungeon check button, Cancel, Execute, receipt, native day end; story dungeon must never show button. Native gameplay and actual save/reload pending.'
  write(mp,p.js(nm));mh=p.sha(mp)
  for n in CONTRACTS:
   x=R/n;c=p.read(x)
   for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
    if key in c:c[key]=mh
   for file,h in after.items():
    if file in c.get('required_files',{}):c['required_files'][file]=h
   c['dungeon_sweep_overlay']=str(E/'source/build_evidence.json');write(x,p.js(c))
  instruction='Ordinary-dungeon sweep only: flag99 tag20260916 default OFF; button requires exact ordinary80 whitelist and live context. Cancel first; explicit confirm; separate RNG; native payout/chest rates and caps; scalar rollback on controlled false; config locked during confirm/receipt; remaining-time exhaustion then original day-end block exactly once. Fatal VM exceptions cannot be caught; no save during transaction. No story/special floors, no save schema changes. Native gameplay pending. Preserve current translations, UI, opening and all prior mods.'
  write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction=instruction,reward_policy=str(E/'source/reward-policy.json'))));write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
  note=f'\n\n### {now[:10]} 일반 던전 소탕 — 적용, 게임 검증 대기\n- 모드 탭 소탕(default OFF), 일반80개층 자동 소탕 버튼, 취소 우선 확인창. R/40 전투 및 R/200 상자를 현재 층 원작 지급 경로로 처리하는 명시적 대체 보상 정책. 무한 던전 전체 보상을 주장하지 않음.\n- 확인/결과 중 설정 재진입 차단, 보상 중 UI yield 없음, 별도 난수, 전체 보상 scalar snapshot과 controlled failure 복구, 정상 시간 소진/던전 종료 체인. 직접 날짜 변경 없음.\n- 새 버튼은 원본 native tab CG5상태138x42, 글자는 별도1:1 FNL259. PACT161/185만 변경, 다른185entry와 raster/font/EX/exe 그대로.\n- compiled fixture: scope10002IDs, rollback7, RNG4000, EXP36, 시간경계11, 취소/중복/모달변경/잠금/6초결과cleanup 검사. HLL/payout 경계는 fixture이며 네이티브 실행 증거가 아님. 지원opcode/해시/원본lambda14/Defender/설치복구fixture 및 읽기전용독립검토 통과.\n- {len(saved)} save hashes 및 recovery unchanged;96other runtimefiles exact. Evidence/rollback: {E}. Manifest {mh}.\n- 남음: 실제 게임에서 토글→취소→소탕→보상·레벨·다음날, 스토리 제외, 재시작설정/세이브로드, 실제성능 확인. 전 게임 한국어화 완료 아님.\n'
  write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'));p.exact_tree(rt,nm['files']);assert saved==p.snapshot_saves()
  assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={n:p.sha(rec/n) for n in p.FILES};assert len(list((R/'ui_cumulative').glob('*/runtime')))==2
  j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(j))
 except BaseException as error:
  errors=[]
  if attempted:
   try:p.pair_restore(E/'before',rt,before,after)
   except BaseException as x:errors.append(repr(x))
  for x,data in reversed(list(snapshots.items())):
   try:
    if data is not None:p.put(x,data)
    elif x.exists():x.unlink()
   except BaseException as x:errors.append(repr(x))
  j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);p.put(E/'journal.json',p.js(j));raise
 report=dict(status=STATUS,runtime=str(rt),manifest_sha256=mh,files=after,unchanged_other_runtime_files=96,save_files_hashes_unchanged=len(saved),recovery_build_unchanged=True,native_gameplay_verified=False,evidence=str(E));p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
 if '--restore' in sys.argv:p.restore()
 elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
 else:main()
