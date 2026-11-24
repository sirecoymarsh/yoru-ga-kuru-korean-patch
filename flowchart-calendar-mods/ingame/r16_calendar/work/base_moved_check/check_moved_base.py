"""r16 pre-build gate follow-up (Claude Opus 5.5, 2026-09-27): the runtime moved after r15 was installed.

Read-only diagnosis, nothing is built. Answers: are r15's pinned functions (index, address, code bytes) and the nine
same-length swap sites still intact in the runtime Codex installed afterwards (rate_overlay 03:03, story_explore 04:01)?
Writes only inside this folder (runtime copy, alice dumps, result json). The r15 folder is only read.
"""
import bisect, collections, hashlib, json, os, re, shutil, struct, subprocess, sys, zlib
from pathlib import Path
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
TMP = HERE / 'tmp'
TMP.mkdir(exist_ok=True)
R15 = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar')
CURRENT = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\ui_cumulative\current.json')
ALICE = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe')
R15_AIN = 'd81ddd5ad383ef870f96eca0c4da763a6cf475445d71f029ffb1f2c692037963'
PINNED = ['KR_T9HomeCasual', 'KR_T9HomeConfig', 'C_SceneHomebase@CheckGameSysButtons', 'C_SceneHomebase@Run', 'LSys3xScript::RunEvent']


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def env():
    e = dict(os.environ)
    e['TEMP'] = e['TMP'] = str(TMP)
    return e


def alice(*args):
    q = subprocess.run([str(ALICE), *map(str, args)], capture_output=True, timeout=900, env=env())
    assert q.returncode == 0, q.stderr.decode('utf8', 'replace')[-2000:]


def unpack(data):
    assert data[:8] == b'AI2\0\0\0\0\0'
    size, csize = struct.unpack_from('<II', data, 8)
    p = zlib.decompress(data[16:16 + csize])
    assert len(p) == size
    return p


def meta(p):
    return json.loads(Path(p).read_text(encoding='utf-8', errors='surrogateescape'), strict=False)


def raw_symbol(m, i):
    n = m['functions'][i]['name']
    return n.encode('utf8', 'surrogateescape').decode('cp932') if any(0xdc80 <= ord(c) <= 0xdcff for c in n) else n


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


def main():
    ptr = json.loads(CURRENT.read_text(encoding='utf-8-sig'))
    rt = Path(ptr['runtime'])
    now = HERE / 'runtime_now.ain'
    h = sha(rt / 'NightRemaster.ain')
    if not now.exists() or sha(now) != h:
        shutil.copy2(rt / 'NightRemaster.ain', now)
    assert sha(now) == h
    if not (HERE / 'runtime_now_meta.json').exists():
        alice('ain', 'dump', '-j', '-o', HERE / 'runtime_now_meta.json', now)
    nm = meta(HERE / 'runtime_now_meta.json')
    r15_ain = R15 / 'candidate' / 'NightRemaster.ain'
    assert sha(r15_ain) == R15_AIN
    om = meta(R15 / 'work' / 'build' / 'candidate_meta.json')
    oman = json.loads((R15 / 'candidate' / 'manifest.json').read_text('utf8'))
    vers = versions(R15 / 'work' / 'build' / 'candidate_raw_code.jam')
    old = unpack(r15_ain.read_bytes())
    new = unpack(now.read_bytes())
    oc = old[16:16 + struct.unpack_from('<I', old, 12)[0]]
    nc = new[16:16 + struct.unpack_from('<I', new, 12)[0]]
    starts = sorted({v['start'] for vs in vers.values() for v in vs})
    byname_o = {raw_symbol(om, f['index']): f for f in om['functions']}
    byname_n = {}
    for f in nm['functions']:
        byname_n.setdefault(raw_symbol(nm, f['index']), f)

    def body_range(f):
        assert any(v['start'] == f['address'] for v in vers[f['index']]), f['index']
        i = bisect.bisect_right(starts, f['address'])
        end = starts[i] - 6 if i < len(starts) else len(oc)
        return f['address'] - 6, end

    out = dict(runtime=str(rt), status=ptr['status'], runtime_ain=h, runtime_pact=sha(rt / 'NightRemasterPact.afa'),
               runtime_ex=sha(rt / 'NightRemasterEX.ex'), manifest_sha256=ptr['manifest_sha256'],
               functions_r15=len(om['functions']), functions_now=len(nm['functions']))
    pins = {}
    for n in PINNED:
        fo, fn = byname_o[n], byname_n[n]
        a, b = body_range(fo)
        pins[n] = dict(index=fn['index'], address=fn['address'], same_entry=fo == nm['functions'][fo['index']],
                       code_bytes=b - a, code_identical=oc[a:b] == nc[a:b])
    out['pinned'] = pins
    sites = []
    for s in oman['same_length_sites']:
        ad = s['site']
        sites.append(dict(function=s['function'], replacement=s['replacement'], site=ad,
                          still_swapped=nc[ad:ad + 6].hex() == s['after'], owner_entry_same=om['functions'][s['fid']] == nm['functions'][s['fid']]))
    out['swap_sites_intact'] = sum(x['still_swapped'] and x['owner_entry_same'] for x in sites)
    out['swap_sites'] = sites
    kr9 = [f for f in om['functions'] if raw_symbol(om, f['index']).startswith('KR_T9')]
    moved = [raw_symbol(om, f['index']) for f in kr9 if nm['functions'][f['index']] != f]
    changed_code = []
    for f in kr9:
        a, b = body_range(f)
        if oc[a:b] != nc[a:b]:
            changed_code.append(raw_symbol(om, f['index']))
    out['kr_t9_functions'] = len(kr9)
    out['kr_t9_entries_changed'] = moved
    out['kr_t9_code_changed'] = changed_code
    changed_entries = [raw_symbol(om, f['index']) for f in om['functions'] if nm['functions'][f['index']] != f]
    out['r15_function_entries_changed_by_codex'] = len(changed_entries)
    out['r15_function_entries_changed_names'] = changed_entries[:60]
    added = nm['functions'][len(om['functions']):]
    out['functions_added_by_codex'] = len(added)
    out['functions_added_prefixes'] = dict(collections.Counter(re.match(r'[A-Za-z]+_[A-Za-z]+', raw_symbol(nm, f['index'])).group(0)
                                                               if re.match(r'[A-Za-z]+_[A-Za-z]+', raw_symbol(nm, f['index'])) else '?' for f in added))
    (HERE / 'result.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
