"""r20 exploration probe (Claude Opus 5.5, 2026-09-27): screenshots and part geometry of the two screens r20 touches, on the
BASE AIN (= the r19 install) plus probe-only code. Nothing here ships. Isolated + muted run folder r20_calendar\\probe\\run.

  python explore_r20.py member [SAVE]    home save -> 파티 편성 (RunMember) -> status window pages 1..3 -> text-part test
  python explore_r20.py partner [SAVE]   Saturday partner-select save (NightR40) -> close the save screen -> partner screen

Per-frame driver: C_UserInputManager::IsClickCancelOtherMouse / IsClickCancel bodies call KR_XTick(kind) (probe only); the
stage machine reads the VM call stack (system.GetFuncStackName) to know which screen waits.
"""
import sys, json, re, struct, shutil, datetime, time
from pathlib import Path
sys.dont_write_bytecode = True
R20 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R20))
import r20lib as L
import probe_calendar_r20 as P

OUT = R20 / 'work' / 'explore'
OUT.mkdir(parents=True, exist_ok=True)

XJAF = r'''
int KR_XB(bool v) { if (v) return 1; return 0; }
string KR_XDigit(int d) {
    if (d == 1) return "１";
    if (d == 2) return "２";
    if (d == 3) return "３";
    if (d == 4) return "４";
    if (d == 5) return "５";
    if (d == 6) return "６";
    if (d == 7) return "７";
    return "０";
}
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
void KR_XDumpAct(string act) {
    if (!PartsEngine.IsExistActivity(act)) { KR_XLog("ACT MISSING " + act); return; }
    int n = PartsEngine.NumofActivityParts(act);
    KR_XLog("ACT " + act + " parts=" + ("%d" % n));
    string pn = "";
    int num = 0;
    for (int i = 0; i < n; i++) {
        if (!PartsEngine.GetActivityParts(i, act, pn, num)) continue;
        float ax = PartsEngine.GetComponentAbsolutePosX(num);
        float ay = PartsEngine.GetComponentAbsolutePosY(num);
        int w = PartsEngine.Parts_GetPartsWidth(num, 1);
        int h = PartsEngine.Parts_GetPartsHeight(num, 1);
        int z = PartsEngine.GetComponentAbsolutePosZ(num);
        int par = PartsEngine.Parts_GetParentPartsNumber(num);
        bool sh = PartsEngine.IsComponentShow(num);
        int shi = 0;
        if (sh) shi = 1;
        KR_XLog("P " + ("%d" % num) + " parent=" + ("%d" % par) + " show=" + ("%d" % shi) + " abs=" + ("%f" % ax) + "," + ("%f" % ay) + " z=" + ("%d" % z) + " wh=" + ("%d" % w) + "x" + ("%d" % h) + " name=" + pn);
    }
}
void KR_XDumpActs(string base) {
    KR_XDumpAct(base);
    for (int k = 1; k <= 3; k++) {
        string nm = base + ":" + ("%d" % k);
        if (PartsEngine.IsExistActivity(nm)) KR_XDumpAct(nm);
    }
}
void KR_XEnd(int code) {
    KR_XSet("Frames", "0");
    AFL_Parts_EndWaitForClick(code);
}
// a runtime text part test: fixed number, font 257, Korean proxy text, optional parent
void KR_XTextTest(int parent, int x, int y) {
    int n = 2026092701;
    KR_XLog("TEXTTEST before exist=" + ("%d" % KR_XB(PartsEngine.IsExist(n))) + " free=" + ("%d" % PartsEngine.GetFreeNumber()));
    PartsEngine.Parts_SetText(n, "특훈 뒤 대화 3번 봄", 1);
    PartsEngine.Parts_SetFont(n, 257, 22, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetText(n, "특훈 뒤 대화 3번 봄", 1);
    if (parent > 0) PartsEngine.Parts_SetParentPartsNumber(n, parent);
    PartsEngine.SetComponentPos(n, x * 1.0, y * 1.0);
    PartsEngine.SetComponentPosZ(n, 9000);
    PartsEngine.SetComponentShow(n, true);
    int m2 = 2026092702;
    PartsEngine.Parts_SetText(m2, "${font r=255 g=224 b=96}이벤트${/font} 남은 대화 ${font r=128 g=224 b=255}5${/font}", 1);
    PartsEngine.Parts_SetFont(m2, 257, 22, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(m2, true, 1);
    PartsEngine.Parts_SetText(m2, "${font r=255 g=224 b=96}이벤트${/font} 남은 대화 ${font r=128 g=224 b=255}5${/font}", 1);
    if (parent > 0) PartsEngine.Parts_SetParentPartsNumber(m2, parent);
    PartsEngine.SetComponentPos(m2, x * 1.0, (y + 30) * 1.0);
    PartsEngine.SetComponentPosZ(m2, 9000);
    PartsEngine.SetComponentShow(m2, true);
    int m3 = 2026092703;
    PartsEngine.Parts_SetText(m3, "흐린 줄 마코토와 3", 1);
    PartsEngine.Parts_SetFont(m3, 257, 22, 150, 150, 150, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetText(m3, "흐린 줄 마코토와 3", 1);
    if (parent > 0) PartsEngine.Parts_SetParentPartsNumber(m3, parent);
    PartsEngine.SetComponentPos(m3, x * 1.0, (y + 60) * 1.0);
    PartsEngine.SetComponentPosZ(m3, 9000);
    PartsEngine.SetComponentShow(m3, true);
    KR_XLog("TEXTTEST made exist=" + ("%d" % KR_XB(PartsEngine.IsExist(n))) + " w=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n, 1)) + " h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n, 1)) + " w2=" + ("%d" % PartsEngine.Parts_GetPartsWidth(m2, 1)) + " abs=" + ("%f" % PartsEngine.GetComponentAbsolutePosX(n)) + "," + ("%f" % PartsEngine.GetComponentAbsolutePosY(n)));
}
// z semantics + a construction panel + mul colour, parented to the status root
void KR_XZTest(int root) {
    int pn = 2026092731;
    Ｐ＿構築手順＿作成(pn, 338, 448, 1);
    Ｐ＿構築手順＿色塗り全(pn, 10, 28, 84, 216, 1);
    Ｐ＿構築手順＿色塗り(pn, 0, 0, 338, 2, 150, 200, 255, 255, 1);
    Ｐ＿構築手順＿色塗り(pn, 0, 446, 338, 2, 150, 200, 255, 255, 1);
    Ｐ＿構築手順＿色塗り(pn, 0, 0, 2, 448, 150, 200, 255, 255, 1);
    Ｐ＿構築手順＿色塗り(pn, 336, 0, 2, 448, 150, 200, 255, 255, 1);
    Ｐ＿構築ビルド(pn, 1);
    PartsEngine.Parts_SetParentPartsNumber(pn, root);
    PartsEngine.SetComponentPos(pn, 32.0, 64.0);
    PartsEngine.SetComponentPosZ(pn, 40);
    PartsEngine.SetComponentShow(pn, true);
    int tn = 2026092732;
    PartsEngine.Parts_SetText(tn, "", 1);
    PartsEngine.Parts_SetFont(tn, 257, 24, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
    PartsEngine.Parts_SetTextEnableTag(tn, true, 1);
    PartsEngine.Parts_SetTextLineSpace(tn, 8, 1);
    PartsEngine.Parts_SetText(tn, "${font r=255 g=224 b=96}이벤트${/font}\n특훈 뒤 대화 ${font r=128 g=224 b=255}12${/font}번 봄\n이달 남은 특훈 뒤 대화 ${font r=128 g=224 b=255}3${/font}\n던전 동행 남은 장면 ${font r=128 g=224 b=255}14${/font}\n　마코토와 ${font r=128 g=224 b=255}3${/font}\n　호시카와와 ${font r=128 g=224 b=255}12${/font}\n　단둘이 ${font r=128 g=224 b=255}2${/font}\n\n${font r=150 g=150 b=150}달력에서 자세히${/font}", 1);
    PartsEngine.Parts_SetParentPartsNumber(tn, root);
    PartsEngine.SetComponentPos(tn, 52.0, 80.0);
    PartsEngine.SetComponentPosZ(tn, 41);
    PartsEngine.SetComponentShow(tn, true);
    AFL_View_Update();
    KR_XLog("ZTEST root z=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(root)) + " panel z=" + ("%d" % PartsEngine.GetComponentPosZ(pn)) + " abs=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(pn)) + " text abs=" + ("%d" % PartsEngine.GetComponentAbsolutePosZ(tn)) + " text w=" + ("%d" % PartsEngine.Parts_GetPartsWidth(tn, 1)) + " h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(tn, 1)) + " panel abs x=" + ("%f" % PartsEngine.GetComponentAbsolutePosX(pn)) + " y=" + ("%f" % PartsEngine.GetComponentAbsolutePosY(pn)));
}
void KR_XZRelease() {
    PartsEngine.Release(2026092731);
    PartsEngine.Release(2026092732);
}
void KR_XTextRelease() {
    PartsEngine.Release(2026092701);
    PartsEngine.Release(2026092702);
    PartsEngine.Release(2026092703);
    KR_XLog("TEXTTEST released exist=" + ("%d" % KR_XB(PartsEngine.IsExist(2026092701))) + " free=" + ("%d" % PartsEngine.GetFreeNumber()));
}
bool KR_XTick(int kind) {
    string stage = KR_XGet("Stage");
    int frames = KR_XNum("Frames") + 1;
    KR_XSet("Frames", "%d" % frames);
    if (frames == 1) KR_XLog("TICK kind=" + ("%d" % kind) + " stage=" + stage + " stack=" + KR_XStack());
    if (frames > 1500) { KR_XLog("STUCK stage=" + stage + " stack=" + KR_XStack()); KR_XShot("x_stuck.bmp"); system.Exit(5); return false; }
    if (frames < 30) return false;
    @@SCRIPT@@
    return false;
}
// probe only: what the player's hover does before the click (C_SceneHomebase@RunMember OnEnterChara: SetInfo + Show)
void KR_XPrepStatus(int charaNo, ref C_HomeMemberView memView) {
    memView.m_StatusView.SetInfo(charaNo);
    memView.m_StatusView.Show();
    KR_XLog("PREPSTATUS " + ("%d" % charaNo));
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

MEMBER = r'''
    if (stage == "") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") return false;
        KR_XLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " dow=" + ("%d" % L_Calendar::GetDayOfWeek()) + " party=" + ("%d" % L_Party::GetPersonID(0)) + "," + ("%d" % L_Party::GetPersonID(1)) + "," + ("%d" % L_Party::GetPersonID(2)) + " free=" + ("%d" % PartsEngine.GetFreeNumber()));
        KR_XShot("x_home.bmp");
        KR_XSet("Stage", "member");
        KR_XEnd(11);
        return false;
    }
    if (stage == "member") {
        if (!KR_XOn("_UpdateInputMember")) return false;
        KR_XShot("x_member.bmp");
        KR_XDumpActs("Game\\Scenes\\4000Homebase\\HomeMember.pact");
        KR_XDumpActs("Game\\Scenes\\Common\\SelectAlly.pact");
        KR_XDumpActs("Game\\Scenes\\4000Homebase\\CharaStatus.pact");
        int who = L_Party::GetPersonID(1);
        if (who <= 1) who = 2;
        KR_XSet("Who", "%d" % who);
        KR_XSet("Stage", "statusdlg");
        KR_XEnd(1000 + who);
        return false;
    }
    if (stage == "statusdlg") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        KR_XShot("x_member_dialog.bmp");
        KR_XSet("Stage", "st1");
        KR_XEnd(3);
        return false;
    }
    if (stage == "st1") {
        if (!KR_XOn("C_Status::_UpdateInput")) return false;
        KR_XShot("x_status_p1.bmp");
        KR_XDumpActs("Game\\Scenes\\4000Homebase\\CharaStatus.pact");
        KR_XSet("Stage", "st2");
        KR_XEnd(2);
        return false;
    }
    if (stage == "st2") {
        KR_XShot("x_status_p2.bmp");
        KR_XSet("Stage", "st3");
        KR_XEnd(2);
        return false;
    }
    if (stage == "st3") {
        KR_XShot("x_status_p3.bmp");
        int root = PartsEngine.GetActivityPartsNumber("Game\\Scenes\\4000Homebase\\CharaStatus.pact", "ルートパーツ");
        KR_XLog("STATUS ROOT " + ("%d" % root) + " abs=" + ("%f" % PartsEngine.GetComponentAbsolutePosX(root)) + "," + ("%f" % PartsEngine.GetComponentAbsolutePosY(root)));
        KR_XSet("Stage", "st3b");
        KR_XEnd(2);
        return false;
    }
    if (stage == "st3b") {
        int root = PartsEngine.GetActivityPartsNumber("Game\\Scenes\\4000Homebase\\CharaStatus.pact", "ルートパーツ");
        KR_XLog("NOW PAGE 1 AGAIN; ZTEST on page 1");
        KR_XZTest(root);
        KR_XShot("x_status_ztest.bmp");
        KR_XZRelease();
        KR_XShot("x_status_zgone.bmp");
        KR_XSet("Stage", "st4");
        KR_XEnd(2);
        return false;
    }
    if (stage == "st4") {
        KR_XShot("x_status_p1_again.bmp");
        KR_XSet("Stage", "st5");
        KR_XEnd(4);
        return false;
    }
    if (stage == "st5") {
        KR_XShot("x_status_nextchara.bmp");
        KR_XSet("Stage", "back");
        KR_XEnd(0);
        return false;
    }
    if (stage == "back") {
        if (!KR_XOn("_UpdateInputMember")) return false;
        KR_XShot("x_member_back.bmp");
        KR_XSet("Stage", "home2");
        return true;
    }
    if (stage == "home2") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        KR_XShot("x_home_after.bmp");
        KR_XLog("free=" + ("%d" % PartsEngine.GetFreeNumber()));
        KR_XLog("END");
        system.Exit(0);
    }
'''

PARTNER = r'''
    if (stage == "") {
        if (KR_XOn("C_SceneSaveLoad@Update")) { KR_XSet("Frames", "0"); return true; }
        if (!KR_XOn("_UpdateInputPartner")) return false;
        string act = "Game\\Scenes\\Common\\SelectAlly.pact";
        for (int p = 2; p <= 8; p++) {
            string nm = "ＣＧ_キャラ" + KR_XDigit(p - 1);
            int cg = PartsEngine.GetActivityPartsNumber(act, nm);
            int shown = KR_XB(PartsEngine.IsComponentShow(cg));
            KR_XLog("PORTRAIT " + ("%d" % p) + " part=" + ("%d" % cg) + " show=" + ("%d" % shown) + " x=" + ("%f" % PartsEngine.GetComponentAbsolutePosX(cg)) + " y=" + ("%f" % PartsEngine.GetComponentAbsolutePosY(cg)));
            if (shown == 0) continue;
            int n1 = 2026092710 + p * 2;
            int size = 16 + (p % 3) * 2;
            string t = "${font r=255 g=255 b=255}대화 ${font r=128 g=224 b=255}12${/font}번 봄${/font}\n${font r=255 g=255 b=255}남은 대화 ${font r=128 g=224 b=255}3${/font}${/font}";
            if (p % 2 == 1) t = "${font r=150 g=150 b=150}대화 12번 봄\n남은 대화 3${/font}";
            PartsEngine.Parts_SetText(n1, t, 1);
            PartsEngine.Parts_SetFont(n1, 257, size, 255, 255, 255, 0.0, 0, 0, 0, 0.0, 1);
            PartsEngine.Parts_SetTextEnableTag(n1, true, 1);
            PartsEngine.Parts_SetTextLineSpace(n1, 2, 1);
            PartsEngine.Parts_SetText(n1, t, 1);
            PartsEngine.SetComponentPos(n1, PartsEngine.GetComponentAbsolutePosX(cg) + 6.0, PartsEngine.GetComponentAbsolutePosY(cg) - 48.0);
            PartsEngine.SetComponentPosZ(n1, 270);
            PartsEngine.SetComponentShow(n1, true);
            KR_XLog("LABEL " + ("%d" % p) + " size=" + ("%d" % size) + " w=" + ("%d" % PartsEngine.Parts_GetPartsWidth(n1, 1)) + " h=" + ("%d" % PartsEngine.Parts_GetPartsHeight(n1, 1)));
        }
        KR_XShot("x_labels.bmp");
        KR_XSet("Hover", "8");
        KR_XSet("Stage", "hover");
        KR_XSet("Frames", "0");
        return false;
    }
    if (stage == "hover") {
        if (frames < 90) return false;
        KR_XShot("x_labels_hover8.bmp");
        KR_XSet("Hover", "2");
        KR_XSet("Stage", "hover2");
        KR_XSet("Frames", "0");
        return false;
    }
    if (stage == "hover2") {
        if (frames < 90) return false;
        KR_XShot("x_labels_hover2.bmp");
        for (int q = 2; q <= 8; q++) PartsEngine.Release(2026092710 + q * 2);
        KR_XLog("END");
        system.Exit(0);
    }
'''


def build(mode, key):
    base = L.base_paths()
    src = base['ain']
    m = L.read_meta(base['meta'])
    work = OUT / ('build_' + mode)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    jaf = P.MUTE_JAF + '\n' + XJAF.replace('@@KEY@@', key).replace('@@SCRIPT@@', MEMBER if mode == 'member' else PARTNER)
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
    om = L.fid_of(m, 'C_SceneTrainingView@GetOnmouseChara')
    patch.append(f"FUNC {om}\n\tS_PUSH \"Hover\"\n\tCALLFUNC KR_XNum\n\tRETURN\nENDFUNC C_SceneTrainingView@GetOnmouseChara\n")
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


def main():
    mode = sys.argv[1]
    save = sys.argv[2] if len(sys.argv) > 2 else ('NightR44.asd' if mode == 'member' else 'NightR40.asd')
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, free
    user_before = P.user_state()
    P.setup_folder()
    key = L.save_records(L.save_path(save))['key']
    info = build(mode, key)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    r = P.run_one(save, 'regs', info, 'X' + stamp)
    shots = []
    from PIL import Image
    dest = OUT / mode
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
