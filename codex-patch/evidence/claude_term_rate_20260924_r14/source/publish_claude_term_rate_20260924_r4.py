"""Claude Opus 5.5 (2026-09-24): transactional install of claude_term_rate r4 over r3.

r4 = r3 + (a) trap results stay readable, also in auto explore: instant disarm, the disarm attempt and every
trap effect dialog also write a line to Codex's dungeon notice (KR_ChestShow; title now 보물상자 · 함정),
(b) homebase achievement panel in the left margin (AddArea), switched by a new mods-tab checkbox
(본거지에 달성률 표시, default off, YoruKR_HomeRate.dat). Rebuilt from the pre-Claude base like r2/r3.
  --verify / --fixture / --restore as in r3.
"""
from pathlib import Path
import copy,datetime,hashlib,json,shutil,sys
import publish_claude_term_rate_20260924 as first
import publish_cheat_menu_20260915 as p
import build_claude_term_rate_20260924_r4 as build
R=build.R;O=build.O;HERE=build.HERE;assert O.name=='claude_term_rate_20260924_r4'
E=R/'evidence/claude_term_rate_20260924_r4'
CONTRACTS=first.CONTRACTS+[first.NEW,'required_claude_term_rate_20260924_r2.json','required_claude_term_rate_20260924_r3.json'];NEW='required_claude_term_rate_20260924_r4.json'
STATUS='CLAUDE_TERM_RATE_R4_INSTALLED_NATIVE_PASS';VERIFIED='CLAUDE_TERM_RATE_R4_STATIC_VM_NATIVE_PASS'
p.O=O;p.E=E;p.FILES=build.FILES
SOURCES=first.SOURCES+['publish_claude_term_rate_20260924_r2.py','ui_probe_claude_term_rate_20260924.py','scan_claude_term_rate_20260924_r2.ps1',
         'publish_claude_term_rate_20260924_r3.py','scan_claude_term_rate_20260924_r3.ps1',
         'claude_home_trap_20260924.jaf','build_claude_term_rate_20260924_r4.py','verify_claude_term_rate_20260924_r4.py',
         'probe_claude_term_rate_20260924_r4.py','home_probe_claude_r4_20260924.py','dungeon_probe_claude_r4_20260924.py',
         'scan_claude_term_rate_20260924_r4.ps1','publish_claude_term_rate_20260924_r4.py']
PROBE_DIRS=['home_probe','dungeon_probe']

def verify():
    ev=p.read(O/'build_evidence.json');files=ev['files'];assert all(p.sha(O/n)==h for n,h in files.items())
    vm=p.read(O/'vm_verification.json');frames=p.read(O/'save_resume_check.json')
    native=p.read(O/'native_probe_result.json');legacy=p.read(O/'native_probe_legacy_result.json')
    for r in [native,legacy]:
        assert r['source_sha256']==files['NightRemaster.ain'] and r.get('exit_code')==0 and not r.get('vm_error') and not r.get('message') and not r.get('timeout') and not r['events'],r.get('log')
    log='\n'.join(native['log']);assert 'FAIL' not in log and log.rstrip().endswith('END')
    for key in ['OLD encode(hook 료) is empty','PASS input: hook proxy, CP949, ASCII, mixed and 5-char names accepted; jamo rejected',
                'PASS eight-term roundtrip','PASS rejected preference write preserves main','VALIDMAIN 0']:assert key in log,key
    lg='\n'.join(legacy['log']);assert 'FAIL' not in lg and lg.rstrip().endswith('END')
    assert 'LOADED 히카리,불지기,쉭쉭이,하자마,토야,진월,진야,호무라 VALIDMAIN 1 MIGRATED 光狩 (호무라)' in lg and 'PASS load keeps main and backup bytes' in lg and 'PASS saved v3, previous v2 main kept as backup' in lg
    home=p.read(O/'home_probe/home_probe_result.json');dungeon=p.read(O/'dungeon_probe/dungeon_probe_result.json')
    for d,r in [('home_probe',home),('dungeon_probe',dungeon)]:
        man=p.read(O/d/'weapon_probe_manifest.json');assert man['source_sha256']==files['NightRemaster.ain'],d
        assert r.get('exit_code')==0 and not r['events'] and not r.get('vm_error') and not r.get('message') and not r.get('timeout'),(d,r.get('log'))
    hl=home['log'];assert hl[1]=='toggle=1' and 'areas=1' in hl and 'toggle part present' in hl and hl[-1]=='SHOT home_probe_4.bmp',hl
    assert home['toggle_file_after']=='YoruKR.HomeRate.1\r\n1\r\n'
    assert dungeon['log'][-1]=='SHOT dungeon_probe_2.bmp',dungeon['log']
    from PIL import Image,ImageChops
    shot=lambda d,n:Image.open(O/d/f'{d}_{n}.png').convert('RGB')
    on=ImageChops.difference(shot('home_probe',0),shot('home_probe',2)).getbbox();off=ImageChops.difference(shot('home_probe',1),shot('home_probe',3)).getbbox()
    box=ImageChops.difference(shot('home_probe',0),shot('home_probe',1)).getbbox()
    assert on is None and off is None and box and box[2]<=160,(on,off,box)
    assert max(max(px) for px in shot('home_probe',1).crop((0,0,160,200)).getdata())==0,'panel must leave no pixels when hidden'
    nbox=ImageChops.difference(shot('dungeon_probe',0),shot('dungeon_probe',2)).getbbox();assert nbox,'dungeon notice must appear'
    scan=p.read(O/'scan_report.json');assert scan['status']=='SCANNED_NO_TARGET_DETECTIONS' and scan['files']==files
    r4=vm['r4']['counts']
    for k,n in [('trap_cell_cases',30),('instant_notice_cases',6),('relieve_notice_cases',2),('trap_dialog_mirrored',3),('relocated_body_is_original_plus_prefix',4),('home_enter_cases',3)]:
        assert r4.get(k)==n,(k,r4.get(k))
    status=dict(status=VERIFIED,author=build.AUTHOR,files=files,
        changes=['trap results kept as dungeon notice lines (instant disarm, disarm attempt, every trap effect dialog); notice title 보물상자 · 함정',
                 'homebase achievement panel in the left margin, mods-tab checkbox 본거지에 달성률 표시 (default off)'],
        vm_counts=vm['counts'],vm_r4_counts=r4,vm_steps=vm['steps'],existing_resume_saves=frames['saves'],saved_return_frames=frames['frames'],existing_save_local_offsets_exact=True,
        old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native_checks_passed=True,
        native=dict(pid=native['pid'],log=native['log'],legacy_pid=legacy['pid'],legacy_log=legacy['log'],home_pid=home['pid'],home_log=home['log'],
                    dungeon_pid=dungeon['pid'],dungeon_log=dungeon['log'],home_panel_diff_box=list(box),dungeon_notice_diff_box=list(nbox)),
        not_verified=['A real trap during auto explore (wrappers covered by VM; notice drawing covered in a resumed dungeon)',
                      'The mods-tab checkbox inside the real config screen (page drawn standalone; sync code is Codex\'s pattern)',
                      'Panel after returning from the config screen during real play'],translator_model=build.AUTHOR)
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
    for folder in ['before','candidate','source']+[f'source/{d}' for d in PROBE_DIRS]:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
        assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
    for file in O.iterdir():
        if file.is_file() and file.suffix in ['.json','.txt','.jaf','.jam','.pactex'] and file.name!='native_raw_code.jam':shutil.copy2(file,E/'source'/file.name)
    for d in PROBE_DIRS:
        for file in (O/d).iterdir():
            if file.is_file() and (file.suffix=='.png' or file.name in [f'{d}_result.json','weapon_probe_manifest.json','claude_probe.txt','probe.jaf']):
                shutil.copy2(file,E/'source'/d/file.name)
    for n in SOURCES:shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['claude_term_rate_r4_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model=build.AUTHOR)
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
                 existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],changed_PACT=[160,177,185],same_length_sites=ev['same_length_sites'],
                 relocated=ev['relocated'],terms=ev['terms'],home_panel=ev['home_panel'],trap_notice=ev['trap_notice'],translator_model=build.AUTHOR)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,claude_term_rate_r4_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],claude_term_rate_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User screen check: trap notice lines during auto explore; mods tab 본거지에 달성률 표시 on -> homebase left panel, off -> gone.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['claude_term_rate_r4_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':(
            'Supersedes r3 (r2/r3 contracts still apply). Trap notices: C_SceneDungeon@StepedOnCell calls KR_T8NoticeInstant (was KR_NoticeInstant), '
            'C_SceneDungeon@Trap calls KR_T8RelieveTrap (was L_Dungeon::RelieveTrap), L_Trap::Execute01-12 call KR_T8TrapDialog (25 sites, was '
            '■シンプルダイアログ) - all same-length swaps; each adds a KR_ChestShow line through KR_T8TrapNotice, which also writes the title '
            '(SceneDungeon KR_ChestTitle, PACT text 보물상자 · 함정) because a resumed dungeon save restores its saved title. KR_T8TrapDialog can sit on a '
            'saved stack during a trap result dialog: later builds must keep it (and KR_T8RelieveTrap) at the same address or rebuild on top of this AIN. '
            'Homebase panel: AddArea.pact group KR_HomeRate (KR_HomeRateTitle/KR_HomeRateBody, hidden by default); C_SceneHomebaseView@BeginTop/EndTop are '
            'relocated with KR_T8HomeEnter/KR_T8HomeLeave prepended; the mods-tab checkbox KR_HomeRateToggle is synced in the relocated '
            'C_ConfigView@EventConfAsraDataForParts/PartsDataForAsra (prepended, Codex pattern); preference file YoruKR_HomeRate.dat (global, default off).')}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,claude_term_rate_r4_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),claude_term_rate_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=(f"\n\n### {now} 함정 결과 알림·본거지 달성률 패널 설치 (Claude Opus 5.5)\n"
              "- 사용자 요청: 자동 탐색에서도 함정을 해제하고 지나갈 때 무엇을 얻었는지/어떤 벌칙을 받았는지 보이게. 원인: 함정 즉시 해제가 켜져 있으면 StepedOnCell이 칸을 조용히 지우고(창 없음), 꺼져 있어도 해제 성공/실패는 0.5초 창뿐. "
              "수정: 즉시 해제·해제 시도(성공 「함정 해제 성공 · 피해 없음」/실패 「함정 해제 실패」)·함정 효과 창 25곳이 모두 코덱스 던전 알림(KR_ChestShow, 3줄 4.5초)에 한 줄씩 남음. 원래 창은 그대로. 알림 제목 보물상자 → 보물상자 · 함정(던전 안 세이브를 불러도 제목이 맞도록 실행 중에도 씀). 함정 해제로 얻는 보상은 원작에 없음.\n"
              "- 사용자 요청: 달성률을 왼쪽 창(본거지 화면 왼쪽 여백)에, 모드 탭 버튼으로 켜고 끄기. 수정: 모드 탭 오른쪽 위 체크박스 「본거지에 달성률 표시」(기본 끔, YoruKR_HomeRate.dat), 켜면 본거지 메뉴가 열릴 때 왼쪽 여백 위쪽에 대사·CG·회상·엔딩·이벤트 다섯 줄(플레이 정보와 같은 집계), 메뉴를 떠나면 숨김. 설정 창을 닫으면 본거지 메뉴가 다시 열리며 바로 반영.\n"
              f"- 검증: VM {qa['vm_steps']}스텝(r3 검사 전부 + r4 20종), 세이브 {qa['existing_resume_saves']}개/복귀 {qa['saved_return_frames']}지점 exact, 네이티브 탐침 4종(입력·이전·본거지 패널 켜기/끄기·던전 알림) 예외 0건, Defender·설치복구 fixture PASS. 실제 자동 탐색 중 함정과 실제 설정 창의 체크박스는 사용자 확인.\n"
              f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}(160 알림 제목·177 AddArea 패널·185 모드 탭); manifest {mh}; evidence {E}; 되돌리기 publish_claude_term_rate_20260924_r4.py --restore.\n")
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
