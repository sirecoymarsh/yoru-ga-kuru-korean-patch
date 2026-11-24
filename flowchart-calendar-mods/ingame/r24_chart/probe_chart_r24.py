"""Claude Opus 5.5 (2026-09-28) r24: the chart probes (r23 probe_chart_r23.py = r22 probe_chart_r22.py, copied) run on the r24
chart candidate, with the r24 steps in the title tour:
  chart1: the target page (locked cells now show name / E number / when / condition in grey, a thumbnail event an empty frame)
          [shot chart_target_locked] -> a locked cell -> its detail page without 이 장면 재생 [shot chart_locked_detail] ->
          돌아가기 -> the page again -> the 「전체 개방」 button (the part number a click gives) -> the same tab and page redrawn open
          [shot chart_button_all, the flag file read back] -> the 「다시 가리기」 button -> locked again [shot chart_button_hide,
          flag read back] -> close -> the title [shot chart_title_after_chart1] -> the r22 tour goes on (menu unlock_all ->
          chart2 -> replay -> title -> revert -> chart3 -> reset_all 아니요 -> END).
Probe-only additions: every select-dialog item is logged with its window (■選択ダイアログ／初期化 / ／選択肢追加 prefixed), the
cell block carries the legend, the three top buttons and each thumbnail part's CG name / construction count, KR_C24Key (the U / R
keys) answers false (no real keyboard in a hidden probe window), the chart frame prefix is on KR_C24Frame (the live delegate)
and the chart's live wait is KR_C24WaitRaw. After a replay the chart comes back (r24, 14:00 request): the chart tick logs
RESUMED + the page (TARGET RESUMED / HOME RESUMED) + a shot (chart_resumed / chart_home_resumed) and closes it. The hidden
probe window is parked off the desktop (park_windows) so the real cursor cannot light the title menu. Results: 증거/probe_chart_r24.json (+ probe_kinds.json / replay_kinds.json).
--- r22's text follows ---
Claude Opus 5.5 (2026-09-28) r22: isolated, muted native probes of the chart candidate (the launcher, save-folder and screenshot
plumbing are r21's probe_modmenu_r21.py; the tours are new).

  python probe_chart_r22.py --title            the title tour (the game boots normally, no save loaded): title [shot] -> request
                                               chart -> the chart (tabs, a page with thumbnail / small / locked cells) -> a locked
                                               cell -> notice -> close -> unlock_all -> chart -> the same cell open -> its page ->
                                               이 장면 재생 (memory mode) -> title [shot = before] -> unlock_revert -> chart ->
                                               locks back (the replayed scene keeps the read mark it got) -> request
                                               reset_all -> the confirm window on the title -> 아니요 -> no marker / .req /
                                               request left, title again [shot] -> END.
  python probe_chart_r22.py --kinds [NO ...]   one boot per scene: title -> request chart -> the chart asks for the replay of NO
                                               directly (the play request slot) -> memory-mode replay (messages clicked through,
                                               the first choice answered) -> back on the title [pixels = before]. 증거/replay_kinds.json
  python probe_chart_r22.py --home [SAVE]      a copied home save: home menu [shot] -> request chart (the r21 home poll) -> the
                                               chart on the home screen -> an open scene -> its page -> replay -> home menu [shot]
  python probe_chart_r22.py --z                the title only: absolute Z of the title root and of the chart root, shots

Everything lives under r22_chart/probe/ on P: (run/ = a copy of the runtime folder with the big assets hard-linked read only,
InstallInfo/SaveFolderSetting.ini type 2 so the saves stay inside run/). The global record files (read marks, CG / recollection /
BGM modes, AFConfig) are COPIES of the user's (work/savecopy, read only from OneDrive); the user's folder is only hashed.
The probe AIN = candidate + probe-only code (never shipped): MAIN -> KR_P22Main (muted; title mode calls the original main, home
mode resumes the copied save), config::detail::SetMute forced, every C_UserInputManager::Is* query 0 (no input), prefixes
(KR_CTitleTick <- KR_P22TitleTick, KR_CFrame <- KR_P22ChartTick, C_SelectDialog@_Update <- KR_P22DialogTick,
■選択メッセージ／選択肢追加 <- KR_P22ChoiceSeen), ■選択メッセージ／実行 -> the first choice, the message key wait -> click-through,
every other AFL_Parts_WaitForClick site except the title's, the select dialog's and the chart's -> log + exit 6.
Clicks are the game's own path: the probe ends the chart's / a dialog's wait with the number a click on that part would give
(AFL_Parts_EndWaitForClick), the request files are written in the hook's format by the probe (TextFile.WriteAll).
The log, the phase and counters are FILES (claude_probe*.txt) or session variables (not in resume images).
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r24lib as L

O = HERE / 'candidate'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterChartProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat']
SETTINGS = ['AFConfig.asd', 'MouseCursorSetting.sav', 'ShowDPSetting.sav', '3DConfig.vsf', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup']
HOME_SAVE = 'NightR44.asd'          # the r18-r21 home save (10/14)
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ['C_SelectDialog@Run', 'C_SceneTitle@Run', 'KR_C24WaitRaw']
SAVE_TYPE = 2
AUDIO_POLICY = 'Master mixer muted before initialization; config mute writes forced on; audio playback/timing retained.'
# one scene of every kind (see build_chart_r22.event_kinds): dated main, stage of a dated bundle, undated card, stage of an
# undated bundle, dungeon card, stage of a dungeon bundle, pool talk (after training), invitation, dungeon walk, recollection
# wrapper and copy, unused, system; plus choices and the battle
KIND_TARGETS = {'dated': 121, 'stage_dated': 273, 'undated': None, 'stage_undated': None, 'dungeon': 41, 'stage_dungeon': 42,
                'pool_talk': 1101, 'pool_invite': 1001, 'pool_walk': 2001, 'memory': 50101, 'memory_copy': 60015, 'unused': 55,
                'system': 6001, 'choice': 258, 'choice_memory': 60017, 'battle': 262}

# the battle scene waits for input in its own frame loop (no AFL_Parts_WaitForClick the probe could answer): its run can only end
# by the timeout, which the verdict reports as 'fail' (not verifiable to the end without a player)
KIND_TIMEOUT = {262: 240}

MUTE_JAF = '''
void KR_P22Mute() {
    KiwiSoundEngine.SetMixerMute(0, true);
}
'''

PROBE_JAF = r'''
// ---- files (survive ResumeLoad) and session variables (not in resume images)
string KR_P22Read(string file) {
    string s = "";
    if (!TextFile.ReadAll(file, s)) return "";
    return s;
}
void KR_P22Log(string text) {
    TextFile.WriteAll("claude_probe.txt", KR_P22Read("claude_probe.txt") + text + "\n");
}
string KR_P22Phase() {
    string s = KR_P22Read("claude_probe_phase.txt");
    int nl = s.Find("\n");
    if (nl >= 0) s = KR_JosaSlice(s, 0, nl);
    return s;
}
void KR_P22SetPhase(string p) {
    TextFile.WriteAll("claude_probe_phase.txt", p);
    KR_P22Log("PHASE " + p);
}
string KR_P22Get(string k) { return SystemService.SystemVariable_Get("YoruKR.P22." + k); }
void KR_P22Set(string k, string v) { SystemService.SystemVariable_Set("YoruKR.P22." + k, v); }
int KR_P22Num(string k) {
    string v = KR_P22Get(k);
    if (v == "") return 0;
    return v.ToInt();
}
void KR_P22SetN(string k, int v) { KR_P22Set(k, "%d" % v); }
int KR_P22B(bool v) {
    if (v) return 1;
    return 0;
}
void KR_P22Shot(string name) {
    AFL_View_Update();
    AFL_View_Update();
    AFL_View_Update();
    if (!SystemService.SaveScreenshot(name + ".bmp", 0, 0, 1280, 720)) system.Exit(9);
    KR_P22Log("SHOT " + name);
}
void KR_P22Block(string kind, string tag, string text) {
    KR_P22Log(kind + " " + tag + " <<<");
    KR_P22Log(text);
    KR_P22Log(">>>");
}
string KR_P22Stack() {
    string t = "";
    for (int i = 0; i < 40; i++) {
        string s = system.GetFuncStackName(i);
        if (s == "") break;
        t = t + s + " | ";
    }
    return t;
}
void KR_P22Req(string cmd) {
    if (!FileOperation.ExistFolder(KR_MFolder())) FileOperation.CreateFolder(KR_MFolder());
    int seq = KR_P22Num("Seq") + 1;
    KR_P22SetN("Seq", seq);
    TextFile.WriteAll(KR_MFile("request.txt"), cmd + "\n" + ("%d" % seq) + "\n2026-09-28 07:00:00\n");
    KR_P22Log("REQUEST " + cmd);
}
int KR_P22Ours() {
    int n = 0;
    for (int i = 0; i < 112; i++) {
        if (PartsEngine.IsExist(KR_CPart(i))) n++;
    }
    return n;
}
// r24: a top button: label, size, clickable
string KR_P24Btn(int k) {
    int n = KR_CPart(k);
    if (!PartsEngine.IsExist(n)) return "-";
    string lab = "";
    if (PartsEngine.IsExist(n + 1)) lab = PartsEngine.GetTextPartsText(n + 1, 1);
    return lab + " " + ("%d" % PartsEngine.Parts_GetPartsWidth(n, 1)) + "x" + ("%d" % PartsEngine.Parts_GetPartsHeight(n, 1)) + " click=" + ("%d" % KR_P22B(PartsEngine.Parts_GetPartsClickable(n)));
}
// r24: the thumbnail slot of a cell: its size and pass-through. No getter with a 「state」 argument that could turn the part into
// another type: Parts_GetPartsConstructionProcessCount wipes a CG part's picture and Parts_GetPartsCGName empties a construction
// part (diagnosed 09-28, work/diag*); CG vs empty frame is read from the screenshot pixels instead (verify --native).
string KR_P24Thumb(int box) {
    int th = box + 1;
    if (!PartsEngine.IsExist(th)) return "0";
    return "1 wh=" + ("%d" % PartsEngine.Parts_GetPartsWidth(th, 1)) + "x" + ("%d" % PartsEngine.Parts_GetPartsHeight(th, 1)) + " pass=" + ("%d" % KR_P22B(PartsEngine.Parts_GetPartsPassCursor(th)));
}
// every cell of the page as drawn (text parts), for the offline comparison with the VM
void KR_P22Cells(string tag) {
    string t = "OURS " + ("%d" % KR_P22Ours()) + " ALL " + KR_CGet("All") + " OPEN " + KR_CGet("Open");
    t = t + "\nHEAD " + PartsEngine.GetTextPartsText(KR_CPart(1), 1);
    t = t + "\nPAGE " + PartsEngine.GetTextPartsText(KR_CPart(3), 1);
    t = t + "\nLEGEND " + PartsEngine.GetTextPartsText(KR_CPart(2), 1);
    t = t + "\nBTN " + KR_P24Btn(38) + " | " + KR_P24Btn(36) + " | " + KR_P24Btn(30);
    for (int s = 0; s < 12; s++) {
        int box = KR_CCellBox(s);
        if (!PartsEngine.IsExist(box)) {
            t = t + "\nCELL " + ("%d" % s) + " -";
            continue;
        }
        string nm = "";
        if (PartsEngine.IsExist(box + 2)) nm = PartsEngine.GetTextPartsText(box + 2, 1);
        string id = "";
        if (PartsEngine.IsExist(box + 3)) id = PartsEngine.GetTextPartsText(box + 3, 1);
        string cd = "";
        if (PartsEngine.IsExist(box + 4)) cd = PartsEngine.GetTextPartsText(box + 4, 1);
        t = t + "\nCELL " + ("%d" % s) + " h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(box, 1)) + " thumb=" + KR_P24Thumb(box) + " name=" + nm + " id=" + id + " cond=" + cd;
    }
    KR_P22Block("CELLS", tag, t);
}
// every chart cell whose event the global records open (the VM draws the same pages from this list)
void KR_P22Global(string tag) {
    string t = "";
    int n = KR_CTabEnd(9);
    for (int i = 0; i < n; i++) {
        if (KR_CGlobal(KR_CCellEv(i)) == 1) t = t + " " + ("%d" % i);
    }
    KR_P22Log("GLOBAL " + tag + " ALL=" + KR_CGet("All") + t);
}
// ---- targets: a page with an open thumbnail cell, an open small cell and a locked cell (under the global records)
void KR_P22Find() {
    for (int t = 0; t <= 9; t++) {
        for (int p = 0; p < KR_CPages(t); p++) {
            int th = -1;
            int sm = -1;
            int lk = -1;
            int lk2 = -1;
            int lt = -1;
            for (int s = 0; s < 12; s++) {
                int i = KR_CTabFirst(t) + p * 12 + s;
                if (i >= KR_CTabEnd(t)) break;
                int no = KR_CCellEv(i);
                if (KR_COpen(no)) {
                    if (KR_CThumb(no) != "") {
                        if (th < 0) th = s;
                    }
                    else if (sm < 0) sm = s;
                }
                else {
                    if (KR_CThumb(no) != "") {
                        if (lt < 0) lt = s;
                    }
                    if (KR_CNoPlay(no) == 0) {
                        if (lk < 0) lk = s;
                        else if (lk2 < 0) lk2 = s;
                    }
                }
            }
            if (th >= 0 && sm >= 0 && lk >= 0 && lk2 >= 0 && (lt >= 0 || KR_P22Get("Relax") == "1")) {
                KR_P22SetN("TT", t);
                KR_P22SetN("TP", p);
                KR_P22SetN("TA", lk);
                KR_P22SetN("TB", lk2);
                KR_P22Log("TARGET tab=" + ("%d" % t) + " page=" + ("%d" % p) + " thumb=" + ("%d" % th) + " small=" + ("%d" % sm) + " locked=" + ("%d" % lk) + "," + ("%d" % lk2) + " locked_thumb=" + ("%d" % lt)
                    + " A=" + ("%d" % KR_CCellEv(KR_CTabFirst(t) + p * 12 + lk)) + " B=" + ("%d" % KR_CCellEv(KR_CTabFirst(t) + p * 12 + lk2)));
                return;
            }
        }
    }
    if (KR_P22Get("Relax") != "1") {
        KR_P22Log("NO TARGET PAGE WITH A LOCKED THUMBNAIL CELL: relaxed");
        KR_P22Set("Relax", "1");
        KR_P22Find();
        return;
    }
    KR_P22Log("NO TARGET PAGE");
    system.Exit(11);
}
// r24: the unlock flag file as the chart reads it (r21 KR_MUnlockAll) and the chart's session value
void KR_P24Flag(string tag) {
    string disk = "";
    int ok = KR_P22B(TextFile.ReadAll(KR_MChartFile(), disk));
    KR_P22Log("FLAG " + tag + " file=" + ("%d" % ok) + " unlock=" + ("%d" % KR_MUnlockAll()) + " all=" + KR_CGet("All") + " len=" + ("%d" % disk.Length()));
}
// r24: the items of the select dialog being built (■選択ダイアログ／初期化 clears, ／選択肢追加 appends)
void KR_P24ItemsClear() { KR_P22Set("Items", ""); }
void KR_P24ItemSeen(int id, string text) {
    KR_P22Set("Items", KR_P22Get("Items") + ("%d" % id) + ":" + text + "|");
}
// navigation inside the chart: returns true when the target page is shown (tab TT, page TP)
bool KR_P22Goto() {
    int t = KR_P22Num("TT");
    int p = KR_P22Num("TP");
    if (KR_P22Num("CurTab") != t) {
        KR_P22SetN("CurTab", t);
        KR_P22SetN("CurPage", 0);
        AFL_Parts_EndWaitForClick(KR_CTabBox(t));
        return false;
    }
    if (KR_P22Num("CurPage") < p) {
        KR_P22SetN("CurPage", KR_P22Num("CurPage") + 1);
        AFL_Parts_EndWaitForClick(2);
        return false;
    }
    return true;
}
void KR_P22Close(string next) {
    KR_P22SetPhase(next);
    AFL_Parts_EndWaitForClick(KR_CPart(30));
}
// ---- the title frame (prefix of KR_CTitleTick)
void KR_P22TitleTick() {
    int f = KR_P22Num("TF") + 1;
    KR_P22SetN("TF", f);
    if (f > 3600) {
        KR_P22Log("STUCK on the title phase=" + KR_P22Phase());
        KR_P22Shot("chart_stuck_title");
        system.Exit(5);
    }
    if (f < 90) return;
    KR_P22SetN("TF", 0);
    string ph = KR_P22Phase();
    if (ph == "boot") {
        int root = 0;
        if (PartsEngine.IsExistActivity(KR_CTitleAct())) root = PartsEngine.GetActivityPartsNumber(KR_CTitleAct(), "ルートパーツ");
        KR_P22Log("TITLE root=" + ("%d" % root) + " z=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(root)) + " maxz=" + ("%d" % PartsEngine.GetComponentAbsoluteMaxPosZ(root)));
        KR_P22Shot("chart_title_before");
        KR_P22SetN("T0", KR_Time());
        KR_P22SetN("CurTab", 0);
        KR_P22SetN("CurPage", 0);
        KR_P22SetN("Step", 0);
        @@BOOT@@
        return;
    }
    if (ph == "replaying") {
        KR_P22Log("RETURNED to the title msgs=" + KR_P22Get("Msgs") + " choices=" + KR_P22Get("Choices") + " ours=" + ("%d" % KR_P22Ours()) + " open=" + KR_CGet("Open") + " play=" + KR_CGet("Play") + " unwind=" + KR_T9Get("Unwind"));
        KR_P22SetPhase("after_replay");
        KR_P22SetN("TF", 0);
        return;
    }
    if (ph == "after_replay") {
        KR_P22Shot("chart_title_after_replay");
        @@AFTER_REPLAY@@
        return;
    }
    if (ph == "after_chart1") {
        KR_P22Shot("chart_title_after_chart1");
        KR_P22Req("unlock_all");
        KR_P22SetPhase("unlock");
        return;
    }
    if (ph == "after_unlock") {
        KR_P22SetN("CurTab", 0);
        KR_P22SetN("CurPage", 0);
        KR_P22SetN("Step", 0);
        KR_P22Req("chart");
        KR_P22SetPhase("chart2");
        return;
    }
    if (ph == "after_revert") {
        KR_P22SetN("CurTab", 0);
        KR_P22SetN("CurPage", 0);
        KR_P22SetN("Step", 0);
        KR_P22Req("chart");
        KR_P22SetPhase("chart3");
        return;
    }
    if (ph == "after_chart3") {
        KR_P22Log("END");
        system.Exit(0);
    }
    if (ph == "after_chart3t") {
        KR_P22Req("reset_all");
        KR_P22SetPhase("reset_no");
        return;
    }
    if (ph == "after_reset_no") {
        KR_P22Log("RESET NO marker=" + ("%d" % KR_P22B(FileOperation.ExistFile(KR_MMarkerFile()))) + " reset_req=" + ("%d" % KR_P22B(FileOperation.ExistFile(KR_MFile("reset.req")))) + " request=" + ("%d" % KR_P22B(FileOperation.ExistFile(KR_MFile("request.txt")))) + " ours=" + ("%d" % KR_P22Ours()));
        KR_P22Shot("chart_title_after_reset_no");
        KR_P22Log("END");
        system.Exit(0);
    }
}
// ---- the chart frame (prefix of KR_CFrame)
void KR_P22ChartTick() {
    int f = KR_P22Num("CF") + 1;
    KR_P22SetN("CF", f);
    if (f > 3600) {
        KR_P22Log("STUCK in the chart phase=" + KR_P22Phase());
        KR_P22Shot("chart_stuck_chart");
        system.Exit(5);
    }
    if (f < 30) return;
    KR_P22SetN("CF", 0);
    string ph = KR_P22Phase();
    int step = KR_P22Num("Step");
    KR_P22SetN("Step", step + 1);
    if (ph == "kchart") {
        KR_P22Log("KIND replay request " + ("%d" % @@TARGET@@) + " ours=" + ("%d" % KR_P22Ours()));
        KR_CSet("Play", "%d" % @@TARGET@@);
        KR_T9Set("Unwind", "1");
        KR_P22SetPhase("replaying");
        AFL_Parts_EndWaitForClick(0);
        return;
    }
    if (ph == "zchart") {
        KR_P22Log("CHART root z=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(KR_CRoot())) + " maxz=" + ("%d" % PartsEngine.GetComponentAbsoluteMaxPosZ(KR_CRoot())));
        KR_P22Cells("Z");
        KR_P22Shot("chart_z");
        KR_P22Close("after_chart3");
        return;
    }
    if (ph == "chart1") {
        if (step == 0) {
            KR_P22Log("CHART root z=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(KR_CRoot())) + " open_ms=" + ("%d" % (KR_Time() - KR_P22Num("T0"))) + " (request written -> first chart frame + 30 frames)");
            KR_P22Global("chart1");
            int d0 = KR_Time();
            for (int rep = 0; rep < 5; rep++) KR_CDraw(0, 0);
            int d1 = KR_Time();
            for (int rep2 = 0; rep2 < 5; rep2++) KR_CDraw(2, 0);
            int d2 = KR_Time();
            KR_CDraw(0, 0);
            KR_P22Log("DRAW ms per page: tab0 " + ("%d" % ((d1 - d0) / 5)) + " tab2(203 cells) " + ("%d" % ((d2 - d1) / 5)));
            KR_P22Find();
            KR_P22Cells("TAB0 P1");
            KR_P22Shot("chart_tab_apr_p1");
            KR_P22SetN("CurTab", 6);
            AFL_Parts_EndWaitForClick(KR_CTabBox(6));
            return;
        }
        if (step == 1) {
            KR_P22Cells("TAB6 P1");
            KR_P22Shot("chart_tab_oct_p1");
            KR_P22SetN("CurTab", 8);
            AFL_Parts_EndWaitForClick(KR_CTabBox(8));
            return;
        }
        if (step == 2) {
            KR_P22Cells("TAB8 P1");
            KR_P22Shot("chart_tab_memory_p1");
            return;
        }
        if (KR_P22Get("Done1") == "") {
            if (!KR_P22Goto()) return;
            KR_P22Cells("TARGET LOCKED");
            KR_P24Flag("before");
            KR_P22Shot("chart_target_locked");
            KR_P22Set("Done1", "1");
            AFL_Parts_EndWaitForClick(KR_CCellBox(KR_P22Num("TA")));
            return;
        }
        if (KR_P22Get("Done2") == "") {
            KR_P22Cells("TARGET AFTER DETAIL");
            KR_P22Shot("chart_target_after_detail");
            KR_P22Set("Done2", "1");
            KR_P22Log("PRESS button all");
            AFL_Parts_EndWaitForClick(KR_CPart(36));
            return;
        }
        if (KR_P22Get("Done3") == "") {
            KR_P22Cells("TARGET BUTTON ALL");
            KR_P24Flag("button_all");
            KR_P22Shot("chart_button_all");
            KR_P22Set("Done3", "1");
            KR_P22Log("PRESS button hide");
            AFL_Parts_EndWaitForClick(KR_CPart(38));
            return;
        }
        KR_P22Cells("TARGET BUTTON HIDE");
        KR_P24Flag("button_hide");
        KR_P22Shot("chart_button_hide");
        KR_P22Close("after_chart1");
        return;
    }
    if (ph == "chart2") {
        if (step == 0) KR_P22Global("chart2");
        if (!KR_P22Goto()) return;
        KR_P22Cells("TARGET UNLOCKED");
        KR_P22Shot("chart_target_unlocked");
        AFL_Parts_EndWaitForClick(KR_CCellBox(KR_P22Num("TA")));
        return;
    }
    if (ph == "chart3") {
        if (step == 0) KR_P22Global("chart3");
        if (!KR_P22Goto()) return;
        KR_P22Cells("TARGET REVERTED");
        KR_P22Shot("chart_target_reverted");
        KR_P22Close("after_chart3t");
        return;
    }
    if (ph == "hchart") {
        if (step == 0) {
            KR_P22Log("CHART home root z=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(KR_CRoot())));
            KR_P22Global("home");
            KR_P22Cells("HOME OPEN");
            KR_P22Shot("chart_home_open");
            // the first open cell of this page that is playable
            for (int s = 0; s < 12; s++) {
                int box = KR_CCellBox(s);
                if (!PartsEngine.IsExist(box)) continue;
                int i = KR_CTabFirst(KR_CTabIndexNow()) + s;
                if (i >= KR_CTabEnd(KR_CTabIndexNow())) break;
                int no = KR_CCellEv(i);
                if (KR_COpen(no) && KR_CNoPlay(no) == 0 && KR_CGlobal(no) == 1) {
                    KR_P22Log("HOME target cell " + ("%d" % s) + " event " + ("%d" % no));
                    KR_P22SetPhase("hpage");
                    AFL_Parts_EndWaitForClick(box);
                    return;
                }
            }
            KR_P22Log("HOME no open cell on the first page");
            system.Exit(12);
        }
        return;
    }
    if (ph == "replaying") {
        // r24: the chart opened again after the replay (same tab / page, the played cell's border gold): record it and close it;
        // the title / home tick then logs RETURNED as in r22
        KR_P22Log("RESUMED chart after the replay msgs=" + KR_P22Get("Msgs") + " ours=" + ("%d" % KR_P22Ours()) + " open=" + KR_CGet("Open") + " last=" + KR_CGet("Last") + " ctx=" + KR_CGet("Ctx") + " play=" + KR_CGet("Play"));
        KR_P22Global("resumed");
        if (KR_CGet("Ctx") == "2") {
            KR_P22Cells("HOME RESUMED");
            KR_P22Shot("chart_home_resumed");
        }
        else {
            KR_P22Cells("TARGET RESUMED");
            KR_P22Shot("chart_resumed");
        }
        KR_P22Close("replaying");
        return;
    }
    KR_P22Log("UNEXPECTED CHART FRAME phase=" + ph);
    KR_P22Shot("chart_unexpected_chart");
    system.Exit(7);
}
int KR_CTabIndexNow() {
    return KR_T9NowMonth() - 4;
}
// ---- dialogs (prefix of C_SelectDialog@_Update)
void KR_P22DialogTick() {
    int f = KR_P22Num("DF") + 1;
    KR_P22SetN("DF", f);
    if (f > 3600) {
        KR_P22Log("STUCK in a dialog phase=" + KR_P22Phase());
        KR_P22Shot("chart_stuck_dialog");
        system.Exit(5);
    }
    if (f < 30) return;
    KR_P22SetN("DF", 0);
    string ph = KR_P22Phase();
    string title = SystemService.SystemVariable_Get("YoruKR.T8.Title");
    if (SystemService.SystemVariable_Get("YoruKR.M.Home") == "1") {
        // the home menu (armed by r21)
        if (ph == "boot") {
            KR_P22Log("HOME menu ours=" + ("%d" % KR_P22Ours()));
            KR_P22Shot("chart_home_before");
            KR_P22SetN("Step", 0);
            KR_P22SetPhase("hchart");
            KR_P22Req("chart");
            return;
        }
        if (ph == "replaying") {
            KR_P22Log("RETURNED to the home menu msgs=" + KR_P22Get("Msgs") + " ours=" + ("%d" % KR_P22Ours()) + " open=" + KR_CGet("Open") + " play=" + KR_CGet("Play"));
            KR_P22SetPhase("home_after");
            return;
        }
        if (ph == "home_after") {
            KR_P22Shot("chart_home_after");
            KR_P22Log("END");
            system.Exit(0);
        }
        return;
    }
    KR_P22Block("DIALOG", ph, title + "\nITEMS " + KR_P22Get("Items"));
    if (ph == "chart1") {
        KR_P22Shot("chart_locked_detail");
        AFL_Parts_EndWaitForClick(0);
        return;
    }
    if (ph == "unlock") {
        KR_P22Shot("chart_unlock_notice");
        KR_P22SetPhase("after_unlock");
        AFL_Parts_EndWaitForClick(1);
        return;
    }
    if (ph == "chart2") {
        KR_P22Shot("chart_detail_open");
        KR_P22SetN("Msgs", 0);
        KR_P22SetPhase("replaying");
        AFL_Parts_EndWaitForClick(13);
        return;
    }
    if (ph == "revert") {
        KR_P22Shot("chart_revert_notice");
        KR_P22SetPhase("after_revert");
        AFL_Parts_EndWaitForClick(1);
        return;
    }
    if (ph == "reset_no") {
        KR_P22Shot("chart_title_reset_confirm");
        KR_P22SetPhase("after_reset_no");
        AFL_Parts_EndWaitForClick(12);
        return;
    }
    if (ph == "hpage") {
        KR_P22Shot("chart_home_detail");
        KR_P22SetN("Msgs", 0);
        KR_P22SetPhase("replaying");
        AFL_Parts_EndWaitForClick(13);
        return;
    }
    KR_P22Log("UNEXPECTED DIALOG phase=" + ph);
    KR_P22Shot("chart_unexpected_dialog");
    system.Exit(7);
}
// ---- the replay: message key waits clicked through, choices answered with the first one
int KR_P22MsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    int n = KR_P22Num("Msgs") + 1;
    KR_P22SetN("Msgs", n);
    if (KR_P22Phase() != "replaying") {
        KR_P22Log("MESSAGE WAIT outside a replay phase=" + KR_P22Phase());
        KR_P22Shot("chart_msg_unexpected");
        system.Exit(8);
    }
    if (n == 1) {
        KR_P22Log("REPLAY first message memory=" + ("%d" % KR_P22B(Ａ＿回想モード実行中確認())) + " fn=" + LSys3xScript::m_FuncName + " ours=" + ("%d" % KR_P22Ours()));
        KR_P22Shot("chart_spoiler_replay_msg1");
    }
    if (n > 4000) {
        KR_P22Log("TOO MANY MESSAGES");
        system.Exit(8);
    }
    return 0;
}
void KR_P22ChoiceSeen(int id) {
    if (KR_P22Get("Choice") == "") KR_P22Set("Choice", "%d" % id);
}
int KR_P22Choice(bool cancel, int time) {
    string c = KR_P22Get("Choice");
    KR_P22Set("Choice", "");
    KR_P22SetN("Choices", KR_P22Num("Choices") + 1);
    int id = 0;
    if (c != "") id = c.ToInt();
    KR_P22Log("CHOICE answered " + ("%d" % id) + " fn=" + LSys3xScript::m_FuncName);
    ■選択メッセージ／初期化();
    return id;
}
int KR_P22Wait(FTPARTS_WaitForClickCallback func, bool cancel) {
    KR_P22Log("UNEXPECTED WAIT phase=" + KR_P22Phase() + " fn=" + LSys3xScript::m_FuncName + " stack=" + KR_P22Stack());
    KR_P22Shot("chart_unexpected_wait");
    system.Exit(6);
    return 0;
}
int KR_P22Main() {
    KR_P22Mute();
    TextFile.WriteAll("claude_probe_phase.txt", "boot");
    KR_P22Log("SAVEFOLDER " + system.GetSaveFolderName());
    KR_P22Log("MODE @@MODE@@");
    @@MAIN@@
}
'''


def build_probe(mode, target=0, key=''):
    """The probe AIN in run/: candidate + PROBE_JAF (+ the patches listed in the module text)."""
    src = O / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    boot = {'title': 'KR_P22Req("chart"); KR_P22SetPhase("chart1");',
            'kinds': 'KR_P22Req("chart"); KR_P22SetPhase("kchart");',
            'z': 'KR_P22Req("chart"); KR_P22SetPhase("zchart");',
            'home': 'KR_P22Log("TITLE in home mode"); system.Exit(13);'}[mode]
    after = {'title': 'KR_P22Req("unlock_revert"); KR_P22SetPhase("revert");',
             'kinds': 'KR_P22Log("END"); system.Exit(0);', 'z': 'system.Exit(14);', 'home': 'system.Exit(14);'}[mode]
    if mode == 'home':
        main = ('PassRegister.SetFileName(0, "NightRAFCGMode.asd");\n    PassRegister.SetFileName(1, "NightRAFMemMode.asd");\n'
                '    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");\n'
                f'    system.ResumeLoad("{key}", "{HOME_SAVE}");\n    system.Exit(2);\n    return 2;')
    else:
        main = 'return main();'
    jaf = MUTE_JAF + PROBE_JAF
    jaf = (jaf.replace('@@BOOT@@', boot).replace('@@AFTER_REPLAY@@', after).replace('@@MAIN@@', main)
           .replace('@@MODE@@', mode).replace('@@TARGET@@', str(target)))
    assert '@@' not in jaf, re.findall(r'@@\w+@@', jaf)
    jaf = L.jaf_literal_encode(jaf)
    work = PROBE / 'build'
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
    for f in added:
        path = work / f"probe_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), f['name']))

    def prefix(name, code):
        fid = L.fid_of(m, name)
        path = work / f'original_{fid}.jam'
        L.cmd('ain', 'dump', '--function', L.symbol(m, fid), '-o', path, src)
        patch.append(L.begin(L.clean(path.read_text('utf8'), name), code))
    prefix('KR_CTitleTick', '\tCALLFUNC KR_P22TitleTick\n')
    prefix('KR_C24Frame', '\tCALLFUNC KR_P22ChartTick\n')
    prefix('■選択ダイアログ／初期化', '\tCALLFUNC KR_P24ItemsClear\n')
    prefix('■選択ダイアログ／選択肢追加', '\t.LOCALREF 番号\n\t.LOCALREF 選択文字列\n\tA_REF\n\tCALLFUNC KR_P24ItemSeen\n')
    kfid = L.fid_of(m, 'KR_C24Key')
    patch.append(f"FUNC {kfid}\n\tPUSH 0\n\tRETURN\nENDFUNC KR_C24Key\n")        # no real keyboard in the probe
    prefix('C_SelectDialog@_Update', '\tCALLFUNC KR_P22DialogTick\n')
    prefix('■選択メッセージ／選択肢追加', '\t.LOCALREF 番号\n\tCALLFUNC KR_P22ChoiceSeen\n')
    run = L.fid_of(m, '■選択メッセージ／実行')
    patch.append(f"FUNC {run}\n\t.LOCALREF bキャンセル\n\t.LOCALREF n時間\n\tCALLFUNC KR_P22Choice\n\tRETURN\nENDFUNC ■選択メッセージ／実行\n")
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_P22Main'])
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    vers = L.versions(L.WORK / 'build' / 'candidate_raw_code.jam')
    waits = []
    for f in m['functions']:
        name = L.raw_symbol(m, f['index'])
        for v in [v for v in vers.get(f['index'], []) if v['start'] == f['address']]:
            for ad, op in v['ops']:
                if op != f'CALLFUNC 0x{wait:x}':
                    continue
                assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, wait)
                if name in LIVE_WAITS:
                    waits.append((name, 'live'))
                    continue
                target_fid = ids['KR_P22MsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_P22Wait']
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, target_fid)
                waits.append((name, 'message click-through' if target_fid == ids['KR_P22MsgWait'] else 'exit'))
    live = sorted(n for n, k in waits if k == 'live')
    assert live == sorted(LIVE_WAITS), live
    assert sum(1 for _, k in waits if k.startswith('message')) == 1, waits
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(waits=len(waits), live=live, probe_sha256=L.sha(out), mode=mode, target=target)


# ---------------------------------------------------------------- folder, launcher (r21 probe)
def setup_folder():
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    assert L.sha(RUN / 'winmm.dll') == L.BASE_WINMM_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
    for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex']:
        shutil.copy2(rt / n, RUN / n)
        shutil.copy2(rt / n, RUN / n.replace('NightRemaster', BOOT, 1))
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
    menu = RUN / 'KRMenu'
    if menu.exists():
        shutil.rmtree(menu)
    return rt


def set_savefolder(savename):
    ini = (RUN / 'AliceStart.ini').read_bytes()
    folder = b'SaveFolder\t= "' + savename.encode('cp932') + b'"'
    ini = re.sub(rb'SaveFolder\t= "[^"]*"', lambda z: folder, ini)
    assert folder in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    (RUN / 'InstallInfo').mkdir(exist_ok=True)
    (RUN / 'InstallInfo' / 'SaveFolderSetting.ini').write_bytes(b'SFSF' + struct.pack('<ii', 0, SAVE_TYPE))
    for n in ['claude_probe.txt', 'claude_probe_phase.txt']:
        if (RUN / n).exists():
            (RUN / n).unlink()
    for b in RUN.glob('*.bmp'):
        b.unlink()


K = C.WinDLL('kernel32', use_last_error=True)
U = C.WinDLL('user32', use_last_error=True)
U.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
U.GetWindowRect.argtypes = [W.HWND, C.POINTER(W.RECT)]
U.SetWindowPos.argtypes = [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT]
ENUM_PROC = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)


def park_windows(pid):
    """r24: keep the probe's own (hidden) windows off the desktop so the real mouse cursor can never hover the title menu: in the
    first r24 per-kind run the title's button highlight followed the user's cursor (5,209 / 6,223 px on 새 게임 / 불러오기 between
    the shots before and after a replay). Only windows of the probe process `pid`; the move is posted (SWP_ASYNCWINDOWPOS), never
    sent, so a debuggee stopped at a debug event cannot block the launcher."""
    moved = []

    def cb(h, l):
        p = W.DWORD()
        U.GetWindowThreadProcessId(h, C.byref(p))
        if p.value == pid:
            r = W.RECT()
            U.GetWindowRect(h, C.byref(r))
            if r.left > -5000:
                U.SetWindowPos(h, None, -6000, -6000, 0, 0, 0x0001 | 0x0004 | 0x0010 | 0x4000)   # NOSIZE NOZORDER NOACTIVATE ASYNC
                moved.append(int(h))
        return True
    U.EnumWindows(ENUM_PROC(cb), 0)
    return moved
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
    """09-24 probe launcher: hidden window, debugger on, MessageBoxA and the VM error handler break-pointed so engine errors are
    captured instead of waiting on a dialog. TEMP/TMP point to P:."""
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
    result = {'pid': pid, 'audio': AUDIO_POLICY, 'ain_sha256': L.sha(RUN / 'NightRemaster.ain'), 'events': []}

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
        parked = 0.0
        result['parked_windows'] = []
        while time.monotonic() < deadline:
            if time.monotonic() - parked > 0.5:
                parked = time.monotonic()
                result['parked_windows'] += [h for h in park_windows(pid) if h not in result['parked_windows']]
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
                            result['message'] = {'cp932': cstr(args[1]).decode('cp932', 'replace')}
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


def user_game_running():
    import subprocess
    cmd = ("@(Get-CimInstance Win32_Process -Filter \"Name = 'NightRemaster.exe'\" | Select-Object ProcessId,ExecutablePath) | ConvertTo-Json -Compress")
    q = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, timeout=60, env=L.env())
    s = q.stdout.decode('utf-8-sig').strip()
    rows = json.loads(s) if s else []
    rows = rows if isinstance(rows, list) else [rows]
    rt = L.runtime()[1].resolve()
    return [r for r in rows if r.get('ExecutablePath') and Path(r['ExecutablePath']).resolve().parent == rt]


def folder_hashes(d):
    return {p.relative_to(d).as_posix(): L.sha(p) for p in sorted(d.rglob('*')) if p.is_file()} if d.exists() else {}


def collect_shots(sub, prefix=''):
    from PIL import Image
    dest = L.EVID / sub
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(RUN.glob('*.bmp')):
        png = dest / (prefix + b.stem + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(png.name)
    return shots


def diff_pixels(a, b):
    from PIL import Image, ImageChops
    x = Image.open(a).convert('RGB')
    y = Image.open(b).convert('RGB')
    if x.size != y.size:
        return -1
    d = ImageChops.difference(x, y)
    return sum(1 for p in d.getdata() if p != (0, 0, 0))


def blocks(log, kind):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'(%s) (.*) <<<$' % kind, log[i])
        if z:
            j = log.index('>>>', i)
            out.setdefault(z.group(2), []).append('\n'.join(log[i + 1:j]))
            i = j
        i += 1
    return out


def write_kinds(doc):
    """증거/replay_kinds.json: the verdict of every replay kind the chart knows (build_chart_r22.event_kinds) and of the two flags
    (choice, battle), from the per-scene boots. A kind is 「ok」 only when every probed scene of it came back to the title with
    the title's pixels unchanged; a kind with a failure is 「fail」 (its scenes get 「재생 불가(게임 안에서만)」); an unprobed kind
    is listed as 「untested」 (treated as playable, reported)."""
    kinds = {}
    for no, r in doc.items():
        k = r.get('kind')
        if not k:
            continue
        base = {'choice': None, 'choice_memory': None, 'battle': None, 'memory_copy': 'memory'}.get(k, k)
        flag = {'choice': 'choice', 'choice_memory': 'choice', 'battle': 'battle'}.get(k)
        ok = r['verdict'] == 'ok' and r.get('title_pixels_differing') == 0
        for key in [x for x in (base, flag) if x]:
            kinds.setdefault(key, []).append((int(no), ok))
    verdicts = {k: ('ok' if all(ok for _, ok in v) else 'fail') for k, v in kinds.items()}
    for k in ('dated', 'stage_dated', 'dungeon', 'stage_dungeon', 'pool_talk', 'pool_invite', 'pool_walk', 'memory', 'unused', 'system',
              'choice', 'battle'):
        verdicts.setdefault(k, 'untested')
    L.writej(L.EVID / 'replay_kinds.json', dict(
        author=L.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(timespec='seconds'), candidate_sha256=L.sha(O / 'NightRemaster.ain'),
        method='one boot per scene: title -> request chart -> the chart asks for the replay (the play request slot) -> memory mode '
               '(AFL_MemoryModeEvent_Begin -> new C_SceneGame -> Prepare + RunEvent -> End -> Cleanup) with the messages clicked through and '
               'the first choice answered -> back on the title; ok = returned to the title, exit 0, no engine error / message box, '
               'title pixels equal to the shot before the chart',
        verdicts=verdicts, scenes={k: [n for n, _ in v] for k, v in kinds.items()},
        events={no: dict(kind=r.get('kind'), verdict=r['verdict'], pixels=r.get('title_pixels_differing'), seconds=r.get('seconds'),
                         messages=r.get('messages'), why=r.get('why'), candidate_sha256=r.get('candidate_sha256')) for no, r in doc.items()}))


def one_run(mode, stamp, target=0, save=None, copy_save=False, timeout=900):
    savename = f'SaveData_R24ChartProbe_{stamp}'
    savedir = RUN / savename
    set_savefolder(savename)
    savedir.mkdir(parents=True)
    files = L.save_manifest()['files']
    for n in COPY_GLOBAL:
        if n in files:
            shutil.copy2(L.save_path(n), savedir / n)
    if copy_save:
        shutil.copy2(L.save_path(save), savedir / save)
    before = folder_hashes(savedir)
    t0 = time.time()
    result = launch(timeout=timeout)
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    after = folder_hashes(savedir)
    result['save_folder'] = str(savedir)
    result['settings_unchanged'] = {n: before.get(n) == after.get(n) for n in SETTINGS if n in before}
    result['changed_files'] = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
    return result


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    ptr, rt = L.runtime()
    assert L.sha(rt / 'NightRemaster.ain') == L.BASE_AIN_SHA, 'runtime moved since the candidate was built'
    man = L.readj(O / 'manifest.json')
    assert L.sha(O / 'NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    assert shutil.disk_usage('P:\\').free >= 10 * 1024 ** 3, 'P: free space below 10 GB'
    user_before = user_state()
    playing = user_game_running()
    setup_folder()
    results = {}
    if args and args[0] == '--kinds':
        wanted = [int(x) for x in args[1:]] or [v for v in KIND_TARGETS.values() if v]
        name_of = {v: k for k, v in KIND_TARGETS.items() if v}
        for no in wanted:
            stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            info = build_probe('kinds', target=no)
            r = one_run('kinds', stamp, target=no, timeout=KIND_TIMEOUT.get(no, 900))
            r['probe'] = info
            r['candidate_sha256'] = man['files']['NightRemaster.ain']['sha256']
            shots = collect_shots('probe_kinds', prefix='k%05d_' % no)
            r['shots'] = shots
            ret = any(l.startswith('RETURNED') for l in r['log'])
            end = 'END' in r['log']
            px = None
            if 'k%05d_chart_title_before.png' % no in shots and 'k%05d_chart_title_after_replay.png' % no in shots:
                px = diff_pixels(L.EVID / 'probe_kinds' / ('k%05d_chart_title_before.png' % no), L.EVID / 'probe_kinds' / ('k%05d_chart_title_after_replay.png' % no))
            verdict = 'ok' if (ret and end and r.get('exit_code') == 0 and 'vm_error' not in r and 'message' not in r) else 'fail'
            why = [l for l in r['log'] if l.startswith(('UNEXPECTED', 'STUCK', 'TOO MANY'))] + ([str(r.get('vm_error'))] if 'vm_error' in r else []) + ([str(r.get('message'))] if 'message' in r else []) + (['timeout: no return to the title within %d s' % KIND_TIMEOUT.get(no, 900)] if r.get('timeout') else [])
            results[str(no)] = dict(kind=name_of.get(no), verdict=verdict, exit_code=r.get('exit_code'), seconds=r['seconds'], candidate_sha256=r['candidate_sha256'],
                                    returned=ret, title_pixels_differing=px, why=why, messages=next((l for l in r['log'] if l.startswith('RETURNED')), None),
                                    choices=[l for l in r['log'] if l.startswith('CHOICE')], log_tail=r['log'][-12:])
            print(no, name_of.get(no), verdict, r.get('exit_code'), r['seconds'], 's', 'px', px, why[:2], flush=True)
        prev = L.readj(L.EVID / 'probe_kinds.json') if (L.EVID / 'probe_kinds.json').exists() else {}
        prev.update(results)
        L.writej(L.EVID / 'probe_kinds.json', prev)
        write_kinds(prev)
    else:
        mode = {'--title': 'title', '--home': 'home', '--z': 'z'}.get(args[0] if args else '--title', 'title')
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        key = L.save_records(L.save_path(HOME_SAVE))['key'] if mode == 'home' else ''
        info = build_probe(mode, key=key)
        r = one_run(mode, stamp, save=HOME_SAVE, copy_save=(mode == 'home'))
        r['probe'] = info
        r['candidate_sha256'] = man['files']['NightRemaster.ain']['sha256']
        r['shots'] = collect_shots('probe_z' if mode == 'z' else 'probe')   # z: own folder (its title shot would replace the tour's)
        results[mode] = r
        for l in r['log']:
            if not l.startswith(('CELL', 'HEAD', 'PAGE', 'OURS')):
                print(l[:300])
        print('exit', r.get('exit_code'), r.get('vm_error'), r.get('message'), r['seconds'], 's', flush=True)
        prev = L.readj(L.EVID / 'probe_chart_r24.json') if (L.EVID / 'probe_chart_r24.json').exists() else {}
        prev[mode] = dict(r, time=stamp)
        L.writej(L.EVID / 'probe_chart_r24.json', prev)
    user_after = user_state()
    changed = sorted(n for n in set(user_before) | set(user_after) if user_before.get(n) != user_after.get(n))
    print('user save folder changed files:', len(changed), '(user game running: %s)' % bool(playing or user_game_running()))


if __name__ == '__main__':
    main()
