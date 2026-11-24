"""Claude Opus 5.5 (2026-09-27) r15: isolated, muted native probe of the calendar candidate.

  python probe_calendar_r15.py [SAVE]              full probe (default save: newest home-base save copy)
  python probe_calendar_r15.py --savefolder-test   only: resume + home menu screenshot + exit (checks the P: save folder)

Everything lives under r15_calendar\\probe\\ on P:
  run\\           a copy of the runtime folder: exe/dll/ini/Data/PACT/EX copied, CG/Font/Sound/Voice/Movie hard-linked,
                 AliceStart.ini BootName = probe name and SaveFolder = an ABSOLUTE P: path (probe\\saves_<stamp>);
  saves_<stamp>\\ the probe's own save folder: global record files + one home-base save, all COPIES from work\\savecopy
                 (the user's save folder is only read, and only when the copy was made; its hashes are compared).
The probe AIN = candidate + probe-only code (never shipped):
  MAIN -> KR_ClaudeProbeMain (Codex diagnostic mute, resume the copied save);
  config::detail::SetMute / C_UserInputManager::Is* patched as in Codex's diagnostic_audio_20260923 (muted, no input);
  C_SelectDialog@_Update gets a prefix KR_CalProbeTick (runs every frame a selection dialog waits);
  the message key wait (CMessageTextView ExecuteKeyWait) -> KR_CalProbeMsgWait: screenshot of the first two waits,
  then returns at once (the engine discards that result); every other AFL_Parts_WaitForClick site -> log + exit.
Tick script (the same paths a player uses; the panel click is sent through KR_T8HomeClick, the r13 handler itself):
  home menu -> click a character row -> r13 window [shot] -> 달력으로 보기 -> lane page [shot] -> 돌아가기 ->
  month page [shot] -> lane of a short one-stage card without choices/battle/chain -> card page [shot] -> 이 장면 재생 ->
  (all windows close, the home menu returns 3, CheckGameSysButtons' casual site replays) [message shots] ->
  home menu again [shot]: END with the event's registration before/after.
The debugger capture follows the 09-24 probe (trace of engine error boxes and VM error messages).
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time, zlib
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r15lib as L

O = HERE / 'candidate'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterCalendarProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat']
AUDIO_POLICY = 'Master mixer muted before initialization; config mute writes forced on; audio playback/timing retained.'
MUTE_JAF = '''
void KR_DiagnosticMute() {
    if (!KiwiSoundEngine.SetMixerMute(0, true) ||
        !config::detail::GetMasterMute()) {
        system.Exit(91);
        return;
    }
}
'''
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
SAVE_TYPE = 2

PROBE_JAF = r'''
void KR_ClaudeProbeLog(string text) {
    string all = SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Log") + text + "\n";
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Log", all);
    TextFile.WriteAll("claude_probe.txt", all);
}
int KR_ClaudeShot(string file) {
    AFL_View_Update(); AFL_View_Update(); AFL_View_Update();
    if (!SystemService.SaveScreenshot(file, 0, 0, 1280, 720)) system.Exit(9);
    KR_ClaudeProbeLog("SHOT " + file);
    return 0;
}
string KR_CPGet(string key) { return SystemService.SystemVariable_Get("YoruKR.CalProbe." + key); }
void KR_CPSet(string key, string value) { SystemService.SystemVariable_Set("YoruKR.CalProbe." + key, value); }
int KR_CPNum(string key) { string v = KR_CPGet(key); if (v == "") return 0; return v.ToInt(); }
int KR_CPB(bool v) { if (v) return 1; return 0; }
string KR_CPTitle() { return SystemService.SystemVariable_Get("YoruKR.T8.Title"); }
string KR_CPHead() {
    string t = KR_CPTitle();
    int nl = t.Find("\n");
    if (nl > 0) t = KR_JosaSlice(t, 0, nl);
    return t;
}
void KR_CPEnd(int code) {
    KR_CPSet("Frames", "0");
    AFL_Parts_EndWaitForClick(code);
}
/*TARGETS*/
int KR_CPPerson() {
    int m = KR_T9NowMonth();
    for (int p = 2; p <= 5; p++) { if (KR_T9LaneCards(m, p - 1) > 0) return p; }
    return 4;
}
void KR_CalProbeTick() {
    string stage = KR_CPGet("Stage");
    int frames = KR_CPNum("Frames") + 1;
    KR_CPSet("Frames", "%d" % frames);
    if (frames > 2400) { KR_ClaudeProbeLog("STUCK stage=" + stage + " head=" + KR_CPHead()); KR_ClaudeShot("cal_stuck.bmp"); system.Exit(5); return; }
    if (frames < 12) return;
    bool home = SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") == "1";
    if (stage == "") {
        if (!home) return;
        int p = KR_CPPerson();
        KR_ClaudeProbeLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()) + " person=" + ("%d" % p));
        KR_ClaudeShot("cal_home_before.bmp");
        @@SAVEFOLDER_TEST@@
        KR_CPSet("Person", "%d" % p);
        KR_CPSet("Stage", "charwin");
        KR_CPSet("Frames", "0");
        KR_T8HomeClick(0, 40, 52 + (p + 5) * 24 + 6);
        KR_ClaudeProbeLog("clicked row " + ("%d" % (p + 5)) + " pick=" + SystemService.SystemVariable_Get("YoruKR.T8.HomePick") + " ctx=" + SystemService.SystemVariable_Get("YoruKR.T9.Ctx"));
        return;
    }
    if (stage == "charwin") {
        if (KR_CPTitle() == "") return;
        KR_ClaudeProbeLog("CHARWIN head=" + KR_CPHead() + " ctx=" + SystemService.SystemVariable_Get("YoruKR.T9.Ctx"));
        KR_ClaudeShot("cal_charwin.bmp");
        KR_CPSet("Stage", "lane1");
        KR_CPEnd(3);
        return;
    }
    if (stage == "lane1") {
        KR_ClaudeProbeLog("LANE head=" + KR_CPHead());
        KR_ClaudeShot("cal_lane.bmp");
        KR_CPSet("Stage", "month");
        KR_CPSet("Month", "%d" % KR_T9NowMonth());
        KR_CPEnd(0);
        return;
    }
    if (stage == "month") {
        int m = KR_CPNum("Month");
        KR_ClaudeProbeLog("MONTH " + ("%d" % m) + " head=" + KR_CPHead());
        if (KR_CPNum("Shots") == 0) {
            KR_ClaudeShot("cal_month.bmp");
            KR_CPSet("Shots", "1");
            int pk = KR_CPPick();
            if (pk < 0) { KR_ClaudeProbeLog("NO TARGET CARD"); system.Exit(4); return; }
            KR_CPSet("Pick", "%d" % pk);
            KR_ClaudeProbeLog("PICK month=" + ("%d" % (pk / 10)) + " candidate=" + ("%d" % (pk % 10)) + " entry=" + ("%d" % KR_CPTargetEntry(pk / 10, pk % 10)));
        }
        int tm = KR_CPNum("Pick") / 10;
        if (m > tm) { KR_CPSet("Month", "%d" % (m - 1)); KR_CPEnd(11); return; }
        if (m < tm) { KR_CPSet("Month", "%d" % (m + 1)); KR_CPEnd(12); return; }
        int t = KR_CPTarget(tm, KR_CPNum("Pick") % 10);
        KR_CPSet("Target", "%d" % t);
        KR_CPSet("Stage", "lane2");
        KR_CPEnd(20 + t / 100);
        return;
    }
    if (stage == "lane2") {
        int t2 = KR_CPNum("Target");
        KR_ClaudeProbeLog("LANE2 head=" + KR_CPHead() + " pick=" + ("%d" % (t2 % 100)));
        KR_CPSet("Stage", "card");
        KR_CPEnd(100 + t2 % 100);
        return;
    }
    if (stage == "card") {
        int entry = KR_CPTargetEntry(KR_CPNum("Pick") / 10, KR_CPNum("Pick") % 10);
        KR_ClaudeProbeLog("CARD head=" + KR_CPHead() + " entry=" + ("%d" % entry) + " seen_before=" + ("%d" % KR_CPB(KR_T9Seen(entry))));
        KR_ClaudeProbeLog("CARD title=" + KR_CPTitle());
        KR_ClaudeShot("cal_card.bmp");
        KR_CPSet("Entry", "%d" % entry);
        KR_CPSet("Stage", "replay");
        KR_CPEnd(13);
        return;
    }
    if (stage == "replay") {
        if (!home) {
            KR_ClaudeProbeLog("UNEXPECTED DIALOG during replay head=" + KR_CPHead());
            KR_ClaudeShot("cal_unexpected.bmp");
            system.Exit(7);
            return;
        }
        int e2 = KR_CPNum("Entry");
        KR_ClaudeProbeLog("BACK TO HOME messages=" + KR_CPGet("Msgs") + " seen_after=" + ("%d" % KR_CPB(KR_T9Seen(e2))) + " play=" + SystemService.SystemVariable_Get("YoruKR.T9.Play") + " playing=" + SystemService.SystemVariable_Get("YoruKR.T9.Playing") + " date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()));
        KR_ClaudeShot("cal_home_after.bmp");
        KR_ClaudeProbeLog("END");
        system.Exit(0);
    }
}
int KR_CalProbeMsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    int n = KR_CPNum("Msgs") + 1;
    KR_CPSet("Msgs", "%d" % n);
    if (KR_CPGet("Stage") != "replay") { KR_ClaudeProbeLog("MESSAGE WAIT outside the replay stage=" + KR_CPGet("Stage")); KR_ClaudeShot("cal_msg_unexpected.bmp"); system.Exit(8); return 0; }
    if (n == 1) KR_ClaudeProbeLog("REPLAY first message; casual site Play=" + SystemService.SystemVariable_Get("YoruKR.T9.Play") + " playing=" + SystemService.SystemVariable_Get("YoruKR.T9.Playing"));
    if (n <= 2) KR_ClaudeShot("cal_spoiler_replay_msg_" + ("%d" % n) + ".bmp");
    if (n > 600) { KR_ClaudeProbeLog("TOO MANY MESSAGES"); system.Exit(8); return 0; }
    return 0;
}
int KR_CalProbeWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    KR_ClaudeProbeLog("UNEXPECTED WAIT stage=" + KR_CPGet("Stage") + " head=" + KR_CPHead());
    KR_ClaudeShot("cal_wait.bmp");
    system.Exit(6);
    return 0;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("SAVEFOLDER " + system.GetSaveFolderName());
    @@WHERE@@
    KR_ClaudeProbeLog("resume loading @@SAVE@@");
    system.ResumeLoad("@@KEY@@", "@@SAVE@@");
    system.Exit(2);
    return 2;
}
'''


def safe_targets():
    """Per month, up to six candidates: a one-stage card whose event has no choice, no battle, no chain and 4-60 messages,
    with its lane and index in the lane (cards come first in a lane page; index < 8 = first page), shortest first."""
    sys.path.insert(0, str(HERE))
    import verify_calendar_r15 as V
    X = V.expectations()
    sch = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    evs = {e['id']: e for e in sch['events']}
    out = {}
    for mo in range(4, 12):
        cards = [c for c in X['cards'] if c['month'] == mo]
        cand = []
        for c in cards:
            e = evs[c['entry']]
            ok = (c['size'] == 1 and not e['has_choice'] and not e['effects']['event_battle'] and not e['chains_to']
                  and 4 <= e['messages']['count'] <= 60 and e['category'] == 'main')
            idx = [x['key'] for x in cards if x['lane'] == c['lane']].index(c['key'])
            if ok and idx < 8:
                cand.append((c['lane'], idx, c['entry'], e['messages']['count']))
        if cand:
            out[mo] = sorted(cand, key=lambda x: x[3])[:6]
    return out


def target_jaf(targets):
    t = ''.join(f'    if (m == {mo} && i == {i}) return {lane * 100 + idx};\n' for mo, cs in sorted(targets.items()) for i, (lane, idx, entry, n) in enumerate(cs))
    e = ''.join(f'    if (m == {mo} && i == {i}) return {entry};\n' for mo, cs in sorted(targets.items()) for i, (lane, idx, entry, n) in enumerate(cs))
    # the latest month <= now whose candidate is registered in this save (no new story shown), else the first candidate now
    pick = ('int KR_CPPick() {\n'
            '    for (int m = KR_T9NowMonth(); m >= 4; m--) {\n'
            '        for (int i = 0; i < 6; i++) {\n'
            '            int e = KR_CPTargetEntry(m, i);\n'
            '            if (e > 0) { if (KR_T9Seen(e)) return m * 10 + i; }\n'
            '        }\n'
            '    }\n'
            '    for (int m2 = KR_T9NowMonth(); m2 <= 11; m2++) { if (KR_CPTargetEntry(m2, 0) > 0) return m2 * 10; }\n'
            '    return -1;\n'
            '}\n')
    return (f'int KR_CPTarget(int m, int i) {{\n{t}    return -1;\n}}\nint KR_CPTargetEntry(int m, int i) {{\n{e}    return 0;\n}}\n' + pick)


def build_probe(source, key, save, savefolder_test, work, where=False):
    src = source / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    targets = safe_targets()
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@KEY@@', key).replace('@@SAVE@@', save).replace('/*TARGETS*/', target_jaf(targets))
    jaf = jaf.replace('@@SAVEFOLDER_TEST@@', 'KR_ClaudeProbeLog("END"); system.Exit(0); return;' if savefolder_test else '')
    jaf = jaf.replace('@@WHERE@@', 'KR_ClaudeProbeLog("END"); system.Exit(0); return 0;' if where else '')
    jaf = L.jaf_literal_encode(jaf)
    (work / 'probe.jaf').write_text(jaf, 'utf8')
    decl = work / 'probe_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'probe.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'probe_declared_meta.json', decl)
    dm = L.read_meta(work / 'probe_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    # Codex diagnostic_audio_20260923: mute and no user input (probe only)
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    patch += [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]
    for f in added:
        path = work / f"probe_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), f['name']))
    upd = L.fid_of(m, 'C_SelectDialog@_Update')
    path = work / f'original_{upd}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SelectDialog@_Update', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SelectDialog@_Update'), '\tCALLFUNC KR_CalProbeTick\n'))
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_ClaudeProbeMain'])
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    vers = L.versions(L.WORK / 'build' / 'candidate_raw_code.jam')
    waits = []
    for f in m['functions']:
        name = L.raw_symbol(m, f['index'])
        for v in [v for v in vers.get(f['index'], []) if v['start'] == f['address']]:
            for ad, op in v['ops']:
                if op != f'CALLFUNC 0x{wait:x}':
                    continue
                assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, wait)
                if name == 'C_SelectDialog@Run':
                    waits.append((name, 'live'))
                    continue
                target = ids['KR_CalProbeMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_CalProbeWait']
                struct.pack_into('<Hi', raw, 16 + ad, 0x30, target)
                waits.append((name, 'message click-through' if target == ids['KR_CalProbeMsgWait'] else 'exit'))
    assert sum(1 for _, k in waits if k == 'live') == 1 and sum(1 for _, k in waits if k.startswith('message')) == 1, waits
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(waits=waits, targets={str(k): v for k, v in targets.items()}, tick_prefix='C_SelectDialog@_Update', probe_sha256=L.sha(out))


def setup_folder(source, savedir):
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
    for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex']:          # PACT/EX are the runtime's (r15 does not change them)
        shutil.copy2(rt / n, RUN / n)
        shutil.copy2(rt / n, RUN / n.replace('NightRemaster', BOOT, 1))
    for n in ['NightRemasterCG.afa', 'NightRemasterFont.fnl', 'NightRemasterSound.afa', 'NightRemasterVoice.afa']:
        for name in [n, n.replace('NightRemaster', BOOT, 1)]:
            t = RUN / name
            if not t.exists():
                os.link(rt / n, t)
            assert os.path.samefile(t, rt / n)
    if not (RUN / 'Movie').exists():
        (RUN / 'Movie').mkdir()
        for f in (rt / 'Movie').iterdir():
            os.link(f, RUN / 'Movie' / f.name)
    ini = (rt / 'AliceStart.ini').read_bytes()
    ini = re.sub(rb'BootName\t= "NightRemaster"', ('BootName\t= "' + BOOT + '"').encode(), ini)
    folder = b'SaveFolder\t= "' + savedir.encode('cp932') + b'"'
    ini = re.sub(rb'SaveFolder\t= "[^"]*"', lambda z: folder, ini)
    assert BOOT.encode() in ini and folder in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    # mainsystem::CSaveFolderSetting reads InstallInfo\SaveFolderSetting.ini: "SFSF", int32 0, int32 type (0 Documents,
    # 1 another shell folder, 2 the folder the engine holds itself); type 2 keeps the probe's saves inside run\ on P:.
    (RUN / 'InstallInfo').mkdir(exist_ok=True)
    (RUN / 'InstallInfo' / 'SaveFolderSetting.ini').write_bytes(b'SFSF' + struct.pack('<ii', 0, SAVE_TYPE))
    log = RUN / 'claude_probe.txt'
    if log.exists():
        log.unlink()
    for b in RUN.glob('cal_*.bmp'):
        b.unlink()


K = C.WinDLL('kernel32', use_last_error=True)
K.WaitForDebugEvent.argtypes = [C.c_void_p, W.DWORD]
K.ContinueDebugEvent.argtypes = [W.DWORD, W.DWORD, W.DWORD]
K.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
K.WriteProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
K.VirtualProtectEx.argtypes = [W.HANDLE, C.c_void_p, C.c_size_t, W.DWORD, C.POINTER(W.DWORD)]
K.OpenThread.argtypes = [W.DWORD, W.BOOL, W.DWORD]
K.OpenThread.restype = W.HANDLE
K.Wow64GetThreadContext.argtypes = [W.HANDLE, C.c_void_p]
K.CloseHandle.argtypes = [W.HANDLE]
K.TerminateProcess.argtypes = [W.HANDLE, W.UINT]


class Context(C.Structure):
    _fields_ = ([(n, W.DWORD) for n in 'ContextFlags Dr0 Dr1 Dr2 Dr3 Dr6 Dr7'.split()] + [('FloatSave', C.c_byte * 112)]
                + [(n, W.DWORD) for n in 'SegGs SegFs SegEs SegDs Edi Esi Ebx Edx Ecx Eax Ebp Eip SegCs EFlags Esp SegSs'.split()]
                + [('ExtendedRegisters', C.c_byte * 512)])


def launch(timeout=900):
    """09-24 probe launcher (probe_claude_term_rate_20260924.launch): hidden window, debugger on, MessageBoxA and the VM
    error handler break-pointed so engine errors are captured instead of waiting on a dialog. TEMP/TMP point to P:."""
    import pefile, win32process
    exe = RUN / 'NightRemaster.exe'
    data = exe.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXE_SHA
    pe = pefile.PE(data=data)
    imp = next(x.address for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports if x.name == b'MessageBoxA')
    needle = b'\xff\x15' + struct.pack('<I', imp)
    sites = [0x6696f0 - 0x400000]
    off = 0
    while (off := data.find(needle, off)) >= 0:
        sites.append(pe.get_rva_from_offset(off))
        off += 1
    startup = win32process.STARTUPINFO()
    startup.dwFlags = 1
    startup.wShowWindow = 0
    env = L.env()
    hp, ht, pid, tid = win32process.CreateProcess(str(exe), None, None, None, False, 2, env, str(RUN), startup)
    handle = int(hp)
    result = {'pid': pid, 'audio': AUDIO_POLICY, 'ain_sha256': L.sha(RUN / 'NightRemaster.ain'), 'events': []}

    def read(addr, n):
        buf = C.create_string_buffer(n)
        got = C.c_size_t()
        if not K.ReadProcessMemory(handle, addr, buf, n, C.byref(got)):
            raise C.WinError(C.get_last_error())
        return buf.raw[:got.value]

    def cstr(addr):
        out = bytearray()
        for n in range(8192):
            v = read(addr + n, 1)
            if v == b'\0':
                return bytes(out)
            out += v
        return bytes(out)
    try:
        bp = {}
        base = 0
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            event = C.create_string_buffer(200)
            if not K.WaitForDebugEvent(event, 1000):
                continue
            raw = event.raw
            code, epid, etid = struct.unpack_from('<III', raw)
            status = 0x10002
            if code == 3:
                base = struct.unpack_from('<Q', raw, 40)[0]
                for rva in sites:
                    addr = base + rva
                    bp[addr] = read(addr, 1)
                    old = W.DWORD()
                    num = C.c_size_t()
                    if not K.VirtualProtectEx(handle, addr, 1, 0x40, C.byref(old)):
                        raise C.WinError(C.get_last_error())
                    if not K.WriteProcessMemory(handle, addr, b'\xcc', 1, C.byref(num)):
                        raise C.WinError(C.get_last_error())
                    tmp = W.DWORD()
                    K.VirtualProtectEx(handle, addr, 1, old.value, C.byref(tmp))
            elif code == 1:
                exc = struct.unpack_from('<I', raw, 16)[0]
                addr = struct.unpack_from('<Q', raw, 32)[0]
                if exc in (0x80000003, 0x4000001f) and addr in bp:
                    thread = K.OpenThread(0x58, False, etid)
                    try:
                        ctx = Context()
                        ctx.ContextFlags = 0x10007
                        if not K.Wow64GetThreadContext(thread, C.byref(ctx)):
                            raise C.WinError(C.get_last_error())
                        if addr == base + 0x6696f0 - 0x400000:
                            ret, op, msg = struct.unpack('<III', read(ctx.Esp, 12))
                            buf = read(msg, 24)
                            length, capacity = struct.unpack_from('<II', buf, 16)
                            ptr = struct.unpack_from('<I', buf)[0] if capacity >= 16 else msg
                            result['vm_error'] = {'command': cstr(op).decode('cp932', 'replace'), 'message': read(ptr, min(length, 8192)).decode('cp932', 'replace')}
                        else:
                            args = struct.unpack('<IIII', read(ctx.Esp, 16))
                            result['message'] = {'cp932': cstr(args[1]).decode('cp932', 'replace')}
                    finally:
                        K.CloseHandle(thread)
                    K.TerminateProcess(handle, 99)
                    K.ContinueDebugEvent(epid, etid, status)
                    break
                if exc not in (0x80000003, 0x4000001f):
                    result['events'].append({'exception': hex(exc), 'address': hex(addr)})
                    status = 0x80010001
            elif code == 5:
                result['exit_code'] = struct.unpack_from('<I', raw, 16)[0]
                K.ContinueDebugEvent(epid, etid, status)
                break
            K.ContinueDebugEvent(epid, etid, status)
        else:
            result['timeout'] = True
    finally:
        K.TerminateProcess(handle, 99)
    return result


def tree_listing(root):
    out = {}
    if root.exists():
        for p in root.rglob('*'):
            try:
                st = p.stat()
                out[str(p.relative_to(root))] = (st.st_size, int(st.st_mtime))
            except OSError:
                pass
    return out


def newest_home_save():
    best = None
    for p in sorted(L.SAVECOPY.glob('NightR*.asd')):
        if not re.fullmatch(r'NightR\d+\.asd', p.name):
            continue
        r = L.save_records(p)
        names = [x['name'].split('(')[0] for x in [r['ip']] + r['returns'] if x['address'] != -1]
        if 'C_SceneHomebase@CheckGameSysButtons' in names and (best is None or p.stat().st_mtime > best.stat().st_mtime):
            best = p
    return best.name


def resolve_savedir(name):
    """Where the engine puts SaveFolder under SaveFolderSetting type 2 (measured with --where)."""
    return RUN / name


def main():
    test = '--savefolder-test' in sys.argv
    where = '--where' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    save = args[0] if args else newest_home_save()
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    savename = f'SaveData_R15CalendarProbe_{stamp}'
    savedir = resolve_savedir(savename)
    work = PROBE / f'build_{stamp}'
    work.mkdir(parents=True)
    ptr, rt = L.runtime()
    assert L.sha(rt / 'NightRemaster.ain') == L.BASE_AIN_SHA, 'runtime moved since the candidate was built'
    man = L.readj(O / 'manifest.json')
    assert L.sha(O / 'NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    user_before = {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}
    alice_dir = L.SAVES.parent
    alice_before = tree_listing(alice_dir)
    key = L.save_records(L.SAVECOPY / save)['key']
    RUN.mkdir(parents=True, exist_ok=True)
    info = build_probe(O, key, save, test, work, where=where)
    (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=man['files']['NightRemaster.ain']['sha256'],
        probe_sha256=info['probe_sha256'], audio=AUDIO_POLICY, save=save, save_folder=str(savedir), author=L.AUTHOR,
        input='Resume of a copied home-base save; user input patched off; dialogs answered by KR_CalProbeTick.'), ensure_ascii=False, indent=1), 'utf8')
    setup_folder(O, savename)
    if not where:
        savedir.mkdir(parents=True)
        for n in COPY_GLOBAL:
            if (L.SAVECOPY / n).exists():
                shutil.copy2(L.SAVECOPY / n, savedir / n)
        shutil.copy2(L.SAVECOPY / save, savedir / save)
    t0 = time.time()
    result = launch(timeout=60 if where else (240 if test else 900))
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result.update(save=save, save_folder=str(savedir), waits=info['waits'], targets=info['targets'], probe_sha256=info['probe_sha256'],
                  candidate_sha256=man['files']['NightRemaster.ain']['sha256'])
    user_after = {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}
    result['user_save_folder_unchanged'] = user_after == user_before
    result['user_save_files'] = len(user_before)
    alice_after = tree_listing(alice_dir)
    result['c_drive_alicesoft_changes'] = sorted(set(alice_after.items()) ^ set(alice_before.items()))[:20]
    result['probe_save_folder_files'] = sorted(p.name for p in savedir.iterdir()) if savedir.exists() else []
    result['run_folder_new_dirs'] = sorted(p.name for p in RUN.iterdir() if p.is_dir())
    shots = []
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    for b in sorted(RUN.glob('cal_*.bmp')):
        png = dest / (b.stem + ('_savefoldertest' if test else '') + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    result['screenshots'] = shots
    name = 'probe_where.json' if where else ('probe_savefolder_test.json' if test else 'probe_result.json')
    L.writej(L.EVID / name, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('waits',)}, ensure_ascii=False, indent=1))
    assert result['user_save_folder_unchanged'], 'user save folder changed'


if __name__ == '__main__':
    main()
