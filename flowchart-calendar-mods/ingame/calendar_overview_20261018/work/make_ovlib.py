# -*- coding: utf-8 -*-
"""Make ovlib.py from calendar_redesign_20261017/hvlib.py (read only): the same helpers, the base moved to the home-panel install
(HOME_PANEL_20261017_INSTALLED_NATIVE_PASS, 10-18 18:21), prefix KR_XV. Also snapshot_base.py (imports ovlib)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
HV = HERE.parent / 'calendar_redesign_20261017'
src = (HV / 'hvlib.py').read_text('utf8')
pairs = [
    ('"""Calendar / completion-rate redesign shared helpers (Claude Opus 5.5, 2026-10-17) - a copy of battle_pace_20261016/bplib.py\n'
     'with the base moved to the battle-pace install (BATTLE_PACE_20261016_INSTALLED_NATIVE_PASS, 10-16 10:18).\n\n'
     'Everything this project writes stays under ingame/calendar_redesign_20261017/ on P:.',
     '"""Event-calendar overview (stage 2) shared helpers (Claude Opus 5.5, 2026-10-18) - a copy of calendar_redesign_20261017/hvlib.py\n'
     'with the base moved to the home-panel install (HOME_PANEL_20261017_INSTALLED_NATIVE_PASS, 10-18 18:21).\n\n'
     'Everything this project writes stays under ingame/calendar_overview_20261018/ on P:.'),
    ("HERE = Path(__file__).resolve().parent                     # ...\ingame\calendar_redesign_20261017",
     "HERE = Path(__file__).resolve().parent                     # ...\ingame\calendar_overview_20261018"),
    ("BASE_AIN_SHA = 'd542fa37d53c5ea16fa014575572e4be64cc850d2c2af348948b09d1261a051c'   # battle-pace install (10-16 10:18)",
     "BASE_AIN_SHA = '99461f9c4d023e6869f2719695923c5ed057d4b67631687268f0a9b4be06b4cc'   # home-panel install (10-18 18:21)"),
    ("BASE_PACT_SHA = 'f1a99eb3a37d6dd8a07c7ce1b1e1d2800974a773947447ef89d3e7e1714bdfac'",
     "BASE_PACT_SHA = '580cea9908a389a86c837eb9bd7d15f16765ef925826c0a086601da2e6b65109'"),
    ("BASE_STATUS = 'BATTLE_PACE_20261016_INSTALLED_NATIVE_PASS'", "BASE_STATUS = 'HOME_PANEL_20261017_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = '0cfa5e0799c1f42a781680bee99a96b48b4d2caacb43177835c742fcfda4469d'",
     "BASE_MANIFEST_SHA = 'a10aa3a5d90b211c4d25702456483139b7999dbd84d92f47b55f3c9c7b16cae2'"),
    ("PREFIX = 'KR_HV'", "PREFIX = 'KR_XV'"),
]
for a, b in pairs:
    assert src.count(a) == 1, a[:70]
    src = src.replace(a, b)
(HERE / 'ovlib.py').write_text(src, 'utf8')
snap = (HV / 'snapshot_base.py').read_text('utf8').replace('import hvlib as L', 'import ovlib as L')
assert 'import ovlib as L' in snap
(HERE / 'snapshot_base.py').write_text(snap, 'utf8')
print('ok')
