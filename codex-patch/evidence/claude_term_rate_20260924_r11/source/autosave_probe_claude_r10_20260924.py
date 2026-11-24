"""Claude Opus 5.5 (2026-09-24) r9: the r8 probe run unchanged against the r10 candidate. Claude Opus 5.5 (2026-09-24) r8: native check of the daily/weekly autosaves (isolated, muted, own SaveFolder).

Same technique as home_probe_claude_*: MAIN resumes a COPY of the user's Monday autosave (NightR999.asd) in the probe's own
SaveFolder; every AFL_Parts_WaitForClick call is swapped for KR_ClaudeAutoWait.
Launch A (first WaitForClick after the resume, i.e. the Monday scene):
  weekday / KR_T8AutoSaveDay / KR_T8AutoSaveSlot logged; the game's own ■セーブ／オートセーブ実行 with KR_T8AutoSaveSlot()
  (Monday -> weekly slot 49) and then with 999, timed; KR_T8NewestAutoSlot and N_SaveLoad::GetNewDataNo (with and without
  autosaves) logged; the load screen and the save screen are opened and photographed on page 1 and page 10 (the hook
  answers the screen's own loop: 10002 = next page, 10003 = close).
Launch B: MAIN resumes the weekly autosave written in launch A; execution continues right after that autosave call.
User saves are only read (a copy of NightR999.asd); the probe SaveFolder is new for every run.
"""
from pathlib import Path
import datetime,json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r10 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
b=e.b;a=e.a;p=e.p;q=e.q
AUTO_JAF=r'''
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
int KR_ClaudeB(bool x) {
    if(x) return 1;
    return 0;
}
string KR_ClaudeNext(string p) {
    if(p=="0") return "1";
    if(p=="1") return "2";
    if(p=="2") return "3";
    if(p=="3") return "4";
    if(p=="4") return "5";
    if(p=="5") return "6";
    if(p=="6") return "7";
    if(p=="7") return "8";
    return "9";
}
int KR_ClaudeScreen(string prefix) {
    string page=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Page");
    if(page=="0") KR_ClaudeShot(prefix+"_p1.bmp");
    if(page=="9") { KR_ClaudeShot(prefix+"_p10.bmp"); return 10003; }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Page",KR_ClaudeNext(page));
    return 10002;
}
int KR_ClaudeAutoWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    string stage=SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Stage");
    if(stage=="load") return KR_ClaudeScreen("auto_probe_load");
    if(stage=="save") return KR_ClaudeScreen("auto_probe_save");
    if(stage!="") {
        KR_ClaudeProbeLog("unexpected wait in stage "+stage);
        KR_ClaudeShot("auto_probe_unexpected.bmp");
        system.Exit(3);
        return 0;
    }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","main");
    KR_ClaudeProbeLog("weekday="+("%d" % L_Calendar::GetDayOfWeek())+" day="+("%d" % KR_T8AutoSaveDay())+" slot="+("%d" % KR_T8AutoSaveSlot()));
    KR_ClaudeShot("auto_probe_0.bmp");
    int t0=system.GetTime();
    ■セーブ／オートセーブ実行(KR_T8AutoSaveSlot());
    string marker="";
    if(TextFile.ReadAll("auto_probe_resume.txt",marker)) {
        KR_ClaudeProbeLog("RESUMED weekly autosave; exists49="+("%d" % KR_ClaudeB(AFL_GameSave_IsExistFile(49))));
        KR_ClaudeShot("auto_probe_resumed.bmp");
        system.Exit(0);
        return 0;
    }
    int t1=system.GetTime();
    KR_ClaudeProbeLog("weekly autosave ms="+("%d" % (t1-t0))+" exists49="+("%d" % KR_ClaudeB(AFL_GameSave_IsExistFile(49)))+" newest="+("%d" % KR_T8NewestAutoSlot()));
    ■セーブ／オートセーブ実行(999);
    int t2=system.GetTime();
    KR_ClaudeProbeLog("daily autosave ms="+("%d" % (t2-t1))+" exists999="+("%d" % KR_ClaudeB(AFL_GameSave_IsExistFile(999)))+" newest="+("%d" % KR_T8NewestAutoSlot()));
    string c49="";
    string c999="";
    AFL_GameSave_GetUserComment(49,c49);
    AFL_GameSave_GetUserComment(999,c999);
    KR_ClaudeProbeLog("comment49 len="+("%d" % c49.Length())+" comment999 len="+("%d" % c999.Length())+" same="+("%d" % KR_ClaudeB(c49==c999)));
    int dn=-5;
    int pn=-5;
    int r0=N_SaveLoad::GetNewDataNo(dn,pn,false);
    KR_ClaudeProbeLog("newest manual: ret="+("%d" % r0)+" idx="+("%d" % dn)+" page="+("%d" % pn));
    int r1=N_SaveLoad::GetNewDataNo(dn,pn,true);
    KR_ClaudeProbeLog("newest with autosaves: ret="+("%d" % r1)+" idx="+("%d" % dn)+" page="+("%d" % pn));
    KR_ClaudeProbeLog("labels "+KR_ClaudeLabels());
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","load");
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Page","0");
    ■セーブ／ロード画面実行();
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","save");
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Page","0");
    ■セーブ／セーブ画面実行();
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","done");
    KR_ClaudeProbeLog("END");
    system.Exit(0);
    return 0;
}
string KR_ClaudeLabels() {
    return KR_T8DispSaveNo(999)+","+KR_T8DispSaveNo(49)+","+KR_T8DispSaveNo(7);
}
int KR_ClaudeProbeMain() {
    KR_DiagnosticMute();
    PassRegister.SetFileName(0,"NightRAFCGMode.asd");
    PassRegister.SetFileName(1,"NightRAFMemMode.asd");
    PassRegister.SetFileName(2,"NightRAFBGMMode.asd");
    string save="NightR999.asd";
    string marker="";
    if(TextFile.ReadAll("auto_probe_resume.txt",marker)) save="NightR49.asd";
    KR_ClaudeProbeLog("resume loading "+save);
    system.ResumeLoad("@@KEY@@",save);
    system.Exit(2);return 2;
}
'''
def build_probe(source,m,key):
    src=source/'NightRemaster.ain'
    jaf=audio.JAF+'\n'+AUTO_JAF.replace('@@KEY@@',key)
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
                    assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait);struct.pack_into('<Hi',rawa,16+ad,0x30,ids['KR_ClaudeAutoWait']);n+=1
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]));return n

def main(save='NightR999.asd'):
    source=e.O;stamp=datetime.datetime.now().strftime('%H%M%S')
    c.O=source;c.ROOT=e.O/'autosave_probe';c.BOOT='NightRemasterClaudeAuto';c.SAVEDIR=f'SaveData_KR_ClaudeAutoSaveProbe_20260924_{stamp}';c.SAVES=p.SAVE.parent/c.SAVEDIR
    assert not c.SAVES.exists();c.ROOT.mkdir(parents=True,exist_ok=True)
    for f in c.ROOT.glob('auto_probe_*'):f.unlink()
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    m=b.read_meta(source/'candidate_meta.json');n=build_probe(source,m,key)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(source/'NightRemaster.ain'),source_sha256=e.h(source/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),
        audio=audio.POLICY,input=f'Resume of a copied {save} (the user\'s Monday autosave); every WaitForClick call ({n}) runs the autosave stages; launch B resumes the weekly autosave.',
        save_folder=c.SAVEDIR,author=e.AUTHOR),indent=2,ensure_ascii=False),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    for x in ['NightRemasterEX.ex']:shutil.copy2(source/x,c.ROOT/x);shutil.copy2(source/x,c.ROOT/x.replace('NightRemaster',c.BOOT,1))
    shutil.copy2(p.SAVE/save,c.SAVES/save);user_copy=e.h(c.SAVES/save)
    slots=lambda:sorted(x for x in c.SAVES.iterdir() if re.fullmatch(r'NightR\d+\.asd',x.name))
    assert [x.name for x in slots()]==[save],'probe SaveFolder must hold only the copied autosave'
    marker=c.ROOT/'auto_probe_resume.txt'
    if marker.exists():marker.rename(c.ROOT/f'auto_probe_resume_{stamp}.old')
    result=dict(save=save,save_folder=c.SAVEDIR,wait_sites=n)
    for launch in ['A','B']:
        log=c.ROOT/'claude_probe.txt'
        if log.exists():log.rename(c.ROOT/f'claude_probe_{stamp}_{launch}_prev.txt')
        if launch=='B':marker.write_text('resume weekly\n','ascii')
        res=c.launch(timeout=240)
        res['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else []
        result[launch]=res
        if launch=='A':
            files={x.name:dict(sha256=e.h(x),size=x.stat().st_size) for x in slots()}
            result['files_after_A']=files;result['user_copy_sha256']=user_copy
            if 'NightR49.asd' in files:
                rec=q.records(c.SAVES/'NightR49.asd');result['weekly_stack']=[rr.get('name','') for rr in rec['returns']]
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image
    for pth in c.ROOT.glob('auto_probe_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    (c.ROOT/'autosave_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    for k in ['A','B']:print(k,{x:y for x,y in result[k].items() if x not in ('events','log')},len(result[k].get('events',[])));print('\n'.join(result[k]['log']))
    print('files',result.get('files_after_A'));print('weekly stack',result.get('weekly_stack'))
if __name__=='__main__':main(*sys.argv[1:])
