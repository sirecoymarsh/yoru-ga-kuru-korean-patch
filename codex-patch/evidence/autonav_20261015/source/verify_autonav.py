# -*- coding: utf-8 -*-
"""Auto-nav candidate verification without the game (Claude Opus 5.5, 2026-10-15).

  python verify_autonav.py             all checks (must pass)
  python verify_autonav.py --selftest  all checks, then each planted defect must make some check fail

Static: the manifest's same-length sites are the only old-code differences (the build asserts it; re-checked here from the bytes),
every site holds our replacement, the pinned functions are byte-identical.
VM (the r23 VM, work/vmcore.py, running the candidate's own compiled bodies; game calls modelled):
  A1 picks: 4 targets x 19 choice events: the answer the 20-second timer picks = an independent model from graph/schedule.json
     (the target's own row in the 4-way person choices; else the answer whose chain raises the target or leads on to the
     target's next choice; else the one raising nobody else; else 1); the star appears on that row only, left of the row
     (parent = the row frame), blinks (alpha 110-255) and cycles colour; it is released when the choice returns
  A2 timing: fires after 20 s of frames (16 ms) and not before; gaps over 250 ms are not counted (backlog, menus)
  A3 the player's own click before 20 s wins; no auto pick afterwards
  A4 off / replay: no target, a calendar replay (KR_T18RunSandboxed on the stack), a chart replay (KR_CReplayRun) or the
     memory mode -> the original choice window runs untouched (no star, no timer)
  A5 storage: KR_ANSetTarget keeps exactly one KR_AUTONAV_<t> name in the save's register; switching / off removes the old one
  A6 new game: the dialog's answer sets the target (or none); KR_ANOpeningQ returns IsPlayOpening's value unchanged
  A7 training: armed only on a story Saturday (CanSelect and GetAfterTrainingEvent(target) > 0, asked once a day): star on the
     target's r20 box, 20 s -> EndWaitForClick(target) and the confirm answers 「예」 without a dialog; manual picks keep the dialog
  A8 top-up: for every target and day (4/9 .. 11/17) and several starting values the target's GetFeeling after KR_ANDateGet =
     max(start, need) with need from an independent parse of the gates (+ 10/15 on: >= 60 and above the other three); the other
     persons are never touched; nothing happens without a target or in a replay
"""
import sys, json, re, copy, collections, datetime
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import anlib as L
import vmcore
from vmcore import VM, Stop

O = HERE / 'candidate'
W = L.WORK / 'build'
EVENTS = [58, 63, 69, 104, 258, 260, 322, 611, 10021, 20041, 20081, 20164, 30001, 30021, 30152, 40021, 40041, 40043, 40061]
RATES = {1: 420, 2: 420, 3: 420, 4: 370, 5: 290, 6: 540, 7: 500, 8: 420}
GLOW = 2026101503
GOLD = (255, 200, 60)
PARENT = 1000777001                              # the row frame part (矩形_項目位置) the model's CreateParts passes
FRAME_MS = 16
WAIT_MS = 20000


# ============================================================== independent expectations (graph/schedule.json only)
def schedule():
    return json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))


def expect_picks(sched):
    ev = {e['id']: e for e in sched['events']}

    def chain(eid):
        """Affection along the chain from eid until the next choice event (inclusive), and that next choice event if any."""
        aff = collections.Counter()
        seen = set()
        while eid in ev and eid not in seen:
            seen.add(eid)
            e = ev[eid]
            for a in e['effects']['affection']:
                aff[a['person']] += a['delta']
            if e['has_choice']:
                return aff, eid
            if len(e['chains_to']) != 1:
                return aff, None
            eid = e['chains_to'][0]
        return aff, None
    out = {}
    for e in EVENTS:
        x = ev[e]
        opts = x['choices']
        res = {}
        for t in (2, 3, 4, 5):
            persons = []
            for o in opts:
                aff, nxt = chain(o['next'])
                persons.append((o['no'], aff, nxt))
            four = len(opts) == 4 and all(len(a) <= 1 for _, a, _ in persons)
            if e in (322, 30152, 611):
                assert four
                res[t] = t - 1
                continue
            own = [no for no, aff, nxt in persons if aff.get(t, 0) > 0 or (nxt is not None and ev[nxt]['person'] == t)]
            if own:
                res[t] = own[0]
                continue
            clean = [no for no, aff, nxt in persons if not any(v > 0 for p, v in aff.items() if p != t)]
            res[t] = clean[0] if clean else 1
        out[e] = res
    return out


def expect_needs(sched):
    start, end = tuple(sched['calendar']['start']), tuple(sched['calendar']['end'])
    gates = []
    for e in sched['events']:
        for t in e.get('triggers') or []:
            for g in t.get('feeling_gate') or []:
                if g['op'] != '>=':
                    continue
                ce = t.get('condition_expr') or ''
                if t['kind'] == 'conditional':
                    a, b = t['date_from'], t['date_to']
                elif t['kind'] == 'scheduled_special':
                    a = b = t['date']
                else:
                    f = re.search(r'IsTodayOrAfter\((\d+), (\d+)\)', ce)
                    l = re.search(r'IsTodayOrBefore\((\d+), (\d+)\)', ce)
                    a = [int(f[1]), int(f[2])] if f else list(start)
                    b = [int(l[1]), int(l[2])] if l else list(end)
                gates.append((g['person'], tuple(a), tuple(b), g['value']))

    def need(t, m, d, others):
        n = max([v for p, a, b, v in gates if p == t and a <= (m, d) <= b] + [0])
        if (m, d) >= (10, 15):
            n = max(n, 60, max(others) + 1)
        return n
    return need, gates


def days(sched):
    m, d = sched['calendar']['start']
    out = []
    mx = {2: 28, 4: 30, 6: 30, 9: 30, 11: 30}
    while True:
        out.append((m, d))
        if [m, d] == sched['calendar']['end']:
            return out
        d += 1
        if d > mx.get(m, 31):
            m, d = m + 1, 1


# ============================================================== the VM with the auto-nav game calls modelled
class ANVM(VM):
    def __init__(self, ain, meta):
        super().__init__(ain, meta)
        VM.GAME = dict(rates=dict(RATES), rate_default=420)
        self.clock = 100000
        self.outer = []
        self.memory_mode = False
        self.after_training = {}
        self.can_select = set()
        self.after_asked = []
        self.sel = None
        self.sel_log = []
        self.alpha = {}
        self.colors = collections.defaultdict(set)
        self.play_opening = 1
        self.dates = 0
        self.today = (4, 9)
        self.cfg = {}
        self.boxes = {}
        self.kids = collections.defaultdict(list)
        self.next_part = 1000500000

    # -- calls the game makes
    def native(self, name, aa):
        if name == '■選択メッセージ／実行':
            return self.select_message(aa)
        if name == '■バックログ起動監視':
            return 0
        if name == 'C_UserInputManager::IsClickCancelOtherMouse':
            return 0
        if name == '_■関数実行中確認':
            return int(aa[0] in [f['name'] for f in self.frames] or aa[0] in self.outer)
        if name == 'Ａ＿回想モード実行中確認':
            return int(self.memory_mode)
        if name == 'N_ScenarioRegister::SetEventFlag':
            n, flag = aa
            had = n in self.registered
            if flag == 1:
                self.registered.add(n)
            elif flag == 0:
                self.registered.discard(n)
            return int(had)
        if name == 'L_RandomScenario::GetAfterTrainingEvent':
            self.after_asked.append(aa[0])
            return self.after_training.get(aa[0], 0)
        if name == 'LAbility::CanSelect':
            return int(aa[0] in self.can_select)
        if name == 'AFL_Activity_IsExistPartsByName':
            return int(aa[1] in self.cfg.get(aa[0], {}))
        if name == 'AFL_Activity_GetPartsNumber':
            return self.cfg.get(aa[0], {}).get(aa[1], 0)
        if name == 'Ｐ＿チェックボックス＿チェック状態取得':
            return int(self.boxes[aa[0]]['checked'])
        if name == 'Ｐ＿チェックボックス＿チェック状態設定':
            self.boxes[aa[0]]['checked'] = int(bool(aa[1]))
            self.boxes[aa[0]]['writes'] += 1
            return None
        if name == 'Ｐ＿チェックボックス＿有効状態取得':
            return int(self.boxes[aa[0]]['enabled'])
        if name == 'Ｐ＿チェックボックス＿有効状態設定':
            self.boxes[aa[0]]['enabled'] = int(bool(aa[1]))
            return None
        return super().native(name, aa)

    def hll(self, lib, method, st):
        if lib == 'system' and method == 'GetTime':
            st.append(self.clock)
            return
        if lib == 'PartsEngine' and method == 'SetComponentAlpha':
            a = st.pop()
            n = st.pop()
            self.alpha.setdefault(n, []).append(a)
            return
        if lib == 'PartsEngine' and method == 'SetComponentMulColor':
            b, g, r, n = st.pop(), st.pop(), st.pop(), st.pop()
            self.colors[n].add((r, g, b))
            self.part(n)['mul'] = (r, g, b)
            return
        if lib == 'PartsEngine' and method == 'SetComponentAddColor':
            b, g, r, n = st.pop(), st.pop(), st.pop(), st.pop()
            self.part(n)['add'] = (r, g, b)
            self.colors[('add', n)].add((r, g, b))
            return
        if lib == 'PartsEngine' and method == 'NumofChild':
            st.append(len(self.kids[st.pop()]))
            return
        if lib == 'PartsEngine' and method == 'GetChild':
            i = st.pop()
            n = st.pop()
            st.append(self.kids[n][i])
            return
        if lib == 'PartsEngine' and method == 'GetComponentPosZ':
            st.append(self.parts.get(st.pop(), {}).get('z', 0))
            return
        if lib == 'PartsEngine' and method == 'Parts_GetPartsWidth':
            st.pop()
            n = st.pop()
            st.append(self.parts.get(n, {}).get('w', 0))
            return
        if lib == 'PartsEngine' and method == 'Parts_GetParentPartsNumber':
            st.append(self.parts.get(st.pop(), {}).get('parent', 0))
            return
        return super().hll(lib, method, st)

    def method(self, fid, obj, aa):
        name = L.raw_symbol(self.meta, fid)
        if name == 'C_Ability@GetFeelingRate':
            return RATES[obj[0]]
        if name == 'C_Ability@AddFeeling':
            self.feel[obj[0]] = self.feel.get(obj[0], 0) + aa[0]
            obj[24] += aa[0]
            return None
        if name == 'C_SelectMessInfo@CreateParts':
            obj['made'] = aa[0]
            box, txt = self.next_part, self.next_part + 1
            self.next_part += 2
            self.parts[box] = dict(kind='row box', show=1, z=20, parent=aa[0], mul=(255, 255, 255), row=obj['id'])
            self.parts[txt] = dict(kind='row text', show=1, z=21, parent=box, mul=(255, 255, 255), row=obj['id'])
            self.kids[aa[0]].append(box)
            self.kids[box].append(txt)
            obj['parts'] = (box, txt)
            return 1
        if name == 'C_SelectMessInfo@Id::get':
            return obj['id']
        if name == 'C_GameFlags@Date::get':
            self.dates += 1
            return dict(kind='C_GameDate', m=self.today[0], d=self.today[1])
        if name == 'C_GameFlags@IsPlayOpening::get':
            return self.play_opening
        if name.startswith('KR_AN'):
            return self.run(name, aa, this=obj)
        return super().method(fid, obj, aa)

    # -- the choice window (C_SelectMessage@Run): rows are made through the CreateParts site, then frames run the Update site
    def select_message(self, aa):
        sim = self.sel
        assert sim is not None, 'a choice window without a scenario'
        rec = dict(n=sim['n'], args=list(aa), stars=[], ended=None, frame=None, result=None)
        self.sel_log.append(rec)
        info_create = self.fs['KR_ANInfoCreate']['index']
        self.parts[PARENT] = dict(kind='frame', show=1, z=5, w=600)
        self.kids[PARENT] = []
        rows = []
        for i in range(sim['n']):
            info = {'kind': 'C_SelectMessInfo', 'id': i + 1}
            r = self.method(info_create, info, [PARENT])
            assert r == 1 and info['made'] == PARENT, ('row creation lost', info)
            rows.append(info['parts'])
        rec['rows'] = rows
        rec['glow'] = dict(self.parts[GLOW]) if GLOW in self.parts else None
        rec['tints'] = collections.defaultdict(set)
        self.ended = None
        for f in range(sim['frames']):
            gap = sim.get('gaps', {}).get(f, 0)
            self.clock += FRAME_MS + gap
            if sim.get('click') and sim['click'][0] == f:
                rec.update(result=sim['click'][1], frame=f, ended='player')
                return sim['click'][1]
            self.run('KR_ANSelFrame')
            for i, (bx, tx) in enumerate(rows):
                rec['tints'][i + 1].add(self.parts[bx]['mul'])
                rec['tints'][i + 1].add(self.parts[tx]['mul'])
            if self.ended is not None:
                rec.update(result=self.ended, frame=f, ended='auto')
                return self.ended
        rec.update(result=sim['default'], frame=sim['frames'], ended='player')
        return sim['default']


def new_vm():
    man = L.readj(O / 'manifest.json')
    assert L.sha(O / 'NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    vm = ANVM(O / 'NightRemaster.ain', L.read_meta(W / 'candidate_meta.json'))
    vm.man = man
    return vm, man


def set_target(vm, t):
    vm.registered = {n for n in vm.registered if not n.startswith('KR_AUTONAV_')}
    if t:
        vm.registered.add('KR_AUTONAV_%d' % t)


def frames_for(ms):
    return ms // FRAME_MS + 2


# ============================================================== checks
def a1_a2(vm, picks, counts):
    for t in (2, 3, 4, 5):
        for e in EVENTS:
            vm.reset()
            set_target(vm, t)
            vm.parts.pop(GLOW, None)
            vm.alpha.clear()
            vm.colors.clear()
            n = 4 if e in (322, 611, 30152) else 2
            vm.sel = dict(n=n, frames=frames_for(WAIT_MS) + 50, default=-99)
            r = vm.run('KR_AN_E%05d' % e, [0, 200])
            rec = vm.sel_log[-1]
            want = picks[e][t]
            assert r == want and rec['ended'] == 'auto', ('A1 pick', e, t, r, want, rec)
            assert rec['args'] == [0, 200], ('A1 the original window gets the event\'s own arguments', rec['args'])
            # A2: not before 20 s, at the first frame on or after 20 s
            elapsed = (rec['frame']) * FRAME_MS
            assert WAIT_MS - FRAME_MS <= elapsed <= WAIT_MS + 2 * FRAME_MS, ('A2 timing', e, t, elapsed)
            g = rec['glow']
            row_h, dy = vm.man['data']['row_h'], vm.man['data']['star_dy']
            assert g and g['parent'] == PARENT and abs(g['pos'][1] - ((want - 1) * row_h + dy)) < 0.01 and g['z'] == 19, ('A1 glow band', e, t, g)
            al = vm.alpha.get(GLOW, [])
            assert al and min(al) <= 5 and max(al) >= 100 and max(al) <= 110, ('A1 glow blink', min(al or [0]), max(al or [0]))
            for row in range(1, n + 1):
                ts = rec['tints'][row]
                if row == want:
                    assert (255, 255, 255) in ts or any(c[1] > 250 for c in ts), ('A1 white phase', e, t, ts)
                    assert any(c[1] <= 205 and c[2] <= 65 for c in ts), ('A1 gold phase', e, t, sorted(ts)[:3])
                else:
                    assert ts == {(255, 255, 255)}, ('A1 another row tinted', e, t, row, ts)
            assert GLOW not in vm.parts, 'A1 glow band left after the choice'
            assert all(vm.parts[p]['mul'] == (255, 255, 255) for bt in rec['rows'] for p in bt), 'A1 row left tinted'
            assert vm.vars.get('YoruKR.AN.Mode', '') == '', 'A1 mode left set'
            counts['A1'] += 1
    # A2 gaps: a 5 s gap (backlog) is not counted -> fires 20 s of frames later, not 15 s
    vm.reset()
    set_target(vm, 2)
    vm.sel = dict(n=2, frames=frames_for(WAIT_MS) + 400, default=-99, gaps={100: 5000})
    r = vm.run('KR_AN_E00069', [0, 200])
    rec = vm.sel_log[-1]
    assert rec['ended'] == 'auto' and rec['frame'] * FRAME_MS >= WAIT_MS - FRAME_MS, ('A2 gap counted', rec)
    counts['A2'] += 1


def a3(vm, counts):
    for clickf, choice in ((10, 2), (600, 1), (1200, 2)):
        vm.reset()
        set_target(vm, 2)
        vm.sel = dict(n=2, frames=3000, default=-99, click=(clickf, choice))
        r = vm.run('KR_AN_E00069', [0, 200])
        assert r == choice and vm.sel_log[-1]['ended'] == 'player', ('A3 player click', clickf, r)
        assert GLOW not in vm.parts
        counts['A3'] += 1


def a4(vm, counts):
    cases = [('no target', dict()), ('calendar replay', dict(outer=['KR_T18RunSandboxed'])),
             ('chart replay', dict(outer=['KR_CReplayRun'])), ('memory mode', dict(memory=True))]
    for label, c in cases:
        for e in EVENTS:
            vm.reset()
            set_target(vm, None if label == 'no target' else 3)
            vm.outer = c.get('outer', [])
            vm.memory_mode = c.get('memory', False)
            vm.parts.pop(GLOW, None)
            vm.sel = dict(n=4 if e in (322, 611, 30152) else 2, frames=frames_for(WAIT_MS) + 200, default=-77)
            r = vm.run('KR_AN_E%05d' % e, [0, 200])
            rec = vm.sel_log[-1]
            assert r == -77 and rec['ended'] == 'player' and rec['glow'] is None and all(ts == {(255, 255, 255)} for ts in rec['tints'].values()), ('A4 untouched', label, e)
            counts['A4'] += 1
        vm.outer = []
        vm.memory_mode = False


def a5(vm, counts):
    vm.reset()
    vm.registered = {'ＥＶ／元／E00001', 'something'}
    for seq in ([2], [3, 5], [4, 0], [5, 5, 2], [0, 0]):
        for t in seq:
            vm.run('KR_ANSetTarget', [t])
        last = seq[-1]
        mine = sorted(n for n in vm.registered if n.startswith('KR_AUTONAV_'))
        assert mine == ([] if last == 0 else ['KR_AUTONAV_%d' % last]), ('A5', seq, mine)
        assert {'ＥＶ／元／E00001', 'something'} <= vm.registered, 'A5 other registrations touched'
        assert vm.run('KR_ANTarget') == last, ('A5 read back', seq)
        counts['A5'] += 1


def a6(vm, counts):
    for ans, want in ((2, 2), (3, 3), (4, 4), (5, 5), (1, 0)):
        for opening in (0, 1):
            vm.reset()
            set_target(vm, None)
            vm.play_opening = opening
            vm.script = [ans]
            r = vm.method(vm.fs['KR_ANOpeningQ']['index'], vm.game_flags, [])
            assert r == opening, ('A6 IsPlayOpening value', r, opening)
            d = vm.dialogs[-1]
            items = sorted(i[0] for i in d['items'])
            assert items == [1, 2, 3, 4, 5], ('A6 items', d['items'])
            title = vmcore.ko(d['title']) if d['title'] else ''
            assert all(len(line) <= 38 for line in title.split('\n')), ('A6 title line width', title)
            assert vm.run('KR_ANTarget') == want, ('A6 target', ans, want)
            counts['A6'] += 1


def a7(vm, counts):
    box = lambda p: 2026092020 + p                   # r20 KR_T20TrBox
    for t in (2, 3, 4, 5):
        for story in (True, False):
            vm.reset()
            set_target(vm, t)
            vm.today = (6, 2)
            vm.vars.pop('YoruKR.AN.TrDay', None)
            vm.outer = ['C_SceneTraining@RunSelectPartner']
            vm.can_select = {2, 3, 4, 5, 6, 7, 8}
            vm.after_training = {t: 10001} if story else {}
            vm.after_asked = []
            cg = 1000600000 + t
            vm.parts[cg] = dict(kind='portrait', show=1, mul=(255, 255, 255))
            vm.parts[box(t)] = dict(kind='box', show=1, parent=cg, add=(0, 0, 0))
            vm.colors.clear()
            vm.ended = None
            fired = None
            for f in range(frames_for(WAIT_MS) + 100):
                vm.clock += FRAME_MS
                assert vm.run('KR_ANTrainFrame') == 0
                if vm.ended is not None:
                    fired = f
                    break
            assert len(vm.after_asked) == 1, ('A7 GetAfterTrainingEvent asked once a day', vm.after_asked)
            if story:
                assert fired is not None and vm.ended == t and WAIT_MS - FRAME_MS <= fired * FRAME_MS <= WAIT_MS + 2 * FRAME_MS, ('A7 fire', t, fired)
                cs = vm.colors[cg]
                assert any(c[1] <= 205 and c[2] <= 65 for c in cs) and len(cs) >= 10, ('A7 portrait shimmer', t, sorted(cs)[:3])
                assert any(c[0] >= 140 for c in vm.colors[('add', box(t))]), ('A7 box glow', t)
                vm.script = []                       # no dialog may run
                r = vm.run('KR_ANTrainConfirm', [1, 200])
                assert r == 1 and vm.parts[cg]['mul'] == (255, 255, 255) and vm.parts[box(t)]['add'] == (0, 0, 0), ('A7 auto confirm restores', r, vm.parts[cg], vm.parts[box(t)])
            else:
                assert fired is None and not vm.colors[cg], ('A7 not a story Saturday', t)
                vm.script = [2]
                vm.cur = dict(title='x', cols=1, items=[], type=None, limit=None, top=None)
                r = vm.run('KR_ANTrainConfirm', [1, 200])
                assert r == 2, ('A7 manual confirm keeps the dialog', r)
            counts['A7'] += 1
    vm.outer = []


def a8(vm, need, sched, counts):
    ds = days(sched)
    for t in (2, 3, 4, 5):
        for (m, d) in ds:
            for start, low in ((0, False), (10, False), (25, False), (58, False), (70, False), (0, True), (40, True), (61, True)):
                vm.reset()
                set_target(vm, t)
                vm.today = (m, d)
                base = {p: (start if p == t else (8 + p if low else 30 + 7 * p)) * RATES[p] + 5 for p in range(1, 9)}
                vm.feel = dict(base)
                vm.method(vm.fs['KR_ANDateGet']['index'], vm.game_flags, [])
                others = [base[p] // RATES[p] for p in (2, 3, 4, 5) if p != t]
                want = max(start, need(t, m, d, others))
                got = vm.feel[t] // RATES[t]
                assert got == want, ('A8 top-up', t, (m, d), start, got, want)
                assert all(vm.feel[p] == base[p] for p in base if p != t), ('A8 another person touched', t, (m, d))
                counts['A8'] += 1
    for label in ('none', 'replay', 'memory'):
        vm.reset()
        set_target(vm, None if label == 'none' else 2)
        vm.outer = ['KR_T18RunSandboxed'] if label == 'replay' else []
        vm.memory_mode = label == 'memory'
        vm.today = (10, 15)
        vm.feel = {p: 5 * RATES[p] for p in range(1, 9)}
        before = dict(vm.feel)
        vm.method(vm.fs['KR_ANDateGet']['index'], vm.game_flags, [])
        assert vm.feel == before, ('A8 no top-up', label)
        counts['A8'] += 1
    vm.outer = []
    vm.memory_mode = False


CFG_ACT = 'Game\Asra\Mods'
CFG_NAMES = ['KR_NavOff', 'KR_NavIzumi', 'KR_NavKyouka', 'KR_NavManami', 'KR_NavMakoto']
CFG_T = [0, 2, 3, 4, 5]


def a9(vm, counts):
    def page(on_mods=True):
        vm.cfg = {CFG_ACT: ({n: 1000900000 + i for i, n in enumerate(CFG_NAMES)} if on_mods else {}) | {'KR_CheatSpeedValue': 1000900099}}
        vm.boxes = {1000900000 + i: dict(checked=0, enabled=1, writes=0) for i in range(5)}

    def frame(click=None):
        r1 = vm.run('KR_ANCfgSeenToParts', [CFG_ACT, 'KR_CheatSpeedValue'])
        if click is not None:                          # the engine toggles the clicked box between the two events
            b = vm.boxes[1000900000 + click]
            if b['enabled']:
                b['checked'] = 1 - b['checked']
        r2 = vm.run('KR_ANCfgSeenToAsra', [CFG_ACT, 'KR_CheatSpeedValue'])
        assert r1 == 1 and r2 == 1, ('A9 the original existence answer', r1, r2)

    def state():
        return [vm.boxes[1000900000 + i]['checked'] for i in range(5)], [vm.boxes[1000900000 + i]['enabled'] for i in range(5)]
    # in game: the boxes follow the save's target; a click on another box switches; a click on the lit box keeps it
    vm.reset()
    vm.outer = ['C_SceneGame@Run']
    for start in (0, 2, 3, 4, 5):
        set_target(vm, start or None)
        page()
        frame()
        chk, en = state()
        assert chk == [int(t == start) for t in CFG_T] and en == [1] * 5, ('A9 show', start, chk, en)
        for i, t in enumerate(CFG_T):
            frame(click=i)
            want = t
            chk, en = state()
            assert vm.run('KR_ANTarget') == want and chk == [int(x == want) for x in CFG_T], ('A9 click', start, i, chk)
            frame(click=i)                             # clicking the lit box again: still that target
            chk, en = state()
            assert vm.run('KR_ANTarget') == want and chk == [int(x == want) for x in CFG_T], ('A9 re-click keeps', start, i, chk)
            w0 = [vm.boxes[1000900000 + k]['writes'] for k in range(5)]
            frame()
            frame()
            assert [vm.boxes[1000900000 + k]['writes'] for k in range(5)] == w0, 'A9 idle frames must not rewrite the boxes'
            counts['A9'] += 1
    # the title's options: no game -> boxes off and locked, clicks change nothing
    vm.outer = []
    set_target(vm, 3)
    page()
    frame(click=1)
    chk, en = state()
    assert chk == [0] * 5 and en == [0] * 5 and vm.run('KR_ANTarget') == 3, ('A9 title', chk, en)
    counts['A9'] += 1
    # another options page (no KR_Nav parts): nothing touched, the original answer stays
    vm.outer = ['C_SceneGame@Run']
    page(on_mods=False)
    vm.boxes = {}
    frame()
    assert vm.run('KR_ANTarget') == 3
    counts['A9'] += 1
    vm.outer = []


def static(man, counts):
    base = L.base_paths()['ain']
    old = L.unpack(base.read_bytes())
    new = L.unpack((O / 'NightRemaster.ain').read_bytes())
    import struct
    n = struct.unpack_from('<I', old, 12)[0]
    allowed = set()
    for s in man['same_length_sites']:
        ad = s['site']
        assert new[16 + ad:16 + ad + 6].hex() == s['after'] and old[16 + ad:16 + ad + 6].hex() == s['before'], ('S site', s['function'])
        allowed |= set(range(ad + 2, ad + 6))
        counts['S1'] += 1
    diff = [i for i in range(n) if old[16 + i] != new[16 + i]]
    assert set(diff) <= allowed, ('S old code changed outside the sites', [hex(x) for x in diff if x not in allowed][:5])
    owners = collections.Counter(s['function'] for s in man['same_length_sites'])
    assert len(man['same_length_sites']) == 27 and sum(1 for o in owners if o.startswith('ＥＶ／元／E')) == 19, owners
    assert owners['C_ConfigView@EventConfAsraDataForParts'] == 1 and owners['C_ConfigView@EventConfPartsDataForAsra'] == 1, owners
    counts['S2'] += 1


def run_all(counts, mutate=None):
    sched = schedule()
    picks = expect_picks(sched)
    need, gates = expect_needs(sched)
    vm, man = new_vm()
    if mutate:
        mutate(vm)
    static(man, counts)
    a1_a2(vm, picks, counts)
    a3(vm, counts)
    a4(vm, counts)
    a5(vm, counts)
    a6(vm, counts)
    a7(vm, counts)
    a8(vm, need, sched, counts)
    a9(vm, counts)
    return picks


def selftest():
    """Each planted defect must make some check fail."""
    def body_patch(fn, old, new, every=False):
        def m(vm):
            ops, labels = vm.load(fn)
            hits = [i for i, o in enumerate(ops) if o == old]
            assert hits, (fn, old)
            for i in (hits if every else hits[:1]):
                ops[i] = new
        return m
    defects = [
        ('pick table off by one', body_patch('KR_ANPick', ['PUSH', '2'], ['PUSH', '3'])),
        ('20 s became 2 s', body_patch('KR_ANWaitMs', ['PUSH', '20000'], ['PUSH', '2000'])),
        ('gaps counted', body_patch('KR_ANAccum', ['PUSH', '250'], ['PUSH', '99999'])),
        ('replay not checked', body_patch('KR_ANActiveTarget', ['CALLFUNC', 'KR_ANReplay'], ['CALLFUNC', 'KR_ANInGame'])),
        ('route floor 60 became 6', body_patch('KR_ANTopUp', ['PUSH', '60'], ['PUSH', '6'], every=True)),
        ('top-up not above the others', body_patch('KR_ANTopUp', ['PUSH', '1'], ['PUSH', '0'], every=True)),
        ('glow band never released', body_patch('KR_ANDrop', ['CALLHLL', 'PartsEngine Release 0'], ['VM_POP_PUSH1'])),
        ('row left gold', body_patch('KR_ANUntint', ['PUSH', '255'], ['PUSH', '254'])),
        ('training shimmer on the text part', body_patch('KR_ANTrainAnim', ['CALLFUNC', 'KR_T20TrBox'], ['CALLFUNC', 'KR_T20TrPart'])),
        ('training armed on any Saturday', body_patch('KR_ANTrainTick', ['CALLFUNC', 'L_RandomScenario::GetAfterTrainingEvent'], ['CALLFUNC', 'LAbility::CanSelect'])),
        ('options change the target at the title', body_patch('KR_ANCfgToAsra', ['CALLFUNC', 'KR_ANInGame'], ['PUSH', '1'])),
        ('radio does not re-light the lit box', body_patch('KR_ANCfgToAsra', ['CALLFUNC', 'KR_ANCfgWrite'], ['CALLFUNC', 'KR_ANCfgToParts'])),
    ]
    failed = []
    for label, m in defects:
        counts = collections.Counter()
        try:
            run_all(counts, mutate=m)
        except (AssertionError, Stop, KeyError, TypeError, IndexError) as ex:
            failed.append(label)
            print('  caught:', label, '->', str(ex)[:120])
            continue
        print('  NOT CAUGHT:', label)
    return failed, len(defects)


def main():
    counts = collections.Counter()
    picks = run_all(counts)
    print('PASS', dict(counts))
    out = dict(time=datetime.datetime.now().astimezone().isoformat(), counts=dict(counts), candidate=L.sha(O / 'NightRemaster.ain'),
               picks={str(e): v for e, v in picks.items()})
    if '--selftest' in sys.argv:
        failed, n = selftest()
        out['selftest'] = dict(planted=n, caught=len(failed))
        assert len(failed) == n, ('a planted defect was not caught', n - len(failed))
        print('SELFTEST', len(failed), '/', n)
    L.writej(L.EVID / 'verify.json', out)


if __name__ == '__main__':
    main()
