"""Verification of the KR_G25 gallery-unlock candidate without the game (Claude Opus 5.5 (claude-opus-5-5), 2026-09-30).

  python verify_gallery_unlock.py            static re-check + VM checks + planted defects -> evidence/vm_verification.json
  python verify_gallery_unlock.py --fast     the same with one read-state (development)

Static (recomputed from the files, not trusted from the build): candidate = manifest, built over the live AIN; old CODE differs
only at the five declared sites; STR0 prefix and MSG1 identical; metadata: only KR_MSetUnlock (address) changed, six functions
appended; pinned functions (index, entry, every code byte) unchanged; the decoded edited instructions; clones op-identical; the
music checks constant true and untouched; no saved frame of the user's resume images in an edited function.

VM (g25vm.py runs the live code of BOTH AINs, the installed one as the reference, with the same world model):
  V1 recollection: CheckEnabelScenario on all 76 EX 回想 slots (+4 slots outside the table) x flag file (none / 0 / 1)
     x calendar (closed / open / open without root) x read state (none / pattern / all): flag 1 and calendar closed -> every slot
     open; everything else = the installed judgment. KR_G25SceneBase (the clone for the calendar) = the installed judgment always.
  V2 CG: UpdateEnableCG + IsOpened on all 60 CG閲覧 cells (90 CGs), same matrix: flag 1 + closed -> 60 open, EnableCGList =
     CGList (90); else = installed.
  V3 calendar: KR_CGlobal (and so KR_P29Read / KR_COpen / KR_CMark / the in-game label getters) on all 915 chart cells and all
     1,164 events, whole matrix: = installed everywhere (also outside the chart, where the in-game calendar reaches it).
  V4 cache / writer: the flag file is read once per session; KR_MSetUnlock (menu bar via KR_CDo, the chart buttons via
     KR_C24Toggle) refreshes the cache at once; a failed write leaves the cache = what the file holds; KR_G25All = 0 while the
     calendar is open; the new notice text, the revert notice unchanged.
  V5 planted defects (each must fail): calendar gate removed / cache not refreshed / CG check not rerouted / flag 0 opens /
     KR_CGlobal still on the flagged judgment (the brief's placement: in-game calendar leak) / DbgEnableAll gate kept.
  V6 in-game calendar labels: KR_T19EvShort / EvHead / EvWhen of all 1,164 events (their choice labels read KR_P29Read ->
     KR_CGlobal outside the chart too) = installed, flag 0 / 1, calendar closed / open. The brief placement (D5) changes them.
"""
from pathlib import Path
import argparse, collections, datetime, json, struct, sys, time
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import g25lib as G
import g25vm as V
L = G.L

R15 = G.STAGING / 'calendar_april_summary_20260929/design/r15_tables.json'
CHARTS = ['closed', 'open', 'open_no_root']
FLAGS = [None, 0, 1]


# ================================================================ static
def static():
    man = G.readj(H / 'candidate/manifest.json')
    cur, rt, got = G.assert_live()
    assert G.readj(H / 'source/source_pointer.json') == cur, 'current.json moved since the build'
    files = {n: L.sha(H / 'candidate' / n) for n in ('NightRemaster.ain', 'winmm.dll')}
    assert files == {n: v['sha256'] for n, v in man['files'].items()}, 'candidate files differ from the manifest'
    assert man['live_sha256'] == G.LIVE_AIN == L.sha(H / 'source/NightRemaster.ain') and files['winmm.dll'] == G.LIVE_WINMM
    src_b, cand_b = (H / 'source/NightRemaster.ain').read_bytes(), (H / 'candidate/NightRemaster.ain').read_bytes()
    raw0, code0, n0 = G.code_of(src_b)
    raw1, code1, n1 = G.code_of(cand_b)
    sites = man['same_length_sites']
    assert [s['tag'] for s in sites] == list('ABCDE')
    allowed = set()
    for s in sites:
        assert code0[s['site']:s['site'] + s['length']].hex() == s['before'] and code1[s['site']:s['site'] + s['length']].hex() == s['after'], s['tag']
        allowed |= set(range(s['site'], s['site'] + s['length']))
    diff = [i for i in range(n0) if code0[i] != code1[i]]
    assert set(diff) <= allowed and diff, [hex(i) for i in diff if i not in allowed][:5]
    rows0, rows1 = L.strings(raw0)[2], L.strings(raw1)[2]
    assert rows1[:len(rows0)] == rows0
    added_rows = [L.decode(r) for r in rows1[len(rows0):]]
    assert sorted(added_rows) == sorted([G.CACHE_VAR, G.NEW_NOTE]), added_rows
    assert L.raw_messages(src_b)[3] == L.raw_messages(cand_b)[3]
    m = L.read_meta(H / 'source/base_meta.json')
    nm = L.read_meta(H / 'work/build/candidate_meta.json')
    L.cmd('ain', 'dump', '-j', '-o', H / 'work/verify_candidate_meta.json', H / 'candidate/NightRemaster.ain', timeout=900)
    assert L.read_meta(H / 'work/verify_candidate_meta.json') == nm, 'work/build/candidate_meta.json is not the candidate meta'
    (H / 'work/verify_candidate_meta.json').unlink()
    changed = [G.names_of(m)[i] for i, (a, b) in enumerate(zip(m['functions'], nm['functions'])) if a != b]
    assert changed == [G.SET_UNLOCK], changed
    appended = G.names_of(nm)[len(m['functions']):]
    assert sorted(appended) == sorted(G.NEW), appended
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], k
    vers0 = L.versions(H / 'source/base_raw_code.jam')
    vers1 = L.versions(H / 'work/build/candidate_raw_code.jam')
    s0 = sorted({v['start'] for vs in vers0.values() for v in vs})
    s1 = sorted({v['start'] for vs in vers1.values() for v in vs})
    pinned = {}
    for n in L.PINNED_ALL:
        i = G.fid(m, n)
        assert m['functions'][i] == nm['functions'][i]
        b0 = G.body_bytes(code0, s0, m['functions'][i]['address'])
        assert b0 == G.body_bytes(code1, s1, m['functions'][i]['address']), n
        pinned[n] = len(b0)
    ids = man['added_functions']
    sc = [o for _, o in G.live_ops(nm, vers1, G.SCENE_CHECK)]
    assert sc[:3] == [f'CALLFUNC 0x{ids["KR_G25All"]:x}', 'PUSH 0x0', 'POP'] and sc[4:7] == ['PUSH 0x1', 'PUSH 0x0', 'POP']
    decoded = {s['tag']: [f'{hex(a)} {o}' for a, o in G.live_ops(nm, vers1, s['function']) if s['site'] <= a < s['site'] + s['length']]
               for s in sites}
    # music: both checks untouched and constant true (the only non-debug path ends in PUSH 1; IFNZ -> PUSH 1; RETURN)
    music = {}
    for n in G.SOUND_CHECKS:
        i = G.fid(m, n)
        b0 = G.body_bytes(code0, s0, m['functions'][i]['address'])
        assert b0 == G.body_bytes(code1, s1, nm['functions'][i]['address']) and m['functions'][i] == nm['functions'][i], n
        ops = [o for _, o in G.live_ops(m, vers0, n)]
        k = next(j for j in range(len(ops) - 1) if ops[j] == 'PUSH 0x1' and ops[j + 1].startswith('IFNZ'))
        tgt = int(ops[k + 1].split()[1], 16)
        after = [o for a, o in G.live_ops(m, vers0, n) if a >= tgt][:2]
        assert after == ['PUSH 0x1', 'RETURN'], (n, after)
        music[n] = dict(constant_true_at=hex([a for a, o in G.live_ops(m, vers0, n)][k]), ops_before=k,
                        debug_path='IsDebugMode && N_ModeSound::DbgEnableAll' if 'CALLHLL system IsDebugMode 0' in ops else None)
    # saved frames (user folder, read only)
    frames = G.save_frames()
    touched = {s['function'] for s in sites} | {G.SET_UNLOCK}
    in_edited = [f for f in frames if 'name' in f and f['name'].split('(')[0] in touched]
    assert not in_edited, in_edited[:3]
    for f in frames:
        if 'address' in f:
            assert code0[f['address']:f['address'] + 6] == code1[f['address']:f['address'] + 6], f
    return dict(files=files, old_code_bytes_changed=len(diff), sites={s['tag']: dict(function=s['function'], site=s['site_hex'],
                before=s['before'], after=s['after'], decoded=decoded[s['tag']]) for s in sites},
                str0_added=added_rows, msg1_exact=True, str0_prefix_exact=True, metadata_changed=changed, appended=appended,
                pinned_bytes=pinned, music=music, saved_frames=len([f for f in frames if 'address' in f]),
                saved_frame_files=sorted({f['save'] for f in frames}), saved_frames_in_edited_functions=0)


# ================================================================ VM
def codes():
    base = V.Code(H / 'source/NightRemaster.ain', H / 'source/base_meta.json', H / 'source/base_raw_code.jam')
    cand = V.Code(H / 'candidate/NightRemaster.ain', H / 'work/build/candidate_meta.json', H / 'work/build/candidate_raw_code.jam')
    return base, cand


def world(tables, base_vm, events, fast):
    """Read states: none / pattern / all (labels of the EX 回想 needEvNo, CG names, first messages of the calendar events)."""
    need = sorted(set(tables['memory'].values()))
    label = {n: base_vm.call('LSys3xScript::GetLabelName', n) for n in need}
    cgs = [c for row in tables['cg'] for c in row['cgs']]
    msgs = {n: base_vm.call('KR_T9EvMsg', n) for n in events}
    firsts = sorted({v for v in msgs.values() if v >= 0})
    states = {
        'none': dict(labels=set(), cg=set(), msgskip=set()),
        'pattern': dict(labels={label[n] for i, n in enumerate(need) if i % 2 == 0}, cg={c for i, c in enumerate(cgs) if i % 3 == 0},
                        msgskip={m_ for i, m_ in enumerate(firsts) if i % 3 == 1}),
        'all': dict(labels=set(label.values()), cg=set(cgs), msgskip=set(firsts)),
    }
    if fast:
        states = {'pattern': states['pattern']}
    return states, label, msgs


def model(tables, st, flag, chart):
    return V.Model(tables, labels=st['labels'], cg_seen=st['cg'], msgskip=st['msgskip'], flag=flag, chart=chart)


def slots(tables):
    valid = sorted((p - 1, i - 1) for p, i in tables['memory'])
    extra = [(0, 12), (6, 12), (7, 0), (0, 40)]
    assert not set(extra) & set(valid)
    return valid, extra


def v1_memory(vm_b, vm_c, tables, states):
    valid, extra = slots(tables)
    fails, table = [], []
    for sn, st in states.items():
        for flag in FLAGS:
            for chart in CHARTS:
                vm_b.model = model(tables, st, flag, chart)
                vm_c.model = model(tables, st, flag, chart)
                opened = 0
                for p, r in valid + extra:
                    b = vm_b.call(G.SCENE_CHECK, p, r)
                    c = vm_c.call(G.SCENE_CHECK, p, r)
                    clone = vm_c.call('KR_G25SceneBase', p, r)
                    want = 1 if (flag == 1 and chart != 'open') else b
                    if c != want:
                        fails.append(f'V1 {sn} flag={flag} chart={chart} slot=({p},{r}) cand={c} want={want} base={b}')
                    if clone != b:
                        fails.append(f'V1 clone {sn} flag={flag} chart={chart} slot=({p},{r}) clone={clone} base={b}')
                    opened += c if (p, r) in set(valid) else 0
                base_open = sum(vm_b.call(G.SCENE_CHECK, p, r) for p, r in valid)
                table.append(dict(state=sn, flag=flag, chart=chart, slots=len(valid), installed_open=base_open, candidate_open=opened,
                                  flag_file_reads=sum(1 for x in vm_c.model.reads if x.endswith('YoruKR_Chart.dat'))))
    return fails, table


def cg_cells(tables):
    return [[i, '', row['thumb'], list(row['cgs']), []] for i, row in enumerate(tables['cg'])]


def v2_cg(vm_b, vm_c, tables, states):
    fails, table = [], []
    upd_b, upd_c = vm_b.c.fid(G.CG_UPDATE), vm_c.c.fid(G.CG_UPDATE)
    op_b, op_c = vm_b.c.fid(G.CG_OPENED), vm_c.c.fid(G.CG_OPENED)
    for sn, st in states.items():
        for flag in FLAGS:
            for chart in CHARTS:
                vm_b.model = model(tables, st, flag, chart)
                vm_c.model = model(tables, st, flag, chart)
                cb, cc = cg_cells(tables), cg_cells(tables)
                ob = oc = eb = ec = 0
                for x, y in zip(cb, cc):
                    vm_b.run(upd_b, [], this=x)
                    vm_c.run(upd_c, [], this=y)
                    b_open, c_open = vm_b.run(op_b, [], this=x), vm_c.run(op_c, [], this=y)
                    ob += b_open
                    oc += c_open
                    eb += len(x[4])
                    ec += len(y[4])
                    if flag == 1 and chart != 'open':
                        if not (c_open == 1 and y[4] == y[3]):
                            fails.append(f'V2 {sn} flag=1 chart={chart} cell {y[0]} open={c_open} enabled={len(y[4])}/{len(y[3])}')
                    elif (c_open, y[4]) != (b_open, x[4]):
                        fails.append(f'V2 {sn} flag={flag} chart={chart} cell {y[0]} cand={c_open},{len(y[4])} base={b_open},{len(x[4])}')
                reads = sum(1 for r in vm_c.model.reads if r.endswith('YoruKR_Chart.dat'))
                if reads > 1:
                    fails.append(f'V2 {sn} flag={flag} chart={chart}: the flag file was read {reads} times for one gallery load')
                table.append(dict(state=sn, flag=flag, chart=chart, cells=len(cb), installed_open_cells=ob, candidate_open_cells=oc,
                                  installed_enabled_cgs=eb, candidate_enabled_cgs=ec, flag_file_reads=reads))
    return fails, table


def v3_calendar(vm_b, vm_c, tables, states, events, cells_only=False):
    fails, table = [], []
    ncell = vm_b.call('KR_CTabEnd', 9)
    cells = [vm_b.call('KR_CCellEv', i) for i in range(ncell)]
    assert cells == [vm_c.call('KR_CCellEv', i) for i in range(ncell)]
    memcells = [n for n in events if vm_b.call('KR_CMemCell', n) > 0]
    todo = sorted(set(cells) | (set() if cells_only else set(events)))
    for sn, st in states.items():
        for flag in FLAGS:
            for chart in CHARTS:
                vm_b.model = model(tables, st, flag, chart)
                vm_c.model = model(tables, st, flag, chart)
                diff = 0
                read_b = 0
                for n in todo:
                    b = vm_b.call(G.CHART_GLOBAL, n)
                    c = vm_c.call(G.CHART_GLOBAL, n)
                    read_b += b
                    if b != c:
                        diff += 1
                        if diff <= 5:
                            fails.append(f'V3 {sn} flag={flag} chart={chart} event {n}: KR_CGlobal cand={c} installed={b}')
                if diff > 5:
                    fails.append(f'V3 {sn} flag={flag} chart={chart}: {diff} events differ in all')
                table.append(dict(state=sn, flag=flag, chart=chart, events=len(todo), global_read_installed=read_b, differing=diff))
    return fails, table, dict(cells=ncell, events=len(events), memory_cell_events=len(memcells))


def v4_cache(vm_c, vm_b, tables, states):
    fails = []
    st = next(iter(states.values()))
    log = {}

    def fresh(flag, chart='closed'):
        vm_c.model = model(tables, st, flag, chart)
        return vm_c.model

    def reads(md):
        return sum(1 for r in md.reads if r.endswith('YoruKR_Chart.dat'))
    md = fresh(1)
    vals = [vm_c.call('KR_G25All') for _ in range(50)]
    if vals != [1] * 50 or reads(md) != 1:
        fails.append(f'V4a flag 1: values {set(vals)} reads {reads(md)} (want 1 / 1)')
    log['a_flag1_50_calls_reads'] = reads(md)
    r = vm_c.call(G.SET_UNLOCK, 0)
    n0 = reads(md)
    v = vm_c.call('KR_G25All')
    if not (r == 1 and md.vars.get(G.CACHE_VAR) == '0' and v == 0 and reads(md) == n0 and md.disk[md.flag_path] == 'YoruKR.Chart.1\r\n0\r\n'):
        fails.append(f'V4b set 0: ret {r} cache {md.vars.get(G.CACHE_VAR)!r} all {v} extra reads {reads(md) - n0}')
    r = vm_c.call(G.SET_UNLOCK, 1)
    v = vm_c.call('KR_G25All')
    if not (r == 1 and md.vars.get(G.CACHE_VAR) == '1' and v == 1):
        fails.append(f'V4c set 1: ret {r} cache {md.vars.get(G.CACHE_VAR)!r} all {v}')
    r = vm_c.call(G.SET_UNLOCK, 7)
    if not (r == 1 and md.vars.get(G.CACHE_VAR) == '1' and md.disk[md.flag_path].endswith('\r\n1\r\n')):
        fails.append('V4c2 set 7 (any non-zero) must write and cache 1')
    md.fail_write = True
    r = vm_c.call(G.SET_UNLOCK, 0)
    if not (r == 0 and md.vars.get(G.CACHE_VAR) == '1' and vm_c.call('KR_G25All') == 1):
        fails.append(f'V4d failed write of 0 over 1: ret {r} cache {md.vars.get(G.CACHE_VAR)!r}')
    md = fresh(None)
    md.fail_write = True
    r = vm_c.call(G.SET_UNLOCK, 1)
    if not (r == 0 and md.vars.get(G.CACHE_VAR) == '0' and vm_c.call('KR_G25All') == 0):
        fails.append(f'V4e failed write, no file: ret {r} cache {md.vars.get(G.CACHE_VAR)!r}')
    md = fresh(None)
    if vm_c.call('KR_G25All') != 0 or md.vars.get(G.CACHE_VAR) != '0':
        fails.append('V4f no file must be 0')
    # the menu-bar dispatch (KR_CDo) and the chart buttons (KR_C24Toggle) go through the forwarder
    md = fresh(0)
    vm_c.calls = []
    vm_c.call(G.NOTICE_OWNER, 'unlock_all', 1)
    notes = [x[1] for x in vm_c.calls if x[0] == 'notice']
    if notes != [G.NEW_NOTE] or md.vars.get(G.CACHE_VAR) != '1' or vm_c.call('KR_G25All') != 1:
        fails.append(f'V4g KR_CDo unlock_all: notices {notes} cache {md.vars.get(G.CACHE_VAR)!r}')
    vm_c.calls = []
    vm_c.call(G.NOTICE_OWNER, 'unlock_revert', 1)
    notes_c = [x[1] for x in vm_c.calls if x[0] == 'notice']
    vm_b.model = model(tables, st, 0, 'closed')
    vm_b.calls = []
    vm_b.call(G.NOTICE_OWNER, 'unlock_revert', 1)
    notes_b = [x[1] for x in vm_b.calls if x[0] == 'notice']
    vm_b.calls = []
    vm_b.call(G.NOTICE_OWNER, 'unlock_all', 1)
    notes_b_all = [x[1] for x in vm_b.calls if x[0] == 'notice']
    if notes_c != notes_b or md.vars.get(G.CACHE_VAR) != '0' or vm_c.call('KR_G25All') != 0:
        fails.append(f'V4h KR_CDo unlock_revert: {notes_c} vs installed {notes_b}, cache {md.vars.get(G.CACHE_VAR)!r}')
    if notes_b_all != [G.OLD_NOTE]:
        fails.append(f'V4h installed unlock_all notice is not the old text: {notes_b_all}')
    log['notices'] = dict(candidate_unlock_all=notes, candidate_unlock_revert=notes_c, installed_unlock_all=notes_b_all,
                          installed_unlock_revert=notes_b)
    vm_c.call('KR_C24Toggle', 1)
    t1 = (md.vars.get(G.CACHE_VAR), md.vars.get('YoruKR.C.All'), vm_c.call('KR_G25All'))
    vm_c.call('KR_C24Toggle', 0)
    t0 = (md.vars.get(G.CACHE_VAR), md.vars.get('YoruKR.C.All'), vm_c.call('KR_G25All'))
    if t1 != ('1', '1', 1) or t0 != ('0', '0', 0):
        fails.append(f'V4i chart buttons: after 1 {t1}, after 0 {t0}')
    # calendar open: 0 whatever the cache says; closing it gives the cached value back without a read
    md = fresh(1, 'open')
    a = vm_c.call('KR_G25All')
    md.set_chart('closed')
    b = vm_c.call('KR_G25All')
    md.set_chart('open')
    c = vm_c.call('KR_G25All')
    n = reads(md)
    if (a, b, c) != (0, 1, 0) or n != 1:
        fails.append(f'V4j calendar open/closed/open: {(a, b, c)} reads {n}')
    log['calendar_open_closed_open'] = [a, b, c]
    return fails, log


LABEL_GETTERS = ['KR_T19EvShort', 'KR_T19EvHead', 'KR_T19EvWhen']


def v6_labels(vm_b, vm_c, tables, states, events):
    """The in-game calendar's scene labels (the r19 getters over the N29 / S29 / R29 / L30 chain; the choice labels read KR_P29Read
    -> KR_CGlobal in any context): candidate = installed for every event, flag 0 / 1, calendar closed / open."""
    fails, table = [], []
    for sn, st in states.items():
        for flag, chart in ((0, 'closed'), (1, 'closed'), (1, 'open')):
            vm_b.model = model(tables, st, flag, chart)
            vm_c.model = model(tables, st, flag, chart)
            for g in LABEL_GETTERS:
                diff = [n for n in events if vm_b.call(g, n) != vm_c.call(g, n)]
                if diff:
                    fails.append(f'V6 {sn} flag={flag} chart={chart} {g}: {len(diff)} labels differ, e.g. E{diff[0]:05d}')
                table.append(dict(state=sn, flag=flag, chart=chart, getter=g, events=len(events), differing=len(diff)))
    return fails, table


def suite(vm_b, vm_c, tables, states, events, light=False):
    out = {}
    f1, t1 = v1_memory(vm_b, vm_c, tables, states)
    f2, t2 = v2_cg(vm_b, vm_c, tables, states)
    f3, t3, info3 = v3_calendar(vm_b, vm_c, tables, states, events, cells_only=light)
    f4, t4 = v4_cache(vm_c, vm_b, tables, states)
    out.update(V1=t1, V2=t2, V3=t3, V3_scope=info3, V4=t4)
    f6 = []
    if not light:
        f6, t6 = v6_labels(vm_b, vm_c, tables, states, events)
        out.update(V6=t6)
    return f1 + f2 + f3 + f4 + f6, out


def defects(cand, tables, states, events, base_vm):
    """Each planted defect is a single-instruction change of the candidate's code, run through the same suite (must fail)."""
    ids = {n: cand.fid(n) for n in G.NEW}
    fop = lambda name, op: [a for a, o in cand.ops[cand.fid(name)] if o == op]
    a_active = fop('KR_G25All', f'CALLFUNC 0x{cand.fid(G.CHART_ACTIVE):x}')
    a_set = fop('KR_G25SetUnlock', 'CALLHLL SystemService SystemVariable_Set 0')
    a_cg = fop(G.CG_UPDATE, f'CALLFUNC 0x{ids["KR_G25Exist"]:x}')
    a_unlock = fop('KR_G25All', f'CALLFUNC 0x{cand.fid(G.UNLOCK_ALL):x}')
    a_glob = fop(G.CHART_GLOBAL, f'CALLFUNC 0x{ids["KR_G25SceneBase"]:x}')
    man = G.readj(H / 'candidate/manifest.json')
    b = next(s for s in man['same_length_sites'] if s['tag'] == 'B')['site']
    for x in (a_active, a_set, a_cg, a_unlock, a_glob):
        assert len(x) == 1, x
    plan = {
        'D1 calendar gate removed (KR_G25All ignores KR_CActive)': {cand.fid('KR_G25All'): {a_active[0]: 'PUSH 0x0'}},
        'D2 cache not refreshed by KR_MSetUnlock': {cand.fid('KR_G25SetUnlock'): {a_set[0]: 'VM_POP2'}},
        'D3 CG judgment not rerouted (UpdateEnableCG keeps the game check)': {cand.fid(G.CG_UPDATE): {a_cg[0]: f'CALLFUNC 0x{cand.fid(G.CG_CHECK):x}'}},
        'D4 flag 0 but open (cache initialised without reading the file)': {cand.fid('KR_G25All'): {a_unlock[0]: 'PUSH 0x1'}},
        'D5 KR_CGlobal on the flagged judgment (the brief placement)': {cand.fid(G.CHART_GLOBAL): {a_glob[0]: f'CALLFUNC 0x{cand.fid(G.SCENE_CHECK):x}'}},
        'D6 DbgEnableAll gate kept (edit B missing)': {cand.fid(G.SCENE_CHECK): {b: 'PUSHGLOBALPAGE', b + 6: 'PUSH 0x134', b + 12: 'X_REF 0x1'}},
    }
    out = {}
    for name, mut in plan.items():
        vm_d = V.VM(cand, None, mutate=mut)
        detail = {}
        try:
            fails, res = suite(base_vm, vm_d, tables, states, events, light=not name.startswith('D5'))
            detail = dict(V3_differing=[r for r in res['V3'] if r['differing']], V6_differing=[r for r in res.get('V6', []) if r['differing']])
            err = None
        except AssertionError as e:
            fails, err = ['assertion: ' + repr(e)[:200]], repr(e)[:200]
        out[name] = dict(caught=bool(fails), failures=len(fails), first=fails[:3], error=err, **detail)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fast', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    rep = dict(author=G.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(timespec='seconds'))
    rep['static'] = static()
    print('static ok', rep['static']['old_code_bytes_changed'], 'bytes', flush=True)
    base, cand = codes()
    tables = V.ex_tables()
    events = sorted(int(n) for n in G.readj(R15)['events'])
    vm_b, vm_c = V.VM(base, None), V.VM(cand, None)
    states, labels, msgs = world(tables, vm_b, events, a.fast)
    rep['world'] = dict(ex=tables['source'], ex_sha256=tables['source_sha256'], memory_slots=len(tables['memory']),
                        cg_cells=len(tables['cg']), cg_names=sum(len(c['cgs']) for c in tables['cg']), music_rows=len(tables['music']),
                        events=len(events), states={k: {kk: len(vv) for kk, vv in v.items()} for k, v in states.items()})
    fails, out = suite(vm_b, vm_c, tables, states, events)
    rep.update(out)
    print('suite', len(fails), 'failures', round(time.time() - t0), 's', flush=True)
    rep['failures'] = fails
    rep['planted_defects'] = defects(cand, tables, states, events, vm_b)
    caught = {k: v['caught'] for k, v in rep['planted_defects'].items()}
    print('defects', caught, flush=True)
    rep['seconds'] = round(time.time() - t0, 1)
    rep['status'] = 'GALLERY_UNLOCK_VM_PASS' if not fails and all(caught.values()) and not a.fast else ('FAST_ONLY' if not fails else 'FAIL')
    rep['candidate_sha256'] = rep['static']['files']['NightRemaster.ain']
    G.writej(H / 'evidence/vm_verification.json', rep)
    print(json.dumps(dict(status=rep['status'], failures=fails[:10], seconds=rep['seconds']), ensure_ascii=False))
    assert rep['status'] in ('GALLERY_UNLOCK_VM_PASS', 'FAST_ONLY'), rep['status']


if __name__ == '__main__':
    main()
