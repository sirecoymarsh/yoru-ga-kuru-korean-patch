"""Immutable inputs for separating story milestones from event collection."""
import json,shutil
from pathlib import Path
import build_save_slots_20260925 as base
b=base.b;p=base.p;q=base.q;a=base.a;R=base.R
O=R/'staging/story_progress_20260926';S=O/'source'
EXPECTED='18f9713ebff1d6126db39b906fee7175ba874d217f79993763a377484ab3e54e'
FILES=['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']
def main():
    ptr=a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime'])
    assert base.h(rt/'NightRemaster.ain')==EXPECTED
    O.mkdir(exist_ok=True);S.mkdir(exist_ok=True)
    for name in FILES:
        dst=S/name
        if not dst.exists():shutil.copy2(rt/name,dst)
        assert base.h(dst)==base.h(rt/name)
    if not (S/'current.json').exists():(S/'current.json').write_text(json.dumps(ptr,ensure_ascii=False,indent=2),'utf8')
    else:assert a.readj(S/'current.json')==ptr
    for name in ['candidate_meta.json','native_raw_code.jam']:
        if not (S/name).exists():shutil.copy2(base.O/name,S/name)
    m=b.read_meta(S/'candidate_meta.json')
    ids=[26436,26438,27495,30089,32171,32290,32346,32347]
    ids += [f['index'] for f in m['functions'] if 'KR_T8' in f['name'] and any(x in f['name'] for x in ['Info','HomeHit','HomeClick','HomePanel','HomeRate'])]
    for fid in sorted(set(ids)):
        out=O/f'f{fid}.jam'
        if not out.exists():out.write_text(base.textdump(m,fid,S/'NightRemaster.ain'),'utf8')
    print('source prepared',O)
    for fid in [32171,32290,27495,30089]:print((O/f'f{fid}.jam').read_text('utf8'))
if __name__=='__main__':main()
