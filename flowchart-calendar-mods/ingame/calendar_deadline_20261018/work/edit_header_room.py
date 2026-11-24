# -*- coding: utf-8 -*-
"""One-off edit (10-18): the first probe drew a deadline header in the last free row with no item under it (「6/30까지」 then
「외 2개」) - a header goes in only when at least one item row fits after it."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'claude_deadline.jaf'
s = p.read_text('utf8')
a = '''    while (k < n && row < 7) {
        int due = KR_DLNum("ou%d" % k);'''
b = '''    while (k < n && row < 6) {
        int due = KR_DLNum("ou%d" % k);'''
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
a = '''    // seven content rows; the eighth says how many more the list holds'''
b = '''    // seven content rows (a header only when an item fits under it); the eighth says how many more the list holds'''
assert s.count(a) == 1
s = s.replace(a, b)
p.write_text(s, 'utf8')
print('ok')
