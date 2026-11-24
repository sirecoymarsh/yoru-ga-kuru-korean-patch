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


