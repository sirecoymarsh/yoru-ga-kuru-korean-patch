"""Muted isolated native UI tour; instrumentation is not shipped."""
from pathlib import Path
import sys,shutil,json,inspect,datetime,re
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import probe_chart_r24 as P
L=P.L;O=L.CODEX/'staging/calendar_portraits_20260929'
L.WORK=O/'work';L.EVID=O/'evidence';L.TMP=O/'work/tmp'
shutil.copy2(F/'work/savecopy_manifest.json',L.WORK/'savecopy_manifest.json')
P.O=O/'candidate';P.PROBE=O/'probe';P.RUN=P.PROBE/'run'
L.BASE_WINMM_SHA=L.sha(O/'source/winmm.dll')
L.BASE_AIN_SHA=L.sha(O/'source/NightRemaster.ain')
P.LIVE_WAITS=P.LIVE_WAITS+['KR_P29WaitRaw']
orig=P.setup_folder
def setup():
    assert P.RUN.resolve().is_relative_to(O.resolve())
    rt=orig();shutil.copy2(P.O/'winmm.dll',P.RUN/'winmm.dll');return rt
P.setup_folder=setup
extra=r'''
int KR_Q29Ours() {
    int n = 0;
    for (int i = 0; i < 80; i++) if (PartsEngine.IsExist(KR_P29Part(i))) n++;
    for (int s = 0; s < 12; s++) for (int j = 0; j < 6; j++) if (PartsEngine.IsExist(KR_P29Mini(s,j))) n++;
    return n;
}
void KR_Q29Ensure(bool yes, string name) {
    if (yes) { KR_P22Log("PASS " + name); return; }
    KR_P22Log("FAIL " + name); KR_P22Shot("portrait_fail"); system.Exit(29);
}
bool KR_Q29Read(int no) {
    string mode = KR_CGet("ProbeRead");
    if (mode == "0") return false;
    if (mode == "1") return true;
    return KR_CGlobal(no) == 1;
}
void KR_Q29WaitFrame() {
    if (KR_P22Num("QFrames") < 8) { KR_P22SetN("QFrames", KR_P22Num("QFrames") + 1); return; }
    AFL_Parts_EndWaitForClick(KR_P22Num("QReply"));
}
void KR_Q29Tour() {
    KR_CSet("Open", "1"); KR_CSet("All", "1"); KR_CSet("Ctx", "1"); KR_CSet("ProbeRead", "1");
    KR_CDraw(0,0);
    KR_Q29Ensure(KR_CCellEv(0)==1 && KR_CCellEv(1)==2 && KR_CCellEv(2)==121,"opening order 1/2/121");
    KR_P22Shot("portraits_list_april");
    KR_CDraw(1,0); KR_P22Shot("portraits_list_may");
    for (int i = 0; i < 915; i++) {
        KR_C24DrawCell(0,i);
        int no = KR_CCellEv(i);
        bool face = KR_P29Count(no)>0;
        if (PartsEngine.IsExist(KR_P29Mini(0,0)) != face) { KR_P22Log("bad cell "+("%d"%i)); system.Exit(29); }
        if (face) {
            int w=0; int h=0;
            PartsEngine.Parts_GetPartsSize(KR_P29Mini(0,0),w,h,1);
            if (w!=240 || h!=300) { KR_P22Log("bad face load "+("%d"%i)); system.Exit(29); }
        }
    }
    KR_P22Log("PASS all 915 list cells rendered");
    KR_CShow(false);
    KR_P29Board(11,KR_T19EvHead(11),1,true); KR_P22Shot("portraits_detail_e00011");
    int fw = 0;
    int fh = 0;
    PartsEngine.Parts_GetPartsSize(KR_P29Part(10),fw,fh,1);
    KR_P22Log("FACE SIZE "+("%d"%fw)+"x"+("%d"%fh)+" alpha="+("%d"%PartsEngine.GetComponentAlpha(KR_P29Part(10)))+" mag="+("%f"%PartsEngine.GetComponentMagX(KR_P29Part(10))));
    KR_Q29Ensure(fw==240 && fh==300,"face asset really loaded");
    KR_Q29Ensure(KR_P29Count(11)==3,"E00011 exact cast, mentioned Manami excluded");
    KR_P29Board(328,KR_T19EvHead(328),2,true); KR_P22Shot("portraits_detail_twelve");
    KR_Q29Ensure(KR_P29Count(328)==12,"twelve participants in two rows");
    KR_P29Board(328,"포트레이트 자산 검증 (동시 등장 예시 아님)",1,true);
    KR_CDrop(KR_P29Part(4));
    for (int j = 0; j < 16; j++) {
        KR_P29Face(KR_P29Part(10+j*2),KR_P29Part(0),j,float(28+(j%8)*136),float(148+(j/8)*172),104.0/240.0);
        KR_CText(KR_P29Part(11+j*2),KR_P29Part(0),float(28+(j%8)*136),float(285+(j/8)*172),18,KR_P29Name(j),4);
    }
    KR_P22Shot("portraits_roster_asset_test");
    KR_CSet("ProbeRead", "0");
    KR_P29Board(11,KR_T19EvHead(11),1,true); KR_P22Shot("portraits_detail_unread_unlocked");
    for (int j = 0; j < 16; j++) KR_Q29Ensure(!PartsEngine.IsExist(KR_P29Part(10+j*2)),"unread no face "+("%d"%j));
    KR_Q29Ensure(!PartsEngine.IsExist(KR_P29Part(4)),"unread summary absent");
    KR_P29ClearBoard(); KR_CDraw(1,0); KR_P22Shot("portraits_list_unread_unlocked");
    for (int s=0;s<12;s++) for (int j=0;j<4;j++) if(PartsEngine.IsExist(KR_P29Mini(s,j))) system.Exit(29);
    KR_P22Log("PASS unread list no faces or counts, even with unlock all");
    KR_CShow(false); KR_CSet("ProbeRead","1");
    KR_P22SetN("QFrames",0); KR_P22SetN("QReply",0);
    int r = KR_P29Run(11,KR_T19EvHead(11),1,true);
    KR_Q29Ensure(r==0,"native detail wait cancel returns zero");
    KR_P22SetN("QFrames",0); KR_P22SetN("QReply",KR_P29Part(60));
    r=KR_P29Run(11,KR_T19EvHead(11),1,true);
    KR_Q29Ensure(r==13,"native detail replay button returns 13");
    KR_P22SetN("QFrames",0); KR_P22SetN("QReply",KR_P29Part(62));
    r=KR_P29Run(328,KR_T19EvHead(328),2,true);
    KR_Q29Ensure(r==14,"native detail stages button returns 14");
    KR_P22SetN("QFrames",0); KR_P22SetN("QReply",KR_P29Part(60));
    r=KR_P29Run(11,KR_T19EvHead(11),1,false);
    KR_Q29Ensure(r==0,"locked replay rejected");
    KR_T9Set("Unwind",""); KR_CSet("Play","");
    KR_P22SetN("QFrames",0); KR_P22SetN("QReply",KR_P29Part(60));
    KR_T9EventPage(11,"");
    KR_Q29Ensure(KR_CGet("Play")=="11" && KR_T9Unwinding(),"event detail forwards to guarded replay request");
    KR_T9Set("Unwind",""); KR_CSet("Play","");
    KR_P22SetN("QFrames",0); KR_P22SetN("QReply",0);
    KR_T9CardPage(KR_CCellRef(KR_CTabFirst(1))-100000,5);
    KR_Q29Ensure(!KR_T9Unwinding(),"card detail cancel returns normally");
    KR_P29Board(262,KR_T19EvHead(262),1,false); KR_P22Shot("portraits_detail_no_replay");
    KR_CClear(); KR_Q29Ensure(KR_Q29Ours()==0,"all portrait parts released");
    KR_CSet("Open",""); KR_CSet("ProbeRead",""); KR_CSet("All","");
    KR_P22Shot("portraits_title_after");
    KR_P22Log("END"); system.Exit(0);
}
'''
# Use the real title initialization; run once at its existing frame boundary.
P.PROBE_JAF+=extra
P.PROBE_JAF=P.PROBE_JAF.replace('        @@BOOT@@','        KR_Q29Tour();\n        @@BOOT@@')
source=inspect.getsource(P.build_probe)
source=source.replace("    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')", "    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')\n    prefix('KR_P29Frame', '\\tCALLFUNC KR_Q29WaitFrame\\n')\n    patch.append(f\"FUNC {L.fid_of(m, 'KR_P29Read')}\\n\\t.LOCALREF no\\n\\tCALLFUNC KR_Q29Read\\n\\tRETURN\\nENDFUNC KR_P29Read\\n\")")
assert "prefix('KR_P29Frame'" in source
(O/'probe/build_probe_instrumentation.py').write_text(source,'utf8')
exec(compile(source,'private_portrait_probe','exec'),P.__dict__)
before=P.user_state();rt=P.setup_folder()
assert L.sha(rt/'NightRemaster.ain')==L.BASE_AIN_SHA
info=P.build_probe('title')
r=P.one_run('title',datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),timeout=240)
r['probe']=info;r['shots']=P.collect_shots('native_portraits');r['candidate_sha256']=L.sha(P.O/'NightRemaster.ain')
after=P.user_state();r['user_files_changed']=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
r['pass']=r.get('exit_code')==0 and 'END' in r['log'] and not any(k in r for k in ['vm_error','message','timeout']) and not r['user_files_changed']
L.writej(O/'evidence/native_portrait_probe.json',r)
print(json.dumps({k:v for k,v in r.items() if k not in ['events','probe']},ensure_ascii=False,indent=2))
assert r['pass']
