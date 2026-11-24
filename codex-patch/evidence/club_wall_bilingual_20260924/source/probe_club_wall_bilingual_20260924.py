"""Muted, private engine render of the five final archive members; no gameplay/save loading."""
import json, shutil, os
from pathlib import Path
import numpy as np
from PIL import Image
import build_claude_term_rate_20260924_r6 as e
import probe_claude_term_rate_20260924 as c
from build_club_wall_bilingual_20260924 import O, h, js, IDS

JAF=r'''
void KR_ClaudeProbeLog(string text) {
    string all=SystemService.SystemVariable_Get("Codex.Graphics.Log")+text+"\n";
    SystemService.SystemVariable_Set("Codex.Graphics.Log",all);
    TextFile.WriteAll("claude_probe.txt",all);
}
void KR_GraphicsShot(string name) {
    int part=PartsEngine.GetFreeNumber();
    if(!PartsEngine.Parts_SetPartsCG(part,name,0,1)) {KR_ClaudeProbeLog("FAIL CG "+name);system.Exit(4);}
    PartsEngine.SetComponentPosZ(part,2000000);
    PartsEngine.SetComponentPos(part,160.0,64.0);
    PartsEngine.SetComponentShow(part,true);
    AFL_View_Update();AFL_View_Update();AFL_View_Update();
    if(!SystemService.SaveScreenshot(name+".bmp",0,0,1280,720)) system.Exit(5);
    KR_ClaudeProbeLog("SHOT "+name);
    PartsEngine.Release(part);
}
void KR_ClaudeProbe() {
    KR_DiagnosticMute();
    KR_GraphicsShot("CG4014");KR_GraphicsShot("CG4013");KR_GraphicsShot("CG5070");
    KR_GraphicsShot("CG1541");KR_GraphicsShot("CG1542");
    KR_ClaudeProbeLog("END");system.Exit(0);
}
'''

def main():
    ev=json.loads((O/'build_evidence.json').read_text('utf8'));assert h(e.O/'NightRemaster.ain')==ev['source_files']['NightRemaster.ain']
    c.e=e;c.O=e.O;c.ROOT=O/'native_final';c.BOOT='NightRemasterWallBilingualFinal';c.SAVEDIR='SaveData_KR_WallBilingualFinal_20260924';c.SAVES=e.p.SAVE.parent/c.SAVEDIR
    c.PROBE_JAF=JAF;before=e.p.snapshot_saves();c.build_probe();c.setup_folder()
    # Atomic replacement of the private hardlinks, not writes through to the game.
    for n in ['NightRemasterCG.afa',c.BOOT+'CG.afa']:
        temp=c.ROOT/(n+'.incoming');shutil.copy2(O/'NightRemasterCG.afa',temp);os.replace(temp,c.ROOT/n)
        assert h(c.ROOT/n)==ev['files']['NightRemasterCG.afa']
    result=c.launch(timeout=80);result['log']=(c.ROOT/'claude_probe.txt').read_text('ascii').splitlines() if (c.ROOT/'claude_probe.txt').exists() else []
    result['candidate_files']=ev['files'];result['save_files_unchanged']=before==e.p.snapshot_saves();js(O/'native_result.json',result)
    assert result.get('exit_code')==0 and not result['events'] and not result.get('message') and not result.get('vm_error') and not result.get('timeout'),result
    assert result['save_files_unchanged'];matches=[]
    for r in ev['records']:
        name=r['archive_name'].split('.')[0];im=Image.open(c.ROOT/(name+'.bmp')).convert('RGB');im.save(c.ROOT/(name+'.png'))
        a=np.array(Image.open(O/f"{r['id']}_reopened.png").convert('RGBA'));s=np.array(im)[64:64+a.shape[0],160:160+a.shape[1]]
        opaque=a[:,:,3]==255;delta=np.max(np.abs(s.astype('int16')-a[:,:,:3].astype('int16')),axis=2)
        fraction=float(np.mean(delta[opaque]<=1));matches.append(dict(id=r['id'],opaque_pixel_match=fraction,screenshot=str(c.ROOT/(name+'.png'))))
        assert fraction>.995,(r['id'],fraction)
    js(O/'native_matches.json',dict(status='ENGINE_RENDER_PASS',files=ev['files'],matches=matches,scope='Private native CG loader and renderer, not full battle animation or story playback; mute instrumented.'))
    print(json.dumps(result,ensure_ascii=False));print(matches)

if __name__=='__main__':main()
