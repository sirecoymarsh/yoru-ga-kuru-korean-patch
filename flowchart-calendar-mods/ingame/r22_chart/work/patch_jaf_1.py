from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'claude_chart_r22.jaf'
s = p.read_text('utf8')
rep = [
("void KR_CBox(int n, int parent, int x, int y, int w, int h, int r, int g, int b, int a, int br, int bg, int bb, int z) {",
 "void KR_CBox(int n, int parent, float x, float y, int w, int h, int r, int g, int b, int a, int br, int bg, int bb, int z) {"),
("    PartsEngine.SetComponentPos(n, itof(x), itof(y));\n    PartsEngine.SetComponentPosZ(n, z);\n    PartsEngine.SetComponentShow(n, true);\n}\nvoid KR_CText(int n, int parent, int x, int y, int size, string text, int z) {",
 "    PartsEngine.SetComponentPos(n, x, y);\n    PartsEngine.SetComponentPosZ(n, z);\n    PartsEngine.SetComponentShow(n, true);\n}\nvoid KR_CText(int n, int parent, float x, float y, int size, string text, int z) {"),
("    PartsEngine.Parts_SetParentPartsNumber(n, parent);\n    PartsEngine.SetComponentPos(n, itof(x), itof(y));\n    PartsEngine.SetComponentPosZ(n, z);\n    PartsEngine.SetComponentShow(n, true);\n    PartsEngine.Parts_SetPassCursor(n, true);\n}",
 "    PartsEngine.Parts_SetParentPartsNumber(n, parent);\n    PartsEngine.SetComponentPos(n, x, y);\n    PartsEngine.SetComponentPosZ(n, z);\n    PartsEngine.SetComponentShow(n, true);\n    PartsEngine.Parts_SetPassCursor(n, true);\n}"),
("float itof(int v) {\n    float f = v;\n    return f;\n}\n", ""),
("    KR_CText(KR_CPart(1), root, 24, 18, 24, head, 5);\n    KR_CText(KR_CPart(2), root, 200, 670, 17,",
 "    KR_CText(KR_CPart(1), root, 24.0, 18.0, 24, head, 5);\n    KR_CText(KR_CPart(2), root, 200.0, 674.0, 17,"),
("    KR_CText(KR_CPart(3), root, 590, 664, 22,", "    KR_CText(KR_CPart(3), root, 590.0, 670.0, 22,"),
("    KR_CBox(KR_CPart(30), root, 1136, 12, 120, 40,", "    KR_CBox(KR_CPart(30), root, 1136.0, 12.0, 120, 40,"),
("    KR_CText(KR_CPart(31), KR_CPart(30), 38, 7, 22, \"닫기\", 1);", "    KR_CText(KR_CPart(31), KR_CPart(30), 38.0, 7.0, 22, \"닫기\", 1);"),
("    KR_CBox(KR_CPart(32), root, 24, 662, 160, 44,", "    KR_CBox(KR_CPart(32), root, 24.0, 662.0, 160, 44,"),
("    KR_CText(KR_CPart(33), KR_CPart(32), 24, 9, 22, \"← 이전 쪽\", 1);", "    KR_CText(KR_CPart(33), KR_CPart(32), 24.0, 9.0, 22, \"← 이전 쪽\", 1);"),
("    KR_CBox(KR_CPart(34), root, 1092, 662, 160, 44,", "    KR_CBox(KR_CPart(34), root, 1092.0, 662.0, 160, 44,"),
("    KR_CText(KR_CPart(35), KR_CPart(34), 24, 9, 22, \"다음 쪽 →\", 1);", "    KR_CText(KR_CPart(35), KR_CPart(34), 24.0, 9.0, 22, \"다음 쪽 →\", 1);"),
("""        if (t == tab) KR_CBox(bx, root, 24 + t * 120, 62, 112, 40, 70, 56, 20, 245, 255, 214, 110, 4);
        else KR_CBox(bx, root, 24 + t * 120, 62, 112, 40, 22, 30, 60, 240, 110, 130, 170, 4);
        string label = KR_CTabName(t);
        int tx = 56 - label.Length() * 11;
        if (t == tab) label = KR_CTint(label, KR_CGold());
        KR_CText(KR_CTabText(t), bx, tx, 8, 22, label, 1);""",
"""        if (t == tab) KR_CBox(bx, root, KR_CTabX(t), 62.0, 112, 40, 70, 56, 20, 245, 255, 214, 110, 4);
        else KR_CBox(bx, root, KR_CTabX(t), 62.0, 112, 40, 22, 30, 60, 240, 110, 130, 170, 4);
        string label = KR_CTabName(t);
        if (t == tab) label = KR_CTint(label, KR_CGold());
        KR_CText(KR_CTabText(t), bx, KR_CTabTx(t), 8.0, 22, label, 1);"""),
("""    int x = 24 + (s % 4) * 309;
    int y = 114 + (s / 4) * 182;
    int h = 118;
    if (thumb != "") h = 172;
    if (open) KR_CBox(box, KR_CRoot(), x, y, 301, h, 18, 30, 72, 236, 120, 170, 255, 10);
    else KR_CBox(box, KR_CRoot(), x, y, 301, h, 34, 34, 42, 236, 90, 90, 104, 10);""",
"""    int h = 118;
    if (thumb != "") h = 172;
    if (open) KR_CBox(box, KR_CRoot(), KR_CCellX(s), KR_CCellY(s), 301, h, 18, 30, 72, 236, 120, 170, 255, 10);
    else KR_CBox(box, KR_CRoot(), KR_CCellX(s), KR_CCellY(s), 301, h, 34, 34, 42, 236, 90, 90, 104, 10);"""),
("""    string idline = KR_CMark(no) + " " + KR_T9EvNo(no);
    string when = KR_CCellWhen(i);
    string name = "？？？";
    string cond = "";
    if (open) {
        name = KR_CCellName(i);
        cond = KR_CCellCond(i);
        if (KR_CNoPlay(no) != 0) {
            if (cond == "") cond = "재생 불가(게임 안에서만)";
            else cond = cond + "\\n재생 불가(게임 안에서만)";
        }
    }
    if (!open) {
        idline = KR_CTint(idline, KR_CGray());
        when = KR_CTint(when, KR_CGray());
        name = KR_CTint(name, KR_CGray());
    }""",
"""    string idline = KR_CMark(no) + " " + KR_T9EvNo(no);
    string when = KR_CCellWhen(i);
    string name = KR_CTint(KR_CCellName(i), KR_CWhite());
    string cond = KR_CCellCond(i);
    if (!open) {
        idline = KR_CTint("● " + KR_T9EvNo(no), KR_CGray());
        when = KR_CTint(when, KR_CGray());
        name = KR_CTint("？？？", KR_CGray());
        cond = "";
    }"""),
("""        KR_CText(id, box, 138, 10, 17, idline + "\\n" + when, 2);
        KR_CText(nm, box, 10, 104, 18, KR_CTint(name, KR_CWhite()), 2);
        if (cond != "") KR_CText(cd, box, 10, 128, 15, KR_CTint(cond, KR_CGray()), 2);
        return;
    }
    KR_CText(nm, box, 10, 8, 18, KR_CTint(name, KR_CWhite()), 2);
    KR_CText(id, box, 10, 52, 16, idline + "　" + when, 2);
    if (cond != "") KR_CText(cd, box, 10, 76, 15, KR_CTint(cond, KR_CGray()), 2);""",
"""        KR_CText(id, box, 138.0, 10.0, 17, idline + "\\n" + when, 2);
        KR_CText(nm, box, 10.0, 104.0, 18, name, 2);
        if (cond != "") KR_CText(cd, box, 10.0, 128.0, 15, KR_CTint(cond, KR_CGray()), 2);
        return;
    }
    KR_CText(nm, box, 10.0, 8.0, 18, name, 2);
    KR_CText(id, box, 10.0, 52.0, 16, idline + "　" + when, 2);
    if (cond != "") KR_CText(cd, box, 10.0, 76.0, 15, KR_CTint(cond, KR_CGray()), 2);"""),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
p.write_text(s, 'utf8')
print('patched')
