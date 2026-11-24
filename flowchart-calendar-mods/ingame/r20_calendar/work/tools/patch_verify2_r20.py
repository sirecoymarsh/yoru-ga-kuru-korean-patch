"""r20 one-off (after patch_verify_r20.py): the real-save r20 checks (probe --regs texts) and the native r20 comparison."""
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'verify_calendar_r20.py'
s = p.read_text(encoding='utf8')
assert 'def r20_real_save_checks' not in s, 'already patched'


def rep(a, b, count=1):
    global s
    assert s.count(a) == count, (a[:90], s.count(a))
    s = s.replace(a, b)


R20_REAL = r'''def r20_blocks(log):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'(STTEXT|STCALC|TRCALC|TRTEXT) (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            out[(z.group(1), z.group(2))] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    return out


def r20_real_save_checks(vm, X, counts):
    """V27/V29 on every real save state: the texts the candidate built natively (probe --regs: KR_T20StText(1..8),
    KR_T20TrText(2..8)) = the VM on the same registrations and date = the model."""
    doc = L.readj(L.EVID / 'probe_regs.json')
    man = L.readj(O / 'manifest.json')
    rows = []
    for r in doc['saves']:
        st = r.get('state')
        if not st:
            continue
        assert r['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256'], 'regs logged by another candidate'
        regs = {X['ev'][e]['fn'] for e in st['regs']}
        today = tuple(st['today'])
        b = r20_blocks(r['log'])
        vm.registered = regs
        vm.today = today
        vm.reset()
        n = 0
        for c in range(1, 9):
            native = b.get(('STCALC', 'REGS %d' % c))
            assert native is not None, ('no native 이벤트 text', r['save'], c)
            assert native == ko(vm.run('KR_T20StText', [c])) == r20_status_text(X, regs, c, today), ('V27 real save: 이벤트 쪽', r['save'], c)
            n += 1
        for q in PARTY_Q:
            native = b.get(('TRCALC', 'REGS %d' % q))
            assert native == ko(vm.run('KR_T20TrText', [q])) == r20_label_text(X, regs, q, today), ('V27 real save: label', r['save'], q)
            n += 1
        ms = next((l for l in r['log'] if l.startswith('R20 texts of 8 persons built in')), '')
        rows.append(dict(save=r['save'], today='%d/%d' % today, texts_equal=n, native_build_ms=ms.split(' in ')[-1] if ms else None,
                         remaining_this_month={PARTY_KR[q - 2]: r20_left(X, regs, q, today) for q in PARTY_Q},
                         talks_seen={PARTY_KR[q - 2]: r20_talk(X, regs, q) for q in PARTY_Q}))
        counts['V27_real_saves'] += 1
        counts['V27_real_texts_equal'] += n
    assert rows, 'no real save state for r20'
    return rows


'''
anchor = "# ============================================================== defects to plant (each must make its check fail)"
rep(anchor, R20_REAL + anchor)

R20_NATIVE = r'''    # ---------------- r20 (native): the 「이벤트」 page as drawn, the partner labels, brightness, part counts, home pixels
    r20 = res['r20']
    vm.flags = set()
    vm.registered = regs
    vm.today = today
    vm.reset()
    texts = r20['status_texts']
    w1 = r20['status_charas']['A']
    w2 = r20['status_charas']['C']
    assert texts['A'] == ko(vm.run('KR_T20StText', [w1])) == r20_status_text(X, regs, w1, today), ('native 이벤트 쪽 A != VM', w1)
    assert texts['C'] == ko(vm.run('KR_T20StText', [w2])) == r20_status_text(X, regs, w2, today), ('native 이벤트 쪽 C != VM', w2)
    match_b = [c for c in range(1, 9) if ko(vm.run('KR_T20StText', [c])) == texts['B']]
    assert len(match_b) == 1 and match_b[0] != w1, ('native 이벤트 쪽 B (next person) matches no single person', match_b)
    sc = r20['status']
    want_ours = dict(home_before=0, page1=0, page4=2, page4_next_person=2, page3_from4=0, page4_from3=2, page1_from4=0, page4_from1=2,
                     after_exit1=0, second_entry_page4=2, after_exit2=0, home_after=0)
    assert {k: v['ours'] for k, v in sc.items()} == want_ours, ('native part counts (status)', {k: v['ours'] for k, v in sc.items()})
    inside = [k for k in sc if k not in ('home_before', 'home_after')]
    assert len({sc[k]['charastatus'] for k in inside}) == 1 and len({sc[k]['selectally'] for k in inside}) == 1, ('the status window\'s own parts changed', sc)
    assert res.get('home_before_after_member', {}).get('differing_pixels') == 0, ('home after the member screen differs', res.get('home_before_after_member'))
    out['r20_status'] = dict(persons=dict(A=w1, B=match_b[0], C=w2), texts_equal_vm=3, part_counts=want_ours,
                             charastatus_parts=sc['page4']['charastatus'], home_pixels_before_after_member=0,
                             event_page_ms=r20.get('event_page_ms'))
    pr = res['partner_run']
    assert pr['exit_code'] == 0 and pr['log'][-1] == 'END' and not pr.get('vm_error') and not pr.get('message'), ('partner run failed', pr.get('exit_code'), pr['log'][-3:])
    plog = pr['log']
    z = re.match(r'PARTNER date=(\d+)/(\d+) now=(\d+)', r20['partner_date'])
    ptoday = (int(z.group(1)), int(z.group(2)))
    pregs_line = next(l for l in plog if l.startswith('REGS'))
    pregs = {X['ev'][int(x)]['fn'] for x in pregs_line.split()[1:]}
    vm.registered = pregs
    vm.today = ptoday
    vm.reset()
    for key, text in r20['partner_calc'].items():
        kind, _, c = key.split()
        c = int(c)
        if kind == 'STCALC':
            assert text == ko(vm.run('KR_T20StText', [c])) == r20_status_text(X, pregs, c, ptoday), ('native partner-save 이벤트 text', c)
        else:
            assert text == ko(vm.run('KR_T20TrText', [c])) == r20_label_text(X, pregs, c, ptoday), ('native partner-save label text', c)
    assert len(r20['partner_calc']) == 15, len(r20['partner_calc'])
    labels = r20['partner_labels']
    shown = sorted(int(k.split()[1]) for k in labels['P0'])
    assert shown and all(sorted(int(k.split()[1]) for k in labels[t]) == shown for t in ('PA', 'PB', 'P2')), ('the labelled portraits changed', labels.keys())
    for tag, blk in labels.items():
        for k, text in blk.items():
            pp = int(k.split()[1])
            assert text == ko(vm.run('KR_T20TrText', [pp])) == r20_label_text(X, pregs, pp, ptoday), ('native label != VM', tag, pp)
    mul = r20['partner_mul']
    ha, hb = HOVER_A, HOVER_B
    want_mul = dict(P0={q: (255, 1) for q in shown}, PA={q: (255 if q == ha else 128, 1) for q in shown},
                    PB={q: (255 if q == hb else 128, 1) for q in shown}, P2={q: (255 if q == hb else 128, 1) for q in shown})
    assert {t: {int(q): tuple(v) for q, v in d.items()} for t, d in mul.items()} == want_mul, ('native brightness', mul)
    pc = r20['partner']
    assert {k: v['ours'] for k, v in pc.items()} == dict(first=2 * len(shown), dialog1=0, again=2 * len(shown), dialog2=0, after_screen=0), \
        ('native part counts (partner)', {k: v['ours'] for k, v in pc.items()})
    assert len({v['selectally'] for k, v in pc.items() if k != 'after_screen'}) == 1, ('SelectAlly\'s own parts changed', pc)
    out['r20_partner'] = dict(save=pr['save'], today='%d/%d' % ptoday, shown=shown, hover=[ha, hb], labels_equal_vm=sum(len(b_) for b_ in labels.values()),
                              brightness=want_mul, part_counts={k: v['ours'] for k, v in pc.items()}, selectally_parts=pc['first']['selectally'])
    counts['N_r20_blocks_identical'] = 3 + sum(len(b_) for b_ in labels.values())
'''
rep("""    counts['N_sandbox_state_equal'] = 1
    return out""", """    counts['N_sandbox_state_equal'] = 1
""" + R20_NATIVE + """    return out""")
rep("""NOTICE_FAIL = '재생 전 상태를 저장하지 못해 재생하지 않았습니다.'""",
    """NOTICE_FAIL = '재생 전 상태를 저장하지 못해 재생하지 않았습니다.'
HOVER_A, HOVER_B = 3, 8               # the two portraits the probe hovers on the partner screen (probe_calendar_r20.HOVER)""")
p.write_text(s, encoding='utf8')
print('patched', p)
