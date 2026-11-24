# -*- coding: utf-8 -*-
"""One-off edit (10-18) after the first native run: the 기한 column cut 「11/30 · 26일」, a talk of several months (마나미 6월 and
11월) showed 「6월」 and 「놓침」 in November, the panel letters read small."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def edit(path, pairs):
    s = path.read_text('utf8')
    for a, b in pairs:
        assert s.count(a) == 1, (path.name, a[:80], s.count(a))
        s = s.replace(a, b)
    path.write_text(s, 'utf8')


edit(HERE / 'claude_deadline.jaf', [
    # the condition of a monthly talk names every month of its pools
    ('''int KR_DLTabOf(int i) {''', '''// the condition shown for a pending scene: a monthly talk names all its months (the calendar's own text names the first)
string KR_DLCond(int no, int i) {
    int info = KR_DLInfo(no);
    if (info / 100000000 != 1) return KR_B29Flat(KR_CCellCond(i));
    int mask = info % 100000000;
    string ms = "";
    for (int m = 4; m <= 11; m++) {
        if (KR_DLBit(mask, m) == 0) continue;
        if (ms != "") ms = ms + " · ";
        ms = ms + ("%d" % m) + "월";
    }
    return KR_XVName(KR_XVLaneNo(no)) + " · " + ms + " · 특훈 뒤 잡담";
}
int KR_DLTabOf(int i) {'''),
    # the row: a wider deadline column
    ('''    KR_CText(KR_LVP(base + 2), box, 38.0, 7.0, 15, KR_CTint(KR_LVCut(KR_DLDueText(due, left), 15, 84), KR_DLTint(left)), 2);
    string name = "？？？";
    if (!hidden) name = KR_B29Flat(KR_CCellName(i));
    KR_CText(KR_LVP(base + 3), box, 126.0, 7.0, 15, KR_CTint(KR_LVCut(name, 15, 236), KR_CWhite()), 2);
    string cond = "";
    if (!hidden) cond = KR_B29Flat(KR_CCellCond(i));''',
     '''    KR_CText(KR_LVP(base + 2), box, 38.0, 7.0, 15, KR_CTint(KR_LVCut(KR_DLDueText(due, left), 15, 104), KR_DLTint(left)), 2);
    string name = "？？？";
    if (!hidden) name = KR_B29Flat(KR_CCellName(i));
    KR_CText(KR_LVP(base + 3), box, 146.0, 7.0, 15, KR_CTint(KR_LVCut(name, 15, 222), KR_CWhite()), 2);
    string cond = "";
    if (!hidden) cond = KR_DLCond(no, i);'''),
    ('''        KR_CText(KR_LVP(62), root, 150.0, 148.0, 14, KR_CTint("장면", KR_CGray()), 5);
        KR_CText(KR_LVP(63), root, 400.0, 148.0, 14, KR_CTint("조건", KR_CGray()), 5);''',
     '''        KR_CText(KR_LVP(62), root, 170.0, 148.0, 14, KR_CTint("장면", KR_CGray()), 5);
        KR_CText(KR_LVP(63), root, 400.0, 148.0, 14, KR_CTint("조건", KR_CGray()), 5);'''),
    # the preview: a pending scene is open now (not 「놓침」), its condition as in the row
    ('''    int lane = KR_XVLaneNo(no);
    int st = KR_LVState(no, t, lane, save, nowTab);
    int left = KR_DLLeft(due, KR_DLToday());
    string cond = "-";
    bool two = false;
    if (!hidden) {
        string c0 = KR_CCellCond(i);''',
     '''    int st = 0;
    if (!save && KR_CGlobal(no) == 1) st = 2;
    int left = KR_DLLeft(due, KR_DLToday());
    string cond = "-";
    bool two = false;
    if (!hidden) {
        string c0 = KR_DLCond(no, i);'''),
])
edit(HERE / 'build_pact_deadline.py', [
    ("TEXTS = [('KR_DL_Title', '기한 있는 장면', st(15, GOLD), X0 + 10, Y0 + 8)]",
     "TEXTS = [('KR_DL_Title', '기한 있는 장면', st(16, GOLD), X0 + 10, Y0 + 7)]"),
    ("    TEXTS += [(f'KR_DL_Text{k}', '', st(12, WHITE), X0 + 36, y + 6), (f'KR_DL_Num{k}', '', st(13, SKY), X0 + 126, y + 5)]",
     "    TEXTS += [(f'KR_DL_Text{k}', '', st(13, WHITE), X0 + 36, y + 5), (f'KR_DL_Num{k}', '', st(14, SKY), X0 + 126, y + 4)]"),
])
edit(HERE / 'claude_deadline.jaf', [
    ('''        if (lane >= 2 && lane <= 8) KR_HVMove(act, "KR_DL_Text" + sk, 1160, y + 6);
        else KR_HVMove(act, "KR_DL_Text" + sk, 1134, y + 6);''',
     '''        if (lane >= 2 && lane <= 8) KR_HVMove(act, "KR_DL_Text" + sk, 1160, y + 5);
        else KR_HVMove(act, "KR_DL_Text" + sk, 1134, y + 5);'''),
    ('''            KR_HVMove(act, "KR_DL_Num" + sk, 1266 - w, y + 5);''', '''            KR_HVMove(act, "KR_DL_Num" + sk, 1266 - w, y + 4);'''),
])
print('ok')
