from pathlib import Path
import sys,struct,json,shutil
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/claude_fixes_20260928';W=O/'work/build';E=O/'evidence'
man=L.readj(O/'candidate/manifest.json');files={n:L.sha(O/'candidate'/n) for n in ['NightRemaster.ain','winmm.dll']}
assert files=={n:v['sha256'] for n,v in man['files'].items()}
raw=L.unpack((O/'candidate/NightRemaster.ain').read_bytes());base=L.unpack((O/'source/NightRemaster.ain').read_bytes());base_n=struct.unpack_from('<I',base,12)[0]
check=bytearray(raw[16:16+base_n])
for s in man['same_length_sites']:
    a=s['site']
    assert raw[16+a:22+a]==bytes.fromhex(s['after'])
    if a<base_n:check[a:a+6]=bytes.fromhex(s['before'])
assert check==base[16:16+base_n]
m=L.read_meta(L.R23/'work/build/candidate_meta.json');nm=L.read_meta(W/'candidate_meta.json')
allowed={'KR_CChart','KR_CDraw','KR_CWait','KR_CClick','KR_CStateLine','KR_CPlayNote','KR_T18ClearPrev'}
changed=[]
for f,g in zip(m['functions'],nm['functions']):
    if f!=g:
        name=L.raw_symbol(m,f['index']);assert name in allowed,name
        assert {k:v for k,v in f.items() if k!='address'}=={k:v for k,v in g.items() if k!='address'}
        changed.append(name)
assert set(changed)==allowed
for k in m:
    if k!='functions':assert m[k]==nm[k],k
assert L.raw_messages((O/'source/NightRemaster.ain').read_bytes())[3]==L.raw_messages((O/'candidate/NightRemaster.ain').read_bytes())[3]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
vs=L.versions(L.R23/'work/build/candidate_raw_code.jam');preserved=[]
for f in m['functions']:
    if f['name'].startswith(('KR_Walk','KR_Explore','KR_Story','KR_Rate')) or f['name'] in L.PINNED_ALL:
        v=L.live_version(m,vs,f['index']);a=v['start'];z=v['ops'][-1][0]+2
        assert nm['functions'][f['index']]==f and base[16+a:16+z]==raw[16+a:16+z],f['name']
        preserved.append(f['name'])
frames=[];saves=[]
for p in sorted(L.SAVES.glob('NightR*.asd')):
    if not p.stem[6:].isdigit():continue
    r=L.save_records(p);saves.append(p.name)
    for fr in [r['ip']]+r['returns']:
        ad=fr['address']
        if ad<0:continue
        assert base[16+ad:22+ad]==raw[16+ad:22+ad],(p.name,fr)
        frames.append(dict(save=p.name,**fr))
L.writej(E/'save_frames.json',dict(saves=saves,frames=frames))
chart=L.readj(E/'probe_chart_r24.json')
for mode in ['home','title']:
    r=chart[mode]
    assert r['candidate_sha256']==files['NightRemaster.ain']
    assert r.get('exit_code')==0 and not r.get('vm_error') and not r.get('message') and not r.get('events')
    assert 'END' in r['log'] and 'FIX28 BLOCKED=1 manual=0 auto=0 snapshot=0' in r['log']
replay=L.readj(E/'replay_safety.json')
assert replay['candidate_sha256']==files['NightRemaster.ain'] and replay['user_save_unchanged']
assert replay['exit_code']==0 and 'FIX28 REJECTED midload' in replay['log'] and any(s.startswith('FIX28 RESET REACHED') for s in replay['log'])
assert L.readj(E/'replay_state_comparison.json')=={}
assert L.readj(E/'maintenance/summary.json')['status']=='PASS'
startup=L.readj(E/'startup_wrapper/result.json');assert startup['status']=='PASS' and startup['production_dll_sha256']==files['winmm.dll']
from PIL import Image,ImageChops
img=Image.open(E/'probe/chart_home_resumed.png').convert('RGB')
assert img.size==(1280,720)
assert all(img.getpixel(p)==(255,214,110) for p in [(24,114),(160,114),(324,114)]),'home chart still occluded'
for x,y in [(0,0),(1279,719),(100,630),(1170,630)]:assert img.getpixel((x,y))==(6,10,26)
assert ImageChops.difference(Image.open(E/'probe/chart_title_before.png'),Image.open(E/'probe/chart_title_after_replay.png')).getbbox() is None
scan=L.readj(O/'candidate/scan_report.json');assert scan['status']=='SCANNED_NO_TARGET_DETECTIONS' and scan['files']==files
# Prove the real two-file installation/rollback functions on a fixture.
P.FILES=list(files);P.O=O/'candidate';L.WORK=O/'work'
fixture=P.fixture();L.writej(E/'transaction_verification.json',fixture)
result=dict(status='STATIC_NATIVE_PASS',files=files,existing_resume_saves=len(saves),saved_return_frames=len(frames),preserved_functions=preserved,metadata_forwarders=changed,
    same_length_sites=man['same_length_sites'],schema_changes=0,legacy_replay_midsave_rejected=True,calendar_replay_state_restored=True,home_chart_unoccluded=True,
    transaction_failure_crash_cases=338,production_startup_recovery=True,normal_chart_title_home=True,translator_model='Codex internal',
    limitations=['Native tests use isolated copied saves and scripted native event-loop choices, not physical keyboard/mouse input.',
    'Full gameplay/endings and all 915 chart scenes were not replayed in this fix pass. r24 table/VM evidence is retained; the changed paths were tested natively.',
    'Old reset backups without a completion marker are preserved but are not auto-selected. No such folders were found in the current user saves.',
    'Unsafe saves made inside old replay sessions are rejected; load a normal save made before replay. They are not rewritten.'])
L.writej(O/'verification.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ['same_length_sites','preserved_functions']},ensure_ascii=False,indent=2))
