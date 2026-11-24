"""Freeze source-bound choice context without changing scenario dialogue."""
from pathlib import Path
import sys,json,shutil,re
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
R=L.CODEX;PRE=R/'staging/calendar_choices_20260929';O=R/'staging/calendar_choice_context_20260929'
cur=L.readj(L.CURRENT);rt=Path(cur['runtime'])
assert L.sha(rt/'NightRemaster.ain')=='6681bc33dc97a99eb59a3280a3b53e505f09fb8aac7e8a1d84c0b64e0c9b08ac'
assert not O.exists(),'Do not overwrite frozen context staging'
for d in ['source','design','work/build','work/tmp','candidate','evidence','probe']:(O/d).mkdir(parents=True)
for n in ['NightRemaster.ain','winmm.dll']:shutil.copy2(rt/n,O/'source'/n)
for n in ['candidate_meta.json','candidate_raw_code.jam']:shutil.copy2(PRE/'work/build'/n,O/'source'/n)
for n in ['cells.json','cast_evidence.json','r19_tables.json','r15_tables.json','schedule.json','groups.json']:shutil.copy2(PRE/'design'/n,O/'design'/n)
L.writej(O/'source_pointer.json',cur);L.writej(O/'source_hashes.json',{n:L.sha(O/'source'/n) for n in ['NightRemaster.ain','winmm.dll']})
old=L.readj(PRE/'design/label_patch.json');events={e['id']:e for e in L.readj(O/'design/schedule.json')['events']}
graph=F.parents[1]/'graph';inputs=L.readj(graph/'inputs.json');jp_path=Path(inputs['files']['NightRemaster.ain']['path'])
assert L.sha(jp_path)==inputs['files']['NightRemaster.ain']['sha256']
jp=L.raw_messages(jp_path.read_bytes())[3];kr=L.raw_messages((O/'source/NightRemaster.ain').read_bytes())[3]
current_strings={L.decode(b) for b in L.strings(L.unpack((O/'source/NightRemaster.ain').read_bytes()))[2]}
contexts={
 'photography':dict(parents=[322,60015],message_ids=[26374,26383,84553],description='함께 촬영할 사람을 고르는 선택',prompt='자… 누구랑 같이 촬영해 볼까……',speaker='주인공의 생각',addressee='자신'),
 'narration':dict(parents=[611,60017],message_ids=list(range(30789,30850))+list(range(86252,86313)),description='슬라이드 해설자를 고르는 선택',prompt='넌 누가 좋다고 생각해?',speaker='쿄카',addressee='주인공'),
 'cinema':dict(parents=[30152],message_ids=list(range(56747,56754)),description='함께 영화를 볼 사람을 고르는 선택',prompt='누구 데려가 볼까…',speaker='주인공의 생각',addressee='자신')}
for c in contexts.values():c['source_lines']=[dict(m=n,jp=jp[n].decode('cp932'),installed_kr=L.decode(kr[n])) for n in c['message_ids']]
patch={k:{} for k in ['ev_head','ev_short','when_fix']};unread={k:{} for k in patch};rows=[];dates={}
names=['이즈미','쿄카','마나미','마코토']
for row in old['choices']:
    no=row['event'];parent=row['parent'];key=next((k for k,c in contexts.items() if parent in c['parents']),None)
    if not key:continue
    c=contexts[key];name=names[row['answer']-1];n=str(no)
    option='『'+row['choice_kr']+'』';assert option in current_strings,(no,option)
    prefix=old['patch']['ev_head'][n].rsplit(' · ',1)[0]
    if key=='photography':short=name+'와 촬영'
    elif key=='narration':short=name+'에게 해설 부탁'
    else:short=name+'를 영화에 초대'
    # All four names end in a vowel. Keep the established Korean particles.
    head=prefix+' · '+short
    lead=re.match(r'^(\d+\. |\d+번 )',old['patch']['ev_short'][n]).group()
    text=c['description']+' · '+c['speaker']+': 「'+c['prompt']+'」 → '+option+' 선택'
    patch['ev_head'][n]=head;patch['ev_short'][n]=lead+short;patch['when_fix'][n]=text
    for k in unread:unread[k][n]=old['unread'][k][n]
    dates[n]=prefix
    rows.append(dict(**row,context_key=key,exact_installed_choice=option,detail=text,title=head,short=lead+short))
assert len(rows)==20
for n,s in patch['ev_short'].items():assert sum(.5 if ord(c)<128 else 1 for c in s)+2<=20,(n,s)
data=dict(translator_model='Codex internal',author='Codex root',translation_quality_sha256=L.sha(Path(r'P:\AI\Codex\skills\contextual-game-localization/references/translation-quality.md')),
    patch=patch,unread=unread,choices=rows,shared={},dates=dates,contexts=contexts,
    source_jp_sha256=L.sha(jp_path),source_installed_sha256=L.sha(O/'source/NightRemaster.ain'),
    scope='20 character choices across photography, slideshow narration and cinema. Detail board adds a dedicated choice field. Existing dialogue, choices, outcomes, prior common joins, date prefixes and unread masking preserved.')
L.writej(O/'design/label_patch.json',data)
print(json.dumps(dict(root=str(O),changed={k:len(v) for k,v in patch.items()}),ensure_ascii=False))
