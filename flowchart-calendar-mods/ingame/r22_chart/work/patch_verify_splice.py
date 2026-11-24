"""One-off: splice the r22 block into verify_chart_r22.py, add the VM op for planted defects, update the r21 texts that r22
changes (the chart screen instead of the 「다음 단계」 notice, the revert wording)."""
from pathlib import Path
here = Path(__file__).resolve().parent
p = here.parent / 'verify_chart_r22.py'
s = p.read_text('utf8')
blk = (here / 'verify_r22_block.py').read_text('utf8')
assert 'def chart_expect' not in s, 'already spliced'
i = s.index('\ndef main():')
s = s[:i] + '\n\n' + blk + '\n' + s[i:]


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90])
    s = s.replace(a, b)


rep("""                elif op == 'VM_NOP':                        # planted defects only (r21): an operation removed
                    pass""", """                elif op == 'VM_NOP':                        # planted defects only (r21): an operation removed
                    pass
                elif op == 'VM_POP_PUSHS':                  # planted defects only (r22): a call that consumes one value and gives ""
                    st.pop()
                    st.append('')""")
rep("T_CHART = '〓모드 메뉴\\n†이벤트 플로우 차트는 다음 단계에서 열립니다'",
    "T_CHART = '<chart>'                    # r22: the chart screen (a chart wait in vm.dialogs) where r21 showed the 「다음 단계」 notice")
rep("T_REVERT = '〓모드 메뉴\\n†전체 개방 되돌리기: 이 저장에서 본 이벤트만 열람·재생됩니다'",
    "T_REVERT = '〓모드 메뉴\\n†전체 개방 되돌리기: 읽은 이벤트만 열람·재생됩니다'   # r22 wording (the chart is save-independent)")
# V34: the chart command is answered by closing the chart (0 = right click); the 「  chart  」 case likewise
rep("            ('chart', [OK], T_CHART, {}, None),", "            ('chart', [0], T_CHART, {}, None),")
rep("""    for cmd, known in (('bogus', False), ('', False), ('CHART', False), ('chart extra', False), ('unlock', False), ('  chart  ', True)):
        vm = mk()
        res, again, ds, code = r21_home(vm, frames=4, each=lambda v, f, c=cmd: hook_request(v, c) if f == 0 else None, answers=[OK] if known else [])""",
    """    for cmd, known in (('bogus', False), ('', False), ('CHART', False), ('chart extra', False), ('unlock', False), ('  chart  ', True)):
        vm = mk()
        res, again, ds, code = r21_home(vm, frames=4, each=lambda v, f, c=cmd: hook_request(v, c) if f == 0 else None, answers=[0] if known else [])""")
# V38: a result and the chart request together
rep("""    res, again, ds, code = r21_home(vm, each=both, answers=[OK, OK])
    assert [ko(d['title']).split('\\n')[0] for d in ds[1:]] == [T_RESULT_HEAD, '〓모드 메뉴'] and ko(ds[2]['title']) == T_CHART, [ko(d['title'])[:12] for d in ds]""",
    """    res, again, ds, code = r21_home(vm, each=both, answers=[OK, 0])
    assert [ko(d['title']).split('\\n')[0] for d in ds[1:]] == [T_RESULT_HEAD, T_CHART] and ko(ds[2]['title']) == T_CHART, [ko(d['title'])[:12] for d in ds]""")
# V39: the home menu serves the pending chart request (close it); our own window = the chart now (its frame is KR_CFrame)
rep("""        res, again, ds, code = r21_home(vm, answers=[OK])
        assert REQ not in vm.disk and ko(ds[1]['title']) == T_CHART""", """        res, again, ds, code = r21_home(vm, answers=[0])
        assert REQ not in vm.disk and ko(ds[1]['title']) == T_CHART""")
rep("""    res, again, ds, code = r21_home(vm, frames=3, answers=[Wait(10, OK, during_notice)])""",
    """    res, again, ds, code = r21_home(vm, frames=3, answers=[Wait(10, 0, during_notice, tick='KR_CFrame')])""")
rep("""    vm.fail_delete = {REQ}
    res, again, ds, code = r21_home(vm, each=lambda v, f: hook_request(v, 'chart') if f == 0 else None, answers=[OK])""",
    """    vm.fail_delete = {REQ}
    res, again, ds, code = r21_home(vm, each=lambda v, f: hook_request(v, 'chart') if f == 0 else None, answers=[0])""")
p.write_text(s, 'utf8')
print('spliced; T_CHART uses:', s.count('T_CHART'))
