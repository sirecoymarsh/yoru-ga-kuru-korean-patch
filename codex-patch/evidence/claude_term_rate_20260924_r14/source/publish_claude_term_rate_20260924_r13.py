"""Claude Opus 5.5 (2026-09-24): transactional install of claude_term_rate r13 over r12.

r13 = r12 + a click on a character in the home base achievement panel opens that character's 「캐릭터별 남은 이벤트」
window (user: 「그 캐릭터별 이벤트 혹시 왼쪽에 캐릭터 이름 클릭해서 그 창 나타나게 할 수 없어?」): C_SceneHomebase@RunHome
(never on a saved stack) is relocated with KR_T8HomeMenuOpen before its top-menu call and KR_T8HomeMenuClose after it;
the panel body takes an L-click only while the top menu waits.

r12 docstring:

r12 = r11 + auto exploration keeps going through a dungeon talk (user: 「던전에서 자동 탐색 중 대화 이벤트가 발생하면
멈추는데 이벤트 자동으로 보고 계속 진행되게」): four same-length call swaps - Codex's C_SceneDungeon@CheckTalk keeps an owned
walk (KR_T8TalkBegin in place of KR_WalkStop) and un-pauses it after the talk (KR_T8TalkEnd in place of Ａ＿全表示);
LSys3xScript::RunEvent switches the message auto mode on for that talk after its saved-state restore (KR_T8EventStart) and
off again before its save-and-release (KR_T8EventEnd), so the player's own auto setting is what the engine keeps.

r11 docstring:

r11 = r10 with colourr11 = r10 with colour in the 「캐릭터별 남은 이벤트」 pages (user: 「색깔이 좀 있으면 좋겠네」): C_SelectDialog@CreateParts'
single title draw call is swapped (same length) to KR_T8TitleDraw, which splits an opted-in title at one-character marks and
draws each run in its colour (labels white, counts sky blue, passed rows grey, headings in the dialog's gold); every other
dialog calls the original unchanged. Native: the split draw in the dialog colour is pixel-identical to the original draw.

r10 docstring:

r10 = r9 with the 「캐릭터별 남은 이벤트」 pages laid out by place / by date / by dungeon party (user: 「현재 표시 방식은
다소 번잡하다 … 날짜별, 장소별, 던전일 경우 같이 있어야 하는 캐릭터들로」): one item per line, dated events in the month
they open, conditions on their own page split into personal / story, dungeon talks by the partner to bring.

r9 docstring:

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
import build_claude_term_rate_20260924_r13 as build
R=build.R;O=build.O;HERE=build.HERE;assert O.name=='claude_term_rate_20260924_r13'
E=R/'evidence/claude_term_rate_20260924_r13'
CONTRACTS=first.CONTRACTS+[first.NEW,'required_claude_term_rate_20260924_r2.json','required_claude_term_rate_20260924_r3.json',
                           'required_claude_term_rate_20260924_r4.json','required_claude_term_rate_20260924_r5.json',
                           'required_claude_term_rate_20260924_r6.json','required_club_wall_bilingual_20260924.json','required_club_wall_cancel_20260924.json',
                           'required_claude_term_rate_20260924_r7.json','required_claude_term_rate_20260924_r9.json',
                           'required_claude_term_rate_20260924_r10.json','required_claude_term_rate_20260924_r11.json',
                           'required_claude_term_rate_20260924_r12.json'];NEW='required_claude_term_rate_20260924_r13.json'
STATUS='CLAUDE_TERM_RATE_R13_INSTALLED_NATIVE_PASS';VERIFIED='CLAUDE_TERM_RATE_R13_STATIC_VM_NATIVE_PASS'
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
         'autosave_probe_claude_r9_20260924.py','charmissing_probe_claude_r9_20260924.py','scan_claude_term_rate_20260924_r9.ps1','publish_claude_term_rate_20260924_r9.py',
         'claude_char_missing_20260924_r10.jaf','build_claude_term_rate_20260924_r10.py','verify_claude_term_rate_20260924_r10.py','probe_claude_term_rate_20260924_r10.py',
         'home_probe_claude_r10_20260924.py','dungeon_probe_claude_r10_20260924.py','toggle_fail_probe_claude_r10_20260924.py','autosave_probe_claude_r10_20260924.py',
         'charmissing_probe_claude_r10_20260924.py','scan_claude_term_rate_20260924_r10.ps1','publish_claude_term_rate_20260924_r10.py',
         'claude_char_missing_20260924_r11.jaf','claude_dialog_color_20260924.jaf','build_claude_term_rate_20260924_r11.py','verify_claude_term_rate_20260924_r11.py',
         'probe_claude_term_rate_20260924_r11.py','home_probe_claude_r11_20260924.py','dungeon_probe_claude_r11_20260924.py','toggle_fail_probe_claude_r11_20260924.py',
         'autosave_probe_claude_r11_20260924.py','colorcheck_probe_claude_r11_20260924.py','scan_claude_term_rate_20260924_r11.ps1','publish_claude_term_rate_20260924_r11.py',
         'claude_talk_continue_20260924.jaf','build_claude_term_rate_20260924_r12.py','verify_claude_term_rate_20260924_r12.py','probe_claude_term_rate_20260924_r12.py',
         'home_probe_claude_r12_20260924.py','dungeon_probe_claude_r12_20260924.py','toggle_fail_probe_claude_r12_20260924.py','autosave_probe_claude_r12_20260924.py',
         'colorcheck_probe_claude_r12_20260924.py','talk_probe_claude_r12_20260924.py','scan_claude_term_rate_20260924_r12.ps1','publish_claude_term_rate_20260924_r12.py',
         'claude_home_pick_20260924.jaf','build_claude_term_rate_20260924_r13.py','verify_claude_term_rate_20260924_r13.py','probe_claude_term_rate_20260924_r13.py',
         'home_probe_claude_r13_20260924.py','dungeon_probe_claude_r13_20260924.py','toggle_fail_probe_claude_r13_20260924.py','autosave_probe_claude_r13_20260924.py',
         'colorcheck_probe_claude_r13_20260924.py','talk_probe_claude_r13_20260924.py','homepick_probe_claude_r13_20260924.py','scan_claude_term_rate_20260924_r13.ps1',
         'publish_claude_term_rate_20260924_r13.py']
PROBE_DIRS=['home_probe','dungeon_probe','toggle_fail_probe','autosave_probe','colorcheck_probe','talk_probe','homepick_probe']

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
    al=A['log'];import re as _re;wd=_re.fullmatch(r'weekday=(\d) day=1 slot=(\d+)',al[1])
    assert al[0]=='resume loading NightR999.asd' and wd and int(wd[2])==(49 if wd[1]=='1' else 999) and al[-1]=='END',al
    wk=next(l for l in al if l.startswith('weekly autosave ms='));dy=next(l for l in al if l.startswith('daily autosave ms='))
    assert wk.endswith(' exists49=1 newest=49') and dy.endswith(' exists999=1 newest=999'),(wk,dy)
    import re
    cm=next(l for l in al if l.startswith('comment49 len='));n49,n999=[int(x) for x in re.findall(r'len=(\d+)',cm)];assert n49>0 and n49==n999 and cm.endswith(' same=1'),cm
    assert 'newest manual: ret=0 idx=-1 page=-1' in al and 'newest with autosaves: ret=1 idx=0 page=0' in al and 'labels 일간,주간,07' in al,al
    for n in ['load_p1','load_p10','save_p1','save_p10']:assert f'SHOT auto_probe_{n}.bmp' in al,n
    assert B['log'][-2:]==['RESUMED weekly autosave; exists49=1','SHOT auto_probe_resumed.bmp'],B['log']
    assert sorted(auto['files_after_A'])==['NightR49.asd','NightR999.asd'] and auto['files_after_A']['NightR999.asd']['sha256']!=auto['user_copy_sha256']
    ws=auto['weekly_stack'];assert ws[-6:]==['■セーブ／オートセーブ実行(int)','C_SceneSaveLoad@RunAutoSave(int)','C_SceneSaveLoad@ExecSave(int, bool)','C_SceneSaveLoad@Save(int)','AFL_GameSave_Save(int, string)','gamesave::detail::Save(int, string)'],ws
    # r13 home pick: resumed home base save (panel on), the top menu's wait live, input patched off; clicks dispatched through
    # the part's own CPartsFunctionSet: a CG-row click is ignored, 쿄카's row opens her window, 돌아가기 brings the top menu back.
    hp=p.read(O/'homepick_probe/homepick_probe_result.json');hl=hp['log']
    assert p.read(O/'homepick_probe/weapon_probe_manifest.json')['source_sha256']==files['NightRemaster.ain']
    assert hp.get('exit_code')==0 and not hp['events'] and not hp.get('message') and not hp.get('timeout') and hl[-1]=='END',hl[-4:]
    top=next(l for l in hl if l.startswith('TOP '));assert ' visible=1 clickable=1 input=1 handlers=1 menu=1 pick=' in top,top
    assert 'after CG-row click menu=1 pick=' in hl and 'after 쿄카-row click menu= pick=3' in hl,hl
    page=next(l for l in hl if l.startswith('PAGE '));assert page.startswith('PAGE title=쿄카 · 아직 못 본 이벤트') and page.endswith(' menu= pick= clickable=0'),page
    assert 'BACK TO TOP menu=1 pick= clickable=1 handlers=1' in hl,hl
    # r12 talk: resumed dungeon save, exploration started, CheckTalk's own conditions armed; input patched off, so the talk
    # can only advance through the auto mode; the walk must stay owned and move on after the talk.
    import re
    tpr=p.read(O/'talk_probe/talk_probe_result.json');tl=tpr['log']
    assert p.read(O/'talk_probe/weapon_probe_manifest.json')['source_sha256']==files['NightRemaster.ain']
    assert tpr.get('exit_code')==0 and not tpr['events'] and not tpr.get('message') and not tpr.get('timeout') and tl[-1]=='END',tl[-4:]
    tb=next(i for i,l in enumerate(tl) if l.startswith('TALK BEGIN '))
    assert ' flag=2026092203 ' in tl[tb] and tl[tb+1].startswith('after begin flag=2026092203 ') and ' TalkFlag=2026092203 ' in tl[tb+1],tl[tb:tb+2]
    msg=[l for l in tl if l.startswith('MSG WAIT ')];assert len(msg)>=2 and all(l.endswith(' auto=1') for l in msg),msg
    te=next(i for i,l in enumerate(tl) if l.startswith('TALK END '))
    assert ' flag=-2026092203 ' in tl[te] and tl[te].endswith(' auto=0') and int(re.search(r'waits=(\d+)',tl[te])[1])>=2,tl[te]
    assert tl[te+1]=='after end flag=2026092203 auto=0 own=1',tl[te+1]
    steps=[l for l in tl[te:] if l.startswith('STEP after ')];assert len(steps)==3 and all(' flag=2026092203 ' in l for l in steps),steps
    assert len({re.search(r' at (\d+),(\d+) ',l).groups() for l in steps})==3 and any(l.startswith('CONTINUED 3 moves after the talk ') for l in tl),steps
    # r11 colour: A = original draw (marks moved to line ends as spaces), B = split runs in the dialog colour, C = colour;
    # A and B must be pixel-identical; the title spy logs the opt-in of every title draw (A off, B/C and all 9 menu pages on).
    ccr=p.read(O/'colorcheck_probe/colorcheck_probe_result.json');cl=ccr['log']
    assert p.read(O/'colorcheck_probe/weapon_probe_manifest.json')['source_sha256']==files['NightRemaster.ain']
    assert ccr.get('exit_code')==0 and not ccr['events'] and not ccr.get('message') and not ccr.get('timeout') and cl[-1]=='END',cl[-3:]
    assert [l for l in cl if l.startswith('SHOT ')]==[f'SHOT cc_{n}_{k}.bmp' for n in ('place','cond','party') for k in 'ABC']+[f'SHOT cc_menu_{i}.bmp' for i in range(9)],cl
    spy=[l for l in cl if l.startswith('SPY ')]
    assert len(spy)==18 and all((' color= optin=0 ' in l) if i in (0,3,6) else (' color=1 optin=1 ' in l) for i,l in enumerate(spy)),spy
    assert all(ccr['compare'][n]['A_vs_B'] is None and ccr['compare'][n]['A_vs_C'] for n in ('place','cond','party')),ccr['compare']
    from PIL import Image as _Image
    cc=lambda n,k:_Image.open(O/'colorcheck_probe'/f'cc_{n}_{k}.png').convert('RGB')
    cc_colour={n:pixels(cc(n,'C'),tuple(ccr['compare'][n]['A_vs_C']),(128,224,255),40)-pixels(cc(n,'A'),tuple(ccr['compare'][n]['A_vs_C']),(128,224,255),40) for n in ('place','cond','party')}
    assert all(v>=100 for v in cc_colour.values()),cc_colour
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
    r5=vm['r5']['counts'];r6=vm['r6']['counts'];r7=vm['r7']['counts'];r8=vm['r8']['counts'];r9=vm['r13']['counts']
    for k,n in [('empty_save_pages',7),('complete_save_pages',7),('partial_on_7_10',1),('every_line_fits',1),('menu_flow',1),
                ('raw_lines_fit',1),('segment_parsing',1),('title_opt_in',1),('title_draw_site',1),('talk_sites',4),
                ('talk_moving_run_auto_and_resumes',1),('talk_player_auto_setting_kept',1),('talk_click_released_auto',1),('talk_manual_walk_unchanged',1),
                ('talk_manual_walk_player_auto',1),('talk_pending_object_kept',1),('talk_lost_walk_not_revived_setting_kept',1),('talk_stale_mark_dropped',1),
                ('talk_other_events_unchanged',1),('talk_end_without_begin',1),('home_runhome_relocated_exact',1),('home_row_mapping',1),
                ('home_click_once_per_wait',1),('home_click_other_rows_ignored',1),('home_click_outside_menu_ignored',1),('home_clickable_parts',1),
                ('home_menu_open',1),('home_menu_close_cases',7)]:
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
        changes=['home base panel: a click on a character opens that character\'s 캐릭터별 남은 이벤트 window (only while the top menu waits); 돌아가기 returns to the top menu',
                 'r12: dungeon talk during auto exploration: the walk keeps its route and ownership, the talk plays in the message auto mode (switched on after RunEvent restores the saved state, off again before it saves), exploration resumes after the talk',
                 'r11: colour in 캐릭터별 남은 이벤트: the selection-dialog title draw (C_SelectDialog@CreateParts) swapped same-length to KR_T8TitleDraw; opted-in titles drawn in runs split at marks (labels white, counts sky blue, passed grey); every other dialog calls the original',
                 'r10: 캐릭터별 남은 이벤트 laid out by place (first page), by date (month rows; dated events in the month they open) and by dungeon party (partner to bring); conditions page split into personal/story',
                 'r9: 캐릭터별 남은 이벤트 (플레이 정보): per character, unseen events of this save by month and kind, date windows and intimacy conditions of personal/story events, 지남 once passed',
                 'daily and weekly autosaves: every morning the game\'s own autosave runs; Monday -> weekly slot 49 (page 10, 주간), other days -> 999 (일간); rest cells/ending keep 999',
                 'weekly slot locked in the save screen, skipped by the newest-manual search, same label font and save comment as 999; game-over resume loads the newer autosave',
                 'r7: monster names, CT-RATE-003; r6: sweep carry-limit list; r5: coloured result texts, per-character event rates'],
        vm_counts=vm['counts'],vm_r5_counts=r5,vm_r6_counts=r6,vm_r7_counts=r7,vm_r8_counts=r8,vm_r13_counts=r9,homepick_native=dict(log=hl),talk_native=dict(log=tl),colorcheck_native=dict(log=cl,compare=ccr['compare'],sky_blue_pixels_added=cc_colour),autosave_native=dict(A=A['log'],B=B['log'],files=auto['files_after_A'],weekly_stack=ws),vm_steps=vm['steps'],existing_resume_saves=frames['saves'],saved_return_frames=frames['frames'],existing_save_local_offsets_exact=True,
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
    full['claude_term_rate_r13_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model=build.AUTHOR)
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
                 relocated=ev['relocated'],terms=ev['terms'],home_panel=ev['home_panel'],trap_notice=ev['trap_notice'],colors=ev['colors'],char_events=ev['char_events'],sweep_lost=ev['sweep_lost'],monster_names=ev['monster_names'],autosave=ev['autosave'],char_missing=ev['char_missing'],char_missing_r10=ev['char_missing_r10'],title_color=ev['title_color'],talk_continue=ev['talk_continue'],home_pick=ev['home_pick'],
                 translator_model=build.AUTHOR)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,claude_term_rate_r13_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],claude_term_rate_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User screen check: click a character name in the home base panel (a real mouse click on the text part); a dungeon talk during auto exploration; the 일간/주간 autosave cells after a new morning.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['claude_term_rate_r13_preserved_by']=str(E);write(R/n,p.js(c))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':(
            'Supersedes r12 (r2-r12 contracts still apply). r13: C_SceneHomebase@RunHome is relocated (it is never on a saved stack; '
            'C_SceneHomebase@Run and CheckGameSysButtons are - keep those in place) with CALLFUNC KR_T8HomeMenuOpen before its top-menu '
            '■選択ダイアログ／実行 and .LOCALREF res / CALLFUNC KR_T8HomeMenuClose / IFNZ <loop head> after it. The home panel body '
            '(PACT 177 KR_HomeRateBody, 8,52 on screen, 24 px a line, lines 7-13 = characters 2-8) takes an L-click (KR_T8HomeClick via '
            'parts::detail::AddMouseLClickEvent) only while the top menu waits; the click ends the wait with 2026092401 and the window '
            '(KR_T8CharMissingPage) opens after the menu dialog has closed (■選択ダイアログ is one global object). A panel layout change '
            'must update KR_T8HomeRow. r12: four same-length CALLFUNC swaps - C_SceneDungeon@CheckTalk (Codex relocation): '
            'KR_WalkStop -> KR_T8TalkBegin (an owned walk keeps route and ownership, YoruKR.T8.TalkFlag = flag 71), Ａ＿全表示 -> KR_T8TalkEnd '
            '(Ａ＿全表示 first, then flag 71 back to +2026092203 when the view\'s Hide paused a moving run); LSys3xScript::RunEvent: '
            'ForceRestoreSkipAutpState -> KR_T8EventStart (original first, then the auto mode on for a marked talk, YoruKR.T8.TalkAuto = 1), '
            'ForceReleaseSkipAutpState -> KR_T8EventEnd (that auto mode off first, then the original saves the player\'s own setting). '
            'RunEvent is on saved stacks (autosaves inside events): keep its code layout; a later Codex CheckTalk must keep both calls. '
            'r11: C_SelectDialog@CreateParts draws its title through KR_T8TitleDraw (same-length '
            'CALLFUNC swap of Ｐ＿構築手順＿テキストアルファブレンド). It colours only a title a KR page opted in (YoruKR.T8.Color = 1 and the drawn text is '
            'YoruKR.T8.Title or 「　」+title+「　」 - the dialog pads its title with a full-width space on each side) and otherwise calls the original with the '
            'same arguments. Marks † ‡ ¶ 〓 (white / sky blue / grey / back to the dialog colour) are not drawn but count in the dialog width: raw lines <= 38 '
            'characters. Runs are placed by leading newlines and CASFont GetFontWidth + letter spacing (native: pixel-identical to the original draw). '
            'r10: 캐릭터별 남은 이벤트 pages by place / date / dungeon party '
            '(KR_T8PlaceText / KR_T8DateText / KR_T8CondText / KR_T8PartyText; lines <= 38 characters, pages <= 14 lines). r9: 플레이 정보 gains 「캐릭터별 남은 이벤트」 '
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
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,claude_term_rate_r13_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),claude_term_rate_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        chars=' / '.join(f"{r['name']} {r['events']}" for r in ev['char_events']['rows'])
        note=(f"\n\n### {now} 본거지 달성률 패널 캐릭터 이름 클릭 → 캐릭터별 남은 이벤트 창 설치 (Claude Opus 5.5)\n"
              "- 사용자: 「그 캐릭터별 이벤트 혹시 왼쪽에 캐릭터 이름 클릭해서 그 창 나타나게 할 수 없어?」 → 본거지 첫 메뉴(멤버 선택·무기 가공…)가 떠 있을 때 왼쪽 달성률 패널의 캐릭터 줄(이름·퍼센트)을 누르면 그 캐릭터의 「캐릭터별 남은 이벤트」 창(장소별 → 날짜별로 보기/던전 파티별로 보기)이 열리고, 돌아가기로 첫 메뉴로 돌아온다. 첫 메뉴는 전역 선택 창 하나라 클릭 안에서 창을 열 수 없어, 클릭은 메뉴 대기를 전용 코드로 끝내고 RunHome(세이브 스택에 오르지 않음; 이전)이 메뉴가 닫힌 뒤 창을 열고 원래 메뉴 반복으로 돌아간다. 패널은 메뉴 대기 중에만 클릭을 받는다.\n"
              "- 네이티브: 본거지 세이브 사본(NightR38, 패널 켬)에서 첫 메뉴의 실제 대기 중 패널 본문의 클릭 처리기(1개)로 CG 줄 클릭(무시)과 쿄카 줄 클릭 → 쿄카 창 열림(창이 떠 있는 동안 패널 클릭 꺼짐) → 돌아가기 → 첫 메뉴 복귀(처리기 여전히 1개). 실제 마우스 클릭의 적중 판정은 사용자 화면 확인.\n"
              "- (r12 내용) 던전 자동 탐색 중 대화 이벤트 자동 진행:\n"
              "- 사용자: 「던전에서 자동 탐색 중 대화 이벤트가 발생하면 멈추는데 이벤트 자동으로 보고 계속 진행되게」 → 자동 탐색 중 던전 대화가 뜨면 메시지 자동 넘김(원작 자동 모드)으로 보여 주고, 끝나면 탐색을 이어 간다. 원인: Codex의 CheckTalk 사본이 대화 전에 KR_WalkStop을 불러 탐색을 끝냈고, 던전 화면 숨김(Hide→KR_WalkPause)도 탐색을 멈춘 상태로 만들었다. 수정: CheckTalk 호출 2곳과 LSys3xScript::RunEvent 호출 2곳을 같은 길이로 교체. RunEvent는 이벤트 시작 때 저장된 자동/스킵 상태를 되살리고 끝날 때 저장 후 끄므로(대화 전에 켠 자동 모드가 첫 대사에서 꺼진 것을 실기 계측으로 확인), 시작 복원 직후 켜고 끝 저장 직전에 끈다 — 플레이어가 평소 쓰는 자동 설정은 그대로 남는다. 클릭하면 원작대로 자동이 풀리고, 수동 이동 중 대화·다른 이벤트는 그대로.\n"
              "- 네이티브: 던전 세이브 사본(NightR36)을 이어 받아 자동 탐색 시작, 대화 조건(층 걸음 300)을 맞춰 첫 걸음에 대화 → 입력을 끈 상태에서 자동 모드로 대사 7개가 넘어가고, 끝난 뒤 탐색 소유 유지, 이어서 3칸 이동(20,6→19,6→18,6). 자동 모드는 대화 중에만 켜졌다가 꺼짐.\n"
              "- (r11 내용) 캐릭터별 남은 이벤트 색 입히기:\n"
              "- 사용자: 「색깔이 좀 있으면 좋겠네」 → 항목 이름 흰색, 개수·다가올 날짜 하늘색, 지난 항목 회색, 머리줄은 대화창 본래 금색. 선택 창 제목은 한 번에 한 색으로 그려져 색 태그가 안 먹으므로, 제목 그리기 호출 하나를 같은 길이로 KR_T8TitleDraw로 바꿔 우리 페이지 제목만 색 구간별로 나눠 그린다(다른 대화창·이야기 선택지는 원래 호출 그대로). 대화창이 제목 앞뒤에 전각 공백을 붙여 그리는 것을 실기 계측으로 확인해 판정에 반영(첫 빌드는 이 때문에 색이 안 들었다).\n"
              "- 네이티브: 쿄카 장소별·날짜 조건·던전 파티 세 쪽에서 색 구간 분할 그리기(단색)가 원래 그리기와 픽셀 동일, 색 화면과 메뉴 9장 스크린숏.\n"
              "- (r10 내용) 화면 정리:\n"
              "- 사용자: 「현재 표시 방식은 다소 번잡하다 … 날짜별, 장소별, 던전일 경우 같이 있어야 하는 캐릭터들로」 → 캐릭터를 고르면 장소별 첫 화면(특훈 뒤 대화·반한 뒤 대화·특훈 권유·토요일 초대·던전 안 대화·날짜가 정해진 이벤트, 한 줄에 하나, 지난 것은 들여쓴 줄), [날짜별로 보기] 달마다 한 줄(특훈 뒤 대화 n개 · 날짜 이벤트 n개, 날짜 이벤트는 열리는 달에), 언제든/지나감 한 줄씩, [날짜 이벤트 조건] 개인·본편 구역, [던전 파티별로 보기] 같이 넣을 캐릭터마다 한 줄. 선택 창 제목은 구성 그리기라 색 태그 불가 → 구조로 정리. 모든 줄 38자·페이지 14줄 이내 검증.\n"
              "- (r9 내용) 캐릭터별 남은 이벤트 첫 판:\n"
              "- 사용자: 「달성률에서 각 캐릭터별로 몇월 며칠의 어느 이벤트가 비어있는지」 → 플레이 정보에 「캐릭터별 남은 이벤트」: 캐릭터 목록(남은 수) → 요약(날짜 이벤트 수, 특훈 뒤 대화 남은 달/지난 달에 놓친 대화, 반한 뒤·특훈 권유·토요일 초대, 던전 동행 짝꿍별) → 날짜 이벤트(개인·본편 날짜 구간, 친밀도 조건, 앞 이벤트, 지남). 캐릭터 이벤트는 달별 무작위 풀이라 날짜 대신 달·종류. 제목은 데이터에 없고 첫 대사는 스포라 넣지 않음. 대화 상자 제목은 줄바꿈이 없고 2048px 넘는 글 텍스처는 엔진 오류라 모든 줄 38자 이내(첫 시도 한 줄 나열에서 오류 확인 후 세 개씩 줄바꿈).\n"
              "- (r8 내용, 이번에 함께 설치) 일간·주간 자동 저장:\n"
              "- 사용자: 「게임에 오토세이브가 없었네?」→ 원작에 999번 「자동」 칸이 있었다(월요일 아침·던전 휴식 칸·엔딩 직전, 게임 오버 「자동 저장에서 재개」). 사용자 제안 「일간 자동 세이브랑 주간 자동 세이브를 분리」로: 매일 아침 원작 자동 저장이 돈다 — 월요일은 주간 칸(49번, 10페이지 마지막 칸, 「주간」), 다른 날은 999번(「일간」). 던전 휴식·엔딩은 그대로 999번.\n"
              "- 원본 코드는 피연산자만: 呼出／１日の始まり의 요일 검사와 슬롯 999(같은 길이 2곳), 불러오기 확인 제목(IsExecLoad), 게임 오버 재개 슬롯 2곳(더 새 자동 저장). 저장 스택엔 원본 함수만 오른다. 화면 함수 5개 이전(세이브 스택에 오르지 않음): 칸 이름표·글꼴·저장 코멘트(능력치 표시)·저장 화면 잠금·최근 수동 저장 찾기에서 49번 제외.\n"
              "- 네이티브: 사용자 월요일 자동 저장 사본을 이어 받아 주간(49) 저장 약 2초·일간(999) 약 1초, 불러오기/저장 화면 1·10페이지 스크린숏(일간·주간 이름표, 저장 화면에선 흐림), 주간 저장 파일을 다시 이어 받기 성공.\n"
              f"- 검증: VM {qa['vm_steps']}스텝(r3·r5·r6·r7 전부 + r8 요일 7종·이름표·잠금·최근 저장 찾기·확인 제목 3종·게임 오버 9경우·이전 함수 5개 원본 대조 + r10/r11 빈/전부/일부 저장·메뉴 흐름·모든 줄 38자 이내·표시 문자 포함 38자·색 구간 분해·제목 판정 + r12 교체 4곳·대화 경우 10가지 + r13 RunHome 이전 본문 대조·줄 대응·클릭 조건·메뉴 열기/닫기 7경우), 세이브 {qa['existing_resume_saves']}개/복귀 {qa['saved_return_frames']}지점 exact, 네이티브 탐침 9종 예외 0건(본거지 패널 클릭 → 캐릭터 창 → 첫 메뉴 복귀, 던전 대화 자동 진행·탐색 이어 가기, 색 분할 그리기 픽셀 동일 3쪽·색 화면 메뉴 9장), Defender·설치복구 fixture PASS.\n"
              f"- AIN {after['NightRemaster.ain']}; PACT {after['NightRemasterPact.afa']}; EX {after['NightRemasterEX.ex']}; manifest {mh}; evidence {E}; 되돌리기 publish_claude_term_rate_20260924_r13.py --restore (→ r12).\n")
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
