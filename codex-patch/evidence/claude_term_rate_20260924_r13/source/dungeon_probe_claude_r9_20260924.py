"""Claude Opus 5.5 (2026-09-24) r9: the r8 probe run unchanged against the r9 candidate. Claude Opus 5.5 (2026-09-24) r8: unchanged r7 probe run against the r9 candidate. Claude Opus 5.5 (2026-09-24) r7 (staged EX; logs the renamed monsters as the engine loads them). r6: isolated, muted screenshots of the coloured result texts in a real dungeon view;
shot 3 is a sweep report whose fixed carry-limit line is replaced from recorded losses (records set directly,
the recorder itself is covered by the VM check).

Resumes a COPY of a dungeon save made at the dungeon's own save button (the resumed parts keep their saved
state: no tag processing, gold base), so this also checks that the r5 writers switch tags on at runtime.
  shot 0: dungeon as resumed
  shot 1: two treasure lines through KR_ChestShow (prepended colouring) + one trap line through KR_T8TrapNotice
  shot 2: instant-kill receipt through KR_NoticeShow (loot option set in the probe's own flags)
  shot 3: a sweep report text through KR_T8SweepColor in a C_MessageDialog (Create's conditional Tag::set),
          on its own layer as KR_SweepTimedRun does
Nothing is walked, no trap is triggered and no game state is saved.
"""
from pathlib import Path
import json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r9 as e
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
b=e.b;a=e.a;p=e.p;q=e.q
PROBE_JAF=r'''
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
string KR_ProbeMonsterName(int id) { return ""; }
int KR_ClaudeDungeonWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    if(SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Stage")!="") { KR_ClaudeShot("dungeon_probe_9.bmp"); system.Exit(3); return 0; }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","1");
    KR_ClaudeShot("dungeon_probe_0.bmp");
    KR_ClaudeProbeLog("monsters="+KR_ProbeMonsterName(17)+","+KR_ProbeMonsterName(28)+","+KR_ProbeMonsterName(23)+","+KR_ProbeMonsterName(27)+","+KR_ProbeMonsterName(3)+","+KR_ProbeMonsterName(21)+","+KR_ProbeMonsterName(6)+","+KR_ProbeMonsterName(18)+","+KR_ProbeMonsterName(1));
    KR_ChestShow("회복 아이템「회복약」{YORU_KR_JOSA:O} 손에 넣었다");
    KR_ChestShow("요소석「어둠」(레벨 3)을 손에 넣었다");
    KR_T8TrapNotice("이즈미{YORU_KR_JOSA:n} 독에 걸렸다");
    KR_ClaudeProbeLog("line3="+KR_ChestRead(KR_ChestPart("KR_ChestLine3")));
    KR_ClaudeShot("dungeon_probe_1.bmp");
    KR_SetLoot(true);
    KR_NoticeShow("이즈미  레벨업! 12 → 13\n경험치 +1234 / 훈련치 +56 / 달조각 +7");
    KR_ClaudeShot("dungeon_probe_2.bmp");
    int last=AFL_Parts_GetActiveLayer();
    int layer=AFL_Parts_AddLayer(-1);
    C_MessageDialog dlg;
    SystemService.SystemVariable_Set("YoruKR.T8.SweepLost","회복약\n회복약\n");
    SystemService.SystemVariable_Set("YoruKR.T8.SweepStone","적색 요소석(3등급)\n적색 요소석(3등급)\n흑색 요소석(10등급)\n");
    dlg.Create(KR_T8SweepColor("이즈미  Lv 12 → 13  경험치 +1234 / 훈련치 +56\n쿄카  Lv 20 → 20  경험치 +980 / 훈련치 +40\n\n달조각 +5\n적색 요소석(3등급) +1\n소지 한도를 넘은 보상은 제외됩니다.\n잠시 후 다음 날로 진행합니다."));
    KR_ClaudeProbeLog("records after report: ["+SystemService.SystemVariable_Get("YoruKR.T8.SweepLost")+"]");
    Ａ＿全表示(1,0);
    KR_ClaudeShot("dungeon_probe_3.bmp");
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
def enc(z):
    s=json.loads(z[0])
    if any('가'<=ch<='힣' for ch in s):return json.dumps(b.encode(s).decode('cp932'),ensure_ascii=False)
    return z[0]
def main(save='NightR36.asd'):
    source=e.O
    c.O=source;c.ROOT=e.O/'dungeon_probe';c.BOOT='NightRemasterClaudeDungeon';c.SAVEDIR='SaveData_KR_ClaudeDungeonProbe_20260924';c.SAVES=p.SAVE.parent/c.SAVEDIR
    c.ROOT.mkdir(parents=True,exist_ok=True)
    for f in c.ROOT.glob('dungeon_probe_*'):f.unlink()
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    src=source/'NightRemaster.ain';m=b.read_meta(source/'candidate_meta.json')
    jaf=audio.JAF+'\n'+re.sub(r'"(?:[^"\\]|\\.)*"',enc,PROBE_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save))
    (c.ROOT/'probe.jaf').write_text(jaf,'utf8');decl=c.ROOT/'probe_declared.ain';b.cmd('ain','edit','--jaf',c.ROOT/'probe.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',c.ROOT/'probe_declared_meta.json',decl);dm=b.read_meta(c.ROOT/'probe_declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[audio.mute_patch(m)]+audio.scripted_input_patches(m)
    for f in added:
        path=c.ROOT/f"probe_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl)
        if f['name']=='KR_ProbeMonsterName':
            patch.append(f"FUNC {f['index']}\n\t.LOCALREF id\n\tCALLFUNC L_MonsterManager::At\n\tPUSH 26155\n\tCALLMETHOD 0\n\tRETURN\nENDFUNC KR_ProbeMonsterName\n");continue
        patch.append(b.clean(b.native_lower(path.read_text('utf8')),f['name']))
    (c.ROOT/'probe.jam').write_text('\n'.join(patch),'utf8');out=c.ROOT/'NightRemaster.ain';b.cmd('ain','edit','--jam',c.ROOT/'probe.jam','-o',out,decl)
    rawa=bytearray(b.unpack(out.read_bytes()));size=struct.unpack_from('<I',rawa,12)[0];struct.pack_into('<I',rawa,24+size,m['functions'][0]['address'])
    struct.pack_into('<I',rawa,rawa.index(b'MAIN')+4,ids['KR_ClaudeProbeMain'])
    wait=next(f['index'] for f in m['functions'] if f['name']=='AFL_Parts_WaitForClick')
    versions=q.versions(source/'native_raw_code.jam');n=0
    for f in m['functions']:
        for v in [v for v in versions.get(f['index'],[]) if v['start']==f['address']]:
            for ad,op in v['ops']:
                if op==f'CALLFUNC 0x{wait:x}':
                    assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait);struct.pack_into('<Hi',rawa,16+ad,0x30,ids['KR_ClaudeDungeonWait']);n+=1
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]))
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(src),source_sha256=e.h(src),probe_sha256=e.h(out),audio=audio.POLICY,
        input=f'Resume of a copied {save}; the first WaitForClick runs the r5 colour stages; no walking, no save.',author=e.AUTHOR),indent=2),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    for n in ['NightRemasterEX.ex']:shutil.copy2(source/n,c.ROOT/n);shutil.copy2(source/n,c.ROOT/n.replace('NightRemaster',c.BOOT,1))
    shutil.copy2(p.SAVE/save,c.SAVES/save)
    if (c.ROOT/'claude_probe.txt').exists():(c.ROOT/'claude_probe.txt').unlink()
    result=c.launch(timeout=180)
    log=c.ROOT/'claude_probe.txt';result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else []
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image
    for pth in c.ROOT.glob('dungeon_probe_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    result['wait_sites']=n;result['save']=save
    (c.ROOT/'dungeon_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='events'},ensure_ascii=False,indent=1),len(result['events']))
if __name__=='__main__':main(*sys.argv[1:])
