"""Claude Opus 5.5 (2026-09-27) r15: in-game event calendar (text menu board) — candidate build.

  python build_calendar_r15.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps (09-24 r3~r14 conventions, but on top of the CURRENT runtime AIN instead of a re-built overlay):
  1. gates: current.json runtime AIN/PACT/EX hashes = 09-27 baseline (963c7db0…), manifest hash, P: free space.
  2. data: chart/build_chart_v2.build() imported as a module (same month/lane/drawer assignment as the PC chart v2) and
     compared with the data block of the published chart/yoru_flowchart_v2.html (the two must not diverge).
     Event names and first message numbers are checked against the live code of the base AIN.
  3. tables baked into jaf (binary-tree getters, no globals, no switch): cards 155, stages, drawers 96, scenes 760,
     per-event first message / 언제 / 누구 (1,164), weekday of the 1st and month lengths. Strings pre-cut with 「…」.
  4. alice ain edit --jaf (declare) -> dump each new function -> native_lower -> alice ain edit --jam (live bodies).
  5. same-length CALLFUNC operand swaps only (no original function relocated):
       C_SceneHomebase@RunHome          ■選択ダイアログ／実行            -> KR_T9HomeMenuRun
       C_SceneHomebase@CheckGameSysButtons ■カジュアルモード設定呼び出し -> KR_T9HomeCasual
                                        ▲コンフィグ実行                 -> KR_T9HomeConfig
       KR_T8CharMissingMenu             ■選択ダイアログ／タイトル設定    -> KR_T9CharMenuTitle
                                        ■選択ダイアログ／実行            -> KR_T9CharMenuRun
                                        KR_T8CharMissingPage             -> KR_T9CharMenuPage
       KR_T8CharMissingPage             ■選択ダイアログ／選択肢追加 (2nd) -> KR_T9CharPageAdd
                                        ■選択ダイアログ／実行            -> KR_T9CharPageRun
                                        KR_T8CharDatePage                -> KR_T9CharDate
  6. invariance: every original function entry identical (address included), every non-function metadata key identical,
     MSG1 identical, STR0 prefix identical, old CODE bytes identical except the swapped operands; native opcode audit.
PACT and EX are not touched. Nothing is written outside r15_calendar\\ (runtime, saves, Codex root: read only).
"""
import sys, io, json, re, struct, shutil, collections, contextlib, datetime, os
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r15lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_calendar_r15.jaf'
LANES = ['main', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'dungeon']
LANE_KR = ['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전']
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
KIND_KR = ['우선 대화', '특훈 뒤 대화', '반한 뒤 대화', '초대', '던전 동행', '그 밖', '회상', '쓰이지 않음']
SLOT_KR = {1: '아침', 2: '밤', 3: '낮', 4: '저녁'}
SLOT_RANK = {1: 0, 3: 1, 4: 2, 2: 3, 0: 9}          # 아침 < 낮 < 저녁 < 밤, 시간대 없음은 뒤로
LIMIT = 38
CAL_START, CAL_END = (4, 9), (11, 17)

SWAPS = [
    # (function, old callee, occurrence index among its calls, new function)
    ('C_SceneHomebase@RunHome', '■選択ダイアログ／実行', 0, 'KR_T9HomeMenuRun'),
    ('C_SceneHomebase@CheckGameSysButtons', '■カジュアルモード設定呼び出し', 0, 'KR_T9HomeCasual'),
    ('C_SceneHomebase@CheckGameSysButtons', '▲コンフィグ実行', 0, 'KR_T9HomeConfig'),
    ('KR_T8CharMissingMenu', '■選択ダイアログ／タイトル設定', 0, 'KR_T9CharMenuTitle'),
    ('KR_T8CharMissingMenu', '■選択ダイアログ／実行', 0, 'KR_T9CharMenuRun'),
    ('KR_T8CharMissingMenu', 'KR_T8CharMissingPage', 0, 'KR_T9CharMenuPage'),
    ('KR_T8CharMissingPage', '■選択ダイアログ／選択肢追加', 1, 'KR_T9CharPageAdd'),
    ('KR_T8CharMissingPage', '■選択ダイアログ／実行', 0, 'KR_T9CharPageRun'),
    ('KR_T8CharMissingPage', 'KR_T8CharDatePage', 0, 'KR_T9CharDate'),
]
EXPECTED_CALLS = {  # how many calls of the old callee each patched function has (all must be accounted for)
    ('C_SceneHomebase@RunHome', '■選択ダイアログ／実行'): 1,
    ('C_SceneHomebase@CheckGameSysButtons', '■カジュアルモード設定呼び出し'): 1,
    ('C_SceneHomebase@CheckGameSysButtons', '▲コンフィグ実行'): 1,
    ('KR_T8CharMissingMenu', '■選択ダイアログ／タイトル設定'): 1,
    ('KR_T8CharMissingMenu', '■選択ダイアログ／実行'): 1,
    ('KR_T8CharMissingMenu', 'KR_T8CharMissingPage'): 1,
    ('KR_T8CharMissingPage', '■選択ダイアログ／選択肢追加'): 3,
    ('KR_T8CharMissingPage', '■選択ダイアログ／実行'): 1,
    ('KR_T8CharMissingPage', 'KR_T8CharDatePage'): 1,
}
# Functions that sit on a saved stack while a calendar replay runs (a save inside the replayed event):
# C_SceneGame@Run > … > C_SceneHomebase@Run > CheckGameSysButtons > KR_T9HomeCasual > LSys3xScript::RunEvent > event.
PINNED_NEW = ['KR_T9HomeCasual']


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- gates
def gates():
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    ptr, rt = L.runtime()
    got = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'NightRemasterPact.afa', 'NightRemasterEX.ex']}
    assert got['NightRemaster.ain'] == L.BASE_AIN_SHA, ('runtime AIN moved since 09-27 00:00 — rebase first', got)
    assert got['NightRemasterPact.afa'] == L.BASE_PACT_SHA and got['NightRemasterEX.ex'] == L.BASE_EX_SHA, got
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    base = L.WORK / 'base' / 'NightRemaster.ain'
    assert L.sha(base) == L.BASE_AIN_SHA, 'work/base copy differs from the runtime AIN'
    return ptr, rt, base, free


# ---------------------------------------------------------------- data
def chart_data():
    sys.path.insert(0, str(L.FLOW / 'chart'))
    import build_chart_v2 as V2
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data = V2.build(str(L.TMP / 'chart_v2_from_r15_build.html'))
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
    ev = data['ev']
    evn = {int(k): v for k, v in ev.items()}
    byname = {}
    for f in m['functions']:
        byname.setdefault(L.raw_symbol(m, f['index']), []).append(f['index'])
    # event names and first MSG against the live code
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
    # cards
    lane_ix = {k: i for i, k in enumerate(LANES)}
    cards = []
    for c in data['cards']:
        pl = c['pl']
        mo = int(c['page'])
        assert pl['m'] == mo and 4 <= mo <= 11, c['key']
        day = pl.get('d', 0)
        slot = pl.get('slot', 0) or 0
        assert 0 <= slot <= 4 and 0 <= day <= 31, (c['key'], pl)
        stages = [r[0] for r in c['rows'] if r[6]]          # counts_here: first appearance of each member
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
        budget = LIMIT - len(when) - 3 - len(suffix)            # "<when> ● <cond><suffix>"
        toks = card_cond(evn[c['entry']], c['pl'])
        c['cond'] = fit_tokens(toks, budget) if toks else ''
        c['row_max'] = len(when) + 3 + len(c['cond']) + len(suffix)
        assert c['row_max'] <= LIMIT, c
    card_range = {}
    for mo in range(4, 12):
        ks = [c['k'] for c in cards if c['month'] == mo]
        card_range[mo] = (min(ks), max(ks) + 1) if ks else (0, 0)
        assert ks == list(range(*card_range[mo])) if ks else True
    # chips
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
        order = [x[0] for x in ch['order'] if x[4]]         # first appearance only (shared chain steps shown once)
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
    # events
    evtab = {}
    for no, e in evn.items():
        evtab[no] = dict(msg=e['m0'] if e['m0'] is not None else -1, when=when_text(e, 34), who=who_text(e, 34), cat=e['cat'])
    w1 = {p['m']: p['w1'] for p in data['pages'] if p.get('m')}
    mlen = dict(V2.MLEN)
    assert (V2.CAL_START, V2.CAL_END) == (CAL_START, CAL_END)
    return dict(cards=cards, stages=stage_tab, card_range=card_range, chips=chips, scenes=scene_tab, chip_range=chip_range,
                events=evtab, w1=w1, mlen=mlen)


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


def small(ret, name, var, pairs, default):
    body = ''.join(f'    if ({var} == {k}) return {v};\n' for k, v in pairs)
    return f'{ret} {name}(int {var}) {{\n{body}    return {default};\n}}\n'


def gen_tables(T):
    out = []
    cr, hr = T['card_range'], T['chip_range']
    out.append(small('int', 'KR_T9CardFirst', 'm', [(mo, cr[mo][0]) for mo in range(4, 12)], 0))
    out.append(small('int', 'KR_T9CardEnd', 'm', [(mo, cr[mo][1]) for mo in range(4, 12)], 0))
    out.append(small('int', 'KR_T9ChipFirst', 'm', [(mo, hr[mo][0]) for mo in range(4, 13)], 0))
    out.append(small('int', 'KR_T9ChipEnd', 'm', [(mo, hr[mo][1]) for mo in range(4, 13)], 0))
    out.append(small('int', 'KR_T9W1', 'm', [(mo, T['w1'][mo]) for mo in range(4, 12)], 0))
    out.append(small('int', 'KR_T9MLen', 'm', [(mo, T['mlen'][mo]) for mo in range(4, 12)], 30))
    cards = T['cards']
    out.append(tree('int', 'KR_T9CardInfo', 'k', [(c['k'], c['lane'] * 100000 + c['day'] * 1000 + c['slot'] * 100 + c['size']) for c in cards], 0))
    out.append(tree('int', 'KR_T9CardEntry', 'k', [(c['k'], c['entry']) for c in cards], 0))
    out.append(tree('int', 'KR_T9CardStage', 'k', [(c['k'], c['stage0']) for c in cards], 0))
    out.append(tree('string', 'KR_T9CardCond', 'k', [(c['k'], q(c['cond'])) for c in cards], '""'))
    out.append(tree('int', 'KR_T9StageEv', 'i', list(enumerate(T['stages'])), 0))
    chips = T['chips']
    out.append(tree('int', 'KR_T9ChipInfo', 'c', [(ch['c'], (ch['lane'] * 10 + ch['kind']) * 1000 + ch['size']) for ch in chips], 0))
    out.append(tree('int', 'KR_T9ChipScene', 'c', [(ch['c'], ch['scene0']) for ch in chips], 0))
    out.append(tree('int', 'KR_T9SceneEv', 's', list(enumerate(T['scenes'])), 0))
    ev = T['events']
    out.append(tree('int', 'KR_T9EvMsg', 'no', [(no, e['msg']) for no, e in ev.items()], -1))
    out.append(tree('string', 'KR_T9EvWhen', 'no', [(no, q(e['when'])) for no, e in ev.items()], '""'))
    out.append(tree('string', 'KR_T9EvWho', 'no', [(no, q(e['who'])) for no, e in ev.items()], '""'))
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
                bad[ch] += 1                 # Hangul outside the 2,350 proxy syllables
                continue
            try:
                b = ch.encode('cp932')
            except UnicodeEncodeError:
                bad[ch] += 1
                continue
            if len(b) == 2 and b[0] in carrier:
                bad[ch] += 1                 # would draw as a Hangul proxy carrier
    return dict(bad)


def jaf_strings(src):
    return [json.loads(z) for z in re.findall(r'"(?:[^"\\]|\\.)*"', src)]


# ---------------------------------------------------------------- compile and patch
def compile_and_patch(base, m, vers, jaf_text, rt):
    W.mkdir(parents=True, exist_ok=True)
    O.mkdir(parents=True, exist_ok=True)
    (W / 'helpers.jaf').write_text(jaf_text, 'utf8')
    decl = W / 'declared.ain'
    L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, base, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl)
    dm = L.read_meta(W / 'declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    assert all(n.startswith('KR_T9') for n in ids), [n for n in ids if not n.startswith('KR_T9')]
    patch = []
    for f in added:
        path = W / f"jaf_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        body = L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n')
        patch.append(L.clean(body, f['name']))
    (W / 'patch.jam').write_text('\n'.join(patch), 'utf8')
    out = O / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', W / 'patch.jam', '-o', out, decl, timeout=900)
    src_bytes = base.read_bytes()
    old = L.unpack(src_bytes)
    raw = bytearray(L.unpack(out.read_bytes()))
    oldn = struct.unpack_from('<I', old, 12)[0]
    newn = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + newn, m['functions'][0]['address'])
    assert raw[16:16 + oldn] == old[16:16 + oldn], 'old CODE prefix changed by the jaf/jam injection'
    # same-length operand swaps inside unchanged original functions
    sig = lambda f: ([a['type'] for a in f['arguments']], f['return-type'])
    sites = []
    for where, oldfn, nth, newfn in SWAPS:
        fid = L.fid_of(m, where)
        oldid = L.fid_of(m, oldfn)
        newid = ids[newfn]
        assert sig(dm['functions'][newid]) == sig(m['functions'][oldid]), (newfn, sig(dm['functions'][newid]), sig(m['functions'][oldid]))
        v = L.live_version(m, vers, fid)
        calls = [ad for ad, op in v['ops'] if op == f'CALLFUNC 0x{oldid:x}']
        assert len(calls) == EXPECTED_CALLS[(where, oldfn)], (where, oldfn, len(calls))
        ad = calls[nth]
        before = struct.pack('<Hi', 0x30, oldid)
        after = struct.pack('<Hi', 0x30, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (where, hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=where, fid=fid, function_address=m['functions'][fid]['address'], site=ad,
                          site_offset=ad - m['functions'][fid]['address'], original=oldfn, original_fid=oldid,
                          replacement=newfn, replacement_fid=newid, before=before.hex(), after=after.hex(),
                          occurrence=nth, calls_of_original_in_function=len(calls)))
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, sites, oldn


def invariance(base, out, m, sites, oldn):
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', out)
    nm = L.read_meta(W / 'candidate_meta.json')
    changed_entries = [f['index'] for f, g in zip(m['functions'], nm['functions']) if f != g]
    assert not changed_entries, ('original function entries changed', changed_entries[:5])
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], ('metadata key changed', k)
    old = L.unpack(base.read_bytes())
    new = L.unpack(out.read_bytes())
    allowed = set(x for s in sites for x in range(s['site'] + 2, s['site'] + 6))
    diff = [i for i in range(oldn) if old[16 + i] != new[16 + i]]
    assert set(diff) <= allowed, [hex(x) for x in diff if x not in allowed][:10]
    assert L.raw_messages(base.read_bytes())[3] == L.raw_messages(out.read_bytes())[3], 'MSG1 changed'
    so, sn = L.strings(old)[2], L.strings(new)[2]
    assert sn[:len(so)] == so, 'STR0 prefix changed'
    return nm, dict(original_function_entries_identical=True, other_metadata_identical=sorted(k for k in m if k != 'functions'),
                    old_code_bytes_changed=len(diff), old_code_changes_only_at_swapped_operands=True, MSG1_exact=True,
                    STR0_prefix_exact=True, STR0_added=len(sn) - len(so), functions_added=len(nm['functions']) - len(m['functions']))


def main():
    t0 = datetime.datetime.now()
    ptr, rt, base, free = gates()
    log('gates ok', L.BASE_AIN_SHA[:16], 'P: free %.1f GB' % (free / 1024 ** 3))
    W.mkdir(parents=True, exist_ok=True)
    m = L.read_meta(L.WORK / 'base' / 'meta.json')
    vers = L.versions(L.WORK / 'base' / 'raw_code.jam')
    data, V2, chart = chart_data()
    log('chart v2 data ok', chart['same_as_published'])
    T = tables(data, V2, m, vers)
    log('tables: cards %d stages %d chips %d scenes %d events %d' % (len(T['cards']), len(T['stages']), len(T['chips']), len(T['scenes']), len(T['events'])))
    src = JAF_SRC.read_text('utf8')
    assert src.count('/*TABLES*/') == 1
    jaf = src.replace('/*TABLES*/', gen_tables(T))
    (W / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    texts = jaf_strings(L.strip_comments(jaf))
    bad = check_alphabet(texts)
    assert not bad, ('characters outside the font map / proxy set', bad)
    built = L.jaf_literal_encode(L.strip_comments(jaf))
    rest = [c for c in built if ('\uac00' <= c <= '\ud7a3')]
    assert not rest, 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, sites, oldn = compile_and_patch(base, m, vers, built, rt)
    log('compiled: %d functions added, %d same-length sites' % (len(ids), len(sites)))
    nm, inv = invariance(base, out, m, sites, oldn)
    log('invariance ok', inv)
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    # bodies for the VM (live versions of everything new or swapped)
    for fid in list(ids.values()) + sorted({s['fid'] for s in sites}):
        L.cmd('ain', 'dump', '--function', L.symbol(nm, fid), '-o', W / f'built_{fid}.jam', out)
    tables_info = dict(cards=len(T['cards']), stages=len(T['stages']), drawers=len(T['chips']), drawer_scenes=len(T['scenes']),
                       events=len(T['events']), day_marks='computed at run time from the card table (days with cards: %d)' % len({(c['month'], c['day']) for c in T['cards'] if c['day']}),
                       months=list(range(4, 12)), memory_page=12, card_range=T['card_range'], chip_range=T['chip_range'],
                       w1=T['w1'], mlen=T['mlen'])
    L.writej(W / 'tables.json', dict(cards=T['cards'], chips=[{k: v for k, v in ch.items()} for ch in T['chips']], stages=T['stages'],
                                     scenes=T['scenes'], events={str(k): v for k, v in T['events'].items()}, w1=T['w1'], mlen=T['mlen'],
                                     card_range={str(k): v for k, v in T['card_range'].items()}, chip_range={str(k): v for k, v in T['chip_range'].items()}))
    man = dict(
        schema='yoru-calendar-r15.candidate.v1', status='CALENDAR_R15_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, chart=chart, tables=tables_info,
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), same_length_sites=sites, relocated_original_functions=[],
        pinned_new_functions={n: nm['functions'][ids[n]]['address'] for n in PINNED_NEW},
        invariance=inv, native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        session_variables=['YoruKR.T9.Ctx', 'YoruKR.T9.Req', 'YoruKR.T9.Play', 'YoruKR.T9.Playing', 'YoruKR.T9.Unwind', 'YoruKR.T9.Open', 'YoruKR.T9.Lane'],
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
