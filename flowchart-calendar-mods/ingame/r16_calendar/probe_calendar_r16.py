"""Claude Opus 5.5 (2026-09-27) r16: isolated, muted native probe of the calendar candidate (after probe_calendar_r15.py).

  python probe_calendar_r16.py [SAVE]              full probe (default: work/probe_pick.json, else the newest home-base save copy)
  python probe_calendar_r16.py --regs SAVE ...     per save: resume, log today's date and every calendar event registered in
                                                   that save (the VM's real-save states, 증거/probe_regs.json), exit
  python probe_calendar_r16.py --savefolder-test   only: resume + home menu screenshot + exit (checks the P: save folder)

Everything lives under r16_calendar\\probe\\ on P:
  run\\           a copy of the runtime folder: exe/dll/ini/Data/PACT/EX copied, CG/Font/Sound/Voice/Movie hard-linked from the
                 RUNTIME (read-only assets), AliceStart.ini BootName = probe name, InstallInfo\\SaveFolderSetting.ini type 2
                 (saves inside run\\ on P:, r15 탐침 메모);
  run\\SaveData_R16CalendarProbe_<stamp>\\  global record files + one save, COPIES (r16lib.save_path: the r15 copy when the file
                 did not change, else the r16 copy). The user's save folder is only read; its hashes are compared.
The probe AIN = candidate + probe-only code (never shipped): MAIN -> KR_ClaudeProbeMain (Codex diagnostic mute, resume the
copied save); config::detail::SetMute / C_UserInputManager::Is* patched (muted, no input); C_SelectDialog@_Update gets the
prefix KR_CalProbeTick (runs every frame a selection dialog waits); the message key wait -> KR_CalProbeMsgWait (shots of
the first two waits, then returns at once); every other AFL_Parts_WaitForClick site -> log + exit.
Tick script (the same paths a player uses; the panel click goes through KR_T8HomeClick, the r13 handler itself):
  home [shot, REGS] -> character row -> r13 window [shot] -> 달력으로 보기 -> lane page [shot: bar line] -> 돌아가기 ->
  month page [shot: three states, ★, bars] -> 달성도 보기 [shot summary] -> 돌아가기 -> months to October (September on
  the way: [shot, 3-column menu]) -> 마나미 lane
  [shots page 1, 2: E-number tails] -> 돌아가기 -> month of a short registered one-stage card -> lane -> card [shot] ->
  이 장면 재생 -> (all windows close, the home menu returns 3, the casual site replays) [message shots: spoiler] ->
  home again [shot]: END. Every page title is logged for the offline comparison (verify_calendar_r16.py --native).
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time, zlib
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r16lib as L

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
MANAMI = 3          # lane 3 = 마나미 (October holds the eight 10/11 rows that now carry E-number tails)

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
void KR_CPTitleLog(string tag) {
    KR_ClaudeProbeLog("TITLE " + tag + " <<<");
    KR_ClaudeProbeLog(KR_CPTitle());
    KR_ClaudeProbeLog(">>>");
}
// every calendar event registered in this save (stage table then drawer scene table), one line
void KR_CPRegs() {
    string t = "REGS";
    for (int i = 0; i < 404; i++) { int e = KR_T9StageEv(i); if (KR_T9Seen(e)) t = t + " " + ("%d" % e); }
    for (int j = 0; j < 760; j++) { int e2 = KR_T9SceneEv(j); if (KR_T9Seen(e2)) t = t + " " + ("%d" % e2); }
    KR_ClaudeProbeLog(t);
}
/*TARGETS*/
int KR_CPPerson() {
    int m = KR_T9NowMonth();
    for (int p = 2; p <= 5; p++) { if (KR_T9LaneCards(m, p - 1) > 0) return p; }
    return 4;
}
// month page navigation: returns true when already on month `want`
bool KR_CPGoto(int want) {
    int m = KR_CPNum("Month");
    if (m > want) { KR_CPSet("Month", "%d" % (m - 1)); KR_CPEnd(11); return false; }
    if (m < want) { KR_CPSet("Month", "%d" % (m + 1)); KR_CPEnd(12); return false; }
    return true;
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
        KR_CPRegs();
        @@REGS_ONLY@@
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
        KR_CPTitleLog("LANE " + ("%d" % KR_T9NowMonth()) + " " + ("%d" % (KR_CPNum("Person") - 1)));
        KR_ClaudeShot("cal_lane.bmp");
        KR_CPSet("Stage", "month");
        KR_CPSet("Month", "%d" % KR_T9NowMonth());
        KR_CPEnd(0);
        return;
    }
    if (stage == "month") {
        KR_CPTitleLog("MONTH " + KR_CPGet("Month"));
        KR_ClaudeShot("cal_month.bmp");
        KR_CPSet("T0", "%d" % KR_Time());
        KR_CPSet("Stage", "summary");
        KR_CPEnd(31);
        return;
    }
    if (stage == "summary") {
        KR_ClaudeProbeLog("SUMMARY opened after " + ("%d" % (KR_Time() - KR_CPNum("T0"))) + " ms (click to shown, incl. building the title)");
        KR_CPTitleLog("SUMMARY");
        KR_ClaudeShot("cal_summary.bmp");
        KR_CPSet("Stage", "tooct");
        KR_CPSet("T1", "%d" % KR_Time());
        KR_CPEnd(0);
        return;
    }
    if (stage == "tooct") {
        if (KR_CPGet("T1") != "") {
            KR_ClaudeProbeLog("MONTH page back after " + ("%d" % (KR_Time() - KR_CPNum("T1"))) + " ms (click to shown, incl. building the title)");
            KR_CPSet("T1", "");
        }
        if (KR_CPNum("Month") == 9 && KR_CPGet("Sep") == "") {
            KR_CPTitleLog("MONTH 9");
            KR_ClaudeShot("cal_month_sep_3col.bmp");
            KR_CPSet("Sep", "1");
        }
        if (!KR_CPGoto(10)) return;
        KR_CPTitleLog("MONTH 10");
        KR_CPSet("Stage", "oct1");
        KR_CPEnd(20 + @@MANAMI@@);
        return;
    }
    if (stage == "oct1") {
        KR_CPTitleLog("LANE 10 @@MANAMI@@ p1");
        KR_ClaudeShot("cal_lane_oct_manami_p1.bmp");
        KR_CPSet("Stage", "oct2");
        KR_CPEnd(12);
        return;
    }
    if (stage == "oct2") {
        KR_CPTitleLog("LANE 10 @@MANAMI@@ p2");
        KR_ClaudeShot("cal_lane_oct_manami_p2.bmp");
        KR_CPSet("Stage", "month2");
        KR_CPEnd(0);
        return;
    }
    if (stage == "month2") {
        if (KR_CPGet("Pick") == "") {
            int pk = KR_CPPick();
            if (pk < 0) { KR_ClaudeProbeLog("NO TARGET CARD"); system.Exit(4); return; }
            KR_CPSet("Pick", "%d" % pk);
            KR_ClaudeProbeLog("PICK month=" + ("%d" % (pk / 10)) + " candidate=" + ("%d" % (pk % 10)) + " entry=" + ("%d" % KR_CPTargetEntry(pk / 10, pk % 10)));
        }
        int tm = KR_CPNum("Pick") / 10;
        if (!KR_CPGoto(tm)) return;
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
// the save to resume comes from run\claude_probe_args.txt (one probe build serves every save of a --regs pass)
string KR_CPArgSave() {
    string s = "";
    if (!TextFile.ReadAll("claude_probe_args.txt", s)) return "";
    int nl = s.Find("\n");
    if (nl > 0) s = KR_JosaSlice(s, 0, nl);
    return s;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0, "NightRAFCGMode.asd");
    PassRegister.SetFileName(1, "NightRAFMemMode.asd");
    PassRegister.SetFileName(2, "NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("SAVEFOLDER " + system.GetSaveFolderName());
    @@WHERE@@
    string save = KR_CPArgSave();
    if (save == "") { KR_ClaudeProbeLog("NO SAVE ARGUMENT"); system.Exit(3); return 3; }
    KR_ClaudeProbeLog("resume loading " + save);
    system.ResumeLoad("@@KEY@@", save);
    system.Exit(2);
    return 2;
}
'''


def expectations():
    import verify_calendar_r16 as V
    return V.expectations()


def safe_targets(X):
    """Per month, up to six candidates: a one-stage card whose event has no choice, no battle, no chain and 4-60 messages,
    with its lane and index in the lane (cards come first in a lane page; index < 8 = first page), shortest first."""
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


def build_probe(source, key, work, mode, targets):
    src = source / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    jaf = MUTE_JAF + '\n' + PROBE_JAF.replace('@@KEY@@', key).replace('/*TARGETS*/', target_jaf(targets))
    jaf = jaf.replace('@@MANAMI@@', str(MANAMI))
    jaf = jaf.replace('@@REGS_ONLY@@', 'KR_ClaudeProbeLog("END"); system.Exit(0); return;' if mode == 'regs' else '')
    jaf = jaf.replace('@@SAVEFOLDER_TEST@@', 'KR_ClaudeProbeLog("END"); system.Exit(0); return;' if mode == 'savefolder' else '')
    jaf = jaf.replace('@@WHERE@@', 'KR_ClaudeProbeLog("END"); system.Exit(0); return 0;' if mode == 'where' else '')
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


def setup_folder():
    ptr, rt = L.runtime()
    RUN.mkdir(parents=True, exist_ok=True)
    for n in ['NightRemaster.exe', 'winmm.dll', 'Version.txt']:
        shutil.copy2(rt / n, RUN / n)
    assert L.sha(RUN / 'NightRemaster.exe') == EXE_SHA
    if not (RUN / 'Data').exists():
        shutil.copytree(rt / 'Data', RUN / 'Data')
    for n in ['NightRemasterPact.afa', 'NightRemasterEX.ex']:          # PACT/EX are the runtime's (r16 does not change them)
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
    assert BOOT.encode() in ini
    (RUN / 'AliceStart.ini').write_bytes(ini)
    return rt


def set_savefolder(savename):
    ini = (RUN / 'AliceStart.ini').read_bytes()
    folder = b'SaveFolder\t= "' + savename.encode('cp932') + b'"'
    ini = re.sub(rb'SaveFolder\t= "[^"]*"', lambda z: folder, ini)
    assert folder in ini
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


def home_saves():
    out = []
    for name, p in L.save_slots().items():
        r = L.save_records(p)
        names = [x['name'].split('(')[0] for x in [r['ip']] + r['returns'] if x['address'] != -1]
        if 'C_SceneHomebase@CheckGameSysButtons' in names:
            out.append((p.stat().st_mtime, name))
    return [n for _, n in sorted(out)]


def user_state():
    return {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}


def run_one(save, mode, info_builder, stamp):
    """Copy the save + global files into a fresh P: save folder inside run\\, launch, collect log and screenshots."""
    savename = f'SaveData_R16CalendarProbe_{stamp}'
    savedir = RUN / savename
    set_savefolder(savename)
    if mode != 'where':
        savedir.mkdir(parents=True)
        for n in COPY_GLOBAL:
            files = L.save_manifest()['files']
            if n in files:
                shutil.copy2(L.save_path(n), savedir / n)
        shutil.copy2(L.save_path(save), savedir / save)
    (RUN / 'claude_probe_args.txt').write_bytes(save.encode('cp932') + b'\n')
    t0 = time.time()
    result = launch(timeout=60 if mode == 'where' else (240 if mode in ('savefolder', 'regs') else 900))
    result['seconds'] = round(time.time() - t0, 1)
    log = RUN / 'claude_probe.txt'
    result['log'] = L.decode(log.read_bytes()).splitlines() if log.exists() else []
    result.update(save=save, save_folder=str(savedir))
    result['probe_save_folder_files'] = sorted(p.name for p in savedir.iterdir()) if savedir.exists() else []
    return result


def parse_regs(log):
    home = next((l for l in log if l.startswith('HOME date=')), None)
    regs = next((l for l in log if l.startswith('REGS')), None)
    if not home or regs is None:
        return None
    z = re.match(r'HOME date=(\d+)/(\d+) now=(\d+)', home)
    return dict(today=[int(z[1]), int(z[2])], now=int(z[3]), regs=sorted(int(x) for x in regs.split()[1:]))


def main():
    mode = 'full'
    if '--savefolder-test' in sys.argv:
        mode = 'savefolder'
    elif '--where' in sys.argv:
        mode = 'where'
    elif '--regs' in sys.argv:
        mode = 'regs'
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ptr, rt = L.runtime()
    assert L.sha(rt / 'NightRemaster.ain') == L.BASE_AIN_SHA, 'runtime moved since the candidate was built'
    man = L.readj(O / 'manifest.json')
    assert L.sha(O / 'NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    if mode == 'regs':
        saves = args or home_saves()
    elif args:
        saves = args[:1]
    elif (L.WORK / 'probe_pick.json').exists():
        saves = [L.readj(L.WORK / 'probe_pick.json')['save']]
    else:
        saves = home_saves()[-1:]
    stamp0 = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    work = PROBE / f'build_{stamp0}_{mode}'
    work.mkdir(parents=True)
    user_before = user_state()
    alice_dir = L.SAVES.parent
    alice_before = tree_listing(alice_dir)
    import verify_calendar_r16 as V
    X = V.expectations()
    targets = safe_targets(X)
    rt = setup_folder()
    results = []
    keys = {L.save_records(L.save_path(s))['key'] for s in saves}
    assert len(keys) == 1, 'saves with different resume keys'
    info = build_probe(O, keys.pop(), work, mode, targets)
    for i, save in enumerate(saves):
        (RUN / 'probe_manifest.json').write_text(json.dumps(dict(source=str(O / 'NightRemaster.ain'), source_sha256=man['files']['NightRemaster.ain']['sha256'],
            probe_sha256=info['probe_sha256'], audio=AUDIO_POLICY, save=save, mode=mode, author=L.AUTHOR,
            input='Resume of a copied home-base save; user input patched off; dialogs answered by KR_CalProbeTick.'), ensure_ascii=False, indent=1), 'utf8')
        r = run_one(save, mode, info, f'{stamp0}_{i:02d}')
        r.update(probe_sha256=info['probe_sha256'], candidate_sha256=man['files']['NightRemaster.ain']['sha256'], mode=mode)
        if mode == 'regs':
            r['state'] = parse_regs(r['log'])
            r['log'] = [l for l in r['log'] if not l.startswith('REGS')]
            print(save, r.get('exit_code'), r['seconds'], r['state'] and (r['state']['today'], len(r['state']['regs'])), flush=True)
        results.append(r)
    user_after = user_state()
    common = dict(user_save_folder_unchanged=user_after == user_before, user_save_files=len(user_before),
                  c_drive_alicesoft_changes=sorted(set(tree_listing(alice_dir).items()) ^ set(alice_before.items()))[:20],
                  run_folder_new_dirs=sorted(p.name for p in RUN.iterdir() if p.is_dir()), waits=info['waits'] if info else None,
                  targets=info['targets'] if info else None)
    if mode == 'regs':
        out = dict(common, saves=results, schema='yoru-calendar-r16.probe-regs.v1', author=L.AUTHOR)
        L.writej(L.EVID / 'probe_regs.json', out)
        print(json.dumps({k: v for k, v in out.items() if k not in ('saves', 'waits')}, ensure_ascii=False, indent=1))
        assert out['user_save_folder_unchanged'], 'user save folder changed'
        return
    result = dict(results[0], **common)
    shots = []
    from PIL import Image
    dest = L.EVID / 'probe'
    dest.mkdir(parents=True, exist_ok=True)
    for b in sorted(RUN.glob('cal_*.bmp')):
        png = dest / (b.stem + ('_savefoldertest' if mode == 'savefolder' else '') + '.png')
        Image.open(b).save(png)
        b.unlink()
        shots.append(str(png))
    result['screenshots'] = shots
    if mode == 'full':
        result['state'] = parse_regs(result['log'])
        result['log'] = [l for l in result['log'] if not l.startswith('REGS')]
        a, b = dest / 'cal_home_before.png', dest / 'cal_home_after.png'
        if a.exists() and b.exists():
            from PIL import ImageChops
            ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
            diff = ImageChops.difference(ia, ib)
            result['home_before_after'] = dict(size=list(ia.size), differing_pixels=sum(1 for px in diff.get_flattened_data() if px != (0, 0, 0)) if hasattr(diff, 'get_flattened_data') else sum(1 for px in diff.getdata() if px != (0, 0, 0)),
                                               bbox=diff.getbbox())
    name = {'where': 'probe_where.json', 'savefolder': 'probe_savefolder_test.json'}.get(mode, 'probe_result.json')
    L.writej(L.EVID / name, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('waits', 'targets')}, ensure_ascii=False, indent=1))
    assert result['user_save_folder_unchanged'], 'user save folder changed'


if __name__ == '__main__':
    main()
