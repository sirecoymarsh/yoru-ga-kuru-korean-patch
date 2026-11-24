"""Claude Opus 5.5 (2026-09-24) r11: native check that the coloured title draw is exact, then colour screenshots.

Isolated, muted, own SaveFolder; resumes a copy of the user's newest save (same technique as charmissing_probe_*).
For 쿄카's place / conditions / party pages:
  A = the page with every colour mark moved to its line's end as a full-width space, drawn by the ORIGINAL call (gate off)
      - same raw line lengths, so the dialog has the same size and position;
  B = the marked page through KR_T8TitleDraw in mono mode (runs split at the marks, all in the dialog colour);
  C = the marked page in colour.
A and B must be pixel-identical (Python compares them); C is for the eye. Then the menu is walked in colour like r10.
"""
from pathlib import Path
import datetime,json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r11 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
import charmissing_probe_claude_r9_20260924 as base
b=e.b;a=e.a;p=e.p;q=e.q
SCRIPT=[3,1,1,0,0,2,0,0,0]
CC_JAF=r'''
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
void KR_ClaudeTitleSpy(int parts, int x, int y, string text, CASFont font, int cs, int ls, int state) {
    string t = SystemService.SystemVariable_Get("YoruKR.T8.Title");
    string col = SystemService.SystemVariable_Get("YoruKR.T8.Color");
    string k = SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Spy");
    int n = k.ToInt();
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Spy", "%d" % (n + 1));
    int eq = 0;
    if (KR_T8TitleOptIn(text)) eq = 1;
    KR_ClaudeProbeLog("SPY " + ("%d" % n) + " len=" + ("%d" % text.Length()) + " tlen=" + ("%d" % t.Length()) + " color=" + col + " optin=" + ("%d" % eq) + " x=" + ("%d" % x) + " y=" + ("%d" % y) + " cs=" + ("%d" % cs) + " ls=" + ("%d" % ls));
    TextFile.WriteAll("spy_text_" + ("%d" % n) + ".txt", text);
    TextFile.WriteAll("spy_title_" + ("%d" % n) + ".txt", t);
    KR_T8TitleDraw(parts, x, y, text, font, cs, ls, state);
}
string KR_ClaudeMarksToTail(string text) {
    string out="";
    string tail="";
    for(int i=0;i<text.Length();i++) {
        string ch=KR_JosaSlice(text,i,1);
        if(ch=="\n") { out=out+tail+"\n"; tail=""; }
        else if(KR_T8IsMark(ch)) tail=tail+"　";
        else out=out+ch;
    }
    return out+tail;
}
void KR_ClaudeShowTitle(string title,bool gate,bool mono,string shot) {
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.ShotName",shot);
    ■選択ダイアログ／初期化();
    ■選択ダイアログ／タイプ設定(2026091602);
    ■選択ダイアログ／クリック制限／全体();
    ■選択ダイアログ／横項目数(1);
    ■選択ダイアログ／タイトル設定(title);
    ■選択ダイアログ／選択肢追加(0,"돌아가기","",false);
    SystemService.SystemVariable_Set("YoruKR.T8.Title",title);
    if(gate) SystemService.SystemVariable_Set("YoruKR.T8.Color","1"); else SystemService.SystemVariable_Set("YoruKR.T8.Color","");
    if(mono) SystemService.SystemVariable_Set("YoruKR.T8.ColorTest","mono"); else SystemService.SystemVariable_Set("YoruKR.T8.ColorTest","");
    ■選択ダイアログ／実行(true,200);
    SystemService.SystemVariable_Set("YoruKR.T8.Title","");
    SystemService.SystemVariable_Set("YoruKR.T8.Color","");
    SystemService.SystemVariable_Set("YoruKR.T8.ColorTest","");
}
int KR_ClaudeCcWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    string stage=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Stage");
    if(stage=="shot") { KR_ClaudeShot(SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.ShotName")); return 0; }
    if(stage=="menu") {
        string step=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Step");
        int n=step.ToInt();
        SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Step","%d" % (n+1));
        KR_ClaudeShot("cc_menu_"+("%d" % n)+".bmp");
        if(n>=@@STEPS@@) { KR_ClaudeProbeLog("script overrun"); system.Exit(4); }
        return KR_ClaudeScripted(n);
    }
    if(stage!="") { KR_ClaudeProbeLog("unexpected wait in stage "+stage); system.Exit(3); return 0; }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","shot");
    string pages="place,cond,party";
    for(int k=0;k<3;k++) {
        string t="";
        string name="";
        if(k==0) { t=KR_T8PlaceText(3); name="place"; }
        if(k==1) { t=KR_T8CondText(3); name="cond"; }
        if(k==2) { t=KR_T8PartyText(3); name="party"; }
        KR_ClaudeShowTitle(KR_ClaudeMarksToTail(t),false,false,"cc_"+name+"_A.bmp");
        KR_ClaudeShowTitle(t,true,true,"cc_"+name+"_B.bmp");
        KR_ClaudeShowTitle(t,true,false,"cc_"+name+"_C.bmp");
    }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","menu");
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Step","0");
    KR_T8CharMissingMenu();
    KR_ClaudeProbeLog("END");
    system.Exit(0);
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
    jaf=audio.JAF+'\n'+CC_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save).replace('@@SCRIPT@@',script).replace('@@STEPS@@',str(len(SCRIPT)))
    # same literal encoding as the r10/r11 build (Korean and the listed marks go through the FNL proxy encoder)
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(b.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('가'<=c<='힣' or c in '·…「」【】　' for c in json.loads(z[0])) else z[0],jaf)
    (c.ROOT/'probe.jaf').write_text(jaf,'utf8');decl=c.ROOT/'probe_declared.ain';b.cmd('ain','edit','--jaf',c.ROOT/'probe.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',c.ROOT/'probe_declared_meta.json',decl);dm=b.read_meta(c.ROOT/'probe_declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    for f in added:
        path=c.ROOT/f"probe_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl);patch.append(b.clean(b.native_lower(path.read_text('utf8')),f['name']))
    (c.ROOT/'probe.jam').write_text('\n'.join(patch),'utf8');out=c.ROOT/'NightRemaster.ain';b.cmd('ain','edit','--jam',c.ROOT/'probe.jam','-o',out,decl)
    rawa=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',rawa,12)[0];struct.pack_into('<I',rawa,24+size,m['functions'][0]['address'])
    struct.pack_into('<I',rawa,rawa.index(b'MAIN')+4,ids['KR_ClaudeProbeMain'])
    site=json.loads((source/'build_evidence.json').read_text('utf8'))['title_color']['site']
    draw=next(f['index'] for f in m['functions'] if f['name']=='KR_T8TitleDraw')
    assert rawa[16+site:16+site+6]==struct.pack('<Hi',0x30,draw);struct.pack_into('<Hi',rawa,16+site,0x30,ids['KR_ClaudeTitleSpy'])
    wait=next(f['index'] for f in m['functions'] if f['name']=='AFL_Parts_WaitForClick')
    versions=q.versions(source/'native_raw_code.jam');n=0
    for f in m['functions']:
        for v in [v for v in versions.get(f['index'],[]) if v['start']==f['address']]:
            for ad,op in v['ops']:
                if op==f'CALLFUNC 0x{wait:x}':
                    assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait);struct.pack_into('<Hi',rawa,16+ad,0x30,ids['KR_ClaudeCcWait']);n+=1
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]));return n

def main(save='NightR39.asd'):
    source=e.O;stamp=datetime.datetime.now().strftime('%H%M%S')
    c.O=source;c.ROOT=e.O/'colorcheck_probe';c.BOOT='NightRemasterClaudeCc';c.SAVEDIR=f'SaveData_KR_ClaudeColorProbe_20260924_{stamp}';c.SAVES=p.SAVE.parent/c.SAVEDIR
    assert not c.SAVES.exists();c.ROOT.mkdir(parents=True,exist_ok=True)
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    m=b.read_meta(source/'candidate_meta.json');n=build_probe(source,m,key,save)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(source/'NightRemaster.ain'),source_sha256=e.h(source/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),
        audio=audio.POLICY,input=f'Resume of a copied {save}; A/B/C title draws for 쿄카 place/cond/party, then the menu in colour ({SCRIPT}).',save_folder=c.SAVEDIR,author=e.AUTHOR),indent=2,ensure_ascii=False),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    for x in ['NightRemasterEX.ex']:shutil.copy2(source/x,c.ROOT/x);shutil.copy2(source/x,c.ROOT/x.replace('NightRemaster',c.BOOT,1))
    shutil.copy2(p.SAVE/save,c.SAVES/save)
    log=c.ROOT/'claude_probe.txt'
    if log.exists():log.rename(c.ROOT/f'claude_probe_{stamp}_prev.txt')
    result=c.launch(timeout=240);result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else [];result.update(save=save,save_folder=c.SAVEDIR,wait_sites=n,script=SCRIPT)
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image,ImageChops
    for pth in c.ROOT.glob('cc_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    cmp={}
    for name in ['place','cond','party']:
        A=Image.open(c.ROOT/f'cc_{name}_A.png').convert('RGB');B=Image.open(c.ROOT/f'cc_{name}_B.png').convert('RGB');C=Image.open(c.ROOT/f'cc_{name}_C.png').convert('RGB')
        cmp[name]=dict(A_vs_B=ImageChops.difference(A,B).getbbox(),A_vs_C=ImageChops.difference(A,C).getbbox())
    result['compare']=cmp
    (c.ROOT/'colorcheck_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print({x:y for x,y in result.items() if x not in ('events','log')},len(result['events']));print('\n'.join(result['log'][-6:]))
if __name__=='__main__':main(*sys.argv[1:])
