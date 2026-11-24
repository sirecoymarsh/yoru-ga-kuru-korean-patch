"""Claude Opus 5.5 (2026-09-24) r14: native check that auto exploration takes the stairs without the next-floor question
and keeps exploring on the new floor.

Isolated, muted, own SaveFolder; resumes a COPY of a dungeon save made at the dungeon's save button (default NightR36).
Probe-only setup on the copy: remaining time 999 (the save has 25 left), instant kill and instant trap release on (the
mod's own options), so the walk is not ended by the clock, a battle or a trap before it reaches stairs.
Probe-only hooks (same-length call swaps in the probe AIN; the r14 code under test is called unchanged):
  ExecMoveDungeon's KR_WalkGuard call -> KR_FloorProbeGuard: starts the exploration once (KR_ExploreStart), then calls
      KR_WalkGuard and logs every step with map / floor / ownership; after the floor changes it counts moves on the new
      floor and exits after 3 (CONTINUED) or when the walk has been lost for 30 guard calls (STOPPED); 800 steps without a
      floor change exit as NO FLOOR CHANGE.
  StepedOnCell's KR_T8FloorDialog call -> spy logging ownership / Pending / AutoFloor around the real call.
  Every AFL_Parts_WaitForClick except the dungeon loop's own exits with a log and a screenshot (the next-floor question
  must not show: user input is patched off); the message key wait stays live for talks (auto mode, r12) and exits for any
  other message.
"""
from pathlib import Path
import datetime,json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r14 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
b=e.b;a=e.a;p=e.p;q=e.q
FP_JAF=r'''
void KR_ClaudeProbeLog(string text) {
    string all=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Log")+text+"\n";
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Log",all);
    TextFile.WriteAll("claude_probe.txt",all);
}
int KR_ClaudeShot(string file) {
    AFL_View_Update();AFL_View_Update();AFL_View_Update();
    if(!SystemService.SaveScreenshot(file,0,0,1280,720)) system.Exit(9);
    KR_ClaudeProbeLog("SHOT "+file);
    return 0;
}
string KR_FPGet(string key) { return SystemService.SystemVariable_Get("YoruKR.FloorProbe."+key); }
void KR_FPSet(string key,string value) { SystemService.SystemVariable_Set("YoruKR.FloorProbe."+key,value); }
int KR_FPNum(string key) { string v=KR_FPGet(key); if(v=="") return 0; return v.ToInt(); }
int KR_FPB(bool v) { if(v) return 1; return 0; }
string KR_FPState(ref C_SceneDungeon scene) {
    return "at "+("%d"%KR_WalkX())+","+("%d"%KR_WalkY())+" map="+("%d"%KR_ExploreMap(scene))+" floor="+("%d"%KR_ExploreFloor(scene))+" flag="+("%d"%KR_Flag(71))+" queue="+("%d"%KR_WalkCount(scene))+" pending="+("%d"%KR_ExploreGet("Pending"))+" time="+("%d"%L_Calendar::GetRemainTime());
}
void KR_FloorProbeGuard(ref C_SceneDungeon scene) {
    string stage=KR_FPGet("Stage");
    if(stage=="") {
        KR_FPSet("Stage","walk");
        L_Calendar::SetRemainTime(999);
        KR_SetLoot(true); KR_SetTrap(true);
        KR_ClaudeProbeLog("RESUMED "+KR_FPState(scene)+" loot="+("%d"%KR_FPB(KR_GetLoot()))+" trap="+("%d"%KR_FPB(KR_GetTrap())));
        KR_FPSet("Map","%d"%KR_ExploreMap(scene)); KR_FPSet("Floor","%d"%KR_ExploreFloor(scene));
        KR_ClaudeShot("floor_probe_0.bmp");
        bool ok=KR_ExploreStart(scene);
        KR_ClaudeProbeLog("START ok="+("%d"%KR_FPB(ok))+" "+KR_FPState(scene));
        KR_FPSet("X","%d"%KR_WalkX()); KR_FPSet("Y","%d"%KR_WalkY());
        if(!ok) { KR_ClaudeProbeLog("END"); system.Exit(4); return; }
    }
    KR_WalkGuard(scene);
    stage=KR_FPGet("Stage");
    if(stage=="walk" && (KR_ExploreFloor(scene)!=KR_FPNum("Floor") || KR_ExploreMap(scene)!=KR_FPNum("Map"))) {
        KR_FPSet("Stage","newfloor"); stage="newfloor"; KR_FPSet("Moves","0");
        KR_FPSet("X","%d"%KR_WalkX()); KR_FPSet("Y","%d"%KR_WalkY());
        KR_ClaudeProbeLog("NEW FLOOR "+KR_FPState(scene)+" own="+("%d"%KR_FPB(KR_WalkOwn())));
        KR_ClaudeShot("floor_probe_new.bmp");
    }
    if(KR_WalkX()!=KR_FPNum("X") || KR_WalkY()!=KR_FPNum("Y")) {
        KR_FPSet("X","%d"%KR_WalkX()); KR_FPSet("Y","%d"%KR_WalkY());
        int moves=KR_FPNum("Moves")+1; KR_FPSet("Moves","%d"%moves);
        int total=KR_FPNum("Total")+1; KR_FPSet("Total","%d"%total);
        KR_ClaudeProbeLog("STEP "+stage+" "+("%d"%moves)+" "+KR_FPState(scene));
        if(stage=="walk" && total>=800) { KR_ClaudeProbeLog("NO FLOOR CHANGE"); KR_ClaudeShot("floor_probe_9.bmp"); KR_ClaudeProbeLog("END"); system.Exit(5); return; }
        if(stage=="newfloor" && moves>=3 && KR_WalkOwn()) {
            KR_ClaudeProbeLog("CONTINUED ON NEW FLOOR "+KR_FPState(scene));
            KR_ClaudeShot("floor_probe_after.bmp");
            KR_ClaudeProbeLog("END"); system.Exit(0); return;
        }
    }
    if(!KR_WalkOwn()) {
        int lost=KR_FPNum("Lost")+1; KR_FPSet("Lost","%d"%lost);
        if(lost>=30) { KR_ClaudeProbeLog("STOPPED in "+stage+" "+KR_FPState(scene)); KR_ClaudeShot("floor_probe_stopped.bmp"); KR_ClaudeProbeLog("END"); system.Exit(0); return; }
    } else KR_FPSet("Lost","0");
}
int KR_FloorProbeDialog(bool show,int wait) {
    KR_ClaudeProbeLog("FLOOR DIALOG own="+("%d"%KR_FPB(KR_WalkOwn()))+" flag="+("%d"%KR_Flag(71))+" pending="+("%d"%KR_ExploreGet("Pending"))+" autofloor="+SystemService.SystemVariable_Get("YoruKR.Explore.AutoFloor"));
    int r=KR_T8FloorDialog(show,wait);
    KR_ClaudeProbeLog("FLOOR DIALOG -> "+("%d"%r)+" resume="+SystemService.SystemVariable_Get("YoruKR.Explore.FloorResume")+" autofloor="+SystemService.SystemVariable_Get("YoruKR.Explore.AutoFloor"));
    return r;
}
void KR_FloorProbeMsgNote() {
    if(SystemService.SystemVariable_Get("YoruKR.T8.TalkFlag")!="") return;
    KR_ClaudeProbeLog("UNEXPECTED MESSAGE stage="+KR_FPGet("Stage"));
    KR_ClaudeShot("floor_probe_msg.bmp");
    KR_ClaudeProbeLog("END"); system.Exit(6);
}
// hand-written body: KR_FloorProbeMsgNote(); return AFL_Parts_WaitForClick(func, cancel)
int KR_FloorProbeMsgWait(FTPARTS_WaitForClickCallback func,bool cancel) { return 0; }
int KR_FloorProbeWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    KR_ClaudeProbeLog("UNEXPECTED WAIT stage="+KR_FPGet("Stage"));
    KR_ClaudeShot("floor_probe_wait.bmp");
    KR_ClaudeProbeLog("END"); system.Exit(6);
    return 0;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0,"NightRAFCGMode.asd");
    PassRegister.SetFileName(1,"NightRAFMemMode.asd");
    PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("resume loading @@SAVE@@");
    system.ResumeLoad("@@KEY@@","@@SAVE@@");
    system.Exit(2);return 2;
}
'''
MSG_LAMBDA='message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
def build_probe(source,m,key,save):
    src=source/'NightRemaster.ain'
    jaf=audio.JAF+'\n'+FP_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save)
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(b.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('가'<=ch<='힣' or ch in '·…「」【】　' for ch in json.loads(z[0])) else z[0],jaf)
    (c.ROOT/'probe.jaf').write_text(jaf,'utf8');decl=c.ROOT/'probe_declared.ain';b.cmd('ain','edit','--jaf',c.ROOT/'probe.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',c.ROOT/'probe_declared_meta.json',decl);dm=b.read_meta(c.ROOT/'probe_declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    bridges={'KR_FloorProbeMsgWait':'\tCALLFUNC KR_FloorProbeMsgNote\n\t.LOCALREF func\n\t.LOCALREF cancel\n\tCALLFUNC AFL_Parts_WaitForClick\n\tRETURN\n'}
    for f in added:
        if f['name'] in bridges:patch.append(b.native_lower(f"FUNC {f['index']}\n"+bridges[f['name']]+f"ENDFUNC {f['name']}\n"));continue
        path=c.ROOT/f"probe_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl);patch.append(b.clean(b.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),f['name']))
    (c.ROOT/'probe.jam').write_text('\n'.join(patch),'utf8');out=c.ROOT/'NightRemaster.ain';b.cmd('ain','edit','--jam',c.ROOT/'probe.jam','-o',out,decl)
    rawa=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',rawa,12)[0];struct.pack_into('<I',rawa,24+size,m['functions'][0]['address'])
    struct.pack_into('<I',rawa,rawa.index(b'MAIN')+4,ids['KR_ClaudeProbeMain'])
    fid=lambda n:next(f['index'] for f in m['functions'] if b.raw_symbol(m,f['index'])==n)
    versions=q.versions(source/'native_raw_code.jam')
    def live(i):return next(v for v in versions[i] if v['start']==m['functions'][i]['address'])
    def swap(where,old,new):
        sites=[ad for ad,op in live(where)['ops'] if op==f'CALLFUNC 0x{old:x}'];assert len(sites)==1,(where,old,sites)
        assert rawa[16+sites[0]:16+sites[0]+6]==struct.pack('<Hi',0x30,old);struct.pack_into('<Hi',rawa,16+sites[0],0x30,new);return sites[0]
    hooks=dict(guard=swap(fid('C_SceneDungeon@ExecMoveDungeon'),fid('KR_WalkGuard'),ids['KR_FloorProbeGuard']),
               floor=swap(fid('C_SceneDungeon@StepedOnCell'),fid('KR_T8FloorDialog'),ids['KR_FloorProbeDialog']))
    wait=fid('AFL_Parts_WaitForClick');waits=[]
    for f in m['functions']:
        name=b.raw_symbol(m,f['index'])
        for v in [v for v in versions.get(f['index'],[]) if v['start']==f['address']]:
            for ad,op in v['ops']:
                if op!=f'CALLFUNC 0x{wait:x}':continue
                assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait)
                if name=='C_SceneDungeon@Run':waits.append((name,'live'));continue
                target=ids['KR_FloorProbeMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_FloorProbeWait']
                struct.pack_into('<Hi',rawa,16+ad,0x30,target);waits.append((name,'msg' if target==ids['KR_FloorProbeMsgWait'] else 'exit'))
    assert sum(1 for _,k in waits if k=='msg')==1 and sum(1 for _,k in waits if k=='live')==1,waits
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]));return dict(hooks=hooks,waits=waits)

def main(save='NightR36.asd'):
    source=e.O;stamp=datetime.datetime.now().strftime('%H%M%S')
    c.O=source;c.ROOT=e.O/'floor_probe';c.BOOT='NightRemasterClaudeFloor';c.SAVEDIR=f'SaveData_KR_ClaudeFloorProbe_20260924_{stamp}';c.SAVES=p.SAVE.parent/c.SAVEDIR
    assert not c.SAVES.exists();c.ROOT.mkdir(parents=True,exist_ok=True)
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    m=b.read_meta(source/'candidate_meta.json');info=build_probe(source,m,key,save)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(source/'NightRemaster.ain'),source_sha256=e.h(source/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),
        audio=audio.POLICY,input=f'Resume of a copied {save}; user input patched off; remaining time 999, instant kill and trap release on (probe copy only); exploration started by KR_ExploreStart.',
        hooks=info['hooks'],save_folder=c.SAVEDIR,author=e.AUTHOR),indent=2,ensure_ascii=False),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    for x in ['NightRemasterEX.ex']:shutil.copy2(source/x,c.ROOT/x);shutil.copy2(source/x,c.ROOT/x.replace('NightRemaster',c.BOOT,1))
    shutil.copy2(p.SAVE/save,c.SAVES/save)
    log=c.ROOT/'claude_probe.txt'
    if log.exists():log.rename(c.ROOT/f'claude_probe_{stamp}_prev.txt')
    result=c.launch(timeout=900);result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else [];result.update(save=save,save_folder=c.SAVEDIR,hooks=info['hooks'],waits=info['waits'])
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image
    for pth in c.ROOT.glob('floor_probe_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    (c.ROOT/'floor_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    lines=result['log'];keep=[l for l in lines if not l.startswith('STEP walk')]
    print({x:y for x,y in result.items() if x not in ('events','log','waits')},len(result['events']),'steps',sum(1 for l in lines if l.startswith('STEP')));print('\n'.join(keep[-40:]))
if __name__=='__main__':main(*sys.argv[1:])
