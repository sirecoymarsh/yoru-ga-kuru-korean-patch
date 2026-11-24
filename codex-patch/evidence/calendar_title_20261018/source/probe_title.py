# -*- coding: utf-8 -*-
"""Claude Opus 5.5 (2026-10-18): isolated, muted native probe of the title-calendar spoiler layer (KR_LT*) - copy of probe_list.py.
Title tour: board rows = 본편 + the companions present from the start + 던전 동행, 회상 · 그 밖 covered; 7월 list closed (rows,
preview, 달 화면으로), 달 화면으로 / 회상 open nothing, 던전 동행 rows naming later companions masked. Home tours as probe_list.py,
plus a 달 화면으로 round trip at home and 회상 · 그 밖 not covered at home.

  python probe_list.py              NightR47 (11/4, home): panel calendar button -> board [row name buttons, hint] -> the 이즈미 x 4월
                                    cell -> list (count = the board's) -> down arrow -> 모든 세이브 -> month chip 전체 -> right arrow
                                    (page 2) -> row chip 전체 (every board row) -> 이즈미 chip -> a read 특훈 뒤 row -> 자세히 (the
                                    detail board above the list) -> back -> 다시 보기 (memory-mode replay, messages clicked through) ->
                                    back on the list -> 한눈에 보기로 -> board -> a row name -> list -> 닫기 -> board -> 닫기 -> home ->
                                    the panel's first companion button -> that companion's list -> 닫기 -> home -> END
  python probe_list.py NightR16.asd 5/20 (마코토 · 모모세 not joined): board rows / list chips without them, the 던전 동행 list masks
                                    every row naming them until read (？？？, no condition, no cast, 자세히 off) -> END
  python probe_list.py TITLE        the title: menubar chart -> board -> the 7월 head -> list (no 이 세이브) -> 달 화면으로 (month view
                                    on 7월) -> back -> 닫기 -> board -> END

Isolation as probe_overview.py (run/ copy, mute, hidden window, input cut off, the user's save folder only read). The board, the
list and the month view wait in KR_C24WaitRaw (frame delegate KR_C24Frame); the detail board in KR_P29WaitRaw (KR_P29Frame).
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ltlib as L

O = HERE / 'candidate'
PACT = None                          # the installed PACT (stage 2 changes the AIN only); set in setup_folder
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterTitleProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat',
               'YoruKR_Chart.dat']
SAVE_TYPE = 2
HOME_SAVE = sys.argv[1] if len(sys.argv) > 1 else 'NightR47.asd'
TITLE = HOME_SAVE == 'TITLE'      # title mode: the game boots normally, the probe asks the menubar request 'chart' on the title   # a save made from the home screen (stack: C_SceneHomebase@Run -> CheckGameSysButtons)
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ('C_SelectDialog@Run', 'C_SelectMessage@Run', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>', 'KR_C24WaitRaw', 'C_SceneTitle@Run',
              'KR_P29WaitRaw')
MODE = 'title' if TITLE else ('may' if HOME_SAVE == 'NightR16.asd' else 'nov')
ROW_Y0, ROW_STEP = 124, 44
CAL_Y = 588

MUTE_JAF = '''
void KR_DiagnosticMute() {
    if (!KiwiSoundEngine.SetMixerMute(0, true) ||
        !config::detail::GetMasterMute()) {
        system.Exit(91);
        return;
    }
}
'''

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
string KR_PRGet(string key) { return SystemService.SystemVariable_Get("YoruKR.LVProbe." + key); }
void KR_PRSet(string key, string value) { SystemService.SystemVariable_Set("YoruKR.LVProbe." + key, value); }
int KR_PRNum(string key) { string v = KR_PRGet(key); if (v == "") return 0; return v.ToInt(); }
int KR_PRB(bool v) { if (v) return 1; return 0; }
string KR_PRMode() { return "@@MODE@@"; }
string KR_PRStage() { return KR_PRRead("claude_probe_stage.txt"); }
void KR_PRStageSet(string s) { TextFile.WriteAll("claude_probe_stage.txt", s); KR_PRLog("STAGE " + s); }
void KR_PRCheck(string what, bool ok) {
    if (ok) { KR_PRLog("OK " + what); return; }
    KR_PRLog("FAIL " + what);
    KR_PRSet("Fails", "%d" % (KR_PRNum("Fails") + 1));
}
void KR_PREndAll() {
    KR_PRLog("FAILS " + ("%d" % KR_PRNum("Fails")));
    KR_PRLog("END");
    system.Exit(0);
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
int KR_PRShown(string act, string n) {
    int p = KR_PRP(act, n);
    if (p <= 0) return -1;
    return KR_PRB(Ｐ＿表示設定取得(p));
}
int KR_PRJoined() {
    int n = 0;
    for (int p = 2; p <= 8; p++) {
        if (KR_T20Joined(p)) n++;
    }
    return n;
}
string KR_PRTxt(int part) {
    if (!PartsEngine.IsExist(part)) return "<none>";
    return Ｐ＿テキスト取得(part, 1);
}
bool KR_PRHas(int part, string s) {
    string t = KR_PRTxt(part);
    return t.Find(s) >= 0;
}
// the screens: the board (stage 2 parts, no list over it), the list (the chart session open on the list root)
bool KR_PRBoard() {
    return KR_XVGet("Open") == "1" && KR_CGet("Open") != "1" && KR_LVGet("Open") != "1" && PartsEngine.IsExist(KR_XVP(0));
}
bool KR_PRList() {
    return KR_LVGet("Open") == "1" && KR_CGet("Open") == "1" && PartsEngine.IsExist(KR_CRoot()) && PartsEngine.IsExist(KR_LVP(1))
        && KR_CActive();
}
int KR_PRBoardRow(int lane) {
    string rs = KR_XVGet("rows");
    int n = rs.ToInt();
    for (int r = 0; r < n; r++) {
        string v = KR_XVGet("row%d" % r);
        if (v.ToInt() == lane) return r;
    }
    return -1;
}
string KR_PRRows() {
    string t = "";
    string rs = KR_XVGet("rows");
    int n = rs.ToInt();
    for (int r = 0; r < n; r++) t = t + KR_XVGet("row%d" % r) + " ";
    return t;
}
// the k-th list cell under (month, lane) in list order, or -1
int KR_PRNth(int month, int lane, int k) {
    int t0 = 0;
    int t1 = 7;
    if (month >= 0) { t0 = month; t1 = month; }
    int c = 0;
    for (int t = t0; t <= t1; t++) {
        for (int i = KR_CTabFirst(t); i < KR_CTabEnd(t); i++) {
            if (!KR_LVMatch(i, lane)) continue;
            if (c == k) return i;
            c++;
        }
    }
    return -1;
}
// the expected count from the board's own counter (KR_XVCount totals of the rows shown)
int KR_PRExpect(int month, int lane) {
    int t0 = 0;
    int t1 = 7;
    if (month >= 0) { t0 = month; t1 = month; }
    int n = 0;
    for (int ln = 0; ln <= 9; ln++) {
        if (ln == 1) continue;
        if (lane >= 0 && ln != lane) continue;
        if (!KR_LVLaneOn(ln)) continue;
        int pk = KR_XVCount(ln, t0, t1, false);
        n = n + pk % 10000;
    }
    return n;
}
bool KR_PRHead(int month, int lane) {
    return KR_PRHas(KR_LVP(2), KR_LVMonthName(month) + " · " + KR_LVLaneName(lane));
}
bool KR_PRFoot(int n) {
    return KR_PRHas(KR_LVP(71), ("%d" % n) + "장면");
}
bool KR_PRSel(int i) {
    return KR_LVGet("selI") == ("%d" % i);
}
string KR_PRRowNames() {
    string t = "";
    for (int s = 0; s < 3; s++) t = t + "[" + KR_PRTxt(KR_LVP(100 + s * 10 + 3)) + "]";
    return t;
}
void KR_PRGo(string stage, int part) {
    KR_PRStageSet(stage);
    KR_PRSet("CFrames", "0");
    AFL_Parts_EndWaitForClick(part);
}

// ---- the home top menu (C_SelectDialog@_Update prefix)
void KR_ProbeDlgTick() {
    string stage = KR_PRStage();
    if (stage.StartsWith("t_")) return;
    int frames = KR_PRNum("DFrames") + 1;
    KR_PRSet("DFrames", "%d" % frames);
    if (frames > 3000) { KR_PRLog("STUCK dialog stage=" + stage); KR_PRShot("lt_stuck.bmp"); system.Exit(5); return; }
    if (frames < 12) return;
    if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") {
        if (stage == "home0" && frames < 600) return;
        KR_PRLog("UNEXPECTED DIALOG stage=" + stage + " frames=" + ("%d" % frames));
        KR_PRShot("lt_unexpected_dialog.bmp");
        system.Exit(7);
        return;
    }
    string act = KR_PRAct();
    if (stage == "home0") {
        if (frames < 40) return;
        KR_PRLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " joined=" + ("%d" % KR_PRJoined()));
        KR_PRCheck("home panel shown with the calendar button", KR_PRRate() == 1 && KR_PRShown(act, "KR_HR_CalBox") == 1);
        KR_PRStageSet("b1");
        KR_PRSet("CFrames", "0");
        KR_T8HomeClick(KR_PRP(act, "KR_HR_CalBox"), 80, @@CAL_Y@@ - KR_HVUp() + 12);
        return;
    }
    if (stage == "home1") {
        if (frames < 40) return;
        KR_PRCheck("closing the board returns to the home menu", KR_PRRate() == 1 && !PartsEngine.IsExist(KR_XVP(0)) && !PartsEngine.IsExist(KR_CRoot()));
        if (KR_PRMode() != "nov") { KR_PREndAll(); return; }
        KR_PRStageSet("p1");
        KR_PRSet("CFrames", "0");
        KR_PRSet("Pick", KR_HVGet("slot0"));
        KR_PRLog("CLICK companion row 1 slot0=" + KR_HVGet("slot0"));
        KR_T8HomeClick(KR_PRP(act, "KR_HR_Box2"), 80, @@ROW_Y0@@ + 20);
        return;
    }
    if (stage == "home2") {
        if (frames < 40) return;
        KR_PRCheck("closing the companion list returns to the home menu", KR_PRRate() == 1 && KR_LVGet("Open") != "1" && !PartsEngine.IsExist(KR_CRoot()));
        KR_PRShot("lt_home_after.bmp");
        KR_PREndAll();
        return;
    }
    KR_PRLog("HOME in stage " + stage);
    KR_PRShot("lt_home_unexpected.bmp");
    system.Exit(6);
}

// ---- the board, the list and the month view share the frame delegate KR_C24Frame (prefix)
void KR_ProbeNov(string stage, int f) {
    if (stage == "b1") {
        if (f == 30) {
            KR_PRCheck("the calendar opens on the board", KR_PRBoard());
            KR_PRLog("ROWS " + KR_PRRows());
            string rs = KR_XVGet("rows");
            int n = rs.ToInt();
            bool boxes = n > 0;
            for (int r = 0; r < n; r++) {
                if (!PartsEngine.IsExist(KR_XVP(100 + r * 40 + 35))) boxes = false;
            }
            KR_PRCheck("every board row has its name button", boxes);
            KR_PRCheck("the board's hint names the list", KR_PRHas(KR_XVP(530), "장면 목록"));
            KR_PRCheck("home: 회상 · 그 밖 are not covered", !PartsEngine.IsExist(KR_XVP(528)) && !PartsEngine.IsExist(KR_XVP(529)));
            KR_PRShot("lt_board.bmp");
        }
        if (f == 32) {
            int row = KR_PRBoardRow(2);
            KR_PRLog("CLICK board cell 이즈미 x 4월 row=" + ("%d" % row));
            KR_PRGo("l1", KR_XVP(100 + row * 40 + 2));
        }
        return;
    }
    if (stage == "l1") {
        if (f == 30) {
            int n = KR_PRExpect(0, 2);
            KR_PRLog("LIST n=" + ("%d" % n) + " lvcount=" + ("%d" % KR_LVCount(0, 2)) + " foot=" + KR_PRTxt(KR_LVP(71)) + " rows=" + KR_PRRowNames());
            KR_PRCheck("a board cell opens the list on that month x row", KR_PRList() && KR_PRHead(0, 2));
            KR_PRCheck("the list count = the board's count for that cell", KR_LVCount(0, 2) == n && KR_PRFoot(n));
            KR_PRCheck("the first row is selected and previewed", KR_PRSel(KR_PRNth(0, 2, 0)) && PartsEngine.IsExist(KR_LVP(310)));
            KR_PRCheck("the board parts are released under the list", !PartsEngine.IsExist(KR_XVP(0)));
            // a row read in another save but not seen in this one keeps its summary and cast closed at home
            int other = -1;
            for (int k = 0; k < 14; k++) {
                int i = KR_PRNth(0, 2, k);
                if (i < 0) break;
                int no = KR_CCellEv(i);
                if (other < 0 && KR_CGlobal(no) == 1 && !N_ScenarioRegister::IsRegisteredEvent(KR_T9Fn(no))) other = k;
            }
            KR_PRLog("READ ELSEWHERE row=" + ("%d" % other) + " text=" + KR_PRTxt(KR_LVP(100 + other * 10 + 8)));
            if (other >= 0) KR_PRCheck("home: a row read only in another save shows no summary and no faces",
                                       KR_PRHas(KR_LVP(100 + other * 10 + 8), "본 뒤에") && !PartsEngine.IsExist(KR_LVP(100 + other * 10 + 4)));
            KR_PRShot("lt_list_apr_izumi.bmp");
        }
        if (f == 32) KR_PRGo("l2", 4);
        return;
    }
    if (stage == "l2") {
        if (f == 30) {
            KR_PRCheck("down arrow selects the next row", KR_PRSel(KR_PRNth(0, 2, 1)));
            KR_PRShot("lt_list_down.bmp");
        }
        if (f == 32) KR_PRGo("l3", KR_LVP(5));
        return;
    }
    if (stage == "l3") {
        if (f == 30) {
            KR_PRCheck("모든 세이브: the legend switches to read / unread", KR_PRHas(KR_LVP(70), "안 읽음") && PartsEngine.IsExist(KR_LVP(3)));
            KR_PRShot("lt_list_allsaves.bmp");
        }
        if (f == 32) KR_PRGo("l4", KR_LVP(10));
        return;
    }
    if (stage == "l4") {
        if (f == 30) {
            int n = KR_PRExpect(-1, 2);
            KR_PRCheck("the 전체 month chip: every month of the row", KR_PRHead(-1, 2) && KR_PRFoot(n) && KR_PRSel(KR_PRNth(-1, 2, 0)));
            KR_PRSet("N4", "%d" % n);
            KR_PRShot("lt_list_izumi_all.bmp");
        }
        if (f == 32) KR_PRGo("l5", 2);
        return;
    }
    if (stage == "l5") {
        if (f == 30) {
            int n = KR_PRNum("N4");
            if (n > 14) KR_PRCheck("right arrow: the next page", KR_PRSel(KR_PRNth(-1, 2, 14)) && KR_PRHas(KR_LVP(71), "2 / "));
            else KR_PRLog("SKIP page check n=" + ("%d" % n));
            KR_PRShot("lt_list_page2.bmp");
        }
        if (f == 32) KR_PRGo("l6", KR_LVP(30));
        return;
    }
    if (stage == "l6") {
        if (f == 30) {
            int n = KR_PRExpect(-1, -1);
            KR_PRLog("ALL n=" + ("%d" % n) + " chips=" + KR_LVGet("chips"));
            KR_PRCheck("the 전체 row chip: every board row (= the board's whole count less 회상 · 그 밖)", KR_PRHead(-1, -1) && KR_PRFoot(n));
            KR_PRCheck("row chips: 전체, 본편, the joined companions, 던전 동행", KR_LVGet("chips") == ("%d" % (3 + KR_PRJoined())));
            KR_PRShot("lt_list_everything.bmp");
        }
        if (f == 32) {
            string cs = KR_LVGet("chips");
            int nc = cs.ToInt();
            int k = -1;
            for (int c = 0; c < nc; c++) {
                if (KR_LVGet("chip%d" % c) == "2") k = c;
            }
            KR_PRGo("l7", KR_LVP(30 + k * 2));
        }
        return;
    }
    if (stage == "l7") {
        if (f == 30) {
            KR_PRCheck("the 이즈미 chip", KR_PRHead(-1, 2));
            int tk = -1;
            for (int k = 0; k < 14; k++) {
                int i = KR_PRNth(-1, 2, k);
                if (i < 0) break;
                int no = KR_CCellEv(i);
                string nm = KR_CCellName(i);
                if (tk < 0 && KR_LVReveal(no, 2) && KR_CCanPlay(no) && nm.Find("특훈 뒤") >= 0) tk = k;
            }
            KR_PRSet("Tk", "%d" % tk);
            if (tk >= 0) KR_PRSet("Ti", "%d" % KR_PRNth(-1, 2, tk));
            KR_PRLog("TARGET k=" + ("%d" % tk) + " i=" + KR_PRGet("Ti"));
            KR_PRCheck("a read, playable 특훈 뒤 row on the first page", tk >= 0);
        }
        if (f == 32) {
            int tk2 = KR_PRNum("Tk");
            if (tk2 < 0) { KR_PREndAll(); return; }
            KR_PRGo("l8", KR_LVP(100 + tk2 * 10));
        }
        return;
    }
    if (stage == "l8") {
        if (f == 30) {
            int ti = KR_PRNum("Ti");
            KR_PRCheck("a row click selects it", KR_PRSel(ti));
            KR_PRCheck("the preview: faces, title, summary, both buttons", PartsEngine.IsExist(KR_LVP(301)) && PartsEngine.IsExist(KR_LVP(310))
                       && PartsEngine.IsExist(KR_LVP(314)) && PartsEngine.IsExist(KR_LVP(316)) && PartsEngine.IsExist(KR_LVP(318)));
            KR_PRLog("PREVIEW title=" + KR_PRTxt(KR_LVP(310)));
            KR_PRShot("lt_preview.bmp");
        }
        if (f == 32) KR_PRGo("d1", KR_LVP(318));
        return;
    }
    if (stage == "l9") {
        if (f == 30) {
            KR_PRCheck("closing the detail board returns to the list (same row)", KR_PRList() && KR_PRSel(KR_PRNum("Ti")) && Ｐ＿表示設定取得(KR_CRoot()));
        }
        if (f == 32) {
            KR_PRSet("MsgsBefore", "%d" % KR_PRNum("Msgs"));
            KR_PRLog("CLICK 다시 보기");
            KR_PRGo("rp", KR_LVP(316));
        }
        return;
    }
    if (stage == "rp") {
        if (f == 30) {
            KR_PRLog("AFTER REPLAY msgs=" + KR_PRGet("Msgs") + " before=" + KR_PRGet("MsgsBefore") + " play=" + KR_CGet("Play") + " unwind=" + KR_T9Get("Unwind"));
            KR_PRCheck("다시 보기 played the scene and came back to the list (same filter, same row)",
                       KR_PRNum("Msgs") > KR_PRNum("MsgsBefore") && KR_PRList() && KR_PRHead(-1, 2) && KR_PRSel(KR_PRNum("Ti")) && KR_CGet("Play") == "");
            KR_PRShot("lt_after_replay.bmp");
        }
        if (f == 32) KR_PRGo("b2", KR_LVP(52));
        return;
    }
    if (stage == "b2") {
        if (f == 30) {
            KR_PRCheck("한눈에 보기로 returns to the board", KR_PRBoard());
            KR_PRShot("lt_board_back.bmp");
        }
        if (f == 32) {
            string rv = KR_XVGet("row2");
            KR_PRSet("L10", rv);
            KR_PRLog("CLICK board row name 2 lane=" + rv);
            KR_PRGo("l10", KR_XVP(100 + 2 * 40 + 35));
        }
        return;
    }
    if (stage == "l10") {
        if (f == 30) {
            int lane = KR_PRNum("L10");
            KR_PRCheck("a row name opens that row in every month", KR_PRList() && KR_PRHead(-1, lane) && KR_PRFoot(KR_PRExpect(-1, lane)));
            KR_PRCheck("home: 달 화면으로 is on", KR_PRHas(KR_LVP(55), KR_CWhite()));
            KR_PRShot("lt_list_byname.bmp");
        }
        if (f == 32) KR_PRGo("lm", KR_LVP(54));
        return;
    }
    if (stage == "lm") {
        if (f == 30) {
            KR_PRLog("MONTH head=" + KR_PRTxt(KR_CPart(1)));
            KR_PRCheck("home: 달 화면으로 opens the month view (list parts released)",
                       KR_CGet("Open") == "1" && KR_LVGet("Open") != "1" && PartsEngine.IsExist(KR_CPart(1)) && !PartsEngine.IsExist(KR_LVP(1)));
            KR_PRShot("lt_home_month.bmp");
        }
        if (f == 32) KR_PRGo("l11", 0);
        return;
    }
    if (stage == "l11") {
        if (f == 30) KR_PRCheck("home: closing the month view returns to the list (same filter)", KR_PRList() && KR_PRHead(-1, KR_PRNum("L10")));
        if (f == 32) KR_PRGo("b3", KR_LVP(7));
        return;
    }
    if (stage == "b3") {
        if (f == 30) KR_PRCheck("닫기 on the list returns to the board", KR_PRBoard());
        if (f == 32) {
            KR_PRStageSet("home1");
            KR_PRSet("DFrames", "0");
            AFL_Parts_EndWaitForClick(KR_XVP(7));
        }
        return;
    }
    if (stage == "p1") {
        if (f == 30) {
            int p = KR_PRNum("Pick");
            KR_PRCheck("the home panel's companion button opens that companion's list (no board under it)",
                       KR_PRList() && KR_PRHead(-1, p) && KR_XVGet("Open") != "1" && KR_PRFoot(KR_PRExpect(-1, p)));
            KR_PRShot("lt_person.bmp");
        }
        if (f == 32) {
            KR_PRStageSet("home2");
            KR_PRSet("DFrames", "0");
            AFL_Parts_EndWaitForClick(KR_LVP(7));
        }
        return;
    }
    KR_PRLog("CHART TICK in stage " + stage);
    KR_PRShot("lt_unexpected.bmp");
    system.Exit(6);
}
// a row names a companion who has not joined (5/20: 마코토, 모모세)
bool KR_PRNamesHidden(int i) {
    string t = KR_CCellName(i) + " " + KR_CCellCond(i);
    return t.Find("마코토") >= 0 || t.Find("모모세") >= 0;
}
void KR_ProbeMay(string stage, int f) {
    if (stage == "b1") {
        if (f == 30) {
            KR_PRCheck("5/20: the board", KR_PRBoard());
            KR_PRLog("ROWS " + KR_PRRows());
            KR_PRCheck("5/20: no 마코토 / 모모세 row", KR_PRBoardRow(5) < 0 && KR_PRBoardRow(8) < 0);
            KR_PRShot("lt_may_board.bmp");
        }
        if (f == 32) KR_PRGo("m1", KR_XVP(100 + KR_PRBoardRow(9) * 40 + 35));
        return;
    }
    if (stage == "m1") {
        if (f == 30) {
            int n = KR_PRExpect(-1, 9);
            KR_PRCheck("5/20: the 던전 동행 name opens its list", KR_PRList() && KR_PRHead(-1, 9) && KR_PRFoot(n));
            string cs = KR_LVGet("chips");
            int nc = cs.ToInt();
            bool chipsOK = true;
            for (int c = 0; c < nc; c++) {
                string v = KR_LVGet("chip%d" % c);
                if (v == "5" || v == "8") chipsOK = false;
            }
            KR_PRCheck("5/20: no 마코토 / 모모세 chip", chipsOK);
            // every row naming them is masked until read; no other row is
            int named = 0;
            int masked = 0;
            int first = -1;
            bool same = true;
            for (int k = 0; k < n; k++) {
                int i = KR_PRNth(-1, 9, k);
                bool nm = KR_PRNamesHidden(i);
                if (nm != KR_LVHidden(i)) same = false;
                if (nm) named++;
                if (nm && !KR_LVReveal(KR_CCellEv(i), 2)) {
                    masked++;
                    if (first < 0) first = k;
                }
            }
            KR_PRLog("MAY n=" + ("%d" % n) + " named=" + ("%d" % named) + " masked=" + ("%d" % masked) + " first=" + ("%d" % first));
            KR_PRCheck("5/20: KR_LVHidden marks exactly the rows naming 마코토 / 모모세", same);
            KR_PRSet("First", "%d" % first);
            KR_PRSet("Pages", "0");
            KR_PRShot("lt_may_dungeon.bmp");
        }
        if (f == 32) {
            KR_PRStageSet("m2");
            KR_PRSet("CFrames", "0");
        }
        return;
    }
    if (stage == "m2") {
        int first2 = KR_PRNum("First");
        if (first2 < 0) {
            KR_PRLog("SKIP: no masked row in this save");
            KR_PRGo("b2m", KR_LVP(7));
            return;
        }
        if (f == 5) {
            int pg = KR_PRNum("Pages");
            if (pg < first2 / 14) {
                KR_PRSet("Pages", "%d" % (pg + 1));
                KR_PRSet("CFrames", "0");
                AFL_Parts_EndWaitForClick(2);
                return;
            }
            KR_PRStageSet("m3");
            KR_PRSet("CFrames", "0");
        }
        return;
    }
    if (stage == "m3") {
        int first3 = KR_PRNum("First");
        int s = first3 - (first3 / 14) * 14;
        if (f == 30) {
            bool clean = true;
            for (int r = 0; r < 14; r++) {
                string t = KR_PRTxt(KR_LVP(100 + r * 10 + 3));
                if (t.Find("마코토") >= 0 || t.Find("모모세") >= 0) clean = false;
            }
            KR_PRLog("PAGE names " + KR_PRTxt(KR_LVP(100 + s * 10 + 3)));
            KR_PRCheck("5/20: the masked row shows ？？？ and no drawn row names 마코토 / 모모세", KR_PRHas(KR_LVP(100 + s * 10 + 3), "？？？") && clean);
        }
        if (f == 32) KR_PRGo("m4", KR_LVP(100 + s * 10));
        return;
    }
    if (stage == "m4") {
        if (f == 30) {
            string t4 = KR_PRTxt(KR_LVP(312));
            KR_PRCheck("5/20: the masked row's preview: ？？？, no condition, no cast, 자세히 off",
                       KR_PRHas(KR_LVP(310), "？？？") && t4.Find("마코토") < 0 && t4.Find("모모세") < 0 && !PartsEngine.IsExist(KR_LVP(301)));
            KR_PRShot("lt_may_masked.bmp");
        }
        if (f == 32) KR_PRGo("b2m", KR_LVP(7));
        return;
    }
    if (stage == "b2m") {
        if (f == 30) KR_PRCheck("5/20: 닫기 returns to the board", KR_PRBoard());
        if (f == 32) {
            KR_PRStageSet("home1");
            KR_PRSet("DFrames", "0");
            AFL_Parts_EndWaitForClick(KR_XVP(7));
        }
        return;
    }
    KR_PRLog("CHART TICK in stage " + stage);
    KR_PRShot("lt_unexpected.bmp");
    system.Exit(6);
}
bool KR_PRRowsStartOK() {
    string rs = KR_XVGet("rows");
    int n = rs.ToInt();
    if (KR_XVGet("row0") != "0") return false;
    if (KR_XVGet("row%d" % (n - 1)) != "9") return false;
    int k = 1;
    for (int p = 2; p <= 8; p++) {
        if (KR_T20JoinDay(p) > 0) continue;
        string v = KR_XVGet("row%d" % k);
        if (v.ToInt() != p) return false;
        k++;
    }
    return k == n - 1;
}
int KR_PRStartCount() {
    int n = 0;
    for (int p = 2; p <= 8; p++) {
        if (KR_T20JoinDay(p) <= 0) n++;
    }
    return n;
}
// every drawn row closed: no faces, the title note
bool KR_PRRowsClosed() {
    for (int s = 0; s < 14; s++) {
        if (!PartsEngine.IsExist(KR_LVP(100 + s * 10))) continue;
        if (PartsEngine.IsExist(KR_LVP(100 + s * 10 + 4))) return false;
        if (!KR_PRHas(KR_LVP(100 + s * 10 + 8), "타이틀에서는")) return false;
    }
    return true;
}
// the cell names a companion who is not there from the start
bool KR_PRNamesLater(int i) {
    string t = KR_CCellName(i) + " " + KR_CCellCond(i);
    for (int p = 2; p <= 8; p++) {
        if (KR_T20JoinDay(p) <= 0) continue;
        if (t.Find(KR_XVName(p)) >= 0) return true;
    }
    return false;
}
void KR_ProbeTitle(string stage, int f) {
    if (stage == "t_b") {
        if (f == 30) {
            KR_PRLog("ROWS " + KR_PRRows() + " start=" + ("%d" % KR_PRStartCount()));
            KR_PRCheck("title: board rows = 본편, the companions present from the start, 던전 동행", KR_PRBoard() && !PartsEngine.IsExist(KR_XVP(3)) && KR_PRRowsStartOK());
            KR_PRCheck("title: 회상 · 그 밖 covered and the hint says why", PartsEngine.IsExist(KR_XVP(528)) && PartsEngine.IsExist(KR_XVP(529)) && KR_PRHas(KR_XVP(531), "타이틀에서는"));
            KR_PRShot("lt_title_board.bmp");
        }
        if (f == 32) KR_PRGo("t_l", KR_XVP(23));
        return;
    }
    if (stage == "t_l") {
        if (f == 30) {
            int n = KR_PRExpect(3, -1);
            KR_PRLog("TITLE LIST n=" + ("%d" % n) + " chips=" + KR_LVGet("chips") + " foot=" + KR_PRTxt(KR_LVP(71)) + " note=" + KR_PRTxt(KR_LVP(108)));
            KR_PRCheck("title: the 7월 list with chips 전체 · 본편 · start companions · 던전 동행",
                       KR_PRList() && KR_PRHead(3, -1) && KR_PRFoot(n) && KR_LVGet("chips") == ("%d" % (3 + KR_PRStartCount())));
            KR_PRCheck("title: every row closed (no faces, the title note)", KR_PRRowsClosed());
            KR_PRCheck("title: the preview closed (no faces, title notes, 다시 보기 · 자세히 off)",
                       !PartsEngine.IsExist(KR_LVP(301)) && KR_PRHas(KR_LVP(309), "타이틀에서는") && KR_PRHas(KR_LVP(314), "타이틀에서는")
                       && KR_PRHas(KR_LVP(317), KR_LVDimC()) && KR_PRHas(KR_LVP(319), KR_LVDimC()));
            KR_PRCheck("title: 달 화면으로 drawn off", KR_PRHas(KR_LVP(55), KR_LVDimC()));
            KR_PRShot("lt_title_list.bmp");
        }
        if (f == 32) KR_PRGo("t_l2", KR_LVP(54));
        return;
    }
    if (stage == "t_l2") {
        if (f == 30) KR_PRCheck("title: 달 화면으로 opens nothing (the list stays)", KR_PRList() && KR_PRHead(3, -1) && !PartsEngine.IsExist(KR_CPart(1)));
        if (f == 32) KR_PRGo("t_b2", KR_LVP(7));
        return;
    }
    if (stage == "t_d") {
        if (f == 30) {
            int n = KR_PRExpect(-1, 9);
            bool same = true;
            int named = 0;
            for (int k = 0; k < n; k++) {
                int i = KR_PRNth(-1, 9, k);
                bool nm = KR_PRNamesLater(i);
                if (nm != KR_LVHidden(i)) same = false;
                if (nm) named++;
            }
            bool clean = true;
            for (int r = 0; r < 14; r++) {
                string t = KR_PRTxt(KR_LVP(100 + r * 10 + 3));
                for (int p = 2; p <= 8; p++) {
                    if (KR_T20JoinDay(p) > 0 && t.Find(KR_XVName(p)) >= 0) clean = false;
                }
            }
            KR_PRLog("TITLE DUNGEON n=" + ("%d" % n) + " naming later companions=" + ("%d" % named));
            KR_PRCheck("title: 던전 동행 rows naming later companions show ？？？ (none drawn by name)", KR_PRHead(-1, 9) && named > 0 && same && clean);
            KR_PRShot("lt_title_dungeon.bmp");
        }
        if (f == 32) KR_PRGo("t_b4", KR_LVP(7));
        return;
    }
    if (stage == "t_b2") {
        if (f == 30) KR_PRCheck("title: 닫기 returns to the board", KR_PRBoard());
        if (f == 32) KR_PRGo("t_d", KR_XVP(100 + KR_PRBoardRow(9) * 40 + 35));
        return;
    }
    if (stage == "t_b4") {
        if (f == 30) KR_PRCheck("title: 닫기 on the 던전 동행 list returns to the board", KR_PRBoard());
        if (f == 32) KR_PRGo("t_b3", KR_XVP(520));
        return;
    }
    if (stage == "t_b3") {
        if (f == 30) {
            KR_PRCheck("title: 회상 opens nothing (the board stays)", KR_PRBoard() && !PartsEngine.IsExist(KR_CPart(1)) && KR_XVGet("Jump") == "");
            KR_PRShot("lt_title_board_back.bmp");
            KR_PREndAll();
        }
        return;
    }
    KR_PRLog("CHART TICK in stage " + stage);
    KR_PRShot("lt_unexpected.bmp");
    system.Exit(6);
}
void KR_ProbeChartTick() {
    string stage = KR_PRStage();
    int f = KR_PRNum("CFrames") + 1;
    KR_PRSet("CFrames", "%d" % f);
    if (f > 3000) { KR_PRLog("CHART STUCK stage=" + stage); KR_PRShot("lt_stuck.bmp"); system.Exit(5); }
    if (KR_PRMode() == "title") KR_ProbeTitle(stage, f);
    else if (KR_PRMode() == "may") KR_ProbeMay(stage, f);
    else KR_ProbeNov(stage, f);
}
// ---- the detail board (KR_P29Frame prefix)
void KR_ProbeDetailTick() {
    string stage = KR_PRStage();
    int f = KR_PRNum("PFrames") + 1;
    KR_PRSet("PFrames", "%d" % f);
    if (f > 3000) { KR_PRLog("DETAIL STUCK stage=" + stage); KR_PRShot("lt_stuck.bmp"); system.Exit(5); }
    if (stage != "d1") {
        KR_PRLog("DETAIL in stage " + stage);
        KR_PRShot("lt_unexpected.bmp");
        system.Exit(6);
        return;
    }
    if (f == 30) {
        KR_PRCheck("자세히 opens the detail board above the list (chart branch, list hidden)",
                   KR_CActive() && PartsEngine.IsExist(KR_P29Part(0)) && !Ｐ＿表示設定取得(KR_CRoot()));
        KR_PRShot("lt_detail.bmp");
    }
    if (f == 32) {
        KR_PRStageSet("l9");
        KR_PRSet("CFrames", "0");
        AFL_Parts_EndWaitForClick(0);
    }
}
void KR_ProbeReq(string cmd) {
    if (!FileOperation.ExistFolder(KR_MFolder())) FileOperation.CreateFolder(KR_MFolder());
    TextFile.WriteAll(KR_MFile("request.txt"), cmd + "\n1\n2026-10-18 21:00:00\n");
    KR_PRLog("REQUEST " + cmd);
}
// the title frame (prefix of KR_CTitleTick): once the title is up, ask for the chart like the menubar does
void KR_ProbeTitleTick() {
    if (KR_PRStage() != "t_req") return;
    int f = KR_PRNum("TFrames") + 1;
    KR_PRSet("TFrames", "%d" % f);
    if (f == 60) {
        KR_PRShot("lt_title.bmp");
        KR_PRStageSet("t_b");
        KR_PRSet("CFrames", "0");
        KR_ProbeReq("chart");
    }
    if (f > 6000) { KR_PRLog("TITLE STUCK"); system.Exit(5); }
}
int KR_ProbeMainTitle() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_PRLog("SAVEFOLDER " + system.GetSaveFolderName());
    KR_PRLog("TITLE MODE");
    return main();
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
    KR_PRShot("lt_wait.bmp");
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
    string save = KR_PRRead("claude_probe_save.txt");
    KR_PRLog("RESUME " + save + " stage=" + KR_PRStage() + " mode=" + KR_PRMode());
    if (save == "") { system.Exit(3); return 3; }
    system.ResumeLoad("@@KEY@@", save);
    system.Exit(2);
    return 2;
}
'''


def build_probe(key, work):
    src = O / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + (PROBE_JAF.replace('@@KEY@@', key).replace('@@CAL_Y@@', str(CAL_Y))
                             .replace('@@ROW_Y0@@', str(ROW_Y0)).replace('@@ROW_STEP@@', str(ROW_STEP)).replace('@@MODE@@', MODE))
    assert '@@' not in jaf
    jaf = L.jaf_literal_encode(jaf)
    work.mkdir(parents=True, exist_ok=True)
    (work / 'probe.jaf').write_text(jaf, 'utf8')
    decl = work / 'probe_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'probe.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'probe_declared_meta.json', decl)
    dm = L.read_meta(work / 'probe_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    patch += [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]
    om = L.fid_of(m, 'C_SceneTrainingView@GetOnmouseChara')
    patch.append(f"FUNC {om}\n\tPUSH 0\n\tRETURN\nENDFUNC C_SceneTrainingView@GetOnmouseChara\n")
    for g in added:
        path = work / f"probe_{g['index']}.jam"
        L.cmd('ain', 'dump', '--function', g['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), g['name']))
    for owner, tick in (('C_SelectDialog@_Update', 'KR_ProbeDlgTick'), ('KR_C24Frame', 'KR_ProbeChartTick'), ('KR_CTitleTick', 'KR_ProbeTitleTick'),
                        ('KR_P29Frame', 'KR_ProbeDetailTick')):
        fid = L.fid_of(m, owner)
        path = work / f'original_{fid}.jam'
        L.cmd('ain', 'dump', '--function', owner, '-o', path, src)
        patch.append(L.begin(L.clean(path.read_text('utf8'), owner), f'\tCALLFUNC {tick}\n'))
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    RUN.mkdir(parents=True, exist_ok=True)
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_ProbeMainTitle' if TITLE else 'KR_ProbeMain'])
    raw_code = L.WORK / 'build' / 'candidate_raw_code.jam'
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    vers = L.versions(raw_code)
    waits = []
    for g in m['functions']:
        name = L.raw_symbol(m, g['index'])
        for v in [v for v in vers.get(g['index'], []) if v['start'] == g['address']]:
            for ad, op in v['ops']:
                if op != f'CALLFUNC 0x{wait:x}':
                    continue
                assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, wait)
                if name in LIVE_WAITS:
                    waits.append((name, 'live'))
                    continue
                target = ids['KR_ProbeMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_ProbeWaitExit']
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, target)
                waits.append((name, 'message click-through' if target == ids['KR_ProbeMsgWait'] else 'exit'))
    live = sorted(n for n, k in waits if k == 'live')
    assert live == sorted(LIVE_WAITS), live
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(waits=len(waits), live_waits=live, probe_sha256=L.sha(out))


def setup_folder():
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
    global PACT
    PACT = rt / 'NightRemasterPact.afa'
    for name in ['NightRemasterPact.afa', BOOT + 'Pact.afa']:
        shutil.copy2(PACT, RUN / name)
    for name in ['NightRemasterEX.ex', BOOT + 'EX.ex']:
        shutil.copy2(rt / 'NightRemasterEX.ex', RUN / name)
    for n in ['NightRemasterCG.afa', 'NightRemasterFont.fnl', 'NightRemasterSound.afa', 'NightRemasterVoice.afa']:
        for name in [n, n.replace('NightRemaster', BOOT, 1)]:
            t = RUN / name
            if not t.exists():
                os.link(rt / n, t)
            assert os.path.samefile(t, rt / n)
    if not (RUN / 'Movie').exists():
        (RUN / 'Movie').mkdir()
        for f in (rt / 'Movie').iterdir():
            os.link(f, RUN / 'Movie' / f.name)
    ini = (rt / 'AliceStart.ini').read_bytes()
    ini = re.sub(rb'BootName\t= "NightRemaster"', ('BootName\t= "' + BOOT + '"').encode(), ini)
    assert BOOT.encode() in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    return rt


def set_savefolder(savename):
    ini = (RUN / 'AliceStart.ini').read_bytes()
    folder = b'SaveFolder\t= "' + savename.encode('cp932') + b'"'
    ini = re.sub(rb'SaveFolder\t= "[^"]*"', lambda z: folder, ini)
    assert folder in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    (RUN / 'InstallInfo').mkdir(exist_ok=True)
    (RUN / 'InstallInfo' / 'SaveFolderSetting.ini').write_bytes(b'SFSF' + struct.pack('<ii', 0, SAVE_TYPE))
    for n in ['claude_probe.txt', 'claude_probe_stage.txt', 'claude_probe_save.txt']:
        if (RUN / n).exists():
            (RUN / n).unlink()
    for b in RUN.glob('lt_*.bmp'):
        b.unlink()


# ---- the 09-24 probe launcher (as probe_autonav.py): hidden window, MessageBoxA and the VM error handler break-pointed
K = C.WinDLL('kernel32', use_last_error=True)
K.WaitForDebugEvent.argtypes = [C.c_void_p, W.DWORD]
K.ContinueDebugEvent.argtypes = [W.DWORD, W.DWORD, W.DWORD]
K.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
K.WriteProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
K.VirtualProtectEx.argtypes = [W.HANDLE, C.c_void_p, C.c_size_t, W.DWORD, C.POINTER(W.DWORD)]
K.OpenThread.argtypes = [W.DWORD, W.BOOL, W.DWORD]
K.OpenThread.restype = W.HANDLE
K.Wow64GetThreadContext.argtypes = [W.HANDLE, C.c_void_p]
K.CloseHandle.argtypes = [W.HANDLE]
K.TerminateProcess.argtypes = [W.HANDLE, W.UINT]


class Context(C.Structure):
    _fields_ = ([(n, W.DWORD) for n in 'ContextFlags Dr0 Dr1 Dr2 Dr3 Dr6 Dr7'.split()] + [('FloatSave', C.c_byte * 112)]
                + [(n, W.DWORD) for n in 'SegGs SegFs SegEs SegDs Edi Esi Ebx Edx Ecx Eax Ebp Eip SegCs EFlags Esp SegSs'.split()]
                + [('ExtendedRegisters', C.c_byte * 512)])


def launch(timeout=900):
    import pefile, win32process
    exe = RUN / 'NightRemaster.exe'
    data = exe.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXE_SHA
    pe = pefile.PE(data=data)
    imp = next(x.address for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name == b'MessageBoxA')
    needle = b'\xff\x15' + struct.pack('<I', imp)
    sites = [0x6696f0 - 0x400000]
    off = 0
    while (off := data.find(needle, off)) >= 0:
        sites.append(pe.get_rva_from_offset(off))
        off += 1
    startup = win32process.STARTUPINFO()
    startup.dwFlags = 1
    startup.wShowWindow = 0
    env = L.env()
    hp, ht, pid, tid = win32process.CreateProcess(str(exe), None, None, None, False, 2, env, str(RUN), startup)
    handle = int(hp)
    result = {'pid': pid, 'ain_sha256': L.sha(RUN / 'NightRemaster.ain'), 'events': []}

    def read(addr, n):
        buf = C.create_string_buffer(n)
        got = C.c_size_t()
        if not K.ReadProcessMemory(handle, addr, buf, n, C.byref(got)):
            raise C.WinError(C.get_last_error())
        return buf.raw[:got.value]

    def cstr(addr):
        out = bytearray()
        for n in range(8192):
            v = read(addr + n, 1)
            if v == b'\0':
                return bytes(out)
            out += v
        return bytes(out)
    try:
        bp = {}
        base = 0
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            event = C.create_string_buffer(200)
            if not K.WaitForDebugEvent(event, 1000):
                continue
            raw = event.raw
            code, epid, etid = struct.unpack_from('<III', raw)
            status = 0x10002
            if code == 3:
                base = struct.unpack_from('<Q', raw, 40)[0]
                for rva in sites:
                    addr = base + rva
                    bp[addr] = read(addr, 1)
                    old = W.DWORD()
                    num = C.c_size_t()
                    if not K.VirtualProtectEx(handle, addr, 1, 0x40, C.byref(old)):
                        raise C.WinError(C.get_last_error())
                    if not K.WriteProcessMemory(handle, addr, b'\xcc', 1, C.byref(num)):
                        raise C.WinError(C.get_last_error())
                    tmp = W.DWORD()
                    K.VirtualProtectEx(handle, addr, 1, old.value, C.byref(tmp))
            elif code == 1:
                exc = struct.unpack_from('<I', raw, 16)[0]
                addr = struct.unpack_from('<Q', raw, 32)[0]
                if exc in (0x80000003, 0x4000001f) and addr in bp:
                    thread = K.OpenThread(0x58, False, etid)
                    try:
                        ctx = Context()
                        ctx.ContextFlags = 0x10007
                        if not K.Wow64GetThreadContext(thread, C.byref(ctx)):
                            raise C.WinError(C.get_last_error())
                        if addr == base + 0x6696f0 - 0x400000:
                            ret, op, msg = struct.unpack('<III', read(ctx.Esp, 12))
                            buf = read(msg, 24)
                            length, capacity = struct.unpack_from('<II', buf, 16)
                            ptr = struct.unpack_from('<I', buf)[0] if capacity >= 16 else msg
                            result['vm_error'] = {'command': cstr(op).decode('cp932', 'replace'), 'message': read(ptr, min(length, 8192)).decode('cp932', 'replace')}
                        else:
                            args = struct.unpack('<IIII', read(ctx.Esp, 16))
                            t = cstr(args[1])
                            result['message'] = {'cp932': t.decode('cp932', 'replace'), 'cp949': t.decode('cp949', 'replace'), 'hex': t.hex()}
                    finally:
                        K.CloseHandle(thread)
                    K.TerminateProcess(handle, 99)
                    K.ContinueDebugEvent(epid, etid, status)
                    break
                if exc not in (0x80000003, 0x4000001f):
                    result['events'].append({'exception': hex(exc), 'address': hex(addr)})
                    status = 0x80010001
            elif code == 5:
                result['exit_code'] = struct.unpack_from('<I', raw, 16)[0]
                K.ContinueDebugEvent(epid, etid, status)
                break
            K.ContinueDebugEvent(epid, etid, status)
        else:
            result['timeout'] = True
    finally:
        K.TerminateProcess(handle, 99)
    return result


def user_state():
    return {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}


def collect_shots():
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(RUN.glob('lt_*.bmp')):
        png = dest / (b.stem + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    return shots


def run():
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    before = user_state()
    setup_folder()
    key = 'title' if TITLE else L.save_records(L.SAVES / HOME_SAVE)['key']
    info = build_probe(key, PROBE / 'work')
    savename = f'SaveData_TitleProbe_{stamp}'
    savedir = RUN / savename
    set_savefolder(savename)
    savedir.mkdir(parents=True)
    for n in COPY_GLOBAL:
        if (L.SAVES / n).exists():
            shutil.copy2(L.SAVES / n, savedir / n)
    if not TITLE:
        shutil.copy2(L.SAVES / HOME_SAVE, savedir / HOME_SAVE)
    (RUN / 'claude_probe_save.txt').write_bytes(HOME_SAVE.encode('cp932'))
    (RUN / 'claude_probe_stage.txt').write_bytes(b't_req' if TITLE else b'home0')
    for f in (RUN / 'KRMenu').glob('*') if (RUN / 'KRMenu').exists() else []:
        f.unlink()
    t0 = time.time()
    result = launch(timeout=900)
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result['shots'] = collect_shots()
    result.update(mode=MODE, save=HOME_SAVE, save_folder=str(savedir), probe=info, candidate_ain=L.sha(O / 'NightRemaster.ain'), candidate_pact=L.sha(PACT))
    result['fails'] = [x for x in result['log'] if x.startswith('FAIL ')]
    result['oks'] = len([x for x in result['log'] if x.startswith('OK ')])
    result['ended'] = 'END' in result['log']
    result['user_save_folder_unchanged'] = before == user_state()
    L.EVID.mkdir(parents=True, exist_ok=True)
    L.writej(L.EVID / f'probe_title_{stamp}.json', result)
    L.writej(L.EVID / ('probe_title.json' if HOME_SAVE == 'NightR47.asd' else (f'probe_title_{HOME_SAVE[:-4]}.json' if HOME_SAVE.endswith('.asd') else f'probe_title_{HOME_SAVE}.json')), result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('probe', 'log')}, ensure_ascii=False, indent=1)[:3000])
    print('\n'.join(result['log'][-60:]))


if __name__ == '__main__':
    run()
