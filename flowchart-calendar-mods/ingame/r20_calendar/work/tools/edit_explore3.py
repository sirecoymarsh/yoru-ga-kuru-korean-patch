p = __file__.replace('edit_explore3.py', 'explore_r20.py')
s = open(p, encoding='utf8').read()
start = s.index("PARTNER = r'''")
end = s.index("'''", start + 15) + 3
new = r"""PARTNER = r'''
    if (stage == "") {
        if (KR_XOn("C_SceneSaveLoad@Update")) { KR_XShot("x_saveload.bmp"); KR_XSet("Frames", "0"); return true; }
        if (!KR_XOn("_UpdateInputPartner")) return false;
        KR_XLog("PARTNER date=" + ("%d" % L_Calendar::GetMonth()) + "/" + ("%d" % L_Calendar::GetDay()) + " dow=" + ("%d" % L_Calendar::GetDayOfWeek()) + " free=" + ("%d" % PartsEngine.GetFreeNumber()));
        KR_XTextTest(0, 200, 470);
        KR_XShot("x_reload_before.bmp");
        KR_XSet("Stage", "reloaded");
        KR_XSet("Frames", "0");
        KR_XLog("RELOAD now (parts made, not released)");
        system.ResumeLoad("@@KEY@@", "NightR40.asd");
        KR_XLog("RELOAD returned (should not)");
        system.Exit(11);
    }
    if (stage == "reloaded") {
        if (KR_XOn("C_SceneSaveLoad@Update")) { KR_XSet("Frames", "0"); return true; }
        if (!KR_XOn("_UpdateInputPartner")) return false;
        KR_XLog("AFTER RELOAD exist1=" + ("%d" % KR_XB(PartsEngine.IsExist(2026092701))) + " exist2=" + ("%d" % KR_XB(PartsEngine.IsExist(2026092702))) + " show1=" + ("%d" % KR_XB(PartsEngine.IsComponentShow(2026092701))) + " free=" + ("%d" % PartsEngine.GetFreeNumber()));
        KR_XShot("x_reload_after.bmp");
        KR_XTextRelease();
        KR_XLog("END");
        system.Exit(0);
    }
'''"""
s = s[:start] + new + s[end:]
open(p, 'w', encoding='utf8').write(s)
print('ok')
