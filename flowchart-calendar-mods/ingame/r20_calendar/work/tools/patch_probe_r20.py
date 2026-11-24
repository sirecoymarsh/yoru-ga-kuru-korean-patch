"""r20 one-off: turn the r19 probe copy (probe_calendar_r20.py) into the r20 probe. Run once (idempotent guard)."""
from pathlib import Path
p = Path(__file__).resolve().parents[2] / 'probe_calendar_r20.py'
s = p.read_text(encoding='utf8')
assert 'KR_CPTick2' not in s, 'already patched'


def rep(a, b, count=1):
    global s
    assert s.count(a) == count, (a[:80], s.count(a))
    s = s.replace(a, b)


# ---- docstring
rep('"""Claude Opus 5.5 (2026-09-27) r19: isolated, muted native probe of the calendar candidate (after probe_calendar_r18.py).',
    '"""Claude Opus 5.5 (2026-09-28) r20: isolated, muted native probe of the calendar candidate (after probe_calendar_r19.py).\n'
    'r20 adds two screens: the status window\'s 「이벤트」 page (home 파티 편성 -> 스테이터스) and the Saturday training partner\n'
    'selection (labels over the portraits). The r19 tour, lock pages and sandbox replay run unchanged after the r20 home stages.\n'
    '\n'
    '  python probe_calendar_r20.py [SAVE]              full probe: run 1 = home save (r20 status stages, then the r19 tour and\n'
    '                                                   sandbox), run 2 = a Saturday partner-select save (NightR40.asd)\n'
    '  python probe_calendar_r20.py --regs SAVE ...     per save: date, registrations, panel, summary AND the r20 texts\n'
    '                                                   (KR_T20StText(1..8), KR_T20TrText(2..8)) for the VM comparison\n'
    '\n'
    'r19 description (still true):')
rep("  run\\\\SaveData_R19CalendarProbe_<stamp>\\\\  global record files + one save, COPIES (r19lib.save_path).",
    "  run\\\\SaveData_R20CalendarProbe_<stamp>\\\\  global record files + one save, COPIES (r20lib.save_path).")
rep("    savename = f'SaveData_R19CalendarProbe_{stamp}'", "    savename = f'SaveData_R20CalendarProbe_{stamp}'")
rep('(verify_calendar_r19.py --native).', '(verify_calendar_r20.py --native).')
rep('    import verify_calendar_r19 as V\n    return V.expectations()', '    import verify_calendar_r20 as V\n    return V.expectations()')
rep('    import verify_calendar_r19 as V\n    X = V.expectations()', '    import verify_calendar_r20 as V\n    X = V.expectations()')
rep("        out = dict(common, saves=results, schema='yoru-calendar-r19.probe-regs.v1', author=L.AUTHOR)",
    "        out = dict(common, saves=results, schema='yoru-calendar-r20.probe-regs.v1', author=L.AUTHOR)")

# ---- probe jaf: r20 helpers + the per-frame tick for non-dialog screens
R20_JAF = r'''
// ---- r20: parts of our own (status page: panel + text; partner select: box + label per portrait)
int KR_CPOurs() {
    int n = 0;
    if (PartsEngine.IsExist(KR_T20StPanel())) n++;
    if (PartsEngine.IsExist(KR_T20StTextPart())) n++;
    for (int p = 2; p <= 8; p++) {
        if (PartsEngine.IsExist(KR_T20TrPart(p))) n++;
        if (PartsEngine.IsExist(KR_T20TrBox(p))) n++;
    }
    return n;
}
void KR_CPCount(string tag) {
    KR_ClaudeProbeLog("COUNT " + tag + " ours=" + ("%d" % KR_CPOurs()) + " charastatus=" + ("%d" % PartsEngine.NumofActivityParts("Game\\Scenes\\4000Homebase\\CharaStatus.pact")) + " selectally=" + ("%d" % PartsEngine.NumofActivityParts("Game\\Scenes\\Common\\SelectAlly.pact")) + " homemember=" + ("%d" % PartsEngine.NumofActivityParts("Game\\Scenes\\4000Homebase\\HomeMember.pact")));
}
// the status page text part as drawn, and every person's texts as the r20 functions give them (the VM recomputes both)
void KR_CPStText(string tag) {
    KR_CPBlock("STTEXT", tag, PartsEngine.GetTextPartsText(KR_T20StTextPart(), 1));
}
void KR_CPR20All(string tag) {
    for (int c = 1; c <= 8; c++) KR_CPBlock("STCALC", tag + " " + ("%d" % c), KR_T20StText(c));
    for (int p = 2; p <= 8; p++) KR_CPBlock("TRCALC", tag + " " + ("%d" % p), KR_T20TrText(p));
}
void KR_CPLabels(string tag) {
    for (int p = 2; p <= 8; p++) {
        int n = KR_T20TrPart(p);
        if (!PartsEngine.IsExist(n)) continue;
        KR_CPBlock("TRTEXT", tag + " " + ("%d" % p), PartsEngine.GetTextPartsText(n, 1));
        KR_ClaudeProbeLog("TRMUL " + tag + " " + ("%d" % p) + " " + ("%d" % PartsEngine.GetComponentMulColorR(n)) + " box=" + ("%d" % KR_CPB(PartsEngine.IsExist(KR_T20TrBox(p)))));
    }
}
string KR_CPStack() {
    string t = "";
    for (int i = 0; i < 40; i++) {
        string s = system.GetFuncStackName(i);
        if (s == "") break;
        t = t + s + " | ";
    }
    return t;
}
bool KR_CPOn(string name) { string t = KR_CPStack(); return t.Find(name) >= 0; }
int KR_CPHover() { return KR_CPNum("Hover"); }
// probe only: what the player's hover does before the click (RunMember OnEnterChara: SetInfo + Show)
void KR_CPPrepStatus(int charaNo, ref C_HomeMemberView memView) {
    memView.m_StatusView.SetInfo(charaNo);
    memView.m_StatusView.Show();
}
bool KR_CPTick2(int kind) {
    string stage = KR_CPGet("Stage");
    bool r20 = stage.Find("r20") == 0;
    bool pr = stage.Find("pt") == 0;
    if (!r20 && !pr) return false;
    int frames = KR_CPNum("Frames2") + 1;
    KR_CPSet("Frames2", "%d" % frames);
    if (frames > 1800) { KR_ClaudeProbeLog("STUCK2 stage=" + stage + " stack=" + KR_CPStack()); KR_ClaudeShot("cal_stuck2.bmp"); system.Exit(5); return false; }
    if (frames < 24) return false;
    @@R20_STAGES@@
    return false;
}
void KR_CPEnd2(int code) {
    KR_CPSet("Frames2", "0");
    AFL_Parts_EndWaitForClick(code);
}
'''

R20_STAGES = r'''
    // ---------------- r20 home: 파티 편성 -> 스테이터스 -> 이벤트 쪽 (two persons, back and forth, exit, enter again)
    if (stage == "r20member" || stage == "r20member2") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPCount(stage);
        int w = KR_CPNum("W1");
        if (stage == "r20member2") w = KR_CPNum("W2");
        else KR_ClaudeShot("cal_member.bmp");
        KR_CPSet("Stage", stage + "dlg");
        KR_CPEnd2(1000 + w);
        return false;
    }
    if (stage == "r20memberdlg" || stage == "r20member2dlg") {
        if (!KR_CPOn("C_SelectDialog@_Update")) return false;
        if (stage == "r20memberdlg") KR_CPSet("Stage", "r20s1");
        else KR_CPSet("Stage", "r20t1");
        KR_CPEnd2(3);
        return false;
    }
    if (stage == "r20s1") {
        if (!KR_CPOn("C_Status::_UpdateInput")) return false;
        KR_CPCount("S1 page1");
        KR_ClaudeShot("cal_status_p1.bmp");
        KR_CPSet("Stage", "r20s2");
        KR_CPEnd2(2);
        return false;
    }
    if (stage == "r20s2") { KR_CPCount("S2 page2"); KR_CPSet("Stage", "r20s3"); KR_CPEnd2(2); return false; }
    if (stage == "r20s3") { KR_CPCount("S3 page3"); KR_CPSet("T0", "%d" % KR_Time()); KR_CPSet("Stage", "r20s4"); KR_CPEnd2(2); return false; }
    if (stage == "r20s4") {
        KR_ClaudeProbeLog("EVENT PAGE shown after " + ("%d" % (KR_Time() - KR_CPNum("T0"))) + " ms (click to shown, incl. counting)");
        KR_CPCount("S4 page4 A");
        KR_ClaudeProbeLog("STCHARA A " + ("%d" % KR_CPNum("W1")));
        KR_CPStText("A");
        KR_ClaudeShot("cal_status_event_a.bmp");
        KR_CPSet("Stage", "r20s4b");
        KR_CPEnd2(4);
        return false;
    }
    if (stage == "r20s4b") {
        KR_CPCount("S4 page4 B (next person)");
        KR_CPStText("B");
        KR_ClaudeShot("cal_status_event_b.bmp");
        KR_CPSet("Stage", "r20s3b");
        KR_CPEnd2(1);
        return false;
    }
    if (stage == "r20s3b") { KR_CPCount("S3B page3 (prev from 4)"); KR_ClaudeShot("cal_status_p3_from4.bmp"); KR_CPSet("Stage", "r20s4c"); KR_CPEnd2(2); return false; }
    if (stage == "r20s4c") { KR_CPCount("S4C page4 (next from 3)"); KR_CPSet("Stage", "r20s1b"); KR_CPEnd2(2); return false; }
    if (stage == "r20s1b") { KR_CPCount("S1B page1 (next from 4)"); KR_ClaudeShot("cal_status_p1_from4.bmp"); KR_CPSet("Stage", "r20s4d"); KR_CPEnd2(1); return false; }
    if (stage == "r20s4d") { KR_CPCount("S4D page4 (prev from 1)"); KR_CPSet("Stage", "r20back1"); KR_CPEnd2(0); return false; }
    if (stage == "r20back1") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPCount("AFTER EXIT 1");
        KR_ClaudeShot("cal_member_after1.bmp");
        KR_CPSet("Stage", "r20member2");
        KR_CPSet("Frames2", "0");
        return false;
    }
    if (stage == "r20t1") {
        if (!KR_CPOn("C_Status::_UpdateInput")) return false;
        KR_CPCount("T1 page1 (second entry)");
        KR_CPSet("Stage", "r20t4");
        KR_CPEnd2(1);
        return false;
    }
    if (stage == "r20t4") {
        KR_CPCount("T4 page4 C (second entry)");
        KR_ClaudeProbeLog("STCHARA C " + ("%d" % KR_CPNum("W2")));
        KR_CPStText("C");
        KR_ClaudeShot("cal_status_event_c.bmp");
        KR_CPSet("Stage", "r20back2");
        KR_CPEnd2(0);
        return false;
    }
    if (stage == "r20back2") {
        if (!KR_CPOn("_UpdateInputMember")) return false;
        KR_CPCount("AFTER EXIT 2");
        KR_CPSet("Stage", "r20home");
        KR_CPSet("Frames2", "0");
        return true;
    }
    if (stage == "r20home") {
        if (!KR_CPOn("C_SelectDialog@_Update")) return false;
        if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") return false;
        if (frames < 60) return false;
        KR_CPCount("HOME after the member screen");
        KR_ClaudeShot("cal_home_r20_after.bmp");
        KR_CPSet("R20", "done");
        KR_CPSet("Stage", "");
        KR_CPSet("Frames", "0");
        return false;
    }
    // ---------------- r20 partner select (run 2): labels, hover A, hover B, confirm (no), again, confirm (yes)
    if (stage == "pt0") {
        if (KR_CPOn("C_SceneSaveLoad@Update")) { KR_CPSet("Frames2", "0"); return true; }
        if (!KR_CPOn("_UpdateInputPartner")) return false;
        KR_ClaudeProbeLog("PARTNER date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()));
        KR_CPRegs();
        KR_CPR20All("PT");
        KR_CPCount("PARTNER 1");
        KR_CPLabels("P0");
        KR_ClaudeShot("cal_partner_nohover.bmp");
        KR_CPSet("Hover", "@@HOVER_A@@");
        KR_CPSet("Stage", "pt1");
        KR_CPSet("Frames2", "0");
        return false;
    }
    if (stage == "pt1" || stage == "pt2") {
        if (frames < 60) return false;
        if (stage == "pt1") {
            KR_CPCount("HOVER A");
            KR_CPLabels("PA");
            KR_ClaudeShot("cal_partner_hover_a.bmp");
            KR_CPSet("Hover", "@@HOVER_B@@");
            KR_CPSet("Stage", "pt2");
            KR_CPSet("Frames2", "0");
            return false;
        }
        KR_CPCount("HOVER B");
        KR_CPLabels("PB");
        KR_ClaudeShot("cal_partner_hover_b.bmp");
        KR_CPSet("Stage", "ptdlg1");
        KR_CPEnd2(@@HOVER_B@@);
        return false;
    }
    if (stage == "ptdlg1" || stage == "ptdlg2") {
        if (!KR_CPOn("C_SelectDialog@_Update")) return false;
        KR_CPCount("CONFIRM DIALOG " + stage);
        if (stage == "ptdlg1") {
            KR_ClaudeShot("cal_partner_dialog.bmp");
            KR_CPSet("Stage", "ptagain");
            KR_CPEnd2(2);
            return false;
        }
        KR_CPSet("Stage", "ptchosen");
        KR_CPEnd2(1);
        return false;
    }
    if (stage == "ptagain") {
        if (!KR_CPOn("_UpdateInputPartner")) return false;
        KR_CPCount("PARTNER 2 (entered again)");
        KR_CPLabels("P2");
        KR_ClaudeShot("cal_partner_again.bmp");
        KR_CPSet("Stage", "ptdlg2");
        KR_CPEnd2(@@HOVER_B@@);
        return false;
    }
'''
rep("/*TARGETS*/\nint KR_CPPerson() {", "/*TARGETS*/\n" + R20_JAF.replace('@@R20_STAGES@@', R20_STAGES) + "\nint KR_CPPerson() {")

# the r19 tick leaves the r20 stages to KR_CPTick2
rep('''void KR_CalProbeTick() {
    string stage = KR_CPGet("Stage");
    string phase = KR_CPPhase();''',
    '''void KR_CalProbeTick() {
    string stage = KR_CPGet("Stage");
    if (stage.Find("r20") == 0 || stage.Find("pt") == 0) return;
    string phase = KR_CPPhase();''')
# stage "": the r20 home stages first (full mode), then the r19 tour
rep('''    if (stage == "") {
        if (!home) return;
        @@REGS_ONLY@@''',
    '''    if (stage == "") {
        if (!home) return;
        @@REGS_ONLY@@
        @@R20_FIRST@@''')
# message waits: the partner run ends at the first message after the screen (the invitation scene)
rep('''    int n = KR_CPMsgs() + 1;
    TextFile.WriteAll("claude_probe_msgs.txt", "%d" % n);
    string phase = KR_CPPhase();''',
    '''    if (KR_CPGet("Stage") == "ptchosen") {
        KR_CPCount("FIRST MESSAGE AFTER THE PARTNER SCREEN");
        KR_ClaudeProbeLog("END");
        system.Exit(0);
        return 0;
    }
    int n = KR_CPMsgs() + 1;
    TextFile.WriteAll("claude_probe_msgs.txt", "%d" % n);
    string phase = KR_CPPhase();''')
# regs mode: log the r20 texts too
rep('''void KR_CPRegsExit(string where) {
    KR_ClaudeProbeLog(where + " date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()));
    KR_CPRegs();''',
    '''void KR_CPRegsExit(string where) {
    KR_ClaudeProbeLog(where + " date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " now=" + ("%d" % KR_T9NowMonth()));
    KR_CPRegs();
    int t20 = KR_Time();
    KR_CPR20All("REGS");
    KR_ClaudeProbeLog("R20 texts of 8 persons built in " + ("%d" % (KR_Time() - t20)) + " ms");''')
# the partner run starts at the partner stage (the save resumes inside RunSelectPartner)
rep('''    KR_ClaudeProbeLog("resume loading " + save);
    system.ResumeLoad("@@KEY@@", save);''',
    '''    KR_ClaudeProbeLog("resume loading " + save);
    if (save == "@@PARTNER_SAVE@@") KR_CPSet("Stage", "pt0");
    system.ResumeLoad("@@KEY@@", save);''')

# ---- build_probe: substitutions, the r20 tick, hover/prep patches, live waits of the r20 screens
rep("    jaf = jaf.replace('@@REGS_ONLY@@', 'KR_CPRegsExit(\"HOME\"); return;' if mode == 'regs' else '')",
    "    jaf = jaf.replace('@@REGS_ONLY@@', 'KR_CPRegsExit(\"HOME\"); return;' if mode == 'regs' else '')\n"
    "    r20_first = ('if (KR_CPGet(\"R20\") != \"done\") { int w1 = L_Party::GetPersonID(1); if (w1 <= 1) w1 = 2; int w2 = 2; '\n"
    "                 'if (w1 == 2) w2 = 3; KR_CPSet(\"W1\", \"%d\" % w1); KR_CPSet(\"W2\", \"%d\" % w2); KR_CPCount(\"HOME before\"); '\n"
    "                 'KR_ClaudeShot(\"cal_home_r20_before.bmp\"); KR_CPSet(\"Stage\", \"r20member\"); KR_CPSet(\"Frames2\", \"0\"); KR_CPEnd(11); return; }')\n"
    "    jaf = jaf.replace('@@R20_FIRST@@', r20_first if mode == 'full' else '')\n"
    "    jaf = jaf.replace('@@PARTNER_SAVE@@', PARTNER_SAVE).replace('@@HOVER_A@@', str(HOVER[0])).replace('@@HOVER_B@@', str(HOVER[1]))")
rep('''    patch += [f"FUNC {f['index']}\\n\\tPUSH 0\\n\\tRETURN\\nENDFUNC {f['name']}\\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]''',
    '''    patch += [f"FUNC {f['index']}\\n\\tPUSH 0\\n\\tRETURN\\nENDFUNC {f['name']}\\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47 and f['name'] != 'C_UserInputManager::IsClickCancelOtherMouse']
    # r20: every per-frame input handler asks IsClickCancelOtherMouse first -> the r20 tick (returns the scripted cancel)
    f = next(f for f in m['functions'] if f['name'] == 'C_UserInputManager::IsClickCancelOtherMouse')
    patch.append(f"FUNC {f['index']}\\n\\tPUSH 1\\n\\tCALLFUNC KR_CPTick2\\n\\tRETURN\\nENDFUNC {f['name']}\\n")
    # r20: the hovered portrait of the partner screen comes from the probe (the window is hidden: no mouse)
    om = L.fid_of(m, 'C_SceneTrainingView@GetOnmouseChara')
    patch.append(f"FUNC {om}\\n\\tCALLFUNC KR_CPHover\\n\\tRETURN\\nENDFUNC C_SceneTrainingView@GetOnmouseChara\\n")
    # r20: the hover a player always does before clicking a portrait of the member view (SetInfo + Show)
    rs = L.fid_of(m, 'C_SceneHomebase@RunStatus')
    path = work / f'original_{rs}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SceneHomebase@RunStatus', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SceneHomebase@RunStatus'), '\\t.LOCALREF charaNo\\n\\t.LOCALREF memView\\n\\tCALLFUNC KR_CPPrepStatus\\n'))''')
rep('''                if name == 'C_SelectDialog@Run':
                    waits.append((name, 'live'))
                    continue''',
    '''                if name == 'C_SelectDialog@Run':
                    waits.append((name, 'live'))
                    continue
                if any(k in name for k in LIVE_R20):
                    waits.append((name, 'live r20'))
                    continue''')
rep("    assert sum(1 for _, k in waits if k == 'live') == 1 and sum(1 for _, k in waits if k.startswith('message')) == 1, waits",
    "    assert sum(1 for _, k in waits if k == 'live') == 1 and sum(1 for _, k in waits if k.startswith('message')) == 1, waits\n"
    "    assert sorted(n for n, k in waits if k == 'live r20') == sorted(LIVE_R20_EXPECT), [w for w in waits if w[1] == 'live r20']")
rep("MIDSAVE_SLOT = 90   # the probe's mid-replay save (inside the probe's own save folder)",
    "MIDSAVE_SLOT = 90   # the probe's mid-replay save (inside the probe's own save folder)\n"
    "PARTNER_SAVE = 'NightR40.asd'     # saved inside the Saturday partner selection (RunSelectPartner > CheckResSysButton > save)\n"
    "HOVER = (3, 8)                    # the two portraits the probe hovers (쿄카, 모모세: both selectable in NightR40)\n"
    "LIVE_R20 = ('C_Status::RunStatus', 'RunSelectPartner', 'RunMember', 'C_SceneSaveLoad@RunCommon')   # waits the r20 screens need\n"
    "LIVE_R20_EXPECT = ['C_Status::RunStatus', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>',\n"
    "                   'C_SceneHomebase@<lambda : C_SceneHomebase@RunMember()(233, 52)>', 'C_SceneSaveLoad@RunCommon']")
p.write_text(s, encoding='utf8')
print('patched', p)
