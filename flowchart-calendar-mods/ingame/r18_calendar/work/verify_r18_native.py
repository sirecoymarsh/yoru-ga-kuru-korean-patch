# ============================================================== native comparison (--native)
def native_checks(vm, X, counts):
    res = L.readj(L.EVID / 'probe_result.json')
    man = L.readj(O / 'manifest.json')
    assert res['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256']
    st = res['state']
    regs = {X['ev'][e]['fn'] for e in st['regs']}
    today = tuple(st['today'])
    blocks = {}
    log = res['log']
    i = 0
    while i < len(log):
        z = re.match(r'(TITLE|ROWS|PANEL|STATE) (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            blocks[(z.group(1), z.group(2))] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    # the states the probe saw for the lock cards (△ needs the global read mark of the first message)
    other = set()
    for l in log:
        z = re.match(r'LOCKCARD entry=(\d+) state=(\d+) size=(\d+)', l)
        if z and z.group(2) == '1' and X['ev'][int(z.group(1))]['m0'] is not None:
            other.add(X['ev'][int(z.group(1))]['m0'])
    vm.registered = regs
    vm.flags = other
    vm.today = today
    out = {}
    for (kind, tag), text in blocks.items():
        parts = tag.split()
        if kind in ('PANEL', 'STATE'):
            continue
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'P'
        vm.script = [0]
        if parts[0] == 'MONTH':
            vm.run('KR_T9MonthPage', [int(parts[1])])
            d = vm.dialogs[-1]
        elif parts[0] == 'SUMMARY':
            vm.run('KR_T18SummaryPage')
            d = vm.dialogs[-1]
        elif parts[0] == 'MEM':
            vm.run('KR_T9MemPage')
            d = vm.dialogs[-1]
        elif parts[0] == 'LANE':
            mo, lane = int(parts[1]), int(parts[2])
            page = int(parts[3][1:]) - 1 if len(parts) > 3 else 0
            vm.script = [12] * page + [0]
            vm.run('KR_T9LanePage', [mo, lane])
            d = vm.dialogs[page]
        elif parts[0] in ('LOCKCARD', 'OPENCARD'):
            k, mo = (int(parts[2]), int(parts[3])) if parts[0] == 'LOCKCARD' else (int(parts[1]), int(parts[2]))
            vm.run('KR_T9CardPage', [k, mo])
            d = vm.dialogs[0]
            if parts[0] == 'LOCKCARD':
                assert not any(iid == 13 for iid, _, _, _ in d['items']), 'native lock card offers play in the VM'
                counts['N_lock_pages_identical'] += 1
        elif parts[0] in ('STAGES', 'OPENEVENT'):
            t = res['target']
            k = next(k for k, c in enumerate(X['cards']) if c['month'] == t['month'] and c['lane'] == t['lane']
                     and [x['key'] for x in X['cards'] if x['month'] == t['month'] and x['lane'] == t['lane']].index(c['key']) == t['index'])
            vm.script = [100 + t['stage'], 0, 0]
            vm.run('KR_T9StagePage', [k, t['month']])
            d = vm.dialogs[0] if parts[0] == 'STAGES' else vm.dialogs[1]
            if parts[0] == 'OPENEVENT':
                assert d['items'][0][:2] == (13, proxy(PLAY)) and d['items'][0][3] == 0, 'the target scene page has no enabled play item'
                assert SANDBOX_NOTE in ko(d['title']).split('\n')
        else:
            raise AssertionError(tag)
        if kind == 'TITLE':
            want = ko(d['title'])
        else:
            want = '\n'.join(ko(t) for iid, t, _, _ in d['items'] if iid >= 100)
        assert text == want, ('native %s differs from the VM' % kind.lower(), tag, [(a, b) for a, b in zip(text.split('\n'), want.split('\n')) if a != b][:2])
        out['%s %s' % (kind, tag)] = 'identical'
        if kind == 'TITLE' and parts[0] == 'MONTH':
            out[tag + ' marks'] = ''.join(sorted(set(m for _, m in calendar_cells(text).values()) - {'　'}))
    counts['N_blocks_identical'] = len(out)
    # the home panel logged natively next to the summary: the same value as the summary's first line
    panels = {tag: text for (kind, tag), text in blocks.items() if kind == 'PANEL'}
    assert panels, 'no native panel text logged'
    values = {tag: native_panel_value(t) for tag, t in panels.items()}
    same = {values[t] for t in values if t in ('HOME', 'SUMMARY', 'AFTER')}
    assert len(same) == 1, ('panel value changed by the sandboxed replay', values)
    summary = blocks[('TITLE', 'SUMMARY')].split('\n')[0]
    head = re.fullmatch(r'〓달성도　전체 [■□]{10} (\d+)/(\d+) \((.+)\)', summary)
    assert head and head.group(3) == values['HOME'] and int(head.group(2)) == PANEL_EVENTS, ('native summary != native panel', summary, values)
    vm.registered = regs
    pk, ptext = panel_value(vm)
    assert int(head.group(1)) == pk and ko(ptext) == head.group(3)
    out['panel_same_save'] = dict(panel_native='전체 ' + values['HOME'], summary_native=summary.lstrip('〓'), vm_panel='%d/1043 %s' % (pk, ko(ptext)),
                                  after_sandbox='전체 ' + values.get('AFTER', '?'), after_midload='전체 ' + values.get('MIDLOAD', '?'))
    out['save'] = res['save']
    out['today'] = '%d/%d' % today
    # r18 sandbox, native: before = the home menu before the calendar opened, after = the home menu after the replay
    sb = res['sandbox']
    t = res['target']
    assert set(sb['states']) >= {'HOME', 'PREPLAY', 'MIDREPLAY', 'AFTER', 'MIDLOAD'}, sb['states']
    assert not sb['home_vs_preplay'], ('state moved before the replay', sb['home_vs_preplay'])
    assert not sb['home_vs_after'], ('state after the sandboxed replay differs from before (outside the allow list)', sb['home_vs_after'])
    assert sb['after_temp_files'] == ['0', '0'] and sb['midreplay_temp_files'] == ['1', '1'], (sb['after_temp_files'], sb['midreplay_temp_files'])
    assert not sb['temp_file_on_disk_at_end'], sb['temp_file_on_disk_at_end']
    assert res.get('home_before_after', {}).get('differing_pixels') == 0, res.get('home_before_after')
    feel = sb['feel']
    who = [a['person'] for a in t['affection']]
    delta = sum(a['delta'] for a in t['affection']) * 300
    assert feel['AFTER'] == feel['HOME'], ('affinity not restored', feel)
    changed = {p + 1: feel['MIDLOAD'][p] - feel['HOME'][p] for p in range(8) if feel['MIDLOAD'][p] != feel['HOME'][p]}
    assert changed == {who[0]: delta}, ('the mid-replay load (no temp file) keeps the replay\'s own effect', changed, who, delta)
    assert sb['midload_temp_files'] == ['0', '0']
    assert sb['date']['HOME'] == sb['date']['AFTER'] == sb['date']['MIDLOAD'], sb['date']
    assert sb['regs_count']['HOME'] == sb['regs_count']['AFTER'], sb['regs_count']
    lock_after = [l for l in log if l.startswith('LOCK AFTER 13')]
    assert lock_after and all('play= unwind= prevset=' in l for l in lock_after), lock_after
    out['sandbox'] = dict(target='E%05d (stage %d of E%05d, %d messages)' % (t['event'], t['stage'] + 1, t['entry'], t['messages']),
                          states=sb['states'], home_vs_after_outside_allow_list=sb['home_vs_after'],
                          allowed_differences=sb['home_vs_after_allowed'], feel=feel, midload_change=changed,
                          session_variables_restored_by_resumeload=sb['session_variables_restored_by_resumeload'],
                          temp_files=dict(midreplay=sb['midreplay_temp_files'], after=sb['after_temp_files'], midload=sb['midload_temp_files'],
                                          on_disk_at_end=sb['temp_file_on_disk_at_end']),
                          home_pixels_before_after=res['home_before_after']['differing_pixels'],
                          home_pixels_before_midload=res.get('home_before_midload', {}).get('differing_pixels'),
                          lock_pages=[l for l in log if l.startswith('LOCKCARD entry=')], lock_after_13=lock_after)
    counts['N_sandbox_state_equal'] = 1
    return out


