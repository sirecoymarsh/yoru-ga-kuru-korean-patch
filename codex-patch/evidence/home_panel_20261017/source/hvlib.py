"""Calendar / completion-rate redesign shared helpers (Claude Opus 5.5, 2026-10-17) - a copy of battle_pace_20261016/bplib.py
with the base moved to the battle-pace install (BATTLE_PACE_20261016_INSTALLED_NATIVE_PASS, 10-16 10:18).

Everything this project writes stays under ingame/calendar_redesign_20261017/ on P:. Nothing is ever written into the runtime, the save
folders or the Codex project.
"""
from pathlib import Path
import collections, hashlib, json, os, re, struct, subprocess, zlib

HERE = Path(__file__).resolve().parent                     # ...\ingame\calendar_redesign_20261017
FLOW = HERE.parent.parent                                  # ...\YoruGaKuru_flowchart_20260922
WORK = HERE / 'work'
TMP = HERE / 'tmp'
EVID = HERE / '증거'
CODEX = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')   # read only
CURRENT = CODEX / 'ui_cumulative' / 'current.json'
ALICE = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe')
PROXY = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4\wansung_build\build_output\fnl_proxy_map_wansung2350.json')
SAVES = Path(r'C:\Users\CadriacLord\OneDrive\문서\AliceSoft\밤이 온다! -Square of the MOON- Remastered\SaveData_KR_UI_Integrated_20260913')  # read only
BASE_AIN_SHA = 'd542fa37d53c5ea16fa014575572e4be64cc850d2c2af348948b09d1261a051c'   # battle-pace install (10-16 10:18)
BASE_PACT_SHA = 'f1a99eb3a37d6dd8a07c7ce1b1e1d2800974a773947447ef89d3e7e1714bdfac'
BASE_EX_SHA = 'de2f9f8affe75a08bc38e577c25ac25b5816b9b1714adf3b3a7ac102db5589c6'
BASE_WINMM_SHA = '0df1aa37edae29a9eb878e8043779b620ba0a3de5ee450cd872a5eac9c1e495e'
BASE_STATUS = 'BATTLE_PACE_20261016_INSTALLED_NATIVE_PASS'
BASE_MANIFEST_SHA = '0cfa5e0799c1f42a781680bee99a96b48b4d2caacb43177835c742fcfda4469d'
BASE_CHART_SHA = 'cc645872b062e42e9d5ed103555bb173c7e6a5df5f24f3a113646bb72de208ea'
AUTHOR = 'Claude Opus 5.5 (claude-opus-5-5)'
PREFIX = 'KR_HV'
# Functions that sit on saved resume stacks and were pinned by earlier layers: every code byte stays (r18-r23 rule).
PINNED = ['KR_T9HomeCasual', 'KR_T9HomeConfig', 'C_SceneHomebase@CheckGameSysButtons', 'C_SceneHomebase@Run', 'LSys3xScript::RunEvent']
SANDBOX = 'KR_T18RunSandboxed'
# auto-nav (10-15): on saved stacks when the player saves with a choice / the partner confirm / the new-game question open
AUTONAV_PINNED = ['KR_AN_E00058', 'KR_AN_E00063', 'KR_AN_E00069', 'KR_AN_E00104', 'KR_AN_E00258', 'KR_AN_E00260', 'KR_AN_E00322', 'KR_AN_E00611', 'KR_AN_E10021', 'KR_AN_E20041', 'KR_AN_E20081', 'KR_AN_E20164', 'KR_AN_E30001', 'KR_AN_E30021', 'KR_AN_E30152', 'KR_AN_E40021', 'KR_AN_E40041', 'KR_AN_E40043', 'KR_AN_E40061',
                  'KR_ANSelect', 'KR_ANSelFrame', 'KR_ANTrainConfirm', 'KR_ANOpeningQ', 'KR_ANNewGame']
PINNED_ALL = PINNED + [SANDBOX, 'KR_CReplayRun'] + AUTONAV_PINNED

for d in (WORK, TMP, EVID):
    d.mkdir(parents=True, exist_ok=True)


def env():
    """Child processes keep their temp files on P: (09-24 C: 0B incident, user rule 09-25)."""
    e = dict(os.environ)
    e['TEMP'] = e['TMP'] = str(TMP)
    e['PYTHONUTF8'] = '1'
    e['PYTHONDONTWRITEBYTECODE'] = '1'
    return e


# --- review_claude_handoff_20260923.sha / readj ---
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def readj(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def writej(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


# --- build_remaster_multiplier_20260915.cmd (timeout raised: whole-code dumps) ---
def cmd(*args, timeout=300):
    q = subprocess.run([str(ALICE), *map(str, args)], capture_output=True, timeout=timeout, env=env())
    if q.returncode != 0:
        err = q.stderr.decode('utf8', 'replace')
        err = '\n'.join(l for l in err.split('\n') if 'WARNING' not in l)
        raise AssertionError(('alice failed', [str(a) for a in args][:4], q.stdout.decode('utf8', 'replace')[-1500:], err[-3000:]))
    return q


# --- integrate_ui_opening_20260913.read_meta ---
def read_meta(p):
    return json.loads(Path(p).read_text(encoding='utf-8', errors='surrogateescape'), strict=False)


# --- build_route_perf_20260915.symbol (raw) / build_term_switch_20260923.symbol (with #n) ---
def raw_symbol(m, i):
    n = m['functions'][i]['name']
    return n.encode('utf8', 'surrogateescape').decode('cp932') if any(0xdc80 <= ord(c) <= 0xdcff for c in n) else n


def symbol(m, i):
    n = raw_symbol(m, i)
    prior = sum(f['name'] == m['functions'][i]['name'] for f in m['functions'][:i])
    return n + (f'#{prior}' if prior else '')


def fid_of(m, name):
    hits = [f['index'] for f in m['functions'] if raw_symbol(m, f['index']) == name]
    assert len(hits) == 1, (name, hits)
    return hits[0]


def gid_of(m, name):
    hits = [i for i, g in enumerate(m['globals']) if fix_name(g['name']) == name]
    assert len(hits) == 1, (name, hits)
    return hits[0]


def fix_name(n):
    return n.encode('utf8', 'surrogateescape').decode('cp932') if isinstance(n, str) and any(0xdc80 <= ord(c) <= 0xdcff for c in n) else n


# --- build_instant_loot_20260915.clean / begin ---
def clean(s, n):
    s = re.sub(r'^EOF .*\n?', '', s, flags=re.M)
    if 'ENDFUNC ' not in s:
        s += '\nENDFUNC ' + n + '\n'
    return s


def begin(s, x):
    return re.sub(r'(^FUNC \d+\n)', lambda m: m[0] + x, s, count=1, flags=re.M)


# --- build_dungeon_sweep_20260916.lr / push / cf ---
def lr(n):
    return f'\t.LOCALREF {n}\n'


def push(n):
    return f'\tPUSH {n}\n'


def cf(n):
    return f'\tCALLFUNC {n}\n'


# --- repair_ui_runtime_weapon_text_20260913.tag / unpack / pack / strings ---
def tag(p, t):
    assert p.count(t) == 1, (t, p.count(t))
    return p.index(t)


def unpack(data):
    assert data[:8] == b'AI2\0\0\0\0\0'
    size, csize = struct.unpack_from('<II', data, 8)
    assert len(data) == 16 + csize
    d = zlib.decompressobj()
    p = d.decompress(data[16:]) + d.flush()
    assert d.eof and not d.unused_data and not d.unconsumed_tail and len(p) == size
    return p


def pack(p, prefix):
    compressed = zlib.compress(p, 9)
    return prefix + struct.pack('<II', len(p), len(compressed)) + compressed


def strings(p):
    start = tag(p, b'STR0')
    count = struct.unpack_from('<I', p, start + 4)[0]
    pos = start + 8
    rows = []
    for _ in range(count):
        end = p.index(b'\0', pos)
        rows.append(p[pos:end])
        pos = end + 1
    assert p[pos:pos + 4] == b'DELG'
    return start, pos, rows


# --- polish_translation_20260917.raw_messages ---
def raw_messages(data):
    p = unpack(data)
    assert p.count(b'MSG1') == 1
    start = p.index(b'MSG1')
    count = struct.unpack_from('<I', p, start + 4)[0]
    pos = start + 12
    raw = []
    for _ in range(count):
        n = struct.unpack_from('<I', p, pos)[0]
        pos += 4
        raw.append(bytes((c - i - 0x60) & 255 for i, c in enumerate(p[pos:pos + n])))
        pos += n
    return p, start, pos, raw


# --- resume_compat_20260923.versions: every FUNC copy in a --raw-code dump, with its ops ---
def versions(path):
    out = collections.defaultdict(list)
    last = 0
    active = None
    for line in Path(path).read_text('utf8').splitlines():
        if line.startswith('FUNC '):
            fid = int(line.split()[1])
            active = dict(start=last + 6, ops=[])
            out[fid].append(active)
            continue
        z = re.match(r'0x([0-9A-Fa-f]+):\s*(.*)', line)
        if z:
            last = int(z[1], 16)
            if z[2] and active is not None:
                active['ops'].append((last, z[2]))
    return out


def live_version(m, vers, fid):
    start = m['functions'][fid]['address']
    return next(v for v in vers[fid] if v['start'] == start)


# --- audit_sys43_native_opcodes_20260915.native_lower / audit ---
def native_lower(jam):
    jam = re.sub(r'(?m)^\tF_PUSH ([-+0-9.eE]+)$', lambda m: '\tPUSH ' + str(struct.unpack('<i', struct.pack('<f', float(m[1])))[0]), jam)
    jam = re.sub(r'(?m)^\tSH_LOCALDELETE (\w+)\n\tSH_LOCALCREATE \1 ([^\n]+)$', lambda m: '\t.LOCALCREATE ' + m[1] + ' ' + m[2], jam)
    assert not re.search(r'(?m)^\t(?:F_PUSH|SH_LOCALCREATE|SH_LOCALDELETE)\b', jam)
    return jam


def audit(ain, meta, raw_jam, exe, ids=None):
    import pefile
    pe = pefile.PE(exe)
    base = pe.OPTIONAL_HEADER.ImageBase
    assert base == 0x400000
    assert pe.get_data(0x667f40 - base, 6) == bytes.fromhex('81 f9 10 01 00 00')
    assert pe.get_data(0x667f4c - base, 7) == bytes.fromhex('0f b6 81 dc 8a 66 00')
    assert pe.get_data(0x667f53 - base, 7) == bytes.fromhex('ff 24 85 20 89 66 00')
    table = pe.get_data(0x668adc - base, 0x111)
    targets = pe.get_data(0x668920 - base, 444)

    def target(op):
        return struct.unpack_from('<I', targets, table[op] * 4)[0] if op <= 0x110 else 0x66888d
    assert target(0) == 0x667f69 and all(target(op) == 0x66888d for op in [64, 129, 130])
    m = read_meta(meta)
    raw = unpack(Path(ain).read_bytes())
    code = raw[16:16 + struct.unpack_from('<I', raw, 12)[0]]
    last = None
    fid = None
    active = False
    unsupported = []
    seen = set()
    count = 0
    opnames = {}
    for line in Path(raw_jam).read_text(encoding='utf8').splitlines():
        if line.startswith('FUNC '):
            fid = int(line.split()[1])
            active = (ids is None or fid in ids) and last + 6 == m['functions'][fid]['address']
            if active:
                seen.add(fid)
            continue
        z = re.match(r'^0x([0-9A-Fa-f]+):\s*(\w+)?', line)
        if not z:
            continue
        addr = int(z[1], 16)
        last = addr
        if not active or z[2] in [None, 'FUNC', 'EOF', 'ENDFUNC']:
            continue
        op = struct.unpack_from('<H', code, addr)[0]
        count += 1
        opnames[str(op)] = z[2]
        if target(op) == 0x66888d:
            unsupported.append(dict(fid=fid, address=addr, opcode=op, name=z[2]))
    if ids is not None:
        assert seen == set(ids), (set(ids) - seen)
    else:
        concrete = {f['index'] for f in m['functions'] if f['address'] != 0xffffffff}
        assert seen == concrete, ('Uncovered executable metadata entries', sorted(concrete - seen))
    return dict(engine_sha256=sha(exe), ain_sha256=sha(ain), native_dispatch='0x667ef0/map0x668adc/table0x668920/default0x66888d',
                active_functions=len(seen), instruction_sites=count, opcodes=opnames, unsupported=unsupported,
                all_active_opcodes_supported=not unsupported)


# --- audit_dynamic_ui_20260915.encode / decode (FNL proxy carriers; same map as the 09-24 builds) ---
_MAP = None


def _proxy():
    global _MAP
    if _MAP is None:
        mapping = json.loads(PROXY.read_text(encoding='utf-8'))['mapping']
        enc = {r['unicode_character']: bytes.fromhex(r['proxy_sjis_hex']) for r in mapping}
        dec = {}
        for r in mapping:
            dec[bytes.fromhex(r['proxy_sjis_hex']).decode('cp932')] = r['unicode_character']
        _MAP = (enc, dec)
    return _MAP


def encode(t):
    enc, _ = _proxy()
    return b''.join(enc[c] if c in enc else c.encode('cp932') for c in t)


def decode(b):
    _, dec = _proxy()
    return ''.join(dec.get(c, c) for c in b.decode('cp932'))


def proxy_alphabet():
    enc, _ = _proxy()
    return set(enc)


def jaf_literal_encode(jaf):
    """Korean (and a few symbols) in string literals -> proxy carriers read as cp932 (09-24 build line 769)."""
    def rep(z):
        s = json.loads(z[0])
        if any('\uac00' <= c <= '\ud7a3' or c in '·…「」【】　' for c in s):
            return json.dumps(encode(s).decode('cp932'), ensure_ascii=False)
        return z[0]
    return re.sub(r'"(?:[^"\\]|\\.)*"', rep, jaf)


def strip_comments(src):
    """`//` and `/* */` comments out, string literals untouched (09-22 build_ingame.py)."""
    out = []
    i, n = 0, len(src)
    instr = False
    while i < n:
        c = src[i]
        if instr:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == '"':
                instr = False
            i += 1
            continue
        if c == '"':
            instr = True
            out.append(c)
            i += 1
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            j = src.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def runtime():
    ptr = readj(CURRENT)
    return ptr, Path(ptr['runtime'])


# --- resume_compat_20260923.Reader / records: RSM14 return records (read only; never rewrites saves) ---
class SaveReader:
    def __init__(self, data):
        self.data = data
        self.p = 0

    def integer(self):
        v = struct.unpack_from('<i', self.data, self.p)[0]
        self.p += 4
        return v

    def string(self):
        end = self.data.index(b'\0', self.p)
        v = self.data[self.p:end].decode('cp932')
        self.p = end + 1
        return v

    def array(self):
        n = self.integer()
        assert 0 <= n < 5000
        return [self.integer() for _ in range(n)]

    def record(self):
        address = self.integer()
        if address == -1:
            return dict(address=address)
        return dict(address=address, name=self.string(), offset=self.integer(), crc=self.integer() & 0xffffffff)


def save_records(path):
    raw = Path(path).read_bytes()
    assert raw[:4] == b'GD\x01\x01'
    data = zlib.decompress(raw[8:])
    assert len(data) == struct.unpack_from('<I', raw, 4)[0]
    if not data.startswith(b'RSM\0'):
        return None
    q = SaveReader(data)
    assert q.string() == 'RSM' and q.integer() == 14
    key = q.string()
    comments = [q.string() for _ in range(q.integer())]
    ip = q.record()
    stack = q.array()
    locals_ = q.array()
    types = q.array()
    structs = q.array()
    assert len(locals_) == len(types)
    n = q.integer()
    assert n in (len(locals_), len(locals_) - 1) and 0 < n < 200
    rr = [q.record() for _ in range(n)]
    assert rr[0]['address'] == -1
    return dict(file=Path(path).name, sha256=sha_bytes(raw), key=key, comments=comments, ip=ip, returns=rr)


def base_paths():
    """The base AIN snapshot (work/base: AIN copy + meta.json + raw code dump), made by snapshot_base.py."""
    own = WORK / 'base'
    ain, meta, raw = own / 'NightRemaster.ain', own / 'meta.json', own / 'raw_code.jam'
    if ain.exists() and meta.exists() and raw.exists() and sha(ain) == BASE_AIN_SHA:
        return dict(ain=ain, meta=meta, raw=raw)
    raise AssertionError('no base snapshot with BASE_AIN_SHA: run snapshot_base.py')


# --- r23 build_feeling_r23.region_ops (r20 build): live body ops incl. code after inline lambdas ---
def region_ops(raw_path, m, fid):
    """The live body of `fid` as ops, including code after inline lambdas and excluding the lambda bodies (r20 build)."""
    owner = raw_symbol(m, fid)
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
                nm = raw_symbol(m, k)
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
