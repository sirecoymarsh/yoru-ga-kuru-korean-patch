# -*- coding: utf-8 -*-
"""Claude Opus 5.5 (2026-10-15): isolated, muted native probes of the auto-nav candidate (user approved: 「격리 사본으로 시험」).

  python probe_autonav.py home     run 1: a copied home save (NightR47): the choice scene E00069 three times through the home
                                   casual site (target 이즈미 -> star on answer 1, auto pick at 20 s; 쿄카 -> answer 2; off ->
                                   no star, the probe answers 1 by hand), the new-game question (KR_ANNewGame, answered 마나미),
                                   then the options opened on the Mods page (page 9): the five boxes, clicks simulated between
                                   the two per-frame events (마코토, 마코토 again, 쓰지 않음)
  python probe_autonav.py train    run 2: a copied save made inside the Saturday partner screen (NightR40): a target with a
                                   story Saturday (or one armed by hand when none), the star on its r20 box, the auto pick at
                                   20 s and the confirm answered without a dialog; END at the first message after the screen

Everything lives under autonav_20261015/probe/ on P: (run/ = a copy of the runtime folder; exe/dll/ini/Data copied, the big
assets hard-linked read only; PACT = the candidate PACT (the Mods row), EX = the runtime's; InstallInfo/SaveFolderSetting.ini
type 2 so the saves stay inside run/). The user's save folder is only read (hashed before and after).
The probe AIN = the candidate + probe-only code (never shipped): MAIN -> KR_ProbeMain (mute, resume the copied save);
config::detail::SetMute forced, C_UserInputManager::Is* -> 0 (no user input), C_SceneTrainingView@GetOnmouseChara -> 0;
C_SelectDialog@_Update gets the prefix KR_ProbeDlgTick; the message key wait -> click-through; every other
AFL_Parts_WaitForClick except the dialog, the choice window and the partner screen -> log + exit;
KR_T9HomeCasual: KR_T18RunSandboxed -> LSys3xScript::RunEvent (plain play, so the auto-nav is not in replay mode) and
■カジュアルモード設定呼び出し -> KR_ProbeCasualOther; ▲コンフィグ実行's casual start page 7 -> 9 (Mods);
our sites wrapped: C_SelectMessage@Update KR_ANSelFrame -> KR_ProbeSelFrame, _UpdateInputPartner KR_ANTrainFrame ->
KR_ProbeTrainFrame, EventConfAsraDataForParts KR_ANCfgSeenToParts -> KR_ProbeCfgToParts.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import anlib as L

O = HERE / 'candidate'
PACT = HERE / 'pact' / 'NightRemasterPact.afa'
PACT_SHA = '9f8c63b9276b00b71904ecd34b7062a9f1fec091ebe5cfaa0bc7ada1c16072ce'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterAutoNavProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat']
SAVE_TYPE = 2
HOME_SAVE = 'NightR47.asd'
PARTNER_SAVE = 'NightR40.asd'
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ('C_SelectDialog@Run', 'C_SelectMessage@Run', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>')
MODS_PAGE = 9

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
// ---- files survive ResumeLoad; session variables hold the in-run counters
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
string KR_PRGet(string key) { return SystemService.SystemVariable_Get("YoruKR.ANProbe." + key); }
void KR_PRSet(string key, string value) { SystemService.SystemVariable_Set("YoruKR.ANProbe." + key, value); }
int KR_PRNum(string key) { string v = KR_PRGet(key); if (v == "") return 0; return v.ToInt(); }
int KR_PRB(bool v) { if (v) return 1; return 0; }
string KR_PRStage() { return KR_PRRead("claude_probe_stage.txt"); }
void KR_PRStageSet(string s) { TextFile.WriteAll("claude_probe_stage.txt", s); KR_PRLog("STAGE " + s); }
void KR_PREnd(int code) { KR_PRSet("DFrames", "0"); AFL_Parts_EndWaitForClick(code); }
string KR_PRFeel() {
    string t = "";
    for (int p = 2; p <= 5; p++) t = t + " f" + ("%d" % p) + "=" + ("%d" % LAbility::m_pAbilities[p - 1].GetFeeling());
    return t;
}
void KR_PRState(string tag) {
    KR_PRLog("STATE " + tag + " date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " target=" + ("%d" % KR_ANTarget()) + " evresult=" + ("%d" % g_EvResult) + " fn=" + LSys3xScript::m_FuncName + KR_PRFeel());
}
string KR_PRPart(int n) {
    if (n <= 0 || !PartsEngine.IsExist(n)) return ("%d" % n) + ":none";
    return ("%d" % n) + ":p" + ("%d" % PartsEngine.Parts_GetParentPartsNumber(n)) + ":z" + ("%d" % PartsEngine.GetComponentPosZ(n)) + ":a" + ("%d" % PartsEngine.GetComponentAlpha(n)) + ":mul" + ("%d" % PartsEngine.GetComponentMulColorR(n)) + "," + ("%d" % PartsEngine.GetComponentMulColorG(n)) + "," + ("%d" % PartsEngine.GetComponentMulColorB(n)) + ":add" + ("%d" % PartsEngine.GetComponentAddColorR(n)) + "," + ("%d" % PartsEngine.GetComponentAddColorG(n)) + "," + ("%d" % PartsEngine.GetComponentAddColorB(n)) + ":w" + ("%d" % PartsEngine.Parts_GetPartsWidth(n, 1)) + ":show" + ("%d" % KR_PRB(PartsEngine.IsComponentShow(n)));
}
void KR_PRRowLog() {
    string t = "ROW n=" + KR_ANGet("RowN") + " n0=" + KR_ANGet("RowN0");
    int n = KR_ANGetInt("RowN");
    for (int i = 0; i < n; i++) t = t + " " + KR_PRPart(KR_ANGetInt("Row" + ("%d" % i)));
    t = t + " glow=" + KR_PRPart(KR_ANGlowPart());
    KR_PRLog(t);
}
void KR_PRTrLog() {
    KR_PRLog("TRAIN cg=" + KR_PRPart(KR_ANGetInt("TrCg")) + " box=" + KR_PRPart(KR_ANGetInt("TrBox")));
}

// ---- run 1: the home menu (a selection dialog) and the new-game question
void KR_PRPlay(string next, int t) {
    KR_ANSetTarget(t);
    KR_PRStageSet(next);
    KR_PRSet("SFrames", "0");
    SystemService.SystemVariable_Set("YoruKR.T9.Play", "69");
    KR_PRLog("PLAY E00069 target=" + ("%d" % KR_ANTarget()));
    KR_PREnd(3);
}
void KR_ProbeDlgTick() {
    string stage = KR_PRStage();
    int frames = KR_PRNum("DFrames") + 1;
    KR_PRSet("DFrames", "%d" % frames);
    if (frames > 3000) { KR_PRLog("STUCK dialog stage=" + stage); KR_PRShot("an_stuck.bmp"); system.Exit(5); return; }
    if (frames < 12) return;
    if (stage == "newgame_dlg") {
        if (frames < 30) return;
        KR_PRShot("an_newgame.bmp");
        KR_PRStageSet("newgame_done");
        KR_PREnd(4);
        return;
    }
    if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") {
        if (stage == "home0" && frames < 600) return;          // right after the resume another window may come first
        KR_PRLog("UNEXPECTED DIALOG stage=" + stage + " frames=" + ("%d" % frames));
        KR_PRShot("an_unexpected_dialog.bmp");
        system.Exit(7);
        return;
    }
    if (stage == "home0") { KR_PRState("HOME"); KR_PRShot("an_home.bmp"); KR_PRPlay("c_izumi", 2); return; }
    if (stage == "c_izumi") { KR_PRState("AFTER_IZUMI"); KR_PRPlay("c_kyouka", 3); return; }
    if (stage == "c_kyouka") { KR_PRState("AFTER_KYOUKA"); KR_PRPlay("c_off", 0); return; }
    if (stage == "c_off") { KR_PRState("AFTER_OFF"); KR_PRStageSet("newgame"); KR_PREnd(3); return; }
    if (stage == "newgame_done") { KR_PRState("AFTER_NEWGAME"); KR_PRStageSet("config"); KR_PREnd(3); return; }
    KR_PRLog("HOME in stage " + stage);
    KR_PRShot("an_home_unexpected.bmp");
    system.Exit(6);
}
// the casual site when no scene is requested (KR_T9HomeCasual's ■カジュアルモード設定呼び出し)
void KR_ProbeCasualOther() {
    string stage = KR_PRStage();
    if (stage == "newgame") {
        KR_PRStageSet("newgame_dlg");
        KR_PRSet("DFrames", "0");
        KR_ANSetTarget(0);
        KR_ANNewGame();
        KR_PRLog("NEWGAME RETURNED target=" + ("%d" % KR_ANTarget()));
        return;
    }
    if (stage == "config") {
        KR_PRStageSet("config_open");
        KR_PRSet("CFrames", "0");
        KR_PRLog("CONFIG OPEN target=" + ("%d" % KR_ANTarget()));
        ▲コンフィグ実行(false, true);
        KR_PRLog("CONFIG RETURNED (unexpected)");
        system.Exit(12);
        return;
    }
    KR_PRLog("CASUAL in stage " + stage);
    system.Exit(6);
}

// ---- the choice window: shots of the star, the off stage answered by hand
bool KR_ProbeSelFrame() {
    string stage = KR_PRStage();
    int f = KR_PRNum("SFrames") + 1;
    KR_PRSet("SFrames", "%d" % f);
    if (f == 1) {
        KR_PRSet("ST0", "%d" % system.GetTime());
        KR_PRLog("CHOICE OPEN stage=" + stage + " target=" + ("%d" % KR_ANTarget()) + " mode=" + KR_ANGet("Mode") + " pick=" + KR_ANGet("Pick"));
    }
    if (f == 40) { KR_PRRowLog(); KR_PRShot("an_choice_" + stage + "_a.bmp"); }
    if (f == 71) { KR_PRRowLog(); KR_PRShot("an_choice_" + stage + "_b.bmp"); }
    if (stage == "c_off" && f == 150) { KR_PRLog("MANUAL PICK 1"); AFL_Parts_EndWaitForClick(1); }
    bool r = KR_ANSelFrame();
    if (f == 1) KR_PRRowLog();
    if (KR_ANGet("Fired") == "1" && KR_ANGet("Mode") == "1" && KR_PRGet("FiredLogged") != stage) {
        KR_PRSet("FiredLogged", stage);
        KR_PRLog("AUTO PICK " + KR_ANGet("Pick") + " after " + ("%d" % (system.GetTime() - KR_PRNum("ST0"))) + " ms acc=" + KR_ANGet("SelAcc") + " frames=" + ("%d" % f));
    }
    if (f > 6000) { KR_PRLog("CHOICE STUCK"); KR_PRShot("an_choice_stuck.bmp"); system.Exit(5); }
    return r;
}

// ---- the options' Mods page: shots and clicks simulated between the two per-frame events
void KR_PRCfgLog(string act, string tag) {
    string t = "CFG " + tag + " target=" + ("%d" % KR_ANTarget()) + " boxes=";
    for (int i = 0; i < 5; i++) {
        int n = AFL_Activity_GetPartsNumber(act, KR_ANCfgName(i));
        t = t + ("%d" % KR_PRB(Ｐ＿チェックボックス＿チェック状態取得(n))) + "/" + ("%d" % KR_PRB(Ｐ＿チェックボックス＿有効状態取得(n))) + " ";
    }
    KR_PRLog(t);
}
bool KR_ProbeCfgToParts(string act, string name) {
    int f = KR_PRNum("CFrames") + 1;
    KR_PRSet("CFrames", "%d" % f);
    bool r = KR_ANCfgSeenToParts(act, name);
    bool mods = AFL_Activity_IsExistPartsByName(act, "KR_NavOff");
    if (f == 1) KR_PRLog("CONFIG page act=" + act + " mods=" + ("%d" % KR_PRB(mods)) + " ingame=" + ("%d" % KR_PRB(KR_ANInGame())));
    if (!mods) {
        if (f == 90) { KR_PRLog("CONFIG not on the Mods page"); KR_PRShot("an_config_wrongpage.bmp"); KR_PRLog("END"); system.Exit(11); }
        return r;
    }
    if (f == 40) { KR_PRCfgLog(act, "BEFORE"); KR_PRShot("an_mods_before.bmp"); }
    if (f == 41) { KR_PRLog("CLICK KR_NavMakoto"); Ｐ＿チェックボックス＿チェック状態設定(AFL_Activity_GetPartsNumber(act, "KR_NavMakoto"), true); }
    if (f == 70) { KR_PRCfgLog(act, "AFTER_MAKOTO"); KR_PRShot("an_mods_makoto.bmp"); }
    if (f == 71) { KR_PRLog("CLICK KR_NavMakoto again"); Ｐ＿チェックボックス＿チェック状態設定(AFL_Activity_GetPartsNumber(act, "KR_NavMakoto"), false); }
    if (f == 100) { KR_PRCfgLog(act, "AFTER_RECLICK"); }
    if (f == 101) { KR_PRLog("CLICK KR_NavOff"); Ｐ＿チェックボックス＿チェック状態設定(AFL_Activity_GetPartsNumber(act, "KR_NavOff"), true); }
    if (f == 130) { KR_PRCfgLog(act, "AFTER_OFF"); KR_PRShot("an_mods_off.bmp"); KR_PRState("CONFIG_END"); KR_PRLog("END"); system.Exit(0); }
    return r;
}

// ---- run 2: the partner screen
bool KR_ProbeTrainFrame() {
    int f = KR_PRNum("TFrames") + 1;
    KR_PRSet("TFrames", "%d" % f);
    if (f == 1) {
        string s = "";
        int pick = 0;
        for (int t = 2; t <= 5; t++) {
            int ev = L_RandomScenario::GetAfterTrainingEvent(t);
            bool can = LAbility::CanSelect(t);
            s = s + " t" + ("%d" % t) + "=" + ("%d" % KR_PRB(can)) + "/" + ("%d" % ev);
            if (pick == 0 && can && ev > 0) pick = t;
        }
        KR_PRState("PARTNER");
        KR_PRLog("PARTNER SCREEN story" + s + " pick=" + ("%d" % pick));
        if (pick == 0) {
            for (int q = 2; q <= 5; q++) {
                if (pick == 0 && LAbility::CanSelect(q)) pick = q;
            }
            KR_ANSetTarget(pick);
            KR_ANSetInt("TrDay", KR_ANToday());
            KR_ANSetInt("TrArmed", 1);
            KR_ANSetInt("TrFired", 0);
            KR_ANSetInt("TrAcc", 0);
            KR_ANSetInt("TrLast", 0);
            KR_PRLog("FORCED ARM target=" + ("%d" % pick));
        }
        else KR_ANSetTarget(pick);
        KR_PRSet("TrTarget", "%d" % pick);
        KR_PRSet("TT0", "%d" % system.GetTime());
    }
    if (f == 40) { KR_PRTrLog(); KR_PRShot("an_partner_a.bmp"); }
    if (f == 71) { KR_PRTrLog(); KR_PRShot("an_partner_b.bmp"); }
    bool r = KR_ANTrainFrame();
    if (KR_ANGet("TrFired") == "1" && KR_PRGet("TrLogged") == "") {
        KR_PRSet("TrLogged", "1");
        KR_PRLog("AUTO PARTNER " + KR_PRGet("TrTarget") + " after " + ("%d" % (system.GetTime() - KR_PRNum("TT0"))) + " ms acc=" + KR_ANGet("TrAcc") + " frames=" + ("%d" % f));
        KR_PRStageSet("ptchosen");
    }
    if (f > 6000) { KR_PRLog("PARTNER STUCK"); KR_PRShot("an_partner_stuck.bmp"); system.Exit(5); }
    return r;
}
int KR_ProbeOnmouse() { return 0; }

// ---- waits
int KR_ProbeMsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    int n = KR_PRNum("Msgs") + 1;
    KR_PRSet("Msgs", "%d" % n);
    string stage = KR_PRStage();
    if (stage == "ptchosen") {
        KR_PRState("FIRST_MESSAGE_AFTER_PARTNER");
        KR_PRLog("AFTER CONFIRM trfired=" + KR_ANGet("TrFired") + " trcg=" + KR_ANGet("TrCg"));
        KR_PRLog("END");
        system.Exit(0);
        return 0;
    }
    if (n > 3000) { KR_PRLog("TOO MANY MESSAGES"); system.Exit(8); return 0; }
    return 0;
}
int KR_ProbeWaitExit(FTPARTS_WaitForClickCallback func, bool cancel) {
    KR_PRLog("UNEXPECTED WAIT stage=" + KR_PRStage());
    KR_PRState("UNEXPECTED_WAIT");
    KR_PRShot("an_wait.bmp");
    system.Exit(4);
    return 0;
}
int KR_ProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_PRLog("SAVEFOLDER " + system.GetSaveFolderName());
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
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@KEY@@', key)
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

    def swap(owner, kind, old, new, expect=1, nth=0):
        fid = L.fid_of(m, owner)
        oldid = old if isinstance(old, int) else L.fid_of(m, old)
        newid = ids[new] if new in ids else L.fid_of(m, new)
        ops = L.region_ops(raw_code, m, fid)
        opcode, key2 = (0x30, f'CALLFUNC 0x{oldid:x}') if kind == 'call' else (0x00, f'PUSH 0x{oldid:x}')
        hits = [i for i, (_, op) in enumerate(ops) if op == key2]
        assert len(hits) == expect, (owner, old, len(hits))
        ad = ops[hits[nth]][0]
        assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', opcode, oldid), (owner, hex(ad))
        struct.pack_into('<Hi', raw, 16 + ad, opcode, newid)
        return dict(owner=owner, site=ad, old=old if isinstance(old, str) else oldid, new=new)
    sites = [
        swap('KR_T9HomeCasual', 'call', 'KR_T18RunSandboxed', 'LSys3xScript::RunEvent'),
        swap('KR_T9HomeCasual', 'call', '■カジュアルモード設定呼び出し', 'KR_ProbeCasualOther'),
        swap('C_SelectMessage@Update', 'call', 'KR_ANSelFrame', 'KR_ProbeSelFrame'),
        swap('C_SceneTraining@_UpdateInputPartner', 'call', 'KR_ANTrainFrame', 'KR_ProbeTrainFrame'),
        swap('C_ConfigView@EventConfAsraDataForParts', 'call', 'KR_ANCfgSeenToParts', 'KR_ProbeCfgToParts'),
    ]
    # ▲コンフィグ実行: the casual start page 7 (two PUSH 7 before Ｓ＿コンフィグ／開始ページ) -> the Mods page
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
    assert sum(1 for _, k in waits if k.startswith('message')) == 1, waits
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(sites=sites, waits=waits, probe_sha256=L.sha(out))


def setup_folder():
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
    assert L.sha(PACT) == PACT_SHA
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
    for b in RUN.glob('an_*.bmp'):
        b.unlink()


# ---- the 09-24 probe launcher (r23 probe_calendar_tour_r23.launch, unchanged): hidden window, MessageBoxA and the VM error
# handler break-pointed so engine errors are captured instead of waiting on a dialog
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


def collect_shots(tag):
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(RUN.glob('an_*.bmp')):
        png = dest / (b.stem + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    return shots


def run(mode):
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    save = HOME_SAVE if mode == 'home' else PARTNER_SAVE
    before = user_state()
    rt = setup_folder()
    key = L.save_records(L.SAVES / save)['key']
    info = build_probe(key, PROBE / 'work')
    savename = f'SaveData_AutoNavProbe_{mode}_{stamp}'
    savedir = RUN / savename
    set_savefolder(savename)
    savedir.mkdir(parents=True)
    for n in COPY_GLOBAL:
        if (L.SAVES / n).exists():
            shutil.copy2(L.SAVES / n, savedir / n)
    shutil.copy2(L.SAVES / save, savedir / save)
    (RUN / 'claude_probe_save.txt').write_bytes(save.encode('cp932'))
    (RUN / 'claude_probe_stage.txt').write_bytes(b'home0' if mode == 'home' else b'pt0')
    t0 = time.time()
    result = launch(timeout=900)
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result['shots'] = collect_shots(mode)
    result.update(mode=mode, save=save, save_folder=str(savedir), probe=info, candidate_ain=L.sha(O / 'NightRemaster.ain'),
                  candidate_pact=L.sha(PACT))
    after = user_state()
    result['user_save_folder_unchanged'] = before == after
    L.writej(L.EVID / f'probe_{mode}.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('probe', 'log')}, ensure_ascii=False, indent=1)[:3000])
    print('\n'.join(result['log'][-60:]))


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'home')
