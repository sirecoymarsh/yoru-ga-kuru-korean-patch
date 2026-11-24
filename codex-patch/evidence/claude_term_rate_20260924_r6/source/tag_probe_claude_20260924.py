"""Claude Opus 5.5 (2026-09-24): isolated, muted experiment - do ${font r= g= b=}...${/font} tags render in
(a) Codex's dungeon notice lines once tag processing is enabled at runtime, and do colours survive the line
shift (KR_ChestRead -> KR_ChestWrite), (b) the loot receipt, (c) a C_MessageDialog (sweep report) as created
today (no change). Resumes a COPY of a dungeon save; nothing is walked or saved. Experiment only, not a build.
"""
from pathlib import Path
import json,re,shutil,struct,sys,zlib
import build_claude_term_rate_20260924_r4 as e
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
void KR_ClaudeTags(string key) {
    int part=KR_ChestPart(key);
    KR_ClaudeProbeLog(key+"="+("%d" % part));
    if(part<0) return;
    Ｐ＿テキストタグ有効設定(part,true,1);
    Ｐ＿フォント色設定(part,255,255,255,1);
}
int KR_ClaudeTagWait(FTPARTS_WaitForClickCallback func,bool cancel) {
    if(SystemService.SystemVariable_Get("YoruKR.ClaudeProbe.Stage")!="") { KR_ClaudeShot("tag_probe_9.bmp"); system.Exit(3); return 0; }
    SystemService.SystemVariable_Set("YoruKR.ClaudeProbe.Stage","1");
    KR_ClaudeTags("KR_ChestLine1");KR_ClaudeTags("KR_ChestLine2");KR_ClaudeTags("KR_ChestLine3");
    KR_ChestShow("회복 아이템「${font r=96 g=255 b=128}회복약${/font}」을 손에 넣었다");
    KR_ChestShow("${font r=255 g=112 b=96}함정 해제 실패${/font}");
    KR_ChestShow("요소석「${font r=176 g=112 b=255}어둠${/font}」(레벨 ${font r=96 g=224 b=255}3${/font})을 손에 넣었다");
    KR_ClaudeShot("tag_probe_0.bmp");
    KR_ChestShow("${font r=128 g=255 b=128}함정 해제 성공 · 피해 없음${/font}");
    KR_ClaudeProbeLog("line1 after shift: "+KR_ChestRead(KR_ChestPart("KR_ChestLine1")));
    KR_ClaudeShot("tag_probe_1.bmp");
    KR_SetLoot(true);
    KR_ClaudeTags("KR_ReceiptBody");
    KR_NoticeShow("적 3체 처치  ${font r=255 g=224 b=96}레벨업!${/font} 12 → 13\n경험치 ${font r=96 g=224 b=255}+1234${/font} / 훈련치 ${font r=128 g=255 b=128}+56${/font}");
    KR_ClaudeShot("tag_probe_2.bmp");
    int last=AFL_Parts_GetActiveLayer();
    int layer=AFL_Parts_AddLayer(-1);
    C_MessageDialog dlg;
    dlg.Create("소탕 결과\n${font r=255 g=224 b=96}회복약${/font} ${font r=96 g=224 b=255}+3${/font}\n경험치 +100");
    Ａ＿全表示(1,0);
    KR_ClaudeShot("tag_probe_3.bmp");
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
    c.O=source;c.ROOT=e.O/'tag_probe';c.BOOT='NightRemasterClaudeTag';c.SAVEDIR='SaveData_KR_ClaudeTagProbe_20260924';c.SAVES=p.SAVE.parent/c.SAVEDIR
    c.ROOT.mkdir(parents=True,exist_ok=True)
    for f in c.ROOT.glob('tag_probe_*'):f.unlink()
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    src=source/'NightRemaster.ain';m=b.read_meta(source/'candidate_meta.json')
    jaf=audio.JAF+'\n'+re.sub(r'"(?:[^"\\]|\\.)*"',enc,PROBE_JAF.replace('@@KEY@@',key).replace('@@SAVE@@',save))
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
                    assert rawa[16+ad:16+ad+6]==struct.pack('<Hi',0x30,wait);struct.pack_into('<Hi',rawa,16+ad,0x30,ids['KR_ClaudeTagWait']);n+=1
    out.write_bytes(b.pack(bytes(rawa),src.read_bytes()[:8]))
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(src),source_sha256=e.h(src),probe_sha256=e.h(out),audio=audio.POLICY,
        input=f'Resume of a copied {save}; tag rendering experiment; no walking, no save.',author=e.AUTHOR),indent=2),'utf8')
    before=p.snapshot_saves()
    c.setup_folder()
    shutil.copy2(p.SAVE/save,c.SAVES/save)
    if (c.ROOT/'claude_probe.txt').exists():(c.ROOT/'claude_probe.txt').unlink()
    result=c.launch(timeout=180)
    log=c.ROOT/'claude_probe.txt';result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else []
    assert p.snapshot_saves()==before,'user save folder changed'
    from PIL import Image
    for pth in c.ROOT.glob('tag_probe_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    (c.ROOT/'tag_probe_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='events'},ensure_ascii=False,indent=1),len(result['events']))
if __name__=='__main__':main(*sys.argv[1:])
