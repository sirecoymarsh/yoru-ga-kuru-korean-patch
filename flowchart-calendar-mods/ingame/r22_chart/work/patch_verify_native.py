"""One-off: the r22 native comparison (--native): the chart pages the probes logged = the VM's drawing of the same pages under the
same global records; the tours' flow (replay returned, parts released, title / home pixels); the per-kind replay verdicts."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'verify_chart_r22.py'
s = p.read_text('utf8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:100])
    s = s.replace(a, b)


NATIVE = r'''
def cells_text(vm):
    """the probe's CELLS block format (KR_P22Cells) from the VM's parts."""
    t = 'OURS %d ALL %s OPEN %s' % (len(vm.ours22()), vm.vars.get('YoruKR.C.All', ''), vm.vars.get('YoruKR.C.Open', ''))
    t += '\nHEAD ' + ko(vm.parts[CPART(1)]['text'])
    t += '\nPAGE ' + ko(vm.parts[CPART(3)]['text'])
    for s_ in range(12):
        box = CPART(40 + s_ * 6)
        if box not in vm.parts:
            t += '\nCELL %d -' % s_
            continue
        g = lambda j: ko(vm.parts[box + j]['text']) if box + j in vm.parts else ''
        t += '\nCELL %d thumb=%d name=%s id=%s cond=%s' % (s_, int(box + 1 in vm.parts), g(2), g(3), g(4))
    return t


def native_state(vm, C, line):
    """GLOBAL <tag> ALL=<0|1> i i i ... -> the VM's read marks / recollection cells so that exactly those cells' events are open."""
    parts = line.split()
    all_ = parts[2] == 'ALL=1'
    opened = {int(x) for x in parts[3:]}
    vm.flags, vm.mem_enabled = set(), set()
    for i in opened:
        no = C['rows'][i]['no']
        m = vm.msg_of.get(no, -1)
        if m >= 0:
            vm.flags.add(m)
        else:
            c = C['memcell'].get(no, 0)
            assert c > 0, ('a globally open event without a first message and without a recollection cell', no)
            vm.mem_enabled.add((c // 100 - 1, c % 100 - 1))
    got = {i for i in range(len(C['rows'])) if cstate(vm, C, C['rows'][i]['no']) == 1}
    assert got == opened, ('native global state cannot be reproduced', sorted(got ^ opened)[:5])
    return all_


def r22_native_checks(cand, nm, X, C, counts):
    doc = L.readj(L.EVID / 'probe_r22.json')
    man = L.readj(O / 'manifest.json')
    cs = man['files']['NightRemaster.ain']['sha256']
    out = {}
    # ---- the title tour
    t = doc['title']
    assert t.get('candidate_sha256') == cs, 'probe_r22.json title tour logged by another candidate'
    assert t.get('exit_code') == 0 and not t.get('vm_error') and not t.get('message') and not t.get('timeout') and t['log'][-1] == 'END', \
        ('title tour', t.get('exit_code'), t.get('vm_error'), t.get('message'), t['log'][-3:])
    log = t['log']
    glob = {l.split()[1]: l for l in log if l.startswith('GLOBAL ')}
    tgt = next(l for l in log if l.startswith('TARGET '))
    tt, tp = int(re.search(r'tab=(\d+)', tgt).group(1)), int(re.search(r'page=(\d+)', tgt).group(1))
    plan = {'TAB0 P1': ('chart1', 0, 0), 'TAB6 P1': ('chart1', 6, 0), 'TAB8 P1': ('chart1', 8, 0), 'TARGET LOCKED': ('chart1', tt, tp),
            'TARGET AFTER NOTICE': ('chart1', tt, tp), 'TARGET UNLOCKED': ('chart2', tt, tp), 'TARGET REVERTED': ('chart3', tt, tp)}
    blocks_ = r22_blocks(log, 'CELLS')
    assert set(blocks_) == set(plan), sorted(blocks_)
    for tag, (g, tab, page) in plan.items():
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, glob[g])
        vm.parts = {}
        chart_open(vm, all_)
        vm.run('KR_CDraw', [tab, page])
        want = cells_text(vm)
        got = blocks_[tag][0]
        assert got == want, ('native chart page differs from the VM', tag, [(a, b) for a, b in zip(got.split('\n'), want.split('\n')) if a != b][:3])
        counts['R22N_pages_equal_vm'] += 1
    # the flow: locked notice, unlock, replay (memory mode) and back on the title, revert
    assert any(l.startswith('REPLAY first message memory=1') and 'ours=0' in l for l in log), 'title tour: the replay did not run in memory mode with the chart closed'
    ret = next(l for l in log if l.startswith('RETURNED to the title'))
    assert 'ours=0' in ret and 'open= ' in ret and 'play= ' in ret, ret
    dl = r22_blocks(log, 'DIALOG')
    assert dl.get('chart1') == [T_LOCKED], ('native locked-cell notice', dl.get('chart1'))
    assert dl.get('unlock') == ['〓모드 메뉴\n†전체 개방: 안 본 이벤트도 열람·재생됩니다'] and dl.get('revert') == [T_REVERT], (dl.get('unlock'), dl.get('revert'))
    a_no = int(re.search(r' A=(\d+)', tgt).group(1))
    b_no = int(re.search(r' B=(\d+)', tgt).group(1))
    vm = chart_vm(cand, nm, X)
    native_state(vm, C, glob['chart2'])
    want_page = '〓' + ko(vm.run('KR_T19EvHead', [a_no])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [a_no])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [a_no])) \
        + '\n' + C_STATE['all'] + '\n' + C_PLAY_NOTE
    assert dl.get('chart2') == [want_page], ('native scene page (chart branch)', dl.get('chart2'), want_page)
    ia = next(i for i, r in enumerate(C['rows']) if r['no'] == a_no and not r['card'])
    ib = next(i for i, r in enumerate(C['rows']) if r['no'] == b_no and not r['card'])
    g1, g3 = set(glob['chart1'].split()[3:]), set(glob['chart3'].split()[3:])
    assert str(ia) not in g1 and str(ib) not in g1, 'the target cells were open before the unlock'
    assert str(ia) in g3 and str(ib) not in g3, ('after the revert: the replayed scene keeps its read mark, the other locks again', str(ia) in g3, str(ib) in g3)
    counts['R22N_title_tour'] = 1
    # pixels: the title after the replay = the title after the first chart (the same title loop state; the shot before the first
    # chart has the title's own hover highlight, see the report)
    shots = L.EVID / 'probe'
    px = diff_png(shots / 'chart_title_after_chart1.png', shots / 'chart_title_after_replay.png') if (shots / 'chart_title_after_chart1.png').exists() else None
    out['title'] = dict(pages=len(plan), replayed=a_no, relocked=b_no, title_after_chart_vs_after_replay_px=px, seconds=t.get('seconds'))
    assert px == 0, ('title pixels after the replay differ from the title after closing the chart', px)
    # ---- the home tour
    h = doc.get('home')
    if h:
        assert h.get('candidate_sha256') == cs and h.get('exit_code') == 0 and h['log'][-1] == 'END', ('home tour', h.get('exit_code'), h['log'][-3:])
        hl = h['log']
        assert any(l.startswith('REPLAY first message memory=1') and 'ours=0' in l for l in hl), 'home tour: no memory-mode replay'
        assert any(l.startswith('RETURNED to the home menu') and 'ours=0' in l for l in hl)
        hb = r22_blocks(hl, 'CELLS')['HOME OPEN'][0]
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, next(l for l in hl if l.startswith('GLOBAL home')))
        vm.parts = {}
        chart_open(vm, all_)
        month = int(re.search(r'HEAD .*?　(\d+)월　', hb).group(1))
        vm.run('KR_CDraw', [month - 4, 0])
        assert hb == cells_text(vm), ('native home chart page differs from the VM', [(a, b) for a, b in zip(hb.split('\n'), cells_text(vm).split('\n')) if a != b][:3])
        pxh = diff_png(shots / 'chart_home_before.png', shots / 'chart_home_after.png')
        out['home'] = dict(home_before_vs_after_px=pxh, seconds=h.get('seconds'))
        assert pxh == 0, ('home pixels after the replay differ', pxh)
        counts['R22N_home_tour'] = 1
    # ---- the per-kind replays
    k = L.readj(L.EVID / 'replay_kinds.json')
    assert k['candidate_sha256'] == cs and all(e.get('candidate_sha256') == cs for e in k['events'].values()), 'replay_kinds.json from another candidate'
    out['kinds'] = k['verdicts']
    counts['R22N_kinds'] = len(k['events'])
    return out


def r22_blocks(log, kind):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'%s (.*) <<<$' % kind, log[i])
        if z:
            j = log.index('>>>', i)
            out.setdefault(z.group(1), []).append('\n'.join(log[i + 1:j]))
            i = j
        i += 1
    return out


def diff_png(a, b):
    from PIL import Image, ImageChops
    x, y = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    if x.size != y.size:
        return -1
    bb = ImageChops.difference(x, y).getbbox()
    if bb is None:
        return 0
    d = ImageChops.difference(x, y).crop(bb)
    return sum(1 for q in d.getdata() if q != (0, 0, 0))

'''
rep('\ndef r16_day_alias():', NATIVE + '\ndef r16_day_alias():')
rep("""        out = native_checks(vm, X, counts)
        r21n = r21_native_checks(lambda: r21_fresh(cand, nm), counts)
        result = dict(schema='yoru-modmenu-r21.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, r21=r21n, counts=dict(counts))""",
    """        out = native_checks(vm, X, counts)                  # the r20 calendar tour run on the r22 candidate (probe_calendar_tour_r22.py)
        C = chart_expect(X, vm)
        r22n = r22_native_checks(cand, nm, X, C, counts)
        result = dict(schema='yoru-chart-r22.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, r22=r22n, counts=dict(counts))""")
p.write_text(s, 'utf8')
print('native wired')
