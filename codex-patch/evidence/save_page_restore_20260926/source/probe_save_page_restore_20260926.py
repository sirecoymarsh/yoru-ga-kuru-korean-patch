"""Muted private-save regression: real latest-slot selection, real save/load screens."""
from pathlib import Path
import datetime,json,shutil,struct,sys,zlib
from PIL import Image
import build_save_page_restore_20260926 as e
import probe_save_slots_20260925 as old
import autosave_probe_claude_r14_20260924 as g
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio

JAF=g.AUTO_JAF.split('string KR_ClaudeNext')[0]+r'''
int KR_PageField(ref C_SceneSaveLoadView view) { return 0; }
void KR_PageObserved(ref C_SceneSaveLoadView view) {
    int actual=KR_PageField(view);
    string stored=SystemService.SystemVariable_Get("Page.Expected");
    int expected=stored.ToInt();
    KR_ClaudeProbeLog("OBSERVED="+("%d"%actual)+" EXPECTED="+("%d"%expected));
    if(actual!=expected) { KR_ClaudeProbeLog("FAIL page");system.Exit(61); }
}
void KR_PageScreens(int slot) {
    int number=-1;int page=-1;
    int found=N_SaveLoad::GetNewDataNo(number,page,false);
    if(slot>=0 && (found!=1 || number!=slot || page!=KR_SavePage(slot))) { KR_ClaudeProbeLog("FAIL newest manual");system.Exit(62); }
    if(slot<0 && found!=0) { KR_ClaudeProbeLog("FAIL empty manual");system.Exit(63); }
    if(page<0) page=0;
    KR_ClaudeProbeLog("LATEST="+("%d"%number)+" PAGE="+("%d"%page));
    int expected=page;
    if(@@BASELINE@@) expected=0;
    SystemService.SystemVariable_Set("Page.Expected","%d"%expected);
    SystemService.SystemVariable_Set("Page.Slot","%d"%slot);
    SystemService.SystemVariable_Set("Page.Stage","load");
    ■セーブ／ロード画面実行();
    SystemService.SystemVariable_Set("Page.Stage","save");
    ■セーブ／セーブ画面実行();
}
int KR_ClaudeAutoWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    string stage=SystemService.SystemVariable_Get("Page.Stage");
    if(stage=="load" || stage=="save") {
        string slot=SystemService.SystemVariable_Get("Page.Slot");
        if(slot=="49" || slot=="-1") KR_ClaudeShot(stage+"_"+slot+".bmp");
        return 10003;
    }
    if(stage!="") { KR_ClaudeProbeLog("FAIL unexpected wait");system.Exit(64); }
    SystemService.SystemVariable_Set("Page.Stage","main");
    KR_PageScreens(49);
    if(!AFL_GameSave_Copy(5,49)) system.Exit(65);
    AFL_GameSave_Delete(49);
    KR_PageScreens(5);
    if(!AFL_GameSave_Copy(4,5)) system.Exit(66);
    AFL_GameSave_Delete(5);
    KR_PageScreens(4);
    if(!AFL_GameSave_Copy(1,4)) system.Exit(67);
    AFL_GameSave_Delete(4);
    KR_PageScreens(1);
    AFL_GameSave_Delete(1);
    KR_PageScreens(-1);
    if(!AFL_GameSave_IsExistFile(999) || !AFL_GameSave_IsExistFile(998)) system.Exit(69);
    KR_ClaudeProbeLog("PASS 49,5,4,1,auto-only; both native screens; no user save writes");
    system.Exit(0);return 0;
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0,"NightRAFCGMode.asd");
    PassRegister.SetFileName(1,"NightRAFMemMode.asd");
    PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    system.ResumeLoad("@@KEY@@","NightR999.asd");
    system.Exit(2);return 2;
}
'''

def main(mode='candidate'):
    assert mode in ['baseline','candidate'];assert e.p.stopped(e.p.RT)
    folder=e.S if mode=='baseline' else e.O
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    c.e=e;c.O=e.O;c.ROOT=e.O/('probe_'+mode+'_'+stamp);c.ROOT.mkdir()
    c.BOOT='NightRemasterSavePage';c.SAVEDIR='SaveData_KR_SavePage_'+stamp;c.SAVES=e.p.SAVE.parent/c.SAVEDIR
    m=e.b.read_meta(folder/'candidate_meta.json');source=folder/'NightRemaster.ain'
    seed=e.p.SAVE/'NightR36.asd';r=e.q.Reader(zlib.decompress(seed.read_bytes()[8:]));r.string();r.integer();key=r.string()
    # Reuse the verified muted save-screen harness; only observation hooks are added.
    old.e=e;old.QA_JAF='void KR_SaveProbeRows(ref C_SceneSaveLoadView view) { }';original_o=e.O
    text=JAF.replace('@@BASELINE@@','true' if mode=='baseline' else 'false')
    # Its source location is a module setting; keep output and private SaveFolder unchanged.
    e.O=folder
    sites=old.build_probe(key,text)
    e.O=original_o
    # Complete the new method reader and observe after the real Init has selected its page.
    pm=e.b.read_meta(c.ROOT/'probe_meta.json');names={f['name']:f['index'] for f in pm['functions']}
    body=e.clean(pm,29571,c.ROOT/'NightRemaster.ain');pos=body.rfind('\tRETURN\n')
    body=body[:pos]+'\tPUSHSTRUCTPAGE\n\tCALLFUNC KR_PageObserved\n'+body[pos:]
    patch=body+'\n'+e.wrapper(pm,names['KR_PageField'],'\t.LOCALREF view\n\tPUSH 12\n\tX_REF 1\n')
    (c.ROOT/'observe.jam').write_text(patch,'utf8');observed=c.ROOT/'observed.ain'
    e.b.cmd('ain','edit','--jam',c.ROOT/'observe.jam','-o',observed,c.ROOT/'NightRemaster.ain')
    raw=bytearray(e.b.unpack(observed.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+size,pm['functions'][0]['address'])
    (c.ROOT/'NightRemaster.ain').write_bytes(e.b.pack(raw,observed.read_bytes()[:8]))
    manifest=dict(source=str(source),source_sha256=e.h(source),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),audio=audio.POLICY,
                  input='Muted copy of dungeon save36; actual save/load screens and actual newest-manual selector. Only private copies are copied/deleted.',save_folder=c.SAVEDIR,author=e.AUTHOR)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(manifest,indent=2),'utf8')
    before=e.p.snapshot_saves();c.setup_folder()
    for source_no,dest_no in [(36,999),(36,998),(49,49)]:
        for file in e.p.SAVE.glob(f'NightR{source_no:02d}.*'):
            shutil.copy2(file,c.SAVES/(f'NightR{dest_no:02d}'+file.suffix))
    assert (c.SAVES/'NightR49.vsf').exists() and (c.SAVES/'NightR999.asd').exists()
    native=c.launch(timeout=100);log=c.ROOT/'claude_probe.txt'
    native['log']=e.b.decode(log.read_bytes()).splitlines() if log.exists() else []
    for img in c.ROOT.glob('*.bmp'):Image.open(img).save(img.with_suffix('.png'))
    result=dict(mode=mode,source_sha256=e.h(source),manifest=manifest,native=native,real_saves_unchanged=before==e.p.snapshot_saves())
    assert result['real_saves_unchanged'];(c.ROOT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2));print('RESULT',c.ROOT/'result.json')

if __name__=='__main__':main(*sys.argv[1:])
