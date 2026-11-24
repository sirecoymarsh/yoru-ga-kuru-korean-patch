"""One-off: extend the copied r21 VM for r22 (chart waits, memory-mode replay, parts of the chart, the title's inputs)."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'verify_chart_r22.py'
s = p.read_text('utf8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:100])
    s = s.replace(a, b)


rep('''    def __init__(self, frames, then, each=None):
        self.frames, self.then, self.each = frames, then, each

    def run(self, vm, d):
        vm.ended = None
        d['polls'] = 0
        d['frames'] = 0
        for f in range(self.frames):
            if self.each:
                self.each(vm, f)
            n0 = len(vm.file_calls)
            d['frames'] += 1
            vm.run('KR_MTick')''', '''    def __init__(self, frames, then, each=None, tick='KR_MTick'):
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
            vm.run(d.get('tick') or self.tick)''')

rep('''        self.guard_saves = False        # r21 checks: any save / load / config / title call is an error
''', '''        self.guard_saves = False        # r21 checks: any save / load / config / title call is an error
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
''')

rep('''        if name == 'N_ScenarioRegister::IsRegisteredEvent':
            return int(aa[0] in self.registered)
''', '''        if name == 'N_ScenarioRegister::IsRegisteredEvent':
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
''')

rep('''        sig = dict(IsExist=(1, True), Release=(1, False), GetActivityPartsNumber=(2, True), IsComponentShow=(1, True),
                   Parts_SetText=(3, True), Parts_SetFont=(12, True), Parts_SetTextEnableTag=(3, False),
                   Parts_SetTextLineSpace=(3, True), Parts_SetParentPartsNumber=(2, False), SetComponentPos=(3, False),
                   SetComponentPosZ=(2, False), SetComponentShow=(2, False), SetComponentMulColor=(4, False))''',
    '''        sig = dict(IsExist=(1, True), Release=(1, False), GetActivityPartsNumber=(2, True), IsComponentShow=(1, True),
                   Parts_SetText=(3, True), Parts_SetFont=(12, True), Parts_SetTextEnableTag=(3, False),
                   Parts_SetTextLineSpace=(3, True), Parts_SetParentPartsNumber=(2, False), SetComponentPos=(3, False),
                   SetComponentPosZ=(2, False), SetComponentShow=(2, False), SetComponentMulColor=(4, False),
                   Parts_SetPassCursor=(2, False), IsExistActivity=(1, True))''')

rep('''        elif method == 'SetComponentMulColor':
            self.part(a[0])['mul'] = tuple(a[1:4])''', '''        elif method == 'SetComponentMulColor':
            self.part(a[0])['mul'] = tuple(a[1:4])
        elif method == 'Parts_SetPassCursor':
            self.part(a[0])['pass'] = int(bool(a[1]))
        elif method == 'IsExistActivity':
            out = int(a[0] in self.act)
        if method == 'SetComponentShow':
            self.shows.append((a[0], int(bool(a[1]))))''')

rep('''    def ours(self):
        return sorted(n for n in self.parts if 2026092000 <= n < 2026092100)
''', '''    def ours(self):
        return sorted(n for n in self.parts if 2026092000 <= n < 2026092100)

    # ---- r22: the chart's parts, waits and the title
    CHART_ROOT = 2026092200
    TITLE_ACT = 'Game\\\\Scenes\\\\0000Title\\\\SceneTitle.pact'
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
''')

p.write_text(s, 'utf8')
print('patched VM')
