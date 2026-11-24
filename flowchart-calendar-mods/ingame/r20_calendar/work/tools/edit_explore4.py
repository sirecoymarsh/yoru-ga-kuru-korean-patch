p = __file__.replace('edit_explore4.py', 'explore_r20.py')
s = open(p, encoding='utf8').read()
start = s.index("PARTNER = r'''")
end = s.index("'''", start + 15) + 3
new = r"""PARTNER = r'''
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
'''"""
s = s[:start] + new + s[end:]
a = 'int KR_XB(bool v) { if (v) return 1; return 0; }'
b = a + '''
string KR_XDigit(int d) {
    if (d == 1) return "１";
    if (d == 2) return "２";
    if (d == 3) return "３";
    if (d == 4) return "４";
    if (d == 5) return "５";
    if (d == 6) return "６";
    if (d == 7) return "７";
    return "０";
}'''
if 'KR_XDigit(int d)' not in s:
    s = s.replace(a, b, 1)
open(p, 'w', encoding='utf8').write(s)
print('ok')
