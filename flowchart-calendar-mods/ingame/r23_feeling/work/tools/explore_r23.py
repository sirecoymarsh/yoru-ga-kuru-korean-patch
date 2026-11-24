"""r23 exploration probe (Claude Opus 5.5, 2026-09-28): where the game draws the affinity moons (C_FeelingView) of the status
window, on the BASE AIN (= the r22 install) plus probe-only code. Nothing here ships. Isolated + muted run folder
r23_feeling\\probe_explore\\run (hard-linked big assets are read only; saves inside run\\ on P:).

  python explore_r23.py [SAVE] [persons...]   home save -> 파티 편성 (RunMember) -> each person: the hover preview (page 0; the
                                              probe calls what the hover calls: SetInfo + Show) and status page 1; part scan
                                              (every part under the status root, two levels), font-size tag test, widths

Per-frame driver: C_UserInputManager::IsClickCancelOtherMouse / IsClickCancel bodies call KR_XTick(kind) (probe only); the
stage machine reads the VM call stack (system.GetFuncStackName) to know which screen waits.
"""
import sys, json, re, struct, shutil, datetime, time
from pathlib import Path
sys.dont_write_bytecode = True
R23 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R23))
import r23lib as L
import probe_calendar_tour_r23 as P

P.PROBE = R23 / 'probe_explore'
P.RUN = P.PROBE / 'run'
P.BOOT = 'NightRemasterFeelExplore'
OUT = R23 / 'work' / 'explore'
OUT.mkdir(parents=True, exist_ok=True)

XJAF = r'''
int KR_XB(bool v) { if (v) return 1; return 0; }
string KR_XRead(string file) {
    string s = "";
    if (!TextFile.ReadAll(file, s)) return "";
    return s;
}
void KR_XLog(string text) {
    TextFile.WriteAll("claude_probe.txt", KR_XRead("claude_probe.txt") + text + "\n");
}
int KR_XShot(string file) {
    AFL_View_Update(); AFL_View_Update(); AFL_View_Update();
    if (!SystemService.SaveScreenshot(file, 0, 0, 1280, 720)) system.Exit(9);
    KR_XLog("SHOT " + file);
    return 0;
}
string KR_XGet(string key) { return SystemService.SystemVariable_Get("YoruKR.X." + key); }
void KR_XSet(string key, string value) { SystemService.SystemVariable_Set("YoruKR.X." + key, value); }
int KR_XNum(string key) { string v = KR_XGet(key); if (v == "") return 0; return v.ToInt(); }
string KR_XStack() {
    string t = "";
    for (int i = 0; i < 40; i++) {
        string s = system.GetFuncStackName(i);
        if (s == "") break;
        t = t + s + " | ";
    }
    return t;
}
bool KR_XOn(string name) { string t = KR_XStack(); return t.Find(name) >= 0; }
void KR_XEnd(int code) {
    KR_XSet("Frames", "0");
    AFL_Parts_EndWaitForClick(code);
}
int KR_XRoot() { return PartsEngine.GetActivityPartsNumber("Game\\Scenes\\4000Homebase\\CharaStatus.pact", "ルートパーツ"); }
void KR_XPart(string tag, int n) {
    int par = PartsEngine.Parts_GetParentPartsNumber(n);
    float ax = PartsEngine.GetComponentAbsolutePosX(n);
    float ay = PartsEngine.GetComponentAbsolutePosY(n);
    float px = PartsEngine.GetComponentPosX(n);
    float py = PartsEngine.GetComponentPosY(n);
    int w = PartsEngine.Parts_GetPartsWidth(n, 1);
    int h = PartsEngine.Parts_GetPartsHeight(n, 1);
    int z = PartsEngine.GetComponentPosZ(n);
    int az = PartsEngine.GetComponentAbsolutePosZ(n);
    KR_XLog(tag + " " + ("%d" % n) + " parent=" + ("%d" % par) + " show=" + ("%d" % KR_XB(PartsEngine.IsComponentShow(n))) + " pos=" + ("%f" % px) + "," + ("%f" % py) + " abs=" + ("%f" % ax) + "," + ("%f" % ay) + " z=" + ("%d" % z) + " absz=" + ("%d" % az) + " wh=" + ("%d" % w) + "x" + ("%d" % h));
}
// every existing part whose parent (or grandparent) is the status root (runtime parts are numbered from 1,000,000,000 up)
void KR_XScan(string tag) {
    int root = KR_XRoot();
    KR_XLog("SCAN " + tag + " root=" + ("%d" % root) + " free=" + ("%d" % PartsEngine.GetFreeNumber()));
    KR_XPart("ROOT", root);
    int hits = 0;
    for (int n = 1000000000; n < 1000040000; n++) {
        if (!PartsEngine.IsExist(n)) continue;
        int par = PartsEngine.Parts_GetParentPartsNumber(n);
        if (par <= 0) continue;
        int gp = 0;
        if (PartsEngine.IsExist(par)) gp = PartsEngine.Parts_GetParentPartsNumber(par);
        if (par != root && gp != root) continue;
        if (par == root) KR_XPart("C1", n);
        else KR_XPart("C2", n);
        hits++;
    }
    KR_XLog("SCAN END " + tag + " hits=" + ("%d" % hits));
}
// the feeling value / rank the game's own functions give
void KR_XFeel(int c) {
    KR_XLog("FEEL " + ("%d" % c) + " GetFeeling=" + ("%d" % LAbility::m_pAbilities[c - 1].GetFeeling()) + " inner=" + ("%d" % LAbility::m_pAbilities[c - 1].GetFeelingInnerValue()) + " rate=" + ("%d" % LAbility::m_pAbilities[c - 1].GetFeelingRate()) + " rank5=" + ("%d" % C_SysVoice::GetFeelingRank_5(c)) + " turning=" + ("%d" % LAbility::GetTurningCharaNo()));
}
// text parts under the moons: plain, size tags, a long line (widths logged)
void KR_XTextTest(int root) {
    int n1 = 2026092801;
    string t1 = "63 / 120";
    PartsEngine.Parts_SetText(n1, "", 1);
    PartsEngine.Parts_SetFont(n1, 257, 20, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(n1, true, 1);
    PartsEngine.Parts_SetText(n1, t1, 1);
    PartsEngine.Parts_SetParentPartsNumber(n1, root);
    PartsEngine.SetComponentPos(n1, 374.0, 128.0);
    PartsEngine.SetComponentPosZ(n1, 300);
    PartsEngine.SetComponentShow(n1, true);
    int n2 = 2026092802;
    string t2 = "${font size=16}단계 5/5${/font} 기본 20";
    PartsEngine.Parts_SetText(n2, "", 1);
    PartsEngine.Parts_SetFont(n2, 257, 20, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(n2, true, 1);
    PartsEngine.Parts_SetText(n2, t2, 1);
    PartsEngine.Parts_SetParentPartsNumber(n2, root);
    PartsEngine.SetComponentPos(n2, 374.0, 152.0);
    PartsEngine.SetComponentPosZ(n2, 300);
    PartsEngine.SetComponentShow(n2, true);
    int n3 = 2026092803;
    string t3 = "친밀도 63 (5/5) · 다음 조건 70 · 10/11 아침 · 인물 · 마나미 · 이즈미와 2";
    PartsEngine.Parts_SetText(n3, "", 1);
    PartsEngine.Parts_SetFont(n3, 257, 20, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(n3, true, 1);
    PartsEngine.Parts_SetText(n3, t3, 1);
    PartsEngine.Parts_SetParentPartsNumber(n3, root);
    PartsEngine.SetComponentPos(n3, 52.0, 560.0);
    PartsEngine.SetComponentPosZ(n3, 300);
    PartsEngine.SetComponentShow(n3, true);
    int n4 = 2026092804;
    string t4 = "${font size=18 r=255 g=224 b=96}단계${/font} ${font size=26}５${/font}/5 · 가나다라마바사아자차카타파하 · 0123456789";
    PartsEngine.Parts_SetText(n4, "", 1);
    PartsEngine.Parts_SetFont(n4, 257, 20, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(n4, true, 1);
    PartsEngine.Parts_SetText(n4, t4, 1);
    PartsEngine.Parts_SetParentPartsNumber(n4, root);
    PartsEngine.SetComponentPos(n4, 52.0, 600.0);
    PartsEngine.SetComponentPosZ(n4, 300);
    PartsEngine.SetComponentShow(n4, true);
    int n5 = 2026092805;
    string t5 = "가가가가가가가가가가 ··········  (5/5)";
    PartsEngine.Parts_SetText(n5, "", 1);
    PartsEngine.Parts_SetFont(n5, 257, 20, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(n5, true, 1);
    PartsEngine.Parts_SetText(n5, t5, 1);
    PartsEngine.Parts_SetParentPartsNumber(n5, root);
    PartsEngine.SetComponentPos(n5, 52.0, 640.0);
    PartsEngine.SetComponentPosZ(n5, 300);
    PartsEngine.SetComponentShow(n5, true);
    AFL_View_Update();
    KR_XLog("TEXTTEST w1=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n1, 1)) + " h1=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n1, 1)) + " w2=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n2, 1)) + " h2=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n2, 1)) + " w3=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n3, 1)) + " h3=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n3, 1)) + " w4=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n4, 1)) + " h4=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n4, 1)) + " w5=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n5, 1)) + " h5=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n5, 1)));
    KR_XLog("TEXTTEST abs1=" + ("%f" % PartsEngine.GetComponentAbsolutePosX(n1)) + "," + ("%f" % PartsEngine.GetComponentAbsolutePosY(n1)) + " az=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(n1)));
}
void KR_XOurs(string tag) {
    int n = 2026092330;
    if (PartsEngine.IsExist(n)) {
        KR_XPart("MOON " + tag, n);
        KR_XLog("MOONTEXT " + tag + " <<<");
        KR_XLog(PartsEngine.GetTextPartsText(n, 1));
        KR_XLog(">>>");
    }
    else KR_XLog("MOON " + tag + " none");
    int t = 2026092002;
    if (PartsEngine.IsExist(t)) {
        KR_XPart("STTEXT " + tag, t);
        KR_XPart("STPANEL " + tag, 2026092001);
        KR_XLog("STTEXTTEXT " + tag + " <<<");
        KR_XLog(PartsEngine.GetTextPartsText(t, 1));
        KR_XLog(">>>");
    }
}
void KR_XTextRelease() {
    for (int n = 2026092801; n <= 2026092805; n++) PartsEngine.Release(n);
}

// the moon layout box of the status view (the first child of the root at 374,66); its label is the next number
int KR_XFeelBox() {
    int root = KR_XRoot();
    for (int n = 1000000000; n < 1000040000; n++) {
        if (!PartsEngine.IsExist(n)) continue;
        if (PartsEngine.Parts_GetParentPartsNumber(n) != root) continue;
        if (PartsEngine.GetComponentPosX(n) == 374.0 && PartsEngine.GetComponentPosY(n) == 66.0) { KR_XSet("Box", "%d" % n); return n; }
    }
    return 0;
}
int KR_XW(int n, int size, string t) {
    PartsEngine.Parts_SetText(n, "", 1);
    PartsEngine.Parts_SetFont(n, 257, size, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(n, true, 1);
    PartsEngine.Parts_SetText(n, t, 1);
    PartsEngine.SetComponentShow(n, false);
    int w = PartsEngine.Parts_GetPartsWidth(n, 1);
    KR_XLog("METRIC size=" + ("%d" % size) + " w=" + ("%d" % w) + " h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n, 1)) + " text=" + t);
    PartsEngine.Release(n);
    return w;
}
void KR_XMetrics(int root) {
    int n = 2026092808;
    for (int s = 18; s <= 24; s += 2) {
        KR_XW(n, s, "가가가가가가가가가가");
        KR_XW(n, s, "0000000000");
        KR_XW(n, s, "1111111111");
        KR_XW(n, s, "··········");
        KR_XW(n, s, "|          |");
        KR_XW(n, s, "||");
        KR_XW(n, s, "((((((((((");
        KR_XW(n, s, "//////////");
        KR_XW(n, s, "::::::::::");
        KR_XW(n, s, "　　　　　　　　　　");
        KR_XW(n, s, "…………………………");
        KR_XW(n, s, "친밀도 31 (3/5) · 다음 조건 50");
        KR_XW(n, s, "10/11 아침 · 인물 · 마나미 · 이즈미와 2");
        KR_XW(n, s, "루트: 네 명 중 가장 높으면");
        KR_XW(n, s, "이달 남은 특훈 뒤 대화 6");
        KR_XW(n, s, "${font r=255 g=224 b=96}이벤트${/font}");
        KR_XW(n, s, "${font size=20}가가가가가가가가가가${/font}");
    }
}
// the planned look: two lines under the moons, white with a dark edge; one more part left in place (leak test)
void KR_XEdge(int root) {
    int n = 2026092810;
    string t = "31 / 120\n${font size=16}단계 3/5${/font}";
    PartsEngine.Parts_SetText(n, "", 1);
    PartsEngine.Parts_SetFont(n, 257, 18, 255, 255, 255, 0.0, 0, 0, 0, 2.0, 1);
    PartsEngine.Parts_SetTextEnableTag(n, true, 1);
    PartsEngine.Parts_SetTextLineSpace(n, 2, 1);
    PartsEngine.Parts_SetText(n, t, 1);
    PartsEngine.Parts_SetParentPartsNumber(n, root);
    PartsEngine.SetComponentPos(n, 374.0, 114.0);
    PartsEngine.SetComponentPosZ(n, 260);
    PartsEngine.SetComponentShow(n, true);
    int m = 2026092809;
    PartsEngine.Parts_SetText(m, "", 1);
    PartsEngine.Parts_SetFont(m, 257, 18, 255, 255, 96, 0.0, 0, 0, 0, 2.0, 1);
    PartsEngine.Parts_SetTextEnableTag(m, true, 1);
    PartsEngine.Parts_SetText(m, "31 / 120 · 단계 3/5", 1);
    PartsEngine.Parts_SetParentPartsNumber(m, root);
    PartsEngine.SetComponentPos(m, 460.0, 114.0);
    PartsEngine.SetComponentPosZ(m, 260);
    PartsEngine.SetComponentShow(m, true);
    KR_XLog("EDGE w=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n, 1)) + " h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n, 1)) + " w2=" + ("%d" % PartsEngine.Parts_GetPartsWidth(m, 1)) + " h2=" + ("%d" % PartsEngine.Parts_GetPartsHeight(m, 1)));
}
bool KR_XTick(int kind) {
    string stage = KR_XGet("Stage");
    int frames = KR_XNum("Frames") + 1;
    KR_XSet("Frames", "%d" % frames);
    if (frames == 1) KR_XLog("TICK kind=" + ("%d" % kind) + " stage=" + stage + " stack=" + KR_XStack());
    if (frames > 1500) { KR_XLog("STUCK stage=" + stage + " stack=" + KR_XStack()); KR_XShot("x_stuck.bmp"); system.Exit(5); return false; }
    if (frames < 30) return false;
    if (stage == "") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") return false;
        KR_XLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " party=" + ("%d" % L_Party::GetPersonID(0)) + "," + ("%d" % L_Party::GetPersonID(1)) + "," + ("%d" % L_Party::GetPersonID(2)));
        for (int c = 1; c <= 8; c++) KR_XFeel(c);
        KR_XSet("Idx", "0");
        KR_XSet("Stage", "member");
        KR_XEnd(11);
        return false;
    }
    if (stage == "member") {
        if (!KR_XOn("_UpdateInputMember")) return false;
        int i = KR_XNum("Idx");
        string list = "@@PERSONS@@";
        if (i >= list.Length()) { KR_XSet("Stage", "home2"); return true; }
        string ch = KR_JosaSlice(list, i, 1);
        int who = ch.ToInt();
        KR_XSet("Who", "%d" % who);
        KR_XSet("Idx", "%d" % (i + 1));
        KR_XShot("x_member_" + ("%d" % who) + ".bmp");
        KR_XSet("Stage", "dlg");
        KR_XEnd(1000 + who);
        return false;
    }
    if (stage == "dlg") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        KR_XSet("Stage", "p1");
        KR_XEnd(3);
        return false;
    }
    if (stage == "p1") {
        if (!KR_XOn("C_Status::_UpdateInput")) return false;
        int w = KR_XNum("Who");
        KR_XShot("x_p1_" + ("%d" % w) + ".bmp");
        KR_XOurs("P1 " + ("%d" % w));
        KR_XScan("P1 " + ("%d" % w));
        KR_XFeel(w);
        if (w == 2 && @@TESTS@@) {
            KR_XTextTest(KR_XRoot());
            KR_XShot("x_p1_texttest.bmp");
            KR_XTextRelease();
            KR_XMetrics(KR_XRoot());
            KR_XEdge(KR_XRoot());
            KR_XShot("x_p1_edge.bmp");
            KR_XLog("LEAKTEST made " + ("%d" % KR_XB(PartsEngine.IsExist(2026092809))) + " moonbox=" + ("%d" % KR_XFeelBox()));
        }
        KR_XSet("Stage", "p4");
        KR_XEnd(1);
        return false;
    }
    if (stage == "p4") {
        int w2 = KR_XNum("Who");
        KR_XShot("x_p4_" + ("%d" % w2) + ".bmp");
        KR_XOurs("P4 " + ("%d" % w2));
        KR_XScan("P4 " + ("%d" % w2));
        KR_XSet("Stage", "back");
        KR_XEnd(0);
        return false;
    }
    if (stage == "back") {
        if (!KR_XOn("_UpdateInputMember")) return false;
        KR_XOurs("BACK " + KR_XGet("Who"));
        KR_XScan("BACK " + KR_XGet("Who"));
        KR_XSet("Stage", "member");
        KR_XSet("Frames", "0");
        return false;
    }
    if (stage == "home2") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        KR_XLog("LEAKTEST home2 ours=" + ("%d" % KR_XB(PartsEngine.IsExist(2026092809))) + " edge=" + ("%d" % KR_XB(PartsEngine.IsExist(2026092810))) + " box=" + KR_XGet("Box") + " boxexist=" + ("%d" % KR_XB(PartsEngine.IsExist(KR_XNum("Box")))) + " label=" + ("%d" % KR_XB(PartsEngine.IsExist(KR_XNum("Box") + 1))) + " root=" + ("%d" % KR_XRoot()));
        KR_XOurs("HOME2");
        KR_XScan("HOME2");
        KR_XShot("x_home_after.bmp");
        KR_XLog("END");
        system.Exit(0);
    }
    return false;
}
// probe only: what the player's hover does before the click (C_SceneHomebase@RunMember OnEnterChara: SetInfo + Show) = page 0
void KR_XPrepStatus(int charaNo, ref C_HomeMemberView memView) {
    memView.m_StatusView.SetInfo(charaNo);
    memView.m_StatusView.Show();
    KR_XLog("PREPSTATUS " + ("%d" % charaNo));
    KR_XShot("x_preview_" + ("%d" % charaNo) + ".bmp");
    KR_XOurs("PREVIEW " + ("%d" % charaNo));
    KR_XScan("PREVIEW " + ("%d" % charaNo));
}
int KR_XMsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    KR_XLog("MESSAGE WAIT stage=" + KR_XGet("Stage") + " stack=" + KR_XStack());
    KR_XShot("x_msg.bmp");
    system.Exit(8);
    return 0;
}
int KR_XMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_XLog("SAVEFOLDER " + system.GetSaveFolderName());
    string s = KR_XRead("claude_probe_args.txt");
    int nl = s.Find("\n");
    if (nl > 0) s = KR_JosaSlice(s, 0, nl);
    KR_XLog("resume loading " + s);
    system.ResumeLoad("@@KEY@@", s);
    system.Exit(2);
    return 2;
}
'''


def build(key, persons):
    base = L.base_paths()
    if CANDIDATE:
        base = dict(ain=R23 / 'candidate' / 'NightRemaster.ain', meta=L.WORK / 'build' / 'candidate_meta.json',
                    raw=L.WORK / 'build' / 'candidate_raw_code.jam')
    src = base['ain']
    m = L.read_meta(base['meta'])
    work = OUT / 'build'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    jaf = P.MUTE_JAF + '\n' + XJAF.replace('@@KEY@@', key).replace('@@PERSONS@@', ''.join(str(p) for p in persons)).replace('@@TESTS@@', 'false' if CANDIDATE else 'true')
    jaf = L.jaf_literal_encode(jaf)
    (work / 'x.jaf').write_text(jaf, 'utf8')
    decl = work / 'x_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'x.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'x_declared_meta.json', decl)
    dm = L.read_meta(work / 'x_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    for f in m['functions']:
        if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47:
            if f['name'] == 'C_UserInputManager::IsClickCancelOtherMouse':
                patch.append(f"FUNC {f['index']}\n\tPUSH 1\n\tCALLFUNC KR_XTick\n\tRETURN\nENDFUNC {f['name']}\n")
            elif f['name'] == 'C_UserInputManager::IsClickCancel':
                patch.append(f"FUNC {f['index']}\n\tPUSH 2\n\tCALLFUNC KR_XTick\n\tRETURN\nENDFUNC {f['name']}\n")
            else:
                patch.append(f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n")
    for f in added:
        path = work / f"x_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), f['name']))
    rs = L.fid_of(m, 'C_SceneHomebase@RunStatus')
    path = work / f'original_{rs}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SceneHomebase@RunStatus', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SceneHomebase@RunStatus'), '\t.LOCALREF charaNo\n\t.LOCALREF memView\n\tCALLFUNC KR_XPrepStatus\n'))
    (work / 'x.jam').write_text('\n'.join(patch), 'utf8')
    out = P.RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'x.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_XMain'])
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    vers = L.versions(base['raw'])
    n = 0
    for f in m['functions']:
        name = L.raw_symbol(m, f['index'])
        if not name.startswith(P.MSG_LAMBDA):
            continue
        for v in [v for v in vers.get(f['index'], []) if v['start'] == f['address']]:
            for ad, op in v['ops']:
                if op == f'CALLFUNC 0x{wait:x}':
                    struct.pack_into('<Hi', raw, 16 + ad, 0x30, ids['KR_XMsgWait'])
                    n += 1
    assert n == 1, n
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(probe_sha256=L.sha(out))


CANDIDATE = False


def main():
    global CANDIDATE
    args = sys.argv[1:]
    if args and args[0] == '--candidate':
        CANDIDATE = True
        args = args[1:]
    save = args[0] if args else 'NightR44.asd'
    persons = [int(x) for x in args[1:]] or [2, 4, 6]
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, free
    assert not P.user_game_running(), 'the user game is running: do not start a probe beside it'
    user_before = P.user_state()
    P.setup_folder()
    key = L.save_records(L.save_path(save))['key']
    info = build(key, persons)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    r = P.run_one(save, 'regs', info, 'X' + stamp)
    shots = []
    from PIL import Image
    dest = OUT / ('shots_candidate' if CANDIDATE else 'shots')
    dest.mkdir(parents=True, exist_ok=True)
    for b in sorted(P.RUN.glob('x_*.bmp')):
        png = dest / (b.stem + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(png.name)
    r['screenshots'] = shots
    r['user_save_folder_unchanged'] = P.user_state() == user_before
    L.writej(dest / 'result.json', r)
    print(json.dumps({k: v for k, v in r.items() if k != 'log'}, ensure_ascii=False, indent=1))
    print('\n'.join(r['log'][:400]))


if __name__ == '__main__':
    main()
