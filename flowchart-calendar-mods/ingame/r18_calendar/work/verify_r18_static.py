# ============================================================== static checks
def swap_of(man):
    s = man['same_length_sites']
    assert len(s) == 1 and s[0]['function'] == L.SWAP_OWNER and s[0]['original'] == L.SWAP_OLD and s[0]['replacement'] == L.SANDBOX, s
    return s[0]


def static_checks(base, cand, man, m, nm, counts, mutate_bytes=None, mutate_meta=None, parts=('S1', 'S2', 'S3', 'S4', 'S6', 'S7')):
    bb = base.read_bytes()
    cb = cand.read_bytes()
    if mutate_bytes:
        cb = mutate_bytes(cb)
    if mutate_meta:
        nm = mutate_meta(copy.deepcopy(nm))
    assert L.sha_bytes(cb) == man['files']['NightRemaster.ain']['sha256'] or mutate_bytes, 'candidate != manifest'
    old = L.unpack(bb)
    new = L.unpack(cb)
    oldn = struct.unpack_from('<I', old, 12)[0]
    fw = {L.fid_of(m, n) for n in FORWARD}
    swap = swap_of(man)
    a, b = swap['site'] + 2, swap['site'] + 6
    sb = L.fid_of(nm, L.SANDBOX)
    if 'S1' in parts:
        for f in m['functions']:
            g = nm['functions'][f['index']]
            if f['index'] in fw:
                assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, f['name']
                assert g['address'] >= oldn, ('forwarder not in the appended code', f['name'])
            else:
                assert g == f, ('base function entry changed', f['index'], f['name'])
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
        assert all(n.startswith('KR_T18') for n in man['added_functions']), 'added functions must all be KR_T18*'
        assert not any(L.raw_symbol(nm, f['index']).startswith(('KR_T16', 'KR_T17')) for f in nm['functions']), 'r16/r17 names in the candidate'
        counts['S1_metadata'] += 1
    if 'S2' in parts:
        diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
        assert diff and set(diff) <= set(range(a, b)), ('base CODE bytes changed beyond the one RunEvent operand', diff[:8])
        assert bytes(new[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, sb), 'the swapped operand is not KR_T18RunSandboxed'
        assert bytes(old[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, L.fid_of(m, L.SWAP_OLD)), 'base site is not the RunEvent call'
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s in rman['same_length_sites']:
            ad = s['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s['after'], ('r15 swap missing in the base', s['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s['after'], ('r15 swap site no longer applied', s['function'], s['replacement'])
        counts['S2_r15_sites_kept'] = len(rman['same_length_sites'])
        counts['S2_base_code_bytes'] = oldn
        counts['S2_base_code_bytes_changed'] = len(diff)
        counts['S2_changed_bytes_inside_the_operand'] = int(set(diff) <= set(range(a, b)))
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed']
        counts['S3_text'] += 1
    if 'S6' in parts:
        ra = L.R15 / 'candidate' / 'NightRemaster.ain'
        rraw = L.unpack(ra.read_bytes())
        rcode = rraw[16:16 + struct.unpack_from('<I', rraw, 12)[0]]
        rm = L.read_meta(L.R15 / 'work' / 'build' / 'candidate_meta.json')
        rv = L.versions(L.R15 / 'work' / 'build' / 'candidate_raw_code.jam')
        starts = sorted({v['start'] for vs in rv.values() for v in vs})
        ccode = new[16:16 + struct.unpack_from('<I', new, 12)[0]]
        bcode = old[16:16 + oldn]
        for name in L.PINNED:
            i = L.fid_of(rm, name)
            f = rm['functions'][i]
            assert nm['functions'][i] == f == m['functions'][i], ('pinned function entry changed', name)
            j = bisect.bisect_right(starts, f['address'])
            end = starts[j] - 6 if j < len(starts) else len(rcode)
            lo = f['address'] - 6
            ref = rcode[lo:end]
            got = ccode[lo:end]
            assert ref == bcode[lo:end], ('pinned code in the base differs from r15', name)
            differ = [lo + k for k in range(len(ref)) if got[k] != ref[k]]
            if name == L.SWAP_OWNER:
                assert differ and set(differ) <= set(range(a, b)), ('pinned KR_T9HomeCasual differs beyond the one operand', [hex(x) for x in differ[:8]])
                counts['S6_KR_T9HomeCasual_bytes_changed'] = len(differ)
            else:
                assert not differ, ('pinned code changed', name)
            counts['S6_pinned_bytes'] += len(ref)
        counts['S6_pinned_functions'] = len(L.PINNED)
    if 'S7' in parts:
        g, r = nm['functions'][sb], nm['functions'][L.fid_of(nm, L.SWAP_OLD)]
        assert g['arguments'] == r['arguments'] == [] and g['return-type'] == r['return-type'] == [47, -1, 0, None], 'sandbox signature'
        assert man['sandbox']['index'] == sb and man['sandbox']['address'] == g['address'], 'manifest sandbox entry'
        assert man['added_functions'][L.SANDBOX] == sb
        counts['S7_sandbox_signature_equal_RunEvent'] = 1
    if 'S4' not in parts:
        return []
    vers = L.versions(L.base_dir() / 'raw_code.jam')
    bycrc = collections.defaultdict(list)
    for f in m['functions']:
        bycrc[f['crc'] & 0xffffffff].append(f)
    frames = []
    live = 0
    for name, path in L.resume_saves().items():
        row_ = L.save_records(path)
        assert row_ is not None, name
        for rr in [row_['ip']] + row_['returns']:
            if rr['address'] == -1:
                continue
            start = rr['address'] - rr['offset']
            choices = [f for f in bycrc[rr['crc']] if rr['name'].startswith(L.raw_symbol(m, f['index']) + '(')
                       and any(v['start'] == start for v in vers[f['index']])]
            assert len(choices) == 1, (name, rr)
            f = choices[0]
            assert f['index'] not in fw or start != f['address'], ('a saved frame is inside a forwarded function', name)
            assert nm['functions'][f['index']] == f or f['index'] in fw, ('saved frame function moved', name, f['name'])
            ad = rr['address']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes(new[16 + ad:16 + ad + 6]), ('saved return bytes differ', name, rr['name'][:40], hex(ad))
            live += int(start == f['address'])
            frames.append(dict(file=name, fid=f['index'], offset=rr['offset'], live=start == f['address'], function=L.raw_symbol(m, f['index'])))
    counts['S4_saves'] = len({x['file'] for x in frames})
    counts['S4_frames'] = len(frames)
    counts['S4_frames_in_live_versions'] = live
    counts['S4_frames_in_KR_T9HomeCasual'] = sum(1 for x in frames if x['function'] == 'KR_T9HomeCasual')
    counts['S4_frames_in_forwarded'] = sum(1 for x in frames if x['function'] in FORWARD)
    return frames


