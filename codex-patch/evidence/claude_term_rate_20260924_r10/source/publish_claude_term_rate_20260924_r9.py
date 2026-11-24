"""Claude Opus 5.5 (2026-09-24): transactional install of claude_term_rate r9 over r7 (r8 was never installed).

r9 = r8 + 「캐릭터별 남은 이벤트」 in 플레이 정보 (user: 「달성률에서 각 캐릭터별로 몇월 며칠의 어느 이벤트가 비어있는지」):
per character, this save's unseen events by month and kind (after-training talks by month with passed months apart,
smitten talks, training/Saturday invitations, dungeon walks by partner) and the date windows / intimacy conditions of
personal and main-story events with 「지남」. Counts and conditions only - no titles.

r8 = r7 + daily and weekly autosaves (user: 「일간 자동 세이브랑 주간 자동 세이브를 분리」): the game's own day-start autosave
runs every morning; Mondays write the weekly slot 49 (page 10, 「주간」), other days 999 (「일간」); dungeon rest cells and the
ending keep writing 999. The weekly slot is locked in the save screen, skipped by the newest-manual search, gets 999's
label font and save comment; the game-over resume loads the newer autosave. Payload AIN + PACT + EX (PACT/EX = r7).

r7 docstring:


r7 = r6 + eight monster names localized in EX block 7 (user decisions: 맥, 날름날름, 소머리, 무지갯빛 새, 털뭉치,
푸른 털뭉치, 범고래호랑이, 불바퀴) + Codex review CT-RATE-003 (home-rate toggle commits only after a verified write).
The payload is AIN + PACT + EX; Codex's CG archive is not touched.

r6 docstring:

r6 = r5 + the sweep report names the rewards the carry limit kept out (consumables at their cap; element stones
clamped at 99: attempts minus gains), in place of the fixed 「소지 한도를 넘은 보상은 제외됩니다.」; stones keep their colour.

r5 docstring:

r5 = r4 + (a) result texts in colour with the engine's ${font r= g= b=} tags: treasure and trap lines (Codex dungeon
notice), the instant-kill receipt, the sweep report dialog (C_MessageDialog switches tag processing on only for
tagged text); (b) per-character event rates (this save) in the homebase panel. Rebuilt from the pre-Claude base.
  --verify / --fixture / --restore as in r4.
"""
from pathlib import Path
import copy,datetime,hashlib,json,math,shutil,sys
import publish_claude_term_rate_20260924 as first
import publish_cheat_menu_20260915 as p
import build_claude_term_rate_20260924_r9 as build
R=build.R;O=build.O;HERE=build.HERE;assert O.name=='claude_term_rate_20260924_r9'
E=R/'evidence/claude_term_rate_20260924_r9'
CONTRACTS=first.CONTRACTS+[first.NEW,'required_claude_term_rate_20260924_r2.json','required_claude_term_rate_20260924_r3.json',
                           'required_claude_term_rate_20260924_r4.json','required_claude_term_rate_20260924_r5.json',
                           'required_claude_term_rate_20260924_r6.json','required_club_wall_bilingual_20260924.json','required_club_wall_cancel_20260924.json',
                           'required_claude_term_rate_20260924_r7.json'];NEW='required_claude_term_rate_20260924_r9.json'
STATUS='CLAUDE_TERM_RATE_R9_INSTALLED_NATIVE_PASS';VERIFIED='CLAUDE_TERM_RATE_R9_STATIC_VM_NATIVE_PASS'
p.O=O;p.E=E;p.FILES=build.FILES
SOURCES=first.SOURCES+['publish_claude_term_rate_20260924_r2.py','ui_probe_claude_term_rate_20260924.py','scan_claude_term_rate_20260924_r2.ps1',
         'publish_claude_term_rate_20260924_r3.py','scan_claude_term_rate_20260924_r3.ps1',
         'claude_home_trap_20260924.jaf','build_claude_term_rate_20260924_r4.py','verify_claude_term_rate_20260924_r4.py',
         'probe_claude_term_rate_20260924_r4.py','home_probe_claude_r4_20260924.py','dungeon_probe_claude_r4_20260924.py',
         'scan_claude_term_rate_20260924_r4.ps1','publish_claude_term_rate_20260924_r4.py',
         'claude_colors_20260924.jaf','claude_home_trap_20260924_r5.jaf','build_claude_term_rate_20260924_r5.py','verify_claude_term_rate_20260924_r5.py',
         'probe_claude_term_rate_20260924_r5.py','home_probe_claude_r5_20260924.py','dungeon_probe_claude_r5_20260924.py','tag_probe_claude_20260924.py',
         'scan_claude_term_rate_20260924_r5.ps1','publish_claude_term_rate_20260924_r5.py',
         'claude_colors_20260924_r6.jaf','build_claude_term_rate_20260924_r6.py','verify_claude_term_rate_20260924_r6.py','probe_claude_term_rate_20260924_r6.py',
         'home_probe_claude_r6_20260924.py','dungeon_probe_claude_r6_20260924.py','scan_claude_term_rate_20260924_r6.ps1','publish_claude_term_rate_20260924_r6.py',
         'claude_home_trap_20260924_r7.jaf','build_claude_term_rate_20260924_r7.py','verify_claude_term_rate_20260924_r7.py','probe_claude_term_rate_20260924_r7.py',
         'home_probe_claude_r7_20260924.py','dungeon_probe_claude_r7_20260924.py','toggle_fail_probe_claude_r7_20260924.py',
         'scan_claude_term_rate_20260924_r7.ps1','publish_claude_term_rate_20260924_r7.py',
         'claude_autosave_20260924.jaf','build_claude_term_rate_20260924_r8.py','verify_claude_term_rate_20260924_r8.py','probe_claude_term_rate_20260924_r8.py',
         'home_probe_claude_r8_20260924.py','dungeon_probe_claude_r8_20260924.py','toggle_fail_probe_claude_r8_20260924.py','autosave_probe_claude_r8_20260924.py',
         'scan_claude_term_rate_20260924_r8.ps1','publish_claude_term_rate_20260924_r8.py',
         'claude_term_rate_20260924_r9.jaf','claude_char_missing_20260924.jaf','build_claude_term_rate_20260924_r9.py','verify_claude_term_rate_20260924_r9.py',
         'probe_claude_term_rate_20260924_r9.py','home_probe_claude_r9_20260924.py','dungeon_probe_claude_r9_20260924.py','toggle_fail_probe_claude_r9_20260924.py',
         'autosave_probe_claude_r9_20260924.py','charmissing_probe_claude_r9_20260924.py','scan_claude_term_rate_20260924_r9.ps1','publish_claude_term_rate_20260924_r9.py']
PROBE_DIRS=['home_probe','dungeon_probe','toggle_fail_probe','autosave_probe','charmissing_probe']

def pixels(img,box,rgb,d=48):return sum(1 for q in img.crop(box).getdata() if math.dist(q,rgb)<=d)

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
    tog=p.read(O/'toggle_fail_probe/toggle_fail_probe_result.json')
    assert tog.get('exit_code')==0 and not tog['events'] and tog['blocker_is_dir'] and tog['log'][1:5]==['before=0','after failed write=0','latch=1','after cache reset=0'],tog['log']
    assert p.read(O/'toggle_fail_probe/weapon_probe_manifest.json')['source_sha256']==files['NightRemaster.ain']
    assert 'monsters=맥,날름날름,소머리,무지갯빛 새,털뭉치,푸른 털뭉치,범고래호랑이,불바퀴,털개' in dungeon['log'],dungeon['log']
    auto=p.read(O/'autosave_probe/autosave_probe_result.json');A=auto['A'];B=auto['B']
    assert p.read(O/'autosave_probe/weapon_probe_manifest.json')['source_sha256']==files['NightRemaster.ain']
    for r in (A,B):assert r.get('exit_code')==0 and not r['events'] and not r.get('vm_error') and not r.get('message') and not r.get('timeout'),r.get('log')
    al=A['log'];assert al[0]=='resume loading NightR999.asd' and al[1]=='weekday=1 day=1 slot=49' and al[-1]=='END',al
    wk=next(l for l in al if l.startswith('weekly autosave ms='));dy=next(l for l in al if l.startswith('daily autosave ms='))
    assert wk.endswith(' exists49=1 newest=49') and dy.endswith(' exists999=1 newest=999'),(wk,dy)
    import re
    cm=next(l for l in al if l.startswith('comment49 len='));n49,n999=[int(x) for x in re.findall(r'len=(\d+)',cm)];assert n49>0 and n49==n999 and cm.endswith(' same=1'),cm
    assert 'newest manual: ret=0 idx=-1 page=-1' in al and 'newest with autosaves: ret=1 idx=0 page=0' in al and 'labels 일간,주간,07' in al,al
    for n in ['load_p1','load_p10','save_p1','save_p10']:assert f'SHOT auto_probe_{n}.bmp' in al,n
    assert B['log'][-2:]==['RESUMED weekly autosave; exists49=1','SHOT auto_probe_resumed.bmp'],B['log']
    assert sorted(auto['files_after_A'])==['NightR49.asd','NightR999.asd'] and auto['files_after_A']['NightR999.asd']['sha256']!=auto['user_copy_sha256']
    ws=auto['weekly_stack'];assert ws[-6:]==['■セーブ／オートセーブ実行(int)','C_SceneSaveLoad@RunAutoSave(int)','C_SceneSaveLoad@ExecSave(int, bool)','C_SceneSaveLoad@Save(int)','AFL_GameSave_Save(int, string)','gamesave::detail::Save(int, string)'],ws
    cmr=p.read(O/'charmissing_probe/charmissing_probe_result.json');cl=cmr['log']
    assert p.read(O/'charmissing_probe/weapon_probe_manifest.json')['source_sha256']==files['NightRemaster.ain']
    assert cmr.get('exit_code')==0 and not cmr['events'] and not cmr.get('message') and not cmr.get('timeout') and cl[-1]=='END',cl[-3:]
    assert [l for l in cl if l.startswith('SHOT ')]==[f'SHOT cm_probe_{i}.bmp' for i in range(9)] and all(f'PAGE {q}' in cl and any(l.startswith(f'DATED {q}') for l in cl) for q in range(2,9))
    dl=dungeon['log'];assert dl[-2:]==['records after report: []','SHOT dungeon_probe_3.bmp'] and 'line3=${font r=208 g=150 b=255}이즈미는 독에 걸렸다${/font}' in dl,dl
    from PIL import Image,ImageChops
    shot=lambda d,n:Image.open(O/d/f'{d}_{n}.png').convert('RGB')
    on=ImageChops.difference(shot('home_probe',0),shot('home_probe',2)).getbbox();off=ImageChops.difference(shot('home_probe',1),shot('home_probe',3)).getbbox()
    box=ImageChops.difference(shot('home_probe',0),shot('home_probe',1)).getbbox()
    assert on is None and off is None and box and box[2]<=150 and box[3]<=400,(on,off,box)
    assert max(max(q) for q in shot('home_probe',1).crop((0,0,160,400)).getdata())==0,'panel must leave no pixels when hidden'
    # the tags must render as colour, not as text: count glyph pixels of each rule colour in each surface
    h0=shot('home_probe',0);d1=shot('dungeon_probe',1);d2=shot('dungeon_probe',2);d3=shot('dungeon_probe',3)
    colours=dict(panel_cyan=pixels(h0,(0,20,160,400),(128,224,255)),panel_gold=pixels(h0,(0,20,160,400),(255,224,96)),
                 notice_green=pixels(d1,(180,40,640,130),(128,255,144)),notice_purple=pixels(d1,(180,40,640,130),(208,150,255)),notice_cyan=pixels(d1,(180,40,640,130),(128,224,255)),
                 receipt_gold=pixels(d2,(180,40,640,110),(255,224,96)),receipt_cyan=pixels(d2,(180,40,640,110),(128,224,255)),
                 dialog_gold=pixels(d3,(260,210,1020,510),(255,224,96)),dialog_cyan=pixels(d3,(260,210,1020,510),(128,224,255)),
                 dialog_orange=pixels(d3,(260,210,1020,510),(255,176,88)),dialog_gray=pixels(d3,(260,210,1020,510),(176,176,176),24))
    assert all(n>=10 for n in colours.values()),colours
    scan=p.read(O/'scan_report.json');assert scan['status']=='SCANNED_NO_TARGET_DETECTIONS' and scan['files']==files
    r5=vm['r5']['counts'];r6=vm['r6']['counts'];r7=vm['r7']['counts'];r8=vm['r8']['counts'];r9=vm['r9']['counts']
    for k,n in [('empty_save_character_pages',7),('complete_save_pages',7),('partial_and_passed',1),('month_passed_boundary',1),('lines_fit_38_chars',1),('menu_flow',1)]:
        assert r9.get(k)==n,(k,r9.get(k))
    for k,n in [('schedule_all_weekdays',7),('load_confirm_titles',3),('game_over_newest_cases',9),('relocated_body_exact',5),('operand_sites',5),
                ('lock_only_autosaves',1),('newest_search_skips_weekly_without_auto',1),('auto_alias',1),('base_code_r7_except_operands',1)]:
        assert r8.get(k)==n,(k,r8.get(k))
    for k,n in [('failed_write_keeps_state_no_retry_storm',1),('retry_after_change_succeeds',1),('readback_mismatch_is_failure',1),('ex_only_eight_names_changed',1),('renamed_monsters',8)]:
        assert r7.get(k)==n,(k,r7.get(k))
    for k,n in [('relocated_body_is_original_plus_prefix',2),('sweep_records',1),('lost_list_in_report',1),('records_cleared_after_report',1),('nothing_lost_line',1),('cancel_report_untouched',1)]:
        assert r6.get(k)==n,(k,r6.get(k))
    for k,n in [('colour_rule_cases',14),('second_pass_unchanged',14),('josa_resolver_leaves_tags',14),('char_event_counts',7),('relocated_body_is_original_plus_prefix',7),
                ('message_dialog_tag_block_only_change',1),('trap_dialog_coloured_dialog_unchanged',9),('instant_notice_cases',6)]:
        assert r5.get(k)==n,(k,r5.get(k))
    status=dict(status=VERIFIED,author=build.AUTHOR,files=files,
        changes=['캐릭터별 남은 이벤트 (플레이 정보): per character, unseen events of this save by month and kind, date windows and intimacy conditions of personal/story events, 지남 once passed',
                 'daily and weekly autosaves: every morning the game\'s own autosave runs; Monday -> weekly slot 49 (page 10, 주간), other days -> 999 (일간); rest cells/ending keep 999',
                 'weekly slot locked in the save screen, skipped by the newest-manual search, same label font and save comment as 999; game-over resume loads the newer autosave',
                 'r7: monster names, CT-RATE-003; r6: sweep carry-limit list; r5: coloured result texts, per-character event rates'],
        vm_counts=vm['counts'],vm_r5_counts=r5,vm_r6_counts=r6,vm_r7_counts=r7,vm_r8_counts=r8,vm_r9_counts=r9,charmissing_native=cl,autosave_native=dict(A=A['log'],B=B['log'],files=auto['files_after_A'],weekly_stack=ws),vm_steps=vm['steps'],existing_resume_saves=frames['saves'],saved_return_frames=frames['frames'],existing_save_local_offsets_exact=True,
        old_CODE_allowlist_exact=True,MSG1_exact=True,STR0_prefix_exact=True,save_schema_changes=0,native_checks_passed=True,colour_pixels=colours,
        native=dict(pid=native['pid'],log=native['log'],legacy_pid=legacy['pid'],legacy_log=legacy['log'],home_pid=home['pid'],home_log=home['log'],
                    dungeon_pid=dungeon['pid'],dungeon_log=dungeon['log'],home_panel_diff_box=list(box)),
        not_verified=['A real chest / trap / instant kill / sweep during play (writers covered by VM; drawing covered in a resumed dungeon)',
                      'The mods-tab checkbox inside the real config screen'],translator_model=build.AUTHOR)
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
    full['claude_term_rate_r9_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model=build.AUTHOR)
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
                 relocated=ev['relocated'],terms=ev['terms'],home_panel=ev['home_panel'],trap_notice=ev['trap_notice'],colors=ev['colors'],char_events=ev['char_events'],sweep_lost=ev['sweep_lost'],monster_names=ev['monster_names'],autosave=ev['autosave'],char_missing=ev['char_missing'],
                 translator_model=build.AUTHOR)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,claude_term_rate_r9_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],claude_term_rate_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User screen check: 플레이 정보 > 캐릭터별 남은 이벤트; the 일간/주간 autosave cells after a new morning; renamed monsters; mods-tab checkbox; sweep list; colours.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['claude_term_rate_r9_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':(
            'Supersedes r7 (r2-r7 contracts still apply; r8 was never installed, r9 contains it). r9: 플레이 정보 gains 「캐릭터별 남은 이벤트」 '
            '(KR_T8CharMissingMenu; counts/date windows generated from handoff_claude_terms_progress_20260923/event_catalog.json; every line <= 38 characters '
            'because the dialog title has no wrap and a text texture over 2048px raises an engine error). r8: daily/weekly autosaves. 呼出／１日の始まり keeps its code; two operands changed: '
            'the Monday test CALLFUNC L_Calendar::GetDayOfWeek -> KR_T8AutoSaveDay (returns 1) and PUSH 999 -> CALLFUNC KR_T8AutoSaveSlot (Monday -> 49). '
            'Every autosave\'s saved stack stays all-original (C_SceneGame@Run > 呼出／１日の始まり > ■セーブ／オートセーブ実行 > C_SceneSaveLoad@RunAutoSave > ExecSave > Save); '
            'keep 呼出／１日の始まり, ■セーブ／オートセーブ実行 and C_SceneSaveLoad@* at their addresses (user autosaves resume inside them). '
            'Slot 49 is the weekly autosave slot (label 주간, locked in the save screen) - do not repurpose it; 999 is labelled 일간. '
            'Relocated (never on a saved stack): C_SaveLoadViewCell@GetDispSaveNo, @GetSaveNoFont, C_SceneSaveLoadView@GetSaveComment, @Update, N_SaveLoad::GetNewDataNo. '
            'Same-length: C_SceneSaveLoad@IsExecLoad title call -> KR_T8SlotTitle; C_SceneGame@ExecGameOver both PUSH 999 -> KR_T8NewestAutoSlot. r7: EX block 7 names of monsters 17/28/23/27/3/21/6/18 are the user\'s localized names '
            '(맥, 날름날름, 소머리, 무지갯빛 새, 털뭉치, 푸른 털뭉치, 범고래호랑이, 불바퀴) - keep them when rebuilding the EX; Codex CT-RATE-003 fixed '
            '(KR_T8HomeRateSet writes, reads back, then commits; YoruKR.HomeRate.Failed latch). r6: L_TreasureBox::ShowGetDialog is relocated with KR_T8SweepChest(txt) prepended (records only '
            'while KR_SweepActive: a consumable followed by 하지만 더는 소지할 수 없다 is lost; element stone texts count as attempts), KR_SweepPay with '
            'KR_T8SweepLostReset prepended; KR_T8SweepColor replaces the fixed KR_SweepItems line with the lost list (stones: attempts minus the report\'s '
            'gains). r5 notes follow. Colour: KR_ChestShow, KR_NoticeShow and KR_SweepReport are relocated with one prepended '
            'reassignment (text = KR_T8ChestColor / KR_T8ReceiptColor / KR_T8SweepColor(text)); KR_T8TrapNotice colours trap lines itself. The writers switch '
            'tag processing on (Ｐ＿テキストタグ有効設定) and set a white base (Ｐ＿フォント色設定) on their parts at runtime, because a resumed save restores the parts\' old '
            'state; PACT 160 has the same settings for fresh activities. C_MessageDialog@Create is relocated with ITextParts Tag::set(true) (CTextParts vtable '
            'slot 25) before Text::set, only when the text contains ${font - every other dialog is untouched. Tags: ${font r=R g=G b=B}...${/font}, josa is '
            'resolved before tags go in. Panel: per-character event rates from the event catalog (person/person2 triggers) via N_ScenarioRegister::IsRegisteredEvent. '
            'KR_T8TrapDialog and KR_T8RelieveTrap may sit on a saved stack (r4 note): keep their addresses in later builds or build on top of this AIN.')}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,claude_term_rate_r9_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),claude_term_rate_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        chars=' / '.join(f"{r['name']} {r['events']}" for r in ev['char_events']['rows'])
        note=(f"\n\n### {now} 캐릭터별 남은 이벤트·일간/주간 자동 저장 설치 (Claude Opus 5.5)\n"
              "- 사용자: 「달성률에서 각 캐릭터별로 몇월 며칠의 어느 이벤트가 비어있는지」 → 플레이 정보에 「캐릭터별 남은 이벤트」: 캐릭터 목록(남은 수) → 요약(날짜 이벤트 수, 특훈 뒤 대화 남은 달/지난 달에 놓친 대화, 반한 뒤·특훈 권유·토요일 초대, 던전 동행 짝꿍별) → 날짜 이벤트(개인·본편 날짜 구간, 친밀도 조건, 앞 이벤트, 지남). 캐릭터 이벤트는 달별 무작위 풀이라 날짜 대신 달·종류. 제목은 데이터에 없고 첫 대사는 스포라 넣지 않음. 대화 상자 제목은 줄바꿈이 없고 2048px 넘는 글 텍스처는 엔진 오류라 모든 줄 38자 이내(첫 시도 한 줄 나열에서 오류 확인 후 세 개씩 줄바꿈).\n"
              "- (r8 내용, 이번에 함께 설치) 일간·주간 자동 저장:\n"
              "- 사용자: 「게임에 오토세이브가 없었네?」→ 원작에 999번 「자동」 칸이 있었다(월요일 아침·던전 휴식 칸·엔딩 직전, 게임 오버 「자동 저장에서 재개」). 사용자 제안 「일간 자동 세이브랑 주간 자동 세이브를 분리」로: 매일 아침 원작 자동 저장이 돈다 — 월요일은 주간 칸(49번, 10페이지 마지막 칸, 「주간」), 다른 날은 999번(「일간」). 던전 휴식·엔딩은 그대로 999번.\n"
              "- 원본 코드는 피연산자만: 呼出／１日の始まり의 요일 검사와 슬롯 999(같은 길이 2곳), 불러오기 확인 제목(IsExecLoad), 게임 오버 재개 슬롯 2곳(더 새 자동 저장). 저장 스택엔 원본 함수만 오른다. 화면 함수 5개 이전(세이브 스택에 오르지 않음): 칸 이름표·글꼴·저장 코멘트(능력치 표시)·저장 화면 잠금·최근 수동 저장 찾기에서 49번 제외.\n"
              "- 네이티브: 사용자 월요일 자동 저장 사본을 이어 받아 주간(49) 저장 약 2초·일간(999) 약 1초, 불러오기/저장 화면 1·10페이지 스크린숏(일간·주간 이름표, 저장 화면에선 흐림), 주간 저장 파일을 다시 이어 받기 성공.\n"
              f"- 검증: VM {qa['vm_steps']}스텝(r3·r5·r6·r7 전부 + r8 요일 7종·이름표·잠금·최근 저장 찾기·확인 제목 3종·게임 오버 9경우·이전 함수 5개 원본 대조 + r9 빈/전부/일부 저장·지남 경계·메뉴 흐름·모든 줄 38자 이내), 세이브 {qa['existing_resume_saves']}개/복귀 {qa['saved_return_frames']}지점 exact, 네이티브 탐침 7종 예외 0건(사용자 최신 세이브 사본으로 캐릭터별 남은 이벤트 화면 9장), Defender·설치복구 fixture PASS.\n"
              f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}; EX {after['NightRemasterEX.ex']}; manifest {mh}; evidence {E}; 되돌리기 publish_claude_term_rate_20260924_r9.py --restore (→ r7).\n")
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
