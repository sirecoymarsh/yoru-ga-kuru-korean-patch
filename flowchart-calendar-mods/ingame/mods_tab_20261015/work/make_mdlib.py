# -*- coding: utf-8 -*-
"""Make mdlib.py from the auto-nav anlib.py: same helpers, base moved to the auto-nav install (10-15 22:31)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'autonav_20261015' / 'anlib.py').read_text('utf8')
EVENTS = [58, 63, 69, 104, 258, 260, 322, 611, 10021, 20041, 20081, 20164, 30001, 30021, 30152, 40021, 40041, 40043, 40061]
pairs = [
    ('"""Auto-nav layer shared helpers (Claude Opus 5.5, 2026-10-15) - a copy of r23_feeling/r23lib.py (the r15-r23 folders are\n'
     'evidence: read only) with the base moved to the runtime current.json points at on 10-15 (claude_text_20261001 install).\n\n'
     'Everything this project writes stays under ingame/autonav_20261015/ on P:.',
     '"""Mods page layer shared helpers (Claude Opus 5.5, 2026-10-15) - a copy of autonav_20261015/anlib.py (itself a copy of\n'
     'r23lib.py) with the base moved to the auto-nav install (AUTONAV_20261015_INSTALLED_NATIVE_PASS, 10-15 22:31).\n\n'
     'Everything this project writes stays under ingame/mods_tab_20261015/ on P:.'),
    ("HERE = Path(__file__).resolve().parent                     # ...\\ingame\\autonav_20261015",
     "HERE = Path(__file__).resolve().parent                     # ...\\ingame\\mods_tab_20261015"),
    ("BASE_AIN_SHA = '3afdd2b1e11a107defa4b91465f97241e7ddc70fb681f0561e8b67fd897aa8f9'   # claude_text_20261001 install (10-01 15:06)",
     "BASE_AIN_SHA = '1e96d3e797184a7a13236208988fe6ca3d37cf55f9e553f0ccc5ad7ed7659188'   # auto-nav install (10-15 22:31)"),
    ("BASE_PACT_SHA = 'd4de68c5d44ff5c80b9c41be21f86059d0ebca2717284f4ed8a7d43f6f029403'",
     "BASE_PACT_SHA = '9f8c63b9276b00b71904ecd34b7062a9f1fec091ebe5cfaa0bc7ada1c16072ce'"),
    ("BASE_STATUS = 'CLAUDE_TEXT_20261001_INSTALLED_VM_PASS'", "BASE_STATUS = 'AUTONAV_20261015_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = 'fcfb8a49c6910889c2f49f50ed796210c2a04211f6e194d0ad992cd796ecd1ea'",
     "BASE_MANIFEST_SHA = '3d3e54691e98ca7bcf261f1469e703aa7a744cadfb2609dadd820ac4fbe00ed4'"),
    ("PREFIX = 'KR_AN'", "PREFIX = 'KR_MD'"),
    ("PINNED_ALL = PINNED + [SANDBOX, 'KR_CReplayRun']",
     "# auto-nav (10-15): on saved stacks when the player saves with a choice / the partner confirm / the new-game question open\n"
     "AUTONAV_PINNED = [" + ', '.join("'KR_AN_E%05d'" % e for e in EVENTS) + ",\n"
     "                  'KR_ANSelect', 'KR_ANSelFrame', 'KR_ANTrainConfirm', 'KR_ANOpeningQ', 'KR_ANNewGame']\n"
     "PINNED_ALL = PINNED + [SANDBOX, 'KR_CReplayRun'] + AUTONAV_PINNED"),
]
for a, b in pairs:
    assert src.count(a) == 1, a[:70]
    src = src.replace(a, b)
(HERE / 'mdlib.py').write_text(src, 'utf8')
snap = (HERE.parent / 'autonav_20261015' / 'snapshot_base.py').read_text('utf8').replace('import anlib as L', 'import mdlib as L')
assert 'import mdlib as L' in snap
(HERE / 'snapshot_base.py').write_text(snap, 'utf8')
print('ok')
