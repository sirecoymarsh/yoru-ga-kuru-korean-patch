"""Claude Opus 5.5 (2026-09-27) r18: in-game event calendar = r17's screens (achievement bars, summary page, drawer rows;
every r17 function renamed KR_T18*) + replay lock + replay sandbox. r17 was installed 07:24 and restored 14:11 (journal
RESTORED), so the base is again the 04:01 AIN (r15 + Codex rate_overlay + story_explore; 18:03 chart menu changed only
winmm.dll and Manual/chart). r18 replaces the r17 candidate (and the never installed r16 one).

  python build_calendar_r18.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/status/manifest = r18lib BASE_*, P: free space >= 10 GB, and r15 inside
     the base: the five pinned functions (entry + code bytes), the nine same-length swap sites and all 93 KR_T9 functions
     (entries + code bytes) equal the r15 candidate (r15_calendar\\candidate, read only).
  2. data: chart/build_chart_v2.build() as a module (= published chart v2 HTML) -> the r15 tables recomputed here must equal
     r15's baked tables (r15_calendar\\work\\build\\tables.json) - the r15 tables inside the base stay valid.
  3. r17 tables (renamed KR_T18*): (a) r16's lane-row tails; (b) the panel-outside set from KR_PlayerEventCount (base AIN).
  4. alice ain edit --jaf (declare the KR_T18* functions) -> dump -> native_lower -> alice ain edit --jam with the lowered
     bodies AND a one-call forwarder body for eight r15 functions (same index, same arguments/return, new address):
       r17: KR_T9MonthPage, KR_T9MemPage, KR_T9LaneTitle, KR_T9CardRow, KR_T9ChipRow, KR_T9MonthChips -> KR_T18*
       r18: KR_T9CardPage -> KR_T18CardPage, KR_T9EventPage -> KR_T18EventPage (replay lock + sandbox note)
     then ONE same-length operand: KR_T9HomeCasual's `CALLFUNC LSys3xScript::RunEvent` -> KR_T18RunSandboxed (same
     signature: no arguments, bool; the return offset and every other byte of the pinned function stay).
  5. invariance: every base function entry identical except the eight forwarded ones (address only); other metadata keys,
     the whole old CODE except those 4 operand bytes, MSG1, STR0 prefix identical; pinned entries + code identical except
     that operand; r15 swap sites still applied; native opcode audit of every live function.
  6. end gate: the runtime hashes are read again. If Codex installed something meanwhile the candidate is DISCARDED
     (files removed, work/REBASE_NEEDED.json written) and the build exits 3 - rebuild on the new base, never install it.
PACT and EX are not touched. Nothing is written outside r18_calendar\\ (runtime, saves, Codex root, r15/r16/r17: read only).
"""
import sys, io, json, re, struct, shutil, collections, contextlib, datetime, os
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r18lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_calendar_r18.jaf'
LANES = ['main', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'dungeon']
LANE_KR = ['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전']
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
KIND_KR = ['우선 대화', '특훈 뒤 대화', '반한 뒤 대화', '초대', '던전 동행', '그 밖', '회상', '쓰이지 않음']
SLOT_KR = {1: '아침', 2: '밤', 3: '낮', 4: '저녁'}
SLOT_RANK = {1: 0, 3: 1, 4: 2, 2: 3, 0: 9}          # 아침 < 낮 < 저녁 < 밤, 시간대 없음은 뒤로
LIMIT = 38
CAL_START, CAL_END = (4, 9), (11, 17)
TAIL = 7                                              # " E30160"

# r15's nine same-length sites (already applied in the base; r17 only checks they are still there)
R15_SITES = [
    ('C_SceneHomebase@RunHome', '■選択ダイアログ／実行', 'KR_T9HomeMenuRun'),
    ('C_SceneHomebase@CheckGameSysButtons', '■カジュアルモード設定呼び出し', 'KR_T9HomeCasual'),
    ('C_SceneHomebase@CheckGameSysButtons', '▲コンフィグ実行', 'KR_T9HomeConfig'),
    ('KR_T8CharMissingMenu', '■選択ダイアログ／タイトル設定', 'KR_T9CharMenuTitle'),
    ('KR_T8CharMissingMenu', '■選択ダイアログ／実行', 'KR_T9CharMenuRun'),
    ('KR_T8CharMissingMenu', 'KR_T8CharMissingPage', 'KR_T9CharMenuPage'),
    ('KR_T8CharMissingPage', '■選択ダイアログ／選択肢追加', 'KR_T9CharPageAdd'),
    ('KR_T8CharMissingPage', '■選択ダイアログ／実行', 'KR_T9CharPageRun'),
    ('KR_T8CharMissingPage', 'KR_T8CharDatePage', 'KR_T9CharDate'),
]
FORWARD = {            # r15 function (index kept) -> r18 body (same arguments and return type)
    'KR_T9MonthPage': 'KR_T18MonthPage',          # r17 screens (renamed)
    'KR_T9MemPage': 'KR_T18MemPage',
    'KR_T9LaneTitle': 'KR_T18LaneTitle',
    'KR_T9CardRow': 'KR_T18CardRow',
    'KR_T9ChipRow': 'KR_T18ChipRow',
    'KR_T9MonthChips': 'KR_T18MonthChips',
    'KR_T9CardPage': 'KR_T18CardPage',            # r18 replay lock (+ sandbox note)
    'KR_T9EventPage': 'KR_T18EventPage',
}
TOTAL_EVENTS, PANEL_EVENTS = 1164, 1043


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- base and r15 references
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


def body_ranges(vers):
    """function start -> end of its code (next FUNC op) over every version in a --raw-code dump."""
    starts = sorted({v['start'] for vs in vers.values() for v in vs})
    return starts


def body_bytes(code, starts, address, limit):
    """FUNC op .. the byte before the next FUNC op of the reference dump (`limit` = reference code length)."""
    import bisect
    i = bisect.bisect_right(starts, address)
    end = starts[i] - 6 if i < len(starts) else limit
    return code[address - 6:end]


def r15_reference():
    """(meta, code, starts, manifest) of the r15 candidate — the byte reference for what r15 put in the base."""
    ain = L.R15 / 'candidate' / 'NightRemaster.ain'
    assert L.sha(ain) == L.R15_AIN_SHA, 'r15 candidate changed (evidence folder must stay as it is)'
    rm = L.read_meta(L.R15 / 'work' / 'build' / 'candidate_meta.json')
    rv = L.versions(L.R15 / 'work' / 'build' / 'candidate_raw_code.jam')
    _, rc, _ = code_of(ain.read_bytes())
    rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
    return rm, rc, body_ranges(rv), rman


def r15_inside(m, code, ref, swap=None):
    """r15's pinned functions, swap sites and every KR_T9 function are byte-identical in `m`/`code` (base or candidate).
    swap = the r18 site (candidate only): inside KR_T9HomeCasual exactly the 4 operand bytes of the RunEvent call differ,
    and they hold swap['after']."""
    rm, rc, rstarts, rman = ref
    out = dict(pinned={}, sites=0, kr_t9=0)
    for name in L.PINNED:
        i = L.fid_of(rm, name)
        f = rm['functions'][i]
        assert m['functions'][i] == f, ('pinned function entry differs from r15', name)
        got = bytearray(body_bytes(code, rstarts, f['address'], len(rc)))
        want = bytearray(body_bytes(rc, rstarts, f['address'], len(rc)))
        differ = [j for j in range(min(len(got), len(want))) if got[j] != want[j]]
        if swap is not None and name == L.SWAP_OWNER:
            rel = swap['site'] - (f['address'] - 6)
            assert len(got) == len(want) and set(differ) <= set(range(rel + 2, rel + 6)), ('pinned code differs beyond the operand', name, differ[:8])
            assert bytes(got[rel:rel + 6]).hex() == swap['after'] and bytes(want[rel:rel + 6]).hex() == swap['before'], ('swap operand', name)
            out['pinned'][name] = dict(index=i, address=f['address'], code_bytes=len(want), bytes_differing=len(differ),
                                       differing_offsets_in_body=differ, operand_site=swap['site'])
            continue
        assert not differ and len(got) == len(want), ('pinned code differs from r15', name)
        out['pinned'][name] = dict(index=i, address=f['address'], code_bytes=len(want), bytes_differing=0)
    for s in rman['same_length_sites']:
        assert code[s['site']:s['site'] + 6].hex() == s['after'], ('r15 swap site no longer applied', s['function'], s['replacement'])
        assert m['functions'][s['fid']] == rm['functions'][s['fid']], ('owner of an r15 swap site moved', s['function'])
        out['sites'] += 1
    for f in rm['functions']:
        if L.raw_symbol(rm, f['index']).startswith('KR_T9'):
            out['kr_t9'] += 1
    return out


def kr_t9_same(m, code, ref, allow=()):
    """Every r15 KR_T9 function except `allow` (forwarded) keeps entry and code bytes."""
    rm, rc, rstarts, _ = ref
    n = 0
    for f in rm['functions']:
        name = L.raw_symbol(rm, f['index'])
        if not name.startswith('KR_T9') or name in allow:
            continue
        assert m['functions'][f['index']] == f, ('KR_T9 entry changed', name)
        assert body_bytes(code, rstarts, f['address'], len(rc)) == body_bytes(rc, rstarts, f['address'], len(rc)), ('KR_T9 code changed', name)
        n += 1
    return n


def gates():
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase r18lib BASE_* on the new runtime first', got, ptr['status'])
    j = L.readj(L.R17_JOURNAL)
    assert j['status'] == 'RESTORED' and j['before']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r17 is installed again?', j['status'])
    assert L.sha(L.R17 / 'candidate' / 'NightRemaster.ain') == L.R17_AIN_SHA, 'r17 candidate changed (evidence must stay)'
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    base = L.base_dir() / 'NightRemaster.ain'          # r17's own snapshot, else r16's (read only) when it is the base AIN
    assert L.sha(base) == L.BASE_AIN_SHA, 'base copy differs from the runtime AIN (run work/snapshot_base_r17.py)'
    return ptr, rt, base, free


# ---------------------------------------------------------------- data (r15 functions, unchanged)
def chart_data():
    sys.path.insert(0, str(L.FLOW / 'chart'))
    import build_chart_v2 as V2
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data = V2.build(str(L.TMP / 'chart_v2_from_r18_build.html'))
    html = (L.FLOW / 'chart' / 'yoru_flowchart_v2.html').read_text('utf8')
    z = re.search(r'<script type="application/json" id="yoru-data">(.*?)</script>', html, re.S)
    pub = json.loads(z.group(1))

    def cards(d):
        return [(c['key'], c['entry'], c['members'], c['lane'], c['page'], c['pl'], c['n']) for c in d['cards']]

    def chips(d):
        return [(ch['id'], ch['page'], ch['lane'], ch['kind'], ch['entries'], [x[0] for x in ch['order']]) for ch in d['chips']]
    diff = dict(cards=cards(data) == cards(pub), chips=chips(data) == chips(pub), join=data['join'] == pub['join'],
                pages=[p['w1'] if 'w1' in p else None for p in data['pages']] == [p['w1'] if 'w1' in p else None for p in pub['pages']])
    assert all(diff.values()), ('PC chart v2 and the in-game tables would diverge — rebuild chart/yoru_flowchart_v2.html first', diff)
    return data, V2, dict(published_chart_sha256=L.sha(L.FLOW / 'chart' / 'yoru_flowchart_v2.html'), same_as_published=diff,
                          builder_sha256=L.sha(L.FLOW / 'chart' / 'build_chart_v2.py'))


def label_name(no):
    return ('E%04d' % no) if no == 1706 else ('E%05d' % no)


def adjust(s):
    return {'E01707': '01707', 'E02132': '02132'}.get(s, s)


def cut(s, n):
    """Cut to n characters with 「…」 (the ellipsis counts)."""
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


def fit_tokens(tokens, budget, sep=' · '):
    """Longest run of whole tokens within budget; 「 …」 marks tokens left out (numbers are never cut in half)."""
    if len(sep.join(tokens)) <= budget:
        return sep.join(tokens)
    out = []
    for t in tokens:
        if len(sep.join(out + [t])) + 2 <= budget:
            out.append(t)
        else:
            break
    if not out:
        return cut(tokens[0], budget)
    return sep.join(out) + ' …'


WHEN_CONT = '\n†　　　'          # a second 「언제」 line: white, under the text after 「언제　」


def when_text(e, budget):
    """「언제」 for the card / scene pages: one or two title lines of <= budget characters, cut only between tokens."""
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


def card_cond(e, pl):
    """Short condition for a lane row (tokens): the first 「언제」 text without the date/slot the row already shows."""
    w = (e['when'] or [''])[0]
    if 'd' not in pl:                     # undated (달만): keep the whole first text (e.g. 던전 · 학교 1층)
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


def tables(data, V2, m, vers):
    """r15's table computation, unchanged (the r15 tables baked in the base must equal this)."""
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
        assert pl['m'] == mo and 4 <= mo <= 11, c['key']
        day = pl.get('d', 0)
        slot = pl.get('slot', 0) or 0
        assert 0 <= slot <= 4 and 0 <= day <= 31, (c['key'], pl)
        stages = [r[0] for r in c['rows'] if r[6]]
        assert sorted(stages) == sorted(c['members']) and len(stages) == c['n'] and stages[0] == c['entry'], c['key']
        assert c['n'] < 100, c['key']
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
        toks = card_cond(evn[c['entry']], c['pl'])
        c['cond'] = fit_tokens(toks, budget) if toks else ''
        c['row_max'] = len(when) + 3 + len(c['cond']) + len(suffix)
        assert c['row_max'] <= LIMIT, c
    card_range = {}
    for mo in range(4, 12):
        ks = [c['k'] for c in cards if c['month'] == mo]
        card_range[mo] = (min(ks), max(ks) + 1) if ks else (0, 0)
        assert ks == list(range(*card_range[mo])) if ks else True
    chips = []
    scene_tab = []
    for ch in data['chips']:
        page = 12 if ch['page'] == 'mem' else int(ch['page'])
        if ch['lane'] in lane_ix:
            lane = lane_ix[ch['lane']]
        elif ch['lane'].startswith('mem'):
            lane = 8 + int(ch['lane'][3:])
        else:
            assert ch['lane'] == 'unused', ch['id']
            lane = 16
        kind = KINDS.index(ch['kind'])
        order = [x[0] for x in ch['order'] if x[4]]
        assert sorted(order) == sorted(ch['entries']) and len(order) == len(set(order)), ch['id']
        assert len(order) < 1000
        chips.append(dict(id=ch['id'], month=page, lane=lane, kind=kind, size=len(order), scene0=len(scene_tab), scenes=order))
        scene_tab += order
    for i, ch in enumerate(chips):
        ch['c'] = i
    chip_range = {}
    for mo in range(4, 13):
        cs = [ch['c'] for ch in chips if ch['month'] == mo]
        chip_range[mo] = (min(cs), max(cs) + 1) if cs else (0, 0)
        assert not cs or cs == list(range(*chip_range[mo])), mo
    assert sorted(scene_tab + stage_tab) == sorted(evn), 'every event exactly once in a card or a drawer'
    evtab = {}
    for no, e in evn.items():
        evtab[no] = dict(msg=e['m0'] if e['m0'] is not None else -1, when=when_text(e, 34), who=who_text(e, 34), cat=e['cat'])
    w1 = {p['m']: p['w1'] for p in data['pages'] if p.get('m')}
    mlen = dict(V2.MLEN)
    assert (V2.CAL_START, V2.CAL_END) == (CAL_START, CAL_END)
    return dict(cards=cards, stages=stage_tab, card_range=card_range, chips=chips, scenes=scene_tab, chip_range=chip_range,
                events=evtab, w1=w1, mlen=mlen)


def same_as_r15_tables(T):
    """The r15 tables live in the base: today's chart data must still produce exactly them."""
    r15 = L.readj(L.R15 / 'work' / 'build' / 'tables.json')
    now = json.loads(json.dumps(dict(cards=T['cards'], chips=T['chips'], stages=T['stages'], scenes=T['scenes'],
                                     events={str(k): v for k, v in T['events'].items()}, w1=T['w1'], mlen=T['mlen'],
                                     card_range={str(k): v for k, v in T['card_range'].items()},
                                     chip_range={str(k): v for k, v in T['chip_range'].items()}), ensure_ascii=False))
    diff = [k for k in now if now[k] != r15.get(k)]
    assert not diff, ('chart data moved since r15 was built: the r15 tables in the base are stale — rebuild r15 tables first', diff)
    return dict(r15_tables_sha256=L.sha(L.R15 / 'work' / 'build' / 'tables.json'), identical=True)


# ---------------------------------------------------------------- r17 tables (r16's tails + the panel-outside set)
def row_parts(c):
    when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
    if c['slot']:
        when += ' ' + SLOT_KR[c['slot']]
    suffix = (' (%d단계)' % c['size']) if c['size'] > 1 else ''
    return when, suffix


def row_text(c, cond, tail, mark='●'):
    when, suffix = row_parts(c)
    t = when + ' ' + mark
    if cond:
        t += ' ' + cond
    t += suffix
    if tail:
        t += ' E%05d' % c['entry']
    return t


def tails(T):
    """Lane rows that collide (text without the mark) inside one (month, lane) get 「 E#####」 and a cond re-fitted."""
    evn = T['_ev']
    groups = collections.defaultdict(list)
    for c in T['cards']:
        when, suffix = row_parts(c)
        groups[(c['month'], c['lane'], when, c['cond'], suffix)].append(c)
    hit = {}
    for key, cs in groups.items():
        if len(cs) < 2:
            continue
        for c in cs:
            when, suffix = row_parts(c)
            budget = LIMIT - len(when) - 3 - len(suffix) - TAIL
            toks = card_cond(evn[c['entry']], c['pl'])
            cond = fit_tokens(toks, budget) if toks else ''
            hit[c['k']] = dict(cond=cond, row=row_text(c, cond, True))
            assert len(hit[c['k']]['row']) <= LIMIT, hit[c['k']]
    rows = collections.defaultdict(list)
    for c in T['cards']:
        t = hit[c['k']]['row'] if c['k'] in hit else row_text(c, c['cond'], False)
        assert len(t) <= LIMIT, t
        rows[(c['month'], c['lane'])].append(t)
    dup = {k: [t for t, n in collections.Counter(v).items() if n > 1] for k, v in rows.items()}
    dup = {k: v for k, v in dup.items() if v}
    assert not dup, ('lane rows still collide after the tails', dup)
    r16 = L.readj(L.R16 / 'work' / 'build' / 'tables.json')['tails']          # r16's baked tails (read only)
    assert {str(k): v for k, v in hit.items()} == r16, 'tails differ from the r16 candidate (chart data moved?)'
    return hit, dict(groups=sum(1 for cs in groups.values() if len(cs) > 1), cards=len(hit),
                     duplicate_rows_after=0, longest_row=max(len(t) for v in rows.values() for t in v), same_as_r16=True)


def panel_groups(base):
    """Event names KR_PlayerEventCount(group) tests, per group, read from the BASE AIN (the r9 panel's own code)."""
    path = W / 'base_KR_PlayerEventCount.jam'
    L.cmd('ain', 'dump', '--function', 'KR_PlayerEventCount', '-o', path, base)
    lines = [l.strip() for l in path.read_text('utf8').splitlines()]
    groups = collections.defaultdict(list)
    cur = None
    for i, l in enumerate(lines):
        if l == '.LOCALREF group' and i + 2 < len(lines) and lines[i + 1].startswith('PUSH ') and lines[i + 2] == 'EQUALE':
            cur = int(lines[i + 1].split()[1])
            continue
        z = re.match(r'S_PUSH "(.*)"', l)
        if z and cur is not None:
            groups[cur].append(json.loads('"' + z.group(1) + '"'))
    return groups


def panel_outside(T, base):
    """The calendar events the home achievement panel does not count (r17 counts only the panel set in months 4-11)."""
    groups = panel_groups(base)
    pset = {n for v in groups.values() for n in v}
    assert sorted(groups) == [0, 1, 2, 3] and len(pset) == sum(len(v) for v in groups.values()) == PANEL_EVENTS, \
        ('panel groups changed', {g: len(v) for g, v in groups.items()})
    ev = T['_ev']
    fns = {e['fn']: no for no, e in ev.items()}
    assert len(fns) == len(ev) == TOTAL_EVENTS
    assert pset <= set(fns), ('the panel counts events the calendar does not have', sorted(pset - set(fns))[:5])
    out = sorted(no for fn, no in fns.items() if fn not in pset)
    where = {}
    for c in T['cards']:
        for s in c['stages']:
            where[s] = ('card', c['month'], c['lane'], c['day'], c['k'])
    for ch in T['chips']:
        for s in ch['scenes']:
            where[s] = ('drawer', ch['month'], ch['lane'], 0, ch['c'])
    m12 = sorted(no for no in ev if where[no][1] == 12)
    assert set(m12) <= set(out), 'a 회상 · 그 밖 event is counted by the panel: the memory page basis would be mixed'
    rest = [no for no in out if where[no][1] != 12]
    assert all(where[no][2] == 8 for no in rest), ('an outside event outside the dungeon lane', [(no, where[no]) for no in rest])
    assert not [no for no in rest if where[no][0] == 'card' and where[no][3]], 'an outside event in a dated card (day cells would differ)'
    cats = collections.Counter(ev[no]['cat'] for no in m12)
    info = dict(panel_events=len(pset), panel_groups={str(g): len(v) for g, v in sorted(groups.items())}, outside=len(out),
                memory_page=len(m12), memory_by_category=dict(cats), dungeon_lane=['E%05d' % no for no in rest],
                dungeon_lane_places=[dict(event='E%05d' % no, kind=where[no][0], month=where[no][1],
                                          card_or_drawer=where[no][4]) for no in rest],
                counted_months_4_11=TOTAL_EVENTS - len(out), panel_code_sha256=L.sha(W / 'base_KR_PlayerEventCount.jam'))
    assert len(out) == TOTAL_EVENTS - PANEL_EVENTS == 121 and len(m12) == 113 and len(rest) == 8, info
    return out, info


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


def gen_tables(hit, outside):
    out = [tree('int', 'KR_T18CardTail', 'k', [(k, 1) for k in hit], 0),
           tree('string', 'KR_T18TailCond', 'k', [(k, q(v['cond'])) for k, v in hit.items()], '""'),
           '// 패널 밖 121 (왼쪽 달성률 패널 KR_PlayerEventCount 0~3 에 없는 달력 장면): 1 = 패널 밖\n'
           + tree('int', 'KR_T18Out', 'no', [(no, 1) for no in outside], 0),
           tree('int', 'KR_T18OutEv', 'i', list(enumerate(outside)), -1),
           'int KR_T18OutTotal() {\n    return %d;\n}\n' % len(outside)]
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
    """One-call body: push every argument (int 10 / bool 47 one stack slot; string 12 as the compiler passes a string local:
    .LOCALREF + A_REF, see KR_T17ChipRow -> KR_T17Row in r17), call the r18 body, return its value (or nothing for void)."""
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
    assert all(n.startswith('KR_T18') for n in ids), [n for n in ids if not n.startswith('KR_T18')]
    sb, rev = dm['functions'][ids[L.SANDBOX]], m['functions'][L.fid_of(m, L.SWAP_OLD)]
    assert sig(sb) == sig(rev) == ([], [47, -1, 0, None]), ('KR_T18RunSandboxed must have RunEvent\'s signature', sig(sb), sig(rev))
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
        assert sig(m['functions'][fid]) == sig(dm['functions'][ids[new]]), (old, new)
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
    swap = sandbox_swap(m, raw, ids[L.SANDBOX])
    assert raw[16:16 + oldn] != old[16:16 + oldn]
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, forwarded, oldn, swap


def sandbox_swap(m, raw, new_fid):
    """The one r18 same-length operand: in KR_T9HomeCasual's live body the single `CALLFUNC LSys3xScript::RunEvent`
    (opcode 0x30 + int32 function number) now calls KR_T18RunSandboxed. Everything else in the function stays."""
    vers = L.versions(L.base_dir() / 'raw_code.jam')
    fid = L.fid_of(m, L.SWAP_OWNER)
    old_fid = L.fid_of(m, L.SWAP_OLD)
    v = L.live_version(m, vers, fid)
    hits = [ad for ad, op in v['ops'] if op == 'CALLFUNC 0x%x' % old_fid]
    assert len(hits) == 1, ('RunEvent calls in KR_T9HomeCasual', hits)
    site = hits[0]
    before = struct.pack('<Hi', 0x30, old_fid)
    after = struct.pack('<Hi', 0x30, new_fid)
    assert bytes(raw[16 + site:16 + site + 6]) == before, ('swap site bytes', bytes(raw[16 + site:16 + site + 6]).hex())
    nxt = [op for ad, op in v['ops'] if ad > site][:1]
    assert nxt == ['POP'], ('the RunEvent result is popped right after the call', nxt)
    raw[16 + site:16 + site + 6] = after
    f = m['functions'][fid]
    return dict(function=L.SWAP_OWNER, fid=fid, function_address=f['address'], site=site, site_offset=site - f['address'],
                return_offset=site + 6 - f['address'], original=L.SWAP_OLD, original_fid=old_fid, replacement=L.SANDBOX,
                replacement_fid=new_fid, before=before.hex(), after=after.hex(), operand_bytes=[site + 2, site + 6],
                occurrence=0, calls_of_original_in_function=1)


def invariance(base, out, m, forwarded, oldn, ref, swap):
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', out)
    nm = L.read_meta(W / 'candidate_meta.json')
    fw = {v['index'] for v in forwarded.values()}
    changed = [f['index'] for f, g in zip(m['functions'], nm['functions']) if f != g]
    assert set(changed) == fw, ('function entries changed beyond the six forwarders', sorted(set(changed) - fw)[:5])
    for i in fw:
        f, g = m['functions'][i], nm['functions'][i]
        assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, f['name']
        assert g['address'] >= oldn, ('a forwarder body is not in the appended code', f['name'])
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], ('metadata key changed', k)
    old = L.unpack(base.read_bytes())
    new = L.unpack(out.read_bytes())
    a, b = swap['operand_bytes']
    diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
    assert diff and set(diff) <= set(range(a, b)), ('old CODE bytes changed beyond the one operand', diff[:8])
    assert new[16:16 + a] == old[16:16 + a] and new[16 + b:16 + oldn] == old[16 + b:16 + oldn]
    assert L.raw_messages(base.read_bytes())[3] == L.raw_messages(out.read_bytes())[3], 'MSG1 changed'
    so, sn = L.strings(old)[2], L.strings(new)[2]
    assert sn[:len(so)] == so, 'STR0 prefix changed'
    _, code, _ = code_of(out.read_bytes())
    inside = r15_inside(nm, code, ref, swap=swap)
    same_t9 = kr_t9_same(nm, code, ref, allow=set(FORWARD) | {L.SWAP_OWNER})
    return nm, dict(original_function_entries_identical_except_forwarded=True, forwarded=sorted(FORWARD),
                    other_metadata_identical=sorted(k for k in m if k != 'functions'), old_code_bytes_changed=len(diff),
                    old_code_bytes_changed_offsets=diff, old_code_bytes_changed_are_the_operand=[a, b],
                    MSG1_exact=True, STR0_prefix_exact=True, STR0_added=len(sn) - len(so),
                    functions_added=len(nm['functions']) - len(m['functions']), pinned=inside['pinned'],
                    r15_swap_sites_applied=inside['sites'], kr_t9_functions_unchanged=same_t9, kr_t9_functions=inside['kr_t9'])


def discard(reason, got):
    for n in ['NightRemaster.ain', 'manifest.json']:
        if (O / n).exists():
            (O / n).unlink()
    L.writej(L.WORK / 'REBASE_NEEDED.json', dict(time=datetime.datetime.now().astimezone().isoformat(), reason=reason, runtime_now=got,
                                               base=dict(ain=L.BASE_AIN_SHA, pact=L.BASE_PACT_SHA, ex=L.BASE_EX_SHA)))
    log('DISCARDED candidate:', reason)
    raise SystemExit(3)


def main():
    t0 = datetime.datetime.now()
    ptr, rt, base, free = gates()
    log('gates ok', L.BASE_AIN_SHA[:16], ptr['status'], 'P: free %.1f GB' % (free / 1024 ** 3))
    W.mkdir(parents=True, exist_ok=True)
    bd = L.base_dir()
    m = L.read_meta(bd / 'meta.json')
    vers = L.versions(bd / 'raw_code.jam')
    ref = r15_reference()
    _, bcode, _ = code_of(base.read_bytes())
    inside = r15_inside(m, bcode, ref)
    t9 = kr_t9_same(m, bcode, ref)
    assert t9 == inside['kr_t9'] == 93, (t9, inside['kr_t9'])
    log('r15 inside the base: pinned %d, swap sites %d, KR_T9 %d byte-identical' % (len(inside['pinned']), inside['sites'], t9))
    data, V2, chart = chart_data()
    log('chart v2 data ok', chart['same_as_published'])
    T = tables(data, V2, m, vers)
    T['_ev'] = {int(k): v for k, v in data['ev'].items()}
    r15t = same_as_r15_tables(T)
    log('tables = r15 baked tables: cards %d stages %d chips %d scenes %d events %d' % (len(T['cards']), len(T['stages']), len(T['chips']), len(T['scenes']), len(T['events'])))
    hit, tail_info = tails(T)
    log('E-number tails', tail_info)
    outside, panel_info = panel_outside(T, base)
    log('panel set', {k: v for k, v in panel_info.items() if k != 'dungeon_lane_places'})
    src = JAF_SRC.read_text('utf8')
    assert src.count('/*TABLES*/') == 1
    assert 'KR_T16' not in L.strip_comments(src) and 'KR_T17' not in L.strip_comments(src), 'r16/r17 names left in the r18 source'
    jaf = src.replace('/*TABLES*/', gen_tables(hit, outside))
    (W / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    texts = jaf_strings(L.strip_comments(jaf))
    bad = check_alphabet(texts)
    assert not bad, ('characters outside the font map / proxy set', bad)
    built = L.jaf_literal_encode(L.strip_comments(jaf))
    rest = [c for c in built if ('\uac00' <= c <= '\ud7a3')]
    assert not rest, 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, forwarded, oldn, swap = compile_and_patch(base, m, built)
    log('compiled: %d functions added, %d forwarders, swap %s -> %s at 0x%x' % (len(ids), len(forwarded), swap['before'], swap['after'], swap['site']))
    nm, inv = invariance(base, out, m, forwarded, oldn, ref, swap)
    log('invariance ok', {k: v for k, v in inv.items() if k != 'pinned'})
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    L.writej(W / 'tables.json', dict(tails={str(k): v for k, v in hit.items()}, tail_info=tail_info, r15_tables=r15t,
                                     panel_outside=outside, panel=panel_info))
    # end gate: Codex may have installed while this ran
    ptr2, rt2, got2 = runtime_now()
    if not base_is_current(ptr2, got2):
        discard('runtime moved during the build', dict(got2, status=ptr2['status'], manifest_sha256=ptr2['manifest_sha256']))
    man = dict(
        schema='yoru-calendar-r18.candidate.v1', status='CALENDAR_R18_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  r17_journal=dict(path=str(L.R17_JOURNAL), status=L.readj(L.R17_JOURNAL)['status']),
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA,
                  checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, chart=chart, r15_tables=r15t, tails=tail_info,
        panel=panel_info, replaces=dict(r17_candidate_ain_sha256=L.R17_AIN_SHA, r17_installed='07:24, restored 14:11 (journal RESTORED)',
                                        r16_candidate_ain_sha256=L.R16_AIN_SHA, r16_installed=False,
                                        function_names='all new functions KR_T18* (r17 KR_T17* renamed; r16 KR_T16* never shipped)'),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), forwarded_functions=forwarded,
        same_length_sites=[swap], r15_same_length_sites_kept=inside['sites'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], invariance=inv,
        sandbox=dict(function=L.SANDBOX, index=ids[L.SANDBOX], address=nm['functions'][ids[L.SANDBOX]]['address'],
                     signature='bool ()  (= LSys3xScript::RunEvent)', temp_file='<EX Ｅ＿セーブファイル名＿接頭語>KRReplay.asd + .vsf',
                     method='game::detail::MemoryModeEvent_Begin/_End/_Cleanup: gamesave::detail::セーブ実行(file,"","",false) '
                            'returns true on the fresh save path, false after gamesave::detail::ロード実行(file) resumed here'),
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
