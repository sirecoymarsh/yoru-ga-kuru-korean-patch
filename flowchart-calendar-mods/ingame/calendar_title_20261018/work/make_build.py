# -*- coding: utf-8 -*-
"""Make build_title_ain.py from calendar_list_20261018/build_list_ain.py (read only): same method, the title-layer sites."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'calendar_list_20261018' / 'build_list_ain.py').read_text('utf8')


def rep(a, b):
    global src
    assert src.count(a) == 1, (a[:80], src.count(a))
    src = src.replace(a, b)


rep('"""Event-calendar scene list, stage 3 - AIN candidate', '"""Title-calendar spoiler layer - AIN candidate')
rep('base = work/base (snapshot of the overview install; snapshot_base.py)', 'base = work/base (snapshot of the scene-list install; snapshot_base.py)')
rep('Method (as build_overview_ain.py): jaf compiles the KR_LV* helpers', 'Method (as build_list_ain.py): jaf compiles the KR_LT* helpers')
rep('import lvlib as L', 'import ltlib as L')
rep("JAF_SRC = HERE / 'claude_list.jaf'", "JAF_SRC = HERE / 'claude_title.jaf'")
a = src[src.index('SITES = ['):src.index(']\n', src.index('SITES = [')) + 2]
b = '''SITES = [
    ('KR_XVRows', 'KR_XVMet', 'KR_LTStart', 'title board rows: 본편, the companions present from the start, 던전 동행'),
    ('KR_LVLanes', 'KR_XVMet', 'KR_LTStart', 'title list rows and chips: the same rows'),
    ('KR_LVReveal', 'KR_P29Read', 'KR_LTRead', 'the title branch reveals no cast / summary / replay / detail (전체 개방 is checked first)'),
    ('KR_LVRow', 'KR_LVNote', 'KR_LTNote', 'title row note: 「타이틀에서는 줄거리를 닫아 둡니다」'),
    ('KR_LVDraw', 'KR_LVPreview', 'KR_LTPreview', 'title preview: the cast, replay line and summary say they are closed'),
    ('KR_LVDraw', 'KR_LVLine', 'KR_LTLine', 'title list: 「달 화면으로」 drawn off'),
    ('KR_LVChart', 'KR_LVBoardExtras', 'KR_LTBoardExtras', 'title board: 회상 · 그 밖 covered and off, the hint'),
    ('KR_LVChart', 'KR_CChart', 'KR_LTMonth', 'no month view from the title board'),
    ('KR_LVRun', 'KR_CChart', 'KR_LTMonth', 'no month view from the title list'),
]
'''
src = src.replace(a, b)
rep("schema='yoru-calendar-list.candidate.v1', status='CALENDAR_LIST_20261018_STAGED_NOT_INSTALLED'",
    "schema='yoru-calendar-title.candidate.v1', status='CALENDAR_TITLE_20261018_STAGED_NOT_INSTALLED'")
rep("rebase lvlib BASE_* first", "rebase ltlib BASE_* first")
(HERE / 'build_title_ain.py').write_text(src, 'utf8')
print('ok')
