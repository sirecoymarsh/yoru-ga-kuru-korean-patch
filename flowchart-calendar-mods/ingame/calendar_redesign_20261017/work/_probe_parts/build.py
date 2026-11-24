def build_probe(key, work):
    src = O / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@KEY@@', key).replace('@@ITEMS@@', str(ITEMS_PAGE))
    assert '@@' not in jaf
    jaf = L.jaf_literal_encode(jaf)
    work.mkdir(parents=True, exist_ok=True)
    (work / 'probe.jaf').write_text(jaf, 'utf8')
    decl = work / 'probe_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'probe.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'probe_declared_meta.json', decl)
    dm = L.read_meta(work / 'probe_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    patch += [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]
    om = L.fid_of(m, 'C_SceneTrainingView@GetOnmouseChara')
    patch.append(f"FUNC {om}\n\tPUSH 0\n\tRETURN\nENDFUNC C_SceneTrainingView@GetOnmouseChara\n")
    for g in added:
        path = work / f"probe_{g['index']}.jam"
        L.cmd('ain', 'dump', '--function', g['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), g['name']))
    upd = L.fid_of(m, 'C_SelectDialog@_Update')
    path = work / f'original_{upd}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SelectDialog@_Update', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SelectDialog@_Update'), '\tCALLFUNC KR_ProbeDlgTick\n'))
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    RUN.mkdir(parents=True, exist_ok=True)
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_ProbeMain'])
    raw_code = L.WORK / 'build' / 'candidate_raw_code.jam'

    def swap(owner, old, new, expect=1, nth=0):
        fid = L.fid_of(m, owner)
        oldid = L.fid_of(m, old)
        newid = ids[new] if new in ids else L.fid_of(m, new)
        ops = L.region_ops(raw_code, m, fid)
        key2 = f'CALLFUNC 0x{oldid:x}'
        hits = [i for i, (_, op) in enumerate(ops) if op == key2]
        assert len(hits) == expect, (owner, old, len(hits))
        ad = ops[hits[nth]][0]
        assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, oldid), (owner, hex(ad))
        struct.pack_into('<Hi', raw, 16 + ad, 0x30, newid)
        return dict(owner=owner, site=ad, old=old, new=new)
    sites = [
        swap('KR_T9HomeCasual', 'KR_T18RunSandboxed', 'LSys3xScript::RunEvent'),
        swap('KR_T9HomeCasual', '■カジュアルモード設定呼び出し', 'KR_ProbeCasualOther'),
        swap('C_ConfigView@EventConfAsraDataForParts', 'KR_MDSeenToParts', 'KR_ProbeCfgToParts'),
    ]
    cfg = L.fid_of(m, '▲コンフィグ実行')
    start = L.fid_of(m, 'Ｓ＿コンフィグ／開始ページ')
    ops = L.region_ops(raw_code, m, cfg)
    n7 = 0
    for i, (ad, op) in enumerate(ops):
        if op == f'CALLFUNC 0x{start:x}':
            pad, pop = ops[i - 1]
            assert pop == 'PUSH 0x7', pop
            assert raw[16 + pad:16 + pad + 6] == struct.pack('<Hi', 0, 7)
            struct.pack_into('<Hi', raw, 16 + pad, 0, MODS_PAGE)
            n7 += 1
    assert n7 == 2, n7
    sites.append(dict(owner='▲コンフィグ実行', change='casual start page 7 -> %d (both)' % MODS_PAGE))
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    vers = L.versions(raw_code)
    waits = []
    for g in m['functions']:
        name = L.raw_symbol(m, g['index'])
        for v in [v for v in vers.get(g['index'], []) if v['start'] == g['address']]:
            for ad, op in v['ops']:
                if op != f'CALLFUNC 0x{wait:x}':
                    continue
                assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, wait)
                if name in LIVE_WAITS:
                    waits.append((name, 'live'))
                    continue
                target = ids['KR_ProbeMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_ProbeWaitExit']
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, target)
                waits.append((name, 'message click-through' if target == ids['KR_ProbeMsgWait'] else 'exit'))
    live = sorted(n for n, k in waits if k == 'live')
    assert live == sorted(LIVE_WAITS), live
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(sites=sites, waits=len(waits), probe_sha256=L.sha(out))


