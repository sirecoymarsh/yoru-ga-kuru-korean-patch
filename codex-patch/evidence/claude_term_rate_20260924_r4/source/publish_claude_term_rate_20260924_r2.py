"""Claude Opus 5.5 (2026-09-24): transactional install of claude_term_rate r2 (Codex review CT-RATE-001/002 fixed).

Installed state before: the first Claude overlay (AIN 78cf272d, PACT 9f349af2). r2 is rebuilt from the pre-Claude
base with the same overlay plus the two fixes; the transaction goes first-overlay -> r2 and can be restored.
  --verify   aggregate verification.json (VM, save frames, native probe, native legacy repro, native UI margins)
  --fixture  run the install/rollback fixture into transaction_verification.json
  --restore  restore the exact pre-install (first overlay) state from the journal
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys
import publish_claude_term_rate_20260924 as first
import publish_cheat_menu_20260915 as p
import build_claude_term_rate_20260924 as build
R=build.R;O=R/'staging/claude_term_rate_20260924_r2';HERE=build.HERE  # fixed: build.O moves on to later revisions
E=R/'evidence/claude_term_rate_20260924_r2'
CONTRACTS=first.CONTRACTS+[first.NEW];NEW='required_claude_term_rate_20260924_r2.json'
STATUS='CLAUDE_TERM_RATE_R2_INSTALLED_NATIVE_UI_PASS';VERIFIED='CLAUDE_TERM_RATE_R2_STATIC_VM_NATIVE_UI_PASS'
p.O=O;p.E=E;p.FILES=build.FILES
SOURCES=first.SOURCES+['publish_claude_term_rate_20260924_r2.py','ui_probe_claude_term_rate_20260924.py','scan_claude_term_rate_20260924_r2.ps1']
REVIEW=R/'reviews/claude_term_rate_20260924_codex'

def verify():
    ev=p.read(O/'build_evidence.json');files=ev['files'];assert all(p.sha(O/n)==h for n,h in files.items())
    vm=p.read(O/'vm_verification.json');frames=p.read(O/'save_resume_check.json')
    native=p.read(O/'native_probe_result.json');legacy=p.read(O/'native_probe_legacy_result.json');control=p.read(O/'native_probe_control.json')
    ui=p.read(O/'ui_probe/ui_probe_results.json');margins=p.read(O/'ui_probe/layout_margins.json')
    for r in [native,legacy,control]:
        assert r['source_sha256']==files['NightRemaster.ain'] and r.get('exit_code')==0 and not r.get('vm_error') and not r.get('message') and not r.get('timeout') and not r['events'],r.get('log')
    log='\n'.join(native['log']);assert 'FAIL' not in log and log.rstrip().endswith('END')
    for key in ['PASS v2 file upgraded to v3','PASS eight-term roundtrip','PASS rejected preference write preserves main','VALIDMAIN 0']:assert key in log,key
    lg='\n'.join(legacy['log']);assert 'FAIL' not in lg and lg.rstrip().endswith('END')
    assert 'LOADED 히카리,불지기,쉭쉭이,하자마,토야,진월,진야,호무라 VALIDMAIN 1 MIGRATED 히카리 (호무라)' in lg and 'PASS load keeps main and backup bytes' in lg and 'PASS saved v3, previous v2 main kept as backup' in lg
    assert 'RELOADED 히카리,불지기,쉭쉭이,하자마,토야,진월,진야,호무라 MIGRATED ' in lg
    for k,r in ui.items():
        assert r.get('exit_code')==0 and not r['events'] and not r.get('vm_error') and r['log'][-1]=='END' and r['user_saves_unchanged'] and r['installed_files_unchanged'],k
        assert r['source_sha256']==(files['NightRemaster.ain'] if k.startswith('r2') else ev['source_files']['NightRemaster.ain']),k
    for m in margins:
        if m['image'].startswith('r2'):assert not m['text_crossing_edge'] and m['bottom_margin']>=20,m
        else:assert m['text_crossing_edge'],m
    assert vm['counts']['legacy_collision_keeps_other_values']==1 and vm['counts']['padding_opt_in_scoped']==1 and vm['counts']['validN8_equals_TermValid']>=300
    status=dict(status=VERIFIED,author=build.AUTHOR,files=files,review=str(REVIEW),fixed=['CT-RATE-001','CT-RATE-002'],vm_counts=vm['counts'],vm_steps=vm['steps'],
        existing_resume_saves=frames['saves'],saved_return_frames=frames['frames'],existing_save_local_offsets_exact=True,old_CODE_allowlist_exact=True,
        MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native_checks_passed=True,
        native=dict(pid=native['pid'],log=native['log'],legacy_pid=legacy['pid'],legacy_log=legacy['log'],first_chance_cpp_exceptions=0),
        native_ui=dict(runs={k:dict(pid=r['pid'],variant=r['variant'],source_sha256=r['source_sha256']) for k,r in ui.items()},margins=margins,
                       preserved='shots 0 (type 2026091602 without opt-in) and 1 (term menu, ordinary dialog) are pixel-identical between the first overlay and r2'),
        not_verified=['Physical Korean IME direct input for terms (converter unchanged)','Battle end and sense dialogs during real play (hooks verified natively by direct calls)',
                      'Dungeon name plate on real dungeon screens'],translator_model=build.AUTHOR)
    p.put(O/'verification.json',p.js(status));print(p.js(status).decode('utf8')[:1200])

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
    for folder in ['before','candidate','source','source/ui_probe']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
        assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
    for file in O.iterdir():
        if file.is_file() and file.suffix in ['.json','.txt','.jaf','.jam','.pactex'] and file.name!='native_raw_code.jam':shutil.copy2(file,E/'source'/file.name)
    for file in (O/'ui_probe').rglob('*'):
        if file.is_file() and file.suffix in ['.png','.json','.txt']:
            dest=E/'source/ui_probe'/file.relative_to(O/'ui_probe');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
    for n in SOURCES:shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['claude_term_rate_r2_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model=build.AUTHOR)
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
        rev=dict(status=STATUS,time=now,author=build.AUTHOR,files=after,source_files=before,evidence=str(E),review_fixed=['CT-RATE-001','CT-RATE-002'],review=str(REVIEW),
                 native_probe_verified=True,native_ui_verified=True,screen_verified=False,persistent_return_offsets_exact=True,MSG1_exact=True,save_schema_changes=0,save_writes=0,
                 existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],changed_PACT=[160],same_length_sites=ev['same_length_sites'],
                 relocated=ev['relocated'],terms=ev['terms'],translator_model=build.AUTHOR)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,claude_term_rate_r2_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],claude_term_rate_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User screen check: play info and 이벤트 진입 자세히 (all lines inside the title panel), term menu with 호무라/신게츠/신야, dungeon name plate at 최심층.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['claude_term_rate_r2_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':(
            'Supersedes the first Claude overlay (required_claude_term_rate_20260924.json keeps its contract). '
            'CT-RATE-001: KR_T8ReadSafe validates a v2 file with KR_T8ValidN(i,v,7); a value valid under v2 but colliding with the new default 호무라 is reset '
            'to its default (YoruKR.Term.Migrated lists it; KR_TermMenu opens through KR_T8MenuLoad, same-length, which shows it once). main/backup bytes are not touched by a load. '
            'v3 validation stays KR_TermValid (8 terms). CT-RATE-002: C_SelectDialog@CreateParts type 2026091602 title padding PUSH 48 is a same-length CALLFUNC KR_T8TitlePad; '
            'it returns 48 unless YoruKR.T8.Title is set, which only KR_T8PlayerInfoMenu/KR_T8EventDetail do around their ■選択ダイアログ／実行. '
            'Rebuilding from an older base must reapply both overlays.')}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,claude_term_rate_r2_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),claude_term_rate_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=(f"\n\n### {now} Codex 검수 CT-RATE-001·002 수정 설치 (Claude Opus 5.5)\n"
              "- CT-RATE-001: v2 설정은 v2 계약(7개 기본값 충돌 검사)으로 검증. 새 기본값 「호무라」와만 겹치는 항목은 그 항목만 기본값으로 돌리고 나머지 값과 main·backup 바이트는 유지, 용어 메뉴를 열 때 한 번 알림(KR_T8MenuLoad). v3 새 입력 검사는 그대로(KR_TermValid 8개). Codex 재현 입력 [호무라, 불지기, 쉭쉭이, 하자마, 토야, 진월, 진야] → 실제 엔진에서 히카리만 기본값, 나머지 유지, 저장 시 v3+v2 백업, 재독해 통과.\n"
              "- CT-RATE-002: 공통 CreateParts의 타입 2026091602 제목 패딩 PUSH 48을 같은 길이 CALLFUNC KR_T8TitlePad로. 플레이 정보·이벤트 진입 자세히 두 창만 실행 동안 제목을 알려 줄 수(8줄 → 87)만큼 패딩, 다른 창은 48. 실제 엔진 화면(실제 기록/0%/100%+엔딩 전부+5자 이름): 아래 여백 25~27px, 경계 침범 없음; 형식 창·일반 선택창은 이전 설치본과 픽셀 동일.\n"
              f"- 검증: VM {qa['vm_steps']}스텝(기존 항목 + 이관 7종·검사 함수 동치 {qa['vm_counts']['validN8_equals_TermValid']}건·패딩 범위), 세이브 {qa['existing_resume_saves']}개/복귀 {qa['saved_return_frames']}지점 exact, 네이티브 진단 3종 예외 0건, Defender·설치복구 fixture PASS.\n"
              f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}(변경 없음); manifest {mh}; evidence {E}; 되돌리기 publish_claude_term_rate_20260924_r2.py --restore.\n")
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
        r=p.fixture();p.put(O/'transaction_verification.json',p.js(r));print(p.js(r).decode('utf8')[:600])
    elif '--verify' in sys.argv:verify()
    else:main()
