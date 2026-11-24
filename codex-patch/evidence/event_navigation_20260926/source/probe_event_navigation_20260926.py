"""Muted copy-save evidence for event goals; never skips/answers a player's story."""
import sys
import build_event_navigation_20260926 as e
import review_navigation_20260926 as r

def main(mode='read45'):
    # Reuse the audited private probe harness, but source the current candidate.
    def prepared():
        assert e.a.readj(e.R/'ui_cumulative/current.json')==e.a.readj(e.S/'source_pointer.json')
        assert e.h(e.O/'NightRemaster.ain')==e.a.readj(e.O/'build_evidence.json')['files']['NightRemaster.ain']
    r.prepare=prepared;r.O=e.O
    save='NightR45.asd' if mode.endswith('45') else 'NightR36.asd'
    walk=mode.startswith('walk')
    if mode=='walk45':
        original=r.f.FP_JAF
        at=original.index('void KR_FloorProbeMsgNote() {')
        end=original.index('// hand-written body:',at)
        r.f.FP_JAF=original[:at]+'''void KR_FloorProbeMsgNote() {
    KR_ClaudeProbeLog("NATIVE STORY at "+("%d"%KR_WalkX())+","+("%d"%KR_WalkY())+" own="+("%d"%KR_FPB(KR_WalkOwn())));
    KR_ClaudeShot("native_story_boundary.bmp");
    if(KR_WalkX()!=1 || KR_WalkY()!=16) { KR_ClaudeProbeLog("FAIL unexpected story position");system.Exit(81);return; }
    KR_ClaudeProbeLog("PASS native movement reached original story; no dialogue/party choice answered");
    KR_ClaudeProbeLog("END");system.Exit(0);
}
'''+original[end:]
    r.main(save,e.O,walk)
if __name__=='__main__':main(*sys.argv[1:])
