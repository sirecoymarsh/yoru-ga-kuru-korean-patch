"""Claude Opus 5.5 (2026-09-24): transactional install of claude_term_rate r3 over r2.

r3 = r2 + (a) term menu rows and preset titles name the original Japanese word, (b) the text input keeps the
FNL proxy text that the shipped winmm.dll IME hook delivers (the CP949 re-encode turned every typed Hangul
name, e.g. 료, into "" and the rename was refused). Rebuilt from the pre-Claude base like r2.
  --verify / --fixture / --restore as in r2.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys
import publish_claude_term_rate_20260924 as first
import publish_cheat_menu_20260915 as p
import build_claude_term_rate_20260924 as build
R=build.R;O=build.O;HERE=build.HERE;assert O.name=='claude_term_rate_20260924_r3'
E=R/'evidence/claude_term_rate_20260924_r3'
CONTRACTS=first.CONTRACTS+[first.NEW,'required_claude_term_rate_20260924_r2.json'];NEW='required_claude_term_rate_20260924_r3.json'
STATUS='CLAUDE_TERM_RATE_R3_INSTALLED_NATIVE_UI_PASS';VERIFIED='CLAUDE_TERM_RATE_R3_STATIC_VM_NATIVE_UI_PASS'
p.O=O;p.E=E;p.FILES=build.FILES
SOURCES=first.SOURCES+['publish_claude_term_rate_20260924_r2.py','ui_probe_claude_term_rate_20260924.py','scan_claude_term_rate_20260924_r2.ps1',
         'publish_claude_term_rate_20260924_r3.py','scan_claude_term_rate_20260924_r3.ps1']

def verify():
    ev=p.read(O/'build_evidence.json');files=ev['files'];assert all(p.sha(O/n)==h for n,h in files.items())
    vm=p.read(O/'vm_verification.json');frames=p.read(O/'save_resume_check.json')
    native=p.read(O/'native_probe_result.json');legacy=p.read(O/'native_probe_legacy_result.json');control=p.read(O/'native_probe_control.json')
    ui=p.read(O/'ui_probe/ui_probe_results.json')
    for r in [native,legacy,control]:
        assert r['source_sha256']==files['NightRemaster.ain'] and r.get('exit_code')==0 and not r.get('vm_error') and not r.get('message') and not r.get('timeout') and not r['events'],r.get('log')
    log='\n'.join(native['log']);assert 'FAIL' not in log and log.rstrip().endswith('END')
    for key in ['OLD encode(hook 료) is empty','PASS input: hook proxy, CP949, ASCII, mixed and 5-char names accepted; jamo rejected',
                'PASS eight-term roundtrip','PASS rejected preference write preserves main','VALIDMAIN 0']:assert key in log,key
    lg='\n'.join(legacy['log']);assert 'FAIL' not in lg and lg.rstrip().endswith('END')
    assert 'LOADED 히카리,불지기,쉭쉭이,하자마,토야,진월,진야,호무라 VALIDMAIN 1 MIGRATED 光狩 (호무라)' in lg and 'PASS load keeps main and backup bytes' in lg and 'PASS saved v3, previous v2 main kept as backup' in lg
    for k,r in ui.items():
        assert r.get('exit_code')==0 and not r['events'] and not r.get('vm_error') and r['log'][-1]=='END' and r['user_saves_unchanged'] and r['installed_files_unchanged'],k
        assert r['source_sha256']==(ev['source_files']['NightRemaster.ain'] if k.startswith('prev') else files['NightRemaster.ain']),k
    from PIL import Image,ImageChops
    import numpy as np
    same={}
    for n in range(6):
        d=np.array(ImageChops.difference(Image.open(O/f'ui_probe/prev_real/review_ui_{n}.png').convert('RGB'),Image.open(O/f'ui_probe/r2_real/review_ui_{n}.png').convert('RGB')))
        same[n]=not d.any()
    assert same=={0:True,1:False,2:True,3:True,4:True,5:True},same
    assert vm['counts']['menu_japanese_labels']==1 and vm['counts']['japanese_label_glyphs_present']==13 and vm['counts']['legacy_collision_keeps_other_values']==1
    status=dict(status=VERIFIED,author=build.AUTHOR,files=files,changes=['term menu Japanese labels','text input keeps hook proxy text (rename 료 refused)'],
        vm_counts=vm['counts'],vm_steps=vm['steps'],existing_resume_saves=frames['saves'],saved_return_frames=frames['frames'],existing_save_local_offsets_exact=True,
        old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native_checks_passed=True,
        native=dict(pid=native['pid'],log=native['log'],legacy_pid=legacy['pid'],legacy_log=legacy['log']),
        native_ui=dict(runs={k:dict(pid=r['pid'],variant=r['variant'],source_sha256=r['source_sha256']) for k,r in ui.items()},
                       compared_with_r2='only shot 1 (term menu, Japanese labels) differs; synthetic type-2026091602 dialog and both achievement pages pixel-identical'),
        not_verified=['Physical Korean IME typing into the rename/term text box (the hook path is covered by the proxy-input case; the user retests)',
                      'Battle end and sense dialogs during real play','Dungeon name plate on real dungeon screens'],translator_model=build.AUTHOR)
    p.put(O/'verification.json',p.js(status));print(p.js(status).decode('utf8')[:900])

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
    full['claude_term_rate_r3_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model=build.AUTHOR)
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
        rev=dict(status=STATUS,time=now,author=build.AUTHOR,files=after,source_files=before,evidence=str(E),changes=qa['changes'],native_probe_verified=True,
                 native_ui_verified=True,screen_verified=False,persistent_return_offsets_exact=True,MSG1_exact=True,save_schema_changes=0,save_writes=0,
                 existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],changed_PACT=[160],same_length_sites=ev['same_length_sites'],
                 relocated=ev['relocated'],terms=ev['terms'],translator_model=build.AUTHOR)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,claude_term_rate_r3_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],claude_term_rate_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User screen check: rename to 료 (and another Hangul name) through the Korean IME, term menu Japanese labels, a typed custom term.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['claude_term_rate_r3_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':(
            'Supersedes r2 (its contract still applies). Text input: the runtime winmm.dll (hangul_name_v4 IME hook) delivers committed Hangul as FNL proxy '
            'carriers, so KR_KoreanInputEncode (CP949 -> proxy) returns "" for every typed Hangul; KR_PlayerRename and KR_TermMenu now call KR_T8InputDialog '
            '(same-length swap) whose KR_T8InputValue keeps the received text when it is not CP949. Do not re-introduce a CP949-only converter while the hook ships. '
            'Term menu rows/preset titles use KR_T8Label (Japanese source word) via same-length swaps of the two KR_TermDefault calls in KR_TermMenu.')}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,claude_term_rate_r3_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),claude_term_rate_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=(f"\n\n### {now} 용어 메뉴 일본어 이름표·한글 이름 입력 수정 설치 (Claude Opus 5.5)\n"
              "- 사용자 요청: 용어 표기 설정의 각 줄과 표기 선택 제목을 원문 일본어로(光狩·火者·チロ·狭間·凍夜·真月·真夜·火群). 한자·가나는 대체 글자와 겹치지 않고 FNL 4벌 모두 글리프 있음, 실제 엔진 화면 확인.\n"
              "- 사용자 제보: 주인공 이름을 「료」로 바꾸면 '사용 가능한 글자와 길이를 확인해 주세요'. 원인: 실행본 winmm.dll(한글 IME 후크)이 확정 한글을 FNL 대체 글자로 넣는데, 09-23 런타임 회귀 수정의 KR_KoreanInputDialog가 이를 CP949로 보고 다시 변환해 빈 문자열이 됨(실제 엔진에서 OLD encode(hook 료)=\"\" 재현) → 모든 한글 이름·용어 직접 입력이 막혀 있었음. 수정: 이름 변경·용어 메뉴의 입력창 호출을 KR_T8InputDialog로(같은 길이), CP949일 때만 변환하고 아니면 받은 글자 유지. 대체 글자/CP949/영문/혼합/5자 통과, 자모 거부(네이티브).\n"
              f"- 검증: VM {qa['vm_steps']}스텝, 세이브 {qa['existing_resume_saves']}개/복귀 {qa['saved_return_frames']}지점 exact, 네이티브 진단 3종 예외 0건, r2 대비 화면은 용어 메뉴만 다름. Defender·설치복구 fixture PASS. 실제 IME 타이핑은 사용자 확인.\n"
              f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}(변경 없음); manifest {mh}; evidence {E}; 되돌리기 publish_claude_term_rate_20260924_r3.py --restore.\n")
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
