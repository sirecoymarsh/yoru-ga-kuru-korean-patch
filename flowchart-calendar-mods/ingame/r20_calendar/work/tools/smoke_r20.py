"""r20 smoke probe (Claude Opus 5.5, 2026-09-28): the CANDIDATE AIN + probe-only driver (explore_r20's), before the full probe.

  python smoke_r20.py member [SAVE]    home -> 파티 편성 -> 스테이터스 -> pages 1..4 (4 = 이벤트), chara switch on page 4, back
                                       and forth, exit, enter again, exit (parts counted after every exit)
  python smoke_r20.py partner [SAVE]   partner select (NightR40): labels, hover 3, hover 8, confirm dialog (no), labels again,
                                       confirm (yes) -> labels gone at the first message wait after the screen
"""
import sys, json, struct, shutil, datetime
from pathlib import Path
sys.dont_write_bytecode = True
R20 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R20))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r20lib as L
import probe_calendar_r20 as P
import explore_r20 as X

OUT = R20 / 'work' / 'smoke'
OUT.mkdir(parents=True, exist_ok=True)

COMMON = r'''
int KR_XOurs() {
    int n = 0;
    if (PartsEngine.IsExist(2026092001)) n++;
    if (PartsEngine.IsExist(2026092002)) n++;
    for (int p = 2; p <= 8; p++) { if (PartsEngine.IsExist(2026092010 + p)) n++; if (PartsEngine.IsExist(2026092020 + p)) n++; }
    return n;
}
void KR_XCount(string tag) {
    int a = PartsEngine.NumofActivityParts("Game\\Scenes\\4000Homebase\\CharaStatus.pact");
    int b = PartsEngine.NumofActivityParts("Game\\Scenes\\Common\\SelectAlly.pact");
    KR_XLog("COUNT " + tag + " ours=" + ("%d" % KR_XOurs()) + " charastatus=" + ("%d" % a) + " selectally=" + ("%d" % b) + " page=" + ("%d" % KR_XPageOf()));
}
'''

MEMBER = r'''
    if (stage == "") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        if (SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu") != "1") return false;
        KR_XLog("HOME date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()));
        KR_XCount("HOME");
        KR_XSet("Stage", "member");
        KR_XEnd(11);
        return false;
    }
    if (stage == "member" || stage == "member2") {
        if (!KR_XOn("_UpdateInputMember")) return false;
        KR_XCount(stage);
        int who = 2;
        if (stage == "member2") who = 5;
        KR_XSet("Stage", stage + "dlg");
        KR_XEnd(1000 + who);
        return false;
    }
    if (stage == "memberdlg" || stage == "member2dlg") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        if (stage == "memberdlg") KR_XSet("Stage", "p1");
        else KR_XSet("Stage", "q1");
        KR_XEnd(3);
        return false;
    }
    if (stage == "p1") {
        if (!KR_XOn("C_Status::_UpdateInput")) return false;
        KR_XCount("P1");
        KR_XShot("s_p1.bmp");
        KR_XSet("Stage", "p2");
        KR_XEnd(2);
        return false;
    }
    if (stage == "p2") { KR_XCount("P2"); KR_XSet("Stage", "p3"); KR_XEnd(2); return false; }
    if (stage == "p3") { KR_XCount("P3"); KR_XSet("Stage", "p4"); KR_XEnd(2); return false; }
    if (stage == "p4") {
        KR_XCount("P4");
        KR_XLog("TEXT P4 <<<");
        KR_XLog(PartsEngine.GetTextPartsText(2026092002, 1));
        KR_XLog(">>>");
        KR_XShot("s_event_a.bmp");
        KR_XSet("Stage", "p4b");
        KR_XEnd(4);
        return false;
    }
    if (stage == "p4b") {
        KR_XCount("P4B");
        KR_XLog("TEXT P4B <<<");
        KR_XLog(PartsEngine.GetTextPartsText(2026092002, 1));
        KR_XLog(">>>");
        KR_XShot("s_event_b.bmp");
        KR_XSet("Stage", "p4c");
        KR_XEnd(1);
        return false;
    }
    if (stage == "p4c") { KR_XCount("PREV_FROM_4"); KR_XShot("s_prev_from4.bmp"); KR_XSet("Stage", "p4d"); KR_XEnd(2); return false; }
    if (stage == "p4d") { KR_XCount("NEXT_TO_4"); KR_XSet("Stage", "p4e"); KR_XEnd(2); return false; }
    if (stage == "p4e") { KR_XCount("NEXT_TO_1"); KR_XShot("s_next_to1.bmp"); KR_XSet("Stage", "p4f"); KR_XEnd(1); return false; }
    if (stage == "p4f") { KR_XCount("PREV_1_TO_4"); KR_XShot("s_prev_1to4.bmp"); KR_XSet("Stage", "exit1"); KR_XEnd(0); return false; }
    if (stage == "exit1") {
        if (!KR_XOn("_UpdateInputMember")) return false;
        KR_XCount("AFTER_EXIT1");
        KR_XShot("s_member_after1.bmp");
        KR_XSet("Stage", "member2");
        return false;
    }
    if (stage == "q1") {
        if (!KR_XOn("C_Status::_UpdateInput")) return false;
        KR_XCount("Q1");
        KR_XSet("Stage", "q4");
        KR_XEnd(1);
        return false;
    }
    if (stage == "q4") {
        KR_XCount("Q4");
        KR_XLog("TEXT Q4 <<<");
        KR_XLog(PartsEngine.GetTextPartsText(2026092002, 1));
        KR_XLog(">>>");
        KR_XShot("s_event_c.bmp");
        KR_XSet("Stage", "exit2");
        KR_XEnd(0);
        return false;
    }
    if (stage == "exit2") {
        if (!KR_XOn("_UpdateInputMember")) return false;
        KR_XCount("AFTER_EXIT2");
        KR_XShot("s_member_after2.bmp");
        KR_XSet("Stage", "home2");
        return true;
    }
    if (stage == "home2") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        KR_XCount("HOME2");
        KR_XShot("s_home_after.bmp");
        KR_XLog("END");
        system.Exit(0);
    }
'''

PARTNER = r'''
    if (stage == "") {
        if (KR_XOn("C_SceneSaveLoad@Update")) { KR_XSet("Frames", "0"); return true; }
        if (!KR_XOn("_UpdateInputPartner")) return false;
        KR_XCount("PARTNER1");
        for (int p = 2; p <= 8; p++) {
            int n = 2026092010 + p;
            if (PartsEngine.IsExist(n)) KR_XLog("LABEL " + ("%d" % p) + " <<<\n" + PartsEngine.GetTextPartsText(n, 1) + "\n>>> mul=" + ("%d" % PartsEngine.GetComponentMulColorR(n)));
        }
        KR_XShot("s_partner.bmp");
        KR_XSet("Hover", "3");
        KR_XSet("Stage", "h3");
        KR_XSet("Frames", "0");
        return false;
    }
    if (stage == "h3" || stage == "h8") {
        if (frames < 60) return false;
        KR_XCount(stage);
        for (int q = 2; q <= 8; q++) {
            int n2 = 2026092010 + q;
            if (PartsEngine.IsExist(n2)) KR_XLog("MUL " + ("%d" % q) + " " + ("%d" % PartsEngine.GetComponentMulColorR(n2)));
        }
        if (stage == "h3") {
            KR_XShot("s_partner_hover3.bmp");
            KR_XSet("Hover", "8");
            KR_XSet("Stage", "h8");
            KR_XSet("Frames", "0");
            return false;
        }
        KR_XShot("s_partner_hover8.bmp");
        KR_XSet("Stage", "dlg1");
        KR_XEnd(8);
        return false;
    }
    if (stage == "dlg1") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        KR_XCount("CONFIRM_DIALOG");
        KR_XShot("s_partner_dialog.bmp");
        KR_XSet("Stage", "again");
        KR_XEnd(2);
        return false;
    }
    if (stage == "again") {
        if (!KR_XOn("_UpdateInputPartner")) return false;
        KR_XCount("PARTNER2");
        KR_XShot("s_partner_again.bmp");
        KR_XSet("Stage", "dlg2");
        KR_XEnd(8);
        return false;
    }
    if (stage == "dlg2") {
        if (!KR_XOn("C_SelectDialog@_Update")) return false;
        KR_XSet("Stage", "chosen");
        KR_XEnd(1);
        return false;
    }
'''

MSGWAIT = r'''
int KR_XMsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {
    KR_XCount("FIRST_MESSAGE_AFTER stage=" + KR_XGet("Stage"));
    KR_XLog("MESSAGE WAIT stack=" + KR_XStack());
    KR_XLog("END");
    system.Exit(0);
    return 0;
}
'''


def build(mode, key):
    src = R20 / 'candidate' / 'NightRemaster.ain'
    m = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
    raw_jam = L.WORK / 'build' / 'candidate_raw_code.jam'
    work = OUT / ('build_' + mode)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    xjaf = X.XJAF
    a = xjaf.index('int KR_XMsgWait(')
    b = xjaf.index('int KR_XMain()')
    xjaf = xjaf[:a] + MSGWAIT + xjaf[b:]
    jaf = P.MUTE_JAF + '\n' + xjaf.replace('@@KEY@@', key).replace('@@SCRIPT@@', MEMBER if mode == 'member' else PARTNER)
    jaf = jaf.replace('int KR_XMsgWait(', 'int KR_XPageOf() { return 0; }\n' + COMMON + '\nint KR_XMsgWait(', 1)
    jaf = L.jaf_literal_encode(jaf)
    (work / 'x.jaf').write_text(jaf, 'utf8')
    decl = work / 'x_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'x.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'x_declared_meta.json', decl)
    dm = L.read_meta(work / 'x_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    for f in m['functions']:
        if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47:
            if f['name'] == 'C_UserInputManager::IsClickCancelOtherMouse':
                patch.append(f"FUNC {f['index']}\n\tPUSH 1\n\tCALLFUNC KR_XTick\n\tRETURN\nENDFUNC {f['name']}\n")
            elif f['name'] == 'C_UserInputManager::IsClickCancel':
                patch.append(f"FUNC {f['index']}\n\tPUSH 2\n\tCALLFUNC KR_XTick\n\tRETURN\nENDFUNC {f['name']}\n")
            else:
                patch.append(f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n")
    for f in added:
        path = work / f"x_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(L.clean(L.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), f['name']))
    om = L.fid_of(m, 'C_SceneTrainingView@GetOnmouseChara')
    patch.append(f"FUNC {om}\n\tS_PUSH \"Hover\"\n\tCALLFUNC KR_XNum\n\tRETURN\nENDFUNC C_SceneTrainingView@GetOnmouseChara\n")
    rs = L.fid_of(m, 'C_SceneHomebase@RunStatus')
    path = work / f'original_{rs}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SceneHomebase@RunStatus', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SceneHomebase@RunStatus'), '\t.LOCALREF charaNo\n\t.LOCALREF memView\n\tCALLFUNC KR_XPrepStatus\n'))
    (work / 'x.jam').write_text('\n'.join(patch), 'utf8')
    out = P.RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'x.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_XMain'])
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    vers = L.versions(raw_jam)
    n = 0
    for f in m['functions']:
        name = L.raw_symbol(m, f['index'])
        if not name.startswith(P.MSG_LAMBDA):
            continue
        for v in [v for v in vers.get(f['index'], []) if v['start'] == f['address']]:
            for ad, op in v['ops']:
                if op == f'CALLFUNC 0x{wait:x}':
                    struct.pack_into('<Hi', raw, 16 + ad, 0x30, ids['KR_XMsgWait'])
                    n += 1
    assert n == 1, n
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    return dict(probe_sha256=L.sha(out))


def main():
    mode = sys.argv[1]
    save = sys.argv[2] if len(sys.argv) > 2 else ('NightR44.asd' if mode == 'member' else 'NightR40.asd')
    assert shutil.disk_usage('P:\\').free >= 10 * 1024 ** 3
    user_before = P.user_state()
    P.setup_folder()
    key = L.save_records(L.save_path(save))['key']
    info = build(mode, key)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    r = P.run_one(save, 'regs', info, 'S' + stamp)
    from PIL import Image
    dest = OUT / mode
    dest.mkdir(parents=True, exist_ok=True)
    shots = []
    for b in sorted(P.RUN.glob('s_*.bmp')):
        Image.open(b).save(dest / (b.stem + '.png'))
        b.unlink()
        shots.append(b.stem + '.png')
    r['screenshots'] = shots
    r['user_save_folder_unchanged'] = P.user_state() == user_before
    L.writej(dest / 'result.json', r)
    print(json.dumps({k: v for k, v in r.items() if k != 'log'}, ensure_ascii=False, indent=1))
    print('\n'.join(r['log']))


if __name__ == '__main__':
    main()
