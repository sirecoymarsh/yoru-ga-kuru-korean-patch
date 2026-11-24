"""Claude Opus 5.5 (2026-09-27) r19: in-game event calendar = the r18 install + human-readable names instead of the internal
event numbers (E#####) on every calendar page + the affinity conditions on the 「언제」 lines (rule 11). Base = the r18 install
(current.json CALENDAR_R18_INSTALLED_NATIVE_PASS, AIN 1f60b685… = the r18 candidate).

  python build_calendar_r19.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/status/manifest = r19lib BASE_*, P: free space >= 10 GB, r18 installed
     (evidence/calendar_r18 journal COMMITTED, the r18 candidate = the runtime AIN), the r18 candidate files unchanged.
  2. data: chart/build_chart_v2.build() as a module (= the published chart v2 HTML, names included). The names are the
     chart's (event_names); this build only bakes them. The r15 tables inside the base must still be what today's data gives
     except the 「언제」 text / lane-row condition of the events whose trigger gained an affinity condition (rule 11).
  3. r19 tables: card heads / tails / lane-row conditions, scene heads / list lines, the 「언제」 lines that differ from the
     r15 table (E##### -> names, affinity kept), the drawer display order, list columns.
  4. alice ain edit --jaf (declare the KR_T19* functions) -> dump -> native_lower -> alice ain edit --jam with the lowered bodies
     AND a one-call forwarder body for five existing functions (same index, same arguments/return, new address):
       KR_T18CardRow -> KR_T19CardRow, KR_T18CardTitle -> KR_T19CardTitle, KR_T18EventTitle -> KR_T19EventTitle,
       KR_T9StagePage -> KR_T19StagePage, KR_T9ChipPage -> KR_T19ChipPage
     No same-length operand changes (r15's nine and r18's one stay as they are in the base).
  5. invariance: every base function entry identical except the five forwarded ones (address only); other metadata keys,
     the WHOLE old CODE, MSG1, STR0 prefix identical; the six pinned functions (r18 list + KR_T18RunSandboxed) keep entry
     and every code byte; r15's nine sites and r18's operand still applied; native opcode audit of every live function.
  6. end gate: the runtime hashes are read again. If Codex installed something meanwhile the candidate is DISCARDED
     (files removed, work/REBASE_NEEDED.json written) and the build exits 3 - rebuild on the new base, never install it.
PACT and EX are not touched. Nothing is written outside r19_calendar\\ (runtime, saves, Codex root, r15-r18: read only).
"""
import sys, io, json, re, struct, shutil, collections, contextlib, datetime, os
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r19lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_calendar_r19.jaf'
LANES = ['main', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'dungeon']
LANE_KR = ['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전']
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
SLOT_KR = {1: '아침', 2: '밤', 3: '낮', 4: '저녁'}
SLOT_RANK = {1: 0, 3: 1, 4: 2, 2: 3, 0: 9}          # 아침 < 낮 < 저녁 < 밤, 시간대 없음은 뒤로
LIMIT = 38
WHEN_BUDGET = 34
CAL_START, CAL_END = (4, 9), (11, 17)
COL_CAP = {3: 13, 2: 20}                              # full-width units an item may use (1280 px, 28 px a glyph, 52 px margin)
E_RE = re.compile(r'E(\d{4,5})')

R15_SITES = 9
FORWARD = {            # existing function (index kept) -> r19 body (same arguments and return type)
    'KR_T18CardRow': 'KR_T19CardRow',             # lane rows: name tails instead of E-number tails
    'KR_T18CardTitle': 'KR_T19CardTitle',         # card page: first line + 「언제」
    'KR_T18EventTitle': 'KR_T19EventTitle',       # scene page: first line + 「언제」
    'KR_T9StagePage': 'KR_T19StagePage',          # stage list
    'KR_T9ChipPage': 'KR_T19ChipPage',            # drawer scene list
}
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
TOTAL_EVENTS, PANEL_EVENTS = 1164, 1043


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- base
def runtime_now():
    ptr, rt = L.runtime()
    got = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'NightRemasterPact.afa', 'NightRemasterEX.ex']}
    return ptr, rt, got


def base_is_current(ptr, got):
    return (got['NightRemaster.ain'] == L.BASE_AIN_SHA and got['NightRemasterPact.afa'] == L.BASE_PACT_SHA
            and got['NightRemasterEX.ex'] == L.BASE_EX_SHA and ptr['status'] == L.BASE_STATUS
            and ptr['manifest_sha256'] == L.BASE_MANIFEST_SHA)


def code_of(ain_bytes):
    raw = L.unpack(ain_bytes)
    n = struct.unpack_from('<I', raw, 12)[0]
    return raw, raw[16:16 + n], n


def gates():
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase r19lib BASE_* on the new runtime first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    j = L.readj(L.CODEX / 'evidence' / 'calendar_r18' / 'journal.json')
    assert j['status'] == 'COMMITTED' and j['after']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r18 not installed as expected', j['status'])
    bp = L.base_paths()
    assert L.sha(bp['ain']) == L.BASE_AIN_SHA
    return ptr, rt, bp, free


def site_list():
    """r15's nine and r18's one same-length operand sites (bytes the base must keep)."""
    r15 = L.readj(L.R15 / 'candidate' / 'manifest.json')['same_length_sites']
    r18 = L.readj(L.R18 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(r15) == R15_SITES and len(r18) == 1
    return [dict(s, by='r15') for s in r15] + [dict(s, by='r18') for s in r18]


def sites_applied(code, sites):
    for s in sites:
        assert code[s['site']:s['site'] + 6].hex() == s['after'], ('same-length site not applied', s['by'], s['function'], s.get('replacement'))
    return len(sites)


def body_bytes(code, starts, address, limit):
    import bisect
    i = bisect.bisect_right(starts, address)
    end = starts[i] - 6 if i < len(starts) else limit
    return code[address - 6:end]


# ---------------------------------------------------------------- data
def chart_data():
    sys.path.insert(0, str(L.FLOW / 'chart'))
    import build_chart_v2 as V2
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data = V2.build(str(L.TMP / 'chart_v2_from_r19_build.html'))
    html = (L.FLOW / 'chart' / 'yoru_flowchart_v2.html').read_text('utf8')
    z = re.search(r'<script type="application/json" id="yoru-data">(.*?)</script>', html, re.S)
    pub = json.loads(z.group(1))

    def cards(d):
        return [(c['key'], c['entry'], c['members'], c['lane'], c['page'], c['pl'], c['n'], c['nm'], c['tail'], c['ref']) for c in d['cards']]

    def chips(d):
        return [(ch['id'], ch['page'], ch['lane'], ch['kind'], ch['entries'], [x[0] for x in ch['order']]) for ch in d['chips']]

    def names(d):
        return {k: (v['nm'], v['ns'], v['nr'], v.get('nk'), v['when']) for k, v in d['ev'].items()}
    diff = dict(cards=cards(data) == cards(pub), chips=chips(data) == chips(pub), join=data['join'] == pub['join'],
                pages=[p.get('w1') for p in data['pages']] == [p.get('w1') for p in pub['pages']], names=names(data) == names(pub))
    assert all(diff.values()), ('PC chart v2 and the in-game tables would diverge — rebuild chart/yoru_flowchart_v2.html first', diff)
    return data, V2, dict(published_chart_sha256=L.sha(L.FLOW / 'chart' / 'yoru_flowchart_v2.html'), same_as_published=diff,
                          builder_sha256=L.sha(L.FLOW / 'chart' / 'build_chart_v2.py'),
                          schedule_sha256=L.sha(L.FLOW / 'graph' / 'schedule.json'))


def label_name(no):
    return ('E%04d' % no) if no == 1706 else ('E%05d' % no)


def adjust(s):
    return {'E01707': '01707', 'E02132': '02132'}.get(s, s)


def cut(s, n):
    if len(s) <= n:
        return s
    return s[:max(0, n - 1)].rstrip(' ·,') + '…'


def who_text(e, budget):
    names = []
    for w in e['who']:
        parts = [p.strip('\u3000 ') for p in w.split('＆')]
        names.append('＆'.join('주인공' if p == '료' else p for p in parts))
    more = e.get('wmore') or 0
    if not names:
        return '화자 표시 없음'
    while True:
        t = ', '.join(names) + (' 외 %d' % more if more else '')
        if len(t) <= budget or len(names) == 1:
            return cut(t, budget)
        names.pop()
        more += 1


def fit_tokens(tokens, budget, sep=' · ', keep=()):
    """Longest run of whole tokens within budget; 「 …」 marks tokens left out. r19: tokens in `keep` (affinity) are never
    dropped - other tokens are dropped from the end first."""
    if len(sep.join(tokens)) <= budget:
        return sep.join(tokens)
    if keep and any(t in keep for t in tokens):
        chosen = [i for i, t in enumerate(tokens) if t in keep]
        for i, t in enumerate(tokens):
            if i in chosen:
                continue
            trial = sorted(chosen + [i])
            if len(sep.join(tokens[j] for j in trial)) + 2 <= budget:
                chosen = trial
        text = sep.join(tokens[j] for j in chosen)
        if len(chosen) < len(tokens):
            text += ' …'
        assert len(text) <= budget, ('affinity tokens alone exceed the budget', tokens, budget)
        return text
    out = []
    for t in tokens:
        if len(sep.join(out + [t])) + 2 <= budget:
            out.append(t)
        else:
            break
    if not out:
        return cut(tokens[0], budget)
    return sep.join(out) + ' …'


WHEN_CONT = '\n†　　　'


def when_text(e, budget):
    """r15's 「언제」 text (unchanged): one or two lines of <= budget characters, cut only between tokens."""
    ws = [w for w in e['when'] if w]
    if not ws:
        return '부르는 자리 없음'
    two = ' / '.join(ws[:2])
    text = two if len(ws) >= 2 and len(two) <= budget else ws[0]
    if len(text) <= budget:
        return text
    toks = text.split(' · ')
    first = []
    while toks and len(' · '.join(first + [toks[0]])) <= budget:
        first.append(toks.pop(0))
    if not first:
        return cut(text, budget)
    return ' · '.join(first) + WHEN_CONT + fit_tokens(toks, budget)


DATE = re.compile(r'^\d{1,2}/\d{1,2}$')


def card_cond(when0, pl):
    """r15's lane-row condition tokens from a 「언제」 text (the date/slot the row already shows removed)."""
    w = when0 or ''
    if 'd' not in pl:
        return [t.strip() for t in w.split(' · ') if t.strip()]
    out = []
    for tok in w.split(' · '):
        tok = tok.strip()
        if DATE.match(tok) or tok in SLOT_KR.values():
            continue
        tok = re.sub(r'^(\d{1,2}/\d{1,2}) 하루만$', '하루만', tok)
        tok = re.sub(r'^(\d{1,2}/\d{1,2}) 부터$', lambda z: '' if z.group(1) == '%d/%d' % (pl['m'], pl['d']) else tok, tok)
        tok = re.sub(r'^특별한 날 \d{1,2}/\d{1,2}$', '특별한 날', tok)
        if tok:
            out.append(tok)
    return out


def r15_tables(data, V2, m, vers):
    """r15's table computation, unchanged (the base's r15 tables must still be today's data)."""
    ev = data['ev']
    evn = {int(k): v for k, v in ev.items()}
    byname = {}
    for f in m['functions']:
        byname.setdefault(L.raw_symbol(m, f['index']), []).append(f['index'])
    for no, e in evn.items():
        assert e['fn'] == 'ＥＶ／元／' + adjust(label_name(no)), (no, e['fn'])
        ids = byname.get(e['fn'], [])
        assert len(ids) == 1, (no, e['fn'], ids)
        v = L.live_version(m, vers, ids[0])
        nums = [int(op.split()[1], 16) for _, op in v['ops'] if op.startswith('MSG ')]
        if e['lines']:
            assert nums and nums[0] == e['m0'], (no, e['m0'], nums[:2])
        else:
            assert not nums and e['m0'] is None, no
    lane_ix = {k: i for i, k in enumerate(LANES)}
    cards = []
    for c in data['cards']:
        pl = c['pl']
        mo = int(c['page'])
        day = pl.get('d', 0)
        slot = pl.get('slot', 0) or 0
        stages = [r[0] for r in c['rows'] if r[6]]
        assert sorted(stages) == sorted(c['members']) and len(stages) == c['n'] and stages[0] == c['entry'], c['key']
        cards.append(dict(key=c['key'], month=mo, lane=lane_ix[c['lane']], day=day, slot=slot, size=c['n'], entry=c['entry'],
                          stages=stages, pl=pl, type=c['type']))
    cards.sort(key=lambda x: (x['month'], x['lane'], x['day'] if x['day'] else 99, SLOT_RANK[x['slot']], x['key']))
    stage_tab = []
    for k, c in enumerate(cards):
        c['k'] = k
        c['stage0'] = len(stage_tab)
        stage_tab += c['stages']
        when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
        if c['slot']:
            when += ' ' + SLOT_KR[c['slot']]
        suffix = (' (%d단계)' % c['size']) if c['size'] > 1 else ''
        budget = LIMIT - len(when) - 3 - len(suffix)
        toks = card_cond((evn[c['entry']]['when'] or [''])[0], c['pl'])
        c['cond'] = fit_tokens(toks, budget) if toks else ''
        c['row_max'] = len(when) + 3 + len(c['cond']) + len(suffix)
    card_range = {}
    for mo in range(4, 12):
        ks = [c['k'] for c in cards if c['month'] == mo]
        card_range[mo] = (min(ks), max(ks) + 1) if ks else (0, 0)
    chips = []
    scene_tab = []
    for ch in data['chips']:
        page = 12 if ch['page'] == 'mem' else int(ch['page'])
        if ch['lane'] in lane_ix:
            lane = lane_ix[ch['lane']]
        elif ch['lane'].startswith('mem'):
            lane = 8 + int(ch['lane'][3:])
        else:
            lane = 16
        kind = KINDS.index(ch['kind'])
        order = [x[0] for x in ch['order'] if x[4]]
        chips.append(dict(id=ch['id'], month=page, lane=lane, kind=kind, size=len(order), scene0=len(scene_tab), scenes=order))
        scene_tab += order
    for i, ch in enumerate(chips):
        ch['c'] = i
    chip_range = {}
    for mo in range(4, 13):
        cs = [ch['c'] for ch in chips if ch['month'] == mo]
        chip_range[mo] = (min(cs), max(cs) + 1) if cs else (0, 0)
    assert sorted(scene_tab + stage_tab) == sorted(evn), 'every event exactly once in a card or a drawer'
    evtab = {}
    for no, e in evn.items():
        evtab[no] = dict(msg=e['m0'] if e['m0'] is not None else -1, when=when_text(e, WHEN_BUDGET), who=who_text(e, WHEN_BUDGET), cat=e['cat'])
    w1 = {p['m']: p['w1'] for p in data['pages'] if p.get('m')}
    assert (V2.CAL_START, V2.CAL_END) == (CAL_START, CAL_END)
    return dict(cards=cards, stages=stage_tab, card_range=card_range, chips=chips, scenes=scene_tab, chip_range=chip_range,
                events=evtab, w1=w1, mlen=dict(V2.MLEN))


def feeling_events(V2, data):
    """event -> (full affinity texts, short texts) for the triggers that carry `feeling_gate` (rule 11), per 「언제」 string."""
    sch = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    persons = data['persons']
    out = {}
    for e in sch['events']:
        full, short = [], []
        for t in e['triggers']:
            if t.get('feeling_gate'):
                full += V2.feeling_tokens(t, persons)
                short += V2.feeling_tokens(t, persons, short=True)
        if full:
            out[e['id']] = (full, short)
    return out


def r15_same(T, feel):
    """The r15 tables live in the base: today's data must produce them, except the 「언제」 text and the lane-row condition
    of the events whose trigger gained an affinity condition (rule 11; those go through the r19 tables)."""
    r15 = L.readj(L.R15 / 'work' / 'build' / 'tables.json')
    now = json.loads(json.dumps(dict(cards=T['cards'], chips=T['chips'], stages=T['stages'], scenes=T['scenes'],
                                     events={str(k): v for k, v in T['events'].items()}, w1=T['w1'], mlen=T['mlen'],
                                     card_range={str(k): v for k, v in T['card_range'].items()},
                                     chip_range={str(k): v for k, v in T['chip_range'].items()}), ensure_ascii=False))
    diff = []
    for key in now:
        if key == 'events':
            for no, v in now[key].items():
                for f in v:
                    if v[f] != r15[key][no][f] and not (f == 'when' and int(no) in feel):
                        diff.append(('events', no, f))
        elif key == 'cards':
            for a, b in zip(now[key], r15[key]):
                for f in a:
                    if a[f] != b[f] and not (f in ('cond', 'row_max') and a['entry'] in feel):
                        diff.append(('cards', a['key'], f))
            assert len(now[key]) == len(r15[key])
        elif now[key] != r15.get(key):
            diff.append(key)
    assert not diff, ('chart data moved since r15 was built beyond rule 11: the r15 tables in the base are stale', diff[:6])
    changed_when = sorted(int(no) for no, v in now['events'].items() if v['when'] != r15['events'][no]['when'])
    changed_cond = sorted(a['key'] for a, b in zip(now['cards'], r15['cards']) if a['cond'] != b['cond'])
    return r15, dict(r15_tables_sha256=L.sha(L.R15 / 'work' / 'build' / 'tables.json'), identical_except_rule11=True,
                     rule11_when_changed=len(changed_when), rule11_cond_changed=changed_cond)


# ---------------------------------------------------------------- r19 tables
def r19_tables(T, data, feel, r15):
    evn = {int(k): v for k, v in data['ev'].items()}
    cards_by_key = {c['key']: c for c in data['cards']}
    stage_of = {}                                          # event -> (card key, stage index 1..)
    for c in T['cards']:
        for i, s in enumerate(c['stages'], start=1):
            stage_of[s] = (c['key'], i)

    def ref(target, ctx):
        """a reference to event `target` inside the 「언제」 line of event `ctx` (names from the chart builder)."""
        if target == ctx:
            return '이 장면'
        a, b = stage_of.get(target), stage_of.get(ctx)
        if a and b and a[0] == b[0]:
            return evn[target]['nk'].split(' · ')[0]           # 「2단계」 / 「2단계 갈래 1」 in the same bundle
        return evn[target]['nr']

    def subst(text, ctx):
        # a memory slot that plays the original event itself: 「회상 3쪽 3칸 · 원본 E30061」 on E30061 -> 「회상 3쪽 3칸」
        text = re.sub(r' · 원본 %s$' % re.escape(label_name(ctx)), '', text)
        return E_RE.sub(lambda z: ref(int(z.group(1)), ctx), text)

    # ---- 「언제」 (card / scene pages)
    whens, fix = {}, {}
    for no, e in evn.items():
        ws = [subst(w, no) for w in e['when'] if w]
        full = feel.get(no, ([], []))[0]
        if not ws:
            text = '부르는 자리 없음'
        else:
            carry = [i for i, w in enumerate(ws) if any(a in w for a in full)]
            if carry and carry[0] > 0:
                text = ws[0] + ' / ' + ws[carry[0]]
            else:
                two = ' / '.join(ws[:2])
                text = two if len(ws) >= 2 and len(two) <= WHEN_BUDGET else ws[0]
            if len(text) > WHEN_BUDGET:
                toks = text.split(' · ')
                first = []
                while toks and len(' · '.join(first + [toks[0]])) <= WHEN_BUDGET:
                    first.append(toks.pop(0))
                if not first:
                    text = cut(text, WHEN_BUDGET)
                else:
                    text = ' · '.join(first) + WHEN_CONT + fit_tokens(toks, WHEN_BUDGET, keep=set(full))
        for a in full:
            assert a in text.replace(WHEN_CONT, ' · '), ('rule 11: affinity text missing on the 「언제」 line', no, a, text)
        assert not E_RE.search(text) and 'E번호' not in text, (no, text)
        for line in text.split('\n'):
            assert len(line.lstrip('†　')) <= WHEN_BUDGET, (no, line)
        whens[no] = text
        if text != r15['events'][str(no)]['when']:
            fix[no] = text
    # ---- lane rows: condition (E-free, affinity kept or shortened), name tail
    rows = collections.defaultdict(list)
    conds, tails, heads = {}, {}, {}
    for c in T['cards']:
        dc = cards_by_key[c['key']]
        heads[c['k']] = dc['nm']
        tails[c['k']] = dc['tail']
        when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
        if c['slot']:
            when += ' ' + SLOT_KR[c['slot']]
        suffix = (' (%d단계)' % c['size']) if c['size'] > 1 else ''
        tail = (' ' + dc['tail']) if dc['tail'] else ''
        budget = LIMIT - len(when) - 3 - len(suffix) - len(tail)
        w0 = subst((evn[c['entry']]['when'] or [''])[0], c['entry'])
        toks = card_cond(w0, c['pl'])
        full, short = feel.get(c['entry'], ([], []))
        fa = [a for a in full if a in toks]
        cond = ' · '.join(toks)
        if len(cond) > budget:
            # rule 11: the full affinity text stays when it fits (other tokens go first); 「쿄카 30+」 only when it cannot
            sm = dict(zip(full, short))
            if len(' · '.join(fa)) + (2 if len(fa) < len(toks) else 0) <= budget:
                cond = fit_tokens(toks, budget, keep=set(fa))
            else:
                toks2 = [sm.get(t, t) for t in toks]
                cond = fit_tokens(toks2, budget, keep={sm[a] for a in fa})
        assert all((a in cond) or (dict(zip(full, short))[a] in cond) for a in fa), ('rule 11 on the lane row', c['key'], cond)
        assert not E_RE.search(cond) and 'E번호' not in cond, (c['key'], cond)
        conds[c['k']] = cond
        row = when + ' ●' + ((' ' + cond) if cond else '') + suffix + tail
        assert len(row) <= LIMIT, (c['key'], row)
        rows[(c['month'], c['lane'])].append(row)
    dup = {k: [t for t, n in collections.Counter(v).items() if n > 1] for k, v in rows.items()}
    dup = {k: v for k, v in dup.items() if v}
    assert not dup, ('lane rows still collide after the name tails', dup)
    # ---- scene heads / list lines, drawer display order, columns
    ev_head = {no: evn[no]['nm'] for no in evn}
    ev_short = {no: evn[no]['ns'] for no in evn}
    for no in evn:
        for t in (ev_head[no], ev_short[no]):
            assert not E_RE.search(t) and 'E번호' not in t, (no, t)
        assert len(ev_head[no]) <= LIMIT - 1, (no, ev_head[no])
    order = []
    chip_cols = {}
    for ch in T['chips']:
        sc = list(ch['scenes'])
        if KINDS[ch['kind']] not in ('mem',):
            sc = sorted(sc)                                     # n번째 · 미사용 n: the number order the names count in
        assert sorted(sc) == sorted(ch['scenes'])
        order += sc
        items = [ev_short[s] + ' ●' for s in sc]
        assert len(items) == len(set(items)), ('drawer list lines collide', ch['id'])
        widest = max(units(t) for t in items)
        chip_cols[ch['c']] = 3 if widest <= COL_CAP[3] else 2
        assert widest <= COL_CAP[chip_cols[ch['c']]], ('drawer list line too wide even for two columns', ch['id'], widest)
    stage_cols = {}
    for c in T['cards']:
        items = [ev_short[s] + ' ●' for s in c['stages']]
        assert len(items) == len(set(items)), ('stage list lines collide', c['key'])
        if c['size'] > 1:
            for i, s in enumerate(c['stages'], start=1):
                assert ev_short[s].startswith('%d. ' % i) or ev_short[s] == '%d.' % i, (c['key'], i, ev_short[s])
        widest = max(units(t) for t in items)
        stage_cols[c['k']] = 3 if widest <= COL_CAP[3] else 2
        assert widest <= COL_CAP[stage_cols[c['k']]], ('stage list line too wide even for two columns', c['key'], widest)
    assert len(order) == len(T['scenes']) == 760
    info = dict(when_fixed=len(fix), when_fixed_e_refs=sum(1 for no in fix if E_RE.search(r15['events'][str(no)]['when'])),
                when_fixed_rule11=sorted(no for no in fix if no in feel), tails=sum(1 for t in tails.values() if t),
                lane_rows_unique=True, widest_list_units=max(max(units(ev_short[s] + ' ●') for s in evn), 0),
                stage_lists_two_columns=sorted(k for k, v in stage_cols.items() if v == 2),
                drawer_lists_two_columns=sorted(c for c, v in chip_cols.items() if v == 2),
                affinity_events=len(feel), longest_head=max(len(h) for h in ev_head.values()),
                longest_row=max(len(r) for v in rows.values() for r in v))
    return dict(heads=heads, tails=tails, conds=conds, ev_head=ev_head, ev_short=ev_short, when_fix=fix, whens=whens,
                order=order, stage_cols=stage_cols, chip_cols=chip_cols, rows=rows), info


def units(t):
    """Glyph width in full-width units: ASCII (digits, spaces, /, parentheses, %) draws half width."""
    return sum(0.5 if ord(ch) < 0x80 else 1.0 for ch in t)


# ---------------------------------------------------------------- jaf generation
def q(s):
    return json.dumps(s, ensure_ascii=False)


def tree(ret, name, var, pairs, default):
    pairs = sorted(pairs)
    keys = [k for k, _ in pairs]
    assert len(keys) == len(set(keys)), name
    lines = [f'{ret} {name}(int {var}) {{']

    def rec(lo, hi, ind):
        if hi - lo <= 6:
            for k, v in pairs[lo:hi]:
                lines.append(f'{ind}if ({var} == {k}) return {v};')
            return
        mid = (lo + hi) // 2
        lines.append(f'{ind}if ({var} < {pairs[mid][0]}) {{')
        rec(lo, mid, ind + '    ')
        lines.append(f'{ind}}}')
        lines.append(f'{ind}else {{')
        rec(mid, hi, ind + '    ')
        lines.append(f'{ind}}}')
    rec(0, len(pairs), '    ')
    lines.append(f'    return {default};')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def gen_tables(R):
    out = [tree('string', 'KR_T19CardHead', 'k', [(k, q(v)) for k, v in R['heads'].items()], '""'),
           tree('string', 'KR_T19CardTail', 'k', [(k, q(v)) for k, v in R['tails'].items() if v], '""'),
           tree('string', 'KR_T19CardCond', 'k', [(k, q(v)) for k, v in R['conds'].items() if v], '""'),
           tree('string', 'KR_T19EvHead', 'no', [(k, q(v)) for k, v in R['ev_head'].items()], '""'),
           tree('string', 'KR_T19EvShort', 'no', [(k, q(v)) for k, v in R['ev_short'].items()], '""'),
           '// r15 표(KR_T9EvWhen)와 다른 「언제」만: E번호 → 이름, 친밀도 조건(규칙 11)\n'
           + tree('string', 'KR_T19WhenFix', 'no', [(k, q(v)) for k, v in R['when_fix'].items()], '""'),
           tree('int', 'KR_T19SceneAt', 'j', list(enumerate(R['order'])), -1),
           tree('int', 'KR_T19StageCols', 'k', [(k, v) for k, v in R['stage_cols'].items() if v != 3], 3),
           tree('int', 'KR_T19ChipCols', 'c', [(c, v) for c, v in R['chip_cols'].items() if v != 3], 3)]
    return '\n'.join(out)


def check_alphabet(texts):
    enc_ok = L.proxy_alphabet()
    carrier = {0x9D, 0x9E, 0x9F} | set(range(0xE0, 0xEB))
    bad = collections.Counter()
    for t in texts:
        for ch in t:
            if ch in enc_ok or ch in '\n':
                continue
            if '\uac00' <= ch <= '\ud7a3':
                bad[ch] += 1
                continue
            try:
                b = ch.encode('cp932')
            except UnicodeEncodeError:
                bad[ch] += 1
                continue
            if len(b) == 2 and b[0] in carrier:
                bad[ch] += 1
    return dict(bad)


def jaf_strings(src):
    return [json.loads(z) for z in re.findall(r'"(?:[^"\\]|\\.)*"', src)]


# ---------------------------------------------------------------- compile and patch
def sig(f):
    return ([a['type'] for a in f['arguments']], f['return-type'])


def forwarder(m, fid, target):
    f = m['functions'][fid]
    assert all(a['type'][0] in (10, 12, 47) for a in f['arguments']), ('forwarders pass int/bool/string arguments only', f['name'])
    assert f['return-type'][0] in (0, 10, 12), ('forwarder return type', f['name'], f['return-type'])
    body = ''.join(f"\t.LOCALREF {a['name']}\n" + ('\tA_REF\n' if a['type'][0] == 12 else '') for a in f['arguments'])
    return f"FUNC {fid}\n{body}\tCALLFUNC {target}\n\tRETURN\nENDFUNC {L.raw_symbol(m, fid)}\n"


def compile_and_patch(base, m, jaf_text):
    W.mkdir(parents=True, exist_ok=True)
    O.mkdir(parents=True, exist_ok=True)
    (W / 'helpers.jaf').write_text(jaf_text, 'utf8')
    decl = W / 'declared.ain'
    L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, base, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl)
    dm = L.read_meta(W / 'declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    assert all(n.startswith('KR_T19') for n in ids), [n for n in ids if not n.startswith('KR_T19')]
    changed = [f['index'] for f, g in zip(m['functions'], dm['functions']) if f != g and f['index'] != 0]
    assert not changed, ('the jaf declaration touched existing functions', changed[:5])
    patch = []
    for f in added:
        path = W / f"jaf_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        body = L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n')
        patch.append(L.clean(body, f['name']))
    forwarded = {}
    for old, new in FORWARD.items():
        fid = L.fid_of(m, old)
        assert sig(m['functions'][fid]) == sig(dm['functions'][ids[new]]), (old, new, sig(m['functions'][fid]), sig(dm['functions'][ids[new]]))
        patch.append(forwarder(m, fid, new))
        forwarded[old] = dict(index=fid, base_address=m['functions'][fid]['address'], target=new, target_index=ids[new])
    (W / 'patch.jam').write_text('\n'.join(patch), 'utf8')
    out = O / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', W / 'patch.jam', '-o', out, decl, timeout=900)
    src_bytes = base.read_bytes()
    old = L.unpack(src_bytes)
    raw = bytearray(L.unpack(out.read_bytes()))
    oldn = struct.unpack_from('<I', old, 12)[0]
    newn = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + newn, m['functions'][0]['address'])       # function 0 keeps its original body
    assert raw[16:16 + oldn] == old[16:16 + oldn], 'old CODE changed by the jaf/jam injection'
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, forwarded, oldn


def invariance(base, out, m, forwarded, oldn, sites, bp):
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', out)
    nm = L.read_meta(W / 'candidate_meta.json')
    fw = {v['index'] for v in forwarded.values()}
    changed = [f['index'] for f, g in zip(m['functions'], nm['functions']) if f != g]
    assert set(changed) == fw, ('function entries changed beyond the forwarders', sorted(set(changed) - fw)[:5])
    for i in fw:
        f, g = m['functions'][i], nm['functions'][i]
        assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, f['name']
        assert g['address'] >= oldn, ('a forwarder body is not in the appended code', f['name'])
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], ('metadata key changed', k)
    old = L.unpack(base.read_bytes())
    new = L.unpack(out.read_bytes())
    assert new[16:16 + oldn] == old[16:16 + oldn], 'old CODE bytes changed'
    assert L.raw_messages(base.read_bytes())[3] == L.raw_messages(out.read_bytes())[3], 'MSG1 changed'
    so, sn = L.strings(old)[2], L.strings(new)[2]
    assert sn[:len(so)] == so, 'STR0 prefix changed'
    _, code, _ = code_of(out.read_bytes())
    n_sites = sites_applied(code, sites)
    # the six pinned functions: entry and every code byte identical to the base (= the r18 candidate)
    vers = L.versions(bp['raw'])
    starts = sorted({v['start'] for vs in vers.values() for v in vs})
    _, bcode, _ = code_of(base.read_bytes())
    pinned = {}
    for name in L.PINNED_ALL:
        i = L.fid_of(m, name)
        f = m['functions'][i]
        assert nm['functions'][i] == f, ('pinned function entry changed', name)
        a = body_bytes(bcode, starts, f['address'], len(bcode))
        b = body_bytes(code, starts, f['address'], len(bcode))
        assert a == b, ('pinned code changed', name)
        pinned[name] = dict(index=i, address=f['address'], code_bytes=len(a), bytes_differing=0)
    t9 = sum(1 for f in nm['functions'] if L.raw_symbol(nm, f['index']).startswith('KR_T9'))
    t18 = sum(1 for f in nm['functions'] if L.raw_symbol(nm, f['index']).startswith('KR_T18'))
    return nm, dict(original_function_entries_identical_except_forwarded=True, forwarded=sorted(FORWARD),
                    other_metadata_identical=sorted(k for k in m if k != 'functions'), old_code_bytes_changed=0,
                    MSG1_exact=True, STR0_prefix_exact=True, STR0_added=len(sn) - len(so),
                    functions_added=len(nm['functions']) - len(m['functions']), pinned=pinned,
                    same_length_sites_kept=n_sites, kr_t9_functions=t9, kr_t18_functions=t18)


def discard(reason, got):
    for n in ['NightRemaster.ain', 'manifest.json', 'Manual/chart/yoru_flowchart_v2.html']:
        if (O / n).exists():
            (O / n).unlink()
    L.writej(L.WORK / 'REBASE_NEEDED.json', dict(time=datetime.datetime.now().astimezone().isoformat(), reason=reason, runtime_now=got,
                                               base=dict(ain=L.BASE_AIN_SHA, pact=L.BASE_PACT_SHA, ex=L.BASE_EX_SHA)))
    log('DISCARDED candidate:', reason)
    raise SystemExit(3)


def main():
    t0 = datetime.datetime.now()
    ptr, rt, bp, free = gates()
    base = bp['ain']
    log('gates ok', L.BASE_AIN_SHA[:16], ptr['status'], 'P: free %.1f GB' % (free / 1024 ** 3))
    W.mkdir(parents=True, exist_ok=True)
    m = L.read_meta(bp['meta'])
    vers = L.versions(bp['raw'])
    sites = site_list()
    _, bcode, _ = code_of(base.read_bytes())
    log('base keeps the r15/r18 same-length sites:', sites_applied(bcode, sites))
    for old, new in R18_FORWARD.items():
        f = m['functions'][L.fid_of(m, old)]
        v = L.live_version(m, vers, f['index'])
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(m, new), 'RETURN'], ('r18 forwarder not in the base', old)
    data, V2, chart = chart_data()
    log('chart v2 data = published (names included)', chart['same_as_published'])
    feel = feeling_events(V2, data)
    T = r15_tables(data, V2, m, vers)
    r15, r15t = r15_same(T, feel)
    log('r15 tables in the base = today\'s data except rule 11:', r15t)
    R, info = r19_tables(T, data, feel, r15)
    log('r19 tables', info)
    src = JAF_SRC.read_text('utf8')
    assert src.count('/*TABLES*/') == 1
    jaf = src.replace('/*TABLES*/', gen_tables(R))
    (W / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    texts = jaf_strings(L.strip_comments(jaf))
    bad = check_alphabet(texts)
    assert not bad, ('characters outside the font map / proxy set', bad)
    assert not any(E_RE.search(t) or 'E번호' in t for t in texts), 'an E-number left in the r19 source'
    built = L.jaf_literal_encode(L.strip_comments(jaf))
    assert not [c for c in built if ('\uac00' <= c <= '\ud7a3')], 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, forwarded, oldn = compile_and_patch(base, m, built)
    log('compiled: %d functions added, %d forwarders' % (len(ids), len(forwarded)))
    nm, inv = invariance(base, out, m, forwarded, oldn, sites, bp)
    log('invariance ok', {k: v for k, v in inv.items() if k != 'pinned'})
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    L.writej(W / 'tables.json', dict(heads={str(k): v for k, v in R['heads'].items()}, tails={str(k): v for k, v in R['tails'].items()},
                                     conds={str(k): v for k, v in R['conds'].items()}, ev_head={str(k): v for k, v in R['ev_head'].items()},
                                     ev_short={str(k): v for k, v in R['ev_short'].items()}, when_fix={str(k): v for k, v in R['when_fix'].items()},
                                     whens={str(k): v for k, v in R['whens'].items()}, order=R['order'],
                                     stage_cols={str(k): v for k, v in R['stage_cols'].items()}, chip_cols={str(k): v for k, v in R['chip_cols'].items()},
                                     info=info, r15_tables=r15t, feeling={str(k): v for k, v in feel.items()}))
    # the help-menu chart (chart-menu contract: a rebuilt chart goes to Manual/chart/yoru_flowchart_v2.html)
    chart_src = L.FLOW / 'chart' / 'yoru_flowchart_v2.html'
    assert L.sha(chart_src) == chart['published_chart_sha256']
    rt_chart = rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html'
    assert L.sha(rt_chart) == L.sha(L.FLOW / 'chart' / 'yoru_flowchart_v2_r18.html'), 'the runtime help-menu chart is not the r18-era chart'
    dst = O / 'Manual' / 'chart' / 'yoru_flowchart_v2.html'
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(chart_src, dst)
    assert L.sha(dst) == chart['published_chart_sha256']
    ptr2, rt2, got2 = runtime_now()
    if not base_is_current(ptr2, got2):
        discard('runtime moved during the build', dict(got2, status=ptr2['status'], manifest_sha256=ptr2['manifest_sha256']))
    man = dict(
        schema='yoru-calendar-r19.candidate.v1', status='CALENDAR_R19_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, r18_installed=True,
                  checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size),
               'Manual/chart/yoru_flowchart_v2.html': dict(sha256=L.sha(dst), size=dst.stat().st_size)},
        chart_runtime_before_sha256=L.sha(rt_chart),
        pact_changed=False, ex_changed=False, chart=chart, r15_tables=r15t, names=info,
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), forwarded_functions=forwarded,
        r18_forwarders_kept=sorted(R18_FORWARD), same_length_sites=[], same_length_sites_kept=inv['same_length_sites_kept'],
        relocated_original_functions=[], pinned_functions=inv['pinned'], invariance=inv,
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        session_variables=['YoruKR.T9.Ctx', 'YoruKR.T9.Req', 'YoruKR.T9.Play', 'YoruKR.T9.Playing', 'YoruKR.T9.Unwind', 'YoruKR.T9.Open', 'YoruKR.T9.Lane',
                           'YoruKR.T18.PrevSet', 'YoruKR.T18.PrevFn', 'YoruKR.T18.PrevSys'],
        serialized_schema_changes=0, translator_model=L.AUTHOR,
        jaf_source_sha256=L.sha(JAF_SRC), build_script_sha256=L.sha(Path(__file__)))
    L.writej(O / 'manifest.json', man)
    log('STAGED', out, man['files']['NightRemaster.ain']['sha256'])
    log('manifest', L.sha(O / 'manifest.json'))


if __name__ == '__main__':
    try:
        main()
    except AssertionError as ex:
        print('ASSERT', str(ex)[-3000:])
        raise SystemExit(1)
