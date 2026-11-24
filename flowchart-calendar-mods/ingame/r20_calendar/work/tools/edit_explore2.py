p = __file__.replace('edit_explore2.py', 'explore_r20.py')
s = open(p, encoding='utf8').read()
start = s.index("PARTNER = r'''")
end = s.index("'''", start + 15) + 3
new = r"""PARTNER = r'''
    if (stage == "") {
        if (KR_XOn("C_SceneSaveLoad@Update")) { KR_XShot("x_saveload.bmp"); KR_XSet("Frames", "0"); return true; }
        if (!KR_XOn("_UpdateInputPartner")) return false;
        KR_XLog("PARTNER date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " dow=" + ("%d" % L_Calendar::GetDayOfWeek()) + " free=" + ("%d" % PartsEngine.GetFreeNumber()));
        for (int p = 2; p <= 8; p++) KR_XLog("CANSELECT " + ("%d" % p) + " " + ("%d" % KR_XB(LAbility::CanSelect(p))));
        KR_XShot("x_partner.bmp");
        KR_XDumpActs("Game\\Scenes\\Common\\SelectAlly.pact");
        KR_XDumpActs("Game\\Scenes\\2000Training\\TrainingSub.pact");
        KR_XDumpActs("Game\\Scenes\\2000Training\\TrainingPartnerStand.pact");
        KR_XDumpActs("Game\\Scenes\\2000Training\\TrainingStatus.pact");
        KR_XTextTest(0, 200, 470);
        KR_XShot("x_partner_texttest.bmp");
        KR_XTextRelease();
        KR_XSet("Hover", "3");
        KR_XSet("Stage", "hover");
        return false;
    }
    if (stage == "hover") {
        if (frames < 90) return false;
        KR_XShot("x_partner_hover3.bmp");
        KR_XDumpActs("Game\\Scenes\\2000Training\\TrainingPartnerStand.pact");
        KR_XSet("Hover", "7");
        KR_XSet("Stage", "hover2");
        KR_XSet("Frames", "0");
        return false;
    }
    if (stage == "hover2") {
        if (frames < 90) return false;
        KR_XShot("x_partner_hover7.bmp");
        KR_XLog("END");
        system.Exit(0);
    }
'''"""
s = s[:start] + new + s[end:]
a = "    rs = L.fid_of(m, 'C_SceneHomebase@RunStatus')"
b = """    om = L.fid_of(m, 'C_SceneTrainingView@GetOnmouseChara')
    patch.append(f"FUNC {om}\\n\\tS_PUSH \\"Hover\\"\\n\\tCALLFUNC KR_XNum\\n\\tRETURN\\nENDFUNC C_SceneTrainingView@GetOnmouseChara\\n")
""" + a
if 'GetOnmouseChara' not in s:
    assert s.count(a) == 1
    s = s.replace(a, b)
open(p, 'w', encoding='utf8').write(s)
print('ok')
