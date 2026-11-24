"""Claude Opus 5.5 (2026-09-24) r13: native check of the home-panel pick (click a character -> that character's window).

Isolated, muted, own SaveFolder; resumes a COPY of a home base save (default NightR38) with the panel switched on.
The top menu's own wait stays live (C_SelectDialog@Run -> AFL_Parts_WaitForClick) and user input is patched off, so the
menu can only end through the click handler. Probe-only hooks:
  C_SelectDialog@_Update gets a prefix call KR_PickProbeTick (runs every frame of a dialog's wait):
    top   : logs the panel body's clickable / input / handler count, dispatches an L-click through the parts engine's own
            function set (CPartsFunctionSet@CallFunctionMouseClick) first on the CG row (must be ignored), then on 쿄카's
            row (must end the menu with the pick code);
    page  : the character window is open -> screenshot, then ends its wait with 0 (돌아가기);
    top2  : the top menu is back -> screenshot, END.
  Every other AFL_Parts_WaitForClick site exits with a log (no hang on an unexpected dialog).
The dispatch goes through the registered handlers exactly as the engine's click message does; the engine's own hit test
of a real mouse click on the text part is not part of this run.
"""
from pathlib import Path
import datetime,json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r13 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
from build_dungeon_sweep_20260916 import push,cf,lr,cm,assign,field
b=e.b;a=e.a;p=e.p;q=e.q
AREA='Game\\\\Scenes\\\\Common\\\\AddArea.pact'
HP_JAF=r'''
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
int KR_PB(bool v) { if(v) return 1; return 0; }
string KR_PGet(string key) { return SystemService.SystemVariable_Get("YoruKR.PickProbe."+key); }
void KR_PSet(string key,string value) { SystemService.SystemVariable_Set("YoruKR.PickProbe."+key,value); }
int KR_PNum(string key) { string v=KR_PGet(key); if(v=="") return 0; return v.ToInt(); }
// hand-written body: handler count of the part's L-click event; dispatch = CPartsFunctionSet@CallFunctionMouseClick(x, y, 1)
int KR_PickDispatch(int number,int x,int y,bool dispatch) { ref parts::detail::CPartsFunctionSet set; int count; return 0; }
int KR_PickBody() {
    if(!AFL_Activity_IsExistPartsByName("@@AREA@@","KR_HomeRateBody")) return -1;
    return AFL_Activity_GetPartsNumber("@@AREA@@","KR_HomeRateBody");
}
string KR_PickState() {
    return "menu="+SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu")+" pick="+SystemService.SystemVariable_Get("YoruKR.T8.HomePick");
}
void KR_PickProbeTick() {
    string stage=KR_PGet("Stage");
    int frames=KR_PNum("Frames")+1; KR_PSet("Frames","%d"%frames);
    if(frames>900) { KR_ClaudeProbeLog("STUCK in stage "+stage+" "+KR_PickState()); KR_ClaudeShot("pick_stuck.bmp"); system.Exit(5); return; }
    if(stage=="") {
        if(SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu")!="1") return;
        int body=KR_PickBody();
        KR_ClaudeProbeLog("TOP body="+("%d"%body)+" visible="+("%d"%KR_PB(Ｐ＿表示設定取得(body)))+" clickable="+("%d"%KR_PB(Ｐ＿クリック可能設定取得(body)))+" input="+("%d"%KR_PB(AFL_Parts_IsEnableInputProcess(body)))+" handlers="+("%d"%KR_PickDispatch(body,0,0,false))+" "+KR_PickState());
        KR_ClaudeShot("pick_top.bmp");
        KR_PickDispatch(body,40,100,true);
        KR_ClaudeProbeLog("after CG-row click "+KR_PickState());
        KR_PSet("Stage","page"); KR_PSet("Frames","0");
        KR_PickDispatch(body,40,256,true);
        KR_ClaudeProbeLog("after 쿄카-row click "+KR_PickState());
        return;
    }
    if(stage=="page") {
        if(SystemService.SystemVariable_Get("YoruKR.T8.Title")=="") return;
        string t=SystemService.SystemVariable_Get("YoruKR.T8.Title");
        int nl=t.Find("\n"); if(nl>0) t=KR_JosaSlice(t,0,nl);
        KR_ClaudeProbeLog("PAGE title="+t+" "+KR_PickState()+" clickable="+("%d"%KR_PB(Ｐ＿クリック可能設定取得(KR_PickBody()))));
        KR_ClaudeShot("pick_page.bmp");
        KR_PSet("Stage","top2"); KR_PSet("Frames","0");
        AFL_Parts_EndWaitForClick(0);
        return;
    }
    if(stage=="top2") {
        if(SystemService.SystemVariable_Get("YoruKR.T8.HomeMenu")!="1") return;
        KR_ClaudeProbeLog("BACK TO TOP "+KR_PickState()+" clickable="+("%d"%KR_PB(Ｐ＿クリック可能設定取得(KR_PickBody())))+" handlers="+("%d"%KR_PickDispatch(KR_PickBody(),0,0,false)));
        KR_ClaudeShot("pick_top2.bmp");
        KR_ClaudeProbeLog("END"); system.Exit(0);
    }
}
int KR_PickProbeWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    KR_ClaudeProbeLog("UNEXPECTED WAIT stage="+KR_PGet("Stage")+" "+KR_PickState());
    KR_ClaudeShot("pick_wait.bmp");
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
def build_probe(source,m,key,save):
    src=source/'NightRemaster.ain'
    jaf=audio.JAF+'\n'+HP_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save).replace('@@AREA@@',AREA)
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(b.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('가'<=ch<='힣' or ch in '·…「」【】　' for ch in json.loads(z[0])) else z[0],jaf)
    (c.ROOT/'probe.jaf').write_text(jaf,'utf8');decl=c.ROOT/'probe_declared.ain';b.cmd('ain','edit','--jaf',c.ROOT/'probe.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',c.ROOT/'probe_declared_meta.json',decl);dm=b.read_meta(c.ROOT/'probe_declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    def bind(fn,name,expr):
        f=dm['functions'][ids[fn]];return assign(next(i for i,v in enumerate(f['arguments']+f['variables']) if v['name']==name),expr)
    s=lr('number')+'\tCALLHLL PartsEngine GetDelegateIndex 0\n'+push(-1)+'\tEQUALE\n\tIFNZ empty_handlers\n'
    s+=bind('KR_PickDispatch','set',cm('\t.GLOBALREF parts::detail::g_PartsMessageManager\n',8734,lr('number'),1))
    s+=field(lr('set'),13)+push(0)+'\tNOTE\n\tIFNZ empty_handlers\n'
    s+=bind('KR_PickDispatch','count',field(lr('set'),12)+'\tCALLHLL Delegate Numof 0\n')
    s+=lr('dispatch')+'\tIFZ no_dispatch\n'+cm(lr('set'),8697,lr('x')+lr('y')+push(1),3)
    s+='no_dispatch:\n\t.LOCALDELETE set\n'+lr('count')+'\tRETURN\nempty_handlers:\n\t.LOCALDELETE set\n'+push(0)+'\tRETURN\n'
    bridges={'KR_PickDispatch':s}
    for f in added:
        if f['name'] in bridges:patch.append(f"FUNC {f['index']}\n"+bridges[f['name']]+f"ENDFUNC {f['name']}\n");continue
        path=c.ROOT/f"probe_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl);patch.append(b.clean(b.native_lower(path.read_text('utf8')).replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),f['name']))
    # C_SelectDialog@_Update (the per-frame callback of every selection dialog's wait) gets the probe tick first
    upd=next(f['index'] for f in m['functions'] if b.raw_symbol(m,f['index'])=='C_SelectDialog@_Update')
    path=c.ROOT/f'original_{upd}.jam';b.cmd('ain','dump','--function','C_SelectDialog@_Update','-o',path,src)
    patch.append(e.begin(b.clean(path.read_text('utf8'),'C_SelectDialog@_Update'),'\tCALLFUNC KR_PickProbeTick\n'))
    (c.ROOT/'probe.jam').write_text('\n'.join(patch),'utf8');out=c.ROOT/'NightRemaster.ain';b.cmd('ain','edit','--jam',c.ROOT/'probe.jam','-o',out,decl)
    rawa=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',rawa,12)[0];struct.pack_into('<I',rawa,24+size,m['functions'][0]['address'])
    struct.pack_into('<I',rawa,rawa.index(b'MAIN')+4,ids['KR_ClaudeProbeMain'])
    wait=next(f['index'] for f in m['functions'] if f['name']=='AFL_Parts_WaitForClick');waits=[]
    versions=q.versions(source/'native_raw_code.jam')
    for f in m['functions']:
        name=b.raw_symbol(m,f['index'])
        for v in [v for v in versions.get(f['index'],[]) if v['start']==f['address']]:
            for ad,op in v['ops']:
                if op!=f'CALLFUNC 0x{wait:x}':continue
                assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait)
                if name=='C_SelectDialog@Run':waits.append((name,'live'));continue
                struct.pack_into('<Hi',rawa,16+ad,0x30,ids['KR_PickProbeWait']);waits.append((name,'exit'))
    assert sum(1 for _,k in waits if k=='live')==1,waits
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]));return dict(update=upd,waits=waits)

def main(save='NightR38.asd'):
    source=e.O;stamp=datetime.datetime.now().strftime('%H%M%S')
    c.O=source;c.ROOT=e.O/'homepick_probe';c.BOOT='NightRemasterClaudePick';c.SAVEDIR=f'SaveData_KR_ClaudePickProbe_20260924_{stamp}';c.SAVES=p.SAVE.parent/c.SAVEDIR
    assert not c.SAVES.exists();c.ROOT.mkdir(parents=True,exist_ok=True)
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    m=b.read_meta(source/'candidate_meta.json');info=build_probe(source,m,key,save)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(source/'NightRemaster.ain'),source_sha256=e.h(source/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),
        audio=audio.POLICY,input=f'Resume of a copied {save} (panel on); user input patched off; clicks dispatched through CPartsFunctionSet@CallFunctionMouseClick in C_SelectDialog@_Update.',
        save_folder=c.SAVEDIR,author=e.AUTHOR),indent=2,ensure_ascii=False),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    for x in ['NightRemasterEX.ex']:shutil.copy2(source/x,c.ROOT/x);shutil.copy2(source/x,c.ROOT/x.replace('NightRemaster',c.BOOT,1))
    shutil.copy2(p.SAVE/save,c.SAVES/save)
    (c.SAVES/'YoruKR_HomeRate.dat').write_bytes(b'YoruKR.HomeRate.1\r\n1\r\n')
    log=c.ROOT/'claude_probe.txt'
    if log.exists():log.rename(c.ROOT/f'claude_probe_{stamp}_prev.txt')
    result=c.launch(timeout=300);result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else [];result.update(save=save,save_folder=c.SAVEDIR,waits=info['waits'])
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image
    for pth in c.ROOT.glob('pick_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    (c.ROOT/'homepick_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print({x:y for x,y in result.items() if x not in ('events','log','waits')},len(result['events']));print('\n'.join(result['log']))
if __name__=='__main__':main(*sys.argv[1:])
