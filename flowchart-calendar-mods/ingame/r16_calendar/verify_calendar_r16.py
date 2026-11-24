"""Claude Opus 5.5 (2026-09-27) r16: verification of the calendar candidate without the game (after verify_calendar_r15.py).

  python verify_calendar_r16.py              all checks (must pass)
  python verify_calendar_r16.py --selftest   all checks, then every check again against a planted defect (each must fail)
  python verify_calendar_r16.py --native     compare the titles the native probe logged with the VM's for the same save

Static (bytes of base vs candidate, read only):
  S1 candidate = manifest; every base function entry identical except the four forwarded r15 screen functions (address
     only, new body in the appended code); non-function metadata identical
  S2 the whole base CODE is unchanged (r16 has no same-length swap); r15's nine swap sites still hold r15's operands
  S3 MSG1 identical, STR0 prefix identical; PACT/EX not in the payload
  S4 user saves (copies, r16lib.save_slots): every saved frame (ip + returns) resolves to the same function entry and the
     same instruction bytes at its return address in the candidate; no frame inside a forwarded function
  S5 native opcode audit of the candidate against the runtime exe dispatch table
  S6 pinned functions (KR_T9HomeCasual, KR_T9HomeConfig, CheckGameSysButtons, Run, RunEvent): index, address and code
     bytes identical to the r15 candidate and to the base
Extended VM (the candidate's own compiled bodies, engine calls modelled):
  V1  r15 tables through the VM = chart v2 data; r16 tail table = the colliding cards
  V2  every page in three save states: title lines <= 38 raw characters, height 64 + 34*lines + 48*rows <= 704 px, items
      within their column, no colour marks in items, dialog <= 1280 px wide, r11 colour opt-in
  V3  month pages: every day cell (colour, mark) for the three states x four "today" dates: 놓침 white ▲ / 앞으로 sky ● /
      다 봄 grey ○ / 본편 day ★ (colour of its state) or ☆ (grey) / none white / out of range grey / today gold; the
      legend line; the menu rows 「이름 k/n □□□□□」 and the column rule (3 columns only where 2 would pass 704 px)
  V4  month navigation 4 -> 11 -> 회상 · 그 밖 -> back
  V5-V9 r15's replay / settings / no-context / fail-safe / original menu flows
  V10 seen states (○ this save, △ other save, ● none)
  V11 achievement: month title k/n (p%) and 10-cell bar = independent count; lane rows sum = month title; months + 회상 · 그
      밖 = 1,164; lane title bar line; summary page every number; lanes + 회상 · 그 밖 = total
  V12 lane rows: tails exactly on the rows that collided in r15, rows unique inside every (month, lane), untouched rows equal r15
  V13 home achievement panel: KR_RateText = KR_T8HomeRateText except one label; panel k (VM, KR_PlayerEventCount 0-3) vs
      calendar k, 1,043 vs 1,164 and where the 121 differ
  V14 real saves (증거/probe_regs.json, logged by probe --regs): month pages of each save's month; a month showing ▲ ● ○ ★
      together is required; the pick for the full native probe (work/probe_pick.json)
"""
import sys, json, re, struct, collections, math, copy, time, random, datetime, io, contextlib, bisect
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r16lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
MARKS = '†‡¶〓'
PICK = 2026092401
H_MAX = 704
COL_CAP = {1: 38, 2: 20, 3: 13}          # full-width units per item (1280 px screen, 28 px a glyph, 52 px item margin)
LANES = ['main', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'dungeon']
LANE_KR = ['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전']
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
SLOT_KR = {1: '아침', 2: '밤', 3: '낮', 4: '저녁'}
SLOT_RANK = {1: 0, 3: 1, 4: 2, 2: 3, 0: 9}
LEGEND16 = '†▲놓침 ‡●앞으로 ¶○다 봄 †★☆본편 〓금색†=오늘'
LANE_LEGEND = '●안 봄 △다른 저장 ○이 저장'
WEEKDAYS = '　일　　　월　　　화　　　수　　　목　　　금　　　토'
FORWARD = {'KR_T9MonthPage': 'KR_T16MonthPage', 'KR_T9MemPage': 'KR_T16MemPage', 'KR_T9LaneTitle': 'KR_T16LaneTitle',
           'KR_T9CardRow': 'KR_T16CardRow'}
TOTAL_EVENTS = 1164


def proxy(s):
    return L.encode(s).decode('cp932')


def ko(s):
    return L.decode(s.encode('cp932'))


class Stop(Exception):
    pass


# ============================================================== VM (r15's, plus .LOCALPLUSA)
class VM:
    def __init__(self, ain, meta, mutate=None):
        self.ain = ain
        self.meta = meta
        self.fs = {}
        for f in meta['functions']:
            self.fs.setdefault(L.raw_symbol(meta, f['index']), f)
        self.code = {}
        self.mutate = mutate or {}
        self.dir = L.WORK / 'vm' / L.sha(ain)[:12]
        self.dir.mkdir(parents=True, exist_ok=True)
        self.vars = {}
        self.registered = set()
        self.flags = set()
        self.today = (6, 13)
        self.cur = None
        self.dialogs = []
        self.script = []
        self.calls = []
        self.steps = 0
        self.getflag_neg = 0
        self.config_inner = None

    def reset(self):
        self.vars = {}
        self.cur = None
        self.dialogs = []
        self.script = []
        self.calls = []
        self.config_inner = None

    def load(self, fid):
        if fid in self.code:
            return self.code[fid]
        path = self.dir / f'{fid}.jam'
        if not path.exists():
            L.cmd('ain', 'dump', '--function', L.symbol(self.meta, fid), '-o', path, self.ain)
        ops = []
        labels = {}
        for line in path.read_text('utf8').splitlines():
            s = line.strip()
            if not s or s.startswith((';', 'FUNC ', 'ENDFUNC ', 'EOF ')):
                continue
            if s.endswith(':'):
                labels[s[:-1]] = len(ops)
            else:
                ops.append(s.split(maxsplit=1))
        name = L.raw_symbol(self.meta, fid)
        if name in self.mutate:
            ops = self.mutate[name]([list(o) for o in ops])
        self.code[fid] = (ops, labels)
        return self.code[fid]

    def run(self, name, args=()):
        f = self.fs[name]
        fid = f['index']
        vs = f['arguments'] + f['variables']
        li = {}
        seen = collections.Counter()
        for i, x in enumerate(vs):
            n = x['name'] + (f'#{seen[x["name"]]}' if seen[x['name']] else '')
            seen[x['name']] += 1
            li[n] = i
        loc = {i: ('' if v['type'][0] == 12 else 0) for i, v in enumerate(vs)}
        loc.update(enumerate(args))
        st = []
        ops, labels = self.load(fid)
        pc = 0
        steps = 0
        while pc < len(ops):
            op, *rest = ops[pc]
            arg = rest[0] if rest else ''
            pc += 1
            steps += 1
            self.steps += 1
            assert steps < 5000000, (name, pc)
            if op == 'PUSH':
                st.append(int(arg, 0))
            elif op == 'S_PUSH':
                st.append(json.loads(arg))
            elif op == '.S_LOCALASSIGN':
                v, x = arg.split(' ', 1)
                loc[li[v]] = json.loads(x)
            elif op == '.LOCALASSIGN':
                v, x = arg.rsplit(' ', 1)
                loc[li[v]] = int(x, 0)
            elif op == '.LOCALPLUSA':
                v, x = arg.rsplit(' ', 1)
                loc[li[v]] += int(x, 0)
            elif op == '.LOCALREF':
                st.append(loc[li[arg]])
            elif op in ('.LOCALINC2', '.LOCALINC3', '.LOCALINC'):
                loc[li[arg]] += 1
            elif op in ('.LOCALDEC2', '.LOCALDEC3', '.LOCALDEC'):
                loc[li[arg]] -= 1
            elif op == 'PUSHLOCALPAGE':
                st.append(loc)
            elif op == 'A_REF':
                assert isinstance(st[-1], (str, list)), (name, st[-1])
            elif op in ('S_ASSIGN', 'X_ASSIGN'):
                assert op == 'S_ASSIGN' or arg == '1'
                v = st.pop()
                i = st.pop()
                pg = st.pop()
                pg[i] = v
                st.append(v)
            elif op == 'X_REF':
                assert arg == '1'
                i = st.pop()
                pg = st.pop()
                st.append(pg[i])
            elif op == 'PLUSA':
                v = st.pop()
                i = st.pop()
                pg = st.pop()
                pg[i] += v
                st.append(pg[i])
            elif op == 'X_DUP':
                st += st[-int(arg):]
            elif op in ('DELETE', 'POP'):
                st.pop()
            elif op == 'NOT':
                st.append(int(not st.pop()))
            elif op in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'LT', 'LTE', 'GT', 'GTE', 'EQUALE', 'NOTE',
                        'S_ADD', 'S_EQUALE', 'S_NOTE', 'S_LT', 'S_GT'):
                z = st.pop()
                x = st.pop()
                if op in ('ADD', 'S_ADD'):
                    v = x + z
                elif op == 'SUB':
                    v = x - z
                elif op == 'MUL':
                    v = x * z
                elif op == 'DIV':
                    v = int(x / z)
                elif op == 'MOD':
                    v = x - int(x / z) * z
                elif op in ('LT', 'S_LT'):
                    v = int(x < z)
                elif op == 'LTE':
                    v = int(x <= z)
                elif op in ('GT', 'S_GT'):
                    v = int(x > z)
                elif op == 'GTE':
                    v = int(x >= z)
                elif op in ('EQUALE', 'S_EQUALE'):
                    v = int(x == z)
                else:
                    v = int(x != z)
                st.append(v)
            elif op == 'S_MOD':
                v = st.pop()
                s = st.pop()
                assert arg == '2'
                st.append(s % v)
            elif op in ('IFZ', 'IFNZ'):
                if bool(st.pop()) == (op == 'IFNZ'):
                    pc = labels[arg]
            elif op == 'JUMP':
                pc = labels[arg]
            elif op == 'CALLFUNC':
                ff = self.fs[arg]
                n = len(ff['arguments'])
                aa = st[-n:] if n else []
                st = st[:-n] if n else st
                out = self.native(arg, aa)
                if ff['return-type'][0] != 0:
                    st.append(out)
            elif op == 'CALLHLL':
                lib, method, _ = arg.split()
                self.hll(lib, method, st)
            elif op == 'RETURN':
                assert len(st) == int(f['return-type'][0] != 0), (name, st)
                return st[0] if st else None
            else:
                raise AssertionError((name, op, arg))
        raise AssertionError(('no return', name))

    def dialog(self):
        if self.cur is None:
            self.cur = dict(title=None, cols=1, items=[], type=None, limit=None)
        return self.cur

    def native(self, name, aa):
        if name == '■選択ダイアログ／初期化':
            self.cur = None
            return None
        if name == '■選択ダイアログ／タイプ設定':
            self.dialog()['type'] = aa[0]
            return None
        if name == '■選択ダイアログ／クリック制限／全体':
            self.dialog()['limit'] = 'all'
            return None
        if name == '■選択ダイアログ／横項目数':
            self.dialog()['cols'] = aa[0]
            return None
        if name == '■選択ダイアログ／タイトル設定':
            self.dialog()['title'] = aa[0]
            return None
        if name == '■選択ダイアログ／選択肢追加':
            self.dialog()['items'].append((aa[0], aa[1], aa[2], int(bool(aa[3]))))
            return None
        if name == '■選択ダイアログ／実行':
            d = self.cur
            self.cur = None
            assert d is not None, 'run without a dialog'
            d['opt_title'] = self.vars.get('YoruKR.T8.Title', '')
            d['opt_color'] = self.vars.get('YoruKR.T8.Color', '')
            d['unwind'] = self.vars.get('YoruKR.T9.Unwind', '')
            self.dialogs.append(d)
            if not self.script:
                raise Stop('dialog without a scripted answer: ' + ko(d['title'] or '').split('\n')[0])
            ans = self.script.pop(0)
            r = ans(d) if callable(ans) else ans
            d['answer'] = r
            return r
        if name == '■選択ダイアログ／存在確認':
            return int(self.cur is not None)
        if name == '■シンプルダイアログ':
            self.calls.append(('simple', ko(aa[0])))
            return None
        if name == 'N_ScenarioRegister::IsRegisteredEvent':
            return int(aa[0] in self.registered)
        if name == 'L_Calendar::GetMonth':
            return self.today[0]
        if name == 'L_Calendar::GetDay':
            return self.today[1]
        if name in ('LSys3xScript::Prepare', 'LSys3xScript::RunEvent', '■ＡＤＶ消し', '■カジュアルモード設定呼び出し',
                    'KR_T8CharDatePage', 'KR_T8InfoPage'):
            self.calls.append((name, list(aa)))
            return 1 if name == 'LSys3xScript::RunEvent' else None
        if name == '▲コンフィグ実行':
            self.calls.append((name, list(aa)))
            if self.config_inner:
                self.config_inner(self)
            return None
        if name == 'KR_T8PlaceText':
            return proxy('PLACE %d' % aa[0])
        if name == 'KR_T8PartyText':
            return proxy('PARTY')
        return self.run(name, aa)

    def hll(self, lib, method, st):
        if lib == 'SystemService':
            if method == 'SystemVariable_Get':
                st.append(self.vars.get(st.pop(), ''))
                return
            if method == 'SystemVariable_Set':
                v = st.pop()
                k = st.pop()
                self.vars[k] = v
                return
        if lib == 'MsgSkip' and method == 'GetFlag':
            m = st.pop()
            if m < 0:
                self.getflag_neg += 1
            st.append(int(m in self.flags))
            return
        if lib == 'String':
            if method == 'ToInt':
                st.append(int(st.pop()))
                return
            if method == 'Length':
                st.append(len(st.pop()))
                return
            if method == 'Find':
                key = st.pop()
                text = st.pop()
                st.append(text.find(key))
                return
            if method == 'GetPart#1':
                count = st.pop()
                idx = st.pop()
                text = st.pop()
                st.append(text[idx:idx + count])
                return
        raise AssertionError((lib, method))

    def v(self, key):
        return self.vars.get('YoruKR.T9.' + key, '')


# ============================================================== expectations (independent of the build script)
def expectations():
    sys.path.insert(0, str(L.FLOW / 'chart'))
    import build_chart_v2 as V2
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data = V2.build(str(L.TMP / 'chart_v2_from_r16_verify.html'))
    ev = {int(k): v for k, v in data['ev'].items()}
    cards = []
    for c in data['cards']:
        pl = c['pl']
        cards.append(dict(key=c['key'], month=int(c['page']), lane=LANES.index(c['lane']), day=pl.get('d', 0), slot=pl.get('slot', 0) or 0,
                          size=c['n'], entry=c['entry'], stages=[r[0] for r in c['rows'] if r[6]]))
    cards.sort(key=lambda x: (x['month'], x['lane'], x['day'] if x['day'] else 99, SLOT_RANK[x['slot']], x['key']))
    chips = []
    for ch in data['chips']:
        month = 12 if ch['page'] == 'mem' else int(ch['page'])
        lane = LANES.index(ch['lane']) if ch['lane'] in LANES else (8 + int(ch['lane'][3:]) if ch['lane'].startswith('mem') else 16)
        chips.append(dict(id=ch['id'], month=month, lane=lane, kind=KINDS.index(ch['kind']), scenes=[x[0] for x in ch['order'] if x[4]]))
    return dict(data=data, ev=ev, cards=cards, chips=chips, w1={p['m']: p['w1'] for p in data['pages'] if p.get('m')}, mlen=V2.MLEN)


# ---- independent r16 display model
def bar(k, n, cells):
    f = min(cells, max(0, (k * cells) // n)) if n > 0 else 0
    return '■' * f + '□' * (cells - f)


def pct(k, n):
    p = (k * 200 + n) // (2 * n) if n > 0 else 0
    if p > 99 and k < n:
        p = 99
    return '(%d%%)' % p


def pct1(k, n):
    p = (k * 2000 + n) // (2 * n) if n > 0 else 0
    if p > 999 and k < n:
        p = 999
    return '(%d.%d%%)' % (p // 10, p % 10)


def month_name(m):
    return '회상 · 그 밖' if m == 12 else '%d월' % m


def seen_fn(X, regs, no):
    return X['ev'][no]['fn'] in regs


def units(X, regs, month, lane=None):
    """(seen, total) scene units of a month (and a lane): card stages + drawer scenes."""
    n = k = 0
    for c in X['cards']:
        if c['month'] == month and (lane is None or c['lane'] == lane):
            n += len(c['stages'])
            k += sum(1 for s in c['stages'] if seen_fn(X, regs, s))
    for ch in X['chips']:
        if ch['month'] == month and (lane is None or ch['lane'] == lane):
            n += len(ch['scenes'])
            k += sum(1 for s in ch['scenes'] if seen_fn(X, regs, s))
    return k, n


def drawer_units(X, regs, month):
    n = k = 0
    for ch in X['chips']:
        if ch['month'] == month:
            n += len(ch['scenes'])
            k += sum(1 for s in ch['scenes'] if seen_fn(X, regs, s))
    return k, n


def day_state(X, regs, month, day, today):
    """(state, main): state 0 none, 1 앞으로, 2 다 봄, 3 놓침."""
    on = [c for c in X['cards'] if c['month'] == month and c['day'] == day]
    if not on:
        return 0, False
    main = any(c['lane'] == 0 for c in on)
    unseen = any(not seen_fn(X, regs, s) for c in on for s in c['stages'])
    if not unseen:
        return 2, main
    return (3 if (month, day) < tuple(today) else 1), main


def want_cell(X, regs, month, day, today):
    inr = not ((month == 4 and day < 9) or (month == 11 and day > 17))
    if not inr:
        col, mark = 3, '　'
    else:
        st, main = day_state(X, regs, month, day, today)
        col = {0: 1, 1: 2, 2: 3, 3: 1}[st]
        if st == 0:
            mark = '　'
        elif main:
            mark = '☆' if st == 2 else '★'
        else:
            mark = {1: '●', 2: '○', 3: '▲'}[st]
    if (month, day) == tuple(today):
        col = 0
    return col, mark


def month_cols(X, month):
    lanes = sum(1 for l in range(9) if units(X, set(), month, l)[1] > 0)
    items = lanes + 4 + (1 if month > 4 else 0)
    weeks = math.ceil((X['w1'][month] + X['mlen'][month]) / 7)
    return 2 if 64 + 34 * (3 + weeks) + 48 * math.ceil(items / 2) <= H_MAX else 3


# ============================================================== static checks
def static_checks(base, cand, man, m, nm, counts, mutate_bytes=None, mutate_meta=None, parts=('S1', 'S2', 'S3', 'S4', 'S6')):
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
        counts['S1_metadata'] += 1
    if 'S2' in parts:
        assert new[16:16 + oldn] == old[16:16 + oldn], 'base CODE bytes changed'
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s in rman['same_length_sites']:
            ad = s['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s['after'], ('r15 swap missing in the base', s['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s['after'], ('r15 swap site no longer applied', s['function'], s['replacement'])
        counts['S2_r15_sites_kept'] = len(rman['same_length_sites'])
        counts['S2_base_code_bytes_identical'] = oldn
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed']
        counts['S3_text'] += 1
    if 'S6' in parts:
        ra = L.R15 / 'candidate' / 'NightRemaster.ain'
        rraw = L.unpack(ra.read_bytes())
        rcode = rraw[16:16 + struct.unpack_from('<I', rraw, 12)[0]]
        rm = L.read_meta(L.R15 / 'work' / 'build' / 'candidate_meta.json')
        rv = L.versions(L.R15 / 'work' / 'build' / 'candidate_raw_code.jam')
        starts = sorted({v['start'] for vs in rv.values() for v in vs})
        ccode = new[16:16 + struct.unpack_from('<I', new, 12)[0]]
        bcode = old[16:16 + oldn]
        for name in L.PINNED:
            i = L.fid_of(rm, name)
            f = rm['functions'][i]
            assert nm['functions'][i] == f == m['functions'][i], ('pinned function entry changed', name)
            j = bisect.bisect_right(starts, f['address'])
            end = starts[j] - 6 if j < len(starts) else len(rcode)
            ref = rcode[f['address'] - 6:end]
            assert ccode[f['address'] - 6:end] == ref == bcode[f['address'] - 6:end], ('pinned code changed', name)
            counts['S6_pinned_bytes'] += len(ref)
        counts['S6_pinned_functions'] = len(L.PINNED)
    if 'S4' not in parts:
        return []
    vers = L.versions(L.WORK / 'base' / 'raw_code.jam')
    bycrc = collections.defaultdict(list)
    for f in m['functions']:
        bycrc[f['crc'] & 0xffffffff].append(f)
    frames = []
    live = 0
    for name, path in L.save_slots().items():
        row = L.save_records(path)
        assert row is not None, name
        for rr in [row['ip']] + row['returns']:
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
    return frames


# ============================================================== VM checks
def table_checks(vm, X, counts):
    cards, chips, ev = X['cards'], X['chips'], X['ev']
    stage_i = 0
    for k, c in enumerate(cards):
        info = vm.run('KR_T9CardInfo', [k])
        got = dict(lane=info // 100000, day=(info // 1000) % 100, slot=(info // 100) % 10, size=info % 100, entry=vm.run('KR_T9CardEntry', [k]))
        want = dict(lane=c['lane'], day=c['day'], slot=c['slot'], size=c['size'], entry=c['entry'])
        assert got == want, (k, c['key'], got, want)
        s0 = vm.run('KR_T9CardStage', [k])
        assert s0 == stage_i and [vm.run('KR_T9StageEv', [s0 + i]) for i in range(c['size'])] == c['stages'], (k, c['key'])
        stage_i += c['size']
        assert vm.run('KR_T9CardMonth', [k]) == c['month']
    for mo in range(4, 12):
        ks = [k for k, c in enumerate(cards) if c['month'] == mo]
        assert (vm.run('KR_T9CardFirst', [mo]), vm.run('KR_T9CardEnd', [mo])) == ((ks[0], ks[-1] + 1) if ks else (0, 0)), mo
        assert vm.run('KR_T9W1', [mo]) == X['w1'][mo] and vm.run('KR_T9MLen', [mo]) == X['mlen'][mo]
    scene_i = 0
    for c, ch in enumerate(chips):
        info = vm.run('KR_T9ChipInfo', [c])
        assert (info // 10000, (info // 1000) % 10, info % 1000) == (ch['lane'], ch['kind'], len(ch['scenes'])), (c, ch['id'])
        s0 = vm.run('KR_T9ChipScene', [c])
        assert s0 == scene_i and [vm.run('KR_T9SceneEv', [s0 + i]) for i in range(len(ch['scenes']))] == ch['scenes'], ch['id']
        scene_i += len(ch['scenes'])
        assert vm.run('KR_T9ChipMonth', [c]) == ch['month'], ch['id']
    for no, e in ev.items():
        assert vm.run('KR_T9EvMsg', [no]) == (e['m0'] if e['m0'] is not None else -1), no
        assert vm.run('KR_T9Fn', [no]) == e['fn'], (no, vm.run('KR_T9Fn', [no]))
        assert ko(vm.run('KR_T9EvWhen', [no])) and ko(vm.run('KR_T9EvWho', [no])), no
    assert sorted([s for c in cards for s in c['stages']] + [s for ch in chips for s in ch['scenes']]) == sorted(ev)
    assert len(ev) == TOTAL_EVENTS
    counts['V1_cards'] = len(cards)
    counts['V1_stages'] = stage_i
    counts['V1_drawers'] = len(chips)
    counts['V1_scenes'] = scene_i
    counts['V1_events'] = len(ev)


def geometry(d):
    title = ko(d['title'])
    lines = title.split('\n')
    cols = d['cols']
    rows = math.ceil(len(d['items']) / cols)
    return lines, rows, 64 + 34 * len(lines) + 48 * rows


WIDEST = dict(title='', item='')


def units_w(t):
    """Glyph width in full-width units: ASCII (digits, spaces, /, parentheses, %) draws half width."""
    return sum(0.5 if ord(ch) < 0x80 else 1.0 for ch in t)


def check_dialog(d, counts):
    """C_SelectDialog@CreateParts: title width = longest line's character count (marks included) x size + spacing + 48;
    column width = max(widest item + 52, title width / columns); the dialog is columns x column width + 4 wide."""
    lines, rows, h = geometry(d)
    for x in lines + [ko(t) for _, t, _, _ in d['items']]:
        assert not re.search(r'[0-9A-Za-z]…', x), ('a number or event id cut by 「…」', x)
    for x in lines:
        assert len(x) <= 38, ('title line over 38', len(x), x)
        if len(x) > len(WIDEST['title']):
            WIDEST['title'] = x
    assert h <= H_MAX, ('dialog too tall', h, len(lines), rows, lines[0])
    cap = COL_CAP[d['cols']]
    widest = 0
    for (iid, text, help_, off) in d['items']:
        t = ko(text)
        assert len(t) <= 38 and units_w(t) <= cap, ('item too wide for its column', d['cols'], units_w(t), t)
        assert not any(mk in t for mk in MARKS), ('colour mark in an item', t)
        widest = max(widest, units_w(t))
        if units_w(t) > units_w(WIDEST['item']):
            WIDEST['item'] = t
    width = max(d['cols'] * (widest * 28 + 52), max(len(x) for x in lines) * 28.5 + 48) + 4
    assert width <= 1280, ('dialog wider than the screen', width, lines[0])
    counts['V2_max_width_px'] = max(counts['V2_max_width_px'], int(width))
    assert d['type'] == 2026091602 and d['limit'] == 'all', 'dialog style'
    assert d['opt_color'] == '1' and d['opt_title'] == d['title'], 'r11 colour opt-in not set for the draw'
    counts['V2_dialogs'] += 1
    counts['V2_max_height'] = max(counts['V2_max_height'], h)
    counts['V2_max_title_lines'] = max(counts['V2_max_title_lines'], len(lines))


def lane_title_expect(X, regs, mo, lane, page, pages):
    nc = sum(1 for c in X['cards'] if c['month'] == mo and c['lane'] == lane)
    ns = sum(len(ch['scenes']) for ch in X['chips'] if ch['month'] == mo and ch['lane'] == lane)
    k, n = units(X, regs, mo, lane)
    tag = ('　〓%d/%d쪽' % (page + 1, pages)) if pages > 1 else ''
    return ('〓%s · %s　†카드 %d · 서랍 %d%s\n%s %d/%d 본 것　%s' % (month_name(mo), LANE_KR[lane], nc, ns, tag, bar(k, n, 10), k, n, LANE_LEGEND))


def pages_all(vm, X, counts, state_name):
    """Every page once (lane/drawer/stage/month-drawer pages through all their sub-pages) + summary + 회상 · 그 밖."""
    cards, chips = X['cards'], X['chips']

    def walk(fn, args, pages):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'P'
        vm.script = [12] * (pages - 1) + [0]
        vm.run(fn, args)
        for d in vm.dialogs:
            check_dialog(d, counts)
        assert not vm.script, (fn, args, 'page count differs', len(vm.script))
        return vm.dialogs

    for mo in range(4, 12):
        for lane in range(9):
            nc = sum(1 for c in cards if c['month'] == mo and c['lane'] == lane)
            nd = sum(1 for ch in chips if ch['month'] == mo and ch['lane'] == lane)
            if nc + nd:
                n = nc + nd
                per = 10 if n <= 10 else 8
                pages = math.ceil(n / per)
                ds = walk('KR_T9LanePage', [mo, lane], pages)
                assert sum(len(d['items']) - (3 if n > 10 else 1) for d in ds) == n, (mo, lane)
                for p, d in enumerate(ds):
                    assert ko(d['title']) == lane_title_expect(X, vm.registered, mo, lane, p, pages), (mo, lane, ko(d['title']))
                counts['V11_lane_titles'] += len(ds)
        n = sum(1 for ch in chips if ch['month'] == mo)
        walk('KR_T9MonthChips', [mo], max(1, math.ceil(n / (10 if n <= 10 else 8))))
    for k, c in enumerate(cards):
        walk('KR_T9CardPage', [k, c['month']], 1)
        if c['size'] > 1:
            walk('KR_T9StagePage', [k, c['month']], math.ceil(c['size'] / 30))
    for i, ch in enumerate(chips):
        walk('KR_T9ChipPage', [i], math.ceil(len(ch['scenes']) / 30))
    vm.reset()
    vm.script = [0]
    vm.run('KR_T9MemPage')
    for d in vm.dialogs:
        check_dialog(d, counts)
    k, n = units(X, vm.registered, 12)
    head = ko(vm.dialogs[0]['title']).split('\n')[0]
    assert head == '〓회상 · 그 밖　%s %d/%d %s' % (bar(k, n, 10), k, n, pct(k, n)), head
    vm.reset()
    vm.script = [0]
    vm.run('KR_T16SummaryPage')
    for d in vm.dialogs:
        check_dialog(d, counts)
    summary_check(ko(vm.dialogs[0]['title']), X, vm.registered, counts)
    assert [(i, ko(t)) for i, t, _, _ in vm.dialogs[0]['items']] == [(0, '돌아가기')]
    counts['V2_states'] += 1


def summary_expect(X, regs):
    lines = []
    tk = tn = 0
    for m in (4, 6, 8, 10):
        k1, n1 = units(X, regs, m)
        k2, n2 = units(X, regs, m + 1)
        tk += k1 + k2
        tn += n1 + n2
        lines.append('†%s %s %d/%d　　%s %s %d/%d' % (month_name(m), bar(k1, n1, 5), k1, n1, month_name(m + 1), bar(k2, n2, 5), k2, n2))
    k, n = units(X, regs, 12)
    tk += k
    tn += n
    lines.append('†%s %s %d/%d' % (month_name(12), bar(k, n, 5), k, n))
    for l in range(0, 9, 2):
        cells = []
        for ll in (l, l + 1):
            if ll > 8:
                continue
            kk = nn = 0
            for m in range(4, 12):
                a, b = units(X, regs, m, ll)
                kk += a
                nn += b
            cells.append('%s %s %d/%d' % (LANE_KR[ll], bar(kk, nn, 5), kk, nn))
        lines.append('†' + '　　'.join(cells))
    return ['〓달성도　전체 %s %d/%d %s' % (bar(tk, tn, 10), tk, tn, pct1(tk, tn))] + lines, tk, tn


def summary_check(title, X, regs, counts):
    want, tk, tn = summary_expect(X, regs)
    got = title.split('\n')
    assert got == want, ('summary page', [(a, b) for a, b in zip(got, want) if a != b][:3])
    assert tn == TOTAL_EVENTS, ('summary total is not 1,164', tn)
    assert len(got) <= 12
    nums = [tuple(map(int, z)) for z in re.findall(r'(\d+)/(\d+)', '\n'.join(got[1:]))]
    months, mem, lanes = nums[:8], nums[8], nums[9:]
    assert len(lanes) == 9
    assert sum(b for _, b in months) + mem[1] == tn and sum(a for a, _ in months) + mem[0] == tk, 'months + 회상 · 그 밖 != total'
    assert sum(b for _, b in lanes) + mem[1] == tn and sum(a for a, _ in lanes) + mem[0] == tk, 'lanes + 회상 · 그 밖 != total'
    counts['V11_summary_pages'] += 1
    return tk, tn


def event_pages(vm, X, counts):
    for no in sorted(X['ev']):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'C'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, proxy('6월 · 호시카와 · 특훈 뒤 대화')])
        check_dialog(vm.dialogs[0], counts)
    counts['V2_event_pages'] = len(X['ev'])


def calendar_cells(title):
    """(line segments with colours) -> {day: (colour, mark)} for the week lines of a month title (after 3 header lines)."""
    rows = title.split('\n')[3:]
    out = {}
    for row in rows:
        color = 0
        chars = []
        for ch in row:
            if ch in MARKS:
                color = {'†': 1, '‡': 2, '¶': 3, '〓': 0}[ch]
                continue
            chars.append((ch, color))
        for i in range(0, len(chars), 4):
            cell = chars[i:i + 3]
            digits = ''.join(c for c, _ in cell[:2]).replace('　', '')
            if not digits:
                continue
            day = int(''.join(str('０１２３４５６７８９'.index(c)) for c in digits))
            out[day] = (cell[1][1], cell[2][0] if len(cell) > 2 else '　')
            assert cell[0][1] == cell[1][1] == (cell[2][1] if len(cell) > 2 else cell[1][1]), ('one day in two colours', day)
    return out


def month_page_check(vm, X, mo, counts, regs, today):
    """One month page: cells, head, legend, weekday line, menu rows, columns, sums. Returns the marks shown."""
    vm.registered = regs
    vm.today = today
    vm.reset()
    vm.script = [0]
    r = vm.run('KR_T9MonthPage', [mo])
    assert r == 0
    d = vm.dialogs[0]
    check_dialog(d, counts)
    title = ko(d['title'])
    lines = title.split('\n')
    k, n = units(X, regs, mo)
    assert lines[0] == '〓%d월 이벤트 달력　%s %d/%d %s' % (mo, bar(k, n, 10), k, n, pct(k, n)), lines[0]
    assert lines[1] == LEGEND16 and lines[2] == WEEKDAYS, lines[1:3]
    cells = calendar_cells(title)
    assert sorted(cells) == list(range(1, X['mlen'][mo] + 1)), (mo, sorted(cells)[:5])
    shown = collections.Counter()
    for day, got in cells.items():
        want = want_cell(X, regs, mo, day, today)
        assert got == want, (mo, day, today, got, want)
        shown[got[1]] += 1
    counts['V3_cells'] += len(cells)
    cols = month_cols(X, mo)
    assert d['cols'] == cols, (mo, d['cols'], cols)
    items = {iid: ko(t) for iid, t, _, _ in d['items']}
    lane_sum = 0
    for lane in range(9):
        a, b = units(X, regs, mo, lane)
        if b:
            assert items.get(20 + lane) == '%s %d/%d %s' % (LANE_KR[lane], a, b, bar(a, b, 5)), (mo, lane, items.get(20 + lane))
            lane_sum += b
        else:
            assert 20 + lane not in items, (mo, lane)
    assert lane_sum == n, ('month menu rows do not add up to the title', mo, lane_sum, n)
    dk, dn = drawer_units(X, regs, mo)
    assert items.get(30) == '%s %d/%d %s' % ('서랍' if cols == 3 else '이달의 서랍', dk, dn, bar(dk, dn, 5)), items.get(30)
    assert (11 in items) == (mo > 4) and 12 in items and 0 in items and items.get(31) == '달성도 보기'
    assert [iid for iid, _, _, _ in d['items']][-2:] == [31, 0], '달성도 보기 must sit right above 돌아가기'
    counts['V3_month_menus'] += 1
    return shown, n


def calendar_checks(vm, X, counts, regs_list):
    for regs in regs_list:
        for today in [(4, 9), (6, 13), (9, 30), (11, 17)]:
            total = 0
            for mo in range(4, 12):
                _, n = month_page_check(vm, X, mo, counts, regs, today)
                total += n
            total += units(X, regs, 12)[1]
            assert total == TOTAL_EVENTS, ('eight months + 회상 · 그 밖 != 1,164', total)
            counts['V11_year_sums'] += 1


def synthetic_mid_month(X, month=8, day=15):
    """A played-in-order state for 8/15 (August is the month with the most days without a main-story card: 1 3 6 7 11 30):
    everything dated before today is seen except the cards of the first such day, nothing later -> ▲ ● ○ ★ ☆ all appear."""
    free = sorted({c['day'] for c in X['cards'] if c['month'] == month and c['day'] and c['day'] < day}
                  - {c['day'] for c in X['cards'] if c['month'] == month and c['lane'] == 0})
    skip = free[0]
    regs = set()
    for c in X['cards']:
        if (c['month'], c['day'] or 1) < (month, day) and not (c['month'] == month and c['day'] == skip):
            regs |= {X['ev'][s]['fn'] for s in c['stages']}
    return regs, (month, day)


def nav_checks(vm, X, counts):
    vm.reset()
    vm.script = [12] * 8 + [11, 11, 0]
    vm.run('KR_T9Calendar', [4, -1])
    heads = [ko(d['title']).split('\n')[0].translate({ord(c): None for c in MARKS}) for d in vm.dialogs]
    want = ['%d월 이벤트 달력' % mo for mo in range(4, 12)] + ['회상 · 그 밖', '11월 이벤트 달력', '10월 이벤트 달력']
    assert [h.split('　')[0] for h in heads] == want, heads
    assert not vm.script
    counts['V4_navigation'] += 1


def home_menu(vm):
    vm.native('■選択ダイアログ／タイトル設定', [proxy('●본거지')])
    for i in (11, 12, 14):
        vm.native('■選択ダイアログ／選択肢追加', [i, proxy('메뉴'), '', 0])


def home_run(vm):
    home_menu(vm)
    r = vm.run('KR_T9HomeMenuRun', [1, 200])
    assert vm.cur is None, 'the home menu dialog was left behind'
    return r


def first_card(X, month, lane):
    ks = [k for k, c in enumerate(X['cards']) if c['month'] == month and c['lane'] == lane]
    return ks[0], X['cards'][ks[0]]


def flow_checks(vm, X, counts):
    vm.reset()
    vm.registered = set()
    pc = next(c for c in X['cards'] if 1 <= c['lane'] <= 7)
    mo, lane = pc['month'], pc['lane']
    vm.today = (mo, 1)
    vm.script = [PICK]
    assert home_run(vm) == PICK and vm.v('Ctx') == 'P'
    k, card = first_card(X, mo, lane)
    vm.script = [3, 100, 13]
    vm.dialogs = []
    vm.run('KR_T8CharMissingPage', [lane + 1])
    items0 = [(i, ko(t)) for i, t, _, _ in vm.dialogs[0]['items']]
    assert items0 == [(1, '날짜별로 보기'), (2, '던전 파티별로 보기'), (3, '달력으로 보기'), (0, '돌아가기')], items0
    heads = [ko(d['title']).split('\n')[0] for d in vm.dialogs]
    name = LANE_KR[lane]
    assert len(vm.dialogs) == 3 and heads[1].startswith('〓%d월 · %s' % (mo, name)) and heads[2].startswith('〓%d' % mo), heads
    assert all(d['unwind'] == '' for d in vm.dialogs), 'a dialog opened while unwinding'
    assert vm.v('Play') == str(card['entry']) and vm.v('Unwind') == '1', (vm.v('Play'), vm.v('Unwind'))
    assert not any(c[0] == 'KR_T8CharDatePage' for c in vm.calls), 'date page opened instead of the calendar'
    vm.script = []
    vm.dialogs = []
    assert home_run(vm) == 3 and not vm.dialogs, 'home menu must return 3 without a dialog'
    assert vm.v('Playing') == '1' and vm.v('Unwind') == '' and vm.v('Ctx') == ''
    vm.calls = []
    vm.run('KR_T9HomeCasual')
    want_fn = X['ev'][card['entry']]['fn']
    assert [c[0] for c in vm.calls] == ['LSys3xScript::Prepare', 'LSys3xScript::RunEvent', '■ＡＤＶ消し'], vm.calls
    assert vm.calls[0][1] == [want_fn] and vm.calls[2][1] == [1, 0], vm.calls
    assert vm.v('Play') == '' and vm.v('Playing') == ''
    vm.script = [11]
    assert home_run(vm) == 11 and len(vm.dialogs) == 1
    counts['V5_play_from_window'] += 1
    vm.reset()
    vm.today = (6, 13)
    k2, card2 = first_card(X, 6, 0)

    def inside(v):
        assert v.v('Ctx') == 'C'
        v.script = [1, 20, 100, 13]
        v.run('KR_T8CharMissingMenu')
        assert not v.script, v.script
        assert v.v('Unwind') == '' and v.v('Req') == str(card2['entry']) and v.v('Play') == '', (v.v('Unwind'), v.v('Req'))
    vm.config_inner = inside
    vm.run('KR_T9HomeConfig', [0, 0])
    simple = [c for c in vm.calls if c[0] == 'simple']
    assert simple == [('simple', '재생을 예약했습니다.\n설정 창을 닫으면 본거지에서 재생합니다.')], simple
    first = [(i, ko(t)) for i, t, _, _ in vm.dialogs[0]['items']]
    assert first[0] == (1, '이벤트 달력') and [i for i, _ in first] == [1, 2, 3, 4, 5, 6, 7, 8, 0], first
    assert vm.v('Play') == str(card2['entry']) and vm.v('Req') == '' and vm.v('Ctx') == '' and vm.v('Unwind') == ''
    card_dialog = vm.dialogs[-1]
    assert '설정 창을 닫으면 본거지에서 재생합니다.' in ko(card_dialog['title']) and card_dialog['items'][0][3] == 0
    vm.script = []
    vm.dialogs = []
    assert home_run(vm) == 3 and not vm.dialogs
    vm.calls = []
    vm.run('KR_T9HomeCasual')
    assert vm.calls[0] == ('LSys3xScript::Prepare', [X['ev'][card2['entry']]['fn']]), vm.calls
    counts['V6_play_from_settings'] += 1
    vm.reset()
    vm.script = [13]
    vm.run('KR_T9CardPage', [k, mo])
    d = vm.dialogs[0]
    assert d['items'][0][:2] == (13, proxy('이 장면 재생')) and d['items'][0][3] == 1, d['items'][0]
    assert '본거지에서 연 달력에서만 재생할 수 있습니다.' in ko(d['title'])
    assert vm.v('Play') == '' and vm.v('Req') == '' and vm.v('Unwind') == ''
    vm.reset()
    vm.vars.update({'YoruKR.T9.Ctx': 'C', 'YoruKR.T9.Req': '10001', 'YoruKR.T9.Unwind': '1'})
    vm.script = [11]
    assert home_run(vm) == 11 and vm.v('Req') == '' and vm.v('Unwind') == '' and vm.v('Play') == ''
    vm.calls = []
    vm.run('KR_T9HomeCasual')
    assert vm.calls == [('■カジュアルモード設定呼び出し', [])], vm.calls
    counts['V7_no_context'] += 1
    vm.reset()
    vm.vars.update({'YoruKR.T9.Play': '10001', 'YoruKR.T9.Playing': '1'})
    vm.script = [12]
    assert home_run(vm) == 12 and vm.v('Play') == '' and vm.v('Playing') == ''
    vm.calls = []
    vm.run('KR_T9HomeCasual')
    assert vm.calls == [('■カジュアルモード設定呼び出し', [])]
    counts['V8_failsafe'] += 1
    vm.reset()
    vm.script = [5, 0, 0]
    vm.run('KR_T8CharMissingMenu')
    assert len(vm.dialogs) == 3 and ko(vm.dialogs[1]['title']) == 'PLACE 5', [ko(d['title'])[:20] for d in vm.dialogs]
    vm.reset()
    vm.script = [1, 2, 0]
    vm.run('KR_T8CharMissingPage', [4])
    assert [c[0] for c in vm.calls] == ['KR_T8CharDatePage', 'KR_T8InfoPage'] and vm.calls[0][1] == [4], vm.calls
    counts['V9_original_dispatch'] += 1
    # summary from the month page and back
    vm.reset()
    vm.today = (6, 13)
    vm.script = [31, 0, 0]
    assert vm.run('KR_T9MonthPage', [6]) == 0
    assert [ko(d['title']).split('\n')[0][:4] for d in vm.dialogs] == ['〓6월 ', '〓달성도', '〓6월 '], [ko(d['title'])[:8] for d in vm.dialogs]
    counts['V11_summary_from_month'] += 1


def seen_checks(vm, X, counts):
    ev = X['ev']
    withmsg = [no for no, e in sorted(ev.items()) if e['m0'] is not None]
    nomsg = [no for no, e in sorted(ev.items()) if e['m0'] is None]
    vm.reset()
    vm.getflag_neg = 0
    a, b, c = withmsg[0], withmsg[1], withmsg[2]
    vm.registered = {ev[a]['fn']}
    vm.flags = {ev[b]['m0']}
    assert [vm.run('KR_T9State', [x]) for x in (a, b, c)] == [2, 1, 0]
    assert [ko(vm.run('KR_T9Mark', [s])) for s in (2, 1, 0)] == ['○', '△', '●']
    vm.flags = set(ev[x]['m0'] for x in withmsg)
    for no in nomsg:
        assert vm.run('KR_T9State', [no]) == 0
    assert vm.getflag_neg == 0, 'MsgSkip.GetFlag called with -1'
    rnd = random.Random(20260927)
    regs = {e['fn'] for no, e in ev.items() if rnd.random() < 0.5}
    vm.registered = regs
    for i, ch in enumerate(X['chips']):
        assert vm.run('KR_T9ChipSeen', [i]) == sum(1 for s in ch['scenes'] if ev[s]['fn'] in regs), ch['id']
    for k, cd in enumerate(X['cards']):
        assert vm.run('KR_T9CardSeenStages', [k]) == sum(1 for s in cd['stages'] if ev[s]['fn'] in regs), cd['key']
    counts['V10_seen_states'] += 1
    vm.flags = set()
    return regs


def row_checks(vm, X, counts):
    """V12: tails exactly where r15's rows collided; rows unique in (month, lane); untouched rows equal r15's."""
    cards = X['cards']
    vm.registered = set()
    rows = collections.defaultdict(list)
    r15rows = collections.defaultdict(list)
    tails = []
    for k, c in enumerate(cards):
        t = ko(vm.run('KR_T9CardRow', [k, c['month']]))
        when = ko(vm.run('KR_T9CardWhen', [k, c['month']]))
        cond = ko(vm.run('KR_T9CardCond', [k]))
        old = when + ' ●' + ((' ' + cond) if cond else '') + ((' (%d단계)' % c['size']) if c['size'] > 1 else '')
        tail = ' E%05d' % c['entry']
        assert len(t) <= 38, t
        if vm.run('KR_T16CardTail', [k]):
            assert t.endswith(tail), t
            tails.append(k)
            body = t[:-len(tail)]
            assert body == old or (body.endswith(' …') and old.startswith(body[:-2])) or re.sub(r' \(\d+단계\)$', '', body).endswith(' …'), (body, old)
        else:
            assert t == old, (t, old)
        rows[(c['month'], c['lane'])].append(t.replace(' ● ', ' ').replace(' ●', ''))
        r15rows[(c['month'], c['lane'])].append((k, old))
    dup = {key: [x for x, n in collections.Counter(v).items() if n > 1] for key, v in rows.items()}
    dup = {key: v for key, v in dup.items() if v}
    assert not dup, ('lane rows collide', dup)
    want = []
    for key, v in r15rows.items():
        cnt = collections.Counter(o for _, o in v)
        want += [k for k, o in v if cnt[o] > 1]
    assert sorted(tails) == sorted(want), ('tails not exactly on the colliding rows', sorted(set(tails) ^ set(want)))
    counts['V12_tailed_rows'] = len(tails)
    counts['V12_collision_groups_in_r15'] = sum(1 for v in r15rows.values() for o, n in collections.Counter(o for _, o in v).items() if n > 1)
    counts['V12_duplicate_rows_after'] = 0
    counts['V12_rows'] = len(cards)


def panel_groups(vm):
    path = vm.dir / 'panel_KR_PlayerEventCount.jam'
    if not path.exists():
        L.cmd('ain', 'dump', '--function', 'KR_PlayerEventCount', '-o', path, vm.ain)
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


def panel_checks(vm, X, counts, states):
    """V13: the home achievement panel (r9 KR_T8, the canonical one) against the calendar summary."""
    texts = {}
    for n in ('KR_T8HomeRateText', 'KR_RateText'):
        p = vm.dir / f'panel_{n}.jam'
        if not p.exists():
            L.cmd('ain', 'dump', '--function', n, '-o', p, vm.ain)
        texts[n] = [l.strip() for l in p.read_text('utf8').splitlines() if l.strip() and not l.startswith(';')]
    a, b = texts['KR_T8HomeRateText'], texts['KR_RateText']
    diff = [(x, y) for x, y in zip(a, b) if x != y and not (x.startswith('FUNC') and y.startswith('FUNC')) and not (x.startswith('ENDFUNC') and y.startswith('ENDFUNC'))
            and not re.match(r'^0x[0-9a-f]+:$', x) and not re.match(r'^(IFNZ|IFZ|JUMP) 0x', x)]
    assert len(a) == len(b) and len(diff) == 1 and all(x.startswith('S_PUSH') for x in diff[0]), ('KR_RateText differs beyond one label', diff[:3])
    label = (ko(json.loads(diff[0][0].split(' ', 1)[1])), ko(json.loads(diff[0][1].split(' ', 1)[1])))
    assert 'PUSH 1043' in a and sum(1 for x in a if x == 'CALLFUNC KR_PlayerEventCount') == 4
    groups = panel_groups(vm)
    pset = {n for v in groups.values() for n in v}
    assert len(pset) == sum(len(v) for v in groups.values()) == 1043, len(pset)
    cal = {e['fn']: no for no, e in X['ev'].items()}
    assert pset <= set(cal), 'the panel counts events the calendar does not have'
    extra = sorted(no for fn, no in cal.items() if fn not in pset)
    where = {}
    for c in X['cards']:
        for s in c['stages']:
            where[s] = '%d월 · %s 카드' % (c['month'], LANE_KR[c['lane']])
    for ch in X['chips']:
        for s in ch['scenes']:
            where[s] = ('회상 재생본' if ch['lane'] < 16 else '게임에서 부르지 않는 장면') if ch['month'] == 12 else ('%d월 · %s 서랍(%s)' % (ch['month'], LANE_KR[ch['lane']], KINDS[ch['kind']]))
    breakdown = collections.Counter(where[no] if X['ev'][no]['cat'] in ('memory_replay', 'unknown') else 'other' for no in extra)
    others = [dict(event='E%05d' % no, place=where[no], category=X['ev'][no]['cat']) for no in extra
              if X['ev'][no]['cat'] not in ('memory_replay', 'unknown')]
    rows = []
    for name, regs in states:
        vm.registered = regs
        pk = sum(vm.run('KR_PlayerEventCount', [g]) for g in range(4))
        vm.reset()
        vm.script = [0]
        vm.run('KR_T16SummaryPage')
        head = ko(vm.dialogs[0]['title']).split('\n')[0]
        ck, cn = map(int, re.search(r'(\d+)/(\d+)', head).groups())
        extra_seen = sum(1 for no in extra if X['ev'][no]['fn'] in regs)
        assert cn == 1043 + len(extra) == TOTAL_EVENTS and ck == pk + extra_seen, (name, ck, pk, extra_seen)
        rows.append(dict(state=name, panel='%d/1043' % pk, calendar='%d/%d' % (ck, cn), calendar_only_seen=extra_seen))
    counts['V13_panel_states'] = len(rows)
    return dict(same_computation_as_KR_T8HomeRateText=True, only_difference_label=label, panel_denominator=1043,
                panel_events=len(pset), calendar_events=len(cal), calendar_only=len(extra), calendar_only_breakdown=dict(breakdown),
                calendar_only_others=others, states=rows)


def real_save_checks(vm, X, counts):
    """V14: month pages of the real save states the probe logged (증거/probe_regs.json)."""
    path = L.EVID / 'probe_regs.json'
    assert path.exists(), 'run probe_calendar_r16.py --regs first (real save states)'
    doc = L.readj(path)
    man = L.readj(O / 'manifest.json')
    rows = []
    for r in doc['saves']:
        if not r.get('state'):
            continue
        assert r['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256'], 'regs logged by another candidate'
        st = r['state']
        byno = {e: X['ev'][e]['fn'] for e in st['regs']}
        regs = set(byno.values())
        today = tuple(st['today'])
        months = {}
        for mo in range(4, 12):
            shown, _ = month_page_check(vm, X, mo, counts, regs, today)
            months[mo] = ''.join(sorted(k for k in shown if k != '　'))
        now = st['now']
        full = [mo for mo, s in months.items() if all(ch in s for ch in '▲●○★')]
        rows.append(dict(save=r['save'], today='%d/%d' % today, now=now, registered=len(regs), marks_by_month=months,
                         months_with_all_four=full, current_month_has_all_four=now in full))
        counts['V14_saves'] += 1
    assert rows, 'no real save state'
    good = [x for x in rows if x['current_month_has_all_four']]
    assert good, ('no save shows ▲ ● ○ ★ together on its own month page', [(x['save'], x['today'], x['marks_by_month'].get(x['now'])) for x in rows])
    mid = [x for x in good if 8 <= int(x['today'].split('/')[1]) <= 23] or good
    pick = sorted(mid, key=lambda x: x['save'])[-1]
    L.writej(L.WORK / 'probe_pick.json', dict(save=pick['save'], today=pick['today'], month=pick['now'],
                                              why='newest save whose own month page shows ▲ ● ○ ★ together (VM on its real registrations)'))
    counts['V14_saves_with_all_four'] = len(good)
    return dict(saves=rows, pick=pick['save'])


# ============================================================== native comparison (--native)
def native_checks(vm, X, counts):
    res = L.readj(L.EVID / 'probe_result.json')
    man = L.readj(O / 'manifest.json')
    assert res['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256']
    st = res['state']
    regs = {X['ev'][e]['fn'] for e in st['regs']}
    today = tuple(st['today'])
    blocks = {}
    log = res['log']
    i = 0
    while i < len(log):
        z = re.match(r'TITLE (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            blocks[z.group(1)] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    vm.registered = regs
    vm.today = today
    out = {}
    for tag, text in blocks.items():
        parts = tag.split()
        vm.reset()
        vm.script = [0]
        if parts[0] == 'MONTH':
            vm.run('KR_T9MonthPage', [int(parts[1])])
        elif parts[0] == 'SUMMARY':
            vm.run('KR_T16SummaryPage')
        elif parts[0] == 'LANE':
            mo, lane = int(parts[1]), int(parts[2])
            page = int(parts[3][1:]) - 1 if len(parts) > 3 else 0
            vm.script = [12] * page + [0]
            vm.run('KR_T9LanePage', [mo, lane])
        want = ko(vm.dialogs[-1 if parts[0] != 'LANE' else page]['title'])
        assert text == want, ('native title differs from the VM', tag, [(a, b) for a, b in zip(text.split('\n'), want.split('\n')) if a != b][:2])
        out[tag] = 'identical'
        if parts[0] == 'MONTH':
            out[tag + ' marks'] = ''.join(sorted(set(m for _, m in calendar_cells(text).values()) - {'　'}))
    counts['N_titles_identical'] = len(out)
    # the home panel for the same save (KR_T8 calculation, the canonical one): k/1043 and its floor-to-0.1 percent
    extra = [no for no, e in X['ev'].items() if e['fn'] not in {n for v in panel_groups(vm).values() for n in v}]
    pk = sum(vm.run('KR_PlayerEventCount', [g]) for g in range(4))
    ck = sum(1 for e in X['ev'].values() if e['fn'] in regs)
    out['panel_same_save'] = dict(panel='%d/1043 = %d.%d%% (KR_T8Pct floors)' % (pk, (pk * 1000 // 1043) // 10, (pk * 1000 // 1043) % 10),
                                  calendar='%d/%d %s (rounded)' % (ck, TOTAL_EVENTS, pct1(ck, TOTAL_EVENTS)),
                                  calendar_only_seen=sum(1 for no in extra if X['ev'][no]['fn'] in regs))
    assert ck == pk + out['panel_same_save']['calendar_only_seen']
    out['save'] = res['save']
    out['today'] = '%d/%d' % today
    return out


# ============================================================== defects to plant (each must make its check fail)
def op_replace(fn, pred, new, nth=0):
    def mut(ops):
        hits = [i for i, o in enumerate(ops) if pred(o)]
        if len(hits) <= nth:
            raise RuntimeError(('defect could not be planted: no op to mutate', fn, len(hits)))
        ops[hits[nth]] = new(ops[hits[nth]])
        return ops
    return {fn: mut}


def seq_replace(fn, pattern, at, new, nth=0):
    """Replace op pattern[at] of the nth place where the op sequence `pattern` occurs."""
    def mut(ops):
        hits = [i for i in range(len(ops) - len(pattern) + 1) if all(ops[i + j] == list(pattern[j]) for j in range(len(pattern)))]
        if len(hits) <= nth:
            raise RuntimeError(('defect could not be planted: no op sequence', fn, pattern))
        ops[hits[nth] + at] = list(new)
        return ops
    return {fn: mut}


def sp(text):
    return 'S_PUSH', json.dumps(text, ensure_ascii=False)


def s_is(o, text):
    return o[0] == 'S_PUSH' and json.loads(o[1]) == text


DEFECTS = [
    # r15's nine (V4 now plants into KR_T16MonthPage, where the month navigation lives since r16)
    ('V2 width: legend 40 chars', 'pages', op_replace('KR_T9Legend', lambda o: o[0] == 'S_PUSH', lambda o: list(sp(proxy('가' * 40))))),
    ('V2 height: 12 rows a lane page', 'pages', op_replace('KR_T9LanePage', lambda o: o == ['.LOCALASSIGN', 'per 8'], lambda o: ['.LOCALASSIGN', 'per 12'])),
    ('V3 colour: unseen days white', 'calendar', op_replace('KR_T9ColorMark', lambda o: s_is(o, '‡'), lambda o: list(sp('†')))),
    ('V4 navigation: next skips a month', 'nav', seq_replace('KR_T16MonthPage', [('.LOCALREF', 'm'), ('PUSH', '1'), ('ADD',), ('RETURN',)], 1, ('PUSH', '2'))),
    ('V5 unwind flag not written', 'flow', op_replace('KR_T9Request', lambda o: s_is(o, 'Unwind'), lambda o: list(sp('Unwound')))),
    ('V6 settings context lost', 'flow', op_replace('KR_T9HomeConfig', lambda o: s_is(o, 'C'), lambda o: list(sp('X')))),
    ('V7 play allowed without context', 'flow', op_replace('KR_T9CanPlay', lambda o: o == ['PUSH', '0'], lambda o: ['PUSH', '1'], nth=1)),
    ('V8 fail-safe removed', 'flow', op_replace('KR_T9HomeMenuRun', lambda o: s_is(o, 'Playing'), lambda o: list(sp('PlayingX')))),
    ('V10 seen: this save shown as other save', 'seen', op_replace('KR_T9State', lambda o: o == ['PUSH', '2'], lambda o: ['PUSH', '1'])),
    # r16's five VM defects
    ('V11 bar: one cell too many', 'pages', seq_replace('KR_T16Bar', [('.LOCALREF', 'i'), ('.LOCALREF', 'f'), ('LT',)], 2, ('LTE',))),
    ('V3 missed shown as upcoming', 'calendar', op_replace('KR_T16DayState', lambda o: o == ['PUSH', '3'], lambda o: ['PUSH', '1'])),
    ('V3 ★ missing (main-story day drawn ●)', 'calendar', op_replace('KR_T16DayMark', lambda o: s_is(o, '★'), lambda o: list(sp('●')))),
    ('V11 summary total mismatch (회상 · 그 밖 left out)', 'summary', op_replace('KR_T16SummaryTitle', lambda o: o == ['.LOCALREF', 'n12'], lambda o: ['PUSH', '0'], nth=0)),
    ('V12 one E-number tail removed', 'rows', None),
]


def table_defect(X):
    no = X['cards'][10]['entry']
    return ('V1 table: one card entry wrong', 'tables', op_replace('KR_T9CardEntry', lambda o: o == ['PUSH', str(no)], lambda o: ['PUSH', str(no + 1)]))


def tail_defect(vm):
    k = next(k for k in range(200) if vm.run('KR_T16CardTail', [k]))
    return seq_replace('KR_T16CardTail', [('PUSH', '1'), ('RETURN',)], 0, ('PUSH', '0')), k


def main():
    selftest = '--selftest' in sys.argv
    native = '--native' in sys.argv
    t0 = time.time()
    man = L.readj(O / 'manifest.json')
    base = L.WORK / 'base' / 'NightRemaster.ain'
    cand = O / 'NightRemaster.ain'
    assert L.sha(base) == L.BASE_AIN_SHA and L.sha(cand) == man['files']['NightRemaster.ain']['sha256']
    m = L.read_meta(L.WORK / 'base' / 'meta.json')
    nm = L.read_meta(W / 'candidate_meta.json')
    assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
    X = expectations()
    counts = collections.Counter()
    vm = VM(cand, nm)
    if native:
        out = native_checks(vm, X, counts)
        result = dict(schema='yoru-calendar-r16.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), titles=out, counts=dict(counts))
        L.writej(W / 'native_compare.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=1))
        print('NATIVE TITLES = VM')
        return
    frames = static_checks(base, cand, man, m, nm, counts)
    audit = L.audit(cand, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', L.runtime()[1] / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'] and audit['ain_sha256'] == L.sha(cand)
    counts['S5_active_functions'] = audit['active_functions']
    table_checks(vm, X, counts)
    regs = seen_checks(vm, X, counts)
    all_regs = {e['fn'] for e in X['ev'].values()}
    mid_regs, mid_today = synthetic_mid_month(X)
    for name, rg in [('none', set()), ('partial', regs), ('all', all_regs)]:
        vm.registered = rg
        vm.flags = set(e['m0'] for e in X['ev'].values() if e['m0'] is not None) if name == 'partial' else set()
        pages_all(vm, X, counts, name)
    vm.flags = set()
    vm.registered = regs
    event_pages(vm, X, counts)
    calendar_checks(vm, X, counts, [set(), regs, all_regs, mid_regs])
    shown, _ = month_page_check(vm, X, mid_today[0], counts, mid_regs, mid_today)
    assert all(ch in shown for ch in '▲●○★☆'), ('synthetic 8/15 state does not show every mark', dict(shown))
    counts['V3_synthetic_mid_month_marks'] = len([c for c in shown if c != '　'])
    nav_checks(vm, X, counts)
    flow_checks(vm, X, counts)
    row_checks(vm, X, counts)
    panel = panel_checks(vm, X, counts, [('none', set()), ('partial', regs), ('all', all_regs), ('mid-August', mid_regs)])
    real = real_save_checks(vm, X, counts)
    result = dict(schema='yoru-calendar-r16.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,
                  counts=dict(counts), vm_steps=vm.steps, widest_title=WIDEST['title'], widest_title_len=len(WIDEST['title']),
                  widest_item=WIDEST['item'], widest_item_len=len(WIDEST['item']), seconds=round(time.time() - t0, 1),
                  saves_checked=counts['S4_saves'], frames_checked=counts['S4_frames'], panel=panel, real_saves=real)
    print(json.dumps({k: v for k, v in result.items() if k not in ('real_saves',)}, ensure_ascii=False, indent=1))
    if selftest:
        planted = []
        groups = dict(pages=lambda v: pages_all(v, X, collections.Counter(), 'partial'),
                      calendar=lambda v: calendar_checks(v, X, collections.Counter(), [regs, mid_regs]),
                      nav=lambda v: nav_checks(v, X, collections.Counter()),
                      flow=lambda v: flow_checks(v, X, collections.Counter()),
                      seen=lambda v: seen_checks(v, X, collections.Counter()),
                      tables=lambda v: table_checks(v, X, collections.Counter()),
                      summary=lambda v: pages_all(v, X, collections.Counter(), 'partial'),
                      rows=lambda v: row_checks(v, X, collections.Counter()))
        tail_mut, tail_k = tail_defect(vm)
        for label, group, mutation in DEFECTS + [table_defect(X)]:
            if mutation is None:
                mutation = tail_mut
            v2 = VM(cand, nm, mutate=mutation)
            v2.registered = regs
            try:
                groups[group](v2)
                planted.append(dict(defect=label, caught=False))
            except (AssertionError, Stop) as ex:
                planted.append(dict(defect=label, caught=True, message=str(ex)[:200]))
            except RuntimeError as ex:
                planted.append(dict(defect=label, caught=False, message='not planted: ' + str(ex)[:160]))

        def flip_site(b):
            raw = bytearray(L.unpack(b))
            s = L.readj(L.R15 / 'candidate' / 'manifest.json')['same_length_sites'][4]
            raw[16 + s['site']:16 + s['site'] + 6] = bytes.fromhex(s['before'])
            return L.pack(bytes(raw), b[:8])

        def touch_return(b):
            raw = bytearray(L.unpack(b))
            fr = next(x for x in frames if x['live'])
            ad = m['functions'][fr['fid']]['address'] + fr['offset']
            raw[16 + ad] ^= 1
            return L.pack(bytes(raw), b[:8])

        def touch_msg(b):
            raw = bytearray(L.unpack(b))
            pos = raw.index(b'MSG1') + 12
            while struct.unpack_from('<I', raw, pos)[0] == 0:
                pos += 4
            raw[pos + 4] ^= 1
            return L.pack(bytes(raw), b[:8])

        def redefine_pinned(meta):
            i = L.fid_of(meta, 'KR_T9HomeCasual')
            meta['functions'][i]['address'] = meta['functions'][-1]['address'] + 64     # what an override would do
            return meta
        for label, kw, part in [('S2 one r15 swap site reverted', dict(mutate_bytes=flip_site), 'S2'),
                                ('S4 a saved return instruction changed', dict(mutate_bytes=touch_return), 'S4'),
                                ('S3 one MSG1 byte changed', dict(mutate_bytes=touch_msg), 'S3'),
                                ('S6 a pinned function redefined (KR_T9HomeCasual moved)', dict(mutate_meta=redefine_pinned), 'S6')]:
            try:
                static_checks(base, cand, man, m, nm, collections.Counter(), parts=(part,), **kw)
                planted.append(dict(defect=label, caught=False))
            except AssertionError as ex:
                planted.append(dict(defect=label, caught=True, message=str(ex)[:200]))
        result['planted_defects'] = planted
        print(json.dumps(planted, ensure_ascii=False, indent=1))
        assert len(planted) == 19, len(planted)
        assert all(p['caught'] for p in planted), [p['defect'] for p in planted if not p['caught']]
    L.writej(W / ('vm_verification_selftest.json' if selftest else 'vm_verification.json'), result)
    print('VERIFIED', round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
