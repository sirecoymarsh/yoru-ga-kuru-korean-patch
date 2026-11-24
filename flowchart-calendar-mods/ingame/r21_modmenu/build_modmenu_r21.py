"""Claude Opus 5.5 (2026-09-28) r21: the game-script side of the menu-bar 「모드」 menu, stage 1 (request consumer), on top of the
r20 install (current.json CALENDAR_R20_INSTALLED_NATIVE_PASS, AIN 9dfac62a… = the r20 candidate).

  python build_modmenu_r21.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/status/manifest = r21lib BASE_*, P: free space >= 10 GB, r20 installed
     (evidence/calendar_r20 journal COMMITTED, the r20 candidate = the runtime AIN), the help-menu chart = the r19 chart.
  2. alice ain edit --jaf (declare the KR_M* functions) -> dump -> native_lower -> alice ain edit --jam with the lowered bodies
     (no hand-written jam body in r21).
  3. two same-length CALLFUNC operand swaps inside unchanged functions, each checked for signature equality and uniqueness:
       KR_T9HomeMenuRun         CALLFUNC ■選択ダイアログ／実行                        -> KR_MHomeRun  (arm the poll while the home menu waits)
       C_SelectDialog@_Update   CALLFUNC C_UserInputManager::IsClickEnterOtherMouse -> KR_MTick     (every frame a selection dialog waits)
  4. invariance: every base function entry identical (no forwarder, no relocation); the old CODE identical except the two
     4-byte operands; MSG1, STR0 prefix identical; the six pinned functions keep entry and every code byte; r15's nine, r18's one
     and r20's seven operand sites and r18's eight / r19's five forwarders still in place; native opcode audit of every live
     function.
  5. end gate: the runtime hashes are read again. If Codex installed something meanwhile the candidate is DISCARDED
     (files removed, work/REBASE_NEEDED.json written) and the build exits 3 - rebuild on the new base, never install it.
PACT, EX, FNL and the help-menu chart are not touched. Nothing is written outside r21_modmenu\\ (runtime, saves, Codex root,
r15-r20: read only).
"""
import sys, io, json, re, struct, shutil, collections, datetime
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r21lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
JAF_SRC = HERE / 'claude_modmenu_r21.jaf'
PREFIX = 'KR_M'
R15_SITES = 9
R20_SITES = 7
R19_FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
               'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
# (owner, kind, original callee, occurrence among its calls in the owner, replacement)
SWAPS = [
    ('KR_T9HomeMenuRun', 'call', '■選択ダイアログ／実行', 0, 'KR_MHomeRun'),
    ('C_SelectDialog@_Update', 'call', 'C_UserInputManager::IsClickEnterOtherMouse', 0, 'KR_MTick'),
]
EXPECTED_CALLS = {    # every call of the original callee in the owner's live body (all accounted for)
    ('KR_T9HomeMenuRun', '■選択ダイアログ／実行'): 1,
    ('C_SelectDialog@_Update', 'C_UserInputManager::IsClickEnterOtherMouse'): 1,
}
CODE = 2026092801                                  # KR_MCode (the home menu's wait ends with it); must differ from these:
TAKEN_CODES = {2026092401: 'KR_T8HomePickCode'}
SESSION_VARIABLES = ['YoruKR.M.Home', 'YoruKR.M.Off']
FILES = dict(request='<game folder>\\KRMenu\\request.txt', last_result='<game folder>\\KRMenu\\last_result.txt',
             reset_req='<game folder>\\KRMenu\\reset.req', restore_req='<game folder>\\KRMenu\\restore.req',
             marker='<save folder>\\YoruKR_reset.marker', chart_flag='<save folder>\\YoruKR_Chart.dat')


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


def chart_inputs():
    """Recorded only (r21 bakes no chart table): the published chart, its builder and graph/schedule.json."""
    return dict(published_chart_sha256=L.sha(L.FLOW / 'chart' / 'yoru_flowchart_v2.html'), builder_sha256=L.sha(L.FLOW / 'chart' / 'build_chart_v2.py'),
                schedule_sha256=L.sha(L.FLOW / 'graph' / 'schedule.json'))


def gates():
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase r21lib BASE_* on the new runtime first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    j = L.readj(L.R20_JOURNAL)
    assert j['status'] == 'COMMITTED' and j['after']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r20 not installed as expected', j['status'])
    assert L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA, 'the runtime help-menu chart is not the r19 chart'
    bp = L.base_paths()
    assert L.sha(bp['ain']) == L.BASE_AIN_SHA
    return ptr, rt, bp, free, chart_inputs()


def site_list():
    """r15's nine, r18's one and r20's seven same-length operand sites (bytes the base must keep)."""
    r15 = L.readj(L.R15 / 'candidate' / 'manifest.json')['same_length_sites']
    r18 = L.readj(L.R18 / 'candidate' / 'manifest.json')['same_length_sites']
    r20 = L.readj(L.R20 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(r15) == R15_SITES and len(r18) == 1 and len(r20) == R20_SITES
    return [dict(s, by='r15') for s in r15] + [dict(s, by='r18') for s in r18] + [dict(s, by='r20') for s in r20]


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
    """The live body of `fid` as ops, INCLUDING the code that follows lambdas compiled inline into it and EXCLUDING the lambda
    bodies themselves (r20 build)."""
    owner = L.raw_symbol(m, fid)
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
                nm = L.raw_symbol(m, k)
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


# ---------------------------------------------------------------- jaf checks
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


# ---------------------------------------------------------------- compile and patch
def sig(f):
    return ([a['type'] for a in f['arguments']], f['return-type'])


def fid_sym(m, name):
    hits = [f['index'] for f in m['functions'] if L.symbol(m, f['index']) == name]
    assert len(hits) == 1, (name, hits)
    return hits[0]


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
    assert all(n.startswith(PREFIX) for n in ids), [n for n in ids if not n.startswith(PREFIX)]
    changed = [f['index'] for f, g in zip(m['functions'], dm['functions']) if f != g and f['index'] != 0]
    assert not changed, ('the jaf declaration touched existing functions', changed[:5])
    patch = []
    for f in added:
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
    sites = []
    for owner, kind, oldfn, nth, newfn in SWAPS:
        assert kind == 'call'
        fid = L.fid_of(m, owner)
        oldid = fid_sym(m, oldfn)
        newid = ids[newfn]
        assert sig(dm['functions'][newid]) == sig(m['functions'][oldid]), (newfn, sig(dm['functions'][newid]), sig(m['functions'][oldid]))
        ops = region_ops(raw_path, m, fid)
        key = f'CALLFUNC 0x{oldid:x}'
        hits = [i for i, (ad, op) in enumerate(ops) if op == key]
        assert len(hits) == EXPECTED_CALLS[(owner, oldfn)], (owner, oldfn, len(hits))
        ad = ops[hits[nth]][0]
        before = struct.pack('<Hi', 0x30, oldid)
        after = struct.pack('<Hi', 0x30, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (owner, hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=owner, fid=fid, function_address=m['functions'][fid]['address'], site=ad,
                          site_offset=ad - m['functions'][fid]['address'], kind='CALLFUNC', original=oldfn, original_fid=oldid,
                          replacement=newfn, replacement_fid=newid, before=before.hex(), after=after.hex(), operand_bytes=[ad + 2, ad + 6],
                          occurrence=nth, calls_of_original_in_function=len(hits)))
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
    log('base keeps the r15/r18/r20 same-length sites:', sites_applied(bcode, old_sites))
    for old_, new_ in list(R18_FORWARD.items()) + list(R19_FORWARD.items()):
        f = m['functions'][L.fid_of(m, old_)]
        v = L.live_version(m, vers, f['index'])
        assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(m, new_), 'RETURN'], ('forwarder not in the base', old_)
    # the codes a home menu wait can end with must stay distinct
    pick = L.live_version(m, vers, L.fid_of(m, 'KR_T8HomePickCode'))
    assert [op for _, op in pick['ops'] if not op.startswith('ENDFUNC')][:2] == ['PUSH 0x%x' % 2026092401, 'RETURN'], 'KR_T8HomePickCode moved'
    assert CODE not in TAKEN_CODES
    jaf = JAF_SRC.read_text('utf8')
    assert ('int KR_MCode() { return %d; }' % CODE) in jaf
    for k in SESSION_VARIABLES:
        assert jaf.count('"%s"' % k) == 1, k
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
    ptr2, rt2, got2 = runtime_now()
    if not base_is_current(ptr2, got2):
        discard('runtime moved during the build', dict(got2, status=ptr2['status'], manifest_sha256=ptr2['manifest_sha256']))
    man = dict(
        schema='yoru-modmenu-r21.candidate.v1', status='MODMENU_R21_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, chart_sha256=L.BASE_CHART_SHA,
                  r20_installed=True, checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False, chart_changed=False, chart_inputs_recorded=chart,
        protocol=dict(design='ingame/설계_v4_메뉴바차트.md 「프로토콜(확정, 09-28 02시)」', files=FILES,
                      commands=['chart', 'unlock_all', 'unlock_revert', 'reset_all', 'reset_restore'], end_code=CODE,
                      unknown_command='deleted and ignored (no window)', stage=1),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=[], forwarded_functions={},
        r18_forwarders_kept=sorted(R18_FORWARD), r19_forwarders_kept=sorted(R19_FORWARD), same_length_sites=sites,
        earlier_same_length_sites_kept=inv['earlier_same_length_sites_kept'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], invariance=inv,
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        session_variables=['YoruKR.T9.Ctx', 'YoruKR.T9.Req', 'YoruKR.T9.Play', 'YoruKR.T9.Playing', 'YoruKR.T9.Unwind', 'YoruKR.T9.Open', 'YoruKR.T9.Lane',
                           'YoruKR.T18.PrevSet', 'YoruKR.T18.PrevFn', 'YoruKR.T18.PrevSys'] + SESSION_VARIABLES,
        new_session_variables=SESSION_VARIABLES, new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
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
