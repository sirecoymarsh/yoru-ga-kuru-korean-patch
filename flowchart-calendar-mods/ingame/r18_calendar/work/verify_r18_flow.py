def flow_checks(vm, X, counts):
    """r15's replay / settings / no-context / fail-safe / original flows (V5-V9); the replay now runs through the sandbox and
    only a scene seen in this save offers the item (r18), so the chosen cards are registered first."""
    vm.reset()
    vm.files = {}
    vm.run_event = None
    pc = next(c for c in X['cards'] if 1 <= c['lane'] <= 7)
    mo, lane = pc['month'], pc['lane']
    k, card = first_card(X, mo, lane)
    vm.registered = {X['ev'][card['entry']]['fn']}
    vm.today = (mo, 1)
    vm.script = [PICK]
    assert home_run(vm) == PICK and vm.v('Ctx') == 'P'
    vm.script = [3, 100, 13]
    vm.dialogs = []
    vm.run('KR_T8CharMissingPage', [lane + 1])
    items0 = [(i, ko(t)) for i, t, _, _ in vm.dialogs[0]['items']]
    assert items0 == [(1, '날짜별로 보기'), (2, '던전 파티별로 보기'), (3, '달력으로 보기'), (0, '돌아가기')], items0
    heads = [ko(d['title']).split('\n')[0] for d in vm.dialogs]
    name = LANE_KR[lane]
    assert len(vm.dialogs) == 3 and heads[1].startswith('〓%d월 · %s' % (mo, name)) and heads[2].startswith('〓%d' % mo), heads
    assert all(d['unwind'] == '' for d in vm.dialogs), 'a dialog opened while unwinding'
    assert vm.v('Play') == str(card['entry']) and vm.v('Unwind') == '1', (vm.v('Play'), vm.v('Unwind'))
    assert not any(c[0] == 'KR_T8CharDatePage' for c in vm.calls), 'date page opened instead of the calendar'
    vm.script = []
    vm.dialogs = []
    assert home_run(vm) == 3 and not vm.dialogs, 'home menu must return 3 without a dialog'
    assert vm.v('Playing') == '1' and vm.v('Unwind') == '' and vm.v('Ctx') == ''
    vm.calls = []
    vm.run_top('KR_T9HomeCasual')
    want_fn = X['ev'][card['entry']]['fn']
    names = [c[0] for c in vm.calls if c[0] != 'delete']
    assert names == ['LSys3xScript::Prepare', 'gamesave::detail::セーブ実行', 'LSys3xScript::RunEvent', 'gamesave::detail::ロード実行',
                     'post_load', '■ＡＤＶ消し'], vm.calls
    assert vm.calls[0] == ('LSys3xScript::Prepare', [want_fn]) and vm.calls[-1] == ('■ＡＤＶ消し', [1, 0]), vm.calls
    assert vm.v('Play') == '' and vm.v('Playing') == ''
    assert TEMP not in vm.files and TEMP_VSF not in vm.files, 'temp file left after the replay'
    vm.script = [11]
    assert home_run(vm) == 11 and len(vm.dialogs) == 1
    counts['V5_play_from_window'] += 1
    vm.reset()
    vm.files = {}
    vm.today = (6, 13)
    k2, card2 = first_card(X, 6, 0)
    vm.registered = {X['ev'][card2['entry']]['fn']}

    def inside(v):
        assert v.v('Ctx') == 'C'
        v.script = [1, 20, 100, 13]
        v.run('KR_T8CharMissingMenu')
        assert not v.script, v.script
        assert v.v('Unwind') == '' and v.v('Req') == str(card2['entry']) and v.v('Play') == '', (v.v('Unwind'), v.v('Req'))
    vm.config_inner = inside
    vm.run('KR_T9HomeConfig', [0, 0])
    simple = [c for c in vm.calls if c[0] == 'simple']
    assert simple == [('simple', '재생을 예약했습니다.\n설정 창을 닫으면 본거지에서 재생합니다.')], simple
    first = [(i, ko(t)) for i, t, _, _ in vm.dialogs[0]['items']]
    assert first[0] == (1, '이벤트 달력') and [i for i, _ in first] == [1, 2, 3, 4, 5, 6, 7, 8, 0], first
    assert vm.v('Play') == str(card2['entry']) and vm.v('Req') == '' and vm.v('Ctx') == '' and vm.v('Unwind') == ''
    card_dialog = vm.dialogs[-1]
    assert NOTE_C in ko(card_dialog['title']).split('\n') and card_dialog['items'][0][3] == 0
    vm.script = []
    vm.dialogs = []
    assert home_run(vm) == 3 and not vm.dialogs
    vm.calls = []
    vm.run_top('KR_T9HomeCasual')
    assert vm.calls[0] == ('LSys3xScript::Prepare', [X['ev'][card2['entry']]['fn']]), vm.calls
    assert [c[0] for c in vm.calls if c[0] != 'delete'][1:4] == ['gamesave::detail::セーブ実行', 'LSys3xScript::RunEvent', 'gamesave::detail::ロード実行']
    counts['V6_play_from_settings'] += 1
    vm.reset()
    vm.registered = {X['ev'][card['entry']]['fn']}
    vm.script = [13]
    vm.run('KR_T9CardPage', [k, mo])
    d = vm.dialogs[0]
    assert d['items'][0][:2] == (13, proxy(PLAY)) and d['items'][0][3] == 1, d['items'][0]
    assert NOTE_NONE in ko(d['title']).split('\n')
    assert vm.v('Play') == '' and vm.v('Req') == '' and vm.v('Unwind') == ''
    vm.reset()
    vm.vars.update({'YoruKR.T9.Ctx': 'C', 'YoruKR.T9.Req': '10001', 'YoruKR.T9.Unwind': '1'})
    vm.script = [11]
    assert home_run(vm) == 11 and vm.v('Req') == '' and vm.v('Unwind') == '' and vm.v('Play') == ''
    vm.calls = []
    vm.run_top('KR_T9HomeCasual')
    assert vm.calls == [('■カジュアルモード設定呼び出し', [])], vm.calls
    counts['V7_no_context'] += 1
    vm.reset()
    vm.vars.update({'YoruKR.T9.Play': '10001', 'YoruKR.T9.Playing': '1'})
    vm.script = [12]
    assert home_run(vm) == 12 and vm.v('Play') == '' and vm.v('Playing') == ''
    vm.calls = []
    vm.run_top('KR_T9HomeCasual')
    assert vm.calls == [('■カジュアルモード設定呼び出し', [])]
    counts['V8_failsafe'] += 1
    vm.reset()
    vm.script = [5, 0, 0]
    vm.run('KR_T8CharMissingMenu')
    assert len(vm.dialogs) == 3 and ko(vm.dialogs[1]['title']) == 'PLACE 5', [ko(d['title'])[:20] for d in vm.dialogs]
    vm.reset()
    vm.script = [1, 2, 0]
    vm.run('KR_T8CharMissingPage', [4])
    assert [c[0] for c in vm.calls] == ['KR_T8CharDatePage', 'KR_T8InfoPage'] and vm.calls[0][1] == [4], vm.calls
    counts['V9_original_dispatch'] += 1
    # summary from the month page and back; drawer page and memory page from the month pages
    vm.reset()
    vm.today = (6, 13)
    vm.script = [31, 0, 30, 0, 0]
    assert vm.run('KR_T9MonthPage', [6]) == 0
    assert [ko(d['title']).split('\n')[0][:4] for d in vm.dialogs] == ['〓6월 ', '〓달성도', '〓6월 ', '〓6월 ', '〓6월 '], [ko(d['title'])[:8] for d in vm.dialogs]
    assert ko(vm.dialogs[3]['title']).startswith('〓6월 · 이달의 서랍')
    counts['V11_summary_from_month'] += 1


# ============================================================== r18: replay lock (V16)
def scene_state(X, regs, flags, no):
    """r15's ○ △ ● from the model: 2 this save (IsRegisteredEvent), 1 another save (MsgSkip of the first message), 0 none."""
    e = X['ev'][no]
    if e['fn'] in regs:
        return 2
    if e['m0'] is not None and e['m0'] in flags:
        return 1
    return 0


def page_lock_check(d, st, ctx, counts, size=1, seen_stages=0):
    lines = ko(d['title']).split('\n')
    items = [(iid, ko(t), off) for iid, t, _, off in d['items']]
    ids = [iid for iid, _, _ in items]
    assert items[-1][:2] == (0, '돌아가기'), items
    if size > 1:
        assert (14, '단계 고르기 (%d단계)' % size) in [(i, t) for i, t, _ in items], items
    stage_txt = '¶단계 %d/%d' % (seen_stages, size)
    if st == 2:
        assert ids[0] == 13 and items[0][1] == PLAY, ('a scene seen in this save lost its replay item', items)
        assert items[0][2] == (0 if ctx in ('P', 'C') else 1), ('r15 context lock', ctx, items[0])
        sl = [l for l in lines if l.startswith(STATE_LINES[2])]
        assert len(sl) == 1, lines
        assert SANDBOX_NOTE in lines and OLD_WARN not in lines, ('sandbox note / old warning', lines)
        assert (NOTE_C in lines) == (ctx == 'C') and (NOTE_NONE in lines) == (ctx not in ('P', 'C')), (ctx, lines)
        assert LOCK_UNSEEN not in lines and LOCK_OTHER not in lines
        if size > 1:
            assert sl[0] == STATE_LINES[2] + '　' + stage_txt, sl
        counts['V16_open_pages'] += 1
    else:
        assert 13 not in ids, ('lock bypassed: 「이 장면 재생」 on a %s page' % '●△'[st], items)
        want = LOCK_UNSEEN if st == 0 else LOCK_OTHER
        ll = [l for l in lines if l.startswith(want)]
        assert len(ll) == 1, ('lock line missing', st, lines)
        assert not any(l.startswith(STATE_LINES[x]) for l in lines for x in (0, 1, 2)), ('the lock line replaces the state line', lines)
        assert SANDBOX_NOTE not in lines and OLD_WARN not in lines and NOTE_C not in lines and NOTE_NONE not in lines, lines
        if size > 1:
            if st == 1:
                assert ll[0] == want and lines[lines.index(ll[0]) + 1] == stage_txt, lines
            else:
                assert ll[0] == want + '　' + stage_txt, ll
        else:
            assert ll[0] == want
        counts['V16_locked_unseen' if st == 0 else 'V16_locked_other'] += 1
    for l in lines:
        assert len(l) <= 38, ('title line over 38', l)


def lock_checks(vm, X, counts):
    ev = X['ev']
    rnd = random.Random(20260928)
    withmsg = [no for no, e in sorted(ev.items()) if e['m0'] is not None]
    part = {e['fn'] for no, e in sorted(ev.items()) if rnd.random() < 0.5}
    flags = {ev[no]['m0'] for no in withmsg if ev[no]['fn'] not in part and rnd.random() < 0.6}
    states = [('none', set(), set()), ('partial', part, flags), ('all', {e['fn'] for e in ev.values()}, set())]
    place = proxy('6월 · 호시카와 · 특훈 뒤 대화')
    for sname, regs, fl in states:
        vm.registered, vm.flags = regs, fl
        for k, c in enumerate(X['cards']):
            st = scene_state(X, regs, fl, c['entry'])
            seen = sum(1 for s in c['stages'] if ev[s]['fn'] in regs)
            for ctx in ('P', 'C', ''):
                vm.reset()
                vm.vars['YoruKR.T9.Ctx'] = ctx
                vm.script = [0]
                vm.run('KR_T9CardPage', [k, c['month']])
                check_dialog(vm.dialogs[0], counts)
                page_lock_check(vm.dialogs[0], st, ctx, counts, size=c['size'], seen_stages=seen)
            # the answer 13 (play) on the page: a request only when ○ (a locked page has no such item; the code ignores it)
            vm.reset()
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            vm.glob[vm.G_FN] = 'E00001'
            vm.script = [13, 0]
            vm.run('KR_T9CardPage', [k, c['month']])
            if st == 2:
                assert vm.v('Play') == str(c['entry']) and vm.v('Unwind') == '1', (k, vm.v('Play'))
                assert vm.vars.get('YoruKR.T18.PrevSet') == '1' and vm.vars.get('YoruKR.T18.PrevFn') == 'E00001'
                counts['V16_card_requests'] += 1
            else:
                assert vm.v('Play') == '' and vm.v('Unwind') == '' and not vm.vars.get('YoruKR.T18.PrevSet'), ('locked card requested', k)
                counts['V16_card_refusals'] += 1
        for no in sorted(ev):
            st = scene_state(X, regs, fl, no)
            for ctx in (('P', 'C', '') if sname == 'partial' else ('P',)):
                vm.reset()
                vm.vars['YoruKR.T9.Ctx'] = ctx
                vm.script = [13 if ctx == 'P' else 0]
                vm.run('KR_T9EventPage', [no, place])
                check_dialog(vm.dialogs[0], counts)
                page_lock_check(vm.dialogs[0], st, ctx, counts)
                if ctx == 'P':
                    assert (vm.v('Play') == str(no)) == (st == 2) and (vm.v('Unwind') == '1') == (st == 2), (no, st, vm.v('Play'))
                    counts['V16_event_pages_answered'] += 1
    # bundles judged stage by stage through the stage list: odd stages seen in this save, even ones read elsewhere / unseen
    vm.flags = set()
    for k, c in enumerate(X['cards']):
        if c['size'] < 2:
            continue
        regs = {ev[s]['fn'] for i, s in enumerate(c['stages']) if i % 2 == 1}
        fl = {ev[s]['m0'] for i, s in enumerate(c['stages']) if i % 4 == 2 and ev[s]['m0'] is not None}
        vm.registered, vm.flags = regs, fl
        n = c['size']
        for i in range(n):
            vm.reset()
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            page, idx = divmod(i, 30)
            vm.script = [12] * page + [100 + i, 0] + [0]
            vm.run('KR_T9StagePage', [k, c['month']])
            d = vm.dialogs[page + 1]
            st = scene_state(X, regs, fl, c['stages'][i])
            page_lock_check(d, st, 'P', counts)
            assert ko(d['title']).split('\n')[0] == '〓%s · %s 묶음 · %d단계' % ('E%05d' % c['stages'][i], 'E%05d' % c['entry'], i + 1), ko(d['title']).split('\n')[0]
            counts['V16_bundle_stages'] += 1
        # the card page itself follows its entry (stage 1)
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'P'
        vm.script = [0]
        vm.run('KR_T9CardPage', [k, c['month']])
        page_lock_check(vm.dialogs[0], scene_state(X, regs, fl, c['entry']), 'P', counts, size=n,
                        seen_stages=sum(1 for s in c['stages'] if ev[s]['fn'] in regs))
    # 회상 · 그 밖 (memory replays and unused scenes): drawer -> scene page, the same lock
    vm.flags = set()
    mem = [(i, ch) for i, ch in enumerate(X['chips']) if ch['month'] == 12]
    for i, ch in mem:
        regs = {ev[s]['fn'] for j, s in enumerate(ch['scenes']) if j % 3 == 0}
        vm.registered = regs
        for j, s in enumerate(ch['scenes'][:4]):
            vm.reset()
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            vm.script = [100 + j, 0, 0]
            vm.run('KR_T9ChipPage', [i])
            page_lock_check(vm.dialogs[1], scene_state(X, regs, set(), s), 'P', counts)
            counts['V16_memory_pages'] += 1
    vm.flags = set()
    counts['V16_states'] = len(states)


# ============================================================== r18: sandbox (V17-V20)
REPLAY_PERSON, REPLAY_DELTA = 3, 300          # ■親密度上昇鏡花１ = C_Ability@AddFeeling(1 x 300) for person 3
ALLOWED_VARS = {'YoruKR.T8.TalkAuto', 'YoruKR.T8.TalkFlag'}     # event-time UI session variables (auto mode of talk events)


def sandbox_setup(vm, X, variant):
    """A save state at the home menu with the target card's entry seen in it; returns (target card index, card)."""
    vm.reset()
    vm.run_event = None
    vm.save_fail = False
    vm.vars_in_save = variant.get('vars_in_save', True)
    k, card = next((k, c) for k, c in enumerate(X['cards']) if c['month'] == 10 and c['lane'] == 3)
    regs = set(variant.get('regs', set())) | {X['ev'][card['entry']]['fn']}
    vm.registered = regs
    vm.flags = {X['ev'][s]['m0'] for s in list(X['ev'])[:40] if X['ev'][s]['m0'] is not None}
    vm.feel = {p: 1000 * p for p in range(1, 10)}
    vm.today = (10, 14)
    vm.glob = {vm.G_FN: 'E00258', vm.G_SYS: 0, vm.G_EVRESULT: 0, vm.G_BEGIN_SELECT: 0, vm.G_CAN_RETURN: variant.get('can_return', 0)}
    vm.files = {PREFIX + '01.asd': dict(kind='user'), PREFIX + '01.vsf': dict(kind='vsf'), PREFIX + '999.asd': dict(kind='user'),
                PREFIX + '999.vsf': dict(kind='vsf')}
    if variant.get('back_select'):
        vm.files[PREFIX + 'BackSelect1.asd'] = dict(kind='resume-game')
        vm.files[PREFIX + 'BackSelect1.vsf'] = dict(kind='vsf')
    if variant.get('stale_temp'):
        vm.files[TEMP] = dict(kind='resume', snap=dict(state=vm.saveable(), frames=[], push=0, rest=None))
        vm.files[TEMP_VSF] = dict(kind='vsf')
    return k, card


def replay_effects(X, log, chain, part=None):
    """What a replay does to the model (everything but the read marks must be undone by the sandbox)."""
    def effects(v):
        log['temp_during'] = TEMP in v.files and TEMP_VSF in v.files
        log['fn_at_start'] = v.glob[v.G_FN]
        log['stale_copy'] = copy.deepcopy(v.files.get(TEMP))
        v.feel[REPLAY_PERSON] = v.feel.get(REPLAY_PERSON, 0) + REPLAY_DELTA
        if part == 'save':
            v.user_save(PREFIX + '90.asd', rest=rest)
        rest(v)

    def rest(v):
        v.registered.add(X['ev'][chain]['fn'])
        v.glob[v.G_FN] = X['ev'][chain]['fn'][len('ＥＶ／元／'):]
        v.glob[v.G_EVRESULT] = 0
        v.glob[v.G_CAN_RETURN] = 1
        v.flags.add(987654)
        v.files[PREFIX + 'BackSelect1.asd'] = dict(kind='resume-game')
        v.files[PREFIX + 'BackSelect1.vsf'] = dict(kind='vsf')
        v.vars['YoruKR.T8.TalkAuto'] = '0'
    return effects


def request_from_window(vm, X, card):
    """Home menu -> character row -> lane page -> first card -> 이 장면 재생 (the player's path, context P)."""
    vm.script = [PICK]
    assert home_run(vm) == PICK and vm.v('Ctx') == 'P'
    vm.script = [3, 100, 13]
    vm.dialogs = []
    vm.run('KR_T8CharMissingPage', [card['lane'] + 1])
    assert vm.v('Play') == str(card['entry']) and vm.v('Unwind') == '1', ('request not made', vm.v('Play'))
    vm.script = []
    vm.dialogs = []
    assert home_run(vm) == 3 and not vm.dialogs


def state_diff(before, after, counts=None):
    """Differences outside the allow list: read marks (global), the game's own post-load deletion of the back-to-choice
    files and flag, event-time UI session variables. Everything else must be equal."""
    out = []
    for key in ('registered', 'feel', 'today'):
        if before[key] != after[key]:
            out.append((key, before[key] ^ after[key] if isinstance(before[key], set) else (before[key], after[key])))
    for g in set(before['glob']) | set(after['glob']):
        if before['glob'].get(g) != after['glob'].get(g) and g != VM.G_CAN_RETURN:
            out.append(('glob', g, before['glob'].get(g), after['glob'].get(g)))
    if after['glob'].get(VM.G_CAN_RETURN) not in (0, before['glob'].get(VM.G_CAN_RETURN)):
        out.append(('glob', VM.G_CAN_RETURN, before['glob'].get(VM.G_CAN_RETURN), after['glob'].get(VM.G_CAN_RETURN)))
    for kv in set(before['vars']) | set(after['vars']):
        if before['vars'].get(kv) != after['vars'].get(kv) and kv not in ALLOWED_VARS:
            out.append(('var', kv, before['vars'].get(kv), after['vars'].get(kv)))
    game_temp = {PREFIX + n + e for n in ('TempSelect', 'BackSelect1', 'BackSelect2', 'SystemSuspend', 'Reload') for e in ('.asd', '.vsf')}
    fb, fa = set(before['files']), set(after['files'])
    extra = fa - fb
    gone = {f for f in fb - fa if f not in game_temp and f not in (TEMP, TEMP_VSF)}      # a leftover temp file is cleaned up
    if extra or gone:
        out.append(('files', sorted(extra), sorted(gone)))
    return out


def sandbox_checks(vm, X, counts):
    ev = X['ev']
    # the model's .vsf name = the game's own TransAddSaveFileName run in the VM
    got = VM.run(vm, 'gamesave::detail::TransAddSaveFileName', [TEMP])
    assert got == vsf(TEMP) == TEMP_VSF, got
    _, target = sandbox_setup(vm, X, {})
    chain = next(no for no in sorted(ev) if no > 30000 and no != target['entry'])      # a later event the replay registers
    variants = [dict(vars_in_save=True), dict(vars_in_save=False), dict(vars_in_save=True, can_return=1, back_select=True),
                dict(vars_in_save=False, stale_temp=True)]
    rows = []
    for var in variants:
        k, card = sandbox_setup(vm, X, var)
        log = {}
        vm.run_event = replay_effects(X, log, chain)
        before = vm.state_all()
        request_from_window(vm, X, card)
        assert vm.vars.get('YoruKR.T18.PrevSet') == '1' and vm.vars.get('YoruKR.T18.PrevFn') == 'E00258'
        vm.calls = []
        vm.run_top('KR_T9HomeCasual')
        vm.script = [11]
        assert home_run(vm) == 11
        after = vm.state_all()
        names = [c[0] for c in vm.calls if c[0] != 'delete']
        assert names == ['LSys3xScript::Prepare', 'gamesave::detail::セーブ実行', 'LSys3xScript::RunEvent', 'gamesave::detail::ロード実行',
                         'post_load', '■ＡＤＶ消し'], names
        assert log['temp_during'], 'the temp file does not exist while the scene plays'
        assert log['fn_at_start'] == ev[card['entry']]['fn'][len('ＥＶ／元／'):], ('RunEvent did not start on the prepared scene', log)
        assert TEMP not in vm.files and TEMP_VSF not in vm.files, 'temp file left after the replay'
        dels = [c[1][0] for c in vm.calls if c[0] == 'delete']
        assert dels.count(TEMP) >= 2 and dels.count(TEMP_VSF) >= 2, dels
        d = state_diff(before, after)
        assert not d, ('global state differs after the sandbox', var, d[:4])
        assert after['glob'][vm.G_FN] == before['glob'][vm.G_FN] == 'E00258' and after['glob'][vm.G_SYS] == 0, 'Prepare\'s globals not restored'
        assert after['feel'][REPLAY_PERSON] == before['feel'][REPLAY_PERSON], 'affinity not restored'
        assert 987654 in after['flags'], 'read marks are global (kept) in the model'
        rows.append(dict(variant=var, calls=names, allowed=dict(flags_added=sorted(after['flags'] - before['flags']),
                                                                files_removed=sorted(set(before['files']) - set(after['files'])),
                                                                can_return=[before['glob'][vm.G_CAN_RETURN], after['glob'][vm.G_CAN_RETURN]],
                                                                vars=sorted(k for k in set(before['vars']) | set(after['vars'])
                                                                            if before['vars'].get(k) != after['vars'].get(k)))))
        counts['V17_sandbox_runs'] += 1
        counts['V17_state_keys_compared'] += len(before['glob']) + len(before['feel']) + len(before['registered']) + 1
    # V18: saved during the replay, loaded after the sandbox finished
    for stale in (False, True):
        k, card = sandbox_setup(vm, X, dict(vars_in_save=True))
        log = {}
        vm.run_event = replay_effects(X, log, chain, part='save')
        before = vm.state_all()
        request_from_window(vm, X, card)
        vm.calls = []
        vm.run_top('KR_T9HomeCasual')
        mine = {PREFIX + '90.asd', PREFIX + '90.vsf'}                                   # the player's own mid-replay save
        d = [x for x in state_diff(before, vm.state_all()) if not (x[0] == 'files' and set(x[1]) <= mine and not x[2])]
        assert not d, ('sandbox did not restore before the mid-replay load', d)
        assert PREFIX + '90.asd' in vm.files
        if stale:
            vm.files[TEMP] = log['stale_copy']
            vm.files[TEMP_VSF] = dict(kind='vsf')
        vm.calls = []
        vm.run_event = None
        vm.resume(vm.files[PREFIX + '90.asd']['snap'])
        names = [c[0] for c in vm.calls if c[0] != 'delete']
        after = vm.state_all()
        if not stale:
            assert names == ['post_load', '■ＡＤＶ消し'], ('the mid-replay load must skip the restore', names)
            assert after['feel'][REPLAY_PERSON] == before['feel'][REPLAY_PERSON] + REPLAY_DELTA, 'the loaded replay should keep its effects'
            assert ev[chain]['fn'] in after['registered'] and after['glob'][vm.G_FN] == ev[chain]['fn'][len('ＥＶ／元／'):]
            assert TEMP not in vm.files and not vm.vars.get('YoruKR.T18.PrevSet')
            counts['V18_mid_replay_load_no_temp'] += 1
        else:
            assert names == ['post_load', 'gamesave::detail::ロード実行', 'post_load', '■ＡＤＶ消し'], names
            d = [x for x in state_diff(before, after) if not (x[0] == 'files' and set(x[1]) <= mine and not x[2])]
            assert not d, ('a leftover temp file must restore', d)
            assert TEMP not in vm.files and TEMP_VSF not in vm.files
            counts['V18_mid_replay_load_temp_left'] += 1
    # V19: ResumeSave fails
    for vis in (True, False):
        k, card = sandbox_setup(vm, X, dict(vars_in_save=vis))
        log = {}
        vm.run_event = replay_effects(X, log, chain)
        vm.save_fail = True
        before = vm.state_all()
        request_from_window(vm, X, card)
        vm.calls = []
        vm.run_top('KR_T9HomeCasual')
        vm.save_fail = False
        names = [c[0] for c in vm.calls if c[0] != 'delete']
        assert 'LSys3xScript::RunEvent' not in names, ('replayed although the resume save failed', names)
        assert ('simple', NOTICE_FAIL) in vm.calls and ('msgbox', ['save failed: ' + TEMP]) in vm.calls, vm.calls
        assert names[-1] == '■ＡＤＶ消し'
        vm.script = [11]
        assert home_run(vm) == 11
        assert not state_diff(before, vm.state_all()), ('state after a failed resume save', state_diff(before, vm.state_all()))
        assert TEMP not in vm.files and TEMP_VSF not in vm.files
        counts['V19_save_failure'] += 1
    # V20: a request that reaches the casual site for a scene not seen in this save
    k, card = sandbox_setup(vm, X, dict(vars_in_save=True))
    unseen = next(s for s in sorted(ev) if ev[s]['fn'] not in vm.registered)
    vm.run_event = replay_effects(X, {}, chain)
    files0 = sorted(vm.files)
    vm.vars['YoruKR.T9.Play'] = str(unseen)
    vm.script = []
    assert home_run(vm) == 3
    vm.calls = []
    vm.run_top('KR_T9HomeCasual')
    names = [c[0] for c in vm.calls]
    assert names == ['LSys3xScript::Prepare', 'simple', '■ＡＤＶ消し'] and vm.calls[1] == ('simple', NOTICE_LOCK), vm.calls
    assert sorted(vm.files) == files0
    counts['V20_casual_site_lock'] += 1
    vm.run_event = None
    vm.files = {}
    return dict(variants=rows, temp_file=TEMP, temp_info_file=TEMP_VSF)


