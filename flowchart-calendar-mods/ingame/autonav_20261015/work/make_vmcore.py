# -*- coding: utf-8 -*-
"""Copy the r23 verifier's VM (class Stop .. end of class VM) into vmcore.py, pointed at this layer's anlib / work folder."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYER = HERE.parent
src = (LAYER.parent / 'r23_feeling' / 'verify_feeling_r23.py').read_text('utf8')
a = src.index('def proxy(s):')
b = src.index('# ============================================================== expectations (independent of the build script)')
body = src[a:b].rstrip() + '\n'
head = '''# -*- coding: utf-8 -*-
"""The VM of ingame/r23_feeling/verify_feeling_r23.py (Claude Opus 5.5, 2026-09-28), copied unchanged by work/make_vmcore.py
(10-15) so the auto-nav verifier can subclass it. The r15-r23 folders stay read only."""
import sys, json, re, struct, collections, math, copy, time, random, datetime, io, contextlib, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import anlib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
PREFIX = 'NightR'
R23_MOON = 2026092330


'''
(LAYER / 'vmcore.py').write_text(head + body, 'utf8')
print('vmcore.py', len((head + body).splitlines()), 'lines')
