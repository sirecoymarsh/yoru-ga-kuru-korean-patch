"""Claude Opus 5.5 (2026-09-28) r24: verification of the chart touch-up candidate (설계_v4 「r24 요구」) without the game (after
verify_feeling_r23.py; every r20 / r21 / r22 / r23 check still runs on the r24 candidate, the r22 chart checks with r24's cells).

  python verify_chart_r24.py              all checks (must pass)
  python verify_chart_r24.py --selftest   all checks, then every check again against a planted defect (each must fail): 56
  python verify_chart_r24.py --native     compare what the native probes logged (증거/probe_result.json: the calendar tour;
                                          증거/probe_regs.json: 14 real saves; 증거/probe_chart_r24.json: the chart tours with the
                                          r24 steps; 증거/replay_kinds.json: the per-kind replays on this candidate) with the VM
  python verify_chart_r24.py --r24-only   (development) the static checks and the chart checks only

Base = the r23 install (= the r23 candidate) + the mod-menu hook r2. r24 = KR_C24* functions and six one-call forwarders of r22
chart functions (index, arguments and return kept, the body a call at a new address): KR_CChart -> KR_C24Chart, KR_CDraw ->
KR_C24Draw, KR_CWait -> KR_C24Wait, KR_CClick -> KR_C24Click, KR_CStateLine -> KR_C24StateLine, KR_CPlayNote -> KR_C24PlayNote.
No same-length swap; the
old CODE is byte-identical. Static checks S1-S8 (r24 versions), the r20 / r21 / r22 / r23 VM checks V1-V54 (the r22 page checks
V42 / V43 now expect r24's cells: a locked cell shows its texts in grey and an empty frame for a thumbnail, and the two buttons)
and r24:
  V55 all 915 cells locked (no global record, 전체 개방 off) vs open (전체 개방 on): the same name / 「● E번호 · 언제」 / condition
      texts at the same places once the colour tags are off (= the r22 tables), locked = grey texts, grey box, an empty frame in
      the thumbnail slot (open = the CG), the same box size
  V56 the detail page of every cell, locked and open: = an independent model (r19 texts from the base, the state line, 단계 k/n,
      the play note) and locked = open minus 이 장면 재생 (the state line 「● 안 읽은 장면 · 전체 개방하면 재생됩니다」; a
      not-playable scene keeps 「재생 불가(게임 안에서만)」); a locked card's stage list still replays a read stage only
  V57 the two buttons (and the U / R keys): 「전체 개방」 / 「다시 가리기」 write YoruKR_Chart.dat 1 / 0 (the menu bar's file and
      format), the chart is drawn again at once on the same tab and page (the snapshot at the next wait = a fresh draw of that
      page in the new state), no part left after the chart; a failed write says so and keeps what the disk holds; a key already
      down when the page is drawn does nothing
  V58 (the user's 14:00 addition) a replay started from the chart ends back in the chart: the same tab and page, the played
      cell's border gold, the parts = a fresh draw of that page after the replay, no chart part during the replay, a second
      replay comes back again, a stage from a card's list marks the card, only 닫기 / cancel leave (title and home)
"""
import sys, json, re, struct, collections, math, copy, time, random, datetime, io, contextlib, bisect
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r24lib as L

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
FORWARD = {'KR_T18CardRow': 'KR_T19CardRow', 'KR_T18CardTitle': 'KR_T19CardTitle', 'KR_T18EventTitle': 'KR_T19EventTitle',
           'KR_T9StagePage': 'KR_T19StagePage', 'KR_T9ChipPage': 'KR_T19ChipPage'}          # r19 forwarders (in the base since r19)
R18_FORWARD = {'KR_T9MonthPage': 'KR_T18MonthPage', 'KR_T9MemPage': 'KR_T18MemPage', 'KR_T9LaneTitle': 'KR_T18LaneTitle',
               'KR_T9CardRow': 'KR_T18CardRow', 'KR_T9ChipRow': 'KR_T18ChipRow', 'KR_T9MonthChips': 'KR_T18MonthChips',
               'KR_T9CardPage': 'KR_T18CardPage', 'KR_T9EventPage': 'KR_T18EventPage'}      # in the base since r18
R22_FORWARD = {'KR_MDo': 'KR_CDoHome', 'KR_T9Seen': 'KR_CSeen', 'KR_T9State': 'KR_CState', 'KR_T9Legend': 'KR_CLegend',
               'KR_T18CardPage': 'KR_CCardPage', 'KR_T18EventPage': 'KR_CEventPage'}        # new in r22
R22_OWNERS = {'C_SceneTitle@Update': ('C_UserInputManager::IsClickConfig', 'KR_CTitleTick'),
              'C_SceneTitle@Run': ('■方向キー処理／削除', 'KR_CTitleServe')}
E_RE = re.compile(r'E\d{4,5}')
WHEN_CONT = '\n†　　　'
PARTY_KR = ['이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세']
NAME_KIND = {'prio': '우선 대화', 'after': '특훈 뒤 대화', 'turned': '반한 뒤 대화', 'invite': '초대'}
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
HOVER_A, HOVER_B = 3, 8               # the two portraits the probe hovers on the partner screen (probe_calendar_r20.HOVER)
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
        # r24 model: the keys the chart's U / R read (AFL_IsKeyDown: virtual key -> down)
        self.keys = {}

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
                elif op == 'VM_JUMP0':                      # planted defects only (r24): start the function over (no return)
                    pc = 0
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
            d['chart_root_show'] = self.parts.get(VM.CHART_ROOT, {}).get('show')      # r24: is the chart hidden behind this window?
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
        if name == 'KR_C24WaitRaw':                   # r24: the chart's live wait (KR_CWait forwards to KR_C24Wait, which calls it)
            return self.chart_wait()
        if name == 'AFL_IsKeyDown':                   # r24: the U / R keys (IbisInputEngine.Key_IsDown in the game)
            self.calls.append(('key', aa[0]))
            return int(bool(self.keys.get(aa[0], 0)))
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
        """KR_C24WaitRaw (r24; r22 KR_CWait's body with the KR_C24Frame delegate): the chart's AFL_Parts_WaitForClick (key cancel).
        The scripted answer is the number a click on a part gives (or 0 = right click / space, 1-4 = the arrow keys); a Wait object
        runs KR_C24Frame per frame. r24 also records the unlock flag file as the disk holds it at this wait."""
        d = dict(kind='chart', title=proxy('<chart>'), cols=0, items=[], parts=self.chart_snapshot(),
                 open=self.vars.get('YoruKR.C.Open', ''), all=self.vars.get('YoruKR.C.All', ''), ctx=self.vars.get('YoruKR.C.Ctx', ''),
                 armed=self.vars.get('YoruKR.M.Home', ''), tick='KR_C24Frame', flag=self.disk.get(CHART))
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
        L.cmd('ain', 'dump', '--function', 'KR_PlayerEventCount', '-o', path, L.base_paths()['ain'])
    groups = parse_panel_groups(path)
    return {n for v in groups.values() for n in v}, groups


def expectations():
    sys.path.insert(0, str(L.FLOW / 'chart'))
    import build_chart_v2 as V2
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data = V2.build(str(L.TMP / 'chart_v2_from_r20_verify.html'))
    ev = {int(k): v for k, v in data['ev'].items()}
    cards = []
    for c in data['cards']:
        pl = c['pl']
        cards.append(dict(key=c['key'], month=int(c['page']), lane=LANES.index(c['lane']), day=pl.get('d', 0), slot=pl.get('slot', 0) or 0,
                          size=c['n'], entry=c['entry'], stages=[r[0] for r in c['rows'] if r[6]], nm=c['nm'], tail=c['tail'],
                          rows=c['rows'], pl=pl))
    cards.sort(key=lambda x: (x['month'], x['lane'], x['day'] if x['day'] else 99, SLOT_RANK[x['slot']], x['key']))
    chips = []
    for ch in data['chips']:
        month = 12 if ch['page'] == 'mem' else int(ch['page'])
        lane = LANES.index(ch['lane']) if ch['lane'] in LANES else (8 + int(ch['lane'][3:]) if ch['lane'].startswith('mem') else 16)
        chips.append(dict(id=ch['id'], month=month, lane=lane, kind=KINDS.index(ch['kind']), scenes=[x[0] for x in ch['order'] if x[4]],
                          order=ch['order'], slots=ch.get('slots') or {}))
    pset, groups = base_panel_set()
    out = {no for no, e in ev.items() if e['fn'] not in pset}
    assert len(pset) == PANEL_EVENTS and pset <= {e['fn'] for e in ev.values()} and len(out) == TOTAL_EVENTS - PANEL_EVENTS
    sch = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    feel = {}
    for e in sch['events']:
        full, short = [], []
        for t in e['triggers']:
            if t.get('feeling_gate'):
                full += V2.feeling_tokens(t, data['persons'])
                short += V2.feeling_tokens(t, data['persons'], short=True)
        if full:
            feel[e['id']] = (full, short)
    return dict(data=data, ev=ev, cards=cards, chips=chips, w1={p['m']: p['w1'] for p in data['pages'] if p.get('m')}, mlen=V2.MLEN,
                out=out, panel_groups=groups, sch={e['id']: e for e in sch['events']}, feel=feel,
                labels=json.loads((L.FLOW / 'graph' / 'labels.json').read_text('utf8')),
                memory=json.loads((L.FLOW / 'graph' / 'memory.json').read_text('utf8')))


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
def r18_site():
    s = L.readj(L.R18 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(s) == 1 and s[0]['function'] == L.SWAP_OWNER and s[0]['original'] == L.SWAP_OLD and s[0]['replacement'] == L.SANDBOX, s
    return s[0]


def r20_sites(man=None):
    """r20's seven same-length sites (in the base since r20; r21 keeps their operands)."""
    sites = L.readj(L.R20 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(sites) == 7, len(sites)
    return sites


def r21_sites(man=None):
    """r21's two same-length sites (in the base since r21; r22 keeps their operands)."""
    sites = L.readj(L.R21 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(sites) == 2, len(sites)
    return sites


def r22_sites(man=None):
    """r22's two same-length sites (in the base since r22; r23 keeps their operands)."""
    sites = L.readj(L.R22 / 'candidate' / 'manifest.json')['same_length_sites']
    assert len(sites) == 2, len(sites)
    return sites


def r23_sites(man):
    sites = man['same_length_sites']
    assert len(sites) == 3, len(sites)
    return sites


R21_OWNERS = {'KR_T9HomeMenuRun': ('■選択ダイアログ／実行', 'KR_MHomeRun'),
              'C_SelectDialog@_Update': ('C_UserInputManager::IsClickEnterOtherMouse', 'KR_MTick')}
SAVE_CALL_PREFIXES = ('gamesave::', 'AFL_GameSave_', '■セーブ', 'Ｓ＿コンフィグ', 'Ａ＿タイトルに戻る', 'C_SceneSaveLoad', 'AFL_MemoryModeEvent_')
MEMORY_MODE = ['AFL_MemoryModeEvent_Begin', 'AFL_MemoryModeEvent_End', 'AFL_MemoryModeEvent_Cleanup']


def live_ops(nm, cv, name):
    v = L.live_version(nm, cv, L.fid_of(nm, name))
    return [op for _, op in v['ops'] if not op.startswith('ENDFUNC')]


def live_ops_at(nm, cv, name):
    v = L.live_version(nm, cv, L.fid_of(nm, name))
    return [(ad, op) for ad, op in v['ops'] if not op.startswith('ENDFUNC')]


def call_graph(nm, cv, roots, stop=()):
    """Every function reachable by CALLFUNC from `roots` in the candidate (names); `stop` functions are listed but not entered."""
    seen = set()
    todo = list(roots)
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        if n in stop:
            continue
        try:
            ops = live_ops(nm, cv, n)
        except (AssertionError, StopIteration):
            continue
        for op in ops:
            if op.startswith('CALLFUNC '):
                todo.append(L.raw_symbol(nm, int(op.split()[1], 16)))
    return seen


def live_ops_fid(nm, cv, fid):
    v = L.live_version(nm, cv, fid)
    return [op for _, op in v['ops'] if not op.startswith('ENDFUNC')]


def call_graph_ids(nm, cv, roots, stop=()):
    """Every function index reachable by CALLFUNC from `roots` (names); `stop` functions are listed but not entered."""
    seen = set()
    todo = [L.fid_of(nm, r) for r in roots]
    stop_ids = {L.fid_of(nm, x) for x in stop}
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        if f in stop_ids:
            continue
        try:
            ops = live_ops_fid(nm, cv, f)
        except (AssertionError, StopIteration):
            continue
        for op in ops:
            if op.startswith('CALLFUNC '):
                todo.append(int(op.split()[1], 16))
    return seen


def norm_jumps(ops_at, base):
    """Ops with jump / branch targets made relative to `base` (the same code at another address compares equal)."""
    out = []
    for ad, op in ops_at:
        z = re.match(r'(JUMP|IFZ|IFNZ) 0x([0-9a-fA-F]+)$', op)
        out.append('%s %+d' % (z.group(1), int(z.group(2), 16) - base) if z else op)
    return out


def replay_body_check(nm, cv):
    """KR_CReplayRun = C_SceneModeScene@ExecScene from AFL_MemoryModeEvent_Begin on (the game's recollection path, same
    locals 2-5), with the event name taken from LSys3xScript::GetLabelName(no) instead of the EX recollection table."""
    ex = live_ops_at(nm, cv, 'C_SceneModeScene@ExecScene')
    rr = live_ops_at(nm, cv, 'KR_CReplayRun')
    begin = 'CALLFUNC 0x%x' % L.fid_of(nm, 'AFL_MemoryModeEvent_Begin')
    i = [op for _, op in ex].index(begin)
    j = [op for _, op in rr].index(begin)
    # jump targets relative to the Begin call: both bodies go on the same way (Begin -> play / clean -> ... -> Cleanup -> RETURN)
    a2 = norm_jumps(ex[i:], ex[i][0])
    b2 = norm_jumps(rr[j:], rr[j][0])
    assert a2 == b2, ('KR_CReplayRun is not ExecScene\'s memory-mode path', [(x, y) for x, y in zip(a2, b2) if x != y][:4], len(a2), len(b2))
    pro = [op for _, op in rr[:j]]
    assert 'CALLFUNC 0x%x' % L.fid_of(nm, 'LSys3xScript::GetLabelName') in pro and not any('CheckEnabelScenario' in L.raw_symbol(nm, int(op.split()[1], 16))
                                                                                       for op in pro if op.startswith('CALLFUNC ')), pro
    ev = nm['functions'][L.fid_of(nm, 'C_SceneModeScene@ExecScene')]
    kr = nm['functions'][L.fid_of(nm, 'KR_CReplayRun')]
    assert [v['type'] for v in ev['variables']] == [v['type'] for v in kr['variables']], 'KR_CReplayRun locals differ from ExecScene'
    return len(a2)


R23_SITES = {'C_HomeStatusView@SetActivePage': ('C_HomeStatusView@IsShowFeelingPage', 'KR_T23FeelShow', 'CALLMETHOD target (PUSH operand)'),
             'C_FeelingView@1': ('C_FeelingView@DeleteMarks', 'KR_T23FvGone', 'CALLMETHOD target (PUSH operand)'),
             'KR_T20StActiveOf': ('KR_T20StDraw', 'KR_T23StDraw', 'CALLFUNC')}


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
    swap = r18_site()
    sb = L.fid_of(nm, L.SANDBOX)
    r20s = r20_sites()
    r21s = r21_sites()
    r22s = r22_sites()
    r23s = r23_sites(L.readj(L.R23 / 'candidate' / 'manifest.json'))        # in the base since r23
    cv = L.versions(W / 'candidate_raw_code.jam')
    if 'S1' in parts:
        fw = {L.fid_of(m, n) for n in R24_FORWARD}
        for f in m['functions']:
            g = nm['functions'][f['index']]
            if f['index'] in fw:
                assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, ('r24 forwarder entry', f['name'])
                assert g['address'] >= oldn, ('an r24 forwarder body is not in the appended code', f['name'])
                continue
            assert g == f, ('base function entry changed (r24 forwards five r22 chart functions and moves nothing else)', f['index'], f['name'])
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
        assert all(n.startswith('KR_C24') for n in man['added_functions']), 'added functions must all be KR_C24*'
        assert [L.raw_symbol(nm, i) for i in range(len(m['functions']), len(nm['functions']))] == sorted(man['added_functions'], key=man['added_functions'].get)
        assert sorted(man['forwarded_functions']) == sorted(R24_FORWARD) and not man['relocated_original_functions'] and not man['same_length_sites'], \
            'r24: the five r22 forwarders, nothing moved, no operand swap'
        assert not any(L.raw_symbol(nm, f['index']).startswith(('KR_T16', 'KR_T17')) for f in nm['functions']), 'r16/r17 names in the candidate'
        for old_, new_ in list(FORWARD.items()) + list(R18_FORWARD.items()) + list(R22_FORWARD.items()) + list(R24_FORWARD.items()):
            v = L.live_version(nm, cv, L.fid_of(nm, old_))
            assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
        for old_, new_ in R24_FORWARD.items():
            f = nm['functions'][L.fid_of(nm, old_)]
            t_ = nm['functions'][L.fid_of(nm, new_)]
            assert [a['type'] for a in f['arguments']] == [a['type'] for a in t_['arguments']] and f['return-type'] == t_['return-type'], ('r24 forwarder signature', old_)
            want = []
            for k, a in enumerate(f['arguments']):
                want += ['PUSHLOCALPAGE', 'PUSH 0x%x' % k, 'X_REF 0x1'] + (['A_REF'] if a['type'][0] == 12 else [])
            want += ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN']
            got = live_ops(nm, cv, old_)
            assert got == want, ('an r24 forwarder body is not one call passing its arguments', old_, got)
        counts['S1_metadata'] += 1
        counts['S1_base_entries_identical'] = len(m['functions']) - len(fw)
        counts['S1_r24_forwarders'] = len(fw)
        counts['S1_forwarders_kept'] = len(FORWARD) + len(R18_FORWARD) + len(R22_FORWARD)
    if 'S2' in parts:
        diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
        assert not diff, ('base CODE bytes changed (r24 changes nothing in place)', [hex(x) for x in diff][:8])
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s_ in rman['same_length_sites'] + [swap] + r20s + r21s + r22s + r23s:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap missing in the base', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap site no longer applied', s_['function'], s_['replacement'])
        assert bytes(new[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, sb), 'KR_T9HomeCasual no longer calls KR_T18RunSandboxed'
        counts['S2_earlier_same_length_sites_kept'] = len(rman['same_length_sites']) + 1 + len(r20s) + len(r21s) + len(r22s) + len(r23s)
        counts['S2_r23_same_length_sites'] = len(r23s)
        counts['S2_r24_same_length_sites'] = 0
        counts['S2_base_code_bytes'] = oldn
        counts['S2_base_code_bytes_changed'] = len(diff)
    if 'S3' in parts:
        assert L.raw_messages(bb)[3] == L.raw_messages(cb)[3], 'MSG1 changed'
        so, sn = L.strings(old)[2], L.strings(new)[2]
        assert sn[:len(so)] == so, 'STR0 prefix changed'
        assert set(man['files']) == {'NightRemaster.ain'} and not man['pact_changed'] and not man['ex_changed'] and not man['fnl_changed'] \
            and not man['chart_changed'] and not man['winmm_changed']
        rt = L.runtime()[1]
        assert L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html') == L.BASE_CHART_SHA and L.sha(rt / 'winmm.dll') == L.BASE_WINMM_SHA
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
        # r21's two sites: their owners still call r21's replacements, which still call the originals
        for s_ in r21s:
            owner_ops = live_ops(nm, cv, s_['function'])
            assert owner_ops.count('CALLFUNC 0x%x' % s_['replacement_fid']) == 1 and owner_ops.count('CALLFUNC 0x%x' % s_['original_fid']) == 0, s_['function']
            assert 'CALLFUNC 0x%x' % s_['original_fid'] in live_ops(nm, cv, s_['replacement']), ('an r21 replacement no longer calls the original', s_['replacement'])
        # r22's two sites (the title): signature, uniqueness, the replacement adds to the original call
        assert sorted(s_['function'] for s_ in r22s) == sorted(R22_OWNERS), [s_['function'] for s_ in r22s]
        for s_ in r22s:
            o, r = nm['functions'][s_['original_fid']], nm['functions'][s_['replacement_fid']]
            assert [a['type'] for a in o['arguments']] == [a['type'] for a in r['arguments']] and o['return-type'] == r['return-type'], ('r22 site signature', s_['replacement'])
            assert s_['calls_of_original_in_function'] == 1, s_
            assert s_['function'] not in L.PINNED_ALL, ('an r22 site inside a pinned function', s_['function'])
            assert (s_['original'], s_['replacement']) == R22_OWNERS[s_['function']], s_
            assert L.raw_symbol(nm, s_['replacement_fid']) == s_['replacement'] and s_['replacement'].startswith('KR_C')
            assert s_['kind'] == 'CALLFUNC' and bytes.fromhex(s_['after']) == struct.pack('<Hi', 0x30, s_['replacement_fid'])
            assert 'CALLFUNC 0x%x' % s_['original_fid'] in live_ops(nm, cv, s_['replacement']), ('the replacement no longer calls the original', s_['replacement'])
            owner_ops = live_ops(nm, cv, s_['function'])
            assert owner_ops.count('CALLFUNC 0x%x' % s_['replacement_fid']) == 1 and owner_ops.count('CALLFUNC 0x%x' % s_['original_fid']) == 0, s_['function']
        # the title's wait: C_SceneTitle@Run waits with the C_SceneTitle@Update delegate (the frame the tick runs in) and calls
        # KR_CTitleServe right after it
        run_ops = live_ops(nm, cv, 'C_SceneTitle@Run')
        k = run_ops.index('CALLFUNC 0x%x' % L.fid_of(nm, 'AFL_Parts_WaitForClick'))
        assert run_ops[k - 4:k - 1] == ['PUSHSTRUCTPAGE', 'PUSH 0x%x' % L.fid_of(nm, 'C_SceneTitle@Update'), 'DG_NEW_FROM_METHOD'], run_ops[k - 4:k]
        assert run_ops[k + 3] == 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_CTitleServe'), run_ops[k:k + 4]
        for shim, tail in (('KR_T20StNext', ['PUSHSTRUCTPAGE', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StNextOf'), 'RETURN']),
                           ('KR_T20StPrev', ['PUSHSTRUCTPAGE', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StPrevOf'), 'RETURN']),
                           ('KR_T20StActive', ['PUSHSTRUCTPAGE', 'PUSHLOCALPAGE', 'PUSH 0x0', 'X_REF 0x1', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T20StActiveOf'), 'RETURN'])):
            got = live_ops(nm, cv, shim)
            assert got == tail, ('r20 CALLMETHOD shim body', shim, got)
        # V37 (static, r21 kept): the exit is the tail of the game's own 「게임 종료」
        ex = live_ops(nm, cv, 'KR_MExit')
        gx = live_ops(nm, cv, 'Ａ＿ゲーム終了')
        k = gx.index('CALLHLL system Exit 0')
        assert gx[k - 1] == 'PUSH 0x0' and gx[k + 1] == 'CALLHLL system Peek 0' and gx[k + 2].startswith('JUMP'), gx[k - 1:k + 3]
        assert ex[:2] == ['PUSH 0x0', 'CALLHLL system Exit 0'] and ex.count('CALLHLL system Peek 0') == 1 and ex.count('CALLHLL system Exit 0') == 1, ex
        # r24: the chart's live wait = KR_C24WaitRaw (r22 KR_CWait's hand-written body with the KR_C24Frame delegate and key cancel);
        # KR_CWait forwards to KR_C24Wait (S1)
        assert live_ops(nm, cv, 'KR_C24WaitRaw') == ['PUSH 0xffffffff', 'PUSH 0x%x' % L.fid_of(nm, 'KR_C24Frame'),
                                                      'DG_NEW_FROM_METHOD', 'PUSH 0x1', 'CALLFUNC 0x%x' % L.fid_of(nm, 'AFL_Parts_WaitForClick'), 'RETURN'], live_ops(nm, cv, 'KR_C24WaitRaw')
        r24_static(nm, cv, m, counts)
        # r22: the replay = the game's memory-mode path
        counts['S8_replay_ops_equal_ExecScene'] = replay_body_check(nm, cv)
        # reachable from the request consumers (home menu, title): no save / load / config / title call except the memory-mode
        # trio inside KR_CReplayRun; the only exit is KR_MExit. A frame (view::detail::View_Update: the engine's system messages
        # and interval saves every frame of every wait) is where the graph stops - r21's windows reach it only through CALLMETHOD
        roots = ['KR_MHomeRun', 'KR_MTick', 'KR_CTitleTick', 'KR_CTitleServe']
        reach_ids = call_graph_ids(nm, cv, roots, stop=('KR_CReplayRun', 'view::detail::View_Update'))
        reach = {L.raw_symbol(nm, f) for f in reach_ids}
        bad = sorted(n for n in reach if n.startswith(SAVE_CALL_PREFIXES) or n == 'Ａ＿ゲーム終了')
        assert not bad, ('a save / load / config / title / confirming exit reachable from the request consumers', bad[:5])
        rr_calls = sorted({L.raw_symbol(nm, int(op.split()[1], 16)) for op in live_ops(nm, cv, 'KR_CReplayRun') if op.startswith('CALLFUNC ')})
        assert rr_calls == sorted(['LSys3xScript::GetLabelName', 'LSys3xScript::Prepare', 'LSys3xScript::RunEvent'] + MEMORY_MODE), rr_calls
        exits = sorted(L.raw_symbol(nm, f) for f in reach_ids if 'CALLHLL system Exit 0' in live_ops_fid(nm, cv, f))
        assert exits == ['KR_MExit'], exits
        # the unlock flag file is read when the chart opens (r24: KR_C24Chart, the body KR_CChart forwards to; also when it opens
        # again after a replay) and after a button's write failed (KR_C24Toggle, to show what the disk holds); the chart never asks
        # the per-save registration
        uid = L.fid_of(nm, 'KR_MUnlockAll')
        callers = sorted(L.raw_symbol(nm, f) for f in reach_ids if 'CALLFUNC 0x%x' % uid in live_ops_fid(nm, cv, f))
        assert callers == ['KR_C24Chart', 'KR_C24Toggle'], callers
        # the flag is written by the menu bar's commands (KR_CDo) and, r24, by the two buttons (KR_C24Toggle) - the same function
        sid = L.fid_of(nm, 'KR_MSetUnlock')
        writers = sorted(L.raw_symbol(nm, f) for f in reach_ids if 'CALLFUNC 0x%x' % sid in live_ops_fid(nm, cv, f))
        assert writers == ['KR_C24Toggle', 'KR_CDo'], writers
        counts['S8_r24_flag_writers'] = len(writers)
        counts['S8_r22_sites_kept'] = len(r22s)
        counts['S8_r21_sites_kept'] = len(r21s)
        # r23's three sites: owner / original / replacement / kind as designed, signature, one call of the original in the owner
        # (now the replacement), a method target is a `this` call (PUSHSTRUCTPAGE before, CALLMETHOD after), not pinned
        assert sorted(s_['function'] for s_ in r23s) == sorted(R23_SITES), [s_['function'] for s_ in r23s]
        for s_ in r23s:
            orig, repl, kind = R23_SITES[s_['function']]
            assert (s_['original'], s_['replacement'], s_['kind']) == (orig, repl, kind), s_
            assert L.raw_symbol(nm, s_['original_fid']) == orig and L.raw_symbol(nm, s_['replacement_fid']) == repl, s_
            o, r = nm['functions'][s_['original_fid']], nm['functions'][s_['replacement_fid']]
            assert [a['type'] for a in o['arguments']] == [a['type'] for a in r['arguments']] and o['return-type'] == r['return-type'], ('r23 site signature', repl)
            assert s_['calls_of_original_in_function'] == 1 and s_['function'] not in L.PINNED_ALL, s_
            opcode = 0x30 if kind == 'CALLFUNC' else 0x00
            assert bytes.fromhex(s_['after']) == struct.pack('<Hi', opcode, s_['replacement_fid'])
            assert bytes.fromhex(s_['before']) == struct.pack('<Hi', opcode, s_['original_fid'])
            ops = live_ops(nm, cv, s_['function'])
            fmt = 'CALLFUNC 0x%x' if kind == 'CALLFUNC' else 'PUSH 0x%x'
            assert ops.count(fmt % s_['replacement_fid']) == 1 and ops.count(fmt % s_['original_fid']) == 0, (s_['function'], repl)
            if kind != 'CALLFUNC':
                k = ops.index(fmt % s_['replacement_fid'])
                assert ops[k - 1] == 'PUSHSTRUCTPAGE' and ops[k + 1] == 'CALLMETHOD 0x0', ops[k - 1:k + 2]
        sap = live_ops(nm, cv, 'C_HomeStatusView@SetActivePage')
        assert sap[-10:] == ['POP', 'PUSHSTRUCTPAGE', 'PUSH 0x9', 'X_REF 0x1', 'PUSH 0x%x' % L.fid_of(nm, 'C_FeelingView@UpdatePage'), 'PUSHSTRUCTPAGE',
                             'PUSH 0x%x' % L.fid_of(nm, 'KR_T23FeelShow'), 'CALLMETHOD 0x0', 'CALLMETHOD 0x1', 'RETURN'], sap[-10:]
        # the hand-written bodies: `this` passed on, the original query / the original DeleteMarks still run
        assert live_ops(nm, cv, 'KR_T23FeelShow') == ['PUSHSTRUCTPAGE', 'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T23FeelShowOf'), 'RETURN']
        assert live_ops(nm, cv, 'KR_T23FvGone') == ['PUSHSTRUCTPAGE', 'PUSH 0x%x' % L.fid_of(nm, 'C_FeelingView@DeleteMarks'), 'CALLMETHOD 0x0',
                                                    'CALLFUNC 0x%x' % L.fid_of(nm, 'KR_T23MoonClear'), 'RETURN']
        assert live_ops(nm, cv, 'KR_T23FvChara')[:16] == ['PUSHLOCALPAGE', 'PUSH 0x0', 'X_REF 0x1', 'PUSH 0x9', 'X_REF 0x1', 'PUSH 0xffffffff', 'EQUALE',
                                                          live_ops(nm, cv, 'KR_T23FvChara')[7], 'PUSHLOCALPAGE', 'PUSH 0x0', 'X_REF 0x1', 'PUSH 0x9',
                                                          'X_REF 0x1', 'PUSH 0x5', 'X_REF 0x1', 'RETURN']
        fs = live_ops(nm, cv, 'KR_T23FeelShowOf')
        assert fs[:7] == ['PUSHLOCALPAGE', 'PUSH 0x1', 'PUSHLOCALPAGE', 'PUSH 0x0', 'X_REF 0x1', 'PUSH 0x%x' % L.fid_of(nm, 'C_HomeStatusView@IsShowFeelingPage'),
                          'CALLMETHOD 0x0'], ('KR_T23FeelShowOf no longer starts with the original query', fs[:7])
        assert 'PUSH 0x%x' % L.fid_of(nm, 'C_FeelingView@Enabled') in fs, 'KR_T23FeelShowOf does not ask the moons\' own Enabled'
        for n in ('KR_T23StDraw',):
            assert 'PUSH 0x%x' % L.fid_of(nm, 'C_FeelingView@Enabled') in live_ops(nm, cv, n), (n, 'does not ask Enabled')
        # KR_T23Feel reads C_Ability@GetFeeling (not the inner value) of LAbility::m_pAbilities[c - 1]; KR_T23Rank calls the game's rank
        fe = live_ops(nm, cv, 'KR_T23Feel')
        assert 'PUSH 0x%x' % L.fid_of(nm, 'C_Ability@GetFeeling') in fe and 'PUSH 0x%x' % L.fid_of(nm, 'C_Ability@GetFeelingInnerValue') not in fe, fe
        assert 'CALLFUNC 0x%x' % L.fid_of(nm, 'C_SysVoice::GetFeelingRank_5') in live_ops(nm, cv, 'KR_T23Rank')
        # nothing reachable from the r23 entry points saves, loads, opens the config / title or exits
        reach23 = call_graph_ids(nm, cv, ['KR_T23FeelShowOf', 'KR_T23MoonClear', 'KR_T23StDraw'], stop=('view::detail::View_Update',))
        names23 = {L.raw_symbol(nm, f) for f in reach23}
        bad = sorted(n for n in names23 if n.startswith(SAVE_CALL_PREFIXES) or n == 'Ａ＿ゲーム終了')
        assert not bad, ('a save / load / title call reachable from the r23 code', bad[:5])
        assert not [f for f in reach23 if 'CALLHLL system Exit 0' in live_ops_fid(nm, cv, f)], 'an exit reachable from the r23 code'
        counts['S8_r23_sites_checked'] = len(r23s)
        counts['S8_r23_reachable_functions'] = len(reach23)
        counts['V37_exit_path_equals_game_exit_tail'] = 1
        counts['V37_functions_reachable_from_consumers'] = len(reach)
        counts['V35_unlock_flag_callers'] = len(callers)
    if 'S4' not in parts:
        return []
    vers = L.versions(L.base_paths()['raw'])
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
            assert nm['functions'][f['index']] == f, ('saved frame function moved', name, f['name'])
            ad = rr['address']
            assert bytes(old[16 + ad:16 + ad + 6]) == bytes(new[16 + ad:16 + ad + 6]), ('saved return bytes differ', name, rr['name'][:40], hex(ad))
            live += int(start == f['address'])
            frames.append(dict(file=name, fid=f['index'], offset=rr['offset'], live=start == f['address'], function=L.raw_symbol(m, f['index']),
                               address=ad))
    counts['S4_saves'] = len({x['file'] for x in frames})
    counts['S4_frames'] = len(frames)
    counts['S4_frames_in_live_versions'] = live
    counts['S4_frames_in_KR_T9HomeCasual'] = sum(1 for x in frames if x['function'] == 'KR_T9HomeCasual')
    counts['S4_frames_in_KR_T18RunSandboxed'] = sum(1 for x in frames if x['function'] == L.SANDBOX)
    counts['S4_frames_in_r22_forwarded'] = sum(1 for x in frames if x['function'] in R22_FORWARD)
    counts['S4_frames_in_r24_forwarded'] = sum(1 for x in frames if x['function'] in R24_FORWARD)
    counts['S4_frames_in_KR_CChart'] = sum(1 for x in frames if x['function'] == 'KR_CChart')
    counts['S4_frames_in_r23_owners'] = sum(1 for x in frames if x['function'] in R23_SITES)
    counts['S4_frames_in_title_owners'] = sum(1 for x in frames if x['function'] in R22_OWNERS)
    counts['S4_frames_in_r21_owners'] = sum(1 for x in frames if x['function'] in R21_OWNERS)
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
    # V25: the in-game name tables = the published chart v2 data (the chart builder's names, baked, not recomputed)
    for k, c in enumerate(cards):
        assert ko(vm.run('KR_T19CardHead', [k])) == c['nm'], ('card name table differs from the chart', c['key'])
        assert ko(vm.run('KR_T19CardTail', [k])) == c['tail'], ('card tail table differs from the chart', c['key'])
    for no, e in ev.items():
        assert ko(vm.run('KR_T19EvHead', [no])) == e['nm'], ('scene name table differs from the chart', no)
        assert ko(vm.run('KR_T19EvShort', [no])) == e['ns'], ('list line table differs from the chart', no)
    j = 0
    for i, ch in enumerate(chips):
        want = list(ch['scenes']) if KINDS[ch['kind']] == 'mem' else sorted(ch['scenes'])
        got = [vm.run('KR_T19SceneAt', [j + x]) for x in range(len(want))]
        assert got == want, ('drawer display order', ch['id'], got[:5], want[:5])
        assert vm.run('KR_T19ChipCols', [i]) in (2, 3)
        j += len(want)
    assert vm.run('KR_T19SceneAt', [j]) == -1 and j == 760
    pub = json.loads(re.search(r'<script type="application/json" id="yoru-data">(.*?)</script>',
                               (L.FLOW / 'chart' / 'yoru_flowchart_v2.html').read_text('utf8'), re.S).group(1))
    assert {int(k): (v['nm'], v['ns']) for k, v in pub['ev'].items()} == {no: (e['nm'], e['ns']) for no, e in ev.items()}, 'the published chart has other names'
    assert [(c['key'], c['nm'], c['tail']) for c in pub['cards']] == [(c['key'], c['nm'], c['tail']) for c in X['data']['cards']]
    counts['V25_name_tables_equal_chart'] = len(ev) + len(cards)


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


def check_dialog(d, counts, max_line=38):
    """C_SelectDialog@CreateParts: title width = longest line's character count (marks included) x size + spacing + 48;
    column width = max(widest item + 52, title width / columns); the dialog is columns x column width + 4 wide."""
    if d.get('kind') == 'chart':
        return                                  # r22: the chart screen is parts, not a select dialog (V42 checks it)
    lines, rows, h = geometry(d)
    for x in lines + [ko(t) for _, t, _, _ in d['items']]:
        assert not E_RE.search(x) and 'E번호' not in x, ('V21: an E-number left on a page', x)
        counts['V21_texts_without_e_numbers'] += 1
        assert not re.search(r'[0-9A-Za-z]…', x), ('a number or event id cut by 「…」', x)
        assert '★' not in x and '☆' not in x, ('★ ☆ left (r17 removed the main-story day mark)', x)
        assert '(본 것 ' not in x, ('old drawer-row form 「(본 것 n)」 left', x)
        bars_ok(x, counts)
    for x in lines:
        assert len(x) <= max_line and len(x) - (x[:1] in MARKS) <= 38, ('title line over 38', len(x), x)
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
    keys = [re.sub(r'[●○△]', '', ko(t)).strip() for iid, t, _, _ in d['items'] if iid not in (0, 11, 12)]
    assert len(keys) == len(set(keys)), ('V22: two items with the same name on one page', [k for k, n in collections.Counter(keys).items() if n > 1][:3])
    counts['V22_items_unique_on_page'] += len(keys)
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
    ev = X['ev']

    def mark(no):
        if ev[no]['fn'] in regs:
            return '○'
        if ev[no]['m0'] is not None and ev[no]['m0'] in vm.flags:
            return '△'
        return '●'
    for k, c in enumerate(cards):
        ds = walk('KR_T9CardPage', [k, c['month']], 1)
        assert ko(ds[0]['title']).split('\n')[0] == '〓' + c['nm'], ('card page first line', c['key'])
        if c['size'] > 1:
            ds = walk('KR_T9StagePage', [k, c['month']], math.ceil(c['size'] / 30))
            got = [ko(t) for d in ds for iid, t, _, _ in d['items'] if iid >= 100]
            assert got == ['%s %s' % (ev[s]['ns'], mark(s)) for s in c['stages']], ('stage list lines', c['key'], got[:3])
            assert all(ko(d['title']).split('\n')[0] == '〓' + c['nm'] and d['cols'] == 3 for d in ds), ('stage list title / columns', c['key'])
            counts['V2_stage_lists'] += 1
    for i, ch in enumerate(chips):
        ds = walk('KR_T9ChipPage', [i], math.ceil(len(ch['scenes']) / 30))
        order = list(ch['scenes']) if KINDS[ch['kind']] == 'mem' else sorted(ch['scenes'])
        got = [ko(t) for d in ds for iid, t, _, _ in d['items'] if iid >= 100]
        assert got == ['%s %s' % (ev[s]['ns'], mark(s)) for s in order], ('drawer list lines', ch['id'], got[:3])
        assert all(d['cols'] == 3 for d in ds), ('drawer list columns', ch['id'])
        counts['V2_drawer_lists'] += 1
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


def when_of(title):
    """the 「언제」 text of a card / scene page title (one or two lines)."""
    lines = title.split('\n')
    i = next(i for i, l in enumerate(lines) if l.startswith('†언제　'))
    text = lines[i][len('†언제　'):]
    if i + 1 < len(lines) and lines[i + 1].startswith('†　　　'):
        text += WHEN_CONT + lines[i + 1][len('†　　　'):]
    return text


def stage_home(X):
    out = {}
    for c in X['cards']:
        for i, s in enumerate(c['stages'], start=1):
            out[s] = (c['key'], i)
    return out


def when_check(X, no, text, counts):
    """V26: the in-game 「언제」 = the chart's 「언제」 strings, each E-number replaced by that scene's name (its list name when it is
    a stage of the same bundle, 「이 장면」 for itself; a memory slot playing the scene itself drops 「 · 원본 …」), cut only
    between whole tokens (「 …」) and never cutting an affinity text (V24)."""
    e = X['ev'][no]
    home = stage_home(X)

    def refs(target):
        opts = {X['ev'][target]['nr']}
        if target == no:
            opts.add('이 장면')
        a, b = home.get(target), home.get(no)
        if a and b and a[0] == b[0]:
            opts.add(X['ev'][target]['nk'].split(' · ')[0])
        return opts
    allowed = []
    for w in e['when']:
        w = re.sub(r' · 원본 E%05d$' % no, '', w)
        for tok in re.split(r' · | / ', w):
            alts = ['']
            pos = 0
            for z in E_RE.finditer(tok):
                alts = [a + tok[pos:z.start()] + r for a in alts for r in refs(int(z.group(0)[1:]))]
                pos = z.end()
            allowed += [a + tok[pos:] for a in alts]
    flat = text.replace(WHEN_CONT, ' · ')
    toks = [t for t in re.split(r' · | / ', flat) if t]
    if toks and toks[-1].endswith(' …'):
        toks[-1] = toks[-1][:-2]
    if toks and toks[-1] == '…':
        toks.pop()
    if text != '부르는 자리 없음':
        bad = [t for t in toks if t not in allowed]
        assert not bad, ('V26: a 「언제」 token that is not the chart\'s', no, bad[:2], text)
    for a in X['feel'].get(no, ([], []))[0]:
        assert a in flat, ('V24: affinity text missing on the 「언제」 line', no, a, text)
        counts['V24_affinity_on_pages'] += 1
    counts['V26_when_tokens'] += len(toks)


def event_pages(vm, X, counts):
    for no in sorted(X['ev']):
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'C'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, proxy('6월 · 호시카와 · 특훈 뒤 대화')])
        d = vm.dialogs[0]
        check_dialog(d, counts)
        title = ko(d['title'])
        assert title.split('\n')[0] == '〓' + X['ev'][no]['nm'], ('scene page first line', no, title.split('\n')[0])
        when_check(X, no, when_of(title), counts)
    counts['V2_event_pages'] = len(X['ev'])


def affinity_checks(vm, X, counts):
    """V24: card pages of the affinity events' cards and every scene page of an affinity event carry the full text; lane rows
    whose chart 「언제」 (first string) carries it show the full or the short form."""
    ev = X['ev']
    for k, c in enumerate(X['cards']):
        for s in c['stages']:
            full, short = X['feel'].get(s, ([], []))
            if not full:
                continue
            vm.reset()
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            if s == c['entry']:
                vm.script = [0]
                vm.run('KR_T9CardPage', [k, c['month']])
                t = when_of(ko(vm.dialogs[0]['title'])).replace(WHEN_CONT, ' · ')
                assert all(a in t for a in full), ('V24: affinity missing on the card page', c['key'], full, t)
                counts['V24_card_pages'] += 1
                row_ = ko(vm.run('KR_T9CardRow', [k, c['month']]))
                cond = ko(vm.run('KR_T19CardCond', [k]))
                w0 = (ev[s]['when'] or [''])[0]
                fa = [a for a in full if a in w0]
                # 「38자 안에 들어가면 쓴다」: the full text must be there whenever it fits next to the row's own parts (+ 「 …」)
                fits = len(row_) - len(cond) + len(' · '.join(fa)) + 2 <= 38
                for a, b in zip(full, short):
                    if a in w0:
                        assert a in row_ or (b in row_ and not fits), ('V24: affinity missing / shortened on the lane row', c['key'], a, row_)
                        counts['V24_lane_rows'] += 1
                        counts['V24_lane_rows_full' if a in row_ else 'V24_lane_rows_short'] += 1
    for no, (full, short) in X['feel'].items():
        vm.reset()
        vm.vars['YoruKR.T9.Ctx'] = 'P'
        vm.script = [0]
        vm.run('KR_T9EventPage', [no, ''])
        t = when_of(ko(vm.dialogs[0]['title'])).replace(WHEN_CONT, ' · ')
        assert all(a in t for a in full), ('V24: affinity missing on the scene page', no, full, t)
        counts['V24_scene_pages'] += 1
    counts['V24_affinity_events'] = len(X['feel'])


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
            assert ko(d['title']).split('\n')[0] == '〓' + ev[c['stages'][i]]['nm'], ko(d['title']).split('\n')[0]
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
    """V12 (r19): lane row = when + mark + condition + stage count + name tail; the tails sit exactly on the cards whose name
    without the tail collides in (month, lane); rows unique in (month, lane); the condition is the chart's first 「언제」 text
    without the row's date/slot, names for E-numbers, affinity kept (V24)."""
    cards = X['cards']
    vm.registered = set()
    rows = collections.defaultdict(list)
    heads = collections.defaultdict(list)
    tails = []
    for k, c in enumerate(cards):
        t = ko(vm.run('KR_T9CardRow', [k, c['month']]))
        when = ko(vm.run('KR_T9CardWhen', [k, c['month']]))
        cond = ko(vm.run('KR_T19CardCond', [k]))
        want = when + ' ●' + ((' ' + cond) if cond else '') + ((' (%d단계)' % c['size']) if c['size'] > 1 else '') + ((' ' + c['tail']) if c['tail'] else '')
        assert t == want, (c['key'], t, want)
        assert len(t) <= 38, t
        assert not E_RE.search(t) and 'E번호' not in t, t
        if c['tail']:
            tails.append(k)
        rows[(c['month'], c['lane'])].append(re.sub(r'[●○△]', '', t))
        heads[(c['month'], c['lane'])].append((k, c['nm'].replace(' · ' + c['tail'], '') if c['tail'] else c['nm']))
    dup = {key: [x for x, n in collections.Counter(v).items() if n > 1] for key, v in rows.items()}
    dup = {key: v for key, v in dup.items() if v}
    assert not dup, ('lane rows collide', dup)
    want = []
    for key, v in heads.items():
        cnt = collections.Counter(h for _, h in v)
        want += [k for k, h in v if cnt[h] > 1]
    assert sorted(tails) == sorted(want), ('tails not exactly on the colliding cards', sorted(set(tails) ^ set(want)))
    names = collections.defaultdict(list)
    for c in cards:
        names[(c['month'], c['lane'])].append(c['nm'])
    assert all(len(v) == len(set(v)) for v in names.values()), 'V22: two cards with the same name in one lane'
    counts['V12_tailed_rows'] = len(tails)
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


# ============================================================== V23: name rules recomputed from the raw data
def josa_wa(name):
    c = name[-1]
    return name + ('과' if '가' <= c <= '힣' and (ord(c) - 0xAC00) % 28 else '와')


def name_rule_checks(vm, X, counts, samples=None):
    """Rules 1-8 recomputed from schedule.json / labels.json / groups.json (the chart builder is not called): the in-game
    tables (KR_T19EvShort / EvHead / CardHead / CardTail, read in the VM) must say the same. Returns samples per rule."""
    sch, lab = X['sch'], X['labels']
    persons = {p['no']: p['kr'] or p['jp'] for p in json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))['persons']}
    party = set(PARTY_KR)
    out = collections.defaultdict(list)

    def speakers(no):
        return [p.strip('\u3000 ') for s_ in lab['cards'][str(no)].get('speakers') or [] for p in s_.split('＆')]

    def companion(no):
        return next((p for p in speakers(no) if p in party), None)

    def short(no):
        return ko(vm.run('KR_T19EvShort', [no]))

    def head(no):
        return ko(vm.run('KR_T19EvHead', [no]))

    def put(rule, no, got, want, data):
        assert got == want, ('V23 rule %s' % rule, no, got, want)
        out[rule].append(dict(event='E%05d' % no, name=got, data=data))
        counts['V23_rule_%s' % rule] += 1
    # rules 5, 6, 8: drawers
    for ch in X['chips']:
        kind = KINDS[ch['kind']]
        ents = sorted(ch['scenes'])
        lane = ch['lane']
        if kind in NAME_KIND:
            for k, no in enumerate(ents, start=1):
                put('6', no, short(no), '%d번째' % k, '%s · %d월 · %s · 이벤트 번호 %d번째로 작음(서랍 %d장)' % (LANE_KR[lane], ch['month'], NAME_KIND[kind], k, len(ents)))
                assert head(no).endswith('%s %d번째' % (NAME_KIND[kind], k)), ('V23 rule 6 head', no, head(no))
        elif kind == 'walk':
            seen = collections.Counter()
            for no in ents:
                e = sch[no]
                me = lane + 1 if 1 <= lane <= 7 else None
                other = [x for x in (e['person'], e['person2']) if x and x != me and x != 1]
                who = josa_wa(persons[other[0]]) if other else ('단둘이' if me else '혼자')
                seen[who] += 1
                put('5', no, short(no), '%s %d번째' % (who, seen[who]),
                    'person %s · person2 %s · 레인 %s · 같은 짝 안 %d번째' % (e['person'], e['person2'], LANE_KR[lane] if lane < 9 else lane, seen[who]))
                assert head(no).endswith('%s 동행 %d번째' % (who, seen[who])), ('V23 rule 5 head', no, head(no))
        elif kind == 'unused':
            for k, no in enumerate(ents, start=1):
                put('8', no, short(no), '미사용 %d' % k, 'category unknown · 번호 순 %d' % k)
        elif kind == 'etc':
            for no in ents:
                put('8', no, short(no), '일요일 시간 끝 처리', 'source 残時間終わり処理／日曜')
        elif kind == 'mem':
            pg = lane - 8
            slot = {}
            for no in ch['scenes']:
                for t in sch[no]['triggers']:
                    if t['kind'] == 'memory_replay':
                        slot[no] = t['slot']
                        assert t['page'] == pg
            for no in ch['scenes']:
                if no in slot:
                    src = sch[no].get('replay_of')
                    date = ''
                    for c in X['cards']:
                        if src in c['stages'] and c['day']:
                            date = ' (%d/%d)' % (c['month'], c['day'])
                    put('7', no, head(no), '회상 · 그 밖 · 회상 %d쪽 %d번%s' % (pg, slot[no], date),
                        'memory_replay page %d slot %d · replay_of E%05d%s' % (pg, slot[no], src or 0, date))
    # rules 1-4: cards
    dungeons = lab['dungeons']
    for k, c in enumerate(X['cards']):
        nm = ko(vm.run('KR_T19CardHead', [k]))
        when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
        if c['slot']:
            when += ' ' + SLOT_KR[c['slot']]
        tail = ko(vm.run('KR_T19CardTail', [k]))
        if c['lane'] == 0 and c['day']:
            want = ' · '.join([when, '본편'] + ([tail] if tail else []) + (['%d단계' % c['size']] if c['size'] > 1 else []))
            put('1', c['entry'], nm, want, '본편 카드 · 날짜 %s · 단계 %d' % (when, c['size']))
        if c['lane'] == 8:
            e = sch[c['entry']]
            srcs = [t['source'] for t in e['triggers'] if t['kind'] == 'dungeon']
            srcs = [x for x in srcs if '@RunEvent' in x] + [x for x in srcs if '@RunEvent' not in x]
            z = re.match(r'^C_EventDungeon\d{4}@RunEvent(\w+)$', srcs[0]) if srcs else None
            if z and srcs[0] in dungeons:
                xx = z.group(1)
                m_ = re.match(r'^B(\d+)$', xx)
                suf = ('사건 %d' % int(m_.group(1))) if m_ else {'R1': '보스', 'Exit': '출구', 'Entrance': '입구', 'B': '사건', 'R': ''}.get(xx, xx)
                place = dungeons[srcs[0]]['kr']
                assert (' · ' + place + (' · ' + suf if suf else '')) in nm, ('V23 rule 4', c['key'], nm)
                out['4'].append(dict(event='E%05d' % c['entry'], name=nm, data='%s → %s · %s' % (srcs[0], place, suf or '(없음)')))
                counts['V23_rule_4'] += 1
        # rule 3: the tail = companion + ordinal inside that companion, among the cards whose name without the tail collides
        if tail:
            grp = sorted((x for x in X['cards'] if x['month'] == c['month'] and x['lane'] == c['lane']
                          and (x['nm'].replace(' · ' + x['tail'], '') if x['tail'] else x['nm']) == nm.replace(' · ' + tail, '')), key=lambda x: x['entry'])
            def pre(no):
                who = companion(no)
                return josa_wa(who) if who else ('혼자' if speakers(no) == ['료'] else '장면')
            same = [x['entry'] for x in grp if pre(x['entry']) == pre(c['entry'])]
            put('3', c['entry'], tail, '%s %d' % (pre(c['entry']), same.index(c['entry']) + 1),
                '겹치는 카드 %d장 · 화자 %s' % (len(grp), '/'.join(speakers(c['entry'])[:3])))
        # rule 2: bundle stages (the list line)
        if c['size'] > 1:
            stages = [r for r in c['rows'] if r[6]]
            for i, r in enumerate(stages, start=1):
                no = r[0]
                via = r[3] if r[2] == 'answer' else None
                who = companion(no)
                got = short(no)
                assert got.startswith('%d. ' % i), ('V23 rule 2 number', no, got)
                if via:
                    assert ('갈래 %d' % via) in got, ('V23 rule 2 branch', no, got)
                if who:
                    assert josa_wa(who) in got, ('V23 rule 2 companion', no, got)
                if len(out['2']) < 40:
                    out['2'].append(dict(event='E%05d' % no, name=got, data='%s %d단계 · via %s · 화자 %s' % (c['key'], i, via or '-', '/'.join(speakers(no)[:3]))))
                counts['V23_rule_2'] += 1
    return {k: v for k, v in sorted(out.items())}


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
    # r19: the probe logs every event read only in another save (△); the VM's read marks = their first messages
    read = st.get('read') or []
    vm.flags = other | {X['ev'][e]['m0'] for e in read if X['ev'][e]['m0'] is not None}
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
        # r19 name pages: a dungeon card and its stage list, drawer scene lists and scene pages opened from them
        elif parts[0] == 'DCARD':
            vm.run('KR_T9CardPage', [int(parts[1]), int(parts[2])])
            d = vm.dialogs[0]
            counts['N_r19_card_pages'] += 1
        elif parts[0] in ('DSTAGES', 'STAGELIST'):
            k = int(parts[1])
            vm.run('KR_T9StagePage', [k, X['cards'][k]['month']])
            d = vm.dialogs[0]
            counts['N_r19_stage_lists'] += 1
        elif parts[0] == 'DRAWER':
            vm.run('KR_T9ChipPage', [int(parts[1])])
            d = vm.dialogs[0]
            counts['N_r19_drawer_lists'] += 1
        elif parts[0] == 'SCENE':
            vm.script = [100 + int(parts[2]), 0, 0]
            vm.run('KR_T9ChipPage', [int(parts[1])])
            d = vm.dialogs[1]
            counts['N_r19_scene_pages'] += 1
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
    # ---------------- r20 (native): the 「이벤트」 page as drawn, the partner labels, brightness, part counts, home pixels
    r20 = res['r20']
    vm.flags = set()
    vm.registered = regs
    vm.today = today
    vm.reset()
    texts = r20['status_texts']
    w1 = r20['status_charas']['A']
    w2 = r20['status_charas']['C']
    feel = {i + 1: v for i, v in enumerate(st['feel'])}
    mode = st['mode']
    vm.feel = dict(feel)
    vm.game_mode = mode

    def page4_want(c, rg, td, fl):
        v = r23_value(R23['G'], fl.get(c, 0), c)
        en = r23_enabled(c, mode)
        return r23_status_text(X, R23['G'], R23['gates'], rg, td, c, v, en), en
    for key, c in (('A', w1), ('C', w2)):
        want, en = page4_want(c, regs, today, feel)
        assert texts[key] == ko(vm.run('KR_T23StText', [c, int(en)])) == want, ('native 이벤트 쪽 %s != VM' % key, c)
    match_b = [c for c in range(1, 9) if ko(vm.run('KR_T23StText', [c, int(r23_enabled(c, mode))])) == texts['B']]
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
    # the dungeon caller (C_SceneDungeon@Run -> C_Status::RunStatusInDungeon): page 4 = the VM, parts gone after the window
    dr = res['dungeon_run']
    assert dr['exit_code'] == 0 and dr['log'][-1] == 'END' and not dr.get('vm_error') and not dr.get('message'), ('dungeon run failed', dr.get('exit_code'), dr['log'][-3:])
    dg = r20['dungeon']
    z = re.match(r'DUNGEON date=(\d+)/(\d+) person=(\d+)', dg['date'])
    dtoday = (int(z.group(1)), int(z.group(2)))
    dregs_line = next(l for l in dr['log'] if l.startswith('REGS'))
    dregs = {X['ev'][int(x)]['fn'] for x in dregs_line.split()[1:]}
    vm.registered = dregs
    vm.today = dtoday
    vm.reset()
    dfeel = {int(k): v for k, v in dg['feel'].items()}
    vm.feel = dict(dfeel)
    want, en = page4_want(dg['person'], dregs, dtoday, dfeel)
    assert dg['text'] == ko(vm.run('KR_T23StText', [dg['person'], int(en)])) == want, ('native dungeon 이벤트 쪽 != VM', dg['person'])
    assert (dg['before']['ours'], dg['page1']['ours'], dg['page4']['ours'], dg['after']['ours']) == (0, 0, 2, 0), ('native part counts (dungeon)', dg)
    assert dg['page1']['charastatus'] == dg['page4']['charastatus'] > 0 and dg['after']['charastatus'] == 0, ('the own parts of the dungeon status window', dg)
    assert 'C_Status::RunStatusInDungeon' in (dg['stack'] or ''), ('the dungeon status window was not opened by RunStatusInDungeon', dg['stack'])
    out['r20_dungeon'] = dict(save=dr['save'], today='%d/%d' % dtoday, person=dg['person'], text_equal_vm=True,
                              part_counts=dict(before=0, page1=0, page4=2, after=0), charastatus_parts=dg['page4']['charastatus'],
                              opened_by='C_SceneDungeon@Run > C_Status::RunStatusInDungeon > C_Status::RunStatus')
    counts['N_r20_blocks_identical'] = 4 + sum(len(b_) for b_ in labels.values())
    return out


# ============================================================== r20: counts, the 「이벤트」 page, the partner labels
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
    vm.feel = dict(R23_SYN_FEEL)                            # r23: the page shows the affinity of a person with moons
    vm.game_mode = 0
    fid = lambda n: vm.fs[n]['index']
    sv = vm.status_view(2, page=1)

    def step(shim):
        vm.method(fid(shim), sv, [])
        return sv[16]

    def ours():
        return [n for n in vm.ours() if n in (ST_PANEL, ST_TEXT)]

    def check_page4(chara):
        t, pnl = vm.parts[ST_TEXT], vm.parts[ST_PANEL]
        v = r23_value(R23['G'], vm.feel.get(chara, 0), chara)
        en = r23_enabled(chara, vm.game_mode)
        assert ko(t['text']) == r23_status_text(X, R23['G'], R23['gates'], regs, today, chara, v, en), ('V30 page-4 text (r23 page)', chara)
        assert t['parent'] == pnl['parent'] == VM.ST_ROOT and t['show'] == pnl['show'] == 1, ('V30 parent/show', t, pnl)
        assert t['pos'] == (52.0, 80.0) and pnl['pos'] == (32.0, 64.0) and (pnl['z'], t['z']) == (40, 41), (t, pnl)
        assert t['font'] == ST_FONT and t['tag'] == 1 and t['linespace'] == 8, t
        assert pnl['construct'][0] == ('create', 338, r23_panel_h(X, R23['G'], R23['gates'], regs, today, chara, v, en)) and pnl.get('built') == 1, pnl
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
    wheel = ['delegate C_Status::OnMouseWheel']           # the delegate RunStatus passes (a delegate value is a list here)
    vm.run('KR_T20StEnd', [wheel])
    assert not ours() and ('AFL_Parts_EraseWholeMouseWheelEvent', [wheel]) in vm.calls, 'V30 parts left after the window closed'
    vm.method(fid('C_HomeStatusView@SetActivePage'), sv, [1])            # BeginStatus of the next opening
    for _ in range(3):
        step('KR_T20StNext')
    assert sv[16] == 4 and len(ours()) == first, ('V30 a second opening makes another number of parts', len(ours()), first)
    vm.run('KR_T20StEnd', [wheel])
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


def r20_blocks(log):
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


# ============================================================== r21: the request consumer (V34-V40)
# the protocol (설계_v4 「프로토콜(확정, 09-28 02시)」) and the texts, written here independently of the jaf
R21_CODE = 2026092801
MENU_DIR = VM.GAME_DIR + 'KRMenu'
REQ = MENU_DIR + '\\request.txt'
RES = MENU_DIR + '\\last_result.txt'
RESET_REQ = MENU_DIR + '\\reset.req'
RESTORE_REQ = MENU_DIR + '\\restore.req'
MARKER = VM.SAVE_DIR + '\\YoruKR_reset.marker'
CHART = VM.SAVE_DIR + '\\YoruKR_Chart.dat'
R21_WRITABLE = {REQ, RES, RESET_REQ, RESTORE_REQ, MARKER, CHART}
T_CHART = '<chart>'                    # r22: the chart screen (a chart wait in vm.dialogs) where r21 showed the 「다음 단계」 notice
T_UNLOCK = '〓모드 메뉴\n†전체 개방: 안 본 이벤트도 열람·재생됩니다'
T_REVERT = '〓모드 메뉴\n†전체 개방 되돌리기: 읽은 이벤트만 열람·재생됩니다'   # r22 wording (the chart is save-independent)
T_FLAG_FAIL = '〓모드 메뉴\n†전체 개방 설정을 저장하지 못했습니다'
T_RESET = '〓전체 리셋\n†전역 진행 기록을 초기화합니다.\n†백업을 만든 뒤 게임을 종료합니다.\n†세이브 파일과 설정은 남습니다.'
T_RESTORE = '〓전체 리셋 되돌리기\n†가장 최근 전체 리셋의 백업을 되돌립니다.\n†게임을 종료합니다. 다시 켜면 되돌린 기록으로 시작합니다.\n†세이브 파일과 설정은 남습니다.'
T_SCHED_FAIL = {'reset': '〓전체 리셋\n†예약 파일을 쓰지 못해 실행하지 않았습니다. 게임은 계속됩니다.',
                'restore': '〓전체 리셋 되돌리기\n†예약 파일을 쓰지 못해 실행하지 않았습니다. 게임은 계속됩니다.'}
T_RESULT_HEAD = '〓모드 메뉴 결과'
SAFE_SET = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-.,:()/')
YES, NO, OK = 11, 12, 1
# every line the native hook (hook_modmenu WriteResult) can leave, and a few harder ones
HOOK_RESULTS = ['reset ok KR_reset_20260928_031500', 'reset failed backup folder', 'reset failed backup copy 3 (nothing deleted)',
                'reset partial 2 files not deleted (backup KR_reset_20260928_031500)', 'restore failed no backup',
                'restore failed keep folder', 'restore partial 1 files (from KR_reset_20260928_031500, previous kept in KR_before_restore_20260928_031501)',
                'restore ok KR_reset_20260928_031500 (previous kept in KR_before_restore_20260928_031501)',
                'reset skipped marker missing', 'restore skipped marker missing', 'maintenance failed save folder unresolved']


def hook_request(vm, cmd, seq=1, lf='\r\n'):
    """What the hook's WriteRequest leaves (cmd, seq, time; ASCII; CR LF; the folder made first; atomic replace)."""
    vm.dirs.add(MENU_DIR)
    vm.disk[REQ] = cmd + lf + str(seq) + lf + '2026-09-28 03:30:00' + lf


def hook_result(vm, text):
    vm.dirs.add(MENU_DIR)
    vm.disk[RES] = text


def model_wrap(s, width=38):
    """Independent model of the result window body: first line, the half-width set (others -> ?), 160 characters, word wrap
    at 38 (a word of 38 or more characters stands on its own line)."""
    line = s.replace('\r', '\n').split('\n')[0].strip(' ')
    line = ''.join(c if c in SAFE_SET else '?' for c in line[:160])
    out, cur = [], ''
    for w in line.split(' '):
        if not w:
            continue
        while len(w) >= width:
            if cur:
                out.append(cur)
                cur = ''
            out.append(w[:width])
            w = w[width:]
        if not w:
            continue
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur += ' ' + w
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return '\n'.join('†' + x for x in out)


def r21_fresh(cand, nm, mutate=None, alias=None):
    v = VM(cand, nm, mutate=mutate, alias=alias)
    v.guard_saves = True
    v.today = (6, 13)
    return v


def r21_home(vm, frames=6, then=11, each=None, answers=()):
    """One pass of RunHome's loop as the game runs it: the home menu built (title, items), KR_T8HomeMenuOpen, KR_T9HomeMenuRun
    (1, 200) -> KR_MHomeRun -> ■選択ダイアログ／実行 waiting `frames` frames (the hook may write at a frame), then KR_T8HomeMenuClose.
    Returns (res, loop again?, the dialogs of this pass, exit code or None)."""
    vm.cur = None                                   # (not vm.reset(): the session variables carry over, as in the game)
    vm.calls = []
    vm.frames = []
    vm.ended = None
    vm.exited = None
    vm.dialogs = []
    vm.script = [Wait(frames, then, each)] + list(answers)
    home_menu(vm)
    vm.run('KR_T8HomeMenuOpen')
    assert vm.vars.get('YoruKR.T8.HomeMenu') == '1'
    try:
        res = vm.run('KR_T9HomeMenuRun', [1, 200])
    except VMExit as ex:
        return None, None, vm.dialogs, ex.code
    assert vm.vars.get('YoruKR.M.Home', '') == '', 'the poll is still armed after the home menu returned'
    assert vm.cur is None, 'a dialog was left behind'
    again = vm.run('KR_T8HomeMenuClose', [res])
    assert not vm.script, ('answers left over (a window did not open)', vm.script)
    return res, bool(again), vm.dialogs, None


def req_marker_invariant(vm):
    """A .req file never exists without the marker saying the same word (the hook acts only on both)."""
    for word, path in (('reset', RESET_REQ), ('restore', RESTORE_REQ)):
        if path in vm.disk:
            assert vm.disk.get(MARKER) == word and vm.disk[path] == word, ('a .req without the matching marker', word, vm.disk.get(MARKER), vm.disk[path])
    assert not (RESET_REQ in vm.disk and RESTORE_REQ in vm.disk), 'both .req files at once'


def writes_of(vm):
    return {p for op, p in vm.file_calls if op in ('write', 'delete', 'mkdir')}


def r21_request_checks(mk, counts):
    """V34: each command as the hook writes it -> consumed, the right window / file / exit; unknown commands ignored."""
    rows = []
    for cmd, answers, title, files_after, exits in (
            ('chart', [0], T_CHART, {}, None),
            ('unlock_all', [OK], T_UNLOCK, {CHART: 'YoruKR.Chart.1\r\n1\r\n'}, None),
            ('unlock_revert', [OK], T_REVERT, {CHART: 'YoruKR.Chart.1\r\n0\r\n'}, None),
            ('reset_all', [YES], T_RESET, {MARKER: 'reset', RESET_REQ: 'reset'}, 0),
            ('reset_restore', [YES], T_RESTORE, {MARKER: 'restore', RESTORE_REQ: 'restore'}, 0)):
        for lf in ('\r\n', '\n'):
            vm = mk()
            res, again, ds, code = r21_home(vm, frames=6, then=11, each=lambda v, f, c=cmd, l=lf: hook_request(v, c, 7, l) if f == 2 else None, answers=answers)
            home, ours = ds[0], ds[1:]
            assert home['armed'] == '1' and home.get('ended_by') == R21_CODE and home['frames'] == 3, ('V34 the home menu did not end on the request', cmd, home.get('ended_by'), home['frames'])
            assert REQ not in vm.disk, ('V34 request.txt left after it was served', cmd)
            assert [ko(d['title']) for d in ours] == [title], ('V34 window', cmd, [ko(d['title']) for d in ours])
            for d in ours:
                check_dialog(d, counts)
            for p, want in files_after.items():
                assert vm.disk.get(p) == want, ('V34 file after', cmd, p, vm.disk.get(p), want)
            assert writes_of(vm) <= R21_WRITABLE | {MENU_DIR}, ('V34 a write outside the protocol files', sorted(writes_of(vm) - R21_WRITABLE))
            req_marker_invariant(vm)
            if exits is None:
                assert code is None and res == PICK and again, ('V34 the home menu is not rebuilt', cmd, res, again, code)
                assert vm.vars.get('YoruKR.T8.HomeMenu') == '' and vm.v('Ctx') == 'P', (cmd, vm.vars.get('YoruKR.T8.HomeMenu'), vm.v('Ctx'))
            else:
                assert code == exits and vm.calls[-1] == ('exit', 0), ('V34 no exit after 예', cmd, code, vm.calls[-3:])
            counts['V34_commands'] += 1
        rows.append(dict(cmd=cmd, window=title.split('\n')[-1], files={Path(p).name: v for p, v in files_after.items()}, exit=exits))
    # unknown commands, blank lines, extra words: deleted, no window, no file, the menu rebuilt; spaces around a command are
    # ignored (the hook writes none)
    for cmd, known in (('bogus', False), ('', False), ('CHART', False), ('chart extra', False), ('unlock', False), ('  chart  ', True)):
        vm = mk()
        res, again, ds, code = r21_home(vm, frames=4, each=lambda v, f, c=cmd: hook_request(v, c) if f == 0 else None, answers=[0] if known else [])
        assert REQ not in vm.disk and code is None and res == PICK and again, ('V34 unknown command', cmd)
        assert len(ds) == (2 if known else 1), ('V34 unknown command opened a window', cmd, [ko(d['title'])[:20] for d in ds[1:]])
        assert writes_of(vm) == {REQ}, ('V34 unknown command wrote a file', cmd, writes_of(vm))
        counts['V34_unknown_ignored'] += int(not known)
    # nothing pending: the home menu waits, polls, and returns the player's pick untouched
    vm = mk()
    res, again, ds, code = r21_home(vm, frames=5, then=12)
    assert res == 12 and not again and len(ds) == 1 and ds[0].get('ended_by') is None and ds[0]['polls'] == 2 * 5, ('V34 idle home menu', res, ds[0].get('polls'))
    assert [op for op, _ in vm.file_calls] == ['exist'] * 10 and {p for _, p in vm.file_calls} == {REQ, RES}
    counts['V39_file_calls_per_armed_frame'] = 2
    return rows


def r21_flag_checks(mk, counts):
    """V35: YoruKR_Chart.dat bytes, the value after a restart (a fresh VM on the same disk), revert, both line ends, a failed
    write (notice, flag unchanged), garbage = 0."""
    vm = mk()
    assert vm.run('KR_MUnlockAll') == 0, 'V35 flag without a file'
    seq = []
    for cmd, want, text in (('unlock_all', 1, T_UNLOCK), ('unlock_revert', 0, T_REVERT), ('unlock_all', 1, T_UNLOCK)):
        res, again, ds, code = r21_home(vm, each=lambda v, f, c=cmd: hook_request(v, c) if f == 1 else None, answers=[OK])
        assert ko(ds[1]['title']) == text and vm.disk[CHART] == 'YoruKR.Chart.1\r\n%d\r\n' % want, ('V35', cmd, vm.disk.get(CHART))
        disk = dict(vm.disk)
        v2 = mk()                                      # the game restarted: only the disk carries over
        v2.disk = disk
        assert v2.run('KR_MUnlockAll') == want, ('V35 flag lost across a restart', cmd)
        seq.append(want)
        counts['V35_flag_saved_and_reloaded'] += 1
    for text, want in (('YoruKR.Chart.1\n1\n', 1), ('YoruKR.Chart.1\r\n1\r\n', 1), ('YoruKR.Chart.1\r\n0\r\n', 0), ('1', 0), ('YoruKR.Chart.1\r\n2\r\n', 0), ('', 0)):
        vm.disk[CHART] = text
        assert vm.run('KR_MUnlockAll') == want, ('V35 flag parse', text)
    vm.disk[CHART] = 'YoruKR.Chart.1\r\n0\r\n'
    vm.fail_write = {CHART}
    res, again, ds, code = r21_home(vm, each=lambda v, f: hook_request(v, 'unlock_all') if f == 1 else None, answers=[OK])
    assert ko(ds[1]['title']) == T_FLAG_FAIL and vm.run('KR_MUnlockAll') == 0 and REQ not in vm.disk, 'V35 a failed write must say so and keep the flag'
    vm.fail_write = set()
    counts['V35_failed_write_reported'] += 1
    return dict(sequence=seq, file_bytes='YoruKR.Chart.1\\r\\n<0|1>\\r\\n')


def r21_reset_checks(mk, counts):
    """V36: 아니요 / cancel -> nothing; 예 -> marker + .req (same word), the opposite .req removed, exit; write failures."""
    rows = []
    for cmd, word, title in (('reset_all', 'reset', T_RESET), ('reset_restore', 'restore', T_RESTORE)):
        other = RESTORE_REQ if word == 'reset' else RESET_REQ
        req = RESET_REQ if word == 'reset' else RESTORE_REQ
        for ans in (NO, -1):
            vm = mk()
            res, again, ds, code = r21_home(vm, each=lambda v, f, c=cmd: hook_request(v, c) if f == 0 else None, answers=[ans])
            assert code is None and res == PICK and again and ko(ds[1]['title']) == title, ('V36 no', cmd, ans, code)
            assert [(i, ko(t)) for i, t, _, _ in ds[1]['items']] == [(NO, '아니요'), (YES, '예')] and ds[1]['cols'] == 2, ds[1]['items']
            assert MARKER not in vm.disk and RESET_REQ not in vm.disk and RESTORE_REQ not in vm.disk and REQ not in vm.disk, ('V36 files after 아니요', cmd)
            assert writes_of(vm) == {REQ}, ('V36 a write after 아니요', cmd, writes_of(vm))
            counts['V36_no_does_nothing'] += 1
        # 예, with a stale opposite .req left from an earlier run and no KRMenu folder of our own making
        vm = mk()
        vm.dirs.add(MENU_DIR)
        vm.disk[other] = 'stale'
        res, again, ds, code = r21_home(vm, each=lambda v, f, c=cmd: hook_request(v, c) if f == 0 else None, answers=[YES])
        assert code == 0 and vm.calls[-1] == ('exit', 0), ('V36 예 did not exit', cmd, code)
        assert vm.disk.get(MARKER) == word and vm.disk.get(req) == word and other not in vm.disk and REQ not in vm.disk, ('V36 files after 예', cmd, sorted(vm.disk))
        order = [(op, p) for op, p in vm.file_calls if op == 'write']
        assert [p for _, p in order[-2:]] == [MARKER, req], ('V36 the marker must be written before the .req', order[-2:])
        req_marker_invariant(vm)
        counts['V36_yes_schedules_and_exits'] += 1
        rows.append(dict(cmd=cmd, marker=vm.disk[MARKER], req=Path(req).name, req_text=vm.disk[req], removed_stale=Path(other).name, exit=code))
        # KR_MSchedule makes KRMenu when it is missing
        vm = mk()
        vm.dirs.discard(MENU_DIR)
        assert vm.run('KR_MSchedule', [word]) == 1 and MENU_DIR in vm.dirs and vm.disk.get(req) == word
        req_marker_invariant(vm)
        # marker write fails: no .req, no exit, a notice
        vm = mk()
        vm.fail_write = {MARKER}
        res, again, ds, code = r21_home(vm, each=lambda v, f, c=cmd: hook_request(v, c) if f == 0 else None, answers=[YES, OK])
        assert code is None and [ko(d['title']) for d in ds[1:]] == [title, T_SCHED_FAIL[word]], ('V36 marker failure', cmd, [ko(d['title'])[:12] for d in ds])
        assert MARKER not in vm.disk and req not in vm.disk, ('V36 files after a marker failure', cmd, sorted(vm.disk))
        # .req write fails: the marker goes again, no exit, a notice
        vm = mk()
        vm.fail_write = {req}
        res, again, ds, code = r21_home(vm, each=lambda v, f, c=cmd: hook_request(v, c) if f == 0 else None, answers=[YES, OK])
        assert code is None and ko(ds[-1]['title']) == T_SCHED_FAIL[word], ('V36 .req failure', cmd)
        assert MARKER not in vm.disk and req not in vm.disk, ('V36 marker left after a .req failure', cmd, sorted(vm.disk))
        req_marker_invariant(vm)
        counts['V36_write_failures_safe'] += 2
    return rows


def r21_result_checks(mk, counts):
    """V38: last_result.txt -> first line, the half-width set, wrapped at 38, deleted; before a request waiting with it."""
    rows = []
    cases = [(t + '\r\n', t) for t in HOOK_RESULTS] + [
        ('reset ok KR_reset_20260928_031500\r\nsecond line\r\n', None), ('  reset ok  \r\n', None), ('reset ok 한글%<>|\r\n', None),
        ('x' * 90 + '\r\n', None), ('word ' * 50, None)]
    for text, first in cases:
        vm = mk()
        res, again, ds, code = r21_home(vm, each=lambda v, f, t=text: hook_result(v, t) if f == 0 else None, answers=[OK])
        want = T_RESULT_HEAD + '\n' + model_wrap(text)
        got = ko(ds[1]['title'])
        assert got == want, ('V38 result window', text[:40], got, want)
        assert RES not in vm.disk and res == PICK and again, ('V38 last_result left / menu not rebuilt', text[:40])
        body = got.split('\n')[1:]
        assert all(x[:1] == '†' for x in body), ('V38 a result line without its colour mark', body)
        body = [x[1:] for x in body]
        assert all(len(x) <= 38 for x in body) and all(set(x) <= SAFE_SET | {'?'} for x in body), ('V38 line too long or unsafe', body)
        if first is not None:
            assert ' '.join(body) == first, ('V38 a hook line changed', first, body)
        check_dialog(ds[1], counts, max_line=39)
        rows.append(body)
        counts['V38_results_shown'] += 1
    # empty result file: deleted, no window
    vm = mk()
    res, again, ds, code = r21_home(vm, each=lambda v, f: hook_result(v, '') if f == 0 else None)
    assert RES not in vm.disk and len(ds) == 1, 'V38 empty result'
    # result and request together: the result first, then the request's window
    vm = mk()

    def both(v, f):
        if f == 0:
            hook_result(v, 'reset ok KR_reset_20260928_031500\r\n')
            hook_request(v, 'chart')
    res, again, ds, code = r21_home(vm, each=both, answers=[OK, 0])
    assert [ko(d['title']).split('\n')[0] for d in ds[1:]] == [T_RESULT_HEAD, T_CHART] and ko(ds[2]['title']) == T_CHART, [ko(d['title'])[:12] for d in ds]
    assert RES not in vm.disk and REQ not in vm.disk
    counts['V38_result_before_request'] += 1
    return dict(windows=len(rows), longest_lines=max(len(r) for r in rows), sample=rows[6])


def r21_scope_checks(mk, counts):
    """V39: the tick reads files only while KR_MHomeRun armed the home menu."""
    # 1 a dialog outside the home menu (title, dungeon, event, the Sunday confirmation: any ■選択ダイアログ／実行 not run by
    #   KR_MHomeRun) with a request waiting: no file call, the wait is not ended, the request stays for the home menu
    for label, prep in (('fresh game (title / dungeon / event)', lambda v: None),
                        ('after a home menu returned a pick', lambda v: r21_home(v, frames=2, then=13)),
                        ('after the r13 panel pick', lambda v: r21_home(v, frames=2, then=PICK))):
        vm = mk()
        prep(vm)
        hook_request(vm, 'chart')
        vm.file_calls = []
        vm.cur = None
        vm.calls = []
        vm.dialogs = []
        vm.script = [Wait(30, 1)]
        vm.native('■選択ダイアログ／タイトル設定', [proxy('●일요일을 끝낼까요?')])
        vm.native('■選択ダイアログ／選択肢追加', [11, proxy('예'), '', 0])
        vm.native('■選択ダイアログ／選択肢追加', [12, proxy('아니요'), '', 0])
        r = vm.native('■選択ダイアログ／実行', [1, 0])
        d = vm.dialogs[0]
        assert r == 1 and d['polls'] == 0 and not vm.file_calls and d.get('ended_by') is None and REQ in vm.disk, ('V39 a poll outside the home menu', label, d['polls'], vm.file_calls[:3])
        counts['V39_dialogs_outside_home_not_polled'] += 1
        # the home menu afterwards serves it
        res, again, ds, code = r21_home(vm, answers=[0])
        assert REQ not in vm.disk and ko(ds[1]['title']) == T_CHART
    # 2 our own windows are not polled: a request written while the chart notice waits is left for the next home menu
    vm = mk()
    hook_request(vm, 'chart')

    def during_notice(v, f):
        if f == 3:
            hook_request(v, 'unlock_all', 2)
    res, again, ds, code = r21_home(vm, frames=3, answers=[Wait(10, 0, during_notice, tick='KR_C24Frame')])
    assert ds[1]['polls'] == 0 and ds[1].get('ended_by') is None and REQ in vm.disk and 'unlock_all' in vm.disk[REQ], ('V39 our own window polled', ds[1]['polls'])
    res, again, ds, code = r21_home(vm, frames=3, answers=[OK])
    assert ko(ds[1]['title']) == T_UNLOCK and REQ not in vm.disk
    counts['V39_own_windows_not_polled'] += 1
    # 3 a request file that cannot be deleted: served once, then the poll stops for the session (no endless re-trigger)
    vm = mk()
    vm.fail_delete = {REQ}
    res, again, ds, code = r21_home(vm, each=lambda v, f: hook_request(v, 'chart') if f == 0 else None, answers=[0])
    assert len(ds) == 2 and vm.vars.get('YoruKR.M.Off') == '1', ('V39 undeletable request', vm.vars.get('YoruKR.M.Off'))
    for _ in range(3):
        res, again, ds, code = r21_home(vm, frames=5, then=11)
        assert res == 11 and len(ds) == 1 and ds[0]['polls'] == 0 and ds[0]['armed'] == '', 'V39 the poll went on after an undeletable file'
    counts['V39_undeletable_stops_polling'] += 1
    # 4 the flag is armed exactly while the home menu waits (never left armed after it, on every exit path)
    for then in (11, 12, 13, 14, 15, PICK, -1):
        vm = mk()
        res, again, ds, code = r21_home(vm, frames=2, then=then)
        assert ds[0]['armed'] == '1' and vm.vars.get('YoruKR.M.Home', '') == '' and res == then, ('V39 arm / disarm', then)
    counts['V39_arm_disarm_paths'] = 7
    return dict(outside_home_dialogs=3, own_windows=1)


def r21_style_checks(counts):
    """V40 is checked on every r21 window by check_dialog (mod-window style, colour opt-in, lines <= 38, height, items)."""
    assert counts['V2_dialogs'] > 0
    counts['V40_r21_windows_checked'] = counts['V34_commands'] + counts['V38_results_shown']


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
            raise RuntimeError('defect could not be planted: no state test in KR_CCardPage (the calendar branch)')
        ops[hits[0] + 1] = ['PUSH', '-1']
        ops[hits[0] + 2] = ['NOTE']
        return ops
    return {'KR_CCardPage': mut}                # r22: KR_T18CardPage forwards here; the first state test = the calendar branch


DEFECTS = [
    # r15's nine (V4 plants into KR_T18MonthPage, where the month navigation lives since r16)
    # KR_CLegend = [chart legend, calendar legend, the compiler's dead 「return ""」]: the calendar legend is the last non-empty string
    ('V2 width: legend 40 chars', 'pages', op_replace('KR_CLegend', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) != '', lambda o: list(sp(proxy('가' * 40))), nth=-1)),
    ('V2 height: 12 rows a lane page', 'pages', op_replace('KR_T9LanePage', lambda o: o == ['.LOCALASSIGN', 'per 8'], lambda o: ['.LOCALASSIGN', 'per 12'])),
    ('V3 colour: unseen days white', 'calendar', op_replace('KR_T9ColorMark', lambda o: s_is(o, '‡'), lambda o: list(sp('†')))),
    ('V4 navigation: next skips a month', 'nav', seq_replace('KR_T18MonthPage', [('.LOCALREF', 'm'), ('PUSH', '1'), ('ADD',), ('RETURN',)], 1, ('PUSH', '2'))),
    ('V5 unwind flag not written', 'flow', op_replace('KR_T9Request', lambda o: s_is(o, 'Unwind'), lambda o: list(sp('Unwound')))),
    ('V6 settings context lost', 'flow', op_replace('KR_T9HomeConfig', lambda o: s_is(o, 'C'), lambda o: list(sp('X')))),
    ('V7 play allowed without context', 'flow', op_replace('KR_T9CanPlay', lambda o: o == ['PUSH', '0'], lambda o: ['PUSH', '1'], nth=1)),
    ('V8 fail-safe removed', 'flow', op_replace('KR_T9HomeMenuRun', lambda o: s_is(o, 'Playing'), lambda o: list(sp('PlayingX')))),
    ('V10 seen: this save shown as other save', 'seen', op_replace('KR_CState', lambda o: o == ['PUSH', '2'], lambda o: ['PUSH', '1'])),
    # r16's kept four VM defects (re-aimed at the r18 bodies)
    ('V11 bar: one cell too many', 'bars', seq_replace('KR_T18Bar', [('.LOCALREF', 'i'), ('.LOCALREF', 'f'), ('LT',)], 2, ('LTE',))),
    ('V3 missed shown as upcoming', 'calendar', op_replace('KR_T18DayState', lambda o: o == ['PUSH', '3'], lambda o: ['PUSH', '1'])),
    ('V11 summary total mismatch (one month left out of 전체)', 'summary', seq_replace('KR_T18SummaryTitle', [('.LOCALREF', 'x2'), ('PUSH', '10000'), ('DIV',)], 0, ('PUSH', '0'))),
    ('V12 one name tail removed (two lane rows collide)', 'rows', None),
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
    """「one name tail removed」: KR_T19CardTail returns "" for the first tailed card (its row collides with a sibling)."""
    k = next(k for k in range(200) if ko(vm.run('KR_T19CardTail', [k])))
    txt = vm.run('KR_T19CardTail', [k])
    return op_replace('KR_T19CardTail', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == txt, lambda o: list(sp(''))), k


def leaf_replace(fn, no, new_text):
    """replace the string a generated table returns for key `no` (the S_PUSH right after its `PUSH no; EQUALE; IFZ`)."""
    def mut(ops):
        # `if (no == N) return "…";` compiles to PUSH N / EQUALE / IFNZ a / JUMP b / a: S_PUSH "…" / RETURN (labels are not ops)
        hits = [i for i in range(len(ops) - 5) if ops[i] == ['PUSH', str(no)] and ops[i + 1] == ['EQUALE'] and ops[i + 2][0] == 'IFNZ'
                and ops[i + 3][0] == 'JUMP' and ops[i + 4][0] == 'S_PUSH']
        if len(hits) != 1:
            raise RuntimeError(('defect could not be planted: no table leaf', fn, no, len(hits)))
        ops[hits[0] + 4] = list(sp(new_text))
        return ops
    return {fn: mut}


def r19_defects(vm, X):
    """The four r19 defects: an E-number left, a duplicate name on one page, a wrong ordinal, an affinity text dropped."""
    ev = X['ev']
    no1 = min(ev)
    e_left = leaf_replace('KR_T19EvHead', no1, vm.run('KR_T19EvHead', [no1]) + proxy(' · ') + 'E%05d' % no1)
    ch = next(ch for ch in X['chips'] if KINDS[ch['kind']] == 'after' and len(ch['scenes']) >= 3)
    a, b = sorted(ch['scenes'])[:2]
    dup = leaf_replace('KR_T19EvShort', b, vm.run('KR_T19EvShort', [a]))
    wch = next(ch for ch in X['chips'] if KINDS[ch['kind']] == 'walk' and len(ch['scenes']) >= 3)
    last = sorted(wch['scenes'])[-1]
    tl = ko(vm.run('KR_T19EvShort', [last]))
    z = re.search(r'(\d+)번째$', tl)
    wrong = tl[:z.start()] + '%d번째' % (int(z.group(1)) + 1)
    ordinal = leaf_replace('KR_T19EvShort', last, proxy(wrong))
    no4 = 30157
    t4 = ko(vm.run('KR_T19WhenFix', [no4]))
    assert '이즈미 친밀도 50 미만' in t4, t4
    drop = leaf_replace('KR_T19WhenFix', no4, proxy(t4.replace(' · 이즈미 친밀도 50 미만', '')))
    return [('V21 one E-number left on a scene page (E%05d)' % no1, 'names_e', e_left),
            ('V22 two lines with the same name in one drawer list (%s: E%05d copies E%05d)' % (ch['id'], b, a), 'names_dup', dup),
            ('V23 a wrong ordinal in a walk drawer (E%05d: %s -> %s)' % (last, tl, wrong), 'names_rule', ordinal),
            ('V24 the affinity condition dropped from a card page (E%05d)' % no4, 'affinity', drop)]


def r20_defects():
    """r20: one remaining count wrong, a parts leak, the hovered person not brightened, a 0-row not left out."""
    return [('V27 one remaining count wrong (이달 남은 특훈 뒤 대화 counts 반한 뒤 instead of 초대)', 'r20_counts',
             seq_replace('KR_T20TrainLeft', [('.LOCALREF', 'k'), ('PUSH', '3'), ('EQUALE',)], 1, ('PUSH', '2'))),
            ('V31 parts leak (the label boxes are not released after the wait)', 'r20_partner',
             op_replace('KR_T20TrClear', lambda o: o == ['CALLHLL', 'PartsEngine Release 0'], lambda o: ['POP'], nth=1)),
            ('V31 the hovered person not brightened (no KR_T20TrMark after AppearStandChara)', 'r20_partner',
             op_replace('KR_T20TrAppear', lambda o: o == ['CALLFUNC', 'KR_T20TrMark'], lambda o: ['POP'])),
            ('V29 a partner row with 0 left in (the 0 test removed)', 'r20_text',
             seq_replace('KR_T20StText', [('.LOCALREF', 'k'), ('PUSH', '0'), ('LTE',)], 1, ('PUSH', '-1')))]


def r21_native_checks(mk, counts):
    """--native (r21): the r21 tour the native probe ran (증거/probe_r21.json, probe_modmenu_r21.py --r21) = the VM: every window
    title, the files after each run (bytes), the exits, the pending requests outside the home menu, the probe's own request bytes =
    the hook's format, the save slot and settings, the engine's own exit writes = the control run's."""
    doc = L.readj(L.EVID / 'probe_r21.json')
    man = L.readj(O / 'manifest.json')
    assert doc['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256'], 'probe_r21.json logged by another candidate'
    long_line = 'restore partial 1 files (from KR_reset_20260928_031500, previous kept in KR_before_restore_20260928_031501)'

    def vm_titles(cmd=None, result=None, answers=(OK,)):
        vm = mk()
        vm.disk.pop(REQ, None)

        def each(v, f):
            if f == 0:
                if result is not None:
                    hook_result(v, result + '\r\n')
                if cmd is not None:
                    hook_request(v, cmd)
        res, again, ds, code = r21_home(vm, each=each, answers=list(answers))
        return [ko(d['title']) for d in ds[1:]]
    want = {}
    for tag in ('CHART', 'BOTH_2', 'DURING_NOTICE', 'SERVED_AFTER_CHARWIN'):
        want[tag] = vm_titles('chart')[0]
    for tag in ('UNLOCK_ALL', 'UNLOCK_ALL_2', 'UNLOCK_ALL_3'):
        want[tag] = vm_titles('unlock_all')[0]
    for tag in ('UNLOCK_REVERT', 'DURING_SERVED_AT_HOME', 'B_UNLOCK_REVERT'):
        want[tag] = vm_titles('unlock_revert')[0]
    want['LAST_RESULT'] = vm_titles(result=long_line)[0]
    want['BOTH_1'] = vm_titles(result='reset ok KR_reset_20260928_031500', cmd='chart', answers=(OK, OK))[0]
    for tag in ('RESET_CONFIRM', 'RESET_CONFIRM_YES'):
        want[tag] = vm_titles('reset_all', answers=(NO,))[0]
    for tag in ('RESTORE_CONFIRM', 'B_RESTORE_CONFIRM_YES'):
        want[tag] = vm_titles('reset_restore', answers=(NO,))[0]
    seen = 0
    runs = {r['run']: r for r in doc['runs']}
    assert set(runs) == {'A', 'B'}, sorted(runs)
    for name, r in runs.items():
        assert r.get('exit_code') == 0 and not r.get('vm_error') and not r.get('message') and not r.get('timeout'), ('run', name, r.get('exit_code'), r.get('vm_error'), r.get('message'))
        assert r['log'][-1].startswith('ANSWER YES'), ('run %s did not end on 예' % name, r['log'][-1])
        b = r21_blocks_log(r['log'])
        for tag, text in b.items():
            if tag == 'CHARWIN':
                continue
            assert tag in want, ('an unexpected window in the native log', tag)
            assert text == want[tag], ('native window differs from the VM', tag, text, want[tag])
            seen += 1
        counts['R21N_windows_equal_vm'] += len([t for t in b if t != 'CHARWIN'])
    a, bb = runs['A'], runs['B']
    la, lb = a['log'], bb['log']
    # run A: the files after it, the stale-free state; run B: the flag read back after the restart, restore scheduled, reset.req gone
    assert a['bytes_after'].get('YoruKR_reset.marker') == 'reset' and a['menu_bytes_after'].get('reset.req') == 'reset' and 'restore.req' not in a['menu_bytes_after'], a['menu_bytes_after']
    assert a['bytes_after'].get('YoruKR_Chart.dat') == 'YoruKR.Chart.1\r\n1\r\n' and 'request.txt' not in a['menu_bytes_after'] and 'last_result.txt' not in a['menu_bytes_after']
    assert any(l.startswith('B START') and 'reset_req=1' in l and 'marker=1' in l and 'unlock=1' in l for l in lb), 'run B: the flag / files after the restart'
    assert bb['bytes_after'].get('YoruKR_reset.marker') == 'restore' and bb['menu_bytes_after'].get('restore.req') == 'restore' and 'reset.req' not in bb['menu_bytes_after'], bb['menu_bytes_after']
    assert bb['bytes_after'].get('YoruKR_Chart.dat') == 'YoruKR.Chart.1\r\n0\r\n'
    counts['R21N_files_after_runs'] = 2
    # the unknown command and the two pending cases
    assert any(l.startswith('UNKNOWN after 30 frames request=0') for l in la), 'unknown command not consumed'
    assert any(l.startswith('DURING own window after 60 frames request=1') for l in la), 'a request was consumed while our own window was open'
    assert any(l.startswith('OUTSIDE HOME character window after 60 frames head_is_ours=0 request=1') for l in la), 'a request was consumed outside the home menu'
    assert [t for t in r21_blocks_log(la) if t.startswith('BOTH')] == ['BOTH_1', 'BOTH_2'], 'result and request not in order'
    for tag in ('AFTER NO reset', 'AFTER NO restore'):
        row = next(l for l in la if l.startswith(tag))
        assert 'reset_req=0' in row and 'restore_req=0' in row and 'marker=0' in row, ('files after 아니요', row)
    counts['R21N_pending_outside_home'] = 2
    # the conventions logged by the probe
    game = next(l for l in la if l.startswith('PATH game='))[len('PATH game='):]
    save = next(l for l in la if l.startswith('PATH save='))[len('PATH save='):]
    assert game.endswith('\\') and Path(game.rstrip('\\')).resolve() == Path(doc['save_folder']).parent.resolve(), ('GetGameFolderPath', game)
    assert not save.endswith('\\') and Path(save).resolve() == Path(doc['save_folder']).resolve(), ('GetSaveFolderName', save)
    api = ' '.join(l for l in la if l.startswith('API '))
    for k in ('exist_abs_exe=1', 'exist_rel_exe=1', 'exist_save_afconfig=1', 'menu_folder_before=0', 'write_into_missing_folder=0',
              'create_folder=1 write=1 read=1 length=6 crlf=1', 'read_missing=0 text=unchanged delete_missing=0', 'delete=1 exist_after=0'):
        assert k in api, ('file API convention', k, api)
    vs = next(l for l in la if l.startswith('VSFILE '))
    assert 'in_save=1' in vs and 'in_game=0' in vs, vs
    vs_bytes = a['bytes_after'].get('YoruKR_ProbeVS.dat', '')
    assert vs_bytes.startswith('VSF\x00') and not vs_bytes.startswith('reset'), ('VSFile format', vs_bytes[:12])
    assert doc['sample_request_bytes'] == 'chart\r\n1\r\n2026-09-28 03:30:00\r\n', doc['sample_request_bytes']
    assert doc['relative_textfile_lands_in_game_folder'] is True
    counts['R21N_conventions'] = 1
    # poll cost and frame time
    cost = next(l for l in la if l.startswith('COST '))
    z = dict(kv.split('=') for kv in cost.split()[1:])
    fr = [int(re.search(r'ms=(\d+)', l).group(1)) for l in la if l.startswith('FRAMES ')]
    assert len(fr) == 2
    perf = dict(calls=int(z['calls']), pending_ms_per_call=int(z['pending_ms']) / int(z['calls']), tick_armed_ms_per_call=int(z['tick_armed_ms']) / int(z['calls']),
                existfile_hit_ms_per_call=int(z['existfile_hit_ms']) / int(z['calls']), sysvar_get_ms_per_call=int(z['sysvar_get_ms']) / int(z['calls']),
                frame_ms_armed=fr[0] / 180, frame_ms_disarmed=fr[1] / 180)
    assert perf['tick_armed_ms_per_call'] < 1.0, ('the armed tick costs a millisecond or more per frame', perf)
    # the save slot and settings untouched; the engine's own exit writes are the control run's
    assert doc['save_slot_unchanged'] is True
    keep = doc['settings_unchanged']
    for n in ('AFConfig.asd', 'MouseCursorSetting.sav', 'ShowDPSetting.sav', '3DConfig.vsf', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup'):
        assert keep.get(n) is True, ('a setting file changed', n)
    ee = doc['engine_exit_writes']
    assert ee['same_set'] and ee['control_exit_code'] == 0, ('the tour changed more than the engine exit does', ee)
    assert doc['user_save_folder_unchanged'] and not doc['c_drive_alicesoft_changes']
    counts['R21N_runs'] = len(runs)
    return dict(windows_equal=seen, perf=perf, engine_exit_writes=ee['control_changed'], shots=[s for r in doc['runs'] for s in r['shots_taken']])


def r21_blocks_log(log):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'TITLE (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            out[z.group(1)] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    return out


def r21_defects():
    """r21's five: the request not deleted, the flag not saved, a .req without the marker, an exit after 아니요, polling outside
    the home menu."""
    return [('V34 request.txt not deleted after it was served (KR_MTake\'s DeleteFile skipped)', 'r21_requests',
             op_replace('KR_MTake', lambda o: o == ['CALLHLL', 'FileOperation DeleteFile 0'], lambda o: ['VM_POP_PUSH1'])),
            ('V35 the unlock flag not saved (the write skipped, the read-back kept)', 'r21_flag',
             op_replace('KR_MSetUnlock', lambda o: o == ['CALLHLL', 'TextFile WriteAll 0'], lambda o: ['VM_POP2_PUSH1'])),
            ('V36 a .req written without the marker (the marker write skipped)', 'r21_reset',
             op_replace('KR_MSchedule', lambda o: o == ['CALLFUNC', 'KR_MWrite'], lambda o: ['VM_POP2_PUSH1'], nth=0)),
            ('V36 아니요 still schedules and exits (the answer test inverted)', 'r21_reset',
             op_replace('KR_MReset', lambda o: o == ['NOT'], lambda o: ['VM_NOP'], nth=0)),
            ('V39 polling outside the home menu (the arm test removed from KR_MTick)', 'r21_scope',
             op_replace('KR_MTick', lambda o: o == ['S_EQUALE'], lambda o: ['VM_POP2_PUSH1'], nth=0))]


def leaf_int(fn, key, new_value):
    """replace the int a generated table returns for `key` (`if (k == key) return v;` = PUSH key / EQUALE / IFNZ / JUMP / PUSH v)."""
    def mut(ops):
        hits = [i for i in range(len(ops) - 5) if ops[i] == ['PUSH', str(key)] and ops[i + 1] == ['EQUALE'] and ops[i + 2][0] == 'IFNZ'
                and ops[i + 3][0] == 'JUMP' and ops[i + 4][0] == 'PUSH']
        if len(hits) != 1:
            raise RuntimeError(('defect could not be planted: no int leaf', fn, key, len(hits)))
        ops[hits[0] + 4] = ['PUSH', str(new_value)]
        return ops
    return {fn: mut}


def r22_defects(C):
    """r22's eight: a locked scene replayable, 「전체 개방」 ignored, the chart exception leaking into the calendar, a parts leak,
    a wrong order, a thumbnail on a cell without CG, the E number missing, a condition missing."""
    first = C['first'][0]
    a, b = C['rows'][first], C['rows'][first + 1]
    swap = leaf_int('KR_CCellRef', 0, b['ref'])
    ci = next(i for i, r in enumerate(C['rows']) if r['cond'])
    return [('V44 a locked scene replayable (KR_CCanPlay skips the lock)', 'r22_flow',
             op_replace('KR_CCanPlay', lambda o: o == ['CALLFUNC', 'KR_COpen'], lambda o: ['VM_POP_PUSH1'])),
            ('V43 「전체 개방」 ignored (the flag read as 0)', 'r22_pages',
             op_replace('KR_CUnlockAll', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == '1', lambda o: list(sp('X')))),
            ('V45 the chart exception applied in the calendar (KR_CActive without the chart-root test)', 'r22_confine',
             op_replace('KR_CActive', lambda o: o == ['CALLHLL', 'PartsEngine IsExist 0'], lambda o: ['VM_POP_PUSH1'])),
            ('V46 parts leak (KR_CClear stops at part 100)', 'r22_flow',
             op_replace('KR_CClear', lambda o: o == ['.LOCALASSIGN', 'i 111'], lambda o: ['.LOCALASSIGN', 'i 100'])),
            ('V41 wrong order (the first two cells of 4월 swapped)', 'r22_tables', swap),
            ('V42 a thumbnail on cells without CG (KR_CThumb default)', 'r22_pages',
             # the first 「""」 = the tree's default return (the last one is the compiler's dead tail after it)
             op_replace('KR_CThumb', lambda o: o[0] == 'S_PUSH' and json.loads(o[1]) == '', lambda o: list(sp('シス／ＣＧモード／サムネイル／CG1001')), nth=0)),
            ('V42 the E number missing from a cell', 'r22_pages',
             op_replace('KR_C24DrawCell', lambda o: o == ['CALLFUNC', 'KR_T9EvNo'], lambda o: ['VM_POP_PUSHS'])),     # r24: the cells are KR_C24DrawCell's
            ('V41 a condition missing (cell %d)' % ci, 'r22_tables', leaf_replace('KR_CCellCond', ci, ''))]


def chart_flow_checks_m(cand, nm, X, C, mutate):
    global chart_vm
    orig = chart_vm
    try:
        chart_vm = lambda c, n, x, mutate_=None, alias=None: orig(c, n, x, mutate=mutate)
        return chart_flow_checks(cand, nm, X, C, collections.Counter())
    finally:
        chart_vm = orig


def chart_confine_checks_m(cand, nm, X, C, mutate):
    """V45 with a planted defect in the r22 candidate's VM (the r21 reference VM is left as it is)."""
    global chart_vm
    orig = chart_vm
    r21 = L.R21 / 'candidate' / 'NightRemaster.ain'
    try:
        chart_vm = lambda c, n, x, mutate_=None, alias=None: orig(c, n, x, mutate=(None if c == r21 else mutate))
        return chart_confine_checks(cand, nm, X, C, collections.Counter())
    finally:
        chart_vm = orig


def cells_text(vm):
    """the probe's CELLS block format (KR_P22Cells, r24 form: + legend, the three top buttons, each thumbnail slot's CG name /
    size / pass-through (CG or empty frame: the screenshot pixels, r24_native_checks), the box height) from the VM's parts."""
    t = 'OURS %d ALL %s OPEN %s' % (len(vm.ours22()), vm.vars.get('YoruKR.C.All', ''), vm.vars.get('YoruKR.C.Open', ''))
    t += '\nHEAD ' + ko(vm.parts[CPART(1)]['text'])
    t += '\nPAGE ' + ko(vm.parts[CPART(3)]['text'])
    t += '\nLEGEND ' + ko(vm.parts[CPART(2)]['text'])

    def btn(k):
        n = CPART(k)
        if n not in vm.parts:
            return '-'
        c = vm.parts[n]['construct'][0]
        lab = ko(vm.parts[n + 1]['text']) if n + 1 in vm.parts else ''
        return '%s %dx%d click=%d' % (lab, c[1], c[2], vm.parts[n].get('click', 0))
    t += '\nBTN ' + btn(38) + ' | ' + btn(36) + ' | ' + btn(30)
    for s_ in range(12):
        box = CPART(40 + s_ * 6)
        if box not in vm.parts:
            t += '\nCELL %d -' % s_
            continue
        g = lambda j: ko(vm.parts[box + j]['text']) if box + j in vm.parts else ''
        th = vm.parts.get(box + 1)
        # the slot's size: an empty frame = its construction size; a CG part = the CG mode thumbnail (120 x 90, every one: r22 event_cg)
        wh = (th['construct'][0][1], th['construct'][0][2]) if th is not None and 'construct' in th else (120, 90)
        ts = '0' if th is None else '1 wh=%dx%d pass=%d' % (wh[0], wh[1], th.get('pass', 0))
        t += '\nCELL %d h=%d thumb=%s name=%s id=%s cond=%s' % (s_, vm.parts[box]['construct'][0][2], ts, g(2), g(3), g(4))
    return t


def native_state(vm, C, line):
    """GLOBAL <tag> ALL=<0|1> i i i ... -> the VM's read marks / recollection cells so that exactly those cells' events are open."""
    parts = line.split()
    all_ = parts[2] == 'ALL=1'
    opened = {int(x) for x in parts[3:]}
    vm.flags, vm.mem_enabled = set(), set()
    for i in opened:
        no = C['rows'][i]['no']
        m = vm.msg_of.get(no, -1)
        if m >= 0:
            vm.flags.add(m)
        else:
            c = C['memcell'].get(no, 0)
            assert c > 0, ('a globally open event without a first message and without a recollection cell', no)
            vm.mem_enabled.add((c // 100 - 1, c % 100 - 1))
    got = {i for i in range(len(C['rows'])) if cstate(vm, C, C['rows'][i]['no']) == 1}
    assert got == opened, ('native global state cannot be reproduced', sorted(got ^ opened)[:5])
    return all_


def r22_native_checks(cand, nm, X, C, counts):
    doc = L.readj(L.EVID / 'probe_r22.json')
    man = L.readj(O / 'manifest.json')
    cs = man['files']['NightRemaster.ain']['sha256']
    out = {}
    # ---- the title tour
    t = doc['title']
    assert t.get('candidate_sha256') == cs, 'probe_r22.json title tour logged by another candidate'
    assert t.get('exit_code') == 0 and not t.get('vm_error') and not t.get('message') and not t.get('timeout') and t['log'][-1] == 'END', \
        ('title tour', t.get('exit_code'), t.get('vm_error'), t.get('message'), t['log'][-3:])
    log = t['log']
    glob = {l.split()[1]: l for l in log if l.startswith('GLOBAL ')}
    tgt = next(l for l in log if l.startswith('TARGET '))
    tt, tp = int(re.search(r'tab=(\d+)', tgt).group(1)), int(re.search(r'page=(\d+)', tgt).group(1))
    plan = {'TAB0 P1': ('chart1', 0, 0), 'TAB6 P1': ('chart1', 6, 0), 'TAB8 P1': ('chart1', 8, 0), 'TARGET LOCKED': ('chart1', tt, tp),
            'TARGET AFTER NOTICE': ('chart1', tt, tp), 'TARGET UNLOCKED': ('chart2', tt, tp), 'TARGET REVERTED': ('chart3', tt, tp)}
    blocks_ = r22_blocks(log, 'CELLS')
    assert set(blocks_) == set(plan), sorted(blocks_)
    for tag, (g, tab, page) in plan.items():
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, glob[g])
        vm.parts = {}
        chart_open(vm, all_)
        vm.run('KR_CDraw', [tab, page])
        want = cells_text(vm)
        got = blocks_[tag][0]
        assert got == want, ('native chart page differs from the VM', tag, [(a, b) for a, b in zip(got.split('\n'), want.split('\n')) if a != b][:3])
        counts['R22N_pages_equal_vm'] += 1
    # the flow: locked notice, unlock, replay (memory mode) and back on the title, revert
    assert any(l.startswith('REPLAY first message memory=1') and 'ours=0' in l for l in log), 'title tour: the replay did not run in memory mode with the chart closed'
    ret = next(l for l in log if l.startswith('RETURNED to the title'))
    assert 'ours=0' in ret and 'open= ' in ret and 'play= ' in ret, ret
    dl = r22_blocks(log, 'DIALOG')
    assert dl.get('chart1') == [T_LOCKED], ('native locked-cell notice', dl.get('chart1'))
    assert dl.get('unlock') == ['〓모드 메뉴\n†전체 개방: 안 본 이벤트도 열람·재생됩니다'] and dl.get('revert') == [T_REVERT], (dl.get('unlock'), dl.get('revert'))
    # reset_all on the title: the r21 confirm window, 아니요 -> no marker, no .req, the request consumed, no chart parts
    assert dl.get('reset_no') == [T_RESET], ('native title reset confirm', dl.get('reset_no'))
    rn = next((l for l in log if l.startswith('RESET NO ')), '')
    assert rn == 'RESET NO marker=0 reset_req=0 request=0 ours=0', ('native title reset 아니요', rn)
    counts['R22N_title_reset_no'] = 1
    a_no = int(re.search(r' A=(\d+)', tgt).group(1))
    b_no = int(re.search(r' B=(\d+)', tgt).group(1))
    vm = chart_vm(cand, nm, X)
    native_state(vm, C, glob['chart2'])
    want_page = '〓' + ko(vm.run('KR_T19EvHead', [a_no])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [a_no])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [a_no])) \
        + '\n' + C_STATE['all'] + '\n' + C_PLAY_NOTE
    assert dl.get('chart2') == [want_page], ('native scene page (chart branch)', dl.get('chart2'), want_page)
    ia = next(i for i, r in enumerate(C['rows']) if r['no'] == a_no and not r['card'])
    ib = next(i for i, r in enumerate(C['rows']) if r['no'] == b_no and not r['card'])
    g1, g3 = set(glob['chart1'].split()[3:]), set(glob['chart3'].split()[3:])
    assert str(ia) not in g1 and str(ib) not in g1, 'the target cells were open before the unlock'
    assert str(ia) in g3 and str(ib) not in g3, ('after the revert: the replayed scene keeps its read mark, the other locks again', str(ia) in g3, str(ib) in g3)
    counts['R22N_title_tour'] = 1
    # pixels: the title after the replay = the title after the first chart (the same title loop state; the shot before the first
    # chart has the title's own hover highlight, see the report)
    shots = L.EVID / 'probe'
    px = diff_png(shots / 'chart_title_after_chart1.png', shots / 'chart_title_after_replay.png') if (shots / 'chart_title_after_chart1.png').exists() else None
    px_rn = diff_png(shots / 'chart_title_after_chart1.png', shots / 'chart_title_after_reset_no.png') if (shots / 'chart_title_after_reset_no.png').exists() else None
    out['title'] = dict(pages=len(plan), replayed=a_no, relocked=b_no, title_after_chart_vs_after_replay_px=px, title_after_chart_vs_after_reset_no_px=px_rn,
                        seconds=t.get('seconds'))
    assert px == 0, ('title pixels after the replay differ from the title after closing the chart', px)
    # ---- the home tour
    h = doc.get('home')
    if h:
        assert h.get('candidate_sha256') == cs and h.get('exit_code') == 0 and h['log'][-1] == 'END', ('home tour', h.get('exit_code'), h['log'][-3:])
        hl = h['log']
        assert any(l.startswith('REPLAY first message memory=1') and 'ours=0' in l for l in hl), 'home tour: no memory-mode replay'
        assert any(l.startswith('RETURNED to the home menu') and 'ours=0' in l for l in hl)
        hb = r22_blocks(hl, 'CELLS')['HOME OPEN'][0]
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, next(l for l in hl if l.startswith('GLOBAL home')))
        vm.parts = {}
        chart_open(vm, all_)
        month = int(re.search(r'HEAD .*?　(\d+)월　', hb).group(1))
        vm.run('KR_CDraw', [month - 4, 0])
        assert hb == cells_text(vm), ('native home chart page differs from the VM', [(a, b) for a, b in zip(hb.split('\n'), cells_text(vm).split('\n')) if a != b][:3])
        pxh = diff_png(shots / 'chart_home_before.png', shots / 'chart_home_after.png')
        out['home'] = dict(home_before_vs_after_px=pxh, seconds=h.get('seconds'))
        assert pxh == 0, ('home pixels after the replay differ', pxh)
        counts['R22N_home_tour'] = 1
    # ---- the per-kind replays
    k = L.readj(L.EVID / 'replay_kinds.json')
    assert k['candidate_sha256'] == cs and all(e.get('candidate_sha256') == cs for e in k['events'].values()), 'replay_kinds.json from another candidate'
    out['kinds'] = k['verdicts']
    counts['R22N_kinds'] = len(k['events'])
    return out


def r22_blocks(log, kind):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'%s (.*) <<<$' % kind, log[i])
        if z:
            j = log.index('>>>', i)
            out.setdefault(z.group(1), []).append('\n'.join(log[i + 1:j]))
            i = j
        i += 1
    return out


def diff_png(a, b):
    from PIL import Image, ImageChops
    x, y = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    if x.size != y.size:
        return -1
    bb = ImageChops.difference(x, y).getbbox()
    if bb is None:
        return 0
    d = ImageChops.difference(x, y).crop(bb)
    return sum(1 for q in d.getdata() if q != (0, 0, 0))


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
    """「one old-form drawer row left」: the 회상 · 그 밖 page calls r15's KR_T9ChipRow body (the r15 candidate AIN, read only:
    「이름 n (본 것 k)」; in the base the r15 index holds r18's forwarder)."""
    d = L.WORK / 'vm' / 'r15'
    d.mkdir(parents=True, exist_ok=True)
    path = d / 'KR_T9ChipRow_r15.jam'
    if not path.exists():
        assert L.sha(L.R15 / 'candidate' / 'NightRemaster.ain') == L.R15_AIN_SHA
        L.cmd('ain', 'dump', '--function', 'KR_T9ChipRow', '-o', path, L.R15 / 'candidate' / 'NightRemaster.ain')
    entry = m['functions'][L.fid_of(m, 'KR_T9ChipRow')]
    return {'KR_T9ChipRow@r15': (entry, path)}, op_replace('KR_T18MemPage', lambda o: o == ['CALLFUNC', 'KR_T9ChipRow'], lambda o: ['CALLFUNC', 'KR_T9ChipRow@r15'])



# ============================================================== r22: the chart screen (V41-V48)
CROOT = 2026092200
CPART = lambda i: CROOT + i
C_TABS = ['4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '회상', '그 밖']
C_GOLD, C_SKY, C_GRAY, C_WHITE = 'r=255 g=214 b=110', 'r=130 g=200 b=255', 'r=150 g=150 b=158', 'r=240 g=240 b=245'
C_NAME_THUMB, C_NAME_SMALL, C_WHEN_THUMB, C_IDWHEN_SMALL, C_COND = 15.5, 15.5, 9.0, 17.5, 18.5
C_NOTE = '재생 불가(게임 안에서만)'
T_LOCKED = '〓이벤트 플로우 차트\n†아직 읽지 않은 장면입니다 · 본 뒤에 열립니다\n†모드 → 전체 개방으로 모든 칸을 열 수 있습니다'
C_PLAY_NOTE = '〓회상 모드처럼 재생합니다 · 진행 상태는 바뀌지 않습니다'
C_NOPLAY_NOTE = '†재생 불가(게임 안에서만)'
C_STATE = {1: '¶△ 읽은 장면입니다 (게임 전역 기록)', 'all': '‡● 안 읽은 장면 · 전체 개방으로 열렸습니다', 0: '‡● 안 읽은 장면입니다 · 본 뒤에 열립니다'}
C_LEGEND = '‡●†안 읽음　¶△†읽음(게임 전역 기록)'
C_CODE = 2026092802
TITLE_ACT_ROOT = None


def tint(s, rgb):
    return '' if s == '' else '${font ' + rgb + '}' + s + '${/font}'


def cunits(t):
    return sum(0.5 if ord(ch) < 0x80 else 1.0 for ch in t)


def ccut(t, budget):
    """(verifier's own) cut a text to `budget` units, 「…」 at the end."""
    if cunits(t) <= budget:
        return t
    out = ''
    for ch in t:
        if cunits(out) + cunits(ch) + 1 > budget:
            break
        out += ch
    return out.rstrip(' ·,') + '…'


def cwrap(tokens, budget, lines):
    """(verifier's own) tokens joined by ' · ' into <= `lines` lines of <= budget units; a token wider than a line is cut; tokens
    left over are dropped and the last line ends in ' …'."""
    out, cur, i = [], '', 0
    while i < len(tokens):
        t = tokens[i]
        trial = t if not cur else cur + ' · ' + t
        if cunits(trial) <= budget:
            cur = trial
            i += 1
        elif not cur:
            cur = ccut(t, budget)
            i += 1
        else:
            out.append(cur)
            cur = ''
            if len(out) == lines:
                break
    if cur and len(out) < lines:
        out.append(cur)
    if i < len(tokens):
        last = out[-1]
        while last and cunits(last + ' …') > budget:
            last = last[:-1]
        out[-1] = last.rstrip(' ·,') + ' …'
    return out


def when_toks(text):
    t = text.replace(WHEN_CONT, ' · ').replace('\n', ' · ')
    t = re.sub(r'[†‡¶〓]', '', t)
    return [x.strip() for x in re.split(r' · | / ', t) if x.strip()]


def chart_memcells():
    """recollection cell (page * 100 + slot) per event, from graph/memory.json and the chain links in graph/schedule.json (the
    verifier's own walk): the cell's replay event, the replay events chained under it, the event the cell needs."""
    mem = json.loads((L.FLOW / 'graph' / 'memory.json').read_text('utf8'))['entries']
    sch = {e['id']: e for e in json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))['events']}
    out = {}
    for e in mem:
        out[e['play']] = e['page'] * 100 + e['id']
    todo = list(out)
    while todo:
        n = todo.pop()
        for t in sch[n].get('chains_to') or []:
            if sch[t]['category'] == 'memory_replay' and t not in out:
                out[t] = out[n]
                todo.append(t)
    for e in mem:
        out.setdefault(e['need'], e['page'] * 100 + e['id'])
    return out


def chart_kinds(X):
    """replay kind of every event (the verifier's own classification) and the choice / battle flags."""
    kind = {}
    for c in X['cards']:
        for i, no in enumerate(c['stages']):
            k = 'dungeon' if c['lane'] == 8 else ('dated' if c['day'] > 0 else 'undated')
            kind[no] = ('stage_' + k) if i else k
    names = {'prio': 'pool_talk', 'after': 'pool_talk', 'turned': 'pool_talk', 'invite': 'pool_invite', 'walk': 'pool_walk', 'etc': 'system',
             'mem': 'memory', 'unused': 'unused'}
    for ch in X['chips']:
        for no in ch['scenes']:
            kind[no] = names[KINDS[ch['kind']]]
    flags = {}
    for no, e in X['sch'].items():
        f = []
        if e.get('has_choice'):
            f.append('choice')
        if (e.get('effects') or {}).get('event_battle'):
            f.append('battle')
        flags[no] = f
    return kind, flags


def chart_expect(X, vm):
    """The chart's cells, recomputed from the chart data and the base's r19 name functions (not from build_chart_r22)."""
    cards, chips = X['cards'], X['chips']
    cg = json.loads((L.FLOW / 'graph' / 'event_cg.json').read_text('utf8'))
    thumb = {int(k): v['thumb'] for k, v in cg['events'].items() if v['thumb']}
    kinds_doc = L.readj(L.R22 / '증거' / 'replay_kinds.json')                    # what the r22 build baked into KR_CNoPlay
    if (L.EVID / 'replay_kinds.json').exists():                                       # r23's own per-kind run on this candidate
        mine = L.readj(L.EVID / 'replay_kinds.json')
        assert mine.get('verdicts') == kinds_doc.get('verdicts'), ('the per-kind replay verdicts differ on the r23 candidate', mine.get('verdicts'))
    verdict = kinds_doc.get('verdicts', {})
    kind, flags = chart_kinds(X)
    noplay = {no: int(any(verdict.get(x) == 'fail' for x in [kind[no]] + flags[no])) for no in kind}
    tabs = []
    for t in range(10):
        cells = []
        if t <= 7:
            m = t + 4
            ks = [k for k, c in enumerate(cards) if c['month'] == m]
            dated = sorted((k for k in ks if cards[k]['day'] > 0 and cards[k]['lane'] != 8), key=lambda k: (cards[k]['day'], SLOT_RANK[cards[k]['slot']], cards[k]['lane'], k))
            undated = sorted((k for k in ks if cards[k]['day'] == 0 and cards[k]['lane'] != 8), key=lambda k: (SLOT_RANK[cards[k]['slot']], cards[k]['lane'], k))
            dungeon = sorted((k for k in ks if cards[k]['lane'] == 8), key=lambda k: (cards[k]['day'] or 99, SLOT_RANK[cards[k]['slot']], k))
            cells += [('card', k) for k in dated + undated + dungeon]
            mine = sorted((i for i, ch in enumerate(chips) if ch['month'] == m), key=lambda i: (chips[i]['lane'], chips[i]['kind'], i))
        else:
            mine = sorted((i for i, ch in enumerate(chips) if ch['month'] == 12 and ((9 <= ch['lane'] <= 15) if t == 8 else ch['lane'] >= 16)),
                          key=lambda i: (chips[i]['lane'], i))
        for i in mine:
            ch = chips[i]
            sc = list(ch['scenes']) if KINDS[ch['kind']] == 'mem' else sorted(ch['scenes'])
            cells += [('scene', no) for no in sc]
        tabs.append(cells)
    rows = []
    for t, cells in enumerate(tabs):
        for kc, x in cells:
            if kc == 'card':
                c = cards[x]
                no = c['entry']
                when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
                if c['slot']:
                    when += ' ' + SLOT_KR[c['slot']]
                toks = ko(vm.run('KR_T19CardHead', [x])).split(' · ')
                assert toks[0] == when, ('V41 a card head does not start with its date', x, toks[0], when)
                name_toks = toks[1:]
                cc = ko(vm.run('KR_T19CardCond', [x]))
                cond_toks = cc.split(' · ') if cc else []
                ref = 100000 + x
            else:
                no = x
                toks = ko(vm.run('KR_T19EvHead', [no])).split(' · ')
                when = ''
                if re.fullmatch(r'\d{1,2}월', toks[0]):
                    when = toks[0]
                    toks = toks[1:]
                if toks[:2] == ['회상', '그 밖']:
                    toks = toks[2:]
                name_toks = toks
                cond_toks = when_toks(ko(vm.run('KR_T19EvWhen', [no])))
                ref = no
            th = thumb.get(no, '')
            if th:
                name = ccut(' · '.join(name_toks), C_NAME_THUMB)
                w = ccut(when, C_WHEN_THUMB)
            else:
                name = '\n'.join(cwrap(name_toks, C_NAME_SMALL, 2))
                w = when
            cl = cwrap(cond_toks, C_COND, 2) if cond_toks else []
            if noplay[no]:
                cl = (cl[:1] if cl else []) + [C_NOTE]
            rows.append(dict(tab=t, ref=ref, no=no, card=kc == 'card', name=name, when=w, cond='\n'.join(cl), thumb=th, noplay=noplay[no],
                             kind=kind[no]))
    first = []
    i = 0
    for cells in tabs:
        first.append(i)
        i += len(cells)
    return dict(rows=rows, first=first + [len(rows)], noplay=noplay, kind=kind, flags=flags, memcell=chart_memcells(), thumb=thumb)


def chart_vm(cand, nm, X, mutate=None, alias=None):
    v = VM(cand, nm, mutate=mutate, alias=alias)
    v.today = (6, 13)
    v.msg_of = {no: (e['m0'] if e['m0'] is not None else -1) for no, e in X['ev'].items()}
    return v


def cstate(vm, C, no):
    """global read state the chart must show: the first message's read mark or the recollection unlock."""
    m = vm.msg_of.get(no, -1)
    if m >= 0 and m in vm.flags:
        return 1
    c = C['memcell'].get(no, 0)
    return int(c > 0 and (c // 100 - 1, c % 100 - 1) in vm.mem_enabled)


def copen(vm, C, no, all_):
    return all_ or cstate(vm, C, no) == 1


def chart_table_checks(vm, X, C, counts):
    """V41: the tables the chart runs on = the verifier's own recomputation."""
    rows = C['rows']
    for t in range(10):
        assert vm.run('KR_CTabFirst', [t]) == C['first'][t] and vm.run('KR_CTabEnd', [t]) == C['first'][t + 1], ('V41 tab range', t)
    for i, r in enumerate(rows):
        assert vm.run('KR_CCellRef', [i]) == r['ref'], ('V41 cell order', i, r['tab'], vm.run('KR_CCellRef', [i]), r['ref'])
        assert vm.run('KR_CCellEv', [i]) == r['no'], ('V41 cell event', i)
        assert ko(vm.run('KR_CCellName', [i])) == r['name'], ('V41 cell name', i, ko(vm.run('KR_CCellName', [i])), r['name'])
        assert ko(vm.run('KR_CCellWhen', [i])) == r['when'], ('V41 cell when', i, ko(vm.run('KR_CCellWhen', [i])), r['when'])
        assert ko(vm.run('KR_CCellCond', [i])) == r['cond'], ('V41 cell condition', i, ko(vm.run('KR_CCellCond', [i])), r['cond'])
        counts['V41_cells'] += 1
    seen = collections.Counter(r['no'] if not r['card'] else ('card', r['ref']) for r in rows)
    assert max(seen.values()) == 1, 'V41 a cell twice'
    stages = sum(len(c['stages']) for c in X['cards'])
    assert len(rows) == len(X['cards']) + sum(len(ch['scenes']) for ch in X['chips']) and stages + sum(len(ch['scenes']) for ch in X['chips']) == TOTAL_EVENTS
    for no in X['ev']:
        assert ko(vm.run('KR_CThumb', [no])) == C['thumb'].get(no, ''), ('V41 thumbnail', no)
        assert vm.run('KR_CMemCell', [no]) == C['memcell'].get(no, 0), ('V41 recollection cell', no, vm.run('KR_CMemCell', [no]), C['memcell'].get(no, 0))
        assert vm.run('KR_CNoPlay', [no]) == C['noplay'][no], ('V41 not-playable table', no)
        assert vm.run('KR_T9EvMsg', [no]) == vm.msg_of[no], ('V41 first message', no)
        counts['V41_events'] += 1
    for t in range(10):
        assert ko(vm.run('KR_CTabName', [t])) == C_TABS[t]
    counts['V41_thumbnail_cells'] = sum(1 for r in rows if r['thumb'])
    counts['V41_small_cells'] = sum(1 for r in rows if not r['thumb'])
    counts['V41_per_tab'] = [C['first'][t + 1] - C['first'][t] for t in range(10)]
    counts['V41_not_playable_events'] = sum(C['noplay'].values())
    return dict(cells=len(rows), per_tab=counts['V41_per_tab'], thumbnails=counts['V41_thumbnail_cells'])


def cell_parts(vm, s):
    box = CPART(40 + s * 6)
    return [vm.parts.get(box + j) for j in range(5)]


def expect_cell(vm, C, i, all_):
    """r24: a locked cell shows the open cell's texts (grey) at the same places; a thumbnail event keeps the thumbnail cell's shape
    with an empty frame where the open cell shows the CG."""
    r = C['rows'][i]
    no = r['no']
    op = copen(vm, C, no, all_)
    st = cstate(vm, C, no)
    th = r['thumb']
    mark = tint('△', C_GRAY) if st == 1 else tint('●', C_SKY)
    ev = 'E%05d' % no
    if op:
        idl, when, name = mark + ' ' + ev, r['when'], tint(r['name'], C_WHITE)
    else:
        idl, when, name = tint('● ' + ev, C_GRAY), tint(r['when'], C_GRAY), tint(r['name'], C_GRAY)
    idtext = idl + ('\n' + when if th else '　' + when)
    # the box border: open = sky, locked = grey (r22 colours); the cell just replayed (YoruKR.C.Last, r24 resume) = gold
    border = (120, 170, 255) if op else (90, 90, 104)
    if vm.vars.get('YoruKR.C.Last', '') == str(i):
        border = (255, 214, 110)
    return dict(open=op, thumb=th, cg=th if op else '', frame=bool(th) and not op, id=idtext, name=name,
                cond=tint(r['cond'], C_GRAY) if r['cond'] else None, h=172 if th else 118, border=border)


def f32(v):
    return struct.unpack('<f', struct.pack('<i', v))[0] if isinstance(v, int) else float(v)


def check_page(vm, C, t, p, all_, counts, strict=True):
    """V42 / V43 / V46: the parts of one drawn page."""
    first, end = C['first'][t], C['first'][t + 1]
    n = end - first
    pages = max(1, (n + 11) // 12)
    opened = sum(1 for i in range(first, end) if copen(vm, C, C['rows'][i]['no'], all_))
    head = tint('이벤트 플로우 차트', C_GOLD) + '　' + C_TABS[t] + '　' + tint('%d/%d' % (opened, n), C_SKY) + ' 열림'
    if all_:
        head += '　' + tint('전체 개방', C_GOLD)
    got_head = ko(vm.parts[CPART(1)]['text'])
    assert got_head == head, ('V42 header', t, p, got_head, head)
    assert ko(vm.parts[CPART(3)]['text']) == '%d / %d쪽' % (p + 1, pages), ('V42 page line', t, p)
    assert ko(vm.parts[CPART(2)]['text']) == C_LEGEND24, ('V42 legend (r24)', ko(vm.parts[CPART(2)]['text']))
    assert vm.parts[CROOT]['show'] == 1 and vm.parts[CROOT].get('z') == 5000, ('V42 root', vm.parts[CROOT].get('z'))
    for b in (30, 32, 34):
        assert vm.parts[CPART(b)].get('click') == 1, ('V42 button not clickable', b)
    close = vm.parts[CPART(30)]
    for b, label, x in R24_BUTTONS:
        bx, lb = vm.parts.get(CPART(b)), vm.parts.get(CPART(b + 1))
        assert bx is not None and bx.get('click') == 1 and bx.get('parent') == CROOT and bx.get('show') == 1 \
            and (f32(bx['pos'][0]), f32(bx['pos'][1])) == (x, 12.0), ('V57 button part', b, bx)
        assert bx['construct'] == close['construct'] and bx.get('z') == close.get('z'), ('V57 a button unlike 닫기 (size / colours / z)', b)
        assert lb is not None and ko(lb['text']) == label and lb.get('parent') == CPART(b) and lb.get('pass') == 1, ('V57 button label', b)
        counts['V57_buttons_drawn'] += 1
    for tt in range(10):
        bx = vm.parts[CPART(10 + tt)]
        assert bx.get('click') == 1, ('V42 tab not clickable', tt)
        label = ko(vm.parts[CPART(20 + tt)]['text'])
        assert label == (tint(C_TABS[tt], C_GOLD) if tt == t else C_TABS[tt]), ('V42 tab label', tt, label)
    want_parts = 1 + 3 + 3 * 2 + 10 * 2 + 2 * 2              # root, header / legend / page, 3 buttons x 2, 10 tabs x 2, r24's 2 buttons x 2
    for s in range(12):
        i = first + p * 12 + s
        box, th, nmp, idp, cdp = cell_parts(vm, s)
        if i >= end:
            assert box is None and th is None and nmp is None and idp is None and cdp is None, ('V46 a part left in an empty slot', t, p, s)
            continue
        e = expect_cell(vm, C, i, all_)
        assert box is not None and box.get('click') == 1 and box['construct'][0] == ('create', 301, e['h']), ('V42 cell box', t, p, s, box and box.get('construct', [None])[0])
        assert box['construct'][1] == (('fill', 18, 30, 72, 236) if e['open'] else ('fill', 34, 34, 42, 236)), ('V43 cell colour (locked = grey)', t, p, s, box['construct'][1])
        assert box['construct'][2] == ('fill', 0, 0, 301, 2) + e['border'] + (255,), ('V58 cell border (gold = the cell just replayed)', t, p, s, box['construct'][2], e['border'])
        counts['V58_gold_borders_drawn'] += int(e['border'] == (255, 214, 110))
        pos = box['pos']
        assert (f32(pos[0]), f32(pos[1])) == (24 + (s % 4) * 309, 114 + (s // 4) * 182), ('V42 cell position', s, pos)
        if e['cg']:
            assert th is not None and th.get('cg') == e['cg'] and 'construct' not in th and th.get('parent') == CPART(40 + s * 6) and th.get('pass') == 1, ('V42 thumbnail', t, p, s, th)
            counts['V42_thumbnails'] += 1
        elif e['frame']:
            assert th is not None and 'cg' not in th and th['construct'][0] == ('create', 120, 90) and th['construct'][1] == ('fill', 22, 22, 28, 255) \
                and th.get('parent') == CPART(40 + s * 6) and th.get('pass') == 1 and (f32(th['pos'][0]), f32(th['pos'][1])) == (8.0, 8.0), \
                ('V55 the empty frame of a locked thumbnail cell', t, p, s, th)
            counts['V55_empty_frames_drawn'] += 1
        else:
            assert th is None, ('V42 a thumbnail slot on a cell without a thumbnail', t, p, s, C['rows'][i]['no'], th)
        assert ko(nmp['text']) == e['name'], ('V42 name', t, p, s, ko(nmp['text']), e['name'])
        assert ko(idp['text']) == e['id'], ('V42 id / when', t, p, s, ko(idp['text']), e['id'])
        assert ('E%05d' % C['rows'][i]['no']) in ko(idp['text']), ('V42 E number missing', t, p, s)
        if e['cond'] is None:
            assert cdp is None, ('V42 a condition on a locked cell / a cell without one', t, p, s)
        else:
            assert cdp is not None and ko(cdp['text']) == e['cond'], ('V42 condition', t, p, s, cdp and ko(cdp['text']), e['cond'])
        for part, budget in ((nmp, C_NAME_THUMB if e['thumb'] else C_NAME_SMALL), (cdp, C_COND)):
            if part is None:
                continue
            for line in re.sub(r'\$\{/?font[^}]*\}', '', ko(part['text'])).split('\n'):
                assert cunits(line) <= budget + 0.01, ('V42 a line wider than its cell', line)
        for line in re.sub(r'\$\{/?font[^}]*\}', '', ko(idp['text'])).split('\n'):
            assert cunits(line) <= (C_WHEN_THUMB if e['thumb'] else C_IDWHEN_SMALL) + 1.5, ('V42 id line too wide', line)
        want_parts += 1 + int(bool(e['thumb'])) + 2 + int(e['cond'] is not None)
        counts['V42_cells_drawn'] += 1
        counts['V43_open_cells' if e['open'] else 'V43_locked_cells'] += 1
    assert len(vm.ours22()) == want_parts, ('V46 part count of a page', t, p, len(vm.ours22()), want_parts)
    counts['V42_pages'] += 1


def chart_open(vm, all_=False, ctx=2):
    vm.vars['YoruKR.C.Open'] = '1'
    vm.vars['YoruKR.C.All'] = '1' if all_ else '0'
    vm.vars['YoruKR.C.Ctx'] = str(ctx)


def chart_state(vm, X, C, kind, rnd=None):
    """global records: none / all / partial (a seeded half of the events and of the recollection cells)."""
    firsts = {m for m in vm.msg_of.values() if m >= 0}
    cells = {(c // 100 - 1, c % 100 - 1) for c in C['memcell'].values()}
    if kind == 'none':
        vm.flags, vm.mem_enabled = set(), set()
    elif kind == 'all':
        vm.flags, vm.mem_enabled = set(firsts), set(cells)
    else:
        r = random.Random(rnd or 22)
        vm.flags = {m for m in sorted(firsts) if r.random() < 0.5}
        vm.mem_enabled = {c for c in sorted(cells) if r.random() < 0.5}


def chart_page_checks(vm, X, C, counts, states=(('none', False), ('partial', False), ('all', False), ('none', True))):
    """V42 / V43 / V46: every page of every tab under four global states (no records / half / all / 「전체 개방」 with none)."""
    for st, all_ in states:
        chart_state(vm, X, C, st)
        vm.parts = {}
        chart_open(vm, all_)
        prev = None
        for t in range(10):
            n = C['first'][t + 1] - C['first'][t]
            for p in range(max(1, (n + 11) // 12)):
                vm.run('KR_CDraw', [t, p])
                check_page(vm, C, t, p, all_, counts)
                prev = (t, p)
        vm.run('KR_CClear')
        assert vm.ours22() == [], ('V46 parts left after KR_CClear', vm.ours22()[:4])
        counts['V43_states'] += 1
    # the open test is the global records (or 「전체 개방」) and never the per-save registration
    chart_state(vm, X, C, 'partial')
    vm.registered = {e['fn'] for e in X['ev'].values()}          # every event registered in this save: must not matter
    vm.parts = {}
    chart_open(vm, False)
    vm.reg_asked = []
    for t in range(10):
        vm.run('KR_CDraw', [t, 0])
        check_page(vm, C, t, 0, False, counts)
    assert not vm.reg_asked, ('V43 IsRegisteredEvent asked while the chart is open', vm.reg_asked[:3])
    vm.run('KR_CClear')
    vm.registered = set()
    counts['V43_registration_ignored'] += 1


def chart_session(vm, ctx, answers, all_=False, title=True):
    """KR_CChart(ctx) with the scripted answers (chart waits and dialogs in order). Returns the dialogs (chart waits included)."""
    vm.cur = None
    vm.calls = []
    vm.dialogs = []
    vm.charts = []
    vm.frames = []
    vm.script = list(answers)
    vm.disk[CHART] = 'YoruKR.Chart.1\r\n%d\r\n' % int(all_)
    vm.dirs.add(VM.SAVE_DIR)
    if title:
        vm.title_scene()
    vm.run('KR_CChart', [ctx])
    assert not vm.script, ('answers left over (a window did not open)', vm.script)
    assert vm.ours22() == [], ('V46 chart parts left after the chart', vm.ours22()[:4])
    assert vm.vars.get('YoruKR.C.Open', '') == '' and vm.vars.get('YoruKR.C.Play', '') == '' and vm.vars.get('YoruKR.T9.Unwind', '') == '', \
        ('V44 chart state left after the chart', vm.vars.get('YoruKR.C.Open'), vm.vars.get('YoruKR.C.Play'), vm.vars.get('YoruKR.T9.Unwind'))
    return vm.dialogs


def box_of(s):
    return CPART(40 + s * 6)


def find_cell(C, vm, all_, pred):
    """(tab, page, slot, cell) of the first cell with pred(row, open)."""
    for t in range(10):
        for i in range(C['first'][t], C['first'][t + 1]):
            r = C['rows'][i]
            if pred(r, copen(vm, C, r['no'], all_)):
                k = i - C['first'][t]
                return t, k // 12, k % 12, i
    return None


def goto(t, p):
    """answers that bring the chart from its first page to (t, p): the tab, then 「다음 쪽」 p times."""
    return [CPART(10 + t)] + [CPART(34)] * p


def chart_flow_checks(cand, nm, X, C, counts):
    """V43 (click on a locked cell) / V44 (page, replay path) / V46 (parts after every way out)."""
    mk = lambda: chart_vm(cand, nm, X)
    out = {}
    # 1 a locked cell (r24): its detail page without 이 장면 재생 (state line 「전체 개방하면 재생됩니다」), 돌아가기, the same
    #   page drawn again; then the close button
    vm = mk()
    chart_state(vm, X, C, 'partial')
    t, p, s, i = find_cell(C, vm, False, lambda r, op: not op and not r['noplay'])
    ds = chart_session(vm, 1, [CPART(10 + t)] + [2] * p + [box_of(s), 0, CPART(30)])
    kinds = [d.get('kind', 'dialog') for d in ds]
    pg = ds[-2]
    assert kinds.count('chart') == 3 + p and pg.get('kind') != 'chart', ('V43 locked cell', kinds)
    assert 13 not in [x[0] for x in pg['items']] and C_STATE24[0] in ko(pg['title']).split('\n'), ('V56 locked cell page', pg['items'], ko(pg['title'])[-40:])
    assert not vm.replays and not any(c[0] == 'KR_T8CharDatePage' for c in vm.calls), 'V43 a locked cell started something'
    assert ds[-1]['parts'] == ds[-3]['parts'], 'V43 the chart after the locked cell\'s page is not the same page'
    assert vm.parts[VM.TITLE_ROOT]['show'] == 1
    check_dialog(pg, counts)
    counts['V43_locked_click_page'] += 1
    out['locked'] = C['rows'][i]['no']
    # 2 an open scene cell (unlocked by 「전체 개방」): the scene page (chart branch), 이 장면 재생 -> the chart closes -> replay
    for ctx in (1, 2):
        vm = mk()
        chart_state(vm, X, C, 'none')
        t, p, s, i = find_cell(C, vm, True, lambda r, op: op and not r['card'] and not r['noplay'])
        no = C['rows'][i]['no']
        ds = chart_session(vm, ctx, goto(t, p) + [box_of(s), 13, CPART(30)], all_=True)     # r24: the chart comes back after the replay (closed)
        pg = [d for d in ds if d.get('kind') != 'chart'][-1]
        want = '〓' + ko(vm.run('KR_T19EvHead', [no])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [no])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [no])) \
            + '\n' + C_STATE['all'] + '\n' + C_PLAY_NOTE
        assert ko(pg['title']) == want, ('V44 scene page (chart branch)', ko(pg['title']), want)
        assert [(i_, ko(x)) for i_, x, _, _ in pg['items']] == [(13, PLAY), (0, '돌아가기')], pg['items']
        check_dialog(pg, counts)
        rp = vm.replays
        assert len(rp) == 1 and rp[0]['no'] == no and rp[0]['ctx'] == ctx, ('V44 replay', rp)
        assert rp[0]['ours'] == [] and rp[0]['open'] == '' and rp[0]['unwind'] == '' and rp[0]['t9play'] == '' and not rp[0]['dialog_open'], ('V44 state at the replay', rp[0])
        if ctx == 1:
            assert rp[0]['title_root_show'] == 0 and vm.parts[VM.TITLE_ROOT]['show'] == 1, ('V44 the title root around the replay', rp[0]['title_root_show'])
        else:
            assert rp[0]['title_root_show'] == 1, 'V44 the home replay touched the title root'
        assert not any(c[0] in ('LSys3xScript::Prepare', 'LSys3xScript::RunEvent') for c in vm.calls if isinstance(c, tuple)), 'V44 the r18 path ran'
        assert vm.v('Play') == '' and vm.v('Playing') == '', 'V44 the r18 play slot was set'
        assert (vm.msg_of[no] in vm.flags) or vm.msg_of[no] < 0, 'V44 model: the replay marks the scene read'
        counts['V44_replays_ctx%d' % ctx] += 1
        out['replay_ctx%d' % ctx] = no
    # 3 an open bundle card: the card page (chart branch), 단계 고르기 (global marks), a stage, 이 장면 재생 -> that stage replays;
    #   a locked stage of an open card offers no replay (the lock holds inside the card too)
    vm = mk()
    chart_state(vm, X, C, 'none')
    cand_cards = [r for r in C['rows'] if r['card'] and X['cards'][r['ref'] - 100000]['size'] >= 3 and not r['noplay']]
    r = cand_cards[0]
    k = r['ref'] - 100000
    card = X['cards'][k]
    st = card['stages']
    vm.flags = {vm.msg_of[st[0]], vm.msg_of[st[1]]} - {-1}          # entry and stage 2 read, stage 3 not
    i = C['rows'].index(r)
    t = r['tab']
    kk = i - C['first'][t]
    stage3 = st[2]
    ds = chart_session(vm, 2, goto(t, kk // 12) + [box_of(kk % 12), 14, 102, 0, 101, 13, CPART(30)])     # r24: + close the chart that comes back
    cardpg, stagepg, lockedpg, stagepg2, openpg = [d for d in ds if d.get('kind') != 'chart']
    wantc = '〓' + ko(vm.run('KR_T19CardHead', [k])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [st[0]])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [st[0]])) \
        + '\n' + C_STATE[1] + '\n¶단계 %d/%d 읽음' % (sum(1 for x in st if cstate(vm, C, x) == 1), len(st)) + '\n' + C_PLAY_NOTE
    assert ko(cardpg['title']) == wantc, ('V44 card page (chart branch)', ko(cardpg['title']), wantc)
    assert [i_ for i_, _, _, _ in cardpg['items']] == [13, 14, 0], cardpg['items']
    lines = ko(stagepg['title']).split('\n')
    assert lines[-1].startswith(C_LEGEND), ('V44 stage list legend (chart)', lines[-1])
    marks = [ko(x)[-1] for i_, x, _h, _d in stagepg['items'] if i_ >= 100]
    assert marks[:3] == ['△', '△', '●'], ('V44 stage list marks (global)', marks[:3])
    assert [i_ for i_, _, _, _ in lockedpg['items']] == [0] and C_STATE24[0] in ko(lockedpg['title']).split('\n'), ('V44 a locked stage offers play', lockedpg['items'])     # r24 state line
    assert [i_ for i_, _, _, _ in openpg['items']] == [13, 0], openpg['items']
    assert len(vm.replays) == 1 and vm.replays[0]['no'] == st[1], ('V44 stage replay', vm.replays)
    for d in (cardpg, stagepg, lockedpg, openpg):
        check_dialog(d, counts)
    counts['V44_card_stage_paths'] += 1
    out['card'] = card['key']
    # 4 cancel (right click / space = 0) and the close button: no replay, no part, the chart state cleared
    for ans in ([0], [CPART(30)], [4, 4, 3, 1, 2, CPART(30)]):
        vm = mk()
        chart_state(vm, X, C, 'partial')
        chart_session(vm, 1, ans)
        assert not vm.replays
        counts['V46_ways_out'] += 1
    return out


def chart_confine_checks(cand, nm, X, C, counts):
    """V45: with the chart closed - and with a stale 「Open」 flag but no chart root - the calendar functions give what the r21
    candidate gives (same save state, same answers)."""
    r21 = L.R21 / 'candidate' / 'NightRemaster.ain'
    r21m = L.read_meta(L.R21 / 'work' / 'build' / 'candidate_meta.json')
    assert L.sha(r21) == L.R21_AIN_SHA
    rnd = random.Random(45)
    regs = {e['fn'] for no, e in X['ev'].items() if rnd.random() < 0.4}
    flags = {e['m0'] for no, e in X['ev'].items() if e['m0'] is not None and rnd.random() < 0.5}
    sample_cards = list(range(0, len(X['cards']), 7))
    sample_scenes = sorted(X['ev'])[::23]

    def run_all(vm, stale):
        vm.registered, vm.flags = set(regs), set(flags)
        vm.mem_enabled = {(0, 0)}
        if stale:
            vm.vars['YoruKR.C.Open'] = '1'                     # a stale flag without the chart root
        vm.parts = {}
        vm.title_scene()
        res = []
        for k in sample_cards:
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            vm.vars['YoruKR.T9.Unwind'] = ''
            vm.vars['YoruKR.T9.Play'] = ''
            vm.cur = None
            vm.dialogs = []
            vm.script = [13]
            vm.run('KR_T9CardPage', [k, X['cards'][k]['month']])
            res.append(('card', k, [(ko(d['title']), [(i, ko(x), dis) for i, x, _, dis in d['items']]) for d in vm.dialogs], vm.v('Play'), vm.v('Unwind')))
        for no in sample_scenes:
            vm.vars['YoruKR.T9.Ctx'] = 'P'
            vm.vars['YoruKR.T9.Unwind'] = ''
            vm.vars['YoruKR.T9.Play'] = ''
            vm.cur = None
            vm.dialogs = []
            vm.script = [13]
            vm.run('KR_T9EventPage', [no, ''])
            res.append(('scene', no, [(ko(d['title']), [(i, ko(x), dis) for i, x, _, dis in d['items']]) for d in vm.dialogs], vm.v('Play'), vm.v('Unwind')))
            res.append(('state', no, vm.run('KR_T9State', [no]), vm.run('KR_T9Seen', [no])))
        res.append(('legend', ko(vm.run('KR_T9Legend'))))
        return res
    ref = run_all(chart_vm(r21, r21m, X), False)
    for stale in (False, True):
        got = run_all(chart_vm(cand, nm, X), stale)
        diff = [(a, b) for a, b in zip(ref, got) if a != b]
        assert len(ref) == len(got) and not diff, ('V45 the calendar differs from r21' + (' with a stale flag' if stale else ''), diff[:2])
        counts['V45_calendar_equal_r21' + ('_stale_flag' if stale else '')] = len(ref)
    return dict(compared=len(ref), cards=len(sample_cards), scenes=len(sample_scenes))


def title_checks(cand, nm, X, C, counts):
    """V47: the title's poll (KR_CTitleTick every frame) and serve (KR_CTitleServe after the wait)."""
    mk = lambda: chart_vm(cand, nm, X)
    # idle: two existence checks a frame, the original IsClickConfig result passed on, no wait ended
    vm = mk()
    for cfg in (0, 1):
        vm.inputs['IsClickConfig'] = cfg
        vm.file_calls = []
        vm.ended = None
        r = vm.run('KR_CTitleTick')
        assert r == cfg and vm.ended is None and [op for op, _ in vm.file_calls] == ['exist', 'exist'], ('V47 idle title frame', r, vm.file_calls)
    vm.calls = []
    vm.run('KR_CTitleServe')
    assert [c for c in vm.calls if c[0] == '■方向キー処理／削除'] and not vm.file_calls[2:], 'V47 serve without a request touched the files'
    counts['V47_title_idle'] += 1
    # a request: the wait ends with KR_CCode, the frame answers false, the serve runs it (ctx 1)
    for cmd, answers, check in (('chart', [0], lambda v, ds: v.charts and v.charts[0]['ctx'] == '1'),
                                ('unlock_all', [OK], lambda v, ds: ko(ds[0]['title']) == '〓모드 메뉴\n†전체 개방: 안 본 이벤트도 열람·재생됩니다' and v.disk.get(CHART) == 'YoruKR.Chart.1\r\n1\r\n'),
                                ('unlock_revert', [OK], lambda v, ds: ko(ds[0]['title']) == T_REVERT and v.disk.get(CHART) == 'YoruKR.Chart.1\r\n0\r\n'),
                                ('reset_all', [NO], lambda v, ds: ko(ds[0]['title']) == T_RESET and MARKER not in v.disk),
                                ('reset_restore', [NO], lambda v, ds: ko(ds[0]['title']) == T_RESTORE and MARKER not in v.disk)):
        vm = mk()
        vm.title_scene()
        hook_request(vm, cmd)
        vm.inputs['IsClickConfig'] = 1
        vm.ended = None
        r = vm.run('KR_CTitleTick')
        assert r == 0 and vm.ended == C_CODE and vm.vars.get('YoruKR.C.TitleReq') == '1', ('V47 title tick with a request', cmd, r, vm.ended)
        vm.calls = []
        vm.dialogs = []
        vm.charts = []
        vm.script = list(answers)
        vm.run('KR_CTitleServe')
        assert vm.calls[0][0] == '■方向キー処理／削除', ('V47 the original call first', vm.calls[:2])
        assert REQ not in vm.disk and vm.vars.get('YoruKR.C.TitleReq') == '', ('V47 request not consumed', cmd)
        assert check(vm, [d for d in vm.dialogs if d.get('kind') != 'chart']), ('V47 command at the title', cmd)
        assert not vm.script
        counts['V47_title_commands'] += 1
    # reset_all 예 at the title: the marker, the .req, the exit (the same code as at home)
    vm = mk()
    hook_request(vm, 'reset_all')
    vm.run('KR_CTitleTick')
    vm.script = [YES]
    try:
        vm.run('KR_CTitleServe')
        raise AssertionError('V47 reset at the title did not exit')
    except VMExit as ex:
        assert ex.code == 0 and vm.disk.get(MARKER) == 'reset' and vm.disk.get(RESET_REQ) == 'reset'
    counts['V47_title_reset_exit'] += 1
    # a result and a request together: the result window first
    vm = mk()
    hook_result(vm, 'reset ok KR_reset_20260928_031500\r\n')
    hook_request(vm, 'unlock_all')
    vm.run('KR_CTitleTick')
    vm.dialogs = []
    vm.script = [OK, OK]
    vm.run('KR_CTitleServe')
    assert [ko(d['title']).split('\n')[0] for d in vm.dialogs] == [T_RESULT_HEAD, '〓모드 메뉴'], [ko(d['title'])[:12] for d in vm.dialogs]
    counts['V47_result_before_request'] += 1
    # an undeletable request: served once, then the title stops polling (the r21 「Off」 rule)
    vm = mk()
    vm.fail_delete = {REQ}
    hook_request(vm, 'unlock_revert')
    vm.run('KR_CTitleTick')
    vm.script = [OK]
    vm.run('KR_CTitleServe')
    assert vm.vars.get('YoruKR.M.Off') == '1'
    vm.file_calls = []
    vm.ended = None
    vm.run('KR_CTitleTick')
    assert not vm.file_calls and vm.ended is None, 'V47 the title polled after an undeletable request'
    counts['V47_undeletable_stops'] += 1
    return dict(commands=counts['V47_title_commands'])


def noplay_checks(cand, nm, X, C, counts):
    """V48: a not-playable scene: the cell note, no 이 장면 재생 on its page, KR_CRequest refuses (synthetic: every scene)."""
    real = [no for no, v in C['noplay'].items() if v]
    counts['V48_not_playable_real'] = len(real)
    every = op_replace('KR_CNoPlay', lambda o: o == ['PUSH', '0'], lambda o: ['PUSH', '1'], nth=0)
    vm = chart_vm(cand, nm, X, mutate=every)
    chart_state(vm, X, C, 'all')
    t, p, s, i = find_cell(C, vm, False, lambda r, op: op and not r['card'])
    no = C['rows'][i]['no']
    ds = chart_session(vm, 1, goto(t, p) + [box_of(s), 0, CPART(30)])
    pg = [d for d in ds if d.get('kind') != 'chart'][0]
    assert [i_ for i_, _, _, _ in pg['items']] == [0] and ko(pg['title']).endswith(C_NOPLAY_NOTE), ('V48 page of a not-playable scene', pg['items'], ko(pg['title'])[-20:])
    assert not vm.replays
    vm.vars['YoruKR.C.All'] = '1'
    vm.run('KR_CRequest', [no])
    assert vm.vars.get('YoruKR.C.Play', '') == '' and vm.vars.get('YoruKR.T9.Unwind', '') == '', 'V48 a request for a not-playable scene was taken'
    counts['V48_page_and_request'] += 1
    # the cell note (real table, or the synthetic one when nothing failed)
    rows = [r for r in C['rows'] if r['noplay']] or []
    for r in rows:
        assert r['cond'].split('\n')[-1] == C_NOTE
    counts['V48_cells_with_note'] = len(rows)
    return dict(real=real)


# ============================================================== r23: the affinity figures (V49-V54)
R23_MOON = 2026092330
R23_MOON_Z = 260
R23_EDGE = struct.unpack('<i', struct.pack('<f', 2.0))[0]
R23_MOON_FONT = (257, 18, 255, 255, 255, 0, 0, 0, 0, R23_EDGE)          # the float arguments reach the VM as their bit patterns
R23_METRICS = {18: dict(full=14, digit=9, space=5, other=6), 20: dict(full=16, digit=10, space=5, other=7),
               22: dict(full=17, digit=11, space=6, other=7), 24: dict(full=19, digit=12, space=6, other=8)}   # measured natively (work/explore)
R23_TEXT_PX = 318                          # the 「이벤트」 page text area: x 52 .. 370 under the status root
R23_HEROINES = [2, 3, 4, 5]
R23_OTHERS = [1, 6, 7, 8]
R23_VALUES = [-3, 0, 1, 14, 15, 16, 29, 30, 31, 44, 45, 46, 59, 60, 61, 119, 120, 121, 150]
R23_DATES = [(4, 20), (5, 30), (6, 30), (7, 27), (8, 30), (9, 16), (10, 11), (10, 14), (11, 1), (11, 2), (11, 17)]
R23_SYN_FEEL = {1: 0, 2: 13438, 3: 35349, 4: 28192, 5: 11000, 6: 2500, 7: 16356, 8: 2750}     # the 10/14 save's values (inner)
R19_NAMES = {}


def r23_px(text, size):
    mm = R23_METRICS[size]
    x = 0
    for ch in text:
        if ch == ' ':
            x += mm['space']
        elif ch.isdigit() and ord(ch) < 128:
            x += mm['digit']
        elif ord(ch) < 128:
            x += mm['other']
        else:
            x += mm['full']
    return x


def game_rules():
    """The base code the figures depend on, read here (not from the build): C_FeelingView@Update (feelVal per moon, at most N
    moons), C_SysVoice::GetFeelingRank_5 (upper bounds, inclusive), C_Ability@GetFeelingRate (per person + default),
    C_FeelingView@Init (the 「친밀도」 label's place), C_FeelingView@Enabled (Classic mode / persons 2..5)."""
    d = L.WORK / 'vm' / 'base'
    d.mkdir(parents=True, exist_ok=True)
    bp = L.base_paths()
    body = {}
    for n in ('C_FeelingView@Update', 'C_FeelingView@Init', 'C_SysVoice::GetFeelingRank_5', 'C_Ability@GetFeelingRate', 'C_FeelingView@Enabled'):
        path = d / (re.sub(r'[^0-9A-Za-z]', '_', n) + '.jam')
        if not path.exists():
            L.cmd('ain', 'dump', '--function', n, '-o', path, bp['ain'])
        body[n] = [l.strip() for l in path.read_text('utf8').splitlines()
                   if l.strip() and not l.startswith(';') and not re.match(r'^0x[0-9a-f]+:$', l.strip()) and not l.startswith(('FUNC', 'ENDFUNC', 'EOF'))]
    txt = '\n'.join(body['C_FeelingView@Update'])
    z = re.search(r'\.LOCALREF feelVal\nPUSH 1\nSUB\nPUSH (\d+)\nDIV\nPUSH 1\nADD', txt)
    z2 = re.search(r'PUSH (\d+)\n\.LOCALREF num\nCALLHLL Math Min 0', txt)
    assert z and z2, 'C_FeelingView@Update changed'
    per, moons = int(z.group(1)), int(z2.group(1))
    rk = body['C_SysVoice::GetFeelingRank_5']
    bounds = [int(rk[i + 1].split()[1]) for i in range(len(rk) - 2) if rk[i] == '.LOCALREF nFeeling' and rk[i + 2] == 'LTE']
    assert bounds == sorted(bounds) and len(bounds) == 4, bounds
    rt = body['C_Ability@GetFeelingRate']
    rates = {}
    for i, o in enumerate(rt):
        z3 = re.match(r'\.CASE \d+:\d+ (-?\d+)$', o)
        if z3:
            rates[int(z3.group(1))] = int(rt[i + 1].split()[1])
    default = int([o for o in rt if o.startswith('PUSH ')][-2].split()[1])
    ini = body['C_FeelingView@Init']
    f32 = lambda i: struct.unpack('<f', struct.pack('<i', int(i)))[0]
    pos = [(f32(ini[i].split()[1]), f32(ini[i + 1].split()[1])) for i in range(len(ini) - 2)
           if ini[i].startswith('PUSH ') and ini[i + 1].startswith('PUSH ') and ini[i + 2].startswith('NEW CASPosF')]
    en = '\n'.join(body['C_FeelingView@Enabled'])
    assert '.LOCALREF charaNo\nPUSH 2\nLT' in en and '.LOCALREF charaNo\nPUSH 5\nGT' in en and '.GLOBALREF Flags' in en, 'C_FeelingView@Enabled changed'
    return dict(per=per, moons=moons, maximum=per * moons, bounds=bounds, rates=rates, rate_default=default, box=pos[0], label=pos[1],
                enabled='GameMode != Classic and 2 <= person <= 5')


def r23_value(G, inner, p):
    return int(inner / G['rates'].get(p, G['rate_default']))


def r23_rank(G, v):
    return 1 + sum(1 for b in G['bounds'] if v > b)


def r23_moon_text(G, v, r):
    return '%d / %d\n${font size=16}단계 %d/5${/font}' % (v, G['maximum'], r)


def r23_enabled(c, mode):
    return mode != 1 and 2 <= c <= 5


def r23_gates():
    """graph/schedule.json's feeling_gate triggers with the last day each can fire (independent of build_feeling_r23)."""
    sched = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    end = tuple(sched['calendar']['end'])
    out = []
    for e in sched['events']:
        for t in e['triggers']:
            for g in t.get('feeling_gate') or []:
                k = t['kind']
                if k == 'conditional':
                    last = tuple(t['date_to'])
                elif k == 'scheduled_special':
                    last = tuple(t['date'])
                else:
                    z = re.search(r'IsTodayOrBefore\((\d+), (\d+)\)', t['condition_expr'])
                    last = (int(z.group(1)), int(z.group(2))) if z else end
                out.append(dict(no=e['id'], person=g['person'], op=g['op'], value=g.get('value', 0), last=last[0] * 100 + last[1]))
    assert len(out) == 28, len(out)
    return out


def r19_name(no):
    if not R19_NAMES:
        R19_NAMES.update({int(k): v for k, v in L.readj(L.R19 / 'work' / 'build' / 'tables.json')['ev_head'].items()})
    return R19_NAMES[no]


def r23_next(X, gates, p, v, regs, today):
    t = today[0] * 100 + today[1]
    c = [g for g in gates if g['person'] == p and g['op'] == '>=' and g['value'] > v and g['last'] >= t and X['ev'][g['no']]['fn'] not in regs]
    return min(c, key=lambda g: (g['value'], g['no'])) if c else None


def r23_route(X, gates, p, regs, today):
    t = today[0] * 100 + today[1]
    gs = [g for g in gates if g['person'] == p and g['op'] == 'highest']
    assert len(gs) == 1, (p, gs)
    g = gs[0]
    return g if g['last'] >= t and X['ev'][g['no']]['fn'] not in regs else None


def r23_block(X, G, gates, regs, today, p, v):
    t = '\n친밀도 ' + tint(str(v), CYAN) + ' (%d/5) · 다음 조건 ' % r23_rank(G, v)
    nx = r23_next(X, gates, p, v, regs, today)
    if nx is None:
        t += tint('없음', GRAY)
    else:
        t += tint(str(nx['value']), CYAN) + '\n${font size=18}　' + r19_name(nx['no']) + '${/font}'
    ro = r23_route(X, gates, p, regs, today)
    if ro is not None:
        t += '\n루트: 네 명 중 가장 높으면\n${font size=18}　' + r19_name(ro['no']) + '${/font}'
    return t, nx, ro


def r23_status_text(X, G, gates, regs, today, c, v, enabled):
    t = r20_status_text(X, regs, c, today)
    if not enabled:
        return t
    i = t.index('\n')
    return t[:i] + r23_block(X, G, gates, regs, today, c, v)[0] + t[i:]


def r23_panel_h(X, G, gates, regs, today, c, v, enabled):
    if not enabled:
        return 448
    _, nx, ro = r23_block(X, G, gates, regs, today, c, v)
    return 448 + 32 + (26 if nx else 0) + (58 if ro else 0)


def r23_lines_fit(text):
    """Every line of the 「이벤트」 page inside the text area (18 px lines are the tagged name lines, the rest 24 px)."""
    widest = 0
    for line in text.split('\n'):
        size = 18 if line.startswith('${font size=18}') else 24
        w = r23_px(untag(line), size)
        assert w <= R23_TEXT_PX, ('V52 a line wider than the page', untag(line), size, w)
        widest = max(widest, w)
    return widest


def r23_value_checks(vm, X, G, counts):
    """V49 / V50: value, maximum, rank and the moon text at the boundaries, for the four heroines (and the value of everyone)."""
    vm.reset()
    vm.registered = set()
    vm.today = (10, 14)
    for p in range(1, 9):
        rate = G['rates'].get(p, G['rate_default'])
        for v in R23_VALUES:
            for inner in ({v * rate, v * rate + (rate - 1)} if v >= 0 else {v * rate, v * rate - (rate - 1)}):
                vm.feel = {p: inner}
                assert r23_value(G, inner, p) == v, (p, v, inner)
                assert vm.run('KR_T23Feel', [p]) == v, ('V49 value (GetFeeling units)', p, v, inner, vm.run('KR_T23Feel', [p]))
                assert vm.run('KR_T23Rank', [p]) == r23_rank(G, v), ('V50 rank', p, v, vm.run('KR_T23Rank', [p]), r23_rank(G, v))
                if p in R23_HEROINES:
                    got = ko(vm.run('KR_T23MoonText', [p]))
                    assert got == r23_moon_text(G, v, r23_rank(G, v)), ('V49 moon text', p, v, got)
                    counts['V49_moon_texts'] += 1
                counts['V50_ranks'] += 1
    assert vm.run('KR_T23MoonMax') == G['maximum'] == 120, ('V49 maximum', vm.run('KR_T23MoonMax'), G['maximum'])
    for v, r in ((15, 1), (16, 2), (30, 2), (31, 3), (45, 3), (46, 4), (60, 4), (61, 5), (0, 1), (-3, 1), (150, 5)):
        assert r23_rank(G, v) == r, ('V50 the model\'s bounds', v, r)
    counts['V49_maximum'] = G['maximum']
    counts['V50_bounds_inclusive'] = len(G['bounds'])


def r23_next_checks(vm, X, G, gates, counts, regs_sets):
    """V51: 「다음 조건」 and the 「루트」 line = the model for values x registrations x dates; names = the base's r19 names."""
    for g in gates:
        assert ko(vm.run('KR_T19EvHead', [g['no']])) == r19_name(g['no']), ('V51 the base\'s r19 name differs from the r19 tables', g['no'])
        assert r23_px('　' + r19_name(g['no']), 18) <= R23_TEXT_PX, ('V51 a gate name wider than the page', g['no'])
        counts['V51_gate_names'] += 1
    tab = [(vm.run('KR_T23GateEv', [i]), vm.run('KR_T23GatePerson', [i]), vm.run('KR_T23GateOp', [i]), vm.run('KR_T23GateValue', [i]),
            vm.run('KR_T23GateLast', [i])) for i in range(vm.run('KR_T23GateN'))]
    ops = {'>=': 0, '<': 1, 'highest': 2}
    assert sorted(tab) == sorted((g['no'], g['person'], ops[g['op']], g['value'], g['last']) for g in gates), 'V51 the gate table != schedule.json'
    evs = [t[0] for t in tab]
    for tag, regs in regs_sets:
        vm.registered = regs
        for today in R23_DATES:
            vm.today = today
            for p in R23_HEROINES:
                rate = G['rates'][p]
                for v in (0, 4, 5, 9, 10, 14, 15, 20, 22, 25, 29, 30, 34, 35, 49, 50, 59, 60, 61):
                    vm.feel = {p: v * rate}
                    k = vm.run('KR_T23Next', [p])
                    want = r23_next(X, gates, p, v, regs, today)
                    assert (evs[k] if k >= 0 else None) == (want['no'] if want else None), ('V51 next condition', tag, today, p, v, k, want)
                    counts['V51_next_checked'] += 1
                    counts['V51_next_none' if want is None else 'V51_next_found'] += 1
                r_ = vm.run('KR_T23Route', [p])
                want = r23_route(X, gates, p, regs, today)
                assert (evs[r_] if r_ >= 0 else None) == (want['no'] if want else None), ('V51 route line', tag, today, p)
                counts['V51_route_checked'] += 1


def r23_text_checks(vm, X, G, gates, counts, states):
    """V52: the 「이벤트」 page text of every person (moons or not, Modern / Classic) = the model; the lines fit; the extra height."""
    widest = 0
    for tag, regs, today in states:
        vm.registered = regs
        vm.today = today
        vm.feel = dict(R23_SYN_FEEL)
        for c in range(1, 9):
            v = r23_value(G, R23_SYN_FEEL.get(c, 0), c)
            for mode in (0, 1):
                en = r23_enabled(c, mode)
                got = ko(vm.run('KR_T23StText', [c, int(en)]))
                want = r23_status_text(X, G, gates, regs, today, c, v, en)
                assert got == want, ('V52 이벤트 쪽', tag, c, mode, [(a, b) for a, b in zip(got.split('\n'), want.split('\n')) if a != b][:2])
                if not en:
                    assert got == r20_status_text(X, regs, c, today), ('V52 a person without moons: not r20\'s text', tag, c)
                widest = max(widest, r23_lines_fit(got))
                counts['V52_texts'] += 1
            if c in R23_HEROINES:
                assert 448 + vm.run('KR_T23FeelExtra', [c]) == r23_panel_h(X, G, gates, regs, today, c, v, True), ('V52 panel height', tag, c)
    counts['V52_widest_line_px'] = widest
    return widest


def r23_lifecycle_checks(vm, X, G, gates, counts, regs, today):
    """V53: the moon text part through the game's paths; V52's page 4 drawn through KR_T20StActiveOf -> KR_T23StDraw."""
    vm.reset()
    vm.registered = regs
    vm.today = today
    vm.feel = dict(R23_SYN_FEEL)
    vm.parts = {}
    vm.calls = []
    vm.game_mode = 0
    fid = lambda n: vm.fs[n]['index']
    seen_shown = collections.Counter()

    def expect(sv, page):
        c = sv[9][5] if isinstance(sv[9], dict) else 0
        en = r23_enabled(c, vm.game_mode) and page in (0, 1)
        p = vm.parts.get(R23_MOON)
        assert sv[9]['moons'] == int(en), ('V53 the moons model disagrees', c, page)
        if not en:
            assert p is None, ('V53 a moon text where the game draws no moons', c, page, vm.game_mode, p and ko(p['text']))
            return
        v = r23_value(G, vm.feel.get(c, 0), c)
        want = r23_moon_text(G, v, r23_rank(G, v))
        assert p is not None and ko(p['text']) == want, ('V53 moon text', c, page, p and ko(p['text']), want)
        assert p['show'] == 1 and p['parent'] == VM.ST_ROOT and p['pos'] == (G['label'][0], G['label'][1] + 18) and p['z'] == R23_MOON_Z, p
        assert p['font'] == R23_MOON_FONT and p['tag'] == 1 and p['linespace'] == 2, p
        seen_shown[c] += 1
        counts['V53_moon_texts_checked'] += 1

    def page4(sv):
        c = sv[11]
        en = r23_enabled(c, vm.game_mode)
        t, pnl = vm.parts[ST_TEXT], vm.parts[ST_PANEL]
        v = r23_value(G, vm.feel.get(c, 0), c)
        assert ko(t['text']) == r23_status_text(X, G, gates, regs, today, c, v, en), ('V52 page 4 drawn', c)
        assert pnl['construct'][0] == ('create', 338, r23_panel_h(X, G, gates, regs, today, c, v, en)), (c, pnl['construct'][0])
        assert t['parent'] == pnl['parent'] == VM.ST_ROOT and t['pos'] == (52.0, 80.0) and pnl['pos'] == (32.0, 64.0), (t, pnl)
        counts['V52_pages_drawn'] += 1
    # the member view's status view: Init -> nothing yet
    sv = vm.status_view_init()
    expect(sv, 0)
    # the hover preview of every person (RunMember OnEnterChara: SetInfo + Show), page 0
    for c in range(1, 9):
        vm.method(fid('C_HomeStatusView@SetInfo'), sv, [c])
        expect(sv, 0)
    # the status window (BeginStatus = SetActivePage(1)) of a heroine, a man, a heroine: pages 1 -> 2 -> 3 -> 4 -> 1 and back to 4
    for c in (2, 6, 4):
        vm.method(fid('C_HomeStatusView@SetInfo'), sv, [c])
        vm.method(fid('C_HomeStatusView@SetActivePage'), sv, [1])
        expect(sv, 1)
        for want_page in (2, 3, 4, 1, 4):
            vm.method(fid('KR_T20StNext' if want_page != 4 or sv[16] == 3 else 'KR_T20StPrev'), sv, [])
            assert sv[16] == want_page, (sv[16], want_page)
            expect(sv, want_page)
            if want_page == 4:
                page4(sv)
        # another person while on page 4 (Up / Down / wheel -> SetInfo -> KR_T20StActive(4)): redrawn, still no moon text
        other = 3 if c != 3 else 5
        vm.method(fid('C_HomeStatusView@SetInfo'), sv, [other])
        expect(sv, 4)
        page4(sv)
        vm.method(fid('C_HomeStatusView@SetInfo'), sv, [c])
        vm.run('KR_T20StEnd', [['delegate C_Status::OnMouseWheel']])         # C_Status::RunStatus ends (r20: page-4 parts gone)
        vm.method(fid('C_HomeStatusView@SetActivePage'), sv, [0])           # EndStatus: back to the preview page
        expect(sv, 0)
    # the member screen closes: the status view (and its moons) destroyed -> nothing of ours left
    vm.status_view_destroy(sv)
    assert R23_MOON not in vm.parts and not [n for n in vm.ours() if n in (ST_PANEL, ST_TEXT)], ('V53 parts left after the view was destroyed', R23_MOON in vm.parts)
    assert ('method', 'C_FeelingView@DeleteMarks', []) in vm.calls, 'V53 the moons\' own DeleteMarks no longer runs in the destructor'
    # the dungeon: a view of its own (C_Status::RunStatusInDungeon: new view, SetInfo, SetActivePage(1)), closed, destroyed
    sv2 = vm.status_view_init()
    vm.method(fid('C_HomeStatusView@SetInfo'), sv2, [5])
    vm.method(fid('C_HomeStatusView@SetActivePage'), sv2, [1])
    expect(sv2, 1)
    vm.run('KR_T20StEnd', [['delegate C_Status::OnMouseWheel']])
    vm.status_view_destroy(sv2)
    assert R23_MOON not in vm.parts, 'V53 moon text left after the dungeon view'
    # two views one after the other (enter the member screen twice): the same single part, nothing left
    for _ in range(2):
        s3 = vm.status_view_init()
        vm.method(fid('C_HomeStatusView@SetInfo'), s3, [3])
        expect(s3, 0)
        vm.status_view_destroy(s3)
        assert R23_MOON not in vm.parts
    # Classic mode: the game draws no moons -> no moon text, page 4 = r20's text
    vm.game_mode = 1
    s4 = vm.status_view_init()
    for c in range(1, 9):
        vm.method(fid('C_HomeStatusView@SetInfo'), s4, [c])
        vm.method(fid('C_HomeStatusView@SetActivePage'), s4, [1])
        expect(s4, 1)
    vm.method(fid('C_HomeStatusView@SetInfo'), s4, [2])
    for _ in range(3):
        vm.method(fid('KR_T20StNext'), s4, [])
    assert s4[16] == 4
    page4(s4)
    vm.run('KR_T20StEnd', [['delegate C_Status::OnMouseWheel']])
    vm.status_view_destroy(s4)
    vm.game_mode = 0
    assert not vm.parts.get(R23_MOON)
    assert set(seen_shown) == set(R23_HEROINES), ('V53 the moon text shown for', sorted(seen_shown))
    counts['V53_views_destroyed'] = len(vm.destroyed)
    counts['V53_persons_with_text'] = len(seen_shown)


def r23_blocks(log):
    out = {}
    i = 0
    while i < len(log):
        z = re.match(r'(R23MOON|R23ST|R23BLOCK) (.*) <<<$', log[i])
        if z:
            j = log.index('>>>', i)
            out[(z.group(1), z.group(2))] = '\n'.join(log[i + 1:j])
            i = j
        i += 1
    return out


def r23_real_save_checks(vm, X, G, gates, counts):
    """V54: every real save (probe --regs): per person the game's GetFeeling / GetFeelingRank_5 and our texts, logged natively =
    the VM on the same state = the model."""
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
        feel = {}
        game = {}
        mode = None
        for l in r['log']:
            z = re.match(r'R23 (\d) inner=(-?\d+) feel=(-?\d+) rank5=(\d+) ours=(-?\d+) rank=(\d+) next=(-?\d+) route=(-?\d+) mode=(\d+)$', l)
            if z:
                c = int(z.group(1))
                feel[c] = int(z.group(2))
                game[c] = tuple(int(z.group(k)) for k in range(3, 9))
                mode = int(z.group(9))
        assert len(feel) == 8 and mode is not None, ('no r23 values logged', r['save'])
        b = r23_blocks(r['log'])
        vm.reset()
        vm.registered = regs
        vm.today = today
        vm.feel = dict(feel)
        vm.game_mode = mode
        row = dict(save=r['save'], today='%d/%d' % today, mode=mode, persons={})
        for c in range(1, 9):
            gfeel, grank, ours, orank, nxt, rte = game[c]
            v = r23_value(G, feel[c], c)
            assert gfeel == ours == v == vm.run('KR_T23Feel', [c]), ('V54 value', r['save'], c, gfeel, ours, v)
            assert orank == grank + 1 == r23_rank(G, v) == vm.run('KR_T23Rank', [c]), ('V54 rank', r['save'], c, grank, orank)
            en = r23_enabled(c, mode)
            if c in R23_HEROINES:
                assert b[('R23MOON', str(c))] == ko(vm.run('KR_T23MoonText', [c])) == r23_moon_text(G, v, r23_rank(G, v)), ('V54 moon text', r['save'], c)
                wn = r23_next(X, gates, c, v, regs, today)
                wr = r23_route(X, gates, c, regs, today)
                assert (vm.run('KR_T23GateEv', [nxt]) if nxt >= 0 else None) == (wn['no'] if wn else None), ('V54 next condition', r['save'], c)
                assert (vm.run('KR_T23GateEv', [rte]) if rte >= 0 else None) == (wr['no'] if wr else None), ('V54 route', r['save'], c)
                row['persons'][c] = dict(value=v, rank=r23_rank(G, v), next=(wn['value'], 'E%05d' % wn['no']) if wn else None,
                                         route=('E%05d' % wr['no']) if wr else None)
            native = b[('R23ST', str(c))]
            assert native == ko(vm.run('KR_T23StText', [c, int(en)])) == r23_status_text(X, G, gates, regs, today, c, v, en), ('V54 이벤트 쪽', r['save'], c)
            counts['V54_texts_equal'] += 1
        rows.append(row)
        counts['V54_real_saves'] += 1
    assert rows, 'no real save state for r23'
    return rows


def r23_defects(G, nm):
    """r23: the value in inner units, a rank bound off by one, the next condition taking an equal threshold, the moon text for men."""
    alias_path = L.WORK / 'vm' / 'defect_rank.jam'
    alias_path.parent.mkdir(parents=True, exist_ok=True)
    b = G['bounds']
    body = ['FUNC 0', '\t.LOCALREF c', '\tCALLFUNC KR_T23Feel', '\tPUSH %d' % b[0], '\tLT', '\tIFNZ r1']
    for k, bound in enumerate(b[1:], 2):
        body += ['\t.LOCALREF c', '\tCALLFUNC KR_T23Feel', '\tPUSH %d' % bound, '\tLT', '\tIFNZ r%d' % k]
    body += ['\tPUSH 5', '\tRETURN'] + sum([['r%d:' % k, '\tPUSH %d' % k, '\tRETURN'] for k in range(1, 5)], []) + ['ENDFUNC KR_T23Rank']
    alias_path.write_text('\n'.join(body) + '\n', 'utf8')
    return [('V49 the value in inner units (KR_T23Feel reads GetFeelingInnerValue)', 'r23_value',
             op_replace('KR_T23Feel', lambda o: o == ['PUSH', str(L.fid_of(nm, 'C_Ability@GetFeeling'))], lambda o: ['PUSH', str(L.fid_of(nm, 'C_Ability@GetFeelingInnerValue'))])),
            ('V50 a rank bound off by one (「< 15」 instead of 「<= 15」 ...)', 'r23_rank', ('alias', 'KR_T23Rank', alias_path)),
            ('V51 the next condition takes a threshold equal to the value (「<」 for 「<=」)', 'r23_next',
             seq_replace('KR_T23Next', [('.LOCALREF', 'w'), ('.LOCALREF', 'v'), ('LTE',)], 2, ('LT',))),
            ('V53 the moon text for men (the Enabled test bypassed)', 'r23_life',
             op_replace('KR_T23FeelShowOf', lambda o: o == ['CALLMETHOD', '1'], lambda o: ['VM_POP3_PUSH1']))]


def r23_native_checks(vm, X, counts):
    """--native (r23): the calendar tour's r23 stages (증거/probe_result.json 'r23'): the moon text wherever the game drew the
    moons (the hover preview and page 1 of two heroines, page 1 in the dungeon) = the model on the save's own values; none for
    a man; page 4 of the second heroine = the VM; no moon text left after the member screen / the dungeon window."""
    res = L.readj(L.EVID / 'probe_result.json')
    man = L.readj(O / 'manifest.json')
    assert res['candidate_sha256'] == man['files']['NightRemaster.ain']['sha256'], 'probe_result.json logged by another candidate'
    G, gates = R23['G'], R23['gates']
    r = res['r23']
    st = res['state']
    regs = {X['ev'][e]['fn'] for e in st['regs']}
    today = tuple(st['today'])
    feel = {i + 1: v for i, v in enumerate(st['feel'])}
    dfeel = {int(k): v for k, v in res['r20']['dungeon']['feel'].items()}
    mode = st['mode']
    out = dict(moon={}, page4={}, leak=r['leak'])
    shown = collections.Counter()
    for tag, m in r['moon'].items():
        c = m['person']
        fl = dfeel if tag.startswith('dungeon') else feel
        en = r23_enabled(c, mode) and m['page'] in (0, 1)
        if not en:
            assert not m['exists'], ('native: a moon text where the game draws no moons', tag, c)
            out['moon'][tag] = dict(person=c, page=m['page'], text=None)
            continue
        v = r23_value(G, fl[c], c)
        want = r23_moon_text(G, v, r23_rank(G, v))
        # our part under the moons' own parent (the status root: the moons' box at 374,66 is found under it) and shown with them
        assert m['exists'] and m['show'] == 1 and m['box'] > 0 and m['boxshow'] == 1, ('native moon part', tag, m)
        assert tag.startswith('dungeon') or m['parent'] == m['root'] > 0, ('native moon part parent', tag, m)
        assert (m['x'], m['y']) == (G['label'][0], G['label'][1] + 18), ('native moon part place', tag, m)
        assert m['text'] == want, ('native moon text != model', tag, m['text'], want)
        shown[c] += 1
        out['moon'][tag] = dict(person=c, page=m['page'], text=m['text'].replace('\n', ' / '))
        counts['R23N_moon_texts_equal'] += 1
    assert len([c for c in shown if c in R23_HEROINES]) >= 2, ('native: fewer than two heroines with a moon text', dict(shown))
    for key, blk in r['page4'].items():
        c = blk['person']
        v = r23_value(G, feel[c], c)
        en = r23_enabled(c, mode)
        vm.reset()
        vm.registered = regs
        vm.today = today
        vm.feel = dict(feel)
        vm.game_mode = mode
        want = r23_status_text(X, G, gates, regs, today, c, v, en)
        assert blk['text'] == ko(vm.run('KR_T23StText', [c, int(en)])) == want, ('native page 4 != VM', key, c)
        assert blk['panel_h'] == r23_panel_h(X, G, gates, regs, today, c, v, en), ('native panel height', key, blk['panel_h'])
        assert blk['text_h'] + 16 <= blk['panel_h'], ('native: the text taller than the panel', key, blk['text_h'], blk['panel_h'])
        assert blk['text_w'] <= R23_TEXT_PX, ('native: the text wider than the page', key, blk['text_w'])
        out['page4'][key] = dict(person=c, panel_h=blk['panel_h'], text_h=blk['text_h'], text_w=blk['text_w'], first_line=untag(want.split('\n')[1]))
        counts['R23N_page4_equal'] += 1
    dp = r['dungeon_page4']
    dlog = res['dungeon_run']['log']
    z = re.match(r'DUNGEON date=(\d+)/(\d+) person=(\d+)', next(l for l in dlog if l.startswith('DUNGEON date=')))
    dtoday = (int(z.group(1)), int(z.group(2)))
    dregs = {X['ev'][int(x)]['fn'] for x in next(l for l in dlog if l.startswith('REGS')).split()[1:]}
    dv = r23_value(G, dfeel[dp['person']], dp['person'])
    den = r23_enabled(dp['person'], mode)
    assert dp['panel_h'] == r23_panel_h(X, G, gates, dregs, dtoday, dp['person'], dv, den) and dp['text_h'] + 16 <= dp['panel_h'] and dp['text_w'] <= R23_TEXT_PX, ('native dungeon page 4 size', dp)
    out['page4']['D'] = dict(person=dp['person'], panel_h=dp['panel_h'], text_h=dp['text_h'], text_w=dp['text_w'])
    assert r['leak'] and all(v == 0 for v in r['leak'].values()), ('native: a moon text left behind', r['leak'])
    counts['R23N_leak_checks'] = len(r['leak'])
    return out


# ============================================================== r24: the chart touch-up (V55-V57)
R24_FORWARD = {'KR_CChart': 'KR_C24Chart', 'KR_CDraw': 'KR_C24Draw', 'KR_CWait': 'KR_C24Wait', 'KR_CClick': 'KR_C24Click',
               'KR_CStateLine': 'KR_C24StateLine', 'KR_CPlayNote': 'KR_C24PlayNote'}   # r22 chart functions whose bodies r24 forwards (index kept)
R24_BUTTONS = [(38, '다시 가리기', 880.0), (36, '전체 개방', 1008.0)]   # (KR_CPart of the box, label, x); y 12, 닫기's size / colours
BTN_ALL, BTN_HIDE = CPART(36), CPART(38)
C_LEGEND24 = tint('●', C_SKY) + ' 안 읽음　' + tint('△', C_GRAY) + ' 읽음(게임 전역 기록)　' + tint('회색 칸', C_GRAY) + ' 잠김'
C_STATE24 = {1: '¶△ 읽은 장면입니다 (게임 전역 기록)', 'all': '‡● 안 읽은 장면 · 전체 개방으로 열렸습니다',
             0: '‡● 안 읽은 장면 · 전체 개방하면 재생됩니다', 'noplay': '‡● 안 읽은 장면입니다'}
T24_FLAG_FAIL = '〓이벤트 플로우 차트\n†전체 개방 설정을 저장하지 못했습니다'
KEY_U, KEY_R = 85, 82
R24_KEEP = ['KR_CReplay', 'KR_CReplayRun', 'KR_CDrawFrame', 'KR_CDrawCell', 'KR_CFrame', 'KR_CClear', 'KR_CDo', 'KR_CServe',
            'KR_CTitleTick', 'KR_CTitleServe', 'KR_CCardPage', 'KR_CEventPage', 'KR_CRequest', 'KR_CCanPlay', 'KR_COpen', 'KR_CGlobal']


def flag_text(v):
    return 'YoruKR.Chart.1\r\n%d\r\n' % v


def r24_static(nm, cv, m, counts):
    """S8 (r24): the wait wrapper answers the two buttons and returns the wait's number; the flag writer is r21's; KR_CChart (kept
    byte for byte) has no answer for the button numbers, so its loop draws the same tab and page again; the keys are U / R and
    read only through KR_C24Key; the r22 functions r24 keeps are in place."""
    fid = lambda n: L.fid_of(nm, n)
    w = live_ops(nm, cv, 'KR_C24Wait')
    assert w.count('CALLFUNC 0x%x' % fid('KR_C24WaitRaw')) == 1 and w.count('CALLFUNC 0x%x' % fid('KR_C24Toggle')) == 2, w
    calls = sorted({L.raw_symbol(nm, int(o.split()[1], 16)) for o in w if o.startswith('CALLFUNC ')})
    assert calls == sorted(['KR_C24WaitRaw', 'KR_C24Toggle', 'KR_C24BtnAll', 'KR_C24BtnHide']), calls
    k = w.index('RETURN')
    assert w[k - 3:k + 1] == ['PUSHLOCALPAGE', 'PUSH 0x0', 'X_REF 0x1', 'RETURN'], ('KR_C24Wait does not return the number the wait gave', w[k - 4:k + 1])
    tg = live_ops(nm, cv, 'KR_C24Toggle')
    assert tg.count('CALLFUNC 0x%x' % fid('KR_MSetUnlock')) == 1 and tg.count('CALLFUNC 0x%x' % fid('KR_MUnlockAll')) == 1 \
        and tg.count('CALLFUNC 0x%x' % fid('KR_MNotice')) == 1, tg
    # the chart loop: KR_CChart forwards to KR_C24Chart (S1); it calls what r22's KR_CChart called (the base body, read from the base
    # dump) and nothing else, answers the same numbers, replays once per pass (KR_CReplay, kept byte for byte) and then goes round
    # again (the jump back right after the replay = the chart opens again after a replay)
    ch = live_ops(nm, cv, 'KR_C24Chart')
    bver = L.versions(L.base_paths()['raw'])
    bm = L.read_meta(L.base_paths()['meta'])
    old = [op for _, op in L.live_version(bm, bver, L.fid_of(bm, 'KR_CChart'))['ops'] if not op.startswith('ENDFUNC')]
    names = lambda ops, mm: sorted({L.raw_symbol(mm, int(o.split()[1], 16)) for o in ops if o.startswith('CALLFUNC ')})
    assert names(ch, nm) == names(old, bm), ('KR_C24Chart calls something r22 KR_CChart did not (or lost a call)', sorted(set(names(ch, nm)) ^ set(names(old, bm))))
    k = ch.index('CALLFUNC 0x%x' % fid('KR_CReplay'))
    assert ch.count('CALLFUNC 0x%x' % fid('KR_CReplay')) == 1 and ch[k + 1].startswith('JUMP '), ('the chart does not go round again after a replay', ch[k:k + 2])
    assert ch.count('CALLFUNC 0x%x' % fid('KR_CClear')) == 2 and ch.count('CALLFUNC 0x%x' % fid('KR_MUnlockAll')) == 1, 'KR_C24Chart clear / flag read'

    def args_of(fn):
        return sorted({int(ch[j - 1].split()[1], 16) for j, o in enumerate(ch) if o == 'CALLFUNC 0x%x' % fid(fn) and ch[j - 1].startswith('PUSH 0x')})
    parts_asked, tabs, cells = args_of('KR_CPart'), args_of('KR_CTabBox'), args_of('KR_CCellBox')
    assert parts_asked == [30, 32, 34] and tabs == [0, 9] and cells == [0, 11], (parts_asked, tabs, cells)
    answered = set(parts_asked) | set(range(10, 20)) | set(range(40, 40 + 6 * 11 + 1))
    assert 36 not in answered and 38 not in answered, 'a button number is one of the chart loop\'s answers'
    fr = live_ops(nm, cv, 'KR_C24Frame')
    assert 'PUSH 0x%x' % KEY_U in fr and 'PUSH 0x%x' % KEY_R in fr and fr.count('CALLFUNC 0x%x' % fid('AFL_Parts_EndWaitForClick')) == 6, fr
    kd = 'CALLFUNC 0x%x' % fid('AFL_IsKeyDown')
    added = [L.raw_symbol(nm, i) for i in range(len(m['functions']), len(nm['functions']))]
    users = sorted(n for n in added if kd in live_ops(nm, cv, n))
    assert users == ['KR_C24Key'], users
    for n in R24_KEEP:
        assert nm['functions'][L.fid_of(nm, n)] == m['functions'][L.fid_of(m, n)], ('an r22 function r24 keeps moved', n)
    reach = {L.raw_symbol(nm, f) for f in call_graph_ids(nm, cv, [n for n in added], stop=('view::detail::View_Update', 'KR_CReplayRun'))}
    bad = sorted(n for n in reach if n.startswith(SAVE_CALL_PREFIXES) or n == 'Ａ＿ゲーム終了')
    assert not bad, ('a save / load / title call reachable from the r24 code', bad[:5])
    counts['S8_r24_kept_r22_functions'] = len(R24_KEEP)
    counts['S8_r24_reachable_functions'] = len(reach)
    counts['S8_r24_wait_checked'] = 1


def r24_cell_checks(cand, nm, X, C, counts, mutate=None):
    """V55: all 915 cells drawn locked (no global record, 전체 개방 off) and open (no global record, 전체 개방 on)."""
    vm = chart_vm(cand, nm, X, mutate=mutate)
    chart_state(vm, X, C, 'none')
    n = frames = 0
    for t in range(10):
        first, end = C['first'][t], C['first'][t + 1]
        for p in range(max(1, (end - first + 11) // 12)):
            snap = {}
            for all_ in (False, True):
                vm.parts = {}
                chart_open(vm, all_)
                vm.run('KR_CDraw', [t, p])
                check_page(vm, C, t, p, all_, counts)
                snap[all_] = {s: copy.deepcopy(cell_parts(vm, s)) for s in range(12)}
            for s in range(12):
                i = first + p * 12 + s
                if i >= end:
                    continue
                r = C['rows'][i]
                lk, op = snap[False][s], snap[True][s]
                for j, what in ((2, 'name'), (3, 'id / when'), (4, 'condition')):
                    a, b = lk[j], op[j]
                    assert (a is None) == (b is None), ('V55 a part on one side only', what, r['no'])
                    if a is None:
                        continue
                    assert untag(ko(a['text'])) == untag(ko(b['text'])), ('V55 locked text != open text', what, r['no'], untag(ko(a['text'])), untag(ko(b['text'])))
                    assert a['pos'] == b['pos'] and a.get('font') == b.get('font') and a.get('parent') == b.get('parent'), ('V55 locked text elsewhere', what, r['no'])
                assert r['name'] and ko(lk[2]['text']) == tint(r['name'], C_GRAY), ('V55 the locked name (grey)', r['no'], ko(lk[2]['text']))
                assert ko(lk[3]['text']).startswith(tint('● E%05d' % r['no'], C_GRAY)), ('V55 the locked E number (grey)', r['no'])
                if r['when']:
                    assert ko(lk[3]['text']).endswith(tint(r['when'], C_GRAY)), ('V55 the locked when (grey)', r['no'])
                if r['cond']:
                    assert ko(lk[4]['text']) == ko(op[4]['text']) == tint(r['cond'], C_GRAY), ('V55 condition', r['no'])
                else:
                    assert lk[4] is None and op[4] is None
                assert lk[0]['construct'][0] == op[0]['construct'][0] and lk[0]['pos'] == op[0]['pos'], ('V55 box size / place', r['no'])
                assert lk[0]['construct'][1] == ('fill', 34, 34, 42, 236) and op[0]['construct'][1] == ('fill', 18, 30, 72, 236), ('V55 box colour', r['no'])
                if r['thumb']:
                    assert op[1].get('cg') == r['thumb'] and 'cg' not in lk[1] and lk[1]['construct'][0] == ('create', 120, 90), ('V55 the thumbnail slot', r['no'])
                    frames += 1
                else:
                    assert lk[1] is None and op[1] is None, ('V55 a thumbnail slot without a thumbnail', r['no'])
                n += 1
    assert n == len(C['rows']) == 915, n
    counts['V55_cells_compared'] = n
    counts['V55_locked_thumbnail_frames'] = frames
    return dict(cells=n, thumbnail_frames=frames)


def r24_page_model(vm, X, C, i, all_):
    """(title, items) of the detail page of cell i (an independent model: r19 texts from the base's functions, the state line,
    단계 k/n, the play note, the items)."""
    r = C['rows'][i]
    no = r['no']
    op = copen(vm, C, no, all_)
    if cstate(vm, C, no) == 1:
        state = C_STATE24[1]
    elif all_:
        state = C_STATE24['all']
    elif r['noplay']:
        state = C_STATE24['noplay']
    else:
        state = C_STATE24[0]
    note = ('\n' + C_NOPLAY_NOTE) if r['noplay'] else (('\n' + C_PLAY_NOTE) if op else '')
    play = op and not r['noplay']
    if r['card']:
        k = r['ref'] - 100000
        card = X['cards'][k]
        st = card['stages']
        entry = st[0]
        assert entry == no
        title = '〓' + ko(vm.run('KR_T19CardHead', [k])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [entry])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [entry])) \
            + '\n' + state
        if len(st) > 1:
            title += '\n¶단계 %d/%d 읽음' % (sum(1 for x in st if cstate(vm, C, x) == 1), len(st))
        title += note
        items = ([(13, PLAY)] if play else []) + ([(14, '단계 고르기 (%d단계)' % len(st))] if len(st) > 1 else []) + [(0, '돌아가기')]
    else:
        title = '〓' + ko(vm.run('KR_T19EvHead', [no])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [no])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [no])) \
            + '\n' + state + note
        items = ([(13, PLAY)] if play else []) + [(0, '돌아가기')]
    return title, items


def r24_click(vm, t, i):
    """KR_CClick(t, i) on a drawn page (the chart root exists, Open = 1): the page it opens, answered 돌아가기 (0)."""
    vm.cur = None
    vm.dialogs = []
    vm.script = [0]
    vm.vars['YoruKR.T9.Unwind'] = ''
    vm.run('KR_CClick', [t, i])
    assert not vm.script and len(vm.dialogs) == 1, ('V56 a cell did not open exactly one page', t, i, len(vm.dialogs))
    assert vm.parts[CROOT]['show'] == 1, 'V56 the chart is not shown again after the page'
    d = vm.dialogs[0]
    return d, ko(d['title']), [(x0, ko(x1)) for x0, x1, _, _ in d['items']]


def r24_detail_checks(cand, nm, X, C, counts, mutate=None):
    """V56: the detail page of every cell, locked and open (no global record; 전체 개방 off / on) = the model, and locked = open
    minus 이 장면 재생 (items and the play note) with the locked state line; a locked card's stage list replays a read stage only."""
    vm = chart_vm(cand, nm, X, mutate=mutate)
    chart_state(vm, X, C, 'none')
    n = 0
    for t in range(10):
        first, end = C['first'][t], C['first'][t + 1]
        for p in range(max(1, (end - first + 11) // 12)):
            got = {}
            for all_ in (False, True):
                vm.parts = {}
                chart_open(vm, all_)
                vm.run('KR_CDraw', [t, p])
                for s in range(12):
                    i = first + p * 12 + s
                    if i >= end:
                        break
                    d, title, items = r24_click(vm, t, i)
                    want_t, want_i = r24_page_model(vm, X, C, i, all_)
                    assert title == want_t, ('V56 page title != model', C['rows'][i]['no'], all_, title, want_t)
                    assert items == want_i, ('V56 page items != model', C['rows'][i]['no'], all_, items, want_i)
                    check_dialog(d, counts)
                    got[(all_, i)] = (title, items)
            for s in range(12):
                i = first + p * 12 + s
                if i >= end:
                    break
                r = C['rows'][i]
                (lt, li), (ot, oi) = got[(False, i)], got[(True, i)]
                assert li == [x for x in oi if x[0] != 13] and ((13, PLAY) in oi) == (not r['noplay']), ('V56 locked items != open items minus 이 장면 재생', r['no'], li, oi)
                lines = ot.split('\n')
                assert C_STATE24['all'] in lines, ('V56 open state line', r['no'])
                lines[lines.index(C_STATE24['all'])] = C_STATE24['noplay' if r['noplay'] else 0]
                if not r['noplay']:
                    assert lines[-1] == C_PLAY_NOTE, ('V56 open play note', r['no'])
                    lines = lines[:-1]
                assert lt.split('\n') == lines, ('V56 locked page != open page minus 이 장면 재생', r['no'], lt, ot)
                n += 1
                counts['V56_locked_pages_without_play'] += 1
    assert n == len(C['rows']), n
    counts['V56_pages_compared'] = n
    # a locked card (entry unread) whose second stage is read: the card page has no 이 장면 재생, its stage list leads to the read
    # stage's page with 이 장면 재생 (replayed through the memory-mode path) and to the locked entry's page without it
    vm = chart_vm(cand, nm, X, mutate=mutate)
    chart_state(vm, X, C, 'none')
    r = next(r for r in C['rows'] if r['card'] and X['cards'][r['ref'] - 100000]['size'] >= 2 and not r['noplay']
             and vm.msg_of.get(X['cards'][r['ref'] - 100000]['stages'][1], -1) >= 0)
    k = r['ref'] - 100000
    st = X['cards'][k]['stages']
    vm.flags = {vm.msg_of[st[1]]}
    i = C['rows'].index(r)
    t = r['tab']
    kk = i - C['first'][t]
    ds = chart_session(vm, 2, goto(t, kk // 12) + [box_of(kk % 12), 14, 100, 0, 101, 13, CPART(30)])     # + close the chart that comes back
    pages = [d for d in ds if d.get('kind') != 'chart']
    cardpg, stagepg, lockedpg, stagepg2, openpg = pages
    assert [x for x, _, _, _ in cardpg['items']] == [14, 0] and C_STATE24[0] in ko(cardpg['title']).split('\n'), ('V56 locked card page', cardpg['items'])
    assert [x for x, _, _, _ in lockedpg['items']] == [0] and C_STATE24[0] in ko(lockedpg['title']).split('\n'), ('V56 the locked entry stage', lockedpg['items'])
    assert [x for x, _, _, _ in openpg['items']] == [13, 0] and C_STATE24[1] in ko(openpg['title']).split('\n'), ('V56 the read stage', openpg['items'])
    assert len(vm.replays) == 1 and vm.replays[0]['no'] == st[1], ('V56 the read stage of a locked card did not replay', vm.replays)
    for d in pages:
        check_dialog(d, counts)
    counts['V56_locked_card_stage_paths'] += 1
    # the not-playable scene (the battle): locked -> 「● 안 읽은 장면입니다」 + 「재생 불가(게임 안에서만)」, no 이 장면 재생
    real = [i for i, r in enumerate(C['rows']) if r['noplay']]
    for i in real:
        vm = chart_vm(cand, nm, X, mutate=mutate)
        chart_state(vm, X, C, 'none')
        t = C['rows'][i]['tab']
        p = (i - C['first'][t]) // 12
        vm.parts = {}
        chart_open(vm, False)
        vm.run('KR_CDraw', [t, p])
        d, title, items = r24_click(vm, t, i)
        lines = title.split('\n')
        assert C_STATE24['noplay'] in lines and lines[-1] == C_NOPLAY_NOTE and 13 not in [x for x, _ in items], ('V56 locked not-playable page', title, items)
        counts['V56_locked_not_playable'] += 1
    return dict(pages=n, locked_card=r['no'], not_playable=[C['rows'][i]['no'] for i in real])


def r24_fresh_page(cand, nm, X, C, flags, mem, t, p, all_, ctx, last=None):
    """the parts a fresh draw of (t, p) gives under the same global records and 전체 개방 value (what a redraw must equal); `last` =
    the cell a replay just played (its border gold)."""
    v = chart_vm(cand, nm, X)
    v.flags, v.mem_enabled = set(flags), set(mem)
    v.parts = {}
    v.title_scene()
    chart_open(v, all_, ctx)
    if last is not None:
        v.vars['YoruKR.C.Last'] = str(last)
    v.run('KR_CDraw', [t, p])
    return v.chart_snapshot()


def r24_resume_checks(cand, nm, X, C, counts, mutate=None):
    """V58 (the user's 14:00 addition): a replay started from the chart ends back in the chart - the same tab and page, the played
    cell's border gold (YoruKR.C.Last), the parts exactly a fresh draw of that page after the replay; nothing of the chart exists
    while the replay runs; a second replay from the chart that came back comes back again; a stage replayed from a card's list
    marks the card; only 닫기 / cancel leave (Last cleared)."""
    mk = lambda: chart_vm(cand, nm, X, mutate=mutate)
    out = {}
    def scene_page(t, p0):
        """the first page from p0 on with two playable scene cells (a page after the first one: the page must be kept too)."""
        first, end = C['first'][t], C['first'][t + 1]
        for p in range(p0, max(1, (end - first + 11) // 12)):
            cells = [i for i in range(first + p * 12, min(end, first + p * 12 + 12)) if not C['rows'][i]['card'] and not C['rows'][i]['noplay']]
            if len(cells) >= 2:
                return p, cells
        raise AssertionError(('V58 no page with two playable scene cells', t, p0))
    for ctx, t, p0, leave in ((1, 1, 3, CPART(30)), (2, 6, 1, 0), (1, 8, 2, CPART(30))):
        vm = mk()
        chart_state(vm, X, C, 'none')
        first, end = C['first'][t], C['first'][t + 1]
        p, cells = scene_page(t, p0)
        assert p >= 1, p
        i1, i2 = cells[0], cells[-1]
        s1, s2 = i1 - first - p * 12, i2 - first - p * 12
        chart_session(vm, ctx, goto(t, p) + [box_of(s1), 13, box_of(s2), 13, leave], all_=True)
        cw = vm.charts
        k = 1 + 1 + p                                    # the first wait on (t, p)
        assert len(cw) == k + 2 and [d['answer'] for d in cw[k - 1:]] == [box_of(s1), box_of(s2), leave], ('V58 chart waits', ctx, len(cw), [d['answer'] for d in cw[k - 1:]])
        nos = [C['rows'][i1]['no'], C['rows'][i2]['no']]
        assert [r['no'] for r in vm.replays] == nos and all(r['ctx'] == ctx for r in vm.replays), ('V58 replays', vm.replays)
        flags = set()
        for j, (rp, cell) in enumerate(zip(vm.replays, (i1, i2))):
            assert rp['ours'] == [] and rp['open'] == '' and rp['unwind'] == '' and rp['play'] == '' and not rp['dialog_open'], ('V58 the chart was not closed for the replay', j, rp)
            if ctx == 1:
                assert rp['title_root_show'] == 0, ('V58 the title root during the replay', rp['title_root_show'])
            m = vm.msg_of[nos[j]]
            if m >= 0:
                flags.add(m)
            d = cw[k + j]
            assert d['open'] == '1' and d['ctx'] == str(ctx) and d['all'] == '1', ('V58 the chart after a replay', j, d['open'], d['ctx'], d['all'])
            fresh = r24_fresh_page(cand, nm, X, C, flags, set(), t, p, True, ctx, last=cell)
            assert d['parts'] == fresh, ('V58 the chart that came back is not the same tab and page (the played cell marked)', ctx, t, p, j,
                                         [(n, d['parts'].get(n, {}).get('text'), fresh.get(n, {}).get('text')) for n in sorted(set(d['parts']) | set(fresh))
                                          if d['parts'].get(n) != fresh.get(n)][:3])
            assert d['parts'][box_of(cell - first - p * 12)]['construct'][2][5:8] == (255, 214, 110), 'V58 the played cell is not marked'
            counts['V58_chart_back_after_replay'] += 1
        assert vm.vars.get('YoruKR.C.Last', '') == '' and not vm.ours22(), ('V58 state after the chart was closed', vm.vars.get('YoruKR.C.Last'))
        if ctx == 1:
            assert vm.parts[VM.TITLE_ROOT]['show'] == 1
        counts['V58_sessions'] += 1
        out['ctx%d_tab%d_page%d' % (ctx, t, p)] = nos
    # a stage from a card's list: the chart comes back on the card's page with the card marked
    vm = mk()
    chart_state(vm, X, C, 'none')
    r = next(r for r in C['rows'] if r['card'] and X['cards'][r['ref'] - 100000]['size'] >= 2 and not r['noplay'])
    i = C['rows'].index(r)
    t = r['tab']
    kk = i - C['first'][t]
    st = X['cards'][r['ref'] - 100000]['stages']
    chart_session(vm, 2, goto(t, kk // 12) + [box_of(kk % 12), 14, 101, 13, CPART(30)], all_=True)
    assert [x['no'] for x in vm.replays] == [st[1]], ('V58 stage replay', vm.replays)
    d = vm.charts[-1]
    fl = {vm.msg_of[st[1]]} - {-1}
    assert d['parts'] == r24_fresh_page(cand, nm, X, C, fl, set(), t, kk // 12, True, 2, last=i), 'V58 the chart after a stage replay'
    counts['V58_card_stage_back'] += 1
    # closing without a replay: no second chart, Last cleared; a new chart does not mark the old cell
    vm = mk()
    chart_state(vm, X, C, 'none')
    vm.vars['YoruKR.C.Last'] = '5'                     # left over from an earlier chart (a stopped replay, say)
    chart_session(vm, 1, [CPART(30)])
    assert len(vm.charts) == 1 and vm.vars.get('YoruKR.C.Last', '') == '' and not any(p_['construct'][2][5:8] == (255, 214, 110)
                                                                                      for n_, p_ in vm.charts[0]['parts'].items() if 40 <= n_ - CROOT < 112 and (n_ - CROOT - 40) % 6 == 0), 'V58 a stale mark'
    counts['V58_no_stale_mark'] += 1
    out['card_stage'] = st[1]
    return out


def r24_button_checks(cand, nm, X, C, counts, mutate=None):
    """V57: the two buttons (and U / R): the flag file written (1 / 0, the menu bar's file and bytes), the chart drawn again at
    once on the same tab and page in the new state, parts gone after the chart, a failed write reported with the disk's value
    kept, a key held while the page was drawn ignored, the flag read by the next chart."""
    mk = lambda: chart_vm(cand, nm, X, mutate=mutate)
    out = {}
    presses = [BTN_ALL, BTN_HIDE, BTN_HIDE, BTN_ALL, BTN_ALL]
    for ctx, t, p in ((1, 2, 1), (2, 8, 2), (1, 9, 0), (2, 0, 3)):
        vm = mk()
        chart_state(vm, X, C, 'partial', rnd=57 + t)
        ds = chart_session(vm, ctx, goto(t, p) + presses + [CPART(30)], all_=False)
        cw = vm.charts
        k0 = 1 + 1 + p                                  # the first wait on (t, p): after the tab and p 「다음 쪽」
        assert len(cw) == k0 + len(presses), ('V57 chart waits', ctx, t, p, len(cw))
        assert [d['answer'] for d in cw[k0 - 1:]] == presses + [CPART(30)], [d['answer'] for d in cw[k0 - 1:]]
        want = 0
        for j, b in enumerate(presses):
            want = 1 if b == BTN_ALL else 0
            d = cw[k0 + j]
            assert d['all'] == str(want) and d['flag'] == flag_text(want), ('V57 the flag after a button', ctx, t, p, j, d['all'], d['flag'])
            fresh = r24_fresh_page(cand, nm, X, C, vm.flags, vm.mem_enabled, t, p, bool(want), ctx)
            assert d['parts'] == fresh, ('V57 the chart was not drawn again on the same tab and page in the new state', ctx, t, p, j,
                                         [(n, d['parts'].get(n, {}).get('text'), fresh.get(n, {}).get('text')) for n in sorted(set(d['parts']) | set(fresh))
                                          if d['parts'].get(n) != fresh.get(n)][:3])
            head = ko(d['parts'][CPART(1)]['text'])
            assert (tint('전체 개방', C_GOLD) in head) == bool(want), ('V57 header 「전체 개방」', head)
            counts['V57_presses_redrawn_in_place'] += 1
        assert vm.disk[CHART] == flag_text(want) and not [n for n in vm.ours22()], 'V57 flag / parts after the chart'
        assert not vm.replays and len([d for d in ds if d.get('kind') != 'chart']) == 0, 'V57 a button opened a window or a replay'
        # the flag carries over: the next chart (a restarted game: only the disk) opens with what the button wrote
        v2 = mk()
        v2.disk, v2.dirs = dict(vm.disk), set(vm.dirs)
        v2.title_scene()
        v2.script = [CPART(30)]
        v2.run('KR_CChart', [1])
        assert v2.charts[0]['all'] == str(want) and v2.run('KR_MUnlockAll') == want and v2.ours22() == [], ('V57 the flag is not what the next chart reads', v2.charts[0]['all'])
        counts['V57_sessions'] += 1
    # a failed write: the notice (the chart hidden behind it), the value the disk holds kept on screen, drawn again in place
    for disk_v, btn in ((0, BTN_ALL), (1, BTN_HIDE)):
        vm = mk()
        chart_state(vm, X, C, 'none')
        vm.fail_write = {CHART}
        ds = chart_session(vm, 1, [btn, OK, CPART(30)], all_=bool(disk_v))
        vm.fail_write = set()
        wins = [d for d in ds if d.get('kind') != 'chart']
        assert len(wins) == 1 and ko(wins[0]['title']) == T24_FLAG_FAIL and wins[0].get('chart_root_show') == 0, ('V57 failed write notice', [ko(d['title'])[:20] for d in wins])
        check_dialog(wins[0], counts)
        assert vm.charts[1]['all'] == str(disk_v) and vm.charts[1]['flag'] == flag_text(disk_v) and vm.charts[1]['parts'][CROOT]['show'] == 1, ('V57 after a failed write', vm.charts[1]['all'])
        counts['V57_failed_write_reported'] += 1
    # the keys: U = 전체 개방, R = 다시 가리기 (press and release); a key held while the page is drawn does nothing; the arrows as r22
    def keys(key, down):
        def each(v, f):
            v.keys[key] = int(f in down)
        return each
    vm = mk()
    chart_state(vm, X, C, 'none')
    chart_session(vm, 1, [Wait(8, CPART(30), keys(KEY_U, {1, 2})), Wait(8, CPART(30), keys(KEY_R, {2, 3, 4})), CPART(30)])
    assert [d['answer'] for d in vm.charts] == [BTN_ALL, BTN_HIDE, CPART(30)] and vm.charts[0].get('ended_by') == BTN_ALL and vm.charts[1].get('ended_by') == BTN_HIDE, \
        ('V57 U / R keys', [d.get('answer') for d in vm.charts])
    assert [d['all'] for d in vm.charts] == ['0', '1', '0'] and vm.disk[CHART] == flag_text(0), [d['all'] for d in vm.charts]
    counts['V57_keys'] += 2
    vm = mk()
    chart_state(vm, X, C, 'none')
    vm.keys[KEY_U] = 1                                  # held down when the chart draws its page
    chart_session(vm, 1, [Wait(8, CPART(30), keys(KEY_U, {0, 1, 2}))])
    assert len(vm.charts) == 1 and vm.charts[0].get('ended_by') is None and vm.disk[CHART] == flag_text(0), ('V57 a held key fired', vm.charts[0].get('ended_by'))
    counts['V57_held_key_ignored'] += 1
    vm = mk()
    chart_state(vm, X, C, 'none')

    def right(v, f):
        v.inputs['IsClickRight'] = int(f == 1)
    chart_session(vm, 1, [Wait(5, CPART(30), right), CPART(30)])
    assert vm.charts[0].get('ended_by') == 2 and ko(vm.charts[1]['parts'][CPART(3)]['text']).startswith('2 / '), 'V57 the arrow keys (r22) lost'
    counts['V57_arrows_kept'] += 1
    out.update(sessions=counts['V57_sessions'], presses=counts['V57_presses_redrawn_in_place'])
    return out


def r24_native_checks(cand, nm, X, C, counts):
    """--native (r24): the chart tours on this candidate (증거/probe_chart_r24.json) and the per-kind replays = the VM."""
    doc = L.readj(L.EVID / 'probe_chart_r24.json')
    man = L.readj(O / 'manifest.json')
    cs = man['files']['NightRemaster.ain']['sha256']
    out = {}
    t = doc['title']
    assert t.get('candidate_sha256') == cs, 'probe_chart_r24.json title tour logged by another candidate'
    assert t.get('exit_code') == 0 and not t.get('vm_error') and not t.get('message') and not t.get('timeout') and t['log'][-1] == 'END', \
        ('title tour', t.get('exit_code'), t.get('vm_error'), t.get('message'), t['log'][-3:])
    log = t['log']
    glob = {l.split()[1]: l for l in log if l.startswith('GLOBAL ')}
    tgt = next(l for l in log if l.startswith('TARGET '))
    tt, tp = int(re.search(r'tab=(\d+)', tgt).group(1)), int(re.search(r'page=(\d+)', tgt).group(1))
    la, lb = [int(x) for x in re.search(r'locked=(\d+),(\d+)', tgt).group(1, 2)]
    lthumb = int(re.search(r'locked_thumb=(-?\d+)', tgt).group(1))
    ia, ib = C['first'][tt] + tp * 12 + la, C['first'][tt] + tp * 12 + lb
    plan = {'TAB0 P1': ('chart1', 0, 0, None, None), 'TAB6 P1': ('chart1', 6, 0, None, None), 'TAB8 P1': ('chart1', 8, 0, None, None),
            'TARGET LOCKED': ('chart1', tt, tp, None, None), 'TARGET AFTER DETAIL': ('chart1', tt, tp, None, None),
            'TARGET BUTTON ALL': ('chart1', tt, tp, True, None), 'TARGET BUTTON HIDE': ('chart1', tt, tp, False, None),
            'TARGET UNLOCKED': ('chart2', tt, tp, None, None), 'TARGET RESUMED': ('resumed', tt, tp, None, ia),
            'TARGET REVERTED': ('chart3', tt, tp, None, None)}
    blocks_ = r22_blocks(log, 'CELLS')
    assert set(blocks_) == set(plan), sorted(blocks_)
    for tag, (g, tab, page, force, last) in plan.items():
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, glob[g])
        if force is not None:
            all_ = force
        vm.parts = {}
        chart_open(vm, all_)
        if last is not None:
            vm.vars['YoruKR.C.Last'] = str(last)
        vm.run('KR_CDraw', [tab, page])
        want = cells_text(vm)
        got = blocks_[tag][0]
        assert got == want, ('native chart page differs from the VM', tag, [(a, b) for a, b in zip(got.split('\n'), want.split('\n')) if a != b][:3])
        counts['R24N_pages_equal_vm'] += 1
    lt = blocks_['TARGET LOCKED'][0]
    assert '？？？' not in lt, 'native: 「？？？」 on the locked target page'
    # CG or empty frame, from the screenshots (the probe does not ask the part: those getters change the part's type): an empty
    # frame = its border (70,70,82) and fill (22,22,28) at the slot; a CG = a picture (many colours) in the slot
    pix = {}
    for tag, shot in (('TARGET LOCKED', 'chart_target_locked'), ('TARGET BUTTON ALL', 'chart_button_all'), ('TARGET BUTTON HIDE', 'chart_button_hide'),
                      ('TAB8 P1', 'chart_tab_memory_p1'), ('TAB0 P1', 'chart_tab_apr_p1')):
        g, tab, page, force, last = plan[tag]
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, glob[g])
        all_ = all_ if force is None else force
        vm.parts = {}
        chart_open(vm, all_)
        vm.run('KR_CDraw', [tab, page])
        from PIL import Image
        im = Image.open(L.EVID / 'probe' / (shot + '.png')).convert('RGB')
        frames_ = cgs = 0
        for s_ in range(12):
            th = vm.parts.get(box_of(s_) + 1)
            if th is None:
                continue
            cx, cy = 24 + (s_ % 4) * 309 + 8, 114 + (s_ // 4) * 182 + 8
            if 'cg' in th:
                colours = len(im.crop((cx + 2, cy + 2, cx + 118, cy + 88)).getcolors(1 << 16) or [])
                assert colours > 64, ('native: no picture in an open thumbnail slot', tag, s_, colours)
                cgs += 1
            else:
                assert im.getpixel((cx, cy)) == (70, 70, 82) and im.getpixel((cx + 60, cy + 45)) == (22, 22, 28), ('native: the empty frame not drawn', tag, s_, im.getpixel((cx, cy)), im.getpixel((cx + 60, cy + 45)))
                frames_ += 1
        pix[tag] = dict(pictures=cgs, empty_frames=frames_)
        counts['R24N_thumbnail_slots_pixel_checked'] += cgs + frames_
    assert pix['TARGET LOCKED']['empty_frames'] >= (1 if lthumb >= 0 else 0) and pix['TARGET BUTTON ALL']['empty_frames'] == 0, pix
    out['thumbnail_pixels'] = pix
    # r24 (14:00): after the replay of A the chart came back on the same tab and page with A's border gold (the block above = the VM
    # with Last = A); the gold border at A's box corner in the shot, no gold on another cell
    rs = next(l for l in log if l.startswith('RESUMED chart after the replay'))
    assert ' open=1 ' in rs and (' last=%d ' % ia) in rs and ' ctx=1 ' in rs, ('native: the chart after the replay', rs)
    from PIL import Image
    im = Image.open(L.EVID / 'probe' / 'chart_resumed.png').convert('RGB')
    corner = lambda s_: (24 + (s_ % 4) * 309, 114 + (s_ // 4) * 182)
    assert im.getpixel(corner(la)) == (255, 214, 110), ('native: the replayed cell is not marked', im.getpixel(corner(la)))
    assert all(im.getpixel(corner(s_)) != (255, 214, 110) for s_ in range(12) if s_ != la), 'native: another cell marked'
    counts['R24N_chart_back_after_replay'] = 1
    # the flag file as the chart read it after each button (the probe's save folder starts without one)
    fl = {l.split()[1]: l for l in log if l.startswith('FLAG ')}
    assert fl['before'] == 'FLAG before file=0 unlock=0 all=0 len=0', fl['before']
    assert fl['button_all'] == 'FLAG button_all file=1 unlock=1 all=1 len=%d' % len(flag_text(1)), fl['button_all']
    assert fl['button_hide'] == 'FLAG button_hide file=1 unlock=0 all=0 len=%d' % len(flag_text(0)), fl['button_hide']
    counts['R24N_flag_after_buttons'] = 2
    # the windows (title + items) = the VM
    dl = r22_blocks(log, 'DIALOG')

    def page_block(g, i, all_):
        vm = chart_vm(cand, nm, X)
        native_state(vm, C, glob[g])
        vm.parts = {}
        chart_open(vm, all_)
        vm.run('KR_CDraw', [tt, tp])
        d, title, items = r24_click(vm, tt, i)
        mt, mi = r24_page_model(vm, X, C, i, all_)
        assert (title, items) == (mt, mi), ('VM page != model', i)
        return title + '\nITEMS ' + ''.join('%d:%s|' % x for x in items), items
    want1, items1 = page_block('chart1', ia, False)
    assert dl.get('chart1') == [want1] and 13 not in [x for x, _ in items1], ('native locked cell page', dl.get('chart1'), want1)
    want2, items2 = page_block('chart2', ia, True)
    assert dl.get('chart2') == [want2] and 13 in [x for x, _ in items2], ('native open cell page', dl.get('chart2'), want2)
    assert dl.get('unlock') == [T_UNLOCK + '\nITEMS 1:확인|'] and dl.get('revert') == [T_REVERT + '\nITEMS 1:확인|'], (dl.get('unlock'), dl.get('revert'))
    assert dl.get('reset_no') == [T_RESET + '\nITEMS 12:아니요|11:예|'], ('native title reset confirm', dl.get('reset_no'))
    counts['R24N_windows_equal_vm'] = 5
    rn = next((l for l in log if l.startswith('RESET NO ')), '')
    assert rn == 'RESET NO marker=0 reset_req=0 request=0 ours=0', ('native title reset 아니요', rn)
    assert any(l.startswith('REPLAY first message memory=1') and 'ours=0' in l for l in log), 'title tour: the replay did not run in memory mode with the chart closed'
    ret = next(l for l in log if l.startswith('RETURNED to the title'))
    assert 'ours=0' in ret and 'open= ' in ret and 'play= ' in ret, ret
    g1, g3 = set(glob['chart1'].split()[3:]), set(glob['chart3'].split()[3:])
    assert str(ia) not in g1 and str(ib) not in g1, 'the target cells were open before the unlock'
    assert str(ia) in g3 and str(ib) not in g3, ('after the revert: the replayed scene keeps its read mark, the other locks again', str(ia) in g3, str(ib) in g3)
    counts['R24N_title_tour'] = 1
    shots = L.EVID / 'probe'
    px = diff_png(shots / 'chart_title_after_chart1.png', shots / 'chart_title_after_replay.png')
    px_rn = diff_png(shots / 'chart_title_after_chart1.png', shots / 'chart_title_after_reset_no.png')
    px_bh = diff_png(shots / 'chart_target_locked.png', shots / 'chart_button_hide.png')
    px_ad = diff_png(shots / 'chart_target_locked.png', shots / 'chart_target_after_detail.png')
    out['title'] = dict(pages=len(plan), locked_page_event=C['rows'][ia]['no'], replayed=C['rows'][ia]['no'], relocked=C['rows'][ib]['no'],
                        locked_thumbnail_slot=lthumb, title_after_chart_vs_after_replay_px=px, title_after_chart_vs_after_reset_no_px=px_rn,
                        target_locked_vs_after_hide_px=px_bh, target_locked_vs_after_detail_px=px_ad, seconds=t.get('seconds'))
    assert px == 0 and px_rn == 0, ('title pixels after the chart / the replay / reset 아니요 differ', px, px_rn)
    assert px_bh == 0 and px_ad == 0, ('the target page after 다시 가리기 / after the detail page is not pixel-identical to the first draw', px_bh, px_ad)
    counts['R24N_title_pixels_equal'] = 2
    h = doc.get('home')
    if h:
        assert h.get('candidate_sha256') == cs and h.get('exit_code') == 0 and h['log'][-1] == 'END', ('home tour', h.get('exit_code'), h['log'][-3:])
        hl = h['log']
        assert any(l.startswith('REPLAY first message memory=1') and 'ours=0' in l for l in hl), 'home tour: no memory-mode replay'
        assert any(l.startswith('RETURNED to the home menu') and 'ours=0' in l for l in hl)
        hb = r22_blocks(hl, 'CELLS')['HOME OPEN'][0]
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, next(l for l in hl if l.startswith('GLOBAL home')))
        vm.parts = {}
        chart_open(vm, all_)
        month = int(re.search(r'HEAD .*?　(\d+)월　', hb).group(1))
        vm.run('KR_CDraw', [month - 4, 0])
        assert hb == cells_text(vm), ('native home chart page differs from the VM', [(a, b) for a, b in zip(hb.split('\n'), cells_text(vm).split('\n')) if a != b][:3])
        # r24 (14:00): the home chart came back after the replay on its first page, the replayed cell marked
        hs = int(re.search(r'HOME target cell (\d+) event', next(l for l in hl if l.startswith('HOME target cell'))).group(1))
        hi = C['first'][month - 4] + hs
        hr = r22_blocks(hl, 'CELLS')['HOME RESUMED'][0]
        vm = chart_vm(cand, nm, X)
        all_ = native_state(vm, C, next(l for l in hl if l.startswith('GLOBAL resumed')))
        vm.parts = {}
        chart_open(vm, all_)
        vm.vars['YoruKR.C.Last'] = str(hi)
        vm.run('KR_CDraw', [month - 4, 0])
        assert hr == cells_text(vm), ('native home chart after the replay differs from the VM', [(a, b) for a, b in zip(hr.split('\n'), cells_text(vm).split('\n')) if a != b][:3])
        from PIL import Image
        im = Image.open(L.EVID / 'probe' / 'chart_home_resumed.png').convert('RGB')
        assert im.getpixel((24 + (hs % 4) * 309, 114 + (hs // 4) * 182)) == (255, 214, 110), 'native: the replayed home cell is not marked'
        counts['R24N_home_chart_back_after_replay'] = 1
        pxh = diff_png(shots / 'chart_home_before.png', shots / 'chart_home_after.png')
        out['home'] = dict(home_before_vs_after_px=pxh, seconds=h.get('seconds'))
        assert pxh == 0, ('home pixels after the replay differ', pxh)
        counts['R24N_home_tour'] = 1
    k = L.readj(L.EVID / 'replay_kinds.json')
    assert k['candidate_sha256'] == cs and all(e.get('candidate_sha256') == cs for e in k['events'].values()), 'replay_kinds.json from another candidate'
    out['kinds'] = k['verdicts']
    counts['R24N_kinds'] = len(k['events'])
    return out


def r24_defects():
    """r24's four: the chart not coming back after a replay, a locked cell without its name, a button that does not write the flag, a
    button that does not redraw."""
    def no_redraw(ops):
        hits = [i for i, o in enumerate(ops) if o == ['CALLFUNC', 'KR_C24Toggle']]
        if not hits or ops[hits[0] + 1][0] != 'JUMP':
            raise RuntimeError('defect could not be planted: no jump after the first toggle in KR_C24Wait')
        ops[hits[0] + 1] = ['VM_JUMP0']              # toggled, then waits again without returning -> KR_CChart does not draw
        return ops
    def no_resume(ops):
        hits = [i for i, o in enumerate(ops) if o == ['CALLFUNC', 'KR_CReplay']]
        if len(hits) != 1 or ops[hits[0] + 1][0] != 'JUMP':
            raise RuntimeError('defect could not be planted: no jump back after the replay in KR_C24Chart')
        ops[hits[0] + 1] = ['RETURN']                 # the resume ignored: back to the title / home menu after a replay (r22)
        return ops
    return [('V58 the chart does not come back after a replay (the resume ignored)', 'r24_resume', {'KR_C24Chart': no_resume}),
            ('V55 a locked cell without its name', 'r24_cells',
             op_replace('KR_C24DrawCell', lambda o: o == ['CALLFUNC', 'KR_CCellName'], lambda o: ['VM_POP_PUSHS'], nth=1)),
            ('V57 a button that does not write the flag file', 'r24_buttons',
             op_replace('KR_C24Toggle', lambda o: o == ['CALLFUNC', 'KR_MSetUnlock'], lambda o: ['VM_POP_PUSH1'])),
            ('V57 a button that does not redraw the chart (the wait goes on)', 'r24_buttons', {'KR_C24Wait': no_redraw})]


R23 = {}


def main():
    selftest = '--selftest' in sys.argv
    native = '--native' in sys.argv
    t0 = time.time()
    man = L.readj(O / 'manifest.json')
    bp = L.base_paths()
    base = bp['ain']
    cand = O / 'NightRemaster.ain'
    assert L.sha(base) == L.BASE_AIN_SHA and L.sha(cand) == man['files']['NightRemaster.ain']['sha256']
    m = L.read_meta(bp['meta'])
    nm = L.read_meta(W / 'candidate_meta.json')
    assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
    X = expectations()
    counts = collections.Counter()
    R23['G'] = game_rules()
    R23['gates'] = r23_gates()
    VM.GAME = dict(bounds=R23['G']['bounds'], rates=R23['G']['rates'], rate_default=R23['G']['rate_default'])
    vm = VM(cand, nm)
    if native:
        # the calendar tour (probe_calendar_tour_r24.py, r20 / r23 stages), the chart tours with r24's steps, the per-kind replays
        out = native_checks(vm, X, counts)
        C = chart_expect(X, vm)
        r24n = r24_native_checks(cand, nm, X, C, counts)
        r23n = r23_native_checks(vm, X, counts)
        result = dict(schema='yoru-chart-r24.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, r24=r24n, r23=r23n,
                      counts=dict(counts))
        L.writej(W / 'native_compare.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=1))
        print('NATIVE = VM')
        return
    frames = static_checks(base, cand, man, m, nm, counts)
    if '--r24-only' in sys.argv:                 # development: the static checks and the chart checks (r22 with r24's cells, r24)
        C = chart_expect(X, vm)
        v22 = chart_vm(cand, nm, X)
        out = dict(tables=chart_table_checks(v22, X, C, counts))
        chart_page_checks(v22, X, C, counts)
        out['flow'] = chart_flow_checks(cand, nm, X, C, counts)
        out['confine'] = chart_confine_checks(cand, nm, X, C, counts)
        out['title'] = title_checks(cand, nm, X, C, counts)
        out['noplay'] = noplay_checks(cand, nm, X, C, counts)
        out['r24_cells'] = r24_cell_checks(cand, nm, X, C, counts)
        out['r24_pages'] = r24_detail_checks(cand, nm, X, C, counts)
        out['r24_buttons'] = r24_button_checks(cand, nm, X, C, counts)
        out['r24_resume'] = r24_resume_checks(cand, nm, X, C, counts)
        print(json.dumps(dict(counts=dict(counts), chart=out), ensure_ascii=False, indent=1, default=str))
        print('R24 CHART VERIFIED', round(time.time() - t0, 1), 's')
        return
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
    vm.registered = regs
    affinity_checks(vm, X, counts)
    rules = name_rule_checks(vm, X, counts)
    # r20
    states = r20_states(X, regs, abo, mid_regs, mid_today)
    r20_count_checks(vm, X, counts, states)
    widest20 = r20_text_checks(vm, X, counts, states)
    r20_status_page_checks(vm, X, counts, regs)
    r20_partner_checks(vm, X, counts, regs)
    r20_real = r20_real_save_checks(vm, X, counts)
    source = r20_training_source(counts)
    walkc = r20_walk_counter_absence(m, counts)
    # r21
    mk = lambda: r21_fresh(cand, nm)
    r21_rows = r21_request_checks(mk, counts)
    r21_flag = r21_flag_checks(mk, counts)
    r21_reset = r21_reset_checks(mk, counts)
    r21_result = r21_result_checks(mk, counts)
    r21_scope = r21_scope_checks(mk, counts)
    r21_style_checks(counts)
    # r22
    C = chart_expect(X, vm)
    v22 = chart_vm(cand, nm, X)
    r22_tables = chart_table_checks(v22, X, C, counts)
    chart_page_checks(v22, X, C, counts)
    r22_flow = chart_flow_checks(cand, nm, X, C, counts)
    r22_confine = chart_confine_checks(cand, nm, X, C, counts)
    r22_title = title_checks(cand, nm, X, C, counts)
    r22_noplay = noplay_checks(cand, nm, X, C, counts)
    # r23
    G, gates = R23['G'], R23['gates']
    r23_value_checks(vm, X, G, counts)
    regs_sets = [('none', set()), ('partial', regs), ('all', all_regs), ('all_but_one', abo)]
    r23_next_checks(vm, X, G, gates, counts, regs_sets)
    widest23 = r23_text_checks(vm, X, G, gates, counts, states)
    r23_lifecycle_checks(vm, X, G, gates, counts, regs, (10, 14))
    r23_real = r23_real_save_checks(vm, X, G, gates, counts)
    # r24
    r24_cells = r24_cell_checks(cand, nm, X, C, counts)
    r24_pages = r24_detail_checks(cand, nm, X, C, counts)
    r24_buttons = r24_button_checks(cand, nm, X, C, counts)
    r24_resume = r24_resume_checks(cand, nm, X, C, counts)
    result = dict(schema='yoru-chart-r24.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,
                  counts=dict(counts), vm_steps=vm.steps, widest_title=WIDEST['title'], widest_title_len=len(WIDEST['title']),
                  widest_item=WIDEST['item'], widest_item_len=len(WIDEST['item']), widest_drawer_row=WIDEST['drawer'],
                  widest_drawer_row_len=len(WIDEST['drawer']), widest_drawer_row_units=units_w(WIDEST['drawer']),
                  seconds=round(time.time() - t0, 1), saves_checked=counts['S4_saves'], frames_checked=counts['S4_frames'],
                  panel=panel, sandbox=sandbox, real_saves=real, name_rule_samples=rules,
                  r20=dict(training_count_source=source, dungeon_companion_count=walkc, widest_event_line=widest20, real_saves=r20_real,
                           states=[t for t, _, _ in states]),
                  r21=dict(commands=r21_rows, flag=r21_flag, reset=r21_reset, results=r21_result, scope=r21_scope,
                           frames_in_saved_stacks=sorted({x['function'] for x in frames if x['function'] in ('C_SceneHomebase@RunHome', 'C_SelectDialog@Run', 'KR_T9HomeMenuRun')})),
                  r22=dict(tables=r22_tables, flow=r22_flow, confine=r22_confine, title=r22_title, noplay=r22_noplay),
                  r23=dict(game_code=G, gates=len(gates), widest_event_line_px=widest23, real_saves=r23_real),
                  r24=dict(cells=r24_cells, pages=r24_pages, buttons=r24_buttons, resume=r24_resume))
    print(json.dumps({k: v for k, v in result.items() if k not in ('real_saves', 'name_rule_samples')}, ensure_ascii=False, indent=1, default=str))
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
                      sandbox=lambda v: sandbox_checks(v, X, collections.Counter()),
                      names_e=lambda v: event_pages(v, X, collections.Counter()),
                      names_dup=lambda v: pages_all(v, X, collections.Counter(), 'partial'),
                      names_rule=lambda v: name_rule_checks(v, X, collections.Counter()),
                      affinity=lambda v: affinity_checks(v, X, collections.Counter()),
                      r20_counts=lambda v: r20_count_checks(v, X, collections.Counter(), states[:2]),
                      r20_text=lambda v: r20_text_checks(v, X, collections.Counter(), states[:3]),
                      r20_partner=lambda v: r20_partner_checks(v, X, collections.Counter(), regs),
                      r21_requests=lambda v: r21_request_checks(lambda: r21_fresh(cand, nm, mutate=v.mutate, alias=v.alias), collections.Counter()),
                      r21_flag=lambda v: r21_flag_checks(lambda: r21_fresh(cand, nm, mutate=v.mutate, alias=v.alias), collections.Counter()),
                      r21_reset=lambda v: r21_reset_checks(lambda: r21_fresh(cand, nm, mutate=v.mutate, alias=v.alias), collections.Counter()),
                      r21_scope=lambda v: r21_scope_checks(lambda: r21_fresh(cand, nm, mutate=v.mutate, alias=v.alias), collections.Counter()),
                      r22_tables=lambda v: chart_table_checks(chart_vm(cand, nm, X, mutate=v.mutate), X, C, collections.Counter()),
                      r22_pages=lambda v: chart_page_checks(chart_vm(cand, nm, X, mutate=v.mutate), X, C, collections.Counter()),
                      r22_flow=lambda v: chart_flow_checks_m(cand, nm, X, C, v.mutate),
                      r22_confine=lambda v: chart_confine_checks_m(cand, nm, X, C, v.mutate),
                      r23_value=lambda v: r23_value_checks(v, X, G, collections.Counter()),
                      r23_rank=lambda v: r23_value_checks(v, X, G, collections.Counter()),
                      r23_next=lambda v: r23_next_checks(v, X, G, gates, collections.Counter(), regs_sets[:2]),
                      r23_life=lambda v: r23_lifecycle_checks(v, X, G, gates, collections.Counter(), regs, (10, 14)),
                      r24_cells=lambda v: r24_cell_checks(cand, nm, X, C, collections.Counter(), mutate=v.mutate),
                      r24_buttons=lambda v: r24_button_checks(cand, nm, X, C, collections.Counter(), mutate=v.mutate),
                      r24_resume=lambda v: r24_resume_checks(cand, nm, X, C, collections.Counter(), mutate=v.mutate))
        tail_mut, tail_k = tail_defect(vm)
        for label, group, mutation in DEFECTS + [table_defect(X)] + r19_defects(vm, X) + r20_defects() + r21_defects() + r22_defects(C) + r23_defects(G, nm) + r24_defects():
            alias = None
            if isinstance(mutation, tuple) and mutation[0] == 'alias':
                alias, mutation = {mutation[1]: (vm.fs[mutation[1]], mutation[2])}, {}
            elif mutation is None:
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
            except (AssertionError, Stop, VMExit) as ex:
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
            site = r18_site()['site']
            assert bytes(raw[16 + site + 8:16 + site + 10]) == struct.pack('<H', 0) and raw[16 + site + 10] == 1, 'PUSH 1 after the POP'
            raw[16 + site + 10] ^= 1                                                       # PUSH 1 -> PUSH 0 (■ＡＤＶ消し's first argument)
            return L.pack(bytes(raw), b[:8])
        for label, kw, part in [('S2 one r15 swap site reverted', dict(mutate_bytes=flip_site), 'S2'),
                                ('S4 a saved return instruction changed', dict(mutate_bytes=touch_return), 'S4'),
                                ('S3 one MSG1 byte changed', dict(mutate_bytes=touch_msg), 'S3'),
                                ('S6 a pinned function redefined (KR_T9HomeCasual moved)', dict(mutate_meta=redefine_pinned), 'S6'),
                                ('S6 a byte of the pinned KR_T9HomeCasual changed (after r18\'s operand)', dict(mutate_bytes=touch_pinned_beyond_operand), 'S6')]:
            try:
                static_checks(base, cand, man, m, nm, collections.Counter(), parts=(part,), **kw)
                planted.append(dict(defect=label, caught=False))
            except AssertionError as ex:
                planted.append(dict(defect=label, caught=True, message=str(ex)[:200]))
        result['planted_defects'] = planted
        print(json.dumps(planted, ensure_ascii=False, indent=1))
        assert len(planted) == 56, len(planted)
        assert all(p['caught'] for p in planted), [p['defect'] for p in planted if not p['caught']]
    L.writej(W / ('vm_verification_selftest.json' if selftest else 'vm_verification.json'), json.loads(json.dumps(result, ensure_ascii=False, default=str)))
    L.writej(L.EVID / ('verify_selftest.json' if selftest else 'verify.json'), json.loads(json.dumps(dict(
        candidate_sha256=result['candidate_sha256'], seconds=result.get('seconds'), counts=result['counts'], r22=result.get('r22'),
        r23=result.get('r23'), r24=result.get('r24'), planted_defects=result.get('planted_defects')), ensure_ascii=False, default=str)))
    print('VERIFIED', round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
