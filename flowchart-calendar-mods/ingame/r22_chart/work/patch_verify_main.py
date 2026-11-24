"""One-off: r22 defects + main() wiring in verify_chart_r22.py."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'verify_chart_r22.py'
s = p.read_text('utf8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90])
    s = s.replace(a, b)


DEF = r'''
def leaf_int(fn, key, new_value):
    """replace the int a generated table returns for `key` (`if (k == key) return v;` = PUSH key / EQUALE / IFNZ / JUMP / PUSH v)."""
    def mut(ops):
        hits = [i for i in range(len(ops) - 5) if ops[i] == ['PUSH', str(key)] and ops[i + 1] == ['EQUALE'] and ops[i + 2][0] == 'IFNZ'
                and ops[i + 3][0] == 'JUMP' and ops[i + 4][0] == 'PUSH']
        if len(hits) != 1:
            raise RuntimeError(('defect could not be planted: no int leaf', fn, key, len(hits)))
        ops[hits[0] + 4] = ['PUSH', str(new_value)]
        return ops
    return {fn: mut}


def r22_defects(C):
    """r22's eight: a locked scene replayable, 「전체 개방」 ignored, the chart exception leaking into the calendar, a parts leak,
    a wrong order, a thumbnail on a cell without CG, the E number missing, a condition missing."""
    first = C['first'][0]
    a, b = C['rows'][first], C['rows'][first + 1]
    swap = leaf_int('KR_CCellRef', 0, b['ref'])
    ci = next(i for i, r in enumerate(C['rows']) if r['cond'])
    return [('V44 a locked scene replayable (KR_CCanPlay skips the lock)', 'r22_flow',
             op_replace('KR_CCanPlay', lambda o: o == ['CALLFUNC', 'KR_COpen'], lambda o: ['VM_POP_PUSH1'])),
            ('V43 「전체 개방」 ignored (the flag read as 0)', 'r22_pages',
             op_replace('KR_CUnlockAll', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == '1', lambda o: list(sp('X')))),
            ('V45 the chart exception applied in the calendar (KR_CActive without the chart-root test)', 'r22_confine',
             op_replace('KR_CActive', lambda o: o == ['CALLHLL', 'PartsEngine IsExist 0'], lambda o: ['VM_POP_PUSH1'])),
            ('V46 parts leak (KR_CClear stops at part 100)', 'r22_flow',
             op_replace('KR_CClear', lambda o: o == ['.LOCALASSIGN', 'i 111'], lambda o: ['.LOCALASSIGN', 'i 100'])),
            ('V41 wrong order (the first two cells of 4월 swapped)', 'r22_tables', swap),
            ('V42 a thumbnail on cells without CG (KR_CThumb default)', 'r22_pages',
             op_replace('KR_CThumb', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == '', lambda o: list(sp('シス／ＣＧモード／サムネイル／CG1001')), nth=-1)),
            ('V42 the E number missing from a cell', 'r22_pages',
             op_replace('KR_CDrawCell', lambda o: o == ['CALLFUNC', 'KR_T9EvNo'], lambda o: ['VM_POP_PUSHS'])),
            ('V41 a condition missing (cell %d)' % ci, 'r22_tables', leaf_replace('KR_CCellCond', ci, ''))]

'''
rep('\ndef r16_day_alias():', DEF + '\ndef r16_day_alias():')

# main: the r22 checks after r21's
rep("""    r21_scope = r21_scope_checks(mk, counts)
    r21_style_checks(counts)
""", """    r21_scope = r21_scope_checks(mk, counts)
    r21_style_checks(counts)
    # r22
    C = chart_expect(X, vm)
    v22 = chart_vm(cand, nm, X)
    r22_tables = chart_table_checks(v22, X, C, counts)
    chart_page_checks(v22, X, C, counts)
    r22_flow = chart_flow_checks(cand, nm, X, C, counts)
    r22_confine = chart_confine_checks(cand, nm, X, C, counts)
    r22_title = title_checks(cand, nm, X, C, counts)
    r22_noplay = noplay_checks(cand, nm, X, C, counts)
""")
rep("""                  r21=dict(commands=r21_rows, flag=r21_flag, reset=r21_reset, results=r21_result, scope=r21_scope,
                           frames_in_saved_stacks=sorted({x['function'] for x in frames if x['function'] in ('C_SceneHomebase@RunHome', 'C_SelectDialog@Run', 'KR_T9HomeMenuRun')})))""",
    """                  r21=dict(commands=r21_rows, flag=r21_flag, reset=r21_reset, results=r21_result, scope=r21_scope,
                           frames_in_saved_stacks=sorted({x['function'] for x in frames if x['function'] in ('C_SceneHomebase@RunHome', 'C_SelectDialog@Run', 'KR_T9HomeMenuRun')})),
                  r22=dict(tables=r22_tables, flow=r22_flow, confine=r22_confine, title=r22_title, noplay=r22_noplay))""")
rep("""                      r21_scope=lambda v: r21_scope_checks(lambda: r21_fresh(cand, nm, mutate=v.mutate, alias=v.alias), collections.Counter()))""",
    """                      r21_scope=lambda v: r21_scope_checks(lambda: r21_fresh(cand, nm, mutate=v.mutate, alias=v.alias), collections.Counter()),
                      r22_tables=lambda v: chart_table_checks(chart_vm(cand, nm, X, mutate=v.mutate), X, C, collections.Counter()),
                      r22_pages=lambda v: chart_page_checks(chart_vm(cand, nm, X, mutate=v.mutate), X, C, collections.Counter()),
                      r22_flow=lambda v: chart_flow_checks_m(cand, nm, X, C, v.mutate),
                      r22_confine=lambda v: chart_confine_checks_m(cand, nm, X, C, v.mutate))""")
rep("""        for label, group, mutation in DEFECTS + [table_defect(X)] + r19_defects(vm, X) + r20_defects() + r21_defects():""",
    """        for label, group, mutation in DEFECTS + [table_defect(X)] + r19_defects(vm, X) + r20_defects() + r21_defects() + r22_defects(C):""")
rep("""        assert len(planted) == 40, len(planted)""", """        assert len(planted) == 48, len(planted)""")
rep("""    L.writej(W / ('vm_verification_selftest.json' if selftest else 'vm_verification.json'), json.loads(json.dumps(result, ensure_ascii=False, default=str)))""",
    """    L.writej(W / ('vm_verification_selftest.json' if selftest else 'vm_verification.json'), json.loads(json.dumps(result, ensure_ascii=False, default=str)))
    L.writej(L.EVID / ('verify_selftest.json' if selftest else 'verify.json'), json.loads(json.dumps(dict(
        candidate_sha256=result['candidate_sha256'], seconds=result.get('seconds'), counts=result['counts'], r22=result.get('r22'),
        planted_defects=result.get('planted_defects')), ensure_ascii=False, default=str)))""")
# mutate-aware wrappers of the flow / confine checks (they build their own VMs)
rep('\ndef r16_day_alias():', r'''
def chart_flow_checks_m(cand, nm, X, C, mutate):
    global chart_vm
    orig = chart_vm
    try:
        chart_vm = lambda c, n, x, mutate_=None, alias=None: orig(c, n, x, mutate=mutate)
        return chart_flow_checks(cand, nm, X, C, collections.Counter())
    finally:
        chart_vm = orig


def chart_confine_checks_m(cand, nm, X, C, mutate):
    """V45 with a planted defect in the r22 candidate's VM (the r21 reference VM is left as it is)."""
    global chart_vm
    orig = chart_vm
    r21 = L.R21 / 'candidate' / 'NightRemaster.ain'
    try:
        chart_vm = lambda c, n, x, mutate_=None, alias=None: orig(c, n, x, mutate=(None if c == r21 else mutate))
        return chart_confine_checks(cand, nm, X, C, collections.Counter())
    finally:
        chart_vm = orig

''' + '\ndef r16_day_alias():')
p.write_text(s, 'utf8')
print('main wired')
