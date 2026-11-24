# -*- coding: utf-8 -*-
"""The VM of ingame/r23_feeling/verify_feeling_r23.py (Claude Opus 5.5, 2026-09-28), copied unchanged by work/make_vmcore.py
(10-15) so the auto-nav verifier can subclass it. The r15-r23 folders stay read only."""
import sys, json, re, struct, collections, math, copy, time, random, datetime, io, contextlib, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import anlib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
PREFIX = 'NightR'
R23_MOON = 2026092330


def proxy(s):
    return L.encode(s).decode('cp932')


def ko(s):
    return L.decode(s.encode('cp932'))


class Stop(Exception):
    pass


class Resume(Exception):
    """system.ResumeLoad: the VM state is replaced by a snapshot and execution continues in the saved frames."""
    def __init__(self, snap):
        super().__init__('resume')
        self.snap = snap


class VMExit(Exception):
    """r21: system.Exit(code) - the game ends here (nothing after it runs)."""
    def __init__(self, code):
        super().__init__('exit %s' % code)
        self.code = code


class Wait:
    """r21: a select dialog that waits `frames` frames. Each frame the outside world may act first (each(vm, frame): the hook
    writes a file), then the dialog's frame handler runs its r21 site (C_SelectDialog@_Update calls KR_MTick where it called
    C_UserInputManager::IsClickEnterOtherMouse; S8 pins that site). The wait ends with the code a handler passed to
    AFL_Parts_EndWaitForClick, else after the last frame with `then` (the player's click)."""
    def __init__(self, frames, then, each=None, tick='KR_MTick'):
        self.frames, self.then, self.each, self.tick = frames, then, each, tick

    def run(self, vm, d):
        vm.ended = None
        d['polls'] = 0
        d['frames'] = 0
        for f in range(self.frames):
            if self.each:
                self.each(vm, f)
            n0 = len(vm.file_calls)
            d['frames'] += 1
            vm.run(d.get('tick') or self.tick)
            d['polls'] += len(vm.file_calls) - n0
            if vm.ended is not None:
                d['ended_by'] = vm.ended
                return vm.ended
        return self.then


def vsf(file):
    """gamesave::detail::TransAddSaveFileName: the part before 「.asd」 + 「.vsf」 (checked against the real body in V17)."""
    i = file.find('.asd')
    return file[:i] + '.vsf'


# ============================================================== VM (r17's, plus globals, the save folder and resume)
class VM:
    G_FN, G_SYS, G_EVRESULT, G_BEGIN_SELECT, G_CAN_RETURN = 214, 215, 190, 70, 72
    GAME_DIR = 'G:\\YoruGame\\'                       # r21: SystemService.GetGameFolderPath (with the trailing 「\\」)
    SAVE_DIR = 'S:\\Saves\\SaveData_KR'               # r21: system.GetSaveFolderName (absolute, no trailing 「\\」; probe log)

    def __init__(self, ain, meta, mutate=None, alias=None):
        """alias: {name: (meta entry, jam path)} - run another body under `name` (planted defects). mutate: {name: f(ops)}."""
        self.ain = ain
        self.meta = meta
        self.fs = {}
        for f in meta['functions']:
            self.fs.setdefault(L.raw_symbol(meta, f['index']), f)
        self.gname = {i: L.fix_name(g['name']) for i, g in enumerate(meta['globals'])}
        self.gid = {n: i for i, n in self.gname.items()}
        assert self.gname[self.G_FN] == 'LSys3xScript::m_FuncName' and self.gname[self.G_SYS] == 'LSys3xScript::m_IsSysScenario'
        assert self.gname[self.G_EVRESULT] == 'g_EvResult' and self.gname[self.G_CAN_RETURN] == 'menu::detail::g_bCanReturnBackSelect'
        assert self.gname[self.G_BEGIN_SELECT] == 'menu::detail::g_bBeginSelect'
        self.alias = alias or {}
        for name, (entry, _) in self.alias.items():
            self.fs[name] = entry
        self.code = {}
        self.mutate = mutate or {}
        self.dir = L.WORK / 'vm' / L.sha(ain)[:12]
        self.dir.mkdir(parents=True, exist_ok=True)
        self.vars = {}
        self.registered = set()
        self.flags = set()
        self.today = (6, 13)
        self.cur = None
        self.dialogs = []
        self.script = []
        self.calls = []
        self.steps = 0
        self.getflag_neg = 0
        self.config_inner = None
        # r18 game model: the saved globals the calendar code and a replay touch, affinity per person, the save folder
        self.glob = {self.G_FN: '', self.G_SYS: 0, self.G_EVRESULT: 0, self.G_BEGIN_SELECT: 0, self.G_CAN_RETURN: 0}
        self.feel = {}
        self.files = {}
        self.frames = []
        self.run_event = None           # callable(vm) for LSys3xScript::RunEvent (the replayed event), None = no effect
        self.save_fail = False          # セーブ実行: ResumeSave reports nSucceeded 0 (nothing written)
        self.vars_in_save = True        # does the resume image carry the SystemService session variables?
        # r20 model: PartsEngine parts by number, activity part names, the hovered portrait of the partner screen
        self.parts = {}
        self.act = {}
        self.hover = 0
        # r21 model: the disk (absolute path -> the text as TextFile.ReadAll returns it), folders, the two folders the game
        # names (GetGameFolderPath ends with 「\\」 like the engine's; GetSaveFolderName does not), injected failures, every file
        # API call in order, the code a frame handler ended a wait with, system.Exit
        self.disk = {}
        self.game_dir = VM.GAME_DIR
        self.save_dir = VM.SAVE_DIR
        self.dirs = {VM.GAME_DIR.rstrip('\\'), VM.SAVE_DIR}
        self.fail_write = set()
        self.fail_delete = set()
        self.file_calls = []
        self.ended = None
        self.exited = None
        self.hll_ref = None
        self.enter = 0
        self.guard_saves = False        # r21 checks: any save / load / config / title call is an error
        # r22 model: the recollection cells the game's recollection mode opens ((page, renban) 0-based), every chart wait and
        # every memory-mode replay in order, the title's input queries, IsRegisteredEvent calls (never while the chart is open),
        # the first message of every event (a replay marks it read: the global read mark is an HLL record the memory mode keeps)
        self.mem_enabled = set()
        self.charts = []
        self.replays = []
        self.inputs = {}
        self.reg_asked = []
        self.msg_of = {}
        self.shows = []
        # r23 model: the game mode (Flags.GameMode: 0 Modern, 1 Classic - the moons are off in Classic), the rates / rank bounds the
        # model reads from the base code (VM.GAME, set once by game_rules()), the r23 sites' targets read from this candidate's code
        self.game_mode = 0
        self.game_flags = dict(kind='C_GameFlags')
        self.site_cache = {}
        self.destroyed = []

    def reset(self):
        self.vars = {}
        self.cur = None
        self.dialogs = []
        self.script = []
        self.calls = []
        self.config_inner = None
        self.frames = []

    def load(self, name):
        if name in self.code:
            return self.code[name]
        if name in self.alias:
            path = self.alias[name][1]
        else:
            fid = self.fs[name]['index']
            path = self.dir / f'{fid}.jam'
            if not path.exists():
                L.cmd('ain', 'dump', '--function', L.symbol(self.meta, fid), '-o', path, self.ain)
        ops = []
        labels = {}
        for line in Path(path).read_text('utf8').splitlines():
            s = line.strip()
            if not s or s.startswith((';', 'FUNC ', 'ENDFUNC ', 'EOF ')):
                continue
            if s.endswith(':'):
                labels[s[:-1]] = len(ops)
            else:
                ops.append(s.split(maxsplit=1))
        if name in self.mutate:
            ops = self.mutate[name]([list(o) for o in ops])
        self.code[name] = (ops, labels)
        return self.code[name]

    def run(self, name, args=(), resume=None, this=None):
        f = self.fs[name]
        vs = f['arguments'] + f['variables']
        li = {}
        seen = collections.Counter()
        for i, x in enumerate(vs):
            n = x['name'] + (f'#{seen[x["name"]]}' if seen[x['name']] else '')
            seen[x['name']] += 1
            li[n] = i
        ops, labels = self.load(name)
        if resume is None:
            loc = {i: ('' if v['type'][0] == 12 else 0) for i, v in enumerate(vs)}
            loc.update(enumerate(args))
            st = []
            pc = 0
        else:
            loc, st = copy.deepcopy((resume['loc'], resume['st']))
            st = [self.glob if (isinstance(x, str) and x == '@GLOBALPAGE') else x for x in st]
            if resume['has_push']:
                st.append(resume['push'])
            pc = resume['pc']
        rec = dict(name=name, loc=loc, st=None, pc=None, ret=False)
        self.frames.append(rec)
        steps = 0
        prev = ('', '')
        try:
            while pc < len(ops):
                if steps:
                    prev = (op, arg)
                op, *rest = ops[pc]
                arg = rest[0] if rest else ''
                pc += 1
                steps += 1
                self.steps += 1
                assert steps < 5000000, (name, pc)
                if op == 'PUSH':
                    st.append(int(arg, 0))
                elif op == 'S_PUSH':
                    st.append(json.loads(arg))
                elif op == '.S_LOCALASSIGN':
                    v, x = arg.split(' ', 1)
                    loc[li[v]] = json.loads(x)
                elif op == '.LOCALASSIGN':
                    v, x = arg.rsplit(' ', 1)
                    loc[li[v]] = int(x, 0)
                elif op == '.LOCALPLUSA':
                    v, x = arg.rsplit(' ', 1)
                    loc[li[v]] += int(x, 0)
                elif op == '.LOCALREF':
                    st.append(loc[li[arg]])
                elif op == '.GLOBALREF':
                    if arg == 'LAbility::m_pAbilities':            # r23: array<ref C_Ability>, person p at p - 1 (LAbility::At)
                        st.append(self.abilities())
                    elif arg == 'Flags':                           # r23: the C_GameFlags object (GameMode::get is modelled)
                        st.append(self.game_flags)
                    else:
                        st.append(self.glob[self.gid[arg]])
                elif op in ('.LOCALINC2', '.LOCALINC3', '.LOCALINC'):
                    loc[li[arg]] += 1
                elif op in ('.LOCALDEC2', '.LOCALDEC3', '.LOCALDEC'):
                    loc[li[arg]] -= 1
                elif op == 'PUSHLOCALPAGE':
                    st.append(loc)
                elif op == 'PUSHGLOBALPAGE':
                    st.append(self.glob)
                elif op == 'A_REF':
                    assert isinstance(st[-1], (str, list)), (name, st[-1])
                elif op in ('S_ASSIGN', 'X_ASSIGN'):
                    assert op == 'S_ASSIGN' or arg == '1'
                    v = st.pop()
                    i = st.pop()
                    pg = st.pop()
                    if pg is self.glob:
                        assert i in self.glob, ('write to an unmodelled global', self.gname.get(i))
                    pg[i] = v
                    st.append(v)
                elif op == 'X_REF':
                    assert arg == '1'
                    i = st.pop()
                    pg = st.pop()
                    st.append(pg[i])
                elif op == 'PLUSA':
                    v = st.pop()
                    i = st.pop()
                    pg = st.pop()
                    pg[i] += v
                    st.append(pg[i])
                elif op == 'X_DUP':
                    st += st[-int(arg):]
                elif op in ('DELETE', 'POP'):
                    st.pop()
                elif op == 'VM_POP_PUSH1':                  # planted defects only: a call that consumes one value and "succeeds"
                    st.pop()
                    st.append(1)
                elif op == 'VM_POP2_PUSH1':                 # planted defects only (r21): a two-argument call that "succeeds"
                    st.pop()
                    st.pop()
                    st.append(1)
                elif op == 'VM_NOP':                        # planted defects only (r21): an operation removed
                    pass
                elif op == 'VM_POP_PUSHS':                  # planted defects only (r22): a call that consumes one value and gives ""
                    st.pop()
                    st.append('')
                elif op == 'VM_POP3_PUSH1':                 # planted defects only (r23): a one-argument CALLMETHOD that answers 1
                    st.pop()
                    st.pop()
                    st.pop()
                    st.append(1)
                elif op == 'NOT':
                    st.append(int(not st.pop()))
                elif op in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'LT', 'LTE', 'GT', 'GTE', 'EQUALE', 'NOTE',
                            'S_ADD', 'S_EQUALE', 'S_NOTE', 'S_LT', 'S_GT'):
                    z = st.pop()
                    x = st.pop()
                    if op in ('ADD', 'S_ADD'):
                        v = x + z
                    elif op == 'SUB':
                        v = x - z
                    elif op == 'MUL':
                        v = x * z
                    elif op == 'DIV':
                        v = int(x / z)
                    elif op == 'MOD':
                        v = x - int(x / z) * z
                    elif op in ('LT', 'S_LT'):
                        v = int(x < z)
                    elif op == 'LTE':
                        v = int(x <= z)
                    elif op in ('GT', 'S_GT'):
                        v = int(x > z)
                    elif op == 'GTE':
                        v = int(x >= z)
                    elif op in ('EQUALE', 'S_EQUALE'):
                        v = int(x == z)
                    else:
                        v = int(x != z)
                    st.append(v)
                elif op == 'S_MOD':
                    v = st.pop()
                    s = st.pop()
                    assert arg == '2'
                    st.append(s % v)
                elif op in ('IFZ', 'IFNZ'):
                    if bool(st.pop()) == (op == 'IFNZ'):
                        pc = labels[arg]
                elif op == 'JUMP':
                    pc = labels[arg]
                elif op == 'CALLFUNC':
                    ff = self.fs[arg]
                    n = len(ff['arguments'])
                    aa = st[-n:] if n else []
                    st = st[:-n] if n else st
                    rec.update(pc=pc, st=list(st), ret=ff['return-type'][0] != 0)
                    out = self.native(arg, aa)
                    if ff['return-type'][0] != 0:
                        st.append(out)
                elif op == 'CALLHLL':
                    lib, method, _ = arg.split()
                    # a wrap<string> / ref string argument is the local named by the .LOCALREF right before the call (r21)
                    self.hll_ref = (loc, li[prev[1]]) if prev[0] == '.LOCALREF' else None
                    self.hll(lib, method, st)
                elif op == 'PUSHSTRUCTPAGE':
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
                    return st[0] if st else None
                else:
                    raise AssertionError((name, op, arg))
            raise AssertionError(('no return', name))
        finally:
            self.frames.pop()

    # ---- resume model
    def saveable(self):
        """What a resume image holds in this model: every modelled global, the registrations, affinity, the date, and (if
        SystemService restores them) the session variables. Not in it: global read marks (MsgSkip), the save folder."""
        return copy.deepcopy(dict(glob=self.glob, registered=self.registered, feel=self.feel, today=self.today, vars=self.vars))

    def snapshot(self, push, rest=None):
        # the operand stack may hold the frame's own local page (PUSHLOCALPAGE) or the global page: copy the local page and
        # the stack together (one deepcopy keeps the reference), and mark the global page so a resume points at the live one
        frames = []
        for r in self.frames:
            st = ['@GLOBALPAGE' if x is self.glob else x for x in r['st']]
            loc, st = copy.deepcopy((r['loc'], st))
            frames.append(dict(name=r['name'], loc=loc, st=st, pc=r['pc'], ret=r['ret']))
        return dict(state=self.saveable(), frames=frames, push=push, rest=rest)

    def restore(self, state):
        self.glob = copy.deepcopy(state['glob'])
        self.registered = set(state['registered'])
        self.feel = dict(state['feel'])
        self.today = tuple(state['today'])
        if self.vars_in_save:
            self.vars = dict(state['vars'])

    def post_load(self):
        """セーブ実行 after ResumeLoad (gamesave::detail::セーブ実行_ロード後復帰処理): TempSelect goes unless a choice is open,
        BackSelect1/2, SystemSuspend and Reload go, g_bCanReturnBackSelect = 0 (the game's own branch, every load)."""
        drop = ['BackSelect1', 'BackSelect2', 'SystemSuspend', 'Reload'] + ([] if self.glob[self.G_BEGIN_SELECT] else ['TempSelect'])
        for n in drop:
            self.files.pop(PREFIX + n + '.asd', None)
            self.files.pop(PREFIX + n + '.vsf', None)
        self.glob[self.G_CAN_RETURN] = 0
        self.calls.append(('post_load', []))

    def resume(self, snap):
        """Continue the saved frames innermost first; each resumed frame gets its callee's return value when it expects one."""
        while True:
            try:
                self.frames = []
                self.restore(snap['state'])
                self.post_load()
                if snap.get('rest'):
                    snap['rest'](self)
                frames = snap['frames']
                pending = [dict(name=f['name'], loc=f['loc'], st=f['st'], pc=f['pc'], ret=f['ret']) for f in frames]
                self.frames = list(pending[:-1])
                val = snap['push']
                for i in reversed(range(len(pending))):
                    fr = pending[i]
                    if i < len(pending) - 1:
                        self.frames.pop()
                    val = self.run(fr['name'], resume=dict(loc=fr['loc'], st=fr['st'], pc=fr['pc'], push=val, has_push=fr['ret']))
                self.frames = []
                return val
            except Resume as r:
                snap = r.snap

    def run_top(self, name, args=()):
        """A harness-level call that may end in ResumeLoad (the sandbox)."""
        self.frames = []
        try:
            return self.run(name, args)
        except Resume as r:
            return self.resume(r.snap)

    def user_save(self, file, rest=None):
        """The player saves while the replayed event runs (the event's own frames are native here): loading it later returns
        from RunEvent (True) into KR_T18RunSandboxed after `rest` (the remainder of the event) ran."""
        self.files[file] = dict(kind='resume', snap=self.snapshot(push=1, rest=rest))
        self.files[vsf(file)] = dict(kind='vsf')
        self.calls.append(('user_save', file))

    def dialog(self):
        if self.cur is None:
            self.cur = dict(title=None, cols=1, items=[], type=None, limit=None, top=None)
        return self.cur

    def native(self, name, aa):
        if name == '■選択ダイアログ／初期化':
            self.cur = None
            return None
        if name == '■選択ダイアログ／タイプ設定':
            self.dialog()['type'] = aa[0]
            return None
        if name == '■選択ダイアログ／クリック制限／全体':
            self.dialog()['limit'] = 'all'
            return None
        if name == '■選択ダイアログ／横項目数':
            self.dialog()['cols'] = aa[0]
            return None
        if name == '■選択ダイアログ／タイトル設定':
            self.dialog()['title'] = aa[0]
            return None
        if name == '■選択ダイアログ／上座標制限値':
            self.dialog()['top'] = aa[0]
            return None
        if name == '■選択ダイアログ／選択肢追加':
            self.dialog()['items'].append((aa[0], aa[1], aa[2], int(bool(aa[3]))))
            return None
        if name == '■選択ダイアログ／実行':
            d = self.cur
            self.cur = None
            assert d is not None, 'run without a dialog'
            d['opt_title'] = self.vars.get('YoruKR.T8.Title', '')
            d['opt_color'] = self.vars.get('YoruKR.T8.Color', '')
            d['unwind'] = self.vars.get('YoruKR.T9.Unwind', '')
            self.dialogs.append(d)
            d['armed'] = self.vars.get('YoruKR.M.Home', '')
            if not self.script:
                raise Stop('dialog without a scripted answer: ' + ko(d['title'] or '').split('\n')[0])
            ans = self.script.pop(0)
            if isinstance(ans, Wait):
                r = ans.run(self, d)
            else:
                r = ans(d) if callable(ans) else ans
            d['answer'] = r
            return r
        if name == '■選択ダイアログ／存在確認':
            return int(self.cur is not None)
        if name == '■シンプルダイアログ':
            self.calls.append(('simple', ko(aa[0])))
            return None
        if name == 'C_SysVoice::GetFeelingRank_5':
            # r23: the game's 5-step rank (bounds read from the base code by game_rules(); LAbility::At(-) = -1 -> rank 0)
            c = aa[0]
            if not 1 <= c <= 8:
                return 0
            v = self.feeling(c)
            return sum(1 for b in VM.GAME['bounds'] if v > b)
        if name == 'N_ScenarioRegister::IsRegisteredEvent':
            self.reg_asked.append((aa[0], self.vars.get('YoruKR.C.Open', ''), int(VM.CHART_ROOT in self.parts)))
            return int(aa[0] in self.registered)
        # ---- r22
        if name == 'N_ModeScene::CheckEnabelScenario':
            return int((aa[0], aa[1]) in self.mem_enabled)
        if name == 'KR_CWait':
            return self.chart_wait()
        if name == 'KR_CReplayRun':
            no, ctx = aa
            self.replays.append(dict(no=no, ctx=ctx, ours=self.ours22(), open=self.vars.get('YoruKR.C.Open', ''),
                                     unwind=self.vars.get('YoruKR.T9.Unwind', ''), play=self.vars.get('YoruKR.C.Play', ''),
                                     t9play=self.vars.get('YoruKR.T9.Play', ''), dialog_open=self.cur is not None,
                                     title_root_show=self.parts.get(VM.TITLE_ROOT, {}).get('show')))
            self.calls.append(('replay', no, ctx))
            m = self.msg_of.get(no)
            if m is not None and m >= 0:
                self.flags.add(m)                  # the replay reads the scene: its read marks stay (MsgSkip is not in the resume image)
            return None
        if name == 'Ａ＿全表示':
            self.calls.append((name, list(aa)))
            return None
        if name == 'Ｐ＿ＣＧ設定':
            self.part(aa[0]).update(cg=aa[1], state=aa[2])
            return None
        if name == 'Ｐ＿クリック可能設定':
            self.part(aa[0])['click'] = int(bool(aa[1]))
            return None
        if name in ('C_UserInputManager::IsClickConfig', 'C_UserInputManager::IsClickLeft', 'C_UserInputManager::IsClickRight',
                    'C_UserInputManager::IsClickUP', 'C_UserInputManager::IsClickDown'):
            self.calls.append((name, []))
            return self.inputs.get(name.split('::')[1], 0)
        if name == 'L_Calendar::GetMonth':
            return self.today[0]
        if name == 'L_Calendar::GetDay':
            return self.today[1]
        if name == 'LSys3xScript::Prepare':
            # the real body: m_IsSysScenario = false; m_FuncName = the name without 「ＥＶ／元／」 when it starts with it
            s = aa[0]
            self.glob[self.G_SYS] = 0
            self.glob[self.G_FN] = s[len('ＥＶ／元／'):] if s.startswith('ＥＶ／元／') else s
            self.calls.append((name, list(aa)))
            return None
        if name == 'LSys3xScript::RunEvent':
            self.calls.append((name, []))
            if self.run_event:
                self.run_event(self)
            return 1
        if name in ('■ＡＤＶ消し', '■カジュアルモード設定呼び出し', 'KR_T8CharDatePage', 'KR_T8InfoPage'):
            self.calls.append((name, list(aa)))
            return None
        if name == '▲コンフィグ実行':
            self.calls.append((name, list(aa)))
            if self.config_inner:
                self.config_inner(self)
            return None
        if name == 'KR_T8PlaceText':
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
            return None
        if name == 'KR_T8PartyText':
            return proxy('PARTY')
        if name == 'EX_String':
            assert aa[0] == 'Ｅ＿セーブファイル名＿接頭語' and aa[1] == '' and aa[2] == 0, aa
            return PREFIX
        if name == 'gamesave::detail::TransAddSaveFileName':
            return vsf(aa[0])
        if name == 'gamesave::detail::セーブ実行':
            file, _, _, dump = aa
            assert not dump
            self.calls.append((name, [file]))
            if self.save_fail:
                self.calls.append(('msgbox', ['save failed: ' + file]))
                return 1
            self.files[file] = dict(kind='resume', snap=self.snapshot(push=0))
            self.files[vsf(file)] = dict(kind='vsf')
            return 1
        if name == 'gamesave::detail::ロード実行':
            file = aa[0]
            self.calls.append((name, [file]))
            got = self.files.get(file)
            assert got is not None and got['kind'] == 'resume', ('ResumeLoad of a missing file (the game stops with an error)', file)
            self.files[PREFIX + 'TempSelect.asd'] = got                   # セーブファイルコピー(-2, file) before the load
            self.files[PREFIX + 'TempSelect.vsf'] = dict(kind='vsf')
            raise Resume(got['snap'])
        # r21: the three engine helpers the request consumer uses (bodies read in the base: SYS_AddPunct appends 「\\」 when the
        # last character is not one; the input query is patched to the model; EndWaitForClick ends the current wait)
        if name == 'SYS_AddPunct':
            return aa[0] if aa[0].endswith('\\') else aa[0] + '\\'
        if name == 'KR_T8HomeClickable':                  # r13: the home panel rows become clickable / not (parts only)
            self.calls.append((name, list(aa)))
            return 0
        if name == 'C_UserInputManager::IsClickEnterOtherMouse':
            self.calls.append((name, []))
            return self.enter
        if name == 'AFL_Parts_EndWaitForClick':
            self.ended = aa[0]
            self.calls.append((name, list(aa)))
            return None
        if self.guard_saves and name.startswith(('gamesave::', 'AFL_GameSave_', '■セーブ', 'Ｓ＿コンフィグ', 'Ａ＿タイトルに戻る', 'Ａ＿ゲーム終了')):
            raise AssertionError(('r21: a save / load / config / title / confirming-exit call reached from the request consumer', name))
        return self.run(name, aa)

    # ---- r20: the objects r20's code touches (status view, training view) as struct pages {member index: value}
    ST_ACT = 'Game\\Scenes\\4000Homebase\\CharaStatus.pact'
    ALLY_ACT = 'Game\\Scenes\\Common\\SelectAlly.pact'
    ST_ROOT = 1000010472
    PORTRAIT = 1000010484                 # + p: the SelectAlly portrait CG of person p

    def status_view(self, chara, page=1, show_item=True):
        self.act[VM.ST_ACT] = {'ルートパーツ': VM.ST_ROOT}
        self.parts.setdefault(VM.ST_ROOT, dict(kind='root', show=1))
        fv = {5: chara, 'kind': 'C_FeelingView', 'moons': None, 'marks': 0}      # r23: m_FeelingView (slot 9), m_CharaNo = slot 5
        return {1: {4: VM.ST_ACT}, 2: 0, 9: fv, 11: chara, 15: int(show_item), 16: page, 'shown': None}

    # ---- r23: the abilities (from self.feel: person -> m_nFeeling), the moons' view, the three r23 sites
    GAME = None

    def abilities(self):
        return [{0: p, 24: self.feel.get(p, 0), 'kind': 'C_Ability'} for p in range(1, 9)]

    def feeling(self, c):
        # C_Ability@GetFeeling = m_nFeeling / GetFeelingRate() (the VM's DIV truncates toward zero like the engine)
        rate = VM.GAME['rates'].get(c, VM.GAME['rate_default'])
        return int(self.feel.get(c, 0) / rate)

    def site_target(self, owner):
        """The function index this candidate's code calls at the r23 site of `owner` (S8 pins the sites' shape)."""
        if owner not in self.site_cache:
            cv = L.versions(W / 'candidate_raw_code.jam') if not hasattr(VM, '_cv') else VM._cv
            VM._cv = cv
            v = L.live_version(self.meta, cv, L.fid_of(self.meta, owner))
            ops = [op for _, op in v['ops'] if not op.startswith('ENDFUNC')]
            if owner == 'C_HomeStatusView@SetActivePage':
                assert ops[-3:] == ['CALLMETHOD 0x0', 'CALLMETHOD 0x1', 'RETURN'] and ops[-5] == 'PUSHSTRUCTPAGE', ops[-6:]
                self.site_cache[owner] = int(ops[-4].split()[1], 16)
            elif owner == 'C_FeelingView@1':
                assert ops[0] == 'PUSHSTRUCTPAGE' and ops[2] == 'CALLMETHOD 0x0', ops[:3]
                self.site_cache[owner] = int(ops[1].split()[1], 16)
            else:
                raise AssertionError(owner)
        return self.site_cache[owner]

    def status_view_init(self, show_item=True):
        """C_HomeStatusView@Init's tail as the game runs it: new C_FeelingView(root), SetChara(0, IsShowFeelingPage()),
        SetActivePage(0) (NowPage starts at 0)."""
        sv = self.status_view(0, page=0, show_item=show_item)
        fid = lambda n: self.fs[n]['index']
        b = self.method(fid('C_HomeStatusView@IsShowFeelingPage'), sv, [])
        self.method(fid('C_FeelingView@SetChara'), sv[9], [0, b])
        self.method(fid('C_HomeStatusView@SetActivePage'), sv, [0])
        return sv

    def status_view_destroy(self, sv):
        """C_HomeStatusView@1 drops m_FeelingView -> C_FeelingView@1 runs: its first call is the r23 site (DeleteMarks's place)."""
        fv = sv[9]
        self.method(self.site_target('C_FeelingView@1'), fv, [])
        fv['destroyed'] = True
        self.destroyed.append(fv)
        sv[9] = -1

    def moon_part(self):
        return self.parts.get(R23_MOON)

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
            # r23: the body ends with m_FeelingView.UpdatePage(<the r23 site>()) - the site's target as this candidate's code has it
            b = self.method(self.site_target('C_HomeStatusView@SetActivePage'), obj, [])
            self.method(self.fs['C_FeelingView@UpdatePage']['index'], obj[9], [b])
            return None
        if name in ('C_HomeStatusView@IsShowFeelingPage', 'C_FeelingView@Enabled'):
            return self.run(name, aa, this=obj)                     # r23: the game's own bodies
        if name == 'C_GameFlags@GameMode::get':
            return self.game_mode
        if name == 'C_Ability@GetFeeling':
            return self.feeling(obj[0])
        if name == 'C_Ability@GetFeelingInnerValue':
            return obj[24]
        if name == 'C_FeelingView@SetChara':
            # the original: m_CharaNo = c; if !Enabled(c) hide; else Update(c, turning, GetFeeling) + UpdatePage(bShow)
            obj[5] = aa[0]
            en = self.method(self.fs['C_FeelingView@Enabled']['index'], obj, [aa[0]])
            obj['moons'] = int(bool(en) and bool(aa[1]))
            obj['marks'] = 1 if en else 0
            return None
        if name == 'C_FeelingView@UpdatePage':
            en = self.method(self.fs['C_FeelingView@Enabled']['index'], obj, [obj[5]])
            obj['moons'] = int(bool(en) and bool(aa[0]))
            return None
        if name == 'C_FeelingView@DeleteMarks':
            obj['marks'] = 0
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
            # the original sets m_CharaNo and the portrait, m_FeelingView.SetChara(c, IsShowFeelingPage()) (r23: the moons), then
            # SetActivePage(NowPage) at the r20 site -> KR_T20StActive (S8)
            obj[11] = aa[0]
            b = self.method(self.fs['C_HomeStatusView@IsShowFeelingPage']['index'], obj, [])
            self.method(self.fs['C_FeelingView@SetChara']['index'], obj[9], [aa[0], b])
            return self.method(self.fs['KR_T20StActive']['index'], obj, [obj[16]])
        if name == 'C_SceneTrainingView@GetOnmouseChara':
            return self.hover
        if name == 'C_SceneTrainingView@AppearStandChara':
            return None
        if name == 'C_SceneTrainingView@SelectAlly::get':
            return obj[10]
        if name.startswith(('KR_T20', 'KR_T23')):
            return self.run(name, aa, this=obj)
        raise AssertionError(('unmodelled method', name))

    def part(self, n):
        return self.parts.setdefault(n, dict(kind='new', show=0))

    def parts_hll(self, method, st):
        # (number of arguments, returns a value)
        sig = dict(IsExist=(1, True), Release=(1, False), GetActivityPartsNumber=(2, True), IsComponentShow=(1, True),
                   Parts_SetText=(3, True), Parts_SetFont=(12, True), Parts_SetTextEnableTag=(3, False),
                   Parts_SetTextLineSpace=(3, True), Parts_SetParentPartsNumber=(2, False), SetComponentPos=(3, False),
                   SetComponentPosZ=(2, False), SetComponentShow=(2, False), SetComponentMulColor=(4, False),
                   Parts_SetPassCursor=(2, False), IsExistActivity=(1, True))
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
            # the float arguments reach the VM as the int bit patterns native_lower gives F_PUSH
            f32 = lambda v: struct.unpack('<f', struct.pack('<i', v))[0] if isinstance(v, int) else float(v)
            self.part(a[0])['pos'] = (f32(a[1]), f32(a[2]))
        elif method == 'SetComponentPosZ':
            self.part(a[0])['z'] = a[1]
        elif method == 'SetComponentShow':
            self.part(a[0])['show'] = int(bool(a[1]))
        elif method == 'SetComponentMulColor':
            self.part(a[0])['mul'] = tuple(a[1:4])
        elif method == 'Parts_SetPassCursor':
            self.part(a[0])['pass'] = int(bool(a[1]))
        elif method == 'IsExistActivity':
            out = int(a[0] in self.act)
        if method == 'SetComponentShow':
            self.shows.append((a[0], int(bool(a[1]))))
        if ret:
            st.append(out)

    def ours(self):
        return sorted(n for n in self.parts if 2026092000 <= n < 2026092100)

    # ---- r22: the chart's parts, waits and the title
    CHART_ROOT = 2026092200
    TITLE_ACT = 'Game\\Scenes\\0000Title\\SceneTitle.pact'
    TITLE_ROOT = 1000010035                  # the title root the native probe logged (any number outside the chart range works)

    def ours22(self):
        return sorted(n for n in self.parts if 2026092200 <= n < 2026092312)

    def title_scene(self):
        self.act[VM.TITLE_ACT] = {'ルートパーツ': VM.TITLE_ROOT}
        self.parts.setdefault(VM.TITLE_ROOT, dict(kind='root', show=1))

    def chart_snapshot(self):
        f32 = lambda v: struct.unpack('<f', struct.pack('<i', v))[0] if isinstance(v, int) else float(v)
        out = {}
        for n in self.ours22():
            q = dict(self.parts[n])
            out[n] = q
        return out

    def chart_wait(self):
        """KR_CWait: the chart's AFL_Parts_WaitForClick (the KR_CFrame delegate, key cancel). The scripted answer is the number a
        click on a part gives (or 0 = right click / space, 1-4 = the arrow keys); a Wait object runs KR_CFrame per frame."""
        d = dict(kind='chart', title=proxy('<chart>'), cols=0, items=[], parts=self.chart_snapshot(),
                 open=self.vars.get('YoruKR.C.Open', ''), all=self.vars.get('YoruKR.C.All', ''), ctx=self.vars.get('YoruKR.C.Ctx', ''),
                 armed=self.vars.get('YoruKR.M.Home', ''), tick='KR_CFrame')
        self.dialogs.append(d)
        self.charts.append(d)
        if not self.script:
            raise Stop('chart wait without a scripted answer')
        ans = self.script.pop(0)
        if isinstance(ans, Wait):
            r = ans.run(self, d)
        else:
            r = ans(self, d) if callable(ans) else ans
        d['answer'] = r
        return r

    def hll(self, lib, method, st):
        if lib == 'PartsEngine':
            self.parts_hll(method, st)
            return
        if lib == 'SystemService':
            if method == 'SystemVariable_Get':
                st.append(self.vars.get(st.pop(), ''))
                return
            if method == 'SystemVariable_Set':
                v = st.pop()
                k = st.pop()
                self.vars[k] = v
                return
        if lib == 'MsgSkip' and method == 'GetFlag':
            m = st.pop()
            if m < 0:
                self.getflag_neg += 1
            st.append(int(m in self.flags))
            return
        if lib == 'system':
            if method == 'ExistSaveFile':
                st.append(int(st.pop() in self.files))
                return
            if method == 'DeleteSaveFile':
                file = st.pop()
                self.calls.append(('delete', [file]))
                st.append(int(self.files.pop(file, None) is not None))
                return
            if method == 'GetSaveFolderName':                     # r21 (09-24 KR_TermFile's first call)
                st.append(self.save_dir)
                return
            if method == 'Exit':                                  # r21: the game ends here
                code = st.pop()
                self.exited = code
                self.calls.append(('exit', code))
                raise VMExit(code)
            if method == 'Peek':
                raise AssertionError('system.Peek reached: system.Exit returned in the model')
        # r21: the file API (absolute paths only in r21's code; TextFile writes CP932 as given and LF as CR LF - 09-24 files,
        # r18 probe note; ReadAll returns the bytes as they are on disk)
        if lib == 'FileOperation':
            p = st.pop()
            assert isinstance(p, str) and re.match(r'^[A-Z]:\\', p), ('r21: a relative or odd path', p)
            if method == 'ExistFile':
                self.file_calls.append(('exist', p))
                st.append(int(p in self.disk))
                return
            if method == 'DeleteFile':
                self.file_calls.append(('delete', p))
                if p in self.disk and p not in self.fail_delete:
                    del self.disk[p]
                    st.append(1)
                else:
                    st.append(0)
                return
            if method == 'ExistFolder':
                self.file_calls.append(('existfolder', p))
                st.append(int(p.rstrip('\\') in self.dirs))
                return
            if method == 'CreateFolder':
                self.file_calls.append(('mkdir', p))
                self.dirs.add(p.rstrip('\\'))
                st.append(1)
                return
        if lib == 'TextFile':
            if method == 'WriteAll':
                text = st.pop()
                p = st.pop()
                assert isinstance(p, str) and re.match(r'^[A-Z]:\\', p), ('r21: a relative or odd path', p)
                self.file_calls.append(('write', p))
                if p in self.fail_write or p.rsplit('\\', 1)[0] not in self.dirs:
                    st.append(0)
                    return
                self.disk[p] = text.replace('\n', '\r\n')
                st.append(1)
                return
            if method == 'ReadAll':
                st.pop()                                         # the value .LOCALREF pushed; the text goes to the local itself
                p = st.pop()
                assert isinstance(p, str) and re.match(r'^[A-Z]:\\', p), ('r21: a relative or odd path', p)
                self.file_calls.append(('read', p))
                assert self.hll_ref is not None, 'TextFile.ReadAll without a local to write into'
                if p in self.disk:
                    loc, idx = self.hll_ref
                    loc[idx] = self.disk[p]
                    st.append(1)
                else:
                    st.append(0)
                return
        if lib == 'SystemService' and method == 'GetGameFolderPath':
            st.append(self.game_dir)
            return
        if lib == 'String':
            if method == 'ToInt':
                st.append(int(st.pop()))
                return
            if method == 'Length':
                st.append(len(st.pop()))
                return
            if method == 'Find':
                key = st.pop()
                text = st.pop()
                st.append(text.find(key))
                return
            if method == 'GetPart#1':
                count = st.pop()
                idx = st.pop()
                text = st.pop()
                st.append(text[idx:idx + count])
                return
        raise AssertionError((lib, method))

    def v(self, key):
        return self.vars.get('YoruKR.T9.' + key, '')

    def state_all(self):
        """Everything the model knows, for before/after comparisons (session variables normalised: '' = unset)."""
        return dict(glob=dict(self.glob), registered=set(self.registered), feel=dict(self.feel), today=tuple(self.today),
                    vars={k: v for k, v in self.vars.items() if v != ''}, flags=set(self.flags), files=sorted(self.files))
