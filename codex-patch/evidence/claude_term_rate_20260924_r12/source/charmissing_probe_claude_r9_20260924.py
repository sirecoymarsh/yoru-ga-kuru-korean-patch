"""Claude Opus 5.5 (2026-09-24) r9: native screenshots of 「캐릭터별 남은 이벤트」 on a resumed copy of the user's newest save.

Isolated, muted, own SaveFolder (same technique as autosave_probe_claude_r8_20260924.py). At the first WaitForClick after the
resume the probe logs every character's page text and dated lines (this save's real state), then opens the menu itself;
every later WaitForClick is a scripted chooser that saves a screenshot and answers with the next choice id:
list -> 쿄카 -> 날짜 이벤트 보기 -> back -> back -> 이즈미 -> 날짜 이벤트 보기 -> back -> back -> close.
User saves are only read (one copied save).
"""
from pathlib import Path
import datetime,json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r9 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
b=e.b;a=e.a;p=e.p;q=e.q
SCRIPT=[3,1,0,0,2,1,0,0,0]
CM_JAF=r'''
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
int KR_ClaudeScripted(int n) {
@@SCRIPT@@
    return 0;
}
int KR_ClaudeCmWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    string stage=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Stage");
    if(stage=="menu") {
        string step=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Step");
        int n=step.ToInt();
        SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Step","%d" % (n+1));
        KR_ClaudeShot("cm_probe_"+("%d" % n)+".bmp");
        if(n>=@@STEPS@@) { KR_ClaudeProbeLog("script overrun"); system.Exit(4); }
        return KR_ClaudeScripted(n);
    }
    if(stage!="") { KR_ClaudeProbeLog("unexpected wait in stage "+stage); system.Exit(3); return 0; }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","menu");
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Step","0");
    for(int p=2;p<=8;p++) {
        KR_ClaudeProbeLog("PAGE "+("%d" % p)+"\n"+KR_T8CharMissingText(p));
        KR_ClaudeProbeLog("DATED "+("%d" % p)+KR_T8DatedLines(p));
    }
    KR_ClaudeProbeLog("TODAY before 6/30="+("%d" % KR_ClaudeB(L_Calendar::IsTodayOrBefore(6,30))));
    KR_T8CharMissingMenu();
    KR_ClaudeProbeLog("END");
    system.Exit(0);
    return 0;
}
int KR_ClaudeB(bool x) {
    if(x) return 1;
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
    script=''.join(f'    if(n=={i}) return {v};\n' for i,v in enumerate(SCRIPT))
    jaf=audio.JAF+'\n'+CM_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save).replace('@@SCRIPT@@',script).replace('@@STEPS@@',str(len(SCRIPT)))
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
                    assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait);struct.pack_into('<Hi',rawa,16+ad,0x30,ids['KR_ClaudeCmWait']);n+=1
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]));return n

def main(save='NightR39.asd'):
    source=e.O;stamp=datetime.datetime.now().strftime('%H%M%S')
    c.O=source;c.ROOT=e.O/'charmissing_probe';c.BOOT='NightRemasterClaudeCm';c.SAVEDIR=f'SaveData_KR_ClaudeCharMissingProbe_20260924_{stamp}';c.SAVES=p.SAVE.parent/c.SAVEDIR
    assert not c.SAVES.exists();c.ROOT.mkdir(parents=True,exist_ok=True)
    for f in c.ROOT.glob('cm_probe_*'):f.unlink()
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    m=b.read_meta(source/'candidate_meta.json');n=build_probe(source,m,key,save)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(source/'NightRemaster.ain'),source_sha256=e.h(source/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),
        audio=audio.POLICY,input=f'Resume of a copied {save}; WaitForClick ({n} sites) opens 캐릭터별 남은 이벤트 and answers {SCRIPT}.',save_folder=c.SAVEDIR,author=e.AUTHOR),indent=2,ensure_ascii=False),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    for x in ['NightRemasterEX.ex']:shutil.copy2(source/x,c.ROOT/x);shutil.copy2(source/x,c.ROOT/x.replace('NightRemaster',c.BOOT,1))
    shutil.copy2(p.SAVE/save,c.SAVES/save)
    log=c.ROOT/'claude_probe.txt'
    if log.exists():log.rename(c.ROOT/f'claude_probe_{stamp}_prev.txt')
    result=c.launch(timeout=240);result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else [];result.update(save=save,save_folder=c.SAVEDIR,wait_sites=n,script=SCRIPT)
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image
    for pth in c.ROOT.glob('cm_probe_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    (c.ROOT/'charmissing_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print({x:y for x,y in result.items() if x not in ('events','log')},len(result['events']));print('\n'.join(result['log']))
if __name__=='__main__':main(*sys.argv[1:])
