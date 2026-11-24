"""Claude Opus 5.5 (2026-09-28) r24: the event flow chart touch-up (설계_v4 「r24 요구」) on top of the r23 install (current.json
FEELING_R23_INSTALLED_NATIVE_PASS: AIN b5ec7f01... = the r23 candidate, winmm.dll a72b1b9d... = the mod-menu hook r2).

  python build_chart_r24.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/winmm/status/manifest = r24lib BASE_*, P: free space >= 10 GB, r23 installed
     (evidence/feeling_r23 journal COMMITTED, the r23 candidate = the runtime AIN), r22 installed below it (evidence/chart_r22),
     the hook r2 installed (mod_menu_r2 journal), the Manual chart unchanged.
  2. the r22 chart the base holds (read only): its cell tables are baked into the base already (r22 build) and stay; the part
     numbers r24 adds (KR_CPart 36-39: the two buttons) must be free in r22's code and inside KR_CClear's range (0..111); the chart
     root Z = r22's; the button labels / legend / widest header must fit (measured glyph advances, r23 explore probe).
  3. alice ain edit --jaf (declare KR_C24*) -> dump -> native_lower -> alice ain edit --jam with the lowered bodies, one hand-written
     body (KR_C24WaitRaw: AFL_Parts_WaitForClick with the KR_C24Frame delegate and key cancel, = r22 KR_CWait's shape) and six
     one-call forwarder bodies for r22 chart functions (same index / arguments / return, new address; r22 did the same to r15 / r18
     / r21 functions):
       KR_CChart -> KR_C24Chart (r22's chart loop + back to the same tab / page after a replay, the user's 14:00 addition),
       KR_CDraw -> KR_C24Draw, KR_CWait -> KR_C24Wait, KR_CClick -> KR_C24Click, KR_CStateLine -> KR_C24StateLine,
       KR_CPlayNote -> KR_C24PlayNote
     No same-length operand swap: no original (game) function and no earlier site is touched.
  4. invariance: every base function entry identical except the six forwarded ones (address only, bodies in the appended code);
     the old CODE byte-identical (nothing changes in place); MSG1, STR0 prefix identical; the six pinned functions keep entry and
     every code byte; r15's nine, r18's one, r20's seven, r21's two, r22's two and r23's three operand sites and r18's eight /
     r19's five / r22's six forwarders in place; the replay functions (KR_CReplay, KR_CReplayRun) and the other r22 chart
     functions r24 keeps byte-identical; native opcode audit.
  5. end gate: the runtime hashes are read again; if Codex installed something meanwhile the candidate is DISCARDED (exit 3).
PACT, EX, FNL, the Manual chart and winmm.dll are not touched. Nothing is written outside r24_chart\\ (runtime, saves, Codex
root, r15-r23: read only).
"""
import sys, json, re, struct, shutil, collections, datetime
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r24lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_chart_r24.jaf'
PREFIX = 'KR_C24'
PART_BASE, PART_COUNT = 2026092200, 112           # r22's chart parts (KR_CPart 0..111; KR_CClear releases all of them)
BUTTON_PARTS = {'KR_C24BtnAll': 36, 'KR_C24BtnHide': 38}       # box = KR_CPart(n), label = KR_CPart(n + 1)
BUTTONS = [('KR_C24BtnHide', '다시 가리기', 880.0), ('KR_C24BtnAll', '전체 개방', 1008.0)]   # 닫기 = (1136, 12) 120 x 40 (r22)
BUTTON_W, BUTTON_H, CLOSE_X, BUTTON_GAP = 120, 40, 1136.0, 8
LABEL_PX = 22
METRICS = {18: dict(full=14, digit=9, space=5, other=6), 20: dict(full=16, digit=10, space=5, other=7),
           22: dict(full=17, digit=11, space=6, other=7), 24: dict(full=19, digit=12, space=6, other=8)}   # measured (r23 work/explore)
METRICS[17] = METRICS[18]            # the legend's 17 px was not measured: the 18 px advances are an upper bound
LEGEND_X, PAGE_X = 200, 590
HEADER_X = 24
KEYS = {'U': 85, 'R': 82}
FORWARD = {            # existing r22 chart function (index kept) -> r24 body (same arguments and return type)
    'KR_CChart': 'KR_C24Chart',           # r22's chart loop + the chart again (same tab / page, the played cell marked) after a replay
    'KR_CDraw': 'KR_C24Draw',             # r22's frame as it is + the new legend + the two buttons + the cells (locked: names, conditions)
    'KR_CWait': 'KR_C24Wait',             # the wait (KR_C24WaitRaw) + the two buttons: flag file and session variable, number returned
    'KR_CClick': 'KR_C24Click',           # a locked cell opens its detail page too (no 이 장면 재생: KR_CCanPlay)
    'KR_CStateLine': 'KR_C24StateLine',   # the locked scene's state line
    'KR_CPlayNote': 'KR_C24PlayNote',     # 「재생 불가」 also on a locked not-playable scene
}
JAM_BODIES = ['KR_C24WaitRaw']
SESSION_VARIABLES = ['YoruKR.C.KeyU', 'YoruKR.C.KeyR', 'YoruKR.C.Last']
UNTOUCHED_R22 = ['KR_CReplay', 'KR_CReplayRun', 'KR_CDrawFrame', 'KR_CDrawCell', 'KR_CFrame', 'KR_CClear', 'KR_CDo', 'KR_CServe',
                 'KR_CTitleTick', 'KR_CTitleServe', 'KR_CCardPage', 'KR_CEventPage', 'KR_CRequest', 'KR_CCanPlay', 'KR_COpen', 'KR_CGlobal']
R15_SITES, R20_SITES, R21_SITES, R22_SITES, R23_SITES = 9, 7, 2, 2, 3
R19_FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
               'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
R22_FORWARD = {'KR_MDo': 'KR_CDoHome', 'KR_T9Seen': 'KR_CSeen', 'KR_T9State': 'KR_CState', 'KR_T9Legend': 'KR_CLegend',
               'KR_T18CardPage': 'KR_CCardPage', 'KR_T18EventPage': 'KR_CEventPage'}
TAB_NAMES = ['4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '회상', '그 밖']


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
    assert base_is_current(ptr, got), ('runtime moved: rebase r24lib BASE_* on the new runtime first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    j = L.readj(L.R23_JOURNAL)
    assert j['status'] == 'COMMITTED' and j['after']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r23 not installed as expected', j['status'])
    j22 = L.readj(L.R22_JOURNAL)
    assert j22['status'] == 'COMMITTED' and j22['after']['NightRemaster.ain'] == L.R22_AIN_SHA, ('r22 not installed as expected', j22['status'])
    assert j['before']['NightRemaster.ain'] == L.R22_AIN_SHA, 'r23 was not installed on the r22 install'
    h = L.readj(L.HOOK_JOURNAL)
    assert h['status'] == 'COMMITTED' and h['after']['winmm.dll'] == L.BASE_WINMM_SHA, ('the mod-menu hook r2 is not installed as expected', h['status'])
    assert L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA, 'the runtime Manual chart moved'
    bp = L.base_paths()
    assert L.sha(bp['ain']) == L.BASE_AIN_SHA
    return ptr, rt, bp, free


def site_list():
    """r15's nine, r18's one, r20's seven, r21's two, r22's two and r23's three same-length operand sites (bytes the base must keep)."""
    out = []
    for by, d, n in (('r15', L.R15, R15_SITES), ('r18', L.R18, 1), ('r20', L.R20, R20_SITES), ('r21', L.R21, R21_SITES),
                     ('r22', L.R22, R22_SITES), ('r23', L.R23, R23_SITES)):
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


# ---------------------------------------------------------------- measured widths (r23 explore probe: 18 / 20 / 22 / 24 px)
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


def untag(t):
    return re.sub(r'\$\{/?font[^}]*\}', '', t)


def layout_checks(r22man, cells):
    """The buttons sit left of 닫기 with the gap the tabs use, the labels fit their boxes, the widest header of every tab ends left
    of the first button, the new legend ends left of the page line."""
    out = {}
    assert r22man['root_z'] == 5000 and r22man['parts'] == dict(first=PART_BASE, count=PART_COUNT), (r22man['root_z'], r22man['parts'])
    xs = [x for _, _, x in BUTTONS] + [CLOSE_X]
    for a, b in zip(xs, xs[1:]):
        assert b - a == BUTTON_W + BUTTON_GAP, ('button spacing', a, b)
    labels = {}
    for fn, label, x in BUTTONS:
        w = width(label, LABEL_PX)
        assert w <= BUTTON_W - 12, ('button label too wide', label, w)
        labels[fn] = dict(label=label, x=x, text_x=float(int((BUTTON_W - w) / 2 * 2) / 2), width_px=w)
    per_tab = [cells['first'][t + 1] - cells['first'][t] if t < 9 else len(cells['rows']) - cells['first'][t] for t in range(10)]
    widest = 0
    for t in range(10):
        n = per_tab[t]
        head = '이벤트 플로우 차트' + '　' + TAB_NAMES[t] + '　' + '%d/%d' % (n, n) + ' 열림' + '　' + '전체 개방'
        widest = max(widest, width(head, 24))
    assert HEADER_X + widest <= BUTTONS[0][2] - 16, ('the header can reach the buttons', widest)
    legend = '● 안 읽음　△ 읽음(게임 전역 기록)　회색 칸 잠김'
    lw = width(legend, 17)
    assert LEGEND_X + lw <= PAGE_X - 16, ('the legend reaches the page line', lw)
    out.update(labels=labels, widest_header_px=widest, header_right=HEADER_X + widest, first_button_x=BUTTONS[0][2], legend_px=lw,
               legend_right=LEGEND_X + lw, page_line_x=PAGE_X, per_tab=per_tab)
    return out


def parts_free(bp, m):
    """KR_CPart(36..39) are not drawn by r22's code (its readable jaf and every KR_C* body of the base), and 36..39 < 112 (KR_CClear)."""
    src = (L.R22 / 'work' / 'build' / 'helpers_readable.jaf').read_text('utf8')
    used = sorted({int(z) for z in re.findall(r'KR_CPart\((\d+)\)', src)})
    for fn, n in BUTTON_PARTS.items():
        for k in (n, n + 1):
            assert k not in used and k < PART_COUNT, ('part number taken or outside KR_CClear', fn, k)
    raw = Path(bp['raw']).read_text('utf8')
    for n in BUTTON_PARTS.values():
        for k in (n, n + 1):
            v = PART_BASE + k
            assert 'PUSH 0x%x' % v not in raw and 'PUSH %d' % v not in raw, ('the part number is a literal in the base', v)
    return dict(r22_parts_used=used, added=sorted(k for n in BUTTON_PARTS.values() for k in (n, n + 1)))


# ---------------------------------------------------------------- jaf, compile and patch
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


def sig(f):
    return ([a['type'] for a in f['arguments']], f['return-type'])


_SYMS = {}


def fid_sym(m, name):
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


def forwarder(m, fid, target):
    f = m['functions'][fid]
    assert all(a['type'][0] in (10, 12, 47) for a in f['arguments']), ('forwarders pass int/bool/string arguments only', f['name'])
    assert f['return-type'][0] in (0, 10, 12, 47), ('forwarder return type', f['name'], f['return-type'])
    body = ''.join(f"\t.LOCALREF {a['name']}\n" + ('\tA_REF\n' if a['type'][0] == 12 else '') for a in f['arguments'])
    return f"FUNC {fid}\n{body}\tCALLFUNC {target}\n\tRETURN\nENDFUNC {L.raw_symbol(m, fid)}\n"


def jam_bodies(m, dm, ids):
    """KR_C24WaitRaw: r22 KR_CWait's body with the KR_C24Frame delegate (AFL_Parts_WaitForClick(frame, key cancel))."""
    wait = m['functions'][L.fid_of(m, 'AFL_Parts_WaitForClick')]
    assert len(wait['arguments']) == 2 and wait['return-type'][0] == 10, (wait['arguments'], wait['return-type'])
    b = {'KR_C24WaitRaw': f"\tPUSH -1\n\tPUSH {ids['KR_C24Frame']}\n\tDG_NEW_FROM_METHOD\n\tPUSH 1\n\tCALLFUNC AFL_Parts_WaitForClick\n\tRETURN\n"}
    return {ids[n]: f"FUNC {ids[n]}\n{body}ENDFUNC {n}\n" for n, body in b.items()}


def compile_and_patch(base, m, jaf_text):
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
    assert set(JAM_BODIES) <= set(ids)
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
    forwarded = {}
    for old, new in FORWARD.items():
        fid = L.fid_of(m, old)
        assert sig(m['functions'][fid]) == sig(dm['functions'][ids[new]]), (old, new, sig(m['functions'][fid]), sig(dm['functions'][ids[new]]))
        patch.append(forwarder(m, fid, new))
        forwarded[old] = dict(index=fid, base_address=m['functions'][fid]['address'], target=new, target_index=ids[new])
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
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, forwarded, oldn


def invariance(base, out, m, forwarded, oldn, old_sites, bp):
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', out)
    nm = L.read_meta(W / 'candidate_meta.json')
    fw = {v['index'] for v in forwarded.values()}
    changed = [f['index'] for f, g in zip(m['functions'], nm['functions']) if f != g]
    assert set(changed) == fw, ('function entries changed beyond the forwarders', sorted(set(changed) - fw)[:5])
    for i in fw:
        f, g = m['functions'][i], nm['functions'][i]
        assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, f['name']
        assert g['address'] >= oldn, ('a forwarder body is not in the appended code', f['name'])
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], ('metadata key changed', k)
    old = L.unpack(base.read_bytes())
    new = L.unpack(out.read_bytes())
    diff = [i for i in range(oldn) if old[16 + i] != new[16 + i]]
    assert not diff, ('old CODE bytes changed (r24 changes nothing in place)', [hex(x) for x in diff][:10])
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
    for name in FORWARD:
        assert name not in L.PINNED_ALL, ('a pinned function forwarded', name)
        assert name not in UNTOUCHED_R22, name
    untouched = {}
    for name in UNTOUCHED_R22:
        i = L.fid_of(m, name)
        f = m['functions'][i]
        assert nm['functions'][i] == f, ('an r22 function r24 keeps moved', name)
        a = body_bytes(bcode, starts, f['address'], len(bcode))
        assert body_bytes(code, starts, f['address'], len(bcode)) == a, ('an r22 function r24 keeps changed', name)
        untouched[name] = dict(index=i, address=f['address'], code_bytes=len(a))
    cvers = L.versions(W / 'candidate_raw_code.jam')
    for old_, new_ in list(R19_FORWARD.items()) + list(R18_FORWARD.items()) + list(R22_FORWARD.items()) + list(FORWARD.items()):
        v = L.live_version(nm, cvers, L.fid_of(nm, old_))
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
    return nm, dict(original_function_entries_identical_except_forwarded=True, forwarded=sorted(FORWARD),
                    other_metadata_identical=sorted(k for k in m if k != 'functions'), old_code_bytes_changed=0,
                    old_code_identical=True, MSG1_exact=True, STR0_prefix_exact=True,
                    STR0_added=len(sn) - len(so), functions_added=len(nm['functions']) - len(m['functions']), pinned=pinned,
                    earlier_same_length_sites_kept=n_old, r22_functions_kept_in_place=untouched,
                    forwarders_kept=dict(r18=len(R18_FORWARD), r19=len(R19_FORWARD), r22=len(R22_FORWARD)))


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
    log('base keeps the r15/r18/r20/r21/r22/r23 same-length sites:', sites_applied(bcode, old_sites))
    for old_, new_ in list(R18_FORWARD.items()) + list(R19_FORWARD.items()) + list(R22_FORWARD.items()):
        f = m['functions'][L.fid_of(m, old_)]
        v = L.live_version(m, vers, f['index'])
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(m, new_), 'RETURN'], ('forwarder not in the base', old_)
    # the r22 chart the base holds: KR_CWait = the r22 hand-written wait, KR_CDraw = frame + cells (what r24 replaces)
    kw = [op for _, op in L.live_version(m, vers, L.fid_of(m, 'KR_CWait'))['ops'] if not op.startswith('ENDFUNC')]
    assert kw == ['PUSH 0xffffffff', 'PUSH 0x%x' % L.fid_of(m, 'KR_CFrame'), 'DG_NEW_FROM_METHOD', 'PUSH 0x1',
                  'CALLFUNC 0x%x' % L.fid_of(m, 'AFL_Parts_WaitForClick'), 'RETURN'], ('the base KR_CWait is not r22\'s wait', kw)
    kd = [op for _, op in L.live_version(m, vers, L.fid_of(m, 'KR_CDraw'))['ops'] if op.startswith('CALLFUNC ')]
    assert kd[0] == 'CALLFUNC 0x%x' % L.fid_of(m, 'KR_CDrawFrame') and kd.count('CALLFUNC 0x%x' % L.fid_of(m, 'KR_CDrawCell')) == 2, kd
    r22man = L.readj(L.R22 / 'candidate' / 'manifest.json')
    cells = L.readj(L.R22 / 'work' / 'build' / 'cells.json')
    assert len(cells['rows']) == 915, len(cells['rows'])
    lay = layout_checks(r22man, cells)
    pf = parts_free(bp, m)
    log('layout', {k: v for k, v in lay.items() if k != 'per_tab'}, 'parts', pf['added'])
    jaf = JAF_SRC.read_text('utf8')
    labels = lay['labels']
    for fn, key in (('KR_C24BtnHide', 'HIDE'), ('KR_C24BtnAll', 'ALL')):
        assert jaf.count('@@%s_X@@' % key) == 1 and jaf.count('@@%s_TX@@' % key) == 1
        jaf = jaf.replace('@@%s_X@@' % key, '%.1f' % labels[fn]['x']).replace('@@%s_TX@@' % key, '%.1f' % labels[fn]['text_x'])
    assert '@@' not in jaf, re.findall(r'@@\w+@@', jaf)
    for fn, n in BUTTON_PARTS.items():
        assert ('int %s() { return KR_CPart(%d); }' % (fn, n)) in jaf, fn
    for k, vk in KEYS.items():
        assert ('"Key%s", %d' % (k, vk)) in jaf, k
    (W / 'helpers_readable.jaf').write_text(jaf, 'utf8')
    texts = jaf_strings(L.strip_comments(jaf))
    bad = check_alphabet(texts)
    assert not bad, ('characters outside the font map / proxy set', bad)
    built = L.jaf_literal_encode(L.strip_comments(jaf))
    assert not [c for c in built if ('\uac00' <= c <= '\ud7a3')], 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, forwarded, oldn = compile_and_patch(base, m, built)
    log('compiled: %d functions added, %d forwarders' % (len(ids), len(forwarded)))
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    nm, inv = invariance(base, out, m, forwarded, oldn, old_sites, bp)
    log('invariance ok', {k: v for k, v in inv.items() if k not in ('pinned', 'r22_functions_kept_in_place')})
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    L.writej(W / 'layout.json', dict(layout=lay, parts=pf))
    ptr2, rt2, got2 = runtime_now()
    if not base_is_current(ptr2, got2):
        discard('runtime moved during the build', dict(got2, status=ptr2['status'], manifest_sha256=ptr2['manifest_sha256']))
    man = dict(
        schema='yoru-chart-r24.candidate.v1', status='CHART_R24_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, winmm_sha256=L.BASE_WINMM_SHA,
                  chart_sha256=L.BASE_CHART_SHA, r23_installed=True, r22_installed=True, hook_r2_installed=True, checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False, chart_changed=False, winmm_changed=False,
        data=dict(r22_cells_sha256=L.sha(L.R22 / 'work' / 'build' / 'cells.json'), cells=len(cells['rows']),
                  tables='r22\'s cell tables in the base are used as they are (names, when, conditions, thumbnails, not-playable)'),
        display=dict(locked_cell='the r19 name, 「● E#####」, when and the condition in grey at the open cell\'s places; a thumbnail event gets '
                                 'an empty 120 x 90 frame (22,22,28 / border 70,70,82) instead of its CG; the grey box stays',
                     locked_click='the detail page (the calendar\'s card / scene page, r22 chart branch) without 이 장면 재생; state line '
                                  '「● 안 읽은 장면 · 전체 개방하면 재생됩니다」 (a not-playable scene: 「● 안 읽은 장면입니다」 + 「재생 불가(게임 안에서만)」)',
                     buttons=[dict(fn=fn, part=PART_BASE + BUTTON_PARTS[fn], label_part=PART_BASE + BUTTON_PARTS[fn] + 1, label=lab, x=x, y=12,
                                   w=BUTTON_W, h=BUTTON_H, text_x=labels[fn]['text_x']) for fn, lab, x in BUTTONS],
                     button_action='write YoruKR_Chart.dat 1 / 0 (r21 KR_MSetUnlock, the menu bar\'s file) and the session variable YoruKR.C.All; '
                                   'the chart loop (KR_C24Chart, the answers of r22 KR_CChart) redraws the same tab and page (the number is not one of its answers)',
                     keys=dict(U='전체 개방', R='다시 가리기', rule='press and release once; a key already down when the page is drawn is ignored'),
                     legend='● 안 읽음　△ 읽음(게임 전역 기록)　회색 칸 잠김', header='r22 as it was (「전체 개방」 when the flag is 1)',
                     resume='a replay started from the chart (the page of a cell, 이 장면 재생) runs as in r22 (chart and windows closed, every '
                            'chart part released, the memory-mode path) and then the chart opens again on the same tab and page with the '
                            'border of the played cell gold (YoruKR.C.Last); only 닫기 / cancel go back to the title / home-base menu; the '
                            'position lives in the locals of KR_C24Chart (gone if the game stops during the replay)'),
        layout=lay,
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=JAM_BODIES, forwarded_functions=forwarded,
        r18_forwarders_kept=sorted(R18_FORWARD), r19_forwarders_kept=sorted(R19_FORWARD), r22_forwarders_kept=sorted(R22_FORWARD),
        same_length_sites=[], earlier_same_length_sites_kept=inv['earlier_same_length_sites_kept'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], r22_functions_kept_in_place=inv['r22_functions_kept_in_place'], invariance=inv,
        parts=dict(first=PART_BASE, count=PART_COUNT, added=[PART_BASE + k for k in pf['added']]),
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        session_variables_new=SESSION_VARIABLES, new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
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
