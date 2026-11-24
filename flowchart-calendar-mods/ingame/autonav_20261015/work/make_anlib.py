# -*- coding: utf-8 -*-
"""Assemble anlib.py = our header + the generic helper section of r23lib.py + our base_paths()."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYER = HERE.parent
src = (LAYER.parent / 'r23_feeling' / 'r23lib.py').read_text('utf8')
a = src.index('# --- review_claude_handoff_20260923.sha / readj ---')
b = src.index('SAVECOPY = WORK')
body = src[a:b].rstrip() + '\n'
head = (HERE / 'anlib_head.py').read_text('utf8')
tail = '''

def base_paths():
    """The base AIN snapshot (work/base: AIN copy + meta.json + raw code dump), made by snapshot_base.py."""
    own = WORK / 'base'
    ain, meta, raw = own / 'NightRemaster.ain', own / 'meta.json', own / 'raw_code.jam'
    if ain.exists() and meta.exists() and raw.exists() and sha(ain) == BASE_AIN_SHA:
        return dict(ain=ain, meta=meta, raw=raw)
    raise AssertionError('no base snapshot with BASE_AIN_SHA: run snapshot_base.py')
'''
(LAYER / 'anlib.py').write_text(head + body + tail, 'utf8')
print('anlib.py', len((head + body + tail).splitlines()), 'lines')
