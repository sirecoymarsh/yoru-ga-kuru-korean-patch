"""r24 shared helpers (Claude Opus 5.5, 2026-09-28) - a copy of r23_feeling/r23lib.py (the r15-r23 folders are evidence:
read only).

r24 = the r23 install (current.json FEELING_R23_INSTALLED_NATIVE_PASS: AIN b5ec7f01... = the r23 candidate, winmm.dll
a72b1b9d... = the mod-menu hook r2) + the chart touch-up (설계_v4 「r24 요구」): locked cells of the event flow chart show the r19
name and the opening condition (no thumbnail, grey; a click opens the detail page without 「이 장면 재생」), and two part buttons
「다시 가리기」 「전체 개방」 left of 「닫기」 write YoruKR_Chart.dat (0 / 1) and redraw the chart in place (tab and page kept).

Small helpers copied from the Codex / 09-24 Claude build modules (via r15-r23) so that nothing is imported from those folders.
Everything this project writes stays under r24_chart/ on P:.
Base snapshot: the base AIN = the r23 candidate, so the r23 candidate folder (AIN + work/build/candidate_meta.json +
candidate_raw_code.jam) is READ; after a rebase work/snapshot_base_r24.py makes r24's own copy (base_paths()).
"""
from pathlib import Path
import collections, hashlib, json, os, re, struct, subprocess, zlib

HERE = Path(__file__).resolve().parent                     # ...\ingame\r24_chart
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
BASE_AIN_SHA = 'b5ec7f01ce25704c505f9f5eabb3f2873ab9aa1fda0d2a1b10b95102346713d3'   # = the r23 candidate (installed 17:47 09-28)
BASE_PACT_SHA = 'd4de68c5d44ff5c80b9c41be21f86059d0ebca2717284f4ed8a7d43f6f029403'
BASE_EX_SHA = 'de2f9f8affe75a08bc38e577c25ac25b5816b9b1714adf3b3a7ac102db5589c6'
BASE_STATUS = 'FEELING_R23_INSTALLED_NATIVE_PASS'
BASE_MANIFEST_SHA = '81a30df971cee6bf4ef92ce7d6c4112aaf9761793f0d95a2d0da4157f4de3581'
BASE_CHART_SHA = 'cc645872b062e42e9d5ed103555bb173c7e6a5df5f24f3a113646bb72de208ea'   # Manual/chart html (r19 install; r20-r24 do not touch it)
BASE_WINMM_SHA = 'a72b1b9d386107bb6370f4ff3f0ff9bd857fbf6223e7d0b1f5399604cd64e199'   # the mod-menu hook r2 (installed 12:06 09-28; r23 / r24 do not touch it)
HOOK1_WINMM_SHA = 'a4dd91102fbea2e1a7992974e53d45ffbeec8e79dc9981c5cc7c5201a01ab053'  # the first mod-menu hook (05:57 09-28; the r2 install's source)
AUTHOR = 'Claude Opus 5.5 (claude-opus-5-5)'
R23 = HERE.parent / 'r23_feeling'                          # read only (evidence: its candidate = the base, installed 17:47 09-28)
R23_AIN_SHA = BASE_AIN_SHA
R23_JOURNAL = CODEX / 'evidence' / 'feeling_r23' / 'journal.json'
R22 = HERE.parent / 'r22_chart'                            # read only (evidence: installed 12:05 09-28, below r23)
R22_AIN_SHA = 'af1026bb5ea14a2ae3daf048f118d5b3f63728af54ca2c0852bdc8ae7e07bddd'
R22_JOURNAL = CODEX / 'evidence' / 'chart_r22' / 'journal.json'
HOOK_JOURNAL = CODEX / 'evidence' / 'mod_menu_r2_20260928' / 'journal.json'   # the hook r2 install (winmm a72b1b9d...)
HOOK1_JOURNAL = CODEX / 'evidence' / 'mod_menu_20260928' / 'journal.json'     # the first hook install (winmm a4dd9110...)
R21 = HERE.parent / 'r21_modmenu'                          # read only (evidence: installed 05:56 09-28, below r22)
R21_AIN_SHA = '3b9865a834db59afe8075564e41d6340317e2d7f52b512243d93b2e687b2ff34'
R21_JOURNAL = CODEX / 'evidence' / 'modmenu_r21' / 'journal.json'
# r15 (installed 02:32 09-27, still inside the base): its candidate is the byte reference for the pinned functions and the swaps
R15 = HERE.parent / 'r15_calendar'                         # read only (evidence)
R16 = HERE.parent / 'r16_calendar'                         # read only (evidence: never installed)
R17 = HERE.parent / 'r17_calendar'                         # read only (evidence: installed 07:24, restored 14:11)
R18 = HERE.parent / 'r18_calendar'                         # read only (evidence: installed 19:0x, below r19)
R19 = HERE.parent / 'r19_calendar'                         # read only (evidence: installed 21:44, below r20)
R20 = HERE.parent / 'r20_calendar'                         # read only (evidence: its candidate = the base, installed 03:02 09-28)
R20_AIN_SHA = '9dfac62ac240370f98362624f39e515a4b730fa463c46955ac26d5fdd6791108'
R19_AIN_SHA = '1d6081e94cbba5a1e33a12cfad2e542bfa7b689b89373f5386475675c53a1948'
R18_AIN_SHA = '1f60b6853151e6f62d8803b669da5ae92b285628e89c504c2b9ac90a74038888'
R20_JOURNAL = CODEX / 'evidence' / 'calendar_r20' / 'journal.json'
R19_JOURNAL = CODEX / 'evidence' / 'calendar_r19' / 'journal.json'
R15_AIN_SHA = 'd81ddd5ad383ef870f96eca0c4da763a6cf475445d71f029ffb1f2c692037963'
R16_AIN_SHA = '4056429f9e9999c8bec64ed244cf0393285529e74c6693b2768176cf8439b2fc'
R17_AIN_SHA = '4f31ae639338a7d686636d58b0a55d93b6913df39bdbf37260e4d4b1e5d11953'
R17_JOURNAL = CODEX / 'evidence' / 'calendar_r17' / 'journal.json'
PINNED = ['KR_T9HomeCasual', 'KR_T9HomeConfig', 'C_SceneHomebase@CheckGameSysButtons', 'C_SceneHomebase@Run', 'LSys3xScript::RunEvent']
SANDBOX = 'KR_T18RunSandboxed'                             # new in r18; pinned from r18 on (on saved stacks during a replay)
PINNED_ALL = PINNED + [SANDBOX]                            # r19-r24: all six keep index, address and every code byte
SWAP_OWNER, SWAP_OLD = 'KR_T9HomeCasual', 'LSys3xScript::RunEvent'   # r18's same-length operand (kept as r18 left it)

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


SAVECOPY = WORK / 'savecopy'                   # only the files that differ from the copies the r23 map points to
R23_SAVEMAP = R23 / 'work' / 'savecopy_manifest.json'   # read only (maps to r15, r16, r18, r19, r20, r21, r22 or r23 copies)


def save_manifest():
    return readj(WORK / 'savecopy_manifest.json')


def save_path(rel):
    """Path of the copy that holds save file `rel` (an r15-r23 copy when unchanged, else the r24 copy)."""
    return Path(save_manifest()['files'][rel]['path'])


def save_slots():
    """Every top-level NightR<n>.asd copy (the user's slots incl. the autosave) as {name: path}."""
    files = save_manifest()['files']
    return {rel: Path(v['path']) for rel, v in sorted(files.items()) if re.fullmatch(r'NightR\d+\.asd', rel)}


def resume_saves():
    """Every top-level .asd copy that is a resume image (RSM): numbered slots and the game's own temporary resume files
    (NightRMemoryMode.asd etc.), as {name: path}. The S4 frame check covers all of them."""
    files = save_manifest()['files']
    out = {}
    for rel, v in sorted(files.items()):
        if '/' in rel or not rel.endswith('.asd'):
            continue
        p = Path(v['path'])
        raw = p.read_bytes()
        if raw[:4] != b'GD\x01\x01':
            continue
        try:
            if zlib.decompressobj().decompress(raw[8:], 8).startswith(b'RSM\0'):
                out[rel] = p
        except zlib.error:
            pass
    return out


def base_paths():
    """The base AIN copy + its meta.json + raw code dump: r24's own snapshot (after a rebase), else the r23 candidate files
    (read only) when the r23 candidate is the base AIN. Nothing is ever written into the r15-r23 folders."""
    own = WORK / 'base'
    for ain, meta, raw in ((own / 'NightRemaster.ain', own / 'meta.json', own / 'raw_code.jam'),
                           (R23 / 'candidate' / 'NightRemaster.ain', R23 / 'work' / 'build' / 'candidate_meta.json',
                            R23 / 'work' / 'build' / 'candidate_raw_code.jam')):
        if ain.exists() and meta.exists() and raw.exists() and sha(ain) == BASE_AIN_SHA:
            return dict(ain=ain, meta=meta, raw=raw)
    raise AssertionError('no base snapshot with BASE_AIN_SHA: run work/snapshot_base_r24.py')
