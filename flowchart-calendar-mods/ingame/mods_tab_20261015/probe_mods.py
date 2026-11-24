# -*- coding: utf-8 -*-
"""Claude Opus 5.5 (2026-10-15): isolated, muted native probe of the redesigned Mods page (user: 「모드 옵션을 좀 보기좋게
다시 만들 수 있을까 … 모든 기능이 제대로 동작하나 체크좀」; isolated-copy testing approved earlier today).

  python probe_mods.py        a copied home save (NightR47), the 달성률 panel switched on in the probe's own save folder:
                              home shot -> the options opened from the home screen on the Mods page (the real path calls
                              ▲コンフィグ実行 directly, as the casual site does here) -> page shot (panel must be hidden, tracks
                              filled) -> every control driven between the two per-frame events and read back from the setting
                              it is bound to (4 reward sliders, battle speed, 9 checkboxes, the 5 navigation boxes) -> the three
                              dialog buttons clicked through their registered click handler (dialog shot, cancelled) -> page
                              shot -> options closed (AFL_Activity_End) -> home: the panel must be back -> the 자동 회복 설정
                              page (config page 10, the EX table row of KR_ItemConfigButton) opened and shot -> END

Everything lives under mods_tab_20261015/probe/ on P: (run/ = a copy of the runtime folder; exe/dll/ini/Data copied, big assets
hard-linked read only; PACT = the candidate PACT; InstallInfo/SaveFolderSetting.ini type 2 so saves stay inside run/). The user's
save folder is only read (hashed before and after).
The probe AIN = the candidate + probe-only code (never shipped): as probe_autonav.py (mute, no user input, dialog tick prefix,
waits, casual site, ▲コンフィグ実行 casual start page 7 -> 9), and the Mods layer site in EventConfAsraDataForParts
(KR_MDSeenToParts) wrapped by KR_ProbeCfgToParts, which calls it first.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mdlib as L

O = HERE / 'candidate'
PACT = HERE / 'NightRemasterPact.afa'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterModsProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat']
SAVE_TYPE = 2
HOME_SAVE = 'NightR47.asd'
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ('C_SelectDialog@Run', 'C_SelectMessage@Run', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>')
MODS_PAGE = 9
ITEMS_PAGE = 10

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
string KR_PRGet(string key) { return SystemService.SystemVariable_Get("YoruKR.MDProbe." + key); }
void KR_PRSet(string key, string value) { SystemService.SystemVariable_Set("YoruKR.MDProbe." + key, value); }
int KR_PRNum(string key) { string v = KR_PRGet(key); if (v == "") return 0; return v.ToInt(); }
int KR_PRB(bool v) { if (v) return 1; return 0; }
string KR_PRStage() { return KR_PRRead("claude_probe_stage.txt"); }
void KR_PRStageSet(string s) { TextFile.WriteAll("claude_probe_stage.txt", s); KR_PRLog("STAGE " + s); }
void KR_PREnd(int code) { KR_PRSet("DFrames", "0"); AFL_Parts_EndWaitForClick(code); }
int KR_PRFloor(float v) { int n = 0; while (n < 100000 && v >= 1.0) { v = v - 1.0; n++; } return n; }
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
int KR_PRPart(string act, string n) { return AFL_Activity_GetPartsNumber(act, n); }
bool KR_PRChecked(string act, string n) { return Ｐ＿チェックボックス＿チェック状態取得(KR_PRPart(act, n)); }
void KR_PRClickBox(string act, string n, bool v) { Ｐ＿チェックボックス＿チェック状態設定(KR_PRPart(act, n), v); }
int KR_PRPos(string act, string n) { return Ｐ＿横スクロールバー＿スクロール位置取得(KR_PRPart(act, n)); }
void KR_PRSetPos(string act, string n, int p) { Ｐ＿横スクロールバー＿スクロール位置設定(KR_PRPart(act, n), p); }
int KR_PRFill(string act, string g) { return KR_PRFloor(Ｐ＿横ゲージ分子取得(KR_PRPart(act, g), 1) + 0.5); }
string KR_PRText(string act, string n) { return Ｐ＿テキスト取得(KR_PRPart(act, n), 1); }
string KR_PRSettings() {
    return "rateEX=" + ("%d" % L_CasualMode::RateEX) + " rateTraining=" + ("%d" % L_CasualMode::RateTrainging) + " rateMoney=" + ("%d" % L_CasualMode::RateMoney)
        + " ratePair=" + ("%d" % L_CasualMode::RatePairTraining) + " speed=" + ("%d" % KR_Speed()) + " trap=" + ("%d" % KR_PRB(KR_GetTrap()))
        + " quick=" + ("%d" % KR_PRB(KR_GetQuick())) + " route=" + ("%d" % KR_PRB(KR_GetRoute())) + " loot=" + ("%d" % KR_PRB(KR_GetLoot()))
        + " sweep=" + ("%d" % KR_PRB(KR_GetSweep())) + " equip=" + ("%d" % KR_PRB(KR_GetAutoEquip())) + " smart=" + ("%d" % KR_PRB(KR_GetSmartAuto()))
        + " homeRate=" + ("%d" % KR_PRB(KR_T8HomeRateOn())) + " nav=" + ("%d" % KR_ANTarget());
}
string KR_PRPage(string act) {
    string t = "";
    t = t + "EX pos" + ("%d" % KR_PRPos(act, "KR_Multiplier_EX")) + " fill" + ("%d" % KR_PRFill(act, "KR_MD_FillEX")) + " '" + KR_PRText(act, "KR_Multiplier_Value_EX") + "'";
    t = t + " | Training pos" + ("%d" % KR_PRPos(act, "KR_Multiplier_Training")) + " fill" + ("%d" % KR_PRFill(act, "KR_MD_FillTraining")) + " '" + KR_PRText(act, "KR_Multiplier_Value_Training") + "'";
    t = t + " | Money pos" + ("%d" % KR_PRPos(act, "KR_Multiplier_Money")) + " fill" + ("%d" % KR_PRFill(act, "KR_MD_FillMoney")) + " '" + KR_PRText(act, "KR_Multiplier_Value_Money") + "'";
    t = t + " | Pair pos" + ("%d" % KR_PRPos(act, "KR_Multiplier_PairTraining")) + " fill" + ("%d" % KR_PRFill(act, "KR_MD_FillPairTraining")) + " '" + KR_PRText(act, "KR_Multiplier_Value_PairTraining") + "'";
    t = t + " | Speed pos" + ("%d" % KR_PRPos(act, "KR_CheatSpeed")) + " fill" + ("%d" % KR_PRFill(act, "KR_MD_FillSpeed")) + " '" + KR_PRText(act, "KR_CheatSpeedValue") + "'";
    return t;
}
string KR_PRBoxes(string act) {
    string t = "";
    t = t + "trap" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_CheatTrap"))) + " quick" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_CheatQuick")));
    t = t + " route" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_CheatRoute"))) + " loot" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_CheatLoot")));
    t = t + " sweep" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_CheatSweep"))) + " equip" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_AutoEquipToggle")));
    t = t + " smart" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_SmartAutoToggle"))) + " homeRate" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_HomeRateToggle")));
    t = t + " nav" + ("%d" % KR_PRB(KR_PRChecked(act, "KR_NavOff"))) + ("%d" % KR_PRB(KR_PRChecked(act, "KR_NavIzumi"))) + ("%d" % KR_PRB(KR_PRChecked(act, "KR_NavKyouka")))
        + ("%d" % KR_PRB(KR_PRChecked(act, "KR_NavManami"))) + ("%d" % KR_PRB(KR_PRChecked(act, "KR_NavMakoto")));
    return t;
}

// ---- the home menu and the dialogs opened by the Mods buttons
void KR_ProbeDlgTick() {
    string stage = KR_PRStage();
    int frames = KR_PRNum("DFrames") + 1;
    KR_PRSet("DFrames", "%d" % frames);
    if (frames > 3000) { KR_PRLog("STUCK dialog stage=" + stage); KR_PRShot("md_stuck.bmp"); system.Exit(5); return; }
    if (frames < 12) return;
    if (stage == "menu_dlg") {
        if (frames < 30) return;
        if (KR_PRNum("MenuDialogs") >= 6) { KR_PRLog("MENU DIALOG LOOP " + KR_PRGet("Menu")); KR_PRShot("md_menu_loop.bmp"); system.Exit(13); return; }
        string k = KR_PRGet("Menu") + ("%d" % (KR_PRNum("MenuDialogs") + 1));
        KR_PRSet("MenuDialogs", "%d" % (KR_PRNum("MenuDialogs") + 1));
        KR_PRShot("md_menu_" + k + ".bmp");
        KR_PRLog("MENU DIALOG " + k + " (cancelled)");
        KR_PREnd(-1);
        return;
    }
    if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") {
        if (stage == "home0" && frames < 600) return;
        KR_PRLog("UNEXPECTED DIALOG stage=" + stage + " frames=" + ("%d" % frames));
        KR_PRShot("md_unexpected_dialog.bmp");
        system.Exit(7);
        return;
    }
    if (stage == "home0") {
        KR_PRLog("HOME panel=" + ("%d" % KR_PRRate()) + " " + KR_PRSettings());
        KR_PRCheck("home panel shown before the options", KR_PRRate() == 1);
        KR_PRShot("md_home.bmp");
        KR_PRStageSet("config");
        KR_PREnd(3);
        return;
    }
    if (stage == "after_config") {
        if (frames < 40) return;
        KR_PRLog("HOME AFTER OPTIONS panel=" + ("%d" % KR_PRRate()));
        KR_PRCheck("home panel back after the options close", KR_PRRate() == 1);
        KR_PRShot("md_home_after.bmp");
        KR_PRStageSet("menus");
        KR_PREnd(3);
        return;
    }
    if (stage == "after_items") {
        KR_PRLog("FAILS " + ("%d" % KR_PRNum("Fails")));
        KR_PRLog("END");
        // last: the return-to-title confirmation (a Windows message box; the launcher captures its text and ends the run)
        KR_PRStageSet("msgbox");
        AFL_Config_SetBackToTitleConfirm(true);
        Ａ＿タイトルに戻る();
        KR_PRLog("MSGBOX RETURNED (unexpected)");
        system.Exit(14);
        return;
    }
    KR_PRLog("HOME in stage " + stage);
    KR_PRShot("md_home_unexpected.bmp");
    system.Exit(6);
}
void KR_ProbeCasualOther() {
    string stage = KR_PRStage();
    if (stage == "config") {
        KR_PRStageSet("config_open");
        KR_PRSet("CFrames", "0");
        ▲コンフィグ実行(false, true);
        KR_PRLog("OPTIONS RETURNED");
        KR_PRStageSet("after_config");
        KR_PRSet("DFrames", "0");
        return;
    }
    if (stage == "menus") {
        KR_PROpenMenu("save");
        KR_PROpenMenu("term");
        KR_PROpenMenu("info");
        KR_PRStageSet("items");
        stage = KR_PRStage();
    }
    if (stage == "items") {
        KR_PRStageSet("items_open");
        KR_PRSet("IFrames", "0");
        Ｓ＿コンフィグ／開始ページ(@@ITEMS@@);
        KR_PRLog("ITEMS PAGE RETURNED");
        KR_PRStageSet("after_items");
        KR_PRSet("DFrames", "0");
        return;
    }
    KR_PRLog("CASUAL in stage " + stage);
    system.Exit(6);
}

// ---- the options: the Mods page driven between the two per-frame events (data->parts here, parts->data next)
void KR_PRButtonOnPage(string act, string n) {
    KR_PRCheck(n + " is on the page and shown", AFL_Activity_IsExistPartsByName(act, n) && Ｐ＿表示設定取得(KR_PRPart(act, n)));
}
// C_ConfigView@ClickEvent dispatches a click on these buttons by part name (registered by name in EventConfLoadedActivity)
void KR_PROpenMenu(string tag) {
    KR_PRStageSet("menu_dlg");
    KR_PRSet("Menu", tag);
    KR_PRSet("MenuDialogs", "0");
    KR_PRSet("DFrames", "0");
    KR_PRLog("OPEN " + tag);
    if (tag == "save") KR_SaveStyleMenu();
    if (tag == "term") KR_TermMenu();
    if (tag == "info") KR_PlayerInfoMenu();
    KR_PRLog("OPEN " + tag + " returned dialogs=" + KR_PRGet("MenuDialogs"));
    KR_PRCheck(tag + " menu opened its dialog", KR_PRNum("MenuDialogs") >= 1);
}
string KR_PRItems(string act) {
    string t = "thr pos" + ("%d" % KR_PRPos(act, "KR_ItemsThreshold")) + " fill" + ("%d" % KR_PRFill(act, "KR_MD_FillThreshold")) + " '" + KR_PRText(act, "KR_ItemsThresholdValue") + "'";
    for (int i = 1; i <= 5; i++) {
        string k = "%d" % i;
        t = t + " | r" + k + " pos" + ("%d" % KR_PRPos(act, "KR_ItemsReserve" + k)) + " fill" + ("%d" % KR_PRFill(act, "KR_MD_FillReserve" + k)) + " '" + KR_PRText(act, "KR_ItemsReserveValue" + k) + "'";
    }
    return t;
}
bool KR_PRItemsFillsOK(string act) {
    if (KR_PRFill(act, "KR_MD_FillThreshold") != (KR_PRPos(act, "KR_ItemsThreshold") * 200 + 80) / 160) return false;
    for (int i = 1; i <= 5; i++) {
        string k = "%d" % i;
        if (KR_PRFill(act, "KR_MD_FillReserve" + k) != (KR_PRPos(act, "KR_ItemsReserve" + k) * 200 + 99) / 198) return false;
    }
    return true;
}
bool KR_ProbeCfgToParts(string act, string name) {
    string stage = KR_PRStage();
    if (stage == "items_open") {
        bool ri = KR_MDSeenToParts(act, name);
        int fi = KR_PRNum("IFrames") + 1;
        KR_PRSet("IFrames", "%d" % fi);
        if (fi == 1) KR_PRLog("ITEMS page act=" + act + " items=" + ("%d" % KR_PRB(AFL_Activity_IsExistPartsByName(act, "KR_ItemsEnabled"))) + " panel=" + ("%d" % KR_PRRate()));
        if (fi == 20) {
            KR_PRLog("ITEMS " + KR_PRItems(act));
            KR_PRCheck("자동 회복 설정 page loads (KR_ItemsEnabled)", AFL_Activity_IsExistPartsByName(act, "KR_ItemsEnabled"));
            KR_PRCheck("자동 회복 tracks follow the sliders", KR_PRItemsFillsOK(act));
            KR_PRSet("ThrText", KR_PRText(act, "KR_ItemsThresholdValue"));
            KR_PRSet("R1Text", KR_PRText(act, "KR_ItemsReserveValue1"));
            KR_PRSetPos(act, "KR_ItemsThreshold", (KR_PRPos(act, "KR_ItemsThreshold") + 20) % 81);
            KR_PRSetPos(act, "KR_ItemsReserve1", (KR_PRPos(act, "KR_ItemsReserve1") + 30) % 100);
        }
        if (fi == 24) {
            KR_PRLog("ITEMS MOVED " + KR_PRItems(act));
            KR_PRCheck("자동 회복 tracks follow after a change", KR_PRItemsFillsOK(act));
            KR_PRCheck("자동 회복 value texts follow the sliders", KR_PRText(act, "KR_ItemsThresholdValue") != KR_PRGet("ThrText") && KR_PRText(act, "KR_ItemsReserveValue1") != KR_PRGet("R1Text"));
        }
        if (fi == 30) {
            KR_PRShot("md_items.bmp");
            AFL_Activity_End();
        }
        if (fi > 600) { KR_PRLog("ITEMS STUCK"); system.Exit(5); }
        return ri;
    }
    int f = KR_PRNum("CFrames") + 1;
    KR_PRSet("CFrames", "%d" % f);
    int panelBefore = KR_PRRate();
    bool r = KR_MDSeenToParts(act, name);
    bool mods = AFL_Activity_IsExistPartsByName(act, "KR_MD_FillEX");
    if (f == 1) {
        KR_PRLog("OPTIONS page act=" + act + " mods=" + ("%d" % KR_PRB(mods)) + " panel before=" + ("%d" % panelBefore) + " after=" + ("%d" % KR_PRRate()));
        KR_PRCheck("home panel hidden on the options page", KR_PRRate() == 0);
    }
    if (!mods) {
        if (f == 90) { KR_PRLog("OPTIONS not on the Mods page"); KR_PRShot("md_wrongpage.bmp"); KR_PRLog("END"); system.Exit(11); }
        return r;
    }
    if (f == 30) {
        KR_PRLog("PAGE " + KR_PRPage(act));
        KR_PRLog("BOXES " + KR_PRBoxes(act));
        KR_PRLog("SETTINGS " + KR_PRSettings());
        KR_PRCheck("EX track follows the slider", KR_PRFill(act, "KR_MD_FillEX") == (KR_PRPos(act, "KR_Multiplier_EX") * 200 + 19) / 38);
        KR_PRCheck("speed track follows the slider", KR_PRFill(act, "KR_MD_FillSpeed") == KR_PRPos(act, "KR_CheatSpeed") * 25);
        KR_PRShot("md_mods_a.bmp");
    }
    // sliders: set a position, read the setting two frames later
    if (f == 40) { KR_PRSetPos(act, "KR_Multiplier_EX", 4); KR_PRSetPos(act, "KR_Multiplier_Training", 9); KR_PRSetPos(act, "KR_Multiplier_Money", 0); KR_PRSetPos(act, "KR_Multiplier_PairTraining", 19); KR_PRSetPos(act, "KR_CheatSpeed", 2); KR_PRLog("SET sliders EX 5x, Training 10x, Money 1x, Pair 20x, speed 3x"); }
    if (f == 44) {
        KR_PRLog("PAGE " + KR_PRPage(act));
        KR_PRLog("SETTINGS " + KR_PRSettings());
        KR_PRCheck("경험치 slider -> RateEX 500", L_CasualMode::RateEX == 500);
        KR_PRCheck("훈련치 slider -> RateTrainging 1000", L_CasualMode::RateTrainging == 1000);
        KR_PRCheck("월편 slider -> RateMoney 100", L_CasualMode::RateMoney == 100);
        KR_PRCheck("동료 특훈치 slider -> RatePairTraining 2000", L_CasualMode::RatePairTraining == 2000);
        KR_PRCheck("전투 속도 slider -> KR_Speed 3", KR_Speed() == 3);
        KR_PRCheck("value texts", KR_PRText(act, "KR_Multiplier_Value_EX") == "5배" && KR_PRText(act, "KR_Multiplier_Value_Training") == "10배" && KR_PRText(act, "KR_Multiplier_Value_Money") == "1배" && KR_PRText(act, "KR_Multiplier_Value_PairTraining") == "20배" && KR_PRText(act, "KR_CheatSpeedValue") == "3배");
        KR_PRCheck("tracks", KR_PRFill(act, "KR_MD_FillEX") == 21 && KR_PRFill(act, "KR_MD_FillTraining") == 47 && KR_PRFill(act, "KR_MD_FillMoney") == 0 && KR_PRFill(act, "KR_MD_FillPairTraining") == 100 && KR_PRFill(act, "KR_MD_FillSpeed") == 50);
    }
    // checkboxes: flip, read the setting, flip back, read again
    if (f == 50) { KR_PRSet("B0", KR_PRSettings()); KR_PRLog("BEFORE BOXES " + KR_PRBoxes(act)); }
    if (f == 51) { KR_PRClickBox(act, "KR_CheatTrap", !KR_GetTrap()); KR_PRClickBox(act, "KR_CheatRoute", !KR_GetRoute()); KR_PRClickBox(act, "KR_CheatSweep", !KR_GetSweep()); KR_PRClickBox(act, "KR_AutoEquipToggle", !KR_GetAutoEquip()); KR_PRClickBox(act, "KR_SmartAutoToggle", !KR_GetSmartAuto()); KR_PRSet("T0", "%d" % KR_PRB(KR_GetTrap())); KR_PRSet("R0", "%d" % KR_PRB(KR_GetRoute())); KR_PRSet("S0", "%d" % KR_PRB(KR_GetSweep())); KR_PRSet("E0", "%d" % KR_PRB(KR_GetAutoEquip())); KR_PRSet("A0", "%d" % KR_PRB(KR_GetSmartAuto())); }
    if (f == 55) {
        KR_PRLog("FLIPPED " + KR_PRSettings());
        KR_PRCheck("함정 즉시 해체 box -> setting", ("%d" % KR_PRB(KR_GetTrap())) != KR_PRGet("T0"));
        KR_PRCheck("다음 층 경로 표시 box -> setting", ("%d" % KR_PRB(KR_GetRoute())) != KR_PRGet("R0"));
        KR_PRCheck("소탕 버튼 표시 box -> setting", ("%d" % KR_PRB(KR_GetSweep())) != KR_PRGet("S0"));
        KR_PRCheck("자동 장착 box -> setting", ("%d" % KR_PRB(KR_GetAutoEquip())) != KR_PRGet("E0"));
        KR_PRCheck("강화 자동 전투 box -> setting", ("%d" % KR_PRB(KR_GetSmartAuto())) != KR_PRGet("A0"));
        KR_PRClickBox(act, "KR_CheatTrap", !KR_GetTrap()); KR_PRClickBox(act, "KR_CheatRoute", !KR_GetRoute()); KR_PRClickBox(act, "KR_CheatSweep", !KR_GetSweep()); KR_PRClickBox(act, "KR_AutoEquipToggle", !KR_GetAutoEquip()); KR_PRClickBox(act, "KR_SmartAutoToggle", !KR_GetSmartAuto());
    }
    if (f == 59) {
        KR_PRLog("FLIPPED BACK " + KR_PRSettings());
        KR_PRCheck("five boxes back to their first state", ("%d" % KR_PRB(KR_GetTrap())) == KR_PRGet("T0") && ("%d" % KR_PRB(KR_GetRoute())) == KR_PRGet("R0") && ("%d" % KR_PRB(KR_GetSweep())) == KR_PRGet("S0") && ("%d" % KR_PRB(KR_GetAutoEquip())) == KR_PRGet("E0") && ("%d" % KR_PRB(KR_GetSmartAuto())) == KR_PRGet("A0"));
    }
    // battle mode: 전투 이펙트 보지 않기 and 일반 적 즉시 처치 share one switch (KR_SetBattleMode)
    if (f == 60) { KR_PRClickBox(act, "KR_CheatQuick", false); KR_PRClickBox(act, "KR_CheatLoot", false); }
    if (f == 63) { KR_PRCheck("battle mode off", !KR_GetQuick() && !KR_GetLoot()); KR_PRClickBox(act, "KR_CheatQuick", true); }
    if (f == 66) { KR_PRCheck("전투 이펙트 보지 않기 box -> quick on, instant kill off", KR_GetQuick() && !KR_GetLoot()); KR_PRClickBox(act, "KR_CheatLoot", true); }
    if (f == 69) { KR_PRCheck("일반 적 즉시 처치 box -> instant kill on, quick off (one switch)", KR_GetLoot() && !KR_GetQuick() && !KR_PRChecked(act, "KR_CheatQuick")); KR_PRClickBox(act, "KR_CheatLoot", false); }
    if (f == 72) { KR_PRCheck("battle mode off again", !KR_GetQuick() && !KR_GetLoot()); }
    // 달성률 항상 표시: flip and back (the setting is a file; read back through KR_T8HomeRateOn)
    if (f == 74) { KR_PRSet("H0", "%d" % KR_PRB(KR_T8HomeRateOn())); KR_PRClickBox(act, "KR_HomeRateToggle", !KR_T8HomeRateOn()); }
    if (f == 78) { KR_PRCheck("달성률 항상 표시 box -> setting", ("%d" % KR_PRB(KR_T8HomeRateOn())) != KR_PRGet("H0")); KR_PRClickBox(act, "KR_HomeRateToggle", !KR_T8HomeRateOn()); }
    if (f == 82) { KR_PRCheck("달성률 항상 표시 back", ("%d" % KR_PRB(KR_T8HomeRateOn())) == KR_PRGet("H0")); }
    // navigation (radio)
    if (f == 84) { KR_PRClickBox(act, "KR_NavIzumi", true); }
    if (f == 88) { KR_PRCheck("오토 내비게이션 이즈미 -> target 2", KR_ANTarget() == 2 && KR_PRChecked(act, "KR_NavIzumi") && !KR_PRChecked(act, "KR_NavOff")); KR_PRClickBox(act, "KR_NavOff", true); }
    if (f == 92) { KR_PRCheck("오토 내비게이션 쓰지 않음 -> target 0", KR_ANTarget() == 0 && KR_PRChecked(act, "KR_NavOff")); }
    // a page shot with the changed values
    if (f == 96) { KR_PRClickBox(act, "KR_CheatRoute", true); KR_PRClickBox(act, "KR_NavIzumi", true); }
    if (f == 100) { KR_PRLog("PAGE " + KR_PRPage(act)); KR_PRLog("BOXES " + KR_PRBoxes(act)); KR_PRShot("md_mods_b.bmp"); }
    // the three dialog buttons through their registered click handler
    if (f == 104) { KR_PRButtonOnPage(act, "KR_SaveStyleButton"); KR_PRButtonOnPage(act, "KR_TermConfigButton"); KR_PRButtonOnPage(act, "KR_PlayerInfoButton"); KR_PRButtonOnPage(act, "KR_ItemConfigButton"); }
    if (f == 108) { KR_PRLog("SETTINGS END " + KR_PRSettings()); KR_PRLog("CLOSE OPTIONS"); AFL_Activity_End(); }
    if (f > 3000) { KR_PRLog("OPTIONS STUCK"); KR_PRShot("md_options_stuck.bmp"); system.Exit(5); }
    return r;
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
    KR_PRShot("md_wait.bmp");
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


def build_probe(key, work):
    src = O / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@KEY@@', key).replace('@@ITEMS@@', str(ITEMS_PAGE))
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
    upd = L.fid_of(m, 'C_SelectDialog@_Update')
    path = work / f'original_{upd}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SelectDialog@_Update', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SelectDialog@_Update'), '\tCALLFUNC KR_ProbeDlgTick\n'))
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    RUN.mkdir(parents=True, exist_ok=True)
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_ProbeMain'])
    raw_code = L.WORK / 'build' / 'candidate_raw_code.jam'

    def swap(owner, old, new, expect=1, nth=0):
        fid = L.fid_of(m, owner)
        oldid = L.fid_of(m, old)
        newid = ids[new] if new in ids else L.fid_of(m, new)
        ops = L.region_ops(raw_code, m, fid)
        key2 = f'CALLFUNC 0x{oldid:x}'
        hits = [i for i, (_, op) in enumerate(ops) if op == key2]
        assert len(hits) == expect, (owner, old, len(hits))
        ad = ops[hits[nth]][0]
        assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, oldid), (owner, hex(ad))
        struct.pack_into('<Hi', raw, 16 + ad, 0x30, newid)
        return dict(owner=owner, site=ad, old=old, new=new)
    sites = [
        swap('KR_T9HomeCasual', 'KR_T18RunSandboxed', 'LSys3xScript::RunEvent'),
        swap('KR_T9HomeCasual', '■カジュアルモード設定呼び出し', 'KR_ProbeCasualOther'),
        swap('C_ConfigView@EventConfAsraDataForParts', 'KR_MDSeenToParts', 'KR_ProbeCfgToParts'),
    ]
    cfg = L.fid_of(m, '▲コンフィグ実行')
    start = L.fid_of(m, 'Ｓ＿コンフィグ／開始ページ')
    ops = L.region_ops(raw_code, m, cfg)
    n7 = 0
    for i, (ad, op) in enumerate(ops):
        if op == f'CALLFUNC 0x{start:x}':
            pad, pop = ops[i - 1]
            assert pop == 'PUSH 0x7', pop
            assert raw[16 + pad:16 + pad + 6] == struct.pack('<Hi', 0, 7)
            struct.pack_into('<Hi', raw, 16 + pad, 0, MODS_PAGE)
            n7 += 1
    assert n7 == 2, n7
    sites.append(dict(owner='▲コンフィグ実行', change='casual start page 7 -> %d (both)' % MODS_PAGE))
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
    return dict(sites=sites, waits=len(waits), probe_sha256=L.sha(out))


def setup_folder():
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
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
    for b in RUN.glob('md_*.bmp'):
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
    for b in sorted(RUN.glob('md_*.bmp')):
        png = dest / (b.stem + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    return shots


def run():
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    before = user_state()
    setup_folder()
    key = L.save_records(L.SAVES / HOME_SAVE)['key']
    info = build_probe(key, PROBE / 'work')
    savename = f'SaveData_ModsProbe_{stamp}'
    savedir = RUN / savename
    set_savefolder(savename)
    savedir.mkdir(parents=True)
    for n in COPY_GLOBAL:
        if (L.SAVES / n).exists():
            shutil.copy2(L.SAVES / n, savedir / n)
    shutil.copy2(L.SAVES / HOME_SAVE, savedir / HOME_SAVE)
    (RUN / 'claude_probe_save.txt').write_bytes(HOME_SAVE.encode('cp932'))
    (RUN / 'claude_probe_stage.txt').write_bytes(b'home0')
    t0 = time.time()
    result = launch(timeout=900)
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result['shots'] = collect_shots()
    result.update(save=HOME_SAVE, save_folder=str(savedir), probe=info, candidate_ain=L.sha(O / 'NightRemaster.ain'), candidate_pact=L.sha(PACT))
    result['fails'] = [x for x in result['log'] if x.startswith('FAIL ')]
    result['oks'] = len([x for x in result['log'] if x.startswith('OK ')])
    want = '타이틀 화면으로 돌아가시겠습니까?\n\n※저장하지 않은 데이터는 사라집니다'
    result['msgbox_title_korean'] = bool(result.get('message')) and result['message'].get('cp949') == want
    result['user_save_folder_unchanged'] = before == user_state()
    L.writej(L.EVID / 'probe_mods.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('probe', 'log')}, ensure_ascii=False, indent=1)[:3000])
    print('\n'.join(result['log'][-90:]))


if __name__ == '__main__':
    run()
