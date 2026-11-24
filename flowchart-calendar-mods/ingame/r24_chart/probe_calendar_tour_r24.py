# Claude Opus 5.5 (2026-09-28) r24: r23 probe_calendar_tour_r23.py run on the r24 chart candidate (only the lib and the probe
# save-folder name changed): the calendar tour (r19 · r20 · r23 steps) and --regs are the native evidence that r24 leaves them.
"""Claude Opus 5.5 (2026-09-28) r23: the calendar tour (and --regs) of r22's probe_calendar_tour_r22.py, run on the r23 FEELING
candidate, with the r23 stages: the moon text on the hover preview (page 0) and page 1 of two heroines, none for a man, page 4 of
both heroines (the affinity block, panel / text size), the dungeon status window's page 1 and page 4, no moon text left after the
member screen / the dungeon window; --regs logs, per person, the game's own GetFeeling / GetFeelingRank_5 / game mode and r23's
texts (KR_T23MoonText, KR_T23StText) for the verifier (V54). Everything else as in r22:
--- r22's text follows ---
Claude Opus 5.5 (2026-09-28) r22: the r20 calendar tour (and --regs) of r21's probe_modmenu_r21.py, run on the r22 CHART candidate
(copied here: only the lib, the probe folder probe_cal/, the boot name and the verifier module name changed). r22 forwards
KR_T9Seen / KR_T9State / KR_T9Legend / KR_T18CardPage / KR_T18EventPage through the chart's KR_C* bodies (chart mode off in the
calendar): this tour is the native evidence that the in-game calendar, the r18 lock and the sandbox replay are unchanged.
Use:  python probe_calendar_tour_r22.py --regs   then   python probe_calendar_tour_r22.py     (not --r21 / --integrated)
--- r21's text follows ---
Claude Opus 5.5 (2026-09-28) r21: isolated, muted native probes of the mod-menu candidate (a copy of probe_calendar_r20.py
with the r21 tour added; every r20 mode runs unchanged on the r21 candidate).

  python probe_modmenu_r21.py --r21             r21 tour (2 runs, one copied home save, one P: save folder): paths and the
                                                file-API conventions, poll cost, home-menu frame time armed / disarmed, the five
                                                commands and an unknown one written by the probe exactly as the hook writes them,
                                                last_result, own window / character window not polled, reset_all 예 -> exit
                                                (run A), then the flag after the restart, unlock_revert, reset_restore 예 -> exit
                                                (run B). 증거/probe_r21.json + 증거/probe/mod_*.png
  python probe_modmenu_r21.py --integrated      r21 + the REAL mod-menu hook (hook_modmenu build_diagnostic winmm.dll in the
                                                probe copy only; the runtime's DLL kept and put back): menu commands posted to the
                                                game window (WM_INITMENU, WM_COMMAND 0x7E10..), the hook's MessageBox answered,
                                                reset_all -> exit -> restart -> the hook's backup / delete -> last_result window ->
                                                reset_restore -> exit -> restart -> restore. 증거/integrated/
  python probe_modmenu_r21.py [SAVE]            r20's full probe on the r21 candidate (home: r20 status stages, the r19 tour,
                                                the sandbox; partner selection; dungeon) - the regression tour through the r21
                                                home-menu path (KR_T9HomeMenuRun -> KR_MHomeRun) and the r21 frame tick
  python probe_modmenu_r21.py --regs SAVE ...   per save: date, registrations, panel, summary and the r20 texts (the VM's real
                                                save checks read 증거/probe_regs.json)

Everything lives under r21_modmenu/probe/ on P: (run/ = a copy of the runtime folder with the big assets hard-linked read
only, InstallInfo/SaveFolderSetting.ini type 2 so the saves stay inside run/). The user's save folder is only read; its
hashes are compared. The probe AIN = candidate + probe-only code (never shipped).

r20 description (still true for the r20 modes):
r20 adds two screens: the status window's 「이벤트」 page (home 파티 편성 -> 스테이터스) and the Saturday training partner
selection (labels over the portraits). The r19 tour, lock pages and sandbox replay run unchanged after the r20 home stages.

  python probe_calendar_r20.py [SAVE]              full probe: run 1 = home save (r20 status stages, then the r19 tour and
                                                   sandbox), run 2 = a Saturday partner-select save (NightR40.asd)
  python probe_calendar_r20.py --regs SAVE ...     per save: date, registrations, panel, summary AND the r20 texts
                                                   (KR_T20StText(1..8), KR_T20TrText(2..8)) for the VM comparison

r19 description (still true):

  python probe_calendar_r19.py [SAVE]              full probe (default: work/probe_pick.json, else the newest home-base save copy)
  python probe_calendar_r19.py --regs SAVE ...     per save: resume, log today's date, every calendar event registered in that
                                                   save, the home panel text (KR_RateText), Σ KR_PlayerEventCount(0..3) and the
                                                   summary title (KR_T18SummaryTitle) (증거/probe_regs.json), exit
  python probe_calendar_r19.py --savefolder-test   only: resume + home menu screenshot + exit (checks the P: save folder)

Everything lives under r19_calendar\\probe\\ on P:
  run\\           a copy of the runtime folder: exe/dll/ini/Data/PACT/EX copied, CG/Font/Sound/Voice/Movie hard-linked from the
                 RUNTIME (read-only assets), AliceStart.ini BootName = probe name, InstallInfo\\SaveFolderSetting.ini type 2
                 (saves inside run\\ on P:); the sandbox's temp file and the probe's mid-replay save land there too.
  run\\SaveData_R24CalTourProbe_<stamp>\\  global record files + one save, COPIES (r21lib.save_path). The user's save folder is
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
  r19 names: a dungeon card [shot cal_card_dungeon, TITLE] -> 단계 고르기 [shot cal_stages_dungeon, TITLE, ROWS] -> back;
  a dungeon-walk drawer (마나미 레인) [shot cal_drawer_walk, TITLE, ROWS] -> a scene with a partner [shot cal_scene_walk, TITLE]
  -> back; an after-training drawer [shot cal_drawer_after, TITLE, ROWS] -> its first scene [shot cal_scene_after, TITLE] -> back
  r18 lock: the first ● card (months 4-11) -> its card page [shot cal_card_locked_unseen, TITLE, ITEMS] -> back; the first △
  card if the save has one [shot cal_card_locked_other]
  r18 sandbox: the target card (a scene seen in this save that raises an affinity) -> card page [shot] -> 단계 고르기 ->
  stage -> scene page [shot, TITLE, ITEMS, STATE PREPLAY] -> 이 장면 재생 -> (all windows close, home menu returns 3, casual
  site -> KR_T18RunSandboxed: temp resume save, RunEvent) [message 1: shot spoiler, STATE MIDREPLAY; message 2: shot spoiler,
  mid-replay save to slot 90] -> ロード実行 of the temp file -> home [shot cal_home_after, STATE AFTER, PANEL] -> load slot 90
  (gamesave::detail::Load) -> the rest of the scene -> home [shot cal_home_midload, STATE MIDLOAD, PANEL]: END.
Every page title, lane-row list, stage list and drawer scene list is logged for the offline comparison
(verify_calendar_r20.py --native).
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time, zlib
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r24lib as L

O = HERE / 'candidate'
PROBE = HERE / 'probe_cal'
RUN = PROBE / 'run'
BOOT = 'NightRemasterCalTourProbe'
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
MANAMI = 3          # lane 3 = 마나미 (October holds the eight 10/11 branch rows: r19 affinity conditions + name tails)
DUNGEON = 8         # lane 8 = 던전 (April: the two drawers whose only scenes are outside the panel)
MIDSAVE_SLOT = 90   # the probe's mid-replay save (inside the probe's own save folder)
PARTNER_SAVE = 'NightR40.asd'     # saved inside the Saturday partner selection (RunSelectPartner > CheckResSysButton > save)
HOVER = (3, 8)                    # the two portraits the probe hovers (쿄카, 모모세: both selectable in NightR40)
DUNGEON_SAVE = 'NightR20.asd'     # saved from the dungeon's save screen (C_SceneDungeon@Run): the dungeon status window
LIVE_R20 = ('C_Status::RunStatus', 'RunSelectPartner', 'RunMember', 'C_SceneSaveLoad@RunCommon', 'C_SceneDungeon@Run')   # waits the r20 screens need
LIVE_R20_EXPECT = ['C_Status::RunStatus', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>',
                   'C_SceneHomebase@<lambda : C_SceneHomebase@RunMember()(233, 52)>', 'C_SceneSaveLoad@RunCommon', 'C_SceneDungeon@Run']

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
// r19: every calendar event read in another save only (△: MsgSkip read mark of its first message, not registered here)
string KR_CPReadText() {
    string t = "";
    for (int i = 0; i < 404; i++) { int e = KR_T9StageEv(i); if (KR_T9State(e) == 1) t = t + " " + ("%d" % e); }
    for (int j = 0; j < 760; j++) { int e2 = KR_T9SceneEv(j); if (KR_T9State(e2) == 1) t = t + " " + ("%d" % e2); }
    return t;
}
void KR_CPRegs() { KR_ClaudeProbeLog("REGS" + KR_CPRegsText()); KR_ClaudeProbeLog("READ" + KR_CPReadText()); }
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
// r19: stage-list / drawer-list lines as KR_T19StagePage / KR_T19ChipPage list them (same functions, same paging)
void KR_CPStageRows(int k, int page) {
    int n = KR_T9CardSize(k);
    int s0 = KR_T9CardStage(k);
    int per = KR_T19ListPer(KR_T19StageCols(k), n);
    int first = page * per;
    int last = first + per;
    if (last > n) last = n;
    string t = "";
    for (int i = first; i < last; i++) {
        if (i > first) t = t + "\n";
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
        if (i > first) t = t + "\n";
        t = t + KR_T19ListItem(KR_T19SceneAt(s0 + i));
    }
    KR_CPBlock("ROWS", "DRAWER " + ("%d" % c) + " p" + ("%d" % (page + 1)), t);
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
    int t20 = KR_Time();
    KR_CPR20All("REGS");
    KR_CPR23("REGS");
    KR_ClaudeProbeLog("R20 texts of 8 persons built in " + ("%d" % (KR_Time() - t20)) + " ms");
    KR_CPPanel("REGS");
    int t0 = KR_Time();
    KR_CPBlock("TITLE", "SUMMARY", KR_T18SummaryTitle());
    KR_ClaudeProbeLog("SUMMARY built in " + ("%d" % (KR_Time() - t0)) + " ms");
    KR_ClaudeProbeLog("END");
    system.Exit(0);
}
/*TARGETS*/

// ---- r23: the affinity values the game gives and r23's texts, per person (the verifier recomputes them, V54)
int KR_CPMode() { int m = Flags.GameMode::get(); return m; }
void KR_CPR23(string tag) {
    int mode = KR_CPMode();
    for (int c = 1; c <= 8; c++) {
        int inner = LAbility::m_pAbilities[c - 1].GetFeelingInnerValue();
        int feel = LAbility::m_pAbilities[c - 1].GetFeeling();
        int rank5 = C_SysVoice::GetFeelingRank_5(c);
        KR_ClaudeProbeLog("R23 " + ("%d" % c) + " inner=" + ("%d" % inner) + " feel=" + ("%d" % feel) + " rank5=" + ("%d" % rank5) + " ours=" + ("%d" % KR_T23Feel(c)) + " rank=" + ("%d" % KR_T23Rank(c)) + " next=" + ("%d" % KR_T23Next(c)) + " route=" + ("%d" % KR_T23Route(c)) + " mode=" + ("%d" % mode));
        bool en = mode != 1 && c >= 2 && c <= 5;
        if (en) KR_CPBlock("R23MOON", ("%d" % c), KR_T23MoonText(c));
        KR_CPBlock("R23ST", ("%d" % c), KR_T23StText(c, en));
    }
}
// the moon text part as it is on screen now (person, page), the status root, the moons' own box under the same parent
int KR_CPMoonBox(int parent) {
    for (int n = 1000000000; n < 1000040000; n++) {
        if (!PartsEngine.IsExist(n)) continue;
        if (PartsEngine.Parts_GetParentPartsNumber(n) != parent) continue;
        if (PartsEngine.GetComponentPosX(n) == 374.0 && PartsEngine.GetComponentPosY(n) == 66.0) return n;
    }
    return 0;
}
void KR_CPMoon(string tag, int person, int page) {
    int n = KR_T23MoonPart();
    int root = PartsEngine.GetActivityPartsNumber("Game\\Scenes\\4000Homebase\\CharaStatus.pact", "ルートパーツ");
    if (!PartsEngine.IsExist(n)) {
        int box0 = KR_CPMoonBox(root);
        int bs0 = 0;
        if (box0 > 0) bs0 = KR_CPB(PartsEngine.IsComponentShow(box0));
        KR_ClaudeProbeLog("R23MOONLOG " + tag + " person=" + ("%d" % person) + " page=" + ("%d" % page) + " exists=0 show=0 parent=0 root=" + ("%d" % root) + " box=" + ("%d" % box0) + " boxshow=" + ("%d" % bs0) + " x=0.0 y=0.0");
        return;
    }
    int par = PartsEngine.Parts_GetParentPartsNumber(n);
    int box = KR_CPMoonBox(par);
    int bs = 0;
    if (box > 0) bs = KR_CPB(PartsEngine.IsComponentShow(box));
    KR_ClaudeProbeLog("R23MOONLOG " + tag + " person=" + ("%d" % person) + " page=" + ("%d" % page) + " exists=1 show=" + ("%d" % KR_CPB(PartsEngine.IsComponentShow(n))) + " parent=" + ("%d" % par) + " root=" + ("%d" % root) + " box=" + ("%d" % box) + " boxshow=" + ("%d" % bs) + " x=" + ("%f" % PartsEngine.GetComponentPosX(n)) + " y=" + ("%f" % PartsEngine.GetComponentPosY(n)));
    KR_CPBlock("R23MOON", tag, PartsEngine.GetTextPartsText(n, 1));
}
void KR_CPPage4(string tag, int person) {
    KR_ClaudeProbeLog("R23PAGE4 " + tag + " person=" + ("%d" % person) + " panel_h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(KR_T20StPanel(), 1)) + " text_h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(KR_T20StTextPart(), 1)) + " text_w=" + ("%d" % PartsEngine.Parts_GetPartsWidth(KR_T20StTextPart(), 1)));
}
void KR_CPLeak(string tag) {
    KR_ClaudeProbeLog("R23LEAK " + tag + " moon=" + ("%d" % KR_CPB(PartsEngine.IsExist(KR_T23MoonPart()))));
}

// ---- r20: parts of our own (status page: panel + text; partner select: box + label per portrait)
int KR_CPOurs() {
    int n = 0;
    if (PartsEngine.IsExist(KR_T20StPanel())) n++;
    if (PartsEngine.IsExist(KR_T20StTextPart())) n++;
    for (int p = 2; p <= 8; p++) {
        if (PartsEngine.IsExist(KR_T20TrPart(p))) n++;
        if (PartsEngine.IsExist(KR_T20TrBox(p))) n++;
    }
    return n;
}
void KR_CPCount(string tag) {
    KR_ClaudeProbeLog("COUNT " + tag + " ours=" + ("%d" % KR_CPOurs()) + " charastatus=" + ("%d" % PartsEngine.NumofActivityParts("Game\\Scenes\\4000Homebase\\CharaStatus.pact")) + " selectally=" + ("%d" % PartsEngine.NumofActivityParts("Game\\Scenes\\Common\\SelectAlly.pact")) + " homemember=" + ("%d" % PartsEngine.NumofActivityParts("Game\\Scenes\\4000Homebase\\HomeMember.pact")));
}
// the status page text part as drawn, and every person's texts as the r20 functions give them (the VM recomputes both)
void KR_CPStText(string tag) {
    KR_CPBlock("STTEXT", tag, PartsEngine.GetTextPartsText(KR_T20StTextPart(), 1));
}
void KR_CPR20All(string tag) {
    for (int c = 1; c <= 8; c++) KR_CPBlock("STCALC", tag + " " + ("%d" % c), KR_T20StText(c));
    for (int p = 2; p <= 8; p++) KR_CPBlock("TRCALC", tag + " " + ("%d" % p), KR_T20TrText(p));
}
void KR_CPLabels(string tag) {
    for (int p = 2; p <= 8; p++) {
        int n = KR_T20TrPart(p);
        if (!PartsEngine.IsExist(n)) continue;
        KR_CPBlock("TRTEXT", tag + " " + ("%d" % p), PartsEngine.GetTextPartsText(n, 1));
        KR_ClaudeProbeLog("TRMUL " + tag + " " + ("%d" % p) + " " + ("%d" % PartsEngine.GetComponentMulColorR(n)) + " box=" + ("%d" % KR_CPB(PartsEngine.IsExist(KR_T20TrBox(p)))));
    }
}
string KR_CPStack() {
    string t = "";
    for (int i = 0; i < 40; i++) {
        string s = system.GetFuncStackName(i);
        if (s == "") break;
        t = t + s + " | ";
    }
    return t;
}
bool KR_CPOn(string name) { string t = KR_CPStack(); return t.Find(name) >= 0; }
int KR_CPHover() { return KR_CPNum("Hover"); }
// probe only: what the player's hover does before the click (RunMember OnEnterChara: SetInfo + Show)
void KR_CPPrepStatus(int charaNo, ref C_HomeMemberView memView) {
    memView.m_StatusView.SetInfo(charaNo);
    memView.m_StatusView.Show();
    // r23: the preview is what a hover shows (page 0): the moons and the moon text of a heroine, nothing for a man
    string who = "man";
    if (charaNo == KR_CPNum("W2")) who = "heroine_a";
    if (charaNo == KR_CPNum("W3")) who = "heroine_b";
    string stg = KR_CPGet("Stage");
    if (stg.Find("r20") == 0 || stg.Find("r23") == 0) {
        AFL_View_Update();
        KR_CPMoon(who + "_preview", charaNo, 0);
        if (who != "man") KR_ClaudeShot("cal_feel_" + who + "_preview.bmp");
    }
}
bool KR_CPTick2(int kind) {
    string stage = KR_CPGet("Stage");
    bool r20 = stage.Find("r20") == 0 || stage.Find("r23") == 0;
    bool pr = stage.Find("pt") == 0;
    bool dg = stage.Find("dg") == 0;
    if (!r20 && !pr && !dg) return false;
    int frames = KR_CPNum("Frames2") + 1;
    KR_CPSet("Frames2", "%d" % frames);
    if (frames > 1800) { KR_ClaudeProbeLog("STUCK2 stage=" + stage + " stack=" + KR_CPStack()); KR_ClaudeShot("cal_stuck2.bmp"); system.Exit(5); return false; }
    if (frames < 24) return false;
    
    // ---------------- r20 home: 파티 편성 -> 스테이터스 -> 이벤트 쪽 (two persons, back and forth, exit, enter again)
    if (stage == "r20member" || stage == "r20member2") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPCount(stage);
        int w = KR_CPNum("W1");
        if (stage == "r20member2") w = KR_CPNum("W2");
        else KR_ClaudeShot("cal_member.bmp");
        KR_CPSet("Stage", stage + "dlg");
        KR_CPEnd2(1000 + w);
        return false;
    }
    if (stage == "r20memberdlg" || stage == "r20member2dlg") {
        if (!KR_CPOn("C_SelectDialog@_Update")) return false;
        if (stage == "r20memberdlg") KR_CPSet("Stage", "r20s1");
        else KR_CPSet("Stage", "r20t1");
        KR_CPEnd2(3);
        return false;
    }
    if (stage == "r20s1") {
        if (!KR_CPOn("C_Status::_UpdateInput")) return false;
        KR_CPCount("S1 page1");
        KR_CPMoon("man_p1", KR_CPNum("W1"), 1);
        KR_ClaudeShot("cal_status_p1.bmp");
        KR_CPSet("Stage", "r20s2");
        KR_CPEnd2(2);
        return false;
    }
    if (stage == "r20s2") { KR_CPCount("S2 page2"); KR_CPSet("Stage", "r20s3"); KR_CPEnd2(2); return false; }
    if (stage == "r20s3") { KR_CPCount("S3 page3"); KR_CPSet("T0", "%d" % KR_Time()); KR_CPSet("Stage", "r20s4"); KR_CPEnd2(2); return false; }
    if (stage == "r20s4") {
        KR_ClaudeProbeLog("EVENT PAGE shown after " + ("%d" % (KR_Time() - KR_CPNum("T0"))) + " ms (click to shown, incl. counting)");
        KR_CPCount("S4 page4 A");
        KR_ClaudeProbeLog("STCHARA A " + ("%d" % KR_CPNum("W1")));
        KR_CPStText("A");
        KR_ClaudeShot("cal_status_event_a.bmp");
        KR_CPSet("Stage", "r20s4b");
        KR_CPEnd2(4);
        return false;
    }
    if (stage == "r20s4b") {
        KR_CPCount("S4 page4 B (next person)");
        KR_CPStText("B");
        KR_ClaudeShot("cal_status_event_b.bmp");
        KR_CPSet("Stage", "r20s3b");
        KR_CPEnd2(1);
        return false;
    }
    if (stage == "r20s3b") { KR_CPCount("S3B page3 (prev from 4)"); KR_ClaudeShot("cal_status_p3_from4.bmp"); KR_CPSet("Stage", "r20s4c"); KR_CPEnd2(2); return false; }
    if (stage == "r20s4c") { KR_CPCount("S4C page4 (next from 3)"); KR_CPSet("Stage", "r20s1b"); KR_CPEnd2(2); return false; }
    if (stage == "r20s1b") { KR_CPCount("S1B page1 (next from 4)"); KR_ClaudeShot("cal_status_p1_from4.bmp"); KR_CPSet("Stage", "r20s4d"); KR_CPEnd2(1); return false; }
    if (stage == "r20s4d") { KR_CPCount("S4D page4 (prev from 1)"); KR_CPSet("Stage", "r20back1"); KR_CPEnd2(0); return false; }
    if (stage == "r20back1") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPCount("AFTER EXIT 1");
        KR_ClaudeShot("cal_member_after1.bmp");
        KR_CPSet("Stage", "r20member2");
        KR_CPSet("Frames2", "0");
        return false;
    }
    if (stage == "r20t1") {
        if (!KR_CPOn("C_Status::_UpdateInput")) return false;
        KR_CPCount("T1 page1 (second entry)");
        KR_CPMoon("heroine_a_p1", KR_CPNum("W2"), 1);
        KR_ClaudeShot("cal_feel_heroine_a_p1.bmp");
        KR_CPSet("Stage", "r20t4");
        KR_CPEnd2(1);
        return false;
    }
    if (stage == "r20t4") {
        KR_CPCount("T4 page4 C (second entry)");
        KR_ClaudeProbeLog("STCHARA C " + ("%d" % KR_CPNum("W2")));
        KR_CPStText("C");
        KR_CPPage4("C", KR_CPNum("W2"));
        KR_CPMoon("heroine_a_p4", KR_CPNum("W2"), 4);
        KR_ClaudeShot("cal_status_event_c.bmp");
        KR_CPSet("Stage", "r20back2");
        KR_CPEnd2(0);
        return false;
    }
    if (stage == "r20back2") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPCount("AFTER EXIT 2");
        KR_CPMoon("after_exit2", KR_CPNum("W2"), 0);
        KR_CPSet("Stage", "r23member3");
        KR_CPSet("Frames2", "0");
        return false;
    }
    // ---------------- r23: the second heroine (W3)
    if (stage == "r23member3") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPSet("Stage", "r23dlg3");
        KR_CPEnd2(1000 + KR_CPNum("W3"));
        return false;
    }
    if (stage == "r23dlg3") {
        if (!KR_CPOn("C_SelectDialog@_Update")) return false;
        KR_CPSet("Stage", "r23p1");
        KR_CPEnd2(3);
        return false;
    }
    if (stage == "r23p1") {
        if (!KR_CPOn("C_Status::_UpdateInput")) return false;
        KR_CPMoon("heroine_b_p1", KR_CPNum("W3"), 1);
        KR_ClaudeShot("cal_feel_heroine_b_p1.bmp");
        KR_CPSet("Stage", "r23p4");
        KR_CPEnd2(1);
        return false;
    }
    if (stage == "r23p4") {
        KR_ClaudeProbeLog("STCHARA M " + ("%d" % KR_CPNum("W3")));
        KR_CPStText("M");
        KR_CPPage4("M", KR_CPNum("W3"));
        KR_CPMoon("heroine_b_p4", KR_CPNum("W3"), 4);
        KR_ClaudeShot("cal_feel_heroine_b_p4.bmp");
        KR_CPSet("Stage", "r23back3");
        KR_CPEnd2(0);
        return false;
    }
    if (stage == "r23back3") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPCount("AFTER EXIT 3");
        KR_CPSet("Stage", "r20home");
        KR_CPSet("Frames2", "0");
        return true;
    }
    if (stage == "r20home") {
        if (!KR_CPOn("C_SelectDialog@_Update")) return false;
        if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") return false;
        if (frames < 60) return false;
        KR_CPLeak("after_member");
        KR_CPCount("HOME after the member screen");
        KR_ClaudeShot("cal_home_r20_after.bmp");
        KR_CPSet("R20", "done");
        KR_CPSet("Stage", "");
        KR_CPSet("Frames", "0");
        return false;
    }
    // ---------------- r20 dungeon (run 3): the status window opened from the dungeon (RunStatusInDungeon)
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
        for (int dc = 1; dc <= 8; dc++) KR_ClaudeProbeLog("R23DFEEL " + ("%d" % dc) + " " + ("%d" % LAbility::m_pAbilities[dc - 1].GetFeelingInnerValue()));
        KR_CPMoon("dungeon_p1", KR_CPNum("WD"), 1);
        KR_ClaudeShot("cal_feel_dungeon_p1.bmp");
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
        KR_CPPage4("D", KR_CPNum("WD"));
        KR_ClaudeShot("cal_status_event_dungeon.bmp");
        KR_CPSet("Stage", "dg5");
        KR_CPEnd2(0);
        return false;
    }
    if (stage == "dg5") {
        if (!KR_CPOn("C_SceneDungeon@")) return false;
        if (frames < 60) return false;
        KR_CPLeak("after_dungeon");
        KR_CPCount("DUNGEON after");
        KR_ClaudeShot("cal_dungeon_after.bmp");
        KR_ClaudeProbeLog("END");
        system.Exit(0);
        return false;
    }
    // ---------------- r20 partner select (run 2): labels, hover A, hover B, confirm (no), again, confirm (yes)
    if (stage == "pt0") {
        if (KR_CPOn("C_SceneSaveLoad@Update")) { KR_CPSet("Frames2", "0"); return true; }
        if (!KR_CPOn("_UpdateInputPartner")) return false;
        KR_ClaudeProbeLog("PARTNER date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()));
        KR_CPRegs();
        KR_CPR20All("PT");
        KR_CPCount("PARTNER 1");
        KR_CPLabels("P0");
        KR_ClaudeShot("cal_partner_nohover.bmp");
        KR_CPSet("Hover", "@@HOVER_A@@");
        KR_CPSet("Stage", "pt1");
        KR_CPSet("Frames2", "0");
        return false;
    }
    if (stage == "pt1" || stage == "pt2") {
        if (frames < 60) return false;
        if (stage == "pt1") {
            KR_CPCount("HOVER A");
            KR_CPLabels("PA");
            KR_ClaudeShot("cal_partner_hover_a.bmp");
            KR_CPSet("Hover", "@@HOVER_B@@");
            KR_CPSet("Stage", "pt2");
            KR_CPSet("Frames2", "0");
            return false;
        }
        KR_CPCount("HOVER B");
        KR_CPLabels("PB");
        KR_ClaudeShot("cal_partner_hover_b.bmp");
        KR_CPSet("Stage", "ptdlg1");
        KR_CPEnd2(@@HOVER_B@@);
        return false;
    }
    if (stage == "ptdlg1" || stage == "ptdlg2") {
        if (!KR_CPOn("C_SelectDialog@_Update")) return false;
        KR_CPCount("CONFIRM DIALOG " + stage);
        if (stage == "ptdlg1") {
            KR_ClaudeShot("cal_partner_dialog.bmp");
            KR_CPSet("Stage", "ptagain");
            KR_CPEnd2(2);
            return false;
        }
        KR_CPSet("Stage", "ptchosen");
        KR_CPEnd2(1);
        return false;
    }
    if (stage == "ptagain") {
        if (!KR_CPOn("_UpdateInputPartner")) return false;
        KR_CPCount("PARTNER 2 (entered again)");
        KR_CPLabels("P2");
        KR_ClaudeShot("cal_partner_again.bmp");
        KR_CPSet("Stage", "ptdlg2");
        KR_CPEnd2(@@HOVER_B@@);
        return false;
    }

    return false;
}
void KR_CPEnd2(int code) {
    KR_CPSet("Frames2", "0");
    AFL_Parts_EndWaitForClick(code);
}

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
    if (stage.Find("r20") == 0 || stage.Find("r23") == 0 || stage.Find("pt") == 0 || stage.Find("dg") == 0) return;
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
        @@R20_FIRST@@
        int p = KR_CPPerson();
        KR_ClaudeProbeLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()) + " person=" + ("%d" % p));
        KR_CPRegs();
        KR_CPPanel("HOME");
        KR_CPState("HOME");
        KR_ClaudeProbeLog("R23MODE " + ("%d" % KR_CPMode()));
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
        KR_CPStageRows(KR_T9LaneCardAt(@@T_MONTH@@, @@T_LANE@@, @@T_INDEX@@), 0);
        KR_ClaudeShot("cal_stages.bmp");
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
    if (KR_CPGet("Stage") == "ptchosen") {
        KR_CPCount("FIRST MESSAGE AFTER THE PARTNER SCREEN");
        KR_ClaudeProbeLog("END");
        system.Exit(0);
        return 0;
    }
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
    if (save == "@@PARTNER_SAVE@@") KR_CPSet("Stage", "pt0");
    if (save == "@@DUNGEON_SAVE@@") KR_CPSet("Stage", "dg0");
    system.ResumeLoad("@@KEY@@", save);
    system.Exit(2);
    return 2;
}
'''


def expectations():
    import verify_chart_r24 as V
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


def name_targets(X):
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
        found = []                              # (has the preferred scene on the first list page, month, ...)
        for month in range(4, 12):
            cs, ch, per = lane_items(month, lane)
            for j, (i, x) in enumerate(ch):
                if KIND[x['kind']] != kind or len(cs) + j >= per:
                    continue
                order = sorted(x['scenes'])
                items = [n for n, no in enumerate(order) if pick(evs[no]) and n < 30]
                found.append((0 if items else 1, month, dict(month=month, lane=lane, row=len(cs) + j, chip=i, item=(items or [0])[0],
                                                             event=order[(items or [0])[0]])))
        if found:
            out[key] = sorted(found, key=lambda x: (x[0], x[1]))[0][2]
    assert set(out) == {'D', 'W', 'A'}, out
    return out


KIND = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']


def target_jaf(t):
    return ''


def build_probe(source, key, work, mode, target, names=None):
    src = source / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@KEY@@', key).replace('/*TARGETS*/', '')
    jaf = jaf.replace('@@MANAMI@@', str(MANAMI)).replace('@@DUNGEON@@', str(DUNGEON)).replace('@@SLOT@@', str(MIDSAVE_SLOT))
    t = target or dict(month=4, lane=0, index=0, stage=0, event=0)
    jaf = (jaf.replace('@@T_MONTH@@', str(t['month'])).replace('@@T_LANE@@', str(t['lane'])).replace('@@T_INDEX@@', str(t['index']))
           .replace('@@T_STAGE@@', str(t['stage'])).replace('@@T_EVENT@@', str(t['event'])))
    nt = names or dict(D=dict(month=4, index=0), W=dict(month=4, lane=1, row=0, chip=0, item=0), A=dict(month=4, lane=1, row=0, chip=0, item=0))
    for p, d in nt.items():
        for f, v in d.items():
            jaf = jaf.replace('@@%s_%s@@' % (p, f.upper()), str(v))
    jaf = jaf.replace('@@REGS_ONLY@@', 'KR_CPRegsExit("HOME"); return;' if mode == 'regs' else '')
    r20_first = ('if (KR_CPGet("R20") != "done") { int w1 = L_Party::GetPersonID(1); if (w1 <= 1) w1 = 2; int w2 = 2; '
                 'if (w1 == 2) w2 = 3; int w3 = 4; if (w2 == 4) w3 = 3; KR_CPSet("W1", "%d" % w1); KR_CPSet("W2", "%d" % w2); KR_CPSet("W3", "%d" % w3); KR_CPCount("HOME before"); '
                 'KR_ClaudeShot("cal_home_r20_before.bmp"); KR_CPSet("Stage", "r20member"); KR_CPSet("Frames2", "0"); KR_CPEnd(11); return; }')
    jaf = jaf.replace('@@R20_FIRST@@', r20_first if mode == 'full' else '')
    jaf = jaf.replace('@@DUNGEON_SAVE@@', DUNGEON_SAVE).replace('@@PARTNER_SAVE@@', PARTNER_SAVE).replace('@@HOVER_A@@', str(HOVER[0])).replace('@@HOVER_B@@', str(HOVER[1]))
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
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47 and f['name'] != 'C_UserInputManager::IsClickCancelOtherMouse']
    # r20: every per-frame input handler asks IsClickCancelOtherMouse first -> the r20 tick (returns the scripted cancel)
    f = next(f for f in m['functions'] if f['name'] == 'C_UserInputManager::IsClickCancelOtherMouse')
    patch.append(f"FUNC {f['index']}\n\tPUSH 1\n\tCALLFUNC KR_CPTick2\n\tRETURN\nENDFUNC {f['name']}\n")
    # r20: the hovered portrait of the partner screen comes from the probe (the window is hidden: no mouse)
    om = L.fid_of(m, 'C_SceneTrainingView@GetOnmouseChara')
    patch.append(f"FUNC {om}\n\tCALLFUNC KR_CPHover\n\tRETURN\nENDFUNC C_SceneTrainingView@GetOnmouseChara\n")
    # r20: the hover a player always does before clicking a portrait of the member view (SetInfo + Show)
    rs = L.fid_of(m, 'C_SceneHomebase@RunStatus')
    path = work / f'original_{rs}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SceneHomebase@RunStatus', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SceneHomebase@RunStatus'), '\t.LOCALREF charaNo\n\t.LOCALREF memView\n\tCALLFUNC KR_CPPrepStatus\n'))
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
                if any(k in name for k in LIVE_R20):
                    waits.append((name, 'live r20'))
                    continue
                target_fid = ids['KR_CalProbeMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_CalProbeWait']
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, target_fid)
                waits.append((name, 'message click-through' if target_fid == ids['KR_CalProbeMsgWait'] else 'exit'))
    assert sum(1 for _, k in waits if k == 'live') == 1 and sum(1 for _, k in waits if k.startswith('message')) == 1, waits
    assert sorted(n for n, k in waits if k == 'live r20') == sorted(LIVE_R20_EXPECT), [w for w in waits if w[1] == 'live r20']
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
    for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex']:          # PACT/EX are the runtime's (r19 does not change them)
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


def collect_shots(mode):
    """cal_*.bmp of the run that just ended -> 증거/probe/*.png (removed from run/)."""
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(RUN.glob('cal_*.bmp')):
        png = dest / (b.stem + ('_savefoldertest' if mode == 'savefolder' else '') + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    return shots


def run_one(save, mode, info_builder, stamp):
    """Copy the save + global files into a fresh P: save folder inside run\\, launch, collect log and screenshots."""
    savename = f'SaveData_R24CalTourProbe_{stamp}'
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
        z = re.match(r'(TITLE|ROWS|PANEL|STATE|STTEXT|STCALC|TRCALC|TRTEXT) (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            out[(z.group(1), z.group(2))] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    return out


def r20_report(log, plog):
    """Parts counts after every r20 step (ours = our fixed-number parts; the three activities' own part counts), the event
    page texts, the partner labels and their brightness."""
    counts = [l for l in log + plog if l.startswith('COUNT ')]
    def ours(tag):
        hits = [l for l in counts if l.startswith('COUNT ' + tag + ' ')]
        assert hits, ('no COUNT line', tag)
        z = re.search(r' ours=(\d+) charastatus=(\d+) selectally=(\d+) homemember=(\d+)', hits[-1])
        return dict(ours=int(z.group(1)), charastatus=int(z.group(2)), selectally=int(z.group(3)), homemember=int(z.group(4)))
    b = blocks(log)
    pb = blocks(plog)
    mul = {}
    for l in plog:
        z = re.match(r'TRMUL (\w+) (\d) (\d+) box=(\d)', l)
        if z:
            mul.setdefault(z.group(1), {})[int(z.group(2))] = (int(z.group(3)), int(z.group(4)))
    rep_ = dict(counts=counts,
                status=dict(page1=ours('S1 page1'), page4=ours('S4 page4 A'), page4_next_person=ours('S4 page4 B (next person)'),
                            page3_from4=ours('S3B page3 (prev from 4)'), page4_from3=ours('S4C page4 (next from 3)'),
                            page1_from4=ours('S1B page1 (next from 4)'), page4_from1=ours('S4D page4 (prev from 1)'),
                            after_exit1=ours('AFTER EXIT 1'), second_entry_page4=ours('T4 page4 C (second entry)'),
                            after_exit2=ours('AFTER EXIT 2'), home_after=ours('HOME after the member screen'),
                            home_before=ours('HOME before')),
                status_texts={t: b.get(('STTEXT', t)) for t in ('A', 'B', 'C')},
                status_charas={l.split()[1]: int(l.split()[2]) for l in log if l.startswith('STCHARA ')},
                partner=dict(first=ours('PARTNER 1'), dialog1=ours('CONFIRM DIALOG ptdlg1'), again=ours('PARTNER 2 (entered again)'),
                             dialog2=ours('CONFIRM DIALOG ptdlg2'), after_screen=ours('FIRST MESSAGE AFTER THE PARTNER SCREEN')),
                partner_labels={tag: {k[1]: v for k, v in pb.items() if k[0] == 'TRTEXT' and k[1].startswith(tag + ' ')} for tag in ('P0', 'PA', 'PB', 'P2')},
                partner_mul=mul, partner_calc={' '.join(k): v for k, v in pb.items() if k[0] in ('STCALC', 'TRCALC')},
                partner_date=next((l for l in plog if l.startswith('PARTNER date=')), None),
                event_page_ms=next((l for l in log if l.startswith('EVENT PAGE shown after')), None))
    return rep_


def r20_dungeon_report(log):
    counts = [l for l in log if l.startswith('COUNT ')]

    def ours(tag):
        hits = [l for l in counts if l.startswith('COUNT ' + tag + ' ')]
        assert hits, ('no COUNT line', tag)
        z = re.search(r' ours=(\d+) charastatus=(\d+) selectally=(\d+) homemember=(\d+)', hits[-1])
        return dict(ours=int(z.group(1)), charastatus=int(z.group(2)), selectally=int(z.group(3)), homemember=int(z.group(4)))
    b = blocks(log)
    return dict(counts=counts, before=ours('DUNGEON before'), page1=ours('DG page1'), page4=ours('DG page4'), after=ours('DUNGEON after'),
                text=b.get(('STTEXT', 'D')), person=next((int(l.split()[2]) for l in log if l.startswith('STCHARA D ')), None),
                date=next((l for l in log if l.startswith('DUNGEON date=')), None),
                stack=next((l for l in log if l.startswith('DUNGEON STATUS stack=')), None))


def r23_report(log, dlog):
    """The r23 stages: moon text logs (preview / page 1 / page 4 / after exits), page-4 sizes, leak lines."""
    moon = {}
    b = blocks_r23(log + dlog)
    for l in log + dlog:
        z = re.match(r'R23MOONLOG (\S+) person=(\d+) page=(\d+) exists=(\d) show=(\d) parent=(\d+) root=(\d+) box=(\d+) boxshow=(\d) x=([-\d.]+) y=([-\d.]+)$', l)
        if z:
            tag = z.group(1)
            moon[tag] = dict(person=int(z.group(2)), page=int(z.group(3)), exists=int(z.group(4)), show=int(z.group(5)), parent=int(z.group(6)),
                             root=int(z.group(7)), box=int(z.group(8)), boxshow=int(z.group(9)), x=float(z.group(10)), y=float(z.group(11)),
                             text=b.get(('R23MOON', tag)))
    page4 = {}
    for l in log:
        z = re.match(r'R23PAGE4 (\w) person=(\d+) panel_h=(\d+) text_h=(\d+) text_w=(\d+)$', l)
        if z and z.group(1) in ('C', 'M'):
            page4[z.group(1)] = dict(person=int(z.group(2)), panel_h=int(z.group(3)), text_h=int(z.group(4)), text_w=int(z.group(5)),
                                     text=blocks(log).get(('STTEXT', z.group(1))))
    dpage = next((dict(person=int(z.group(2)), panel_h=int(z.group(3)), text_h=int(z.group(4)), text_w=int(z.group(5)))
                  for z in (re.match(r'R23PAGE4 (D) person=(\d+) panel_h=(\d+) text_h=(\d+) text_w=(\d+)$', l) for l in dlog) if z), None)
    leak = {}
    for l in log + dlog:
        z = re.match(r'R23LEAK (\S+) moon=(\d)$', l)
        if z:
            leak[z.group(1)] = int(z.group(2))
    return dict(moon=moon, page4=page4, dungeon_page4=dpage, leak=leak)


def blocks_r23(log):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'(R23MOON|R23ST) (.*) <<<$', log[i])
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
    read = next((l for l in log if l.startswith('READ')), None)
    if not home or regs is None:
        return None
    z = re.match(r'(HOME|WAIT) date=(\d+)/(\d+) now=(\d+)', home)
    b = blocks(log)
    pn = next((int(l.split()[1]) for l in log if l.startswith('PANELN ')), None)
    panel = next((t for (k, tag), t in b.items() if k == 'PANEL'), None)
    return dict(at='home' if z[1] == 'HOME' else 'wait', today=[int(z[2]), int(z[3])], now=int(z[4]),
                regs=sorted(int(x) for x in regs.split()[1:]), read=sorted(int(x) for x in read.split()[1:]) if read else None,
                panel=panel, panel_count=pn,
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


# ============================================================== r21: the mod-menu tour (python probe_modmenu_r21.py --r21)
# Two runs on one copied home save and ONE save folder (run B starts from what run A left):
#   run A: home -> paths + file-API experiments -> poll cost (5,000 calls each) -> home-menu frame time armed / disarmed ->
#          request.txt written by the probe itself (no hook) for chart / unlock_all / unlock_revert / unlock_all / an unknown
#          command -> last_result.txt (a long hook line) -> last_result + request together -> reset_all 아니요 ->
#          reset_restore 아니요 -> a request written while our own notice is open (not consumed until home) -> the r13 panel
#          click opens the character window and a request written there waits for home -> reset_all 예: the game's exit
#   run B: home -> the flag read back after the restart -> unlock_revert -> reset_restore 예 (the stale reset.req from run A goes)
# The probe writes the request exactly as the hook does (cmd, seq, time; CR LF; TextFile writes LF as CR LF).
R21_BOOT_SAVE = 'NightR44.asd'
R21_JAF = r'''
string KR_CPRead(string file) {
    string s = "";
    if (!TextFile.ReadAll(file, s)) return "";
    return s;
}
void KR_ClaudeProbeLog(string text) {
    TextFile.WriteAll("claude_probe.txt", KR_CPRead("claude_probe.txt") + text + "\n");
}
int KR_ClaudeShot(string file) {
    AFL_View_Update(); AFL_View_Update(); AFL_View_Update();
    if (!SystemService.SaveScreenshot(file, 0, 0, 1280, 720)) system.Exit(9);
    KR_ClaudeProbeLog("SHOT " + file);
    return 0;
}
string KR_M21Get(string key) { return SystemService.SystemVariable_Get("YoruKR.M21." + key); }
void KR_M21Set(string key, string value) { SystemService.SystemVariable_Set("YoruKR.M21." + key, value); }
int KR_M21Num(string key) { string v = KR_M21Get(key); if (v == "") return 0; return v.ToInt(); }
int KR_M21B(bool v) { if (v) return 1; return 0; }
string KR_M21Title() { return SystemService.SystemVariable_Get("YoruKR.T8.Title"); }
string KR_M21Head() {
    string t = KR_M21Title();
    int nl = t.Find("\n");
    if (nl > 0) t = KR_JosaSlice(t, 0, nl);
    return t;
}
bool KR_M21Home() { return SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") == "1" && KR_M21Title() == ""; }
void KR_M21Block(string kind, string tag, string text) {
    KR_ClaudeProbeLog(kind + " " + tag + " <<<");
    KR_ClaudeProbeLog(text);
    KR_ClaudeProbeLog(">>>");
}
void KR_M21Go(string stage) {
    KR_M21Set("Stage", stage);
    KR_M21Set("Frames", "0");
}
void KR_M21End(string stage, int code) {
    KR_M21Go(stage);
    AFL_Parts_EndWaitForClick(code);
}
// what the hook's WriteRequest leaves: cmd CR LF seq CR LF time CR LF (the folder made first)
void KR_M21Request(string cmd) {
    int seq = KR_M21Num("Seq") + 1;
    KR_M21Set("Seq", "%d" % seq);
    if (!FileOperation.ExistFolder(KR_MFolder())) FileOperation.CreateFolder(KR_MFolder());
    TextFile.WriteAll(KR_MFile("request.txt"), cmd + "\n" + ("%d" % seq) + "\n2026-09-28 03:30:00\n");
    KR_M21Set("TReq", "%d" % KR_Time());
    KR_ClaudeProbeLog("REQUEST " + cmd + " seq=" + ("%d" % seq) + " exist=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MFile("request.txt")))));
}
void KR_M21Result(string line) {
    if (!FileOperation.ExistFolder(KR_MFolder())) FileOperation.CreateFolder(KR_MFolder());
    TextFile.WriteAll(KR_MFile("last_result.txt"), line + "\n");
    KR_M21Set("TReq", "%d" % KR_Time());
    KR_ClaudeProbeLog("RESULT written: " + line);
}
string KR_M21Files() {
    string t = "request=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MFile("request.txt"))));
    t = t + " last_result=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MFile("last_result.txt"))));
    t = t + " reset_req=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MFile("reset.req"))));
    t = t + " restore_req=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MFile("restore.req"))));
    t = t + " marker=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MMarkerFile())));
    t = t + " chart=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MChartFile())));
    t = t + " unlock=" + ("%d" % KR_MUnlockAll());
    t = t + " off=" + SystemService.SystemVariable_Get("YoruKR.M.Off");
    return t;
}
void KR_M21Window(string tag) {
    KR_M21Block("TITLE", tag, KR_M21Title());
    KR_ClaudeProbeLog("SHOWN " + tag + " after " + ("%d" % (KR_Time() - KR_M21Num("TReq"))) + " ms, " + ("%d" % KR_M21Num("Frames")) + " frames of this window; " + KR_M21Files());
}
// ---- file API conventions (logged; the verifier and the report read them)
void KR_M21Paths() {
    string g = SystemService.GetGameFolderPath();
    string s = system.GetSaveFolderName();
    KR_ClaudeProbeLog("PATH game=" + g);
    KR_ClaudeProbeLog("PATH save=" + s);
    KR_ClaudeProbeLog("PATH menu=" + KR_MFolder() + " request=" + KR_MFile("request.txt"));
    KR_ClaudeProbeLog("PATH chart=" + KR_MChartFile() + " marker=" + KR_MMarkerFile());
    KR_ClaudeProbeLog("API exist_abs_exe=" + ("%d" % KR_M21B(FileOperation.ExistFile(g + "NightRemaster.exe"))) + " exist_rel_exe=" + ("%d" % KR_M21B(FileOperation.ExistFile("NightRemaster.exe"))) + " exist_save_afconfig=" + ("%d" % KR_M21B(FileOperation.ExistFile(s + "\\AFConfig.asd"))));
    KR_ClaudeProbeLog("API menu_folder_before=" + ("%d" % KR_M21B(FileOperation.ExistFolder(KR_MFolder()))));
    bool w0 = TextFile.WriteAll(KR_MFile("probe_crlf.txt"), "a\nb\n");
    KR_ClaudeProbeLog("API write_into_missing_folder=" + ("%d" % KR_M21B(w0)));
    bool mk = FileOperation.CreateFolder(KR_MFolder());
    bool w1 = TextFile.WriteAll(KR_MFile("probe_crlf.txt"), "a\nb\n");
    string back = "";
    bool r1 = TextFile.ReadAll(KR_MFile("probe_crlf.txt"), back);
    KR_ClaudeProbeLog("API create_folder=" + ("%d" % KR_M21B(mk)) + " write=" + ("%d" % KR_M21B(w1)) + " read=" + ("%d" % KR_M21B(r1)) + " length=" + ("%d" % back.Length()) + " crlf=" + ("%d" % KR_M21B(back == "a\r\nb\r\n")));
    string miss = "unchanged";
    bool r2 = TextFile.ReadAll(KR_MFile("no_such_file.txt"), miss);
    KR_ClaudeProbeLog("API read_missing=" + ("%d" % KR_M21B(r2)) + " text=" + miss + " delete_missing=" + ("%d" % KR_M21B(FileOperation.DeleteFile(KR_MFile("no_such_file.txt")))));
    bool d1 = FileOperation.DeleteFile(KR_MFile("probe_crlf.txt"));
    KR_ClaudeProbeLog("API delete=" + ("%d" % KR_M21B(d1)) + " exist_after=" + ("%d" % KR_M21B(FileOperation.ExistFile(KR_MFile("probe_crlf.txt")))));
    TextFile.WriteAll(KR_MFile("probe_sample_request.txt"), "chart\n1\n2026-09-28 03:30:00\n");
    TextFile.WriteAll("claude_probe_relative.txt", "rel\n");
    bool vo = VSFile.OpenForWrite("YoruKR_ProbeVS.dat");
    bool vw = VSFile.WriteString("reset");
    bool vi = VSFile.WriteInt(1);
    bool vc = VSFile.Close();
    int vv = 0;
    string vs = "";
    bool ro = VSFile.OpenForRead("YoruKR_ProbeVS.dat");
    bool rs = VSFile.ReadString(vs);
    bool ri = VSFile.ReadInt(vv);
    VSFile.Close();
    KR_ClaudeProbeLog("VSFILE open=" + ("%d" % KR_M21B(vo)) + " string=" + ("%d" % KR_M21B(vw)) + " int=" + ("%d" % KR_M21B(vi)) + " close=" + ("%d" % KR_M21B(vc)) + " reopen=" + ("%d" % KR_M21B(ro)) + " read=" + vs + "/" + ("%d" % vv) + " " + ("%d" % KR_M21B(rs && ri)) + " in_save=" + ("%d" % KR_M21B(FileOperation.ExistFile(s + "\\YoruKR_ProbeVS.dat"))) + " in_game=" + ("%d" % KR_M21B(FileOperation.ExistFile(g + "YoruKR_ProbeVS.dat"))));
}
// ---- poll cost: 5,000 calls each, milliseconds
void KR_M21Cost() {
    int n = 5000;
    int t0 = KR_Time();
    for (int i = 0; i < n; i++) KR_MPending();
    int t1 = KR_Time();
    for (int j = 0; j < n; j++) SystemService.SystemVariable_Get("YoruKR.M.Home");
    int t2 = KR_Time();
    string exe = SystemService.GetGameFolderPath() + "NightRemaster.exe";
    for (int k = 0; k < n; k++) FileOperation.ExistFile(exe);
    int t3 = KR_Time();
    for (int q = 0; q < n; q++) KR_MTick();
    int t4 = KR_Time();
    KR_ClaudeProbeLog("COST calls=" + ("%d" % n) + " pending_ms=" + ("%d" % (t1 - t0)) + " sysvar_get_ms=" + ("%d" % (t2 - t1)) + " existfile_hit_ms=" + ("%d" % (t3 - t2)) + " tick_armed_ms=" + ("%d" % (t4 - t3)));
}
void KR_M21Tick() {
    string stage = KR_M21Get("Stage");
    int frames = KR_M21Num("Frames") + 1;
    KR_M21Set("Frames", "%d" % frames);
    int total = KR_M21Num("Total") + 1;
    KR_M21Set("Total", "%d" % total);
    if (total > 20000) { KR_ClaudeProbeLog("STUCK stage=" + stage + " head=" + KR_M21Head()); KR_ClaudeShot("mod_stuck.bmp"); system.Exit(5); return; }
    bool home = KR_M21Home();
    string head = KR_M21Head();
    // ---------------- run A
    if (stage == "") {
        if (!home || frames < 20) return;
        KR_ClaudeProbeLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " armed=" + SystemService.SystemVariable_Get("YoruKR.M.Home") + " run=" + KR_M21Get("Run"));
        if (KR_M21Get("Run") == "C") {
            // control: the same save, nothing of r21 used; the game ends through system.Exit(0) directly (what Ａ＿ゲーム終了
            // does after its confirmation) - the files the engine itself writes on the way out
            KR_ClaudeProbeLog("CONTROL " + KR_M21Files());
            KR_ClaudeProbeLog("CONTROL EXIT (system.Exit(0) from the probe)");
            system.Exit(0);
            return;
        }
        if (KR_M21Get("Run") == "B") {
            KR_ClaudeProbeLog("B START " + KR_M21Files());
            KR_ClaudeShot("mod_home_b.bmp");
            KR_M21Request("unlock_revert");
            KR_M21Go("b_revert");
            return;
        }
        KR_M21Paths();
        KR_ClaudeShot("mod_home_before.bmp");
        KR_M21Cost();
        KR_M21Set("T0", "%d" % KR_Time());
        KR_M21Go("frames_armed");
        return;
    }
    if (stage == "frames_armed") {
        if (frames < 180) return;
        KR_ClaudeProbeLog("FRAMES armed=" + SystemService.SystemVariable_Get("YoruKR.M.Home") + " n=180 ms=" + ("%d" % (KR_Time() - KR_M21Num("T0"))));
        SystemService.SystemVariable_Set("YoruKR.M.Home", "");
        KR_M21Set("T0", "%d" % KR_Time());
        KR_M21Go("frames_disarmed");
        return;
    }
    if (stage == "frames_disarmed") {
        if (frames < 180) return;
        KR_ClaudeProbeLog("FRAMES armed=" + SystemService.SystemVariable_Get("YoruKR.M.Home") + " n=180 ms=" + ("%d" % (KR_Time() - KR_M21Num("T0"))));
        SystemService.SystemVariable_Set("YoruKR.M.Home", "1");
        KR_M21Request("chart");
        KR_M21Go("chart");
        return;
    }
    if (stage == "chart") {
        if (home) return;
        KR_M21Window("CHART");
        KR_ClaudeShot("mod_chart.bmp");
        KR_M21End("unlock1", 1);
        return;
    }
    if (stage == "unlock1") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Request("unlock_all");
        KR_M21Go("unlock1w");
        return;
    }
    if (stage == "unlock1w") {
        if (home) return;
        KR_M21Window("UNLOCK_ALL");
        KR_ClaudeShot("mod_unlock_all.bmp");
        KR_M21End("revert", 1);
        return;
    }
    if (stage == "revert") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Request("unlock_revert");
        KR_M21Go("revertw");
        return;
    }
    if (stage == "revertw") {
        if (home) return;
        KR_M21Window("UNLOCK_REVERT");
        KR_ClaudeShot("mod_unlock_revert.bmp");
        KR_M21End("unlock2", 1);
        return;
    }
    if (stage == "unlock2") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Request("unlock_all");
        KR_M21Go("unlock2w");
        return;
    }
    if (stage == "unlock2w") {
        if (home) return;
        KR_M21Window("UNLOCK_ALL_2");
        KR_M21End("unknown", 1);
        return;
    }
    if (stage == "unknown") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Request("bogus");
        KR_M21Go("unknownw");
        return;
    }
    if (stage == "unknownw") {
        if (!home) { KR_ClaudeProbeLog("UNEXPECTED WINDOW for an unknown command head=" + head); KR_ClaudeShot("mod_unexpected.bmp"); system.Exit(7); return; }
        if (frames < 30) return;
        KR_ClaudeProbeLog("UNKNOWN after 30 frames " + KR_M21Files());
        KR_ClaudeShot("mod_unknown_home.bmp");
        KR_M21Result("restore partial 1 files (from KR_reset_20260928_031500, previous kept in KR_before_restore_20260928_031501)");
        KR_M21Go("resultw");
        return;
    }
    if (stage == "resultw") {
        if (home) return;
        KR_M21Window("LAST_RESULT");
        KR_ClaudeShot("mod_last_result.bmp");
        KR_M21End("both", 1);
        return;
    }
    if (stage == "both") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Result("reset ok KR_reset_20260928_031500");
        KR_M21Request("chart");
        KR_M21Go("both1");
        return;
    }
    if (stage == "both1") {
        if (home) return;
        KR_M21Window("BOTH_1");
        KR_M21End("both2", 1);
        return;
    }
    if (stage == "both2") {
        if (home) { KR_ClaudeProbeLog("UNEXPECTED HOME after the first of two windows"); system.Exit(7); return; }
        if (frames < 5) return;
        KR_M21Window("BOTH_2");
        KR_M21End("resetno", 1);
        return;
    }
    if (stage == "resetno") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Request("reset_all");
        KR_M21Go("resetnow");
        return;
    }
    if (stage == "resetnow") {
        if (home) return;
        KR_M21Window("RESET_CONFIRM");
        KR_ClaudeShot("mod_reset_confirm.bmp");
        KR_ClaudeProbeLog("ANSWER NO reset");
        KR_M21End("resetno2", 12);
        return;
    }
    if (stage == "resetno2") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("AFTER NO reset " + KR_M21Files());
        KR_M21Request("reset_restore");
        KR_M21Go("restorenow");
        return;
    }
    if (stage == "restorenow") {
        if (home) return;
        KR_M21Window("RESTORE_CONFIRM");
        KR_ClaudeShot("mod_restore_confirm.bmp");
        KR_ClaudeProbeLog("ANSWER NO restore");
        KR_M21End("during", 12);
        return;
    }
    if (stage == "during") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("AFTER NO restore " + KR_M21Files());
        KR_M21Request("chart");
        KR_M21Go("duringw");
        return;
    }
    if (stage == "duringw") {
        if (home) return;
        if (frames == 5) { KR_M21Window("DURING_NOTICE"); KR_M21Request("unlock_revert"); return; }
        if (frames < 65) return;
        KR_ClaudeProbeLog("DURING own window after 60 frames " + KR_M21Files());
        KR_ClaudeShot("mod_own_window_pending.bmp");
        KR_M21End("duringb", 1);
        return;
    }
    if (stage == "duringb") {
        if (home) return;
        KR_M21Window("DURING_SERVED_AT_HOME");
        KR_M21End("unlock3", 1);
        return;
    }
    if (stage == "unlock3") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Request("unlock_all");
        KR_M21Go("unlock3w");
        return;
    }
    if (stage == "unlock3w") {
        if (home) return;
        KR_M21Window("UNLOCK_ALL_3");
        KR_M21End("panel", 1);
        return;
    }
    if (stage == "panel") {
        if (!home || frames < 10) return;
        int p = 2;
        KR_M21Set("Person", "%d" % p);
        KR_ClaudeProbeLog("PANEL click row person=" + ("%d" % p));
        KR_T8HomeClick(0, 40, 52 + (p + 5) * 24 + 6);
        KR_M21Go("charwin");
        return;
    }
    if (stage == "charwin") {
        if (home) return;
        if (frames == 5) { KR_M21Block("TITLE", "CHARWIN", KR_M21Title()); KR_M21Request("chart"); return; }
        if (frames < 65) return;
        KR_ClaudeProbeLog("OUTSIDE HOME character window after 60 frames head_is_ours=" + ("%d" % KR_M21B(head.Find("〓모드") == 0)) + " " + KR_M21Files());
        KR_ClaudeShot("mod_outside_home_pending.bmp");
        KR_M21End("charback", 0);
        return;
    }
    if (stage == "charback") {
        if (home) return;
        if (head.Find("〓모드") != 0) return;
        KR_M21Window("SERVED_AFTER_CHARWIN");
        KR_M21End("final", 1);
        return;
    }
    if (stage == "final") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_ClaudeShot("mod_home_after.bmp");
        KR_M21Request("reset_all");
        KR_M21Go("finalw");
        return;
    }
    if (stage == "finalw") {
        if (home) return;
        KR_M21Window("RESET_CONFIRM_YES");
        KR_ClaudeProbeLog("ANSWER YES reset (the next thing is the game's exit)");
        KR_M21End("exited", 11);
        return;
    }
    // ---------------- run B (same save folder)
    if (stage == "b_revert") {
        if (home) return;
        KR_M21Window("B_UNLOCK_REVERT");
        KR_ClaudeShot("mod_b_unlock_revert.bmp");
        KR_M21End("b_restore", 1);
        return;
    }
    if (stage == "b_restore") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME " + KR_M21Files());
        KR_M21Request("reset_restore");
        KR_M21Go("b_restorew");
        return;
    }
    if (stage == "b_restorew") {
        if (home) return;
        KR_M21Window("B_RESTORE_CONFIRM_YES");
        KR_ClaudeShot("mod_b_restore_confirm.bmp");
        KR_ClaudeProbeLog("ANSWER YES restore (the next thing is the game's exit)");
        KR_M21End("exited", 11);
        return;
    }
    if (stage == "exited") {
        KR_ClaudeProbeLog("NOT EXITED after 예 head=" + head + " " + KR_M21Files());
        KR_ClaudeShot("mod_not_exited.bmp");
        system.Exit(8);
        return;
    }
}
int KR_M21Wait(FTPARTS_WaitForClickCallback func, bool cancel) {
    KR_ClaudeProbeLog("UNEXPECTED WAIT stage=" + KR_M21Get("Stage") + " head=" + KR_M21Head());
    KR_ClaudeShot("mod_wait.bmp");
    system.Exit(6);
    return 0;
}
string KR_M21Arg(string key) {
    string s = KR_CPRead("claude_probe_args.txt");
    int at = s.Find(key + "=");
    if (at < 0) return "";
    s = KR_JosaSlice(s, at + key.Length() + 1, s.Length() - at - key.Length() - 1);
    int nl = s.Find("\n");
    if (nl >= 0) s = KR_JosaSlice(s, 0, nl);
    return s;
}
int KR_M21Main() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("SAVEFOLDER " + system.GetSaveFolderName());
    string save = KR_M21Arg("save");
    KR_M21Set("Run", KR_M21Arg("run"));
    if (save == "") { KR_ClaudeProbeLog("NO SAVE ARGUMENT"); system.Exit(3); return 3; }
    KR_ClaudeProbeLog("resume loading " + save + " run=" + KR_M21Get("Run"));
    system.ResumeLoad("@@KEY@@", save);
    system.Exit(2);
    return 2;
}
'''


def build_probe_r21(source, key, work, extra='', tick='KR_M21Tick', stem='probe_r21'):
    """The r21 probe AIN: candidate + R21_JAF; MAIN -> KR_M21Main; config::detail::SetMute forced; every C_UserInputManager::Is*
    query returns 0 (no input at all); C_SelectDialog@_Update gets the prefix KR_M21Tick (the candidate's body, so the r21
    site KR_MTick stays in it); every AFL_Parts_WaitForClick site except C_SelectDialog@Run -> KR_M21Wait (log + exit 6)."""
    src = source / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + R21_JAF.replace('@@KEY@@', key) + '\n' + extra
    assert '@@' not in jaf, re.findall(r'@@\w+@@', jaf)
    jaf = L.jaf_literal_encode(jaf)
    (work / (stem + '.jaf')).write_text(jaf, 'utf8')
    decl = work / (stem + '_declared.ain')
    L.cmd('ain', 'edit', '--jaf', work / (stem + '.jaf'), '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / (stem + '_declared_meta.json'), decl)
    dm = L.read_meta(work / (stem + '_declared_meta.json'))
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    patch += [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]
    for f in added:
        path = work / f"{stem}_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), f['name']))
    upd = L.fid_of(m, 'C_SelectDialog@_Update')
    path = work / f'original_{upd}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SelectDialog@_Update', '-o', path, src)
    body = path.read_text('utf8')
    assert 'CALLFUNC KR_MTick' in body, 'the candidate _Update has no r21 site'
    patch.append(L.begin(L.clean(body, 'C_SelectDialog@_Update'), '\tCALLFUNC %s\n' % tick))
    (work / (stem + '.jam')).write_text('\n'.join(patch), 'utf8')
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / (stem + '.jam'), '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_M21Main'])
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
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, ids['KR_M21Wait'])
                waits.append((name, 'exit'))
    assert sum(1 for _, k in waits if k == 'live') == 1, waits
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(waits=len(waits), tick_prefix='C_SelectDialog@_Update', tick=tick, probe_sha256=L.sha(out))


R21_SAVE_KEEP = ['AFConfig.asd', 'CommonSystemData.sav', 'Volume.sav', 'WindowSetting.sav', 'MouseCursorSetting.sav', 'ShowDPSetting.sav',
                 '3DConfig.vsf', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup']


def folder_hashes(d):
    return {p.relative_to(d).as_posix(): L.sha(p) for p in sorted(d.rglob('*')) if p.is_file()} if d.exists() else {}


def run_r21(savedir, save, run, stamp):
    """One r21 run in `savedir` (made by the caller; run B reuses run A's)."""
    set_savefolder(savedir.name)
    for b in RUN.glob('mod_*.bmp'):
        b.unlink()
    (RUN / 'claude_probe_args.txt').write_bytes(('save=' + save + '\nrun=' + run + '\n').encode('cp932'))
    t0 = time.time()
    result = launch(timeout=600)
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result.update(save=save, run=run, save_folder=str(savedir))
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(RUN.glob('mod_*.bmp')):
        png = dest / (b.stem + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(png.name)
    result['shots_taken'] = shots
    return result


def r21_blocks(log):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'(TITLE) (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            out[z.group(2)] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    return out


def main_r21():
    ptr, rt = L.runtime()
    assert L.sha(rt / 'NightRemaster.ain') == L.BASE_AIN_SHA, 'runtime moved since the candidate was built'
    man = L.readj(O / 'manifest.json')
    assert L.sha(O / 'NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    assert shutil.disk_usage('P:\\').free >= 10 * 1024 ** 3, 'P: free space below 10 GB'
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    work = PROBE / f'build_{stamp}_r21'
    work.mkdir(parents=True)
    user_before = user_state()
    alice_dir = L.SAVES.parent
    alice_before = tree_listing(alice_dir)
    playing_before = user_game_running()
    rt = setup_folder()
    menu = RUN / 'KRMenu'
    if menu.exists():
        shutil.rmtree(menu)
    for n in ['claude_probe_relative.txt']:
        if (RUN / n).exists():
            (RUN / n).unlink()
    key = L.save_records(L.save_path(R21_BOOT_SAVE))['key']
    info = build_probe_r21(O, key, work)
    savedir = RUN / f'SaveData_R24CalTourProbe_{stamp}'
    savedir.mkdir(parents=True)
    files = L.save_manifest()['files']
    for n in COPY_GLOBAL:
        if n in files:
            shutil.copy2(L.save_path(n), savedir / n)
    shutil.copy2(L.save_path(R21_BOOT_SAVE), savedir / R21_BOOT_SAVE)
    before = folder_hashes(savedir)
    (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=man['files']['NightRemaster.ain']['sha256'],
        probe_sha256=info['probe_sha256'], audio=AUDIO_POLICY, save=R21_BOOT_SAVE, mode='r21', author=L.AUTHOR,
        input='Resume of a copied home save; user input patched off; the request / result files written by the probe tick exactly as '
              'the hook writes them; dialogs answered with EndWaitForClick codes (1 확인, 11 예, 12 아니요, 0 닫기).'), ensure_ascii=False, indent=1), 'utf8')
    runs = []
    for run in ('A', 'B'):
        r = run_r21(savedir, R21_BOOT_SAVE, run, stamp)
        r['files_after'] = dict(save=folder_hashes(savedir), menu=folder_hashes(menu))
        r['bytes_after'] = {n: (savedir / n).read_bytes().decode('latin-1') for n in ['YoruKR_reset.marker', 'YoruKR_Chart.dat', 'YoruKR_ProbeVS.dat'] if (savedir / n).exists()}
        r['menu_bytes_after'] = {p.name: p.read_bytes().decode('latin-1') for p in sorted(menu.glob('*'))} if menu.exists() else {}
        print('run', run, 'exit', r.get('exit_code'), r['seconds'], 's', 'shots', len(r['shots_taken']), 'last', (r['log'] or [''])[-1][:80], flush=True)
        runs.append(r)
    after = folder_hashes(savedir)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    # run C (control): a fresh copy of the same files, nothing of r21 used, the game ends through system.Exit(0) directly
    ctrl = RUN / f'SaveData_R24CalTourProbe_{stamp}_control'
    ctrl.mkdir(parents=True)
    for n in COPY_GLOBAL:
        if n in files:
            shutil.copy2(L.save_path(n), ctrl / n)
    shutil.copy2(L.save_path(R21_BOOT_SAVE), ctrl / R21_BOOT_SAVE)
    cbefore = folder_hashes(ctrl)
    rc = run_r21(ctrl, R21_BOOT_SAVE, 'C', stamp)
    cafter = folder_hashes(ctrl)
    cchanged = sorted(k for k in set(cbefore) | set(cafter) if cbefore.get(k) != cafter.get(k))
    print('run C exit', rc.get('exit_code'), rc['seconds'], 's', 'last', (rc['log'] or [''])[-1][:80], flush=True)

    def norm(names):
        return sorted({re.sub(r'^Backup/\d{4}_\d\d_\d\d_\d\d_\d\d_\d\d/', 'Backup/<time>/', k) for k in names})
    ours = {'YoruKR_Chart.dat', 'YoruKR_reset.marker', 'YoruKR_ProbeVS.dat'}
    engine_exit = dict(tour_changed_not_ours=norm(k for k in changed if k not in ours), control_changed=norm(cchanged),
                       same_set=norm(k for k in changed if k not in ours) == norm(cchanged), control_exit_code=rc.get('exit_code'),
                       control_log=rc['log'][-3:], note='files the engine itself writes when the game ends (CommonSystemData / Volume / '
                                                          'WindowSetting, its Backup\\<time>\\ copy): the same set with and without r21')
    user_after = user_state()
    playing_after = user_game_running()
    rel = RUN / 'claude_probe_relative.txt'
    result = dict(schema='yoru-feeling-r23.caltour.probe.v1', author=L.AUTHOR, candidate_sha256=man['files']['NightRemaster.ain']['sha256'],
                  probe=info, save=R21_BOOT_SAVE, save_folder=str(savedir), runs=runs,
                  save_folder_before=before, save_folder_after=after, save_folder_changed=changed, engine_exit_writes=engine_exit,
                  control_run=dict(exit_code=rc.get('exit_code'), seconds=rc.get('seconds'), log=rc['log'], vm_error=rc.get('vm_error'),
                                   message=rc.get('message'), save_folder=str(ctrl)),
                  save_slot_unchanged=before.get(R21_BOOT_SAVE) == after.get(R21_BOOT_SAVE),
                  settings_unchanged={n: before.get(n) == after.get(n) for n in R21_SAVE_KEEP if n in before},
                  sample_request_bytes=(menu / 'probe_sample_request.txt').read_bytes().decode('latin-1') if (menu / 'probe_sample_request.txt').exists() else None,
                  relative_textfile_lands_in_game_folder=rel.exists(),
                  user_save_folder_unchanged=user_after == user_before, user_save_files=len(user_before),
                  user_save_folder_changed_files=sorted(k for k in set(user_before) | set(user_after) if user_before.get(k) != user_after.get(k)),
                  user_game_running=dict(before=playing_before, after=playing_after),
                  c_drive_alicesoft_changes=sorted(set(tree_listing(alice_dir).items()) ^ set(alice_before.items()))[:20])
    L.writej(L.EVID / 'probe_r21.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('runs', 'save_folder_before', 'save_folder_after')}, ensure_ascii=False, indent=1))
    assert all(Path(next(l for l in r['log'] if l.startswith('SAVEFOLDER '))[len('SAVEFOLDER '):]).resolve() == savedir.resolve() for r in runs), 'a run saved elsewhere'
    assert result['user_save_folder_unchanged'] or (playing_before or playing_after), 'user save folder changed while the user game was not running'


# ============================================================== r21 + the real hook (python probe_modmenu_r21.py --integrated)
# The probe copy's winmm.dll is replaced by the mod-menu hook's DIAGNOSTIC build for these runs only (the runtime's DLL, which
# the copy started with, is kept in probe/ and put back at the end). One copied home save, one P: save folder, three runs:
#   I1: home -> the driver installs the hook's menu (WM_INITMENU) and posts 「이벤트 플로우 차트」, 「전체 개방」, 「전체 개방 되돌리기」
#       (WM_COMMAND id) -> the hook writes request.txt -> the game's windows; 「전체 리셋」 -> the hook's MessageBox -> 아니오 (no
#       request); 「전체 리셋」 -> MessageBox 예 -> request -> the game's confirmation 예 -> marker + reset.req -> the game's exit
#   I2: restart -> the hook (first timer call, before the engine reads its global files) backs up + deletes the 8 global files ->
#       last_result -> the game's result window -> 「전체 리셋 되돌리기」 -> MessageBox 예 -> the game's confirmation 예 -> exit
#   I3: restart -> the hook restores the newest backup -> last_result -> the game's result window -> home -> the probe ends (77)
# The probe tick (prefix of C_SelectDialog@_Update) drives the game's own windows and tells the driver when the home menu is ready
# (run\claude_probe_state.txt 「READY n action」); the driver (this script, inside the debugger loop, never blocking on the game)
# posts the menu commands and answers the MessageBox (run\claude_probe_driver.txt 「DONE action」).
HOOK_DIAG = L.FLOW / 'hook_modmenu' / 'build_diagnostic' / 'winmm.dll'
HOOK_DIAG_SHA = 'ae9f5a2bb10bef522ef02d7007ccc91079a851b794b33f636b12127b29fd3646'
HOOK_RELEASE_SHA = 'cd16d367794c5c608350f97e282f9e15281edbfe1b564566dedef2b074e3a187'
GLOBAL8 = ['NightRAFInfo.asd', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
           'NightRMsgSkip.msk', 'CommonGameData.asd', 'YoruKR_HomeRate.dat']
SETTINGS = ['AFConfig.asd', 'CommonSystemData.sav', 'Volume.sav', 'WindowSetting.sav', 'MouseCursorSetting.sav', 'ShowDPSetting.sav',
            '3DConfig.vsf', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup']
ENGINE_EXIT_WRITES = {'CommonSystemData.sav', 'Volume.sav', 'WindowSetting.sav'}     # the r21 tour's control run (engine, every exit)
INT_JAF = r'''
void KR_M22Ready(string action) {
    int n = KR_M21Num("ReadyN") + 1;
    KR_M21Set("ReadyN", "%d" % n);
    KR_M21Set("TReq", "%d" % KR_Time());
    KR_ClaudeProbeLog("READY " + ("%d" % n) + " " + action + " " + KR_M21Files());
    TextFile.WriteAll("claude_probe_state.txt", "READY " + ("%d" % n) + " " + action);
}
string KR_M22Driver() {
    string s = KR_CPRead("claude_probe_driver.txt");
    int nl = s.Find("\n");
    if (nl >= 0) s = KR_JosaSlice(s, 0, nl);
    int cr = s.Find("\r");
    if (cr >= 0) s = KR_JosaSlice(s, 0, cr);
    return s;
}
void KR_M22Panel(string tag) { KR_M21Block("PANEL", tag, KR_RateText()); }
void KR_M22Fail(string why, int code) {
    KR_ClaudeProbeLog("FAIL " + why + " stage=" + KR_M21Get("Stage") + " head=" + KR_M21Head() + " " + KR_M21Files());
    KR_ClaudeShot("int_fail.bmp");
    system.Exit(code);
}
void KR_M22Tick() {
    string stage = KR_M21Get("Stage");
    int frames = KR_M21Num("Frames") + 1;
    KR_M21Set("Frames", "%d" % frames);
    int total = KR_M21Num("Total") + 1;
    KR_M21Set("Total", "%d" % total);
    if (total > 60000) { KR_M22Fail("STUCK", 5); return; }
    bool home = KR_M21Home();
    string head = KR_M21Head();
    bool ours = KR_M21Title() != "" && (head.Find("〓모드") == 0 || head.Find("〓전체") == 0);
    string run = KR_M21Get("Run");
    if (stage == "") {
        if (run == "I1") {
            if (!home || frames < 20) return;
            KR_ClaudeProbeLog("HOME I1 date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " armed=" + SystemService.SystemVariable_Get("YoruKR.M.Home") + " menu=" + KR_MFolder() + " save=" + system.GetSaveFolderName());
            KR_M22Panel("I1_HOME");
            KR_ClaudeShot("int_home_1.bmp");
            KR_M22Ready("chart");
            KR_M21Go("w_chart");
            return;
        }
        // I2 / I3: the hook left last_result.txt before the game started -> the first home menu shows it
        if (ours) {
            string tag = "RESET_RESULT";
            string file = "int_reset_result.bmp";
            string next = "i2home";
            if (run == "I3") { tag = "RESTORE_RESULT"; file = "int_restore_result.bmp"; next = "i3home"; }
            KR_ClaudeProbeLog("HOME " + run + " date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " save=" + system.GetSaveFolderName());
            KR_M21Window(tag);
            KR_M22Panel(tag);
            KR_ClaudeShot(file);
            KR_M21End(next, 1);
            return;
        }
        if (home && frames > 900) KR_M22Fail("NO RESULT WINDOW (the hook left no last_result?)", 72);
        return;
    }
    if (stage == "w_chart" || stage == "w_unlock" || stage == "w_revert") {
        if (!ours) { if (frames > 1800) KR_M22Fail("NO WINDOW after the menu command", 73); return; }
        string tag2 = "CHART";
        string file2 = "int_chart.bmp";
        string next2 = "home2";
        if (stage == "w_unlock") { tag2 = "UNLOCK_ALL"; file2 = "int_unlock_all.bmp"; next2 = "home3"; }
        if (stage == "w_revert") { tag2 = "UNLOCK_REVERT"; file2 = "int_unlock_revert.bmp"; next2 = "home4"; }
        KR_M21Window(tag2);
        KR_ClaudeShot(file2);
        KR_M21End(next2, 1);
        return;
    }
    if (stage == "home2" || stage == "home3") {
        if (!home || frames < 10) return;
        if (stage == "home2") { KR_M22Ready("unlock_all"); KR_M21Go("w_unlock"); }
        else { KR_M22Ready("unlock_revert"); KR_M21Go("w_revert"); }
        return;
    }
    if (stage == "home4") {
        if (!home || frames < 10) return;
        KR_M22Ready("reset_no");
        KR_M21Go("w_reset_no");
        return;
    }
    if (stage == "w_reset_no") {
        if (ours) { KR_M22Fail("A WINDOW after the MessageBox 아니오", 74); return; }
        if (KR_M22Driver() != "DONE reset_no") { if (frames > 3600) KR_M22Fail("the driver never answered", 75); return; }
        if (KR_M21Get("TNo") == "") { KR_M21Set("TNo", "%d" % frames); return; }
        if (frames - KR_M21Num("TNo") < 60) return;
        KR_ClaudeProbeLog("AFTER MESSAGEBOX NO 60 frames home=" + ("%d" % KR_M21B(home)) + " " + KR_M21Files());
        KR_ClaudeShot("int_after_msgbox_no.bmp");
        KR_M21Go("home5");
        return;
    }
    if (stage == "home5") {
        if (!home || frames < 10) return;
        KR_M22Ready("reset_yes");
        KR_M21Go("w_reset");
        return;
    }
    if (stage == "w_reset" || stage == "w_restore") {
        if (!ours) { if (frames > 3600) KR_M22Fail("NO CONFIRMATION after the MessageBox 예", 76); return; }
        if (stage == "w_reset") {
            KR_M21Window("RESET_CONFIRM");
            KR_ClaudeShot("int_reset_confirm.bmp");
            KR_ClaudeProbeLog("ANSWER YES reset (the next thing is the game's exit)");
        }
        else {
            KR_M21Window("RESTORE_CONFIRM");
            KR_ClaudeShot("int_restore_confirm.bmp");
            KR_ClaudeProbeLog("ANSWER YES restore (the next thing is the game's exit)");
        }
        KR_M21End("exited", 11);
        return;
    }
    if (stage == "i2home") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME I2 " + KR_M21Files());
        KR_M22Panel("I2_HOME");
        KR_ClaudeShot("int_home_after_reset.bmp");
        KR_M22Ready("restore_yes");
        KR_M21Go("w_restore");
        return;
    }
    if (stage == "i3home") {
        if (!home || frames < 10) return;
        KR_ClaudeProbeLog("BACK HOME I3 " + KR_M21Files());
        KR_M22Panel("I3_HOME");
        KR_ClaudeShot("int_home_after_restore.bmp");
        KR_ClaudeProbeLog("END INTEGRATED");
        system.Exit(77);
        return;
    }
    if (stage == "exited") {
        if (frames < 600) return;
        KR_M22Fail("NOT EXITED after 예", 8);
        return;
    }
}
'''


def launch_driven(driver, timeout=900):
    """launch() with a driver: the debugger loop waits at most 100 ms per event and gives the driver a turn after every event
    it continued (and every empty wait). The driver only posts messages and reads windows / files (it never waits on the game
    thread), so a debug event can never dead-lock it."""
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
    driver.attach(pid)

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
            if not K.WaitForDebugEvent(event, 100):
                driver.tick()
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
            driver.tick()
        else:
            result['timeout'] = True
    finally:
        K.TerminateProcess(handle, 99)
        driver.detach()
    return result


class HookDriver:
    """Plays the user at the menu bar: installs the hook's 「모드」 menu (WM_INITMENU, as opening the menu bar does), posts the
    item's WM_COMMAND, answers the hook's MessageBox (#32770) with IDYES / IDNO, captures it (PrintWindow, on a worker thread
    so the debugger loop never waits on the game). Every action is logged with a timestamp."""
    WM_COMMAND, WM_INITMENU = 0x111, 0x116
    NAMES = ['chart', 'unlock_all', 'unlock_revert', 'reset_all', 'reset_restore']
    TITLES = {'reset_all': '전체 리셋', 'reset_restore': '전체 리셋 되돌리기'}

    def __init__(self, shots_dir, tag):
        import threading
        self.threading = threading
        self.U = C.WinDLL('user32', use_last_error=True)
        self.G = C.WinDLL('gdi32', use_last_error=True)
        self.U.GetMenu.restype = W.HMENU
        self.U.GetSubMenu.restype = W.HMENU
        self.U.GetSubMenu.argtypes = [W.HMENU, C.c_int]
        self.U.GetMenuItemCount.argtypes = [W.HMENU]
        self.U.GetMenuItemID.argtypes = [W.HMENU, C.c_int]
        self.U.GetMenuItemID.restype = W.UINT
        self.U.GetMenuStringW.argtypes = [W.HMENU, W.UINT, W.LPWSTR, C.c_int, W.UINT]
        self.U.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
        self.U.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
        self.U.GetMenu.argtypes = [W.HWND]
        self.U.GetDC.restype = C.c_void_p
        self.U.GetDC.argtypes = [C.c_void_p]
        self.U.ReleaseDC.argtypes = [C.c_void_p, C.c_void_p]
        self.U.PrintWindow.argtypes = [W.HWND, C.c_void_p, W.UINT]
        self.U.GetWindowRect.argtypes = [W.HWND, C.POINTER(W.RECT)]
        self.G.CreateCompatibleDC.restype = C.c_void_p
        self.G.CreateCompatibleDC.argtypes = [C.c_void_p]
        self.G.CreateCompatibleBitmap.restype = C.c_void_p
        self.G.CreateCompatibleBitmap.argtypes = [C.c_void_p, C.c_int, C.c_int]
        self.G.SelectObject.restype = C.c_void_p
        self.G.SelectObject.argtypes = [C.c_void_p, C.c_void_p]
        self.G.GetDIBits.argtypes = [C.c_void_p, C.c_void_p, W.UINT, W.UINT, C.c_void_p, C.c_void_p, W.UINT]
        self.G.DeleteObject.argtypes = [C.c_void_p]
        self.G.DeleteDC.argtypes = [C.c_void_p]
        self.shots_dir = shots_dir
        self.tag = tag
        self.log = []
        self.state = 'idle'
        self.last_ready = 0
        self.pid = None
        self.hwnd = None
        self.ids = None
        self.items = None
        self.action = None
        self.deadline = 0
        self.capture = None
        self.box = None
        for n in ('claude_probe_state.txt', 'claude_probe_driver.txt'):
            if (RUN / n).exists():
                (RUN / n).unlink()

    def note(self, *a):
        self.log.append('%s %s' % (datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3], ' '.join(str(x) for x in a)))

    def attach(self, pid):
        self.pid = pid
        self.note('attach pid', pid)

    def detach(self):
        if self.capture is not None:
            self.capture.join(5)
        self.note('detach state', self.state)

    def windows(self, cls=None):
        out = []
        proto = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

        def cb(h, _):
            pid = W.DWORD()
            self.U.GetWindowThreadProcessId(h, C.byref(pid))
            if pid.value == self.pid:
                buf = C.create_unicode_buffer(256)
                self.U.GetClassNameW(h, buf, 256)
                if cls is None or buf.value == cls:
                    t = C.create_unicode_buffer(256)
                    self.U.GetWindowTextW(h, t, 256)
                    out.append((h, buf.value, t.value))
            return True
        self.U.EnumWindows(proto(cb), 0)
        return out

    def game_window(self):
        for h, cls, title in self.windows():
            if cls != '#32770' and self.U.GetMenu(h):
                return h
        return None

    def menu_items(self):
        bar = self.U.GetMenu(self.hwnd)
        n = self.U.GetMenuItemCount(bar)
        tops = []
        for i in range(n):
            buf = C.create_unicode_buffer(256)
            self.U.GetMenuStringW(bar, i, buf, 256, 0x400)
            tops.append(buf.value)
        return bar, tops

    def read_ids(self):
        bar, tops = self.menu_items()
        k = next((i for i, t in enumerate(tops) if t.endswith('(&M)')), None)
        if k is None:
            return None
        pop = self.U.GetSubMenu(bar, k)
        items = []
        ids = []
        for j in range(self.U.GetMenuItemCount(pop)):
            mid = self.U.GetMenuItemID(pop, j)
            buf = C.create_unicode_buffer(256)
            self.U.GetMenuStringW(pop, j, buf, 256, 0x400)
            items.append(('%04X' % mid if mid != 0xFFFFFFFF else '----', buf.value))
            if 0x7E10 <= mid <= 0x7EFF:
                ids.append(mid)
        self.items = dict(top=tops, mod=items)
        return ids

    def post(self, h, msg, wp, lp=0):
        ok = self.U.PostMessageW(h, msg, wp, lp)
        self.note('post', hex(h), hex(msg), hex(wp), 'ok' if ok else 'FAILED %d' % C.get_last_error())
        return ok

    def grab(self, h, name):
        """PrintWindow of the MessageBox into a PNG (worker thread: PrintWindow waits on the box's thread)."""
        def work():
            try:
                from PIL import Image
                r = W.RECT()
                self.U.GetWindowRect(h, C.byref(r))
                w, hh = r.right - r.left, r.bottom - r.top
                sdc = self.U.GetDC(0)
                mdc = self.G.CreateCompatibleDC(sdc)
                bmp = self.G.CreateCompatibleBitmap(sdc, w, hh)
                self.G.SelectObject(mdc, bmp)
                ok = self.U.PrintWindow(h, mdc, 2)
                bi = (C.c_uint32 * 10)(40, w, -hh, 1 | (32 << 16), 0, 0, 0, 0, 0, 0)
                buf = C.create_string_buffer(w * hh * 4)
                self.G.GetDIBits(mdc, bmp, 0, hh, buf, bi, 0)
                Image.frombuffer('RGBA', (w, hh), buf.raw, 'raw', 'BGRA', 0, 1).convert('RGB').save(self.shots_dir / name)
                self.G.DeleteObject(bmp)
                self.G.DeleteDC(mdc)
                self.U.ReleaseDC(0, sdc)
                self.note('captured', name, w, hh, 'printwindow', ok)
            except Exception as ex:          # the capture is evidence only
                self.note('capture failed', name, repr(ex)[:120])
        self.capture = self.threading.Thread(target=work, daemon=True)
        self.capture.start()

    def done(self, action):
        (RUN / 'claude_probe_driver.txt').write_text('DONE ' + action + '\n', 'ascii')
        self.note('done', action)

    def tick(self):
        try:
            self._tick()
        except Exception as ex:
            self.note('driver error', repr(ex)[:200])
            self.state = 'error'

    def _tick(self):
        now = time.monotonic()
        if self.state == 'idle':
            f = RUN / 'claude_probe_state.txt'
            if not f.exists():
                return
            z = re.match(r'READY (\d+) (\w+)', f.read_text('ascii', 'replace'))
            if not z or int(z.group(1)) <= self.last_ready:
                return
            self.last_ready = int(z.group(1))
            self.action = z.group(2)
            self.note('ready', self.last_ready, self.action)
            self.hwnd = self.hwnd or self.game_window()
            if self.ids is None:
                bar, tops = self.menu_items()
                self.note('menu bar before', tops)
                self.post(self.hwnd, self.WM_INITMENU, bar)
                self.state, self.deadline = 'menu', now + 10
                return
            self.fire(now)
            return
        if self.state == 'menu':
            ids = self.read_ids()
            if ids and len(ids) == 5:
                self.ids = ids
                self.note('menu installed', self.items)
                self.fire(now)
            elif now > self.deadline:
                self.note('menu not installed', self.menu_items()[1])
                self.state = 'error'
            return
        if self.state == 'box':
            if self.box is None:
                title = self.TITLES[self.cmd]
                found = [h for h, cls, t in self.windows('#32770') if t == title]
                if found:
                    self.box = found[0]
                    self.note('messagebox', hex(self.box), title)
                    self.grab(self.box, 'msgbox_%s_%s.png' % (self.cmd, 'yes' if self.answer == 6 else 'no'))
                    self.box_seen = now
                elif now > self.deadline:
                    self.note('no messagebox', title)
                    self.state = 'error'
                return
            if self.capture is not None and self.capture.is_alive() and now - self.box_seen < 3:
                return
            self.post(self.box, self.WM_COMMAND, self.answer)
            if self.action == 'reset_no':
                self.done('reset_no')
            self.box = None
            self.state = 'idle'
            return

    def fire(self, now):
        cmd = {'reset_no': 'reset_all', 'reset_yes': 'reset_all', 'restore_yes': 'reset_restore'}.get(self.action, self.action)
        self.cmd = cmd
        self.post(self.hwnd, self.WM_COMMAND, self.ids[self.NAMES.index(cmd)])
        if cmd in self.TITLES:
            self.answer = 7 if self.action == 'reset_no' else 6
            self.state, self.deadline, self.box = 'box', now + 10, None
        else:
            self.state = 'idle'


def int_blocks(log):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'(TITLE|PANEL) (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            out[(z.group(1), z.group(2))] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    return out


def main_integrated():
    ptr, rt = L.runtime()
    assert L.sha(rt / 'NightRemaster.ain') == L.BASE_AIN_SHA, 'runtime moved since the candidate was built'
    man = L.readj(O / 'manifest.json')
    cand_sha = man['files']['NightRemaster.ain']['sha256']
    assert L.sha(O / 'NightRemaster.ain') == cand_sha
    assert L.sha(HOOK_DIAG) == HOOK_DIAG_SHA, ('the hook diagnostic build moved', L.sha(HOOK_DIAG))
    assert shutil.disk_usage('P:\\').free >= 10 * 1024 ** 3, 'P: free space below 10 GB'
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    work = PROBE / f'build_{stamp}_integrated'
    work.mkdir(parents=True)
    ev = L.EVID / 'integrated'
    if ev.exists():
        shutil.rmtree(ev)
    ev.mkdir(parents=True)
    user_before = user_state()
    alice_dir = L.SAVES.parent
    alice_before = tree_listing(alice_dir)
    playing_before = user_game_running()
    rt = setup_folder()
    # the probe copy's DLL: kept (it is the runtime's), replaced by the hook's diagnostic build for these runs, put back at the end
    kept = PROBE / 'winmm_runtime_copy_kept.dll'
    shutil.copy2(RUN / 'winmm.dll', kept)
    original_sha = L.sha(kept)
    assert original_sha == L.sha(rt / 'winmm.dll')
    shutil.copy2(HOOK_DIAG, RUN / 'winmm.dll')
    assert L.sha(RUN / 'winmm.dll') == HOOK_DIAG_SHA
    menu = RUN / 'KRMenu'
    if menu.exists():
        shutil.rmtree(menu)
    hooklog = RUN / 'hangul_ime_hook.log'
    if hooklog.exists():
        hooklog.unlink()
    key = L.save_records(L.save_path(R21_BOOT_SAVE))['key']
    info = build_probe_r21(O, key, work, extra=INT_JAF, tick='KR_M22Tick', stem='probe_integrated')
    savedir = RUN / f'SaveData_R21Integrated_{stamp}'
    savedir.mkdir(parents=True)
    files = L.save_manifest()['files']
    for n in COPY_GLOBAL:
        if n in files:
            shutil.copy2(L.save_path(n), savedir / n)
    shutil.copy2(L.save_path(R21_BOOT_SAVE), savedir / R21_BOOT_SAVE)
    (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=cand_sha, probe_sha256=info['probe_sha256'],
        audio=AUDIO_POLICY, save=R21_BOOT_SAVE, mode='integrated', hook=str(HOOK_DIAG), hook_sha256=HOOK_DIAG_SHA, author=L.AUTHOR,
        input='Resume of a copied home save; user input patched off; the game\'s own windows answered by the probe tick (EndWaitForClick); '
              'the menu-bar commands and the hook\'s MessageBox driven from outside by the debugger loop (PostMessage).'), ensure_ascii=False, indent=1), 'utf8')
    snaps = {'start': folder_hashes(savedir)}
    menus = {}
    runs = []
    try:
        for run in ('I1', 'I2', 'I3'):
            set_savefolder(savedir.name)
            for b in RUN.glob('int_*.bmp'):
                b.unlink()
            snaps['before_' + run] = folder_hashes(savedir)
            menus['before_' + run] = {p.name: p.read_bytes().decode('latin-1') for p in sorted(menu.glob('*'))} if menu.exists() else {}
            (RUN / 'claude_probe_args.txt').write_bytes(('save=' + R21_BOOT_SAVE + '\nrun=' + run + '\n').encode('cp932'))
            drv = HookDriver(ev, run)
            t0 = time.time()
            r = launch_driven(drv, timeout=600)
            r['seconds'] = round(time.time() - t0, 1)
            log = RUN / 'claude_probe.txt'
            r['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
            r['driver'] = drv.log
            r['menu_items'] = drv.items
            r['run'] = run
            from PIL import Image
            shots = []
            for b in sorted(RUN.glob('int_*.bmp')):
                png = ev / (b.stem + '.png')
                Image.open(b).save(png)
                b.unlink()
                shots.append(png.name)
            r['shots_taken'] = shots
            snaps['after_' + run] = folder_hashes(savedir)
            menus['after_' + run] = {p.name: p.read_bytes().decode('latin-1') for p in sorted(menu.glob('*'))} if menu.exists() else {}
            r['bytes_after'] = {n: (savedir / n).read_bytes().decode('latin-1') for n in ['YoruKR_reset.marker', 'YoruKR_Chart.dat'] if (savedir / n).exists()}
            print('run', run, 'exit', r.get('exit_code'), r['seconds'], 's', 'shots', len(shots), 'last', (r['log'] or [''])[-1][:70],
                  'driver', (drv.log or [''])[-1][:80], flush=True)
            runs.append(r)
            if r.get('exit_code') not in (0, 77):
                break
    finally:
        shutil.copy2(kept, RUN / 'winmm.dll')
        assert L.sha(RUN / 'winmm.dll') == original_sha
    if hooklog.exists():
        shutil.copy2(hooklog, ev / 'hangul_ime_hook.log')
    backups = {}
    for d in sorted((savedir / 'Backup').glob('KR_*')) if (savedir / 'Backup').exists() else []:
        backups[d.name] = {p.name: L.sha(p) for p in sorted(d.iterdir()) if p.is_file()}
        if (d / 'manifest.txt').exists():
            backups[d.name]['manifest.txt:text'] = (d / 'manifest.txt').read_text('ascii', 'replace')
    user_after = user_state()
    playing_after = user_game_running()
    result = dict(schema='yoru-feeling-r23.caltour.integrated.v1', author=L.AUTHOR, candidate_sha256=cand_sha, probe=info, hook=str(HOOK_DIAG),
                  hook_sha256=HOOK_DIAG_SHA, hook_release_sha256=HOOK_RELEASE_SHA, runtime_winmm_sha256=original_sha,
                  probe_copy_winmm_after=L.sha(RUN / 'winmm.dll'), save=R21_BOOT_SAVE, save_folder=str(savedir), runs=runs,
                  snapshots=snaps, menu_files=menus, backups=backups,
                  hook_log=[l for l in (hooklog.read_text('ascii', 'replace').splitlines() if hooklog.exists() else []) if ' mod_' in l or 'iat_hooks' in l],
                  user_save_folder_unchanged=user_after == user_before, user_save_files=len(user_before),
                  user_save_folder_changed_files=sorted(k for k in set(user_before) | set(user_after) if user_before.get(k) != user_after.get(k)),
                  user_game_running=dict(before=playing_before, after=playing_after),
                  c_drive_alicesoft_changes=sorted(set(tree_listing(alice_dir).items()) ^ set(alice_before.items()))[:20])
    result['checks'] = integrated_checks(result, savedir)
    result['pass'] = all(v is True for v in result['checks'].values())
    L.writej(ev / 'probe_integrated.json', result)
    for r in runs:
        (ev / ('probe_log_%s.txt' % r['run'])).write_text('\n'.join(r['log']) + '\n', 'utf8')
        (ev / ('driver_log_%s.txt' % r['run'])).write_text('\n'.join(r['driver']) + '\n', 'utf8')
    L.writej(ev / 'hashes.json', dict(checked=datetime.datetime.now().astimezone().isoformat(),
                                      files={p.name: L.sha(p) for p in sorted(ev.iterdir()) if p.is_file() and p.name != 'hashes.json'}))
    print(json.dumps(dict(checks=result['checks'], passed=result['pass'], backups=list(backups)), ensure_ascii=False, indent=1))
    assert result['pass'], [k for k, v in result['checks'].items() if v is not True]


def integrated_checks(res, savedir):
    """Everything the coordinator asked for, stated as booleans (the verifier and publish --verify read them)."""
    runs = {r['run']: r for r in res['runs']}
    c = {}
    c['three_runs'] = set(runs) == {'I1', 'I2', 'I3'}
    if not c['three_runs']:
        return c
    i1, i2, i3 = runs['I1'], runs['I2'], runs['I3']
    c['no_engine_error'] = all(not r.get('vm_error') and not r.get('message') and not r.get('timeout') and not r.get('events') for r in runs.values())
    # the process exit code does not carry system.Exit's argument (the probe's own Exit(77) also ends with 0, first run 04:42):
    # which exit it was is read from the log - the last line before the process ended
    c['exits'] = all(r.get('exit_code') == 0 for r in (i1, i2, i3)) and i3['log'][-1] == 'END INTEGRATED'
    c['exit_right_after_yes'] = i1['log'][-1].startswith('ANSWER YES reset') and i2['log'][-1].startswith('ANSWER YES restore')
    mod = (i1.get('menu_items') or {}).get('mod') or []
    top = (i1.get('menu_items') or {}).get('top') or []
    c['menu_shape'] = len(top) == 3 and top[1].endswith('(&M)') and len(mod) == 6 and [m for m, _ in mod if m.startswith('7E')] == ['7E10', '7E11', '7E12', '7E13', '7E14']
    b1, b2, b3 = int_blocks(i1['log']), int_blocks(i2['log']), int_blocks(i3['log'])
    want = {'CHART': '〓모드 메뉴\n†이벤트 플로우 차트는 다음 단계에서 열립니다',
            'UNLOCK_ALL': '〓모드 메뉴\n†전체 개방: 안 본 이벤트도 열람·재생됩니다',
            'UNLOCK_REVERT': '〓모드 메뉴\n†전체 개방 되돌리기: 이 저장에서 본 이벤트만 열람·재생됩니다',
            'RESET_CONFIRM': '〓전체 리셋\n†전역 진행 기록을 초기화합니다.\n†백업을 만든 뒤 게임을 종료합니다.\n†세이브 파일과 설정은 남습니다.'}
    c['windows_from_menu_commands'] = all(b1.get(('TITLE', k)) == v for k, v in want.items())
    c['restore_confirm_window'] = b2.get(('TITLE', 'RESTORE_CONFIRM'), '').startswith('〓전체 리셋 되돌리기\n')
    hook = res['hook_log']
    written = [l.split()[-1] for l in hook if 'mod_request_written' in l]
    c['hook_requests_written'] = written == ['chart', 'unlock_all', 'unlock_revert', 'reset_all', 'reset_restore']
    c['hook_messagebox_no_cancelled'] = sum(1 for l in hook if 'mod_command_cancelled' in l and l.endswith('reset_all')) == 1
    c['no_window_after_messagebox_no'] = any(l.startswith('AFTER MESSAGEBOX NO 60 frames home=1 request=0') for l in i1['log'])
    c['requests_consumed'] = all('request.txt' not in res['menu_files']['after_' + k] for k in ('I1', 'I2', 'I3'))
    # marker written by the game (TextFile) accepted by the hook: after I1 the files are the bare words, I2 started with the reset
    m1 = res['menu_files']['after_I1']
    c['marker_and_req_after_I1'] = i1['bytes_after'].get('YoruKR_reset.marker') == 'reset' and m1.get('reset.req') == 'reset' and 'restore.req' not in m1
    bk = sorted(k for k in res['backups'] if k.startswith('KR_reset_'))
    kp = sorted(k for k in res['backups'] if k.startswith('KR_before_restore_'))
    c['hook_backup_in_engine_save_folder'] = len(bk) == 1 and len(kp) == 1
    if not (bk and kp):
        return c
    snap1 = res['snapshots']['after_I1']
    backup = res['backups'][bk[0]]
    present = [n for n in GLOBAL8 if n in snap1]
    c['backup_equals_state_before_reset'] = all(backup.get(n) == snap1[n] for n in present) and sorted(n for n in backup if n in GLOBAL8) == sorted(present)
    c['backup_manifest_lists_them'] = sorted(backup.get('manifest.txt:text', '').split()) == sorted(present)
    r2 = next((l for l in i2['log'] if l.startswith('SHOWN RESET_RESULT')), '')
    t2 = b2.get(('TITLE', 'RESET_RESULT'), '')
    c['reset_result_window'] = t2 == '〓모드 메뉴 결과\n†reset ok ' + bk[0]
    c['marker_accepted_by_hook'] = c['reset_result_window']        # the hook acted only because the game's marker said reset
    c['save_folder_resolution_equal'] = all(('save=' + str(savedir)) in ' '.join(r['log']) for r in (i1, i2)) and c['hook_backup_in_engine_save_folder']
    # the hook deleted the global files before the engine read them: the home panel after the reset shows nothing read
    p1, p2, p3 = b1.get(('PANEL', 'I1_HOME')), b2.get(('PANEL', 'I2_HOME')), b3.get(('PANEL', 'I3_HOME'))
    c['panel_reset_then_restored'] = bool(p1) and p2 is not None and p2 != p1 and p3 == p1
    t3 = b3.get(('TITLE', 'RESTORE_RESULT'), '')
    c['restore_result_window'] = t3.startswith('〓모드 메뉴 결과\n†restore ok ' + bk[0]) and kp[0] in t3.replace('\n†', ' ')
    snap3 = res['snapshots']['after_I3']
    c['global_files_restored'] = all(snap3.get(n) == backup.get(n) for n in present)
    m3 = res['menu_files']['after_I3']
    c['maintenance_files_cleared'] = not any(n in m3 for n in ('reset.req', 'restore.req', 'request.txt', 'last_result.txt')) and 'YoruKR_reset.marker' not in snap3
    s0 = res['snapshots']['start']
    c['save_slot_unchanged'] = snap3.get(R21_BOOT_SAVE) == s0.get(R21_BOOT_SAVE) is not None
    c['settings_untouched_by_hook_and_game'] = all(snap3.get(n) == s0.get(n) for n in SETTINGS if n in s0 and n not in ENGINE_EXIT_WRITES)
    c['only_engine_exit_writes_among_settings'] = sorted(n for n in SETTINGS if n in s0 and snap3.get(n) != s0.get(n)) == sorted(n for n in ENGINE_EXIT_WRITES if n in s0 and snap3.get(n) != s0.get(n))
    c['hook_never_touched_settings'] = not any(n in backup or n in res['backups'][kp[0]] for n in SETTINGS + [R21_BOOT_SAVE, 'YoruKR_Chart.dat'])
    c['flag_after_runs'] = i1['bytes_after'].get('YoruKR_Chart.dat') == 'YoruKR.Chart.1\r\n0\r\n'
    c['chart_flag_survives_reset'] = res['snapshots']['after_I2'].get('YoruKR_Chart.dat') == snap1.get('YoruKR_Chart.dat') is not None
    c['probe_copy_dll_put_back'] = res['probe_copy_winmm_after'] == res['runtime_winmm_sha256']
    c['user_save_folder_unchanged'] = res['user_save_folder_unchanged'] and not res['c_drive_alicesoft_changes']
    return c


def main():
    if '--r21' in sys.argv:
        main_r21()
        return
    if '--integrated' in sys.argv:
        main_integrated()
        return
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
    if mode == 'full':
        saves = saves + [PARTNER_SAVE, DUNGEON_SAVE]     # r20 run 2: the Saturday partner selection, run 3: the dungeon status
    stamp0 = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    work = PROBE / f'build_{stamp0}_{mode}'
    work.mkdir(parents=True)
    user_before = user_state()
    alice_dir = L.SAVES.parent
    alice_before = tree_listing(alice_dir)
    playing_before = user_game_running()
    import verify_chart_r24 as V
    X = V.expectations()
    target = None
    names = None
    if mode == 'full':
        regs_doc = L.readj(L.EVID / 'probe_regs.json')
        row = next(s for s in regs_doc['saves'] if s['save'] == saves[0] and s.get('state'))
        target = sandbox_target(X, set(row['state']['regs']))
        print('sandbox target', target, flush=True)
        names = name_targets(X)
        print('name pages', names, flush=True)
    rt = setup_folder()
    results = []
    keys = {L.save_records(L.save_path(s))['key'] for s in saves}
    assert len(keys) == 1, 'saves with different resume keys'
    info = build_probe(O, keys.pop(), work, mode, target, names)
    for i, save in enumerate(saves):
        (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=man['files']['NightRemaster.ain']['sha256'],
            probe_sha256=info['probe_sha256'], audio=AUDIO_POLICY, save=save, mode=mode, author=L.AUTHOR,
            input='Resume of a copied save; user input patched off; dialogs answered by KR_CalProbeTick; the r20 screens driven by '
                  'KR_CPTick2 (IsClickCancelOtherMouse) with EndWaitForClick codes; the partner hover and the member-view hover '
                  'simulated (GetOnmouseChara / SetInfo + Show).'), ensure_ascii=False, indent=1), 'utf8')
        r = run_one(save, mode, info, f'{stamp0}_{i:02d}')
        r['shots_taken'] = collect_shots(mode)
        r.update(probe_sha256=info['probe_sha256'], candidate_sha256=man['files']['NightRemaster.ain']['sha256'], mode=mode)
        if mode == 'regs':
            r['state'] = parse_regs(r['log'])
            r['log'] = [l for l in r['log'] if not l.startswith(('REGS', 'READ'))]
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
                  target=info['target'] if info else None, name_pages=names)
    if mode == 'regs':
        out = dict(common, saves=results, schema='yoru-feeling-r23.caltour.probe-regs.v1', author=L.AUTHOR)
        L.writej(L.EVID / 'probe_regs.json', out)
        print(json.dumps({k: v for k, v in out.items() if k not in ('saves', 'waits')}, ensure_ascii=False, indent=1))
        assert out['probe_save_folder_inside_run'], 'a probe run saved outside run'
        assert out['user_save_folder_unchanged'] or (playing_before or playing_after), 'user save folder changed while the user game was not running'
        return
    result = dict(results[0], **common)
    if mode == 'full':
        pr = results[1]
        result['partner_run'] = dict(save=pr['save'], exit_code=pr.get('exit_code'), seconds=pr.get('seconds'), log=pr['log'],
                                     vm_error=pr.get('vm_error'), message=pr.get('message'), events=pr.get('events'),
                                     save_folder=pr.get('save_folder'), shots=pr.get('shots_taken'))
        dr = results[2]
        result['dungeon_run'] = dict(save=dr['save'], exit_code=dr.get('exit_code'), seconds=dr.get('seconds'), log=dr['log'],
                                     vm_error=dr.get('vm_error'), message=dr.get('message'), events=dr.get('events'),
                                     save_folder=dr.get('save_folder'), shots=dr.get('shots_taken'))
    dest = L.EVID / 'probe'
    result['screenshots'] = [s_ for r_ in results for s_ in r_.get('shots_taken', [])]
    if mode == 'full':
        result['state'] = parse_regs(result['log'])
        result['log'] = [l for l in result['log'] if not l.startswith(('REGS', 'READ'))]
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
        a, b = dest / 'cal_home_r20_before.png', dest / 'cal_home_r20_after.png'
        if a.exists() and b.exists():
            result['home_before_after_member'] = diff_pixels(a, b)
        a2 = dest / 'cal_home_before.png'
        if a.exists() and a2.exists():
            result['home_r20_before_vs_calendar_home_before'] = diff_pixels(a, a2)
        result['r20'] = r20_report(result['log'], result['partner_run']['log'])
        result['r20']['dungeon'] = r20_dungeon_report(result['dungeon_run']['log'])
        # r23: the save's affinity (STATE HOME: GetFeelingInnerValue of persons 1..8), the game mode, the dungeon save's affinity
        home_state = parse_state(blocks(result['log'])[('STATE', 'HOME')])
        result['state']['feel'] = [int(home_state['feel%d' % q]) for q in range(1, 9)]
        result['state']['mode'] = next(int(l.split()[1]) for l in result['log'] if l.startswith('R23MODE '))
        result['r20']['dungeon']['feel'] = {int(l.split()[1]): int(l.split()[2]) for l in result['dungeon_run']['log'] if l.startswith('R23DFEEL ')}
        result['r23'] = r23_report(result['log'], result['dungeon_run']['log'])
        a, b = dest / 'cal_dungeon_before.png', dest / 'cal_dungeon_after.png'
        if a.exists() and b.exists():
            result['dungeon_before_after_status'] = diff_pixels(a, b)
    name = {'where': 'probe_where.json', 'savefolder': 'probe_savefolder_test.json'}.get(mode, 'probe_result.json')
    L.writej(L.EVID / name, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('waits', 'log')}, ensure_ascii=False, indent=1))
    assert result['probe_save_folder_inside_run'], 'the probe saved outside run'
    assert result['user_save_folder_unchanged'] or (playing_before or playing_after), 'user save folder changed while the user game was not running'


if __name__ == '__main__':
    main()
