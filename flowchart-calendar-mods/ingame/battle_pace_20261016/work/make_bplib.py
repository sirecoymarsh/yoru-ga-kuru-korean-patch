# -*- coding: utf-8 -*-
"""Make bplib.py from mods_tab_20261015/mdlib.py (read only): the same helpers, the base moved to the Mods-tab install
(MODS_TAB_20261015_INSTALLED_NATIVE_PASS, 10-16 00:21), prefix KR_BP. Also snapshot_base.py (imports bplib)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MT = HERE.parent / 'mods_tab_20261015'
src = (MT / 'mdlib.py').read_text('utf8')
pairs = [
    ('"""Mods page layer shared helpers (Claude Opus 5.5, 2026-10-15) - a copy of autonav_20261015/anlib.py (itself a copy of\n'
     'r23lib.py) with the base moved to the auto-nav install (AUTONAV_20261015_INSTALLED_NATIVE_PASS, 10-15 22:31).\n\n'
     'Everything this project writes stays under ingame/mods_tab_20261015/ on P:.',
     '"""Battle-pace layer shared helpers (Claude Opus 5.5, 2026-10-16) - a copy of mods_tab_20261015/mdlib.py with the base moved\n'
     'to the Mods-tab install (MODS_TAB_20261015_INSTALLED_NATIVE_PASS, 10-16 00:21).\n\n'
     'Everything this project writes stays under ingame/battle_pace_20261016/ on P:.'),
    ("HERE = Path(__file__).resolve().parent                     # ...\\ingame\\mods_tab_20261015",
     "HERE = Path(__file__).resolve().parent                     # ...\\ingame\\battle_pace_20261016"),
    ("BASE_AIN_SHA = '1e96d3e797184a7a13236208988fe6ca3d37cf55f9e553f0ccc5ad7ed7659188'   # auto-nav install (10-15 22:31)",
     "BASE_AIN_SHA = '4ed365048d3f91bbbdf4a994dbfce827da37a06620c96737485c9bd2ba6d2573'   # Mods-tab install (10-16 00:21)"),
    ("BASE_PACT_SHA = '9f8c63b9276b00b71904ecd34b7062a9f1fec091ebe5cfaa0bc7ada1c16072ce'",
     "BASE_PACT_SHA = 'f1a99eb3a37d6dd8a07c7ce1b1e1d2800974a773947447ef89d3e7e1714bdfac'"),
    ("BASE_STATUS = 'AUTONAV_20261015_INSTALLED_NATIVE_PASS'", "BASE_STATUS = 'MODS_TAB_20261015_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = '3d3e54691e98ca7bcf261f1469e703aa7a744cadfb2609dadd820ac4fbe00ed4'",
     "BASE_MANIFEST_SHA = '85982cd74e70feaf4f66b3490567e984e12e154e2d2b5ac6b83d46703076aa10'"),
    ("PREFIX = 'KR_MD'", "PREFIX = 'KR_BP'"),
]
for a, b in pairs:
    assert src.count(a) == 1, a[:70]
    src = src.replace(a, b)
(HERE / 'bplib.py').write_text(src, 'utf8')
snap = (MT / 'snapshot_base.py').read_text('utf8').replace('import mdlib as L', 'import bplib as L')
assert 'import bplib as L' in snap
# the Mods-tab layer put CP949 message-box strings into STR0: alice's -c dump cannot convert them (iconv), and the build only
# needs -j and --raw-code, so the structured dump is skipped here
line = "    L.cmd('ain', 'dump', '-c', '-o', own / 'code.jam', dst, timeout=900)\n"
assert snap.count(line) == 1
snap = snap.replace(line, '')
(HERE / 'snapshot_base.py').write_text(snap, 'utf8')
print('ok')
