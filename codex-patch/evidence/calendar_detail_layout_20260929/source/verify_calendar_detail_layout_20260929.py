"""Hash-bound append-only, save compatibility, native layout and transaction checks."""
from pathlib import Path
import sys,struct,json,re
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
from PIL import Image,ImageChops
O=L.CODEX/'staging/calendar_detail_layout_20260929';W=O/'work/build';E=O/'evidence'
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
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert (O/'source/winmm.dll').read_bytes()==(O/'candidate/winmm.dll').read_bytes()
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
probe=L.readj(E/'native_detail_probe.json')
assert probe['pass'] and probe['candidate_sha256']==files['NightRemaster.ain'] and not probe['user_files_changed']
assert all(x in probe['log'] for x in ['PASS all 915 detail boards fit, no clipped info','PASS detail cancel','PASS card guarded replay request','PASS stage button','PASS all detail parts released'])
log='\n'.join(probe['log'])
assert '†' not in log,'Legacy dialog color marker leaked into Parts text'
def plain(s):return re.sub(r'\s+','',re.sub(r'\$\{[^}]*\}','',s))
checked=[]
for hit in re.finditer(r'OLD WHEN ([^\n]+)\nOLD WHO ([^\n]+)\n(?:OLD STAGES ([^\n]+)\n)?DETAIL (\d+) <<<\n(.*?)\n>>>',log,re.S):
    when,who,stages,no,info=hit.groups();p=plain(info)
    assert plain(when) in p and plain(who) in p,(no,info)
    if stages:assert plain(stages)+'단계읽음' in p,(no,stages)
    checked.append(int(no))
assert set(checked)=={11,16,1,328,1001,262},checked
unread=re.search(r'UNREAD <<<\n(.*?)\n>>>',log,re.S).group(1)
assert all(n not in unread for n in ['이즈미','쿄카','마나미','줄거리'])
assert '열람 후 표시됩니다' in unread
shots=E/'native_detail'
oldshots=L.CODEX/'evidence/calendar_portraits_20260929/screenshots'
assert ImageChops.difference(Image.open(shots/'detail_list_unchanged.png').convert('RGB'),Image.open(oldshots/'portraits_list_may.png').convert('RGB')).getbbox() is None,'List visual changed'
assert ImageChops.difference(Image.open(shots/'chart_title_before.png'),Image.open(shots/'detail_title_after.png')).getbbox() is None,'Detail parts leaked on close'
assert len(list(shots.glob('*.png')))>=10
P.FILES=list(files);P.O=O/'candidate';L.WORK=O/'work'
fx=P.fixture();L.writej(E/'transaction_verification.json',fx)
result=dict(status='STATIC_NATIVE_VISUAL_PASS',files=files,existing_resume_saves=len(saves),saved_return_frames=len(frames),metadata_forwarders=changed,
    old_code_prefix_exact=True,original_strings_prefix_exact=True,serialized_schema_changes=0,original_messages_exact=True,dll_byte_exact=True,native_opcode_audit=True,
    native_rendered_detail_boards=915,original_information_verified_events=checked,list_pixel_exact=True,unread_even_unlocked_hidden=True,detail_native_cancel_play_stage=True,
    mini_size=[32,40],detail_size=[104,130],summary_events=[11],restored_fields=man['restored_fields'],translator_model='Codex internal',
    limitations=['Only the approved E00011 summary exists; other scenes retain information and portraits without fabricated summaries.',
    'Original who/when/stage/condition getters are preserved, including existing anonymous-speaker labels and shortened cast lists.',
    'Native diagnostics use hidden muted private saves and scripted engine event-loop choices, not physical user input.',
    'All 915 detail boards checked for bounds, not all scenes/endings replayed; extended gameplay is outside this UI patch verification.'])
L.writej(O/'verification.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
