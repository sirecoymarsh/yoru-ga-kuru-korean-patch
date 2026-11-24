"""One-off: turn the copied r17 build script into build_calendar_r18.py (exact block replacements, each asserted once)."""
from pathlib import Path

P = Path(__file__).resolve().parent.parent / 'build_calendar_r18.py'
t = P.read_text('utf8')


def rep(old, new, count=1):
    global t
    assert t.count(old) == count, (t.count(old), old[:80])
    t = t.replace(old, new)


# ---- docstring
i = t.index('"""', 3)
t = '''"""Claude Opus 5.5 (2026-09-27) r18: in-game event calendar = r17's screens (achievement bars, summary page, drawer rows;
every r17 function renamed KR_T18*) + replay lock + replay sandbox. r17 was installed 07:24 and restored 14:11 (journal
RESTORED), so the base is again the 04:01 AIN (r15 + Codex rate_overlay + story_explore; 18:03 chart menu changed only
winmm.dll and Manual/chart). r18 replaces the r17 candidate (and the never installed r16 one).

  python build_calendar_r18.py            build candidate/NightRemaster.ain + candidate/manifest.json

Steps:
  1. start gates: current.json runtime AIN/PACT/EX/status/manifest = r18lib BASE_*, P: free space >= 10 GB, and r15 inside
     the base: the five pinned functions (entry + code bytes), the nine same-length swap sites and all 93 KR_T9 functions
     (entries + code bytes) equal the r15 candidate (r15_calendar\\\\candidate, read only).
  2. data: chart/build_chart_v2.build() as a module (= published chart v2 HTML) -> the r15 tables recomputed here must equal
     r15's baked tables (r15_calendar\\\\work\\\\build\\\\tables.json) - the r15 tables inside the base stay valid.
  3. r17 tables (renamed KR_T18*): (a) r16's lane-row tails; (b) the panel-outside set from KR_PlayerEventCount (base AIN).
  4. alice ain edit --jaf (declare the KR_T18* functions) -> dump -> native_lower -> alice ain edit --jam with the lowered
     bodies AND a one-call forwarder body for eight r15 functions (same index, same arguments/return, new address):
       r17: KR_T9MonthPage, KR_T9MemPage, KR_T9LaneTitle, KR_T9CardRow, KR_T9ChipRow, KR_T9MonthChips -> KR_T18*
       r18: KR_T9CardPage -> KR_T18CardPage, KR_T9EventPage -> KR_T18EventPage (replay lock + sandbox note)
     then ONE same-length operand: KR_T9HomeCasual's `CALLFUNC LSys3xScript::RunEvent` -> KR_T18RunSandboxed (same
     signature: no arguments, bool; the return offset and every other byte of the pinned function stay).
  5. invariance: every base function entry identical except the eight forwarded ones (address only); other metadata keys,
     the whole old CODE except those 4 operand bytes, MSG1, STR0 prefix identical; pinned entries + code identical except
     that operand; r15 swap sites still applied; native opcode audit of every live function.
  6. end gate: the runtime hashes are read again. If Codex installed something meanwhile the candidate is DISCARDED
     (files removed, work/REBASE_NEEDED.json written) and the build exits 3 - rebuild on the new base, never install it.
PACT and EX are not touched. Nothing is written outside r18_calendar\\\\ (runtime, saves, Codex root, r15/r16/r17: read only).
''' + t[i:]

rep('import r17lib as L', 'import r18lib as L')
rep("JAF_SRC = HERE / 'claude_calendar_r17.jaf'", "JAF_SRC = HERE / 'claude_calendar_r18.jaf'")
rep('''FORWARD = {            # r15 screen function (index kept) -> r17 body (same arguments and return type)
    'KR_T9MonthPage': 'KR_T17MonthPage',
    'KR_T9MemPage': 'KR_T17MemPage',
    'KR_T9LaneTitle': 'KR_T17LaneTitle',
    'KR_T9CardRow': 'KR_T17CardRow',
    'KR_T9ChipRow': 'KR_T17ChipRow',
    'KR_T9MonthChips': 'KR_T17MonthChips',
}''', '''FORWARD = {            # r15 function (index kept) -> r18 body (same arguments and return type)
    'KR_T9MonthPage': 'KR_T18MonthPage',          # r17 screens (renamed)
    'KR_T9MemPage': 'KR_T18MemPage',
    'KR_T9LaneTitle': 'KR_T18LaneTitle',
    'KR_T9CardRow': 'KR_T18CardRow',
    'KR_T9ChipRow': 'KR_T18ChipRow',
    'KR_T9MonthChips': 'KR_T18MonthChips',
    'KR_T9CardPage': 'KR_T18CardPage',            # r18 replay lock (+ sandbox note)
    'KR_T9EventPage': 'KR_T18EventPage',
}''')

# ---- r15_inside: the pinned KR_T9HomeCasual may differ from r15 in the one swapped operand (candidate only)
rep('''def r15_inside(m, code, ref):
    """r15's pinned functions, swap sites and every KR_T9 function are byte-identical in `m`/`code` (base or candidate)."""
    rm, rc, rstarts, rman = ref
    out = dict(pinned={}, sites=0, kr_t9=0)
    for name in L.PINNED:
        i = L.fid_of(rm, name)
        f = rm['functions'][i]
        assert m['functions'][i] == f, ('pinned function entry differs from r15', name)
        assert body_bytes(code, rstarts, f['address'], len(rc)) == body_bytes(rc, rstarts, f['address'], len(rc)), ('pinned code differs from r15', name)
        out['pinned'][name] = dict(index=i, address=f['address'], code_bytes=len(body_bytes(rc, rstarts, f['address'], len(rc))))''',
    '''def r15_inside(m, code, ref, swap=None):
    """r15's pinned functions, swap sites and every KR_T9 function are byte-identical in `m`/`code` (base or candidate).
    swap = the r18 site (candidate only): inside KR_T9HomeCasual exactly the 4 operand bytes of the RunEvent call differ,
    and they hold swap['after']."""
    rm, rc, rstarts, rman = ref
    out = dict(pinned={}, sites=0, kr_t9=0)
    for name in L.PINNED:
        i = L.fid_of(rm, name)
        f = rm['functions'][i]
        assert m['functions'][i] == f, ('pinned function entry differs from r15', name)
        got = bytearray(body_bytes(code, rstarts, f['address'], len(rc)))
        want = bytearray(body_bytes(rc, rstarts, f['address'], len(rc)))
        differ = [j for j in range(min(len(got), len(want))) if got[j] != want[j]]
        if swap is not None and name == L.SWAP_OWNER:
            rel = swap['site'] - (f['address'] - 6)
            assert len(got) == len(want) and set(differ) <= set(range(rel + 2, rel + 6)), ('pinned code differs beyond the operand', name, differ[:8])
            assert bytes(got[rel:rel + 6]).hex() == swap['after'] and bytes(want[rel:rel + 6]).hex() == swap['before'], ('swap operand', name)
            out['pinned'][name] = dict(index=i, address=f['address'], code_bytes=len(want), bytes_differing=len(differ),
                                       differing_offsets_in_body=differ, operand_site=swap['site'])
            continue
        assert not differ and len(got) == len(want), ('pinned code differs from r15', name)
        out['pinned'][name] = dict(index=i, address=f['address'], code_bytes=len(want), bytes_differing=0)''')

rep('''def gates():
    free = shutil.disk_usage('P:\\\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase r17lib BASE_* on the new runtime first', got, ptr['status'])''',
    '''def gates():
    free = shutil.disk_usage('P:\\\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase r18lib BASE_* on the new runtime first', got, ptr['status'])
    j = L.readj(L.R17_JOURNAL)
    assert j['status'] == 'RESTORED' and j['before']['NightRemaster.ain'] == L.BASE_AIN_SHA, ('r17 is installed again?', j['status'])
    assert L.sha(L.R17 / 'candidate' / 'NightRemaster.ain') == L.R17_AIN_SHA, 'r17 candidate changed (evidence must stay)\'''')

rep("data = V2.build(str(L.TMP / 'chart_v2_from_r17_build.html'))", "data = V2.build(str(L.TMP / 'chart_v2_from_r18_build.html'))")

# ---- tables: KR_T18 names
rep('''    out = [tree('int', 'KR_T17CardTail', 'k', [(k, 1) for k in hit], 0),
           tree('string', 'KR_T17TailCond', 'k', [(k, q(v['cond'])) for k, v in hit.items()], '""'),
           '// 패널 밖 121 (왼쪽 달성률 패널 KR_PlayerEventCount 0~3 에 없는 달력 장면): 1 = 패널 밖\\n'
           + tree('int', 'KR_T17Out', 'no', [(no, 1) for no in outside], 0),
           tree('int', 'KR_T17OutEv', 'i', list(enumerate(outside)), -1),
           'int KR_T17OutTotal() {\\n    return %d;\\n}\\n' % len(outside)]''',
    '''    out = [tree('int', 'KR_T18CardTail', 'k', [(k, 1) for k in hit], 0),
           tree('string', 'KR_T18TailCond', 'k', [(k, q(v['cond'])) for k, v in hit.items()], '""'),
           '// 패널 밖 121 (왼쪽 달성률 패널 KR_PlayerEventCount 0~3 에 없는 달력 장면): 1 = 패널 밖\\n'
           + tree('int', 'KR_T18Out', 'no', [(no, 1) for no in outside], 0),
           tree('int', 'KR_T18OutEv', 'i', list(enumerate(outside)), -1),
           'int KR_T18OutTotal() {\\n    return %d;\\n}\\n' % len(outside)]''')

# ---- forwarder: int / bool / string arguments
rep('''def forwarder(m, fid, target):
    """One-call body: push every argument (int 10 / bool 47, one stack slot each), call the r17 body, return its value
    (or nothing for void)."""
    f = m['functions'][fid]
    assert all(a['type'][0] in (10, 47) for a in f['arguments']), ('forwarders pass int/bool arguments only', f['name'])
    assert f['return-type'][0] in (0, 10, 12), ('forwarder return type', f['name'], f['return-type'])
    body = ''.join(f"\\t.LOCALREF {a['name']}\\n" for a in f['arguments'])''',
    '''def forwarder(m, fid, target):
    """One-call body: push every argument (int 10 / bool 47 one stack slot; string 12 as the compiler passes a string local:
    .LOCALREF + A_REF, see KR_T17ChipRow -> KR_T17Row in r17), call the r18 body, return its value (or nothing for void)."""
    f = m['functions'][fid]
    assert all(a['type'][0] in (10, 12, 47) for a in f['arguments']), ('forwarders pass int/bool/string arguments only', f['name'])
    assert f['return-type'][0] in (0, 10, 12), ('forwarder return type', f['name'], f['return-type'])
    body = ''.join(f"\\t.LOCALREF {a['name']}\\n" + ('\\tA_REF\\n' if a['type'][0] == 12 else '') for a in f['arguments'])''')

rep('''    assert all(n.startswith('KR_T17') for n in ids), [n for n in ids if not n.startswith('KR_T17')]''',
    '''    assert all(n.startswith('KR_T18') for n in ids), [n for n in ids if not n.startswith('KR_T18')]
    sb, rev = dm['functions'][ids[L.SANDBOX]], m['functions'][L.fid_of(m, L.SWAP_OLD)]
    assert sig(sb) == sig(rev) == ([], [47, -1, 0, None]), ('KR_T18RunSandboxed must have RunEvent\\'s signature', sig(sb), sig(rev))''')

rep('''    struct.pack_into('<I', raw, 24 + newn, m['functions'][0]['address'])       # function 0 keeps its original body
    assert raw[16:16 + oldn] == old[16:16 + oldn], 'old CODE changed by the jaf/jam injection'
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, forwarded, oldn''',
    '''    struct.pack_into('<I', raw, 24 + newn, m['functions'][0]['address'])       # function 0 keeps its original body
    assert raw[16:16 + oldn] == old[16:16 + oldn], 'old CODE changed by the jaf/jam injection'
    swap = sandbox_swap(m, raw, ids[L.SANDBOX])
    assert raw[16:16 + oldn] != old[16:16 + oldn]
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, forwarded, oldn, swap


def sandbox_swap(m, raw, new_fid):
    """The one r18 same-length operand: in KR_T9HomeCasual's live body the single `CALLFUNC LSys3xScript::RunEvent`
    (opcode 0x30 + int32 function number) now calls KR_T18RunSandboxed. Everything else in the function stays."""
    vers = L.versions(L.base_dir() / 'raw_code.jam')
    fid = L.fid_of(m, L.SWAP_OWNER)
    old_fid = L.fid_of(m, L.SWAP_OLD)
    v = L.live_version(m, vers, fid)
    hits = [ad for ad, op in v['ops'] if op == 'CALLFUNC 0x%x' % old_fid]
    assert len(hits) == 1, ('RunEvent calls in KR_T9HomeCasual', hits)
    site = hits[0]
    before = struct.pack('<Hi', 0x30, old_fid)
    after = struct.pack('<Hi', 0x30, new_fid)
    assert bytes(raw[16 + site:16 + site + 6]) == before, ('swap site bytes', bytes(raw[16 + site:16 + site + 6]).hex())
    nxt = [op for ad, op in v['ops'] if ad > site][:1]
    assert nxt == ['POP'], ('the RunEvent result is popped right after the call', nxt)
    raw[16 + site:16 + site + 6] = after
    f = m['functions'][fid]
    return dict(function=L.SWAP_OWNER, fid=fid, function_address=f['address'], site=site, site_offset=site - f['address'],
                return_offset=site + 6 - f['address'], original=L.SWAP_OLD, original_fid=old_fid, replacement=L.SANDBOX,
                replacement_fid=new_fid, before=before.hex(), after=after.hex(), operand_bytes=[site + 2, site + 6],
                occurrence=0, calls_of_original_in_function=1)''')

rep('''def invariance(base, out, m, forwarded, oldn, ref):''', '''def invariance(base, out, m, forwarded, oldn, ref, swap):''')
rep('''    old = L.unpack(base.read_bytes())
    new = L.unpack(out.read_bytes())
    assert new[16:16 + oldn] == old[16:16 + oldn], 'old CODE bytes changed'
    assert L.raw_messages(base.read_bytes())[3] == L.raw_messages(out.read_bytes())[3], 'MSG1 changed\'''',
    '''    old = L.unpack(base.read_bytes())
    new = L.unpack(out.read_bytes())
    a, b = swap['operand_bytes']
    diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
    assert diff and set(diff) <= set(range(a, b)), ('old CODE bytes changed beyond the one operand', diff[:8])
    assert new[16:16 + a] == old[16:16 + a] and new[16 + b:16 + oldn] == old[16 + b:16 + oldn]
    assert L.raw_messages(base.read_bytes())[3] == L.raw_messages(out.read_bytes())[3], 'MSG1 changed\'''')
rep('''    inside = r15_inside(nm, code, ref)
    same_t9 = kr_t9_same(nm, code, ref, allow=set(FORWARD))
    return nm, dict(original_function_entries_identical_except_forwarded=True, forwarded=sorted(FORWARD),
                    other_metadata_identical=sorted(k for k in m if k != 'functions'), old_code_bytes_changed=0,''',
    '''    inside = r15_inside(nm, code, ref, swap=swap)
    same_t9 = kr_t9_same(nm, code, ref, allow=set(FORWARD) | {L.SWAP_OWNER})
    return nm, dict(original_function_entries_identical_except_forwarded=True, forwarded=sorted(FORWARD),
                    other_metadata_identical=sorted(k for k in m if k != 'functions'), old_code_bytes_changed=len(diff),
                    old_code_bytes_changed_offsets=diff, old_code_bytes_changed_are_the_operand=[a, b],''')

rep('''    assert 'KR_T16' not in L.strip_comments(src), 'r16 names left in the r17 source\'''',
    '''    assert 'KR_T16' not in L.strip_comments(src) and 'KR_T17' not in L.strip_comments(src), 'r16/r17 names left in the r18 source\'''')
rep('''    out, dm, ids, forwarded, oldn = compile_and_patch(base, m, built)
    log('compiled: %d functions added, %d forwarders' % (len(ids), len(forwarded)))
    nm, inv = invariance(base, out, m, forwarded, oldn, ref)''',
    '''    out, dm, ids, forwarded, oldn, swap = compile_and_patch(base, m, built)
    log('compiled: %d functions added, %d forwarders, swap %s -> %s at 0x%x' % (len(ids), len(forwarded), swap['before'], swap['after'], swap['site']))
    nm, inv = invariance(base, out, m, forwarded, oldn, ref, swap)''')

rep('''        schema='yoru-calendar-r17.candidate.v1', status='CALENDAR_R17_STAGED_NOT_INSTALLED', author=L.AUTHOR,''',
    '''        schema='yoru-calendar-r18.candidate.v1', status='CALENDAR_R18_STAGED_NOT_INSTALLED', author=L.AUTHOR,''')
rep('''        panel=panel_info, replaces=dict(r16_candidate_ain_sha256=L.R16_AIN_SHA, r16_installed=False,
                                        function_names='all new functions KR_T17* (r16 KR_T16* are not in this candidate)'),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), forwarded_functions=forwarded,
        same_length_sites=[], r15_same_length_sites_kept=inside['sites'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], invariance=inv,''',
    '''        panel=panel_info, replaces=dict(r17_candidate_ain_sha256=L.R17_AIN_SHA, r17_installed='07:24, restored 14:11 (journal RESTORED)',
                                        r16_candidate_ain_sha256=L.R16_AIN_SHA, r16_installed=False,
                                        function_names='all new functions KR_T18* (r17 KR_T17* renamed; r16 KR_T16* never shipped)'),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), forwarded_functions=forwarded,
        same_length_sites=[swap], r15_same_length_sites_kept=inside['sites'], relocated_original_functions=[],
        pinned_functions=inv['pinned'], invariance=inv,
        sandbox=dict(function=L.SANDBOX, index=ids[L.SANDBOX], address=nm['functions'][ids[L.SANDBOX]]['address'],
                     signature='bool ()  (= LSys3xScript::RunEvent)', temp_file='<EX Ｅ＿セーブファイル名＿接頭語>KRReplay.asd + .vsf',
                     method='game::detail::MemoryModeEvent_Begin/_End/_Cleanup: gamesave::detail::セーブ実行(file,"","",false) '
                            'returns true on the fresh save path, false after gamesave::detail::ロード実行(file) resumed here'),''')
rep('''        session_variables=['YoruKR.T9.Ctx', 'YoruKR.T9.Req', 'YoruKR.T9.Play', 'YoruKR.T9.Playing', 'YoruKR.T9.Unwind', 'YoruKR.T9.Open', 'YoruKR.T9.Lane'],''',
    '''        session_variables=['YoruKR.T9.Ctx', 'YoruKR.T9.Req', 'YoruKR.T9.Play', 'YoruKR.T9.Playing', 'YoruKR.T9.Unwind', 'YoruKR.T9.Open', 'YoruKR.T9.Lane',
                           'YoruKR.T18.PrevSet', 'YoruKR.T18.PrevFn', 'YoruKR.T18.PrevSys'],''')
rep('''        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],''',
    '''        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  r17_journal=dict(path=str(L.R17_JOURNAL), status=L.readj(L.R17_JOURNAL)['status']),''')
P.write_text(t, 'utf8')
print('patched', P)
