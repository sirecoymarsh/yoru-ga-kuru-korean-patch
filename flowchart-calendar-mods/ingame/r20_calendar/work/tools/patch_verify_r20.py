"""r20 one-off: turn the r19 verifier copy (verify_calendar_r20.py) into the r20 verifier. Run once."""
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'verify_calendar_r20.py'
s = p.read_text(encoding='utf8')
assert 'r20_count_checks' not in s, 'already patched'


def rep(a, b, count=1):
    global s
    assert s.count(a) == count, (a[:90], s.count(a))
    s = s.replace(a, b)


# ------------------------------------------------------------------ docstring
head_end = s.index('import sys, json, re, struct')
s = '''"""Claude Opus 5.5 (2026-09-28) r20: verification of the calendar candidate without the game (after verify_calendar_r19.py).

  python verify_calendar_r20.py              all checks (must pass)
  python verify_calendar_r20.py --selftest   all checks, then every check again against a planted defect (each must fail): 35
  python verify_calendar_r20.py --native     compare what the native probe logged (titles, rows, lists, the home panel, the
                                             sandbox before/after state, the lock pages, AND the r20 texts, labels, brightness,
                                             part counts) with the VM for the same save

Base = the r19 install (= the r19 candidate). r20 = the status window's 「이벤트」 page + the partner-select labels.
Static (bytes of base vs candidate, read only):
  S1 candidate = manifest; every base function entry identical (r20 has no forwarder and relocates nothing); non-function
     metadata identical; every added function is KR_T20*; r19's five and r18's eight forwarders still forward
  S2 the base CODE is unchanged except the 4-byte operands of r20's seven same-length sites; r15's nine and r18's one site still
     hold their operands
  S3 MSG1 identical, STR0 prefix identical; the payload is the AIN only (PACT/EX/FNL/help-menu chart untouched)
  S4 user saves (copies, every RSM resume file): every saved frame resolves to the same function entry and the same bytes at its
     return address in the candidate (incl. the two saves made inside the partner selection, NightR34/NightR40)
  S5 native opcode audit of the candidate against the runtime exe dispatch table
  S6 the six pinned functions: index, address and every code byte identical to the base; the first five vs the r15 candidate
     differ only in r18's operand
  S7 KR_T18RunSandboxed has RunEvent's signature and KR_T9HomeCasual still calls it
  S8 r20's seven sites: the original callee and the replacement have the same signature, each site is the only call of that
     callee in its owner, no site inside a pinned function; the four CALLMETHOD shims pass `this` on
Extended VM (the candidate's own compiled bodies, engine calls modelled; r20 adds struct pages, CALLMETHOD and PartsEngine):
  V1-V26 r19's checks (tables, geometry, day cells, navigation, flows, seen states, counts, rows, panel, real saves, bars, lock,
      sandbox, names, affinity)
  V27 counts: 특훈 뒤 대화 본 수 · 이달 남은 특훈 뒤 대화 · 던전 동행 남은 장면(상대별) for every person and state = an independent
      model from the chart drawers + graph/schedule.json; the sums agree with the calendar's own drawer rows (KR_T18ChipCount)
  V28 「이달」: the remaining count follows today's month (every month 4-11 = the model; it changes between months)
  V29 the 「이벤트」 page text of every person = the model (0-rows left out, partners who have not joined yet left out, total =
      the sum of the rows, at most 13 lines, every line inside the panel)
  V30 the status window in the VM: 1->2->3->4->1 and 1->4->3->2->1, page 0 unchanged, the page-4 parts (panel + text) exist only on
      page 4, redrawn for another person (SetInfo), gone when the window closes (KR_T20StEnd), the same count when entered again
  V31 the partner screen in the VM: one box + one label per shown portrait (none for a hidden one), label = the model, the hovered
      person bright (255) and the others dim (128), all bright with no hover, all gone after the wait (KR_T20TrKeyDel), the same
      count when entered again, no second set when the loop asks again
  V32 the training-count source read from the base code: C_Ability.training is a point pool (battle / fixed income add to it,
      Saturday ReflectStatus spreads it over four stats and SetTraining(0) empties it) -> not a count
  V33 no per-person dungeon companion counter in C_Ability, L_Party, L_BattleIncome, L_DungeonInfo (members and globals listed)
"""
''' + s[head_end:]

rep("import r20lib as L\n", "import r20lib as L\n")
rep("FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',\n"
    "           'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}          # r19 forwarders",
    "FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',\n"
    "           'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}          # r19 forwarders (in the base since r19)")
rep("        data = V2.build(str(L.TMP / 'chart_v2_from_r19_verify.html'))",
    "        data = V2.build(str(L.TMP / 'chart_v2_from_r20_verify.html'))")

# ------------------------------------------------------------------ VM: struct pages, CALLMETHOD, PartsEngine
rep("""        self.save_fail = False          # セーブ実行: ResumeSave reports nSucceeded 0 (nothing written)
        self.vars_in_save = True        # does the resume image carry the SystemService session variables?""",
    """        self.save_fail = False          # セーブ実行: ResumeSave reports nSucceeded 0 (nothing written)
        self.vars_in_save = True        # does the resume image carry the SystemService session variables?
        # r20 model: PartsEngine parts by number, activity part names, the hovered portrait of the partner screen
        self.parts = {}
        self.act = {}
        self.hover = 0""")
rep("    def run(self, name, args=(), resume=None):", "    def run(self, name, args=(), resume=None, this=None):")
rep("""                elif op == 'RETURN':
                    assert len(st) == int(f['return-type'][0] != 0), (name, st)
                    return st[0] if st else None""",
    """                elif op == 'PUSHSTRUCTPAGE':
                    assert this is not None, ('PUSHSTRUCTPAGE outside a method call', name)
                    st.append(this)
                elif op == 'CALLMETHOD':
                    n = int(arg, 0)
                    aa = st[-n:] if n else []
                    st = st[:-n] if n else st
                    fid = st.pop()
                    obj = st.pop()
                    ff = self.meta['functions'][fid]
                    rec.update(pc=pc, st=list(st), ret=ff['return-type'][0] != 0)
                    out = self.method(fid, obj, aa)
                    if ff['return-type'][0] != 0:
                        st.append(out)
                elif op == 'SP_INC':
                    st.pop()
                elif op == 'RETURN':
                    assert len(st) == int(f['return-type'][0] != 0), (name, st)
                    return st[0] if st else None""")
rep("""    def hll(self, lib, method, st):
        if lib == 'SystemService':""",
    """    # ---- r20: the objects r20's code touches (status view, training view) as struct pages {member index: value}
    ST_ACT = 'Game\\\\Scenes\\\\4000Homebase\\\\CharaStatus.pact'
    ALLY_ACT = 'Game\\\\Scenes\\\\Common\\\\SelectAlly.pact'
    ST_ROOT = 1000010472
    PORTRAIT = 1000010484                 # + p: the SelectAlly portrait CG of person p

    def status_view(self, chara, page=1, show_item=True):
        self.act[VM.ST_ACT] = {'ルートパーツ': VM.ST_ROOT}
        self.parts.setdefault(VM.ST_ROOT, dict(kind='root', show=1))
        return {1: {4: VM.ST_ACT}, 2: 0, 11: chara, 15: int(show_item), 16: page, 'shown': None}

    def training_view(self, shown):
        names = '０１２３４５６７'
        self.act[VM.ALLY_ACT] = {'ＣＧ_キャラ' + names[p - 1]: VM.PORTRAIT + p for p in range(2, 9)}
        for p in range(2, 9):
            self.parts[VM.PORTRAIT + p] = dict(kind='portrait', person=p, show=int(p in shown))
        return {10: {0: {4: VM.ALLY_ACT}, 1: 0}, 'kind': 'C_SceneTrainingView'}

    def method(self, fid, obj, aa):
        name = L.raw_symbol(self.meta, fid)
        self.calls.append(('method', name, list(aa)))
        if name == 'C_HomeStatusView@SetActivePage':
            page = aa[0]
            obj[16] = page
            obj['shown'] = dict(basic=page in (0, 1), item=page != 0 and bool(obj[15]), skill=page == 3, weapon=page == 2,
                                switch=page != 0, feeling=page in (0, 1))
            return None
        if name == 'C_HomeStatusView@NowPage::get':
            return obj[16]
        if name in ('C_HomeStatusView@NextPage', 'C_HomeStatusView@PrevPage'):
            # the original bodies: if (NowPage == 0) return; page = NowPage = NowPage +- 1; wrap 3 -> 1 / 1 -> 3; SetActivePage(page)
            if obj[16] == 0:
                return None
            page = obj[16] + (1 if name.endswith('NextPage') else -1)
            obj[16] = page
            if page > 3:
                page = 1
            if page < 1:
                page = 3
            return self.method(self.fs['C_HomeStatusView@SetActivePage']['index'], obj, [page])
        if name == 'C_HomeStatusView@SetInfo':
            # the original sets m_CharaNo and the portrait, then SetActivePage(NowPage) at the r20 site -> KR_T20StActive (S8)
            obj[11] = aa[0]
            return self.method(self.fs['KR_T20StActive']['index'], obj, [obj[16]])
        if name == 'C_SceneTrainingView@GetOnmouseChara':
            return self.hover
        if name == 'C_SceneTrainingView@AppearStandChara':
            return None
        if name == 'C_SceneTrainingView@SelectAlly::get':
            return obj[10]
        if name.startswith('KR_T20'):
            return self.run(name, aa, this=obj)
        raise AssertionError(('unmodelled method', name))

    def part(self, n):
        return self.parts.setdefault(n, dict(kind='new', show=0))

    def parts_hll(self, method, st):
        # (number of arguments, returns a value)
        sig = dict(IsExist=(1, True), Release=(1, False), GetActivityPartsNumber=(2, True), IsComponentShow=(1, True),
                   Parts_SetText=(3, True), Parts_SetFont=(12, True), Parts_SetTextEnableTag=(3, False),
                   Parts_SetTextLineSpace=(3, True), Parts_SetParentPartsNumber=(2, False), SetComponentPos=(3, False),
                   SetComponentPosZ=(2, False), SetComponentShow=(2, False), SetComponentMulColor=(4, False))
        assert method in sig, ('unmodelled PartsEngine call', method)
        n, ret = sig[method]
        a = st[-n:]
        del st[-n:]
        out = None
        if method == 'IsExist':
            out = int(a[0] in self.parts)
        elif method == 'Release':
            self.parts.pop(a[0], None)
            self.calls.append(('release', a[0]))
        elif method == 'GetActivityPartsNumber':
            out = self.act.get(a[0], {}).get(a[1], 0)
        elif method == 'IsComponentShow':
            out = int(bool(self.parts.get(a[0], {}).get('show')))
        elif method == 'Parts_SetText':
            self.part(a[0]).update(text=a[1], state=a[2])
            out = 1
        elif method == 'Parts_SetFont':
            self.part(a[0])['font'] = tuple(a[1:11])
            out = 1
        elif method == 'Parts_SetTextEnableTag':
            self.part(a[0])['tag'] = int(bool(a[1]))
        elif method == 'Parts_SetTextLineSpace':
            self.part(a[0])['linespace'] = a[1]
            out = 1
        elif method == 'Parts_SetParentPartsNumber':
            self.part(a[0])['parent'] = a[1]
        elif method == 'SetComponentPos':
            self.part(a[0])['pos'] = (a[1], a[2])
        elif method == 'SetComponentPosZ':
            self.part(a[0])['z'] = a[1]
        elif method == 'SetComponentShow':
            self.part(a[0])['show'] = int(bool(a[1]))
        elif method == 'SetComponentMulColor':
            self.part(a[0])['mul'] = tuple(a[1:4])
        if ret:
            st.append(out)

    def ours(self):
        return sorted(n for n in self.parts if 2026092000 <= n < 2026092100)

    def hll(self, lib, method, st):
        if lib == 'PartsEngine':
            self.parts_hll(method, st)
            return
        if lib == 'SystemService':""")
rep("""        if name == 'KR_T8PlaceText':
            return proxy('PLACE %d' % aa[0])""",
    """        if name == 'KR_T8PlaceText':
            return proxy('PLACE %d' % aa[0])
        # r20: the construction helpers the panels use (parts::detail construction process), the direction-key cleanup
        if name == 'Ｐ＿構築手順＿作成':
            self.part(aa[0]).update(construct=[('create', aa[1], aa[2])], state=aa[3])
            return None
        if name in ('Ｐ＿構築手順＿色塗り全', 'Ｐ＿構築手順＿色塗り'):
            self.part(aa[0]).setdefault('construct', []).append(('fill',) + tuple(aa[1:-1]))
            return None
        if name == 'Ｐ＿構築ビルド':
            self.part(aa[0])['built'] = 1
            return None
        if name in ('■方向キー処理／削除', 'AFL_Parts_EraseWholeMouseWheelEvent'):
            self.calls.append((name, list(aa)))
            return None""")

# ------------------------------------------------------------------ static checks for r20
start = s.index('def static_checks(')
end = s.index('# ============================================================== VM checks')
s = s[:start] + r'''def r20_sites(man):
    sites = man['same_length_sites']
    assert len(sites) == 7, len(sites)
    return sites


def static_checks(base, cand, man, m, nm, counts, mutate_bytes=None, mutate_meta=None, parts=('S1', 'S2', 'S3', 'S4', 'S6', 'S7', 'S8')):
    bb = base.read_bytes()
    cb = cand.read_bytes()
    if mutate_bytes:
        cb = mutate_bytes(cb)
    if mutate_meta:
        nm = mutate_meta(copy.deepcopy(nm))
    assert L.sha_bytes(cb) == man['files']['NightRemaster.ain']['sha256'] or mutate_bytes, 'candidate != manifest'
    old = L.unpack(bb)
    new = L.unpack(cb)
    oldn = struct.unpack_from('<I', old, 12)[0]
    fw = {L.fid_of(m, n) for n in FORWARD}
    swap = r18_site()
    sb = L.fid_of(nm, L.SANDBOX)
    r20s = r20_sites(man)
    if 'S1' in parts:
        for f in m['functions']:
            assert nm['functions'][f['index']] == f, ('base function entry changed', f['index'], f['name'])
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
        assert all(n.startswith('KR_T20') for n in man['added_functions']), 'added functions must all be KR_T20*'
        assert not any(L.raw_symbol(nm, f['index']).startswith(('KR_T16', 'KR_T17')) for f in nm['functions']), 'r16/r17 names in the candidate'
        cv = L.versions(W / 'candidate_raw_code.jam')
        for old_, new_ in list(FORWARD.items()) + list(R18_FORWARD.items()):
            v = L.live_version(nm, cv, L.fid_of(nm, old_))
            assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
        counts['S1_metadata'] += 1
    if 'S2' in parts:
        allowed = {x for s_ in r20s for x in range(s_['site'] + 2, s_['site'] + 6)}
        diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
        assert set(diff) <= allowed, ('base CODE bytes changed outside r20\'s operands', [hex(x) for x in diff if x not in allowed][:8])
        for s_ in r20s:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['before'], ('r20 site: the base holds another operand', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('r20 site not applied', s_['function'], s_['replacement'])
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s_ in rman['same_length_sites'] + [swap]:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap missing in the base', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap site no longer applied', s_['function'], s_['replacement'])
        assert bytes(new[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, sb), 'KR_T9HomeCasual no longer calls KR_T18RunSandboxed'
        counts['S2_earlier_same_length_sites_kept'] = len(rman['same_length_sites']) + 1
        counts['S2_r20_same_length_sites'] = len(r20s)
        counts['S2_base_code_bytes'] = oldn
        counts['S2_base_code_bytes_changed'] = len(diff)
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed'] and not man['fnl_changed'] and not man['chart_changed']
        assert L.sha(L.runtime()[1] / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA
        counts['S3_text'] += 1
    if 'S6' in parts:
        rv = L.versions(L.base_paths()['raw'])
        starts = sorted({v['start'] for vs in rv.values() for v in vs})
        ccode = new[16:16 + struct.unpack_from('<I', new, 12)[0]]
        bcode = old[16:16 + oldn]
        ra = L.R15 / 'candidate' / 'NightRemaster.ain'
        rraw = L.unpack(ra.read_bytes())
        rcode = rraw[16:16 + struct.unpack_from('<I', rraw, 12)[0]]
        rm = L.read_meta(L.R15 / 'work' / 'build' / 'candidate_meta.json')
        for name in L.PINNED_ALL:
            i = L.fid_of(m, name)
            f = m['functions'][i]
            assert nm['functions'][i] == f, ('pinned function entry changed', name)
            j = bisect.bisect_right(starts, f['address'])
            end = starts[j] - 6 if j < len(starts) else oldn
            lo = f['address'] - 6
            assert ccode[lo:end] == bcode[lo:end], ('pinned code changed', name)
            if name in L.PINNED:
                assert rm['functions'][L.fid_of(rm, name)] == f, ('pinned entry differs from r15', name)
                differ = [lo + k for k in range(end - lo) if rcode[lo + k] != bcode[lo + k]]
                if name == L.SWAP_OWNER:
                    assert differ and set(differ) <= set(range(swap['site'] + 2, swap['site'] + 6)), ('KR_T9HomeCasual differs from r15 beyond r18\'s operand', differ[:8])
                else:
                    assert not differ, ('pinned code differs from r15', name)
            counts['S6_pinned_bytes'] += end - lo
        counts['S6_pinned_functions'] = len(L.PINNED_ALL)
    if 'S7' in parts:
        g, r = nm['functions'][sb], nm['functions'][L.fid_of(nm, L.SWAP_OLD)]
        assert g['arguments'] == r['arguments'] == [] and g['return-type'] == r['return-type'] == [47, -1, 0, None], 'sandbox signature'
        assert man['pinned_functions'][L.SANDBOX]['index'] == sb and man['pinned_functions'][L.SANDBOX]['address'] == g['address']
        counts['S7_sandbox_signature_equal_RunEvent'] = 1
    if 'S8' in parts:
        cv = L.versions(W / 'candidate_raw_code.jam')
        for s_ in r20s:
            o, r = nm['functions'][s_['original_fid']], nm['functions'][s_['replacement_fid']]
            assert [a['type'] for a in o['arguments']] == [a['type'] for a in r['arguments']] and o['return-type'] == r['return-type'], ('r20 site signature', s_['replacement'])
            assert s_['calls_of_original_in_function'] == 1, s_
            assert s_['function'] not in L.PINNED_ALL, ('an r20 site inside a pinned function', s_['function'])
            assert L.raw_symbol(nm, s_['replacement_fid']) == s_['replacement'] and s_['replacement'].startswith('KR_T20')
            opcode = 0x30 if s_['kind'] == 'CALLFUNC' else 0x00
            assert bytes.fromhex(s_['after']) == struct.pack('<Hi', opcode, s_['replacement_fid'])
        for shim, tail in (('KR_T20StNext', ['PUSHSTRUCTPAGE', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StNextOf'), 'RETURN']),
                           ('KR_T20StPrev', ['PUSHSTRUCTPAGE', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StPrevOf'), 'RETURN']),
                           ('KR_T20StActive', ['PUSHSTRUCTPAGE', '.LOCALREF 0x0', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StActiveOf'), 'RETURN'])):
            v = L.live_version(nm, cv, L.fid_of(nm, shim))
            got = [op for _, op in v['ops'] if not op.startswith('ENDFUNC')]
            assert got == tail, ('CALLMETHOD shim body', shim, got)
        counts['S8_r20_sites_checked'] = len(r20s)
    if 'S4' not in parts:
        return []
    vers = L.versions(L.base_paths()['raw'])
    bycrc = collections.defaultdict(list)
    for f in m['functions']:
        bycrc[f['crc'] & 0xffffffff].append(f)
    frames = []
    live = 0
    r20_owners = {s_['function'] for s_ in r20s}
    for name, path in L.resume_saves().items():
        row_ = L.save_records(path)
        assert row_ is not None, name
        for rr in [row_['ip']] + row_['returns']:
            if rr['address'] == -1:
                continue
            start = rr['address'] - rr['offset']
            choices = [f for f in bycrc[rr['crc']] if rr['name'].startswith(L.raw_symbol(m, f['index']) + '(')
                       and any(v['start'] == start for v in vers[f['index']])]
            assert len(choices) == 1, (name, rr)
            f = choices[0]
            assert f['index'] not in fw or start != f['address'], ('a saved frame is inside a forwarded function', name)
            assert nm['functions'][f['index']] == f, ('saved frame function moved', name, f['name'])
            ad = rr['address']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes(new[16 + ad:16 + ad + 6]), ('saved return bytes differ', name, rr['name'][:40], hex(ad))
            live += int(start == f['address'])
            frames.append(dict(file=name, fid=f['index'], offset=rr['offset'], live=start == f['address'], function=L.raw_symbol(m, f['index']),
                               address=ad))
    # frames resolved to a lambda compiled inline into an r20 owner (the engine names the frame after the lambda): the return
    # address lies in the owner's code; its bytes are compared above
    counts['S4_saves'] = len({x['file'] for x in frames})
    counts['S4_frames'] = len(frames)
    counts['S4_frames_in_live_versions'] = live
    counts['S4_frames_in_KR_T9HomeCasual'] = sum(1 for x in frames if x['function'] == 'KR_T9HomeCasual')
    counts['S4_frames_in_KR_T18RunSandboxed'] = sum(1 for x in frames if x['function'] == L.SANDBOX)
    counts['S4_frames_in_forwarded'] = sum(1 for x in frames if x['function'] in FORWARD)
    counts['S4_frames_in_r20_owners'] = sum(1 for x in frames if x['function'] in r20_owners or 'RunSelectPartner' in x['function'])
    return frames


''' + s[end:]

# ------------------------------------------------------------------ r20 checks
anchor = '# ============================================================== defects to plant (each must make its check fail)'
R20 = r'''# ============================================================== r20: counts, the 「이벤트」 page, the partner labels
PARTY_Q = [2, 3, 4, 5, 6, 7, 8]
R20_TALK = ('prio', 'after', 'turned')
R20_LEFT = ('after', 'prio', 'invite')
GOLD, CYAN, GRAY = 'r=255 g=224 b=96', 'r=128 g=224 b=255', 'r=150 g=150 b=150'
ST_PANEL, ST_TEXT, TR_BASE, TR_BOX = 2026092001, 2026092002, 2026092010, 2026092020
ST_FONT = (257, 24, 255, 255, 255, 0.0, 0, 0, 0, 0.0)
TR_FONT = (257, 20, 255, 255, 255, 0.0, 0, 0, 0, 0.0)
ST_LINE_PX = 24                   # the page text is 24 px; one full-width glyph ~ 24 px, ASCII half
ST_TEXT_MAX_PX = 530 - 212        # the panel's inner right edge (192 + 338) minus the text start (160 + 52)


def r20_pairs(X):
    out = {}
    for ch in X['chips']:
        if KINDS[ch['kind']] != 'walk':
            continue
        for no in ch['scenes']:
            e = X['sch'][no]
            assert e['category'] == 'dungeon_walk', no
            out[no] = (e['person'], e['person2'] or 0)
    return out


def r20_join(X):
    return {LANES.index(lane) + 1: md[0] * 100 + md[1] for lane, md in X['data']['join'].items()}


def r20_month(today):
    return min(11, max(4, today[0]))


def r20_talk(X, regs, p):
    return sum(1 for ch in X['chips'] if 4 <= ch['month'] <= 11 and ch['lane'] == p - 1 and KINDS[ch['kind']] in R20_TALK
               for s in ch['scenes'] if X['ev'][s]['fn'] in regs)


def r20_left(X, regs, p, today):
    m = r20_month(today)
    return sum(1 for ch in X['chips'] if ch['month'] == m and ch['lane'] == p - 1 and KINDS[ch['kind']] in R20_LEFT
               for s in ch['scenes'] if X['ev'][s]['fn'] not in regs)


def r20_walk(X, regs, p, q):
    n = 0
    for no, (a, b) in r20_pairs(X).items():
        if X['ev'][no]['fn'] in regs:
            continue
        if (a, b) == (p, q) or (q > 0 and (a, b) == (q, p)):
            n += 1
    return n


def r20_joined(X, q, today):
    j = r20_join(X).get(q)
    return j is None or today[0] * 100 + today[1] >= j


def tint(t, rgb):
    return '' if t == '' else '${font ' + rgb + '}' + t + '${/font}'


def r20_status_text(X, regs, c, today):
    t = tint('이벤트', GOLD)
    if c < 2 or c > 8:
        return t + '\n동료의 쪽에서만 셉니다' + '\n\n' + tint('달력에서 자세히', GRAY)
    t += '\n특훈 뒤 대화 ' + tint(str(r20_talk(X, regs, c)), CYAN) + '번 봄'
    t += '\n이달 남은 특훈 뒤 대화 ' + tint(str(r20_left(X, regs, c, today)), CYAN)
    rows = []
    total = 0
    for q in PARTY_Q:
        if q == c or not r20_joined(X, q, today):
            continue
        k = r20_walk(X, regs, c, q)
        if k > 0:
            total += k
            rows.append('　' + PARTY_KR[q - 2] + '와 ' + tint(str(k), CYAN))
    k = r20_walk(X, regs, c, 0)
    if k > 0:
        total += k
        rows.append('　단둘이 ' + tint(str(k), CYAN))
    t += '\n던전 동행 남은 장면 ' + tint(str(total), CYAN) + ''.join('\n' + r for r in rows)
    return t + '\n\n' + tint('달력에서 자세히', GRAY)


def r20_label_text(X, regs, p, today):
    return '대화 ' + tint(str(r20_talk(X, regs, p)), CYAN) + '번 봄\n남은 대화 ' + tint(str(r20_left(X, regs, p, today)), CYAN)


def untag(t):
    return re.sub(r'\$\{/?font[^}]*\}', '', t)


def r20_states(X, regs, abo, mid_regs, mid_today):
    all_regs = {e['fn'] for e in X['ev'].values()}
    return [('none 4/9', set(), (4, 9)), ('partial 6/13', regs, (6, 13)), ('all 11/10', all_regs, (11, 10)),
            ('all_but_one 7/20', abo, (7, 20)), ('mid-August', mid_regs, mid_today), ('partial 5/18 (before 마나미 joins)', regs, (5, 18)),
            ('partial 6/29 (before 마코토 joins)', regs, (6, 29))]


def r20_count_checks(vm, X, counts, states):
    """V27 (+ the calendar's own drawer rows) and V28 (the month)."""
    for tag, regs, today in states:
        vm.registered = regs
        vm.today = today
        for p in PARTY_Q:
            assert vm.run('KR_T20TalkSeen', [p]) == r20_talk(X, regs, p), ('V27 특훈 뒤 대화 본 수', tag, p)
            assert vm.run('KR_T20TrainLeft', [p]) == r20_left(X, regs, p, today), ('V27 이달 남은 특훈 뒤 대화', tag, p)
            for q in [0] + PARTY_Q:
                if q == p:
                    continue
                assert vm.run('KR_T20WalkLeft', [p, q]) == r20_walk(X, regs, p, q), ('V27 던전 동행 남은 장면', tag, p, q)
                counts['V27_walk_pairs_checked'] += 1
            counts['V27_person_states'] += 1
        # the calendar's drawer rows (KR_T18ChipCount = what the lane page prints) give the same sums
        m = r20_month(today)
        cal_left = cal_walk = 0
        for i, ch in enumerate(X['chips']):
            if not (1 <= ch['lane'] <= 7):
                continue
            x = vm.run('KR_T18ChipCount', [i, ch['month']])
            k, n = x % 10000, x // 10000
            if ch['month'] == m and KINDS[ch['kind']] in R20_LEFT:
                cal_left += n - k
            if KINDS[ch['kind']] == 'walk':
                cal_walk += n - k
        assert sum(vm.run('KR_T20TrainLeft', [p]) for p in PARTY_Q) == cal_left, ('V27 Σ 이달 남은 != calendar drawer rows', tag)
        pair_sum = sum(vm.run('KR_T20WalkLeft', [p, q]) for p in PARTY_Q for q in PARTY_Q if q > p)
        solo_sum = sum(vm.run('KR_T20WalkLeft', [p, 0]) for p in PARTY_Q)
        assert pair_sum + solo_sum == cal_walk, ('V27 Σ 던전 동행 남은 != calendar walk drawer rows', tag, pair_sum, solo_sum, cal_walk)
        counts['V27_calendar_sums_equal'] += 1
    # V28: 「이달」 follows today's month
    tag, regs, _ = states[1]
    vm.registered = regs
    seen = collections.defaultdict(set)
    for mo in range(4, 12):
        vm.today = (mo, 15)
        for p in PARTY_Q:
            got = vm.run('KR_T20TrainLeft', [p])
            assert got == r20_left(X, regs, p, (mo, 15)), ('V28 month', mo, p)
            seen[p].add(got)
    assert any(len(v) > 1 for v in seen.values()), 'V28: the remaining count never changes with the month'
    counts['V28_months_checked'] = 8
    counts['V28_persons_whose_value_changes'] = sum(1 for v in seen.values() if len(v) > 1)


def r20_text_checks(vm, X, counts, states):
    """V29: the 「이벤트」 page text and the partner label of every person = the model; layout limits."""
    widest = ''
    for tag, regs, today in states:
        vm.registered = regs
        vm.today = today
        for c in range(1, 9):
            got = ko(vm.run('KR_T20StText', [c]))
            want = r20_status_text(X, regs, c, today)
            assert got == want, ('V29 이벤트 쪽', tag, c, [(a, b) for a, b in zip(got.split('\n'), want.split('\n')) if a != b][:2])
            lines = got.split('\n')
            assert len(lines) <= 13, ('V29 too many lines', tag, c, len(lines))
            assert not re.search(r'　\S+ \$\{font ' + re.escape(CYAN) + r'\}0\$\{/font\}', got), ('V29 a 0-row shown', tag, c)
            for line in lines:
                w = units_w(untag(line)) * ST_LINE_PX
                assert w <= ST_TEXT_MAX_PX, ('V29 line wider than the panel', tag, c, untag(line), w)
                if units_w(untag(line)) > units_w(widest):
                    widest = untag(line)
            rows = [l for l in lines if l.startswith('　')]
            nums = [int(re.search(r'\{font ' + re.escape(CYAN) + r'\}(\d+)', r).group(1)) for r in rows]
            if 2 <= c <= 8:
                total = int(re.search(r'던전 동행 남은 장면 \$\{font ' + re.escape(CYAN) + r'\}(\d+)', got).group(1))
                assert total == sum(nums) and len(rows) <= 7, ('V29 total / rows', tag, c)
                for q in PARTY_Q:
                    if q != c and not r20_joined(X, q, today):
                        assert PARTY_KR[q - 2] + '와 ' not in got, ('V29 a partner shown before joining', tag, c, q)
            counts['V29_texts'] += 1
        for p in PARTY_Q:
            assert ko(vm.run('KR_T20TrText', [p])) == r20_label_text(X, regs, p, today), ('V29 label', tag, p)
            counts['V29_labels'] += 1
    counts['V29_widest_line_px'] = units_w(widest) * ST_LINE_PX
    return widest


def r20_status_page_checks(vm, X, counts, regs, today=(10, 14)):
    """V30: the status window driven through the r20 shims (as C_Status::RunStatus / SetInfo call them)."""
    vm.registered = regs
    vm.today = today
    vm.parts = {}
    vm.calls = []
    fid = lambda n: vm.fs[n]['index']
    sv = vm.status_view(2, page=1)

    def step(shim):
        vm.method(fid(shim), sv, [])
        return sv[16]

    def ours():
        return [n for n in vm.ours() if n in (ST_PANEL, ST_TEXT)]

    def check_page4(chara):
        t, pnl = vm.parts[ST_TEXT], vm.parts[ST_PANEL]
        assert ko(t['text']) == r20_status_text(X, regs, chara, today), ('V30 page-4 text', chara)
        assert t['parent'] == pnl['parent'] == VM.ST_ROOT and t['show'] == pnl['show'] == 1, ('V30 parent/show', t, pnl)
        assert t['pos'] == (52.0, 80.0) and pnl['pos'] == (32.0, 64.0) and (pnl['z'], t['z']) == (40, 41), (t, pnl)
        assert t['font'] == ST_FONT and t['tag'] == 1 and t['linespace'] == 8, t
        assert pnl['construct'][0] == ('create', 338, 448) and pnl.get('built') == 1, pnl
        assert sv['shown'] == dict(basic=False, item=True, skill=False, weapon=False, switch=True, feeling=False), sv['shown']
    pages = [step('KR_T20StNext') for _ in range(4)]
    assert pages == [2, 3, 4, 1], ('V30 next', pages)
    pages = [step('KR_T20StPrev') for _ in range(4)]
    assert pages == [4, 3, 2, 1], ('V30 prev', pages)
    # page by page: our parts only on page 4
    for want_page, shim in [(2, 'KR_T20StNext'), (3, 'KR_T20StNext'), (4, 'KR_T20StNext')]:
        assert step(shim) == want_page
        assert (len(ours()) == 2) == (want_page == 4), ('V30 parts on page', want_page, ours())
    check_page4(2)
    first = len(ours())
    # another person on page 4 (Up/Down or the wheel -> SetInfo): redrawn
    vm.method(fid('C_HomeStatusView@SetInfo'), sv, [3])
    assert sv[16] == 4 and len(ours()) == 2
    check_page4(3)
    # another person on page 1: nothing of ours
    assert step('KR_T20StNext') == 1 and not ours()
    vm.method(fid('C_HomeStatusView@SetInfo'), sv, [5])
    assert not ours()
    # page 0 (the hover preview): next / prev do nothing
    sv0 = vm.status_view(2, page=0)
    vm.method(fid('KR_T20StNext'), sv0, [])
    vm.method(fid('KR_T20StPrev'), sv0, [])
    assert sv0[16] == 0 and not ours()
    # the window closes on page 4 (C_Status::RunStatus end -> KR_T20StEnd): gone; the next opening starts clean
    assert step('KR_T20StPrev') == 4 and len(ours()) == 2
    vm.run('KR_T20StEnd', [None])
    assert not ours() and ('AFL_Parts_EraseWholeMouseWheelEvent', [None]) in vm.calls, 'V30 parts left after the window closed'
    vm.method(fid('C_HomeStatusView@SetActivePage'), sv, [1])            # BeginStatus of the next opening
    for _ in range(3):
        step('KR_T20StNext')
    assert sv[16] == 4 and len(ours()) == first, ('V30 a second opening makes another number of parts', len(ours()), first)
    vm.run('KR_T20StEnd', [None])
    assert not vm.ours()
    counts['V30_status_page_steps'] = 1
    counts['V30_parts_on_page4'] = first


def r20_partner_checks(vm, X, counts, regs, today=(9, 22), shown=(2, 3, 4, 5, 6, 8)):
    """V31: the partner screen driven through the r20 hooks (SelectAlly::get in the key loop, AppearStandChara on hover,
    ■方向キー処理／削除 after the wait)."""
    vm.registered = regs
    vm.today = today
    vm.parts = {}
    vm.calls = []
    fid = lambda n: vm.fs[n]['index']
    v = vm.training_view(set(shown))

    def labels():
        return {n - TR_BASE: vm.parts[n] for n in vm.ours() if TR_BASE < n < TR_BASE + 10}

    def boxes():
        return {n - TR_BOX: vm.parts[n] for n in vm.ours() if TR_BOX < n < TR_BOX + 10}

    def bright():
        return {p: part['mul'][0] for p, part in labels().items()}
    vm.hover = 0
    got = vm.method(fid('KR_T20TrAlly'), v, [])
    assert got is v[10], 'V31 KR_T20TrAlly must return m_SelectAlly'
    lab, box = labels(), boxes()
    assert sorted(lab) == sorted(box) == sorted(shown), ('V31 labels for the shown portraits only', sorted(lab), sorted(box), shown)
    for p, part in lab.items():
        assert ko(part['text']) == r20_label_text(X, regs, p, today), ('V31 label text', p)
        assert part['parent'] == VM.PORTRAIT + p and box[p]['parent'] == VM.PORTRAIT + p, ('V31 parent', p)
        assert part['font'] == TR_FONT and part['tag'] == 1 and part['z'] == 21 and box[p]['z'] == 20, (p, part, box[p])
        assert part['pos'] == (10.0, -52.0) and box[p]['pos'] == (4.0, -56.0), (p, part['pos'], box[p]['pos'])
    assert set(bright().values()) == {255}, ('V31 no hover: every label bright', bright())
    n_first = len(vm.ours())
    for who in shown[:3] + (0,):
        vm.method(fid('KR_T20TrAppear'), v, [who, 350])
        want = {p: (255 if who <= 0 or p == who else 128) for p in shown}
        assert bright() == want, ('V31 hover', who, bright())
        counts['V31_hover_states'] += 1
    assert ('method', 'C_SceneTrainingView@AppearStandChara', [shown[0], 350]) in vm.calls, 'V31 the stand picture call is kept'
    # the loop asks again without a KeyDel (a system button returned): nothing made twice
    vm.method(fid('KR_T20TrAlly'), v, [])
    assert len(vm.ours()) == n_first
    vm.run('KR_T20TrKeyDel')
    assert not vm.ours() and ('■方向キー処理／削除', []) in vm.calls, ('V31 parts left after the wait', vm.ours())
    vm.hover = shown[-1]
    vm.method(fid('KR_T20TrAlly'), v, [])
    assert len(vm.ours()) == n_first, ('V31 entered again: another number of parts', len(vm.ours()), n_first)
    assert bright() == {p: (255 if p == shown[-1] else 128) for p in shown}, ('V31 the hovered person when the labels are made', bright())
    vm.run('KR_T20TrKeyDel')
    assert not vm.ours()
    counts['V31_parts_per_entry'] = n_first
    counts['V31_labels'] = len(shown)


def r20_training_source(counts):
    """V32: C_Ability.training is a point pool, read from the base code (not a count of trainings)."""
    d = L.WORK / 'vm' / 'base'
    d.mkdir(parents=True, exist_ok=True)
    bp = L.base_paths()
    body = {}
    for n in ('C_Ability@GetTraining', 'C_Ability@SetTraining', 'C_Ability@AddTrain', 'C_SceneTraining@ReflectStatus', 'L_BattleIncome::Settle',
              'LFixedIncome::Settle', 'LAbility::PrepareAbilities'):
        path = d / (n.replace(':', '_').replace('@', '_') + '.jam')
        if not path.exists():
            L.cmd('ain', 'dump', '--function', n, '-o', path, bp['ain'])
        body[n] = [l.strip() for l in path.read_text('utf8').splitlines() if l.strip() and not l.startswith(';') and not l.strip().endswith(':')
                   and not l.startswith(('FUNC', 'ENDFUNC'))]
    assert body['C_Ability@GetTraining'][:2] == ['.STRUCTREF C_Ability training', 'RETURN'], body['C_Ability@GetTraining']
    add = body['C_Ability@AddTrain']
    assert add[:6] == ['PUSHSTRUCTPAGE', 'PUSH 27305', '.STRUCTREF C_Ability training', '.LOCALREF nTrainAdd', 'ADD', 'CALLMETHOD 1'], add
    rs = body['C_SceneTraining@ReflectStatus']
    i = rs.index('PUSH 27339')                    # nTraining = pa.GetTraining()
    j = next(k for k in range(i, len(rs) - 2) if rs[k:k + 3] == ['PUSH 27305', 'PUSH 0', 'CALLMETHOD 1'])   # pa.SetTraining(0)
    spread = [k for k in range(i, j) if rs[k] == 'PUSH 27312']                                            # AddAbility per stat
    assert spread, 'ReflectStatus does not hand the points to the four stats'
    settle = sum(1 for l in body['L_BattleIncome::Settle'] if l == 'PUSH 27304')
    fixed = sum(1 for l in body['LFixedIncome::Settle'] if l == 'PUSH 27304')
    assert settle >= 1 and fixed >= 1, (settle, fixed)
    counts['V32_training_is_points'] = 1
    return dict(verdict='C_Ability.training is a point pool (「훈련치」): not a count of trainings',
                getter='C_Ability@GetTraining = .STRUCTREF C_Ability training',
                added_by=['L_BattleIncome::Settle (AddTrain x%d, per battle income)' % settle, 'LFixedIncome::Settle (AddTrain x%d)' % fixed,
                          'LAbility::PrepareAbilities (SetTraining 150 at the start)'],
                emptied_by='C_SceneTraining@ReflectStatus: nTraining = GetTraining(); spread over four stats (AddAbility x%d sites); SetTraining(0)' % len(spread),
                capped='C_Ability@SetTraining caps at 99999',
                used_instead='the person\'s after-training conversations seen in this save (특훈 뒤 · 반한 뒤 · 우선 대화 drawers, all months): 「특훈 뒤 대화 n번 봄」')


def r20_walk_counter_absence(m, counts):
    """V33: no per-person dungeon companion counter in the game's data (members and globals of the four places)."""
    st = {L.fix_name(x['name']): [L.fix_name(y['name']) for y in x['members']] for x in m['structures']}
    glob = [L.fix_name(g['name']) for g in m['globals']]
    places = dict(C_Ability=st['C_Ability'], income_t=st['income_t'], C_DungeonInfo=st['C_DungeonInfo'],
                  L_Party_globals=[g for g in glob if g.startswith('L_Party::')],
                  L_BattleIncome_globals=[g for g in glob if g.startswith('L_BattleIncome::')],
                  L_DungeonInfo_globals=[g for g in glob if g.startswith('L_DungeonInfo::')])
    words = re.compile(r'walk|companion|together|accompan|dungeon.?count|同行|回数|times', re.I)
    hits = {k: [x for x in v if words.search(x)] for k, v in places.items()}
    assert not any(hits.values()), ('V33 a companion counter candidate', hits)
    counts['V33_places_checked'] = len(places)
    return dict(verdict='no per-person dungeon companion counter: the companion count is left out (remaining scenes only)', places=places)


'''
rep(anchor, R20 + anchor)

# ------------------------------------------------------------------ defects: 4 more (35)
rep("""    return [('V21 one E-number left on a scene page (E%05d)' % no1, 'names_e', e_left),""",
    """    return [('V21 one E-number left on a scene page (E%05d)' % no1, 'names_e', e_left),""")
rep("""def r16_day_alias():""",
    """def r20_defects():
    \"\"\"r20: one remaining count wrong, a parts leak, the hovered person not brightened, a 0-row not left out.\"\"\"
    return [('V27 one remaining count wrong (이달 남은 특훈 뒤 대화 counts 반한 뒤 instead of 초대)', 'r20_counts',
             seq_replace('KR_T20TrainLeft', [('.LOCALREF', 'k'), ('PUSH', '3'), ('EQUALE',)], 1, ('PUSH', '2'))),
            ('V31 parts leak (the label boxes are not released after the wait)', 'r20_partner',
             op_replace('KR_T20TrClear', lambda o: o == ['CALLHLL', 'PartsEngine Release 0'], lambda o: ['POP'], nth=1)),
            ('V31 the hovered person not brightened (no KR_T20TrMark after AppearStandChara)', 'r20_partner',
             op_replace('KR_T20TrAppear', lambda o: o == ['CALLFUNC', 'KR_T20TrMark'], lambda o: ['POP'])),
            ('V29 a partner row with 0 left in (the 0 test removed)', 'r20_text',
             seq_replace('KR_T20StText', [('.LOCALREF', 'k'), ('PUSH', '0'), ('LTE',)], 1, ('PUSH', '-1')))]


def r16_day_alias():""")

# ------------------------------------------------------------------ main
rep("""        result = dict(schema='yoru-calendar-r19.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, counts=dict(counts))""",
    """        result = dict(schema='yoru-calendar-r20.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, counts=dict(counts))""")
rep("""    rules = name_rule_checks(vm, X, counts)
    result = dict(schema='yoru-calendar-r19.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,""",
    """    rules = name_rule_checks(vm, X, counts)
    # r20
    states = r20_states(X, regs, abo, mid_regs, mid_today)
    r20_count_checks(vm, X, counts, states)
    widest20 = r20_text_checks(vm, X, counts, states)
    r20_status_page_checks(vm, X, counts, regs)
    r20_partner_checks(vm, X, counts, regs)
    r20_real = r20_real_save_checks(vm, X, counts)
    source = r20_training_source(counts)
    walkc = r20_walk_counter_absence(m, counts)
    result = dict(schema='yoru-calendar-r20.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,""")
rep("""                  panel=panel, sandbox=sandbox, real_saves=real, name_rule_samples=rules)""",
    """                  panel=panel, sandbox=sandbox, real_saves=real, name_rule_samples=rules,
                  r20=dict(training_count_source=source, dungeon_companion_count=walkc, widest_event_line=widest20, real_saves=r20_real,
                           states=[t for t, _, _ in states]))""")
rep("""                      affinity=lambda v: affinity_checks(v, X, collections.Counter()))""",
    """                      affinity=lambda v: affinity_checks(v, X, collections.Counter()),
                      r20_counts=lambda v: r20_count_checks(v, X, collections.Counter(), states[:2]),
                      r20_text=lambda v: r20_text_checks(v, X, collections.Counter(), states[:3]),
                      r20_partner=lambda v: r20_partner_checks(v, X, collections.Counter(), regs))""")
rep("""        for label, group, mutation in DEFECTS + [table_defect(X)] + r19_defects(vm, X):""",
    """        for label, group, mutation in DEFECTS + [table_defect(X)] + r19_defects(vm, X) + r20_defects():""")
rep("""        assert len(planted) == 31, len(planted)""", """        assert len(planted) == 35, len(planted)""")
p.write_text(s, encoding='utf8')
print('patched', p)
