from pathlib import Path
import sys,struct,json,hashlib
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
from PIL import Image,ImageChops
O=L.CODEX/'staging/calendar_portraits_20260929';W=O/'work/build';E=O/'evidence'
man=L.readj(O/'candidate/manifest.json');files={n:L.sha(O/'candidate'/n) for n in ['NightRemaster.ain','winmm.dll']}
assert files=={n:v['sha256'] for n,v in man['files'].items()}
raw=L.unpack((O/'candidate/NightRemaster.ain').read_bytes());base=L.unpack((O/'source/NightRemaster.ain').read_bytes())
oldn=struct.unpack_from('<I',base,12)[0];assert raw[16:16+oldn]==base[16:16+oldn]
m=L.read_meta(O/'source/candidate_meta.json');nm=L.read_meta(W/'candidate_meta.json')
allowed=set(man['forwarded']);changed=[]
for f,g in zip(m['functions'],nm['functions']):
    if f!=g:
        name=L.raw_symbol(m,f['index']);assert name in allowed
        assert {k:v for k,v in f.items() if k!='address'}=={k:v for k,v in g.items() if k!='address'}
        changed.append(name)
assert set(changed)==allowed
for k in m:
    if k!='functions':assert m[k]==nm[k]
for n in L.PINNED_ALL:assert m['functions'][L.fid_of(m,n)]==nm['functions'][L.fid_of(m,n)]
assert L.raw_messages((O/'source/NightRemaster.ain').read_bytes())[3]==L.raw_messages((O/'candidate/NightRemaster.ain').read_bytes())[3]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==[s.replace(L.encode('이벤트 플로우 차트'),L.encode('이벤트 캘린더')) for s in L.strings(base)[2]]
db=(O/'source/winmm.dll').read_bytes();dn=(O/'candidate/winmm.dll').read_bytes();dp=man['dll_string_patch'];a=dp['offset'];b=a+len(bytes.fromhex(dp['before']))
assert db[a:b]==bytes.fromhex(dp['before']) and dn[a:b]==bytes.fromhex(dp['after']) and db[:a]==dn[:a] and db[b:]==dn[b:]
audit=L.readj(W/'native_opcode_audit.json');assert audit['ain_sha256']==files['NightRemaster.ain'] and audit['all_active_opcodes_supported']
saves=[];frames=[]
for p in sorted(L.SAVES.glob('NightR*.asd')):
    if not p.stem[6:].isdigit():continue
    r=L.save_records(p);saves.append(p.name)
    for fr in [r['ip']]+r['returns']:
        ad=fr['address']
        if ad<0:continue
        assert base[16+ad:22+ad]==raw[16+ad:22+ad],(p.name,fr)
        frames.append(dict(save=p.name,**fr))
L.writej(E/'save_frames.json',dict(saves=saves,frames=frames))
probe=L.readj(E/'native_portrait_probe.json')
assert probe['pass'] and probe['candidate_sha256']==files['NightRemaster.ain'] and not probe['user_files_changed']
assert all(x in probe['log'] for x in ['PASS face asset really loaded','PASS all 915 list cells rendered','PASS event detail forwards to guarded replay request','PASS card detail cancel returns normally'])
shots=E/'native_portraits';img=Image.open(shots/'portraits_roster_asset_test.png').convert('RGB')
counts=[]
for i in range(16):
    x=108+(i%8)*136;y=198+(i//8)*172
    pixels=list(img.crop((x,y,x+104,y+130)).getdata());nonbg=sum(p!=(14,25,55) for p in pixels)
    assert nonbg>3000 and len(set(pixels))>100,(i,nonbg,len(set(pixels)))
    counts.append(nonbg)
img=Image.open(shots/'portraits_list_may.png').convert('RGB')
for i in range(3):
    pixels=list(img.crop((186+i*36,188,218+i*36,228)).getdata())
    assert sum(p!=(18,30,72) for p in pixels)>250 and len(set(pixels))>30
unread=Image.open(shots/'portraits_detail_unread_unlocked.png').convert('RGB')
assert len(set(unread.crop((108,278,1196,410)).getdata()))==1,'unread face area leaked'
assert ImageChops.difference(Image.open(shots/'chart_title_before.png'),Image.open(shots/'portraits_title_after.png')).getbbox() is None
P.FILES=list(files);P.O=O/'candidate';L.WORK=O/'work'
fx=P.fixture();L.writej(E/'transaction_verification.json',fx)
result=dict(status='STATIC_NATIVE_VISUAL_PASS',files=files,existing_resume_saves=len(saves),saved_return_frames=len(frames),metadata_forwarders=changed,
    old_code_prefix_exact=True,serialized_schema_changes=0,original_messages_exact=True,dll_code_exact=True,native_opcode_audit=True,
    native_rendered_cells=915,portrait_asset_pixels=counts,unread_even_unlocked_hidden=True,detail_native_cancel_play_stage=True,
    mini_size=[32,40],detail_size=[104,130],summary_events=[11],translator_model='Codex internal',
    limitations=['Scene cast is derived from explicit speaker tags. Silent-only appearances and anonymous speaker identities are not inferred.',
    'Only the approved E00011 summary is authored; other scenes show portraits without fabricated summaries.',
    'Native diagnostics use hidden muted private saves and scripted engine event-loop choices, not physical user input.',
    'All 915 cells rendered, not all scenes/endings replayed; long gameplay remains outside this visual UI patch verification.'])
L.writej(O/'verification.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
