"""one-off: turn the copy of probe_calendar_r18.py into probe_calendar_r19.py (r19 pages: dungeon card + its stage list, a
dungeon-walk drawer list + scene page, an after-training drawer list + scene page, the target stage list rows)."""
from pathlib import Path

P = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r19_calendar\probe_calendar_r19.py')
s = P.read_text(encoding='utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:100], s.count(old))
    s = s.replace(old, new)


rep('''"""Claude Opus 5.5 (2026-09-27) r18: isolated, muted native probe of the calendar candidate (after probe_calendar_r17.py).

  python probe_calendar_r18.py [SAVE]              full probe (default: work/probe_pick.json, else the newest home-base save copy)
  python probe_calendar_r18.py --regs SAVE ...     per save: resume, log today's date, every calendar event registered in that''',
    '''"""Claude Opus 5.5 (2026-09-27) r19: isolated, muted native probe of the calendar candidate (after probe_calendar_r18.py).

  python probe_calendar_r19.py [SAVE]              full probe (default: work/probe_pick.json, else the newest home-base save copy)
  python probe_calendar_r19.py --regs SAVE ...     per save: resume, log today's date, every calendar event registered in that''')
rep('''  python probe_calendar_r18.py --savefolder-test   only: resume + home menu screenshot + exit (checks the P: save folder)''',
    '''  python probe_calendar_r19.py --savefolder-test   only: resume + home menu screenshot + exit (checks the P: save folder)''')
rep('''Everything lives under r18_calendar\\\\probe\\\\ on P:''', '''Everything lives under r19_calendar\\\\probe\\\\ on P:''')
rep('''  run\\\\SaveData_R18CalendarProbe_<stamp>\\\\  global record files + one save, COPIES (r18lib.save_path).''',
    '''  run\\\\SaveData_R19CalendarProbe_<stamp>\\\\  global record files + one save, COPIES (r19lib.save_path).''')
rep('''  r18 lock: the first ● card''', '''  r19 names: a dungeon card [shot cal_card_dungeon, TITLE] -> 단계 고르기 [shot cal_stages_dungeon, TITLE, ROWS] -> back;
  a dungeon-walk drawer (마나미 레인) [shot cal_drawer_walk, TITLE, ROWS] -> a scene with a partner [shot cal_scene_walk, TITLE]
  -> back; an after-training drawer [shot cal_drawer_after, TITLE, ROWS] -> its first scene [shot cal_scene_after, TITLE] -> back
  r18 lock: the first ● card''')
rep('''Every page title and drawer-row list is logged for the offline comparison (verify_calendar_r18.py --native).''',
    '''Every page title, lane-row list, stage list and drawer scene list is logged for the offline comparison
(verify_calendar_r19.py --native).''')
rep('import r18lib as L\n', 'import r19lib as L\n')
rep('''MANAMI = 3          # lane 3 = 마나미 (October holds the eight 10/11 rows that carry E-number tails; page 2 has drawer rows)''',
    '''MANAMI = 3          # lane 3 = 마나미 (October holds the eight 10/11 branch rows: r19 affinity conditions + name tails)''')

# ---- probe jaf: helpers for list rows
rep('''void KR_CPMemRows() {''', '''// r19: stage-list / drawer-list lines as KR_T19StagePage / KR_T19ChipPage list them (same functions, same paging)
void KR_CPStageRows(int k, int page) {
    int n = KR_T9CardSize(k);
    int s0 = KR_T9CardStage(k);
    int per = KR_T19ListPer(KR_T19StageCols(k), n);
    int first = page * per;
    int last = first + per;
    if (last > n) last = n;
    string t = "";
    for (int i = first; i < last; i++) {
        if (i > first) t = t + "\\n";
        t = t + KR_T19ListItem(KR_T9StageEv(s0 + i));
    }
    KR_CPBlock("ROWS", "STAGELIST " + ("%d" % k) + " p" + ("%d" % (page + 1)), t);
}
void KR_CPChipRows(int c, int page) {
    int n = KR_T9ChipSize(c);
    int s0 = KR_T9ChipScene(c);
    int per = KR_T19ListPer(KR_T19ChipCols(c), n);
    int first = page * per;
    int last = first + per;
    if (last > n) last = n;
    string t = "";
    for (int i = first; i < last; i++) {
        if (i > first) t = t + "\\n";
        t = t + KR_T19ListItem(KR_T19SceneAt(s0 + i));
    }
    KR_CPBlock("ROWS", "DRAWER " + ("%d" % c) + " p" + ("%d" % (page + 1)), t);
}
void KR_CPMemRows() {''')

# ---- tick: after the April dungeon lane -> r19 pages -> lock
rep('''    if (stage == "aprdun") {
        KR_CPTitleLog("LANE 4 @@DUNGEON@@");
        KR_CPLaneRows(4, @@DUNGEON@@, 0);
        KR_ClaudeShot("cal_lane_apr_dungeon.bmp");
        KR_CPSet("Stage", "lock");
        KR_CPSet("LockSt", "0");
        KR_CPEnd(0);
        return;
    }''', '''    if (stage == "aprdun") {
        KR_CPTitleLog("LANE 4 @@DUNGEON@@");
        KR_CPLaneRows(4, @@DUNGEON@@, 0);
        KR_ClaudeShot("cal_lane_apr_dungeon.bmp");
        KR_CPSet("Stage", "dcard");
        KR_CPEnd(0);
        return;
    }
    // ---- r19 names: a dungeon card and its stage list
    if (stage == "dcard") {
        if (!KR_CPGoto(@@D_MONTH@@)) return;
        KR_CPSet("Stage", "dcardlane");
        KR_CPEnd(20 + @@DUNGEON@@);
        return;
    }
    if (stage == "dcardlane") {
        KR_CPTitleLog("LANE @@D_MONTH@@ @@DUNGEON@@");
        KR_CPLaneRows(@@D_MONTH@@, @@DUNGEON@@, 0);
        KR_CPSet("Stage", "dcardopen");
        KR_CPEnd(100 + @@D_INDEX@@);
        return;
    }
    if (stage == "dcardopen") {
        int kd = KR_T9LaneCardAt(@@D_MONTH@@, @@DUNGEON@@, @@D_INDEX@@);
        KR_CPTitleLog("DCARD " + ("%d" % kd) + " @@D_MONTH@@");
        KR_ClaudeShot("cal_card_dungeon.bmp");
        KR_CPSet("Stage", "dstages");
        KR_CPEnd(14);
        return;
    }
    if (stage == "dstages") {
        int kd2 = KR_T9LaneCardAt(@@D_MONTH@@, @@DUNGEON@@, @@D_INDEX@@);
        KR_CPTitleLog("DSTAGES " + ("%d" % kd2) + " @@D_MONTH@@");
        KR_CPStageRows(kd2, 0);
        KR_ClaudeShot("cal_stages_dungeon.bmp");
        KR_CPSet("Stage", "dback1");
        KR_CPEnd(0);
        return;
    }
    if (stage == "dback1") { KR_CPSet("Stage", "dback2"); KR_CPEnd(0); return; }
    if (stage == "dback2") { KR_CPSet("Stage", "walk"); KR_CPEnd(0); return; }
    // ---- r19 names: a dungeon-walk drawer list and one of its scenes (a partner walk)
    if (stage == "walk") {
        if (!KR_CPGoto(@@W_MONTH@@)) return;
        KR_CPSet("Stage", "walklane");
        KR_CPEnd(20 + @@W_LANE@@);
        return;
    }
    if (stage == "walklane") {
        KR_CPSet("Stage", "walklist");
        KR_CPEnd(100 + @@W_ROW@@);
        return;
    }
    if (stage == "walklist") {
        KR_CPTitleLog("DRAWER @@W_CHIP@@");
        KR_CPChipRows(@@W_CHIP@@, 0);
        KR_ClaudeShot("cal_drawer_walk.bmp");
        KR_CPSet("Stage", "walkscene");
        KR_CPEnd(100 + @@W_ITEM@@);
        return;
    }
    if (stage == "walkscene") {
        KR_CPTitleLog("SCENE @@W_CHIP@@ @@W_ITEM@@");
        KR_ClaudeShot("cal_scene_walk.bmp");
        KR_CPSet("Stage", "wback1");
        KR_CPEnd(0);
        return;
    }
    if (stage == "wback1") { KR_CPSet("Stage", "wback2"); KR_CPEnd(0); return; }
    if (stage == "wback2") { KR_CPSet("Stage", "after"); KR_CPEnd(0); return; }
    // ---- r19 names: an after-training drawer list and its first scene
    if (stage == "after") {
        if (!KR_CPGoto(@@A_MONTH@@)) return;
        KR_CPSet("Stage", "afterlane");
        KR_CPEnd(20 + @@A_LANE@@);
        return;
    }
    if (stage == "afterlane") {
        KR_CPSet("Stage", "afterlist");
        KR_CPEnd(100 + @@A_ROW@@);
        return;
    }
    if (stage == "afterlist") {
        KR_CPTitleLog("DRAWER @@A_CHIP@@");
        KR_CPChipRows(@@A_CHIP@@, 0);
        KR_ClaudeShot("cal_drawer_after.bmp");
        KR_CPSet("Stage", "afterscene");
        KR_CPEnd(100 + @@A_ITEM@@);
        return;
    }
    if (stage == "afterscene") {
        KR_CPTitleLog("SCENE @@A_CHIP@@ @@A_ITEM@@");
        KR_ClaudeShot("cal_scene_after.bmp");
        KR_CPSet("Stage", "aback1");
        KR_CPEnd(0);
        return;
    }
    if (stage == "aback1") { KR_CPSet("Stage", "aback2"); KR_CPEnd(0); return; }
    if (stage == "aback2") {
        KR_CPSet("Stage", "lock");
        KR_CPSet("LockSt", "0");
        KR_CPEnd(0);
        return;
    }''')
rep('''    if (stage == "sbxstages") {
        KR_CPTitleLog("STAGES");''', '''    if (stage == "sbxstages") {
        KR_CPTitleLog("STAGES");
        KR_CPStageRows(KR_T9LaneCardAt(@@T_MONTH@@, @@T_LANE@@, @@T_INDEX@@), 0);
        KR_ClaudeShot("cal_stages.bmp");''')

# ---- python side: targets, placeholders, names
rep('''def target_jaf(t):
''', '''def name_targets(X):
    """r19 probe pages: (D) the first dungeon card with stages on the first page of its October lane page, (W) the 마나미 lane's
    dungeon-walk drawer (first lane page) and its first scene with a partner (마코토 when there is one), (A) the 이즈미 lane's
    after-training drawer (first lane page) and its first scene."""
    def lane_items(month, lane):
        cs = [(k, c) for k, c in enumerate(X['cards']) if c['month'] == month and c['lane'] == lane]
        ch = [(i, x) for i, x in enumerate(X['chips']) if x['month'] == month and x['lane'] == lane]
        n = len(cs) + len(ch)
        return cs, ch, (10 if n <= 10 else 8)
    out = {}
    for month in (10, 11, 9, 8, 7, 6, 5):
        cs, ch, per = lane_items(month, 8)
        hit = [(j, k) for j, (k, c) in enumerate(cs) if c['size'] > 1 and j < per]
        if hit:
            out['D'] = dict(month=month, index=hit[0][0], k=hit[0][1])
            break
    sch = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    evs = {e['id']: e for e in sch['events']}
    for kind, lane, key, pick in (('walk', 3, 'W', lambda e: 5 in (e['person'], e['person2'])), ('after', 1, 'A', lambda e: True)):
        for month in range(4, 12):
            cs, ch, per = lane_items(month, lane)
            for j, (i, x) in enumerate(ch):
                if KIND[x['kind']] != kind or len(cs) + j >= per:
                    continue
                order = sorted(x['scenes'])
                items = [n for n, no in enumerate(order) if pick(evs[no])] or [0]
                if items[0] < 30:
                    out[key] = dict(month=month, lane=lane, row=len(cs) + j, chip=i, item=items[0], event=order[items[0]])
                    break
            if key in out:
                break
    assert set(out) == {'D', 'W', 'A'}, out
    return out


KIND = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']


def target_jaf(t):
''')
rep('''def build_probe(source, key, work, mode, target):''', '''def build_probe(source, key, work, mode, target, names=None):''')
rep('''    jaf = (jaf.replace('@@T_MONTH@@', str(t['month'])).replace('@@T_LANE@@', str(t['lane'])).replace('@@T_INDEX@@', str(t['index']))
           .replace('@@T_STAGE@@', str(t['stage'])).replace('@@T_EVENT@@', str(t['event'])))''',
    '''    jaf = (jaf.replace('@@T_MONTH@@', str(t['month'])).replace('@@T_LANE@@', str(t['lane'])).replace('@@T_INDEX@@', str(t['index']))
           .replace('@@T_STAGE@@', str(t['stage'])).replace('@@T_EVENT@@', str(t['event'])))
    nt = names or dict(D=dict(month=4, index=0), W=dict(month=4, lane=1, row=0, chip=0, item=0), A=dict(month=4, lane=1, row=0, chip=0, item=0))
    for p, d in nt.items():
        for f, v in d.items():
            jaf = jaf.replace('@@%s_%s@@' % (p, f.upper()), str(v))''')
rep('''    savename = f'SaveData_R18CalendarProbe_{stamp}\'''', '''    savename = f'SaveData_R19CalendarProbe_{stamp}\'''')
rep('''    import verify_calendar_r18 as V
    X = V.expectations()
    target = None''', '''    import verify_calendar_r19 as V
    X = V.expectations()
    target = None
    names = None''')
rep('''        target = sandbox_target(X, set(row['state']['regs']))
        print('sandbox target', target, flush=True)''', '''        target = sandbox_target(X, set(row['state']['regs']))
        print('sandbox target', target, flush=True)
        names = name_targets(X)
        print('name pages', names, flush=True)''')
rep('''    info = build_probe(O, keys.pop(), work, mode, target)''', '''    info = build_probe(O, keys.pop(), work, mode, target, names)''')
rep('''                  target=info['target'] if info else None)''', '''                  target=info['target'] if info else None, name_pages=names)''')
rep('''        out = dict(common, saves=results, schema='yoru-calendar-r18.probe-regs.v1', author=L.AUTHOR)''',
    '''        out = dict(common, saves=results, schema='yoru-calendar-r19.probe-regs.v1', author=L.AUTHOR)''')
rep('''def expectations():
    import verify_calendar_r18 as V''', '''def expectations():
    import verify_calendar_r19 as V''')
rep('''    for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex']:          # PACT/EX are the runtime's (r18 does not change them)''',
    '''    for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex']:          # PACT/EX are the runtime's (r19 does not change them)''')
assert 'r18lib' not in s and 'verify_calendar_r18' not in s
P.write_text(s, encoding='utf-8', newline='\n')
print('ok')
