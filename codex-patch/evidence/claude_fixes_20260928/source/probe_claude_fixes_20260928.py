"""Reuse the earlier muted, private-save native tour; never edit Claude's probe."""
from pathlib import Path
import sys,shutil,json
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F))
import probe_chart_r24 as P
L=P.L;O=L.CODEX/'staging/claude_fixes_20260928'
L.WORK=O/'work';L.EVID=O/'evidence';L.TMP=O/'work/tmp'
shutil.copy2(F/'work/savecopy_manifest.json',L.WORK/'savecopy_manifest.json')
P.O=O/'candidate';P.PROBE=O/'probe';P.RUN=P.PROBE/'run'
original_setup=P.setup_folder
def setup():
    rt=original_setup();shutil.copy2(P.O/'winmm.dll',P.RUN/'winmm.dll');return rt
P.setup_folder=setup
P.PROBE_JAF=P.PROBE_JAF.replace('KR_P22Cells("HOME OPEN");',
    'KR_P22Log("FIX28 root Z="+("%d" % PartsEngine.GetComponentAbsolutePosZ(KR_CRoot()))); KR_P22Cells("HOME OPEN");')
P.PROBE_JAF=P.PROBE_JAF.replace('if (n == 1) {','''if (n == 1) {
    string fname = "blocked_snapshot";
    bool disabled=KR_F28SaveBlocked();
    bool manual=KR_F28ExecSave(89,false);
    bool automatic=KR_F28ExecSave(89,true);
    bool snapshot=KR_F28Snapshot(fname);
    KR_F28QuickSave();
    KR_P22Log("FIX28 BLOCKED="+("%d" % KR_P22B(disabled))+" manual="+("%d" % KR_P22B(manual))+" auto="+("%d" % KR_P22B(automatic))+" snapshot="+("%d" % KR_P22B(snapshot)));
    if(!disabled||manual||automatic||snapshot)system.Exit(28);
''')
P.main()
