# -*- coding: utf-8 -*-
"""Make probe_deadline.py from calendar_title_20261018/probe_title.py (read only): the same launcher and tours (the list now runs
through KR_DLRun / KR_DLDraw), the PACT candidate in the run folder, and before the home tours the deadline panel:
home menu -> the panel (rows, counts, sorted deadlines, only joined companions) -> 「목록에서 보기」 (KR_DLClick) -> the list on
기한 (count = the panel's, rows in deadline order) -> 전체 chip -> 기한 chip -> 닫기 -> home (the panel again) -> the old tour.
The title tour also checks that the title list has no 기한 chip."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'calendar_title_20261018' / 'probe_title.py').read_text('utf8')


def rep(a, b):
    global src
    assert src.count(a) == 1, (a[:90], src.count(a))
    src = src.replace(a, b)


rep('import ltlib as L', 'import dllib as L')
rep("BOOT = 'NightRemasterTitleProbe'", "BOOT = 'NightRemasterDeadlineProbe'")
src = src.replace('lt_', 'dl_')
rep("savename = f'SaveData_TitleProbe_{stamp}'", "savename = f'SaveData_DeadlineProbe_{stamp}'")
src = src.replace("probe_title_{stamp}.json", "probe_deadline_{stamp}.json").replace("'probe_title.json'", "'probe_deadline.json'")
src = src.replace("f'probe_title_{HOME_SAVE[:-4]}.json'", "f'probe_deadline_{HOME_SAVE[:-4]}.json'").replace("f'probe_title_{HOME_SAVE}.json'", "f'probe_deadline_{HOME_SAVE}.json'")
# the PACT candidate (this layer adds the panel parts to AddArea)
rep("    PACT = rt / 'NightRemasterPact.afa'", "    PACT = O / 'NightRemasterPact.afa'")

# ---- probe helpers for the panel and the 기한 list
rep('''// ---- the home top menu (C_SelectDialog@_Update prefix)''', r'''// ---- the deadline panel
string KR_PRT(string act, string n) {
    int p = KR_PRP(act, n);
    if (p <= 0) return "<none>";
    return Ｐ＿テキスト取得(p, 1);
}
string KR_PRDLRows(string act) {
    string t = "";
    for (int k = 0; k < 8; k++) {
        if (KR_PRShown(act, "KR_DL_Text%d" % k) != 1) continue;
        t = t + "[" + KR_PRT(act, "KR_DL_Text%d" % k) + "|" + KR_PRT(act, "KR_DL_Num%d" % k) + "]";
    }
    return t;
}
// every pending scene: deadline order, unseen in this save, its companion joined, open today
bool KR_PRDLListOK(int n) {
    int today = KR_DLToday();
    int prev = 0;
    for (int k = 0; k < n; k++) {
        int ci = KR_DLNum("o%d" % k);
        int due = KR_DLNum("ou%d" % k);
        int no = KR_CCellEv(ci);
        int lane = KR_XVLaneNo(no);
        if (due < prev || due < today) return false;
        if (N_ScenarioRegister::IsRegisteredEvent(KR_T9Fn(no))) return false;
        if (lane < 2 || lane > 8 || !KR_T20Joined(lane)) return false;
        if (KR_DLDue(KR_DLInfo(no), today) != due) return false;
        prev = due;
    }
    return true;
}
// an independent count: this month's unseen 이즈미 특훈 뒤 대화 cells (by name) = the panel's 이즈미 monthly count this month
int KR_PRIzumiMonth() {
    int t = L_Calendar::GetMonth() - 4;
    int c = 0;
    for (int i = KR_CTabFirst(t); i < KR_CTabEnd(t); i++) {
        string nm = KR_CCellName(i);
        if (nm.Find("이즈미 · 특훈 뒤 대화") != 0) continue;
        if (N_ScenarioRegister::IsRegisteredEvent(KR_T9Fn(KR_CCellEv(i)))) continue;
        c++;
    }
    return c;
}
int KR_PRIzumiPending() {
    string ns = KR_DLGet("n");
    int n = ns.ToInt();
    int today = KR_DLToday();
    int end = (today / 100) * 100 + KR_DLMonthDays(today / 100);
    int c = 0;
    for (int k = 0; k < n; k++) {
        int no = KR_CCellEv(KR_DLNum("o%d" % k));
        if (KR_XVLaneNo(no) == 2 && KR_DLInfo(no) / 100000000 == 1 && KR_DLNum("ou%d" % k) == end) c++;
    }
    return c;
}

// ---- the home top menu (C_SelectDialog@_Update prefix)''')
rep('''        KR_PRCheck("home panel shown with the calendar button", KR_PRRate() == 1 && KR_PRShown(act, "KR_HR_CalBox") == 1);
        KR_PRStageSet("b1");
        KR_PRSet("CFrames", "0");
        KR_T8HomeClick(KR_PRP(act, "KR_HR_CalBox"), 80, @@CAL_Y@@ - KR_HVUp() + 12);
        return;
    }''', '''        KR_PRCheck("home panel shown with the calendar button", KR_PRRate() == 1 && KR_PRShown(act, "KR_HR_CalBox") == 1);
        int pn = KR_DLNum("panel");
        KR_PRLog("DEADLINE panel n=" + KR_DLGet("panel") + " today=" + ("%d" % KR_DLToday()) + " rows=" + KR_PRDLRows(act));
        KR_PRLog("IZUMI this month: cells unseen=" + ("%d" % KR_PRIzumiMonth()) + " pending=" + ("%d" % KR_PRIzumiPending()));
        KR_PRCheck("deadline panel: shown with its rows and button (something is pending)",
                   pn > 0 && KR_PRShown(act, "KR_DL_Box") == 1 && KR_PRShown(act, "KR_DL_Title") == 1 && KR_PRShown(act, "KR_DL_Text0") == 1
                   && KR_PRShown(act, "KR_DL_BtnBox") == 1 && KR_PRShown(act, "KR_DL_BtnText") == 1);
        KR_PRCheck("deadline panel: the first row is the nearest deadline", KR_PRHas(KR_PRP(act, "KR_DL_Text0"), KR_DLDate(KR_DLNum("ou0")) + "까지"));
        KR_PRCheck("deadline list data: deadline order, unseen here, joined companions, open today", KR_PRDLListOK(pn));
        KR_PRCheck("deadline panel: this month's 이즈미 talks = the unseen 이즈미 특훈 뒤 대화 cells of this month", KR_PRIzumiMonth() == KR_PRIzumiPending());
        KR_PRShot("dl_home_panel.bmp");
        KR_PRSet("PanelN", "%d" % pn);
        KR_PRStageSet("dl1");
        KR_PRSet("CFrames", "0");
        KR_PRLog("CLICK 목록에서 보기");
        KR_DLClick(KR_PRP(act, "KR_DL_BtnBox"), 1200, 340);
        return;
    }
    if (stage == "homeD") {
        if (frames < 40) return;
        KR_PRCheck("closing the 기한 list returns to the home menu with the panel again", KR_PRRate() == 1 && KR_PRShown(act, "KR_DL_Box") == 1 && KR_DLGet("Pick") == "");
        KR_PRStageSet("b1");
        KR_PRSet("CFrames", "0");
        KR_T8HomeClick(KR_PRP(act, "KR_HR_CalBox"), 80, @@CAL_Y@@ - KR_HVUp() + 12);
        return;
    }''')
# the 기한 list stages (both home tours), dispatched before the tour's own stages
rep('''void KR_ProbeChartTick() {
    string stage = KR_PRStage();
    int f = KR_PRNum("CFrames") + 1;
    KR_PRSet("CFrames", "%d" % f);
    if (f > 3000) { KR_PRLog("CHART STUCK stage=" + stage); KR_PRShot("dl_stuck.bmp"); system.Exit(5); }''', '''void KR_ProbeDL(string stage, int f) {
    if (stage == "dl1") {
        if (f == 30) {
            int n = KR_PRNum("PanelN");
            KR_PRLog("DL LIST foot=" + KR_PRTxt(KR_LVP(71)) + " head=" + KR_PRTxt(KR_LVP(2)) + " row0=" + KR_PRTxt(KR_LVP(102)) + " / " + KR_PRTxt(KR_LVP(103)));
            KR_PRCheck("목록에서 보기 opens the list on 기한 (count = the panel's)", KR_PRList() && KR_PRHas(KR_LVP(2), "기한 있는 장면") && KR_PRFoot(n)
                       && KR_DLNum("n") == n && PartsEngine.IsExist(KR_LVP(28)));
            KR_PRCheck("기한 rows: the first row shows the nearest deadline", KR_PRHas(KR_LVP(102), KR_DLDate(KR_DLNum("ou0"))));
            KR_PRCheck("기한 preview: the deadline line", KR_PRHas(KR_LVP(312), KR_DLDate(KR_DLNum("ou0")) + "까지"));
            KR_PRShot("dl_list_deadline.bmp");
        }
        if (f == 32) KR_PRGo("dl2", KR_LVP(10));
        return;
    }
    if (stage == "dl2") {
        if (f == 30) KR_PRCheck("the 전체 month chip leaves 기한", KR_PRList() && KR_PRHead(-1, -1));
        if (f == 32) KR_PRGo("dl3", KR_LVP(28));
        return;
    }
    if (stage == "dl3") {
        if (f == 30) KR_PRCheck("the 기한 chip comes back to 기한", KR_PRList() && KR_PRHas(KR_LVP(2), "기한 있는 장면") && KR_PRFoot(KR_PRNum("PanelN")));
        if (f == 32) {
            KR_PRStageSet("homeD");
            KR_PRSet("DFrames", "0");
            AFL_Parts_EndWaitForClick(KR_LVP(7));
        }
        return;
    }
    KR_PRLog("CHART TICK in stage " + stage);
    KR_PRShot("dl_unexpected.bmp");
    system.Exit(6);
}
void KR_ProbeChartTick() {
    string stage = KR_PRStage();
    int f = KR_PRNum("CFrames") + 1;
    KR_PRSet("CFrames", "%d" % f);
    if (f > 3000) { KR_PRLog("CHART STUCK stage=" + stage); KR_PRShot("dl_stuck.bmp"); system.Exit(5); }
    if (stage.StartsWith("dl")) { KR_ProbeDL(stage, f); return; }''')
# the home list has the 기한 chip; the title list has none
rep('''            KR_PRCheck("the board parts are released under the list", !PartsEngine.IsExist(KR_XVP(0)));''',
    '''            KR_PRCheck("the board parts are released under the list", !PartsEngine.IsExist(KR_XVP(0)));
            KR_PRCheck("home: the list has the 기한 chip", PartsEngine.IsExist(KR_LVP(28)));''')
rep('''            KR_PRCheck("title: 달 화면으로 drawn off", KR_PRHas(KR_LVP(55), KR_LVDimC()));''',
    '''            KR_PRCheck("title: 달 화면으로 drawn off", KR_PRHas(KR_LVP(55), KR_LVDimC()));
            KR_PRCheck("title: no 기한 chip", !PartsEngine.IsExist(KR_LVP(28)));''')
(HERE / 'probe_deadline.py').write_text(src, 'utf8')
print('ok', len(src.splitlines()))
