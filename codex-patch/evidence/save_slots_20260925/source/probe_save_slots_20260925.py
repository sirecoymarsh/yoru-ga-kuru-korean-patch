"""Muted, isolated native save/load roundtrip. Never writes the user's saves."""
from pathlib import Path
import datetime,json,re,shutil,sys,zlib,struct
import build_save_slots_20260925 as e
import autosave_probe_claude_r14_20260924 as g
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
from PIL import Image

QA_JAF='''
int KR_SaveProbeCell(ref C_SceneSaveLoadView view,int row,int method) { return 0; }
int KR_SaveProbeField(ref C_SceneSaveLoadView view,int field) { return 0; }
int KR_SaveProbeCount(ref C_SceneSaveLoadView view) { return 0; }
int KR_SaveProbeSelectable(ref C_SceneSaveLoadView view,int row,bool need) { return 0; }
void KR_SaveProbeHover(ref C_SceneSaveLoadView view,int slot) { }
void KR_SaveProbeRows(ref C_SceneSaveLoadView view) {
    int page=KR_SaveProbeField(view,12); int type=KR_SaveProbeField(view,11);
    int count=KR_SaveProbeCount(view);
    if(count!=KR_SaveRows(page)) { KR_ClaudeProbeLog("FAIL row count");system.Exit(61); }
    string row="ROWS page="+("%d" % page)+" type="+("%d" % type)+":";
    for(int i=0;i<count;i++) {
        int slot=KR_SaveProbeCell(view,i,29588);
        int clickable=KR_SaveProbeCell(view,i,29595);
        bool want=KR_T8IsManualSlot(slot);
        if(type==1) want=AFL_GameSave_IsExistFile(slot);
        if(slot!=KR_SaveSlot(page,i) || clickable!=KR_ClaudeB(want)) {
            KR_ClaudeProbeLog("FAIL slot or clickability");system.Exit(62);
        }
        int selected=KR_SaveProbeSelectable(view,i,type==1);
        if((clickable==0 && selected!=-1) || (clickable==1 && selected!=slot)) { KR_ClaudeProbeLog("FAIL keyboard selector");system.Exit(63); }
        row=row+" "+("%d" % slot)+"/"+("%d" % clickable);
    }
    KR_ClaudeProbeLog(row);
    if(type==1 && page==0) KR_SaveProbeHover(view,998);
}
'''

def build_probe(key,jaf):
    b=e.b;src=e.O/'NightRemaster.ain';m=b.read_meta(e.O/'candidate_meta.json');decl=c.ROOT/'probe_declared.ain'
    (c.ROOT/'probe.jaf').write_text(audio.JAF+'\n'+jaf.replace('@@KEY@@',key)+'\n'+QA_JAF,'utf8')
    b.cmd('ain','edit','--jaf',c.ROOT/'probe.jaf','-o',decl,src);b.cmd('ain','dump','-j','-o',c.ROOT/'probe_meta.json',decl)
    dm=b.read_meta(c.ROOT/'probe_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added}
    patches=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    for f in added:
        body=b.clean(b.native_lower(e.textdump(dm,f['index'],decl)),f['name'])
        if f['name']=='KR_SaveProbeCell':body=e.wrapper(dm,f['index'],'\t.LOCALREF view\n\tPUSH 8\n\tX_REF 1\n\t.LOCALREF row\n\tX_REF 1\n\t.LOCALREF method\n\tCALLMETHOD 0\n')
        if f['name']=='KR_SaveProbeField':body=e.wrapper(dm,f['index'],'\t.LOCALREF view\n\t.LOCALREF field\n\tX_REF 1\n')
        if f['name']=='KR_SaveProbeCount':body=e.wrapper(dm,f['index'],'\t.LOCALREF view\n\tPUSH 8\n\tX_REF 1\n\tCALLHLL Array Numof 65538\n')
        if f['name']=='KR_SaveProbeSelectable':body=e.wrapper(dm,f['index'],'\t.LOCALREF view\n\tPUSH 29584\n\t.LOCALREF row\n\t.LOCALREF need\n\tCALLMETHOD 2\n')
        if f['name']=='KR_SaveProbeHover':body=e.wrapper(dm,f['index'],'\t.LOCALREF view\n\tPUSH 29579\n\t.LOCALREF slot\n\tCALLMETHOD 1\n')
        patches.append(body)
    body=e.clean(m,29577,src);pos=body.rfind('\tRETURN\n');body=body[:pos]+'\tPUSHSTRUCTPAGE\n\tCALLFUNC KR_SaveProbeRows\n'+body[pos:];patches.append(body)
    (c.ROOT/'probe.jam').write_text('\n'.join(patches),'utf8');out=c.ROOT/'NightRemaster.ain'
    b.cmd('ain','edit','--jam',c.ROOT/'probe.jam','-o',out,decl)
    raw=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
    struct.pack_into('<I',raw,raw.index(b'MAIN')+4,ids['KR_ClaudeProbeMain'])
    wait=next(f['index'] for f in m['functions'] if f['name']=='AFL_Parts_WaitForClick');v=e.q.versions(e.O/'native_raw_code.jam');sites=0
    for f in m['functions']:
        for version in v.get(f['index'],[]):
            if version['start']!=f['address']:continue
            for ad,op in version['ops']:
                if op==f'CALLFUNC 0x{wait:x}':
                    assert raw[16+ad:22+ad]==struct.pack('<Hi',0x30,wait)
                    struct.pack_into('<Hi',raw,16+ad,0x30,ids['KR_ClaudeAutoWait']);sites+=1
    out.write_bytes(b.pack(raw,src.read_bytes()[:8]));return sites

def main(source_override=None):
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    c.e=e;c.O=e.O;c.ROOT=e.O/('native_probe_'+stamp);c.ROOT.mkdir()
    c.BOOT='NightRemasterSaveCards';c.SAVEDIR='SaveData_KR_SaveCards_'+stamp;c.SAVES=e.p.SAVE.parent/c.SAVEDIR
    g.e=e;g.c=c
    jaf=g.AUTO_JAF.replace('NightR49.asd','NightR998.asd')
    jaf=jaf.replace('AFL_GameSave_IsExistFile(49)','AFL_GameSave_IsExistFile(998)').replace('AFL_GameSave_GetUserComment(49,','AFL_GameSave_GetUserComment(998,').replace('KR_T8DispSaveNo(49)','KR_T8DispSaveNo(998)')
    jaf=jaf.replace('■セーブ／オートセーブ実行(KR_T8WeeklySlot());','SystemService.SystemVariable_Set("YoruKR.Save.WeeklyPending","1");\n    ■セーブ／オートセーブ実行(KR_T8WeeklySlot());')
    jaf=jaf.replace('int t1=system.GetTime();','int t1=system.GetTime();\n    string weekly="";string daily="";AFL_GameSave_GetUserComment(998,weekly);AFL_GameSave_GetUserComment(999,daily);\n    KR_ClaudeProbeLog("WEEKLY_AND_DAILY_MATCH="+("%d" % KR_ClaudeB(weekly==daily))+" SNAPSHOT="+weekly);')
    jaf=jaf.replace('if(page=="0") KR_ClaudeShot(prefix+"_p1.bmp");','KR_ClaudeShot(prefix+"_page"+page+".bmp");')
    jaf=jaf.replace('string c49="";','KR_ClaudeProbeLog("SCENE="+("%d" % KR_SaveScene())+" MAP="+("%d" % KR_SaveMap()));\n    string c49="";')
    jaf=jaf.replace('string c49="";','■セーブ／オートセーブ実行(4);\n    string c49="";')
    source=source_override or ('NightR49.asd' if (e.p.SAVE/'NightR49.asd').exists() else 'NightR999.asd')
    r=e.q.Reader(zlib.decompress((e.p.SAVE/source).read_bytes()[8:]));r.string();r.integer();key=r.string()
    sites=build_probe(key,jaf)
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(e.O/'NightRemaster.ain'),source_sha256=e.h(e.O/'NightRemaster.ain'),probe_sha256=e.h(c.ROOT/'NightRemaster.ain'),audio=audio.POLICY,save_folder=c.SAVEDIR,input='Private copy; native weekly/daily saves; load/save every page; resume newly written 998.',author=e.AUTHOR),indent=2),'utf8')
    before=e.p.snapshot_saves();c.setup_folder()
    shutil.copy2(e.O/'NightRemasterEX.ex',c.ROOT/'NightRemasterEX.ex');shutil.copy2(e.O/'NightRemasterEX.ex',c.ROOT/(c.BOOT+'EX.ex'))
    for slot in [1,4,5,49]:
        for old in e.p.SAVE.glob(f'NightR{slot:02d}.*'):shutil.copy2(old,c.SAVES/old.name)
    shutil.copy2(e.p.SAVE/source,c.SAVES/'NightR999.asd')
    sentinel={x.name:e.h(x) for x in c.SAVES.glob('NightR49.*')}
    result=dict(source_sha256=e.h(e.O/'NightRemaster.ain'),root=str(c.ROOT),save_folder=str(c.SAVES),source_save=source,sites=sites)
    for launch in ['A','B']:
        if launch=='B':(c.ROOT/'auto_probe_resume.txt').write_text('resume\n','ascii')
        log=c.ROOT/'claude_probe.txt'
        if log.exists():shutil.copy2(log,c.ROOT/f'launch_{launch}_previous.txt');log.unlink()
        native=c.launch(timeout=150)
        native['log']=e.b.decode(log.read_bytes()).splitlines() if log.exists() else []
        result[launch]=native
        (c.ROOT/f'launch_{launch}.json').write_text(json.dumps(native,ensure_ascii=False,indent=2),'utf8')
        print(launch,{k:v for k,v in native.items() if k not in ['events','log']},flush=True);print('\n'.join(native['log']),flush=True)
        if native.get('exit_code')!=0 or native.get('events'):break
    for img in c.ROOT.glob('*.bmp'):Image.open(img).save(img.with_suffix('.png'))
    result['manual49_unchanged']=sentinel=={x.name:e.h(x) for x in c.SAVES.glob('NightR49.*')}
    result['real_saves_unchanged']=before==e.p.snapshot_saves()
    assert result['manual49_unchanged'] and result['real_saves_unchanged']
    result['files']={x.name:e.h(x) for x in c.SAVES.glob('NightR[0-9]*.*')}
    (c.ROOT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    e.save('latest_native_probe.json',dict(path=str(c.ROOT/'result.json'),source_sha256=result['source_sha256']))
    print('RESULT',c.ROOT/'result.json',flush=True)
if __name__=='__main__':main(*sys.argv[1:])
