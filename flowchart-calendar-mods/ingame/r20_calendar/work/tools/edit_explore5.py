p = __file__.replace('edit_explore5.py', 'explore_r20.py')
s = open(p, encoding='utf8').read()
a = 'void KR_XTextRelease() {'
b = '''// z semantics + a construction panel + mul colour, parented to the status root
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
    PartsEngine.Parts_SetText(tn, "${font r=255 g=224 b=96}이벤트${/font}\\n특훈 뒤 대화 ${font r=128 g=224 b=255}12${/font}번 봄\\n이달 남은 특훈 뒤 대화 ${font r=128 g=224 b=255}3${/font}\\n던전 동행 남은 장면 ${font r=128 g=224 b=255}14${/font}\\n　마코토와 ${font r=128 g=224 b=255}3${/font}\\n　호시카와와 ${font r=128 g=224 b=255}12${/font}\\n　단둘이 ${font r=128 g=224 b=255}2${/font}\\n\\n${font r=150 g=150 b=150}달력에서 자세히${/font}", 1);
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
''' + a
if 'KR_XZTest' not in s:
    s = s.replace(a, b, 1)
a = '''        KR_XTextTest(root, 60, 120);
        KR_XShot("x_status_texttest.bmp");
        KR_XTextRelease();
        KR_XShot("x_status_textgone.bmp");'''
b = '''        KR_XSet("Stage", "st3b");
        KR_XEnd(2);
        return false;
    }
    if (stage == "st3b") {
        int root = PartsEngine.GetActivityPartsNumber("Game\\\\Scenes\\\\4000Homebase\\\\CharaStatus.pact", "ルートパーツ");
        KR_XLog("NOW PAGE 1 AGAIN; ZTEST on page 1");
        KR_XZTest(root);
        KR_XShot("x_status_ztest.bmp");
        KR_XZRelease();
        KR_XShot("x_status_zgone.bmp");'''
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
open(p, 'w', encoding='utf8').write(s)
print('ok')
