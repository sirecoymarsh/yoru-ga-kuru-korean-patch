# -*- coding: utf-8 -*-
"""Print the raw ops around every intended same-length site in the base AIN (read only)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import anlib as L

bp = L.base_paths()
m = L.read_meta(bp['meta'])
vers = L.versions(bp['raw'])

EVENTS = [58, 63, 69, 104, 258, 260, 322, 611, 10021, 20041, 20081, 20164, 30001, 30021, 30152, 40021, 40041, 40043, 40061]
SITES = [('ＥＶ／元／E%05d' % e, 'CALLFUNC', '■選択メッセージ／実行') for e in EVENTS] + [
    ('C_SelectMessage@CreateParts', 'PUSH', 'C_SelectMessInfo@CreateParts'),
    ('C_SelectMessage@Update', 'CALLFUNC', '■バックログ起動監視'),
    ('C_SceneTraining@_UpdateInputPartner', 'CALLFUNC', 'C_UserInputManager::IsClickCancelOtherMouse'),
    ('C_SceneTraining@RunSelectPartner', 'CALLFUNC', '■選択ダイアログ／実行'),
    ('L_EventCall::Check', 'PUSH', 'C_GameFlags@Date::get'),
    ('C_SceneGame@Run', 'PUSH', 'C_GameFlags@IsPlayOpening::get'),
]
for owner, kind, target in SITES:
    fid = L.fid_of(m, owner)
    tid = L.fid_of(m, target)
    v = L.live_version(m, vers, fid)
    ops = v['ops']
    key = '%s 0x%x' % (kind, tid)
    hits = [i for i, (ad, op) in enumerate(ops) if op == key]
    print('==', owner, fid, '->', target, tid, 'hits', len(hits))
    for i in hits[:2]:
        ctx = [op for _, op in ops[max(0, i - 4):i + 4]]
        print('   ', hex(ops[i][0]), ctx)
