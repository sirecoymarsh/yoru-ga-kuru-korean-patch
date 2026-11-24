# -*- coding: utf-8 -*-
"""Home 달성률 panel redesign, stage 1 - AIN candidate (Claude Opus 5.5, 2026-10-17). Stage only: never touches the runtime,
the saves or Codex files.

base = work/base (snapshot of the battle-pace install; snapshot_base.py). Output: candidate/NightRemaster.ain + manifest.json
(the PACT candidate comes from build_pact_home.py and must exist first).
Method (as build_pace_ain.py): jaf compiles the KR_HV* helpers (appended functions), then same-length CALLFUNC operand swaps
wire them in. Old CODE bytes may differ only at the swapped operands; MSG1 exact; STR0 prefix exact; function entries and all
other metadata identical; pinned functions (r18-r23 + auto-nav) byte-identical; native opcode audit against the shipped exe.
"""
import datetime, json, shutil, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvlib as L
import build_pact_home as PH

W = L.WORK / 'build'
O = HERE / 'candidate'
JAF_SRC = HERE / 'claude_home_panel.jaf'
# (owner, original callee, replacement): each owner calls the original exactly once in its live body
SITES = [
    ('KR_RateRender', 'KR_RateText', 'KR_HVText', 'panel values -> session variables, change key for the hidden body'),
    ('KR_RateRender', 'Ｐ＿テキスト設定', 'KR_HVSetText', 'body takes the key, then the owning AddArea instance is painted'),
    ('KR_T8HomeMenuOpen', 'KR_T8HomeClickable', 'KR_HVClickable', 'buttons take clicks while the home top menu waits'),
    ('KR_T8HomeMenuClose', 'KR_T8HomeClickable', 'KR_HVClickable', 'buttons stop taking clicks'),
    ('KR_T8HomeClick', 'KR_T8HomeRow', 'KR_HVRow', 'screen y -> character row / calendar button'),
    ('KR_T8HomeMenuClose', 'KR_T8CharMissingPage', 'KR_HVPick', 'calendar button -> KR_CDoHome("chart"); rows -> the old window'),
]


def log(*a):
    print(*a, flush=True)


def runtime_now():
    ptr, rt = L.runtime()
    got = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'NightRemasterPact.afa', 'NightRemasterEX.ex', 'winmm.dll']}
    return ptr, rt, got


def base_is_current(ptr, got):
    return (got['NightRemaster.ain'] == L.BASE_AIN_SHA and got['NightRemasterPact.afa'] == L.BASE_PACT_SHA
            and got['NightRemasterEX.ex'] == L.BASE_EX_SHA and got['winmm.dll'] == L.BASE_WINMM_SHA
            and ptr['status'] == L.BASE_STATUS and ptr['manifest_sha256'] == L.BASE_MANIFEST_SHA)


def gates():
    free = shutil.disk_usage('P:\\').free
    assert free >= 8 * 1024 ** 3, ('P: free space below 8 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase hvlib BASE_* first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    assert (O / 'NightRemasterPact.afa').exists(), 'run build_pact_home.py first'
    return ptr, rt, L.base_paths(), free


def code_of(ain_bytes):
    raw = L.unpack(ain_bytes)
    n = struct.unpack_from('<I', raw, 12)[0]
    return raw, raw[16:16 + n], n


def body_bytes(code, starts, address, limit):
    import bisect
    i = bisect.bisect_right(starts, address)
    end = starts[i] - 6 if i < len(starts) else limit
    return code[address - 6:end]


def sig(f):
    return ([a['type'] for a in f['arguments']], f['return-type'])


def plan_sites(m, raw_path):
    plan = []
    for owner, old, new, note in SITES:
        fid = L.fid_of(m, owner)
        assert owner not in L.PINNED_ALL, owner
        oldid = L.fid_of(m, old)
        ops = L.region_ops(raw_path, m, fid)
        hits = [i for i, (_, op) in enumerate(ops) if op == f'CALLFUNC 0x{oldid:x}']
        assert len(hits) == 1, (owner, old, len(hits))
        plan.append(dict(owner=owner, fid=fid, site=ops[hits[0]][0], original=old, replacement=new, note=note))
    return plan


def compile_and_patch(base, m, raw_path, jaf_text, plan):
    W.mkdir(parents=True, exist_ok=True)
    O.mkdir(parents=True, exist_ok=True)
    (W / 'helpers.jaf').write_text(jaf_text, 'utf8')
    decl = W / 'declared.ain'
    L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, base, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl)
    dm = L.read_meta(W / 'declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    assert all(n.startswith(L.PREFIX) for n in ids), [n for n in ids if not n.startswith(L.PREFIX)]
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
    for p in plan:
        oldid = L.fid_of(m, p['original'])
        newid = ids[p['replacement']]
        assert sig(dm['functions'][newid]) == sig(m['functions'][oldid]), (p['replacement'], sig(dm['functions'][newid]), sig(m['functions'][oldid]))
        ad = p['site']
        before = struct.pack('<Hi', 0x30, oldid)
        after = struct.pack('<Hi', 0x30, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (p['owner'], hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        fa = m['functions'][p['fid']]['address']
        sites.append(dict(function=p['owner'], fid=p['fid'], function_address=fa, site=ad, site_offset=ad - fa, kind='CALLFUNC',
                          original=p['original'], original_fid=oldid, replacement=p['replacement'], replacement_fid=newid,
                          before=before.hex(), after=after.hex(), operand_bytes=[ad + 2, ad + 6], note=p['note'], owner_is_original=True))
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, sites, oldn


def invariance(base, out, m, sites, oldn, bp):
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
    return nm, dict(original_function_entries_identical=True, other_metadata_identical=sorted(k for k in m if k != 'functions'),
                    old_code_bytes_changed=len(diff), old_code_changes_only_at_swapped_operands=True, MSG1_exact=True,
                    STR0_prefix_exact=True, STR0_added=len(sn) - len(so), functions_added=len(nm['functions']) - len(m['functions']),
                    pinned=pinned)


def main():
    t0 = datetime.datetime.now()
    ptr, rt, bp, free = gates()
    base = bp['ain']
    log('gates ok', L.BASE_AIN_SHA[:16], ptr['status'], 'P: free %.1f GB' % (free / 1024 ** 3))
    m = L.read_meta(bp['meta'])
    plan = plan_sites(m, bp['raw'])
    log('sites: %d' % len(plan))
    pev0 = L.readj(L.WORK / 'pact' / 'build_evidence.json')
    cal_text = next(r for r in pev0['rects'] if r['name'] == 'KR_HR_CalText')['rect']
    jaf = L.strip_comments(JAF_SRC.read_text('utf8'))
    jaf = jaf.replace('@@CALTEXT_X@@', str(int(round(cal_text[0])))).replace('@@CALTEXT_Y@@', str(int(round(cal_text[1]))))
    assert '@@' not in jaf, 'a layout placeholder left in the jaf'
    built = L.jaf_literal_encode(jaf)
    assert not [c for c in built if ('\uac00' <= c <= '\ud7a3')], 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, sites, oldn = compile_and_patch(base, m, bp['raw'], built, plan)
    log('compiled: %d functions added, %d call sites' % (len(ids), len(sites)))
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    nm, inv = invariance(base, out, m, sites, oldn, bp)
    log('invariance ok', {k: v for k, v in inv.items() if k != 'pinned'})
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    pev = L.readj(L.WORK / 'pact' / 'build_evidence.json')
    pact = O / 'NightRemasterPact.afa'
    assert L.sha(pact) == pev['outputs']['NightRemasterPact.afa'], 'PACT candidate differs from its build evidence'
    ptr2, rt2, got2 = runtime_now()
    assert base_is_current(ptr2, got2), ('runtime moved during the build', got2)
    man = dict(
        schema='yoru-home-panel.candidate.v1', status='HOME_PANEL_20261017_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, winmm_sha256=L.BASE_WINMM_SHA,
                  checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size),
               'NightRemasterPact.afa': dict(sha256=L.sha(pact), size=pact.stat().st_size)},
        pact_changed=True, pact_changed_entries=[PH.ENTRY], pact_new_parts=pev['made'], ex_changed=False, fnl_changed=False,
        winmm_changed=False, added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=[],
        same_length_sites=sites, relocated_original_functions=[], pinned_functions=inv['pinned'], invariance=inv,
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
        jaf_source_sha256=L.sha(JAF_SRC), build_script_sha256=L.sha(Path(__file__)), pact_build_script_sha256=L.sha(HERE / 'build_pact_home.py'))
    L.writej(O / 'manifest.json', man)
    log('STAGED', out, man['files']['NightRemaster.ain']['sha256'])


if __name__ == '__main__':
    try:
        main()
    except AssertionError as ex:
        print('ASSERT', str(ex)[-3000:])
        raise SystemExit(1)
