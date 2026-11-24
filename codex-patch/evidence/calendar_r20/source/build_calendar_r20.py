"""Claude Opus 5.5 (2026-09-27) r20: 「몇 번 갔나 · 남은 이벤트」 on the two screens where the player picks people, on top of the
r19 install (current.json CALENDAR_R19_INSTALLED_NATIVE_PASS, AIN 1d6081e9… = the r19 candidate).

  python build_calendar_r20.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/status/manifest = r20lib BASE_*, P: free space >= 10 GB, r19 installed
     (evidence/calendar_r19 journal COMMITTED, the r19 candidate = the runtime AIN), the help-menu chart = the r19 chart, and the
     chart inputs (published chart, builder, graph/schedule.json) = the ones r19 was built from (the calendar tables in the base
     are then today's data).
  2. data: chart/build_chart_v2.build() as a module (= the published chart). r20 tables: the (person, person2) pair of every
     scene in a dungeon-walk drawer (graph/schedule.json), the join days (chart `join`: 마나미 5/19, 마코토 6/30, 모모세 6/16).
  3. alice ain edit --jaf (declare the KR_T20* functions) -> dump -> native_lower -> alice ain edit --jam with the lowered bodies,
     except nine functions whose body is written here in jam: three readers of values inside structs / interfaces
     (KR_T20SvPage, KR_T20SvAct, KR_T20AllyAct), five CALLMETHOD targets that pass `this` on (KR_T20StNext, KR_T20StPrev,
     KR_T20StActive, KR_T20TrAlly, KR_T20TrAppear) and KR_T20StEnd (passes its delegate argument on).
  4. seven same-length operand swaps inside unchanged original functions (a method call is `PUSH <function> … CALLMETHOD n`, so
     its target is the PUSH operand; a plain call is `CALLFUNC <function>`), each checked for signature equality:
       C_Status::RunStatus               PUSH C_HomeStatusView@PrevPage          -> KR_T20StPrev
       C_Status::RunStatus               PUSH C_HomeStatusView@NextPage          -> KR_T20StNext
       C_Status::RunStatus               CALLFUNC AFL_Parts_EraseWholeMouseWheelEvent -> KR_T20StEnd
       C_HomeStatusView@SetInfo          PUSH C_HomeStatusView@SetActivePage     -> KR_T20StActive
       C_SceneTraining@RunSelectPartner  PUSH C_SceneTrainingView@SelectAlly::get -> KR_T20TrAlly   (the direction-key loop)
       C_SceneTraining@RunSelectPartner  CALLFUNC ■方向キー処理／削除           -> KR_T20TrKeyDel
       C_SceneTraining@_UpdateInputPartner PUSH C_SceneTrainingView@AppearStandChara -> KR_T20TrAppear
  5. invariance: every base function entry identical (no forwarder, no relocation); the old CODE identical except the seven
     4-byte operands; MSG1, STR0 prefix identical; the six pinned functions keep entry and every code byte; r15's nine and r18's
     one operand sites and r19's five forwarders still in place; native opcode audit of every live function.
  6. end gate: the runtime hashes are read again. If Codex installed something meanwhile the candidate is DISCARDED
     (files removed, work/REBASE_NEEDED.json written) and the build exits 3 - rebuild on the new base, never install it.
PACT, EX, FNL and the help-menu chart are not touched. Nothing is written outside r20_calendar\\ (runtime, saves, Codex root,
r15-r19: read only).
"""
import sys, io, json, re, struct, shutil, collections, contextlib, datetime
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r20lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_calendar_r20.jaf'
LANES = ['main', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'dungeon']
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
R15_SITES = 9
R19_FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
               'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
# the parts r20 draws (fixed numbers; the game's GetFreeNumber counts up from 1,000,000,000)
ST_PANEL, ST_TEXT, TR_BASE, TR_BOX = 2026092001, 2026092002, 2026092010, 2026092020
ST_PANEL_Z, ST_TEXT_Z, TR_BOX_Z, TR_Z = 40, 41, 20, 21   # relative to the parent part (status root z 204 -> 244/245; portrait 253.. -> 273..)
# (owner, kind, original callee, occurrence among its calls in the owner, replacement, the ops that follow the operand up to
# and including the CALLMETHOD that consumes it - method sites only; the argument expressions are pinned exactly)
SWAPS = [
    ('C_Status::RunStatus', 'method', 'C_HomeStatusView@PrevPage', 0, 'KR_T20StPrev', ['CALLMETHOD 0x0']),
    ('C_Status::RunStatus', 'method', 'C_HomeStatusView@NextPage', 0, 'KR_T20StNext', ['CALLMETHOD 0x0']),
    ('C_Status::RunStatus', 'call', 'AFL_Parts_EraseWholeMouseWheelEvent', 0, 'KR_T20StEnd', None),
    ('C_HomeStatusView@SetInfo', 'method', 'C_HomeStatusView@SetActivePage', 0, 'KR_T20StActive',
     ['PUSHSTRUCTPAGE', 'PUSH 0x6efb', 'CALLMETHOD 0x0', 'CALLMETHOD 0x1']),
    ('C_SceneTraining@RunSelectPartner', 'method', 'C_SceneTrainingView@SelectAlly::get', 0, 'KR_T20TrAlly', ['CALLMETHOD 0x0']),
    ('C_SceneTraining@RunSelectPartner', 'call', '■方向キー処理／削除', 0, 'KR_T20TrKeyDel', None),
    ('C_SceneTraining@_UpdateInputPartner', 'method', 'C_SceneTrainingView@AppearStandChara', 0, 'KR_T20TrAppear',
     ['PUSHLOCALPAGE', 'PUSH 0x0', 'X_REF 0x2', 'X_REF 0x1', 'PUSH 0x15e', 'CALLMETHOD 0x2']),
]
EXPECTED_CALLS = {    # every call of the original callee in the owner's live body (all accounted for)
    ('C_Status::RunStatus', 'C_HomeStatusView@PrevPage'): 1,
    ('C_Status::RunStatus', 'C_HomeStatusView@NextPage'): 1,
    ('C_Status::RunStatus', 'AFL_Parts_EraseWholeMouseWheelEvent'): 1,
    ('C_HomeStatusView@SetInfo', 'C_HomeStatusView@SetActivePage'): 1,
    ('C_SceneTraining@RunSelectPartner', 'C_SceneTrainingView@SelectAlly::get'): 1,
    ('C_SceneTraining@RunSelectPartner', '■方向キー処理／削除'): 1,
    ('C_SceneTraining@_UpdateInputPartner', 'C_SceneTrainingView@AppearStandChara'): 1,
}
JAM_BODIES = ['KR_T20SvPage', 'KR_T20SvAct', 'KR_T20AllyAct', 'KR_T20StNext', 'KR_T20StPrev', 'KR_T20StActive', 'KR_T20StEnd',
              'KR_T20TrAlly', 'KR_T20TrAppear']
# the member slots the jam readers use, checked against the struct layouts in the base metadata
SLOTS = {('C_HomeStatusView', 'm_Act'): 1, ('C_HomeStatusView', '<NowPage>'): 16, ('C_HomeStatusView', 'm_CharaNo'): 11,
         ('C_SceneTrainingView', 'm_SelectAlly'): 10, ('C_SelectAlly', 'm_Act'): 0,
         ('activity::detail::CActivityWrap', '<Handle>'): 4}


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
    assert base_is_current(ptr, got), ('runtime moved: rebase r20lib BASE_* on the new runtime first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    j = L.readj(L.R19_JOURNAL)
    assert j['status'] == 'COMMITTED' and j['after']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r19 not installed as expected', j['status'])
    assert L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA, 'the runtime help-menu chart is not the r19 chart'
    bp = L.base_paths()
    assert L.sha(bp['ain']) == L.BASE_AIN_SHA
    r19c = L.readj(L.R19 / 'candidate' / 'manifest.json')['chart']
    now = dict(published_chart_sha256=L.sha(L.FLOW / 'chart' / 'yoru_flowchart_v2.html'), builder_sha256=L.sha(L.FLOW / 'chart' / 'build_chart_v2.py'),
               schedule_sha256=L.sha(L.FLOW / 'graph' / 'schedule.json'))
    assert all(r19c[k] == v for k, v in now.items()), ('chart data moved since r19 was built: the calendar tables in the base are stale', now)
    return ptr, rt, bp, free, now


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


def region_ops(raw_path, m, fid):
    """The live body of `fid` as ops, INCLUDING the code that follows lambdas compiled inline into it (a lambda's FUNC ..
    ENDFUNC sits in the middle of its owner's code; L.versions would give the rest of the owner to the lambda) and EXCLUDING
    the lambda bodies themselves."""
    owner = L.raw_symbol(m, fid)
    start = m['functions'][fid]['address']
    lines = Path(raw_path).read_text('utf8').splitlines()
    ops = []
    last = 0
    state = 'seek'
    inner = None
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
                    state, inner = 'lambda', k
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
            state, inner = 'in', None
    assert ops and ops[0][0] == start, (owner, ops[:1], start)
    return ops


# ---------------------------------------------------------------- data
def chart_data():
    sys.path.insert(0, str(L.FLOW / 'chart'))
    import build_chart_v2 as V2
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data = V2.build(str(L.TMP / 'chart_v2_from_r20_build.html'))
    html = (L.FLOW / 'chart' / 'yoru_flowchart_v2.html').read_text('utf8')
    z = re.search(r'<script type="application/json" id="yoru-data">(.*?)</script>', html, re.S)
    pub = json.loads(z.group(1))

    def chips(d):
        return [(ch['id'], ch['page'], ch['lane'], ch['kind'], ch['entries'], [x[0] for x in ch['order']]) for ch in d['chips']]
    same = dict(chips=chips(data) == chips(pub), join=data['join'] == pub['join'])
    assert all(same.values()), ('PC chart v2 and the in-game tables would diverge', same)
    return data, V2


def r20_tables(data):
    """Walk pairs for every scene in a dungeon-walk drawer, and the join days (month * 100 + day)."""
    sch = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    evs = {e['id']: e for e in sch['events']}
    pairs = {}
    per_chip = []
    for ch in data['chips']:
        if ch['kind'] != 'walk':
            continue
        scenes = [x[0] for x in ch['order'] if x[4]]
        for no in scenes:
            e = evs[no]
            assert e['category'] == 'dungeon_walk', (no, e['category'])
            p, q = e['person'], e['person2'] or 0
            assert 1 <= p <= 8 and (q == 0 or 2 <= q <= 8) and p != q, (no, p, q)
            if p > 1 and q:
                assert p < q, ('walk pair not in person order', no, p, q)
            pairs[no] = p * 10 + q
        per_chip.append((ch['id'], len(scenes)))
    assert len(pairs) == sum(n for _, n in per_chip) == len(set(pairs))
    join = {}
    for lane, (mo, dd) in data['join'].items():
        p = LANES.index(lane) + 1
        join[p] = mo * 100 + dd
    assert join == {4: 519, 5: 630, 8: 616}, join
    walk_events = sorted(e['id'] for e in sch['events'] if e['category'] == 'dungeon_walk')
    assert sorted(pairs) == walk_events, ('a dungeon-walk scene outside the walk drawers', sorted(set(walk_events) ^ set(pairs))[:5])
    info = dict(walk_scenes=len(pairs), walk_drawers=len(per_chip),
                pairs=dict(collections.Counter('%d-%d' % divmod(v, 10) for v in pairs.values())), join=join)
    return dict(pairs=pairs, join=join), info


# ---------------------------------------------------------------- jaf generation
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
    return ('// 던전 동행 서랍의 장면마다 person * 10 + person2 (person2 가 없으면 0); 동행 장면이 아니면 -1\n'
            + tree('int', 'KR_T20WalkPair', 'no', list(R['pairs'].items()), -1)
            + '// 합류하는 날(월 * 100 + 일, 달력의 합류 규칙과 같다); 처음부터 있으면 0\n'
            + tree('int', 'KR_T20JoinDay', 'p', list(R['join'].items()), 0))


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


def fid_sym(m, name):
    """Index by the dump symbol (duplicate names carry #n: 'C_SceneTrainingView@SelectAlly::get' is the first of two)."""
    hits = [f['index'] for f in m['functions'] if L.symbol(m, f['index']) == name]
    assert len(hits) == 1, (name, hits)
    return hits[0]


def struct_slot(m, sname, member):
    s = next(x for x in m['structures'] if L.fix_name(x['name']) == sname)
    names = [L.fix_name(x['name']) for x in s['members']]
    return names.index(member)


def jam_bodies(m, dm, ids):
    """The nine hand-written bodies (index -> jam text)."""
    for (sname, member), slot in SLOTS.items():
        assert struct_slot(m, sname, member) == slot, ('struct layout differs from what the jam readers assume', sname, member)
    fn = lambda n: L.fid_of(m, n)
    b = {}
    b['KR_T20SvPage'] = '\t.LOCALREF sv\n\tPUSH 16\n\tX_REF 1\n\tRETURN\n'
    # sv.m_Act is an interface (object page, vtable offset); its object is an activity::detail::CActivityWrap whose <Handle> is
    # the PartsEngine activity name (AFL_Activity_Load#1's result)
    b['KR_T20SvAct'] = ('\t.LOCALREF sv\n\tPUSH 1\n\tX_REF 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ kr_t20_noact\n'
                        '\t.LOCALREF sv\n\tPUSH 1\n\tX_REF 1\n\tPUSH 4\n\tX_REF 1\n\tA_REF\n\tRETURN\n'
                        'kr_t20_noact:\n\tS_PUSH ""\n\tRETURN\n')
    b['KR_T20AllyAct'] = ('\t.LOCALREF v\n\tPUSH 10\n\tX_REF 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ kr_t20_noally\n'
                          '\t.LOCALREF v\n\tPUSH 10\n\tX_REF 1\n\tPUSH 0\n\tX_REF 1\n\tPUSH -1\n\tEQUALE\n\tIFNZ kr_t20_noally\n'
                          '\t.LOCALREF v\n\tPUSH 10\n\tX_REF 1\n\tPUSH 0\n\tX_REF 1\n\tPUSH 4\n\tX_REF 1\n\tA_REF\n\tRETURN\n'
                          'kr_t20_noally:\n\tS_PUSH ""\n\tRETURN\n')
    # CALLMETHOD targets: `this` (the status view / the training view) is passed on as the first argument
    b['KR_T20StNext'] = f"\tPUSHSTRUCTPAGE\n\tCALLFUNC KR_T20StNextOf\n\tRETURN\n"
    b['KR_T20StPrev'] = f"\tPUSHSTRUCTPAGE\n\tCALLFUNC KR_T20StPrevOf\n\tRETURN\n"
    b['KR_T20StActive'] = f"\tPUSHSTRUCTPAGE\n\t.LOCALREF page\n\tCALLFUNC KR_T20StActiveOf\n\tRETURN\n"
    # C_SceneTrainingView@SelectAlly::get returns m_SelectAlly with one more reference (X_DUP 1 / SP_INC), as here
    b['KR_T20TrAlly'] = (f"\tPUSHSTRUCTPAGE\n\tCALLFUNC KR_T20TrEnsure\n"
                         f"\tPUSHSTRUCTPAGE\n\tPUSH 10\n\tX_REF 1\n\tX_DUP 1\n\tSP_INC\n\tRETURN\n")
    b['KR_T20TrAppear'] = (f"\tPUSHSTRUCTPAGE\n\tPUSH {fn('C_SceneTrainingView@AppearStandChara')}\n\t.LOCALREF charaNo\n\t.LOCALREF time\n"
                           f"\tCALLMETHOD 2\n\t.LOCALREF charaNo\n\tCALLFUNC KR_T20TrMark\n\tRETURN\n")
    # AFL_Parts_EraseWholeMouseWheelEvent passes its delegate on with .LOCALREF / A_REF (its own body), so does this
    b['KR_T20StEnd'] = "\t.LOCALREF delegateObject\n\tA_REF\n\tCALLFUNC AFL_Parts_EraseWholeMouseWheelEvent\n\tCALLFUNC KR_T20StClear\n\tRETURN\n"
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
    assert all(n.startswith('KR_T20') for n in ids), [n for n in ids if not n.startswith('KR_T20')]
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
    # same-length operand swaps inside unchanged original functions
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
            assert follow[-1] == f'CALLMETHOD 0x{nargs:x}', (owner, oldfn, nargs)
            hits = [i for i, (ad, op) in enumerate(ops) if op == key]
            for i in hits:
                assert [op for _, op in ops[i + 1:i + 1 + len(follow)]] == follow, ('method site shape', owner, oldfn, [op for _, op in ops[i + 1:i + 1 + len(follow)]])
        assert len(hits) == EXPECTED_CALLS[(owner, oldfn)], (owner, oldfn, len(hits))
        ad = ops[hits[nth]][0]
        before = struct.pack('<Hi', opcode, oldid)
        after = struct.pack('<Hi', opcode, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (owner, hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=owner, fid=fid, function_address=m['functions'][fid]['address'], site=ad,
                          site_offset=ad - m['functions'][fid]['address'], kind='CALLMETHOD target (PUSH operand)' if kind == 'method' else 'CALLFUNC',
                          original=oldfn, original_fid=oldid, replacement=newfn, replacement_fid=newid, before=before.hex(),
                          after=after.hex(), operand_bytes=[ad + 2, ad + 6], occurrence=nth, calls_of_original_in_function=len(hits)))
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
    for old_, new_ in list(R19_FORWARD.items()) + list(R18_FORWARD.items()):
        v = L.live_version(nm, cvers, L.fid_of(nm, old_))
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
    return nm, dict(original_function_entries_identical=True, other_metadata_identical=sorted(k for k in m if k != 'functions'),
                    old_code_bytes_changed=len(diff), old_code_changes_only_at_swapped_operands=True, MSG1_exact=True,
                    STR0_prefix_exact=True, STR0_added=len(sn) - len(so), functions_added=len(nm['functions']) - len(m['functions']),
                    pinned=pinned, earlier_same_length_sites_kept=n_old)


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
    ptr, rt, bp, free, chart = gates()
    base = bp['ain']
    log('gates ok', L.BASE_AIN_SHA[:16], ptr['status'], 'P: free %.1f GB' % (free / 1024 ** 3))
    W.mkdir(parents=True, exist_ok=True)
    m = L.read_meta(bp['meta'])
    vers = L.versions(bp['raw'])
    old_sites = site_list()
    _, bcode, _ = code_of(base.read_bytes())
    log('base keeps the r15/r18 same-length sites:', sites_applied(bcode, old_sites))
    for old_, new_ in list(R18_FORWARD.items()) + list(R19_FORWARD.items()):
        f = m['functions'][L.fid_of(m, old_)]
        v = L.live_version(m, vers, f['index'])
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(m, new_), 'RETURN'], ('forwarder not in the base', old_)
    data, V2 = chart_data()
    R, info = r20_tables(data)
    log('r20 tables', info)
    src = JAF_SRC.read_text('utf8')
    assert src.count('/*TABLES*/') == 1
    jaf = src.replace('/*TABLES*/', gen_tables(R))
    for k, v in dict(ST_PANEL_Z=ST_PANEL_Z, ST_TEXT_Z=ST_TEXT_Z, TR_BOX_Z=TR_BOX_Z, TR_Z=TR_Z).items():
        assert jaf.count('@@%s@@' % k) == 1, k
        jaf = jaf.replace('@@%s@@' % k, str(v))
    assert '@@' not in jaf
    for n, v in (('KR_T20StPanel', ST_PANEL), ('KR_T20StTextPart', ST_TEXT)):
        assert ('int %s() { return %d; }' % (n, v)) in jaf, n
    assert ('return %d + p;' % TR_BASE) in jaf and ('return %d + p;' % TR_BOX) in jaf
    (W / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    texts = jaf_strings(L.strip_comments(jaf))
    bad = check_alphabet(texts)
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
    L.writej(W / 'tables.json', dict(pairs={str(k): v for k, v in R['pairs'].items()}, join={str(k): v for k, v in R['join'].items()}, info=info))
    ptr2, rt2, got2 = runtime_now()
    if not base_is_current(ptr2, got2):
        discard('runtime moved during the build', dict(got2, status=ptr2['status'], manifest_sha256=ptr2['manifest_sha256']))
    man = dict(
        schema='yoru-calendar-r20.candidate.v1', status='CALENDAR_R20_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, chart_sha256=L.BASE_CHART_SHA,
                  r19_installed=True, checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False, chart_changed=False, chart_inputs=chart, tables=info,
        parts=dict(status_panel=ST_PANEL, status_text=ST_TEXT, training_labels=[TR_BASE + p for p in range(2, 9)],
                   training_boxes=[TR_BOX + p for p in range(2, 9)],
                   z_relative=dict(status_panel=ST_PANEL_Z, status_text=ST_TEXT_Z, training_box=TR_BOX_Z, training_label=TR_Z)),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=JAM_BODIES, forwarded_functions={},
        r18_forwarders_kept=sorted(R18_FORWARD), r19_forwarders_kept=sorted(R19_FORWARD), same_length_sites=sites,
        earlier_same_length_sites_kept=inv['earlier_same_length_sites_kept'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], invariance=inv,
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        session_variables=['YoruKR.T9.Ctx', 'YoruKR.T9.Req', 'YoruKR.T9.Play', 'YoruKR.T9.Playing', 'YoruKR.T9.Unwind', 'YoruKR.T9.Open', 'YoruKR.T9.Lane',
                           'YoruKR.T18.PrevSet', 'YoruKR.T18.PrevFn', 'YoruKR.T18.PrevSys'],
        new_session_variables=[], new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
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
