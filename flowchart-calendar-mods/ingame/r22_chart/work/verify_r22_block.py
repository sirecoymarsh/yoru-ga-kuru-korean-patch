# ============================================================== r22: the chart screen (V41-V48)
CROOT = 2026092200
CPART = lambda i: CROOT + i
C_TABS = ['4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '회상', '그 밖']
C_GOLD, C_SKY, C_GRAY, C_WHITE = 'r=255 g=214 b=110', 'r=130 g=200 b=255', 'r=150 g=150 b=158', 'r=240 g=240 b=245'
C_NAME_THUMB, C_NAME_SMALL, C_WHEN_THUMB, C_IDWHEN_SMALL, C_COND = 15.5, 15.5, 9.0, 17.5, 18.5
C_NOTE = '재생 불가(게임 안에서만)'
T_LOCKED = '〓이벤트 플로우 차트\n†아직 읽지 않은 장면입니다 · 본 뒤에 열립니다\n†모드 → 전체 개방으로 모든 칸을 열 수 있습니다'
C_PLAY_NOTE = '〓회상 모드처럼 재생합니다 · 진행 상태는 바뀌지 않습니다'
C_NOPLAY_NOTE = '†재생 불가(게임 안에서만)'
C_STATE = {1: '¶△ 읽은 장면입니다 (게임 전역 기록)', 'all': '‡● 안 읽은 장면 · 전체 개방으로 열렸습니다', 0: '‡● 안 읽은 장면입니다 · 본 뒤에 열립니다'}
C_LEGEND = '‡●†안 읽음　¶△†읽음(게임 전역 기록)'
C_CODE = 2026092802
TITLE_ACT_ROOT = None


def tint(s, rgb):
    return '' if s == '' else '${font ' + rgb + '}' + s + '${/font}'


def cunits(t):
    return sum(0.5 if ord(ch) < 0x80 else 1.0 for ch in t)


def ccut(t, budget):
    """(verifier's own) cut a text to `budget` units, 「…」 at the end."""
    if cunits(t) <= budget:
        return t
    out = ''
    for ch in t:
        if cunits(out) + cunits(ch) + 1 > budget:
            break
        out += ch
    return out.rstrip(' ·,') + '…'


def cwrap(tokens, budget, lines):
    """(verifier's own) tokens joined by ' · ' into <= `lines` lines of <= budget units; a token wider than a line is cut; tokens
    left over are dropped and the last line ends in ' …'."""
    out, cur, i = [], '', 0
    while i < len(tokens):
        t = tokens[i]
        trial = t if not cur else cur + ' · ' + t
        if cunits(trial) <= budget:
            cur = trial
            i += 1
        elif not cur:
            cur = ccut(t, budget)
            i += 1
        else:
            out.append(cur)
            cur = ''
            if len(out) == lines:
                break
    if cur and len(out) < lines:
        out.append(cur)
    if i < len(tokens):
        last = out[-1]
        while last and cunits(last + ' …') > budget:
            last = last[:-1]
        out[-1] = last.rstrip(' ·,') + ' …'
    return out


def when_toks(text):
    t = text.replace(WHEN_CONT, ' · ').replace('\n', ' · ')
    t = re.sub(r'[†‡¶〓]', '', t)
    return [x.strip() for x in re.split(r' · | / ', t) if x.strip()]


def chart_memcells():
    """recollection cell (page * 100 + slot) per event, from graph/memory.json and the chain links in graph/schedule.json (the
    verifier's own walk): the cell's replay event, the replay events chained under it, the event the cell needs."""
    mem = json.loads((L.FLOW / 'graph' / 'memory.json').read_text('utf8'))['entries']
    sch = {e['id']: e for e in json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))['events']}
    out = {}
    for e in mem:
        out[e['play']] = e['page'] * 100 + e['id']
    todo = list(out)
    while todo:
        n = todo.pop()
        for t in sch[n].get('chains_to') or []:
            if sch[t]['category'] == 'memory_replay' and t not in out:
                out[t] = out[n]
                todo.append(t)
    for e in mem:
        out.setdefault(e['need'], e['page'] * 100 + e['id'])
    return out


def chart_kinds(X):
    """replay kind of every event (the verifier's own classification) and the choice / battle flags."""
    kind = {}
    for c in X['cards']:
        for i, no in enumerate(c['stages']):
            k = 'dungeon' if c['lane'] == 8 else ('dated' if c['day'] > 0 else 'undated')
            kind[no] = ('stage_' + k) if i else k
    names = {'prio': 'pool_talk', 'after': 'pool_talk', 'turned': 'pool_talk', 'invite': 'pool_invite', 'walk': 'pool_walk', 'etc': 'system',
             'mem': 'memory', 'unused': 'unused'}
    for ch in X['chips']:
        for no in ch['scenes']:
            kind[no] = names[KINDS[ch['kind']]]
    flags = {}
    for no, e in X['sch'].items():
        f = []
        if e.get('has_choice'):
            f.append('choice')
        if (e.get('effects') or {}).get('event_battle'):
            f.append('battle')
        flags[no] = f
    return kind, flags


def chart_expect(X, vm):
    """The chart's cells, recomputed from the chart data and the base's r19 name functions (not from build_chart_r22)."""
    cards, chips = X['cards'], X['chips']
    cg = json.loads((L.FLOW / 'graph' / 'event_cg.json').read_text('utf8'))
    thumb = {int(k): v['thumb'] for k, v in cg['events'].items() if v['thumb']}
    kinds_doc = L.readj(L.EVID / 'replay_kinds.json') if (L.EVID / 'replay_kinds.json').exists() else {}
    verdict = kinds_doc.get('verdicts', {})
    kind, flags = chart_kinds(X)
    noplay = {no: int(any(verdict.get(x) == 'fail' for x in [kind[no]] + flags[no])) for no in kind}
    tabs = []
    for t in range(10):
        cells = []
        if t <= 7:
            m = t + 4
            ks = [k for k, c in enumerate(cards) if c['month'] == m]
            dated = sorted((k for k in ks if cards[k]['day'] > 0 and cards[k]['lane'] != 8), key=lambda k: (cards[k]['day'], SLOT_RANK[cards[k]['slot']], cards[k]['lane'], k))
            undated = sorted((k for k in ks if cards[k]['day'] == 0 and cards[k]['lane'] != 8), key=lambda k: (SLOT_RANK[cards[k]['slot']], cards[k]['lane'], k))
            dungeon = sorted((k for k in ks if cards[k]['lane'] == 8), key=lambda k: (cards[k]['day'] or 99, SLOT_RANK[cards[k]['slot']], k))
            cells += [('card', k) for k in dated + undated + dungeon]
            mine = sorted((i for i, ch in enumerate(chips) if ch['month'] == m), key=lambda i: (chips[i]['lane'], chips[i]['kind'], i))
        else:
            mine = sorted((i for i, ch in enumerate(chips) if ch['month'] == 12 and ((9 <= ch['lane'] <= 15) if t == 8 else ch['lane'] >= 16)),
                          key=lambda i: (chips[i]['lane'], i))
        for i in mine:
            ch = chips[i]
            sc = list(ch['scenes']) if KINDS[ch['kind']] == 'mem' else sorted(ch['scenes'])
            cells += [('scene', no) for no in sc]
        tabs.append(cells)
    rows = []
    for t, cells in enumerate(tabs):
        for kc, x in cells:
            if kc == 'card':
                c = cards[x]
                no = c['entry']
                when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
                if c['slot']:
                    when += ' ' + SLOT_KR[c['slot']]
                toks = ko(vm.run('KR_T19CardHead', [x])).split(' · ')
                assert toks[0] == when, ('V41 a card head does not start with its date', x, toks[0], when)
                name_toks = toks[1:]
                cc = ko(vm.run('KR_T19CardCond', [x]))
                cond_toks = cc.split(' · ') if cc else []
                ref = 100000 + x
            else:
                no = x
                toks = ko(vm.run('KR_T19EvHead', [no])).split(' · ')
                when = ''
                if re.fullmatch(r'\d{1,2}월', toks[0]):
                    when = toks[0]
                    toks = toks[1:]
                if toks[:2] == ['회상', '그 밖']:
                    toks = toks[2:]
                name_toks = toks
                cond_toks = when_toks(ko(vm.run('KR_T19EvWhen', [no])))
                ref = no
            th = thumb.get(no, '')
            if th:
                name = ccut(' · '.join(name_toks), C_NAME_THUMB)
                w = ccut(when, C_WHEN_THUMB)
            else:
                name = '\n'.join(cwrap(name_toks, C_NAME_SMALL, 2))
                w = when
            cl = cwrap(cond_toks, C_COND, 2) if cond_toks else []
            if noplay[no]:
                cl = (cl[:1] if cl else []) + [C_NOTE]
            rows.append(dict(tab=t, ref=ref, no=no, card=kc == 'card', name=name, when=w, cond='\n'.join(cl), thumb=th, noplay=noplay[no],
                             kind=kind[no]))
    first = []
    i = 0
    for cells in tabs:
        first.append(i)
        i += len(cells)
    return dict(rows=rows, first=first + [len(rows)], noplay=noplay, kind=kind, flags=flags, memcell=chart_memcells(), thumb=thumb)


def chart_vm(cand, nm, X, mutate=None, alias=None):
    v = VM(cand, nm, mutate=mutate, alias=alias)
    v.today = (6, 13)
    v.msg_of = {no: (e['m0'] if e['m0'] is not None else -1) for no, e in X['ev'].items()}
    return v


def cstate(vm, C, no):
    """global read state the chart must show: the first message's read mark or the recollection unlock."""
    m = vm.msg_of.get(no, -1)
    if m >= 0 and m in vm.flags:
        return 1
    c = C['memcell'].get(no, 0)
    return int(c > 0 and (c // 100 - 1, c % 100 - 1) in vm.mem_enabled)


def copen(vm, C, no, all_):
    return all_ or cstate(vm, C, no) == 1


def chart_table_checks(vm, X, C, counts):
    """V41: the tables the chart runs on = the verifier's own recomputation."""
    rows = C['rows']
    for t in range(10):
        assert vm.run('KR_CTabFirst', [t]) == C['first'][t] and vm.run('KR_CTabEnd', [t]) == C['first'][t + 1], ('V41 tab range', t)
    for i, r in enumerate(rows):
        assert vm.run('KR_CCellRef', [i]) == r['ref'], ('V41 cell order', i, r['tab'], vm.run('KR_CCellRef', [i]), r['ref'])
        assert vm.run('KR_CCellEv', [i]) == r['no'], ('V41 cell event', i)
        assert ko(vm.run('KR_CCellName', [i])) == r['name'], ('V41 cell name', i, ko(vm.run('KR_CCellName', [i])), r['name'])
        assert ko(vm.run('KR_CCellWhen', [i])) == r['when'], ('V41 cell when', i, ko(vm.run('KR_CCellWhen', [i])), r['when'])
        assert ko(vm.run('KR_CCellCond', [i])) == r['cond'], ('V41 cell condition', i, ko(vm.run('KR_CCellCond', [i])), r['cond'])
        counts['V41_cells'] += 1
    seen = collections.Counter(r['no'] if not r['card'] else ('card', r['ref']) for r in rows)
    assert max(seen.values()) == 1, 'V41 a cell twice'
    stages = sum(len(c['stages']) for c in X['cards'])
    assert len(rows) == len(X['cards']) + sum(len(ch['scenes']) for ch in X['chips']) and stages + sum(len(ch['scenes']) for ch in X['chips']) == TOTAL_EVENTS
    for no in X['ev']:
        assert ko(vm.run('KR_CThumb', [no])) == C['thumb'].get(no, ''), ('V41 thumbnail', no)
        assert vm.run('KR_CMemCell', [no]) == C['memcell'].get(no, 0), ('V41 recollection cell', no, vm.run('KR_CMemCell', [no]), C['memcell'].get(no, 0))
        assert vm.run('KR_CNoPlay', [no]) == C['noplay'][no], ('V41 not-playable table', no)
        assert vm.run('KR_T9EvMsg', [no]) == vm.msg_of[no], ('V41 first message', no)
        counts['V41_events'] += 1
    for t in range(10):
        assert ko(vm.run('KR_CTabName', [t])) == C_TABS[t]
    counts['V41_thumbnail_cells'] = sum(1 for r in rows if r['thumb'])
    counts['V41_small_cells'] = sum(1 for r in rows if not r['thumb'])
    counts['V41_per_tab'] = [C['first'][t + 1] - C['first'][t] for t in range(10)]
    counts['V41_not_playable_events'] = sum(C['noplay'].values())
    return dict(cells=len(rows), per_tab=counts['V41_per_tab'], thumbnails=counts['V41_thumbnail_cells'])


def cell_parts(vm, s):
    box = CPART(40 + s * 6)
    return [vm.parts.get(box + j) for j in range(5)]


def expect_cell(vm, C, i, all_):
    r = C['rows'][i]
    no = r['no']
    op = copen(vm, C, no, all_)
    st = cstate(vm, C, no)
    th = r['thumb'] if op else ''
    mark = tint('△', C_GRAY) if st == 1 else tint('●', C_SKY)
    ev = 'E%05d' % no
    if op:
        idl, when, name, cond = mark + ' ' + ev, r['when'], tint(r['name'], C_WHITE), r['cond']
    else:
        idl, when, name, cond = tint('● ' + ev, C_GRAY), tint(r['when'], C_GRAY), tint('？？？', C_GRAY), ''
    idtext = idl + ('\n' + when if th else '　' + when)
    return dict(open=op, thumb=th, id=idtext, name=name, cond=tint(cond, C_GRAY) if cond else None, h=172 if th else 118)


def f32(v):
    return struct.unpack('<f', struct.pack('<i', v))[0] if isinstance(v, int) else float(v)


def check_page(vm, C, t, p, all_, counts, strict=True):
    """V42 / V43 / V46: the parts of one drawn page."""
    first, end = C['first'][t], C['first'][t + 1]
    n = end - first
    pages = max(1, (n + 11) // 12)
    opened = sum(1 for i in range(first, end) if copen(vm, C, C['rows'][i]['no'], all_))
    head = tint('이벤트 플로우 차트', C_GOLD) + '　' + C_TABS[t] + '　' + tint('%d/%d' % (opened, n), C_SKY) + ' 열림'
    if all_:
        head += '　' + tint('전체 개방', C_GOLD)
    got_head = ko(vm.parts[CPART(1)]['text'])
    assert got_head == head, ('V42 header', t, p, got_head, head)
    assert ko(vm.parts[CPART(3)]['text']) == '%d / %d쪽' % (p + 1, pages), ('V42 page line', t, p)
    assert vm.parts[CROOT]['show'] == 1 and vm.parts[CROOT].get('z') == 5000, ('V42 root', vm.parts[CROOT].get('z'))
    for b in (30, 32, 34):
        assert vm.parts[CPART(b)].get('click') == 1, ('V42 button not clickable', b)
    for tt in range(10):
        bx = vm.parts[CPART(10 + tt)]
        assert bx.get('click') == 1, ('V42 tab not clickable', tt)
        label = ko(vm.parts[CPART(20 + tt)]['text'])
        assert label == (tint(C_TABS[tt], C_GOLD) if tt == t else C_TABS[tt]), ('V42 tab label', tt, label)
    want_parts = 1 + 3 + 3 * 2 + 10 * 2                      # root, header / legend / page, 3 buttons x 2, 10 tabs x 2
    for s in range(12):
        i = first + p * 12 + s
        box, th, nmp, idp, cdp = cell_parts(vm, s)
        if i >= end:
            assert box is None and th is None and nmp is None and idp is None and cdp is None, ('V46 a part left in an empty slot', t, p, s)
            continue
        e = expect_cell(vm, C, i, all_)
        assert box is not None and box.get('click') == 1 and box['construct'][0] == ('create', 301, e['h']), ('V42 cell box', t, p, s, box and box.get('construct', [None])[0])
        pos = box['pos']
        assert (f32(pos[0]), f32(pos[1])) == (24 + (s % 4) * 309, 114 + (s // 4) * 182), ('V42 cell position', s, pos)
        if e['thumb']:
            assert th is not None and th.get('cg') == e['thumb'] and th.get('parent') == CPART(40 + s * 6), ('V42 thumbnail', t, p, s, th)
            counts['V42_thumbnails'] += 1
        else:
            assert th is None, ('V42 a thumbnail on a cell without one (or a locked cell)', t, p, s, C['rows'][i]['no'], th)
        assert ko(nmp['text']) == e['name'], ('V42 name', t, p, s, ko(nmp['text']), e['name'])
        assert ko(idp['text']) == e['id'], ('V42 id / when', t, p, s, ko(idp['text']), e['id'])
        assert ('E%05d' % C['rows'][i]['no']) in ko(idp['text']), ('V42 E number missing', t, p, s)
        if e['cond'] is None:
            assert cdp is None, ('V42 a condition on a locked cell / a cell without one', t, p, s)
        else:
            assert cdp is not None and ko(cdp['text']) == e['cond'], ('V42 condition', t, p, s, cdp and ko(cdp['text']), e['cond'])
        for part, budget in ((nmp, C_NAME_THUMB if e['thumb'] else C_NAME_SMALL), (cdp, C_COND)):
            if part is None:
                continue
            for line in re.sub(r'\$\{/?font[^}]*\}', '', ko(part['text'])).split('\n'):
                assert cunits(line) <= budget + 0.01, ('V42 a line wider than its cell', line)
        for line in re.sub(r'\$\{/?font[^}]*\}', '', ko(idp['text'])).split('\n'):
            assert cunits(line) <= (C_WHEN_THUMB if e['thumb'] else C_IDWHEN_SMALL) + 1.5, ('V42 id line too wide', line)
        want_parts += 1 + int(bool(e['thumb'])) + 2 + int(e['cond'] is not None)
        counts['V42_cells_drawn'] += 1
        counts['V43_open_cells' if e['open'] else 'V43_locked_cells'] += 1
    assert len(vm.ours22()) == want_parts, ('V46 part count of a page', t, p, len(vm.ours22()), want_parts)
    counts['V42_pages'] += 1


def chart_open(vm, all_=False, ctx=2):
    vm.vars['YoruKR.C.Open'] = '1'
    vm.vars['YoruKR.C.All'] = '1' if all_ else '0'
    vm.vars['YoruKR.C.Ctx'] = str(ctx)


def chart_state(vm, X, C, kind, rnd=None):
    """global records: none / all / partial (a seeded half of the events and of the recollection cells)."""
    firsts = {m for m in vm.msg_of.values() if m >= 0}
    cells = {(c // 100 - 1, c % 100 - 1) for c in C['memcell'].values()}
    if kind == 'none':
        vm.flags, vm.mem_enabled = set(), set()
    elif kind == 'all':
        vm.flags, vm.mem_enabled = set(firsts), set(cells)
    else:
        r = random.Random(rnd or 22)
        vm.flags = {m for m in sorted(firsts) if r.random() < 0.5}
        vm.mem_enabled = {c for c in sorted(cells) if r.random() < 0.5}


def chart_page_checks(vm, X, C, counts, states=(('none', False), ('partial', False), ('all', False), ('none', True))):
    """V42 / V43 / V46: every page of every tab under four global states (no records / half / all / 「전체 개방」 with none)."""
    for st, all_ in states:
        chart_state(vm, X, C, st)
        vm.parts = {}
        chart_open(vm, all_)
        prev = None
        for t in range(10):
            n = C['first'][t + 1] - C['first'][t]
            for p in range(max(1, (n + 11) // 12)):
                vm.run('KR_CDraw', [t, p])
                check_page(vm, C, t, p, all_, counts)
                prev = (t, p)
        vm.run('KR_CClear')
        assert vm.ours22() == [], ('V46 parts left after KR_CClear', vm.ours22()[:4])
        counts['V43_states'] += 1
    # the open test is the global records (or 「전체 개방」) and never the per-save registration
    chart_state(vm, X, C, 'partial')
    vm.registered = {e['fn'] for e in X['ev'].values()}          # every event registered in this save: must not matter
    vm.parts = {}
    chart_open(vm, False)
    vm.reg_asked = []
    for t in range(10):
        vm.run('KR_CDraw', [t, 0])
        check_page(vm, C, t, 0, False, counts)
    assert not vm.reg_asked, ('V43 IsRegisteredEvent asked while the chart is open', vm.reg_asked[:3])
    vm.run('KR_CClear')
    vm.registered = set()
    counts['V43_registration_ignored'] += 1


def chart_session(vm, ctx, answers, all_=False, title=True):
    """KR_CChart(ctx) with the scripted answers (chart waits and dialogs in order). Returns the dialogs (chart waits included)."""
    vm.cur = None
    vm.calls = []
    vm.dialogs = []
    vm.charts = []
    vm.frames = []
    vm.script = list(answers)
    vm.disk[CHART] = 'YoruKR.Chart.1\r\n%d\r\n' % int(all_)
    vm.dirs.add(VM.SAVE_DIR)
    if title:
        vm.title_scene()
    vm.run('KR_CChart', [ctx])
    assert not vm.script, ('answers left over (a window did not open)', vm.script)
    assert vm.ours22() == [], ('V46 chart parts left after the chart', vm.ours22()[:4])
    assert vm.vars.get('YoruKR.C.Open', '') == '' and vm.vars.get('YoruKR.C.Play', '') == '' and vm.vars.get('YoruKR.T9.Unwind', '') == '', \
        ('V44 chart state left after the chart', vm.vars.get('YoruKR.C.Open'), vm.vars.get('YoruKR.C.Play'), vm.vars.get('YoruKR.T9.Unwind'))
    return vm.dialogs


def box_of(s):
    return CPART(40 + s * 6)


def find_cell(C, vm, all_, pred):
    """(tab, page, slot, cell) of the first cell with pred(row, open)."""
    for t in range(10):
        for i in range(C['first'][t], C['first'][t + 1]):
            r = C['rows'][i]
            if pred(r, copen(vm, C, r['no'], all_)):
                k = i - C['first'][t]
                return t, k // 12, k % 12, i
    return None


def goto(t, p):
    """answers that bring the chart from its first page to (t, p): the tab, then 「다음 쪽」 p times."""
    return [CPART(10 + t)] + [CPART(34)] * p


def chart_flow_checks(cand, nm, X, C, counts):
    """V43 (click on a locked cell) / V44 (page, replay path) / V46 (parts after every way out)."""
    mk = lambda: chart_vm(cand, nm, X)
    out = {}
    # 1 a locked cell: the notice, nothing opened, the chart goes on; then the close button
    vm = mk()
    chart_state(vm, X, C, 'partial')
    t, p, s, i = find_cell(C, vm, False, lambda r, op: not op)
    ds = chart_session(vm, 1, [CPART(10 + t)] + [2] * p + [box_of(s), OK, CPART(30)])
    kinds = [d.get('kind', 'dialog') for d in ds]
    assert kinds.count('chart') == 3 + p and ko(ds[-2]['title']) == T_LOCKED, ('V43 locked cell', kinds, ko(ds[-2]['title'])[:30])
    assert not vm.replays and not any(c[0] == 'KR_T8CharDatePage' for c in vm.calls), 'V43 a locked cell opened something'
    assert vm.parts[VM.TITLE_ROOT]['show'] == 1
    check_dialog(ds[-2], counts)
    counts['V43_locked_click_notice'] += 1
    out['locked'] = C['rows'][i]['no']
    # 2 an open scene cell (unlocked by 「전체 개방」): the scene page (chart branch), 이 장면 재생 -> the chart closes -> replay
    for ctx in (1, 2):
        vm = mk()
        chart_state(vm, X, C, 'none')
        t, p, s, i = find_cell(C, vm, True, lambda r, op: op and not r['card'] and not r['noplay'])
        no = C['rows'][i]['no']
        ds = chart_session(vm, ctx, goto(t, p) + [box_of(s), 13], all_=True)
        pg = ds[-1]
        want = '〓' + ko(vm.run('KR_T19EvHead', [no])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [no])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [no])) \
            + '\n' + C_STATE['all'] + '\n' + C_PLAY_NOTE
        assert ko(pg['title']) == want, ('V44 scene page (chart branch)', ko(pg['title']), want)
        assert [(i_, ko(x)) for i_, x, _, _ in pg['items']] == [(13, PLAY), (0, '돌아가기')], pg['items']
        check_dialog(pg, counts)
        rp = vm.replays
        assert len(rp) == 1 and rp[0]['no'] == no and rp[0]['ctx'] == ctx, ('V44 replay', rp)
        assert rp[0]['ours'] == [] and rp[0]['open'] == '' and rp[0]['unwind'] == '' and rp[0]['t9play'] == '' and not rp[0]['dialog_open'], ('V44 state at the replay', rp[0])
        if ctx == 1:
            assert rp[0]['title_root_show'] == 0 and vm.parts[VM.TITLE_ROOT]['show'] == 1, ('V44 the title root around the replay', rp[0]['title_root_show'])
        else:
            assert rp[0]['title_root_show'] == 1, 'V44 the home replay touched the title root'
        assert not any(c[0] in ('LSys3xScript::Prepare', 'LSys3xScript::RunEvent') for c in vm.calls if isinstance(c, tuple)), 'V44 the r18 path ran'
        assert vm.v('Play') == '' and vm.v('Playing') == '', 'V44 the r18 play slot was set'
        assert (vm.msg_of[no] in vm.flags) or vm.msg_of[no] < 0, 'V44 model: the replay marks the scene read'
        counts['V44_replays_ctx%d' % ctx] += 1
        out['replay_ctx%d' % ctx] = no
    # 3 an open bundle card: the card page (chart branch), 단계 고르기 (global marks), a stage, 이 장면 재생 -> that stage replays;
    #   a locked stage of an open card offers no replay (the lock holds inside the card too)
    vm = mk()
    chart_state(vm, X, C, 'none')
    cand_cards = [r for r in C['rows'] if r['card'] and X['cards'][r['ref'] - 100000]['size'] >= 3 and not r['noplay']]
    r = cand_cards[0]
    k = r['ref'] - 100000
    card = X['cards'][k]
    st = card['stages']
    vm.flags = {vm.msg_of[st[0]], vm.msg_of[st[1]]} - {-1}          # entry and stage 2 read, stage 3 not
    i = C['rows'].index(r)
    t = r['tab']
    kk = i - C['first'][t]
    stage3 = st[2]
    ds = chart_session(vm, 2, goto(t, kk // 12) + [box_of(kk % 12), 14, 102, 0, 101, 13])
    cardpg, stagepg, lockedpg, stagepg2, openpg = [d for d in ds if d.get('kind') != 'chart']
    wantc = '〓' + ko(vm.run('KR_T19CardHead', [k])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [st[0]])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [st[0]])) \
        + '\n' + C_STATE[1] + '\n¶단계 %d/%d 읽음' % (sum(1 for x in st if cstate(vm, C, x) == 1), len(st)) + '\n' + C_PLAY_NOTE
    assert ko(cardpg['title']) == wantc, ('V44 card page (chart branch)', ko(cardpg['title']), wantc)
    assert [i_ for i_, _, _, _ in cardpg['items']] == [13, 14, 0], cardpg['items']
    lines = ko(stagepg['title']).split('\n')
    assert lines[-1].startswith(C_LEGEND), ('V44 stage list legend (chart)', lines[-1])
    marks = [ko(x)[-1] for _, x, _, _ in stagepg['items'] if _ >= 100]
    assert marks[:3] == ['△', '△', '●'], ('V44 stage list marks (global)', marks[:3])
    assert [i_ for i_, _, _, _ in lockedpg['items']] == [0] and C_STATE[0] in ko(lockedpg['title']), ('V44 a locked stage offers play', lockedpg['items'])
    assert [i_ for i_, _, _, _ in openpg['items']] == [13, 0], openpg['items']
    assert len(vm.replays) == 1 and vm.replays[0]['no'] == st[1], ('V44 stage replay', vm.replays)
    for d in (cardpg, stagepg, lockedpg, openpg):
        check_dialog(d, counts)
    counts['V44_card_stage_paths'] += 1
    out['card'] = card['key']
    # 4 cancel (right click / space = 0) and the close button: no replay, no part, the chart state cleared
    for ans in ([0], [CPART(30)], [4, 4, 3, 1, 2, CPART(30)]):
        vm = mk()
        chart_state(vm, X, C, 'partial')
        chart_session(vm, 1, ans)
        assert not vm.replays
        counts['V46_ways_out'] += 1
    return out


def chart_confine_checks(cand, nm, X, C, counts):
    """V45: with the chart closed - and with a stale 「Open」 flag but no chart root - the calendar functions give what the r21
    candidate gives (same save state, same answers)."""
    r21 = L.R21 / 'candidate' / 'NightRemaster.ain'
    r21m = L.read_meta(L.R21 / 'work' / 'build' / 'candidate_meta.json')
    assert L.sha(r21) == L.BASE_AIN_SHA
    rnd = random.Random(45)
    regs = {e['fn'] for no, e in X['ev'].items() if rnd.random() < 0.4}
    flags = {e['m0'] for no, e in X['ev'].items() if e['m0'] is not None and rnd.random() < 0.5}
    sample_cards = list(range(0, len(X['cards']), 7))
    sample_scenes = sorted(X['ev'])[::23]

    def run_all(vm, stale):
        vm.registered, vm.flags = set(regs), set(flags)
        vm.mem_enabled = {(0, 0)}
        if stale:
            vm.vars['YoruKR.C.Open'] = '1'                     # a stale flag without the chart root
        vm.parts = {}
        vm.title_scene()
        res = []
        for k in sample_cards:
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            vm.vars['YoruKR.T9.Unwind'] = ''
            vm.vars['YoruKR.T9.Play'] = ''
            vm.cur = None
            vm.dialogs = []
            vm.script = [13]
            vm.run('KR_T9CardPage', [k, X['cards'][k]['month']])
            res.append(('card', k, [(ko(d['title']), [(i, ko(x), dis) for i, x, _, dis in d['items']]) for d in vm.dialogs], vm.v('Play'), vm.v('Unwind')))
        for no in sample_scenes:
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            vm.vars['YoruKR.T9.Unwind'] = ''
            vm.vars['YoruKR.T9.Play'] = ''
            vm.cur = None
            vm.dialogs = []
            vm.script = [13]
            vm.run('KR_T9EventPage', [no, ''])
            res.append(('scene', no, [(ko(d['title']), [(i, ko(x), dis) for i, x, _, dis in d['items']]) for d in vm.dialogs], vm.v('Play'), vm.v('Unwind')))
            res.append(('state', no, vm.run('KR_T9State', [no]), vm.run('KR_T9Seen', [no])))
        res.append(('legend', ko(vm.run('KR_T9Legend'))))
        return res
    ref = run_all(chart_vm(r21, r21m, X), False)
    for stale in (False, True):
        got = run_all(chart_vm(cand, nm, X), stale)
        diff = [(a, b) for a, b in zip(ref, got) if a != b]
        assert len(ref) == len(got) and not diff, ('V45 the calendar differs from r21' + (' with a stale flag' if stale else ''), diff[:2])
        counts['V45_calendar_equal_r21' + ('_stale_flag' if stale else '')] = len(ref)
    return dict(compared=len(ref), cards=len(sample_cards), scenes=len(sample_scenes))


def title_checks(cand, nm, X, C, counts):
    """V47: the title's poll (KR_CTitleTick every frame) and serve (KR_CTitleServe after the wait)."""
    mk = lambda: chart_vm(cand, nm, X)
    # idle: two existence checks a frame, the original IsClickConfig result passed on, no wait ended
    vm = mk()
    for cfg in (0, 1):
        vm.inputs['IsClickConfig'] = cfg
        vm.file_calls = []
        vm.ended = None
        r = vm.run('KR_CTitleTick')
        assert r == cfg and vm.ended is None and [op for op, _ in vm.file_calls] == ['exist', 'exist'], ('V47 idle title frame', r, vm.file_calls)
    vm.calls = []
    vm.run('KR_CTitleServe')
    assert [c for c in vm.calls if c[0] == '■方向キー処理／削除'] and not vm.file_calls[2:], 'V47 serve without a request touched the files'
    counts['V47_title_idle'] += 1
    # a request: the wait ends with KR_CCode, the frame answers false, the serve runs it (ctx 1)
    for cmd, answers, check in (('chart', [0], lambda v, ds: v.charts and v.charts[0]['ctx'] == '1'),
                                ('unlock_all', [OK], lambda v, ds: ko(ds[0]['title']) == '〓모드 메뉴\n†전체 개방: 안 본 이벤트도 열람·재생됩니다' and v.disk.get(CHART) == 'YoruKR.Chart.1\r\n1\r\n'),
                                ('unlock_revert', [OK], lambda v, ds: ko(ds[0]['title']) == T_REVERT and v.disk.get(CHART) == 'YoruKR.Chart.1\r\n0\r\n'),
                                ('reset_all', [NO], lambda v, ds: ko(ds[0]['title']) == T_RESET and MARKER not in v.disk),
                                ('reset_restore', [NO], lambda v, ds: ko(ds[0]['title']) == T_RESTORE and MARKER not in v.disk)):
        vm = mk()
        vm.title_scene()
        hook_request(vm, cmd)
        vm.inputs['IsClickConfig'] = 1
        vm.ended = None
        r = vm.run('KR_CTitleTick')
        assert r == 0 and vm.ended == C_CODE and vm.vars.get('YoruKR.C.TitleReq') == '1', ('V47 title tick with a request', cmd, r, vm.ended)
        vm.calls = []
        vm.dialogs = []
        vm.charts = []
        vm.script = list(answers)
        vm.run('KR_CTitleServe')
        assert vm.calls[0][0] == '■方向キー処理／削除', ('V47 the original call first', vm.calls[:2])
        assert REQ not in vm.disk and vm.vars.get('YoruKR.C.TitleReq') == '', ('V47 request not consumed', cmd)
        assert check(vm, [d for d in vm.dialogs if d.get('kind') != 'chart']), ('V47 command at the title', cmd)
        assert not vm.script
        counts['V47_title_commands'] += 1
    # reset_all 예 at the title: the marker, the .req, the exit (the same code as at home)
    vm = mk()
    hook_request(vm, 'reset_all')
    vm.run('KR_CTitleTick')
    vm.script = [YES]
    try:
        vm.run('KR_CTitleServe')
        raise AssertionError('V47 reset at the title did not exit')
    except VMExit as ex:
        assert ex.code == 0 and vm.disk.get(MARKER) == 'reset' and vm.disk.get(RESET_REQ) == 'reset'
    counts['V47_title_reset_exit'] += 1
    # a result and a request together: the result window first
    vm = mk()
    hook_result(vm, 'reset ok KR_reset_20260928_031500\r\n')
    hook_request(vm, 'unlock_all')
    vm.run('KR_CTitleTick')
    vm.dialogs = []
    vm.script = [OK, OK]
    vm.run('KR_CTitleServe')
    assert [ko(d['title']).split('\n')[0] for d in vm.dialogs] == [T_RESULT_HEAD, '〓모드 메뉴'], [ko(d['title'])[:12] for d in vm.dialogs]
    counts['V47_result_before_request'] += 1
    # an undeletable request: served once, then the title stops polling (the r21 「Off」 rule)
    vm = mk()
    vm.fail_delete = {REQ}
    hook_request(vm, 'unlock_revert')
    vm.run('KR_CTitleTick')
    vm.script = [OK]
    vm.run('KR_CTitleServe')
    assert vm.vars.get('YoruKR.M.Off') == '1'
    vm.file_calls = []
    vm.ended = None
    vm.run('KR_CTitleTick')
    assert not vm.file_calls and vm.ended is None, 'V47 the title polled after an undeletable request'
    counts['V47_undeletable_stops'] += 1
    return dict(commands=counts['V47_title_commands'])


def noplay_checks(cand, nm, X, C, counts):
    """V48: a not-playable scene: the cell note, no 이 장면 재생 on its page, KR_CRequest refuses (synthetic: every scene)."""
    real = [no for no, v in C['noplay'].items() if v]
    counts['V48_not_playable_real'] = len(real)
    every = op_replace('KR_CNoPlay', lambda o: o == ['PUSH', '0'], lambda o: ['PUSH', '1'], nth=0)
    vm = chart_vm(cand, nm, X, mutate=every)
    chart_state(vm, X, C, 'all')
    t, p, s, i = find_cell(C, vm, False, lambda r, op: op and not r['card'])
    no = C['rows'][i]['no']
    ds = chart_session(vm, 1, goto(t, p) + [box_of(s), 0, CPART(30)])
    pg = [d for d in ds if d.get('kind') != 'chart'][0]
    assert [i_ for i_, _, _, _ in pg['items']] == [0] and ko(pg['title']).endswith(C_NOPLAY_NOTE), ('V48 page of a not-playable scene', pg['items'], ko(pg['title'])[-20:])
    assert not vm.replays
    vm.vars['YoruKR.C.All'] = '1'
    vm.run('KR_CRequest', [no])
    assert vm.vars.get('YoruKR.C.Play', '') == '' and vm.vars.get('YoruKR.T9.Unwind', '') == '', 'V48 a request for a not-playable scene was taken'
    counts['V48_page_and_request'] += 1
    # the cell note (real table, or the synthetic one when nothing failed)
    rows = [r for r in C['rows'] if r['noplay']] or []
    for r in rows:
        assert r['cond'].split('\n')[-1] == C_NOTE
    counts['V48_cells_with_note'] = len(rows)
    return dict(real=real)
