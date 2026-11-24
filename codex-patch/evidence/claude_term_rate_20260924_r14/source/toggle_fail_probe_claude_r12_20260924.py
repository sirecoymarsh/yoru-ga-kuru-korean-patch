"""Claude Opus 5.5 (2026-09-24) r9: the r8 probe run unchanged against the r12 candidate. Claude Opus 5.5 (2026-09-24) r8: unchanged r7 probe run against the r12 candidate. Claude Opus 5.5 (2026-09-24) r7 CT-RATE-003 native check (Codex method): a directory with the preference file name in a
dedicated probe SaveFolder makes the write fail; the toggle must stay off and not retry every update. Based on the home probe:
isolated, muted screenshots of the homebase achievement panel and the mods page.

Same technique as home_probe_claude_20260924.py: MAIN resumes a COPY of a user save in the probe's own
SaveFolder, every AFL_Parts_WaitForClick call is swapped for the screenshot function. The probe save folder
gets YoruKR_HomeRate.dat = on, so shot 0 is what C_SceneHomebaseView@BeginTop (KR_T8HomeEnter) left on screen.
Shots: 0 natural (on) / 1 toggle off + BeginTop hook / 2 on again / 3 EndTop hook / 4 Asra\\Mods.pact loaded on top.
"""
from pathlib import Path
import json,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r12 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
b=e.b;a=e.a;p=e.p;q=e.q
HOME_JAF=r'''
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
int KR_ClaudeHomeWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    if(SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Stage")!="") {
        KR_ClaudeShot("home_probe_9.bmp");
        system.Exit(3);
        return 0;
    }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","1");
    if(KR_T8HomeRateGet()) KR_ClaudeProbeLog("before=1"); else KR_ClaudeProbeLog("before=0");
    KR_T8HomeRateSet(true);
    if(KR_T8HomeRateGet()) KR_ClaudeProbeLog("after failed write=1"); else KR_ClaudeProbeLog("after failed write=0");
    KR_ClaudeProbeLog("latch="+SystemService.SystemVariable_Get("YoruKR.HomeRate.Failed"));
    KR_T8HomeRateSet(true);KR_T8HomeRateSet(true);
    SystemService.SystemVariable_Set("YoruKR.HomeRate","");
    if(KR_T8HomeRateGet()) KR_ClaudeProbeLog("after cache reset=1"); else KR_ClaudeProbeLog("after cache reset=0");
    system.Exit(0);
    if(KR_T8HomeRateGet()) KR_ClaudeProbeLog("toggle=1"); else KR_ClaudeProbeLog("toggle=0");
    KR_ClaudeShot("home_probe_0.bmp");
    KR_ClaudeProbeLog("text="+KR_T8HomeRateText());
    KR_T8HomeRateSet(false);
    KR_T8HomeEnter();
    KR_ClaudeShot("home_probe_1.bmp");
    KR_T8HomeRateSet(true);
    KR_ClaudeProbeLog("areas="+("%d" % KR_T8HomeShow(true)));
    KR_ClaudeShot("home_probe_2.bmp");
    KR_T8HomeLeave();
    KR_ClaudeShot("home_probe_3.bmp");
    string act=AFL_Activity_Load("Asra\\Mods.pact");
    KR_ClaudeProbeLog("mods="+act);
    if(AFL_Activity_IsExistPartsByName(act,"KR_HomeRateToggle")) KR_ClaudeProbeLog("toggle part present");
    if(AFL_Activity_IsExistPartsByName(act,"ルートパーツ")) Ｐ＿Ｚ座標設定(AFL_Activity_GetPartsNumber(act,"ルートパーツ"),900000);
    KR_ClaudeShot("home_probe_4.bmp");
    system.Exit(0);
    return 0;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0,"NightRAFCGMode.asd");
    PassRegister.SetFileName(1,"NightRAFMemMode.asd");
    PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    KR_ClaudeProbeLog("resume loading");
    system.ResumeLoad("@@KEY@@","@@SAVE@@");
    system.Exit(2);return 2;
}
'''
def main(save='NightR38.asd'):
    source=e.O
    c.O=source;c.ROOT=e.O/'toggle_fail_probe';c.BOOT='NightRemasterClaudeToggle';c.SAVEDIR='SaveData_KR_ClaudeToggleFailProbe_20260924';c.SAVES=p.SAVE.parent/c.SAVEDIR
    c.ROOT.mkdir(parents=True,exist_ok=True)
    for f in c.ROOT.glob('home_probe_*'):f.unlink()
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    src=source/'NightRemaster.ain';m=b.read_meta(source/'candidate_meta.json')
    jaf=audio.JAF+'\n'+HOME_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save)
    (c.ROOT/'probe.jaf').write_text(jaf,'utf8');decl=c.ROOT/'probe_declared.ain';b.cmd('ain','edit','--jaf',c.ROOT/'probe.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',c.ROOT/'probe_declared_meta.json',decl);dm=b.read_meta(c.ROOT/'probe_declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    for f in added:
        path=c.ROOT/f"probe_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl);patch.append(b.clean(b.native_lower(path.read_text('utf8')),f['name']))
    (c.ROOT/'probe.jam').write_text('\n'.join(patch),'utf8');out=c.ROOT/'NightRemaster.ain';b.cmd('ain','edit','--jam',c.ROOT/'probe.jam','-o',out,decl)
    rawa=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',rawa,12)[0];struct.pack_into('<I',rawa,24+size,m['functions'][0]['address'])
    struct.pack_into('<I',rawa,rawa.index(b'MAIN')+4,ids['KR_ClaudeProbeMain'])
    wait=next(f['index'] for f in m['functions'] if f['name']=='AFL_Parts_WaitForClick')
    versions=q.versions(source/'native_raw_code.jam');n=0
    for f in m['functions']:
        for v in [v for v in versions.get(f['index'],[]) if v['start']==f['address']]:
            for ad,op in v['ops']:
                if op==f'CALLFUNC 0x{wait:x}':
                    assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait);struct.pack_into('<Hi',rawa,16+ad,0x30,ids['KR_ClaudeHomeWait']);n+=1
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]))
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(src),source_sha256=e.h(src),probe_sha256=e.h(out),audio=audio.POLICY,
        input=f'Resume of a copied {save}; every WaitForClick call ({n}) runs the r4 panel stages and exits.',author=e.AUTHOR),indent=2),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    for n in ['NightRemasterEX.ex']:shutil.copy2(source/n,c.ROOT/n);shutil.copy2(source/n,c.ROOT/n.replace('NightRemaster',c.BOOT,1))
    shutil.copy2(p.SAVE/save,c.SAVES/save)
    blocker=c.SAVES/'YoruKR_HomeRate.dat'
    assert not blocker.is_file(),'probe folder must not hold a real preference file'
    blocker.mkdir(exist_ok=True)
    if (c.ROOT/'claude_probe.txt').exists():(c.ROOT/'claude_probe.txt').unlink()
    result=c.launch(timeout=180)
    log=c.ROOT/'claude_probe.txt';result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else []
    result['blocker_is_dir']=blocker.is_dir()
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image
    for pth in c.ROOT.glob('home_probe_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    result['wait_sites']=n;result['save']=save
    (c.ROOT/'toggle_fail_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='events'},ensure_ascii=False,indent=1),len(result['events']))
if __name__=='__main__':main(*sys.argv[1:])
