"""Claude Opus 5.5 (2026-09-27) r18: isolated, muted native probe of the calendar candidate (after probe_calendar_r17.py).

  python probe_calendar_r18.py [SAVE]              full probe (default: work/probe_pick.json, else the newest home-base save copy)
  python probe_calendar_r18.py --regs SAVE ...     per save: resume, log today's date, every calendar event registered in that
                                                   save, the home panel text (KR_RateText), Σ KR_PlayerEventCount(0..3) and the
                                                   summary title (KR_T18SummaryTitle) (증거/probe_regs.json), exit
  python probe_calendar_r18.py --savefolder-test   only: resume + home menu screenshot + exit (checks the P: save folder)

Everything lives under r18_calendar\\probe\\ on P:
  run\\           a copy of the runtime folder: exe/dll/ini/Data/PACT/EX copied, CG/Font/Sound/Voice/Movie hard-linked from the
                 RUNTIME (read-only assets), AliceStart.ini BootName = probe name, InstallInfo\\SaveFolderSetting.ini type 2
                 (saves inside run\\ on P:); the sandbox's temp file and the probe's mid-replay save land there too.
  run\\SaveData_R18CalendarProbe_<stamp>\\  global record files + one save, COPIES (r18lib.save_path). The user's save folder is
                 only read; its hashes are compared.
The probe AIN = candidate + probe-only code (never shipped): MAIN -> KR_ClaudeProbeMain (Codex diagnostic mute, resume the
copied save); config::detail::SetMute / C_UserInputManager::Is* patched (muted, no input); C_SelectDialog@_Update gets the
prefix KR_CalProbeTick (runs every frame a selection dialog waits); the message key wait -> KR_CalProbeMsgWait (click-through,
screenshots of the first two waits, the mid-replay save); every other AFL_Parts_WaitForClick site -> log + exit.
The log, the phase and the message counter are FILES (claude_probe*.txt): ResumeLoad may bring session variables back to the
saved values, files are outside the resume image.
Tick script (the paths a player uses):
  r17 tour: home [shot, STATE HOME, PANEL] -> character row -> r13 window [shot] -> 달력으로 보기 -> lane page [shot, ROWS] ->
  돌아가기 -> month page [shot] -> 달성도 보기 [shot] -> 돌아가기 -> month page [shot, = first] -> September [shot, 3 columns] ->
  October 마나미 [shots p1, p2] -> 11월 -> 회상 · 그 밖 [shot, ROWS] -> April -> 던전 lane [shot, ROWS] -> 돌아가기
  r18 lock: the first ● card (months 4-11) -> its card page [shot cal_card_locked_unseen, TITLE, ITEMS] -> back; the first △
  card if the save has one [shot cal_card_locked_other]
  r18 sandbox: the target card (a scene seen in this save that raises an affinity) -> card page [shot] -> 단계 고르기 ->
  stage -> scene page [shot, TITLE, ITEMS, STATE PREPLAY] -> 이 장면 재생 -> (all windows close, home menu returns 3, casual
  site -> KR_T18RunSandboxed: temp resume save, RunEvent) [message 1: shot spoiler, STATE MIDREPLAY; message 2: shot spoiler,
  mid-replay save to slot 90] -> ロード実行 of the temp file -> home [shot cal_home_after, STATE AFTER, PANEL] -> load slot 90
  (gamesave::detail::Load) -> the rest of the scene -> home [shot cal_home_midload, STATE MIDLOAD, PANEL]: END.
Every page title and drawer-row list is logged for the offline comparison (verify_calendar_r18.py --native).
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time, zlib
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r18lib as L

O = HERE / 'candidate'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterCalendarProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat']
AUDIO_POLICY = 'Master mixer muted before initialization; config mute writes forced on; audio playback/timing retained.'
MUTE_JAF = '''
void KR_DiagnosticMute() {
    if (!KiwiSoundEngine.SetMixerMute(0, true) ||
        !config::detail::GetMasterMute()) {
        system.Exit(91);
        return;
    }
}
'''
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
SAVE_TYPE = 2
MANAMI = 3          # lane 3 = 마나미 (October holds the eight 10/11 rows that carry E-number tails; page 2 has drawer rows)
DUNGEON = 8         # lane 8 = 던전 (April: the two drawers whose only scenes are outside the panel)
MIDSAVE_SLOT = 90   # the probe's mid-replay save (inside the probe's own save folder)

PROBE_JAF = r'''
// ---- files: survive ResumeLoad (session variables may not)
string KR_CPRead(string file) {
    string s = "";
    if (!TextFile.ReadAll(file, s)) return "";
    return s;
}
void KR_ClaudeProbeLog(string text) {
    TextFile.WriteAll("claude_probe.txt", KR_CPRead("claude_probe.txt") + text + "\n");
}
string KR_CPPhase() {
    string s = KR_CPRead("claude_probe_phase.txt");
    int nl = s.Find("\n");
    if (nl >= 0) s = KR_JosaSlice(s, 0, nl);
    return s;
}
void KR_CPSetPhase(string p) {
    TextFile.WriteAll("claude_probe_phase.txt", p);          // no newline: WriteAll writes a lone LF as CR LF, ReadAll returns the raw bytes
    KR_ClaudeProbeLog("PHASE " + p);
}
int KR_CPMsgs() {
    string s = KR_CPRead("claude_probe_msgs.txt");
    int nl = s.Find("\n");
    if (nl >= 0) s = KR_JosaSlice(s, 0, nl);
    if (s == "") return 0;
    return s.ToInt();
}
int KR_ClaudeShot(string file) {
    AFL_View_Update(); AFL_View_Update(); AFL_View_Update();
    if (!SystemService.SaveScreenshot(file, 0, 0, 1280, 720)) system.Exit(9);
    KR_ClaudeProbeLog("SHOT " + file);
    return 0;
}
string KR_CPGet(string key) { return SystemService.SystemVariable_Get("YoruKR.CalProbe." + key); }
void KR_CPSet(string key, string value) { SystemService.SystemVariable_Set("YoruKR.CalProbe." + key, value); }
int KR_CPNum(string key) { string v = KR_CPGet(key); if (v == "") return 0; return v.ToInt(); }
int KR_CPB(bool v) { if (v) return 1; return 0; }
string KR_CPTitle() { return SystemService.SystemVariable_Get("YoruKR.T8.Title"); }
string KR_CPHead() {
    string t = KR_CPTitle();
    int nl = t.Find("\n");
    if (nl > 0) t = KR_JosaSlice(t, 0, nl);
    return t;
}
void KR_CPEnd(int code) {
    KR_CPSet("Frames", "0");
    AFL_Parts_EndWaitForClick(code);
}
void KR_CPBlock(string kind, string tag, string text) {
    KR_ClaudeProbeLog(kind + " " + tag + " <<<");
    KR_ClaudeProbeLog(text);
    KR_ClaudeProbeLog(">>>");
}
void KR_CPTitleLog(string tag) { KR_CPBlock("TITLE", tag, KR_CPTitle()); }
// every calendar event registered in this save (stage table then drawer scene table), one line
string KR_CPRegsText() {
    string t = "";
    for (int i = 0; i < 404; i++) { int e = KR_T9StageEv(i); if (KR_T9Seen(e)) t = t + " " + ("%d" % e); }
    for (int j = 0; j < 760; j++) { int e2 = KR_T9SceneEv(j); if (KR_T9Seen(e2)) t = t + " " + ("%d" % e2); }
    return t;
}
void KR_CPRegs() { KR_ClaudeProbeLog("REGS" + KR_CPRegsText()); }
// drawer/card rows of a lane page as KR_T9LanePage lists them (same functions, same paging)
void KR_CPLaneRows(int m, int l, int page) {
    int nc = KR_T9LaneCards(m, l);
    int n = nc + KR_T9LaneChips(m, l);
    int per = 10;
    if (n > 10) per = 8;
    int first = page * per;
    int last = first + per;
    if (last > n) last = n;
    string t = "";
    for (int i = first; i < last; i++) {
        if (i > first) t = t + "\n";
        if (i < nc) t = t + KR_T9CardRow(KR_T9LaneCardAt(m, l, i), m);
        else t = t + KR_T9ChipRow(KR_T9LaneChipAt(m, l, i - nc), false);
    }
    KR_CPBlock("ROWS", "LANE " + ("%d" % m) + " " + ("%d" % l) + " p" + ("%d" % (page + 1)), t);
}
void KR_CPMemRows() {
    int c0 = KR_T9ChipFirst(12);
    int n = KR_T9ChipEnd(12) - c0;
    string t = "";
    for (int i = 0; i < n; i++) {
        if (i > 0) t = t + "\n";
        t = t + KR_T9ChipRow(c0 + i, false);
    }
    KR_CPBlock("ROWS", "MEM", t);
}
int KR_CPPanelN() {
    int n = 0;
    for (int g = 0; g <= 3; g++) n += KR_PlayerEventCount(g);
    return n;
}
// the home panel exactly as the runtime builds it (Codex KR_RateText = r9 KR_T8HomeRateText with one label) and its count
void KR_CPPanel(string tag) {
    KR_CPBlock("PANEL", tag, KR_RateText());
    KR_ClaudeProbeLog("PANELN " + ("%d" % KR_CPPanelN()));
}
int KR_CPExist(string name) {
    return KR_CPB(system.ExistSaveFile(EX_String("Ｅ＿セーブファイル名＿接頭語", "", 0) + name));
}
// r18: the saved state a replay can change, before / after (one key=value per line; the verifier compares them)
void KR_CPState(string tag) {
    string t = "date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay());
    t = t + "\nremain=" + ("%d" % L_Calendar::GetRemainTime());
    t = t + "\nfn=" + LSys3xScript::m_FuncName;
    t = t + "\nsys=" + ("%d" % KR_CPB(LSys3xScript::m_IsSysScenario));
    t = t + "\nevresult=" + ("%d" % g_EvResult);
    t = t + "\ncanret=" + ("%d" % KR_CPB(menu::detail::g_bCanReturnBackSelect));
    t = t + "\nbeginsel=" + ("%d" % KR_CPB(menu::detail::g_bBeginSelect));
    for (int p = 1; p <= 8; p++) t = t + "\nfeel" + ("%d" % p) + "=" + ("%d" % LAbility::m_pAbilities[p - 1].GetFeelingInnerValue());
    t = t + "\nplaymin=" + ("%d" % time::detail::g_PlayMinuteTime);
    t = t + "\nlevel=" + ("%d" % L_GameLevel::m_nLevel);
    string party = "";
    int np = L_Party::m_nPersons.Numof();
    for (int i = 0; i < np; i++) party = party + ("%d," % L_Party::m_nPersons[i]);
    t = t + "\nparty=" + party;
    string flags = "";
    int nf = g_sysFlagList.Numof();
    for (int f = 0; f < nf; f++) flags = flags + ("%d," % g_sysFlagList[f]);
    t = t + "\nsysflags=" + flags;
    string names = "";
    int nn = g_eventNameList.Numof();
    for (int k = 0; k < nn; k++) names = names + g_eventNameList[k] + ",";
    t = t + "\nevnames=" + names;
    string reg = "";
    int nr = N_ScenarioRegister::detail::_EV_TABLE.Numof();
    for (int r = 0; r < nr; r++) reg = reg + N_ScenarioRegister::detail::_EV_TABLE[r] + ",";
    t = t + "\nevtable=" + reg;
    string greg = "";
    int ng = game::detail::_EV_TABLE.Numof();
    for (int q = 0; q < ng; q++) greg = greg + game::detail::_EV_TABLE[q] + ",";
    t = t + "\ngevtable=" + greg;
    t = t + "\npanel=" + ("%d" % KR_CPPanelN());
    t = t + "\nregs=" + KR_CPRegsText();
    t = t + "\ntemp_asd=" + ("%d" % KR_CPExist("KRReplay.asd"));
    t = t + "\ntemp_vsf=" + ("%d" % KR_CPExist("KRReplay.vsf"));
    t = t + "\ntempselect=" + ("%d" % KR_CPExist("TempSelect.asd"));
    t = t + "\nbackselect1=" + ("%d" % KR_CPExist("BackSelect1.asd"));
    t = t + "\nbackselect2=" + ("%d" % KR_CPExist("BackSelect2.asd"));
    t = t + "\nslot90=" + ("%d" % KR_CPExist("90.asd"));
    t = t + "\nt18=" + KR_T18Get("PrevSet") + "|" + KR_T18Get("PrevFn") + "|" + KR_T18Get("PrevSys");
    t = t + "\nt9=" + KR_T9Get("Play") + "|" + KR_T9Get("Playing") + "|" + KR_T9Get("Ctx") + "|" + KR_T9Get("Req") + "|" + KR_T9Get("Unwind");
    t = t + "\nmarker=" + KR_CPGet("Marker");
    KR_CPBlock("STATE", tag, t);
}
// --regs: everything the VM needs for this save, then exit (at the home menu, or at the first click wait)
void KR_CPRegsExit(string where) {
    KR_ClaudeProbeLog(where + " date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()));
    KR_CPRegs();
    KR_CPPanel("REGS");
    int t0 = KR_Time();
    KR_CPBlock("TITLE", "SUMMARY", KR_T18SummaryTitle());
    KR_ClaudeProbeLog("SUMMARY built in " + ("%d" % (KR_Time() - t0)) + " ms");
    KR_ClaudeProbeLog("END");
    system.Exit(0);
}
/*TARGETS*/
int KR_CPPerson() {
    int m = KR_T9NowMonth();
    for (int p = 2; p <= 5; p++) { if (KR_T9LaneCards(m, p - 1) > 0) return p; }
    return 4;
}
// month page navigation: returns true when already on month `want` (12 = 회상 · 그 밖)
bool KR_CPGoto(int want) {
    int m = KR_CPNum("Month");
    if (m > want) { KR_CPSet("Month", "%d" % (m - 1)); KR_CPEnd(11); return false; }
    if (m < want) { KR_CPSet("Month", "%d" % (m + 1)); KR_CPEnd(12); return false; }
    return true;
}
// the first card (months 4-11) whose entry has state st (0 ●, 1 △) and sits on the first page of its lane:
// month * 10000 + lane * 100 + index in the lane, or -1
int KR_CPFindCard(int st) {
    for (int m = 4; m <= 11; m++) {
        for (int l = 0; l <= 8; l++) {
            int n = KR_T9LaneCards(m, l) + KR_T9LaneChips(m, l);
            int per = 10;
            if (n > 10) per = 8;
            int nc = KR_T9LaneCards(m, l);
            for (int i = 0; i < nc && i < per; i++) {
                int k = KR_T9LaneCardAt(m, l, i);
                if (KR_T9State(KR_T9CardEntry(k)) == st) return m * 10000 + l * 100 + i;
            }
        }
    }
    return -1;
}
void KR_CPItems(string tag) {
    KR_ClaudeProbeLog("ITEMS " + tag + " " + SystemService.SystemVariable_Get("YoruKR.CalProbe.Items"));
}
void KR_CalProbeTick() {
    string stage = KR_CPGet("Stage");
    string phase = KR_CPPhase();
    int frames = KR_CPNum("Frames") + 1;
    KR_CPSet("Frames", "%d" % frames);
    if (frames > 2400) { KR_ClaudeProbeLog("STUCK stage=" + stage + " phase=" + phase + " head=" + KR_CPHead()); KR_ClaudeShot("cal_stuck.bmp"); system.Exit(5); return; }
    if (frames < 12) return;
    bool home = SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") == "1";
    // after the sandbox restore / the mid-replay load the files say where we are (session variables may be the saved ones)
    if (phase == "replay") {
        if (!home) { KR_ClaudeProbeLog("UNEXPECTED DIALOG after the replay head=" + KR_CPHead()); KR_ClaudeShot("cal_unexpected.bmp"); system.Exit(7); return; }
        KR_ClaudeProbeLog("BACK TO HOME (sandbox) messages=" + ("%d" % KR_CPMsgs()) + " stage_var=" + stage);
        KR_CPState("AFTER");
        KR_CPPanel("AFTER");
        KR_ClaudeShot("cal_home_after.bmp");
        KR_CPSetPhase("midload");
        KR_ClaudeProbeLog("LOADING slot @@SLOT@@ (saved during the replay)");
        AFL_GameSave_Load(@@SLOT@@);
        KR_ClaudeProbeLog("LOAD RETURNED (should not)");
        system.Exit(10);
        return;
    }
    if (phase == "midload") {
        if (!home) { KR_ClaudeProbeLog("UNEXPECTED DIALOG after the mid-replay load head=" + KR_CPHead()); KR_ClaudeShot("cal_unexpected2.bmp"); system.Exit(7); return; }
        KR_ClaudeProbeLog("BACK TO HOME (mid-replay load) messages=" + ("%d" % KR_CPMsgs()));
        KR_CPState("MIDLOAD");
        KR_CPPanel("MIDLOAD");
        KR_ClaudeShot("cal_home_midload.bmp");
        KR_CPSetPhase("done");
        KR_ClaudeProbeLog("END");
        system.Exit(0);
        return;
    }
    if (stage == "") {
        if (!home) return;
        @@REGS_ONLY@@
        int p = KR_CPPerson();
        KR_ClaudeProbeLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()) + " person=" + ("%d" % p));
        KR_CPRegs();
        KR_CPPanel("HOME");
        KR_CPState("HOME");
        KR_ClaudeShot("cal_home_before.bmp");
        @@SAVEFOLDER_TEST@@
        KR_CPSet("Person", "%d" % p);
        KR_CPSet("Stage", "charwin");
        KR_CPSet("Frames", "0");
        KR_T8HomeClick(0, 40, 52 + (p + 5) * 24 + 6);
        KR_ClaudeProbeLog("clicked row " + ("%d" % (p + 5)) + " pick=" + SystemService.SystemVariable_Get("YoruKR.T8.HomePick") + " ctx=" + SystemService.SystemVariable_Get("YoruKR.T9.Ctx"));
        return;
    }
    if (stage == "charwin") {
        if (KR_CPTitle() == "") return;
        KR_ClaudeProbeLog("CHARWIN head=" + KR_CPHead() + " ctx=" + SystemService.SystemVariable_Get("YoruKR.T9.Ctx"));
        KR_ClaudeShot("cal_charwin.bmp");
        KR_CPSet("Stage", "lane1");
        KR_CPEnd(3);
        return;
    }
    if (stage == "lane1") {
        int lm = KR_T9NowMonth();
        int ll = KR_CPNum("Person") - 1;
        KR_CPTitleLog("LANE " + ("%d" % lm) + " " + ("%d" % ll));
        KR_CPLaneRows(lm, ll, 0);
        KR_ClaudeShot("cal_lane.bmp");
        KR_CPSet("Stage", "month");
        KR_CPSet("Month", "%d" % lm);
        KR_CPEnd(0);
        return;
    }
    if (stage == "month") {
        KR_CPTitleLog("MONTH " + KR_CPGet("Month"));
        KR_ClaudeShot("cal_month.bmp");
        KR_CPSet("T0", "%d" % KR_Time());
        KR_CPSet("Stage", "summary");
        KR_CPEnd(31);
        return;
    }
    if (stage == "summary") {
        KR_ClaudeProbeLog("SUMMARY opened after " + ("%d" % (KR_Time() - KR_CPNum("T0"))) + " ms (click to shown, incl. building the title)");
        KR_CPTitleLog("SUMMARY");
        KR_CPPanel("SUMMARY");
        KR_ClaudeShot("cal_summary.bmp");
        KR_CPSet("Stage", "monthback");
        KR_CPSet("T1", "%d" % KR_Time());
        KR_CPEnd(0);
        return;
    }
    if (stage == "monthback") {
        KR_ClaudeProbeLog("MONTH page back after " + ("%d" % (KR_Time() - KR_CPNum("T1"))) + " ms (click to shown, incl. building the title)");
        KR_CPTitleLog("MONTH " + KR_CPGet("Month") + " back");
        KR_ClaudeShot("cal_month_back.bmp");
        KR_CPSet("Stage", "tosep");
        KR_CPSet("Frames", "0");
        return;
    }
    if (stage == "tosep") {
        if (!KR_CPGoto(9)) return;
        KR_CPTitleLog("MONTH 9");
        KR_ClaudeShot("cal_month_sep_3col.bmp");
        KR_CPSet("Stage", "tooct");
        KR_CPSet("Frames", "0");
        return;
    }
    if (stage == "tooct") {
        if (!KR_CPGoto(10)) return;
        KR_CPTitleLog("MONTH 10");
        KR_CPSet("Stage", "oct1");
        KR_CPEnd(20 + @@MANAMI@@);
        return;
    }
    if (stage == "oct1") {
        KR_CPTitleLog("LANE 10 @@MANAMI@@ p1");
        KR_CPLaneRows(10, @@MANAMI@@, 0);
        KR_ClaudeShot("cal_lane_oct_manami_p1.bmp");
        KR_CPSet("Stage", "oct2");
        KR_CPEnd(12);
        return;
    }
    if (stage == "oct2") {
        KR_CPTitleLog("LANE 10 @@MANAMI@@ p2");
        KR_CPLaneRows(10, @@MANAMI@@, 1);
        KR_ClaudeShot("cal_lane_oct_manami_p2.bmp");
        KR_CPSet("Stage", "tomem");
        KR_CPEnd(0);
        return;
    }
    if (stage == "tomem") {
        if (!KR_CPGoto(12)) return;
        KR_CPTitleLog("MEM");
        KR_CPMemRows();
        KR_ClaudeShot("cal_memory.bmp");
        KR_CPSet("Stage", "toapr");
        KR_CPSet("Month", "11");
        KR_CPEnd(11);
        return;
    }
    if (stage == "toapr") {
        if (!KR_CPGoto(4)) return;
        KR_CPSet("Stage", "aprdun");
        KR_CPEnd(20 + @@DUNGEON@@);
        return;
    }
    if (stage == "aprdun") {
        KR_CPTitleLog("LANE 4 @@DUNGEON@@");
        KR_CPLaneRows(4, @@DUNGEON@@, 0);
        KR_ClaudeShot("cal_lane_apr_dungeon.bmp");
        KR_CPSet("Stage", "lock");
        KR_CPSet("LockSt", "0");
        KR_CPEnd(0);
        return;
    }
    // ---- r18 lock pages: the first ● card, then the first △ card (when the save has one)
    if (stage == "lock") {
        int st = KR_CPNum("LockSt");
        if (KR_CPGet("LockAt") == "") {
            int at = KR_CPFindCard(st);
            KR_ClaudeProbeLog("LOCK FIND state=" + ("%d" % st) + " at=" + ("%d" % at));
            if (at < 0) {
                if (st == 0) { KR_CPSet("LockSt", "1"); return; }
                KR_CPSet("Stage", "sbx");
                KR_CPSet("Frames", "0");
                return;
            }
            KR_CPSet("LockAt", "%d" % at);
        }
        int at2 = KR_CPNum("LockAt");
        if (!KR_CPGoto(at2 / 10000)) return;
        KR_CPSet("Stage", "locklane");
        KR_CPEnd(20 + (at2 / 100) % 100);
        return;
    }
    if (stage == "locklane") {
        KR_CPSet("Stage", "lockcard");
        KR_CPEnd(100 + KR_CPNum("LockAt") % 100);
        return;
    }
    if (stage == "lockcard") {
        int st2 = KR_CPNum("LockSt");
        int at3 = KR_CPNum("LockAt");
        int k = KR_T9LaneCardAt(at3 / 10000, (at3 / 100) % 100, at3 % 100);
        KR_CPTitleLog("LOCKCARD " + ("%d" % st2) + " " + ("%d" % k) + " " + ("%d" % (at3 / 10000)));
        KR_ClaudeProbeLog("LOCKCARD entry=" + ("%d" % KR_T9CardEntry(k)) + " state=" + ("%d" % KR_T9State(KR_T9CardEntry(k))) + " size=" + ("%d" % KR_T9CardSize(k)));
        if (st2 == 0) KR_ClaudeShot("cal_card_locked_unseen.bmp");
        else KR_ClaudeShot("cal_card_locked_other.bmp");
        KR_CPSet("Stage", "lockback");
        KR_CPEnd(13);
        return;
    }
    if (stage == "lockback") {
        // the answer 13 on a locked card: no request; KR_T18CardPage returns to the lane page -> 돌아가기 to the month page
        KR_ClaudeProbeLog("LOCK AFTER 13 head=" + KR_CPHead() + " play=" + KR_T9Get("Play") + " unwind=" + KR_T9Get("Unwind") + " prevset=" + KR_T18Get("PrevSet"));
        int st3 = KR_CPNum("LockSt");
        KR_CPSet("LockAt", "");
        if (st3 == 0) { KR_CPSet("LockSt", "1"); KR_CPSet("Stage", "lock"); }
        else KR_CPSet("Stage", "sbx");
        KR_CPEnd(0);
        return;
    }
    // ---- r18 sandbox: target card -> 단계 고르기 -> stage -> scene page -> 이 장면 재생
    if (stage == "sbx") {
        if (!KR_CPGoto(@@T_MONTH@@)) return;
        KR_CPSet("Stage", "sbxlane");
        KR_CPEnd(20 + @@T_LANE@@);
        return;
    }
    if (stage == "sbxlane") {
        KR_ClaudeProbeLog("SBX LANE head=" + KR_CPHead());
        KR_CPSet("Stage", "sbxcard");
        KR_CPEnd(100 + @@T_INDEX@@);
        return;
    }
    if (stage == "sbxcard") {
        int k2 = KR_T9LaneCardAt(@@T_MONTH@@, @@T_LANE@@, @@T_INDEX@@);
        KR_CPTitleLog("OPENCARD " + ("%d" % k2) + " @@T_MONTH@@");
        KR_ClaudeProbeLog("SBX CARD entry=" + ("%d" % KR_T9CardEntry(k2)) + " state=" + ("%d" % KR_T9State(KR_T9CardEntry(k2))) + " size=" + ("%d" % KR_T9CardSize(k2)));
        KR_ClaudeShot("cal_card_open.bmp");
        if (@@T_STAGE@@ == 0) {
            KR_CPSet("Stage", "sbxevent0");
            KR_CPSet("Marker", "before-save");
            KR_CPState("PREPLAY");
            KR_CPSetPhase("replay");
            KR_CPEnd(13);
            return;
        }
        KR_CPSet("Stage", "sbxstages");
        KR_CPEnd(14);
        return;
    }
    if (stage == "sbxstages") {
        KR_CPTitleLog("STAGES");
        KR_CPSet("Stage", "sbxevent");
        KR_CPEnd(100 + @@T_STAGE@@);
        return;
    }
    if (stage == "sbxevent") {
        KR_CPTitleLog("OPENEVENT @@T_EVENT@@");
        KR_ClaudeProbeLog("SBX EVENT seen_before=" + ("%d" % KR_CPB(KR_T9Seen(@@T_EVENT@@))) + " state=" + ("%d" % KR_T9State(@@T_EVENT@@)));
        KR_ClaudeShot("cal_event_open.bmp");
        KR_CPSet("Marker", "before-save");
        KR_CPState("PREPLAY");
        KR_CPSetPhase("replay");
        KR_CPSet("Stage", "replay");
        KR_CPEnd(13);
        return;
    }
    if (stage == "replay") {
        KR_ClaudeProbeLog("UNEXPECTED DIALOG during the replay stage head=" + KR_CPHead());
        KR_ClaudeShot("cal_unexpected3.bmp");
        system.Exit(7);
    }
}
int KR_CalProbeMsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    @@WAIT_REGS@@
    int n = KR_CPMsgs() + 1;
    TextFile.WriteAll("claude_probe_msgs.txt", "%d" % n);
    string phase = KR_CPPhase();
    if (phase != "replay" && phase != "midload") { KR_ClaudeProbeLog("MESSAGE WAIT outside the replay phase=" + phase); KR_ClaudeShot("cal_msg_unexpected.bmp"); system.Exit(8); return 0; }
    if (n == 1) {
        KR_ClaudeProbeLog("REPLAY first message; casual site Play=" + KR_T9Get("Play") + " playing=" + KR_T9Get("Playing"));
        KR_CPSet("Marker", "during-replay");
        KR_CPState("MIDREPLAY");
    }
    if (n <= 2) KR_ClaudeShot("cal_spoiler_replay_msg_" + ("%d" % n) + ".bmp");
    if (n == 2) {
        bool saved = AFL_GameSave_Save(@@SLOT@@, "");
        if (saved) KR_ClaudeProbeLog("MIDSAVE saved slot @@SLOT@@ (fresh path) exist=" + ("%d" % KR_CPExist("@@SLOT@@.asd")));
        else KR_ClaudeProbeLog("MIDSAVE resumed (slot @@SLOT@@ loaded) phase=" + KR_CPPhase() + " marker=" + KR_CPGet("Marker"));
    }
    if (n > 600) { KR_ClaudeProbeLog("TOO MANY MESSAGES"); system.Exit(8); return 0; }
    return 0;
}
int KR_CalProbeWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    @@WAIT_REGS@@
    KR_ClaudeProbeLog("UNEXPECTED WAIT stage=" + KR_CPGet("Stage") + " phase=" + KR_CPPhase() + " head=" + KR_CPHead());
    KR_ClaudeShot("cal_wait.bmp");
    system.Exit(6);
    return 0;
}
// the save to resume comes from run\claude_probe_args.txt (one probe build serves every save of a --regs pass)
string KR_CPArgSave() {
    string s = KR_CPRead("claude_probe_args.txt");
    int nl = s.Find("\n");
    if (nl > 0) s = KR_JosaSlice(s, 0, nl);
    return s;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("SAVEFOLDER " + system.GetSaveFolderName());
    @@WHERE@@
    string save = KR_CPArgSave();
    if (save == "") { KR_ClaudeProbeLog("NO SAVE ARGUMENT"); system.Exit(3); return 3; }
    KR_ClaudeProbeLog("resume loading " + save);
    system.ResumeLoad("@@KEY@@", save);
    system.Exit(2);
    return 2;
}
'''


def expectations():
    import verify_calendar_r18 as V
    return V.expectations()


REPLAY_CANDIDATES = [273, 20165, 30154, 324, 20083]     # scenes that raise an affinity (graph/schedule.json effects.affection)


def sandbox_target(X, regs):
    """The replay target: a scene seen in this save (○) that raises an affinity, with no choice / battle / chain, reachable
    as card (first lane page) -> 단계 고르기 -> stage. Returns (month, lane, index in lane, stage index or 0, event)."""
    sch = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    evs = {e['id']: e for e in sch['events']}
    for no in REPLAY_CANDIDATES:
        e = evs[no]
        if no not in regs or e['has_choice'] or e['effects']['event_battle'] or e['chains_to'] or not e['effects']['affection']:
            continue
        for c in X['cards']:
            if no in c['stages']:
                same = [x for x in X['cards'] if x['month'] == c['month'] and x['lane'] == c['lane']]
                idx = [x['key'] for x in same].index(c['key'])
                n = len(same) + sum(1 for ch in X['chips'] if ch['month'] == c['month'] and ch['lane'] == c['lane'])
                per = 10 if n <= 10 else 8
                if idx < per and c['stages'].index(no) < 30:
                    return dict(month=c['month'], lane=c['lane'], index=idx, stage=c['stages'].index(no), event=no, entry=c['entry'],
                                size=c['size'], messages=e['messages']['count'], affection=e['effects']['affection'])
    raise AssertionError('no replay target registered in this save')


def target_jaf(t):
    return ''


def build_probe(source, key, work, mode, target):
    src = source / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@KEY@@', key).replace('/*TARGETS*/', '')
    jaf = jaf.replace('@@MANAMI@@', str(MANAMI)).replace('@@DUNGEON@@', str(DUNGEON)).replace('@@SLOT@@', str(MIDSAVE_SLOT))
    t = target or dict(month=4, lane=0, index=0, stage=0, event=0)
    jaf = (jaf.replace('@@T_MONTH@@', str(t['month'])).replace('@@T_LANE@@', str(t['lane'])).replace('@@T_INDEX@@', str(t['index']))
           .replace('@@T_STAGE@@', str(t['stage'])).replace('@@T_EVENT@@', str(t['event'])))
    jaf = jaf.replace('@@REGS_ONLY@@', 'KR_CPRegsExit("HOME"); return;' if mode == 'regs' else '')
    jaf = jaf.replace('@@WAIT_REGS@@', 'if (KR_CPGet("Stage") == "") { KR_CPRegsExit("WAIT"); return 0; }' if mode == 'regs' else '')
    jaf = jaf.replace('@@SAVEFOLDER_TEST@@', 'KR_ClaudeProbeLog("END"); system.Exit(0); return;' if mode == 'savefolder' else '')
    jaf = jaf.replace('@@WHERE@@', 'KR_ClaudeProbeLog("END"); system.Exit(0); return 0;' if mode == 'where' else '')
    assert '@@' not in jaf, re.findall(r'@@\w+@@', jaf)
    jaf = L.jaf_literal_encode(jaf)
    (work / 'probe.jaf').write_text(jaf, 'utf8')
    decl = work / 'probe_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'probe.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'probe_declared_meta.json', decl)
    dm = L.read_meta(work / 'probe_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    # Codex diagnostic_audio_20260923: mute and no user input (probe only)
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    patch += [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]
    for f in added:
        path = work / f"probe_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), f['name']))
    upd = L.fid_of(m, 'C_SelectDialog@_Update')
    path = work / f'original_{upd}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SelectDialog@_Update', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SelectDialog@_Update'), '\tCALLFUNC KR_CalProbeTick\n'))
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_ClaudeProbeMain'])
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
                if name == 'C_SelectDialog@Run':
                    waits.append((name, 'live'))
                    continue
                target_fid = ids['KR_CalProbeMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_CalProbeWait']
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, target_fid)
                waits.append((name, 'message click-through' if target_fid == ids['KR_CalProbeMsgWait'] else 'exit'))
    assert sum(1 for _, k in waits if k == 'live') == 1 and sum(1 for _, k in waits if k.startswith('message')) == 1, waits
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(waits=waits, target=target, tick_prefix='C_SelectDialog@_Update', probe_sha256=L.sha(out))


def setup_folder():
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
    for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex']:          # PACT/EX are the runtime's (r18 does not change them)
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
    return rt


def set_savefolder(savename):
    ini = (RUN / 'AliceStart.ini').read_bytes()
    folder = b'SaveFolder\t= "' + savename.encode('cp932') + b'"'
    ini = re.sub(rb'SaveFolder\t= "[^"]*"', lambda z: folder, ini)
    assert folder in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    # mainsystem::CSaveFolderSetting reads InstallInfo\SaveFolderSetting.ini: "SFSF", int32 0, int32 type (0 Documents,
    # 1 another shell folder, 2 the folder the engine holds itself); type 2 keeps the probe's saves inside run\ on P:.
    (RUN / 'InstallInfo').mkdir(exist_ok=True)
    (RUN / 'InstallInfo' / 'SaveFolderSetting.ini').write_bytes(b'SFSF' + struct.pack('<ii', 0, SAVE_TYPE))
    for n in ['claude_probe.txt', 'claude_probe_phase.txt', 'claude_probe_msgs.txt']:
        if (RUN / n).exists():
            (RUN / n).unlink()
    for b in RUN.glob('cal_*.bmp'):
        b.unlink()


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
    """09-24 probe launcher (probe_claude_term_rate_20260924.launch): hidden window, debugger on, MessageBoxA and the VM
    error handler break-pointed so engine errors are captured instead of waiting on a dialog. TEMP/TMP point to P:."""
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


def tree_listing(root):
    out = {}
    if root.exists():
        for p in root.rglob('*'):
            try:
                st = p.stat()
                out[str(p.relative_to(root))] = (st.st_size, int(st.st_mtime))
            except OSError:
                pass
    return out


def home_saves():
    out = []
    for name, p in L.save_slots().items():
        r = L.save_records(p)
        names = [x['name'].split('(')[0] for x in [r['ip']] + r['returns'] if x['address'] != -1]
        if 'C_SceneHomebase@CheckGameSysButtons' in names:
            out.append((p.stat().st_mtime, name))
    return [n for _, n in sorted(out)]


def user_state():
    return {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}


def user_game_running():
    """The user's own game (the runtime exe) — the user may be playing while the isolated probe runs; its saves then change
    the user's folder (never the probe: the probe's save folder is inside run/, logged by the probe as SAVEFOLDER)."""
    import subprocess
    cmd = ("@(Get-CimInstance Win32_Process -Filter \"Name = 'NightRemaster.exe'\" | Select-Object ProcessId,ExecutablePath) | ConvertTo-Json -Compress")
    q = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, timeout=60, env=L.env())
    s = q.stdout.decode('utf-8-sig').strip()
    rows = json.loads(s) if s else []
    rows = rows if isinstance(rows, list) else [rows]
    rt = L.runtime()[1].resolve()
    return [r for r in rows if r.get('ExecutablePath') and Path(r['ExecutablePath']).resolve().parent == rt]


def probe_folder_ok(results):
    """Every run logged a save folder inside run/ (the probe never saves into the user's folder)."""
    ok = True
    for r in results:
        sf = next((l[len('SAVEFOLDER '):] for l in r['log'] if l.startswith('SAVEFOLDER ')), None)
        ok = ok and sf is not None and Path(sf).resolve().is_relative_to(RUN.resolve())
    return ok


def run_one(save, mode, info_builder, stamp):
    """Copy the save + global files into a fresh P: save folder inside run\\, launch, collect log and screenshots."""
    savename = f'SaveData_R18CalendarProbe_{stamp}'
    savedir = RUN / savename
    set_savefolder(savename)
    if mode != 'where':
        savedir.mkdir(parents=True)
        for n in COPY_GLOBAL:
            files = L.save_manifest()['files']
            if n in files:
                shutil.copy2(L.save_path(n), savedir / n)
        shutil.copy2(L.save_path(save), savedir / save)
    (RUN / 'claude_probe_args.txt').write_bytes(save.encode('cp932') + b'\n')
    t0 = time.time()
    result = launch(timeout=60 if mode == 'where' else (240 if mode in ('savefolder', 'regs') else 900))
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result.update(save=save, save_folder=str(savedir))
    result['probe_save_folder_files'] = sorted(p.name for p in savedir.iterdir()) if savedir.exists() else []
    return result


def blocks(log):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'(TITLE|ROWS|PANEL|STATE) (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            out[(z.group(1), z.group(2))] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    return out


def parse_state(text):
    out = {}
    for line in text.split('\n'):
        k, _, v = line.partition('=')
        out[k] = v
    return out


def parse_regs(log):
    home = next((l for l in log if re.match(r'(HOME|WAIT) date=', l)), None)
    regs = next((l for l in log if l.startswith('REGS')), None)
    if not home or regs is None:
        return None
    z = re.match(r'(HOME|WAIT) date=(\d+)/(\d+) now=(\d+)', home)
    b = blocks(log)
    pn = next((int(l.split()[1]) for l in log if l.startswith('PANELN ')), None)
    panel = next((t for (k, tag), t in b.items() if k == 'PANEL'), None)
    return dict(at='home' if z[1] == 'HOME' else 'wait', today=[int(z[2]), int(z[3])], now=int(z[4]),
                regs=sorted(int(x) for x in regs.split()[1:]), panel=panel, panel_count=pn,
                summary=b.get(('TITLE', 'SUMMARY')))


def diff_pixels(a, b):
    from PIL import Image, ImageChops
    ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    diff = ImageChops.difference(ia, ib)
    data = diff.get_flattened_data() if hasattr(diff, 'get_flattened_data') else diff.getdata()
    return dict(size=list(ia.size), differing_pixels=sum(1 for px in data if px != (0, 0, 0)), bbox=diff.getbbox())


# ---- r18 state comparison (the same allow list as the VM's V17, stated on the native keys)
ALLOWED_NATIVE = {
    'canret': 'the game\'s own post-load branch sets g_bCanReturnBackSelect = 0 on every load',
    'tempselect': 'the game\'s own post-load branch deletes TempSelect (back-to-choice copy) on every load',
    'backselect1': 'the game\'s own post-load branch deletes BackSelect1 on every load',
    'backselect2': 'the game\'s own post-load branch deletes BackSelect2 on every load',
    'marker': 'the probe\'s own session variable (shows whether SystemService restores session variables)',
    't9': 'calendar session variables (UI flow)', 't18': 'calendar session variables (UI flow)',
    'slot90': 'the probe\'s own mid-replay save file',
}


def compare_states(a, b, allowed=ALLOWED_NATIVE):
    out = {}
    for k in sorted(set(a) | set(b)):
        if a.get(k) == b.get(k):
            continue
        if k == 'playmin' and a.get(k, '').lstrip('-').isdigit() and b.get(k, '').lstrip('-').isdigit() and abs(int(a[k]) - int(b[k])) <= 1:
            continue
        if k in allowed:
            continue
        out[k] = (a.get(k, '')[:120], b.get(k, '')[:120])
    return out


def sandbox_report(log):
    b = blocks(log)
    st = {tag: parse_state(t) for (kind, tag), t in b.items() if kind == 'STATE'}
    rep = dict(states=sorted(st))
    if 'HOME' in st and 'AFTER' in st:
        rep['home_vs_after'] = compare_states(st['HOME'], st['AFTER'])
        rep['home_vs_after_allowed'] = {k: (st['HOME'].get(k), st['AFTER'].get(k)) for k in ALLOWED_NATIVE
                                        if st['HOME'].get(k) != st['AFTER'].get(k)}
        rep['after_temp_files'] = [st['AFTER'].get('temp_asd'), st['AFTER'].get('temp_vsf')]
    if 'HOME' in st and 'PREPLAY' in st:
        rep['home_vs_preplay'] = compare_states(st['HOME'], st['PREPLAY'])
    if 'MIDREPLAY' in st:
        rep['midreplay_temp_files'] = [st['MIDREPLAY'].get('temp_asd'), st['MIDREPLAY'].get('temp_vsf')]
        rep['midreplay_marker'] = st['MIDREPLAY'].get('marker')
    if 'AFTER' in st:
        rep['session_variables_restored_by_resumeload'] = st['AFTER'].get('marker') == 'before-save'
        rep['after_marker'] = st['AFTER'].get('marker')
    if 'HOME' in st and 'MIDLOAD' in st:
        rep['home_vs_midload'] = compare_states(st['HOME'], st['MIDLOAD'])
        rep['midload_temp_files'] = [st['MIDLOAD'].get('temp_asd'), st['MIDLOAD'].get('temp_vsf')]
    for tag in ('HOME', 'PREPLAY', 'MIDREPLAY', 'AFTER', 'MIDLOAD'):
        if tag in st:
            rep.setdefault('feel', {})[tag] = [int(st[tag].get('feel%d' % p, '0') or 0) for p in range(1, 9)]
            rep.setdefault('date', {})[tag] = st[tag].get('date')
            rep.setdefault('panel', {})[tag] = st[tag].get('panel')
            rep.setdefault('regs_count', {})[tag] = len(st[tag].get('regs', '').split())
            rep.setdefault('fn', {})[tag] = st[tag].get('fn')
    return rep


def main():
    mode = 'full'
    if '--savefolder-test' in sys.argv:
        mode = 'savefolder'
    elif '--where' in sys.argv:
        mode = 'where'
    elif '--regs' in sys.argv:
        mode = 'regs'
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ptr, rt = L.runtime()
    assert L.sha(rt / 'NightRemaster.ain') == L.BASE_AIN_SHA, 'runtime moved since the candidate was built'
    man = L.readj(O / 'manifest.json')
    assert L.sha(O / 'NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    if mode == 'regs':
        saves = args or home_saves()
    elif args:
        saves = args[:1]
    elif (L.WORK / 'probe_pick.json').exists():
        saves = [L.readj(L.WORK / 'probe_pick.json')['save']]
    else:
        saves = home_saves()[-1:]
    stamp0 = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    work = PROBE / f'build_{stamp0}_{mode}'
    work.mkdir(parents=True)
    user_before = user_state()
    alice_dir = L.SAVES.parent
    alice_before = tree_listing(alice_dir)
    playing_before = user_game_running()
    import verify_calendar_r18 as V
    X = V.expectations()
    target = None
    if mode == 'full':
        regs_doc = L.readj(L.EVID / 'probe_regs.json')
        row = next(s for s in regs_doc['saves'] if s['save'] == saves[0] and s.get('state'))
        target = sandbox_target(X, set(row['state']['regs']))
        print('sandbox target', target, flush=True)
    rt = setup_folder()
    results = []
    keys = {L.save_records(L.save_path(s))['key'] for s in saves}
    assert len(keys) == 1, 'saves with different resume keys'
    info = build_probe(O, keys.pop(), work, mode, target)
    for i, save in enumerate(saves):
        (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=man['files']['NightRemaster.ain']['sha256'],
            probe_sha256=info['probe_sha256'], audio=AUDIO_POLICY, save=save, mode=mode, author=L.AUTHOR,
            input='Resume of a copied home-base save; user input patched off; dialogs answered by KR_CalProbeTick.'), ensure_ascii=False, indent=1), 'utf8')
        r = run_one(save, mode, info, f'{stamp0}_{i:02d}')
        r.update(probe_sha256=info['probe_sha256'], candidate_sha256=man['files']['NightRemaster.ain']['sha256'], mode=mode)
        if mode == 'regs':
            r['state'] = parse_regs(r['log'])
            r['log'] = [l for l in r['log'] if not l.startswith('REGS')]
            st = r['state']
            print(save, r.get('exit_code'), r['seconds'], st and (st['at'], st['today'], len(st['regs']), st['panel_count']), flush=True)
        results.append(r)
    user_after = user_state()
    playing_after = user_game_running()
    changed = sorted(k for k in set(user_before) | set(user_after) if user_before.get(k) != user_after.get(k))
    common = dict(user_save_folder_unchanged=user_after == user_before, user_save_files=len(user_before),
                  user_save_folder_changed_files=changed, user_game_running=dict(before=playing_before, after=playing_after),
                  probe_save_folder_inside_run=probe_folder_ok(results),
                  c_drive_alicesoft_changes=sorted(set(tree_listing(alice_dir).items()) ^ set(alice_before.items()))[:20],
                  run_folder_new_dirs=sorted(p.name for p in RUN.iterdir() if p.is_dir()), waits=info['waits'] if info else None,
                  target=info['target'] if info else None)
    if mode == 'regs':
        out = dict(common, saves=results, schema='yoru-calendar-r18.probe-regs.v1', author=L.AUTHOR)
        L.writej(L.EVID / 'probe_regs.json', out)
        print(json.dumps({k: v for k, v in out.items() if k not in ('saves', 'waits')}, ensure_ascii=False, indent=1))
        assert out['probe_save_folder_inside_run'], 'a probe run saved outside run'
        assert out['user_save_folder_unchanged'] or (playing_before or playing_after), 'user save folder changed while the user game was not running'
        return
    result = dict(results[0], **common)
    shots = []
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    for b in sorted(RUN.glob('cal_*.bmp')):
        png = dest / (b.stem + ('_savefoldertest' if mode == 'savefolder' else '') + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    result['screenshots'] = shots
    if mode == 'full':
        result['state'] = parse_regs(result['log'])
        result['log'] = [l for l in result['log'] if not l.startswith('REGS')]
        a, b = dest / 'cal_home_before.png', dest / 'cal_home_after.png'
        if a.exists() and b.exists():
            result['home_before_after'] = diff_pixels(a, b)
        a2 = dest / 'cal_home_midload.png'
        if a.exists() and a2.exists():
            result['home_before_midload'] = diff_pixels(a, a2)
        a, b = dest / 'cal_month.png', dest / 'cal_month_back.png'
        if a.exists() and b.exists():
            result['month_before_after_summary'] = diff_pixels(a, b)
        result['sandbox'] = sandbox_report(result['log'])
        savedir = Path(result['save_folder'])
        result['sandbox']['files_at_end'] = sorted(p.name for p in savedir.iterdir()) if savedir.exists() else []
        result['sandbox']['temp_file_on_disk_at_end'] = [n for n in result['sandbox']['files_at_end'] if 'KRReplay' in n]
    name = {'where': 'probe_where.json', 'savefolder': 'probe_savefolder_test.json'}.get(mode, 'probe_result.json')
    L.writej(L.EVID / name, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('waits', 'log')}, ensure_ascii=False, indent=1))
    assert result['probe_save_folder_inside_run'], 'the probe saved outside run'
    assert result['user_save_folder_unchanged'] or (playing_before or playing_after), 'user save folder changed while the user game was not running'


if __name__ == '__main__':
    main()
