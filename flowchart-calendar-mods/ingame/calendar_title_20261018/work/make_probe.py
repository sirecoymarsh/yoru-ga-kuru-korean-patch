# -*- coding: utf-8 -*-
"""Make probe_title.py from calendar_list_20261018/probe_list.py (read only): the same launcher and home tours, a new title tour
(rows of the companions present from the start, every row / the preview closed, 달 화면으로 and 회상 open nothing, 던전 동행 rows
naming later companions masked), and on the home tour a 달 화면으로 round trip and a check that 회상 · 그 밖 stay open."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'calendar_list_20261018' / 'probe_list.py').read_text('utf8')


def rep(a, b):
    global src
    assert src.count(a) == 1, (a[:90], src.count(a))
    src = src.replace(a, b)


rep('"""Claude Opus 5.5 (2026-10-18): isolated, muted native probe of the event-calendar scene list (stage 3).',
    '"""Claude Opus 5.5 (2026-10-18): isolated, muted native probe of the title-calendar spoiler layer (KR_LT*) - copy of probe_list.py.\n'
    'Title tour: board rows = 본편 + the companions present from the start + 던전 동행, 회상 · 그 밖 covered; 7월 list closed (rows,\n'
    'preview, 달 화면으로), 달 화면으로 / 회상 open nothing, 던전 동행 rows naming later companions masked. Home tours as probe_list.py,\n'
    'plus a 달 화면으로 round trip at home and 회상 · 그 밖 not covered at home.')
rep('import lvlib as L', 'import ltlib as L')
rep("BOOT = 'NightRemasterListProbe'", "BOOT = 'NightRemasterTitleProbe'")
src = src.replace('lv_', 'lt_')        # shots
assert 'lt_list' in src
# result files and save folder
rep("savename = f'SaveData_ListProbe_{stamp}'", "savename = f'SaveData_TitleProbe_{stamp}'")
src = src.replace("probe_list_{stamp}.json", "probe_title_{stamp}.json").replace("'probe_list.json'", "'probe_title.json'")
src = src.replace("f'probe_list_{HOME_SAVE[:-4]}.json'", "f'probe_title_{HOME_SAVE[:-4]}.json'").replace("f'probe_list_{HOME_SAVE}.json'", "f'probe_title_{HOME_SAVE}.json'")

# ---- home tour: 회상 · 그 밖 not covered at home; a 달 화면으로 round trip before 닫기
rep('''            KR_PRCheck("the board's hint names the list", KR_PRHas(KR_XVP(530), "장면 목록"));''',
    '''            KR_PRCheck("the board's hint names the list", KR_PRHas(KR_XVP(530), "장면 목록"));
            KR_PRCheck("home: 회상 · 그 밖 are not covered", !PartsEngine.IsExist(KR_XVP(528)) && !PartsEngine.IsExist(KR_XVP(529)));''')
rep('''            KR_PRCheck("a row name opens that row in every month", KR_PRList() && KR_PRHead(-1, lane) && KR_PRFoot(KR_PRExpect(-1, lane)));
            KR_PRShot("lt_list_byname.bmp");
        }
        if (f == 32) KR_PRGo("b3", KR_LVP(7));
        return;
    }''',
    '''            KR_PRCheck("a row name opens that row in every month", KR_PRList() && KR_PRHead(-1, lane) && KR_PRFoot(KR_PRExpect(-1, lane)));
            KR_PRCheck("home: 달 화면으로 is on", KR_PRHas(KR_LVP(55), KR_CWhite()));
            KR_PRShot("lt_list_byname.bmp");
        }
        if (f == 32) KR_PRGo("lm", KR_LVP(54));
        return;
    }
    if (stage == "lm") {
        if (f == 30) {
            KR_PRLog("MONTH head=" + KR_PRTxt(KR_CPart(1)));
            KR_PRCheck("home: 달 화면으로 opens the month view (list parts released)",
                       KR_CGet("Open") == "1" && KR_LVGet("Open") != "1" && PartsEngine.IsExist(KR_CPart(1)) && !PartsEngine.IsExist(KR_LVP(1)));
            KR_PRShot("lt_home_month.bmp");
        }
        if (f == 32) KR_PRGo("l11", 0);
        return;
    }
    if (stage == "l11") {
        if (f == 30) KR_PRCheck("home: closing the month view returns to the list (same filter)", KR_PRList() && KR_PRHead(-1, KR_PRNum("L10")));
        if (f == 32) KR_PRGo("b3", KR_LVP(7));
        return;
    }''')

# ---- the title tour
a = src[src.index('bool KR_PRRowsMetOK() {'):src.index('void KR_ProbeChartTick() {')]
b = r'''bool KR_PRRowsStartOK() {
    string rs = KR_XVGet("rows");
    int n = rs.ToInt();
    if (KR_XVGet("row0") != "0") return false;
    if (KR_XVGet("row%d" % (n - 1)) != "9") return false;
    int k = 1;
    for (int p = 2; p <= 8; p++) {
        if (KR_T20JoinDay(p) > 0) continue;
        string v = KR_XVGet("row%d" % k);
        if (v.ToInt() != p) return false;
        k++;
    }
    return k == n - 1;
}
int KR_PRStartCount() {
    int n = 0;
    for (int p = 2; p <= 8; p++) {
        if (KR_T20JoinDay(p) <= 0) n++;
    }
    return n;
}
// every drawn row closed: no faces, the title note
bool KR_PRRowsClosed() {
    for (int s = 0; s < 14; s++) {
        if (!PartsEngine.IsExist(KR_LVP(100 + s * 10))) continue;
        if (PartsEngine.IsExist(KR_LVP(100 + s * 10 + 4))) return false;
        if (!KR_PRHas(KR_LVP(100 + s * 10 + 8), "타이틀에서는")) return false;
    }
    return true;
}
// the cell names a companion who is not there from the start
bool KR_PRNamesLater(int i) {
    string t = KR_CCellName(i) + " " + KR_CCellCond(i);
    for (int p = 2; p <= 8; p++) {
        if (KR_T20JoinDay(p) <= 0) continue;
        if (t.Find(KR_XVName(p)) >= 0) return true;
    }
    return false;
}
void KR_ProbeTitle(string stage, int f) {
    if (stage == "t_b") {
        if (f == 30) {
            KR_PRLog("ROWS " + KR_PRRows() + " start=" + ("%d" % KR_PRStartCount()));
            KR_PRCheck("title: board rows = 본편, the companions present from the start, 던전 동행", KR_PRBoard() && !PartsEngine.IsExist(KR_XVP(3)) && KR_PRRowsStartOK());
            KR_PRCheck("title: 회상 · 그 밖 covered and the hint says why", PartsEngine.IsExist(KR_XVP(528)) && PartsEngine.IsExist(KR_XVP(529)) && KR_PRHas(KR_XVP(531), "타이틀에서는"));
            KR_PRShot("lt_title_board.bmp");
        }
        if (f == 32) KR_PRGo("t_l", KR_XVP(23));
        return;
    }
    if (stage == "t_l") {
        if (f == 30) {
            int n = KR_PRExpect(3, -1);
            KR_PRLog("TITLE LIST n=" + ("%d" % n) + " chips=" + KR_LVGet("chips") + " foot=" + KR_PRTxt(KR_LVP(71)) + " note=" + KR_PRTxt(KR_LVP(108)));
            KR_PRCheck("title: the 7월 list with chips 전체 · 본편 · start companions · 던전 동행",
                       KR_PRList() && KR_PRHead(3, -1) && KR_PRFoot(n) && KR_LVGet("chips") == ("%d" % (3 + KR_PRStartCount())));
            KR_PRCheck("title: every row closed (no faces, the title note)", KR_PRRowsClosed());
            KR_PRCheck("title: the preview closed (no faces, title notes, 다시 보기 · 자세히 off)",
                       !PartsEngine.IsExist(KR_LVP(301)) && KR_PRHas(KR_LVP(309), "타이틀에서는") && KR_PRHas(KR_LVP(314), "타이틀에서는")
                       && KR_PRHas(KR_LVP(317), KR_LVDimC()) && KR_PRHas(KR_LVP(319), KR_LVDimC()));
            KR_PRCheck("title: 달 화면으로 drawn off", KR_PRHas(KR_LVP(55), KR_LVDimC()));
            KR_PRShot("lt_title_list.bmp");
        }
        if (f == 32) KR_PRGo("t_l2", KR_LVP(54));
        return;
    }
    if (stage == "t_l2") {
        if (f == 30) KR_PRCheck("title: 달 화면으로 opens nothing (the list stays)", KR_PRList() && KR_PRHead(3, -1) && !PartsEngine.IsExist(KR_CPart(1)));
        if (f == 32) KR_PRGo("t_b2", KR_LVP(7));
        return;
    }
    if (stage == "t_d") {
        if (f == 30) {
            int n = KR_PRExpect(-1, 9);
            bool same = true;
            int named = 0;
            for (int k = 0; k < n; k++) {
                int i = KR_PRNth(-1, 9, k);
                bool nm = KR_PRNamesLater(i);
                if (nm != KR_LVHidden(i)) same = false;
                if (nm) named++;
            }
            bool clean = true;
            for (int r = 0; r < 14; r++) {
                string t = KR_PRTxt(KR_LVP(100 + r * 10 + 3));
                for (int p = 2; p <= 8; p++) {
                    if (KR_T20JoinDay(p) > 0 && t.Find(KR_XVName(p)) >= 0) clean = false;
                }
            }
            KR_PRLog("TITLE DUNGEON n=" + ("%d" % n) + " naming later companions=" + ("%d" % named));
            KR_PRCheck("title: 던전 동행 rows naming later companions show ？？？ (none drawn by name)", KR_PRHead(-1, 9) && named > 0 && same && clean);
            KR_PRShot("lt_title_dungeon.bmp");
        }
        if (f == 32) KR_PRGo("t_b4", KR_LVP(7));
        return;
    }
    if (stage == "t_b2") {
        if (f == 30) KR_PRCheck("title: 닫기 returns to the board", KR_PRBoard());
        if (f == 32) KR_PRGo("t_d", KR_XVP(100 + KR_PRBoardRow(9) * 40 + 35));
        return;
    }
    if (stage == "t_b4") {
        if (f == 30) KR_PRCheck("title: 닫기 on the 던전 동행 list returns to the board", KR_PRBoard());
        if (f == 32) KR_PRGo("t_b3", KR_XVP(520));
        return;
    }
    if (stage == "t_b3") {
        if (f == 30) {
            KR_PRCheck("title: 회상 opens nothing (the board stays)", KR_PRBoard() && !PartsEngine.IsExist(KR_CPart(1)) && KR_XVGet("Jump") == "");
            KR_PRShot("lt_title_board_back.bmp");
            KR_PREndAll();
        }
        return;
    }
    KR_PRLog("CHART TICK in stage " + stage);
    KR_PRShot("lt_unexpected.bmp");
    system.Exit(6);
}
'''
src = src.replace(a, b)
(HERE / 'probe_title.py').write_text(src, 'utf8')
print('ok', len(src.splitlines()))
