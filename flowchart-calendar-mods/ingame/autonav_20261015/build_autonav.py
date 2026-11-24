# -*- coding: utf-8 -*-
"""Auto-nav layer candidate build (Claude Opus 5.5, 2026-10-15). Stage only: never touches the runtime, the saves or Codex files.

base = work/base (snapshot of the runtime current.json points at; snapshot_base.py). Output: candidate/NightRemaster.ain + manifest.
Method: jaf declares/compiles the KR_AN* helpers (appended functions), three bodies are hand-written jam, then same-length operand
swaps (SWAPS) wire them in. Old CODE bytes may differ only at the swapped operands; MSG1 exact; STR0 prefix exact; function entries
and all other metadata identical; pinned functions byte-identical; native opcode audit against the shipped exe.
"""
import collections, datetime, json, re, shutil, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import anlib as L

W = L.WORK / 'build'
O = HERE / 'candidate'
JAF_SRC = HERE / 'claude_autonav.jaf'
CHOICES = HERE / 'choice_table.json'
SCHEDULE = L.FLOW / 'graph' / 'schedule.json'
NAME_TO_T = {'이즈미': 2, '쿄카': 3, '마나미': 4, '마코토': 5}
EVENTS = [58, 63, 69, 104, 258, 260, 322, 611, 10021, 20041, 20081, 20164, 30001, 30021, 30152, 40021, 40041, 40043, 40061]
STAR = dict(BLINK_MS=1000, GOLD_G=55, GOLD_B=195, GLOW_W=720, GLOW_PAD=10, GLOW_X='-10.0', GLOW_A0=0, GLOW_A1=110,
            BOX_R=150, BOX_G=110, BOX_B=20, ROW_H=40)
ROW_H, STAR_DY = 40, 0
JAM_BODIES = ['KR_ANInfoCreate', 'KR_ANDateGet', 'KR_ANOpeningQ']

# (owner, kind, original fid or name, occurrence, replacement, expected ops before, expected ops after) -- ops compared by name only
SWAPS = [('ＥＶ／元／E%05d' % e, 'call', '■選択メッセージ／実行', 0, 'KR_AN_E%05d' % e,
          ['PUSHLOCALPAGE', 'PUSH', 'PUSH', 'PUSH'], ['X_ASSIGN', 'POP']) for e in EVENTS] + [
    ('C_SelectMessage@CreateParts', 'method', 'C_SelectMessInfo@CreateParts', 0, 'KR_ANInfoCreate',
     ['PUSHLOCALPAGE', 'PUSH', 'X_REF', 'X_REF'], ['PUSHLOCALPAGE', 'PUSH', 'X_REF', 'CALLMETHOD']),
    ('C_SelectMessage@Update', 'call', '■バックログ起動監視', 0, 'KR_ANSelFrame', [], ['IFNZ', 'JUMP', 'RETURN']),
    ('C_SceneTraining@_UpdateInputPartner', 'call', 'C_UserInputManager::IsClickCancelOtherMouse', 0, 'KR_ANTrainFrame',
     ['PUSH', 'IFNZ', 'JUMP', 'RETURN'], ['IFNZ', 'JUMP', 'JUMP']),
    ('C_SceneTraining@RunSelectPartner', 'call', '■選択ダイアログ／実行', 0, 'KR_ANTrainConfirm',
     ['PUSHLOCALPAGE', 'PUSH', 'PUSH', 'PUSH'], ['X_ASSIGN', 'POP']),
    ('L_EventCall::Check', 'method', 26479, 0, 'KR_ANDateGet',
     ['PUSHGLOBALPAGE', 'PUSH', 'PUSHGLOBALPAGE', 'PUSH', 'X_REF'], ['CALLMETHOD', 'PUSHLOCALPAGE', 'PUSH', 'X_REF']),
    ('C_SceneGame@Run', 'method', 26529, 0, 'KR_ANOpeningQ', ['PUSHGLOBALPAGE', 'PUSH', 'X_REF'], ['CALLMETHOD', 'IFNZ', 'JUMP']),
    # the options' Mods page: the last existence check (KR_CheatSpeedValue) of each per-frame sync runs on every path
    ('C_ConfigView@EventConfAsraDataForParts', 'call', 'AFL_Activity_IsExistPartsByName', 10, 'KR_ANCfgSeenToParts',
     ['PUSHSTRUCTPAGE', 'PUSH', 'X_REF', 'A_REF', 'S_PUSH'], ['IFZ', 'PUSHSTRUCTPAGE']),
    ('C_ConfigView@EventConfPartsDataForAsra', 'call', 'AFL_Activity_IsExistPartsByName', 12, 'KR_ANCfgSeenToAsra',
     ['PUSHSTRUCTPAGE', 'PUSH', 'X_REF', 'A_REF', 'S_PUSH'], ['IFZ', 'PUSHSTRUCTPAGE']),
]
EXPECTED_HITS = {('L_EventCall::Check', 26479): 2,
                 ('C_ConfigView@EventConfAsraDataForParts', 'AFL_Activity_IsExistPartsByName'): 11,
                 ('C_ConfigView@EventConfPartsDataForAsra', 'AFL_Activity_IsExistPartsByName'): 13}
LAST_ON_EVERY_PATH = {'C_ConfigView@EventConfAsraDataForParts', 'C_ConfigView@EventConfPartsDataForAsra'}


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


def gates():
    free = shutil.disk_usage('P:\\').free
    assert free >= 8 * 1024 ** 3, ('P: free space below 8 GB', free)
    ptr, rt, got = runtime_now()
    assert base_is_current(ptr, got), ('runtime moved: rebase anlib BASE_* first', got, ptr['status'])
    assert L.sha(Path(ptr['manifest'])) == ptr['manifest_sha256'], 'current.json manifest hash mismatch'
    bp = L.base_paths()
    return ptr, rt, bp, free


def code_of(ain_bytes):
    raw = L.unpack(ain_bytes)
    n = struct.unpack_from('<I', raw, 12)[0]
    return raw, raw[16:16 + n], n


def body_bytes(code, starts, address, limit):
    import bisect
    i = bisect.bisect_right(starts, address)
    end = starts[i] - 6 if i < len(starts) else limit
    return code[address - 6:end]


# ---------------------------------------------------------------- data
def load_choices():
    rows = json.loads(CHOICES.read_text('utf8'))
    out = {}
    for r in rows:
        assert r['id'] in EVENTS, r['id']
        nos = [o['no'] for o in r['opts']]
        assert nos == list(range(1, len(nos) + 1)), (r['id'], nos)
        picks = {NAME_TO_T[k]: v for k, v in r['picks'].items()}
        assert set(picks) == {2, 3, 4, 5} and all(v in nos for v in picks.values()), (r['id'], picks)
        out[r['id']] = picks
    assert sorted(out) == sorted(EVENTS), sorted(set(EVENTS) - set(out))
    # four-way person choices: the person's own row (1 izumi .. 4 makoto)
    for e in (322, 30152, 611):
        assert out[e] == {2: 1, 3: 2, 4: 3, 5: 4}, (e, out[e])
    return out


def load_needs():
    sched = json.loads(SCHEDULE.read_text('utf8'))
    start, end = tuple(sched['calendar']['start']), tuple(sched['calendar']['end'])
    rows = []
    for e in sched['events']:
        for t in e.get('triggers') or []:
            for g in t.get('feeling_gate') or []:
                if g['op'] != '>=':
                    continue
                k = t.get('kind')
                if k == 'conditional':
                    f, l = tuple(t['date_from']), tuple(t['date_to'])
                elif k == 'scheduled_special':
                    f = l = tuple(t['date'])
                elif k == 'after_training_priority':
                    a = re.findall(r'IsTodayOrAfter\((\d+), (\d+)\)', t['condition_expr'])
                    b = re.findall(r'IsTodayOrBefore\((\d+), (\d+)\)', t['condition_expr'])
                    f = (int(a[0][0]), int(a[0][1])) if a else start
                    l = (int(b[0][0]), int(b[0][1])) if b else end
                else:
                    raise AssertionError(('gate kind', k))
                rows.append(dict(person=g['person'], value=g['value'], frm=f[0] * 100 + f[1], last=l[0] * 100 + l[1], ev=e['id'], kind=k))
    assert len(rows) == 20 and all(2 <= r['person'] <= 5 for r in rows), len(rows)
    return sorted(rows, key=lambda r: (r['person'], r['frm'], r['value']))


def gen_tables(choices, needs):
    out = []
    lines = ['int KR_ANPick(int ev, int t) {']
    for e in EVENTS:
        p = choices[e]
        lines.append('    if (ev == %d) {' % e)
        for t in (2, 3, 4, 5):
            lines.append('        if (t == %d) return %d;' % (t, p[t]))
        lines.append('        return 0;')
        lines.append('    }')
    lines.append('    return 0;')
    lines.append('}')
    out.append('\n'.join(lines))
    lines = ['int KR_ANNeed(int t, int d) {', '    int n = 0;']
    for r in needs:
        lines.append('    if (t == %d && d >= %d && d <= %d && n < %d) n = %d;   // E%05d %s' % (r['person'], r['frm'], r['last'], r['value'], r['value'], r['ev'], r['kind']))
    lines.append('    return n;')
    lines.append('}')
    out.append('\n'.join(lines))
    lines = ['float KR_ANRowY(int id) {']
    for i in range(1, 5):
        lines.append('    if (id == %d) return %s;' % (i, '%.1f' % ((i - 1) * ROW_H + STAR_DY)))
    lines.append('    return %s;' % ('%.1f' % STAR_DY))
    lines.append('}')
    out.append('\n'.join(lines))
    for e in EVENTS:
        out.append('int KR_AN_E%05d(bool c, int tm) { return KR_ANSelect(%d, c, tm); }' % (e, e))
    return '\n\n'.join(out) + '\n'


def check_alphabet(texts):
    alpha = L.proxy_alphabet()
    bad = []
    for t in texts:
        for c in t:
            if '\uac00' <= c <= '\ud7a3' and c not in alpha:
                bad.append((t, c))
            elif not ('\uac00' <= c <= '\ud7a3'):
                try:
                    c.encode('cp932')
                except UnicodeEncodeError:
                    bad.append((t, c))
    return bad


def jaf_strings(src):
    return [json.loads(z) for z in re.findall(r'"(?:[^"\\]|\\.)*"', src)]


# ---------------------------------------------------------------- compile and patch
def sig(f):
    return ([a['type'] for a in f['arguments']], f['return-type'])


def jam_bodies(m, ids):
    info_create = L.fid_of(m, 'C_SelectMessInfo@CreateParts')
    info_id = 27943                       # C_SelectMessInfo@Id::get (two entries share the name; Update calls 27943)
    assert L.raw_symbol(m, info_id) == 'C_SelectMessInfo@Id::get' and m['functions'][info_id]['return-type'][0] == 10, m['functions'][info_id]['return-type']
    b = {}
    # this = the answer row (C_SelectMessInfo): original CreateParts(parentId) result stays on the stack and is returned
    b['KR_ANInfoCreate'] = (f"\t.LOCALREF parentId\n\tCALLFUNC KR_ANRowBegin\n\tPUSHSTRUCTPAGE\n\tPUSH {info_create}\n\t.LOCALREF parentId\n\tCALLMETHOD 1\n"
                            f"\tPUSHSTRUCTPAGE\n\tPUSH {info_id}\n\tCALLMETHOD 0\n\t.LOCALREF parentId\n\tCALLFUNC KR_ANInfoMade\n\tRETURN\n")
    # this = Flags (C_GameFlags): top up first, then the original Date::get reference is returned as is
    b['KR_ANDateGet'] = "\tCALLFUNC KR_ANTopUp\n\tPUSHSTRUCTPAGE\n\tPUSH 26479\n\tCALLMETHOD 0\n\tRETURN\n"
    # this = Flags: ask the auto-nav target on a new game, then the original IsPlayOpening::get value
    b['KR_ANOpeningQ'] = "\tCALLFUNC KR_ANNewGame\n\tPUSHSTRUCTPAGE\n\tPUSH 26529\n\tCALLMETHOD 0\n\tRETURN\n"
    assert L.raw_symbol(m, 26479) == 'C_GameFlags@Date::get' and L.raw_symbol(m, 26529) == 'C_GameFlags@IsPlayOpening::get'
    out = {}
    for name, body in b.items():
        out[ids[name]] = f"FUNC {ids[name]}\n{body}ENDFUNC {name}\n"
    return out


def target_fid(m, t):
    return t if isinstance(t, int) else L.fid_of(m, t)


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
    assert all(n.startswith(L.PREFIX) for n in ids), [n for n in ids if not n.startswith(L.PREFIX)]
    assert set(JAM_BODIES) <= set(ids), set(JAM_BODIES) - set(ids)
    changed = [f['index'] for f, g in zip(m['functions'], dm['functions']) if f != g and f['index'] != 0]
    assert not changed, ('the jaf declaration touched existing functions', changed[:5])
    jams = jam_bodies(m, ids)
    patch = []
    for f in added:
        if f['index'] in jams:
            patch.append(jams[f['index']])
            continue
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
    for owner, kind, oldfn, nth, newfn, before_ops, after_ops in SWAPS:
        fid = L.fid_of(m, owner)
        oldid = target_fid(m, oldfn)
        newid = ids[newfn]
        assert sig(dm['functions'][newid]) == sig(m['functions'][oldid]), (newfn, sig(dm['functions'][newid]), sig(m['functions'][oldid]))
        ops = L.region_ops(raw_path, m, fid)
        opcode, key = (0x30, f'CALLFUNC 0x{oldid:x}') if kind == 'call' else (0x00, f'PUSH 0x{oldid:x}')
        hits = [i for i, (ad, op) in enumerate(ops) if op == key]
        assert len(hits) == EXPECTED_HITS.get((owner, oldfn), 1), (owner, oldfn, len(hits))
        i = hits[nth]
        got_before = [op.split()[0] for _, op in ops[max(0, i - len(before_ops)):i]]
        got_after = [op.split()[0] for _, op in ops[i + 1:i + 1 + len(after_ops)]]
        assert got_before == before_ops and got_after == after_ops, ('site shape', owner, got_before, got_after)
        if owner in LAST_ON_EVERY_PATH:
            # every jump before the site lands at or before it, and the only RETURN is the body's last op: all paths reach it
            assert nth == len(hits) - 1, (owner, nth, len(hits))
            for _, op in ops[:i]:
                z = re.match(r'(IFZ|IFNZ|JUMP) 0x([0-9a-f]+)$', op)
                if z:
                    assert int(z[2], 16) <= ops[i][0], ('a jump past the site', owner, op)
            rets = [k for k, (_, op) in enumerate(ops) if op == 'RETURN']
            assert rets == [len(ops) - 1], (owner, rets)
        if kind == 'method':
            nargs = len([a for a in m['functions'][oldid]['arguments'] if a['type'][0] != 0])
            call = next(op for _, op in ops[i + 1:i + 8] if op.startswith('CALLMETHOD'))
            assert call == f'CALLMETHOD 0x{nargs:x}', (owner, call, nargs)
        ad = ops[i][0]
        before = struct.pack('<Hi', opcode, oldid)
        after = struct.pack('<Hi', opcode, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (owner, hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=owner, fid=fid, function_address=m['functions'][fid]['address'], site=ad,
                          site_offset=ad - m['functions'][fid]['address'],
                          kind='CALLMETHOD target (PUSH operand)' if kind == 'method' else 'CALLFUNC',
                          original=L.raw_symbol(m, oldid), original_fid=oldid, replacement=newfn, replacement_fid=newid,
                          before=before.hex(), after=after.hex(), operand_bytes=[ad + 2, ad + 6], occurrence=nth,
                          calls_of_original_in_function=len(hits), owner_is_original=not owner.startswith('KR_')))
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
    raw_text = Path(bp['raw']).read_text('utf8')
    for part in (2026101503,):
        assert ('PUSH 0x%x' % part) not in raw_text, ('part number used in the base', part)
    choices = load_choices()
    needs = load_needs()
    log('choices', len(choices), 'needs', len(needs), collections.Counter(r['person'] for r in needs))
    jaf = JAF_SRC.read_text('utf8')
    assert jaf.count('/*TABLES*/') == 1
    jaf = jaf.replace('/*TABLES*/', gen_tables(choices, needs))
    for k, v in STAR.items():
        jaf = jaf.replace('@@%s@@' % k, str(v))
    assert '@@' not in jaf, re.findall(r'@@\w+@@', jaf)
    (W.mkdir(parents=True, exist_ok=True), (W / 'helpers_readable.jaf').write_text(jaf, 'utf8'))
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
    nm, inv = invariance(base, out, m, sites, oldn, bp)
    log('invariance ok', {k: v for k, v in inv.items() if k != 'pinned'})
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    ptr2, rt2, got2 = runtime_now()
    assert base_is_current(ptr2, got2), ('runtime moved during the build', got2)
    man = dict(
        schema='yoru-autonav.candidate.v1', status='AUTONAV_20261015_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, winmm_sha256=L.BASE_WINMM_SHA,
                  checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False, winmm_changed=False,
        data=dict(choice_table_sha256=L.sha(CHOICES), schedule_sha256=L.sha(SCHEDULE), events=EVENTS, needs=needs, star=STAR,
                  row_h=ROW_H, star_dy=STAR_DY, wait_ms=20000, storage='N_ScenarioRegister _EV_TABLE name KR_AUTONAV_<2..5>',
                  session_variables='YoruKR.AN.*'),
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=JAM_BODIES,
        same_length_sites=sites, relocated_original_functions=[], pinned_functions=inv['pinned'], invariance=inv,
        parts=dict(choice_glow_band=2026101503, choice_row='the answer row parts found as new children of 矩形_項目位置 (tinted)',
                   training='the target portrait (parent of the r20 box, tinted) and the r20 box (add colour)'),
        native_opcode_audit=dict(active_functions=audit['active_functions'], instruction_sites=audit['instruction_sites'],
                                 all_active_opcodes_supported=True, engine_sha256=audit['engine_sha256']),
        new_globals=0, new_struct_members=0, serialized_schema_changes=0, translator_model=L.AUTHOR,
        jaf_source_sha256=L.sha(JAF_SRC), build_script_sha256=L.sha(Path(__file__)))
    L.writej(O / 'manifest.json', man)
    log('STAGED', out, man['files']['NightRemaster.ain']['sha256'])


if __name__ == '__main__':
    try:
        main()
    except AssertionError as ex:
        print('ASSERT', str(ex)[-3000:])
        raise SystemExit(1)
