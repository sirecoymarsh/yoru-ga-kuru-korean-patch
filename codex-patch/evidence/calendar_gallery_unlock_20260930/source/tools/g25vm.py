"""A small interpreter of the LIVE System4 code of one AIN, for the KR_G25 checks (Claude Opus 5.5 (claude-opus-5-5), 2026-09-30).

It executes the instructions alice decodes from the bytes (--raw-code --no-macros dump: addresses, no macros), so the same-length
edits are run exactly as the engine would see them. The world outside the code is a model:
  session variables (SystemService.SystemVariable_Get / _Set), the save folder disk (TextFile.ReadAll / WriteAll: the engine writes
  CP932 with CRLF, ReadAll returns what is on disk), chart parts (PartsEngine.IsExist), PassRegister handles (ExistText),
  MsgSkip read marks, arrays (Array.Free / PushBack / Empty), system.IsDebugMode (false: a release build),
  and three game functions stubbed by name: EX_IA2Int (the EX 回想 table), ■閲覧／シナリオ登録確認 (a set of registered event
  labels), SYS_AddPunct (the engine's path helper), KR_MNotice (records the notice text instead of opening a window).
Pure table functions (only compares / jumps / constant returns) are memoized per argument.
mutate = {fid: {address: 'OP operands'}} replaces single instructions (planted defects); pseudo-op VM_POP2 pops two values.
"""
from pathlib import Path
import re, struct, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import g25lib as G
L = G.L

FW_DIGITS = str.maketrans('0123456789-', '０１２３４５６７８９－')
PURE_OPS = {'PUSHLOCALPAGE', 'PUSH', 'S_PUSH', 'X_REF', 'EQUALE', 'LT', 'LTE', 'GT', 'GTE', 'NOTE', 'IFZ', 'IFNZ', 'JUMP', 'RETURN'}


def s32(x):
    x = int(x, 0)
    return x - (1 << 32) if x >= 1 << 31 else x


def fmt(f, v):
    """System4 string % one value: %d / %0Nd / %D (full-width digits) / %s."""
    def rep(z):
        spec = z[0]
        if spec == '%%':
            return '%'
        if spec.endswith('D'):
            return str(v).translate(FW_DIGITS)
        if spec.endswith('s'):
            return str(v)
        return ('%' + spec[1:]) % v
    return re.sub(r'%%|%0?\d*[dDs]', rep, f, count=1)


class Code:
    """The live instructions of one AIN, per function (FUNC / ENDFUNC nesting aware), plus names and STR0."""
    def __init__(self, ain, meta, raw_jam):
        self.ain = Path(ain)
        self.m = L.read_meta(meta)
        self.name = G.names_of(self.m)
        self.by_name = {}
        for i, n in enumerate(self.name):
            self.by_name.setdefault(n, i)
        self.ops = {}
        for ad, op, fid in G.live_instructions(self.m, raw_jam):
            self.ops.setdefault(fid, []).append((ad, op))
        raw = L.unpack(self.ain.read_bytes())
        self.rows = [L.decode(r) for r in L.strings(raw)[2]]
        self.libs = {lib['name']: {f['name']: f for f in lib['functions']} for lib in self.m['libraries']}

    def fid(self, name):
        return self.by_name[name]


class Stop(Exception):
    pass


class VM:
    CHART_ROOT = 2026092200

    def __init__(self, code, model, mutate=None):
        self.c = code
        self.model = model
        self.mutate = mutate or {}
        self.loaded = {}
        self.memo = {}
        self.pure = {}
        self.glob = {0x134: 0, 0x136: 0}          # N_ModeScene::DbgEnableAll, N_ModeSound::DbgEnableAll (false in release)
        self.calls = []
        self.steps = 0

    # ---- code
    def load(self, fid):
        if fid in self.loaded:
            return self.loaded[fid]
        ops = list(self.c.ops[fid])
        mut = self.mutate.get(fid, {})
        if mut:
            ops = [(ad, mut.get(ad, op)) for ad, op in ops]
            assert set(mut) <= {ad for ad, _ in ops}, ('mutation address not in the function', fid)
        index = {ad: i for i, (ad, _) in enumerate(ops)}
        parsed = [(op.split()[0], op.split()[1:]) for _, op in ops]
        self.loaded[fid] = (ops, index, parsed)
        self.pure[fid] = all(o in PURE_OPS for o, _ in parsed) and not mut
        return self.loaded[fid]

    def call(self, name, *args, this=None):
        return self.run(self.c.fid(name), list(args), this)

    def run(self, fid, args, this=None):
        f = self.c.m['functions'][fid]
        ops, index, parsed = self.load(fid)
        key = (fid, tuple(args))
        if self.pure[fid] and key in self.memo:
            return self.memo[key]
        vs = f['arguments'] + f['variables']
        loc = [('' if v['type'][0] == 12 else ([] if v['type'][0] == 79 else 0)) for v in vs]
        for i, a in enumerate(args):
            loc[i] = a
        st = []
        pc = 0
        last_ref = None
        n = 0
        while True:
            op, a = parsed[pc]
            pc += 1
            n += 1
            assert n < 3_000_000, ('runaway', self.c.name[fid])
            if op == 'PUSH':
                st.append(s32(a[0]))
            elif op == 'S_PUSH':
                st.append(self.c.rows[int(a[0], 0)])
            elif op == 'PUSHLOCALPAGE':
                st.append(loc)
            elif op == 'PUSHGLOBALPAGE':
                st.append(self.glob)
            elif op == 'PUSHSTRUCTPAGE':
                assert this is not None, ('PUSHSTRUCTPAGE outside a method', self.c.name[fid])
                st.append(this)
            elif op == 'X_REF':
                k = int(a[0], 0)
                i = st.pop()
                pg = st.pop()
                last_ref = (pg, i)
                st.extend(pg[i + j] for j in range(k))
            elif op == 'X_ASSIGN':
                k = int(a[0], 0)
                vals = st[-k:]
                del st[-k:]
                i = st.pop()
                pg = st.pop()
                if pg is self.glob:
                    assert i in self.glob, ('write to an unmodelled global', i)
                for j, v in enumerate(vals):
                    pg[i + j] = v
                st.extend(vals)
            elif op == 'S_ASSIGN':
                v = st.pop()
                i = st.pop()
                pg = st.pop()
                pg[i] = v
                st.append(v)
            elif op == 'X_DUP':
                st.extend(st[-int(a[0], 0):])
            elif op == 'X_MOV':
                x, y = int(a[0], 0), int(a[1], 0)
                w = st[-x:]
                st[-x:] = w[-y:] + w[:-y]
            elif op in ('DELETE', 'POP', 'SP_INC'):
                st.pop()
            elif op == 'VM_POP2':
                st.pop()
                st.pop()
            elif op == 'A_REF':
                pass
            elif op == 'INC':
                i = st.pop()
                pg = st.pop()
                pg[i] += 1
            elif op == 'X_A_SIZE':
                st.append(len(st.pop()))
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
                st.append(fmt(s, v))
            elif op in ('IFZ', 'IFNZ'):
                if bool(st.pop()) == (op == 'IFNZ'):
                    pc = index[int(a[0], 16)]
            elif op == 'JUMP':
                pc = index[int(a[0], 16)]
            elif op == 'CALLFUNC':
                cf = int(a[0], 16)
                g = self.c.m['functions'][cf]
                k = len(g['arguments'])
                for x in g['arguments']:
                    assert x['type'][0] in (10, 12, 47), ('a by-ref argument (not modelled)', self.c.name[cf])
                aa = st[-k:] if k else []
                if k:
                    del st[-k:]
                out = self.native(cf, aa)
                if g['return-type'][0] != 0:
                    st.append(out)
            elif op == 'CALLHLL':
                lib, method = a[0], a[1]
                h = self.c.libs[lib][method]
                k = len(h['arguments'])
                aa = st[-k:] if k else []
                if k:
                    del st[-k:]
                out = self.hll(lib, method, aa, last_ref)
                if h['return-type'] != 0:
                    st.append(out)
            elif op == 'CALLMETHOD':
                k = int(a[0], 0)
                aa = st[-k:] if k else []
                if k:
                    del st[-k:]
                cf = st.pop()
                obj = st.pop()
                out = self.run(cf, aa, this=obj)
                if self.c.m['functions'][cf]['return-type'][0] != 0:
                    st.append(out)
            elif op == 'RETURN':
                ret = f['return-type'][0] != 0
                assert len(st) == int(ret), ('stack at RETURN', self.c.name[fid], st)
                v = st[0] if ret else None
                if self.pure[fid]:
                    self.memo[key] = v
                return v
            else:
                raise AssertionError(('unmodelled op', op, a, self.c.name[fid]))

    # ---- the outside world
    def native(self, fid, aa):
        name = self.c.name[fid]
        mdl = self.model
        if name == 'EX_IA2Int':
            return mdl.ex_int(*aa)
        if name == '■閲覧／シナリオ登録確認':
            self.calls.append(('registered?', aa[0]))
            return int(aa[0] in mdl.labels)
        if name == 'SYS_AddPunct':
            return aa[0] if aa[0].endswith('\\') else aa[0] + '\\'
        if name == 'KR_MNotice':
            self.calls.append(('notice', aa[0]))
            return None
        if name in ('KR_CShow',):
            self.calls.append((name, list(aa)))
            return None
        return self.run(fid, aa)

    def hll(self, lib, method, aa, last_ref):
        mdl = self.model
        key = f'{lib}.{method}'
        if key == 'system.IsDebugMode':
            return 0
        if key == 'system.GetSaveFolderName':
            return mdl.save_dir
        if key == 'SystemService.SystemVariable_Get':
            return mdl.vars.get(aa[0], '')
        if key == 'SystemService.SystemVariable_Set':
            mdl.vars[aa[0]] = aa[1]
            self.calls.append(('set', aa[0], aa[1]))
            return None
        if key == 'TextFile.ReadAll':
            path = aa[0]
            mdl.reads.append(path)
            if path not in mdl.disk:
                return 0
            pg, i = last_ref
            pg[i] = mdl.disk[path]
            return 1
        if key == 'TextFile.WriteAll':
            path, text = aa
            mdl.writes.append((path, text))
            if mdl.fail_write:
                return 0
            mdl.disk[path] = text.replace('\r\n', '\n').replace('\n', '\r\n')
            return 1
        if key == 'PartsEngine.IsExist':
            return int(aa[0] in mdl.parts)
        if key == 'PassRegister.ExistText':
            mdl.cg_asked.append(aa[1])
            return int(aa[1] in mdl.passreg.get(aa[0], set()))
        if key == 'MsgSkip.GetFlag':
            return int(aa[0] in mdl.msgskip)
        if key == 'Array.Free':
            aa[0].clear()
            return None
        if key == 'Array.PushBack':
            aa[0].append(aa[1])
            return None
        if key == 'Array.Empty':
            return int(len(aa[0]) == 0)
        raise AssertionError(('unmodelled HLL', key))


class Model:
    """The world: EX tables, the save-folder disk, session variables, chart parts, read marks."""
    def __init__(self, tables, labels=(), cg_seen=(), msgskip=(), flag=None, chart='closed', save_dir='S:\\Saves\\SaveData_KR'):
        self.tables = tables
        self.labels = set(labels)
        self.passreg = {0: set(cg_seen)}
        self.msgskip = set(msgskip)
        self.save_dir = save_dir
        self.disk = {}
        self.vars = {}
        self.parts = set()
        self.reads = []
        self.writes = []
        self.cg_asked = []
        self.fail_write = False
        self.set_flag(flag)
        self.set_chart(chart)

    @property
    def flag_path(self):
        return self.save_dir + '\\' + 'YoruKR_Chart.dat'

    def set_flag(self, flag):
        """None = no file; 0 / 1 = the file as KR_MSetUnlock leaves it (CRLF on disk)."""
        if flag is None:
            self.disk.pop(self.flag_path, None)
        else:
            self.disk[self.flag_path] = 'YoruKR.Chart.1\r\n%d\r\n' % flag

    def set_chart(self, chart):
        """closed | open (session Open = 1 and the chart root part exists) | open_no_root (Open = 1, root not built yet)."""
        self.vars['YoruKR.C.Open'] = '' if chart == 'closed' else '1'
        self.parts.discard(VM.CHART_ROOT)
        if chart == 'open':
            self.parts.add(VM.CHART_ROOT)

    def ex_int(self, name, key, col, default, id_):
        z = re.fullmatch(r'回想\.ページ([０-９]+)', name)
        assert z and col == 'needEvNo' and id_ == 0, (name, col, id_)
        page = int(z[1].translate(str.maketrans('０１２３４５６７８９', '0123456789')))
        return self.tables['memory'].get((page, key), default)


# ---------------------------------------------------------------- EX tables (the live EX dump, read only)
EX_DUMP = Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r22_chart/work/ex_runtime.x')


def ex_tables():
    """回想 pages (page, id) -> needEvNo / playEvNo, CG閲覧 rows (thumb, cg ints), 音楽鑑賞 rows, from the EX dump of the live EX."""
    text = EX_DUMP.read_text('utf-8')
    mem = {}
    play = {}
    i = text.index('tree 回想 = {')
    j = text.index('\n};', i)
    page = None
    for line in text[i:j].splitlines():
        z = re.match(r'\s*ページ([０-９]+) = \(table\)', line)
        if z:
            page = int(z[1].translate(str.maketrans('０１２３４５６７８９', '0123456789')))
            continue
        z = re.match(r'\s*\{ (\d+), (\d+), (\d+) \},?$', line)
        if z and page:
            mem[(page, int(z[1]))] = int(z[2])
            play[(page, int(z[1]))] = int(z[3])
    cg = []
    i = text.index('tree CG閲覧 = {')
    j = text.index('\n};', i)
    for line in text[i:j].splitlines():
        z = re.match(r'\s*\{ "([^"]*)", "([^"]*)", (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+) \},?$', line)
        if z:
            ints = [int(z[k]) for k in range(3, 10)]
            cg.append(dict(txt=z[1], thumb=z[2], cgs=['CG%04d' % x for x in ints if x]))
    music = []
    i = text.index('table 音楽鑑賞 = {')
    j = text.index('\n};', i)
    for line in text[i:j].splitlines():
        z = re.match(r'\s*\{ (\d+), (\d+), "', line)
        if z:
            music.append(dict(no=int(z[1]), bgm=int(z[2])))
    return dict(memory=mem, play=play, cg=cg, music=music, source=str(EX_DUMP), source_sha256=L.sha(EX_DUMP))
