# -*- coding: utf-8 -*-
"""One-off edit (10-18): gate the cast, summary, replay and detail board on a scene the player has seen (home: this save)."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'claude_list.jaf'
s = p.read_text('utf8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep('''// Spoilers: the list has the board's rows only (본편, joined (home) / met (title) companions, 던전 동행). A row whose name or
// condition names a companion outside them shows ？？？ until it is read, and 「자세히」 stays off for it. The cast and the summary
// show for read scenes only (KR_P29Read, as the detail board).''',
'''// Spoilers: the list has the board's rows only (본편, joined (home) / met (title) companions, 던전 동행). The cast, the summary,
// 「다시 보기」 and 「자세히」 open only for a scene the player has seen: at home one seen in THIS save (the user's save folder
// holds 11월 saves from 09-26 while the play now is before 5/19 - 「지금은 마나미나 모모세는 스포일러야」), on the title (no
// save) one read in any save, everywhere with 전체 개방. A row whose name or condition names a companion outside the rows shows
// ？？？ (and no condition) until then.''')
rep('''int KR_LVCount(int month, int lane) {''',
'''// the scene's cast, summary, replay and detail board may show (see the head comment)
bool KR_LVReveal(int no, int ctx) {
    if (KR_CUnlockAll()) return true;
    if (ctx == 2) return N_ScenarioRegister::IsRegisteredEvent(KR_T9Fn(no));
    return KR_P29Read(no);
}
int KR_LVCount(int month, int lane) {''')
rep('''string KR_LVNote(int st) {
    if (st == 1) return "놓친 장면 · 줄거리는 본 뒤에";''',
'''string KR_LVNote(int st) {
    if (st == 2) return "이 세이브에서 보면 줄거리가 나옵니다";
    if (st == 1) return "놓친 장면 · 줄거리는 본 뒤에";''')
rep('''string KR_LVPlayText(int no) {
    if (KR_CCanPlay(no)) return "가능";
    if (KR_CNoPlay(no) != 0) return "불가 (게임 안에서만)";
    return "본 뒤에 가능";
}''',
'''string KR_LVPlayText(int no, bool reveal) {
    if (KR_CNoPlay(no) != 0) return "불가 (게임 안에서만)";
    if (reveal && KR_CCanPlay(no)) return "가능";
    return "본 뒤에 가능";
}''')
# the row
rep('''void KR_LVRow(int s, int i, int t, bool save, int nowTab, bool selected, int filter) {''',
    '''void KR_LVRow(int ctx, int s, int i, int t, bool save, int nowTab, bool selected, int filter) {''')
rep('''    int lane = KR_XVLaneNo(no);
    bool read = KR_P29Read(no);
    bool hidden = false;
    if (!read) hidden = KR_LVHidden(i);
    int st = KR_LVState(no, t, lane, save, nowTab);
    if (selected)''',
'''    int lane = KR_XVLaneNo(no);
    bool reveal = KR_LVReveal(no, ctx);
    bool hidden = false;
    if (!reveal) hidden = KR_LVHidden(i);
    int st = KR_LVState(no, t, lane, save, nowTab);
    if (selected)''')
rep('''    if (!read) {
        KR_CText(KR_LVP(base + 8), box, 470.0, 7.0, 15, KR_CTint(KR_LVNote(st), KR_LVDimC()), 2);''',
'''    if (!reveal) {
        KR_CText(KR_LVP(base + 8), box, 470.0, 7.0, 15, KR_CTint(KR_LVCut(KR_LVNote(st), 15, 300), KR_LVDimC()), 2);''')
# the preview
rep('''void KR_LVPreview(int i, int t, bool save, int nowTab) {''', '''void KR_LVPreview(int ctx, int i, int t, bool save, int nowTab) {''')
rep('''    int lane = KR_XVLaneNo(no);
    bool read = KR_P29Read(no);
    bool hidden = false;
    if (!read) hidden = KR_LVHidden(i);
    int st = KR_LVState(no, t, lane, save, nowTab);
    // the cast (read scenes only, as the detail board)
    string cast = "";
    if (read) {''',
'''    int lane = KR_XVLaneNo(no);
    bool reveal = KR_LVReveal(no, ctx);
    bool hidden = false;
    if (!reveal) hidden = KR_LVHidden(i);
    int st = KR_LVState(no, t, lane, save, nowTab);
    // the cast (scenes the player has seen only)
    string cast = "";
    if (reveal) {''')
rep('''KR_LVStateText(no, st, save) + "\\n" + KR_LVPlayText(no);''', '''KR_LVStateText(no, st, save) + "\\n" + KR_LVPlayText(no, reveal);''')
rep('''    string story = "";
    if (read) story = KR_W29Story(no);
    if (story == "") {
        if (read) KR_CText(KR_LVP(314), pane, 20.0, 0.0 + ty, 15, KR_CTint("줄거리가 없는 장면입니다", KR_CGray()), 4);
        else KR_CText(KR_LVP(314), pane, 20.0, 0.0 + ty, 15, KR_CTint("본 뒤에 나옵니다", KR_CGray()), 4);
    }''',
'''    string story = "";
    if (reveal) story = KR_W29Story(no);
    if (story == "") {
        string none = "본 뒤에 나옵니다";
        if (reveal) none = "줄거리가 없는 장면입니다";
        else if (ctx == 2 && KR_CGlobal(no) == 1) none = "다른 세이브에서 읽은 장면 · 이 세이브에서 보면 나옵니다";
        KR_CText(KR_LVP(314), pane, 20.0, 0.0 + ty, 15, KR_CTint(KR_LVWrap(none, 15, 392, 2), KR_CGray()), 4);
    }''')
rep('''    KR_LVButton(KR_LVP(316), pane, 20.0, 494.0, 194, 44, "다시 보기", 20, false, KR_CCanPlay(no));
    KR_LVButton(KR_LVP(318), pane, 226.0, 494.0, 194, 44, "자세히", 20, false, !hidden);''',
'''    KR_LVButton(KR_LVP(316), pane, 20.0, 494.0, 194, 44, "다시 보기", 20, false, reveal && KR_CCanPlay(no));
    KR_LVButton(KR_LVP(318), pane, 226.0, 494.0, 194, 44, "자세히", 20, false, reveal);''')
rep('''                KR_LVRow(s, i, t, save, nowTab, k2 == sel, lane);''', '''                KR_LVRow(ctx, s, i, t, save, nowTab, k2 == sel, lane);''')
rep('''        if (si != "") KR_LVPreview(si.ToInt(), st.ToInt(), save, nowTab);''', '''        if (si != "") KR_LVPreview(ctx, si.ToInt(), st.ToInt(), save, nowTab);''')
rep('''            if (r == KR_LVP(316)) {
                KR_CRequest(KR_CCellEv(i));
                continue;
            }
            if (r == KR_LVP(318)) {
                if (!KR_P29Read(KR_CCellEv(i)) && KR_LVHidden(i)) continue;
                KR_CClick(t, i);
                continue;
            }''',
'''            if (!KR_LVReveal(KR_CCellEv(i), ctx)) continue;
            if (r == KR_LVP(316)) {
                KR_CRequest(KR_CCellEv(i));
                continue;
            }
            if (r == KR_LVP(318)) {
                KR_CClick(t, i);
                continue;
            }''')
assert 'bool read' not in s and 'if (read)' not in s and 'if (!read)' not in s
p.write_text(s, 'utf8')
print('ok')
