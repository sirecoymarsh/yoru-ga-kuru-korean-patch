"""r20 one-off: a third run in the full probe - a dungeon save (the status window opened from the dungeon, C_Status::
RunStatusInDungeon, the other caller of the status window) -> pages 1..4 -> 「이벤트」 -> exit -> parts gone."""
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'probe_calendar_r20.py'
s = p.read_text(encoding='utf8')
assert 'DUNGEON_SAVE' not in s, 'already patched'


def rep(a, b, count=1):
    global s
    assert s.count(a) == count, (a[:90], s.count(a))
    s = s.replace(a, b)


rep("HOVER = (3, 8)                    # the two portraits the probe hovers (쿄카, 모모세: both selectable in NightR40)",
    "HOVER = (3, 8)                    # the two portraits the probe hovers (쿄카, 모모세: both selectable in NightR40)\n"
    "DUNGEON_SAVE = 'NightR20.asd'     # saved from the dungeon's save screen (C_SceneDungeon@Run): the dungeon status window")
rep("LIVE_R20 = ('C_Status::RunStatus', 'RunSelectPartner', 'RunMember', 'C_SceneSaveLoad@RunCommon')   # waits the r20 screens need",
    "LIVE_R20 = ('C_Status::RunStatus', 'RunSelectPartner', 'RunMember', 'C_SceneSaveLoad@RunCommon', 'C_SceneDungeon@Run')   # waits the r20 screens need")
rep("                   'C_SceneHomebase@<lambda : C_SceneHomebase@RunMember()(233, 52)>', 'C_SceneSaveLoad@RunCommon']",
    "                   'C_SceneHomebase@<lambda : C_SceneHomebase@RunMember()(233, 52)>', 'C_SceneSaveLoad@RunCommon', 'C_SceneDungeon@Run']")
rep('''    bool pr = stage.Find("pt") == 0;
    if (!r20 && !pr) return false;''',
    '''    bool pr = stage.Find("pt") == 0;
    bool dg = stage.Find("dg") == 0;
    if (!r20 && !pr && !dg) return false;''')
rep('''    if (stage.Find("r20") == 0 || stage.Find("pt") == 0) return;''',
    '''    if (stage.Find("r20") == 0 || stage.Find("pt") == 0 || stage.Find("dg") == 0) return;''')
rep('''    if (save == "@@PARTNER_SAVE@@") KR_CPSet("Stage", "pt0");''',
    '''    if (save == "@@PARTNER_SAVE@@") KR_CPSet("Stage", "pt0");
    if (save == "@@DUNGEON_SAVE@@") KR_CPSet("Stage", "dg0");''')
rep("    jaf = jaf.replace('@@PARTNER_SAVE@@', PARTNER_SAVE)",
    "    jaf = jaf.replace('@@DUNGEON_SAVE@@', DUNGEON_SAVE).replace('@@PARTNER_SAVE@@', PARTNER_SAVE)")
DG = r'''    // ---------------- r20 dungeon (run 3): the status window opened from the dungeon (RunStatusInDungeon)
    if (stage == "dg0") {
        if (KR_CPOn("C_SceneSaveLoad@Update")) { KR_CPSet("Frames2", "0"); return true; }
        if (!KR_CPOn("C_SceneDungeon@")) return false;
        if (frames < 60) return false;
        int wd = L_Party::GetPersonID(1);
        if (wd <= 1) wd = L_Party::GetPersonID(2);
        if (wd <= 1) wd = 1;
        KR_CPSet("WD", "%d" % wd);
        KR_ClaudeProbeLog("DUNGEON date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " person=" + ("%d" % wd));
        KR_CPRegs();
        KR_CPCount("DUNGEON before");
        KR_ClaudeShot("cal_dungeon_before.bmp");
        KR_CPSet("Stage", "dg1");
        KR_CPEnd2(1000 + wd);
        return false;
    }
    if (stage == "dg1") {
        if (!KR_CPOn("C_Status::_UpdateInput")) return false;
        KR_ClaudeProbeLog("DUNGEON STATUS stack=" + KR_CPStack());
        KR_CPCount("DG page1");
        KR_CPSet("Stage", "dg2");
        KR_CPEnd2(2);
        return false;
    }
    if (stage == "dg2") { KR_CPSet("Stage", "dg3"); KR_CPEnd2(2); return false; }
    if (stage == "dg3") { KR_CPSet("Stage", "dg4"); KR_CPEnd2(2); return false; }
    if (stage == "dg4") {
        KR_CPCount("DG page4");
        KR_ClaudeProbeLog("STCHARA D " + KR_CPGet("WD"));
        KR_CPStText("D");
        KR_ClaudeShot("cal_status_event_dungeon.bmp");
        KR_CPSet("Stage", "dg5");
        KR_CPEnd2(0);
        return false;
    }
    if (stage == "dg5") {
        if (!KR_CPOn("C_SceneDungeon@")) return false;
        if (frames < 60) return false;
        KR_CPCount("DUNGEON after");
        KR_ClaudeShot("cal_dungeon_after.bmp");
        KR_ClaudeProbeLog("END");
        system.Exit(0);
        return false;
    }
'''
rep('''    // ---------------- r20 partner select (run 2): labels, hover A, hover B, confirm (no), again, confirm (yes)''',
    DG + '''    // ---------------- r20 partner select (run 2): labels, hover A, hover B, confirm (no), again, confirm (yes)''')
rep('''    if mode == 'full':
        saves = saves + [PARTNER_SAVE]          # r20 run 2: the Saturday partner selection''',
    '''    if mode == 'full':
        saves = saves + [PARTNER_SAVE, DUNGEON_SAVE]     # r20 run 2: the Saturday partner selection, run 3: the dungeon status''')
rep("""        result['partner_run'] = dict(save=pr['save'], exit_code=pr.get('exit_code'), seconds=pr.get('seconds'), log=pr['log'],
                                     vm_error=pr.get('vm_error'), message=pr.get('message'), events=pr.get('events'),
                                     save_folder=pr.get('save_folder'), shots=pr.get('shots_taken'))""",
    """        result['partner_run'] = dict(save=pr['save'], exit_code=pr.get('exit_code'), seconds=pr.get('seconds'), log=pr['log'],
                                     vm_error=pr.get('vm_error'), message=pr.get('message'), events=pr.get('events'),
                                     save_folder=pr.get('save_folder'), shots=pr.get('shots_taken'))
        dr = results[2]
        result['dungeon_run'] = dict(save=dr['save'], exit_code=dr.get('exit_code'), seconds=dr.get('seconds'), log=dr['log'],
                                     vm_error=dr.get('vm_error'), message=dr.get('message'), events=dr.get('events'),
                                     save_folder=dr.get('save_folder'), shots=dr.get('shots_taken'))""")
rep("""        result['r20'] = r20_report(result['log'], result['partner_run']['log'])""",
    """        result['r20'] = r20_report(result['log'], result['partner_run']['log'])
        result['r20']['dungeon'] = r20_dungeon_report(result['dungeon_run']['log'])
        a, b = dest / 'cal_dungeon_before.png', dest / 'cal_dungeon_after.png'
        if a.exists() and b.exists():
            result['dungeon_before_after_status'] = diff_pixels(a, b)""")
rep('''def parse_state(text):''',
    '''def r20_dungeon_report(log):
    counts = [l for l in log if l.startswith('COUNT ')]

    def ours(tag):
        hits = [l for l in counts if l.startswith('COUNT ' + tag + ' ')]
        assert hits, ('no COUNT line', tag)
        z = re.search(r' ours=(\\d+) charastatus=(\\d+) selectally=(\\d+) homemember=(\\d+)', hits[-1])
        return dict(ours=int(z.group(1)), charastatus=int(z.group(2)), selectally=int(z.group(3)), homemember=int(z.group(4)))
    b = blocks(log)
    return dict(counts=counts, before=ours('DUNGEON before'), page1=ours('DG page1'), page4=ours('DG page4'), after=ours('DUNGEON after'),
                text=b.get(('STTEXT', 'D')), person=next((int(l.split()[2]) for l in log if l.startswith('STCHARA D ')), None),
                date=next((l for l in log if l.startswith('DUNGEON date=')), None),
                stack=next((l for l in log if l.startswith('DUNGEON STATUS stack=')), None))


def parse_state(text):''')
p.write_text(s, encoding='utf8')
print('patched', p)
