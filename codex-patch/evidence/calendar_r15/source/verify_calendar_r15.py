"""Claude Opus 5.5 (2026-09-27) r15: verification of the calendar candidate without the game.

  python verify_calendar_r15.py              all checks (must pass)
  python verify_calendar_r15.py --selftest   all checks, then every check again against a planted defect (each must fail)

Static (bytes of base vs candidate, read only):
  S1 candidate = manifest; every original function entry identical; non-function metadata identical
  S2 old CODE differs only at the nine swapped CALLFUNC operands; each site's before/after bytes and signatures
  S3 MSG1 identical, STR0 prefix identical; PACT/EX not in the payload
  S4 user saves (COPIES in work/savecopy): every saved frame (ip + returns) resolves to the same function entry and the
     same instruction bytes at its return address in the candidate
  S5 native opcode audit of the candidate against the runtime exe dispatch table
Extended VM (the candidate's own compiled bodies, engine calls modelled; the 09-24 VM design):
  V1 baked tables read back through the VM = chart v2 data re-derived here (cards, stages, drawers, scenes, first
     messages, event names built by the engine's own GetLabelName/_AdjustOriginalName)
  V2 every page in three save states (none / partial / all seen): title lines <= 38 raw characters (colour marks
     counted), dialog height 64 + 34*lines + 48*rows <= 704 px, item texts within their column, no colour marks in
     items, r11 opt-in (YoruKR.T8.Title / Color) set for the draw
  V3 month-page calendar: every day cell's colour and mark (blue ● unseen card, grey ○ all seen, white none, grey out of
     range, gold today) for several "today" dates
  V4 month navigation 4 -> 11 -> 회상 · 그 밖 -> back
  V5 play from the r13 character window (context P): request -> every window closes -> home menu returns 3 without a
     dialog -> casual site replays through LSys3xScript::Prepare(name) + RunEvent + ■ＡＤＶ消し(true, 0) -> next menu normal
  V6 play from 플레이 정보 inside the home-opened settings (context C): reserved, armed only after ▲コンフィグ実行 returns
  V7 no home context: play item locked, note shown, request ignored; a reservation whose settings never returned is dropped
  V8 fail-safe (a returned 3 that the casual site did not consume) and the casual button unchanged when nothing is queued
  V9 the patched r9/r13 menus keep their own items and dispatch (characters 2-8, 날짜별로 보기, 던전 파티별로 보기)
  V10 seen states: this save ○ (IsRegisteredEvent), other save △ (MsgSkip.GetFlag(first message)), none ●; events
     without messages never query MsgSkip; page counts equal an independent count
"""
import sys, json, re, struct, collections, math, copy, time, random, datetime, io, contextlib
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r15lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
MARKS = '†‡¶〓'
PICK = 2026092401
H_MAX = 704
COL_CAP = {1: 38, 2: 20, 3: 13}          # full-width units per item (1280 px screen, 28 px a glyph, 52 px item margin)
LANES = ['main', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'dungeon']
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
SLOT_RANK = {1: 0, 3: 1, 4: 2, 2: 3, 0: 9}


def proxy(s):
    return L.encode(s).decode('cp932')


def ko(s):
    return L.decode(s.encode('cp932'))


class Stop(Exception):
    pass


# ============================================================== VM
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
        # the engine's setters create g_MainSelect when it is -1 (■選択ダイアログ／タイトル設定: NEW C_SelectDialog)
        if self.cur is None:
            self.cur = dict(title=None, cols=1, items=[], type=None, limit=None)
        return self.cur

    def native(self, name, aa):
        if name == '■選択ダイアログ／初期化':
            self.cur = None                   # deletes g_MainSelect (= -1)
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
        data = V2.build(str(L.TMP / 'chart_v2_from_r15_verify.html'))
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


# ============================================================== static checks
def static_checks(base, cand, man, m, nm, counts, mutate_bytes=None, parts=('S1', 'S2', 'S3', 'S4')):
    bb = base.read_bytes()
    cb = cand.read_bytes()
    if mutate_bytes:
        cb = mutate_bytes(cb)
    assert L.sha_bytes(cb) == man['files']['NightRemaster.ain']['sha256'] or mutate_bytes, 'candidate != manifest'
    old = L.unpack(bb)
    new = L.unpack(cb)
    oldn = struct.unpack_from('<I', old, 12)[0]
    sites = man['same_length_sites']
    # S1 metadata
    if 'S1' in parts:
        assert [f for f in m['functions']] == nm['functions'][:len(m['functions'])], 'original function entries changed'
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        counts['S1_metadata'] += 1
    # S2 code: only the nine operands
    if 'S2' in parts:
        assert len(sites) == 9
        allowed = set()
        for s in sites:
            ad = s['site']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes.fromhex(s['before']), s
            assert bytes(new[16 + ad:16 + ad + 6]) == bytes.fromhex(s['after']), ('swap site not applied', s['function'], s['replacement'])
            of, nf = m['functions'][s['original_fid']], nm['functions'][s['replacement_fid']]
            assert ([a['type'] for a in of['arguments']], of['return-type']) == ([a['type'] for a in nf['arguments']], nf['return-type'])
            allowed |= set(range(ad + 2, ad + 6))
        diff = [i for i in range(oldn) if old[16 + i] != new[16 + i]]
        assert set(diff) <= allowed, [hex(x) for x in diff if x not in allowed][:8]
        counts['S2_code_sites'] += len(sites)
    # S3 text sections
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed']
        counts['S3_text'] += 1
    if 'S4' not in parts:
        return []
    # S4 saves (copies)
    vers = L.versions(L.WORK / 'base' / 'raw_code.jam')
    bycrc = collections.defaultdict(list)
    for f in m['functions']:
        bycrc[f['crc'] & 0xffffffff].append(f)
    frames = []
    live = 0
    for path in sorted(L.SAVECOPY.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd', path.name):
            continue
        row = L.save_records(path)
        assert row is not None, path.name
        for rr in [row['ip']] + row['returns']:
            if rr['address'] == -1:
                continue
            start = rr['address'] - rr['offset']
            choices = [f for f in bycrc[rr['crc']] if rr['name'].startswith(L.raw_symbol(m, f['index']) + '(')
                       and any(v['start'] == start for v in vers[f['index']])]
            assert len(choices) == 1, (path.name, rr)
            f = choices[0]
            assert nm['functions'][f['index']] == f
            ad = rr['address']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes(new[16 + ad:16 + ad + 6]), ('saved return bytes differ', path.name, rr['name'][:40], hex(ad))
            assert not any(s['site'] <= ad < s['site'] + 6 for s in sites), ('a saved frame returns into a swapped site', path.name)
            live += int(start == f['address'])
            frames.append(dict(file=path.name, fid=f['index'], offset=rr['offset'], live=start == f['address']))
    counts['S4_saves'] = len({x['file'] for x in frames})
    counts['S4_frames'] = len(frames)
    counts['S4_frames_in_live_versions'] = live
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


def units(t):
    """Glyph width in full-width units: ASCII (digits, spaces, /, parentheses) draws half width."""
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
        assert len(t) <= 38 and units(t) <= cap, ('item too wide for its column', d['cols'], units(t), t)
        assert not any(mk in t for mk in MARKS), ('colour mark in an item', t)
        widest = max(widest, units(t))
        if units(t) > units(WIDEST['item']):
            WIDEST['item'] = t
    width = max(d['cols'] * (widest * 28 + 52), max(len(x) for x in lines) * 28.5 + 48) + 4
    assert width <= 1280, ('dialog wider than the screen', width, lines[0])
    counts['V2_max_width_px'] = max(counts['V2_max_width_px'], int(width))
    assert d['type'] == 2026091602 and d['limit'] == 'all', 'dialog style'
    assert d['opt_color'] == '1' and d['opt_title'] == d['title'], 'r11 colour opt-in not set for the draw'
    counts['V2_dialogs'] += 1
    counts['V2_max_height'] = max(counts['V2_max_height'], h)
    counts['V2_max_title_lines'] = max(counts['V2_max_title_lines'], len(lines))


def pages_all(vm, X, counts, state_name):
    """Every page once (lane/drawer/stage/month-drawer pages through all their sub-pages)."""
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
                ds = walk('KR_T9LanePage', [mo, lane], math.ceil(n / per))
                assert sum(len(d['items']) - (3 if n > 10 else 1) for d in ds) == n, (mo, lane)
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
    counts['V2_states'] += 1


def event_pages(vm, X, counts):
    for no in sorted(X['ev']):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'C'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, proxy('6월 · 호시카와 · 특훈 뒤 대화')])
        check_dialog(vm.dialogs[0], counts)
    counts['V2_event_pages'] = len(X['ev'])


def calendar_cells(title):
    """(line segments with colours) -> {day: (colour, mark)} for the week lines of a month title."""
    rows = title.split('\n')[2:]
    out = {}
    for row in rows:
        color = 0
        chars = []
        for ch in row:
            if ch in MARKS:
                color = {'†': 1, '‡': 2, '¶': 3, '〓': 0}[ch]
                continue
            chars.append((ch, color))
        # cells of 4 full-width characters: two digits, mark, gap
        for i in range(0, len(chars), 4):
            cell = chars[i:i + 3]
            digits = ''.join(c for c, _ in cell[:2]).replace('　', '')
            if not digits:
                continue
            day = int(''.join(str('０１２３４５６７８９'.index(c)) for c in digits))
            out[day] = (cell[1][1], cell[2][0] if len(cell) > 2 else '　')
            assert cell[0][1] == cell[1][1], ('digits of one day in two colours', day)
    return out


def calendar_checks(vm, X, counts, regs_list):
    cards = X['cards']
    for regs in regs_list:
        for today in [(4, 9), (6, 13), (9, 30), (11, 17)]:
            vm.registered = regs
            vm.today = today
            for mo in range(4, 12):
                vm.reset()
                vm.script = [0]
                r = vm.run('KR_T9MonthPage', [mo])
                assert r == 0
                d = vm.dialogs[0]
                check_dialog(d, counts)
                cells = calendar_cells(ko(d['title']))
                assert sorted(cells) == list(range(1, X['mlen'][mo] + 1)), (mo, sorted(cells)[:5])
                for day, (col, mark) in cells.items():
                    on = [c for c in cards if c['month'] == mo and c['day'] == day]
                    inr = not ((mo == 4 and day < 9) or (mo == 11 and day > 17))
                    unseen = any(X['ev'][c['entry']]['fn'] not in regs for c in on)
                    want_mark = ('●' if unseen else '○') if (on and inr) else '　'
                    want_col = 3 if not inr else (2 if unseen and on else (3 if on else 1))
                    if (mo, day) == today:
                        want_col = 0
                    assert (col, mark) == (want_col, want_mark), (mo, day, (col, mark), (want_col, want_mark))
                counts['V3_cells'] += len(cells)
                # month menu: one row per lane with units, counts = independent count
                items = {iid: ko(t) for iid, t, _, _ in d['items']}
                for lane in range(9):
                    units = [c for c in cards if c['month'] == mo and c['lane'] == lane]
                    scenes = [s for ch in X['chips'] if ch['month'] == mo and ch['lane'] == lane for s in ch['scenes']]
                    n = len(units) + len(scenes)
                    k = sum(1 for c in units if X['ev'][c['entry']]['fn'] in regs) + sum(1 for s in scenes if X['ev'][s]['fn'] in regs)
                    if n:
                        assert items.get(20 + lane) == '%s %d (본 것 %d)' % (['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전'][lane], n, k), (mo, lane, items.get(20 + lane))
                    else:
                        assert 20 + lane not in items, (mo, lane)
                assert (11 in items) == (mo > 4) and 12 in items and 0 in items and 30 in items
                counts['V3_month_menus'] += 1


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
    """What C_SceneHomebase@RunHome builds before its ■選択ダイアログ／実行 (now KR_T9HomeMenuRun)."""
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
    # ---- V5 context P: home menu -> panel pick -> r13 window -> 달력으로 보기 -> lane -> card -> play
    vm.reset()
    vm.registered = set()
    pc = next(c for c in X['cards'] if 1 <= c['lane'] <= 7)          # first card in a person lane
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
    name = ['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전'][lane]
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
    # ---- V6 context C: settings from the home menu -> 플레이 정보 -> 캐릭터별 남은 이벤트 -> 이벤트 달력 -> 본편 -> card -> play
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
    # ---- V7 no home context: locked item + note, request ignored
    vm.reset()
    vm.script = [13]
    vm.run('KR_T9CardPage', [k, mo])
    d = vm.dialogs[0]
    assert d['items'][0][:2] == (13, proxy('이 장면 재생')) and d['items'][0][3] == 1, d['items'][0]
    assert '본거지에서 연 달력에서만 재생할 수 있습니다.' in ko(d['title'])
    assert vm.v('Play') == '' and vm.v('Req') == '' and vm.v('Unwind') == ''
    #      settings that never returned (a load inside the settings): the next home menu drops the reservation
    vm.reset()
    vm.vars.update({'YoruKR.T9.Ctx': 'C', 'YoruKR.T9.Req': '10001', 'YoruKR.T9.Unwind': '1'})
    vm.script = [11]
    assert home_run(vm) == 11 and vm.v('Req') == '' and vm.v('Unwind') == '' and vm.v('Play') == ''
    vm.calls = []
    vm.run('KR_T9HomeCasual')
    assert vm.calls == [('■カジュアルモード設定呼び出し', [])], vm.calls
    counts['V7_no_context'] += 1
    # ---- V8 fail-safe and plain casual button
    vm.reset()
    vm.vars.update({'YoruKR.T9.Play': '10001', 'YoruKR.T9.Playing': '1'})
    vm.script = [12]
    assert home_run(vm) == 12 and vm.v('Play') == '' and vm.v('Playing') == ''
    vm.calls = []
    vm.run('KR_T9HomeCasual')
    assert vm.calls == [('■カジュアルモード設定呼び出し', [])]
    counts['V8_failsafe'] += 1
    # ---- V9 the r9/r13 menus keep their own dispatch
    vm.reset()
    vm.script = [5, 0, 0]
    vm.run('KR_T8CharMissingMenu')
    assert len(vm.dialogs) == 3 and ko(vm.dialogs[1]['title']) == 'PLACE 5', [ko(d['title'])[:20] for d in vm.dialogs]
    vm.reset()
    vm.script = [1, 2, 0]
    vm.run('KR_T8CharMissingPage', [4])
    assert [c[0] for c in vm.calls] == ['KR_T8CharDatePage', 'KR_T8InfoPage'] and vm.calls[0][1] == [4], vm.calls
    counts['V9_original_dispatch'] += 1


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
    # partial save: page counts equal an independent count
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


# ============================================================== defects to plant (each must make its check fail)
def op_replace(fn, pred, new, nth=0):
    def mut(ops):
        hits = [i for i, o in enumerate(ops) if pred(o)]
        if len(hits) <= nth:
            raise RuntimeError(('defect could not be planted: no op to mutate', fn, len(hits)))
        ops[hits[nth]] = new(ops[hits[nth]])
        return ops
    return {fn: mut}


def sp(text):
    return 'S_PUSH', json.dumps(text, ensure_ascii=False)


DEFECTS = [
    ('V2 width: legend 40 chars', 'pages', op_replace('KR_T9Legend', lambda o: o[0] == 'S_PUSH', lambda o: list(sp(proxy('가' * 40))))),
    ('V2 height: 12 rows a lane page', 'pages', op_replace('KR_T9LanePage', lambda o: o == ['.LOCALASSIGN', 'per 8'], lambda o: ['.LOCALASSIGN', 'per 12'])),
    ('V3 colour: unseen days white', 'calendar', op_replace('KR_T9ColorMark', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == '‡', lambda o: list(sp('†')))),
    ('V4 navigation: next skips a month', 'nav', op_replace('KR_T9MonthPage', lambda o: o == ['PUSH', '1'], lambda o: ['PUSH', '2'], nth=3)),
    ('V5 unwind flag not written', 'flow', op_replace('KR_T9Request', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == 'Unwind', lambda o: list(sp('Unwound')))),
    ('V6 settings context lost', 'flow', op_replace('KR_T9HomeConfig', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == 'C', lambda o: list(sp('X')))),
    ('V7 play allowed without context', 'flow', op_replace('KR_T9CanPlay', lambda o: o == ['PUSH', '0'], lambda o: ['PUSH', '1'], nth=1)),
    ('V8 fail-safe removed', 'flow', op_replace('KR_T9HomeMenuRun', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == 'Playing', lambda o: list(sp('PlayingX')))),
    ('V10 seen: this save shown as other save', 'seen', op_replace('KR_T9State', lambda o: o == ['PUSH', '2'], lambda o: ['PUSH', '1'])),
]


def table_defect(X):
    no = X['cards'][10]['entry']
    return ('V1 table: one card entry wrong', 'tables', op_replace('KR_T9CardEntry', lambda o: o == ['PUSH', str(no)], lambda o: ['PUSH', str(no + 1)]))


def main():
    selftest = '--selftest' in sys.argv
    t0 = time.time()
    man = L.readj(O / 'manifest.json')
    base = L.WORK / 'base' / 'NightRemaster.ain'
    cand = O / 'NightRemaster.ain'
    assert L.sha(base) == L.BASE_AIN_SHA and L.sha(cand) == man['files']['NightRemaster.ain']['sha256']
    m = L.read_meta(L.WORK / 'base' / 'meta.json')
    nm = L.read_meta(W / 'candidate_meta.json')
    assert L.sha(W / 'candidate_meta.json') and len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
    X = expectations()
    counts = collections.Counter()
    frames = static_checks(base, cand, man, m, nm, counts)
    audit = L.audit(cand, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', L.runtime()[1] / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'] and audit['ain_sha256'] == L.sha(cand)
    counts['S5_active_functions'] = audit['active_functions']
    vm = VM(cand, nm)
    table_checks(vm, X, counts)
    regs = seen_checks(vm, X, counts)
    all_regs = {e['fn'] for e in X['ev'].values()}
    for name, rg in [('none', set()), ('partial', regs), ('all', all_regs)]:
        vm.registered = rg
        vm.flags = set(e['m0'] for e in X['ev'].values() if e['m0'] is not None) if name == 'partial' else set()
        pages_all(vm, X, counts, name)
    vm.registered = regs
    event_pages(vm, X, counts)
    calendar_checks(vm, X, counts, [set(), regs, all_regs])
    nav_checks(vm, X, counts)
    flow_checks(vm, X, counts)
    result = dict(schema='yoru-calendar-r15.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,
                  counts=dict(counts), vm_steps=vm.steps, widest_title=WIDEST['title'], widest_title_len=len(WIDEST['title']),
                  widest_item=WIDEST['item'], widest_item_len=len(WIDEST['item']), seconds=round(time.time() - t0, 1),
                  saves_checked=counts['S4_saves'], frames_checked=counts['S4_frames'])
    print(json.dumps(result, ensure_ascii=False, indent=1))
    if selftest:
        planted = []
        groups = dict(pages=lambda v: pages_all(v, X, collections.Counter(), 'all'),
                      calendar=lambda v: calendar_checks(v, X, collections.Counter(), [regs]),
                      nav=lambda v: nav_checks(v, X, collections.Counter()),
                      flow=lambda v: flow_checks(v, X, collections.Counter()),
                      seen=lambda v: seen_checks(v, X, collections.Counter()),
                      tables=lambda v: table_checks(v, X, collections.Counter()))
        for label, group, mutation in DEFECTS + [table_defect(X)]:
            v2 = VM(cand, nm, mutate=mutation)
            v2.registered = all_regs
            try:
                groups[group](v2)
                planted.append(dict(defect=label, caught=False))
            except (AssertionError, Stop) as ex:
                planted.append(dict(defect=label, caught=True, message=str(ex)[:160]))
        # static defects on a copy of the candidate bytes
        def flip_site(b):
            raw = bytearray(L.unpack(b))
            s = man['same_length_sites'][4]
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
            while struct.unpack_from('<I', raw, pos)[0] == 0:     # first non-empty message: flip its first data byte
                pos += 4
            raw[pos + 4] ^= 1
            return L.pack(bytes(raw), b[:8])
        for label, fn, part in [('S2 one swap site reverted', flip_site, 'S2'), ('S4 a saved return instruction changed', touch_return, 'S4'),
                                ('S3 one MSG1 byte changed', touch_msg, 'S3')]:
            try:
                static_checks(base, cand, man, m, nm, collections.Counter(), mutate_bytes=fn, parts=(part,))
                planted.append(dict(defect=label, caught=False))
            except AssertionError as ex:
                planted.append(dict(defect=label, caught=True, message=str(ex)[:160]))
        result['planted_defects'] = planted
        print(json.dumps(planted, ensure_ascii=False, indent=1))
        assert all(p['caught'] for p in planted), [p['defect'] for p in planted if not p['caught']]
    L.writej(W / ('vm_verification_selftest.json' if selftest else 'vm_verification.json'), result)
    print('VERIFIED', round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
