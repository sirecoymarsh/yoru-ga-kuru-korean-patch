# -*- coding: utf-8 -*-
"""Make hvlib.py from battle_pace_20261016/bplib.py (read only): the same helpers, the base moved to the battle-pace install
(BATTLE_PACE_20261016_INSTALLED_NATIVE_PASS, 10-16 10:18), prefix KR_HV. Also snapshot_base.py (imports hvlib)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BP = HERE.parent / 'battle_pace_20261016'
src = (BP / 'bplib.py').read_text('utf8')
pairs = [
    ('"""Battle-pace layer shared helpers (Claude Opus 5.5, 2026-10-16) - a copy of mods_tab_20261015/mdlib.py with the base moved\n'
     'to the Mods-tab install (MODS_TAB_20261015_INSTALLED_NATIVE_PASS, 10-16 00:21).\n\n'
     'Everything this project writes stays under ingame/battle_pace_20261016/ on P:.',
     '"""Calendar / completion-rate redesign shared helpers (Claude Opus 5.5, 2026-10-17) - a copy of battle_pace_20261016/bplib.py\n'
     'with the base moved to the battle-pace install (BATTLE_PACE_20261016_INSTALLED_NATIVE_PASS, 10-16 10:18).\n\n'
     'Everything this project writes stays under ingame/calendar_redesign_20261017/ on P:.'),
    ("HERE = Path(__file__).resolve().parent                     # ...\\ingame\\battle_pace_20261016",
     "HERE = Path(__file__).resolve().parent                     # ...\\ingame\\calendar_redesign_20261017"),
    ("BASE_AIN_SHA = '4ed365048d3f91bbbdf4a994dbfce827da37a06620c96737485c9bd2ba6d2573'   # Mods-tab install (10-16 00:21)",
     "BASE_AIN_SHA = 'd542fa37d53c5ea16fa014575572e4be64cc850d2c2af348948b09d1261a051c'   # battle-pace install (10-16 10:18)"),
    ("BASE_STATUS = 'MODS_TAB_20261015_INSTALLED_NATIVE_PASS'", "BASE_STATUS = 'BATTLE_PACE_20261016_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = '85982cd74e70feaf4f66b3490567e984e12e154e2d2b5ac6b83d46703076aa10'",
     "BASE_MANIFEST_SHA = '0cfa5e0799c1f42a781680bee99a96b48b4d2caacb43177835c742fcfda4469d'"),
    ("PREFIX = 'KR_BP'", "PREFIX = 'KR_HV'"),
]
for a, b in pairs:
    assert src.count(a) == 1, a[:70]
    src = src.replace(a, b)
(HERE / 'hvlib.py').write_text(src, 'utf8')
snap = (BP / 'snapshot_base.py').read_text('utf8').replace('import bplib as L', 'import hvlib as L')
assert 'import hvlib as L' in snap
(HERE / 'snapshot_base.py').write_text(snap, 'utf8')
print('ok')
