# -*- coding: utf-8 -*-
"""Mods page layer AIN candidate (Claude Opus 5.5, 2026-10-15). Stage only: never touches the runtime, the saves or Codex files.

base = work/base (snapshot of the auto-nav install; snapshot_base.py). Output: candidate/NightRemaster.ain + manifest.json.
Method (as build_autonav.py): jaf compiles the KR_MD* helpers (appended functions), then two same-length CALLFUNC operand swaps
wire them in. Old CODE bytes may differ only at the swapped operands; MSG1 exact; STR0 prefix exact; function entries and all
other metadata identical; pinned functions (r18-r23 + auto-nav) byte-identical; native opcode audit against the shipped exe.
"""
import datetime, json, re, shutil, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mdlib as L

W = L.WORK / 'build'
O = HERE / 'candidate'
JAF_SRC = HERE / 'claude_mods.jaf'
SITE_BEFORE = ['PUSHSTRUCTPAGE', 'PUSH', 'X_REF', 'A_REF', 'S_PUSH']
SITE_AFTER = ['IFZ', 'PUSHSTRUCTPAGE']
# (owner, kind, original, occurrence, replacement, expected ops before, expected ops after)
SWAPS = [
    ('C_ConfigView@EventConfAsraDataForParts', 'call', 'KR_ANCfgSeenToParts', 0, 'KR_MDSeenToParts', SITE_BEFORE, SITE_AFTER),
    ('C_ConfigView@EventConfPartsDataForAsra', 'call', 'KR_ANCfgSeenToAsra', 0, 'KR_MDSeenToAsra', SITE_BEFORE, SITE_AFTER),
]
LAST_ON_EVERY_PATH = {'C_ConfigView@EventConfAsraDataForParts', 'C_ConfigView@EventConfPartsDataForAsra'}
# Windows message boxes (system.MsgBox* / system.Error -> MessageBoxA): Windows decodes the bytes with the system code page, so
# Japanese CP932 text and the Korean written with FNL proxy characters both show as garbage on a Korean Windows (user, 10-15:
# 「지금 경고문 번역 안됐네? … 어쨌든 번역은 해줘」). Each text is re-pointed (same-length S_PUSH operand swap) to a new CP949 string.
S_PUSH = 0x41
MESSAGE_KO = {   # the three player-facing texts that were never translated; wording as the patch's own prompts (〜하시겠습니까?)
    'ゲームを終了しますか？\n\n※セーブされていないデータは失われます': '게임을 종료하시겠습니까?\n\n※저장하지 않은 데이터는 사라집니다',
    'タイトル画面に戻りますか？\n\n※セーブされていないデータは失われます': '타이틀 화면으로 돌아가시겠습니까?\n\n※저장하지 않은 데이터는 사라집니다',
    '【 %s 】\nムービー再生に失敗しました': '【 %s 】\n동영상 재생에 실패했습니다',
}


def message_plan(m, raw_path, strs):
    """Every live message-box text: the Korean written with proxy characters and the three Japanese ones above."""
    vers = L.versions(raw_path)
    plan = []
    for fid, vs in vers.items():
        for v in vs:
            if v['start'] != m['functions'][fid]['address']:
                continue
            ops = v['ops']
            for i, (ad, op) in enumerate(ops):
                if not (op.startswith('CALLHLL system MsgBox') or op.startswith('CALLHLL system Error')):
                    continue
                for j in range(max(0, i - 8), i):
                    o = ops[j][1]
                    if not o.startswith('S_PUSH '):
                        continue
                    sid = int(o.split()[1], 16)
                    jp = strs[sid].decode('cp932', 'replace')
                    if jp in MESSAGE_KO:
                        ko = MESSAGE_KO[jp]
                    else:
                        try:
                            ko = L.decode(strs[sid])
                        except Exception:
                            continue
                        if not re.search('[가-힣]', ko):
                            continue
                    ko.encode('cp949')
                    plan.append(dict(function=L.raw_symbol(m, fid), fid=fid, site=ops[j][0], call=op.split()[2], old_sid=sid,
                                     old_text=jp, ko=ko))
    plan.sort(key=lambda p: p['site'])
    assert len({p['site'] for p in plan}) == len(plan)
    uniq = sorted({p['ko'] for p in plan})
    markers = {}
    for k, ko in enumerate(uniq):
        n = len(ko.encode('cp949'))
        assert n >= 8 and b'\0' not in ko.encode('cp949')
        markers[ko] = ('KRMSG%02d' % k).ljust(n, '_')
    return plan, markers


def message_jaf(markers):
    lines = ['void KR_MDMsgTexts() {', '    // holds the CP949 message-box texts in STR0 (the build overwrites these same-length markers); never called',
             '    string s = "";']
    for ko, mk in markers.items():
        lines.append('    s = "%s";' % mk)
    lines.append('}')
    return '\n' + '\n'.join(lines) + '\n'


def apply_messages(raw, old, plan, markers):
    """In the built AIN (unpacked): overwrite each marker with its CP949 bytes, then re-point every message site to it."""
    strs = L.strings(bytes(raw))[2]
    sid_of = {}
    for ko, mk in markers.items():
        b = mk.encode('ascii')
        assert bytes(raw).count(b) == 1, ('marker not unique', mk)
        idx = [i for i, s in enumerate(strs) if s == b]
        assert len(idx) == 1, mk
        sid_of[ko] = idx[0]
        at = bytes(raw).index(b)
        kb = ko.encode('cp949')
        assert len(kb) == len(b)
        raw[at:at + len(b)] = kb
    sites = []
    for p in plan:
        ad = p['site']
        before = struct.pack('<Hi', S_PUSH, p['old_sid'])
        after = struct.pack('<Hi', S_PUSH, sid_of[p['ko']])
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (p['function'], hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=p['function'], fid=p['fid'], site=ad, kind='S_PUSH (message box text)', call=p['call'],
                          original_sid=p['old_sid'], replacement_sid=sid_of[p['ko']], text_ko=p['ko'], text_cp949=p['ko'].encode('cp949').hex(),
                          before=before.hex(), after=after.hex(), operand_bytes=[ad + 2, ad + 6], owner_is_original=not p['function'].startswith('KR_')))
    check = L.strings(bytes(raw))[2]
    for ko, sid in sid_of.items():
        assert check[sid] == ko.encode('cp949'), ko
    return sites


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
    assert base_is_current(ptr, got), ('runtime moved: rebase mdlib BASE_* first', got, ptr['status'])
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


def compile_and_patch(base, m, raw_path, jaf_text, plan=None, markers=None):
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
    for owner, kind, oldfn, nth, newfn, before_ops, after_ops in SWAPS:
        fid = L.fid_of(m, owner)
        oldid = L.fid_of(m, oldfn)
        newid = ids[newfn]
        assert sig(dm['functions'][newid]) == sig(m['functions'][oldid]), (newfn, sig(dm['functions'][newid]), sig(m['functions'][oldid]))
        ops = L.region_ops(raw_path, m, fid)
        key = f'CALLFUNC 0x{oldid:x}'
        hits = [i for i, (ad, op) in enumerate(ops) if op == key]
        assert len(hits) == 1, (owner, oldfn, len(hits))
        i = hits[nth]
        got_before = [op.split()[0] for _, op in ops[max(0, i - len(before_ops)):i]]
        got_after = [op.split()[0] for _, op in ops[i + 1:i + 1 + len(after_ops)]]
        assert got_before == before_ops and got_after == after_ops, ('site shape', owner, got_before, got_after)
        if owner in LAST_ON_EVERY_PATH:
            for _, op in ops[:i]:
                z = re.match(r'(IFZ|IFNZ|JUMP) 0x([0-9a-f]+)$', op)
                if z:
                    assert int(z[2], 16) <= ops[i][0], ('a jump past the site', owner, op)
            rets = [k for k, (_, op) in enumerate(ops) if op == 'RETURN']
            assert rets == [len(ops) - 1], (owner, rets)
        ad = ops[i][0]
        before = struct.pack('<Hi', 0x30, oldid)
        after = struct.pack('<Hi', 0x30, newid)
        assert bytes(raw[16 + ad:16 + ad + 6]) == before == bytes(old[16 + ad:16 + ad + 6]), (owner, hex(ad))
        raw[16 + ad:16 + ad + 6] = after
        sites.append(dict(function=owner, fid=fid, function_address=m['functions'][fid]['address'], site=ad,
                          site_offset=ad - m['functions'][fid]['address'], kind='CALLFUNC', original=oldfn, original_fid=oldid,
                          replacement=newfn, replacement_fid=newid, before=before.hex(), after=after.hex(), operand_bytes=[ad + 2, ad + 6],
                          occurrence=nth, calls_of_original_in_function=len(hits), owner_is_original=True))
    msg_sites = apply_messages(raw, old, plan, markers) if plan else []
    out.write_bytes(L.pack(bytes(raw), src_bytes[:8]))
    return out, dm, ids, sites, oldn, msg_sites


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
    jaf = JAF_SRC.read_text('utf8')
    W.mkdir(parents=True, exist_ok=True)
    plan, markers = message_plan(m, bp['raw'], L.strings(L.unpack(base.read_bytes()))[2])
    log('message boxes: %d sites, %d texts' % (len(plan), len(markers)))
    jaf = jaf + message_jaf(markers)
    built = L.jaf_literal_encode(L.strip_comments(jaf))
    assert not [c for c in built if ('\uac00' <= c <= '\ud7a3')], 'Hangul left after proxy encoding'
    for c in set(built):
        c.encode('cp932')
    out, dm, ids, sites, oldn, msg_sites = compile_and_patch(base, m, bp['raw'], built, plan, markers)
    log('compiled: %d functions added, %d call sites, %d message sites' % (len(ids), len(sites), len(msg_sites)))
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', out, timeout=900)
    nm, inv = invariance(base, out, m, sites + msg_sites, oldn, bp)
    log('invariance ok', {k: v for k, v in inv.items() if k != 'pinned'})
    audit = L.audit(out, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    ptr2, rt2, got2 = runtime_now()
    assert base_is_current(ptr2, got2), ('runtime moved during the build', got2)
    man = dict(
        schema='yoru-mods.candidate.v1', status='MODS_20261015_STAGED_NOT_INSTALLED', author=L.AUTHOR,
        built=t0.strftime('%Y-%m-%dT%H:%M:%S'), seconds=(datetime.datetime.now() - t0).seconds,
        base=dict(runtime=str(rt), manifest=ptr['manifest'], manifest_sha256=ptr['manifest_sha256'], status=ptr['status'],
                  ain_sha256=L.BASE_AIN_SHA, pact_sha256=L.BASE_PACT_SHA, ex_sha256=L.BASE_EX_SHA, winmm_sha256=L.BASE_WINMM_SHA,
                  checked_at_start_and_end=True),
        files={'NightRemaster.ain': dict(sha256=L.sha(out), size=out.stat().st_size)},
        pact_changed=False, ex_changed=False, fnl_changed=False, winmm_changed=False,
        added_functions=dict(sorted(ids.items(), key=lambda x: x[1])), jam_bodies=[],
        same_length_sites=sites, message_box_sites=msg_sites,
        message_box_note='system.MsgBox*/Error texts re-pointed to CP949 strings (Windows shows MessageBoxA text in the system '
                         'code page; the FNL proxy characters and Japanese CP932 showed as garbage on Korean Windows)',
        relocated_original_functions=[], pinned_functions=inv['pinned'], invariance=inv,
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
