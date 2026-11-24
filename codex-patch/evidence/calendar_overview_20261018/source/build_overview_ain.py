# -*- coding: utf-8 -*-
"""Event-calendar overview, stage 2 - AIN candidate (Claude Opus 5.5, 2026-10-18). Stage only: never touches the runtime, the
saves or Codex files.

base = work/base (snapshot of the home-panel install; snapshot_base.py). Output: candidate/NightRemaster.ain + manifest.json.
Method (as build_home_ain.py): jaf compiles the KR_XV* helpers (appended functions), then same-length CALLFUNC operand swaps
wire them in. Old CODE bytes may differ only at the swapped operands; MSG1 exact; STR0 prefix exact; function entries and all
other metadata identical; pinned functions (r18-r23 + auto-nav) byte-identical; native opcode audit against the shipped exe.
The row of every event is baked into the jaf as an if-tree (schedule.json lanes, build_chart.lane_of), looked up by the event
each installed chart cell names (KR_CCellEv), so the cell order of later calendar layers does not matter.
"""
import datetime, json, shutil, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ovlib as L

W = L.WORK / 'build'
O = HERE / 'candidate'
JAF_SRC = HERE / 'claude_overview.jaf'
FLOW = HERE.parent.parent
CELLS = HERE.parent / 'r22_chart' / 'work' / 'build' / 'cells.json'
# (owner, original callee, replacement): each owner calls the original exactly once in its live body
SITES = [
    ('KR_CDo', 'KR_CChart', 'KR_XVChart', 'the chart request (title ctx 1, home ctx 2) opens the overview board first'),
    ('KR_C24Chart', 'KR_CWait', 'KR_XVWait', 'after a jump from the board the month view answers its first wait with that month tab'),
]
TAB_ENDS = [143, 259, 462, 518, 582, 640, 731, 802, 887, 915]   # KR_CTabEnd of the installed chart (r22)


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


def bake_lanes():
    """KR_XVLaneNo(no): an if-tree over every event of schedule.json -> row id (0 본편, 2-8 companions, 9 던전 동행, 10 회상,
    11 그 밖), as r22's table generator writes its tables. Every event the installed chart's cells name (r22 cells.json) must
    be in the tree."""
    sys.path.insert(0, str(FLOW / 'chart'))
    import build_chart as B
    s = B.load('schedule.json')
    code = {'main': 0, 'dungeon': 9, 'memory': 10, 'etc': 11}
    lane = {}
    for e in s['events']:
        ln = B.lane_of(e)
        lane[e['id']] = code[ln] if ln in code else int(ln[1:])
    rows = json.loads(CELLS.read_text('utf8'))['rows']
    assert len(rows) == TAB_ENDS[-1], len(rows)
    assert all(r['no'] in lane for r in rows), [r['no'] for r in rows if r['no'] not in lane][:5]
    pairs = sorted(lane.items())
    lines = ['int KR_XVLaneNo(int no) {']

    def rec(lo, hi, ind):
        if hi - lo <= 6:
            for k, v in pairs[lo:hi]:
                lines.append(f'{ind}if (no == {k}) return {v};')
            return
        mid = (lo + hi) // 2
        lines.append(f'{ind}if (no < {pairs[mid][0]}) {{')
        rec(lo, mid, ind + '    ')
        lines.append(f'{ind}}}')
        lines.append(f'{ind}else {{')
        rec(mid, hi, ind + '    ')
        lines.append(f'{ind}}}')
    rec(0, len(pairs), '    ')
    lines.append('    return 11;')
    lines.append('}')
    counts = {}
    for r in rows:
        k = f"{r['tab']}:{lane[r['no']]}"
        counts[k] = counts.get(k, 0) + 1
    return '\n'.join(lines), len(pairs), counts


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
    tree, events, counts = bake_lanes()
    jaf = L.strip_comments(JAF_SRC.read_text('utf8'))
    jaf = jaf.replace('@@LANE_TREE@@', tree)
    assert '@@' not in jaf, 'a placeholder left in the jaf'
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
    ptr2, rt2, got2 = runtime_now()
    assert base_is_current(ptr2, got2), ('runtime moved during the build', got2)
    man = dict(
        schema='yoru-calendar-overview.candidate.v1', status='CALENDAR_OVERVIEW_20261018_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, winmm_sha256=L.BASE_WINMM_SHA,
                  checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False,
        winmm_changed=False, added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=[],
        same_length_sites=sites, relocated_original_functions=[], pinned_functions=inv['pinned'], invariance=inv,
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
        jaf_source_sha256=L.sha(JAF_SRC), build_script_sha256=L.sha(Path(__file__)),
        baked=dict(events=events, lane_counts_r22_cells=counts, cells_source=str(CELLS), cells_sha256=L.sha(CELLS)))
    L.writej(O / 'manifest.json', man)
    log('STAGED', out, man['files']['NightRemaster.ain']['sha256'])


if __name__ == '__main__':
    try:
        main()
    except AssertionError as ex:
        print('ASSERT', str(ex)[-3000:])
        raise SystemExit(1)
