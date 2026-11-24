# -*- coding: utf-8 -*-
"""One-off edit (10-18): a main-story card is named just 「본편」 - the preview title adds its time (「본편 · 7/2 아침」)."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'claude_list.jaf'
s = p.read_text('utf8')
a = '''    string name = "？？？";
    if (!hidden) name = KR_B29Flat(KR_CCellName(i));
    KR_CText(KR_LVP(310), pane, 20.0, 150.0, 19, KR_CTint(KR_LVCut(name, 19, 400), KR_CGold()), 4);
    // 언제 · 조건 · 함께 · 상태 · 다시 보기 (labels and values as two texts with the same line spacing)
    string when = KR_B29Flat(KR_CCellWhen(i));
    if (when == "") when = "-";'''
b = '''    string when = KR_B29Flat(KR_CCellWhen(i));
    if (when == "") when = "-";
    string name = "？？？";
    if (!hidden) {
        name = KR_B29Flat(KR_CCellName(i));
        if (name.Find(" · ") < 0 && when != "-") name = name + " · " + when;
    }
    KR_CText(KR_LVP(310), pane, 20.0, 150.0, 19, KR_CTint(KR_LVCut(name, 19, 400), KR_CGold()), 4);
    // 언제 · 조건 · 함께 · 상태 · 다시 보기 (labels and values as two texts with the same line spacing)'''
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
p.write_text(s, 'utf8')
print('ok')
