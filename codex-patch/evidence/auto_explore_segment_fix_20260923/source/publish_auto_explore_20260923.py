"""One-file, hash-bound automatic exploration extension; never writes saves."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_resume_compat_20260923 as previous
import publish_cheat_menu_20260915 as p
R=p.R;O=R/'staging/auto_explore_20260923';E=R/'evidence/auto_explore_20260923';HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_auto_explore_20260923.json'
STATUS='AUTO_EXPLORE_INSTALLED_NATIVE_FIXTURE_PASS_GAMEPLAY_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
 ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
 if E.exists():
  j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
  assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
 assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
 mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
 if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
 for filename,status in [('verification.json','AUTO_EXPLORE_STATIC_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
  check=p.read(O/filename);assert check['status']==status and check['files']==after
 qa=p.read(O/'verification.json');assert qa['existing_save_local_offsets_exact'] and qa['same_length_sites']==7
 probe=p.read(O/'native_probe_results.json');assert probe['status']=='NATIVE_FIXTURE_PASS' and probe['candidate_files']==after and probe['exit_code']==0 and probe['assertions']==25
 assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
 manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
 fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
 saves=p.snapshot_saves();assert saves==p.read(O/'save_hashes_before_build.json')
 keep=p.read(R/'required_build_retention.json');rec=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
 assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
 paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
 assert len(paths)==len(set(x.name for x in paths))
 snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
 for n in CONTRACTS:
  c=p.read(R/n)
  for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
   if k in c:assert c[k]==current['manifest_sha256'],n
 E.mkdir(parents=True);assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
 for folder in ['before','candidate','source']:(E/folder).mkdir()
 metadata=[]
 for path,data in snapshots.items():
  if data is not None:p.put(E/'before'/path.name,data)
  metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
 for n in p.FILES:
  shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
  assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
 assert saves==p.snapshot_saves()
 for f in O.iterdir():
  if f.is_file() and f.suffix in ['.json','.jam']:shutil.copy2(f,E/'source'/f.name)
 for n in ['auto_explore_helpers_20260923.jaf','build_auto_explore_20260923.py','verify_auto_explore_20260923.py','auto_explore_probe_20260923.jaf','build_auto_explore_probe_20260923.py','publish_auto_explore_20260923.py','scan_auto_explore_20260923.ps1','resume_compat_20260923.py','publish_resume_compat_20260923.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:shutil.copy2(HERE/n,E/'source'/n)
 latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
 assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
 full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
 full['auto_explore_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,STR0_prefix_exact=True)
 translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
 p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
 def write(path,data):
  assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
 attempted=False
 try:
  assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
  now=datetime.datetime.now().astimezone().isoformat()
  rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),patched_existing=ev['patched_existing'],same_length_instruction_sites=7,persistent_return_offsets_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,save_writes=0,native_verified=False,native_fixture_assertions=25,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'])
  nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,auto_explore_revision=rev,runtime_verified=False);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],auto_explore_overlay=str(E/'source/build_evidence.json'))
  for row in nm['files']:
   if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
  nm['next']='Native gameplay retest: route OFF visible-only exploration; route ON existing guide; successful enemy/chest/trap resumes; cancel/manual/story stops; new stairs preference follows only this expedition. Existing saves, BGM, summary and mods preserved.'
  write(mp,p.js(nm));mh=p.sha(mp)
  for n in CONTRACTS:
   c=p.read(R/n)
   for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
    if k in c:c[k]=mh
   for file,h in after.items():
    if file in c.get('required_files',{}):c['required_files'][file]=h
   c['auto_explore_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
  write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Keep existing resume-compat entrances and function-local offsets stable. This overlay changes only seven same-length instructions inside original persistent code, appends 23 helpers and redirects six old helper entries. No serialized fields added. Route OFF must not inspect unknown topology or hidden objects. Session stair preference resets at fresh expedition and load. Preserve native combat/rewards/trap probabilities and original guided/puzzle planners. Verify currently saved return offsets before future changes; never rewrite saves. Native fixture passed; actual interactive gameplay not yet verified.')))
  latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),auto_explore_overlay=str(E/'source/build_evidence.json'));write(R/'latest_worked_translation.json',p.js(latest))
  write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
  note=f'\n\n### {now} 자동 탐색 / 이번 탐색 자동 층 이동 설치\n- 경로 안내ON: 기존 최단경로/퍼즐 계획 유지. OFF: IsSteppedOn 또는 IsSeen으로 공개된 통행가능 영역만 탐색. 발견된 다음층→보이는 적/상자/함정→미방문 칸 우선, 최대4걸음 구간 후 재계획. 매프레임 BFS 없음. 숨겨진 통로/출구/물체 조회 없음.\n- 일반 전투 승리·상자·해제 완료 함정 후 같은 맵/층/좌표/제거상태 확인 후 재계획. 도주/패배·미해결 물체·워프·일반이벤트/특수퍼즐상자·수동조작은 중지. 함정은 원작 최고확률 동료 자동선택 경로만 활성화, 원작 성공확률/피해/보상/즉시처치 모드 유지.\n- 기존 다음층 선택에 “이번 탐색은 묻지 않고 이동” 추가. 이후 같은 탐색에서는 묻지 않음. 새 탐색/로드 시 초기화. 층 전환 후 계속 자동이동하되 실패한 전환/취소는 중지, 수동계단에서는 자동이동을 임의 시작하지 않음.\n- 저장호환: 기존CODE내7명령만 동일길이 교체, 영속함수 주소/로컬/CRC/스위치/복귀별칭 보존. 현재RSM 저장{qa["existing_resume_saves"]}개/{qa["saved_return_frames"]}복귀 전량 exact. 23헬퍼추가/기존6헬퍼진입만 변경, 번역MSG1/STR0접두부 유지.\n- 검증: 실제 Sys43엔진 격리진단 PID53596/exit0, 경로/성공재개/취소/층선호 초기화25assertions PASS. 가짜월드/선택창 경계를 쓴 진단이며 실제 플레이 전환·UI 확인은 남음. Defender/설치복구 fixture PASS.\n- 다른97runtime파일/세이브{len(saves)}파일/복구빌드 보존. AIN {after["NightRemaster.ain"]}; manifest {mh}; evidence/rollback {E}.\n- 기존 별도보류: 달력9월 원밖 숫자, 부실 벽글씨 이미지 한국어화. 이벤트 경험률은 이미 모드→플레이 정보에 구현됨.\n'
  write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
  p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves();assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={n:p.sha(rec/n) for n in p.FILES}
  j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(j))
 except BaseException as error:
  errors=[]
  if attempted:
   try:p.pair_restore(E/'before',rt,before,after)
   except BaseException as failure:errors.append(repr(failure))
  for path,data in reversed(list(snapshots.items())):
   try:
    if data is not None:p.put(path,data)
    elif path.exists():path.unlink()
   except BaseException as failure:errors.append(repr(failure))
  j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);p.put(E/'journal.json',p.js(j));raise
 report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=97,unchanged_save_files=len(saves),save_preservation='hash-only; zero save writes',recovery_unchanged=True,native_verified=False,evidence=str(E))
 p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))

if __name__=='__main__':
 if '--restore' in sys.argv:p.restore()
 elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
 else:main()
