# -*- coding: utf-8 -*-
"""Make dllib.py from calendar_title_20261018/ltlib.py (read only): the same helpers, the base moved to the title-layer install
(CALENDAR_TITLE_20261018_INSTALLED_NATIVE_PASS, 10-18 20:59), prefix KR_DL. Also snapshot_base.py (imports dllib)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
LT = HERE.parent / 'calendar_title_20261018'
src = (LT / 'ltlib.py').read_text('utf8')
pairs = [
    ("Title-calendar spoiler layer shared helpers", "Deadline-alert layer shared helpers"),
    ("a copy of calendar_list_20261018/lvlib.py", "a copy of calendar_title_20261018/ltlib.py"),
    ("with the base moved to the scene-list install (CALENDAR_LIST_20261018_INSTALLED_NATIVE_PASS, 10-18 20:23).",
     "with the base moved to the title-layer install (CALENDAR_TITLE_20261018_INSTALLED_NATIVE_PASS, 10-18 20:59)."),
    ("Everything this project writes stays under ingame/calendar_title_20261018/ on P:.",
     "Everything this project writes stays under ingame/calendar_deadline_20261018/ on P:."),
    ("# ...\ingame\calendar_title_20261018", "# ...\ingame\calendar_deadline_20261018"),
    ("BASE_AIN_SHA = 'fe4b6db8a7e59813f14901feda812d9ab4451f6c4493bfb1877b75a57bc4a855'   # scene-list install (10-18 20:23)",
     "BASE_AIN_SHA = '9be1a952441336b80be40cd5300addec04620a80da17885e47e3e4daf2553729'   # title-layer install (10-18 20:59)"),
    ("BASE_STATUS = 'CALENDAR_LIST_20261018_INSTALLED_NATIVE_PASS'", "BASE_STATUS = 'CALENDAR_TITLE_20261018_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = '1ccbab7f0557497968c29f0f56148bc1817817cbb4c5fc1bb01696eadbd45d39'",
     "BASE_MANIFEST_SHA = '01baac4304726283d25457b3d31cd59498e0981faf6bed6b3cb59d52e25abaab'"),
    ("PREFIX = 'KR_LT'", "PREFIX = 'KR_DL'"),
]
for a, b in pairs:
    assert src.count(a) == 1, (a[:70], src.count(a))
    src = src.replace(a, b)
(HERE / 'dllib.py').write_text(src, 'utf8')
snap = (LT / 'snapshot_base.py').read_text('utf8').replace('import ltlib as L', 'import dllib as L')
assert 'import dllib as L' in snap
(HERE / 'snapshot_base.py').write_text(snap, 'utf8')
print('ok')
