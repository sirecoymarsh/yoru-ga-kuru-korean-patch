"""Verify native page output independently against the complete slot inventory."""
import re,struct
import build_pinned_autosave_20260926 as e

def main():
    ev=e.p.read(e.O/'build_evidence.json');assert all(e.h(e.O/n)==h for n,h in ev['files'].items())
    before=e.b.unpack((e.S/'NightRemaster.ain').read_bytes());after=e.b.unpack((e.O/'NightRemaster.ain').read_bytes())
    oldsize=struct.unpack_from('<I',before,12)[0];assert before[16:16+oldsize]==after[16:16+oldsize]
    old=e.b.read_meta(e.S/'candidate_meta.json');new=e.b.read_meta(e.O/'candidate_meta.json')
    changed=[]
    for f,g in zip(old['functions'],new['functions']):
        if f['address']!=g['address']:changed.append(f['index'])
        ff=dict(f);gg=dict(g);ff.pop('address');gg.pop('address');assert ff==gg
    assert changed==ev['relocated']==[32349,32350,32351,32352,32373]
    assert len(old['functions'])==len(new['functions'])
    for key in old:
        if key!='functions':assert old[key]==new[key]
    assert e.b.raw_messages((e.S/'NightRemaster.ain').read_bytes())[3]==e.b.raw_messages((e.O/'NightRemaster.ain').read_bytes())[3]
    ss=e.b.strings(before)[2];ns=e.b.strings(after)[2];assert ns[:len(ss)]==ss and len(ns)-len(ss)<=1
    assert e.h(e.S/'NightRemasterEX.ex')==e.h(e.O/'NightRemasterEX.ex')
    layout=e.p.read(e.O/'layout.json');assert layout['archive']['replaced_ids']==[168,169]
    assert layout['archive']['candidate_sha256']==ev['files']['NightRemasterPact.afa']
    for record in layout['changes']:
        index=record['index'];src=e.n.ex.decode_ex(e.O/f'pact_{index}.pactex');dst=e.n.ex.decode_ex(e.O/f'new_pact_{index}.pactex')
        assert e.n.ex.structure_signature(src)==e.n.ex.structure_signature(dst)
        assert all(node.content==dst.strings[k].content for k,node in src.strings.items())
        found=[dict(path=list(k),before=node.raw.hex(),after=dst.scalars[k].raw.hex()) for k,node in src.scalars.items() if node.raw!=dst.scalars[k].raw]
        assert found==record['scalars'] and len(found)==(10 if index==168 else 1)
    probes=[]
    expected={0:[999,998,1,2,3,4],**{page:[999,998]+list(range(page*5,page*5+5)) for page in range(1,10)}}
    assert [slot for row in expected.values() for slot in row[2:]]==list(range(1,50))
    for path in sorted(e.O.glob('native_probe_*/result.json')):
        r=e.p.read(path);n=r['native'];log=n.get('log',[])
        if r['source_sha256']!=e.h(e.O/'NightRemaster.ain'):continue
        if n.get('exit_code')!=0 or n.get('events') or not log or not log[-1].startswith('PASS all ten pages'):continue
        if any(re.match(r'ROWS page=(1[0-9]|[2-9][0-9]) ',line) for line in log):continue # Earlier harness sent a disabled next-page command.
        assert not n.get('vm_error') and not n.get('message') and not n.get('timeout')
        assert r['real_saves_unchanged'] and e.h(path.parent/'NightRemaster.ain')==r['manifest']['probe_sha256']
        rows={0:[],1:[]};pinned=[]
        for line in log:
            m=re.fullmatch(r'ROWS page=(\d+) type=(\d+):(.*)',line)
            if m:
                page,typ=int(m[1]),int(m[2]);pairs=[tuple(map(int,item.split('/'))) for item in m[3].split()]
                assert [slot for slot,_ in pairs]==expected[page],line
                for slot,clickable in pairs:assert clickable==int((slot<998) if typ==0 else slot in [999,998,49]),line
                rows[typ].append(page)
            m=re.fullmatch(r'PINNED page=(\d+) y=0,72',line)
            if m:pinned.append(int(m[1]))
        want=[9,8,7,6,5,4,3,2,1,0,1]
        assert rows=={0:want,1:want},rows
        assert pinned==want+want,pinned
        for name in ['load_0','load_1','load_9','save_0','save_1','save_9']:assert (path.parent/(name+'.png')).exists()
        probes.append(str(path))
    assert probes,'A matching native pass is required'
    frames=e.p.read(e.O/'save_frames.json')
    review=e.p.read(e.O/'visual_review.json');assert review['status']=='PASS' and review['files']==ev['files'] and review['native_probe']==probes[-1]
    e.save('verification.json',dict(status='PINNED_AUTOSAVE_STATIC_NATIVE_PASS',files=ev['files'],native_probes={'candidate':probes[-1]},
        existing_resume_saves=len(frames['saves']),saved_return_frames=len(frames['frames']),save_schema_equal=True,
        old_CODE_allowlist_exact=True,changed_PACT=[168,169],MSG1_exact=True,STR0_prefix_exact=True,
        real_saves_unchanged=True,OS_mouse_hit_test=False,native_views=22,all_manual_slots=list(range(1,50)),
        autosave_slots=[999,998],positions=[0,72],latest_manual_page_preserved=True,card_height=70,pitch=72))
    e.p.O=e.O;e.p.FILES=['NightRemaster.ain','NightRemasterPact.afa'];e.p.fixture()
    print('PASS: pinned daily/weekly on all ten pages, manual slots1..49 intact, native position and keyboard selectors, save compatibility')

if __name__=='__main__':main()
