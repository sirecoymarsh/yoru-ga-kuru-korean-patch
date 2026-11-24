PROBE_JAF = r'''
string KR_PRRead(string file) {
    string s = "";
    if (!TextFile.ReadAll(file, s)) return "";
    return s;
}
void KR_PRLog(string text) {
    TextFile.WriteAll("claude_probe.txt", KR_PRRead("claude_probe.txt") + text + "\n");
}
void KR_PRShot(string file) {
    AFL_View_Update(); AFL_View_Update(); AFL_View_Update();
    if (!SystemService.SaveScreenshot(file, 0, 0, 1280, 720)) system.Exit(9);
    KR_PRLog("SHOT " + file);
}
string KR_PRGet(string key) { return SystemService.SystemVariable_Get("YoruKR.HVProbe." + key); }
void KR_PRSet(string key, string value) { SystemService.SystemVariable_Set("YoruKR.HVProbe." + key, value); }
int KR_PRNum(string key) { string v = KR_PRGet(key); if (v == "") return 0; return v.ToInt(); }
int KR_PRB(bool v) { if (v) return 1; return 0; }
string KR_PRStage() { return KR_PRRead("claude_probe_stage.txt"); }
void KR_PRStageSet(string s) { TextFile.WriteAll("claude_probe_stage.txt", s); KR_PRLog("STAGE " + s); }
void KR_PREnd(int code) { KR_PRSet("DFrames", "0"); AFL_Parts_EndWaitForClick(code); }
void KR_PRCheck(string what, bool ok) {
    if (ok) { KR_PRLog("OK " + what); return; }
    KR_PRLog("FAIL " + what);
    KR_PRSet("Fails", "%d" % (KR_PRNum("Fails") + 1));
}
int KR_PRRate() {
    for (int i = -1; i < 4; i++) {
        string a = KR_T8AreaName(i);
        if (AFL_Activity_IsExistPartsByName(a, "KR_HomeRate")) return KR_PRB(Ｐ＿表示設定取得(AFL_Activity_GetPartsNumber(a, "KR_HomeRate")));
    }
    return -1;
}
string KR_PRAct() {
    for (int i = -1; i < 4; i++) {
        string a = KR_T8AreaName(i);
        if (AFL_Activity_IsExistPartsByName(a, "KR_HR_Box2")) return a;
    }
    return "";
}
int KR_PRP(string act, string n) {
    if (act == "") return 0;
    if (!AFL_Activity_IsExistPartsByName(act, n)) return 0;
    return AFL_Activity_GetPartsNumber(act, n);
}
string KR_PRT(string act, string n) {
    int p = KR_PRP(act, n);
    if (p <= 0) return "<none>";
    return Ｐ＿テキスト取得(p, 1);
}
int KR_PRShown(string act, string n) {
    int p = KR_PRP(act, n);
    if (p <= 0) return -1;
    return KR_PRB(Ｐ＿表示設定取得(p));
}
int KR_PREv() { return KR_PlayerEventCount(0) + KR_PlayerEventCount(1) + KR_PlayerEventCount(2) + KR_PlayerEventCount(3); }
string KR_PRPanel(string act) {
    string t = "ev='" + KR_PRT(act, "KR_HR_EvValue") + "' story='" + KR_PRT(act, "KR_HR_Story") + "'";
    for (int p = 2; p <= 8; p++) t = t + " c" + ("%d" % p) + "='" + KR_PRT(act, "KR_HR_Pct" + ("%d" % p)) + "'";
    for (int j = 0; j <= 3; j++) t = t + " a" + ("%d" % j) + "='" + KR_PRT(act, "KR_HR_AllValue" + ("%d" % j)) + "'";
    t = t + " body=" + ("%d" % KR_PRShown(act, "KR_HomeRateBody")) + " cal=" + ("%d" % KR_PRShown(act, "KR_HR_CalBox")) + "/" + ("%d" % KR_PRShown(act, "KR_HR_CalText"));
    return t;
}
string KR_PRExpect() {
    string t = "ev=" + KR_T8Pct(KR_PREv(), 1043);
    for (int p = 2; p <= 8; p++) t = t + " c" + ("%d" % p) + "=" + KR_T8Pct(KR_T8CharEvents(p), KR_T8CharTotal(p));
    t = t + " read=" + KR_T8Pct(KR_T8ReadCount(), 74966) + " cg=" + KR_T8Pct(KR_T8CgCount(), 60) + " scene=" + KR_T8Pct(KR_T8SceneCount(), 66) + " end=" + ("%d" % KR_T8EndingCount());
    return t;
}
bool KR_PRValuesOK(string act) {
    if (KR_PRT(act, "KR_HR_EvValue") != KR_T8Pct(KR_PREv(), 1043)) return false;
    for (int p = 2; p <= 8; p++) {
        if (KR_PRT(act, "KR_HR_Pct" + ("%d" % p)) != KR_T8Pct(KR_T8CharEvents(p), KR_T8CharTotal(p))) return false;
    }
    if (KR_PRT(act, "KR_HR_AllValue0") != KR_T8Pct(KR_T8ReadCount(), 74966)) return false;
    if (KR_PRT(act, "KR_HR_AllValue1") != KR_T8Pct(KR_T8CgCount(), 60)) return false;
    if (KR_PRT(act, "KR_HR_AllValue2") != KR_T8Pct(KR_T8SceneCount(), 66)) return false;
    if (KR_PRT(act, "KR_HR_AllValue3") != ("%d" % KR_T8EndingCount()) + " / 5") return false;
    if (KR_PRT(act, "KR_HR_Story") != KR_StoryHome()) return false;
    return true;
}

// ---- the home top menu and the character window (C_SelectDialog@_Update prefix)
void KR_ProbeDlgTick() {
    string stage = KR_PRStage();
    int frames = KR_PRNum("DFrames") + 1;
    KR_PRSet("DFrames", "%d" % frames);
    if (frames > 3000) { KR_PRLog("STUCK dialog stage=" + stage); KR_PRShot("hv_stuck.bmp"); system.Exit(5); return; }
    if (frames < 12) return;
    if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") {
        if (stage == "char") {
            if (frames < 40) return;
            KR_PRShot("hv_char.bmp");
            KR_PRCheck("the 쿄카 row opened the character window", true);
            KR_PRStageSet("after_char");
            KR_PREnd(-1);
            return;
        }
        if (stage == "home0" && frames < 600) return;
        KR_PRLog("UNEXPECTED DIALOG stage=" + stage + " frames=" + ("%d" % frames));
        KR_PRShot("hv_unexpected_dialog.bmp");
        system.Exit(7);
        return;
    }
    string act = KR_PRAct();
    if (stage == "home0") {
        if (frames < 40) return;
        KR_PRLog("HOME panel=" + ("%d" % KR_PRRate()) + " act=" + act + " " + KR_PRPanel(act));
        KR_PRLog("EXPECT " + KR_PRExpect() + " story=" + KR_StoryHome());
        KR_PRCheck("panel shown", KR_PRRate() == 1);
        KR_PRCheck("new panel parts present", act != "");
        KR_PRCheck("values = the old panel's sources and totals", KR_PRValuesOK(act));
        KR_PRCheck("old text body hidden", KR_PRShown(act, "KR_HomeRateBody") == 0);
        KR_PRCheck("calendar button shown while the top menu waits", KR_PRShown(act, "KR_HR_CalBox") == 1 && KR_PRShown(act, "KR_HR_CalText") == 1);
        KR_PRShot("hv_home.bmp");
        KR_PRStageSet("chart");
        KR_PRLog("CLICK calendar button");
        KR_T8HomeClick(KR_PRP(act, "KR_HR_CalBox"), 80, @@CAL_Y@@ + 12);
        return;
    }
    if (stage == "chart") {
        KR_PRLog("HOME again before the chart frame (stage chart) frames=" + ("%d" % frames));
        KR_PRShot("hv_no_chart.bmp");
        system.Exit(12);
        return;
    }
    if (stage == "after_chart") {
        if (frames < 40) return;
        KR_PRLog("HOME AFTER CHART panel=" + ("%d" % KR_PRRate()) + " " + KR_PRPanel(act));
        KR_PRCheck("chart frames ran", KR_PRNum("ChartFrames") >= 30);
        KR_PRCheck("panel and calendar button back after the chart", KR_PRRate() == 1 && KR_PRShown(act, "KR_HR_CalBox") == 1);
        KR_PRShot("hv_home_after_chart.bmp");
        KR_PRStageSet("char");
        KR_PRLog("CLICK 쿄카 row");
        KR_T8HomeClick(KR_PRP(act, "KR_HR_Box3"), 80, @@ROW_Y0@@ + @@ROW_STEP@@ + 20);
        return;
    }
    if (stage == "after_char") {
        if (frames < 40) return;
        KR_PRCheck("panel back after the character window", KR_PRRate() == 1 && KR_PRShown(act, "KR_HR_CalBox") == 1);
        KR_PRShot("hv_home_end.bmp");
        KR_PRCheck("row map: 이즈미 top, 모모세 bottom, gaps and the title area empty",
                   KR_HVRow(@@ROW_Y0@@) == 2 && KR_HVRow(@@ROW_Y0@@ + 6 * @@ROW_STEP@@ + 39) == 8 && KR_HVRow(@@ROW_Y0@@ + 40) == 0 && KR_HVRow(100) == 0 && KR_HVRow(@@ROW_Y0@@ + 7 * @@ROW_STEP@@) == 0);
        KR_PRCheck("row map: calendar button marks the pick", KR_HVRow(@@CAL_Y@@ + 5) == 2 && KR_HVGet("Cal") == "1");
        KR_HVPut("Cal", "");
        KR_PRLog("FAILS " + ("%d" % KR_PRNum("Fails")));
        KR_PRLog("END");
        system.Exit(0);
        return;
    }
    KR_PRLog("HOME in stage " + stage);
    KR_PRShot("hv_home_unexpected.bmp");
    system.Exit(6);
}
// ---- the event calendar's frame delegate (KR_CFrame prefix): a shot, then close (wait result 0)
void KR_ProbeChartTick() {
    int f = KR_PRNum("ChartFrames") + 1;
    KR_PRSet("ChartFrames", "%d" % f);
    if (f == 1) KR_PRLog("CHART open panel=" + ("%d" % KR_PRRate()));
    if (f == 30) KR_PRShot("hv_chart.bmp");
    if (f == 32) {
        KR_PRStageSet("after_chart");
        KR_PRSet("DFrames", "0");
        AFL_Parts_EndWaitForClick(0);
    }
    if (f > 3000) { KR_PRLog("CHART STUCK"); system.Exit(5); }
}

// ---- waits
int KR_ProbeMsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    int n = KR_PRNum("Msgs") + 1;
    KR_PRSet("Msgs", "%d" % n);
    if (n > 3000) { KR_PRLog("TOO MANY MESSAGES"); system.Exit(8); return 0; }
    return 0;
}
int KR_ProbeWaitExit(FTPARTS_WaitForClickCallback func, bool cancel) {
    KR_PRLog("UNEXPECTED WAIT stage=" + KR_PRStage());
    KR_PRShot("hv_wait.bmp");
    system.Exit(4);
    return 0;
}
int KR_ProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_PRLog("SAVEFOLDER " + system.GetSaveFolderName());
    KR_T8HomeRateSet(true);
    KR_PRLog("HOMERATE ON " + ("%d" % KR_PRB(KR_T8HomeRateOn())));
    string save = KR_PRRead("claude_probe_save.txt");
    KR_PRLog("RESUME " + save + " stage=" + KR_PRStage());
    if (save == "") { system.Exit(3); return 3; }
    system.ResumeLoad("@@KEY@@", save);
    system.Exit(2);
    return 2;
}
'''


