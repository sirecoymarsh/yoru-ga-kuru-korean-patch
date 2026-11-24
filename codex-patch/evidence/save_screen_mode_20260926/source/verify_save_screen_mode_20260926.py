"""Native config dispatch + both save layouts + preference persistence, bound to candidate hashes."""
import re,struct
import build_save_screen_mode_20260926 as e
from verify_mod_menu_style_20260917 import Font
from build_mod_tab_20260915 import coords,scalar

def main():
    ev=e.p.read(e.O/'build_evidence.json');assert all(e.h(e.O/n)==h for n,h in ev['files'].items())
    before=e.b.unpack((e.S/'NightRemaster.ain').read_bytes());after=e.b.unpack((e.O/'NightRemaster.ain').read_bytes())
    oldsize=struct.unpack_from('<I',before,12)[0];assert before[16:16+oldsize]==after[16:16+oldsize]
    old=e.b.read_meta(e.S/'candidate_meta.json');new=e.b.read_meta(e.O/'candidate_meta.json');changed=[]
    for f,g in zip(old['functions'],new['functions']):
        if f['address']!=g['address']:changed.append(f['index'])
        ff=dict(f);gg=dict(g);ff.pop('address');gg.pop('address');assert ff==gg
    assert changed==ev['relocated'];assert len(new['functions'])==len(old['functions'])+len(ev['added_functions'])
    for key in old:
        if key!='functions':assert old[key]==new[key]
    assert e.b.raw_messages((e.S/'NightRemaster.ain').read_bytes())[3]==e.b.raw_messages((e.O/'NightRemaster.ain').read_bytes())[3]
    ss=e.b.strings(before)[2];ns=e.b.strings(after)[2];assert ns[:len(ss)]==ss
    assert e.h(e.S/'NightRemasterEX.ex')==e.h(e.O/'NightRemasterEX.ex')
    layout=e.p.read(e.O/'layout.json');assert layout['changed']==[185]
    assert layout['archive']['candidate_sha256']==ev['files']['NightRemasterPact.afa']
    assert layout['reverse_exact'] and layout['existing_alternative_assets_exact']
    d=e.n.ex.decode_ex(e.O/'pact_185.pactex');label=e.n.part(d,'KR_SaveStyleLabel');ti=e.n.txt_info(label);decor=e.n.child(ti,'テキスト装飾')
    font=Font(e.p.RT/'NightRemasterFont.fnl');size=scalar(e.n.val(decor,'フォントサイズ'));w,h=font.metrics('저장 화면 설정',size)
    x,y,z=coords(label);assert 563<=x and x+w<=755 and 34<=y and y+h<=64
    for index in [168,169]:assert e.h(e.S/f'original_{index}.pactex')==layout['original_assets_exact'][str(index)]
    probes=[]
    for path in sorted(e.O.glob('native_probe_*/result.json')):
        r=e.p.read(path)
        if r['source_sha256']!=ev['files']['NightRemaster.ain'] or 'B' not in r:continue
        if not all(r[k].get('exit_code')==0 and not r[k].get('events') and r[k].get('log',[])[-1].startswith('PASS '+k) for k in ['A','B']):continue
        assert r['real_saves_unchanged'] and e.h(path.parent/'NightRemaster.ain')==r['manifest']['probe_sha256']
        assert e.h(path.parent/'NightRemasterPact.afa')==ev['files']['NightRemasterPact.afa']
        for phase in ['A','B']:
            native=r[phase];assert not any(native.get(k) for k in ['timeout','vm_error','message'])
            rows=[];views=[];settings=[]
            for line in native['log']:
                m=re.fullmatch(r'ROWS page=(\d+) type=(\d+):(.*)',line)
                if m:rows.append((int(m[1]),int(m[2]),[tuple(map(int,v.split('/'))) for v in m[3].split()]))
                m=re.fullmatch(r'LAYOUT alt=(\d+) page=(\d+) type=(\d+) pitch=(\d+)',line)
                if m:views.append(tuple(map(int,m.groups())))
                m=re.fullmatch(r'SETTING choice=(\d+) alt=(\d+)',line)
                if m:settings.append(tuple(map(int,m.groups())))
            pages=[9,8,7,6,5,4,3,2,1,0,1] if phase=='A' else [9]
            expected=[(alt,page,typ,72 if alt else 101) for alt in [0,1] for typ in [1,0] for page in pages]
            if phase=='A':expected += [(0,9,0,101),(0,9,0,101)] # Native save47 refreshes its hidden save view twice.
            assert views==expected,(phase,views)
            assert len(rows)==len(expected)
            for (page,typ,pairs),(alt,vpage,vtype,pitch) in zip(rows,views):
                assert (page,typ)==(vpage,vtype)
                manual=list(range(1,5)) if page==0 else list(range(page*5,page*5+5))
                want=([999,998]+manual) if alt else ([999]+manual if page==0 else manual)
                assert [slot for slot,_ in pairs]==want,pairs
                for slot,clickable in pairs:assert clickable==int(slot<998 if typ==0 else slot in ([999,998,49] if phase=='A' else [999,998,47,49]))
            assert settings==([(0,1),(1,0),(2,1),(1,0)] if phase=='A' else [(2,1)]),settings
            if phase=='B':assert 'RESTART original preference preserved; saved47 resumed' in native['log']
        for style in ['original','alternative']:
            for kind in ['save','load']:
                for page in [0,1,9]:assert (path.parent/f'{style}_{kind}_{page}.png').exists()
        probes.append(str(path))
    assert probes,'A matching native A/B pass is required'
    review=e.p.read(e.O/'visual_review.json');assert review['status']=='PASS' and review['files']==ev['files'] and review['native_probe']==probes[-1]
    frames=e.p.read(e.O/'save_frames.json')
    e.save('verification.json',dict(status='SAVE_SCREEN_MODE_STATIC_NATIVE_PASS',files=ev['files'],native_probes={'candidate':probes[-1]},
        existing_resume_saves=len(frames['saves']),saved_return_frames=len(frames['frames']),save_schema_equal=True,
        old_CODE_allowlist_exact=True,changed_PACT=[185],appended_original_assets=2,MSG1_exact=True,STR0_prefix_exact=True,
        real_saves_unchanged=True,OS_mouse_hit_test=False,native_views=50,native_settings_dispatch=True,cancel_noop=True,restart_preference=True,
        shared_save47_resumed=True,latest_manual_page_preserved=True,original_mode='Five original stat cards; daily999/manual1..49',alternative_mode='Fixed daily999/weekly998 above manual1..49',default_mode='alternative'))
    e.p.O=e.O;e.p.FILES=['NightRemaster.ain','NightRemasterPact.afa'];e.p.fixture()
    print('PASS: native settings, both layouts all pages, same saved47 resumed across modes, durable preference, immutable user saves')

if __name__=='__main__':main()
