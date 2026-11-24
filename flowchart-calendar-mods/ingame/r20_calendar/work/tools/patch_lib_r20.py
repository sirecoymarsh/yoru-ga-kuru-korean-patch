"""r20 one-off: adapt the r19lib.py copy (r20lib.py) to the r19 install as the base. Run once."""
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'r20lib.py'
s = p.read_text(encoding='utf8')
old_head = s[:s.index('from pathlib import Path')]
new_head = r'''"""r20 shared helpers (Claude Opus 5.5, 2026-09-27) - a copy of r19_calendar\\r19lib.py (the r15-r19 folders are evidence:
read only).

r20 = the r19 install (21:44, current.json CALENDAR_R19_INSTALLED_NATIVE_PASS) + 「몇 번 갔나 · 남은 이벤트」 on the two screens
where the player picks people: a new 「이벤트」 page of the status window (C_HomeStatusView: dungeon member selection at the home
base and the status window in the dungeon) and two text lines under each portrait of the Saturday training partner selection
(C_SceneTraining@RunSelectPartner). The counts come only from what the game already holds (IsRegisteredEvent of this save and
the calendar tables); no global, no struct field, no save schema change.

Small helpers copied from the Codex / 09-24 Claude build modules (OneDrive `밤이 온다 한국어화`, read only) so that nothing
is imported from that folder. Everything this project writes stays under r20_calendar\\ on P:.
Base snapshot: the base AIN = the r19 candidate, so the r19 candidate folder (AIN + candidate_meta.json + candidate_raw_code.jam)
is READ; after a rebase work\\snapshot_base_r20.py makes r20's own copy (base_paths()).
Save copies: files unchanged since the r19 copy map are READ from where that map points (r15/r16/r18/r19 savecopy); only new or
changed files are copied into r20_calendar\\work\\savecopy (work\\savecopy_manifest.json maps every file to its copy).
"""
'''
s = new_head + s[len(old_head):]
rep = [
    ("HERE = Path(__file__).resolve().parent                     # ...\\ingame\\r19_calendar",
     "HERE = Path(__file__).resolve().parent                     # ...\\ingame\\r20_calendar"),
    ("BASE_AIN_SHA = '1f60b6853151e6f62d8803b669da5ae92b285628e89c504c2b9ac90a74038888'   # = the r18 candidate (installed 19:0x)",
     "BASE_AIN_SHA = '1d6081e94cbba5a1e33a12cfad2e542bfa7b689b89373f5386475675c53a1948'   # = the r19 candidate (installed 21:44)"),
    ("BASE_STATUS = 'CALENDAR_R18_INSTALLED_NATIVE_PASS'", "BASE_STATUS = 'CALENDAR_R19_INSTALLED_NATIVE_PASS'"),
    ("BASE_MANIFEST_SHA = 'e24243319ff6a1a90afb7956ce75a92241db6eb3e6053bee117fd967cfc6b78c'",
     "BASE_MANIFEST_SHA = '13280ac23d670946fff46f9a9be5d38fcab0f421aab865ba48b5f67eda4fa21f'\n"
     "BASE_CHART_SHA = 'cc645872b062e42e9d5ed103555bb173c7e6a5df5f24f3a113646bb72de208ea'   # help-menu chart (r19 install; r20 does not touch it)"),
    ("R18 = HERE.parent / 'r18_calendar'                         # read only (evidence: its candidate = the base, installed 19:0x)\nR18_AIN_SHA = BASE_AIN_SHA",
     "R18 = HERE.parent / 'r18_calendar'                         # read only (evidence: installed 19:0x, below r19)\n"
     "R19 = HERE.parent / 'r19_calendar'                         # read only (evidence: its candidate = the base, installed 21:44)\n"
     "R19_AIN_SHA = BASE_AIN_SHA\n"
     "R18_AIN_SHA = '1f60b6853151e6f62d8803b669da5ae92b285628e89c504c2b9ac90a74038888'\n"
     "R19_JOURNAL = CODEX / 'evidence' / 'calendar_r19' / 'journal.json'"),
    ("PINNED_ALL = PINNED + [SANDBOX]                            # r19: all six keep index, address and every code byte",
     "PINNED_ALL = PINNED + [SANDBOX]                            # r19 and r20: all six keep index, address and every code byte"),
    ("SAVECOPY = WORK / 'savecopy'                   # only the files that differ from the copies the r18 map points to\n"
     "R18_SAVEMAP = R18 / 'work' / 'savecopy_manifest.json'   # read only (maps to r15, r16 or r18 copies)",
     "SAVECOPY = WORK / 'savecopy'                   # only the files that differ from the copies the r19 map points to\n"
     "R19_SAVEMAP = R19 / 'work' / 'savecopy_manifest.json'   # read only (maps to r15, r16, r18 or r19 copies)"),
    ('    """Path of the copy that holds save file `rel` (an r15 / r16 / r18 copy when unchanged, else the r19 copy)."""',
     '    """Path of the copy that holds save file `rel` (an r15 / r16 / r18 / r19 copy when unchanged, else the r20 copy)."""'),
]
for a, b in rep:
    assert s.count(a) == 1, (a[:70], s.count(a))
    s = s.replace(a, b)
new_bp = '''def base_paths():
    """The base AIN copy + its meta.json + raw code dump: r20's own snapshot (after a rebase), else the r19 candidate files
    (read only) when the r19 candidate is the base AIN. Nothing is ever written into the r15-r19 folders."""
    own = WORK / 'base'
    for ain, meta, raw in ((own / 'NightRemaster.ain', own / 'meta.json', own / 'raw_code.jam'),
                           (R19 / 'candidate' / 'NightRemaster.ain', R19 / 'work' / 'build' / 'candidate_meta.json',
                            R19 / 'work' / 'build' / 'candidate_raw_code.jam')):
        if ain.exists() and meta.exists() and raw.exists() and sha(ain) == BASE_AIN_SHA:
            return dict(ain=ain, meta=meta, raw=raw)
    raise AssertionError('no base snapshot with BASE_AIN_SHA: run work/snapshot_base_r20.py')
'''
s = s[:s.index('def base_paths():')] + new_bp
p.write_text(s, encoding='utf8')
print('patched', p)
