"""One muted private run: retained information, 915 layouts, unread, and close paths."""
from pathlib import Path
import sys,shutil,json,inspect,datetime
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import probe_chart_r24 as P
L=P.L;O=L.CODEX/'staging/calendar_detail_layout_20260929'
L.WORK=O/'work';L.EVID=O/'evidence';L.TMP=O/'work/tmp'
shutil.copy2(F/'work/savecopy_manifest.json',L.WORK/'savecopy_manifest.json')
P.O=O/'candidate';P.PROBE=O/'probe';P.RUN=P.PROBE/'run'
L.BASE_WINMM_SHA=L.sha(O/'source/winmm.dll');L.BASE_AIN_SHA=L.sha(O/'source/NightRemaster.ain')
P.LIVE_WAITS=P.LIVE_WAITS+['KR_P29WaitRaw']
orig=P.setup_folder
def setup():
    assert P.RUN.resolve().is_relative_to(O.resolve())
    return orig()
P.setup_folder=setup
extra=r'''
bool KR_Q29Read(int no) {
    string mode=KR_CGet("ProbeRead");
    if(mode=="0")return false;
    if(mode=="1")return true;
    return KR_CGlobal(no)==1;
}
void KR_Q29WaitFrame() {
    if(KR_P22Num("QFrames")<8){KR_P22SetN("QFrames",KR_P22Num("QFrames")+1);return;}
    AFL_Parts_EndWaitForClick(KR_P22Num("QReply"));
}
void KR_Q29Ensure(bool yes,string name) {
    if(yes){KR_P22Log("PASS "+name);return;}
    KR_P22Log("FAIL "+name);KR_P22Shot("detail_fail");system.Exit(29);
}
void KR_Q29Bounds(int no) {
    int w=0;int h=0;int iw=0;int ih=0;
    PartsEngine.Parts_GetPartsSize(KR_P29Part(0),w,h,1);
    PartsEngine.Parts_GetPartsSize(KR_P29Part(4),iw,ih,1);
    int x=int(PartsEngine.GetComponentPosX(KR_P29Part(4)));
    int y=int(PartsEngine.GetComponentPosY(KR_P29Part(4)));
    int buttonY=int(PartsEngine.GetComponentPosY(KR_P29Part(64)));
    if(h>680 || x+iw>w-20 || y+ih>buttonY-12) {
        KR_P22Log("BOUNDS FAIL "+("%d"%no)+" board="+("%d"%w)+"x"+("%d"%h)+" info="+("%d"%x)+","+("%d"%y)+","+("%d"%iw)+","+("%d"%ih));
        KR_P22Shot("detail_bounds_fail");system.Exit(29);
    }
}
void KR_Q29Detail(int no,int k,string shot) {
    int stages=1;
    string head=KR_T19EvHead(no);
    if(k>=0){stages=KR_T9CardSize(k);head=KR_T19CardHead(k);}
    KR_P29Board(no,head,stages,KR_CCanPlay(no)); KR_Q29Bounds(no);
    KR_P22Log("OLD WHEN "+KR_T19EvWhen(no));
    KR_P22Log("OLD WHO "+KR_T9EvWho(no));
    if(k>=0 && stages>1)KR_P22Log("OLD STAGES "+("%d"%KR_T9CardSeenStages(k))+"/"+("%d"%stages));
    KR_P22Log("DETAIL "+("%d"%no)+" <<<\n"+KR_B29Info(no,stages,22)+"\n>>>");
    KR_P22Shot(shot);
}
void KR_Q29Tour() {
    KR_CSet("Open","1");KR_CSet("Ctx","1");KR_CSet("All","1");KR_CSet("ProbeRead","1");
    KR_CDraw(1,0);KR_P22Shot("detail_list_unchanged");KR_CShow(false);
    for(int i=0;i<915;i++) {
        int no=KR_CCellEv(i);int cref=KR_CCellRef(i);int stages=1;string head=KR_T19EvHead(no);
        if(cref>=100000){stages=KR_T9CardSize(cref-100000);head=KR_T19CardHead(cref-100000);}
        KR_P29Board(no,head,stages,KR_CCanPlay(no));KR_Q29Bounds(no);
    }
    KR_P22Log("PASS all 915 detail boards fit, no clipped info");
    KR_Q29Detail(11,7,"detail_e00011");
    KR_Q29Detail(16,12,"detail_stage_progress");
    KR_Q29Detail(1,1,"detail_opening_cast");
    KR_Q29Detail(328,-1,"detail_twelve_cast");
    KR_Q29Detail(1001,-1,"detail_long_conditions");
    KR_Q29Detail(262,73,"detail_no_replay");
    KR_CSet("ProbeRead","0");KR_P29Board(11,KR_T19EvHead(11),1,true);KR_Q29Bounds(11);
    KR_P22Shot("detail_unread_unlocked");
    for(int i=0;i<16;i++)if(PartsEngine.IsExist(KR_P29Part(10+i*2)))system.Exit(29);
    KR_P22Log("UNREAD <<<\n"+KR_B29Info(11,1,22)+"\n>>>");
    KR_CSet("ProbeRead","1");KR_P22SetN("QFrames",0);KR_P22SetN("QReply",0);
    int r=KR_P29Run(11,KR_T19EvHead(11),1,true);KR_Q29Ensure(r==0,"detail cancel");
    KR_T9Set("Unwind","");KR_CSet("Play","");KR_P22SetN("QFrames",0);KR_P22SetN("QReply",KR_P29Part(60));
    KR_T9CardPage(7,5);KR_Q29Ensure(KR_CGet("Play")=="11" && KR_T9Unwinding(),"card guarded replay request");
    KR_T9Set("Unwind","");KR_CSet("Play","");KR_P22SetN("QFrames",0);KR_P22SetN("QReply",KR_P29Part(62));
    r=KR_P29Run(16,KR_T19CardHead(12),2,true);KR_Q29Ensure(r==14,"stage button");
    KR_CClear();
    for(int i=0;i<80;i++)if(PartsEngine.IsExist(KR_P29Part(i)))system.Exit(29);
    KR_P22Log("PASS all detail parts released");KR_CSet("Open","");KR_CSet("ProbeRead","");KR_CSet("All","");
    KR_P22Shot("detail_title_after");KR_P22Log("END");system.Exit(0);
}
'''
P.PROBE_JAF+=extra;P.PROBE_JAF=P.PROBE_JAF.replace('        @@BOOT@@','        KR_Q29Tour();\n        @@BOOT@@')
source=inspect.getsource(P.build_probe)
source=source.replace("    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')", "    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')\n    prefix('KR_P29Frame', '\\tCALLFUNC KR_Q29WaitFrame\\n')\n    patch.append(f\"FUNC {L.fid_of(m, 'KR_P29Read')}\\n\\t.LOCALREF no\\n\\tCALLFUNC KR_Q29Read\\n\\tRETURN\\nENDFUNC KR_P29Read\\n\")")
assert "prefix('KR_P29Frame'" in source
(O/'probe/build_probe_instrumentation.py').write_text(source,'utf8');exec(compile(source,'private_detail_probe','exec'),P.__dict__)
before=P.user_state();rt=P.setup_folder();assert L.sha(rt/'NightRemaster.ain')==L.BASE_AIN_SHA
info=P.build_probe('title');r=P.one_run('title',datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),timeout=300)
r['probe']=info;r['shots']=P.collect_shots('native_detail');r['candidate_sha256']=L.sha(P.O/'NightRemaster.ain')
after=P.user_state();r['user_files_changed']=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
r['pass']=r.get('exit_code')==0 and 'END' in r['log'] and not any(k in r for k in ['vm_error','message','timeout']) and not r['user_files_changed']
L.writej(O/'evidence/native_detail_probe.json',r)
print(json.dumps({k:v for k,v in r.items() if k not in ['events','probe']},ensure_ascii=False,indent=2));assert r['pass']
