# -*- coding: utf-8 -*-
"""Show a function from the original code dump with CALLMETHOD/PUSH function numbers resolved to names.
usage: python -X utf8 jamshow.py <name-substring-or-FUNC-number> [maxlines]
"""
import re, sys
import os
D = os.environ.get('JAMDUMP', r'P:\AI\yoru-autonav\dump')
names = {}
for l in open(D + r'\functions.txt', encoding='utf-8', errors='replace'):
    m = re.match(r'/\* 0x([0-9a-f]+) \*/\t(.*)', l)
    if m:
        n = int(m.group(1), 16)
        sig = m.group(2)
        mm = re.search(r'([^\s(]+)\(', sig)
        names[n] = mm.group(1) if mm else sig
code = open(D + r'\code.jam', encoding='utf-8', errors='replace').read().split('\n')
key = sys.argv[1]
maxl = int(sys.argv[2]) if len(sys.argv) > 2 else 400
# find header '; <name>' followed (soon) by FUNC n
starts = []
for i, l in enumerate(code):
    if l.startswith('FUNC '):
        num = int(l.split()[1])
        # header comment is the first ';' line block above
        j = i - 1
        while j > 0 and code[j - 1].startswith(';'):
            j -= 1
        hdr = code[j] if code[j].startswith(';') else ''
        if (key.isdigit() and num == int(key)) or (not key.isdigit() and key in hdr):
            starts.append((j, i, num, hdr))
for j, i, num, hdr in starts[:3]:
    print('=' * 20, hdr, 'FUNC', num)
    k = j
    out = 0
    while k < len(code) and out < maxl:
        l = code[k]
        if k > i and (l.startswith('FUNC ') or (l.startswith(';') and code[k+1:k+2] and code[k+1].startswith(';') and k > i + 2 and code[k-1].strip() == '')):
            break
        m = re.match(r'(\s*PUSH )(\d+)$', l)
        if m and int(m.group(2)) in names and int(m.group(2)) > 20000:
            l = l + '    ; ' + names[int(m.group(2))]
        print(l)
        k += 1
        out += 1
