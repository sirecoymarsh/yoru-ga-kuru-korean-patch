# -*- coding: utf-8 -*-
"""Replace control characters produced by shell escape collapse (BEL from a backslash-a) in a text file."""
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
n = s.count(chr(7))
s = s.replace(chr(7), chr(92) + 'a')
open(p, 'w', encoding='utf-8').write(s)
print('fixed', n)
