# -*- coding: utf-8 -*-
"""Claude Opus 5.5 (2026-10-17): isolated, muted native probe of the redesigned home 달성률 panel (stage 1).

  python probe_home.py     a copied home save (NightR47), the panel switched on in the probe's own save folder:
                           home shot (values must equal the old panel's sources, the old text body hidden, the calendar
                           button shown while the top menu waits) -> the calendar button clicked through the panel's click
                           handler (KR_T8HomeClick with the button's screen y) -> the event calendar opens (KR_CDoHome) ->
                           chart shot -> closed -> home shot -> the 쿄카 row clicked -> the character window -> shot ->
                           cancelled -> home shot -> row map checks -> END

Everything lives under calendar_redesign_20261017/probe/ on P: (run/ = a copy of the runtime folder; exe/dll/ini/Data copied,
big assets hard-linked read only; PACT = the candidate PACT; InstallInfo/SaveFolderSetting.ini type 2 so saves stay inside
run/). The user's save folder is only read (hashed before and after).
The probe AIN = the candidate + probe-only code (never shipped), as probe_mods.py: mute, no user input, the dialog tick prefix in
C_SelectDialog@_Update, waits; plus a tick prefix in the chart's frame delegate KR_C24Frame (Codex C24 layer; KR_CWait -> KR_C24Wait -> KR_C24WaitRaw). Real mouse hit-testing and the
cursor-over state are not exercised (input is cut off); the click handler is called with the button's coordinates.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvlib as L

O = HERE / 'candidate'
PACT = O / 'NightRemasterPact.afa'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterHomeProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat',
               'YoruKR_Chart.dat']
SAVE_TYPE = 2
HOME_SAVE = sys.argv[1] if len(sys.argv) > 1 else 'NightR47.asd'   # a save made from the home screen (stack: C_SceneHomebase@Run -> CheckGameSysButtons)
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ('C_SelectDialog@Run', 'C_SelectMessage@Run', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>', 'KR_C24WaitRaw')
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
    string t = "date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " n=" + KR_HVGet("n");
    t = t + " ev='" + KR_PRT(act, "KR_HR_EvValue") + "' story='" + KR_PRT(act, "KR_HR_Story") + "'";
    for (int k = 0; k < 7; k++) {
        string s = "%d" % (k + 2);
        t = t + " [" + KR_PRT(act, "KR_HR_Name" + s) + " " + KR_PRT(act, "KR_HR_Pct" + s) + " shown" + ("%d" % KR_PRShown(act, "KR_HR_Box" + s)) + "]";
    }
    for (int j = 0; j <= 3; j++) t = t + " a" + ("%d" % j) + "='" + KR_PRT(act, "KR_HR_AllValue" + ("%d" % j)) + "'";
    t = t + " body=" + ("%d" % KR_PRShown(act, "KR_HomeRateBody")) + " cal=" + ("%d" % KR_PRShown(act, "KR_HR_CalBox")) + "/" + ("%d" % KR_PRShown(act, "KR_HR_CalText"));
    return t;
}
string KR_PRExpect() {
    string t = "ev=" + KR_T8Pct(KR_PREv(), 1043) + " joined=";
    for (int p = 2; p <= 8; p++) {
        if (KR_T20Joined(p)) t = t + ("%d" % p);
    }
    for (int p = 2; p <= 8; p++) t = t + " c" + ("%d" % p) + "=" + KR_T8Pct(KR_T8CharEvents(p), KR_T8CharTotal(p));
    t = t + " read=" + KR_T8Pct(KR_T8ReadCount(), 74966) + " cg=" + KR_T8Pct(KR_T8CgCount(), 60) + " scene=" + KR_T8Pct(KR_T8SceneCount(), 66) + " end=" + ("%d" % KR_T8EndingCount());
    return t;
}
int KR_PRJoined() {
    int n = 0;
    for (int p = 2; p <= 8; p++) {
        if (KR_T20Joined(p)) n++;
    }
    return n;
}
// slots: the joined companions in person order, then hidden slots
bool KR_PRSlotsOK(string act) {
    int k = 0;
    for (int p = 2; p <= 8; p++) {
        if (!KR_T20Joined(p)) continue;
        string s = "%d" % (k + 2);
        if (KR_HVNum("slot%d" % k) != p) return false;
        if (KR_PRT(act, "KR_HR_Name" + s) != KR_HVName(p)) return false;
        if (KR_PRShown(act, "KR_HR_Box" + s) != 1 || KR_PRShown(act, "KR_HR_Face" + s) != 1 || KR_PRShown(act, "KR_HR_Name" + s) != 1) return false;
        k++;
    }
    if (KR_HVNum("n") != k) return false;
    for (int j = k; j < 7; j++) {
        string s = "%d" % (j + 2);
        if (KR_PRShown(act, "KR_HR_Box" + s) != 0 || KR_PRShown(act, "KR_HR_Face" + s) != 0 || KR_PRShown(act, "KR_HR_Name" + s) != 0
            || KR_PRShown(act, "KR_HR_Pct" + s) != 0 || KR_PRShown(act, "KR_HR_Bar" + s) != 0) return false;
    }
    return true;
}
bool KR_PRValuesOK(string act) {
    if (KR_PRT(act, "KR_HR_EvValue") != KR_T8Pct(KR_PREv(), 1043)) return false;
    int k = 0;
    for (int p = 2; p <= 8; p++) {
        if (!KR_T20Joined(p)) continue;
        if (KR_PRT(act, "KR_HR_Pct" + ("%d" % (k + 2))) != KR_T8Pct(KR_T8CharEvents(p), KR_T8CharTotal(p))) return false;
        k++;
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
            KR_PRCheck("the second row opened that companion's window", KR_PRGet("Pick") != "");
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
        KR_PRCheck("only joined companions, in person order; the other rows hidden", KR_PRSlotsOK(act) && KR_HVNum("n") == KR_PRJoined());
        KR_PRCheck("old text body hidden", KR_PRShown(act, "KR_HomeRateBody") == 0);
        KR_PRCheck("calendar button shown while the top menu waits", KR_PRShown(act, "KR_HR_CalBox") == 1 && KR_PRShown(act, "KR_HR_CalText") == 1);
        KR_PRShot("hv_home.bmp");
        KR_PRStageSet("chart");
        KR_PRLog("CLICK calendar button y=" + ("%d" % (@@CAL_Y@@ - KR_HVUp() + 12)));
        KR_T8HomeClick(KR_PRP(act, "KR_HR_CalBox"), 80, @@CAL_Y@@ - KR_HVUp() + 12);
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
        KR_PRLog("CLICK second row = person " + KR_HVGet("slot1"));
        KR_PRSet("Pick", KR_HVGet("slot1"));
        KR_T8HomeClick(KR_PRP(act, "KR_HR_Box3"), 80, @@ROW_Y0@@ + @@ROW_STEP@@ + 20);
        return;
    }
    if (stage == "after_char") {
        if (frames < 40) return;
        KR_PRCheck("panel back after the character window", KR_PRRate() == 1 && KR_PRShown(act, "KR_HR_CalBox") == 1);
        KR_PRShot("hv_home_end.bmp");
        int n = KR_HVNum("n");
        KR_PRCheck("row map: first row = first joined, last row = last joined, gaps / title / rows past the last empty",
                   KR_HVRow(@@ROW_Y0@@) == KR_HVNum("slot0") && KR_HVRow(@@ROW_Y0@@ + (n - 1) * @@ROW_STEP@@ + 39) == KR_HVNum("slot%d" % (n - 1))
                   && KR_HVRow(@@ROW_Y0@@ + 40) == 0 && KR_HVRow(100) == 0 && KR_HVRow(@@ROW_Y0@@ + n * @@ROW_STEP@@ + 2) == 0);
        KR_PRCheck("row map: the calendar button (moved up with the rows) marks the pick", KR_HVRow(@@CAL_Y@@ - KR_HVUp() + 5) == 2 && KR_HVGet("Cal") == "1");
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
// ---- the event calendar's frame delegate (KR_C24Frame prefix): a shot, then close (wait result 0)
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


def build_probe(key, work):
    src = O / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + (PROBE_JAF.replace('@@KEY@@', key).replace('@@CAL_Y@@', str(CAL_Y))
                             .replace('@@ROW_Y0@@', str(ROW_Y0)).replace('@@ROW_STEP@@', str(ROW_STEP)))
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
    for owner, tick in (('C_SelectDialog@_Update', 'KR_ProbeDlgTick'), ('KR_C24Frame', 'KR_ProbeChartTick')):
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
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_ProbeMain'])
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
    for b in RUN.glob('hv_*.bmp'):
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
    for b in sorted(RUN.glob('hv_*.bmp')):
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
    savename = f'SaveData_HomeProbe_{stamp}'
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
    result['ended'] = 'END' in result['log']
    result['user_save_folder_unchanged'] = before == user_state()
    L.EVID.mkdir(parents=True, exist_ok=True)
    L.writej(L.EVID / f'probe_home_{stamp}.json', result)
    L.writej(L.EVID / ('probe_home.json' if HOME_SAVE == 'NightR47.asd' else f'probe_home_{HOME_SAVE[:-4]}.json'), result)   # publish_home.py --verify reads probe_home.json
    print(json.dumps({k: v for k, v in result.items() if k not in ('probe', 'log')}, ensure_ascii=False, indent=1)[:3000])
    print('\n'.join(result['log'][-60:]))


if __name__ == '__main__':
    run()
