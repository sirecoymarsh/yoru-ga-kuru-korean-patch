# -*- coding: utf-8 -*-
"""One-off fix (10-18): the apostrophe in the generator's contract text needs a double backslash."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'make_publish_list.py'
s = p.read_text('utf8')
a = r"""'user\'s save folder holds later saves"""
b = r"""'user\\'s save folder holds later saves"""
assert s.count(a) == 1, s.count(a)
s = s.replace(a, b)
p.write_text(s, 'utf8')
print('ok')
