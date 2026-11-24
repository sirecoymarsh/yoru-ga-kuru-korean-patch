from pathlib import Path
import json,hashlib,shutil,re,datetime
R=Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922')
O=R/'staging/calendar_choices_20260929'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
fresh=not O.exists()
cur=read(R/'ui_cumulative/current.json');rt=Path(cur['runtime'])
assert sha(rt/'NightRemaster.ain')=='acb3e7abefcd37d58dbc8ac7d6bc38c01c5bec7b5ee244580c2f62ce989cdb3c'
assert sha(Path(cur['manifest']))==cur['manifest_sha256']
if fresh:
    for d in ['source','design','work/build','work/tmp','candidate','evidence','probe']:(O/d).mkdir(parents=True,exist_ok=True)
    for n in ['NightRemaster.ain','winmm.dll']:shutil.copy2(rt/n,O/'source'/n)
    for n in ['candidate_meta.json','candidate_raw_code.jam']:shutil.copy2(R/'staging/calendar_detail_layout_20260929/work/build'/n,O/'source'/n)
    for n in ['cells.json','cast_evidence.json']:shutil.copy2(R/'staging/calendar_detail_layout_20260929/design'/n,O/'design'/n)
    for source,name in [(F/'graph/groups.json','groups.json'),(F/'graph/schedule.json','schedule.json'),(F/'ingame/r19_calendar/work/build/tables.json','r19_tables.json'),(F/'ingame/r15_calendar/work/build/tables.json','r15_tables.json')]:shutil.copy2(source,O/'design'/name)
    write(O/'source_pointer.json',cur);write(O/'source_hashes.json',{n:sha(O/'source'/n) for n in ['NightRemaster.ain','winmm.dll']})
else:
    assert read(O/'source_pointer.json')==cur
    assert sha(O/'source/NightRemaster.ain')==sha(rt/'NightRemaster.ain')
T=read(O/'design/r19_tables.json');G=read(O/'design/groups.json');S=read(O/'design/schedule.json');V=read(O/'design/r15_tables.json')
# Authored compact UI labels, not replacements for the actual game choices.
compact={109:'보통 정도',110:'완전 별로다',271:'사실대로 말한다',272:'얼버무린다',273:'진실을 전한다',274:'조용히 있는다',
323:'이즈미',324:'쿄카',325:'마나미',326:'마코토',612:'이즈미',613:'쿄카',614:'마나미',615:'마코토',
801:'꽤 힘들다',802:'전혀 괜찮아',803:'먼저 간다',804:'기다린다',805:'부실에 남는다',806:'교사로 돌아간다',
20082:'밖으로 데리고 나감',20083:'그 자리에 남음',20165:'공원으로 간다',20166:'무시한다',
30153:'이즈미를 부른다',30154:'쿄카를 부른다',30155:'마나미를 부른다',30156:'마코토를 부른다',40062:'얻어먹으러 간다',40063:'가지 않는다',
60201:'이즈미',60202:'쿄카',60203:'마나미',60204:'마코토',65001:'이즈미',65002:'쿄카',65003:'마나미',65004:'마코토'}
kr={r['event']:r['via']['text_kr'].strip('『』') for g in G['groups'] for r in g['rows'] if r['via']['kind']=='answer'}
for a,b in zip(range(60201,60205),range(323,327)):kr[a]=kr[b]
for a,b in zip(range(65001,65005),range(612,616)):kr[a]=kr[b]
events={e['id']:e for e in S['events']};choices={c['next']:dict(parent=e['id'],**c) for e in S['events'] for c in e['choices']}
assert set(compact)=={int(n) for n,s in T['ev_head'].items() if re.search(r'갈래\s*\d',s)}
patch={k:{} for k in ['ev_head','ev_short','when_fix','conds','stage_cols','chip_cols']};evidence=[]
for no,label in compact.items():
    c=choices[no];old=T['ev_head'][str(no)]
    prefix=re.split(r' · \d+단계',old)[0] if '단계' in old else re.sub(r' 갈래 \d+.*$','',old)
    head=prefix+' · '+label+' 선택 후'
    if len(head)>38:head=head.replace(' · 본편','').replace(' · 던전','')
    assert len(head)<=38,(no,head)
    start=re.match(r'^(\d+\. |\d+번 )',T['ev_short'][str(no)]).group()
    patch['ev_head'][str(no)]=head
    patch['ev_short'][str(no)]=start+label+' 선택'
    patch['when_fix'][str(no)]='「'+kr[no]+'」 선택 후'
    evidence.append(dict(event=no,parent=c['parent'],answer=c['no'],source_jp=c['text_jp'],choice_kr=kr[no],compact=label,chain_to=events[no]['chains_to']))
shared={}
for parent in {c['parent'] for no,c in choices.items() if no in compact}:
    destinations=[c['next'] for c in events[parent]['choices']]
    if not all(x in compact for x in destinations):continue
    common=set.intersection(*(set(events[x]['chains_to']) for x in destinations))
    for no in common:
        # Prove every incoming continuation belongs to these alternatives.
        incoming={e['id'] for e in S['events'] if no in e['chains_to'] and (events[no]['category']=='memory_replay' or e['category']!='memory_replay')}
        if incoming!=set(destinations):continue
        shared[no]=dict(parent=parent,branches=destinations,labels=[compact[x] for x in destinations])
        old=T['ev_head'][str(no)]
        prefix=re.split(r' · \d+단계',old)[0] if '단계' in old else re.sub(r' 이어서$','',old)
        patch['ev_head'][str(no)]=prefix+' · 선택 후 공통 장면'
        start=re.match(r'^(\d+\. |\d+번 )',T['ev_short'][str(no)]).group()
        patch['ev_short'][str(no)]=start+'선택 후 공통 장면'
        labels=shared[no]['labels']
        if labels==['이즈미','쿄카','마나미','마코토']:
            when='이즈미·쿄카·마나미·마코토 중 누구를 선택해도 이어짐'
        else:when='「'+kr[destinations[0]]+'」 또는\n「'+kr[destinations[1]]+'」 선택 후 합류'
        patch['when_fix'][str(no)]=when
assert set(shared)=={59,64,111,328,616,60025,60205},shared
# References to a choice-specific scene: preserve date, one-day condition and replay identity.
patch['when_fix'].update({'70':'6/7 밤 · 그날 아침 「교사로 돌아간다」 선택 후',
 '50205':'회상 2쪽 5칸 · 원본 10/14 아침 쿄카\n「부끄러워도 신경 쓰지 않고 눌러앉는다」 선택 후',
 '50402':'회상 4쪽 2칸 · 원본 8/11 밤 마코토\n「얻어먹으러 간다」 선택 후'})
patch['conds']['25']='하루만 · 6/7 아침 「교사로 돌아간다」 선택 후'
for c in V['cards']:
    if any(str(no) in patch['ev_short'] for no in c['stages']):patch['stage_cols'][str(c['k'])]=2
for c in V['chips']:
    if any(str(no) in patch['ev_short'] for no in c['scenes']):patch['chip_cols'][str(c['c'])]=2
for no,short in patch['ev_short'].items():
    assert sum(0.5 if ord(c)<128 else 1 for c in short)+2<=20,(no,short)
for k in ['ev_head','ev_short','when_fix','conds']:
    for no,s in patch[k].items():assert not re.search(r'갈래\s*\d|\(답 \d+\)',s)
unread={k:{} for k in ['ev_head','ev_short','when_fix','conds']}
for no,text in patch['ev_head'].items():unread['ev_head'][no]=text.rsplit(' · ',1)[0]+' · 미열람 장면'
for no,text in patch['ev_short'].items():unread['ev_short'][no]=re.match(r'^(\d+\. |\d+번 )',text).group()+'미열람 장면'
for no in patch['when_fix']:unread['when_fix'][no]='선택 후 이어지는 미열람 장면'
unread['when_fix'].update({'70':'6/7 밤 · 그날 아침 선택에 따라 발생','50205':'회상 2쪽 5칸 · 10/14 아침 미열람 장면','50402':'회상 4쪽 2칸 · 8/11 밤 미열람 장면'})
unread['conds']['25']='하루만 · 6/7 아침 선택에 따라 발생'
write(O/'design/label_patch.json',dict(translator_model='Codex internal',translation_quality_sha256=sha(Path(r'P:\AI\Codex\skills\contextual-game-localization\references\translation-quality.md')),patch=patch,unread=unread,choices=evidence,shared=shared,
    scope='Calendar display getters only. Original choices, scenario outcomes, ending conditions, portraits, summaries and save layout unchanged.',
    notes=['Bare companion names removed from choice branches and verified common continuation titles. Actual companion outings remain unchanged.','Compact list/title labels summarize full choice wording; detail When preserves full existing Korean choice text.']))
print(json.dumps(dict(root=str(O),counts={k:len(v) for k,v in patch.items()},shared=shared),ensure_ascii=False,indent=2))
