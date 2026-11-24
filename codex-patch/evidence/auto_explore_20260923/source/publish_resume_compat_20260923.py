"""One-file, hash-bound load compatibility fix; never writes saves."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_player_tools_20260923 as previous
import publish_cheat_menu_20260915 as p
R=p.R;O=R/'staging/load_error_20260923';E=R/'evidence/resume_compat_20260923';HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_resume_compat_20260923.json'
STATUS='RESUME_COMPAT_INSTALLED_STATIC_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
 ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
 if E.exists():
  j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
  assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
 assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
 mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
 if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
 for filename,status in [('verification.json','RESUME_COMPAT_STATIC_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
  check=p.read(O/filename);assert check['status']==status and check['files']==after
 qa=p.read(O/'verification.json');assert qa['existing_resume_saves']==37 and qa['saved_return_frames']==950 and qa['shim_entry_count']==9
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
 for n in ['resume_compat_20260923.py','build_resume_compat_20260923.py','verify_resume_compat_20260923.py','publish_resume_compat_20260923.py','scan_resume_compat_20260923.ps1','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:shutil.copy2(HERE/n,E/'source'/n)
 latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
 assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
 full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
 full['resume_compat_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_STR0_exact=True)
 translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
 p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
 def write(path,data):
  assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
 attempted=False
 try:
  assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
  now=datetime.datetime.now().astimezone().isoformat()
  rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),patched_existing=ev['patched_existing'],old_CODE_STR0_MSG1_exact=True,save_schema_changes=0,save_writes=0,native_verified=False,existing_saves_checked=37,frames_checked=950,redirected_frames=32,shim_entry_count=9)
  nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,resume_compat_revision=rev,runtime_verified=False);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],resume_compat_overlay=str(E/'source/build_evidence.json'))
  for row in nm['files']:
   if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
  nm['next']='Native retest: load the same dungeon save that failed (including slot36), move, save into a spare slot and reload. Existing saves untouched. Player Info native retest also remains pending.'
  write(mp,p.js(nm));mh=p.sha(mp)
  for n in CONTRACTS:
   c=p.read(R/n)
   for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
    if k in c:c[k]=mh
   for file,h in after.items():
    if file in c.get('required_files',{}):c['required_files'][file]=h
   c['resume_compat_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
  write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Keep compatibility entrances and current live body relative positions stable in persistent methods21031/28637/28642/28664. Old CODE prefix and unchanged CRC alone do NOT guarantee save compatibility. Run return-record audit on current saves and check all saved function-local offsets before further method insertions. Never rewrite or reset saves. Native reload not verified yet.')))
  latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),resume_compat_overlay=str(E/'source/build_evidence.json'));write(R/'latest_worked_translation.json',p.js(latest))
  write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
  note=f'\n\n### {now} 던전 저장 로딩 오류 — 복귀 오프셋 호환 패치 설치\n- 사용자 확인: 던전 안에서 만든 저장을 불러올 때 구조체 페이지0 및 C_SceneDungeon@SetMotionWaitInForceStop 오류.\n- 원인 증거: NightR36의 Run 로컬복귀0x9e2가 자동이동 코드 추가 후 PUSH28652로 바뀌어 PUSHSTRUCTPAGE를 건너뜀. 정상 복귀 POP는 새 본문0xa30. 이름변경/이벤트율 기능을 되돌리는 방식이 아니라 누적 모드의 저장 복귀 호환 처리.\n- 현재 37개RSM14 저장의950복귀위치 전량대조. 4함수(21031/28637/28642/28664),9호환진입점으로32저장프레임 연결. 함수CRC/로컬/구조체/글로벌 보존, 현재 본문은 절대분기주소 이동 외 바이트동일. 정상호출은 호환표를 건너뛰며 최신 자동이동/번역/모드 유지.\n- 검증: compiled 바이트·새 저장 상대오프셋 산술·native opcode지원·Defender·설치/복구/중단/tamper fixture PASS. 실제 같은 던전 저장 로딩·이동·다른 슬롯 저장/재로딩은 사용자 재검증 필요. 외부 임의구버전 저장 전체 호환을 주장하지 않음.\n- 세이브{len(saves)}파일 모두 해시보존/쓰기0, 다른97runtime파일 및 복구빌드 보존. AIN {after["NightRemaster.ain"]}; manifest {mh}; evidence/rollback {E}.\n- 후속 작업은 required_resume_compat_20260923.json의 복귀 오프셋 계약을 지킬 것. CODE 접두부/CRC 보존만으로 로딩호환을 선언하지 말 것.\n'
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
