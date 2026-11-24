"""One-off: the r22 static checks S1-S8 replace r21's (the r21 sites / forwarders are now earlier work the base must keep)."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'verify_chart_r22.py'
s = p.read_text('utf8')
a = s.index('def r21_sites(man):')
b = s.index('# ============================================================== VM checks')
NEW = r'''def r21_sites(man=None):
    """r21's two same-length sites (in the base since r21; r22 keeps their operands)."""
    sites = L.readj(L.R21 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(sites) == 2, len(sites)
    return sites


def r22_sites(man):
    sites = man['same_length_sites']
    assert len(sites) == 2, len(sites)
    return sites


R21_OWNERS = {'KR_T9HomeMenuRun': ('■選択ダイアログ／実行', 'KR_MHomeRun'),
              'C_SelectDialog@_Update': ('C_UserInputManager::IsClickEnterOtherMouse', 'KR_MTick')}
SAVE_CALL_PREFIXES = ('gamesave::', 'AFL_GameSave_', '■セーブ', 'Ｓ＿コンフィグ', 'Ａ＿タイトルに戻る', 'C_SceneSaveLoad', 'AFL_MemoryModeEvent_')
MEMORY_MODE = ['AFL_MemoryModeEvent_Begin', 'AFL_MemoryModeEvent_End', 'AFL_MemoryModeEvent_Cleanup']


def live_ops(nm, cv, name):
    v = L.live_version(nm, cv, L.fid_of(nm, name))
    return [op for _, op in v['ops'] if not op.startswith('ENDFUNC')]


def live_ops_at(nm, cv, name):
    v = L.live_version(nm, cv, L.fid_of(nm, name))
    return [(ad, op) for ad, op in v['ops'] if not op.startswith('ENDFUNC')]


def call_graph(nm, cv, roots, stop=()):
    """Every function reachable by CALLFUNC from `roots` in the candidate (names); `stop` functions are listed but not entered."""
    seen = set()
    todo = list(roots)
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        if n in stop:
            continue
        try:
            ops = live_ops(nm, cv, n)
        except (AssertionError, StopIteration):
            continue
        for op in ops:
            if op.startswith('CALLFUNC '):
                todo.append(L.raw_symbol(nm, int(op.split()[1], 16)))
    return seen


def norm_jumps(ops_at):
    """Ops with jump / branch targets made relative to the body start (the same code at another address compares equal)."""
    start = ops_at[0][0]
    out = []
    for ad, op in ops_at:
        z = re.match(r'(JUMP|IFZ|IFNZ) 0x([0-9a-fA-F]+)$', op)
        out.append('%s +%d' % (z.group(1), int(z.group(2), 16) - start) if z else op)
    return out


def replay_body_check(nm, cv):
    """KR_CReplayRun = C_SceneModeScene@ExecScene from AFL_MemoryModeEvent_Begin on (the game's recollection path, same
    locals 2-5), with the event name taken from LSys3xScript::GetLabelName(no) instead of the EX recollection table."""
    ex = live_ops_at(nm, cv, 'C_SceneModeScene@ExecScene')
    rr = live_ops_at(nm, cv, 'KR_CReplayRun')
    begin = 'CALLFUNC 0x%x' % L.fid_of(nm, 'AFL_MemoryModeEvent_Begin')
    i = [op for _, op in ex].index(begin)
    j = [op for _, op in rr].index(begin)
    a = norm_jumps(ex[i:])
    b = norm_jumps(rr[j:])
    # jump targets relative to Begin: both bodies end the same way (Begin -> play / clean -> ... -> Cleanup -> RETURN)
    a2 = [re.sub(r'(JUMP|IFZ|IFNZ) \+(\d+)', lambda z: '%s +%d' % (z.group(1), int(z.group(2)) - (ex[i][0] - ex[0][0])), x) for x in a]
    b2 = [re.sub(r'(JUMP|IFZ|IFNZ) \+(\d+)', lambda z: '%s +%d' % (z.group(1), int(z.group(2)) - (rr[j][0] - rr[0][0])), x) for x in b]
    assert a2 == b2, ('KR_CReplayRun is not ExecScene\'s memory-mode path', [(x, y) for x, y in zip(a2, b2) if x != y][:4], len(a2), len(b2))
    pro = [op for _, op in rr[:j]]
    assert 'CALLFUNC 0x%x' % L.fid_of(nm, 'LSys3xScript::GetLabelName') in pro and not any('CheckEnabelScenario' in L.raw_symbol(nm, int(op.split()[1], 16))
                                                                                       for op in pro if op.startswith('CALLFUNC ')), pro
    ev = nm['functions'][L.fid_of(nm, 'C_SceneModeScene@ExecScene')]
    kr = nm['functions'][L.fid_of(nm, 'KR_CReplayRun')]
    assert [v['type'] for v in ev['variables']] == [v['type'] for v in kr['variables']], 'KR_CReplayRun locals differ from ExecScene'
    return len(a2)


def static_checks(base, cand, man, m, nm, counts, mutate_bytes=None, mutate_meta=None, parts=('S1', 'S2', 'S3', 'S4', 'S6', 'S7', 'S8')):
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
    fw22 = {L.fid_of(m, n) for n in R22_FORWARD}
    swap = r18_site()
    sb = L.fid_of(nm, L.SANDBOX)
    r20s = r20_sites()
    r21s = r21_sites()
    r22s = r22_sites(man)
    cv = L.versions(W / 'candidate_raw_code.jam')
    if 'S1' in parts:
        for f in m['functions']:
            g = nm['functions'][f['index']]
            if f['index'] in fw22:
                assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, ('forwarded entry changed beyond its address', f['name'])
                assert g['address'] >= oldn, ('a forwarder body is not in the appended code', f['name'])
            else:
                assert g == f, ('base function entry changed', f['index'], f['name'])
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
        assert all(n.startswith('KR_C') for n in man['added_functions']), 'added functions must all be KR_C*'
        assert not any(L.raw_symbol(nm, f['index']).startswith(('KR_T16', 'KR_T17')) for f in nm['functions']), 'r16/r17 names in the candidate'
        for old_, new_ in list(FORWARD.items()) + list(R18_FORWARD.items()) + list(R22_FORWARD.items()):
            v = L.live_version(nm, cv, L.fid_of(nm, old_))
            assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
        for name in R22_FORWARD:
            assert name not in L.PINNED_ALL, ('a pinned function forwarded', name)
        counts['S1_metadata'] += 1
        counts['S1_r22_forwarders'] = len(R22_FORWARD)
    if 'S2' in parts:
        allowed = {x for s_ in r22s for x in range(s_['site'] + 2, s_['site'] + 6)}
        diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
        assert set(diff) <= allowed, ('base CODE bytes changed outside r22\'s operands', [hex(x) for x in diff if x not in allowed][:8])
        for s_ in r22s:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['before'], ('r22 site: the base holds another operand', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('r22 site not applied', s_['function'], s_['replacement'])
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s_ in rman['same_length_sites'] + [swap] + r20s + r21s:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap missing in the base', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap site no longer applied', s_['function'], s_['replacement'])
        assert bytes(new[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, sb), 'KR_T9HomeCasual no longer calls KR_T18RunSandboxed'
        counts['S2_earlier_same_length_sites_kept'] = len(rman['same_length_sites']) + 1 + len(r20s) + len(r21s)
        counts['S2_r22_same_length_sites'] = len(r22s)
        counts['S2_base_code_bytes'] = oldn
        counts['S2_base_code_bytes_changed'] = len(diff)
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed'] and not man['fnl_changed'] \
            and not man['chart_changed'] and not man['winmm_changed']
        rt = L.runtime()[1]
        assert L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA and L.sha(rt / 'winmm.dll') == L.BASE_WINMM_SHA
        counts['S3_text'] += 1
    if 'S6' in parts:
        rv = L.versions(L.base_paths()['raw'])
        starts = sorted({v['start'] for vs in rv.values() for v in vs})
        ccode = new[16:16 + struct.unpack_from('<I', new, 12)[0]]
        bcode = old[16:16 + oldn]
        ra = L.R15 / 'candidate' / 'NightRemaster.ain'
        rraw = L.unpack(ra.read_bytes())
        rcode = rraw[16:16 + struct.unpack_from('<I', rraw, 12)[0]]
        rm = L.read_meta(L.R15 / 'work' / 'build' / 'candidate_meta.json')
        for name in L.PINNED_ALL:
            i = L.fid_of(m, name)
            f = m['functions'][i]
            assert nm['functions'][i] == f, ('pinned function entry changed', name)
            j = bisect.bisect_right(starts, f['address'])
            end = starts[j] - 6 if j < len(starts) else oldn
            lo = f['address'] - 6
            assert ccode[lo:end] == bcode[lo:end], ('pinned code changed', name)
            if name in L.PINNED:
                assert rm['functions'][L.fid_of(rm, name)] == f, ('pinned entry differs from r15', name)
                differ = [lo + k for k in range(end - lo) if rcode[lo + k] != bcode[lo + k]]
                if name == L.SWAP_OWNER:
                    assert differ and set(differ) <= set(range(swap['site'] + 2, swap['site'] + 6)), ('KR_T9HomeCasual differs from r15 beyond r18\'s operand', differ[:8])
                else:
                    assert not differ, ('pinned code differs from r15', name)
            counts['S6_pinned_bytes'] += end - lo
        counts['S6_pinned_functions'] = len(L.PINNED_ALL)
    if 'S7' in parts:
        g, r = nm['functions'][sb], nm['functions'][L.fid_of(nm, L.SWAP_OLD)]
        assert g['arguments'] == r['arguments'] == [] and g['return-type'] == r['return-type'] == [47, -1, 0, None], 'sandbox signature'
        assert man['pinned_functions'][L.SANDBOX]['index'] == sb and man['pinned_functions'][L.SANDBOX]['address'] == g['address']
        counts['S7_sandbox_signature_equal_RunEvent'] = 1
    if 'S8' in parts:
        # r21's two sites: their owners still call r21's replacements, which still call the originals
        for s_ in r21s:
            owner_ops = live_ops(nm, cv, s_['function'])
            assert owner_ops.count('CALLFUNC 0x%x' % s_['replacement_fid']) == 1 and owner_ops.count('CALLFUNC 0x%x' % s_['original_fid']) == 0, s_['function']
            assert 'CALLFUNC 0x%x' % s_['original_fid'] in live_ops(nm, cv, s_['replacement']), ('an r21 replacement no longer calls the original', s_['replacement'])
        # r22's two sites (the title): signature, uniqueness, the replacement adds to the original call
        assert sorted(s_['function'] for s_ in r22s) == sorted(R22_OWNERS), [s_['function'] for s_ in r22s]
        for s_ in r22s:
            o, r = nm['functions'][s_['original_fid']], nm['functions'][s_['replacement_fid']]
            assert [a['type'] for a in o['arguments']] == [a['type'] for a in r['arguments']] and o['return-type'] == r['return-type'], ('r22 site signature', s_['replacement'])
            assert s_['calls_of_original_in_function'] == 1, s_
            assert s_['function'] not in L.PINNED_ALL, ('an r22 site inside a pinned function', s_['function'])
            assert (s_['original'], s_['replacement']) == R22_OWNERS[s_['function']], s_
            assert L.raw_symbol(nm, s_['replacement_fid']) == s_['replacement'] and s_['replacement'].startswith('KR_C')
            assert s_['kind'] == 'CALLFUNC' and bytes.fromhex(s_['after']) == struct.pack('<Hi', 0x30, s_['replacement_fid'])
            assert 'CALLFUNC 0x%x' % s_['original_fid'] in live_ops(nm, cv, s_['replacement']), ('the replacement no longer calls the original', s_['replacement'])
            owner_ops = live_ops(nm, cv, s_['function'])
            assert owner_ops.count('CALLFUNC 0x%x' % s_['replacement_fid']) == 1 and owner_ops.count('CALLFUNC 0x%x' % s_['original_fid']) == 0, s_['function']
        # the title's wait: C_SceneTitle@Run waits with the C_SceneTitle@Update delegate (the frame the tick runs in) and calls
        # KR_CTitleServe right after it
        run_ops = live_ops(nm, cv, 'C_SceneTitle@Run')
        k = run_ops.index('CALLFUNC 0x%x' % L.fid_of(nm, 'AFL_Parts_WaitForClick'))
        assert run_ops[k - 4:k - 1] == ['PUSHSTRUCTPAGE', 'PUSH 0x%x' % L.fid_of(nm, 'C_SceneTitle@Update'), 'DG_NEW_FROM_METHOD'], run_ops[k - 4:k]
        assert run_ops[k + 3] == 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_CTitleServe'), run_ops[k:k + 4]
        for shim, tail in (('KR_T20StNext', ['PUSHSTRUCTPAGE', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StNextOf'), 'RETURN']),
                           ('KR_T20StPrev', ['PUSHSTRUCTPAGE', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StPrevOf'), 'RETURN']),
                           ('KR_T20StActive', ['PUSHSTRUCTPAGE', 'PUSHLOCALPAGE', 'PUSH 0x0', 'X_REF 0x1', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StActiveOf'), 'RETURN'])):
            got = live_ops(nm, cv, shim)
            assert got == tail, ('r20 CALLMETHOD shim body', shim, got)
        # V37 (static, r21 kept): the exit is the tail of the game's own 「게임 종료」
        ex = live_ops(nm, cv, 'KR_MExit')
        gx = live_ops(nm, cv, 'Ａ＿ゲーム終了')
        k = gx.index('CALLHLL system Exit 0')
        assert gx[k - 1] == 'PUSH 0x0' and gx[k + 1] == 'CALLHLL system Peek 0' and gx[k + 2].startswith('JUMP'), gx[k - 1:k + 3]
        assert ex[:2] == ['PUSH 0x0', 'CALLHLL system Exit 0'] and ex.count('CALLHLL system Peek 0') == 1 and ex.count('CALLHLL system Exit 0') == 1, ex
        # r22: the chart's wait = AFL_Parts_WaitForClick with the KR_CFrame delegate and key cancel (hand-written body)
        assert live_ops(nm, cv, 'KR_CWait') == ['PUSH -0x1' if 'PUSH -0x1' in live_ops(nm, cv, 'KR_CWait') else 'PUSH 0xffffffff', 'PUSH 0x%x' % L.fid_of(nm, 'KR_CFrame'),
                                                 'DG_NEW_FROM_METHOD', 'PUSH 0x1', 'CALLFUNC 0x%x' % L.fid_of(nm, 'AFL_Parts_WaitForClick'), 'RETURN'], live_ops(nm, cv, 'KR_CWait')
        # r22: the replay = the game's memory-mode path
        counts['S8_replay_ops_equal_ExecScene'] = replay_body_check(nm, cv)
        # reachable from the request consumers (home menu, title): no save / load / config / title call except the memory-mode
        # trio inside KR_CReplayRun; the only exit is KR_MExit
        roots = ['KR_MHomeRun', 'KR_MTick', 'KR_CTitleTick', 'KR_CTitleServe']
        reach = call_graph(nm, cv, roots, stop=('KR_CReplayRun',))
        bad = sorted(n for n in reach if n.startswith(SAVE_CALL_PREFIXES) or n == 'Ａ＿ゲーム終了')
        assert not bad, ('a save / load / config / title / confirming exit reachable from the request consumers', bad[:5])
        rr_calls = sorted({L.raw_symbol(nm, int(op.split()[1], 16)) for op in live_ops(nm, cv, 'KR_CReplayRun') if op.startswith('CALLFUNC ')})
        assert rr_calls == sorted(['LSys3xScript::GetLabelName', 'LSys3xScript::Prepare', 'LSys3xScript::RunEvent'] + MEMORY_MODE), rr_calls
        exits = sorted(n for n in reach if 'CALLHLL system Exit 0' in live_ops(nm, cv, n))
        assert exits == ['KR_MExit'], exits
        # the unlock flag file is read once, when the chart opens (KR_CChart); the chart never asks the per-save registration
        uid = L.fid_of(nm, 'KR_MUnlockAll')
        callers = sorted(n for n in reach if 'CALLFUNC 0x%x' % uid in live_ops(nm, cv, n))
        assert callers == ['KR_CChart'], callers
        counts['S8_r22_sites_checked'] = len(r22s)
        counts['S8_r21_sites_kept'] = len(r21s)
        counts['V37_exit_path_equals_game_exit_tail'] = 1
        counts['V37_functions_reachable_from_consumers'] = len(reach)
        counts['V35_unlock_flag_callers'] = len(callers)
    if 'S4' not in parts:
        return []
    vers = L.versions(L.base_paths()['raw'])
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
            assert f['index'] not in fw22 or start != f['address'], ('a saved frame is inside a function r22 forwards', name, f['name'])
            if f['index'] not in fw22:
                assert nm['functions'][f['index']] == f, ('saved frame function moved', name, f['name'])
            ad = rr['address']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes(new[16 + ad:16 + ad + 6]), ('saved return bytes differ', name, rr['name'][:40], hex(ad))
            live += int(start == f['address'])
            frames.append(dict(file=name, fid=f['index'], offset=rr['offset'], live=start == f['address'], function=L.raw_symbol(m, f['index']),
                               address=ad))
    counts['S4_saves'] = len({x['file'] for x in frames})
    counts['S4_frames'] = len(frames)
    counts['S4_frames_in_live_versions'] = live
    counts['S4_frames_in_KR_T9HomeCasual'] = sum(1 for x in frames if x['function'] == 'KR_T9HomeCasual')
    counts['S4_frames_in_KR_T18RunSandboxed'] = sum(1 for x in frames if x['function'] == L.SANDBOX)
    counts['S4_frames_in_r22_forwarded'] = sum(1 for x in frames if x['function'] in R22_FORWARD)
    counts['S4_frames_in_title_owners'] = sum(1 for x in frames if x['function'] in R22_OWNERS)
    counts['S4_frames_in_r21_owners'] = sum(1 for x in frames if x['function'] in R21_OWNERS)
    return frames


'''
s = s[:a] + NEW + s[b:]
p.write_text(s, 'utf8')
print('static checks replaced')
