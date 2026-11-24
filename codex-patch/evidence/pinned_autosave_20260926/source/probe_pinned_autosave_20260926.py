"""Muted/private native wheel-page navigation, pinned coordinates and selection checks."""
import datetime,json,shutil,struct,zlib
from PIL import Image
import build_pinned_autosave_20260926 as e
import probe_save_slots_20260925 as old
import autosave_probe_claude_r14_20260924 as g
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio

JAF=g.AUTO_JAF.split('string KR_ClaudeNext')[0]+r'''
float KR_PinY(ref C_SceneSaveLoadView view,int row) { ref CASPosF pos;return 0.0; }
void KR_PinPositions(ref C_SceneSaveLoadView view) {
    int page=KR_SaveProbeField(view,12);
    SystemService.SystemVariable_Set("Pin.Page","%d"%page);
    for(int i=0;i<KR_SaveProbeCount(view);i++) {
        if(KR_PinY(view,i)!=(i*72)) { KR_ClaudeProbeLog("FAIL row position");system.Exit(64); }
    }
    KR_ClaudeProbeLog("PINNED page="+("%d"%page)+" y=0,72");
}
int KR_ClaudeAutoWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    string stage=SystemService.SystemVariable_Get("Pin.Stage");
    if(stage=="load" || stage=="save") {
        string value=SystemService.SystemVariable_Get("Pin.Step");int step=value.ToInt();
        string page=SystemService.SystemVariable_Get("Pin.Page");
        if(page=="0" || page=="1" || page=="9") KR_ClaudeShot(stage+"_"+page+".bmp");
        SystemService.SystemVariable_Set("Pin.Step","%d"%(step+1));
        if(step==9) return 10002;
        if(step==10) return 10003;
        return 10001;
    }
    if(stage!="") { KR_ClaudeProbeLog("FAIL unexpected wait");system.Exit(65); }
    SystemService.SystemVariable_Set("Pin.Stage","load");SystemService.SystemVariable_Set("Pin.Step","0");
    ■セーブ／ロード画面実行();
    SystemService.SystemVariable_Set("Pin.Stage","save");SystemService.SystemVariable_Set("Pin.Step","0");
    ■セーブ／セーブ画面実行();
    KR_ClaudeProbeLog("PASS all ten pages, next and previous; auto-save rows fixed; actual selectors checked");
    system.Exit(0);return 0;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0,"NightRAFCGMode.asd");PassRegister.SetFileName(1,"NightRAFMemMode.asd");PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    system.ResumeLoad("@@KEY@@","NightR999.asd");system.Exit(2);return 2;
}
'''

def main():
    assert e.p.stopped(e.p.RT),'Do not overlap a running player game'
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');c.e=e;c.O=e.O;c.ROOT=e.O/('native_probe_'+stamp);c.ROOT.mkdir()
    c.BOOT='NightRemasterPinnedAuto';c.SAVEDIR='SaveData_KR_PinnedAuto_'+stamp;c.SAVES=e.p.SAVE.parent/c.SAVEDIR
    old.e=e
    old.QA_JAF=old.QA_JAF.replace('if(type==1 && page==0) KR_SaveProbeHover(view,998);','if(type==1 && page==9) KR_SaveProbeHover(view,49);\n    KR_PinPositions(view);')
    seed=e.p.SAVE/'NightR36.asd';r=e.q.Reader(zlib.decompress(seed.read_bytes()[8:]));r.string();r.integer();key=r.string()
    sites=old.build_probe(key,JAF)
    pm=e.b.read_meta(c.ROOT/'probe_meta.json');fid=next(f['index'] for f in pm['functions'] if f['name']=='KR_PinY')
    ops='''\tPUSHLOCALPAGE
\tPUSH 2
\t.LOCALREF view
\tPUSH 8
\tX_REF 1
\t.LOCALREF row
\tX_REF 1
\tPUSH 29592
\tCALLMETHOD 0
\tX_ASSIGN 1
\tPOP
\t.LOCALREF pos
\tPUSH 1
\tX_REF 1
\t.LOCALDELETE pos
'''
    (c.ROOT/'position.jam').write_text(e.wrapper(pm,fid,ops),'utf8');out=c.ROOT/'observed.ain'
    e.b.cmd('ain','edit','--jam',c.ROOT/'position.jam','-o',out,c.ROOT/'NightRemaster.ain')
    raw=bytearray(e.b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,pm['functions'][0]['address'])
    (c.ROOT/'NightRemaster.ain').write_bytes(e.b.pack(raw,out.read_bytes()[:8]))
    manifest=dict(source=str(e.O/'NightRemaster.ain'),source_sha256=e.h(e.O/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),audio=audio.POLICY,
        input='Resume copied save36; native next/previous page returns; exact native cells, y coordinates and selection enabled checks; no save writes.',save_folder=c.SAVEDIR,author=e.AUTHOR)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(manifest,indent=2),'utf8')
    before=e.p.snapshot_saves();c.setup_folder()
    for source_no,dest_no in [(36,999),(36,998),(49,49)]:
        for f in e.p.SAVE.glob(f'NightR{source_no:02d}.*'):shutil.copy2(f,c.SAVES/(f'NightR{dest_no:02d}'+f.suffix))
    native=c.launch(timeout=130);log=c.ROOT/'claude_probe.txt'
    native['log']=e.b.decode(log.read_bytes()).splitlines() if log.exists() else []
    for img in c.ROOT.glob('*.bmp'):Image.open(img).save(img.with_suffix('.png'))
    result=dict(source_sha256=e.h(e.O/'NightRemaster.ain'),manifest=manifest,native=native,real_saves_unchanged=before==e.p.snapshot_saves())
    assert result['real_saves_unchanged'];(c.ROOT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2));print('RESULT',c.ROOT/'result.json')

if __name__=='__main__':main()
