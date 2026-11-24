# -*- coding: utf-8 -*-
"""Make ltlib.py from calendar_list_20261018/lvlib.py (read only): the same helpers, the base moved to the scene-list install
(CALENDAR_LIST_20261018_INSTALLED_NATIVE_PASS, 10-18 20:23), prefix KR_LT. Also snapshot_base.py (imports ltlib)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
LV = HERE.parent / 'calendar_list_20261018'
src = (LV / 'lvlib.py').read_text('utf8')
head = src[:src.index('\nimport ') if '\nimport ' in src else 0]
pairs = [
    ("Event-calendar list (stage 3) shared helpers", "Title-calendar spoiler layer shared helpers"),
    ("a copy of calendar_overview_20261018/ovlib.py", "a copy of calendar_list_20261018/lvlib.py"),
    ("with the base moved to the overview install (CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS, 10-18 19:15).",
     "with the base moved to the scene-list install (CALENDAR_LIST_20261018_INSTALLED_NATIVE_PASS, 10-18 20:23)."),
    ("Everything this project writes stays under ingame/calendar_list_20261018/ on P:.",
     "Everything this project writes stays under ingame/calendar_title_20261018/ on P:."),
    ("# ...\ingame\calendar_list_20261018", "# ...\ingame\calendar_title_20261018"),
    ("BASE_AIN_SHA = 'b5a6ceb09e18ef3a5e08e000a511275ff091325ea0967418964a2076a913b959'   # overview install (10-18 19:15)",
     "BASE_AIN_SHA = 'fe4b6db8a7e59813f14901feda812d9ab4451f6c4493bfb1877b75a57bc4a855'   # scene-list install (10-18 20:23)"),
    ("BASE_STATUS = 'CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS'", "BASE_STATUS = 'CALENDAR_LIST_20261018_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = '6ec9691303a83d064bc6849c7ae3a3b631b6695ddff7280be4dbf918308290a5'",
     "BASE_MANIFEST_SHA = '1ccbab7f0557497968c29f0f56148bc1817817cbb4c5fc1bb01696eadbd45d39'"),
    ("PREFIX = 'KR_LV'", "PREFIX = 'KR_LT'"),
]
for a, b in pairs:
    assert src.count(a) == 1, (a[:70], src.count(a))
    src = src.replace(a, b)
(HERE / 'ltlib.py').write_text(src, 'utf8')
snap = (LV / 'snapshot_base.py').read_text('utf8').replace('import lvlib as L', 'import ltlib as L')
assert 'import ltlib as L' in snap
(HERE / 'snapshot_base.py').write_text(snap, 'utf8')
print('ok')
