"""Muted private-save native continuation test. No live saves or input."""
import sys,shutil,struct,json
from pathlib import Path
sys.dont_write_bytecode=True
import build_story_explore_20260927 as b
l=b.l;p=b.p;O=b.O
import probe_calendar_r15 as q
from PIL import Image
JAF=q.PROBE_JAF[:q.PROBE_JAF.index('/*TARGETS*/')]+r'''
string KR_SPState(ref C_SceneDungeon scene) {
    return "map="+("%d"%KR_ExploreMap(scene))+" floor="+("%d"%KR_ExploreFloor(scene))+" at="+("%d"%KR_WalkX())+","+("%d"%KR_WalkY())+" flag="+("%d"%KR_Flag(71))+" pending="+("%d"%KR_ExploreGet("Pending"))+" queue="+("%d"%KR_WalkCount(scene));
}
void KR_SPAssert(bool ok,string note) { if(!ok) {KR_ClaudeProbeLog("FAIL "+note);system.Exit(41);} }
void KR_StoryProbeSetupRest(ref C_SceneDungeon scene) { ref C_MapCellInfo cell; array<CASPos> route; }
void KR_SPBattleReady() {}
void KR_SPSetupStoryFloor(ref C_SceneDungeon scene) {}
bool KR_SPPartyChoice() {
    KR_ClaudeProbeLog("NATIVE PARTY CHOICE boundary messages="+KR_CPGet("Messages"));
    KR_SPAssert(KR_CPNum("Messages")>1 && KR_WalkOwn(),"automatic story before party choice");
    if("@@MODE@@"=="story_return") {
        KR_ClaudeProbeLog("FIXTURE retain current party; original choice UI tested separately");return true;
    }
    KR_CPSet("PartyPrompt","1");KR_CPSet("PartyFrames","0");
    return L_SelectParty::Run07();
}
void KR_SPDamage(int index) { ref C_Ability pa; }
bool KR_SPRecoveryAt(int index) { ref C_Ability pa; return false; }
bool KR_SPRecovered() { for(int i=0;i<3;i++) {if(!KR_SPRecoveryAt(i)) return false;} return true; }
void KR_SPCheckResult(ref C_SceneDungeon scene) {
    KR_ExploreSet("Pending",7);KR_ExploreSet("StoryActive",1);KR_Poke(71,2026092203);
    SystemService.SystemVariable_Set("YoruKR.Explore.ResultStarted","");
    KR_SPAssert(!KR_ExploreResultEnter(),"result readable delay starts");
    int started=KR_Time();while(KR_Time()-started<900) AFL_View_Update();
    KR_SPAssert(KR_ExploreResultEnter(),"story result automatically confirms");
    KR_ExploreLevelDialog("AUTO EXPLORATION RESUME TEST",0);
    KR_ClaudeProbeLog("PASS native story result timer and level notification closed without input");
    KR_ExploreStop(scene);KR_StoryClear();
}
void KR_SPRest(ref C_MapInfo map,ref C_SceneDungeon scene) {
    ref C_MapCellInfo cell=map.GetCellInfo(1,15);
    cell.ObjectType=8;
}
void KR_StoryProbeGuard(ref C_SceneDungeon scene) {
    if(KR_CPGet("Started")=="") {
        KR_CPSet("Started","1");
        if("@@MODE@@"=="story_floor") {
            // Fixture enters the map through native creation, including entrance dialogue.
            KR_ExploreSet("Pending",2);KR_ExploreSet("FloorResume",1);
            KR_ExploreSet("StoryActive",1);KR_Poke(71,-2026092203);
            KR_SPSetupStoryFloor(scene);
        }
        KR_CPSet("Started","1");KR_CPSet("Map","%d"%KR_ExploreMap(scene));KR_CPSet("Floor","%d"%KR_ExploreFloor(scene));
        L_Calendar::SetRemainTime(999);KR_SetRoute(true);KR_SetLoot(true);KR_SetTrap(true);
        AFL_Config_SetAutoModeWaitTimeRate(1.0);
        KR_SPBattleReady();
        KR_ClaudeProbeLog("RESUMED "+KR_SPState(scene));
        // Cancellation and load/new-trip reset must not resurrect an owned route.
        KR_ExploreSet("StoryActive",1);KR_ExploreSet("Pending",8);KR_Poke(71,0);
        KR_StoryGuard(scene);KR_SPAssert(!KR_WalkOwn() && KR_ExploreGet("StoryActive")==0,"cancel stays stopped");
        KR_StoryResetTrip();KR_SPAssert(KR_ExploreGet("Pending")==0 && KR_ExploreGet("FloorResume")==0,"trip reset");
        if("@@MODE@@"=="normal") KR_SPCheckResult(scene);
        if("@@MODE@@"=="rest") KR_StoryProbeSetupRest(scene);
        else KR_SPAssert(KR_ExploreStart(scene),"initial route");
        KR_CPSet("X","%d"%KR_WalkX());KR_CPSet("Y","%d"%KR_WalkY());
        if("@@MODE@@"=="story_floor") {
            KR_ClaudeProbeLog("FIXTURE native event-completion boundary 501 (no story flags changed)");
            KR_StoryTransition(501);return;
        }
    }
    int before=KR_ExploreGet("Pending");
    KR_WalkGuard(scene);
    if(before>=6 && before<=8) {
        KR_ClaudeProbeLog("RETURNED HANDLER "+("%d"%before)+" "+KR_SPState(scene));
        KR_SPAssert(KR_WalkOwn() && KR_WalkCount(scene)>0,"handler resume");
        if(before==8) {
            KR_SPAssert(KR_SPRecovered(),"rest complete");
            KR_ClaudeProbeLog("PASS native rest fully recovered and exploration replanned");
            KR_ClaudeShot("cal_rest_resumed.bmp");KR_ClaudeProbeLog("END");system.Exit(0);
        }
        KR_CPSet("StoryReturned","1");
    }
    if(KR_ExploreMap(scene)!=KR_CPNum("Map") || KR_ExploreFloor(scene)!=KR_CPNum("Floor")) {
        KR_CPSet("NewFloor","1");KR_ClaudeProbeLog("NEW FLOOR "+KR_SPState(scene));
        KR_SPAssert(KR_WalkOwn() && KR_WalkCount(scene)>0,"floor resume");
        KR_CPSet("FloorMoves","%d"%(KR_CPNum("FloorMoves")+1));
        if(KR_CPNum("FloorMoves")>=3) {KR_ClaudeShot("cal_floor_resumed.bmp");KR_ClaudeProbeLog("PASS continued on new floor");KR_ClaudeProbeLog("END");system.Exit(0);}
    }
    if(KR_WalkX()!=KR_CPNum("X") || KR_WalkY()!=KR_CPNum("Y")) {
        KR_CPSet("X","%d"%KR_WalkX());KR_CPSet("Y","%d"%KR_WalkY());KR_CPSet("Moves","%d"%(KR_CPNum("Moves")+1));
        KR_ClaudeProbeLog("STEP "+KR_SPState(scene));
        if("@@MODE@@"=="story_return" && KR_CPGet("StoryReturned")=="1") {
            KR_CPSet("ReturnedMoves","%d"%(KR_CPNum("ReturnedMoves")+1));
            if(KR_CPNum("ReturnedMoves")>=3) {KR_ClaudeShot("cal_story_resumed.bmp");KR_ClaudeProbeLog("PASS three moves after original story handler and trigger removal");KR_ClaudeProbeLog("END");system.Exit(0);}
        }
    }
    if(!KR_WalkOwn()) {KR_ClaudeProbeLog("STOPPED "+KR_SPState(scene));system.Exit(42);}
    KR_SPAssert(KR_CPNum("Moves")<800,"bounded travel");
}
void KR_SPMessage() {
    KR_CPSet("Messages","%d"%(KR_CPNum("Messages")+1));
    KR_ClaudeProbeLog("MESSAGE "+KR_CPGet("Messages"));
    KR_SPAssert(KR_WalkOwn(),"event owns exploration");
    KR_SPAssert(Ａ＿オートモード中確認(),"native dialogue auto mode");
    if(KR_CPNum("Messages")==1) {KR_ClaudeProbeLog("NATIVE STORY AUTO flag="+("%d"%KR_Flag(71)));KR_ClaudeShot("cal_story_auto.bmp");}
}
void KR_SPFrame() {
    if(KR_CPGet("PartyPrompt")=="1") {
        KR_CPSet("PartyFrames","%d"%(KR_CPNum("PartyFrames")+1));
        if(KR_CPNum("PartyFrames")>=40) {
            KR_CPSet("PartyPrompt","done");KR_ClaudeShot("cal_party_manual.bmp");
            KR_ClaudeProbeLog("PASS 13 automatic story lines; native party selection awaits player");KR_ClaudeProbeLog("END");system.Exit(0);return;
        }
    }
    if(KR_CPNum("Messages")<1) return;
    if(KR_Time()-KR_CPNum("LastWatch")<10000) return;
    KR_CPSet("LastWatch","%d"%KR_Time());
    KR_ClaudeProbeLog("WATCH messages="+KR_CPGet("Messages")+" auto="+("%d"%KR_CPB(Ａ＿オートモード中確認()))+" timer="+("%d"%AFL_GetAutoModeTimePos())+"/"+("%d"%AFL_GetAutoModeTimeLength()));
}
void KR_CalProbeTick() {
    if(KR_CPGet("DialogSeen")=="1") return;
    KR_CPSet("DialogSeen","1");
    KR_ClaudeProbeLog("NATIVE CHOICE preserved: "+KR_CPTitle());
    KR_ClaudeShot("cal_choice.bmp");
    KR_SPAssert(KR_CPNum("Messages")>0 && KR_WalkOwn(),"choice after owned story");
    KR_ClaudeProbeLog("PASS story auto dialogue; choice intentionally not answered");KR_ClaudeProbeLog("END");system.Exit(0);
}
int KR_CalProbeMsgWait(FTPARTS_WaitForClickCallback func,bool cancel) { return 0; }
int KR_CalProbeWait(FTPARTS_WaitForClickCallback func,bool cancel) {KR_ClaudeProbeLog("UNEXPECTED WAIT");system.Exit(43);return 0;}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();PassRegister.SetFileName(0,"NightRAFCGMode.asd");PassRegister.SetFileName(1,"NightRAFMemMode.asd");PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("SAVEFOLDER "+system.GetSaveFolderName());system.ResumeLoad("@@KEY@@","@@SAVE@@");system.Exit(2);return 2;
}
'''

def main():
    assert not p.processes(),'Player is still running'
    mode=sys.argv[1];save='NightR36.asd' if mode=='normal' else 'NightR45.asd'
    root=O/('native_'+mode);root.mkdir(exist_ok=True)
    if (root/'result.json').exists():
        import datetime
        prev=root/('previous_'+datetime.datetime.now().strftime('%H%M%S'));prev.mkdir();shutil.copy2(root/'result.json',prev/'result.json')
        if (root/'run/NightRemaster.ain').exists():shutil.copy2(root/'run/NightRemaster.ain',prev/'probe.ain')
    q.PROBE=root;q.RUN=root/'run';q.RUN.mkdir(exist_ok=True);work=root/'build';work.mkdir(exist_ok=True)
    q.BOOT='NightRemasterStoryProbe';q.safe_targets=lambda:{};q.target_jaf=lambda targets:''
    # The rest setup bridge below accesses the exact field ABI, not guessed JAF properties.
    jaf=JAF[:JAF.index('void KR_SPRest(')]+JAF[JAF.index('void KR_StoryProbeGuard('):]
    q.PROBE_JAF=jaf.replace('@@MODE@@',mode)
    l.WORK=root/'work';(l.WORK/'build').mkdir(parents=True,exist_ok=True)
    for n in ['candidate_meta.json','candidate_raw_code.jam']:shutil.copy2(O/n,l.WORK/'build'/n)
    before=p.snapshot_saves();key=l.save_records(l.SAVES/save)['key'];q.build_probe(O,key,save,False,work)
    pr=q.RUN/'NightRemaster.ain';l.cmd('ain','dump','-j','-o',work/'m.json',pr);m=l.read_meta(work/'m.json');fid=lambda name:l.fid_of(m,name)
    patch=f"FUNC {fid('KR_CalProbeMsgWait')}\n\tCALLFUNC KR_SPMessage\n\t.LOCALREF func\n\tA_REF\n\t.LOCALREF cancel\n\tCALLFUNC AFL_Parts_WaitForClick\n\tRETURN\nENDFUNC KR_CalProbeMsgWait\n"
    body=b.dump(m,fid('KR_RateViewUpdate'),pr).replace('\tCALLFUNC KR_RateTick\n','\tCALLFUNC KR_RateTick\n\tCALLFUNC KR_SPFrame\n')
    patch+='\n'+body
    patch+=f'\nFUNC {fid("KR_SPBattleReady")}\n\t.GLOBALREF Flags\n\tPUSH 26611\n\tPUSH 1\n\tCALLMETHOD 1\n\tPUSH 1\n\tCALLFUNC Conf_SetAutoBattleContinuous\n\tRETURN\nENDFUNC KR_SPBattleReady\n'
    patch+=f'\nFUNC {fid("KR_SPSetupStoryFloor")}\n\t.LOCALREF scene\n\tPUSH 28639\n\tPUSH 601\n\tPUSH 0\n\tCALLMETHOD 2\n\tRETURN\nENDFUNC KR_SPSetupStoryFloor\n'
    for name,body in [('KR_SPDamage','\t.LOCALREF pa\n\tPUSH 27364\n\t.LOCALREF pa\n\tPUSH 27338\n\tCALLMETHOD 0\n\tPUSH 20\n\tSUB\n\tCALLMETHOD 1\n\tPOP\n\t.LOCALDELETE pa\n\tRETURN\n'),('KR_SPRecoveryAt','\t.LOCALREF pa\n\tPUSH 27330\n\tCALLMETHOD 0\n\t.LOCALDELETE pa\n\tRETURN\n')]:
        patch+=f'\nFUNC {fid(name)}\n\tPUSHLOCALPAGE\n\tPUSH 1\n\t.LOCALREF index\n\tCALLFUNC L_Party::AbilityAt\n\tX_ASSIGN 1\n\tPOP\n\t.LOCALREF pa\n\tSP_INC\n'+body+f'ENDFUNC {name}\n'
    # Fixture only: a real event-dungeon rest tile one normal step away, damaged party.
    if mode=='rest':
        patch+=f"\nFUNC {fid('KR_StoryProbeSetupRest')}\n"
        patch+='\tPUSHLOCALPAGE\n\tPUSH 2\n\tX_DUP 2\n\tX_REF 1\n\tDELETE\n\tPUSH 0\n\tX_A_INIT 0\n\tPOP\n'
        patch+='\t.LOCALREF scene\n\tPUSH 28659\n\tCALLMETHOD 0\n\tPUSHLOCALPAGE\n\tPUSH 1\n\t.LOCALREF scene\n\tPUSH 6\n\tX_REF 1\n\tPUSH 27082\n\tPUSH 1\n\tPUSH 15\n\tCALLMETHOD 2\n\tX_ASSIGN 1\n\tPOP\n\t.LOCALREF cell\n\tSP_INC\n'
        for setter,value in [(27007,8),(27010,0),(27019,1),(27022,1),(27025,0)]:
            assert m['functions'][setter]['return-type'][0]==0
            patch+=f'\t.LOCALREF cell\n\tPUSH {setter}\n\tPUSH {value}\n\tCALLMETHOD 1\n'
        for index in range(3):patch+=f'\tPUSH {index}\n\tCALLFUNC KR_SPDamage\n'
        patch+='\t.LOCALREF route\n\tPUSH 1\n\tPUSH 15\n\tCALLFUNC KR_RouteAppendLinear\n\t.LOCALREF scene\n\t.LOCALREF route\n\tCALLFUNC KR_WalkCommit\n\tS_PUSH "rest queue"\n\tCALLFUNC KR_SPAssert\n\tPUSH 71\n\tPUSH 2026092203\n\tCALLFUNC KR_Poke\n\tS_PUSH "RouteMode"\n\tPUSH 1\n\tCALLFUNC KR_ExploreSet\n\t.LOCALREF scene\n\tPUSH 1\n\tCALLFUNC KR_WalkLabels\n\t.LOCALDELETE route\n\t.LOCALDELETE cell\n\tRETURN\n'
        patch+='ENDFUNC KR_StoryProbeSetupRest\n'
    (work/'bridges.jam').write_text(patch,'utf8');l.cmd('ain','edit','--jam',work/'bridges.jam','-o',work/'bridged.ain',pr)
    raw=bytearray(l.unpack((work/'bridged.ain').read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
    # Alice's generic JAF subtype marker is not the native CASPos array ABI.
    at=raw.index(b'KR_StoryProbeSetupRest\0');pos=raw.index(b'route\0\0',at)+7
    vals=struct.unpack_from('<7i',raw,pos);assert vals==(79,13,1,13,514,0,0),vals
    struct.pack_into('<7i',raw,pos,79,514,1,13,514,0,0)
    cm=l.read_meta(O/'candidate_meta.json');vs=l.versions(O/'candidate_raw_code.jam')
    def callsites(owner,name):
        target=f'CALLFUNC 0x{l.fid_of(cm,name):x}'
        return [ad for ad,op in l.live_version(cm,vs,l.fid_of(cm,owner))['ops'] if op==target]
    for ad in callsites('C_SceneDungeon@Run','AFL_Parts_WaitForClick'):struct.pack_into('<Hi',raw,16+ad,0x30,fid('AFL_Parts_WaitForClick'))
    hits=callsites('C_SceneDungeon@ExecMoveDungeon','KR_WalkGuard');assert len(hits)==1
    struct.pack_into('<Hi',raw,16+hits[0],0x30,fid('KR_StoryProbeGuard'))
    hits=callsites('C_EventDungeon0605@RunEventB1','L_SelectParty::Run07');assert len(hits)==1
    struct.pack_into('<Hi',raw,16+hits[0],0x30,fid('KR_SPPartyChoice'))
    pr.write_bytes(l.pack(raw,pr.read_bytes()[:8]));q.setup_folder(O,'SaveData_StoryProbe');sd=q.RUN/'SaveData_StoryProbe';sd.mkdir(exist_ok=True)
    for n in q.COPY_GLOBAL:
        if (l.SAVES/n).exists():shutil.copy2(l.SAVES/n,sd/n)
    shutil.copy2(l.SAVES/save,sd/save)
    l.writej(q.RUN/'probe_manifest.json',dict(source_sha256=l.sha(O/'NightRemaster.ain'),probe_sha256=l.sha(pr),audio=q.AUDIO_POLICY,save=save,mode=mode))
    result=q.launch(240);log=q.RUN/'claude_probe.txt';result['log']=l.decode(log.read_bytes()).splitlines() if log.exists() else []
    result.update(source_sha256=l.sha(O/'NightRemaster.ain'),probe_sha256=l.sha(pr),real_saves_unchanged=before==p.snapshot_saves(),save=save)
    for img in q.RUN.glob('cal_*.bmp'):Image.open(img).save(root/(img.stem+'.png'))
    l.writej(root/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='log'},ensure_ascii=False,indent=2));print('\n'.join(result['log'][-50:]))
if __name__=='__main__':main()
