"""Build the KR_G25 gallery-unlock candidate over the installed AIN (Claude Opus 5.5 (claude-opus-5-5), 2026-09-30).

  python build_gallery_unlock.py            build candidate/NightRemaster.ain (+ winmm.dll copy, manifest) and run the static gates

Base = the installed AIN abae5787... (current.json CALENDAR_SUMMARY_STACK_20260929_INSTALLED_NATIVE_PASS). Its meta dump and raw
code dump are copied from the stack top that was installed (same bytes, hashes pinned) and re-checked against a fresh dump.

The layer (kr_g25_gallery_unlock.jaf + two byte clones + five same-length edits):
  new   KR_G25All()                  flag for the galleries: 0 while the event calendar is open, else the cached menu-bar flag
        KR_G25Exist(string)          CG mode check: flag on -> true, else PassRegister.ExistText(0, name) (= the game's check)
        KR_G25SceneBase(int, int)    byte clone of the ORIGINAL N_ModeScene::CheckEnabelScenario (for KR_CGlobal)
        KR_G25SetUnlockBase(int)     byte clone of the r21 KR_MSetUnlock body
        KR_G25SetUnlock(int)         Base, then the cache = what was written (or what the file holds after a failed write)
        KR_G25NoteText()             holds the new 전체 개방 notice literal (STR0 row for KR_CDo)
  fwd   KR_MSetUnlock                one-line forwarder to KR_G25SetUnlock (index / arguments / locals / return kept)
  same-length (old CODE otherwise byte-identical, no function moves):
    A  CheckEnabelScenario  CALLHLL system IsDebugMode 0 (14)   -> CALLFUNC KR_G25All; PUSH 0; POP (6+6+2)
    B  CheckEnabelScenario  PUSHGLOBALPAGE; PUSH 0x134; X_REF 1 (.GLOBALREF N_ModeScene::DbgEnableAll, 14) -> PUSH 1; PUSH 0; POP
    C  KR_CGlobal           CALLFUNC N_ModeScene::CheckEnabelScenario -> CALLFUNC KR_G25SceneBase (operand)
    D  UpdateEnableCG       CALLFUNC Ａ＿ＣＧモード確認 -> CALLFUNC KR_G25Exist (operand)
    E  KR_CDo               S_PUSH <old unlock notice> -> S_PUSH <new notice row> (operand)
Why C: the brief placed the flag inside CheckEnabelScenario and relied on KR_CActive() for the calendar; but KR_CGlobal is also
reached OUTSIDE the chart (label getters KR_R29* / KR_S29* / KR_U29* call KR_P29Read -> KR_CGlobal from the in-game calendar,
where KR_CActive() is false), so the flag would have reached the in-game calendar's 151 recollection-cell events. With C the
calendar code never calls the flagged judgment at all; KR_G25All still returns 0 while the chart is open (brief contract).
"""
from pathlib import Path
import datetime, json, re, shutil, struct, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import g25lib as G
L = G.L

O = H
W = O / 'work' / 'build'
S = O / 'source'
C = O / 'candidate'
JAF = O / 'kr_g25_gallery_unlock.jaf'


def log(*a):
    print(*a, flush=True)


def snapshot(cur, rt):
    """source/: the installed AIN + winmm.dll + the base meta / raw dumps (hash-pinned copies of the installed stack top's)."""
    for d in (S, W, C, O / 'evidence', O / 'design'):
        d.mkdir(parents=True, exist_ok=True)
    pairs = {S / 'NightRemaster.ain': (rt / 'NightRemaster.ain', G.LIVE_AIN), S / 'winmm.dll': (rt / 'winmm.dll', G.LIVE_WINMM),
             S / 'base_meta.json': (G.STACK_TOP / 'work/build/candidate_meta.json', G.STACK_META_SHA),
             S / 'base_raw_code.jam': (G.STACK_TOP / 'work/build/candidate_raw_code.jam', G.STACK_RAW_SHA)}
    for dst, (src, want) in pairs.items():
        if dst.exists():
            assert L.sha(dst) == want, ('source copy changed', dst.name)
            continue
        assert L.sha(src) == want, ('pinned input moved', str(src))
        shutil.copy2(src, dst)
    assert L.sha(G.STACK_TOP / 'candidate/NightRemaster.ain') == G.LIVE_AIN, 'the stack top is not the installed AIN'
    ptr = S / 'source_pointer.json'
    if ptr.exists():
        assert L.readj(ptr) == cur, 'current.json moved since the snapshot: re-baseline'
    else:
        G.writej(ptr, cur)
    L.cmd('ain', 'dump', '-j', '-o', W / 'base_meta_check.json', S / 'NightRemaster.ain', timeout=900)
    assert L.read_meta(W / 'base_meta_check.json') == L.read_meta(S / 'base_meta.json'), 'base meta is not the dump of the installed AIN'
    (W / 'base_meta_check.json').unlink()


def one(ops, pred, what):
    hits = [(a, o) for a, o in ops if pred(o)]
    assert len(hits) == 1, (what, hits[:5], len(hits))
    return hits[0][0]


def plan(m, vers, rows, code, raw_path):
    """Every patch site from the live base code, with its exact original bytes; callers census."""
    name = G.names_of(m)
    for n, want in G.EXPECTED_FIDS.items():
        assert G.fid(m, n) == want, (n, G.fid(m, n), want)
    assert not any(n.startswith('KR_G25') for n in name), 'KR_G25 prefix already in the installed AIN'
    f = lambda n: m['functions'][G.fid(m, n)]
    sig = lambda x: ([a['type'] for a in x['arguments']], x['return-type'])
    assert sig(f(G.SCENE_CHECK)) == ([[10, -1, 0, None], [10, -1, 0, None]], [47, -1, 0, None])
    assert sig(f(G.CG_CHECK)) == ([[12, -1, 0, None]], [47, -1, 0, None])
    assert sig(f(G.SET_UNLOCK)) == ([[10, -1, 0, None]], [47, -1, 0, None])
    assert sig(f(G.UNLOCK_ALL)) == ([], [10, -1, 0, None]) and sig(f(G.CHART_ACTIVE)) == ([], [47, -1, 0, None])
    assert L.fix_name(m['globals'][0x134]['name']) == 'N_ModeScene::DbgEnableAll' and m['globals'][0x134]['type'][0] == 47
    sc = G.live_ops(m, vers, G.SCENE_CHECK)
    want_head = ['CALLHLL system IsDebugMode 0', 'IFZ', 'PUSHGLOBALPAGE', 'PUSH 0x134', 'X_REF 0x1', 'IFZ', 'PUSH 0x1', 'JUMP', 'PUSH 0x0',
                 'IFNZ', 'JUMP', 'PUSH 0x1', 'RETURN']
    got_head = [o if not o.startswith(('IFZ', 'IFNZ', 'JUMP')) else o.split()[0] for _, o in sc[:13]]
    assert got_head == want_head, got_head
    a, b = sc[0][0], sc[2][0]
    assert sc[1][0] == a + 14 and sc[5][0] == b + 14
    assert code[a:a + 14] == struct.pack('<Hiii', G.OP['CALLHLL'], 0, 6, 0)
    assert code[b:b + 14] == G.ins('PUSHGLOBALPAGE') + G.ins('PUSH', 0x134) + G.ins('X_REF', 1)
    lib = m['libraries'][0]
    assert lib['name'] == 'system' and lib['functions'][6]['name'] == 'IsDebugMode' and not lib['functions'][6]['arguments']
    scene_fid, cg_fid = G.fid(m, G.SCENE_CHECK), G.fid(m, G.CG_CHECK)
    cg = one(G.live_ops(m, vers, G.CG_UPDATE), lambda o: o == f'CALLFUNC 0x{cg_fid:x}', 'CG check in UpdateEnableCG')
    gl = one(G.live_ops(m, vers, G.CHART_GLOBAL), lambda o: o == f'CALLFUNC 0x{scene_fid:x}', 'scene check in KR_CGlobal')
    old_note = G.str_index(rows, G.OLD_NOTE)
    nd = one(G.live_ops(m, vers, G.NOTICE_OWNER), lambda o: o == f'S_PUSH 0x{old_note:x}', 'old notice in KR_CDo')
    for site, fn_ in ((cg, cg_fid), (gl, scene_fid)):
        assert code[site:site + 6] == G.ins('CALLFUNC', fn_)
    assert code[nd:nd + 6] == G.ins('S_PUSH', old_note)
    # census of the whole live code: callers of the two judgments, users of the old notice, every jump target
    census = {'scene_check_calls': [], 'cg_check_calls': {}, 'old_notice_pushes': [], 'debug_global_refs': []}
    targets = set()
    for ad, o, fid_ in G.live_instructions(m, raw_path):
        if o == f'CALLFUNC 0x{scene_fid:x}':
            census['scene_check_calls'].append(dict(function=name[fid_], site=ad))
        elif o == f'CALLFUNC 0x{cg_fid:x}':
            census['cg_check_calls'][name[fid_]] = census['cg_check_calls'].get(name[fid_], 0) + 1
        elif o == f'S_PUSH 0x{old_note:x}':
            census['old_notice_pushes'].append(dict(function=name[fid_], site=ad))
        elif o == 'PUSH 0x134':
            census['debug_global_refs'].append(dict(function=name[fid_], site=ad))
        z = re.match(r'(?:IFZ|IFNZ|JUMP) 0x([0-9a-f]+)$', o)
        if z:
            targets.add(int(z[1], 16))
    inside = sorted(t for t in targets if a < t < a + 14 or b < t < b + 14)
    assert not inside, ('a jump lands inside a replaced window', [hex(t) for t in inside])
    assert sorted(c['function'] for c in census['scene_check_calls']) == sorted(['C_SceneModeScene@ExecScene', 'C_SceneModeSceneSelectView@Init', G.CHART_GLOBAL]), census['scene_check_calls']
    assert census['cg_check_calls'] == {G.CG_UPDATE: 1, 'KR_T8CgCount': 90}, census['cg_check_calls']
    assert [c['function'] for c in census['old_notice_pushes']] == [G.NOTICE_OWNER]
    census['jump_targets_checked'] = len(targets)
    census['note'] = ('scene check: C_SceneModeScene@ExecScene (play), C_SceneModeSceneSelectView@Init (the select view; the '
                      'call follows a nested lambda body in the code) and KR_CGlobal (the calendar). CG check: the CG mode cell '
                      'update and the home panel CG rate KR_T8CgCount (90 direct calls, left alone). PUSH 0x134 sites = the '
                      'DbgEnableAll global (debug buttons / Run reset, all behind IsDebugMode or a reset to 0).')
    return dict(A=a, B=b, C=gl, D=cg, E=nd, old_note=old_note, census=census)


def main():
    t0 = datetime.datetime.now()
    cur, rt, got = G.assert_live()
    free = shutil.disk_usage('P:\\').free
    assert free >= 5 * 1024 ** 3, ('P: free space below 5 GB', free)
    snapshot(cur, rt)
    src = S / 'NightRemaster.ain'
    m = L.read_meta(S / 'base_meta.json')
    vers = L.versions(S / 'base_raw_code.jam')
    raw0, code0, n0 = G.code_of(src.read_bytes())
    rows0 = L.strings(raw0)[2]
    p = plan(m, vers, rows0, code0, S / 'base_raw_code.jam')
    log('sites', {k: hex(v) for k, v in p.items() if k in 'ABCDE'}, 'old notice row', hex(p['old_note']))
    # ---- the JAF: two stubs with the originals' exact signatures (bodies replaced by clones) + the layer
    fs = {n: m['functions'][G.fid(m, n)] for n in (G.SCENE_CHECK, G.SET_UNLOCK)}
    layer = JAF.read_text('utf-8')
    assert G.title_width(G.NEW_NOTE) <= 38 and json.dumps(G.NEW_NOTE, ensure_ascii=False) in layer
    for c in set(G.NEW_NOTE):
        assert c in L.proxy_alphabet() or c.encode('cp932'), c
    r21 = G.jaf_function(G.R21_JAF.read_text('utf-8'), 'KR_MSetUnlock')          # recorded: the readable body the clone carries
    jaf = G.stub('KR_G25SceneBase', fs[G.SCENE_CHECK]) + '\n' + G.stub('KR_G25SetUnlockBase', fs[G.SET_UNLOCK]) + '\n' + layer
    (W / 'helpers_readable.jaf').write_text('// stubs: bodies replaced by byte clones of N_ModeScene::CheckEnabelScenario / KR_MSetUnlock\n' + jaf, 'utf-8')
    (W / 'kr_msetunlock_r21_readable.jaf').write_text(r21 + '\n', 'utf-8')
    (W / 'helpers.jaf').write_text(L.jaf_literal_encode(L.strip_comments(jaf)), 'utf-8')
    decl = W / 'declared.ain'
    L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl, timeout=900)
    dm = L.read_meta(W / 'declared_meta.json')
    added = {L.raw_symbol(dm, f['index']): f['index'] for f in dm['functions'][len(m['functions']):]}
    assert set(added) == set(G.NEW), added
    for new, old in (('KR_G25SceneBase', G.SCENE_CHECK), ('KR_G25SetUnlockBase', G.SET_UNLOCK)):
        a_, b_ = m['functions'][G.fid(m, old)], dm['functions'][added[new]]
        strip = lambda xs: [(x['name'], x['type'], x.get('group-index')) for x in xs]      # name2 is the original compiler's own field
        assert strip(a_['arguments']) == strip(b_['arguments']) and strip(a_['variables']) == strip(b_['variables'])
        assert a_['return-type'] == b_['return-type'], (new, old)
    for new, old in (('KR_G25SetUnlock', G.SET_UNLOCK), ('KR_G25Exist', G.CG_CHECK)):
        a_, b_ = m['functions'][G.fid(m, old)], dm['functions'][added[new]]
        assert [x['type'] for x in a_['arguments']] == [x['type'] for x in b_['arguments']] and a_['return-type'] == b_['return-type'], new
    assert dm['functions'][added['KR_G25All']]['return-type'][0] == 10 and not dm['functions'][added['KR_G25All']]['arguments']
    # ---- bodies: compiled helpers, two byte clones, the forwarder
    patch = []
    for n in ('KR_G25All', 'KR_G25Exist', 'KR_G25SetUnlock', 'KR_G25NoteText'):
        L.cmd('ain', 'dump', '--function', n, '-o', W / f'{n}.jam', decl)
        patch.append(G.lowered(W / f'{n}.jam', n))
    clones = {}
    for new, old in (('KR_G25SceneBase', G.SCENE_CHECK), ('KR_G25SetUnlockBase', G.SET_UNLOCK)):
        path = W / f'{new}_original.jam'
        L.cmd('ain', 'dump', '--function', old, '-o', path, src)
        jam = L.clean(path.read_text('utf-8'), old)
        jam = re.sub(r'(?m)^FUNC .*$', f'FUNC {added[new]}', jam)
        jam = re.sub(r'(?m)^ENDFUNC .*$', f'ENDFUNC {new}', jam)
        patch.append(jam)
        clones[new] = old
    sfid = G.fid(m, G.SET_UNLOCK)
    assert [L.fix_name(x['name']) for x in m['functions'][sfid]['arguments']] == ['v']
    patch.append(f'FUNC {sfid}\n\t.LOCALREF v\n\tCALLFUNC KR_G25SetUnlock\n\tRETURN\nENDFUNC {G.SET_UNLOCK}\n')
    (W / 'patch.jam').write_text('\n'.join(patch), 'utf-8')
    cand = C / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', W / 'patch.jam', '-o', cand, decl, timeout=900)
    raw = bytearray(L.unpack(cand.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])       # function 0 keeps its original body
    assert bytes(raw[16:16 + n0]) == code0, 'the jaf / jam injection changed old CODE'
    rows1 = L.strings(bytes(raw))[2]
    assert rows1[:len(rows0)] == rows0
    new_note = G.str_index(rows1, G.NEW_NOTE)
    assert new_note >= len(rows0), 'the new notice is not a new STR0 row'
    ids = {n: added[n] for n in G.NEW}
    edits = [
        ('A', G.SCENE_CHECK, p['A'], code0[p['A']:p['A'] + 14], G.ins('CALLFUNC', ids['KR_G25All']) + G.ins('PUSH', 0) + G.ins('POP'),
         'CALLHLL system IsDebugMode 0 -> CALLFUNC KR_G25All; PUSH 0; POP'),
        ('B', G.SCENE_CHECK, p['B'], code0[p['B']:p['B'] + 14], G.ins('PUSH', 1) + G.ins('PUSH', 0) + G.ins('POP'),
         '.GLOBALREF N_ModeScene::DbgEnableAll -> PUSH 1; PUSH 0; POP'),
        ('C', G.CHART_GLOBAL, p['C'], G.ins('CALLFUNC', G.fid(m, G.SCENE_CHECK)), G.ins('CALLFUNC', ids['KR_G25SceneBase']),
         'CALLFUNC N_ModeScene::CheckEnabelScenario -> CALLFUNC KR_G25SceneBase'),
        ('D', G.CG_UPDATE, p['D'], G.ins('CALLFUNC', G.fid(m, G.CG_CHECK)), G.ins('CALLFUNC', ids['KR_G25Exist']),
         'CALLFUNC Ａ＿ＣＧモード確認 -> CALLFUNC KR_G25Exist'),
        ('E', G.NOTICE_OWNER, p['E'], G.ins('S_PUSH', p['old_note']), G.ins('S_PUSH', new_note),
         'S_PUSH old 전체 개방 notice -> S_PUSH new notice'),
    ]
    sites = []
    for tag, owner, at, before, after, what in edits:
        assert len(before) == len(after) and bytes(raw[16 + at:16 + at + len(before)]) == before == code0[at:at + len(before)], tag
        raw[16 + at:16 + at + len(after)] = after
        fo = m['functions'][G.fid(m, owner)]
        sites.append(dict(tag=tag, function=owner, fid=fo['index'], function_address=fo['address'], site=at, site_hex=hex(at),
                          offset_in_function=at - fo['address'], length=len(before), before=before.hex(), after=after.hex(), what=what))
    cand.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    # ---- gates
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', cand, timeout=900)
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', cand, timeout=900)
    nm = L.read_meta(W / 'candidate_meta.json')
    changed = [i for i, (x, y) in enumerate(zip(m['functions'], nm['functions'])) if x != y]
    assert changed == [sfid], [G.names_of(nm)[i] for i in changed]
    assert {k: v for k, v in m['functions'][sfid].items() if k != 'address'} == {k: v for k, v in nm['functions'][sfid].items() if k != 'address'}
    assert nm['functions'][sfid]['address'] >= n0
    assert [L.raw_symbol(nm, i) for i in range(len(m['functions']), len(nm['functions']))] == [L.raw_symbol(dm, i) for i in range(len(m['functions']), len(dm['functions']))]
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], ('metadata key changed', k)
    rawc, code1, n1 = G.code_of(cand.read_bytes())
    allowed = set()
    for s in sites:
        lo = s['site'] + (0 if s['tag'] in 'AB' else 2)
        allowed |= set(range(lo, s['site'] + s['length']))
    diff = [i for i in range(n0) if code0[i] != code1[i]]
    assert diff and set(diff) <= allowed, [hex(i) for i in diff if i not in allowed][:10]
    rows2 = L.strings(rawc)[2]
    assert rows2[:len(rows0)] == rows0, 'STR0 prefix changed'
    added_rows = [L.decode(r) for r in rows2[len(rows0):]]
    assert L.raw_messages(cand.read_bytes())[3] == L.raw_messages(src.read_bytes())[3], 'MSG1 changed'
    vers1 = L.versions(W / 'candidate_raw_code.jam')
    starts0 = sorted({v['start'] for vs in vers.values() for v in vs})
    starts1 = sorted({v['start'] for vs in vers1.values() for v in vs})
    pinned = {}
    for n in L.PINNED_ALL:
        i = G.fid(m, n)
        assert m['functions'][i] == nm['functions'][i], ('pinned entry changed', n)
        a0 = G.body_bytes(code0, starts0, m['functions'][i]['address'])
        a1 = G.body_bytes(code1, starts1, m['functions'][i]['address'])
        assert a0 == a1, ('pinned code changed', n)
        pinned[n] = dict(index=i, address=m['functions'][i]['address'], code_bytes=len(a0), bytes_differing=0)
    for s in sites:
        assert s['function'] not in L.PINNED_ALL
    # decoded views of the edited functions (candidate raw dump)
    fid1 = lambda n: G.fid(nm, n)
    sc1 = [o for _, o in G.live_ops(nm, vers1, G.SCENE_CHECK)]
    assert sc1[:4] == [f'CALLFUNC 0x{ids["KR_G25All"]:x}', 'PUSH 0x0', 'POP', sc1[3]] and sc1[3].startswith('IFZ')
    assert sc1[4:7] == ['PUSH 0x1', 'PUSH 0x0', 'POP'] and sc1[7].startswith('IFZ')
    sc0 = [o for _, o in G.live_ops(m, vers, G.SCENE_CHECK)]
    assert sc1[8:] == sc0[6:], 'CheckEnabelScenario changed beyond the two windows'
    assert len(sc1) == len(sc0) + 2
    # stack effect of the windows: CALLHLL IsDebugMode (+1) == CALLFUNC KR_G25All (+1) PUSH (+1) POP (-1);
    # PUSHGLOBALPAGE (+1) PUSH (+1) X_REF 1 (-2+1) == PUSH (+1) PUSH (+1) POP (-1)
    eff = {'CALLFUNC KR_G25All': +1, 'CALLHLL IsDebugMode': +1, 'PUSH': +1, 'POP': -1, 'PUSHGLOBALPAGE': +1, 'X_REF 1': -1}
    assert eff['CALLHLL IsDebugMode'] == eff['CALLFUNC KR_G25All'] + eff['PUSH'] + eff['POP']
    assert eff['PUSHGLOBALPAGE'] + eff['PUSH'] + eff['X_REF 1'] == eff['PUSH'] + eff['PUSH'] + eff['POP']
    one(G.live_ops(nm, vers1, G.CG_UPDATE), lambda o: o == f'CALLFUNC 0x{ids["KR_G25Exist"]:x}', 'KR_G25Exist in UpdateEnableCG')
    one(G.live_ops(nm, vers1, G.CHART_GLOBAL), lambda o: o == f'CALLFUNC 0x{ids["KR_G25SceneBase"]:x}', 'KR_G25SceneBase in KR_CGlobal')
    one(G.live_ops(nm, vers1, G.NOTICE_OWNER), lambda o: o == f'S_PUSH 0x{new_note:x}', 'new notice in KR_CDo')
    fw = [o for _, o in G.live_ops(nm, vers1, G.SET_UNLOCK)]
    assert fw[-2:] == [f'CALLFUNC 0x{ids["KR_G25SetUnlock"]:x}', 'RETURN'] and len(fw) <= 6, fw
    for new, old in clones.items():
        L.cmd('ain', 'dump', '--function', new, '-o', W / f'{new}_candidate.jam', cand)
        a_ = G.normalized_body((W / f'{new}_original.jam').read_text('utf-8'))
        b_ = G.normalized_body((W / f'{new}_candidate.jam').read_text('utf-8'))
        assert a_ == b_, ('clone differs from the original', new)
    audit = L.audit(cand, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    G.writej(W / 'native_opcode_audit.json', audit)
    shutil.copy2(S / 'winmm.dll', C / 'winmm.dll')
    assert L.sha(C / 'winmm.dll') == G.LIVE_WINMM
    frames = G.save_frames()
    touched = {G.SCENE_CHECK, G.CHART_GLOBAL, G.CG_UPDATE, G.NOTICE_OWNER, G.SET_UNLOCK}
    hit = [fr for fr in frames if 'name' in fr and fr['name'].split('(')[0] in touched]
    assert not hit, ('a saved frame sits in an edited function', hit[:3])
    live_code = code0
    for fr in frames:
        if 'address' in fr:
            assert live_code[fr['address']:fr['address'] + 6] == code1[fr['address']:fr['address'] + 6], fr
    ptr2 = G.runtime_now()
    assert ptr2[2]['NightRemaster.ain'] == G.LIVE_AIN and L.readj(L.CURRENT) == cur, 'the live build moved during the build'
    now = datetime.datetime.now().astimezone().isoformat()
    man = dict(
        tool=G.TOOL, kind='gallery_unlock_layer', status='GALLERY_UNLOCK_STAGED_NATIVE_PENDING', key=G.KEY, author=G.AUTHOR,
        provenance=dict(model='Claude Opus 5.5', model_id='claude-opus-5-5', designer='Claude Fable (brief 09-30)', builder=G.AUTHOR),
        built=now, seconds=(datetime.datetime.now() - t0).seconds,
        base=str(S / 'NightRemaster.ain'), base_sha256=G.LIVE_AIN, live_sha256=G.LIVE_AIN, live_manifest_sha256=G.LIVE_MANIFEST,
        live_status=G.LIVE_STATUS, base_meta_sha256=G.STACK_META_SHA, base_raw_sha256=G.STACK_RAW_SHA,
        files={n: dict(sha256=L.sha(C / n), size=(C / n).stat().st_size) for n in ('NightRemaster.ain', 'winmm.dll')},
        added_functions=ids, forwarded={G.SET_UNLOCK: dict(index=sfid, base_address=m['functions'][sfid]['address'],
                                                              address=nm['functions'][sfid]['address'], target='KR_G25SetUnlock')},
        clones={k: v for k, v in clones.items()}, same_length_sites=sites, notice=dict(old_row=p['old_note'], new_row=new_note,
                                                                                    old=G.OLD_NOTE, new=G.NEW_NOTE, width=G.title_width(G.NEW_NOTE)),
        str0_added=added_rows, census=p['census'], cache_variable=G.CACHE_VAR,
        gates=dict(metadata_changed=[G.SET_UNLOCK], functions_appended=len(ids), other_metadata_identical=sorted(k for k in m if k != 'functions'),
                   old_code_bytes_changed=len(diff), old_code_changes_only_at_sites=True, str0_prefix_exact=True, msg1_exact=True,
                   pinned=pinned, clones_op_identical=sorted(clones), forwarder_one_call=True, native_opcodes_supported=True,
                   dll_unchanged=True, no_jump_into_windows=True, saved_frames_checked=len([f for f in frames if 'address' in f]),
                   saved_frames_in_edited_functions=0, relocated_original_functions=0, serialized_schema_changes=0),
        music=dict(checks=G.SOUND_CHECKS, change='none (both are constant true in this build; verified by verify_gallery_unlock.py)'),
        installed=False, note='Not installed. publish_gallery_unlock.py --check only; --install needs the user\'s permission.')
    G.writej(C / 'manifest.json', man)
    G.writej(O / 'design' / 'sites.json', dict(sites=sites, census=p['census'], added=ids, notice=man['notice']))
    log(json.dumps(dict(candidate=str(cand), sha256=man['files']['NightRemaster.ain']['sha256'], added=ids,
                        sites=[(s['tag'], s['function'], s['site_hex']) for s in sites], str0_added=len(added_rows),
                        old_code_bytes_changed=len(diff), seconds=man['seconds']), ensure_ascii=False))
    return man


if __name__ == '__main__':
    main()
