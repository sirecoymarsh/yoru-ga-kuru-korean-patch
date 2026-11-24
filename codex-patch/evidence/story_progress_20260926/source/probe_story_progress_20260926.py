"""Mute/private-save native save roundtrip, panels, and checkpoint assertions."""
import sys
import build_story_progress_20260926 as e
import probe_save_slots_20260925 as old
old.e=e
checks='void KR_StoryChecks() {\n'
checks+='N_ScenarioRegister::ClearAllEvent(); if(KR_StoryStage()!=0) { KR_ClaudeProbeLog("FAIL empty");system.Exit(81); }\n'
for code,label,ids in e.STAGES:
    for event in ids:
        checks+=f'N_ScenarioRegister::ClearAllEvent(); N_ScenarioRegister::RegisterEvent("ＥＶ／元／E{event:05d}"); if(KR_StoryStage()!={code}) {{ KR_ClaudeProbeLog("FAIL stage {code} event {event}");system.Exit(82); }}\n'
checks+='N_ScenarioRegister::ClearAllEvent(); N_ScenarioRegister::RegisterEvent("ＥＶ／元／エンディング終了"); if(KR_StoryStage()!=13) { KR_ClaudeProbeLog("FAIL ending");system.Exit(83); }\n'
checks+='N_ScenarioRegister::RegisterEvent("ＥＶ／元／E00001"); if(KR_StoryStage()!=13) { KR_ClaudeProbeLog("FAIL regression");system.Exit(84); }\n'
checks+='N_ScenarioRegister::ClearAllEvent(); N_ScenarioRegister::RegisterEvent("ＥＶ／元／E10001"); if(KR_StoryStage()!=0) { KR_ClaudeProbeLog("FAIL side-event advanced story");system.Exit(85); }\n'
checks+='for(int y=0;y<410;y++) { int want=0; if(y>=220 && y<388) want=(y-52)/24-5; if(KR_T8HomeRow(y)!=want) { KR_ClaudeProbeLog("FAIL home click mapping");system.Exit(86); }}\n'
checks+='KR_ClaudeProbeLog("PASS story checkpoint aliases, side-event separation, home click rows");\n}\n'
old.QA_JAF += '\n'+e.base.korean(checks)
extra=r'''
    KR_ClaudeProbeLog("STORY="+("%d" % KR_StoryStage())+" "+KR_StoryNow());
    KR_ClaudeProbeLog("HOME_TEXT="+KR_T8HomeRateText());
    if(KR_SaveScene()!=11) {
        SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","info");
        KR_T8PlayerInfoMenu();
        SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","detail");
        KR_T8EventDetail(KR_PlayerEventCount(0),KR_PlayerEventCount(1),KR_PlayerEventCount(2),KR_PlayerEventCount(3));
    }
    if(KR_SaveScene()==11) { KR_T8HomeShow(true);KR_ClaudeShot("story_home.bmp"); }
    KR_StoryChecks();
'''
old.g.AUTO_JAF=old.g.AUTO_JAF.replace('if(stage=="load")', 'if(stage=="info" || stage=="detail") { KR_ClaudeShot("story_"+stage+".bmp");return 0; }\n    if(stage=="load")')
old.g.AUTO_JAF=old.g.AUTO_JAF.replace('KR_ClaudeProbeLog("END");',extra+'\n    KR_ClaudeProbeLog("END");')
setup=old.c.setup_folder
def enabled():
    setup();(old.c.SAVES/'YoruKR_HomeRate.dat').write_bytes(b'YoruKR.HomeRate.1\r\n1\r\n')
old.c.setup_folder=enabled
if __name__=='__main__':old.main(sys.argv[1] if len(sys.argv)>1 else 'NightR36.asd')
