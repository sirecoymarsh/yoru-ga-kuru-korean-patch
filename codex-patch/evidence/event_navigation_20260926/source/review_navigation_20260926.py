"""Current-build navigation review. Private saves, muted, no live-file writes."""
from pathlib import Path
import datetime,json,shutil,struct,sys,zlib
import build_story_progress_20260926 as e
import floor_probe_claude_r14_20260924 as f
import probe_claude_term_rate_20260924 as c
import diagnostic_audio_20260923 as audio
b=e.b;p=e.p;q=e.q
O=e.R/'staging/navigation_review_20260926'
EXPECTED='dc34355abbdf7753821ef834f3b44b8cf76f9d00d8ab226350c150a1e569c759'
EXTRA=r'''
void KR_RVRead(ref C_SceneDungeon scene) { return; }
void KR_RVGrid(ref C_MapInfo map,ref C_SceneDungeonMiniMapView view,ref C_SceneDungeon scene) {
    int mode=KR_ExploreMap(scene);
    KR_ClaudeProbeLog("VALID="+("%d"%KR_FPB(KR_WalkValid(scene)))+" ROUTE="+("%d"%KR_FPB(KR_GetRoute())));
    for(int y=0;y<30;y++) {
        string row="GRID "+("%d"%y)+":";
        for(int x=0;x<30;x++) row=row+("%d"%KR_PuzzleCell(map,x,y))+",";
        KR_ClaudeProbeLog(row);
        row="SEEN "+("%d"%y)+":";
        for(int x=0;x<30;x++) row=row+("%d"%KR_ExploreCell(scene,x,y))+",";
        KR_ClaudeProbeLog(row);
    }
    array<CASPos> route;
    KR_SetRoute(true);KR_Poke(89,0);
    KR_DrawRoute(map,view,KR_WalkX(),KR_WalkY());
    KR_ExploreGuidedPlan(scene,route);
    KR_ClaudeProbeLog("GUIDED="+("%d"%KR_WalkRouteCount(route))+" valid="+("%d"%KR_FPB(KR_WalkPathValid(scene,route))));
    for(int i=0;i<KR_WalkRouteCount(route);i++) KR_ClaudeProbeLog("POINT "+("%d"%KR_WalkPoint(route,i,0))+","+("%d"%KR_WalkPoint(route,i,1)));
    KR_ClaudeShot("navigation_guided.bmp");
    route.Free();KR_SetRoute(false);KR_Poke(89,0);
    KR_ExplorePlan(scene,route);
    KR_ClaudeProbeLog("UNGUIDED="+("%d"%KR_WalkRouteCount(route))+" valid="+("%d"%KR_FPB(KR_WalkPathValid(scene,route))));
    KR_SetRoute(true);
    bool guided=KR_ExploreStart(scene);
    KR_ClaudeProbeLog("START_GUIDED="+("%d"%KR_FPB(guided))+" queue="+("%d"%KR_WalkCount(scene)));
    KR_ExploreStop(scene);KR_SetRoute(false);
    bool nearby=KR_ExploreStart(scene);
    KR_ClaudeProbeLog("START_UNGUIDED="+("%d"%KR_FPB(nearby))+" queue="+("%d"%KR_WalkCount(scene)));
    KR_ExploreStop(scene);
    KR_ClaudeProbeLog("END");system.Exit(0);
}
'''

def prepare():
    ptr=e.a.readj(e.R/'ui_cumulative/current.json');rt=Path(ptr['runtime'])
    assert e.h(rt/'NightRemaster.ain')==EXPECTED
    O.mkdir(exist_ok=True)
    for name in ['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']:
        dest=O/name
        if not dest.exists():shutil.copy2(rt/name,dest)
        assert e.h(dest)==e.h(rt/name)
    for name in ['candidate_meta.json','native_raw_code.jam']:
        if not (O/name).exists():shutil.copy2(e.O/name,O/name)
    out=O/'source_pointer.json'
    if not out.exists():out.write_text(json.dumps(ptr,ensure_ascii=False,indent=2),'utf8')
    assert e.a.readj(out)==ptr

def main(save='NightR45.asd',source=None,walk=False):
    prepare();source=Path(source) if source else O
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    c.e=e;c.O=source;c.ROOT=O/f'probe_{save[:-4]}_{stamp}';c.BOOT='NightRemasterNavigation'
    c.SAVEDIR='SaveData_KR_Navigation_'+stamp;c.SAVES=p.SAVE.parent/c.SAVEDIR
    c.ROOT.mkdir();assert not c.SAVES.exists()
    raw=zlib.decompress((p.SAVE/save).read_bytes()[8:]);r=q.Reader(raw);r.string();r.integer();key=r.string()
    m=b.read_meta(source/'candidate_meta.json')
    original=f.FP_JAF
    if not walk:
        start=original.index('    string stage=KR_FPGet("Stage");',original.index('void KR_FloorProbeGuard'))
        end=original.index('\nint KR_FloorProbeDialog',start)
        f.FP_JAF=original[:start]+'\n    KR_ClaudeProbeLog("RESUMED "+KR_FPState(scene));\n    KR_RVRead(scene);\n}\n'+original[end:]+EXTRA
    else:
        f.FP_JAF=original.replace('KR_SetLoot(true); KR_SetTrap(true);','KR_SetLoot(true); KR_SetTrap(true); KR_SetRoute(true);')
    info=f.build_probe(source,m,key,save);f.FP_JAF=original
    out=c.ROOT/'NightRemaster.ain'
    if not walk:
        dm=b.read_meta(c.ROOT/'probe_declared_meta.json');ids={x['name']:x['index'] for x in dm['functions']}
        patch=e.wrapper(dm,ids['KR_RVRead'],'\t.LOCALREF scene\n\tPUSH 6\n\tX_REF 1\n\t.LOCALREF scene\n\tPUSH 2\n\tX_REF 1\n\tPUSH 3\n\tX_REF 1\n\t.LOCALREF scene\n\tCALLFUNC KR_RVGrid\n')
        (c.ROOT/'bridge.jam').write_text(patch,'utf8');bridge=c.ROOT/'bridged.ain'
        b.cmd('ain','edit','--jam',c.ROOT/'bridge.jam','-o',bridge,out)
        raw=bytearray(b.unpack(bridge.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
        struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);struct.pack_into('<I',raw,raw.index(b'MAIN')+4,ids['KR_ClaudeProbeMain'])
        # Compiler's generic ref-array subtype must match original CASPos ownership ABI.
        at=raw.index(b'KR_RVGrid\0');pos=raw.index(b'route\0\0',at)+7
        vals=struct.unpack_from('<7i',raw,pos);assert vals==(79,13,1,13,514,0,0),vals
        struct.pack_into('<7i',raw,pos,79,514,1,13,514,0,0)
        out.write_bytes(b.pack(raw,out.read_bytes()[:8]))
    (c.ROOT/'weapon_probe_manifest.json').write_text(json.dumps(dict(source=str(source/'NightRemaster.ain'),source_sha256=e.h(source/'NightRemaster.ain'),probe_sha256=e.h(out),audio=audio.POLICY,input='Private saved state; input disabled; read-only planners and screenshots, then exit.' if not walk else 'Private save; guided auto exploration; time 999, instant enemy/trap options only in private memory.',hooks=info['hooks'],save_folder=c.SAVEDIR,author='Codex internal'),indent=2),'utf8')
    before=p.snapshot_saves();c.setup_folder();shutil.copy2(p.SAVE/save,c.SAVES/save)
    result=c.launch(timeout=150);log=c.ROOT/'claude_probe.txt'
    result['log']=b.decode(log.read_bytes()).splitlines() if log.exists() else []
    result.update(save=save,real_saves_unchanged=p.snapshot_saves()==before)
    assert result['real_saves_unchanged']
    from PIL import Image
    for path in c.ROOT.glob('*.bmp'):Image.open(path).save(path.with_suffix('.png'))
    (c.ROOT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print(c.ROOT);print(json.dumps({k:v for k,v in result.items() if k not in ['events','log']},ensure_ascii=False))
    print('\n'.join(l for l in result['log'] if not l.startswith(('GRID','SEEN','STEP'))))
if __name__=='__main__':main(*sys.argv[1:])
