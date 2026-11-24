"""Cumulative installed-base audit and save/transaction gates for April UI."""
from pathlib import Path
import sys,struct,json
sys.dont_write_bytecode=True
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/calendar_april_adaptive_minis_20260929';E=O/'evidence'
cur=L.readj(L.CURRENT);rt=Path(cur['runtime']);man=L.readj(O/'candidate/manifest.json')
assert cur==L.readj(O/'source_pointer.json')
assert L.sha(rt/'NightRemaster.ain')==man['live_sha256']
assert P.stopped(rt),'Do not change a running game'
files={n:L.sha(O/'candidate'/n) for n in ['NightRemaster.ain','winmm.dll']}
assert files=={n:v['sha256'] for n,v in man['files'].items()}
for stage in ['calendar_april_readability_20260929','calendar_april_summary_20260929','calendar_april_adaptive_minis_20260929']:
    base=R/'staging'/stage;v=L.readj(base/'verification.json');p=L.readj(base/'evidence/native_april_probe.json')
    assert v['candidate_sha256']==p['candidate_sha256']==L.sha(base/'candidate/NightRemaster.ain')
    assert p['pass'] and not p['user_files_changed']
raw=L.unpack((O/'candidate/NightRemaster.ain').read_bytes());base=L.unpack((rt/'NightRemaster.ain').read_bytes())
oldn=struct.unpack_from('<I',base,12)[0];assert raw[16:16+oldn]==base[16:16+oldn]
m=L.read_meta(R/'staging/calendar_choice_context_20260929/work/build/candidate_meta.json')
nm=L.read_meta(O/'work/build/candidate_meta.json')
allowed={'KR_CDraw','KR_P29Board','KR_P29Buttons','KR_T9StagePage','KR_P29DropMinis'}
changed=[]
for f,g in zip(m['functions'],nm['functions']):
    if f!=g:
        assert f['name'] in allowed
        assert {k:v for k,v in f.items() if k!='address'}=={k:v for k,v in g.items() if k!='address'}
        changed.append(f['name'])
assert set(changed)==allowed
for k in m:
    if k!='functions':assert m[k]==nm[k],k
for n in L.PINNED_ALL:assert m['functions'][L.fid_of(m,n)]==nm['functions'][L.fid_of(m,n)]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert L.raw_messages((rt/'NightRemaster.ain').read_bytes())[3]==L.raw_messages((O/'candidate/NightRemaster.ain').read_bytes())[3]
assert (rt/'winmm.dll').read_bytes()==(O/'candidate/winmm.dll').read_bytes()
saves=[];frames=[]
for p in sorted(L.SAVES.glob('NightR*.asd')):
    if not p.stem[6:].isdigit():continue
    r=L.save_records(p);saves.append(p.name)
    for fr in [r['ip']]+r['returns']:
        a=fr['address']
        if a<0:continue
        assert base[16+a:22+a]==raw[16+a:22+a],(p.name,fr)
        frames.append(dict(save=p.name,**fr))
L.writej(E/'save_frames.json',dict(saves=saves,frames=frames))
P.FILES=list(files);P.O=O/'candidate';L.WORK=O/'work'
tx=P.fixture();L.writej(E/'transaction_verification.json',tx)
qa=L.readj(R/'staging/calendar_april_summary_20260929/evidence/semantic_qa.json')
assert not qa['unresolved'] and qa['reviewed_events']==146
report=dict(status='APRIL_CUMULATIVE_INSTALL_PREFLIGHT_PASS',files=files,live_source_sha256=man['live_sha256'],
 original_code_prefix_exact=True,original_messages_exact=True,original_strings_prefix_exact=True,serialized_schema_changes=0,
 pinned_functions_unchanged=L.PINNED_ALL,changed_forwarders=changed,added_functions=nm['functions'][len(m['functions']):],
 existing_resume_saves=len(saves),saved_return_frames=len(frames),native_143_cells_three_states=True,native_146_details_two_states=True,
 source_reviewed_summaries=146,transaction_fixture_pass=True,dll_unchanged=True,
 limitations=['April only; no expansion to other months.','Display-only update, not an all-route replay or gameplay test.'])
L.writej(E/'install_preflight.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='added_functions'},ensure_ascii=False,indent=2))
