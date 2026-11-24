"""Claude Opus 5.5 (2026-09-27) r18: verification of the calendar candidate without the game (after verify_calendar_r17.py).

  python verify_calendar_r18.py              all checks (must pass)
  python verify_calendar_r18.py --selftest   all checks, then every check again against a planted defect (each must fail)
  python verify_calendar_r18.py --native     compare what the native probe logged (titles, drawer rows, the home panel, the
                                             sandbox before/after state, the lock pages) with the VM for the same save

Static (bytes of base vs candidate, read only):
  S1 candidate = manifest; every base function entry identical except the eight forwarded r15 functions (address only, new
     body in the appended code); non-function metadata identical; every added function is KR_T18*
  S2 the whole base CODE is unchanged except the 4 operand bytes of KR_T9HomeCasual's `CALLFUNC LSys3xScript::RunEvent`,
     which now hold KR_T18RunSandboxed; r15's nine swap sites still hold r15's operands
  S3 MSG1 identical, STR0 prefix identical; PACT/EX not in the payload
  S4 user saves (copies, every RSM resume file): every saved frame (ip + returns) resolves to the same function entry and the
     same instruction bytes at its return address in the candidate; no frame inside a forwarded function
  S5 native opcode audit of the candidate against the runtime exe dispatch table
  S6 pinned functions (KR_T9HomeCasual, KR_T9HomeConfig, CheckGameSysButtons, Run, RunEvent): index and address identical to
     the r15 candidate and to the base; code bytes identical except KR_T9HomeCasual's one operand (exactly those bytes differ)
  S7 KR_T18RunSandboxed has RunEvent's signature (no arguments, bool) and sits where the manifest says (pinned from r18 on)
Extended VM (the candidate's own compiled bodies, engine calls modelled):
  V1-V15 r17's checks on the renamed KR_T18* bodies (tables, page geometry, day cells, navigation, r15 flows, seen states,
      achievement counts, rows, panel, real saves, bars). The r15 replay flows now go through the sandbox.
  V16 replay lock: every card page and every scene page (1,164 events) in three save states and three contexts: 「이 장면 재생」
      only when that scene is ○ (IsRegisteredEvent); ● / △ pages carry the lock line instead of the item and never request;
      bundle stages judged one by one from the stage list; 회상 · 그 밖 replays too; the sandbox note on ○ pages
  V17 sandbox: the whole replay flow (home menu -> window -> 이 장면 재생 -> home menu returns 3 -> KR_T9HomeCasual (candidate
      bytes: the swapped operand) -> KR_T18RunSandboxed) with the engine's resume modelled (ResumeSave = snapshot of every
      saved global + the VM frames; ResumeLoad = restore + the game's own post-load branch + continue the saved frames).
      The whole global state before the window == after the replay except the allow list (global read marks, the game's own
      post-load deletion of the back-to-choice files and flag, UI session variables); the temp file exists during the replay
      and is gone after; Prepare's two globals are back; both with and without SystemService restoring session variables
  V18 saved during the replay, loaded later: no temp file -> the rest of the event runs and the restore is skipped (safety
      valve); a leftover temp file -> restored to it
  V19 ResumeSave fails (no .asd/.vsf written): no RunEvent, the notice, Prepare's globals back, no temp file
  V20 a request that bypasses the lock reaching the casual site: KR_T18RunSandboxed refuses (no save, no RunEvent)
"""
import sys, json, re, struct, collections, math, copy, time, random, datetime, io, contextlib, bisect
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r18lib as L

O = HERE / 'candidate'
W = L.WORK / 'build'
MARKS = '†‡¶〓'
PICK = 2026092401
H_MAX = 704
SUMMARY_TOP = 186                          # ■選択ダイアログ／上座標制限値 on the summary page (clears the panel's 전체 row)
PANEL_ROW_BOTTOM = 170                     # the home panel's 「전체」 row ends above this y (probe screenshot, r16 cal_home_before)
COL_CAP = {1: 38, 2: 20, 3: 13}          # full-width units per item (1280 px screen, 28 px a glyph, 52 px item margin)
LANES = ['main', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'dungeon']
LANE_KR = ['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전']
KINDS = ['prio', 'after', 'turned', 'invite', 'walk', 'etc', 'mem', 'unused']
KIND_KR = ['우선 대화', '특훈 뒤 대화', '반한 뒤 대화', '초대', '던전 동행', '그 밖', '회상', '쓰이지 않음']
SLOT_KR = {1: '아침', 2: '밤', 3: '낮', 4: '저녁'}
SLOT_RANK = {1: 0, 3: 1, 4: 2, 2: 3, 0: 9}
LEGEND17 = '†▲놓침 ‡●앞으로 ¶○다 봄 〓금색†=오늘'
LANE_LEGEND = '●안 봄 △다른 저장 ○이 저장'
WEEKDAYS = '　일　　　월　　　화　　　수　　　목　　　금　　　토'
MEM_HEAD = '〓회상 · 그 밖 (패널 밖)'
MEM_NOTE = '†회상 화면의 재생본과 게임에서 부르지 않는 장면'
OUT_LINE = '†패널 밖 %d/%d (회상 재생본·미사용·던전)'
FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
           'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
           'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}
TOTAL_EVENTS = 1164
PANEL_EVENTS = 1043
BAR_RE = re.compile(r'([■□]{10}|[■□]{5}) (\d+)/(\d+)|(\d+)/(\d+) ([■□]{5})(?![■□])')
# r18 texts (independent of the jaf)
PLAY = '이 장면 재생'
LOCK_UNSEEN = '‡● 안 본 장면입니다 · 재생은 본 뒤에'
LOCK_OTHER = '†△ 다른 저장에서만 읽은 장면입니다 · 이 저장에서 본 뒤에'
SANDBOX_NOTE = '〓재생이 끝나면 진행 상태는 재생 전으로 돌아갑니다'
OLD_WARN = '〓사슬이 이어지고 읽음·친밀도가 오릅니다. 검수용 저장에서 쓰세요'
NOTE_C = '¶설정 창을 닫으면 본거지에서 재생합니다.'
NOTE_NONE = '¶본거지에서 연 달력에서만 재생할 수 있습니다.'
STATE_LINES = {2: '¶○ 이 저장에서 봤습니다', 1: '†△ 다른 저장에서만 읽었습니다', 0: '‡● 아직 안 봤습니다'}
NOTICE_FAIL = '재생 전 상태를 저장하지 못해 재생하지 않았습니다.'
NOTICE_LOCK = '이 저장에서 본 장면만 재생할 수 있습니다.'
PREFIX = 'NightR'                           # EX Ｅ＿セーブファイル名＿接頭語 of this game (the user's slots are NightR%02d.asd)
TEMP = PREFIX + 'KRReplay.asd'
TEMP_VSF = PREFIX + 'KRReplay.vsf'
GAME_TEMPS = ['QC', 'TempSelect', 'BackSelect1', 'BackSelect2', 'MemoryMode', 'SystemSuspend', 'Reload']


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


def vsf(file):
    """gamesave::detail::TransAddSaveFileName: the part before 「.asd」 + 「.vsf」 (checked against the real body in V17)."""
    i = file.find('.asd')
    return file[:i] + '.vsf'


# ============================================================== VM (r17's, plus globals, the save folder and resume)
class VM:
    G_FN, G_SYS, G_EVRESULT, G_BEGIN_SELECT, G_CAN_RETURN = 214, 215, 190, 70, 72

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

    def run(self, name, args=(), resume=None):
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
        try:
            while pc < len(ops):
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
                    self.hll(lib, method, st)
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
            if not self.script:
                raise Stop('dialog without a scripted answer: ' + ko(d['title'] or '').split('\n')[0])
            ans = self.script.pop(0)
            r = ans(d) if callable(ans) else ans
            d['answer'] = r
            return r
        if name == '■選択ダイアログ／存在確認':
            return int(self.cur is not None)
        if name == '■シンプルダイアログ':
            self.calls.append(('simple', ko(aa[0])))
            return None
        if name == 'N_ScenarioRegister::IsRegisteredEvent':
            return int(aa[0] in self.registered)
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
        return self.run(name, aa)

    def hll(self, lib, method, st):
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


# ============================================================== expectations (independent of the build script)
def parse_panel_groups(path):
    lines = [l.strip() for l in Path(path).read_text('utf8').splitlines()]
    groups = collections.defaultdict(list)
    cur = None
    for i, l in enumerate(lines):
        if l == '.LOCALREF group' and i + 2 < len(lines) and lines[i + 1].startswith('PUSH ') and lines[i + 2] == 'EQUALE':
            cur = int(lines[i + 1].split()[1])
            continue
        z = re.match(r'S_PUSH "(.*)"', l)
        if z and cur is not None:
            groups[cur].append(json.loads('"' + z.group(1) + '"'))
    return groups


def base_panel_set():
    """The event names the r9 panel counts, read from the BASE AIN (not from anything the r17 build produced)."""
    d = L.WORK / 'vm' / 'base'
    d.mkdir(parents=True, exist_ok=True)
    path = d / 'KR_PlayerEventCount.jam'
    if not path.exists():
        L.cmd('ain', 'dump', '--function', 'KR_PlayerEventCount', '-o', path, L.base_dir() / 'NightRemaster.ain')
    groups = parse_panel_groups(path)
    return {n for v in groups.values() for n in v}, groups


def expectations():
    sys.path.insert(0, str(L.FLOW / 'chart'))
    import build_chart_v2 as V2
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data = V2.build(str(L.TMP / 'chart_v2_from_r18_verify.html'))
    ev = {int(k): v for k, v in data['ev'].items()}
    cards = []
    for c in data['cards']:
        pl = c['pl']
        cards.append(dict(key=c['key'], month=int(c['page']), lane=LANES.index(c['lane']), day=pl.get('d', 0), slot=pl.get('slot', 0) or 0,
                          size=c['n'], entry=c['entry'], stages=[r[0] for r in c['rows'] if r[6]]))
    cards.sort(key=lambda x: (x['month'], x['lane'], x['day'] if x['day'] else 99, SLOT_RANK[x['slot']], x['key']))
    chips = []
    for ch in data['chips']:
        month = 12 if ch['page'] == 'mem' else int(ch['page'])
        lane = LANES.index(ch['lane']) if ch['lane'] in LANES else (8 + int(ch['lane'][3:]) if ch['lane'].startswith('mem') else 16)
        chips.append(dict(id=ch['id'], month=month, lane=lane, kind=KINDS.index(ch['kind']), scenes=[x[0] for x in ch['order'] if x[4]]))
    pset, groups = base_panel_set()
    out = {no for no, e in ev.items() if e['fn'] not in pset}
    assert len(pset) == PANEL_EVENTS and pset <= {e['fn'] for e in ev.values()} and len(out) == TOTAL_EVENTS - PANEL_EVENTS
    return dict(data=data, ev=ev, cards=cards, chips=chips, w1={p['m']: p['w1'] for p in data['pages'] if p.get('m')}, mlen=V2.MLEN,
                out=out, panel_groups=groups)


# ---- independent r17 display model (Fraction arithmetic, not the jaf's integer formulas)
def bar(k, n, cells):
    f = math.floor(Fraction(k * cells, n) + Fraction(1, 2)) if n > 0 else 0
    f = min(cells, max(0, f))
    if k < n and f == cells:
        f = cells - 1
    return '■' * f + '□' * (cells - f)


def pct(k, n):
    p = math.floor(Fraction(100 * k, n) + Fraction(1, 2)) if n > 0 else 0
    if k < n:
        p = min(p, 99)
    return '(%d%%)' % p


def t8pct(k, total):
    """r9 KR_T8Pct as the panel prints it: 0.1% floored, 「0.0%」 for nothing, at most 100.0%."""
    if total <= 0 or k <= 0:
        return '0.0%'
    per = min(1000, (k * 1000) // total)
    return '%d.%d%%' % (per // 10, per % 10)


def month_name(m):
    return '회상 · 그 밖' if m == 12 else '%d월' % m


def seen_fn(X, regs, no):
    return X['ev'][no]['fn'] in regs


def counted(X, month, no):
    """r17: 4-11월 count only the panel set; 회상 · 그 밖 counts all of its own (all outside the panel)."""
    return month == 12 or no not in X['out']


def tally(X, regs, month, scenes):
    n = k = 0
    for s in scenes:
        if counted(X, month, s):
            n += 1
            k += int(seen_fn(X, regs, s))
    return k, n


def units(X, regs, month, lane=None):
    """(seen, total) counted scene units of a month (and a lane): card stages + drawer scenes."""
    n = k = 0
    for c in X['cards']:
        if c['month'] == month and (lane is None or c['lane'] == lane):
            a, b = tally(X, regs, month, c['stages'])
            k += a
            n += b
    for ch in X['chips']:
        if ch['month'] == month and (lane is None or ch['lane'] == lane):
            a, b = tally(X, regs, month, ch['scenes'])
            k += a
            n += b
    return k, n


def has_list(X, month, lane):
    return any(c['month'] == month and c['lane'] == lane for c in X['cards']) or any(ch['month'] == month and ch['lane'] == lane for ch in X['chips'])


def drawer_units(X, regs, month):
    n = k = 0
    for ch in X['chips']:
        if ch['month'] == month:
            a, b = tally(X, regs, month, ch['scenes'])
            k += a
            n += b
    return k, n


def row(name, k, n):
    return '%s %d/%d %s' % (name, k, n, bar(k, n, 5))


def chip_name(ch, with_lane):
    l = ch['lane']
    if l >= 9:
        return ('회상 %d쪽' % (l - 8)) if l <= 15 else '쓰이지 않는 장면'
    name = KIND_KR[ch['kind']]
    return (LANE_KR[l] + ' · ' + name) if with_lane else name


def chip_row(X, regs, ch, with_lane):
    k, n = tally(X, regs, ch['month'], ch['scenes'])
    return row(chip_name(ch, with_lane), k, n)


def day_state(X, regs, month, day, today):
    """state 0 none, 1 앞으로, 2 다 봄, 3 놓침 (every stage of the dated cards of that day)."""
    on = [c for c in X['cards'] if c['month'] == month and c['day'] == day]
    if not on:
        return 0
    unseen = any(not seen_fn(X, regs, s) for c in on for s in c['stages'])
    if not unseen:
        return 2
    return 3 if (month, day) < tuple(today) else 1


def want_cell(X, regs, month, day, today):
    inr = not ((month == 4 and day < 9) or (month == 11 and day > 17))
    if not inr:
        col, mark = 3, '　'
    else:
        st = day_state(X, regs, month, day, today)
        col = {0: 1, 1: 2, 2: 3, 3: 1}[st]
        mark = {0: '　', 1: '●', 2: '○', 3: '▲'}[st]
    if (month, day) == tuple(today):
        col = 0
    return col, mark


def month_cols(X, month):
    lanes = sum(1 for l in range(9) if has_list(X, month, l))
    items = lanes + 4 + (1 if month > 4 else 0)
    weeks = math.ceil((X['w1'][month] + X['mlen'][month]) / 7)
    return 2 if 64 + 34 * (3 + weeks) + 48 * math.ceil(items / 2) <= H_MAX else 3


# ============================================================== static checks
def swap_of(man):
    s = man['same_length_sites']
    assert len(s) == 1 and s[0]['function'] == L.SWAP_OWNER and s[0]['original'] == L.SWAP_OLD and s[0]['replacement'] == L.SANDBOX, s
    return s[0]


def static_checks(base, cand, man, m, nm, counts, mutate_bytes=None, mutate_meta=None, parts=('S1', 'S2', 'S3', 'S4', 'S6', 'S7')):
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
    swap = swap_of(man)
    a, b = swap['site'] + 2, swap['site'] + 6
    sb = L.fid_of(nm, L.SANDBOX)
    if 'S1' in parts:
        for f in m['functions']:
            g = nm['functions'][f['index']]
            if f['index'] in fw:
                assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, f['name']
                assert g['address'] >= oldn, ('forwarder not in the appended code', f['name'])
            else:
                assert g == f, ('base function entry changed', f['index'], f['name'])
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
        assert all(n.startswith('KR_T18') for n in man['added_functions']), 'added functions must all be KR_T18*'
        assert not any(L.raw_symbol(nm, f['index']).startswith(('KR_T16', 'KR_T17')) for f in nm['functions']), 'r16/r17 names in the candidate'
        counts['S1_metadata'] += 1
    if 'S2' in parts:
        diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
        assert diff and set(diff) <= set(range(a, b)), ('base CODE bytes changed beyond the one RunEvent operand', diff[:8])
        assert bytes(new[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, sb), 'the swapped operand is not KR_T18RunSandboxed'
        assert bytes(old[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, L.fid_of(m, L.SWAP_OLD)), 'base site is not the RunEvent call'
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s in rman['same_length_sites']:
            ad = s['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s['after'], ('r15 swap missing in the base', s['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s['after'], ('r15 swap site no longer applied', s['function'], s['replacement'])
        counts['S2_r15_sites_kept'] = len(rman['same_length_sites'])
        counts['S2_base_code_bytes'] = oldn
        counts['S2_base_code_bytes_changed'] = len(diff)
        counts['S2_changed_bytes_inside_the_operand'] = int(set(diff) <= set(range(a, b)))
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed']
        counts['S3_text'] += 1
    if 'S6' in parts:
        ra = L.R15 / 'candidate' / 'NightRemaster.ain'
        rraw = L.unpack(ra.read_bytes())
        rcode = rraw[16:16 + struct.unpack_from('<I', rraw, 12)[0]]
        rm = L.read_meta(L.R15 / 'work' / 'build' / 'candidate_meta.json')
        rv = L.versions(L.R15 / 'work' / 'build' / 'candidate_raw_code.jam')
        starts = sorted({v['start'] for vs in rv.values() for v in vs})
        ccode = new[16:16 + struct.unpack_from('<I', new, 12)[0]]
        bcode = old[16:16 + oldn]
        for name in L.PINNED:
            i = L.fid_of(rm, name)
            f = rm['functions'][i]
            assert nm['functions'][i] == f == m['functions'][i], ('pinned function entry changed', name)
            j = bisect.bisect_right(starts, f['address'])
            end = starts[j] - 6 if j < len(starts) else len(rcode)
            lo = f['address'] - 6
            ref = rcode[lo:end]
            got = ccode[lo:end]
            assert ref == bcode[lo:end], ('pinned code in the base differs from r15', name)
            differ = [lo + k for k in range(len(ref)) if got[k] != ref[k]]
            if name == L.SWAP_OWNER:
                assert differ and set(differ) <= set(range(a, b)), ('pinned KR_T9HomeCasual differs beyond the one operand', [hex(x) for x in differ[:8]])
                counts['S6_KR_T9HomeCasual_bytes_changed'] = len(differ)
            else:
                assert not differ, ('pinned code changed', name)
            counts['S6_pinned_bytes'] += len(ref)
        counts['S6_pinned_functions'] = len(L.PINNED)
    if 'S7' in parts:
        g, r = nm['functions'][sb], nm['functions'][L.fid_of(nm, L.SWAP_OLD)]
        assert g['arguments'] == r['arguments'] == [] and g['return-type'] == r['return-type'] == [47, -1, 0, None], 'sandbox signature'
        assert man['sandbox']['index'] == sb and man['sandbox']['address'] == g['address'], 'manifest sandbox entry'
        assert man['added_functions'][L.SANDBOX] == sb
        counts['S7_sandbox_signature_equal_RunEvent'] = 1
    if 'S4' not in parts:
        return []
    vers = L.versions(L.base_dir() / 'raw_code.jam')
    bycrc = collections.defaultdict(list)
    for f in m['functions']:
        bycrc[f['crc'] & 0xffffffff].append(f)
    frames = []
    live = 0
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
            assert nm['functions'][f['index']] == f or f['index'] in fw, ('saved frame function moved', name, f['name'])
            ad = rr['address']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes(new[16 + ad:16 + ad + 6]), ('saved return bytes differ', name, rr['name'][:40], hex(ad))
            live += int(start == f['address'])
            frames.append(dict(file=name, fid=f['index'], offset=rr['offset'], live=start == f['address'], function=L.raw_symbol(m, f['index'])))
    counts['S4_saves'] = len({x['file'] for x in frames})
    counts['S4_frames'] = len(frames)
    counts['S4_frames_in_live_versions'] = live
    counts['S4_frames_in_KR_T9HomeCasual'] = sum(1 for x in frames if x['function'] == 'KR_T9HomeCasual')
    counts['S4_frames_in_forwarded'] = sum(1 for x in frames if x['function'] in FORWARD)
    return frames


# ============================================================== VM checks
def table_checks(vm, X, counts):
    cards, chips, ev = X['cards'], X['chips'], X['ev']
    stage_i = 0
    for k, c in enumerate(cards):
        info = vm.run('KR_T9CardInfo', [k])
        got = dict(lane=info // 100000, day=(info // 1000) % 100, slot=(info // 100) % 10, size=info % 100, entry=vm.run('KR_T9CardEntry', [k]))
        want = dict(lane=c['lane'], day=c['day'], slot=c['slot'], size=c['size'], entry=c['entry'])
        assert got == want, (k, c['key'], got, want)
        s0 = vm.run('KR_T9CardStage', [k])
        assert s0 == stage_i and [vm.run('KR_T9StageEv', [s0 + i]) for i in range(c['size'])] == c['stages'], (k, c['key'])
        stage_i += c['size']
        assert vm.run('KR_T9CardMonth', [k]) == c['month']
    for mo in range(4, 12):
        ks = [k for k, c in enumerate(cards) if c['month'] == mo]
        assert (vm.run('KR_T9CardFirst', [mo]), vm.run('KR_T9CardEnd', [mo])) == ((ks[0], ks[-1] + 1) if ks else (0, 0)), mo
        assert vm.run('KR_T9W1', [mo]) == X['w1'][mo] and vm.run('KR_T9MLen', [mo]) == X['mlen'][mo]
    scene_i = 0
    for c, ch in enumerate(chips):
        info = vm.run('KR_T9ChipInfo', [c])
        assert (info // 10000, (info // 1000) % 10, info % 1000) == (ch['lane'], ch['kind'], len(ch['scenes'])), (c, ch['id'])
        s0 = vm.run('KR_T9ChipScene', [c])
        assert s0 == scene_i and [vm.run('KR_T9SceneEv', [s0 + i]) for i in range(len(ch['scenes']))] == ch['scenes'], ch['id']
        scene_i += len(ch['scenes'])
        assert vm.run('KR_T9ChipMonth', [c]) == ch['month'], ch['id']
    for no, e in ev.items():
        assert vm.run('KR_T9EvMsg', [no]) == (e['m0'] if e['m0'] is not None else -1), no
        assert vm.run('KR_T9Fn', [no]) == e['fn'], (no, vm.run('KR_T9Fn', [no]))
        assert ko(vm.run('KR_T9EvWhen', [no])) and ko(vm.run('KR_T9EvWho', [no])), no
    assert sorted([s for c in cards for s in c['stages']] + [s for ch in chips for s in ch['scenes']]) == sorted(ev)
    assert len(ev) == TOTAL_EVENTS
    # r17 panel-outside table = what the BASE panel code does not count
    got_out = {no for no in ev if vm.run('KR_T18Out', [no]) == 1}
    assert got_out == X['out'], ('KR_T18Out differs from the base panel set', sorted(got_out ^ X['out'])[:5])
    assert all(vm.run('KR_T18Out', [no]) == 0 for no in ev if no not in X['out'])
    total = vm.run('KR_T18OutTotal')
    assert total == len(X['out']) == TOTAL_EVENTS - PANEL_EVENTS == 121
    assert sorted(vm.run('KR_T18OutEv', [i]) for i in range(total)) == sorted(X['out']) and vm.run('KR_T18OutEv', [total]) == -1
    m12 = {s for ch in chips if ch['month'] == 12 for s in ch['scenes']}
    assert m12 <= X['out'] and len(m12) == 113, 'the 회상 · 그 밖 page must be entirely outside the panel'
    rest = sorted(X['out'] - m12)
    assert len(rest) == 8 and all(any(no in c['stages'] and c['lane'] == 8 and not c['day'] for c in cards)
                                  or any(no in ch['scenes'] and ch['lane'] == 8 for ch in chips) for no in rest), rest
    counts['V1_cards'] = len(cards)
    counts['V1_stages'] = stage_i
    counts['V1_drawers'] = len(chips)
    counts['V1_scenes'] = scene_i
    counts['V1_events'] = len(ev)
    counts['V1_panel_outside'] = len(X['out'])


def geometry(d):
    title = ko(d['title'])
    lines = title.split('\n')
    cols = d['cols']
    rows = math.ceil(len(d['items']) / cols)
    return lines, rows, 64 + 34 * len(lines) + 48 * rows


WIDEST = dict(title='', item='', drawer='')


def units_w(t):
    """Glyph width in full-width units: ASCII (digits, spaces, /, parentheses, %) draws half width."""
    return sum(0.5 if ord(ch) < 0x80 else 1.0 for ch in t)


def bars_ok(text, counts):
    """Every bar printed anywhere = the r17 rule for the k/n next to it."""
    for z in BAR_RE.finditer(text):
        if z.group(1):
            b, k, n = z.group(1), int(z.group(2)), int(z.group(3))
        else:
            k, n, b = int(z.group(4)), int(z.group(5)), z.group(6)
        assert b == bar(k, n, len(b)), ('bar does not follow the r17 rule', b, k, n, text[:60])
        counts['V2_bars_checked'] += 1


def check_dialog(d, counts):
    """C_SelectDialog@CreateParts: title width = longest line's character count (marks included) x size + spacing + 48;
    column width = max(widest item + 52, title width / columns); the dialog is columns x column width + 4 wide."""
    lines, rows, h = geometry(d)
    for x in lines + [ko(t) for _, t, _, _ in d['items']]:
        assert not re.search(r'[0-9A-Za-z]…', x), ('a number or event id cut by 「…」', x)
        assert '★' not in x and '☆' not in x, ('★ ☆ left (r17 removed the main-story day mark)', x)
        assert '(본 것 ' not in x, ('old drawer-row form 「(본 것 n)」 left', x)
        bars_ok(x, counts)
    for x in lines:
        assert len(x) <= 38, ('title line over 38', len(x), x)
        if len(x) > len(WIDEST['title']):
            WIDEST['title'] = x
    if d.get('top') is not None:
        assert d['top'] >= PANEL_ROW_BOTTOM and d['top'] + h <= 720 - 8, ('lowered dialog does not fit', d['top'], h, lines[0])
    else:
        assert h <= H_MAX, ('dialog too tall', h, len(lines), rows, lines[0])
    cap = COL_CAP[d['cols']]
    widest = 0
    for (iid, text, help_, off) in d['items']:
        t = ko(text)
        assert len(t) <= 38 and units_w(t) <= cap, ('item too wide for its column', d['cols'], units_w(t), t)
        assert not any(mk in t for mk in MARKS), ('colour mark in an item', t)
        widest = max(widest, units_w(t))
        if units_w(t) > units_w(WIDEST['item']):
            WIDEST['item'] = t
    width = max(d['cols'] * (widest * 28 + 52), max(len(x) for x in lines) * 28.5 + 48) + 4
    assert width <= 1280, ('dialog wider than the screen', width, lines[0])
    counts['V2_max_width_px'] = max(counts['V2_max_width_px'], int(width))
    assert d['type'] == 2026091602 and d['limit'] == 'all', 'dialog style'
    assert d['opt_color'] == '1' and d['opt_title'] == d['title'], 'r11 colour opt-in not set for the draw'
    counts['V2_dialogs'] += 1
    counts['V2_max_height'] = max(counts['V2_max_height'], h)
    counts['V2_max_title_lines'] = max(counts['V2_max_title_lines'], len(lines))


def lane_title_expect(X, regs, mo, lane, page, pages):
    nc = sum(1 for c in X['cards'] if c['month'] == mo and c['lane'] == lane)
    ns = sum(len(ch['scenes']) for ch in X['chips'] if ch['month'] == mo and ch['lane'] == lane)
    k, n = units(X, regs, mo, lane)
    tag = ('　〓%d/%d쪽' % (page + 1, pages)) if pages > 1 else ''
    return ('〓%s · %s　†카드 %d · 서랍 %d%s\n%s %d/%d 본 것　%s' % (month_name(mo), LANE_KR[lane], nc, ns, tag, bar(k, n, 10), k, n, LANE_LEGEND))


def drawer_row_check(X, regs, got, ch, with_lane, counts):
    want = chip_row(X, regs, ch, with_lane)
    assert got == want, ('drawer row', ch['id'], got, want)
    counts['V11_drawer_rows'] += 1
    if len(got) > len(WIDEST['drawer']):
        WIDEST['drawer'] = got


def pages_all(vm, X, counts, state_name):
    """Every page once (lane/drawer/stage/month-drawer pages through all their sub-pages) + summary + 회상 · 그 밖."""
    cards, chips = X['cards'], X['chips']
    regs = vm.registered

    def walk(fn, args, pages):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'P'
        vm.script = [12] * (pages - 1) + [0]
        vm.run(fn, args)
        for d in vm.dialogs:
            check_dialog(d, counts)
        assert not vm.script, (fn, args, 'page count differs', len(vm.script))
        return vm.dialogs

    for mo in range(4, 12):
        for lane in range(9):
            lane_cards = [c for c in cards if c['month'] == mo and c['lane'] == lane]
            lane_chips = [ch for ch in chips if ch['month'] == mo and ch['lane'] == lane]
            nc, nd = len(lane_cards), len(lane_chips)
            if nc + nd:
                n = nc + nd
                per = 10 if n <= 10 else 8
                pages = math.ceil(n / per)
                ds = walk('KR_T9LanePage', [mo, lane], pages)
                assert sum(len(d['items']) - (3 if n > 10 else 1) for d in ds) == n, (mo, lane)
                for p, d in enumerate(ds):
                    assert ko(d['title']) == lane_title_expect(X, regs, mo, lane, p, pages), (mo, lane, ko(d['title']))
                    for iid, text, _, _ in d['items']:
                        if iid >= 100 + nc:
                            drawer_row_check(X, regs, ko(text), lane_chips[iid - 100 - nc], False, counts)
                counts['V11_lane_titles'] += len(ds)
        mchips = [ch for ch in chips if ch['month'] == mo]
        n = len(mchips)
        per = 10 if n <= 10 else 8
        pages = max(1, math.ceil(n / per))
        ds = walk('KR_T9MonthChips', [mo], pages)
        dk, dn = drawer_units(X, regs, mo)
        for p, d in enumerate(ds):
            tag = ('　〓%d/%d쪽' % (p + 1, pages)) if pages > 1 else ''
            want = '〓%s · 이달의 서랍　†장면 %d · 본 것 %d\n†서랍을 고르면 장면 목록이 나옵니다%s' % (month_name(mo), dn, dk, tag)
            assert ko(d['title']) == want, ('이달의 서랍 title', mo, ko(d['title']), want)
            for iid, text, _, _ in d['items']:
                if iid >= 100:
                    drawer_row_check(X, regs, ko(text), mchips[iid - 100], True, counts)
        counts['V11_month_drawer_pages'] += len(ds)
    for k, c in enumerate(cards):
        walk('KR_T9CardPage', [k, c['month']], 1)
        if c['size'] > 1:
            walk('KR_T9StagePage', [k, c['month']], math.ceil(c['size'] / 30))
    for i, ch in enumerate(chips):
        walk('KR_T9ChipPage', [i], math.ceil(len(ch['scenes']) / 30))
    mem_check(vm, X, counts)
    vm.reset()
    vm.script = [0]
    vm.run('KR_T18SummaryPage')
    for d in vm.dialogs:
        check_dialog(d, counts)
    assert vm.dialogs[0]['top'] == SUMMARY_TOP, ('summary page not lowered below the panel', vm.dialogs[0]['top'])
    summary_check(vm, ko(vm.dialogs[0]['title']), X, regs, counts)
    assert [(i, ko(t)) for i, t, _, _ in vm.dialogs[0]['items']] == [(0, '돌아가기')]
    counts['V2_states'] += 1


def mem_check(vm, X, counts):
    regs = vm.registered
    vm.reset()
    vm.script = [0]
    vm.run('KR_T9MemPage')
    for d in vm.dialogs:
        check_dialog(d, counts)
    d = vm.dialogs[0]
    k, n = units(X, regs, 12)
    assert n == 113, n
    want = [MEM_HEAD, '%s %d/%d %s' % (bar(k, n, 10), k, n, pct(k, n)), MEM_NOTE]
    assert ko(d['title']).split('\n') == want, ('회상 · 그 밖 title', ko(d['title']).split('\n'), want)
    mchips = [ch for ch in X['chips'] if ch['month'] == 12]
    items = [(iid, ko(t)) for iid, t, _, _ in d['items']]
    assert [i for i, _ in items] == [100 + j for j in range(len(mchips))] + [11, 0], items
    for iid, t in items[:len(mchips)]:
        drawer_row_check(X, regs, t, mchips[iid - 100], False, counts)
    assert items[-2:] == [(11, '← 11월'), (0, '돌아가기')]
    counts['V11_memory_pages'] += 1


def panel_value(vm):
    """The r9 panel's 「전체」 value for the VM's registrations, computed by the panel's own functions."""
    pk = sum(vm.run('KR_PlayerEventCount', [g]) for g in range(4))
    return pk, vm.run('KR_T8Pct', [pk, PANEL_EVENTS])


def summary_expect(X, regs):
    lines = []
    tk = tn = 0
    months = []
    for m in (4, 6, 8, 10):
        k1, n1 = units(X, regs, m)
        k2, n2 = units(X, regs, m + 1)
        months += [(k1, n1), (k2, n2)]
        tk += k1 + k2
        tn += n1 + n2
        lines.append('†%s %s %d/%d　　%s %s %d/%d' % (month_name(m), bar(k1, n1, 5), k1, n1, month_name(m + 1), bar(k2, n2, 5), k2, n2))
    lanes = []
    for l in range(0, 9, 2):
        cells = []
        for ll in (l, l + 1):
            if ll > 8:
                continue
            kk = nn = 0
            for m in range(4, 12):
                a, b = units(X, regs, m, ll)
                kk += a
                nn += b
            lanes.append((kk, nn))
            cells.append('%s %s %d/%d' % (LANE_KR[ll], bar(kk, nn, 5), kk, nn))
        lines.append('†' + '　　'.join(cells))
    ok = sum(1 for no in X['out'] if seen_fn(X, regs, no))
    lines.append(OUT_LINE % (ok, len(X['out'])))
    head = '〓달성도　전체 %s %d/%d (%s)' % (bar(tk, tn, 10), tk, tn, t8pct(tk, tn))
    return [head] + lines, tk, tn, months, lanes, ok


def summary_check(vm, title, X, regs, counts, native_panel=None):
    want, tk, tn, months, lanes, ok = summary_expect(X, regs)
    got = title.split('\n')
    assert got == want, ('summary page', [(a, b) for a, b in zip(got, want) if a != b][:3], len(got), len(want))
    assert tn == PANEL_EVENTS, ('summary total is not the panel 1,043', tn)
    assert len(got) == 11 and len(months) == 8 and len(lanes) == 9
    nums = [tuple(map(int, z)) for z in re.findall(r'(\d+)/(\d+)', '\n'.join(got[1:10]))]
    assert nums == months + lanes, 'summary numbers differ from the model'
    assert sum(b for _, b in months) == sum(b for _, b in lanes) == PANEL_EVENTS, 'months / lanes do not add up to 1,043'
    assert sum(a for a, _ in months) == sum(a for a, _ in lanes) == tk, 'months / lanes seen do not add up to the first line'
    all_seen = sum(1 for no in X['ev'] if seen_fn(X, regs, no))
    assert tk + ok == all_seen, ('panel set + outside != every registered calendar event', tk, ok, all_seen)
    # the first line = the home panel (r9 KR_T8, canonical), computed by the panel's own functions in the VM
    saved = vm.registered
    vm.registered = regs
    pk, ptext = panel_value(vm)
    vm.registered = saved
    head = re.fullmatch(r'〓달성도　전체 [■□]{10} (\d+)/(\d+) \((.+)\)', got[0])
    assert head and int(head.group(1)) == pk and int(head.group(2)) == PANEL_EVENTS and head.group(3) == ko(ptext) == t8pct(pk, PANEL_EVENTS), \
        ('summary first line != panel', got[0], pk, ko(ptext))
    if native_panel is not None:
        assert head.group(3) == native_panel, ('summary first line != the natively logged panel value', got[0], native_panel)
    counts['V11_summary_pages'] += 1
    counts['V13_summary_equals_panel'] += 1
    return tk, tn, pk, ko(ptext)


def event_pages(vm, X, counts):
    for no in sorted(X['ev']):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'C'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, proxy('6월 · 호시카와 · 특훈 뒤 대화')])
        check_dialog(vm.dialogs[0], counts)
    counts['V2_event_pages'] = len(X['ev'])


def calendar_cells(title):
    """(line segments with colours) -> {day: (colour, mark)} for the week lines of a month title (after 3 header lines)."""
    rows = title.split('\n')[3:]
    out = {}
    for row_ in rows:
        color = 0
        chars = []
        for ch in row_:
            if ch in MARKS:
                color = {'†': 1, '‡': 2, '¶': 3, '〓': 0}[ch]
                continue
            chars.append((ch, color))
        for i in range(0, len(chars), 4):
            cell = chars[i:i + 3]
            digits = ''.join(c for c, _ in cell[:2]).replace('　', '')
            if not digits:
                continue
            day = int(''.join(str('０１２３４５６７８９'.index(c)) for c in digits))
            out[day] = (cell[1][1], cell[2][0] if len(cell) > 2 else '　')
            assert cell[0][1] == cell[1][1] == (cell[2][1] if len(cell) > 2 else cell[1][1]), ('one day in two colours', day)
    return out


def month_page_check(vm, X, mo, counts, regs, today):
    """One month page: cells, head, legend, weekday line, menu rows, columns, sums. Returns the marks shown."""
    vm.registered = regs
    vm.today = today
    vm.reset()
    vm.script = [0]
    r = vm.run('KR_T9MonthPage', [mo])
    assert r == 0
    d = vm.dialogs[0]
    check_dialog(d, counts)
    title = ko(d['title'])
    lines = title.split('\n')
    k, n = units(X, regs, mo)
    assert lines[0] == '〓%d월 이벤트 달력　%s %d/%d %s' % (mo, bar(k, n, 10), k, n, pct(k, n)), lines[0]
    assert lines[1] == LEGEND17 and lines[2] == WEEKDAYS, lines[1:3]
    cells = calendar_cells(title)
    assert sorted(cells) == list(range(1, X['mlen'][mo] + 1)), (mo, sorted(cells)[:5])
    shown = collections.Counter()
    for day, got in cells.items():
        want = want_cell(X, regs, mo, day, today)
        assert got == want, (mo, day, today, got, want)
        shown[got[1]] += 1
    counts['V3_cells'] += len(cells)
    cols = month_cols(X, mo)
    assert d['cols'] == cols, (mo, d['cols'], cols)
    items = {iid: ko(t) for iid, t, _, _ in d['items']}
    off = {iid: o for iid, _, _, o in d['items']}
    lane_sum = 0
    for lane in range(9):
        if has_list(X, mo, lane):
            a, b = units(X, regs, mo, lane)
            assert items.get(20 + lane) == row(LANE_KR[lane], a, b), (mo, lane, items.get(20 + lane))
            lane_sum += b
        else:
            assert 20 + lane not in items, (mo, lane)
    assert lane_sum == n, ('month menu rows do not add up to the title', mo, lane_sum, n)
    dk, dn = drawer_units(X, regs, mo)
    assert items.get(30) == row('서랍' if cols == 3 else '이달의 서랍', dk, dn), items.get(30)
    assert off[30] == int(not any(ch['month'] == mo and ch['scenes'] for ch in X['chips']))
    assert (11 in items) == (mo > 4) and 12 in items and 0 in items and items.get(31) == '달성도 보기'
    assert [iid for iid, _, _, _ in d['items']][-2:] == [31, 0], '달성도 보기 must sit right above 돌아가기'
    counts['V3_month_menus'] += 1
    return shown, n


def calendar_checks(vm, X, counts, regs_list):
    for regs in regs_list:
        for today in [(4, 9), (6, 13), (9, 30), (11, 17)]:
            total = 0
            for mo in range(4, 12):
                _, n = month_page_check(vm, X, mo, counts, regs, today)
                total += n
            assert total == PANEL_EVENTS, ('eight months != the panel 1,043', total)
            counts['V11_year_sums'] += 1


def synthetic_mid_month(X, month=8, day=15):
    """A played-in-order state for 8/15: everything dated before today is seen except the cards of one earlier day
    without a main-story card, nothing later -> ▲ ● ○ all appear (as r16)."""
    free = sorted({c['day'] for c in X['cards'] if c['month'] == month and c['day'] and c['day'] < day}
                  - {c['day'] for c in X['cards'] if c['month'] == month and c['lane'] == 0})
    skip = free[0]
    regs = set()
    for c in X['cards']:
        if (c['month'], c['day'] or 1) < (month, day) and not (c['month'] == month and c['day'] == skip):
            regs |= {X['ev'][s]['fn'] for s in c['stages']}
    return regs, (month, day)


def all_but_one(X):
    """Everything registered except one June main-story card stage: bars at k = n - 1 (the 「never full before complete」
    cells: June 231/232, 본편 lane, 전체 1042/1043)."""
    c = next(c for c in X['cards'] if c['month'] == 6 and c['lane'] == 0)
    miss = c['stages'][0]
    return {e['fn'] for no, e in X['ev'].items() if no != miss}


def nav_checks(vm, X, counts):
    vm.reset()
    vm.script = [12] * 8 + [11, 11, 0]
    vm.run('KR_T9Calendar', [4, -1])
    heads = [ko(d['title']).split('\n')[0].translate({ord(c): None for c in MARKS}) for d in vm.dialogs]
    want = ['%d월 이벤트 달력' % mo for mo in range(4, 12)] + ['회상 · 그 밖 (패널 밖)', '11월 이벤트 달력', '10월 이벤트 달력']
    assert [h.split('　')[0] for h in heads] == want, heads
    assert not vm.script
    counts['V4_navigation'] += 1


def home_menu(vm):
    vm.native('■選択ダイアログ／タイトル設定', [proxy('●본거지')])
    for i in (11, 12, 14):
        vm.native('■選択ダイアログ／選択肢追加', [i, proxy('메뉴'), '', 0])


def home_run(vm):
    home_menu(vm)
    r = vm.run('KR_T9HomeMenuRun', [1, 200])
    assert vm.cur is None, 'the home menu dialog was left behind'
    return r


def first_card(X, month, lane):
    ks = [k for k, c in enumerate(X['cards']) if c['month'] == month and c['lane'] == lane]
    return ks[0], X['cards'][ks[0]]


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


def seen_checks(vm, X, counts):
    ev = X['ev']
    withmsg = [no for no, e in sorted(ev.items()) if e['m0'] is not None]
    nomsg = [no for no, e in sorted(ev.items()) if e['m0'] is None]
    vm.reset()
    vm.getflag_neg = 0
    a, b, c = withmsg[0], withmsg[1], withmsg[2]
    vm.registered = {ev[a]['fn']}
    vm.flags = {ev[b]['m0']}
    assert [vm.run('KR_T9State', [x]) for x in (a, b, c)] == [2, 1, 0]
    assert [ko(vm.run('KR_T9Mark', [s])) for s in (2, 1, 0)] == ['○', '△', '●']
    vm.flags = set(ev[x]['m0'] for x in withmsg)
    for no in nomsg:
        assert vm.run('KR_T9State', [no]) == 0
    assert vm.getflag_neg == 0, 'MsgSkip.GetFlag called with -1'
    rnd = random.Random(20260927)
    regs = {e['fn'] for no, e in ev.items() if rnd.random() < 0.5}
    vm.registered = regs
    for i, ch in enumerate(X['chips']):
        assert vm.run('KR_T9ChipSeen', [i]) == sum(1 for s in ch['scenes'] if ev[s]['fn'] in regs), ch['id']
        x = vm.run('KR_T18ChipCount', [i, ch['month']])
        assert (x % 10000, x // 10000) == tally(X, regs, ch['month'], ch['scenes']), ch['id']
    for k, cd in enumerate(X['cards']):
        assert vm.run('KR_T9CardSeenStages', [k]) == sum(1 for s in cd['stages'] if ev[s]['fn'] in regs), cd['key']
        x = vm.run('KR_T18CardCount', [k])
        assert (x % 10000, x // 10000) == tally(X, regs, cd['month'], cd['stages']), cd['key']
    counts['V10_seen_states'] += 1
    vm.flags = set()
    return regs


def row_checks(vm, X, counts):
    """V12: tails exactly where r15's rows collided; rows unique in (month, lane); untouched rows equal r15's."""
    cards = X['cards']
    vm.registered = set()
    rows = collections.defaultdict(list)
    r15rows = collections.defaultdict(list)
    tails = []
    for k, c in enumerate(cards):
        t = ko(vm.run('KR_T9CardRow', [k, c['month']]))
        when = ko(vm.run('KR_T9CardWhen', [k, c['month']]))
        cond = ko(vm.run('KR_T9CardCond', [k]))
        old = when + ' ●' + ((' ' + cond) if cond else '') + ((' (%d단계)' % c['size']) if c['size'] > 1 else '')
        tail = ' E%05d' % c['entry']
        assert len(t) <= 38, t
        if vm.run('KR_T18CardTail', [k]):
            assert t.endswith(tail), t
            tails.append(k)
            body = t[:-len(tail)]
            assert body == old or (body.endswith(' …') and old.startswith(body[:-2])) or re.sub(r' \(\d+단계\)$', '', body).endswith(' …'), (body, old)
        else:
            assert t == old, (t, old)
        rows[(c['month'], c['lane'])].append(t.replace(' ● ', ' ').replace(' ●', ''))
        r15rows[(c['month'], c['lane'])].append((k, old))
    dup = {key: [x for x, n in collections.Counter(v).items() if n > 1] for key, v in rows.items()}
    dup = {key: v for key, v in dup.items() if v}
    assert not dup, ('lane rows collide', dup)
    want = []
    for key, v in r15rows.items():
        cnt = collections.Counter(o for _, o in v)
        want += [k for k, o in v if cnt[o] > 1]
    assert sorted(tails) == sorted(want), ('tails not exactly on the colliding rows', sorted(set(tails) ^ set(want)))
    counts['V12_tailed_rows'] = len(tails)
    counts['V12_collision_groups_in_r15'] = sum(1 for v in r15rows.values() for o, n in collections.Counter(o for _, o in v).items() if n > 1)
    counts['V12_duplicate_rows_after'] = 0
    counts['V12_rows'] = len(cards)


def bar_checks(vm, counts):
    """V15: the jaf bar against the model for every 0 <= k <= n <= 120, and the rule itself on the model."""
    for cells in (5, 10):
        for n in range(0, 121):
            for k in range(0, n + 1):
                got = vm.run('KR_T18Bar', [k, n, cells])
                assert got == bar(k, n, cells), ('KR_T18Bar', k, n, cells, got)
                counts['V15_bars'] += 1
    # the rule, stated independently of both implementations
    assert bar(1, 10, 5) == '■□□□□' and bar(9, 100, 5) == '□□□□□' and bar(10, 100, 5) == '■□□□□'   # 5칸: 10% 부터 한 칸
    assert bar(1, 20, 10) == '■□□□□□□□□□' and bar(9, 10, 5) == '■■■■□' and bar(10, 10, 5) == '■■■■■'
    assert bar(19, 20, 10) == '■■■■■■■■■□' and bar(1042, 1043, 10) == '■■■■■■■■■□' and bar(0, 0, 5) == '□□□□□'
    assert bar(3, 20, 5) == '■□□□□' and bar(1, 20, 5) == '□□□□□'                                     # .75 -> 1, .25 -> 0
    for cells in (5, 10):
        for n in range(1, 121):
            for k in range(n):
                assert bar(k, n, cells).count('■') <= cells - 1


def panel_checks(vm, X, counts, states):
    """V13: the home achievement panel (r9 KR_T8, the canonical one) against the calendar summary's first line."""
    texts = {}
    for n in ('KR_T8HomeRateText', 'KR_RateText'):
        p = vm.dir / f'panel_{n}.jam'
        if not p.exists():
            L.cmd('ain', 'dump', '--function', n, '-o', p, vm.ain)
        texts[n] = [l.strip() for l in p.read_text('utf8').splitlines() if l.strip() and not l.startswith(';')]
    a, b = texts['KR_T8HomeRateText'], texts['KR_RateText']
    diff = [(x, y) for x, y in zip(a, b) if x != y and not (x.startswith('FUNC') and y.startswith('FUNC')) and not (x.startswith('ENDFUNC') and y.startswith('ENDFUNC'))
            and not re.match(r'^0x[0-9a-f]+:$', x) and not re.match(r'^(IFNZ|IFZ|JUMP) 0x', x)]
    assert len(a) == len(b) and len(diff) == 1 and all(x.startswith('S_PUSH') for x in diff[0]), ('KR_RateText differs beyond one label', diff[:3])
    label = (ko(json.loads(diff[0][0].split(' ', 1)[1])), ko(json.loads(diff[0][1].split(' ', 1)[1])))
    for t in (a, b):
        i = t.index('PUSH 1043')
        assert t[i - 1] == '.LOCALREF ev' and t[i + 1] == 'CALLFUNC KR_T8Pct', 'the panel 전체 line is not KR_T8Pct(ev, 1043)'
        assert sum(1 for x in t if x == 'CALLFUNC KR_PlayerEventCount') == 4
    path = vm.dir / 'panel_KR_PlayerEventCount.jam'
    if not path.exists():
        L.cmd('ain', 'dump', '--function', 'KR_PlayerEventCount', '-o', path, vm.ain)
    cand_groups = parse_panel_groups(path)
    assert cand_groups == X['panel_groups'], 'candidate KR_PlayerEventCount differs from the base'
    rows = []
    for name, regs in states:
        vm.registered = regs
        vm.reset()
        vm.script = [0]
        vm.run('KR_T18SummaryPage')
        tk, tn, pk, ptext = summary_check(vm, ko(vm.dialogs[0]['title']), X, regs, collections.Counter())
        rows.append(dict(state=name, panel='%d/1043 %s' % (pk, ptext), summary_first_line=ko(vm.dialogs[0]['title']).split('\n')[0].lstrip('〓')))
    counts['V13_panel_states'] = len(rows)
    out_where = collections.Counter()
    for no in X['out']:
        ch = next((ch for ch in X['chips'] if no in ch['scenes']), None)
        if ch and ch['month'] == 12:
            out_where['회상 재생본' if ch['lane'] < 16 else '게임에서 부르지 않는 장면'] += 1
        else:
            out_where['던전 레인'] += 1
    return dict(same_computation_as_KR_T8HomeRateText=True, only_difference_label=label, panel_denominator=PANEL_EVENTS,
                panel_percent='KR_T8Pct (0.1% floored)', calendar_events=TOTAL_EVENTS, panel_outside=len(X['out']),
                panel_outside_breakdown=dict(out_where),
                dungeon_lane_outside=['E%05d' % no for no in sorted(X['out']) if not any(no in ch['scenes'] and ch['month'] == 12 for ch in X['chips'])],
                states=rows)


def native_panel_value(text):
    """「전체」 value from a natively logged KR_RateText (the home panel text)."""
    for line in text.split('\n'):
        z = re.match(r'^전체\s+(.*)$', line)
        if z:
            v = re.sub(r'[†‡¶〓]', '', z.group(1)).strip()
            m = re.search(r'(\d+\.\d%)', v)
            return m.group(1) if m else v
    raise AssertionError(('no 전체 line in the panel text', text[:200]))


def real_save_checks(vm, X, counts):
    """V14: month pages and the summary of the real save states the probe logged (증거/probe_regs.json)."""
    path = L.EVID / 'probe_regs.json'
    assert path.exists(), 'run probe_calendar_r17.py --regs first (real save states)'
    doc = L.readj(path)
    man = L.readj(O / 'manifest.json')
    rows = []
    for r in doc['saves']:
        if not r.get('state'):
            continue
        assert r['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256'], 'regs logged by another candidate'
        st = r['state']
        byno = {e: X['ev'][e]['fn'] for e in st['regs']}
        regs = set(byno.values())
        today = tuple(st['today'])
        months = {}
        for mo in range(4, 12):
            shown, _ = month_page_check(vm, X, mo, counts, regs, today)
            months[mo] = ''.join(sorted(k for k in shown if k != '　'))
        vm.registered = regs
        vm.reset()
        vm.script = [0]
        vm.run('KR_T18SummaryPage')
        vm_title = ko(vm.dialogs[0]['title'])
        npanel = native_panel_value(st['panel']) if st.get('panel') else None
        tk, tn, pk, ptext = summary_check(vm, vm_title, X, regs, counts, native_panel=npanel)
        native = dict(panel_value=npanel, panel_count=st.get('panel_count'), summary_equal_vm=None)
        if st.get('summary') is not None:
            assert st['summary'] == vm_title, ('native summary title differs from the VM', r['save'],
                                               [(a, b) for a, b in zip(st['summary'].split('\n'), vm_title.split('\n')) if a != b][:2])
            native['summary_equal_vm'] = True
        if st.get('panel_count') is not None:
            assert st['panel_count'] == pk == tk, ('native Σ KR_PlayerEventCount differs', r['save'], st['panel_count'], pk, tk)
        now = st['now']
        full = [mo for mo, s in months.items() if all(ch in s for ch in '▲●○')]
        rows.append(dict(save=r['save'], at=st.get('at', 'home'), today='%d/%d' % today, now=now, registered=len(regs),
                         marks_by_month=months, months_with_all_three=full, current_month_has_all_three=now in full,
                         summary_first_line=vm_title.split('\n')[0].lstrip('〓'), panel='%d/1043 %s' % (pk, ptext), native=native))
        counts['V14_saves'] += 1
        counts['V14_native_panel_equal'] += int(npanel is not None)
        counts['V14_native_summary_equal'] += int(native['summary_equal_vm'] is True)
    assert rows, 'no real save state'
    good = [x for x in rows if x['current_month_has_all_three'] and x['at'] == 'home']
    assert good, ('no home save shows ▲ ● ○ together on its own month page', [(x['save'], x['today'], x['marks_by_month'].get(x['now'])) for x in rows])
    mid = [x for x in good if 8 <= int(x['today'].split('/')[1]) <= 23] or good
    pick = sorted(mid, key=lambda x: x['save'])[-1]
    L.writej(L.WORK / 'probe_pick.json', dict(save=pick['save'], today=pick['today'], month=pick['now'],
                                              why='newest home save whose own month page shows ▲ ● ○ together (VM on its real registrations)'))
    counts['V14_saves_with_all_three'] = len(good)
    return dict(saves=rows, pick=pick['save'])


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
