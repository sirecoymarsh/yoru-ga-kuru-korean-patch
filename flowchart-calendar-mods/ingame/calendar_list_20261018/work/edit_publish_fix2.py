# -*- coding: utf-8 -*-
"""One-off fix (10-18): replace the whole two-line nm['next'] statement (up to the following write)."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'make_publish_list.py'
s = p.read_text('utf8')
a = """src = between(src, "        nm['next'] = (", "\\n", '''"""
b = """src = between(src, "        nm['next'] = (", "        write(mp, js(nm))", '''"""
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
a2 = """                      '합류 전 동료가 칩 · 줄 이름에 안 보이는지.')''')"""
b2 = """                      '합류 전 동료가 칩 · 줄 이름에 안 보이는지.')
''')"""
assert s.count(a2) == 1, s.count(a2)
s = s.replace(a2, b2)
p.write_text(s, 'utf8')
print('ok')
