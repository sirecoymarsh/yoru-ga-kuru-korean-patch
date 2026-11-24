# -*- coding: utf-8 -*-
"""One-off edit (10-18): cell names / times can hold a line break (the 7월 dungeon stage names on the title probe ran onto a
second line under their row) - flatten them with the summary board's own KR_B29Flat before cutting to one line."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'claude_list.jaf'
s = p.read_text('utf8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep('''string KR_LVLabel(int i, int lane, int filter) {
    string name = KR_CCellName(i);''', '''string KR_LVLabel(int i, int lane, int filter) {
    string name = KR_B29Flat(KR_CCellName(i));''')
rep('''    string when = KR_CCellWhen(i);
    KR_CText(KR_LVP(base + 2), box, 38.0, 7.0, 15, KR_CTint(KR_LVCut(when, 15, 84), tint), 2);''',
    '''    string when = KR_B29Flat(KR_CCellWhen(i));
    KR_CText(KR_LVP(base + 2), box, 38.0, 7.0, 15, KR_CTint(KR_LVCut(when, 15, 84), tint), 2);''')
rep('''    if (!hidden) name = KR_CCellName(i);
    KR_CText(KR_LVP(310), pane, 20.0, 150.0, 19, KR_CTint(KR_LVCut(name, 19, 400), KR_CGold()), 4);''',
    '''    if (!hidden) name = KR_B29Flat(KR_CCellName(i));
    KR_CText(KR_LVP(310), pane, 20.0, 150.0, 19, KR_CTint(KR_LVCut(name, 19, 400), KR_CGold()), 4);''')
rep('''    string when = KR_CCellWhen(i);
    if (when == "") when = "-";''', '''    string when = KR_B29Flat(KR_CCellWhen(i));
    if (when == "") when = "-";''')
p.write_text(s, 'utf8')
print('ok')
