# -*- coding: utf-8 -*-
"""One-off edit (10-18): map probe_home -> probe_deadline in the publish generator as well."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'make_publish_deadline.py'
s = p.read_text('utf8')
a = "('home-copy.tmp', 'deadline-copy.tmp'), ('publish_home', 'publish_deadline')]:"
b = "('home-copy.tmp', 'deadline-copy.tmp'), ('publish_home', 'publish_deadline'), ('probe_home', 'probe_deadline')]:"
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
a2 = 'src = between(src, "def probe_home_ok(p):",'
b2 = 'src = between(src, "def probe_deadline_ok(p):",'
assert s.count(a2) == 1, s.count(a2)
s = s.replace(a2, b2)
p.write_text(s, 'utf8')
print('ok')
