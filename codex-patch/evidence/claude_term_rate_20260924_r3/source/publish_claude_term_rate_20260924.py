"""Claude Opus 5.5 (2026-09-24): transactional install of the claude_term_rate candidate.

Same transaction as publish_runtime_repairs_20260923.py (Codex): hash-bound pair apply, metadata
snapshot, rollback on any failure, recovery build untouched, user saves read-only.
  --verify   aggregate verification.json from the VM, save-frame and native probe evidence
  --fixture  run the install/rollback fixture into transaction_verification.json
  --restore  restore the exact pre-install state from the journal
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys
import publish_runtime_repairs_20260923 as previous
import publish_cheat_menu_20260915 as p
import build_claude_term_rate_20260924 as build
R=build.R;O=build.O;E=R/'evidence/claude_term_rate_20260924';HERE=build.HERE
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_claude_term_rate_20260924.json'
STATUS='CLAUDE_TERM_RATE_INSTALLED_NATIVE_PROBE_PASS';VERIFIED='CLAUDE_TERM_RATE_STATIC_VM_NATIVE_PASS'
p.O=O;p.E=E;p.FILES=build.FILES
SOURCES=['claude_term_rate_20260924.jaf','build_claude_term_rate_20260924.py','verify_claude_term_rate_20260924.py','probe_claude_term_rate_20260924.py',
         'publish_claude_term_rate_20260924.py','scan_claude_term_rate_20260924.ps1','diagnostic_audio_20260923.py']

def verify():
    ev=p.read(O/'build_evidence.json');files=ev['files'];assert all(p.sha(O/n)==h for n,h in files.items())
    vm=p.read(O/'vm_verification.json');frames=p.read(O/'save_resume_check.json');native=p.read(O/'native_probe_result.json')
    base=p.read(O/'native_probe_base_control.json');control=p.read(O/'native_probe_control.json')
    assert native['source_sha256']==files['NightRemaster.ain'] and native.get('exit_code')==0 and not native.get('vm_error') and not native.get('message') and not native.get('timeout')
    log='\n'.join(native['log']);assert 'FAIL' not in log and log.rstrip().endswith('END')
    for key in ['PASS v2 file upgraded to v3','PASS eight-term roundtrip','PASS rejected preference write preserves main','VALIDMAIN 0']:assert key in log,key
    # First-chance C++ exceptions: identical count on the installed base AIN with the same boot-only probe.
    assert len(native['events'])==len(control['events'])==len(base['events']) and base.get('exit_code')==0 and control.get('exit_code')==0
    assert all(x==native['events'][0] for x in native['events']+control['events']+base['events'])
    status=dict(status=VERIFIED,author=build.AUTHOR,files=files,vm_counts=vm['counts'],vm_steps=vm['steps'],existing_resume_saves=frames['saves'],saved_return_frames=frames['frames'],
        existing_save_local_offsets_exact=True,old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native_checks_passed=True,
        native=dict(pid=native['pid'],probe_sha256=native['probe_sha256'],log=native['log'],first_chance_cpp_exceptions=len(native['events']),
                    same_exceptions_on_installed_base_boot=len(base['events'])),
        info_page=vm['info_page'],detail_page=vm['detail_page'],
        not_verified=['On-screen layout of the 10-row term menu, the info page and the widened dungeon name plate (user screen check)',
                      'Physical Korean IME direct input for terms (unchanged converter; covered by Codex native domain test)',
                      'Battle end and sense dialogs during real play (hooks verified natively by direct calls)'],translator_model=build.AUTHOR)
    p.put(O/'verification.json',p.js(status));print(p.js(status).decode('utf8')[:1500])

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json'),'current.json moved since the build: rebuild on the newer install'
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for name,status in [('verification.json',VERIFIED),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/name);assert check['status']==status and check['files']==after,name
    fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    saves=p.snapshot_saves()
    keep=p.read(R/'required_build_retention.json');rec=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
    assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths));snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
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
    for file in O.iterdir():
        if file.is_file() and file.suffix in ['.json','.txt','.jaf','.jam','.pactex'] and file.name!='native_raw_code.jam':shutil.copy2(file,E/'source'/file.name)
    for n in SOURCES:shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['claude_term_rate_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model=build.AUTHOR)
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    qa=p.read(O/'verification.json')
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,author=build.AUTHOR,files=after,source_files=before,evidence=str(E),native_probe_verified=True,screen_verified=False,
                 persistent_return_offsets_exact=True,MSG1_exact=True,save_schema_changes=0,save_writes=0,existing_saves_checked=qa['existing_resume_saves'],
                 frames_checked=qa['saved_return_frames'],changed_PACT=[160],same_length_sites=ev['same_length_sites'],relocated=ev['relocated'],
                 terms=ev['terms'],preference_file='YoruKR.Terms.3 (8 values); v2 (7 values) still read, 호무라 default',translator_model=build.AUTHOR)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,claude_term_rate_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],claude_term_rate_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User screen check: term menu (8 rows), 호무라/신게츠/신야 presets, dungeon name plate width at 최심층, battle-end and sense texts with a changed 히카리, weapon id_092 comment, item creation 카샤의 영약, play-info page and 이벤트 진입 자세히.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['claude_term_rate_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':(
            'Claude overlay. Eight terms (index 7 호무라 new; presets 참된 달→신게츠, 참된 밤→신야). Preference file YoruKR.Terms.3 with 8 values; KR_T8ReadSafe also reads v2. '
            'Existing helpers redirect to KR_T8*: KR_TermDefault/Preset/Cap/Message/Display/ReadSafe/SaveSafe and KR_PlayerInfoMenu. Loops over terms use 8 (same-length PUSH edits in '
            'KR_TermMenu/Refresh/Load/Valid). Dungeon names (狭間 10, 火群 61) follow the chosen term even at defaults; the SceneDungeon name plate is 324x36. '
            'C_BattleMessageView@Printf calls KR_T8BattleText and L_Dungeon::Sense pushes KR_T8SenseFormat (same-length). L_Weapon::GetComment and C_ConsumeItem@sMoldName getters apply KR_TermDisplay. '
            'Play info shows engine-wide read rate over 74,966 event messages, CG 60 cells, recollection 66 numbers and 5 endings; the per-save event rate moved to its detail page. '
            'When rebuilding from an older base, reapply this overlay instead of dropping it.')}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,claude_term_rate_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),claude_term_rate_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        n=qa['native']
        note=(f"\n\n### {now} 용어 선택·달성률 완성 설치 (Claude Opus 5.5)\n"
              "- 용어 8개: 호무라(火群) 추가(호무라/화군/불무리), 참된 달·참된 밤의 셋째 후보를 일본어 발음 신게츠(真月 しんげつ, 음성 1188·1471 받아쓰기)·신야(真夜 루비)로. 설정 파일 YoruKR.Terms.3(8값), v2 파일도 읽음(호무라 기본값).\n"
              "- 대사 밖 누락 6곳 연결: 전투 종료(Printf), 기척 감지(Sense 서식), 서양관 내부 틈 1~5, 무기 설명 id_092(GetComment), 무기 제작 설명(ADV 연결문), 아이템 제작 메뉴(sMoldName). 던전 이름(狭間 10·火群 61)은 기본값에서도 용어를 따름(사용자 결정) → 던전 이름판 300→324px(PACT 160).\n"
              f"- 플레이 정보: 대사 완독률(전역 읽음 표시, 본편 이벤트 74,966줄), CG 60칸, 회상 66, 엔딩 5(본 결말만 이름), 이 저장의 이벤트 진입률은 '이벤트 진입 자세히'로.\n"
              f"- 검증: VM(MSG1 100,944 기본값 동일, 시나리오 3종 5,370행·동적 72페이지·폭, 저장/복구/메뉴), 세이브 {qa['existing_resume_saves']}개/복귀 {qa['saved_return_frames']}지점 exact, 격리·음소거 네이티브 진단 통과(대사 21,109줄 98ms 등; 부팅 C++ 1차 예외 {n['first_chance_cpp_exceptions']}건은 설치본 부팅에서도 동일). Defender·설치복구 fixture PASS. 화면 확인은 사용자 몫.\n"
              f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}; manifest {mh}; evidence {E}.\n")
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves();assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={x:p.sha(rec/x) for x in p.FILES}
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
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_save_files=len(saves),recovery_unchanged=True,evidence=str(E),author=build.AUTHOR)
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--fixture' in sys.argv:
        r=p.fixture();p.put(O/'transaction_verification.json',p.js(r));print(p.js(r).decode('utf8')[:800])
    elif '--verify' in sys.argv:verify()
    else:main()
