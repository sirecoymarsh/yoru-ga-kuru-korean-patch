"""KR_G25 gallery-unlock layer: shared constants and helpers (Claude Opus 5.5 (claude-opus-5-5), 2026-09-30).

The layer ties the menu-bar 「전체 개방」 flag (save folder YoruKR_Chart.dat, r21 KR_MUnlockAll / KR_MSetUnlock) to the game's own
galleries: 추억 감상 (recollection mode: N_ModeScene::CheckEnabelScenario) and CG 감상 (S_ModeCGCellInfo@UpdateEnableCG).
Music mode needs nothing (both of its checks are constant true in this build).

The r24 library (P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart/r24lib.py) is imported READ ONLY for the
AIN / alice / proxy helpers; its WORK / TMP / EVID are re-pointed into this folder before anything runs, so alice temp files and
every output stay here.
"""
from pathlib import Path
import hashlib, json, re, struct, sys, bisect
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
F = Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')     # read-only reference library
if str(F) not in sys.path:
    sys.path.insert(0, str(F))
import r24lib as L

L.WORK = H / 'work'
L.TMP = H / 'work' / 'tmp'
L.EVID = H / 'evidence'
for _d in (L.WORK, L.TMP, L.EVID):
    _d.mkdir(parents=True, exist_ok=True)

R = L.CODEX
STAGING = R / 'staging'
AUTHOR = 'Claude Opus 5.5 (claude-opus-5-5)'
TOOL = 'calendar_gallery_unlock_20260930'
KEY = 'calendar_gallery_unlock_20260930'
STATUS_INSTALLED = 'CALENDAR_GALLERY_UNLOCK_20260930_INSTALLED_NATIVE_PASS'
PY = 'P:/AI/forge/venv/Scripts/python.exe'

# ---- the installed build this layer stands on (current.json, 09-30 00:1x install of the summary stack)
LIVE_STATUS = 'CALENDAR_SUMMARY_STACK_20260929_INSTALLED_NATIVE_PASS'
LIVE_AIN = 'abae5787031cbf8330a429a4b5d9683241268d87f077d88de24974465ff5c109'
LIVE_MANIFEST = '974b35edba6c1581cd67e46238ba19e6f9e189d8ca32f6597640c2430d9f73a7'
LIVE_WINMM = '0df1aa37edae29a9eb878e8043779b620ba0a3de5ee450cd872a5eac9c1e495e'
LIVE_PACT = 'd4de68c5d44ff5c80b9c41be21f86059d0ebca2717284f4ed8a7d43f6f029403'
LIVE_EX = 'de2f9f8affe75a08bc38e577c25ac25b5816b9b1714adf3b3a7ac102db5589c6'
LIVE_EXE = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
# the stack top that was installed (same AIN bytes): its meta dump and raw code dump are the base snapshot
STACK_TOP = STAGING / 'calendar_summary_layer_tools_20260929/layers/final_stack/15_TF29'
STACK_META_SHA = '4c9babefdb430c495b286575580cdf3c7731aeb2aa4bbb9e0ed38bf87da480a8'
STACK_RAW_SHA = '050094edb6fe606ebd209226d75d0a2bdc90ec22a8f61808d75c13dc6354a9d1'
R21_JAF = F.parent / 'r21_modmenu' / 'claude_modmenu_r21.jaf'        # read only: the readable KR_MSetUnlock source

# ---- names
SCENE_CHECK = 'N_ModeScene::CheckEnabelScenario'      # the recollection judgment (page, renban) -> bool
CG_UPDATE = 'S_ModeCGCellInfo@UpdateEnableCG'         # fills EnableCGList (member 4) from CGList (member 3)
CG_CHECK = 'Ａ＿ＣＧモード確認'                         # bool (string): PassRegister.ExistText(0, name)
CG_OPENED = 'S_ModeCGCellInfo@IsOpened'
SET_UNLOCK = 'KR_MSetUnlock'                          # r21: writes YoruKR_Chart.dat (the one writer of the flag)
UNLOCK_ALL = 'KR_MUnlockAll'                          # r21: reads it (the file, every call)
CHART_ACTIVE = 'KR_CActive'                           # r22: the event calendar (menu-bar chart) is open
CHART_GLOBAL = 'KR_CGlobal'                           # r22: the calendar's global read mark (calls SCENE_CHECK)
NOTICE_OWNER = 'KR_CDo'                               # r22: the menu request dispatch (the 전체 개방 notice)
SOUND_CHECKS = ['C_SceneModeSoundView@IsEnableSound', 'S_SoundModeCellInfo@IsEnable']
EXPECTED_FIDS = {SCENE_CHECK: 29755, CG_UPDATE: 29714, CG_CHECK: 6145, CG_OPENED: 29711, SET_UNLOCK: 0x7f65, UNLOCK_ALL: 0x7f64,
                 CHART_ACTIVE: 0x7f8a, CHART_GLOBAL: 0x7f8b, NOTICE_OWNER: 32693}
NEW = ['KR_G25All', 'KR_G25Exist', 'KR_G25SceneBase', 'KR_G25SetUnlockBase', 'KR_G25SetUnlock', 'KR_G25NoteText']
CACHE_VAR = 'YoruKR.G25.All'
OLD_NOTE = '〓모드 메뉴\n†전체 개방: 안 본 이벤트도 열람·재생됩니다'
NEW_NOTE = '〓모드 메뉴\n†전체 개방: 안 본 이벤트·회상·CG도 열람·재생됩니다'

# ---- opcodes (read from the installed code at the patch sites, re-asserted by the build)
OP = dict(PUSH=0x00, POP=0x01, PUSHGLOBALPAGE=0x04, CALLFUNC=0x30, S_PUSH=0x41, CALLHLL=0x5a, X_REF=0x10c)


def ins(op, *operands):
    return struct.pack('<H', OP[op]) + b''.join(struct.pack('<i', x) for x in operands)


def sha(p):
    return L.sha(p)


def readj(p):
    return L.readj(p)


def writej(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def assert_inside(p):
    """Every output of this layer stays inside this folder (never the runtime, current.json, contracts or other agents)."""
    p = Path(p).resolve()
    assert p.is_relative_to(H.resolve()), ('write outside the layer folder', str(p))
    return p


def runtime_now():
    cur = L.readj(L.CURRENT)
    rt = Path(cur['runtime'])
    got = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'winmm.dll', 'NightRemasterPact.afa', 'NightRemasterEX.ex', 'NightRemaster.exe']}
    return cur, rt, got


def assert_live():
    """The installed build is still the one this layer was designed on (re-baseline if not)."""
    cur, rt, got = runtime_now()
    assert cur['status'] == LIVE_STATUS and cur['manifest_sha256'] == LIVE_MANIFEST, ('current.json moved', cur['status'], cur['manifest_sha256'])
    assert L.sha(Path(cur['manifest'])) == LIVE_MANIFEST, 'manifest file differs from current.json'
    assert got == {'NightRemaster.ain': LIVE_AIN, 'winmm.dll': LIVE_WINMM, 'NightRemasterPact.afa': LIVE_PACT,
                   'NightRemasterEX.ex': LIVE_EX, 'NightRemaster.exe': LIVE_EXE}, ('runtime files moved', got)
    return cur, rt, got


def code_of(ain_bytes):
    raw = L.unpack(ain_bytes)
    n = struct.unpack_from('<I', raw, 12)[0]
    return raw, raw[16:16 + n], n


def fid(m, name):
    return L.fid_of(m, name)


def names_of(m):
    return [L.raw_symbol(m, f['index']) for f in m['functions']]


def live_ops(m, vers, name_or_fid):
    """[(address, 'OP operands')] of the live body of a function (raw dump, no macros), up to its ENDFUNC."""
    i = name_or_fid if isinstance(name_or_fid, int) else L.fid_of(m, name_or_fid)
    v = L.live_version(m, vers, i)
    out = []
    for ad, op in v['ops']:
        if op.startswith('ENDFUNC'):
            break
        out.append((ad, op))
    return out


def live_instructions(m, raw_path):
    """Every instruction of the LIVE code as (address, 'OP operands', owner fid), from a --raw-code --no-macros dump.
    Ownership follows the FUNC / ENDFUNC nesting (a lambda body sits inside its enclosing function's code; the code after the
    lambda's ENDFUNC belongs to the enclosing function again). A FUNC block is live when its body start is the function's
    metadata address (relocated old bodies are dead code)."""
    out = []
    stack = []
    last = 0
    for line in Path(raw_path).read_text('utf8').splitlines():
        if line.startswith('FUNC '):
            n = int(line.split()[1])
            live = n < len(m['functions']) and m['functions'][n]['address'] == last + 6
            stack.append((n, live))
            continue
        z = re.match(r'0x([0-9A-Fa-f]+):\s*(.*)', line)
        if not z:
            continue
        last = int(z[1], 16)
        op = z[2].strip()
        if not op:
            continue
        if op.startswith('ENDFUNC'):
            if stack:
                stack.pop()
            continue
        if op.startswith('EOF'):
            continue
        if stack and stack[-1][1]:
            out.append((last, op, stack[-1][0]))
    return out


def body_ranges(m, vers, code_len):
    """Start of every FUNC body in the raw dump (for the byte extent of a function)."""
    return sorted({v['start'] for vs in vers.values() for v in vs})


def body_bytes(code, starts, address):
    i = bisect.bisect_right(starts, address)
    end = starts[i] - 6 if i < len(starts) else len(code)
    return code[address:end]


def jam_ops(text):
    """Instruction lines of an `ain dump --function` file: (label or None, op, operand-text)."""
    out = []
    for line in text.splitlines():
        if not line or line.startswith(';') or line.startswith('FUNC ') or line.startswith('ENDFUNC ') or line.startswith('EOF'):
            continue
        z = re.match(r'^(0x[0-9A-Fa-f]+):$', line)
        if z:
            out.append((z[1].lower(), None, None))
            continue
        s = line.strip()
        op, _, rest = s.partition(' ')
        out.append((None, op, rest))
    return out


def normalized_body(text):
    """Op sequence with jump labels renamed by first appearance (a clone at another address compares equal)."""
    labels = {}

    def lab(x):
        x = x.lower()
        if x not in labels:
            labels[x] = f'L{len(labels)}'
        return labels[x]
    out = []
    for label, op, rest in jam_ops(text):
        if label:
            out.append(lab(label) + ':')
        else:
            out.append(op + ' ' + re.sub(r'0x[0-9A-Fa-f]+', lambda z: lab(z[0]), rest))
    return out


JAF_TYPES = {10: 'int', 11: 'float', 12: 'string', 47: 'bool'}
JAF_DEFAULT = {'int': '0', 'float': '0.0', 'string': '""', 'bool': 'false'}


def jaf_type(t):
    assert t[0] in JAF_TYPES and t[1] == -1 and t[2] == 0, ('unsupported type in a cloned signature', t)
    return JAF_TYPES[t[0]]


def stub(name, f):
    """A JAF declaration with the same arguments, locals (in order, same names) and return type as metadata entry f; the body is
    replaced by the byte clone afterwards."""
    args = ', '.join(f'{jaf_type(a["type"])} {L.fix_name(a["name"])}' for a in f['arguments'])
    ret = jaf_type(f['return-type'])
    lines = [f'{ret} {name}({args}) {{']
    for v in f['variables']:
        t = jaf_type(v['type'])
        lines.append(f'    {t} {L.fix_name(v["name"])} = {JAF_DEFAULT[t]};')
    lines.append(f'    return {JAF_DEFAULT[ret]};')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def jaf_function(text, name):
    """The full text of `<type> name(...) { ... }` in a JAF source (brace matched)."""
    start = re.search(r'^(?:void|int|string|bool) ' + re.escape(name) + r'\(', text, re.M).start()
    pos = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[pos] == '{') - (text[pos] == '}')
        pos += 1
    return text[start:pos]


def lowered(p, name):
    """An `ain dump --function` jam made re-assemblable (the build line of the earlier layers)."""
    jam = L.native_lower(Path(p).read_text('utf-8'))
    jam = re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',
                 lambda z: '\t.LOCALASSIGN ' + z[1] + ' ' + str(struct.unpack('<i', struct.pack('<f', float(z[2])))[0]), jam)
    return L.clean(jam.replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), name)


def str_index(rows, text):
    """Index of the one STR0 row that decodes to `text` (proxy carriers)."""
    enc = L.encode(text)
    hits = [i for i, r in enumerate(rows) if r == enc]
    assert len(hits) == 1, (text[:20], hits)
    return hits[0]


def title_width(text):
    """Full-width units of the longest line (ASCII = 0.5; the †‡¶〓 marks are colour switches the dialog does not draw)."""
    best = 0
    for line in text.split('\n'):
        line = line.lstrip('†‡¶〓')
        best = max(best, sum(0.5 if ord(c) < 0x80 else 1 for c in line))
    return best


def save_frames(names=None):
    """Every frame (IP + return records) of every resume image in the user's save folder (read only): numbered slots and the
    game's own temporary resume files."""
    out = []
    for path in sorted(L.SAVES.glob('*.asd')):
        raw = path.read_bytes()
        if raw[:4] != b'GD\x01\x01':
            continue
        try:
            rec = L.save_records(path)
        except Exception as e:                      # not a resume image (global record) or unreadable: listed, not used
            out.append(dict(save=path.name, error=repr(e)[:120]))
            continue
        if rec is None:
            continue
        for fr in [rec['ip']] + rec['returns']:
            if fr['address'] < 0:
                continue
            out.append(dict(save=path.name, **fr))
    return out
