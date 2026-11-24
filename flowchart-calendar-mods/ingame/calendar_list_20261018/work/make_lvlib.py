# -*- coding: utf-8 -*-
"""Make lvlib.py from calendar_overview_20261018/ovlib.py (read only): the same helpers, the base moved to the overview install
(CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS, 10-18 19:15), prefix KR_LV. Also snapshot_base.py (imports lvlib)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OV = HERE.parent / 'calendar_overview_20261018'
src = (OV / 'ovlib.py').read_text('utf8')
pairs = [
    ('"""Event-calendar overview (stage 2) shared helpers (Claude Opus 5.5, 2026-10-18) - a copy of calendar_redesign_20261017/hvlib.py\n'
     'with the base moved to the home-panel install (HOME_PANEL_20261017_INSTALLED_NATIVE_PASS, 10-18 18:21).\n\n'
     'Everything this project writes stays under ingame/calendar_overview_20261018/ on P:.',
     '"""Event-calendar list (stage 3) shared helpers (Claude Opus 5.5, 2026-10-18) - a copy of calendar_overview_20261018/ovlib.py\n'
     'with the base moved to the overview install (CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS, 10-18 19:15).\n\n'
     'Everything this project writes stays under ingame/calendar_list_20261018/ on P:.'),
    ("HERE = Path(__file__).resolve().parent                     # ...\ingame\calendar_overview_20261018",
     "HERE = Path(__file__).resolve().parent                     # ...\ingame\calendar_list_20261018"),
    ("BASE_AIN_SHA = '99461f9c4d023e6869f2719695923c5ed057d4b67631687268f0a9b4be06b4cc'   # home-panel install (10-18 18:21)",
     "BASE_AIN_SHA = 'b5a6ceb09e18ef3a5e08e000a511275ff091325ea0967418964a2076a913b959'   # overview install (10-18 19:15)"),
    ("BASE_STATUS = 'HOME_PANEL_20261017_INSTALLED_NATIVE_PASS'", "BASE_STATUS = 'CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = 'a10aa3a5d90b211c4d25702456483139b7999dbd84d92f47b55f3c9c7b16cae2'",
     "BASE_MANIFEST_SHA = '6ec9691303a83d064bc6849c7ae3a3b631b6695ddff7280be4dbf918308290a5'"),
    ("PREFIX = 'KR_XV'", "PREFIX = 'KR_LV'"),
]
for a, b in pairs:
    assert src.count(a) == 1, a[:70]
    src = src.replace(a, b)
(HERE / 'lvlib.py').write_text(src, 'utf8')
snap = (OV / 'snapshot_base.py').read_text('utf8').replace('import ovlib as L', 'import lvlib as L')
assert 'import lvlib as L' in snap
(HERE / 'snapshot_base.py').write_text(snap, 'utf8')
print('ok')
