"""Claude Opus 5.5 (2026-09-28) r22: the event flow chart screen of the menu-bar 「모드」 menu (stage 2), on top of the r21 install
(current.json MOD_MENU_INSTALLED_NATIVE_PASS: AIN 3b9865a8... = the r21 candidate, winmm.dll a4dd9110... = the mod-menu hook).

  python build_chart_r22.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/status/manifest = r22lib BASE_*, the hook DLL = BASE_WINMM_SHA, P: free space
     >= 10 GB, r21 installed (evidence/modmenu_r21 journal COMMITTED, the r21 candidate = the runtime AIN).
  2. data (read only): the r15 tables (r15_calendar/work/build/tables.json - cards, drawers, stages, scenes) and the r19 tables
     (r19_calendar/work/build/tables.json - names, lane-row conditions, 「언제」 lines, drawer display order): both are baked into
     the base already (the verifier checks the base's table functions return them); graph/event_cg.json (thumbnails; must be
     what event_cg_r22.py extracts today); graph/memory.json via event_cg.json (the recollection cells); 증거/replay_kinds.json
     (which kinds replay from the title; absent before the first probe = every scene marked playable, recorded in the manifest).
  3. r22 tables: the chart's cells per tab (4-11월 · 회상 · 그 밖) in display order, each cell's name / when / condition texts
     fitted to the cell (thumbnail cells and small cells have different widths), thumbnails, recollection cells, not-playable scenes,
     the tab / cell positions (float constants: no int->float conversion at run time).
  4. alice ain edit --jaf (declare KR_C*) -> dump -> native_lower -> alice ain edit --jam with the lowered bodies, two hand-written
     bodies (KR_CWait: AFL_Parts_WaitForClick with the KR_CFrame delegate; KR_CReplayRun: C_SceneModeScene@ExecScene's memory-mode
     path with the event number as input) and one-call forwarder bodies for six existing functions (same index / arguments /
     return, new address):
       KR_MDo -> KR_CDoHome, KR_T9Seen -> KR_CSeen, KR_T9State -> KR_CState, KR_T9Legend -> KR_CLegend,
       KR_T18CardPage -> KR_CCardPage, KR_T18EventPage -> KR_CEventPage
  5. two same-length CALLFUNC operand swaps inside unchanged original functions (signature equality, uniqueness checked):
       C_SceneTitle@Update   CALLFUNC C_UserInputManager::IsClickConfig -> KR_CTitleTick   (the title's per-frame poll)
       C_SceneTitle@Run      CALLFUNC ■方向キー処理／削除                -> KR_CTitleServe  (right after the title's wait)
  6. invariance: every base function entry identical except the six forwarded ones (address only); the old CODE identical except
     the two 4-byte operands; MSG1, STR0 prefix identical; the six pinned functions keep entry and every code byte; r15's nine,
     r18's one, r20's seven and r21's two operand sites and r18's eight / r19's five forwarders still in place; native opcode audit.
  7. end gate: the runtime hashes are read again; if Codex installed something meanwhile the candidate is DISCARDED (exit 3).
PACT, EX, FNL, the Manual chart and winmm.dll are not touched. Nothing is written outside r22_chart\\ (runtime, saves, Codex root,
r15-r21: read only).
"""
import sys, io, json, re, struct, shutil, collections, datetime
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r22lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_chart_r22.jaf'
PREFIX = 'KR_C'
PART_BASE, PART_COUNT = 2026092200, 112
CODE = 2026092802                                   # KR_CCode: the title wait ends with it
TAKEN_CODES = {2026092401: 'KR_T8HomePickCode', 2026092801: 'KR_MCode'}
ROOT_Z = 5000                                       # the chart root's Z (children are relative); measured: see 인계 (probe --z)
SLOT_KR = {1: '아침', 2: '밤', 3: '낮', 4: '저녁'}
SLOT_RANK = {1: 0, 3: 1, 4: 2, 2: 3, 0: 9}
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
TAB_NAMES = ['4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '회상', '그 밖']
WHEN_CONT = '\n†　　　'
E_RE = re.compile(r'E\d{4,5}')
R15_SITES, R20_SITES, R21_SITES = 9, 7, 2
R19_FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
               'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
FORWARD = {            # existing function (index kept) -> r22 body (same arguments and return type)
    'KR_MDo': 'KR_CDoHome',               # r21 request dispatch in the home menu: chart -> the chart screen
    'KR_T9Seen': 'KR_CSeen',              # r15: in the chart = global read (MsgSkip / recollection unlock), else IsRegisteredEvent
    'KR_T9State': 'KR_CState',            # r15: in the chart = 1 read / 0 unread (△ / ●), else 2 / 1 / 0 as before
    'KR_T9Legend': 'KR_CLegend',          # r15: the stage list legend in the chart
    'KR_T18CardPage': 'KR_CCardPage',     # r18: card page (the calendar keeps r18's body inside KR_CCardPage)
    'KR_T18EventPage': 'KR_CEventPage',   # r18: scene page (idem)
}
SWAPS = [
    ('C_SceneTitle@Update', 'call', 'C_UserInputManager::IsClickConfig', 0, 'KR_CTitleTick'),
    ('C_SceneTitle@Run', 'call', '■方向キー処理／削除', 0, 'KR_CTitleServe'),
]
EXPECTED_CALLS = {('C_SceneTitle@Update', 'C_UserInputManager::IsClickConfig'): 1, ('C_SceneTitle@Run', '■方向キー処理／削除'): 1}
JAM_BODIES = ['KR_CWait', 'KR_CReplayRun']
SESSION_VARIABLES = ['YoruKR.C.Open', 'YoruKR.C.Ctx', 'YoruKR.C.All', 'YoruKR.C.Play', 'YoruKR.C.TitleReq']
# cell text budgets (full-width units; ASCII = 0.5): thumbnail cells 18 px name in 285 px, 17 px id/when in 155 px, 15 px condition
# in 285 px (2 lines); small cells 18 px name 2 lines, 16 px id + when in 285 px, 15 px condition 2 lines
NAME_THUMB, NAME_SMALL, WHEN_THUMB, IDWHEN_SMALL, COND = 15.5, 15.5, 9.0, 17.5, 18.5
COND_LINES = 2
UNPLAYABLE_NOTE = '재생 불가(게임 안에서만)'


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- base
def runtime_now():
    ptr, rt = L.runtime()
    got = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'NightRemasterPact.afa', 'NightRemasterEX.ex', 'winmm.dll']}
    return ptr, rt, got


def base_is_current(ptr, got):
    return (got['NightRemaster.ain'] == L.BASE_AIN_SHA and got['NightRemasterPact.afa'] == L.BASE_PACT_SHA
            and got['NightRemasterEX.ex'] == L.BASE_EX_SHA and got['winmm.dll'] == L.BASE_WINMM_SHA
            and ptr['status'] == L.BASE_STATUS and ptr['manifest_sha256'] == L.BASE_MANIFEST_SHA)


def code_of(ain_bytes):
    raw = L.unpack(ain_bytes)
    n = struct.unpack_from('<I', raw, 12)[0]
    return raw, raw[16:16 + n], n


def gates():
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase r22lib BASE_* on the new runtime first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    j = L.readj(L.R21_JOURNAL)
    assert j['status'] == 'COMMITTED' and j['after']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r21 not installed as expected', j['status'])
    h = L.readj(L.HOOK_JOURNAL)
    assert h['status'] == 'COMMITTED' and h['after']['winmm.dll'] == L.BASE_WINMM_SHA, ('the mod-menu hook is not installed as expected', h['status'])
    assert L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA, 'the runtime Manual chart moved'
    bp = L.base_paths()
    assert L.sha(bp['ain']) == L.BASE_AIN_SHA
    return ptr, rt, bp, free


def site_list():
    """r15's nine, r18's one, r20's seven and r21's two same-length operand sites (bytes the base must keep)."""
    out = []
    for by, d, n in (('r15', L.R15, R15_SITES), ('r18', L.R18, 1), ('r20', L.R20, R20_SITES), ('r21', L.R21, R21_SITES)):
        s = L.readj(d / 'candidate' / 'manifest.json')['same_length_sites']
        assert len(s) == n, (by, len(s))
        out += [dict(x, by=by) for x in s]
    return out


def sites_applied(code, sites):
    for s in sites:
        assert code[s['site']:s['site'] + 6].hex() == s['after'], ('same-length site not applied', s['by'], s['function'], s.get('replacement'))
    return len(sites)


def body_bytes(code, starts, address, limit):
    import bisect
    i = bisect.bisect_right(starts, address)
    end = starts[i] - 6 if i < len(starts) else limit
    return code[address - 6:end]


def region_ops(raw_path, m, fid):
    """The live body of `fid` as ops, including code after inline lambdas and excluding the lambda bodies (r20 build)."""
    owner = L.raw_symbol(m, fid)
    start = m['functions'][fid]['address']
    lines = Path(raw_path).read_text('utf8').splitlines()
    ops = []
    last = 0
    state = 'seek'
    for line in lines:
        if line.startswith('FUNC '):
            k = int(line.split()[1])
            if state == 'seek':
                if k == fid and last + 6 == start:
                    state = 'in'
                continue
            if state == 'in':
                nm = L.raw_symbol(m, k)
                if nm.startswith(owner.split('@')[0] + '@<lambda : ' + owner + '('):
                    state = 'lambda'
                    continue
                break
            continue
        z = re.match(r'0x([0-9A-Fa-f]+):\s*(.*)', line)
        if not z:
            continue
        last = int(z[1], 16)
        body = z[2]
        if state == 'in' and body:
            if body.startswith('ENDFUNC'):
                continue
            ops.append((last, body))
        elif state == 'lambda' and body.startswith('ENDFUNC'):
            state = 'in'
    assert ops and ops[0][0] == start, (owner, ops[:1], start)
    return ops


# ---------------------------------------------------------------- data
def units(t):
    return sum(0.5 if ord(ch) < 0x80 else 1.0 for ch in t)


def cut(t, budget):
    if units(t) <= budget:
        return t
    out = ''
    for ch in t:
        if units(out + ch) + 1 > budget:
            break
        out += ch
    return out.rstrip(' ·,') + '…'


def wrap(tokens, budget, lines, sep=' · '):
    """Tokens into at most `lines` lines of <= budget units, breaking between tokens (a token longer than a line is cut);
    tokens that do not fit are dropped from the end and marked with 「…」."""
    out, cur = [], ''
    rest = list(tokens)
    while rest:
        t = rest[0]
        trial = t if not cur else cur + sep + t
        if units(trial) <= budget:
            cur = trial
            rest.pop(0)
            continue
        if not cur:                      # one token wider than a line
            cur = cut(t, budget)
            rest.pop(0)
            continue
        out.append(cur)
        cur = ''
        if len(out) == lines:
            break
    if cur and len(out) < lines:
        out.append(cur)
    if rest:
        last = out[-1] if out else ''
        while last and units(last + ' …') > budget:
            last = last[:-1]
        out[-1] = last.rstrip(' ·,') + ' …'
    return out


def when_tokens(text):
    """An r19 「언제」 text (colour marks, continuation lines) as tokens."""
    t = text.replace(WHEN_CONT, ' · ').replace('\n', ' · ')
    t = re.sub(r'[†‡¶〓]', '', t)
    return [x.strip() for x in re.split(r' · | / ', t) if x.strip()]


def load_data():
    r15 = L.readj(L.R15 / 'work' / 'build' / 'tables.json')
    r19 = L.readj(L.R19 / 'work' / 'build' / 'tables.json')
    cg = json.loads((L.FLOW / 'graph' / 'event_cg.json').read_text('utf8'))
    import event_cg_r22 as ECG
    buf = io.StringIO()
    fresh = ECG.build()
    assert ECG.comparable(fresh) == ECG.comparable(cg), 'graph/event_cg.json is not what event_cg_r22.py extracts today: rerun it'
    assert all(v['ok'] for v in cg['gates'].values()), ('event_cg gates', {k: v['ok'] for k, v in cg['gates'].items()})
    sched = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    kinds_path = L.EVID / 'replay_kinds.json'
    kinds = L.readj(kinds_path) if kinds_path.exists() else None
    return r15, r19, cg, sched, kinds


def event_kinds(r15, sched):
    """Replay kind of every event (the per-kind probe runs one or more of each; 증거/replay_kinds.json holds the verdicts)."""
    ev = {e['id']: e for e in sched['events']}
    kind = {}
    for c in r15['cards']:
        for i, no in enumerate(c['stages']):
            k = 'dungeon' if c['lane'] == 8 else ('dated' if c['day'] > 0 else 'undated')
            if i > 0:
                k = 'stage_' + k
            kind[no] = k
    for ch in r15['chips']:
        kd = KINDS[ch['kind']]
        for no in ch['scenes']:
            kind[no] = {'prio': 'pool_talk', 'after': 'pool_talk', 'turned': 'pool_talk', 'invite': 'pool_invite', 'walk': 'pool_walk',
                        'etc': 'system', 'mem': 'memory', 'unused': 'unused'}[kd]
    assert len(kind) == 1164
    flags = {}
    for no in kind:
        e = ev[no]
        f = []
        if e.get('has_choice'):
            f.append('choice')
        if (e.get('effects') or {}).get('event_battle'):
            f.append('battle')
        flags[no] = f
    return kind, flags


def chart_cells(r15, r19, cg, sched, kinds):
    cards = r15['cards']
    heads = {int(k): v for k, v in r19['heads'].items()}
    conds = {int(k): v for k, v in r19['conds'].items()}
    ev_head = {int(k): v for k, v in r19['ev_head'].items()}
    whens = {int(k): v for k, v in r19['whens'].items()}
    order = r19['order']
    thumb = {int(k): v['thumb'] for k, v in cg['events'].items()}
    kind, flags = event_kinds(r15, sched)
    noplay = {}
    verdict = (kinds or {}).get('verdicts', {})
    for no in kind:
        bad = [x for x in [kind[no]] + flags[no] if verdict.get(x) == 'fail']
        noplay[no] = 1 if bad else 0
    # visible scene order per drawer (r19 KR_T19SceneAt)
    scene_at = {}
    j = 0
    for ch in r15['chips']:
        scene_at[ch['c']] = order[j:j + ch['size']]
        assert sorted(scene_at[ch['c']]) == sorted(ch['scenes'])
        j += ch['size']
    assert j == len(order) == 760
    tabs = []
    for t in range(10):
        cells = []
        if t <= 7:
            m = t + 4
            ks = [c for c in cards if c['month'] == m]
            ks.sort(key=lambda c: (0 if c['day'] > 0 and c['lane'] != 8 else (2 if c['lane'] == 8 else 1),
                                   c['day'] if c['day'] > 0 else 99, SLOT_RANK[c['slot']], c['lane'], c['k']))
            cells += [('card', c['k']) for c in ks]
            chips = [ch for ch in r15['chips'] if ch['month'] == m]
            chips.sort(key=lambda ch: (ch['lane'], ch['kind'], ch['c']))
            for ch in chips:
                cells += [('scene', no) for no in scene_at[ch['c']]]
        else:
            chips = [ch for ch in r15['chips'] if ch['month'] == 12 and ((9 <= ch['lane'] <= 15) if t == 8 else ch['lane'] >= 16)]
            chips.sort(key=lambda ch: (ch['lane'], ch['c']))
            for ch in chips:
                cells += [('scene', no) for no in scene_at[ch['c']]]
        tabs.append(cells)
    total = sum(len(c) for c in tabs)
    assert total == len(cards) + 760, total
    rows = []
    for t, cells in enumerate(tabs):
        for kindc, x in cells:
            if kindc == 'card':
                c = cards[x]
                no = c['entry']
                when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
                if c['slot']:
                    when += ' ' + SLOT_KR[c['slot']]
                toks = heads[x].split(' · ')
                if toks and toks[0] == when:
                    toks = toks[1:]
                name_toks = toks
                cond_toks = [y for y in conds[x].split(' · ') if y] if conds.get(x) else []
                ref = 100000 + x
            else:
                no = x
                toks = ev_head[no].split(' · ')
                month = None
                if toks and re.fullmatch(r'\d{1,2}월', toks[0]):
                    month = toks[0]
                    toks = toks[1:]
                if toks[:2] == ['회상', '그 밖']:
                    toks = toks[2:]
                when = month or ''
                name_toks = toks
                cond_toks = when_tokens(whens[no])
                ref = no
            th = thumb.get(no)
            if th:
                name = cut(' · '.join(name_toks), NAME_THUMB)
                w = cut(when, WHEN_THUMB)
            else:
                name = '\n'.join(wrap(name_toks, NAME_SMALL, 2))
                w = when
            cl = wrap(cond_toks, COND, COND_LINES) if cond_toks else []
            if noplay[no]:
                cl = (cl[:COND_LINES - 1] if cl else []) + [UNPLAYABLE_NOTE]
            cond = '\n'.join(cl)
            idw = ('● E%05d' % no) + ('\n' + w if th else '　' + w)
            for line in idw.split('\n'):
                assert units(line) <= (WHEN_THUMB if th else IDWHEN_SMALL) + 0.01, ('id/when line too wide', no, line)
            for line in name.split('\n'):
                assert units(line) <= (NAME_THUMB if th else NAME_SMALL) + 0.01, ('name line too wide', no, line)
            for line in cond.split('\n'):
                assert units(line) <= COND + 0.01, ('condition line too wide', no, line)
            assert not re.search(r'[†‡¶〓]', name + cond + w), (no, name, cond, w)
            rows.append(dict(tab=t, ref=ref, no=no, card=kindc == 'card', name=name, when=w, cond=cond, thumb=th or '',
                             kind=kind[no], flags=flags[no], noplay=noplay[no]))
    first, i = [], 0
    for cells in tabs:
        first.append(i)
        i += len(cells)
    return rows, first, kind, flags, noplay


def mem_cells(cg, sched):
    """Recollection cell (page * 100 + slot, 1-based) of every event the game's recollection check can open: the replay events of the
    76 cells, the chain-only replay events under them (their root cell) and the source events the cells need (needEvNo)."""
    out = {}
    cells = cg['memory_cells']
    for c in cells:
        out[c['play']] = c['page'] * 100 + c['slot']
    ev = {e['id']: e for e in sched['events']}
    changed = True
    while changed:
        changed = False
        for no, code in list(out.items()):
            for t in ev[no].get('chains_to') or []:
                if ev[t]['category'] == 'memory_replay' and t not in out:
                    out[t] = code
                    changed = True
    for c in cells:
        out.setdefault(c['need'], c['page'] * 100 + c['slot'])
    return out


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


def fl(v):
    return '%.1f' % v


def gen_tables(rows, first, mem, noplay, thumbs):
    n = len(rows)
    ends = first[1:] + [n]
    tab_x = [24 + t * 120 for t in range(10)]
    tab_tx = [(112 - units(nm) * 22) / 2 for nm in TAB_NAMES]
    out = [tree('int', 'KR_CTabFirst', 't', list(enumerate(first)), 0),
           tree('int', 'KR_CTabEnd', 't', list(enumerate(ends)), 0),
           tree('int', 'KR_CCellRef', 'i', [(i, r['ref']) for i, r in enumerate(rows)], -1),
           tree('string', 'KR_CCellName', 'i', [(i, q(r['name'])) for i, r in enumerate(rows)], '""'),
           tree('string', 'KR_CCellWhen', 'i', [(i, q(r['when'])) for i, r in enumerate(rows) if r['when']], '""'),
           tree('string', 'KR_CCellCond', 'i', [(i, q(r['cond'])) for i, r in enumerate(rows) if r['cond']], '""'),
           tree('string', 'KR_CThumb', 'no', [(no, q(t)) for no, t in sorted(thumbs.items()) if t], '""'),
           tree('int', 'KR_CMemCell', 'no', sorted(mem.items()), 0),
           tree('int', 'KR_CNoPlay', 'no', [(no, v) for no, v in sorted(noplay.items()) if v], 0),
           tree('float', 'KR_CTabX', 't', [(t, fl(x)) for t, x in enumerate(tab_x)], '0.0'),
           tree('float', 'KR_CTabTx', 't', [(t, fl(x)) for t, x in enumerate(tab_tx)], '0.0'),
           tree('float', 'KR_CCellX', 's', [(s, fl(24 + (s % 4) * 309)) for s in range(12)], '0.0'),
           tree('float', 'KR_CCellY', 's', [(s, fl(114 + (s // 4) * 182)) for s in range(12)], '0.0')]
    return '\n'.join(out)


def check_alphabet(texts):
    enc_ok = L.proxy_alphabet()
    carrier = {0x9D, 0x9E, 0x9F} | set(range(0xE0, 0xEB))
    bad = collections.Counter()
    for t in texts:
        for ch in t:
            if ch in enc_ok or ch in '\n\r\t':
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


_SYMS = {}


def fid_sym(m, name):
    """Index by the dump symbol (duplicate names carry #n); the symbol table is computed once (L.symbol is O(n) per call)."""
    key = id(m)
    if key not in _SYMS:
        seen = collections.Counter()
        table = collections.defaultdict(list)
        for f in m['functions']:
            n = L.raw_symbol(m, f['index'])
            raw = f['name']
            table[n + (f'#{seen[raw]}' if seen[raw] else '')].append(f['index'])
            seen[raw] += 1
        _SYMS[key] = table
    hits = _SYMS[key].get(name, [])
    assert len(hits) == 1, (name, hits)
    return hits[0]


def forwarder(m, fid, target):
    f = m['functions'][fid]
    assert all(a['type'][0] in (10, 12, 47) for a in f['arguments']), ('forwarders pass int/bool/string arguments only', f['name'])
    assert f['return-type'][0] in (0, 10, 12, 47), ('forwarder return type', f['name'], f['return-type'])
    body = ''.join(f"\t.LOCALREF {a['name']}\n" + ('\tA_REF\n' if a['type'][0] == 12 else '') for a in f['arguments'])
    return f"FUNC {fid}\n{body}\tCALLFUNC {target}\n\tRETURN\nENDFUNC {L.raw_symbol(m, fid)}\n"


def jam_bodies(m, dm, ids):
    """KR_CWait (the chart's wait: AFL_Parts_WaitForClick with the KR_CFrame delegate and key cancel) and KR_CReplayRun
    (C_SceneModeScene@ExecScene's memory-mode path, the event name from LSys3xScript::GetLabelName(no) instead of the EX
    recollection table). The method / constructor numbers are looked up by name and the locals checked against the jaf."""
    fn = lambda n: L.fid_of(m, n)
    get, put, ctor = fid_sym(m, 'C_GameFlags@IsExecNameEntry::get'), fid_sym(m, 'C_GameFlags@IsExecNameEntry::set'), fid_sym(m, 'C_SceneGame@0')
    assert (get, put, ctor) == (26526, 26528, 28164), (get, put, ctor)          # the numbers C_SceneModeScene@ExecScene uses
    rr = dm['functions'][ids['KR_CReplayRun']]
    names = [a['name'] for a in rr['arguments']] + [v['name'] for v in rr['variables']]
    assert names[:6] == ['no', 'ctx', 'evName', 'b', 'sg', 'dummy'], names
    ex = m['functions'][fn('C_SceneModeScene@ExecScene')]
    exn = [a['name'] for a in ex['arguments']] + [v['name'] for v in ex['variables']]
    assert exn[2:4] == ['evName', 'b'] and [v['type'] for v in ex['variables']][:4] == [v['type'] for v in rr['variables']][:4], (exn, ex['variables'], rr['variables'])
    b = {}
    b['KR_CWait'] = (f"\tPUSH -1\n\tPUSH {ids['KR_CFrame']}\n\tDG_NEW_FROM_METHOD\n\tPUSH 1\n\tCALLFUNC AFL_Parts_WaitForClick\n\tRETURN\n")
    b['KR_CReplayRun'] = (
        "\tPUSHLOCALPAGE\n\tPUSH 2\n\tX_DUP 2\n\tX_REF 1\n\tDELETE\n\t.LOCALREF no\n\tCALLFUNC LSys3xScript::GetLabelName\n\tX_ASSIGN 1\n\tPOP\n"
        "\tCALLFUNC AFL_MemoryModeEvent_Begin\n\tIFNZ kr_c_play\n\tJUMP kr_c_clean\n"
        "kr_c_play:\n"
        f"\tPUSHLOCALPAGE\n\tPUSH 3\n\t.GLOBALREF Flags\n\tPUSH {get}\n\tCALLMETHOD 0\n\tX_ASSIGN 1\n\tPOP\n"
        f"\t.GLOBALREF Flags\n\tPUSH {put}\n\tPUSH 0\n\tX_DUP 1\n\tX_MOV 4 1\n\tCALLMETHOD 1\n\tPOP\n"
        f"\tPUSHLOCALPAGE\n\tPUSH 4\n\tNEW C_SceneGame {ctor}\n\t.LOCALREF dummy\n\tDELETE\n\tPUSHLOCALPAGE\n\tPUSH 5\n\tX_MOV 3 2\n\tX_ASSIGN 1\n\tX_ASSIGN 1\n\tSP_INC\n\t.LOCALDELETE dummy\n"
        "\t.LOCALREF evName\n\tA_REF\n\tCALLFUNC LSys3xScript::Prepare\n\tCALLFUNC LSys3xScript::RunEvent\n\tPOP\n"
        "\tPUSHLOCALPAGE\n\tPUSH 4\n\tX_DUP 2\n\tX_REF 1\n\tPUSH -1\n\tX_MOV 2 1\n\tDELETE\n\tX_ASSIGN 1\n\tSP_INC\n"
        f"\t.GLOBALREF Flags\n\tPUSH {put}\n\t.LOCALREF b\n\tX_DUP 1\n\tX_MOV 4 1\n\tCALLMETHOD 1\n\tPOP\n"
        "\tCALLFUNC AFL_MemoryModeEvent_End\n\t.LOCALDELETE dummy\n\t.LOCALDELETE sg\n"
        "kr_c_clean:\n\tCALLFUNC AFL_MemoryModeEvent_Cleanup\n\tRETURN\n")
    out = {}
    for name, body in b.items():
        out[ids[name]] = f"FUNC {ids[name]}\n{body}ENDFUNC {name}\n"
    return out


def compile_and_patch(base, m, raw_path, jaf_text):
    W.mkdir(parents=True, exist_ok=True)
    O.mkdir(parents=True, exist_ok=True)
    (W / 'helpers.jaf').write_text(jaf_text, 'utf8')
    decl = W / 'declared.ain'
    L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, base, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl)
    dm = L.read_meta(W / 'declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    assert all(n.startswith(PREFIX) for n in ids), [n for n in ids if not n.startswith(PREFIX)]
    assert set(JAM_BODIES) <= set(ids)
    changed = [f['index'] for f, g in zip(m['functions'], dm['functions']) if f != g and f['index'] != 0]
    assert not changed, ('the jaf declaration touched existing functions', changed[:5])
    jams = jam_bodies(m, dm, ids)
    patch = []
    for f in added:
        if f['index'] in jams:
            patch.append(jams[f['index']])
            continue
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
    sites = []
    for owner, kind, oldfn, nth, newfn in SWAPS:
        assert kind == 'call'
        fid = L.fid_of(m, owner)
        oldid = fid_sym(m, oldfn)
        newid = ids[newfn]
        assert sig(dm['functions'][newid]) == sig(m['functions'][oldid]), (newfn, sig(dm['functions'][newid]), sig(m['functions'][oldid]))
        ops = region_ops(raw_path, m, fid)
        key = f'CALLFUNC 0x{oldid:x}'
        hits = [i for i, (ad, op) in enumerate(ops) if op == key]
        assert len(hits) == EXPECTED_CALLS[(owner, oldfn)], (owner, oldfn, len(hits))
        ad = ops[hits[nth]][0]
        before = struct.pack('<Hi', 0x30, oldid)
        after = struct.pack('<Hi', 0x30, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (owner, hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=owner, fid=fid, function_address=m['functions'][fid]['address'], site=ad,
                          site_offset=ad - m['functions'][fid]['address'], kind='CALLFUNC', original=oldfn, original_fid=oldid,
                          replacement=newfn, replacement_fid=newid, before=before.hex(), after=after.hex(), operand_bytes=[ad + 2, ad + 6],
                          occurrence=nth, calls_of_original_in_function=len(hits)))
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, forwarded, sites, oldn


def invariance(base, out, m, forwarded, sites, oldn, old_sites, bp):
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
    allowed = set(x for s in sites for x in range(s['site'] + 2, s['site'] + 6))
    diff = [i for i in range(oldn) if old[16 + i] != new[16 + i]]
    assert set(diff) <= allowed and len(diff) > 0, [hex(x) for x in diff if x not in allowed][:10]
    assert L.raw_messages(base.read_bytes())[3] == L.raw_messages(out.read_bytes())[3], 'MSG1 changed'
    so, sn = L.strings(old)[2], L.strings(new)[2]
    assert sn[:len(so)] == so, 'STR0 prefix changed'
    _, code, _ = code_of(out.read_bytes())
    n_old = sites_applied(code, old_sites)
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
    for s in sites:
        assert s['function'] not in L.PINNED_ALL, ('a swap inside a pinned function', s)
    for name in FORWARD:
        assert name not in L.PINNED_ALL, ('a pinned function forwarded', name)
    cvers = L.versions(W / 'candidate_raw_code.jam')
    for old_, new_ in list(R19_FORWARD.items()) + list(R18_FORWARD.items()) + list(FORWARD.items()):
        v = L.live_version(nm, cvers, L.fid_of(nm, old_))
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
    return nm, dict(original_function_entries_identical_except_forwarded=True, forwarded=sorted(FORWARD),
                    other_metadata_identical=sorted(k for k in m if k != 'functions'), old_code_bytes_changed=len(diff),
                    old_code_changes_only_at_swapped_operands=True, MSG1_exact=True, STR0_prefix_exact=True,
                    STR0_added=len(sn) - len(so), functions_added=len(nm['functions']) - len(m['functions']), pinned=pinned,
                    earlier_same_length_sites_kept=n_old)


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
    ptr, rt, bp, free = gates()
    base = bp['ain']
    log('gates ok', L.BASE_AIN_SHA[:16], ptr['status'], 'P: free %.1f GB' % (free / 1024 ** 3))
    W.mkdir(parents=True, exist_ok=True)
    m = L.read_meta(bp['meta'])
    vers = L.versions(bp['raw'])
    old_sites = site_list()
    _, bcode, _ = code_of(base.read_bytes())
    log('base keeps the r15/r18/r20/r21 same-length sites:', sites_applied(bcode, old_sites))
    for old_, new_ in list(R18_FORWARD.items()) + list(R19_FORWARD.items()):
        f = m['functions'][L.fid_of(m, old_)]
        v = L.live_version(m, vers, f['index'])
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(m, new_), 'RETURN'], ('forwarder not in the base', old_)
    for c, name in TAKEN_CODES.items():
        v = L.live_version(m, vers, L.fid_of(m, name))
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][:2] == ['PUSH 0x%x' % c, 'RETURN'], (name, 'moved')
    assert CODE not in TAKEN_CODES
    r15, r19, cg, sched, kinds = load_data()
    rows, first, kind, flags, noplay = chart_cells(r15, r19, cg, sched, kinds)
    mem = mem_cells(cg, sched)
    thumbs = {int(k): v['thumb'] for k, v in cg['events'].items() if v['thumb']}
    log('cells', len(rows), 'tabs', [len([r for r in rows if r['tab'] == t]) for t in range(10)], 'thumb cells',
        sum(1 for r in rows if r['thumb']), 'mem events', len(mem), 'not playable', sum(noplay.values()),
        'replay kinds', 'probed' if kinds else 'NOT PROBED (all playable)')
    jaf = JAF_SRC.read_text('utf8')
    assert jaf.count('/*TABLES*/') == 1 and jaf.count('@@ROOT_Z@@') == 1
    assert ('int KR_CCode() { return %d; }' % CODE) in jaf
    jaf = jaf.replace('/*TABLES*/', gen_tables(rows, first, mem, noplay, thumbs)).replace('@@ROOT_Z@@', str(ROOT_Z))
    (W / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    texts = jaf_strings(L.strip_comments(jaf))
    bad = check_alphabet(texts)
    assert not bad, ('characters outside the font map / proxy set', bad)
    built = L.jaf_literal_encode(L.strip_comments(jaf))
    assert not [c for c in built if ('\uac00' <= c <= '\ud7a3')], 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, forwarded, sites, oldn = compile_and_patch(base, m, bp['raw'], built)
    log('compiled: %d functions added, %d forwarders, %d same-length sites' % (len(ids), len(forwarded), len(sites)))
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    nm, inv = invariance(base, out, m, forwarded, sites, oldn, old_sites, bp)
    log('invariance ok', {k: v for k, v in inv.items() if k != 'pinned'})
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    L.writej(W / 'cells.json', dict(rows=rows, first=first, mem={str(k): v for k, v in mem.items()},
                                    noplay={str(k): v for k, v in noplay.items() if v}, kinds={str(k): v for k, v in kind.items()},
                                    flags={str(k): v for k, v in flags.items() if v}))
    ptr2, rt2, got2 = runtime_now()
    if not base_is_current(ptr2, got2):
        discard('runtime moved during the build', dict(got2, status=ptr2['status'], manifest_sha256=ptr2['manifest_sha256']))
    man = dict(
        schema='yoru-chart-r22.candidate.v1', status='CHART_R22_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, winmm_sha256=L.BASE_WINMM_SHA,
                  chart_sha256=L.BASE_CHART_SHA, r21_installed=True, hook_installed=True, checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False, chart_changed=False, winmm_changed=False,
        data=dict(r15_tables_sha256=L.sha(L.R15 / 'work' / 'build' / 'tables.json'), r19_tables_sha256=L.sha(L.R19 / 'work' / 'build' / 'tables.json'),
                  event_cg_sha256=L.sha(L.FLOW / 'graph' / 'event_cg.json'), schedule_sha256=L.sha(L.FLOW / 'graph' / 'schedule.json'),
                  replay_kinds=(L.sha(L.EVID / 'replay_kinds.json') if kinds else None),
                  cells=len(rows), per_tab=[len([r for r in rows if r['tab'] == t]) for t in range(10)],
                  thumbnail_cells=sum(1 for r in rows if r['thumb']), small_cells=sum(1 for r in rows if not r['thumb']),
                  memory_events=len(mem), not_playable_events=sum(noplay.values()), cell_order='dated cards (day, slot) -> undated cards -> '
                  'dungeon cards -> drawer scenes (lane, kind, r19 display order); 회상 = memory drawers (page, cell / chain order); 그 밖 = unused'),
        protocol=dict(design='ingame/설계_v4_메뉴바차트.md 「C」 + 「정정(09-28 06시)」', commands_on_title=['chart', 'unlock_all', 'unlock_revert', 'reset_all', 'reset_restore'],
                      title_end_code=CODE, home='r21 KR_MHomeRun unchanged; KR_MDo forwarded to KR_CDoHome'),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=JAM_BODIES, forwarded_functions=forwarded,
        r18_forwarders_kept=sorted(R18_FORWARD), r19_forwarders_kept=sorted(R19_FORWARD), same_length_sites=sites,
        earlier_same_length_sites_kept=inv['earlier_same_length_sites_kept'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], invariance=inv, root_z=ROOT_Z, parts=dict(first=PART_BASE, count=PART_COUNT),
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        session_variables_new=SESSION_VARIABLES, new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
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
