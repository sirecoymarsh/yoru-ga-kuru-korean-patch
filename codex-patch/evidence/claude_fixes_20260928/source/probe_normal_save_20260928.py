from pathlib import Path
import sys,shutil
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import probe_chart_r24 as P
L=P.L;O=L.CODEX/'staging/claude_fixes_20260928'
L.WORK=O/'work';L.EVID=O/'evidence/normal_save';L.EVID.mkdir(exist_ok=True);L.TMP=O/'work/tmp'
P.O=O/'candidate';P.PROBE=O/'probe_save';P.RUN=P.PROBE/'run'
setup=P.setup_folder
def patched_setup():
    r=setup();shutil.copy2(P.O/'winmm.dll',P.RUN/'winmm.dll');return r
P.setup_folder=patched_setup
P.PROBE_JAF=P.PROBE_JAF.replace('KR_P22Log("HOME menu ours="', '''
        if (KR_F28SaveBlocked()) system.Exit(28);
        if (KR_P22Read("normal_save_resuming.txt") == "1") {
            KR_P22Log("PASS normal native auto-save and load through guarded method; END");
            system.Exit(0); return;
        }
        C_SceneSaveLoad saveScene;
        saveScene.RunAutoSave(88);
        if (KR_P22Read("normal_save_resuming.txt") == "1") {
            KR_P22Log("PASS normal native auto-save and load through guarded method; END");
            system.Exit(0); return;
        }
        if (!KR_T18SandboxSaved(gamesave::detail::セーブファイル名(88))) system.Exit(29);
        KR_P22Log("NORMAL SAVE 88 PRESENT");
        TextFile.WriteAll("normal_save_resuming.txt","1");
        AFL_GameSave_Load(88);
        system.Exit(30);
        KR_P22Log("HOME menu ours="''')
sys.argv=[sys.argv[0],'--home'];P.main()
r=L.readj(L.EVID/'probe_chart_r24.json')['home']
assert r.get('exit_code')==0 and not r.get('vm_error') and not r.get('message'),r
assert 'NORMAL SAVE 88 PRESENT' in r['log'] and any(s.startswith('PASS normal native') for s in r['log'])
