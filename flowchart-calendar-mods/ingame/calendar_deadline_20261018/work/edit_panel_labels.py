# -*- coding: utf-8 -*-
"""One-off edit (10-18): 「호시카와 특훈 뒤」 ran into its count 「10」 on the panel (PACT text with an outline draws wider than
the estimate) - a monthly row is the companion's name and 「N개」, as the mockup's rows."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'claude_deadline.jaf'
s = p.read_text('utf8')
a = '''            KR_DLRowSet(act, row, p, KR_XVName(p) + " 특훈 뒤", "%d" % c, numTint);'''
b = '''            KR_DLRowSet(act, row, p, KR_XVName(p), ("%d" % c) + "개", numTint);'''
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
a = '''//     deadline - a header 「4/30까지 · 4일 남음」 (orange within 7 days), a row per companion for the monthly talks (count), a'''
b = '''//     deadline - a header 「4/30까지 · 4일 남음」 (orange within 7 days), a row per companion for the monthly talks (「N개」), a'''
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
p.write_text(s, 'utf8')
print('ok')
