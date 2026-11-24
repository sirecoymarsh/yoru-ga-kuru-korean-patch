"""Hash-bound append-only, save compatibility, native layout and transaction checks."""
from pathlib import Path
import sys,struct,json,re
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
from PIL import Image,ImageChops
O=L.CODEX/'staging/calendar_choices_20260929';W=O/'work/build';E=O/'evidence'
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
probe=L.readj(E/'native_choices_probe.json')
assert probe['pass'] and probe['candidate_sha256']==files['NightRemaster.ain'] and not probe['user_files_changed']
assert all(x in probe['log'] for x in ['PASS all 915 detail boards fit, no clipped info','PASS all changed detail boards fit','PASS all changed getter outputs read and unread','PASS detail cancel','PASS card guarded replay request','PASS stage button','PASS all detail parts released'])
log='\n'.join(probe['log']);assert 'LABEL FAIL' not in log
assert '호시카와와' not in re.search(r'DETAIL 328 <<<\n(.*?)\n>>>',log,re.S).group(1)
shots=E/'native_choices';oldshots=L.CODEX/'evidence/calendar_detail_layout_20260929/screenshots'
for new,old in [('detail_list_unchanged.png','detail_list_unchanged.png'),('detail_e00011.png','detail_e00011.png')]:
    assert ImageChops.difference(Image.open(shots/new).convert('RGB'),Image.open(oldshots/old).convert('RGB')).getbbox() is None,new
assert ImageChops.difference(Image.open(shots/'chart_title_before.png'),Image.open(shots/'detail_title_after.png')).getbbox() is None,'Detail parts leaked on close'
assert all((shots/n).is_file() for n in ['choice_common.png','choice_izumi.png','choice_kyoka.png','choice_common_unread.png','choice_list_names.png','choice_list_actions.png','choice_recollection_long.png'])
labels=L.readj(O/'design/label_patch.json');assert L.sha(O/'design/label_patch.json')==man['choice_label_sha256']
review=L.readj(E/'label_review.json');assert review['status']=='PASS' and review['label_patch_sha256']==man['choice_label_sha256']
# Existing native getters are cloned as fallback; compare normalized disassembly, not just source promises.
for new,old in man['cloned_getters'].items():
    p=W/(new+'_verified.jam');L.cmd('ain','dump','--function',new,'-o',p,O/'candidate/NightRemaster.ain')
    def norm(t):
        # Cloning relocates function IDs and absolute jump labels. Preserve all
        # instructions/operands, comparing each jump's destination by label order.
        labels={s:f'L{i}' for i,s in enumerate(re.findall(r'^(0x[0-9a-f]+):',t,re.M))}
        out=[]
        for line in t.splitlines():
            line=line.strip()
            if not line or line.startswith(';') or re.match(r'^(?:FUNC|ENDFUNC|EOF) ',line):continue
            if line.endswith(':') and line[:-1] in labels:line=labels[line[:-1]]+':'
            elif re.fullmatch(r'(?:IFZ|IFNZ|JUMP) 0x[0-9a-f]+',line):
                op,dst=line.split();assert dst in labels;line=op+' '+labels[dst]
            out.append(line)
        return out
    assert norm(p.read_text('utf8'))==norm((W/(old+'_original.jam')).read_text('utf8')),(new,'fallback instructions changed')
P.FILES=list(files);P.O=O/'candidate';L.WORK=O/'work'
fx=P.fixture();L.writej(E/'transaction_verification.json',fx)
result=dict(status='STATIC_NATIVE_VISUAL_PASS',files=files,existing_resume_saves=len(saves),saved_return_frames=len(frames),metadata_forwarders=changed,
    old_code_prefix_exact=True,original_strings_prefix_exact=True,serialized_schema_changes=0,original_messages_exact=True,dll_byte_exact=True,native_opcode_audit=True,
    original_fallback_getters_instruction_exact=True,native_rendered_list_detail_boards=915,native_rendered_changed_detail_boards=len(labels['patch']['when_fix']),
    read_and_unread_getter_checks=2*sum(len(v) for v in labels['patch'].values()),list_pixel_exact=True,unmodified_detail_pixel_exact=True,unread_even_unlocked_hidden=True,
    detail_native_cancel_play_stage=True,mini_size=[32,40],detail_size=[104,130],choice_scenes=len(labels['choices']),common_scenes=len(labels['shared']),
    changed_counts=man['changed_counts'],translator_model='Codex internal',
    limitations=['Scope: 38 numbered branch scenes, 7 common continuations and their references. Fourteen other after-training-priority answer-number labels remain outside this batch.',
    'Native diagnostics use hidden muted private saves and scripted engine event-loop choices, not physical user input.',
    'Display getters and branch-menu columns only; original choice wording, scenario outcomes, ending logic, summaries, portraits and saved state are unchanged.',
    'No all-route gameplay or all-ending replay claim.'])
L.writej(O/'verification.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
