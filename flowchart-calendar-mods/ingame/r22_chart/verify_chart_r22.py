"""Claude Opus 5.5 (2026-09-28) r22: verification of the chart candidate (menu-bar 「모드」 stage 2) without the game (after
verify_modmenu_r21.py; every r20 / r21 check still runs on the r22 candidate).

  python verify_chart_r22.py              all checks (must pass)
  python verify_chart_r22.py --selftest   all checks, then every check again against a planted defect (each must fail): 48
  python verify_chart_r22.py --native     compare what the native probes logged (증거/probe_r22.json: the title tour and the
                                          home tour; 증거/probe_kinds.json) with the VM

Base = the r21 install (= the r21 candidate). r22 = the event flow chart screen (설계_v4 「C」 + 「정정(09-28 06시)」): KR_C*
functions, two same-length CALLFUNC operands (C_SceneTitle@Update IsClickConfig -> KR_CTitleTick, C_SceneTitle@Run
■方向キー処理／削除 -> KR_CTitleServe), six one-call forwarders (KR_MDo, KR_T9Seen, KR_T9State, KR_T9Legend, KR_T18CardPage,
KR_T18EventPage), two hand-written bodies (KR_CWait, KR_CReplayRun). Static checks S1-S8 (r22 versions) and the r20 / r21 VM
checks V1-V40 (the calendar and the home request consumer through the forwarders; V34 / V38 / V39 now see the chart screen
where r21 showed the 「다음 단계」 notice), then r22:
  V41 the chart's cells: every tab (4-11월 · 회상 · 그 밖) in display order (dated cards by day and slot -> undated cards ->
      dungeon cards -> drawer scenes by lane, kind and the drawers' own display order; 회상 = the memory drawers, 그 밖 = unused)
      recomputed from the chart data (not from the build); names / when / conditions = the r19 texts the base holds, fitted to
      the cell; thumbnails = graph/event_cg.json; the base's r15 / r19 table functions return those texts
  V42 every page of every tab drawn in the VM: 12 cells (or fewer on the last page), each cell's parts (box, thumbnail only when the
      event has a CG and the cell is open, name, 「표식 E번호 · 언제」, condition), line widths inside the cell, header count,
      page line, tabs (the current one gold), close / page buttons clickable, no part left from the previous page
  V43 lock and unlock: open = the first message's global read mark (MsgSkip) or the game's recollection unlock
      (N_ModeScene::CheckEnabelScenario) or 「전체 개방」 (YoruKR_Chart.dat = 1, read once when the chart opens); a locked cell
      shows 「？？？」, no thumbnail, no condition, grey 「● E번호」 and its date; clicking it shows the notice and opens nothing;
      the per-save registration (IsRegisteredEvent) is never asked while the chart is open
  V44 clicking an open cell opens the calendar's card page / scene page (KR_T9CardPage -> KR_T18CardPage -> KR_CCardPage,
      KR_T9EventPage -> ... -> KR_CEventPage) with the global state line and the chart's play note; 이 장면 재생 -> the chart and
      every window close (Unwind), all chart parts released, then KR_CReplay -> KR_CReplayRun(no, ctx) once (the game's
      memory-mode path; on the title the title root hidden around it); no r18 play slot, no sandbox call; afterwards the chart
      stays closed
  V45 the chart mode stays in the chart: with the chart closed (or a stale flag without the chart root) the card / scene pages,
      KR_T9Seen, KR_T9State and KR_T9Legend give exactly the r21 candidate's results (per-save ○ △ ●, the r18 lock, the sandbox
      play request)
  V46 parts: after every way out of the chart (close, cancel, replay, a reset exit is a process exit) no part of the chart range
      is left; a page draw makes exactly the parts it needs
  V47 the title: KR_CTitleTick polls the two files every title frame (not after an undeletable file), ends the title's wait with
      KR_CCode and returns false when something waits, else returns the original IsClickConfig; KR_CTitleServe calls
      ■方向キー処理／削除 first and serves the result, then the request (all five commands; chart with ctx 1)
  V48 not-playable scenes (the per-kind probe's verdicts, table KR_CNoPlay): the cell says 「재생 불가(게임 안에서만)」, the page
      has no 이 장면 재생, a request for it is refused
"""
import sys, json, re, struct, collections, math, copy, time, random, datetime, io, contextlib, bisect
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r22lib as L

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


def r22_sites(man):
    sites = man['same_length_sites']
    assert len(sites) == 2, len(sites)
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
    fw22 = {L.fid_of(m, n) for n in R22_FORWARD}
    swap = r18_site()
    sb = L.fid_of(nm, L.SANDBOX)
    r20s = r20_sites()
    r21s = r21_sites()
    r22s = r22_sites(man)
    cv = L.versions(W / 'candidate_raw_code.jam')
    if 'S1' in parts:
        for f in m['functions']:
            g = nm['functions'][f['index']]
            if f['index'] in fw22:
                assert {k: v for k, v in f.items() if k != 'address'} == {k: v for k, v in g.items() if k != 'address'}, ('forwarded entry changed beyond its address', f['name'])
                assert g['address'] >= oldn, ('a forwarder body is not in the appended code', f['name'])
            else:
                assert g == f, ('base function entry changed', f['index'], f['name'])
        for k in m:
            if k != 'functions':
                assert m[k] == nm[k], k
        assert len(nm['functions']) == len(m['functions']) + len(man['added_functions'])
        assert all(n.startswith('KR_C') for n in man['added_functions']), 'added functions must all be KR_C*'
        assert not any(L.raw_symbol(nm, f['index']).startswith(('KR_T16', 'KR_T17')) for f in nm['functions']), 'r16/r17 names in the candidate'
        for old_, new_ in list(FORWARD.items()) + list(R18_FORWARD.items()) + list(R22_FORWARD.items()):
            v = L.live_version(nm, cv, L.fid_of(nm, old_))
            assert [op for _, op in v['ops'] if not op.startswith('ENDFUNC')][-2:] == ['CALLFUNC 0x%x' % L.fid_of(nm, new_), 'RETURN'], ('forwarder lost', old_)
        for name in R22_FORWARD:
            assert name not in L.PINNED_ALL, ('a pinned function forwarded', name)
        counts['S1_metadata'] += 1
        counts['S1_r22_forwarders'] = len(R22_FORWARD)
    if 'S2' in parts:
        allowed = {x for s_ in r22s for x in range(s_['site'] + 2, s_['site'] + 6)}
        diff = [j for j in range(oldn) if new[16 + j] != old[16 + j]]
        assert set(diff) <= allowed, ('base CODE bytes changed outside r22\'s operands', [hex(x) for x in diff if x not in allowed][:8])
        for s_ in r22s:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['before'], ('r22 site: the base holds another operand', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('r22 site not applied', s_['function'], s_['replacement'])
        rman = L.readj(L.R15 / 'candidate' / 'manifest.json')
        assert len(rman['same_length_sites']) == 9
        for s_ in rman['same_length_sites'] + [swap] + r20s + r21s:
            ad = s_['site']
            assert bytes(old[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap missing in the base', s_['function'])
            assert bytes(new[16 + ad:16 + ad + 6]).hex() == s_['after'], ('swap site no longer applied', s_['function'], s_['replacement'])
        assert bytes(new[16 + swap['site']:16 + swap['site'] + 6]) == struct.pack('<Hi', 0x30, sb), 'KR_T9HomeCasual no longer calls KR_T18RunSandboxed'
        counts['S2_earlier_same_length_sites_kept'] = len(rman['same_length_sites']) + 1 + len(r20s) + len(r21s)
        counts['S2_r22_same_length_sites'] = len(r22s)
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
        # r22: the chart's wait = AFL_Parts_WaitForClick with the KR_CFrame delegate and key cancel (hand-written body)
        assert live_ops(nm, cv, 'KR_CWait') == ['PUSH 0xffffffff', 'PUSH 0x%x' % L.fid_of(nm, 'KR_CFrame'),
                                                 'DG_NEW_FROM_METHOD', 'PUSH 0x1', 'CALLFUNC 0x%x' % L.fid_of(nm, 'AFL_Parts_WaitForClick'), 'RETURN'], live_ops(nm, cv, 'KR_CWait')
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
        # the unlock flag file is read once, when the chart opens (KR_CChart); the chart never asks the per-save registration
        uid = L.fid_of(nm, 'KR_MUnlockAll')
        callers = sorted(L.raw_symbol(nm, f) for f in reach_ids if 'CALLFUNC 0x%x' % uid in live_ops_fid(nm, cv, f))
        assert callers == ['KR_CChart'], callers
        counts['S8_r22_sites_checked'] = len(r22s)
        counts['S8_r21_sites_kept'] = len(r21s)
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
            assert f['index'] not in fw22 or start != f['address'], ('a saved frame is inside a function r22 forwards', name, f['name'])
            if f['index'] not in fw22:
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
    assert dg['text'] == ko(vm.run('KR_T20StText', [dg['person']])) == r20_status_text(X, dregs, dg['person'], dtoday), ('native dungeon 이벤트 쪽 != VM', dg['person'])
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
    res, again, ds, code = r21_home(vm, frames=3, answers=[Wait(10, 0, during_notice, tick='KR_CFrame')])
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
             op_replace('KR_CDrawCell', lambda o: o == ['CALLFUNC', 'KR_T9EvNo'], lambda o: ['VM_POP_PUSHS'])),
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
    """the probe's CELLS block format (KR_P22Cells) from the VM's parts."""
    t = 'OURS %d ALL %s OPEN %s' % (len(vm.ours22()), vm.vars.get('YoruKR.C.All', ''), vm.vars.get('YoruKR.C.Open', ''))
    t += '\nHEAD ' + ko(vm.parts[CPART(1)]['text'])
    t += '\nPAGE ' + ko(vm.parts[CPART(3)]['text'])
    for s_ in range(12):
        box = CPART(40 + s_ * 6)
        if box not in vm.parts:
            t += '\nCELL %d -' % s_
            continue
        g = lambda j: ko(vm.parts[box + j]['text']) if box + j in vm.parts else ''
        t += '\nCELL %d thumb=%d name=%s id=%s cond=%s' % (s_, int(box + 1 in vm.parts), g(2), g(3), g(4))
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
    kinds_doc = L.readj(L.EVID / 'replay_kinds.json') if (L.EVID / 'replay_kinds.json').exists() else {}
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
    r = C['rows'][i]
    no = r['no']
    op = copen(vm, C, no, all_)
    st = cstate(vm, C, no)
    th = r['thumb'] if op else ''
    mark = tint('△', C_GRAY) if st == 1 else tint('●', C_SKY)
    ev = 'E%05d' % no
    if op:
        idl, when, name, cond = mark + ' ' + ev, r['when'], tint(r['name'], C_WHITE), r['cond']
    else:
        idl, when, name, cond = tint('● ' + ev, C_GRAY), tint(r['when'], C_GRAY), tint('？？？', C_GRAY), ''
    idtext = idl + ('\n' + when if th else '　' + when)
    return dict(open=op, thumb=th, id=idtext, name=name, cond=tint(cond, C_GRAY) if cond else None, h=172 if th else 118)


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
    assert vm.parts[CROOT]['show'] == 1 and vm.parts[CROOT].get('z') == 5000, ('V42 root', vm.parts[CROOT].get('z'))
    for b in (30, 32, 34):
        assert vm.parts[CPART(b)].get('click') == 1, ('V42 button not clickable', b)
    for tt in range(10):
        bx = vm.parts[CPART(10 + tt)]
        assert bx.get('click') == 1, ('V42 tab not clickable', tt)
        label = ko(vm.parts[CPART(20 + tt)]['text'])
        assert label == (tint(C_TABS[tt], C_GOLD) if tt == t else C_TABS[tt]), ('V42 tab label', tt, label)
    want_parts = 1 + 3 + 3 * 2 + 10 * 2                      # root, header / legend / page, 3 buttons x 2, 10 tabs x 2
    for s in range(12):
        i = first + p * 12 + s
        box, th, nmp, idp, cdp = cell_parts(vm, s)
        if i >= end:
            assert box is None and th is None and nmp is None and idp is None and cdp is None, ('V46 a part left in an empty slot', t, p, s)
            continue
        e = expect_cell(vm, C, i, all_)
        assert box is not None and box.get('click') == 1 and box['construct'][0] == ('create', 301, e['h']), ('V42 cell box', t, p, s, box and box.get('construct', [None])[0])
        pos = box['pos']
        assert (f32(pos[0]), f32(pos[1])) == (24 + (s % 4) * 309, 114 + (s // 4) * 182), ('V42 cell position', s, pos)
        if e['thumb']:
            assert th is not None and th.get('cg') == e['thumb'] and th.get('parent') == CPART(40 + s * 6), ('V42 thumbnail', t, p, s, th)
            counts['V42_thumbnails'] += 1
        else:
            assert th is None, ('V42 a thumbnail on a cell without one (or a locked cell)', t, p, s, C['rows'][i]['no'], th)
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
    # 1 a locked cell: the notice, nothing opened, the chart goes on; then the close button
    vm = mk()
    chart_state(vm, X, C, 'partial')
    t, p, s, i = find_cell(C, vm, False, lambda r, op: not op)
    ds = chart_session(vm, 1, [CPART(10 + t)] + [2] * p + [box_of(s), OK, CPART(30)])
    kinds = [d.get('kind', 'dialog') for d in ds]
    assert kinds.count('chart') == 3 + p and ko(ds[-2]['title']) == T_LOCKED, ('V43 locked cell', kinds, ko(ds[-2]['title'])[:30])
    assert not vm.replays and not any(c[0] == 'KR_T8CharDatePage' for c in vm.calls), 'V43 a locked cell opened something'
    assert vm.parts[VM.TITLE_ROOT]['show'] == 1
    check_dialog(ds[-2], counts)
    counts['V43_locked_click_notice'] += 1
    out['locked'] = C['rows'][i]['no']
    # 2 an open scene cell (unlocked by 「전체 개방」): the scene page (chart branch), 이 장면 재생 -> the chart closes -> replay
    for ctx in (1, 2):
        vm = mk()
        chart_state(vm, X, C, 'none')
        t, p, s, i = find_cell(C, vm, True, lambda r, op: op and not r['card'] and not r['noplay'])
        no = C['rows'][i]['no']
        ds = chart_session(vm, ctx, goto(t, p) + [box_of(s), 13], all_=True)
        pg = ds[-1]
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
    ds = chart_session(vm, 2, goto(t, kk // 12) + [box_of(kk % 12), 14, 102, 0, 101, 13])
    cardpg, stagepg, lockedpg, stagepg2, openpg = [d for d in ds if d.get('kind') != 'chart']
    wantc = '〓' + ko(vm.run('KR_T19CardHead', [k])) + '\n†언제　' + ko(vm.run('KR_T19EvWhen', [st[0]])) + '\n†누구　' + ko(vm.run('KR_T9EvWho', [st[0]])) \
        + '\n' + C_STATE[1] + '\n¶단계 %d/%d 읽음' % (sum(1 for x in st if cstate(vm, C, x) == 1), len(st)) + '\n' + C_PLAY_NOTE
    assert ko(cardpg['title']) == wantc, ('V44 card page (chart branch)', ko(cardpg['title']), wantc)
    assert [i_ for i_, _, _, _ in cardpg['items']] == [13, 14, 0], cardpg['items']
    lines = ko(stagepg['title']).split('\n')
    assert lines[-1].startswith(C_LEGEND), ('V44 stage list legend (chart)', lines[-1])
    marks = [ko(x)[-1] for i_, x, _h, _d in stagepg['items'] if i_ >= 100]
    assert marks[:3] == ['△', '△', '●'], ('V44 stage list marks (global)', marks[:3])
    assert [i_ for i_, _, _, _ in lockedpg['items']] == [0] and C_STATE[0] in ko(lockedpg['title']), ('V44 a locked stage offers play', lockedpg['items'])
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
    assert L.sha(r21) == L.BASE_AIN_SHA
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
    vm = VM(cand, nm)
    if native:
        # the r20 tour (probe full, run on the r21 candidate) and the r21 tour (probe --r21), each = the VM
        out = native_checks(vm, X, counts)                  # the r20 calendar tour run on the r22 candidate (probe_calendar_tour_r22.py)
        C = chart_expect(X, vm)
        r22n = r22_native_checks(cand, nm, X, C, counts)
        result = dict(schema='yoru-chart-r22.native-compare.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), blocks=out, r22=r22n, counts=dict(counts))
        L.writej(W / 'native_compare.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=1))
        print('NATIVE = VM')
        return
    frames = static_checks(base, cand, man, m, nm, counts)
    if '--r22-only' in sys.argv:                 # development: the static checks and the r22 checks only
        C = chart_expect(X, vm)
        v22 = chart_vm(cand, nm, X)
        out = dict(tables=chart_table_checks(v22, X, C, counts))
        chart_page_checks(v22, X, C, counts)
        out['flow'] = chart_flow_checks(cand, nm, X, C, counts)
        out['confine'] = chart_confine_checks(cand, nm, X, C, counts)
        out['title'] = title_checks(cand, nm, X, C, counts)
        out['noplay'] = noplay_checks(cand, nm, X, C, counts)
        print(json.dumps(dict(counts=dict(counts), r22=out), ensure_ascii=False, indent=1, default=str))
        print('R22 VERIFIED', round(time.time() - t0, 1), 's')
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
    result = dict(schema='yoru-modmenu-r21.verify.v1', author=L.AUTHOR, candidate_sha256=L.sha(cand), base_sha256=L.BASE_AIN_SHA,
                  counts=dict(counts), vm_steps=vm.steps, widest_title=WIDEST['title'], widest_title_len=len(WIDEST['title']),
                  widest_item=WIDEST['item'], widest_item_len=len(WIDEST['item']), widest_drawer_row=WIDEST['drawer'],
                  widest_drawer_row_len=len(WIDEST['drawer']), widest_drawer_row_units=units_w(WIDEST['drawer']),
                  seconds=round(time.time() - t0, 1), saves_checked=counts['S4_saves'], frames_checked=counts['S4_frames'],
                  panel=panel, sandbox=sandbox, real_saves=real, name_rule_samples=rules,
                  r20=dict(training_count_source=source, dungeon_companion_count=walkc, widest_event_line=widest20, real_saves=r20_real,
                           states=[t for t, _, _ in states]),
                  r21=dict(commands=r21_rows, flag=r21_flag, reset=r21_reset, results=r21_result, scope=r21_scope,
                           frames_in_saved_stacks=sorted({x['function'] for x in frames if x['function'] in ('C_SceneHomebase@RunHome', 'C_SelectDialog@Run', 'KR_T9HomeMenuRun')})),
                  r22=dict(tables=r22_tables, flow=r22_flow, confine=r22_confine, title=r22_title, noplay=r22_noplay))
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
                      r22_confine=lambda v: chart_confine_checks_m(cand, nm, X, C, v.mutate))
        tail_mut, tail_k = tail_defect(vm)
        for label, group, mutation in DEFECTS + [table_defect(X)] + r19_defects(vm, X) + r20_defects() + r21_defects() + r22_defects(C):
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
        assert len(planted) == 48, len(planted)
        assert all(p['caught'] for p in planted), [p['defect'] for p in planted if not p['caught']]
    L.writej(W / ('vm_verification_selftest.json' if selftest else 'vm_verification.json'), json.loads(json.dumps(result, ensure_ascii=False, default=str)))
    L.writej(L.EVID / ('verify_selftest.json' if selftest else 'verify.json'), json.loads(json.dumps(dict(
        candidate_sha256=result['candidate_sha256'], seconds=result.get('seconds'), counts=result['counts'], r22=result.get('r22'),
        planted_defects=result.get('planted_defects')), ensure_ascii=False, default=str)))
    print('VERIFIED', round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
