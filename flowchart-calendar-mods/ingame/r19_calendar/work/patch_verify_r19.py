"""one-off: turn the copy of verify_calendar_r18.py into verify_calendar_r19.py (r19 static rules, names, rule 11, 31 defects)."""
from pathlib import Path

P = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r19_calendar\verify_calendar_r19.py')
s = P.read_text(encoding='utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:100], s.count(old))
    s = s.replace(old, new)


# ------------------------------------------------------------------ header
head_end = s.index('import sys, json, re, struct')
rep(s[:head_end], '''"""Claude Opus 5.5 (2026-09-27) r19: verification of the calendar candidate without the game (after verify_calendar_r18.py).

  python verify_calendar_r19.py              all checks (must pass)
  python verify_calendar_r19.py --selftest   all checks, then every check again against a planted defect (each must fail): 31
  python verify_calendar_r19.py --native     compare what the native probe logged (titles, rows, lists, the home panel, the
                                             sandbox before/after state, the lock pages) with the VM for the same save

Base = the r18 install (= the r18 candidate). r19 = names instead of E-numbers + affinity conditions (rule 11).
Static (bytes of base vs candidate, read only):
  S1 candidate = manifest; every base function entry identical except the five r19 forwarders (address only, new body in the
     appended code: KR_T18CardRow, KR_T18CardTitle, KR_T18EventTitle, KR_T9StagePage, KR_T9ChipPage); non-function metadata
     identical; every added function is KR_T19*
  S2 the WHOLE base CODE is unchanged; r15's nine swap sites and r18's RunEvent operand still hold their operands
  S3 MSG1 identical, STR0 prefix identical; PACT/EX not in the payload
  S4 user saves (copies, every RSM resume file): every saved frame resolves to the same function entry and the same bytes at its
     return address in the candidate; no frame inside a forwarded function
  S5 native opcode audit of the candidate against the runtime exe dispatch table
  S6 the six pinned functions (KR_T9HomeCasual, KR_T9HomeConfig, CheckGameSysButtons, Run, RunEvent, KR_T18RunSandboxed): index,
     address and every code byte identical to the base; the first five vs the r15 candidate differ only in r18's operand
  S7 KR_T18RunSandboxed has RunEvent's signature and KR_T9HomeCasual still calls it (r18 operand kept)
Extended VM (the candidate's own compiled bodies, engine calls modelled):
  V1-V20 r18's checks (tables, geometry, day cells, navigation, flows, seen states, counts, rows, panel, real saves, bars, lock,
      sandbox); the stage-page title and the lane rows now carry names
  V21 no E-number (E\\d{4,5}) and no word 「E번호」 in any title line or item of any page (every page walk, every scene page)
  V22 names unique on a page: list items (marks removed) unique in every dialog; card names unique per (month, lane)
  V23 name rules 1-8 recomputed here from schedule.json / labels.json / groups.json (independent of the chart builder):
      ordinals, partners, slots, dungeon places; samples per rule for the handoff table
  V24 rule 11: every event with an affinity condition shows 「<인물> 친밀도 v 이상/미만/…」 on its card page and scene page
      「언제」 line; lane rows whose 「언제」 carries it show it (full or 「쿄카 30+」)
  V25 in-game name tables = the published PC chart v2 data (ev nm/ns, cards nm/tail, drawer display order)
  V26 in-game 「언제」 lines = the chart's 「언제」 strings with each E-number replaced by that scene's name (no other change)
"""
''')
rep('import r18lib as L\n', 'import r19lib as L\n')
rep('''FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
           'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
           'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
''', '''FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
           'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}          # r19 forwarders
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}      # in the base since r18
E_RE = re.compile(r'E\\d{4,5}')
WHEN_CONT = '\\n†　　　'
PARTY_KR = ['이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세']
NAME_KIND = {'prio': '우선 대화', 'after': '특훈 뒤 대화', 'turned': '반한 뒤 대화', 'invite': '초대'}
''')

# ------------------------------------------------------------------ expectations: names
rep('''        data = V2.build(str(L.TMP / 'chart_v2_from_r18_verify.html'))''',
    '''        data = V2.build(str(L.TMP / 'chart_v2_from_r19_verify.html'))''')
rep('''        cards.append(dict(key=c['key'], month=int(c['page']), lane=LANES.index(c['lane']), day=pl.get('d', 0), slot=pl.get('slot', 0) or 0,
                          size=c['n'], entry=c['entry'], stages=[r[0] for r in c['rows'] if r[6]]))''',
    '''        cards.append(dict(key=c['key'], month=int(c['page']), lane=LANES.index(c['lane']), day=pl.get('d', 0), slot=pl.get('slot', 0) or 0,
                          size=c['n'], entry=c['entry'], stages=[r[0] for r in c['rows'] if r[6]], nm=c['nm'], tail=c['tail'],
                          rows=c['rows'], pl=pl))''')
rep('''        chips.append(dict(id=ch['id'], month=month, lane=lane, kind=KINDS.index(ch['kind']), scenes=[x[0] for x in ch['order'] if x[4]]))''',
    '''        chips.append(dict(id=ch['id'], month=month, lane=lane, kind=KINDS.index(ch['kind']), scenes=[x[0] for x in ch['order'] if x[4]],
                          order=ch['order'], slots=ch.get('slots') or {}))''')
rep('''    return dict(data=data, ev=ev, cards=cards, chips=chips, w1={p['m']: p['w1'] for p in data['pages'] if p.get('m')}, mlen=V2.MLEN,
                out=out, panel_groups=groups)''',
    '''    sch = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    feel = {}
    for e in sch['events']:
        full, short = [], []
        for t in e['triggers']:
            if t.get('feeling_gate'):
                full += V2.feeling_tokens(t, data['persons'])
                short += V2.feeling_tokens(t, data['persons'], short=True)
        if full:
            feel[e['id']] = (full, short)
    return dict(data=data, ev=ev, cards=cards, chips=chips, w1={p['m']: p['w1'] for p in data['pages'] if p.get('m')}, mlen=V2.MLEN,
                out=out, panel_groups=groups, sch={e['id']: e for e in sch['events']}, feel=feel,
                labels=json.loads((L.FLOW / 'graph' / 'labels.json').read_text('utf8')),
                memory=json.loads((L.FLOW / 'graph' / 'memory.json').read_text('utf8')))''')

# ------------------------------------------------------------------ static checks (r19)
st0 = s.index('def swap_of(man):')
st1 = s.index('# ============================================================== VM checks')
rep(s[st0:st1], '''def r18_site():
    s = L.readj(L.R18 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(s) == 1 and s[0]['function'] == L.SWAP_OWNER and s[0]['original'] == L.SWAP_OLD and s[0]['replacement'] == L.SANDBOX, s
    return s[0]


def static_checks(base, cand, man, m, nm, counts, mutate_bytes=None, mutate_meta=None, parts=('S1', 'S2', 'S3', 'S4', 'S6', 'S7')):
    bb = base.read_bytes()
    cb = cand.read_bytes()
    if mutate_bytes:
        cb = mutate_bytes(cb)
    if mutate_meta:
        nm = mutate_meta(copy.deepcopy(nm))
    assert L.sha_bytes(cb) == man['files']['NightRemaster.ain']['sha256'] or mutate_bytes, 'candidate != manifest'
    old = L.unpack(bb)
    new = L.unpack(cb)
    oldn = struct.unpack_from('<I', old, 12)[0]
    fw = {L.fid_of(m, n) for n in FORWARD}
    swap = r18_site()
    sb = L.fid_of(nm, L.SANDBOX)
    if 'S1' in parts:
        for f in m['functions']:
            g = nm['functions'][f['index']]
            if f['index'] in fw:
                assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, f['name']
                assert g['address'] >= oldn, ('forwarder not in the appended code', f['name'])
            else:
                assert g == f, ('base function entry changed', f['index'], f['name'])
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
        assert all(n.startswith('KR_T19') for n in man['added_functions']), 'added functions must all be KR_T19*'
        assert not any(L.raw_symbol(nm, f['index']).startswith(('KR_T16', 'KR_T17')) for f in nm['functions']), 'r16/r17 names in the candidate'
        counts['S1_metadata'] += 1
    if 'S2' in parts:
        diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
        assert not diff, ('base CODE bytes changed', diff[:8])
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s_ in rman['same_length_sites'] + [swap]:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap missing in the base', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap site no longer applied', s_['function'], s_['replacement'])
        assert bytes(new[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, sb), 'KR_T9HomeCasual no longer calls KR_T18RunSandboxed'
        counts['S2_same_length_sites_kept'] = len(rman['same_length_sites']) + 1
        counts['S2_base_code_bytes'] = oldn
        counts['S2_base_code_bytes_changed'] = len(diff)
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed']
        counts['S3_text'] += 1
    if 'S6' in parts:
        rv = L.versions(L.base_paths()['raw'])
        starts = sorted({v['start'] for vs in rv.values() for v in vs})
        ccode = new[16:16 + struct.unpack_from('<I', new, 12)[0]]
        bcode = old[16:16 + oldn]
        ra = L.R15 / 'candidate' / 'NightRemaster.ain'
        rraw = L.unpack(ra.read_bytes())
        rcode = rraw[16:16 + struct.unpack_from('<I', rraw, 12)[0]]
        rm = L.read_meta(L.R15 / 'work' / 'build' / 'candidate_meta.json')
        for name in L.PINNED_ALL:
            i = L.fid_of(m, name)
            f = m['functions'][i]
            assert nm['functions'][i] == f, ('pinned function entry changed', name)
            j = bisect.bisect_right(starts, f['address'])
            end = starts[j] - 6 if j < len(starts) else oldn
            lo = f['address'] - 6
            assert ccode[lo:end] == bcode[lo:end], ('pinned code changed', name)
            if name in L.PINNED:
                assert rm['functions'][L.fid_of(rm, name)] == f, ('pinned entry differs from r15', name)
                differ = [lo + k for k in range(end - lo) if rcode[lo + k] != bcode[lo + k]]
                if name == L.SWAP_OWNER:
                    assert differ and set(differ) <= set(range(swap['site'] + 2, swap['site'] + 6)), ('KR_T9HomeCasual differs from r15 beyond r18\\'s operand', differ[:8])
                else:
                    assert not differ, ('pinned code differs from r15', name)
            counts['S6_pinned_bytes'] += end - lo
        counts['S6_pinned_functions'] = len(L.PINNED_ALL)
    if 'S7' in parts:
        g, r = nm['functions'][sb], nm['functions'][L.fid_of(nm, L.SWAP_OLD)]
        assert g['arguments'] == r['arguments'] == [] and g['return-type'] == r['return-type'] == [47, -1, 0, None], 'sandbox signature'
        assert man['pinned_functions'][L.SANDBOX]['index'] == sb and man['pinned_functions'][L.SANDBOX]['address'] == g['address']
        counts['S7_sandbox_signature_equal_RunEvent'] = 1
    if 'S4' not in parts:
        return []
    vers = L.versions(L.base_paths()['raw'])
    bycrc = collections.defaultdict(list)
    for f in m['functions']:
        bycrc[f['crc'] & 0xffffffff].append(f)
    frames = []
    live = 0
    for name, path in L.resume_saves().items():
        row_ = L.save_records(path)
        assert row_ is not None, name
        for rr in [row_['ip']] + row_['returns']:
            if rr['address'] == -1:
                continue
            start = rr['address'] - rr['offset']
            choices = [f for f in bycrc[rr['crc']] if rr['name'].startswith(L.raw_symbol(m, f['index']) + '(')
                       and any(v['start'] == start for v in vers[f['index']])]
            assert len(choices) == 1, (name, rr)
            f = choices[0]
            assert f['index'] not in fw or start != f['address'], ('a saved frame is inside a forwarded function', name)
            assert nm['functions'][f['index']] == f or f['index'] in fw, ('saved frame function moved', name, f['name'])
            ad = rr['address']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes(new[16 + ad:16 + ad + 6]), ('saved return bytes differ', name, rr['name'][:40], hex(ad))
            live += int(start == f['address'])
            frames.append(dict(file=name, fid=f['index'], offset=rr['offset'], live=start == f['address'], function=L.raw_symbol(m, f['index'])))
    counts['S4_saves'] = len({x['file'] for x in frames})
    counts['S4_frames'] = len(frames)
    counts['S4_frames_in_live_versions'] = live
    counts['S4_frames_in_KR_T9HomeCasual'] = sum(1 for x in frames if x['function'] == 'KR_T9HomeCasual')
    counts['S4_frames_in_KR_T18RunSandboxed'] = sum(1 for x in frames if x['function'] == L.SANDBOX)
    counts['S4_frames_in_forwarded'] = sum(1 for x in frames if x['function'] in FORWARD)
    return frames


''')

# ------------------------------------------------------------------ V25 tables = chart names
rep('''    counts['V1_panel_outside'] = len(X['out'])
''', '''    counts['V1_panel_outside'] = len(X['out'])
    # V25: the in-game name tables = the published chart v2 data (the chart builder's names, baked, not recomputed)
    for k, c in enumerate(cards):
        assert ko(vm.run('KR_T19CardHead', [k])) == c['nm'], ('card name table differs from the chart', c['key'])
        assert ko(vm.run('KR_T19CardTail', [k])) == c['tail'], ('card tail table differs from the chart', c['key'])
    for no, e in ev.items():
        assert ko(vm.run('KR_T19EvHead', [no])) == e['nm'], ('scene name table differs from the chart', no)
        assert ko(vm.run('KR_T19EvShort', [no])) == e['ns'], ('list line table differs from the chart', no)
    j = 0
    for i, ch in enumerate(chips):
        want = list(ch['scenes']) if KINDS[ch['kind']] == 'mem' else sorted(ch['scenes'])
        got = [vm.run('KR_T19SceneAt', [j + x]) for x in range(len(want))]
        assert got == want, ('drawer display order', ch['id'], got[:5], want[:5])
        assert vm.run('KR_T19ChipCols', [i]) in (2, 3)
        j += len(want)
    assert vm.run('KR_T19SceneAt', [j]) == -1 and j == 760
    pub = json.loads(re.search(r'<script type="application/json" id="yoru-data">(.*?)</script>',
                               (L.FLOW / 'chart' / 'yoru_flowchart_v2.html').read_text('utf8'), re.S).group(1))
    assert {int(k): (v['nm'], v['ns']) for k, v in pub['ev'].items()} == {no: (e['nm'], e['ns']) for no, e in ev.items()}, 'the published chart has other names'
    assert [(c['key'], c['nm'], c['tail']) for c in pub['cards']] == [(c['key'], c['nm'], c['tail']) for c in X['data']['cards']]
    counts['V25_name_tables_equal_chart'] = len(ev) + len(cards)
''')

# ------------------------------------------------------------------ V21 / V22 in check_dialog
rep('''    for x in lines + [ko(t) for _, t, _, _ in d['items']]:
        assert not re.search(r'[0-9A-Za-z]…', x), ('a number or event id cut by 「…」', x)''',
    '''    for x in lines + [ko(t) for _, t, _, _ in d['items']]:
        assert not E_RE.search(x) and 'E번호' not in x, ('V21: an E-number left on a page', x)
        counts['V21_texts_without_e_numbers'] += 1
        assert not re.search(r'[0-9A-Za-z]…', x), ('a number or event id cut by 「…」', x)''')
rep('''    counts['V2_dialogs'] += 1
''', '''    counts['V2_dialogs'] += 1
    keys = [re.sub(r'[●○△]', '', ko(t)).strip() for iid, t, _, _ in d['items'] if iid not in (0, 11, 12)]
    assert len(keys) == len(set(keys)), ('V22: two items with the same name on one page', [k for k, n in collections.Counter(keys).items() if n > 1][:3])
    counts['V22_items_unique_on_page'] += len(keys)
''')

# ------------------------------------------------------------------ lists: stage / drawer items are the names
rep('''    for k, c in enumerate(cards):
        walk('KR_T9CardPage', [k, c['month']], 1)
        if c['size'] > 1:
            walk('KR_T9StagePage', [k, c['month']], math.ceil(c['size'] / 30))
    for i, ch in enumerate(chips):
        walk('KR_T9ChipPage', [i], math.ceil(len(ch['scenes']) / 30))''',
    '''    ev = X['ev']

    def mark(no):
        if ev[no]['fn'] in regs:
            return '○'
        if ev[no]['m0'] is not None and ev[no]['m0'] in vm.flags:
            return '△'
        return '●'
    for k, c in enumerate(cards):
        ds = walk('KR_T9CardPage', [k, c['month']], 1)
        assert ko(ds[0]['title']).split('\\n')[0] == '〓' + c['nm'], ('card page first line', c['key'])
        if c['size'] > 1:
            ds = walk('KR_T9StagePage', [k, c['month']], math.ceil(c['size'] / 30))
            got = [ko(t) for d in ds for iid, t, _, _ in d['items'] if iid >= 100]
            assert got == ['%s %s' % (ev[s]['ns'], mark(s)) for s in c['stages']], ('stage list lines', c['key'], got[:3])
            assert all(ko(d['title']).split('\\n')[0] == '〓' + c['nm'] and d['cols'] == 3 for d in ds), ('stage list title / columns', c['key'])
            counts['V2_stage_lists'] += 1
    for i, ch in enumerate(chips):
        ds = walk('KR_T9ChipPage', [i], math.ceil(len(ch['scenes']) / 30))
        order = list(ch['scenes']) if KINDS[ch['kind']] == 'mem' else sorted(ch['scenes'])
        got = [ko(t) for d in ds for iid, t, _, _ in d['items'] if iid >= 100]
        assert got == ['%s %s' % (ev[s]['ns'], mark(s)) for s in order], ('drawer list lines', ch['id'], got[:3])
        assert all(d['cols'] == 3 for d in ds), ('drawer list columns', ch['id'])
        counts['V2_drawer_lists'] += 1''')

# ------------------------------------------------------------------ scene pages: first line, 「언제」 (V24, V26)
rep('''def event_pages(vm, X, counts):
    for no in sorted(X['ev']):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'C'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, proxy('6월 · 호시카와 · 특훈 뒤 대화')])
        check_dialog(vm.dialogs[0], counts)
    counts['V2_event_pages'] = len(X['ev'])''',
    '''def when_of(title):
    """the 「언제」 text of a card / scene page title (one or two lines)."""
    lines = title.split('\\n')
    i = next(i for i, l in enumerate(lines) if l.startswith('†언제　'))
    text = lines[i][len('†언제　'):]
    if i + 1 < len(lines) and lines[i + 1].startswith('†　　　'):
        text += WHEN_CONT + lines[i + 1][len('†　　　'):]
    return text


def stage_home(X):
    out = {}
    for c in X['cards']:
        for i, s in enumerate(c['stages'], start=1):
            out[s] = (c['key'], i)
    return out


def when_check(X, no, text, counts):
    """V26: the in-game 「언제」 = the chart's 「언제」 strings, each E-number replaced by that scene's name (its list name when it is
    a stage of the same bundle, 「이 장면」 for itself; a memory slot playing the scene itself drops 「 · 원본 …」), cut only
    between whole tokens (「 …」) and never cutting an affinity text (V24)."""
    e = X['ev'][no]
    home = stage_home(X)

    def refs(target):
        opts = {X['ev'][target]['nr']}
        if target == no:
            opts.add('이 장면')
        a, b = home.get(target), home.get(no)
        if a and b and a[0] == b[0]:
            opts.add(X['ev'][target]['nk'].split(' · ')[0])
        return opts
    allowed = []
    for w in e['when']:
        w = re.sub(r' · 원본 E%05d$' % no, '', w)
        for tok in re.split(r' · | / ', w):
            alts = ['']
            pos = 0
            for z in E_RE.finditer(tok):
                alts = [a + tok[pos:z.start()] + r for a in alts for r in refs(int(z.group(0)[1:]))]
                pos = z.end()
            allowed += [a + tok[pos:] for a in alts]
    flat = text.replace(WHEN_CONT, ' · ')
    toks = [t for t in re.split(r' · | / ', flat) if t]
    if toks and toks[-1].endswith(' …'):
        toks[-1] = toks[-1][:-2]
    if toks and toks[-1] == '…':
        toks.pop()
    if text != '부르는 자리 없음':
        bad = [t for t in toks if t not in allowed]
        assert not bad, ('V26: a 「언제」 token that is not the chart\\'s', no, bad[:2], text)
    for a in X['feel'].get(no, ([], []))[0]:
        assert a in flat, ('V24: affinity text missing on the 「언제」 line', no, a, text)
        counts['V24_affinity_on_pages'] += 1
    counts['V26_when_tokens'] += len(toks)


def event_pages(vm, X, counts):
    for no in sorted(X['ev']):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'C'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, proxy('6월 · 호시카와 · 특훈 뒤 대화')])
        d = vm.dialogs[0]
        check_dialog(d, counts)
        title = ko(d['title'])
        assert title.split('\\n')[0] == '〓' + X['ev'][no]['nm'], ('scene page first line', no, title.split('\\n')[0])
        when_check(X, no, when_of(title), counts)
    counts['V2_event_pages'] = len(X['ev'])


def affinity_checks(vm, X, counts):
    """V24: card pages of the affinity events' cards and every scene page of an affinity event carry the full text; lane rows
    whose chart 「언제」 (first string) carries it show the full or the short form."""
    ev = X['ev']
    for k, c in enumerate(X['cards']):
        for s in c['stages']:
            full, short = X['feel'].get(s, ([], []))
            if not full:
                continue
            vm.reset()
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            if s == c['entry']:
                vm.script = [0]
                vm.run('KR_T9CardPage', [k, c['month']])
                t = when_of(ko(vm.dialogs[0]['title'])).replace(WHEN_CONT, ' · ')
                assert all(a in t for a in full), ('V24: affinity missing on the card page', c['key'], full, t)
                counts['V24_card_pages'] += 1
                row_ = ko(vm.run('KR_T9CardRow', [k, c['month']]))
                w0 = (ev[s]['when'] or [''])[0]
                for a, b in zip(full, short):
                    if a in w0:
                        assert a in row_ or b in row_, ('V24: affinity missing on the lane row', c['key'], a, row_)
                        counts['V24_lane_rows'] += 1
    for no, (full, short) in X['feel'].items():
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'P'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, ''])
        t = when_of(ko(vm.dialogs[0]['title'])).replace(WHEN_CONT, ' · ')
        assert all(a in t for a in full), ('V24: affinity missing on the scene page', no, full, t)
        counts['V24_scene_pages'] += 1
    counts['V24_affinity_events'] = len(X['feel'])''')

# ------------------------------------------------------------------ lock checks: the stage-page first line is the name
rep('''            assert ko(d['title']).split('\\n')[0] == '〓%s · %s 묶음 · %d단계' % ('E%05d' % c['stages'][i], 'E%05d' % c['entry'], i + 1), ko(d['title']).split('\\n')[0]''',
    '''            assert ko(d['title']).split('\\n')[0] == '〓' + ev[c['stages'][i]]['nm'], ko(d['title']).split('\\n')[0]''')

# ------------------------------------------------------------------ V12 rows (r19)
r0 = s.index('def row_checks(vm, X, counts):')
r1 = s.index('def bar_checks(vm, counts):')
rep(s[r0:r1], '''def row_checks(vm, X, counts):
    """V12 (r19): lane row = when + mark + condition + stage count + name tail; the tails sit exactly on the cards whose name
    without the tail collides in (month, lane); rows unique in (month, lane); the condition is the chart's first 「언제」 text
    without the row's date/slot, names for E-numbers, affinity kept (V24)."""
    cards = X['cards']
    vm.registered = set()
    rows = collections.defaultdict(list)
    heads = collections.defaultdict(list)
    tails = []
    for k, c in enumerate(cards):
        t = ko(vm.run('KR_T9CardRow', [k, c['month']]))
        when = ko(vm.run('KR_T9CardWhen', [k, c['month']]))
        cond = ko(vm.run('KR_T19CardCond', [k]))
        want = when + ' ●' + ((' ' + cond) if cond else '') + ((' (%d단계)' % c['size']) if c['size'] > 1 else '') + ((' ' + c['tail']) if c['tail'] else '')
        assert t == want, (c['key'], t, want)
        assert len(t) <= 38, t
        assert not E_RE.search(t) and 'E번호' not in t, t
        if c['tail']:
            tails.append(k)
        rows[(c['month'], c['lane'])].append(re.sub(r'[●○△]', '', t))
        heads[(c['month'], c['lane'])].append((k, c['nm'].replace(' · ' + c['tail'], '') if c['tail'] else c['nm']))
    dup = {key: [x for x, n in collections.Counter(v).items() if n > 1] for key, v in rows.items()}
    dup = {key: v for key, v in dup.items() if v}
    assert not dup, ('lane rows collide', dup)
    want = []
    for key, v in heads.items():
        cnt = collections.Counter(h for _, h in v)
        want += [k for k, h in v if cnt[h] > 1]
    assert sorted(tails) == sorted(want), ('tails not exactly on the colliding cards', sorted(set(tails) ^ set(want)))
    names = collections.defaultdict(list)
    for c in cards:
        names[(c['month'], c['lane'])].append(c['nm'])
    assert all(len(v) == len(set(v)) for v in names.values()), 'V22: two cards with the same name in one lane'
    counts['V12_tailed_rows'] = len(tails)
    counts['V12_duplicate_rows_after'] = 0
    counts['V12_rows'] = len(cards)


''')

# ------------------------------------------------------------------ V23 name rules (independent recomputation)
n0 = s.index('# ============================================================== native comparison (--native)')
rep(s[n0:n0 + len('# ============================================================== native comparison (--native)')],
    """# ============================================================== V23: name rules recomputed from the raw data
def josa_wa(name):
    c = name[-1]
    return name + ('과' if '가' <= c <= '힣' and (ord(c) - 0xAC00) % 28 else '와')


def name_rule_checks(vm, X, counts, samples=None):
    \"\"\"Rules 1-8 recomputed from schedule.json / labels.json / groups.json (the chart builder is not called): the in-game
    tables (KR_T19EvShort / EvHead / CardHead / CardTail, read in the VM) must say the same. Returns samples per rule.\"\"\"
    sch, lab = X['sch'], X['labels']
    persons = {p['no']: p['kr'] or p['jp'] for p in json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))['persons']}
    party = set(PARTY_KR)
    out = collections.defaultdict(list)

    def speakers(no):
        return [p.strip('\\u3000 ') for s_ in lab['cards'][str(no)].get('speakers') or [] for p in s_.split('＆')]

    def companion(no):
        return next((p for p in speakers(no) if p in party), None)

    def short(no):
        return ko(vm.run('KR_T19EvShort', [no]))

    def head(no):
        return ko(vm.run('KR_T19EvHead', [no]))

    def put(rule, no, got, want, data):
        assert got == want, ('V23 rule %s' % rule, no, got, want)
        out[rule].append(dict(event='E%05d' % no, name=got, data=data))
        counts['V23_rule_%s' % rule] += 1
    # rules 5, 6, 8: drawers
    for ch in X['chips']:
        kind = KINDS[ch['kind']]
        ents = sorted(ch['scenes'])
        lane = ch['lane']
        if kind in NAME_KIND:
            for k, no in enumerate(ents, start=1):
                put('6', no, short(no), '%d번째' % k, '%s · %d월 · %s · 이벤트 번호 %d번째로 작음(서랍 %d장)' % (LANE_KR[lane], ch['month'], NAME_KIND[kind], k, len(ents)))
                assert head(no).endswith('%s %d번째' % (NAME_KIND[kind], k)), ('V23 rule 6 head', no, head(no))
        elif kind == 'walk':
            seen = collections.Counter()
            for no in ents:
                e = sch[no]
                me = lane + 1 if 1 <= lane <= 7 else None
                other = [x for x in (e['person'], e['person2']) if x and x != me and x != 1]
                who = josa_wa(persons[other[0]]) if other else ('단둘이' if me else '혼자')
                seen[who] += 1
                put('5', no, short(no), '%s %d번째' % (who, seen[who]),
                    'person %s · person2 %s · 레인 %s · 같은 짝 안 %d번째' % (e['person'], e['person2'], LANE_KR[lane] if lane < 9 else lane, seen[who]))
                assert head(no).endswith('%s 동행 %d번째' % (who, seen[who])), ('V23 rule 5 head', no, head(no))
        elif kind == 'unused':
            for k, no in enumerate(ents, start=1):
                put('8', no, short(no), '미사용 %d' % k, 'category unknown · 번호 순 %d' % k)
        elif kind == 'etc':
            for no in ents:
                put('8', no, short(no), '일요일 시간 끝 처리', 'source 残時間終わり処理／日曜')
        elif kind == 'mem':
            pg = lane - 8
            slot = {}
            for no in ch['scenes']:
                for t in sch[no]['triggers']:
                    if t['kind'] == 'memory_replay':
                        slot[no] = t['slot']
                        assert t['page'] == pg
            for no in ch['scenes']:
                if no in slot:
                    src = sch[no].get('replay_of')
                    date = ''
                    for c in X['cards']:
                        if src in c['stages'] and c['day']:
                            date = ' (%d/%d)' % (c['month'], c['day'])
                    put('7', no, head(no), '회상 · 그 밖 · 회상 %d쪽 %d번%s' % (pg, slot[no], date),
                        'memory_replay page %d slot %d · replay_of E%05d%s' % (pg, slot[no], src or 0, date))
    # rules 1-4: cards
    dungeons = lab['dungeons']
    for k, c in enumerate(X['cards']):
        nm = ko(vm.run('KR_T19CardHead', [k]))
        when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
        if c['slot']:
            when += ' ' + SLOT_KR[c['slot']]
        tail = ko(vm.run('KR_T19CardTail', [k]))
        if c['lane'] == 0 and c['day']:
            want = ' · '.join([when, '본편'] + ([tail] if tail else []) + (['%d단계' % c['size']] if c['size'] > 1 else []))
            put('1', c['entry'], nm, want, '본편 카드 · 날짜 %s · 단계 %d' % (when, c['size']))
        if c['lane'] == 8:
            e = sch[c['entry']]
            srcs = [t['source'] for t in e['triggers'] if t['kind'] == 'dungeon']
            srcs = [x for x in srcs if '@RunEvent' in x] + [x for x in srcs if '@RunEvent' not in x]
            z = re.match(r'^C_EventDungeon\\d{4}@RunEvent(\\w+)$', srcs[0]) if srcs else None
            if z and srcs[0] in dungeons:
                xx = z.group(1)
                m_ = re.match(r'^B(\\d+)$', xx)
                suf = ('사건 %d' % int(m_.group(1))) if m_ else {'R1': '보스', 'Exit': '출구', 'Entrance': '입구', 'B': '사건', 'R': ''}.get(xx, xx)
                place = dungeons[srcs[0]]['kr']
                assert (' · ' + place + (' · ' + suf if suf else '')) in nm, ('V23 rule 4', c['key'], nm)
                out['4'].append(dict(event='E%05d' % c['entry'], name=nm, data='%s → %s · %s' % (srcs[0], place, suf or '(없음)')))
                counts['V23_rule_4'] += 1
        # rule 3: the tail = companion + ordinal inside that companion, among the cards whose name without the tail collides
        if tail:
            grp = sorted((x for x in X['cards'] if x['month'] == c['month'] and x['lane'] == c['lane']
                          and (x['nm'].replace(' · ' + x['tail'], '') if x['tail'] else x['nm']) == nm.replace(' · ' + tail, '')), key=lambda x: x['entry'])
            def pre(no):
                who = companion(no)
                return josa_wa(who) if who else ('혼자' if speakers(no) == ['료'] else '장면')
            same = [x['entry'] for x in grp if pre(x['entry']) == pre(c['entry'])]
            put('3', c['entry'], tail, '%s %d' % (pre(c['entry']), same.index(c['entry']) + 1),
                '겹치는 카드 %d장 · 화자 %s' % (len(grp), '/'.join(speakers(c['entry'])[:3])))
        # rule 2: bundle stages (the list line)
        if c['size'] > 1:
            stages = [r for r in c['rows'] if r[6]]
            for i, r in enumerate(stages, start=1):
                no = r[0]
                via = r[3] if r[2] == 'answer' else None
                who = companion(no)
                got = short(no)
                assert got.startswith('%d. ' % i), ('V23 rule 2 number', no, got)
                if via:
                    assert ('갈래 %d' % via) in got, ('V23 rule 2 branch', no, got)
                if who:
                    assert josa_wa(who) in got, ('V23 rule 2 companion', no, got)
                if len(out['2']) < 40:
                    out['2'].append(dict(event='E%05d' % no, name=got, data='%s %d단계 · via %s · 화자 %s' % (c['key'], i, via or '-', '/'.join(speakers(no)[:3]))))
                counts['V23_rule_2'] += 1
    return {k: v for k, v in sorted(out.items())}


# ============================================================== native comparison (--native)""")

# ------------------------------------------------------------------ defects
rep('''    ('V12 one E-number tail removed', 'rows', None),''', '''    ('V12 one name tail removed (two lane rows collide)', 'rows', None),''')
rep('''    # r18 (VM)''', '''    # r18 (VM)''')
d0 = s.index("def table_defect(X):")
rep(s[d0:s.index("def r16_day_alias():")], '''def table_defect(X):
    no = X['cards'][10]['entry']
    return ('V1 table: one card entry wrong', 'tables', op_replace('KR_T9CardEntry', lambda o: o == ['PUSH', str(no)], lambda o: ['PUSH', str(no + 1)]))


def tail_defect(vm):
    """「one name tail removed」: KR_T19CardTail returns "" for the first tailed card (its row collides with a sibling)."""
    k = next(k for k in range(200) if ko(vm.run('KR_T19CardTail', [k])))
    txt = vm.run('KR_T19CardTail', [k])
    return op_replace('KR_T19CardTail', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == txt, lambda o: list(sp(''))), k


def leaf_replace(fn, no, new_text):
    """replace the string a generated table returns for key `no` (the S_PUSH right after its `PUSH no; EQUALE; IFZ`)."""
    def mut(ops):
        hits = [i for i in range(len(ops) - 4) if ops[i] == ['PUSH', str(no)] and ops[i + 1] == ['EQUALE'] and ops[i + 2][0] == 'IFZ'
                and ops[i + 3][0] == 'S_PUSH']
        if len(hits) != 1:
            raise RuntimeError(('defect could not be planted: no table leaf', fn, no, len(hits)))
        ops[hits[0] + 3] = list(sp(new_text))
        return ops
    return {fn: mut}


def r19_defects(vm, X):
    """The four r19 defects: an E-number left, a duplicate name on one page, a wrong ordinal, an affinity text dropped."""
    ev = X['ev']
    no1 = min(ev)
    e_left = leaf_replace('KR_T19EvHead', no1, vm.run('KR_T19EvHead', [no1]) + proxy(' · ') + 'E%05d' % no1)
    ch = next(ch for ch in X['chips'] if KINDS[ch['kind']] == 'after' and len(ch['scenes']) >= 3)
    a, b = sorted(ch['scenes'])[:2]
    dup = leaf_replace('KR_T19EvShort', b, vm.run('KR_T19EvShort', [a]))
    wch = next(ch for ch in X['chips'] if KINDS[ch['kind']] == 'walk' and len(ch['scenes']) >= 3)
    last = sorted(wch['scenes'])[-1]
    tl = ko(vm.run('KR_T19EvShort', [last]))
    z = re.search(r'(\d+)번째$', tl)
    wrong = tl[:z.start()] + '%d번째' % (int(z.group(1)) + 1)
    ordinal = leaf_replace('KR_T19EvShort', last, proxy(wrong))
    no4 = 30157
    t4 = ko(vm.run('KR_T19WhenFix', [no4]))
    assert '이즈미 친밀도 50 미만' in t4, t4
    drop = leaf_replace('KR_T19WhenFix', no4, proxy(t4.replace(' · 이즈미 친밀도 50 미만', '')))
    return [('V21 one E-number left on a scene page (E%05d)' % no1, 'names_e', e_left),
            ('V22 two lines with the same name in one drawer list (%s: E%05d copies E%05d)' % (ch['id'], b, a), 'names_dup', dup),
            ('V23 a wrong ordinal in a walk drawer (E%05d: %s -> %s)' % (last, tl, wrong), 'names_rule', ordinal),
            ('V24 the affinity condition dropped from a card page (E%05d)' % no4, 'affinity', drop)]


''')
rep('''def old_row_alias(m):
    """「one old-form drawer row left」: the 회상 · 그 밖 page calls r15's KR_T9ChipRow body (base AIN, 「이름 n (본 것 k)」)."""
    d = L.WORK / 'vm' / 'base'
    d.mkdir(parents=True, exist_ok=True)
    path = d / 'KR_T9ChipRow_r15.jam'
    if not path.exists():
        L.cmd('ain', 'dump', '--function', 'KR_T9ChipRow', '-o', path, L.base_dir() / 'NightRemaster.ain')''',
    '''def old_row_alias(m):
    """「one old-form drawer row left」: the 회상 · 그 밖 page calls r15's KR_T9ChipRow body (the r15 candidate AIN, read only:
    「이름 n (본 것 k)」; in the base the r15 index holds r18's forwarder)."""
    d = L.WORK / 'vm' / 'r15'
    d.mkdir(parents=True, exist_ok=True)
    path = d / 'KR_T9ChipRow_r15.jam'
    if not path.exists():
        assert L.sha(L.R15 / 'candidate' / 'NightRemaster.ain') == L.R15_AIN_SHA
        L.cmd('ain', 'dump', '--function', 'KR_T9ChipRow', '-o', path, L.R15 / 'candidate' / 'NightRemaster.ain')''')

# ------------------------------------------------------------------ main
rep('''    man = L.readj(O / 'manifest.json')
    bd = L.base_dir()
    base = bd / 'NightRemaster.ain'
    cand = O / 'NightRemaster.ain'
    assert L.sha(base) == L.BASE_AIN_SHA and L.sha(cand) == man['files']['NightRemaster.ain']['sha256']
    m = L.read_meta(bd / 'meta.json')''',
    '''    man = L.readj(O / 'manifest.json')
    bp = L.base_paths()
    base = bp['ain']
    cand = O / 'NightRemaster.ain'
    assert L.sha(base) == L.BASE_AIN_SHA and L.sha(cand) == man['files']['NightRemaster.ain']['sha256']
    m = L.read_meta(bp['meta'])''')
rep('''        result = dict(schema='yoru-calendar-r18.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, counts=dict(counts))''',
    '''        result = dict(schema='yoru-calendar-r19.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, counts=dict(counts))''')
rep('''    lock_checks(vm, X, counts)
    sandbox = sandbox_checks(vm, X, counts)
    real = real_save_checks(vm, X, counts)
    result = dict(schema='yoru-calendar-r18.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,''',
    '''    lock_checks(vm, X, counts)
    sandbox = sandbox_checks(vm, X, counts)
    real = real_save_checks(vm, X, counts)
    vm.registered = regs
    affinity_checks(vm, X, counts)
    rules = name_rule_checks(vm, X, counts)
    result = dict(schema='yoru-calendar-r19.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,''')
rep('''                  panel=panel, sandbox=sandbox, real_saves=real)
    print(json.dumps({k: v for k, v in result.items() if k not in ('real_saves',)}, ensure_ascii=False, indent=1, default=str))''',
    '''                  panel=panel, sandbox=sandbox, real_saves=real, name_rule_samples=rules)
    print(json.dumps({k: v for k, v in result.items() if k not in ('real_saves', 'name_rule_samples')}, ensure_ascii=False, indent=1, default=str))''')
rep('''                      lock=lambda v: lock_checks(v, X, collections.Counter()),
                      sandbox=lambda v: sandbox_checks(v, X, collections.Counter()))
        tail_mut, tail_k = tail_defect(vm)
        for label, group, mutation in DEFECTS + [table_defect(X)]:''',
    '''                      lock=lambda v: lock_checks(v, X, collections.Counter()),
                      sandbox=lambda v: sandbox_checks(v, X, collections.Counter()),
                      names_e=lambda v: event_pages(v, X, collections.Counter()),
                      names_dup=lambda v: pages_all(v, X, collections.Counter(), 'partial'),
                      names_rule=lambda v: name_rule_checks(v, X, collections.Counter()),
                      affinity=lambda v: affinity_checks(v, X, collections.Counter()))
        tail_mut, tail_k = tail_defect(vm)
        for label, group, mutation in DEFECTS + [table_defect(X)] + r19_defects(vm, X):''')
rep('''        def touch_pinned_beyond_operand(b):
            raw = bytearray(L.unpack(b))
            site = swap_of(man)['site']
            assert bytes(raw[16 + site + 8:16 + site + 10]) == struct.pack('<H', 0) and raw[16 + site + 10] == 1, 'PUSH 1 after the POP'
            raw[16 + site + 10] ^= 1                                                       # PUSH 1 -> PUSH 0 (■ＡＤＶ消し's first argument)
            return L.pack(bytes(raw), b[:8])''',
    '''        def touch_pinned_beyond_operand(b):
            raw = bytearray(L.unpack(b))
            site = r18_site()['site']
            assert bytes(raw[16 + site + 8:16 + site + 10]) == struct.pack('<H', 0) and raw[16 + site + 10] == 1, 'PUSH 1 after the POP'
            raw[16 + site + 10] ^= 1                                                       # PUSH 1 -> PUSH 0 (■ＡＤＶ消し's first argument)
            return L.pack(bytes(raw), b[:8])''')
rep('''                                ('S6 a byte of the pinned KR_T9HomeCasual other than the RunEvent operand changed', dict(mutate_bytes=touch_pinned_beyond_operand), 'S6')]:''',
    '''                                ('S6 a byte of the pinned KR_T9HomeCasual changed (after r18\\'s operand)', dict(mutate_bytes=touch_pinned_beyond_operand), 'S6')]:''')
rep('''        assert len(planted) == 27, len(planted)''', '''        assert len(planted) == 31, len(planted)''')
s = s.replace("L.base_dir() / 'NightRemaster.ain'", "L.base_paths()['ain']")
assert 'base_dir' not in s, [l for l in s.splitlines() if 'base_dir' in l][:5]
P.write_text(s, encoding='utf-8', newline='\n')
print('ok')
