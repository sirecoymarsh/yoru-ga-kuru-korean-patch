# -*- coding: utf-8 -*-
"""Make build_deadline_ain.py from calendar_title_20261018/build_title_ain.py (read only): the same method, plus
  - the baked deadline tables (KR_DLInfo, KR_DLPre) from schedule.json, for the events the installed calendar cells name;
  - the hand-written body of KR_DLBindClick (EraseMouseLClickEvent / AddMouseLClickEvent with a KR_DLClick delegate, as r13);
  - the PACT candidate (build_pact_deadline.py) recorded in the manifest (pact_changed)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
src = (HERE.parent / 'calendar_title_20261018' / 'build_title_ain.py').read_text('utf8')


def rep(a, b):
    global src
    assert src.count(a) == 1, (a[:80], src.count(a))
    src = src.replace(a, b)


rep('"""Title-calendar spoiler layer - AIN candidate', '"""Deadline-alert layer - AIN candidate')
rep('base = work/base (snapshot of the scene-list install; snapshot_base.py)',
    'base = work/base (snapshot of the title-layer install; snapshot_base.py); the PACT candidate comes from build_pact_deadline.py')
rep('Method (as build_list_ain.py): jaf compiles the KR_LT* helpers', 'Method (as build_title_ain.py): jaf compiles the KR_DL* helpers')
rep('import ltlib as L', 'import ltlib as L'.replace('ltlib', 'dllib'))
rep("JAF_SRC = HERE / 'claude_title.jaf'", "JAF_SRC = HERE / 'claude_deadline.jaf'\nFLOW = HERE.parent.parent\nCELLS = HERE.parent / 'r22_chart' / 'work' / 'build' / 'cells.json'")
a = src[src.index('SITES = ['):src.index(']\n', src.index('SITES = [')) + 2]
b = '''SITES = [
    ('KR_T8HomeMenuOpen', 'KR_HVClickable', 'KR_DLClickable', 'the home top menu opens: the left panel as before, then the deadline panel is filled and shown'),
    ('KR_T8HomeMenuClose', 'KR_HVClickable', 'KR_DLClickable', 'the home top menu closes: the deadline panel is hidden'),
    ('KR_HVPick', 'KR_LVPerson', 'KR_DLPick', "the panel's 「목록에서 보기」 pick opens the list on 기한; a companion pick opens that companion's list"),
    ('KR_LVChart', 'KR_LVRun', 'KR_DLRun', 'the board opens the list loop with the 기한 chip'),
    ('KR_LVPerson', 'KR_LVRun', 'KR_DLRun', "a companion's list loop with the 기한 chip"),
]
END = {4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30}


def bake_deadlines():
    """KR_DLInfo(no) = kind * 100000000 + from * 10000 + due and KR_DLPre(no) as if-trees, for the events of the installed
    calendar cells (r22 cells.json, tabs 0-7): kind 1 = after_training pools of some months (the month mask), kind 2 =
    an after_training_priority with IsTodayOrBefore in its condition (window, the earlier priority talk it needs)."""
    import json, re
    sys.path.insert(0, str(FLOW / 'chart'))
    import build_chart as B
    s = B.load('schedule.json')
    ev = {e['id']: e for e in s['events']}
    rows = json.loads(CELLS.read_text('utf8'))['rows']
    nos = sorted({r['no'] for r in rows if r['tab'] <= 7})
    info, pre = {}, {}
    for no in nos:
        e = ev.get(no)
        if not e:
            continue
        for t in e['triggers']:
            x = t.get('condition_expr') or ''
            b_ = re.search(r'IsTodayOrBefore\\((\\d+), (\\d+)\\)', x)
            if b_:
                a_ = re.search(r'IsTodayOrAfter\\((\\d+), (\\d+)\\)', x)
                ps = [int(p) for p in re.findall(r'(?<!!\\()LEventFlag::GetOnce\\("E(\\d+)"\\)', x) if int(p) != no]
                assert len(ps) <= 1 and all(p >= 10000 for p in ps), (no, ps)
                frm = int(a_.group(1)) * 100 + int(a_.group(2)) if a_ else 0
                info[no] = 2 * 100000000 + frm * 10000 + int(b_.group(1)) * 100 + int(b_.group(2))
                if ps:
                    pre[no] = ps[0]
        if no not in info and e['category'] == 'after_training':
            ms = sorted({t.get('month') for t in e['triggers'] if t['kind'] == 'pool' and t.get('month')})
            if ms:
                assert all(4 <= m <= 11 for m in ms), (no, ms)
                info[no] = 1 * 100000000 + sum(1 << (m - 4) for m in ms)

    def tree(fn, table, default):
        pairs = sorted(table.items())
        lines = ['int %s(int no) {' % fn]

        def rec(lo, hi, ind):
            if hi - lo <= 6:
                for k, v in pairs[lo:hi]:
                    lines.append(f'{ind}if (no == {k}) return {v};')
                return
            mid = (lo + hi) // 2
            lines.append(f'{ind}if (no < {pairs[mid][0]}) {{')
            rec(lo, mid, ind + '    ')
            lines.append(f'{ind}}}')
            lines.append(f'{ind}else {{')
            rec(mid, hi, ind + '    ')
            lines.append(f'{ind}}}')
        rec(0, len(pairs), '    ')
        lines.append(f'    return {default};')
        lines.append('}')
        return '\\n'.join(lines)
    kinds = {}
    for v in info.values():
        kinds[v // 100000000] = kinds.get(v // 100000000, 0) + 1
    return tree('KR_DLInfo', info, 0), tree('KR_DLPre', pre, 0), dict(events=len(info), kinds=kinds, prerequisites=pre)


def bind_body(fid, click):
    """KR_DLBindClick(number): EraseMouseLClickEvent, then AddMouseLClickEvent (number, delegate KR_DLClick) - r13 home_bind_body."""
    s = ''
    for fn in ['parts::detail::EraseMouseLClickEvent', 'parts::detail::AddMouseLClickEvent']:
        s += L.lr('number') + L.push(-1) + L.push(click) + '\\tDG_NEW_FROM_METHOD\\n' + L.cf(fn)
    return f'FUNC {fid}\\n' + s + '\\tRETURN\\nENDFUNC KR_DLBindClick\\n'
'''
src = src.replace(a, b)
# the hand-written body replaces the compiled placeholder of KR_DLBindClick
rep('''    for f in added:
        path = W / f"jaf_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        body = L.native_lower(path.read_text('utf8')).replace('\\tF_ASSIGN\\n', '\\tX_ASSIGN 1\\n')
        patch.append(L.clean(body, f['name']))''',
    '''    for f in added:
        if f['name'] == 'KR_DLBindClick':
            patch.append(bind_body(f['index'], ids['KR_DLClick']))
            continue
        path = W / f"jaf_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        body = L.native_lower(path.read_text('utf8')).replace('\\tF_ASSIGN\\n', '\\tX_ASSIGN 1\\n')
        patch.append(L.clean(body, f['name']))''')
rep('''    jaf = L.strip_comments(JAF_SRC.read_text('utf8'))
    assert '@@' not in jaf, 'a placeholder left in the jaf\'''',
    '''    assert (O / 'NightRemasterPact.afa').exists(), 'run build_pact_deadline.py first'
    info_tree, pre_tree, baked = bake_deadlines()
    jaf = L.strip_comments(JAF_SRC.read_text('utf8'))
    jaf = jaf.replace('@@INFO_TREE@@', info_tree).replace('@@PRE_TREE@@', pre_tree)
    assert '@@' not in jaf, 'a placeholder left in the jaf\'''')
rep("schema='yoru-calendar-title.candidate.v1', status='CALENDAR_TITLE_20261018_STAGED_NOT_INSTALLED'",
    "schema='yoru-calendar-deadline.candidate.v1', status='CALENDAR_DEADLINE_20261018_STAGED_NOT_INSTALLED'")
rep("files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},\n        pact_changed=False,",
    "files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size),\n               'NightRemasterPact.afa': dict(sha256=L.sha(O / 'NightRemasterPact.afa'), size=(O / 'NightRemasterPact.afa').stat().st_size)},\n        pact_changed=True, pact_changed_entries=[177], pact_new_parts=L.readj(L.WORK / 'pact' / 'build_evidence.json')['made'],")
rep("jam_bodies=[]", "jam_bodies=['KR_DLBindClick (EraseMouseLClickEvent / AddMouseLClickEvent with the KR_DLClick delegate, as r13 KR_T8HomeBindClick)']")
rep("jaf_source_sha256=L.sha(JAF_SRC), build_script_sha256=L.sha(Path(__file__)))",
    "jaf_source_sha256=L.sha(JAF_SRC), build_script_sha256=L.sha(Path(__file__)), baked=baked,\n        pact_build_script_sha256=L.sha(HERE / 'build_pact_deadline.py'), pact_evidence=L.readj(L.WORK / 'pact' / 'build_evidence.json')['outputs'])")
rep("rebase ltlib BASE_* first", "rebase dllib BASE_* first")
(HERE / 'build_deadline_ain.py').write_text(src, 'utf8')
print('ok')
