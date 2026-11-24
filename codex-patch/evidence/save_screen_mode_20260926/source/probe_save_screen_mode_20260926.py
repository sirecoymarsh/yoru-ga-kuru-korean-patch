"""Muted native settings dispatch, both layouts, independent preferences and cross-mode resume."""
import datetime,json,shutil,struct,zlib
from PIL import Image
import build_save_screen_mode_20260926 as e
import probe_save_slots_20260925 as old
import autosave_probe_claude_r14_20260924 as g
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio

JAF=g.AUTO_JAF.split('string KR_ClaudeNext')[0]+r'''
float KR_StyleY(ref C_SceneSaveLoadView view,int row) { ref CASPosF pos;return 0.0; }
void KR_StyleRows(ref C_SceneSaveLoadView view) {
    int page=KR_SaveProbeField(view,12);int type=KR_SaveProbeField(view,11);
    SystemService.SystemVariable_Set("Style.Page","%d"%page);
    int pitch=101;if(KR_SaveViewAlt()) pitch=72;
    for(int i=0;i<KR_SaveProbeCount(view);i++) if(KR_StyleY(view,i)!=(i*pitch)) system.Exit(67);
    KR_ClaudeProbeLog("LAYOUT alt="+("%d"%KR_ClaudeB(KR_SaveViewAlt()))+" page="+("%d"%page)+" type="+("%d"%type)+" pitch="+("%d"%pitch));
}
void KR_StyleConfig(int choice) {
    C_ConfigView conf;
    int previous=AFL_Parts_GetActiveLayer();int layer=AFL_Parts_AddTopLayer();AFL_Parts_SetActiveLayer(layer);
    string act=AFL_Activity_Load("Asra\\Mods.pact");
    conf.EventConfLoadedActivity("Asra\\Mods.pact",act);
    conf.EventConfAsraDataForParts(0,0,act);
    int number=AFL_Activity_GetPartsNumber(act,"KR_SaveStyleButton");
    if(number<=0) system.Exit(68);
    KR_ClaudeShot("mods.bmp");
    SystemService.SystemVariable_Set("Style.Stage","choose");
    SystemService.SystemVariable_Set("Style.Choice","%d"%choice);
    conf.ClickEvent(number,0,0);
    AFL_Activity_Release(act);
    AFL_Parts_EraseLayer(layer);AFL_Parts_SetActiveLayer(previous);
    KR_ClaudeProbeLog("SETTING choice="+("%d"%choice)+" alt="+("%d"%KR_ClaudeB(KR_SaveStyleAlt())));
}
void KR_StyleScreens(bool browse) {
    SystemService.SystemVariable_Set("Style.Browse","0");if(browse) SystemService.SystemVariable_Set("Style.Browse","1");
    SystemService.SystemVariable_Set("Style.Stage","load");SystemService.SystemVariable_Set("Style.Step","0");
    ■セーブ／ロード画面実行();
    SystemService.SystemVariable_Set("Style.Stage","save");SystemService.SystemVariable_Set("Style.Step","0");
    ■セーブ／セーブ画面実行();
}
int KR_ClaudeAutoWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    string stage=SystemService.SystemVariable_Get("Style.Stage");
    if(stage=="choose") {
        string chosen=SystemService.SystemVariable_Get("Style.Choice");
        KR_ClaudeShot("choice_"+chosen+".bmp");
        return chosen.ToInt();
    }
    if(stage=="load" || stage=="save") {
        string value=SystemService.SystemVariable_Get("Style.Step");int step=value.ToInt();
        string page=SystemService.SystemVariable_Get("Style.Page");
        string style="original";if(KR_SaveViewAlt()) style="alternative";
        if(page=="0" || page=="1" || page=="9") KR_ClaudeShot(style+"_"+stage+"_"+page+".bmp");
        SystemService.SystemVariable_Set("Style.Step","%d"%(step+1));
        if(SystemService.SystemVariable_Get("Style.Browse")!="1" || step==10) return 10003;
        if(step==9) return 10002;
        return 10001;
    }
    if(stage!="") { KR_ClaudeProbeLog("FAIL unexpected wait");system.Exit(69); }
    if(!KR_SaveStyleAlt()) { KR_ClaudeProbeLog("FAIL default mode");system.Exit(70); }
    KR_StyleConfig(0);if(!KR_SaveStyleAlt()) system.Exit(71);
    KR_StyleConfig(1);if(KR_SaveStyleAlt()) system.Exit(72);
    KR_StyleScreens(true);
    KR_StyleConfig(2);if(!KR_SaveStyleAlt()) system.Exit(73);
    KR_StyleScreens(true);
    KR_StyleConfig(1);if(KR_SaveStyleAlt()) system.Exit(74);
    SystemService.SystemVariable_Set("Style.Stage","saving");
    ■セーブ／オートセーブ実行(47);
    // On the second process ResumeLoad re-enters here, after the real saved writer.
    if(FileOperation.ExistFile("restart.flag")) {
        if(KR_SaveStyleAlt()) system.Exit(75);
        KR_ClaudeProbeLog("RESTART original preference preserved; saved47 resumed");
        KR_StyleScreens(false);
        KR_StyleConfig(2);if(!KR_SaveStyleAlt()) system.Exit(76);
        KR_StyleScreens(false);
        KR_ClaudeProbeLog("PASS B cross-mode saved47 resume and restart preference");system.Exit(0);return 0;
    }
    if(!AFL_GameSave_IsExistFile(47)) system.Exit(77);
    TextFile.WriteAll("restart.flag","resume\n");
    KR_ClaudeProbeLog("PASS A both layouts all ten pages, native config dispatch, cancel and persisted original choice");
    system.Exit(0);return 0;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0,"NightRAFCGMode.asd");PassRegister.SetFileName(1,"NightRAFMemMode.asd");PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    if(FileOperation.ExistFile("restart.flag")) system.ResumeLoad("@@KEY@@","NightR47.asd");
    else system.ResumeLoad("@@KEY@@","NightR999.asd");
    system.Exit(2);return 2;
}
'''

def main():
    assert e.p.stopped(e.p.RT),'Do not overlap a player game'
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');c.e=e;c.O=e.O;c.ROOT=e.O/('native_probe_'+stamp);c.ROOT.mkdir()
    c.BOOT='NightRemasterSaveStyle';c.SAVEDIR='SaveData_KR_SaveStyle_'+stamp;c.SAVES=e.p.SAVE.parent/c.SAVEDIR
    old.e=e;old.QA_JAF=old.QA_JAF.replace('if(type==1 && page==0) KR_SaveProbeHover(view,998);','if(type==1 && page==9) KR_SaveProbeHover(view,49);\n    KR_StyleRows(view);')
    seed=e.p.SAVE/'NightR36.asd';r=e.q.Reader(zlib.decompress(seed.read_bytes()[8:]));r.string();r.integer();key=r.string()
    sites=old.build_probe(key,JAF)
    pm=e.b.read_meta(c.ROOT/'probe_meta.json');fid=next(f['index'] for f in pm['functions'] if f['name']=='KR_StyleY')
    ops='\tPUSHLOCALPAGE\n\tPUSH 2\n\t.LOCALREF view\n\tPUSH 8\n\tX_REF 1\n\t.LOCALREF row\n\tX_REF 1\n\tPUSH 29592\n\tCALLMETHOD 0\n\tX_ASSIGN 1\n\tPOP\n\t.LOCALREF pos\n\tPUSH 1\n\tX_REF 1\n\t.LOCALDELETE pos\n'
    (c.ROOT/'position.jam').write_text(e.wrapper(pm,fid,ops),'utf8');out=c.ROOT/'observed.ain'
    e.b.cmd('ain','edit','--jam',c.ROOT/'position.jam','-o',out,c.ROOT/'NightRemaster.ain')
    raw=bytearray(e.b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,pm['functions'][0]['address'])
    (c.ROOT/'NightRemaster.ain').write_bytes(e.b.pack(raw,out.read_bytes()[:8]))
    manifest=dict(source=str(e.O/'NightRemaster.ain'),source_sha256=e.h(e.O/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),audio=audio.POLICY,
        input='Copied save36; actual config ClickEvent; original and alternative save/load all pages; private preference marker; save47/resume47 across restart. No user saves written.',save_folder=c.SAVEDIR,author=e.AUTHOR)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(manifest,indent=2),'utf8')
    before=e.p.snapshot_saves();c.setup_folder()
    for source_no,dest_no in [(36,999),(36,998),(49,49)]:
        for f in e.p.SAVE.glob(f'NightR{source_no:02d}.*'):shutil.copy2(f,c.SAVES/(f'NightR{dest_no:02d}'+f.suffix))
    result=dict(source_sha256=e.h(e.O/'NightRemaster.ain'),manifest=manifest)
    for launch in ['A','B']:
        log=c.ROOT/'claude_probe.txt'
        if log.exists():shutil.copy2(log,c.ROOT/('previous_'+launch+'.txt'));log.unlink()
        native=c.launch(timeout=180);native['log']=e.b.decode(log.read_bytes()).splitlines() if log.exists() else []
        result[launch]=native
        print(launch,json.dumps(native,ensure_ascii=False,indent=2),flush=True)
        for img in c.ROOT.glob('*.bmp'):Image.open(img).save(img.with_suffix('.png'))
        if native.get('exit_code')!=0 or native.get('events'):break
    result['real_saves_unchanged']=before==e.p.snapshot_saves();assert result['real_saves_unchanged']
    (c.ROOT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print('RESULT',c.ROOT/'result.json')

if __name__=='__main__':main()
