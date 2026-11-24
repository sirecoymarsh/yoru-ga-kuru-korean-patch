"""r17 shared helpers (Claude Opus 5.5, 2026-09-27) — a copy of r16_calendar\\r16lib.py (r15 and r16 folders are evidence: read only).

Small helpers copied from the Codex / 09-24 Claude build modules (OneDrive `밤이 온다 한국어화`, read only) so that nothing
is imported from that folder (several of its modules mkdir/read relative to the working directory at import time).
Origin of each copy is noted. Everything this project writes stays under r17_calendar\\ on P:.
r17 base = the runtime current.json points to when the build runs (09-27 04:01: r15 + Codex rate_overlay + story_explore;
the same base as the uninstalled r16 candidate, which r17 replaces).
Base snapshot: when r16_calendar\\work\\base holds the base AIN (same hash) its AIN / meta / raw dump are READ from there;
otherwise work\\snapshot_base_r17.py makes r17's own copy (base_dir()).
Save copies: files unchanged since the r16 copy map are READ from where the r16 map points (r15 or r16 savecopy); only new or
changed files are copied into r17_calendar\\work\\savecopy (work\\savecopy_manifest.json maps every file to the copy that holds it).
"""
from pathlib import Path
import collections, hashlib, json, os, re, struct, subprocess, zlib

HERE = Path(__file__).resolve().parent                     # ...\ingame\r17_calendar
FLOW = HERE.parent.parent                                  # ...\YoruGaKuru_flowchart_20260922
WORK = HERE / 'work'
TMP = HERE / 'tmp'
EVID = HERE / '증거'
CODEX = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')   # read only
CURRENT = CODEX / 'ui_cumulative' / 'current.json'
ALICE = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe')
PROXY = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4\wansung_build\build_output\fnl_proxy_map_wansung2350.json')
CATALOG = CODEX / 'handoff_claude_terms_progress_20260923' / 'event_catalog.json'
ONEDRIVE = Path(r'C:\Users\CadriacLord\OneDrive\문서\ChatGPT\밤이 온다 한국어화')   # read only
SAVES = Path(r'C:\Users\CadriacLord\OneDrive\문서\AliceSoft\밤이 온다! -Square of the MOON- Remastered\SaveData_KR_UI_Integrated_20260913')  # read only
BASE_AIN_SHA = 'cbed62c2aa3bd33c8471a098cc1f6a3e7f83c60c32d02b2cbf2b0dd63bc24a9f'
BASE_PACT_SHA = 'd4de68c5d44ff5c80b9c41be21f86059d0ebca2717284f4ed8a7d43f6f029403'
BASE_EX_SHA = 'de2f9f8affe75a08bc38e577c25ac25b5816b9b1714adf3b3a7ac102db5589c6'
BASE_STATUS = 'STORY_EXPLORE_INSTALLED_NATIVE_PASS'
BASE_MANIFEST_SHA = '1f6caca554e07dc36838e6e2c36c4e88b7be96320dfe654d50811f721b1e6561'
AUTHOR = 'Claude Opus 5.5 (claude-opus-5-5)'
# r15 (installed 02:32, still inside the base): its candidate is the byte reference for the pinned functions and the swaps
R15 = HERE.parent / 'r15_calendar'                         # read only (evidence)
R16 = HERE.parent / 'r16_calendar'                         # read only (evidence: the uninstalled r16 candidate r17 replaces)
R16_AIN_SHA = '4056429f9e9999c8bec64ed244cf0393285529e74c6693b2768176cf8439b2fc'
R15_AIN_SHA = 'd81ddd5ad383ef870f96eca0c4da763a6cf475445d71f029ffb1f2c692037963'
PINNED = ['KR_T9HomeCasual', 'KR_T9HomeConfig', 'C_SceneHomebase@CheckGameSysButtons', 'C_SceneHomebase@Run', 'LSys3xScript::RunEvent']

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


SAVECOPY = WORK / 'savecopy'                   # only the files that differ from the copies the r16 map points to
R16_SAVEMAP = R16 / 'work' / 'savecopy_manifest.json'   # read only (maps to r15 or r16 copies)


def save_manifest():
    return readj(WORK / 'savecopy_manifest.json')


def save_path(rel):
    """Path of the copy that holds save file `rel` (an r15 / r16 copy when unchanged, else the r17 copy)."""
    return Path(save_manifest()['files'][rel]['path'])


def save_slots():
    """Every top-level NightR<n>.asd copy (the user's slots incl. the autosave) as {name: path}."""
    files = save_manifest()['files']
    return {rel: Path(v['path']) for rel, v in sorted(files.items()) if re.fullmatch(r'NightR\d+\.asd', rel)}


def base_dir():
    """Folder holding the base AIN copy + meta.json + raw_code.jam: r17's own snapshot, else r16's (read only) when its AIN
    is the base AIN. Nothing is ever written into the r16 folder."""
    for d in (WORK / 'base', R16 / 'work' / 'base'):
        a = d / 'NightRemaster.ain'
        if a.exists() and (d / 'meta.json').exists() and (d / 'raw_code.jam').exists() and sha(a) == BASE_AIN_SHA:
            return d
    raise AssertionError('no base snapshot with BASE_AIN_SHA: run work/snapshot_base_r17.py')
