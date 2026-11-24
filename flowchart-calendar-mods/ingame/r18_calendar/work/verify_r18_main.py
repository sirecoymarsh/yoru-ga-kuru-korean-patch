# ============================================================== defects to plant (each must make its check fail)
def op_replace(fn, pred, new, nth=0):
    def mut(ops):
        hits = [i for i, o in enumerate(ops) if pred(o)]
        if len(hits) <= nth:
            raise RuntimeError(('defect could not be planted: no op to mutate', fn, len(hits)))
        ops[hits[nth]] = new(ops[hits[nth]])
        return ops
    return {fn: mut}


def seq_replace(fn, pattern, at, new, nth=0):
    """Replace op pattern[at] of the nth place where the op sequence `pattern` occurs."""
    def mut(ops):
        hits = [i for i in range(len(ops) - len(pattern) + 1) if all(ops[i + j] == list(pattern[j]) for j in range(len(pattern)))]
        if len(hits) <= nth:
            raise RuntimeError(('defect could not be planted: no op sequence', fn, pattern))
        ops[hits[nth] + at] = list(new)
        return ops
    return {fn: mut}


def sp(text):
    return 'S_PUSH', json.dumps(text, ensure_ascii=False)


def s_is(o, text):
    return o[0] == 'S_PUSH' and json.loads(o[1]) == text


def lock_bypass():
    """「open = KR_T9State(no) == 2」 on the card page becomes 「!= -1」: every card offers 이 장면 재생."""
    def mut(ops):
        hits = [i for i in range(len(ops) - 2) if ops[i] == ['CALLFUNC', 'KR_T9State'] and ops[i + 1] == ['PUSH', '2'] and ops[i + 2] == ['EQUALE']]
        if not hits:
            raise RuntimeError('defect could not be planted: no state test in KR_T18CardPage')
        ops[hits[0] + 1] = ['PUSH', '-1']
        ops[hits[0] + 2] = ['NOTE']
        return ops
    return {'KR_T18CardPage': mut}


DEFECTS = [
    # r15's nine (V4 plants into KR_T18MonthPage, where the month navigation lives since r16)
    ('V2 width: legend 40 chars', 'pages', op_replace('KR_T9Legend', lambda o: o[0] == 'S_PUSH', lambda o: list(sp(proxy('가' * 40))))),
    ('V2 height: 12 rows a lane page', 'pages', op_replace('KR_T9LanePage', lambda o: o == ['.LOCALASSIGN', 'per 8'], lambda o: ['.LOCALASSIGN', 'per 12'])),
    ('V3 colour: unseen days white', 'calendar', op_replace('KR_T9ColorMark', lambda o: s_is(o, '‡'), lambda o: list(sp('†')))),
    ('V4 navigation: next skips a month', 'nav', seq_replace('KR_T18MonthPage', [('.LOCALREF', 'm'), ('PUSH', '1'), ('ADD',), ('RETURN',)], 1, ('PUSH', '2'))),
    ('V5 unwind flag not written', 'flow', op_replace('KR_T9Request', lambda o: s_is(o, 'Unwind'), lambda o: list(sp('Unwound')))),
    ('V6 settings context lost', 'flow', op_replace('KR_T9HomeConfig', lambda o: s_is(o, 'C'), lambda o: list(sp('X')))),
    ('V7 play allowed without context', 'flow', op_replace('KR_T9CanPlay', lambda o: o == ['PUSH', '0'], lambda o: ['PUSH', '1'], nth=1)),
    ('V8 fail-safe removed', 'flow', op_replace('KR_T9HomeMenuRun', lambda o: s_is(o, 'Playing'), lambda o: list(sp('PlayingX')))),
    ('V10 seen: this save shown as other save', 'seen', op_replace('KR_T9State', lambda o: o == ['PUSH', '2'], lambda o: ['PUSH', '1'])),
    # r16's kept four VM defects (re-aimed at the r18 bodies)
    ('V11 bar: one cell too many', 'bars', seq_replace('KR_T18Bar', [('.LOCALREF', 'i'), ('.LOCALREF', 'f'), ('LT',)], 2, ('LTE',))),
    ('V3 missed shown as upcoming', 'calendar', op_replace('KR_T18DayState', lambda o: o == ['PUSH', '3'], lambda o: ['PUSH', '1'])),
    ('V11 summary total mismatch (one month left out of 전체)', 'summary', seq_replace('KR_T18SummaryTitle', [('.LOCALREF', 'x2'), ('PUSH', '10000'), ('DIV',)], 0, ('PUSH', '0'))),
    ('V12 one E-number tail removed', 'rows', None),
    # r17's
    ('V3 ★ left on main-story days (r16 day-mark bodies)', 'calendar', 'r16_days'),
    ('V11 one panel-outside scene counted (E00996)', 'summary', op_replace('KR_T18Out', lambda o: o == ['PUSH', '996'], lambda o: ['PUSH', '-996'])),
    ('V15 last bar cell filled before completion', 'bars', seq_replace('KR_T18Bar', [('.LOCALREF', 'cells'), ('PUSH', '1'), ('SUB',)], 1, ('PUSH', '0'))),
    ('V11 one old-form drawer row left (회상 · 그 밖 page)', 'pages', 'old_row'),
    # r18 (VM)
    ('V16 lock bypass: a ● / △ card offers 이 장면 재생', 'lock', lock_bypass()),
    ('V17 restore skipped (affinity stays raised)', 'sandbox', op_replace('KR_T18RunSandboxed', lambda o: o == ['CALLFUNC', 'gamesave::detail::ロード実行'], lambda o: ['DELETE'])),
    ('V17 temp file left behind', 'sandbox', op_replace('KR_T18SandboxDelete', lambda o: o == ['CALLHLL', 'system DeleteSaveFile 0'], lambda o: ['VM_POP_PUSH1'])),
    ('V19 ResumeSave failure still replays', 'sandbox', op_replace('KR_T18RunSandboxed', lambda o: o == ['CALLFUNC', 'KR_T18SandboxSaved'], lambda o: ['VM_POP_PUSH1'])),
]


def table_defect(X):
    no = X['cards'][10]['entry']
    return ('V1 table: one card entry wrong', 'tables', op_replace('KR_T9CardEntry', lambda o: o == ['PUSH', str(no)], lambda o: ['PUSH', str(no + 1)]))


def tail_defect(vm):
    k = next(k for k in range(200) if vm.run('KR_T18CardTail', [k]))
    return seq_replace('KR_T18CardTail', [('PUSH', '1'), ('RETURN',)], 0, ('PUSH', '0')), k


def r16_day_alias():
    """「★ left on main-story days」: KR_T18DayState / DayMark / DayColor run r16's KR_T16 bodies (the r16 candidate, read
    only) - exactly the r16 day rendering with ★/☆."""
    d = L.WORK / 'vm' / 'r16'
    d.mkdir(parents=True, exist_ok=True)
    rm = L.read_meta(L.R16 / 'work' / 'build' / 'candidate_meta.json')
    ain = L.R16 / 'candidate' / 'NightRemaster.ain'
    assert L.sha(ain) == L.R16_AIN_SHA
    alias = {}
    for part in ('DayState', 'DayMark', 'DayColor'):
        name = 'KR_T16' + part
        i = L.fid_of(rm, name)
        path = d / f'{name}.jam'
        if not path.exists():
            L.cmd('ain', 'dump', '--function', name, '-o', path, ain)
        alias['KR_T18' + part] = (rm['functions'][i], path)
    return alias, {}


def old_row_alias(m):
    """「one old-form drawer row left」: the 회상 · 그 밖 page calls r15's KR_T9ChipRow body (base AIN, 「이름 n (본 것 k)」)."""
    d = L.WORK / 'vm' / 'base'
    d.mkdir(parents=True, exist_ok=True)
    path = d / 'KR_T9ChipRow_r15.jam'
    if not path.exists():
        L.cmd('ain', 'dump', '--function', 'KR_T9ChipRow', '-o', path, L.base_dir() / 'NightRemaster.ain')
    entry = m['functions'][L.fid_of(m, 'KR_T9ChipRow')]
    return {'KR_T9ChipRow@r15': (entry, path)}, op_replace('KR_T18MemPage', lambda o: o == ['CALLFUNC', 'KR_T9ChipRow'], lambda o: ['CALLFUNC', 'KR_T9ChipRow@r15'])


def main():
    selftest = '--selftest' in sys.argv
    native = '--native' in sys.argv
    t0 = time.time()
    man = L.readj(O / 'manifest.json')
    bd = L.base_dir()
    base = bd / 'NightRemaster.ain'
    cand = O / 'NightRemaster.ain'
    assert L.sha(base) == L.BASE_AIN_SHA and L.sha(cand) == man['files']['NightRemaster.ain']['sha256']
    m = L.read_meta(bd / 'meta.json')
    nm = L.read_meta(W / 'candidate_meta.json')
    assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
    X = expectations()
    counts = collections.Counter()
    vm = VM(cand, nm)
    if native:
        out = native_checks(vm, X, counts)
        result = dict(schema='yoru-calendar-r18.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, counts=dict(counts))
        L.writej(W / 'native_compare.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=1))
        print('NATIVE = VM')
        return
    frames = static_checks(base, cand, man, m, nm, counts)
    audit = L.audit(cand, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', L.runtime()[1] / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'] and audit['ain_sha256'] == L.sha(cand)
    counts['S5_active_functions'] = audit['active_functions']
    table_checks(vm, X, counts)
    bar_checks(vm, counts)
    regs = seen_checks(vm, X, counts)
    all_regs = {e['fn'] for e in X['ev'].values()}
    abo = all_but_one(X)
    mid_regs, mid_today = synthetic_mid_month(X)
    for name, rg in [('none', set()), ('partial', regs), ('all', all_regs), ('all_but_one', abo)]:
        vm.registered = rg
        vm.flags = set(e['m0'] for e in X['ev'].values() if e['m0'] is not None) if name == 'partial' else set()
        pages_all(vm, X, counts, name)
    vm.flags = set()
    vm.registered = regs
    event_pages(vm, X, counts)
    calendar_checks(vm, X, counts, [set(), regs, all_regs, mid_regs, abo])
    shown, _ = month_page_check(vm, X, mid_today[0], counts, mid_regs, mid_today)
    assert all(ch in shown for ch in '▲●○'), ('synthetic 8/15 state does not show every mark', dict(shown))
    counts['V3_synthetic_mid_month_marks'] = len([c for c in shown if c != '　'])
    nav_checks(vm, X, counts)
    flow_checks(vm, X, counts)
    row_checks(vm, X, counts)
    panel = panel_checks(vm, X, counts, [('none', set()), ('partial', regs), ('all', all_regs), ('all_but_one', abo), ('mid-August', mid_regs)])
    lock_checks(vm, X, counts)
    sandbox = sandbox_checks(vm, X, counts)
    real = real_save_checks(vm, X, counts)
    result = dict(schema='yoru-calendar-r18.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,
                  counts=dict(counts), vm_steps=vm.steps, widest_title=WIDEST['title'], widest_title_len=len(WIDEST['title']),
                  widest_item=WIDEST['item'], widest_item_len=len(WIDEST['item']), widest_drawer_row=WIDEST['drawer'],
                  widest_drawer_row_len=len(WIDEST['drawer']), widest_drawer_row_units=units_w(WIDEST['drawer']),
                  seconds=round(time.time() - t0, 1), saves_checked=counts['S4_saves'], frames_checked=counts['S4_frames'],
                  panel=panel, sandbox=sandbox, real_saves=real)
    print(json.dumps({k: v for k, v in result.items() if k not in ('real_saves',)}, ensure_ascii=False, indent=1, default=str))
    if selftest:
        planted = []
        groups = dict(pages=lambda v: pages_all(v, X, collections.Counter(), 'partial'),
                      calendar=lambda v: calendar_checks(v, X, collections.Counter(), [regs, mid_regs]),
                      nav=lambda v: nav_checks(v, X, collections.Counter()),
                      flow=lambda v: flow_checks(v, X, collections.Counter()),
                      seen=lambda v: seen_checks(v, X, collections.Counter()),
                      tables=lambda v: table_checks(v, X, collections.Counter()),
                      summary=lambda v: pages_all(v, X, collections.Counter(), 'partial'),
                      rows=lambda v: row_checks(v, X, collections.Counter()),
                      bars=lambda v: bar_checks(v, collections.Counter()),
                      lock=lambda v: lock_checks(v, X, collections.Counter()),
                      sandbox=lambda v: sandbox_checks(v, X, collections.Counter()))
        tail_mut, tail_k = tail_defect(vm)
        for label, group, mutation in DEFECTS + [table_defect(X)]:
            alias = None
            if mutation is None:
                mutation = tail_mut
            elif mutation == 'r16_days':
                alias, mutation = r16_day_alias()
            elif mutation == 'old_row':
                alias, mutation = old_row_alias(m)
            v2 = VM(cand, nm, mutate=mutation, alias=alias)
            v2.registered = regs
            try:
                groups[group](v2)
                planted.append(dict(defect=label, caught=False))
            except (AssertionError, Stop) as ex:
                planted.append(dict(defect=label, caught=True, message=str(ex)[:200]))
            except RuntimeError as ex:
                planted.append(dict(defect=label, caught=False, message='not planted: ' + str(ex)[:160]))

        def flip_site(b):
            raw = bytearray(L.unpack(b))
            s = L.readj(L.R15 / 'candidate' / 'manifest.json')['same_length_sites'][4]
            raw[16 + s['site']:16 + s['site'] + 6] = bytes.fromhex(s['before'])
            return L.pack(bytes(raw), b[:8])

        def touch_return(b):
            raw = bytearray(L.unpack(b))
            fr = next(x for x in frames if x['live'])
            ad = m['functions'][fr['fid']]['address'] + fr['offset']
            raw[16 + ad] ^= 1
            return L.pack(bytes(raw), b[:8])

        def touch_msg(b):
            raw = bytearray(L.unpack(b))
            pos = raw.index(b'MSG1') + 12
            while struct.unpack_from('<I', raw, pos)[0] == 0:
                pos += 4
            raw[pos + 4] ^= 1
            return L.pack(bytes(raw), b[:8])

        def redefine_pinned(meta):
            i = L.fid_of(meta, 'KR_T9HomeCasual')
            meta['functions'][i]['address'] = meta['functions'][-1]['address'] + 64     # what an override would do
            return meta

        def touch_pinned_beyond_operand(b):
            raw = bytearray(L.unpack(b))
            site = swap_of(man)['site']
            assert bytes(raw[16 + site + 8:16 + site + 10]) == struct.pack('<H', 0) and raw[16 + site + 10] == 1, 'PUSH 1 after the POP'
            raw[16 + site + 10] ^= 1                                                       # PUSH 1 -> PUSH 0 (■ＡＤＶ消し's first argument)
            return L.pack(bytes(raw), b[:8])
        for label, kw, part in [('S2 one r15 swap site reverted', dict(mutate_bytes=flip_site), 'S2'),
                                ('S4 a saved return instruction changed', dict(mutate_bytes=touch_return), 'S4'),
                                ('S3 one MSG1 byte changed', dict(mutate_bytes=touch_msg), 'S3'),
                                ('S6 a pinned function redefined (KR_T9HomeCasual moved)', dict(mutate_meta=redefine_pinned), 'S6'),
                                ('S6 a byte of the pinned KR_T9HomeCasual other than the RunEvent operand changed', dict(mutate_bytes=touch_pinned_beyond_operand), 'S6')]:
            try:
                static_checks(base, cand, man, m, nm, collections.Counter(), parts=(part,), **kw)
                planted.append(dict(defect=label, caught=False))
            except AssertionError as ex:
                planted.append(dict(defect=label, caught=True, message=str(ex)[:200]))
        result['planted_defects'] = planted
        print(json.dumps(planted, ensure_ascii=False, indent=1))
        assert len(planted) == 27, len(planted)
        assert all(p['caught'] for p in planted), [p['defect'] for p in planted if not p['caught']]
    L.writej(W / ('vm_verification_selftest.json' if selftest else 'vm_verification.json'), json.loads(json.dumps(result, ensure_ascii=False, default=str)))
    print('VERIFIED', round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
