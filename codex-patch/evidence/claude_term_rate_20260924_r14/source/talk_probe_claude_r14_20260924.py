"""Claude Opus 5.5 (2026-09-24) r14 run of an earlier probe. r13 run of the r12 probe. r12: native check that auto exploration keeps going through a dungeon talk.

Isolated, muted, own SaveFolder; resumes a COPY of a dungeon save made at the dungeon's save button (default NightR36).
Probe-only hooks (same-length call swaps in the probe AIN; the r12 code under test is called unchanged):
  ExecMoveDungeon's KR_WalkGuard call -> KR_TalkProbeGuard: first call sets m_nFloorWalkCount = 300 and m_bFloorMessage =
      false (so CheckTalk's own conditions hold at the next step), starts the exploration through KR_ExploreStart, then logs
      every step; after the talk it counts moves while the walk stays owned and exits after 3 (or logs STOPPED).
  CheckTalk's KR_T8TalkBegin / KR_T8TalkEnd calls -> spies that log flag 71 and the message auto mode around the real calls.
  The message key wait (CMessageTextView ExecuteKeyWait lambda) stays live: user input is patched off, so the talk can only
      advance through the auto mode; the spy screenshots the first message waits of the talk.
  Every other AFL_Parts_WaitForClick site except the dungeon's own loop exits with a log (no hang on dialogs/battles).
"""
from pathlib import Path
import datetime,json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r14 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
b=e.b;a=e.a;p=e.p;q=e.q
MOVES_AFTER=3
TP_JAF=r'''
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
string KR_TPGet(string key) { return SystemService.SystemVariable_Get("YoruKR.TalkProbe."+key); }
void KR_TPSet(string key,string value) { SystemService.SystemVariable_Set("YoruKR.TalkProbe."+key,value); }
int KR_TPNum(string key) { string v=KR_TPGet(key); if(v=="") return 0; return v.ToInt(); }
int KR_TPB(bool v) { if(v) return 1; return 0; }
// jaf cannot dereference ref C_SceneDungeon members: these three get hand-written bodies (members 9 m_nFloorWalkCount, 10 m_bFloorMessage)
int KR_TPWalkCount(ref C_SceneDungeon scene) { return 0; }
int KR_TPFloorMsg(ref C_SceneDungeon scene) { return 0; }
void KR_TPArm(ref C_SceneDungeon scene) { }
int KR_TPAuto() { if(Ａ＿オートモード中確認()) return 1; return 0; }
string KR_TPState(ref C_SceneDungeon scene) {
    return "at "+("%d"%KR_WalkX())+","+("%d"%KR_WalkY())+" flag="+("%d"%KR_Flag(71))+" queue="+("%d"%KR_WalkCount(scene))+" pending="+("%d"%KR_ExploreGet("Pending"))+" walk="+("%d"%KR_TPWalkCount(scene));
}
void KR_TalkProbeGuard(ref C_SceneDungeon scene) {
    string stage=KR_TPGet("Stage");
    if(stage=="") {
        KR_TPSet("Stage","walk");
        KR_ClaudeProbeLog("RESUMED "+KR_TPState(scene)+" floorMessage="+("%d"%KR_TPFloorMsg(scene))+" auto="+("%d"%KR_TPAuto()));
        KR_ClaudeShot("talk_probe_0.bmp");
        KR_TPArm(scene);
        KR_ClaudeProbeLog("ARMED walk="+("%d"%KR_TPWalkCount(scene))+" floorMessage="+("%d"%KR_TPFloorMsg(scene)));
        KR_ExploreSet("AutoFloor",1);
        bool ok=KR_ExploreStart(scene);
        KR_ClaudeProbeLog("START ok="+("%d"%KR_TPB(ok))+" "+KR_TPState(scene));
        KR_TPSet("X","%d"%KR_WalkX()); KR_TPSet("Y","%d"%KR_WalkY());
        if(!ok) { system.Exit(4); return; }
    }
    KR_WalkGuard(scene);
    stage=KR_TPGet("Stage");
    if(KR_WalkX()!=KR_TPNum("X") || KR_WalkY()!=KR_TPNum("Y")) {
        KR_TPSet("X","%d"%KR_WalkX()); KR_TPSet("Y","%d"%KR_WalkY());
        int moves=KR_TPNum("Moves")+1; KR_TPSet("Moves","%d"%moves);
        KR_ClaudeProbeLog("STEP "+stage+" "+("%d"%moves)+" "+KR_TPState(scene));
        if(stage=="walk" && moves>=12) { KR_ClaudeProbeLog("NO TALK"); KR_ClaudeShot("talk_probe_9.bmp"); system.Exit(5); return; }
        if(stage=="after" && moves>=@@MOVES_AFTER@@) {
            KR_ClaudeProbeLog("CONTINUED "+("%d"%moves)+" moves after the talk "+KR_TPState(scene));
            KR_ClaudeShot("talk_probe_after.bmp");
            KR_ClaudeProbeLog("END"); system.Exit(0); return;
        }
    }
    if(stage=="after" && !KR_WalkOwn()) {
        KR_ClaudeProbeLog("STOPPED after the talk "+KR_TPState(scene));
        KR_ClaudeShot("talk_probe_stopped.bmp");
        KR_ClaudeProbeLog("END"); system.Exit(0); return;
    }
}
void KR_TalkProbeBegin(ref C_SceneDungeon scene) {
    KR_ClaudeProbeLog("TALK BEGIN "+KR_TPState(scene)+" auto="+("%d"%KR_TPAuto()));
    KR_T8TalkBegin(scene);
    KR_ClaudeProbeLog("after begin flag="+("%d"%KR_Flag(71))+" queue="+("%d"%KR_WalkCount(scene))+" auto="+("%d"%KR_TPAuto())+" TalkFlag="+SystemService.SystemVariable_Get("YoruKR.T8.TalkFlag")+" TalkAuto="+SystemService.SystemVariable_Get("YoruKR.T8.TalkAuto"));
    KR_TPSet("Stage","talk"); KR_TPSet("Waits","0");
}
void KR_TalkProbeEnd(int effect,int time) {
    KR_ClaudeProbeLog("TALK END waits="+KR_TPGet("Waits")+" flag="+("%d"%KR_Flag(71))+" auto="+("%d"%KR_TPAuto()));
    KR_T8TalkEnd(effect,time);
    KR_ClaudeProbeLog("after end flag="+("%d"%KR_Flag(71))+" auto="+("%d"%KR_TPAuto())+" own="+("%d"%KR_TPB(KR_WalkOwn())));
    KR_TPSet("Stage","after"); KR_TPSet("Moves","0");
    KR_ClaudeShot("talk_probe_end.bmp");
}
void KR_TalkProbeMsgNote() {
    if(KR_TPGet("Stage")=="talk") {
        int n=KR_TPNum("Waits")+1; KR_TPSet("Waits","%d"%n);
        if(n<=3) { KR_ClaudeProbeLog("MSG WAIT "+("%d"%n)+" auto="+("%d"%KR_TPAuto())); KR_ClaudeShot("talk_probe_msg_"+("%d"%n)+".bmp"); }
    }
}
// jaf cannot pass a functype argument on: hand-written body = KR_TalkProbeMsgNote(); return AFL_Parts_WaitForClick(func, cancel)
int KR_TalkProbeMsgWait(FTPARTS_WaitForClickCallback func,bool cancel) { return 0; }
int KR_TalkProbeWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    KR_ClaudeProbeLog("UNEXPECTED WAIT stage="+KR_TPGet("Stage")+" auto="+("%d"%KR_TPAuto()));
    KR_ClaudeShot("talk_probe_wait.bmp");
    system.Exit(6);
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
    jaf=audio.JAF+'\n'+TP_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save).replace('@@MOVES_AFTER@@',str(MOVES_AFTER))
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(b.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('가'<=ch<='힣' or ch in '·…「」【】　' for ch in json.loads(z[0])) else z[0],jaf)
    (c.ROOT/'probe.jaf').write_text(jaf,'utf8');decl=c.ROOT/'probe_declared.ain';b.cmd('ain','edit','--jaf',c.ROOT/'probe.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',c.ROOT/'probe_declared_meta.json',decl);dm=b.read_meta(c.ROOT/'probe_declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    bridges={'KR_TPWalkCount':'\t.LOCALREF scene\n\tPUSH 9\n\tX_REF 1\n\tRETURN\n',
             'KR_TPFloorMsg':'\t.LOCALREF scene\n\tPUSH 10\n\tX_REF 1\n\tRETURN\n',
             'KR_TalkProbeMsgWait':'\tCALLFUNC KR_TalkProbeMsgNote\n\t.LOCALREF func\n\t.LOCALREF cancel\n\tCALLFUNC AFL_Parts_WaitForClick\n\tRETURN\n',
             'KR_TPArm':'\t.LOCALREF scene\n\tPUSH 9\n\tPUSH 300\n\tX_ASSIGN 1\n\tPOP\n\t.LOCALREF scene\n\tPUSH 10\n\tPUSH 0\n\tX_ASSIGN 1\n\tPOP\n\tRETURN\n'}
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
    hooks=dict(guard=swap(fid('C_SceneDungeon@ExecMoveDungeon'),fid('KR_WalkGuard'),ids['KR_TalkProbeGuard']),
               begin=swap(fid('C_SceneDungeon@CheckTalk'),fid('KR_T8TalkBegin'),ids['KR_TalkProbeBegin']),
               end=swap(fid('C_SceneDungeon@CheckTalk'),fid('KR_T8TalkEnd'),ids['KR_TalkProbeEnd']))
    wait=fid('AFL_Parts_WaitForClick');waits=[]
    for f in m['functions']:
        name=b.raw_symbol(m,f['index'])
        for v in [v for v in versions.get(f['index'],[]) if v['start']==f['address']]:
            for ad,op in v['ops']:
                if op!=f'CALLFUNC 0x{wait:x}':continue
                assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait)
                if name=='C_SceneDungeon@Run':waits.append((name,'live'));continue
                target=ids['KR_TalkProbeMsgWait'] if name.startswith(MSG_LAMBDA) else ids['KR_TalkProbeWait']
                struct.pack_into('<Hi',rawa,16+ad,0x30,target);waits.append((name,'msg' if target==ids['KR_TalkProbeMsgWait'] else 'exit'))
    assert sum(1 for _,k in waits if k=='msg')==1 and sum(1 for _,k in waits if k=='live')==1,waits
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]));return dict(hooks=hooks,waits=waits)

def main(save='NightR36.asd'):
    source=e.O;stamp=datetime.datetime.now().strftime('%H%M%S')
    c.O=source;c.ROOT=e.O/'talk_probe';c.BOOT='NightRemasterClaudeTalk';c.SAVEDIR=f'SaveData_KR_ClaudeTalkProbe_20260924_{stamp}';c.SAVES=p.SAVE.parent/c.SAVEDIR
    assert not c.SAVES.exists();c.ROOT.mkdir(parents=True,exist_ok=True)
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    m=b.read_meta(source/'candidate_meta.json');info=build_probe(source,m,key,save)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(source/'NightRemaster.ain'),source_sha256=e.h(source/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),
        audio=audio.POLICY,input=f'Resume of a copied {save}; user input patched off; walk count 300 and floor-talk flag cleared, exploration started by KR_ExploreStart; message key wait live (auto mode only).',
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
    for pth in c.ROOT.glob('talk_probe_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    (c.ROOT/'talk_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print({x:y for x,y in result.items() if x not in ('events','log','waits')},len(result['events']));print('\n'.join(result['log']))
if __name__=='__main__':main(*sys.argv[1:])
