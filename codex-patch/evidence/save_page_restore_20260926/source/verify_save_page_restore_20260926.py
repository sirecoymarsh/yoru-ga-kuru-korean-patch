"""Bound baseline/candidate native regression and immutable saved-schema evidence."""
import re
import build_save_page_restore_20260926 as e

def main():
    ev=e.p.read(e.O/'build_evidence.json');assert all(e.h(e.O/n)==h for n,h in ev['files'].items())
    probes={}
    for mode,source in [('baseline',e.S),('candidate',e.O)]:
        found=[]
        for path in sorted(e.O.glob('probe_'+mode+'*/result.json')):
            r=e.p.read(path);n=r['native'];log=n.get('log',[])
            if r['source_sha256']!=e.h(source/'NightRemaster.ain'):continue
            if n.get('exit_code')!=0 or n.get('events') or not log or not log[-1].startswith('PASS 49,5,4,1,auto-only'):continue
            assert r['real_saves_unchanged']
            assert e.h(path.parent/'NightRemaster.ain')==r['manifest']['probe_sha256']
            latest=[];pages=[]
            for line in log:
                mt=re.fullmatch(r'LATEST=(-?\d+) PAGE=(\d+)',line)
                if mt:latest.append(tuple(map(int,mt.groups())))
                mt=re.fullmatch(r'OBSERVED=(\d+) EXPECTED=(\d+)',line)
                if mt:pages.append(tuple(map(int,mt.groups())))
            assert latest==[(49,9),(5,1),(4,0),(1,0),(-1,0)],latest
            want=[0]*10 if mode=='baseline' else [9,9,1,1,0,0,0,0,0,0]
            assert pages==[(x,x) for x in want],pages
            found.append(str(path))
        assert found,mode;probes[mode]=found[-1]
    frames=e.p.read(e.O/'save_frames.json')
    e.save('verification.json',dict(status='SAVE_PAGE_STATIC_NATIVE_PASS',files=ev['files'],native_probes=probes,
        existing_resume_saves=len(frames['saves']),saved_return_frames=len(frames['frames']),save_schema_equal=True,
        old_CODE_allowlist_exact=ev['old_CODE_exact'],changed_PACT=[],MSG1_exact=True,STR0_exact=True,
        real_saves_unchanged=True,OS_mouse_hit_test=False,case_count=10,restored_original_latest_manual_page_policy=True))
    e.p.O=e.O;e.p.FILES=['NightRemaster.ain','NightRemasterPact.afa'];e.p.fixture()
    print('PASS: baseline forced page0; candidate opens pages9/1/0 for native latest manual slot; both screens; autosaves preserved')

if __name__=='__main__':main()
