"""Claude Opus 5.5 (2026-09-24): native UI screenshots for the Codex review CT-RATE-002 (and layout preservation).

Same technique as Codex's review (reviews/claude_term_rate_20260924_codex): muted isolated engine, the single
AFL_Parts_WaitForClick inside C_SelectDialog@Run replaced by a scripted chooser that saves a screenshot first.
Runs the installed first overlay ('prev') and the r2 candidate under identical fixtures; user saves read-only.
"""
from pathlib import Path
import json,shutil,struct,sys
import build_claude_term_rate_20260924 as e
import probe_claude_term_rate_20260924 as c
b=e.b;a=e.a
PREV=e.R/'staging/claude_term_rate_20260924'
OUT=e.O/'ui_probe'
UI_JAF=r'''
void KR_ReviewLog(string text) {
    string all=SystemService.SystemVariable_Get("YoruKR.Review.Log")+text+"\n";
    SystemService.SystemVariable_Set("YoruKR.Review.Log",all);TextFile.WriteAll("review_ui.txt",all);
}
int KR_ReviewChoice(FTPARTS_WaitForClickCallback func,bool cancel) {
    string value=SystemService.SystemVariable_Get("YoruKR.Review.Choice");int n=value.ToInt();
    SystemService.SystemVariable_Set("YoruKR.Review.Choice","%d"%(n+1));
    AFL_View_Update();AFL_View_Update();
    if(!SystemService.SaveScreenshot("review_ui_"+("%d"%n)+".bmp",0,0,1280,720)) system.Exit(9);
    KR_ReviewLog("SHOT "+("%d"%n));
    if(n==2) return 2;
    if(n>5) system.Exit(10);
    return 0;
}
int KR_UIEvents(int g) {
    if(g==0) return @@STORY@@;
    if(g==1) return @@TRAINING@@;
    if(g==2) return @@INVITE@@;
    return @@WALK@@;
}
void KR_UISynthetic() {
    ■選択ダイアログ／初期化();
    ■選択ダイアログ／タイプ設定(2026091602);
    ■選択ダイアログ／クリック制限／全体();
    ■選択ダイアログ／横項目数(1);
    ■選択ダイアログ／タイトル設定("형식 확인\n둘째 줄\n셋째 줄\n넷째 줄\n다섯째 줄\n여섯째 줄");
    ■選択ダイアログ／選択肢追加(0,"닫기","",false);
    ■選択ダイアログ／実行(true,200);
}
void KR_ClaudeProbe() {
    KR_DiagnosticMute();KR_TermLoad();C_UserInputManager::Init();
    KR_ReviewLog("BEGIN");
    KR_UISynthetic();
    KR_TermMenu();
    KR_PlayerInfoMenu();
    KR_T8EventDetail(@@STORY@@,@@TRAINING@@,@@INVITE@@,@@WALK@@);
    KR_ReviewLog("END");system.Exit(0);
}
'''
VARIANTS={
 # real global records copied from the user's save folder; per-save state synthetic
 'real':dict(events=(0,0,0,0),name='료',consts={}),
 # zero everything
 'zero':dict(events=(0,0,0,0),name='료',consts={'KR_T8ReadCount':0,'KR_T8CgCount':0,'KR_T8SceneCount':0,'Ａ＿回想確認':0}),
 # everything reached, all ending names shown, longest (5 syllable) protagonist name
 'full':dict(events=(398,362,42,241),name='가나다라마',consts={'KR_T8ReadCount':74966,'KR_T8CgCount':60,'KR_T8SceneCount':66,'Ａ＿回想確認':1}),
}
def run(label,source,variant):
    v=VARIANTS[variant];c.O=source;c.ROOT=OUT/f'{label}_{variant}';c.BOOT='NightRemasterClaudeUI';c.SAVEDIR='SaveData_KR_ClaudeUIProbe_20260924';c.SAVES=e.p.SAVE.parent/c.SAVEDIR
    c.ROOT.mkdir(parents=True,exist_ok=True)
    for f in c.ROOT.glob('review_ui_*'):f.unlink()
    jaf=UI_JAF
    for k,x in zip(['@@STORY@@','@@TRAINING@@','@@INVITE@@','@@WALK@@'],v['events']):jaf=jaf.replace(k,str(x))
    c.PROBE_JAF=jaf
    before=e.p.snapshot_saves();ptr=a.readj(e.R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);installed={n:e.h(rt/n) for n in e.FILES}
    c.build_probe();c.setup_folder()
    if (c.ROOT/'review_ui.txt').exists():(c.ROOT/'review_ui.txt').unlink()
    m=b.read_meta(c.ROOT/'probe_declared_meta.json')
    def uname(s):  # meta keeps raw cp932 bytes as surrogate escapes
        try:return s.encode('utf-8','surrogateescape').decode('cp932')
        except UnicodeDecodeError:return s
    by={}
    for f in m['functions']:by.setdefault(uname(f['name']),f['index'])
    patches=[f"FUNC {by['KR_PlayerReady']}\n\tPUSH 1\n\tRETURN\nENDFUNC KR_PlayerReady\n",
             f"FUNC {by['KR_PlayerEventCount']}\n\t.LOCALREF group\n\tCALLFUNC KR_UIEvents\n\tRETURN\nENDFUNC KR_PlayerEventCount\n",
             f"FUNC {by['LAbility::GetPlayerName']}\n\tS_PUSH "+json.dumps(b.encode(v['name']).decode('cp932'),ensure_ascii=False)+"\n\tRETURN\nENDFUNC LAbility::GetPlayerName\n"]
    for name,x in v['consts'].items():patches.append(f"FUNC {by[name]}\n\tPUSH {x}\n\tRETURN\nENDFUNC {name}\n")
    patch=c.ROOT/'ui_fixture.jam';patch.write_text('\n'.join(patches),'utf8');tmp=c.ROOT/'ui_fixture.ain'
    b.cmd('ain','edit','--jam',patch,'-o',tmp,c.ROOT/'NightRemaster.ain')
    raw=bytearray(b.unpack(tmp.read_bytes()));size=struct.unpack_from('<I',raw,12)[0];struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
    start=m['functions'][27928]['address'];end=m['functions'][27929]['address'];needle=struct.pack('<Hi',0x30,by['AFL_Parts_WaitForClick'])
    part=raw[16+start:16+end];assert part.count(needle)==1
    struct.pack_into('<Hi',raw,16+start+part.index(needle),0x30,by['KR_ReviewChoice'])
    out=c.ROOT/'NightRemaster.ain';out.write_bytes(b.pack(bytes(raw),tmp.read_bytes()[:8]))
    mp=c.ROOT/'weapon_probe_manifest.json';mf=a.readj(mp);mf.update(probe_sha256=e.h(out),author=e.AUTHOR,input=f'UI-only fixture {variant}: synthetic Ready/event counters/name/consts; native menus and layout, scripted choices.')
    mp.write_text(json.dumps(mf,ensure_ascii=False,indent=2),'utf8')
    result=c.launch(timeout=120)
    log=c.ROOT/'review_ui.txt';result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else []
    result['source_sha256']=e.h(source/'NightRemaster.ain');result['variant']=variant
    result['user_saves_unchanged']=e.p.snapshot_saves()==before;result['installed_files_unchanged']=all(e.h(rt/n)==h for n,h in installed.items())
    from PIL import Image
    for pth in c.ROOT.glob('review_ui_*.bmp'):Image.open(pth).save(pth.with_suffix('.png'));pth.unlink()
    assert result['user_saves_unchanged'] and result['installed_files_unchanged'],result
    return result

def main():
    OUT.mkdir(exist_ok=True);results={}
    for label,source in [('prev',PREV),('r2',e.O)]:
        for variant in (['real'] if label=='prev' else ['real','zero','full']):
            results[f'{label}_{variant}']=run(label,source,variant)
    (OUT/'ui_probe_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({k:dict(exit=r.get('exit_code'),timeout=r.get('timeout'),events=len(r['events']),vm_error=r.get('vm_error'),log=r['log']) for k,r in results.items()},ensure_ascii=False,indent=1))
if __name__=='__main__':main()
