"""Muted isolated real-save HUD visibility/cache checks in home, dungeon and dialogue."""
import sys,shutil,struct,re,json,datetime
from pathlib import Path
sys.dont_write_bytecode=True
import build_rate_overlay_20260927 as b
l=b.l;p=b.p;O=b.O
import probe_calendar_r15 as q
from PIL import Image

JAF=q.PROBE_JAF[:q.PROBE_JAF.index('/*TARGETS*/')]+r'''
void KR_CalProbeTick() {}
void KR_RateProbeAssert(bool on) {
    int found=0;
    for(int i=-1;i<4;i++) {
        string act=KR_T8AreaName(i);
        if(!AFL_Activity_IsExistPartsByName(act,"KR_HomeRate")) continue;
        int panel=AFL_Activity_GetPartsNumber(act,"KR_HomeRate");
        int body=AFL_Activity_GetPartsNumber(act,"KR_HomeRateBody");
        if(Ｐ＿表示設定取得(panel)!=on) { KR_ClaudeProbeLog("FAIL visible");system.Exit(41); }
        if(on && Ｐ＿テキスト取得(body,1)!=KR_RateGet("Body")) { KR_ClaudeProbeLog("FAIL text");system.Exit(42); }
        found++;
    }
    if(found==0) { KR_ClaudeProbeLog("FAIL no panel");system.Exit(43); }
}
void KR_RateProbeFrame() {
    if(KR_CPGet("Running")=="1") return;
    if(!KR_PlayerReady()) return;
    int count=KR_CPNum("Frames")+1;KR_CPSet("Frames","%d"%count);
    if(count<35) return;
    KR_CPSet("Running","1");
    KR_T8HomeRateSet(true);KR_RateRender(true);KR_RateProbeAssert(true);
    KR_ClaudeProbeLog("READY home="+SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu")+" builds="+KR_RateGet("Builds")+" ms="+KR_RateGet("BuildMs"));
    KR_ClaudeShot("cal_on.bmp");
    string builds=KR_RateGet("Builds");
    for(int i=0;i<50;i++) {KR_RateSet("Tick","");KR_RateTick();}
    if(KR_RateGet("Builds")!=builds) {KR_ClaudeProbeLog("FAIL cache");system.Exit(44);}
    KR_ClaudeProbeLog("CACHE 50 updates no rescan");
    KR_T8HomeLeave();KR_RateProbeAssert(true);
    KR_ClaudeProbeLog("HOME LEAVE keeps visible");
    KR_T8HomeRateSet(false);KR_RateRender(false);KR_RateProbeAssert(false);KR_ClaudeShot("cal_off.bmp");
    KR_T8HomeRateSet(true);KR_RateRender(true);KR_RateProbeAssert(true);KR_ClaudeShot("cal_reenabled.bmp");
    KR_RateAfterLoad();if(KR_RateGet("Body")!="") system.Exit(45);
    KR_RateRender(true);KR_RateProbeAssert(true);
    KR_ClaudeProbeLog("LOAD INVALIDATION rebuilt");
    KR_RateEventReleased();if(KR_RateGet("Body")!="") system.Exit(46);
    KR_RateRender(true);KR_RateProbeAssert(true);
    KR_ClaudeProbeLog("EVENT INVALIDATION rebuilt");
    KR_ClaudeProbeLog("END");system.Exit(0);
}
int KR_CalProbeMsgWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    while(true) { AFL_View_Update(); }
    return 0;
}
int KR_CalProbeWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    while(true) { AFL_View_Update(); }
    return 0;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0,"NightRAFCGMode.asd");
    PassRegister.SetFileName(1,"NightRAFMemMode.asd");
    PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("SAVEFOLDER "+system.GetSaveFolderName());
    KR_ClaudeProbeLog("resume @@SAVE@@");
    system.ResumeLoad("@@KEY@@","@@SAVE@@");system.Exit(2);return 2;
}
'''

def main():
    assert not p.processes(),'Do not launch while the player game is open'
    label=sys.argv[1];save={'home':'NightR47.asd','dungeon':'NightR45.asd','dialogue':'NightR49.asd','battle':'NightR47.asd','title':'NightR47.asd'}[label]
    ev=l.readj(O/'build_evidence.json');assert all(l.sha(O/n)==h for n,h in ev['files'].items())
    root=O/('native_'+label);root.mkdir(exist_ok=True);q.PROBE=root;q.RUN=root/'run';q.RUN.mkdir(exist_ok=True)
    q.PROBE_JAF=JAF;q.BOOT='NightRemasterRateProbe';q.safe_targets=lambda:{};q.target_jaf=lambda targets:''
    if label=='battle':
        # Return through the real home-menu cleanup before entering the game's event-battle routine.
        q.PROBE_JAF=q.PROBE_JAF.replace('    KR_CPSet("Running","1");', '''    if(KR_CPGet("Stage")=="") {
        if(SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu")!="1") return;
        KR_CPSet("Stage","battle");KR_CPSet("Frames","0");
        AFL_Parts_EndWaitForClick(3);return;
    }
    if(KR_CPGet("BattleStarted")!="1") return;
    KR_CPSet("Running","1");''')
        q.PROBE_JAF+='\nvoid KR_RateProbeBattleStart() { KR_CPSet("BattleStarted","1"); KR_CPSet("Frames","0"); KR_ClaudeProbeLog("ACTUAL EVENT BATTLE 7"); ■イベント戦闘実行(0); system.Exit(47); }\n'
    if label=='title':
        a=q.PROBE_JAF.index('void KR_RateProbeFrame()');z=q.PROBE_JAF.index('int KR_CalProbeMsgWait(',a)
        q.PROBE_JAF=q.PROBE_JAF[:a]+r'''void KR_RateProbeFrame() {
    if(KR_CPGet("Running")=="1") return;
    if(KR_CPGet("Start")=="") {KR_CPSet("Start","%d"%KR_Time());return;}
    if(KR_Time()-KR_CPNum("Start")<8000) return;
    KR_CPSet("Running","1");
    if(KR_PlayerReady()) {KR_ClaudeProbeLog("FAIL title ready");system.Exit(48);}
    KR_ClaudeShot("cal_title.bmp");KR_ClaudeProbeLog("NORMAL STARTUP no gameplay HUD");KR_ClaudeProbeLog("END");system.Exit(0);
}
'''+q.PROBE_JAF[z:]
    work=root/'build';work.mkdir(exist_ok=True)
    l.WORK=O/'probe_work';(l.WORK/'build').mkdir(parents=True,exist_ok=True)
    for name in ['candidate_meta.json','candidate_raw_code.jam']:shutil.copy2(O/name,l.WORK/'build'/name)
    original_runtime=l.runtime;l.runtime=lambda:(l.readj(O/'source_pointer.json'),Path(l.readj(O/'source_pointer.json')['runtime']))
    key=l.save_records(l.SAVES/save)['key'];before=p.snapshot_saves()
    info=q.build_probe(O,key,save,False,work)
    # Add the native test driver after the installed HUD tick, preserving its behavior.
    pr=q.RUN/'NightRemaster.ain';l.cmd('ain','dump','-j','-o',work/'m.json',pr);m=l.read_meta(work/'m.json')
    name='KR_RateViewUpdate';fid=l.fid_of(m,name)
    body=b.dump(m,fid,pr);body=body.replace('\tCALLFUNC KR_RateTick\n','\tCALLFUNC KR_RateTick\n\tCALLFUNC KR_RateProbeFrame\n')
    if label=='battle':
        name='KR_T9HomeCasual';fid=l.fid_of(m,name)
        assert not m['functions'][fid]['arguments']
        body+=f'\nFUNC {fid}\n\tCALLFUNC KR_RateProbeBattleStart\n\tRETURN\nENDFUNC {name}\n'
    if label=='title':
        original=l.unpack((O/'NightRemaster.ain').read_bytes());mainid=struct.unpack_from('<I',original,original.index(b'MAIN')+4)[0]
        body+='\n'+l.begin(b.dump(m,mainid,pr),'\tCALLFUNC KR_DiagnosticMute\n')
    (work/'frame.jam').write_text(body,'utf8');l.cmd('ain','edit','--jam',work/'frame.jam','-o',work/'instrumented.ain',pr)
    raw=bytearray(l.unpack((work/'instrumented.ain').read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
    if label=='title':
        original=l.unpack((O/'NightRemaster.ain').read_bytes());struct.pack_into('<I',raw,raw.index(b'MAIN')+4,struct.unpack_from('<I',original,original.index(b'MAIN')+4)[0])
    pr.write_bytes(l.pack(raw,pr.read_bytes()[:8]))
    info['probe_sha256']=l.sha(pr)
    l.writej(q.RUN/'probe_manifest.json',dict(source_sha256=ev['files']['NightRemaster.ain'],probe_sha256=l.sha(pr),audio=q.AUDIO_POLICY))
    savename='SaveData_RateProbe';q.setup_folder(O,savename)
    for n in ['NightRemasterPact.afa','NightRemasterEX.ex']:
        src=O/n if (O/n).exists() else b.S/n
        for dest in [n,n.replace('NightRemaster',q.BOOT,1)]:shutil.copy2(src,q.RUN/dest)
    sd=q.RUN/savename;sd.mkdir(exist_ok=True)
    for n in q.COPY_GLOBAL:
        if (l.SAVES/n).exists():shutil.copy2(l.SAVES/n,sd/n)
    shutil.copy2(l.SAVES/save,sd/save)
    (sd/'YoruKR_HomeRate.dat').write_bytes(b'YoruKR.HomeRate.1\n1\n')
    result=q.launch(90)
    log=q.RUN/'claude_probe.txt';result['log']=l.decode(log.read_bytes()).splitlines() if log.exists() else []
    result.update(source_sha256=ev['files']['NightRemaster.ain'],pact_sha256=ev['files']['NightRemasterPact.afa'],probe_sha256=info['probe_sha256'],real_saves_unchanged=before==p.snapshot_saves(),save=save)
    for img in q.RUN.glob('cal_*.bmp'):Image.open(img).save(root/(img.stem+'.png'))
    l.writej(root/'result.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
    assert result.get('exit_code')==0 and result['log'][-1]=='END' and not result['events'] and result['real_saves_unchanged']
if __name__=='__main__':main()
