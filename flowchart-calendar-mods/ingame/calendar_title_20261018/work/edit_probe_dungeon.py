# -*- coding: utf-8 -*-
"""One-off edit (10-18): 7월 has no 던전 동행 rows, so the title masking check was empty - check the 던전 동행 list of every month
(the board's 던전 동행 name) instead: 7월 list -> 닫기 -> board -> 던전 동행 name -> list -> 닫기 -> board -> 회상 -> END."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'make_probe.py'
s = p.read_text('utf8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep('''        if (f == 32) {
            string cs = KR_LVGet("chips");
            int nc = cs.ToInt();
            int k = -1;
            for (int c = 0; c < nc; c++) {
                if (KR_LVGet("chip%d" % c) == "9") k = c;
            }
            KR_PRGo("t_d", KR_LVP(30 + k * 2));
        }
        return;
    }''', '''        if (f == 32) KR_PRGo("t_b2", KR_LVP(7));
        return;
    }''')
rep('''    if (stage == "t_d") {
        if (f == 30) {
            int n = KR_PRExpect(3, 9);''', '''    if (stage == "t_d") {
        if (f == 30) {
            int n = KR_PRExpect(-1, 9);''')
rep('''                int i = KR_PRNth(3, 9, k);''', '''                int i = KR_PRNth(-1, 9, k);''')
rep('''            KR_PRLog("TITLE DUNGEON 7월 n=" + ("%d" % n) + " naming later companions=" + ("%d" % named));
            KR_PRCheck("title: 던전 동행 rows naming later companions show ？？？ (none drawn by name)", KR_PRHead(3, 9) && same && clean);''',
    '''            KR_PRLog("TITLE DUNGEON n=" + ("%d" % n) + " naming later companions=" + ("%d" % named));
            KR_PRCheck("title: 던전 동행 rows naming later companions show ？？？ (none drawn by name)", KR_PRHead(-1, 9) && named > 0 && same && clean);''')
rep('''        if (f == 32) KR_PRGo("t_b2", KR_LVP(7));
        return;
    }
    if (stage == "t_b2") {
        if (f == 30) KR_PRCheck("title: 닫기 returns to the board", KR_PRBoard());
        if (f == 32) KR_PRGo("t_b3", KR_XVP(520));
        return;
    }''', '''        if (f == 32) KR_PRGo("t_b4", KR_LVP(7));
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
    }''')
p.write_text(s, 'utf8')
print('ok')
