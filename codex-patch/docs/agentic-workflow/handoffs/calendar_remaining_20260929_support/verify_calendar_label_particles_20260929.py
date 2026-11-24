"""Label-only cumulative, native and reversible-install gates."""
from pathlib import Path
import sys,struct,json
sys.dont_write_bytecode=True
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/calendar_label_particles_20260929_r2';E=O/'evidence'
cur=L.readj(L.CURRENT);rt=Path(cur['runtime']);man=L.readj(O/'candidate/manifest.json')
assert cur==L.readj(O/'source_pointer.json') and L.sha(rt/'NightRemaster.ain')==man['live_sha256']
files={n:L.sha(O/'candidate'/n) for n in ['NightRemaster.ain','winmm.dll']}
assert files=={n:v['sha256'] for n,v in man['files'].items()}
p=L.readj(E/'native_labels_probe.json');assert p['pass'] and p['candidate_sha256']==files['NightRemaster.ain']
assert p['checked_labels_per_read_mode']==2638 and p['checked_read_modes']==2
raw=L.unpack((O/'candidate/NightRemaster.ain').read_bytes());base=L.unpack((O/'source/NightRemaster.ain').read_bytes())
oldn=struct.unpack_from('<I',base,12)[0];assert raw[16:16+oldn]==base[16:16+oldn]
m=L.read_meta(O/'source/candidate_meta.json');nm=L.read_meta(O/'work/build/candidate_meta.json')
allowed={'KR_T19EvShort','KR_T19EvHead','KR_T19CardHead','KR_T19CardTail'};changed=[]
for a,b in zip(m['functions'],nm['functions']):
    if a!=b:
        assert a['name'] in allowed
        assert {k:v for k,v in a.items() if k!='address'}=={k:v for k,v in b.items() if k!='address'}
        changed.append(a['name'])
assert set(changed)==allowed and len(nm['functions'])==len(m['functions'])+8
for k in m:
    if k!='functions':assert m[k]==nm[k],k
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert L.raw_messages((O/'source/NightRemaster.ain').read_bytes())[3]==L.raw_messages((O/'candidate/NightRemaster.ain').read_bytes())[3]
assert (rt/'winmm.dll').read_bytes()==(O/'candidate/winmm.dll').read_bytes()
saves=[];frames=[]
for path in sorted(L.SAVES.glob('NightR*.asd')):
    if not path.stem[6:].isdigit():continue
    r=L.save_records(path);saves.append(path.name)
    for fr in [r['ip']]+r['returns']:
        a=fr['address']
        if a<0:continue
        assert base[16+a:22+a]==raw[16+a:22+a],(path.name,fr)
        frames.append(dict(save=path.name,**fr))
L.writej(E/'save_frames.json',dict(saves=saves,frames=frames))
P.FILES=list(files);P.O=O/'candidate';L.WORK=O/'work'
tx=P.fixture();L.writej(E/'transaction_verification.json',tx)
qa=L.readj(E/'semantic_qa.json');assert qa['status']=='PASS' and not qa['unresolved']
assert qa['translation_map_sha256']==L.sha(O/'design/label_patch.json')
report=dict(status='LABEL_PARTICLES_PREFLIGHT_PASS',files=files,source_sha256=man['source_sha256'],
    counts=man['counts'],original_code_prefix_exact=True,original_messages_exact=True,original_strings_prefix_exact=True,
    serialized_schema_changes=0,changed_forwarders=changed,existing_resume_saves=len(saves),saved_return_frames=len(frames),
    native_label_assertions=5276,native_picker_paths=['calendar','achievement','other_names','unread'],
    transaction_fixture_pass=True,dll_unchanged=True,translator_model='Codex internal',
    limitations=['Display-only labels; no scenario, choice outcomes or save-layout edits.','Native diagnostics used a muted private copy and scripted modal cancellation, not an all-route gameplay test.'])
L.writej(E/'install_preflight.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
