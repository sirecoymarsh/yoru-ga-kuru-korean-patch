"""Claude Opus 5.5 (2026-09-28) r23: the affinity figures (설계_v3 「r23 요구」) on top of the r22 install (current.json
MOD_MENU_R2_INSTALLED_NATIVE_PASS: AIN af1026bb... = the r22 candidate, winmm.dll a72b1b9d... = the mod-menu hook r2).

  python build_feeling_r23.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/winmm/status/manifest = r23lib BASE_*, P: free space >= 10 GB, r22 installed
     (evidence/chart_r22 journal COMMITTED, the r22 candidate = the runtime AIN), the hook r2 installed (mod_menu_r2 journal).
  2. game code (read from the base AIN, never guessed): C_FeelingView@Update (a moon = 60, at most 2 moons -> the maximum 120),
     @CreateMark (moon phases), @Init (the moons at 374,66 and the 「친밀도」 label at 374,96 under the status root, z 200 / 250),
     @Enabled (Classic game mode or a person outside 2..5 -> no moons), C_Ability@GetFeeling (= m_nFeeling / GetFeelingRate) and
     @GetFeelingRate (per person), C_SysVoice::GetFeelingRank_5 (the rank boundaries), C_HomeStatusView@IsShowFeelingPage
     (pages 0 and 1) - every constant the jaf and the verifier use is asserted here and written to the manifest.
  3. data (read only): graph/schedule.json feeling_gate triggers (28: 11 priority talks + 5 conditional calls + 8 E30152
     branches + 4 E10501 「highest」 branches; r19 put them there) = the r19 tables' affinity list; their r19 names (r19 tables
     ev_head = the base's KR_T19EvHead) must fit one 18 px line of the 「이벤트」 page (measured glyph advances, 증거/metrics).
  4. alice ain edit --jaf (declare KR_T23*) -> dump -> native_lower -> alice ain edit --jam with the lowered bodies and three
     hand-written ones (KR_T23FeelShow / KR_T23FvGone: CALLMETHOD targets that pass `this` on; KR_T23FvChara: the moon's person).
  5. three same-length operand swaps (signature equality, uniqueness and the call shape checked):
       C_HomeStatusView@SetActivePage  PUSH C_HomeStatusView@IsShowFeelingPage -> KR_T23FeelShow  (CALLMETHOD target)
       C_FeelingView@1 (destructor)    PUSH C_FeelingView@DeleteMarks        -> KR_T23FvGone    (CALLMETHOD target)
       KR_T20StActiveOf (r20)          CALLFUNC KR_T20StDraw                  -> KR_T23StDraw    (CALLFUNC)
  6. invariance: every base function entry identical (no forwarder in r23); the old CODE identical except the three 4-byte operands;
     MSG1, STR0 prefix identical; the six pinned functions keep entry and every code byte; r15's nine, r18's one, r20's seven,
     r21's two and r22's two operand sites and the r18 (8) / r19 (5) / r22 (6) forwarders in place; native opcode audit.
  7. end gate: the runtime hashes are read again; if Codex installed something meanwhile the candidate is DISCARDED (exit 3).
PACT, EX, FNL, the Manual chart and winmm.dll are not touched. Nothing is written outside r23_feeling\\ (runtime, saves, Codex
root, r15-r22: read only).
"""
import sys, json, re, struct, shutil, collections, datetime
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r23lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_feeling_r23.jaf'
PREFIX = 'KR_T23'
MOON_PART = 2026092330
TAKEN_PARTS = [(2026092001, 2026092028, 'r20'), (2026092200, 2026092311, 'r22'), (2026091500, 2026091701, 'r15-r17')]
ST_PANEL_Z, ST_TEXT_Z = 40, 41              # r20's page-4 panel / text (relative to the status root)
MOON_Z = 260                                # above the moons (200) and the 「친밀도」 label (250), relative to the status root
MOON_GAP = 18                               # the text starts 18 px under the label's top (the label is 44 x 16: explore probe)
ST_TEXT_MAX_PX = 318                        # the page-4 text area: x 52 .. 370 under the root (r20)
METRICS = {18: dict(full=14, digit=9, space=5, other=6), 20: dict(full=16, digit=10, space=5, other=7),
           22: dict(full=17, digit=11, space=6, other=7), 24: dict(full=19, digit=12, space=6, other=8)}   # measured (work/explore)
R15_SITES, R20_SITES, R21_SITES, R22_SITES = 9, 7, 2, 2
R19_FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
               'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
R22_FORWARD = {'KR_MDo': 'KR_CDoHome', 'KR_T9Seen': 'KR_CSeen', 'KR_T9State': 'KR_CState', 'KR_T9Legend': 'KR_CLegend',
               'KR_T18CardPage': 'KR_CCardPage', 'KR_T18EventPage': 'KR_CEventPage'}
SWAPS = [   # (owner, kind, original callee, occurrence, replacement, the ops that must follow a method target's PUSH)
    ('C_HomeStatusView@SetActivePage', 'method', 'C_HomeStatusView@IsShowFeelingPage', 0, 'KR_T23FeelShow', ['CALLMETHOD 0x0', 'CALLMETHOD 0x1', 'RETURN']),
    ('C_FeelingView@1', 'method', 'C_FeelingView@DeleteMarks', 0, 'KR_T23FvGone', ['CALLMETHOD 0x0']),
    ('KR_T20StActiveOf', 'call', 'KR_T20StDraw', 0, 'KR_T23StDraw', None),
]
EXPECTED_CALLS = {('C_HomeStatusView@SetActivePage', 'C_HomeStatusView@IsShowFeelingPage'): 1,
                  ('C_FeelingView@1', 'C_FeelingView@DeleteMarks'): 1,
                  ('KR_T20StActiveOf', 'KR_T20StDraw'): 1}
JAM_BODIES = ['KR_T23FeelShow', 'KR_T23FvGone', 'KR_T23FvChara']
SLOTS = {('C_HomeStatusView', 'm_FeelingView'): 9, ('C_HomeStatusView', 'm_CharaNo'): 11, ('C_HomeStatusView', '<NowPage>'): 16,
         ('C_FeelingView', 'm_Root'): 0, ('C_FeelingView', 'm_Label'): 3, ('C_FeelingView', 'm_CharaNo'): 5,
         ('C_Ability', 'id'): 0, ('C_Ability', 'm_nFeeling'): 24}
OP_CODE = {'>=': 0, '<': 1, 'highest': 2}


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
    assert base_is_current(ptr, got), ('runtime moved: rebase r23lib BASE_* on the new runtime first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    j = L.readj(L.R22_JOURNAL)
    assert j['status'] == 'COMMITTED' and j['after']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r22 not installed as expected', j['status'])
    h = L.readj(L.HOOK_JOURNAL)
    assert h['status'] == 'COMMITTED' and h['after']['winmm.dll'] == L.BASE_WINMM_SHA, ('the mod-menu hook r2 is not installed as expected', h['status'])
    assert L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA, 'the runtime Manual chart moved'
    bp = L.base_paths()
    assert L.sha(bp['ain']) == L.BASE_AIN_SHA
    return ptr, rt, bp, free


def site_list():
    """r15's nine, r18's one, r20's seven, r21's two and r22's two same-length operand sites (bytes the base must keep)."""
    out = []
    for by, d, n in (('r15', L.R15, R15_SITES), ('r18', L.R18, 1), ('r20', L.R20, R20_SITES), ('r21', L.R21, R21_SITES), ('r22', L.R22, R22_SITES)):
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


# ---------------------------------------------------------------- game code (read, asserted, recorded)
def dump_fn(ain, name, d):
    d.mkdir(parents=True, exist_ok=True)
    path = d / (re.sub(r'[^0-9A-Za-z_]', '_', name) + '.jam')
    if not path.exists():
        L.cmd('ain', 'dump', '--function', name, '-o', path, ain)
    ops = []
    for line in path.read_text('utf8').splitlines():
        s = line.strip()
        if not s or s.startswith((';', 'FUNC ', 'ENDFUNC', 'EOF')) or re.match(r'^0x[0-9a-f]+:$', s):
            continue
        ops.append(s)
    return ops


def f32(i):
    return struct.unpack('<f', struct.pack('<i', i))[0]


def find_seq(ops, seq, start=0):
    for i in range(start, len(ops) - len(seq) + 1):
        if ops[i:i + len(seq)] == seq:
            return i
    return -1


def game_code(bp, m):
    """Every constant r23 depends on, read from the base AIN (the named dump of single functions)."""
    d = W / 'game'
    ain = bp['ain']
    fn = lambda n: L.fid_of(m, n)
    up = dump_fn(ain, 'C_FeelingView@Update', d)
    i = find_seq(up, ['.LOCALREF feelVal', 'PUSH 1', 'SUB', 'PUSH 60', 'DIV', 'PUSH 1', 'ADD'])
    assert i >= 0, 'C_FeelingView@Update: num = (feelVal - 1) / 60 + 1 not found'
    j = find_seq(up, ['PUSH 2', '.LOCALREF num', 'CALLHLL Math Min 0'])
    assert j >= 0, 'C_FeelingView@Update: dispNum = Math.Min(2, num) not found'
    k = find_seq(up, ['.LOCALREF feelVal', 'PUSH 1', 'SUB', 'PUSH 60', 'MOD'])
    assert k >= 0 and find_seq(up, ['.LOCALASSIGN val 59']) >= 0, 'C_FeelingView@Update: the fill of the last moon changed'
    assert find_seq(up, ['.LOCALREF feelVal', 'PUSH 0', 'EQUALE']) >= 0, 'C_FeelingView@Update: the empty-moon case changed'
    per_moon, moons = 60, 2
    cm = dump_fn(ain, 'C_FeelingView@CreateMark', d)
    phases = [int(cm[x + 1].split()[1]) for x in range(len(cm) - 2) if cm[x] == '.LOCALREF val' and cm[x + 1].startswith('PUSH ') and cm[x + 2] == 'GTE']
    assert phases == [59, 48, 36, 24, 12, 0], phases
    assert '"シス／親密度／黄月／%D"' in ' '.join(cm) or any('黄月' in o for o in cm), 'moon CG names changed'
    rank = dump_fn(ain, 'C_SysVoice::GetFeelingRank_5', d)
    bounds = [int(rank[x + 1].split()[1]) for x in range(len(rank) - 2) if rank[x] == '.LOCALREF nFeeling' and rank[x + 1].startswith('PUSH ') and rank[x + 2] == 'LTE']
    assert bounds == [15, 30, 45, 60], bounds
    assigned = [int(o.split()[2]) for o in rank if o.startswith('.LOCALASSIGN nRank ')]
    assert assigned == [0, 0, 1, 2, 3, 4], assigned
    assert find_seq(rank, ['.LOCALREF pa', 'PUSH %d' % fn('C_Ability@GetFeeling'), 'CALLMETHOD 0']) >= 0, 'GetFeelingRank_5 no longer reads GetFeeling'
    gf = dump_fn(ain, 'C_Ability@GetFeeling', d)
    assert gf[:5] == ['.STRUCTREF C_Ability m_nFeeling', 'PUSHSTRUCTPAGE', 'PUSH %d' % fn('C_Ability@GetFeelingRate'), 'CALLMETHOD 0', 'DIV'], gf
    rt_ = dump_fn(ain, 'C_Ability@GetFeelingRate', d)
    assert rt_[0] == '.STRUCTREF C_Ability id' and rt_[1].startswith('SWITCH '), rt_[:2]
    sw = m['switches'][int(rt_[1].split()[1])]
    rates = {}
    for x, o in enumerate(rt_):
        z = re.match(r'\.CASE \d+:\d+ (\d+)$', o)
        if z:
            assert rt_[x + 1].startswith('PUSH ') and rt_[x + 2] == 'RETURN', rt_[x:x + 3]
            rates[int(z.group(1))] = int(rt_[x + 1].split()[1])
    assert sorted(rates) == sorted(c['value'] for c in sw['cases']), (rates, sw)
    tail = [o for o in rt_ if o.startswith('PUSH ')]
    default = int(tail[-2].split()[1])
    assert rates == {2: 420, 3: 420, 4: 370, 5: 290, 6: 540, 7: 500, 8: 420} and default == 420, (rates, default)
    en = dump_fn(ain, 'C_FeelingView@Enabled', d)
    gm = fid_sym(m, 'C_GameFlags@GameMode::get')
    assert en[:5] == ['.GLOBALREF Flags', 'PUSH %d' % gm, 'CALLMETHOD 0', 'PUSH 1', 'EQUALE'], en[:5]
    assert find_seq(en, ['.LOCALREF charaNo', 'PUSH 2', 'LT']) >= 0 and find_seq(en, ['.LOCALREF charaNo', 'PUSH 5', 'GT']) >= 0, en
    enum = next(e for e in m['enums'] if e['name'] == 'E_GameMode')['values']
    assert enum == ['Modern', 'Classic'], enum
    ini = dump_fn(ain, 'C_FeelingView@Init', d)
    pos = [(f32(int(ini[x].split()[1])), f32(int(ini[x + 1].split()[1]))) for x in range(len(ini) - 2)
           if ini[x].startswith('PUSH ') and ini[x + 1].startswith('PUSH ') and ini[x + 2].startswith('NEW CASPosF')]
    zs = [int(ini[x + 3].split()[1]) for x in range(len(ini) - 4) if ini[x] == 'PUSH 50' and ini[x + 1] == 'ADD' and ini[x + 2] == 'X_REF 1'
          and ini[x + 3].startswith('PUSH ')]
    assert pos == [(374.0, 66.0), (374.0, 96.0)] and zs == [200, 250], (pos, zs)
    assert '"シス／親密度／親密度"' in ini or any('親密度／親密度' in o for o in ini), 'the 親密度 label CG changed'
    sp = dump_fn(ain, 'C_HomeStatusView@IsShowFeelingPage', d)
    now = fid_sym(m, 'C_HomeStatusView@NowPage::get')
    assert [o for o in sp if o.startswith('PUSH ') and o != 'PUSH %d' % now] == ['PUSH 0', 'PUSH 1', 'PUSH 0', 'PUSH 1', 'PUSH 0'], sp
    assert sum(1 for o in sp if o == 'PUSH %d' % now) == 2, sp
    sc = dump_fn(ain, 'C_FeelingView@SetChara', d)
    assert find_seq(sc, ['PUSHSTRUCTPAGE', 'PUSH 5', '.LOCALREF charaNo', 'X_ASSIGN 1']) == 0, 'SetChara no longer stores m_CharaNo first'
    assert find_seq(sc, ['CALLFUNC LAbility::At']) > 0 and find_seq(sc, ['PUSH %d' % fn('C_Ability@GetFeeling'), 'CALLMETHOD 0', 'CALLMETHOD 3']) > 0, sc
    upg = dump_fn(ain, 'C_FeelingView@UpdatePage', d)
    assert find_seq(upg, ['PUSHSTRUCTPAGE', 'PUSH %d' % fn('C_FeelingView@Enabled'), '.STRUCTREF C_FeelingView m_CharaNo', 'CALLMETHOD 1', 'NOT']) == 0, upg[:6]
    at = dump_fn(ain, 'LAbility::At', d)
    assert find_seq(at, ['.GLOBALREF LAbility::m_pAbilities', '.LOCALREF idx', 'X_REF 1']) > 0 and find_seq(at, ['.LOCALREF charaNo', 'PUSH 1', 'SUB']) >= 0, at
    return dict(per_moon=per_moon, moons=moons, maximum=per_moon * moons, moon_phase_from_val=phases,
                rank_upper_bounds=bounds, rank_display='GetFeelingRank_5 + 1 of 5',
                rank_table=[dict(rank=r + 1, feeling=('<= 15' if r == 0 else ('>= 61' if r == 4 else '%d-%d' % (bounds[r - 1] + 1, bounds[r])))) for r in range(5)],
                rates=rates, rate_default=default, value='C_Ability@GetFeeling = m_nFeeling / GetFeelingRate (integer division)',
                enabled='C_FeelingView@Enabled: false when Flags.GameMode == Classic (1) or the person is outside 2..5',
                moons_at=dict(box=pos[0], label=pos[1], z=zs, parent='the status activity root (ルートパーツ)'),
                shown_on_pages='C_HomeStatusView@IsShowFeelingPage: NowPage 0 (the hover preview) or 1')


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


# ---------------------------------------------------------------- data
def width(s, size):
    mm = METRICS[size]
    x = 0
    for ch in s:
        if ch == ' ':
            x += mm['space']
        elif ch.isdigit() and ord(ch) < 128:
            x += mm['digit']
        elif ord(ch) < 128:
            x += mm['other']
        else:
            x += mm['full']
    return x


def gate_last(t, end):
    """The last day the gated trigger can fire (month * 100 + day): conditional -> date_to, scheduled_special -> date, a priority
    talk -> its L_Calendar::IsTodayOrBefore(m, d) or, without one, the calendar's last day."""
    k = t.get('kind')
    if k == 'conditional':
        m, d = t['date_to']
    elif k == 'scheduled_special':
        m, d = t['date']
    elif k == 'after_training_priority':
        z = re.findall(r'IsTodayOrBefore\((\d+), (\d+)\)', t['condition_expr'])
        assert len(z) <= 1, t['condition_expr']
        m, d = (int(z[0][0]), int(z[0][1])) if z else end
    else:
        raise AssertionError(('unknown gated trigger kind', k))
    return m * 100 + d


def load_gates():
    sched = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    r19 = L.readj(L.R19 / 'work' / 'build' / 'tables.json')
    end = tuple(sched['calendar']['end'])
    rows = []
    for e in sched['events']:
        for t in e.get('triggers') or []:
            for g in t.get('feeling_gate') or []:
                rows.append(dict(no=e['id'], person=g['person'], op=g['op'], value=g.get('value', 0), among=g.get('among'),
                                 no_route=bool(t.get('no_route')), kind=t.get('kind'), last=gate_last(t, end)))
    assert len(rows) == 28 and len({r['no'] for r in rows}) == 28, len(rows)
    assert {str(r['no']) for r in rows} == set(r19['feeling']), 'schedule feeling gates != the r19 affinity list'
    assert all(2 <= r['person'] <= 5 for r in rows), 'a gate on a person without moons'
    assert collections.Counter(r['op'] for r in rows) == {'>=': 20, '<': 4, 'highest': 4}, collections.Counter(r['op'] for r in rows)
    for r in rows:
        if r['op'] == 'highest':
            assert r['among'] == [2, 3, 4, 5] and r['no_route'], r
        r['name'] = r19['ev_head'][str(r['no'])]
        r['name_px'] = width('　' + r['name'], 18)
        assert r['name_px'] <= ST_TEXT_MAX_PX, ('a gate name wider than the page', r)
    per = collections.Counter(r['person'] for r in rows if r['op'] == 'highest')
    assert per == {2: 1, 3: 1, 4: 1, 5: 1}, per
    rows.sort(key=lambda r: (r['person'], r['no']))
    return rows, sched


# ---------------------------------------------------------------- jaf generation
def q(s):
    return json.dumps(s, ensure_ascii=False)


def tree(ret, name, var, pairs, default):
    pairs = sorted(pairs)
    lines = [f'{ret} {name}(int {var}) {{']
    for k, v in pairs:
        lines.append(f'    if ({var} == {k}) return {v};')
    lines.append(f'    return {default};')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def gen_tables(gates_):
    out = ['int KR_T23GateN() { return %d; }\n' % len(gates_),
           tree('int', 'KR_T23GateEv', 'i', [(i, g['no']) for i, g in enumerate(gates_)], -1),
           tree('int', 'KR_T23GatePerson', 'i', [(i, g['person']) for i, g in enumerate(gates_)], 0),
           tree('int', 'KR_T23GateOp', 'i', [(i, OP_CODE[g['op']]) for i, g in enumerate(gates_)], -1),
           tree('int', 'KR_T23GateValue', 'i', [(i, g['value']) for i, g in enumerate(gates_)], 0),
           tree('int', 'KR_T23GateLast', 'i', [(i, g['last']) for i, g in enumerate(gates_)], 0)]
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


def struct_slot(m, sname, member):
    s = next(x for x in m['structures'] if L.fix_name(x['name']) == sname)
    names = [L.fix_name(x['name']) for x in s['members']]
    return names.index(member)


def jam_bodies(m, dm, ids):
    """KR_T23FeelShow (this = the status view: KR_T23FeelShowOf(this) -> the bool the original query gives), KR_T23FvGone
    (this = the moons: the original DeleteMarks, then our part released), KR_T23FvChara (sv.m_FeelingView.m_CharaNo)."""
    for (sname, member), slot in SLOTS.items():
        assert struct_slot(m, sname, member) == slot, ('struct layout differs from what the jam bodies assume', sname, member)
    dele = L.fid_of(m, 'C_FeelingView@DeleteMarks')
    b = {}
    b['KR_T23FeelShow'] = "\tPUSHSTRUCTPAGE\n\tCALLFUNC KR_T23FeelShowOf\n\tRETURN\n"
    b['KR_T23FvGone'] = f"\tPUSHSTRUCTPAGE\n\tPUSH {dele}\n\tCALLMETHOD 0\n\tCALLFUNC KR_T23MoonClear\n\tRETURN\n"
    b['KR_T23FvChara'] = ("\t.LOCALREF sv\n\tPUSH 9\n\tX_REF 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ kr_t23_nofv\n"
                          "\t.LOCALREF sv\n\tPUSH 9\n\tX_REF 1\n\tPUSH 5\n\tX_REF 1\n\tRETURN\n"
                          "kr_t23_nofv:\n\tPUSH 0\n\tRETURN\n")
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
    assert set(JAM_BODIES) <= set(ids), set(JAM_BODIES) - set(ids)
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
    for owner, kind, oldfn, nth, newfn, follow in SWAPS:
        fid = L.fid_of(m, owner)
        oldid = fid_sym(m, oldfn)
        newid = ids[newfn]
        assert sig(dm['functions'][newid]) == sig(m['functions'][oldid]), (newfn, sig(dm['functions'][newid]), sig(m['functions'][oldid]))
        ops = region_ops(raw_path, m, fid)
        if kind == 'call':
            opcode, key = 0x30, f'CALLFUNC 0x{oldid:x}'
            hits = [i for i, (ad, op) in enumerate(ops) if op == key]
        else:
            opcode, key = 0x00, f'PUSH 0x{oldid:x}'
            nargs = len([a for a in m['functions'][oldid]['arguments'] if a['type'][0] != 0])
            assert follow[0] == f'CALLMETHOD 0x{nargs:x}', (owner, oldfn, nargs)
            hits = [i for i, (ad, op) in enumerate(ops) if op == key]
            for i in hits:
                assert [op for _, op in ops[i + 1:i + 1 + len(follow)]] == follow, ('method site shape', owner, oldfn, [op for _, op in ops[i + 1:i + 1 + len(follow)]])
                assert ops[i - 1][1] == 'PUSHSTRUCTPAGE', ('method site object', owner, oldfn, ops[i - 1])
        assert len(hits) == EXPECTED_CALLS[(owner, oldfn)], (owner, oldfn, len(hits))
        ad = ops[hits[nth]][0]
        before = struct.pack('<Hi', opcode, oldid)
        after = struct.pack('<Hi', opcode, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (owner, hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=owner, fid=fid, function_address=m['functions'][fid]['address'], site=ad,
                          site_offset=ad - m['functions'][fid]['address'], kind='CALLMETHOD target (PUSH operand)' if kind == 'method' else 'CALLFUNC',
                          original=oldfn, original_fid=oldid, replacement=newfn, replacement_fid=newid, before=before.hex(),
                          after=after.hex(), operand_bytes=[ad + 2, ad + 6], occurrence=nth, calls_of_original_in_function=len(hits),
                          owner_is_original=not owner.startswith('KR_')))
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, sites, oldn


def invariance(base, out, m, sites, oldn, old_sites, bp):
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', out)
    nm = L.read_meta(W / 'candidate_meta.json')
    changed = [f['index'] for f, g in zip(m['functions'], nm['functions']) if f != g]
    assert not changed, ('original function entries changed', changed[:5])
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
    cvers = L.versions(W / 'candidate_raw_code.jam')
    for old_, new_ in list(R19_FORWARD.items()) + list(R18_FORWARD.items()) + list(R22_FORWARD.items()):
        v = L.live_version(nm, cvers, L.fid_of(nm, old_))
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
    return nm, dict(original_function_entries_identical=True, forwarded=[], other_metadata_identical=sorted(k for k in m if k != 'functions'),
                    old_code_bytes_changed=len(diff), old_code_changes_only_at_swapped_operands=True, MSG1_exact=True, STR0_prefix_exact=True,
                    STR0_added=len(sn) - len(so), functions_added=len(nm['functions']) - len(m['functions']), pinned=pinned,
                    earlier_same_length_sites_kept=n_old, forwarders_kept=dict(r18=len(R18_FORWARD), r19=len(R19_FORWARD), r22=len(R22_FORWARD)))


def discard(reason, got):
    for n in ['NightRemaster.ain', 'manifest.json']:
        if (O / n).exists():
            (O / n).unlink()
    L.writej(L.WORK / 'REBASE_NEEDED.json', dict(time=datetime.datetime.now().astimezone().isoformat(), reason=reason, runtime_now=got,
                                               base=dict(ain=L.BASE_AIN_SHA, pact=L.BASE_PACT_SHA, ex=L.BASE_EX_SHA, winmm=L.BASE_WINMM_SHA)))
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
    log('base keeps the r15/r18/r20/r21/r22 same-length sites:', sites_applied(bcode, old_sites))
    for old_, new_ in list(R18_FORWARD.items()) + list(R19_FORWARD.items()) + list(R22_FORWARD.items()):
        f = m['functions'][L.fid_of(m, old_)]
        v = L.live_version(m, vers, f['index'])
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(m, new_), 'RETURN'], ('forwarder not in the base', old_)
    for lo, hi, by in TAKEN_PARTS:
        assert not (lo <= MOON_PART <= hi), ('part number taken', by)
    assert 'PUSH %d' % MOON_PART not in Path(bp['raw']).read_text('utf8').replace('0x%x' % MOON_PART, str(MOON_PART)), 'the part number is used in the base'
    gc = game_code(bp, m)
    log('game code', {k: v for k, v in gc.items() if k in ('maximum', 'rank_upper_bounds', 'rates', 'moons_at')})
    gates_, sched = load_gates()
    log('feeling gates', len(gates_), collections.Counter(g['op'] for g in gates_), 'widest name line %d px' % max(g['name_px'] for g in gates_))
    jaf = JAF_SRC.read_text('utf8')
    assert jaf.count('/*TABLES*/') == 1 and jaf.count('@@MOON_MAX@@') == 1
    mx, my = gc['moons_at']['label'][0], gc['moons_at']['label'][1] + MOON_GAP
    jaf = (jaf.replace('/*TABLES*/', gen_tables(gates_)).replace('@@MOON_MAX@@', str(gc['maximum']))
           .replace('@@MOON_X@@', '%.1f' % mx).replace('@@MOON_Y@@', '%.1f' % my).replace('@@MOON_Z@@', str(MOON_Z))
           .replace('@@ST_PANEL_Z@@', str(ST_PANEL_Z)).replace('@@ST_TEXT_Z@@', str(ST_TEXT_Z)))
    assert '@@' not in jaf, re.findall(r'@@\w+@@', jaf)
    (W / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    texts = jaf_strings(L.strip_comments(jaf))
    bad = check_alphabet(texts + [g['name'] for g in gates_])
    assert not bad, ('characters outside the font map / proxy set', bad)
    built = L.jaf_literal_encode(L.strip_comments(jaf))
    assert not [c for c in built if ('\uac00' <= c <= '\ud7a3')], 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, sites, oldn = compile_and_patch(base, m, bp['raw'], built)
    log('compiled: %d functions added, %d same-length sites' % (len(ids), len(sites)))
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    nm, inv = invariance(base, out, m, sites, oldn, old_sites, bp)
    log('invariance ok', {k: v for k, v in inv.items() if k != 'pinned'})
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    L.writej(W / 'gates.json', dict(gates=gates_, game_code=gc))
    ptr2, rt2, got2 = runtime_now()
    if not base_is_current(ptr2, got2):
        discard('runtime moved during the build', dict(got2, status=ptr2['status'], manifest_sha256=ptr2['manifest_sha256']))
    man = dict(
        schema='yoru-feeling-r23.candidate.v1', status='FEELING_R23_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, winmm_sha256=L.BASE_WINMM_SHA,
                  chart_sha256=L.BASE_CHART_SHA, r22_installed=True, hook_r2_installed=True, checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False, chart_changed=False, winmm_changed=False,
        data=dict(schedule_sha256=L.sha(L.FLOW / 'graph' / 'schedule.json'), r19_tables_sha256=L.sha(L.R19 / 'work' / 'build' / 'tables.json'),
                  feeling_gates=len(gates_), gate_ops=dict(collections.Counter(g['op'] for g in gates_)),
                  widest_name_line_px=max(g['name_px'] for g in gates_), name_line_budget_px=ST_TEXT_MAX_PX, metrics_px=METRICS),
        game_code=gc,
        display=dict(moon_text='「<GetFeeling> / %d」 + 「단계 <GetFeelingRank_5 + 1>/5」 (18 / 16 px, white with a black edge 2.0)' % gc['maximum'],
                     moon_text_part=MOON_PART, moon_text_at=dict(parent='status root', x=mx, y=my, z=MOON_Z),
                     shown_when='C_HomeStatusView@IsShowFeelingPage() and m_FeelingView.Enabled(m_FeelingView.m_CharaNo) (the same test the moons use)',
                     event_page='the r20 「이벤트」 page of a person with moons: right under the title 「친밀도 v (r/5) · 다음 조건 n」 + the gate name '
                                '(18 px, indented) + 「루트: 네 명 중 가장 높으면」 + name when that scene is not seen; the panel grows by the lines',
                     next_condition='the smallest >= threshold above the value among the person\'s gates whose scene is not registered in this '
                                    'save and whose last day (KR_T23GateLast) is not past (ties: the lower event number); none -> 「없음」; '
                                    'the 「highest」 gate (E10501 family, 11/1) gets its own 「루트」 line while unseen and not past'),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=JAM_BODIES, forwarded_functions={},
        r18_forwarders_kept=sorted(R18_FORWARD), r19_forwarders_kept=sorted(R19_FORWARD), r22_forwarders_kept=sorted(R22_FORWARD),
        same_length_sites=sites, earlier_same_length_sites_kept=inv['earlier_same_length_sites_kept'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], invariance=inv, parts=dict(moon_text=MOON_PART, event_page_panel_and_text='r20 2026092001 / 2026092002'),
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        session_variables_new=[], new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
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
