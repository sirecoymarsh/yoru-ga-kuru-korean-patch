"""Claude Opus 5.5 (2026-09-24) r14: the r13 checks plus the next-floor question skip (StepedOnCell site; KR_T8FloorDialog
with Codex's real KR_ExploreFloorDialog code and the dialog, KR_Flag and KR_Poke stubbed).

r13 docstring: Claude Opus 5.5 (2026-09-24) r13: the r12 checks plus the home-panel pick (RunHome relocated with exactly two
insertions; row mapping, click gating, menu open/close and clickable parts with the engine calls stubbed).

r12 docstring: Claude Opus 5.5 (2026-09-24) r12: the r11 checks plus the dungeon-talk continuation (four swapped call sites; talk begin,
RunEvent start/end and talk end with KR_Flag/KR_Poke, KR_WalkStop, the auto mode calls, the engine's auto/skip restore and
release and Ａ＿全表示 stubbed).

r11 docstring: Claude Opus 5.5 (2026-09-24) r11: the r10 checks on the marked-up pages (marks stripped), then the colour runs:
segment parsing, raw line length (marks count in the dialog width) and the same-length title-draw site.

r10 docstring: every r8 check (r3/r5/r6/r7 + daily/weekly autosaves) against the r10 candidate, then the
missing-events pages by place / date / dungeon party:
- nothing seen (4/1): place rows equal the catalog grouping, every month row and every dated event is listed, nothing passed;
- everything seen: every page says so;
- partial save on 7/10 (이즈미 saw E10001 and every April talk): talks split into this month on / missed months, dated events
  sit in the month they open (or this month once open), passed ones go to 「지나감」 and to the conditions page with 「(지남)」;
- the menu flow place -> date -> conditions -> back -> party -> back;
- every line <= 38 characters and every page <= 14 lines in all states (the dialog widens with its longest line).
"""
import collections,json,re
import build_claude_term_rate_20260924_r14 as e
import verify_claude_term_rate_20260924_r8 as V8
V7=V8.V7;V6=V7.V6;V5=V7.V5
for mod in (V8,V7,V6,V5):mod.e=e;mod.O=e.O
V5.v3.e=e;V5.v3.O=e.O
V5.v3.MENU_EXTRA=['캐릭터별 남은 이벤트'];V8.STRICT_SHIFT=False
FN=re.compile(r'(?m)^(?:int|string|bool|void) (KR_\w+)\(')
V8.NEW_FUNCTIONS=sum(len(FN.findall((e.HERE/n).read_text('utf8'))) for n in ['claude_autosave_20260924.jaf','claude_char_missing_20260924_r11.jaf','claude_dialog_color_20260924.jaf','claude_talk_continue_20260924.jaf','claude_home_pick_20260924.jaf','claude_floor_skip_20260924.jaf'])
import json as _j
_ev=_j.load(open(e.O/'build_evidence.json',encoding='utf8'))
V8.EXTRA_SITES=[_ev['title_color']['site']]+[x['site'] for x in _ev['talk_continue']['sites']]+[_ev['floor_skip']['site']]
V8.EXTRA_RELOCATED=[28543]   # r13: C_SceneHomebase@RunHome (checked below: original + exactly two insertions)
MARKS={ord(c):None for c in '†‡¶〓'}
b=e.b;a=e.a;O=e.O;proxy=V5.proxy;ko=V5.ko

class VM10(V8.VM8):
    def __init__(self):
        super().__init__();self.today=(4,1)
    def native(self,name,aa):
        if name=='L_Calendar::IsTodayOrBefore':return int(self.today<=(aa[0],aa[1]))
        return super().native(name,aa)

def raw_lines(v,fn,p):return ko(v.run(fn,[p])).split('\n')
def lines(v,fn,p):return [x.translate(MARKS) for x in raw_lines(v,fn,p)]

def main():
    V8.main()
    ev=a.readj(O/'build_evidence.json');rows={r['person']:r for r in ev['char_missing']['rows']};d10=ev['char_missing_r10']['dated']
    counts=collections.Counter();v=VM10();cat=a.readj(e.CATALOG)['events'];fn_of={x['key']:x['fn'] for x in cat}
    cats=lambda p:{int(k):n for k,n in rows[p]['categories'].items()}
    # 1. nothing seen on 4/1
    v.registered=set();v.today=(4,1)
    for p,name in e.CHARS:
        c=cats(p);total=rows[p]['total'];dated=[d for d in d10 if d['person']==p]
        for k,n in c.items():assert v.run('KR_T8MissCount',[p,k])==n,(p,k)
        pl=lines(v,'KR_T8PlaceText',p);assert pl[0]==f'{name} · 아직 못 본 이벤트 {total}개 / 전체 {total}개',pl[0]
        talk=sum(n for k,n in c.items() if 104<=k<=111);walk=sum(n for k,n in c.items() if k>=300)+c.get(203,0)
        want=[(f'특훈 뒤 대화',talk),('반한 뒤 대화',c.get(200,0)),('특훈 권유',c.get(201,0)),('토요일 초대',c.get(202,0)),('던전 안 대화',walk),('날짜가 정해진 이벤트',len(dated))]
        assert pl[1:]==[f'　{l}　{n}개' for l,n in want if n>0],(p,pl)
        dl=lines(v,'KR_T8DateText',p);assert dl[0]==f'{name} · 날짜별로 남은 이벤트' and not any('지나감' in x for x in dl),dl
        for m in range(4,12):
            t=c.get(100+m,0);dd=sum(1 for d in dated if d['frm'][0]==m)
            row=[x for x in dl if x.startswith(f'　{m}월　')]
            if t+dd==0:assert not row,(p,m,row)
            else:
                exp=f'　{m}월　'+(f'특훈 뒤 대화 {t}개' if t else '')+(' · ' if t and dd else '')+(f'날짜 이벤트 {dd}개' if dd else '')
                assert row==[exp],(p,m,row,exp)
        cl=lines(v,'KR_T8CondText',p);assert cl[0]==f'{name} · 날짜가 정해진 이벤트'
        assert [x for x in cl[1:] if not x.startswith(('개인 이벤트','본편 이벤트'))]==[d['open'].translate(MARKS) for d in dated],(p,cl)
        pt=lines(v,'KR_T8PartyText',p)
        assert pt[1:]==[f'　{ko(v.run("KR_T8CharName",[q]))}와 함께　{c[300+q]}개' for q in range(2,9) if c.get(300+q)]+([f'　누구와 가든　{c[300]}개'] if c.get(300) else [])+([f'　처음 데려갈 때　{c[203]}개'] if c.get(203) else []),pt
        counts['empty_save_pages']+=1
    # 2. everything seen
    v.registered={x['fn'] for x in cat}
    for p,name in e.CHARS:
        assert lines(v,'KR_T8PlaceText',p)[1:]==['이 저장에서 모두 봤습니다.'] and lines(v,'KR_T8DateText',p)[1:]==['이 저장에서 모두 봤습니다.']
        assert lines(v,'KR_T8PartyText',p)[1:]==['던전에서 볼 대화는 모두 봤습니다.'] and lines(v,'KR_T8CondText',p)==[f'{name} · 날짜가 정해진 이벤트']
        counts['complete_save_pages']+=1
    # 3. partial save on 7/10: 이즈미 saw E10001 and every April talk
    april={x['fn'] for x in cat if any(t.get('kind')=='pool' and t.get('person')==2 and t.get('pool_kind')=='after_training' and t.get('month')==4 for t in x['triggers'])}
    v.registered={fn_of['E10001']}|april;v.today=(7,10);c=cats(2)
    pl=lines(v,'KR_T8PlaceText',2);talk=sum(c[100+m] for m in range(7,12));missed=c[105]+c[106]
    assert pl[1]==f'　특훈 뒤 대화　{talk}개' and pl[2]==f'　　지난 달에 놓친 대화　{missed}개',pl
    assert pl[-2:]==['　날짜가 정해진 이벤트　4개','　　날짜가 지난 이벤트　1개'],pl
    dl=lines(v,'KR_T8DateText',2)
    assert dl[1:6]==[f'　7월　특훈 뒤 대화 {c[107]}개',f'　8월　특훈 뒤 대화 {c[108]}개 · 날짜 이벤트 2개',f'　9월　특훈 뒤 대화 {c[109]}개 · 날짜 이벤트 1개',
                     f'　10월　특훈 뒤 대화 {c[110]}개 · 날짜 이벤트 1개',f'　11월　특훈 뒤 대화 {c[111]}개'],dl
    assert dl[-1]==f'　지나감　{missed+1}개 (이번 회차엔 볼 수 없음)' and dl[-2].startswith('　언제든 (날짜 무관)　'),dl
    cl=lines(v,'KR_T8CondText',2);op={d['key']:d for d in d10 if d['person']==2}
    assert cl[1]=='개인 이벤트 (특훈 뒤에 나옴)' and cl[2:5]==[op['E10061']['open'].translate(MARKS),op['E10041']['open'].translate(MARKS),op['E10101']['open'].translate(MARKS)] and cl[5]==op['E10021']['passed'].translate(MARKS),cl
    assert cl[6:]==['본편 이벤트 (달성률에는 넣지 않음)',op['E10081']['open'].translate(MARKS)],cl;counts['partial_on_7_10']+=1
    # 4. widths and heights in every state
    widest='';tallest=0
    for regs in [set(),{fn_of[k] for k in ('E10001','E20021','E30001','E40001')}|april,{x['fn'] for x in cat}]:
        for today in [(4,1),(6,20),(7,10),(9,9),(10,16),(12,1)]:
            v.registered=regs;v.today=today
            for p,_ in e.CHARS:
                for fn in ('KR_T8PlaceText','KR_T8DateText','KR_T8CondText','KR_T8PartyText'):
                    ls=lines(v,fn,p);tallest=max(tallest,len(ls));widest=max([widest]+ls,key=len)
    assert len(widest)<=38 and tallest<=14,(len(widest),widest,tallest);counts['every_line_fits']+=1
    # 5. menu flow: info(3) -> list(이즈미) -> place(날짜별) -> date(조건) -> cond(back) -> date(back) -> place(파티) -> party(back) -> place(back) -> list(back) -> info(close)
    v.registered=set();v.today=(5,1);v.titles=[];v.choices=[];v.dialog=[3,2,1,1,0,0,2,0,0,0,0]
    v.run('KR_T8PlayerInfoMenu');assert not v.dialog,v.dialog
    heads=[t.split('\n')[0].translate(MARKS) for t in v.titles]
    assert heads[1:10]==['캐릭터별 남은 이벤트','이즈미 · 아직 못 본 이벤트 126개 / 전체 126개','이즈미 · 날짜별로 남은 이벤트','이즈미 · 날짜가 정해진 이벤트',
                         '이즈미 · 날짜별로 남은 이벤트','이즈미 · 아직 못 본 이벤트 126개 / 전체 126개','이즈미 · 던전에서 볼 대화 (파티에 같이 넣기)',
                         '이즈미 · 아직 못 본 이벤트 126개 / 전체 126개','캐릭터별 남은 이벤트'],heads
    labels=[[x[1] for x in ch] for ch in v.choices]
    assert labels[2]==['날짜별로 보기','던전 파티별로 보기','돌아가기'] and labels[3]==['날짜 이벤트 조건','돌아가기'] and labels[4]==['돌아가기'] and labels[7]==['돌아가기'],labels
    counts['menu_flow']+=1
    # r11: marks count in the dialog width (C_SelectDialog@CreateParts uses the raw length)
    raw_widest=''
    for regs in [set(),{fn_of[k] for k in ('E10001','E20021','E30001','E40001')}|april,{x['fn'] for x in cat}]:
        for today in [(4,1),(6,20),(7,10),(9,9),(10,16),(12,1)]:
            v.registered=regs;v.today=today
            for p,_ in e.CHARS:
                for fn in ('KR_T8PlaceText','KR_T8DateText','KR_T8CondText','KR_T8PartyText'):
                    raw_widest=max([raw_widest]+raw_lines(v,fn,p),key=len)
    assert len(raw_widest)<=38,(len(raw_widest),raw_widest);counts['raw_lines_fit']+=1
    # segment parsing (what KR_T8TitleDraw draws per run)
    row=proxy('　†특훈 뒤 대화　‡14개');assert v.run('KR_T8SegCount',[row])==3
    assert [ko(v.run('KR_T8SegText',[row,k])) for k in range(3)]==['　','특훈 뒤 대화　','14개'] and [v.run('KR_T8SegColor',[row,k]) for k in range(3)]==[0,1,2]
    row=proxy('쿄카 · 아직 못 본 이벤트 ‡117개〓 / 전체 129개');assert [ko(v.run('KR_T8SegText',[row,k])) for k in range(3)]==['쿄카 · 아직 못 본 이벤트 ','117개',' / 전체 129개'] and [v.run('KR_T8SegColor',[row,k]) for k in range(3)]==[0,2,0]
    row=proxy('　¶5/26～6/30　친밀도 25 이상　(지남)');assert v.run('KR_T8SegCount',[row])==2 and v.run('KR_T8SegColor',[row,1])==3
    for p,_ in e.CHARS:
        for fn in ('KR_T8PlaceText','KR_T8DateText','KR_T8CondText','KR_T8PartyText'):
            t=v.run(fn,[p]);assert ko(v.run('KR_T8Plain',[t]))==ko(t).translate(MARKS)
    counts['segment_parsing']+=1
    # opt-in gate: C_SelectDialog draws '　'+title+'　' (native spy 2026-09-24); the bare title is accepted too, nothing else
    t=proxy('쿄카 · 아직 못 본 이벤트\n　†특훈 뒤 대화　‡14개');sp=proxy('　')
    v.cache['YoruKR.T8.Title']=t;v.cache['YoruKR.T8.Color']='1'
    assert v.run('KR_T8TitleOptIn',[sp+t+sp])==1 and v.run('KR_T8TitleOptIn',[t])==1,'padded or bare title must opt in'
    assert v.run('KR_T8TitleOptIn',[sp+t])==0 and v.run('KR_T8TitleOptIn',[t+sp])==0 and v.run('KR_T8TitleOptIn',[proxy('다른 제목')])==0,'other text must fall through'
    v.cache['YoruKR.T8.Color']='';assert v.run('KR_T8TitleOptIn',[sp+t+sp])==0,'colour flag off'
    v.cache['YoruKR.T8.Color']='1';v.cache['YoruKR.T8.Title']='';assert v.run('KR_T8TitleOptIn',[sp+sp])==0 and v.run('KR_T8TitleOptIn',[''])==0,'no title published'
    v.cache['YoruKR.T8.Color']='';counts['title_opt_in']+=1
    # the swapped title draw call
    info=a.readj(O/'build_evidence.json')['title_color'];m=b.read_meta(O/'candidate_meta.json')
    fnid=lambda s:next(f['index'] for f in m['functions'] if b.raw_symbol(m,f['index'])==s)
    raw=b.unpack((O/'NightRemaster.ain').read_bytes());base=b.unpack((O/'baseline_NightRemaster.ain').read_bytes());import struct
    assert struct.unpack_from('<Hi',raw,16+info['site'])==(0x30,fnid('KR_T8TitleDraw')) and struct.unpack_from('<Hi',base,16+info['site'])==(0x30,fnid('Ｐ＿構築手順＿テキストアルファブレンド'))
    counts['title_draw_site']+=1
    # r12 talk: the four swapped calls, then TalkBegin -> (Hide) -> RunEvent start/end hooks -> TalkEnd with the engine stubbed
    tinfo=a.readj(O/'build_evidence.json')['talk_continue']
    assert len(tinfo['sites'])==4,tinfo
    for sinfo in tinfo['sites']:
        assert struct.unpack_from('<Hi',raw,16+sinfo['site'])==(0x30,fnid(sinfo['replacement'])) and struct.unpack_from('<Hi',base,16+sinfo['site'])==(0x30,fnid(sinfo['original'])),sinfo
        counts['talk_sites']+=1
    world=dict(flag=0,auto=0,saved=0,stops=0,shows=[]);orig_native=v.native;orig_hll=v.hll;OWN=2026092203
    def native(name,aa):
        if name=='KR_Flag':assert list(aa)==[71],aa;return world['flag']
        if name=='KR_Poke':assert aa[0]==71,aa;world['flag']=aa[1];return None
        if name=='KR_WalkStop':world['stops']+=1;return None
        if name=='Ａ＿オートモード中確認':return world['auto']
        if name=='Ｓ＿オート':world['auto']=1-world['auto'];return None
        if name=='Ａ＿オートモード解除':world['auto']=0;return None
        if name=='Ａ＿全表示':world['shows'].append(tuple(aa));return None
        # engine (LSys3xScript): restore = toggle when the saved state differs (and flip the saved bit); release = save, then off
        if name=='LSys3xScript::ForceRestoreSkipAutpState':
            if world['saved']!=world['auto']:world['saved']=1-world['saved'];world['auto']=1-world['auto']
            return None
        if name=='LSys3xScript::ForceReleaseSkipAutpState':world['saved']=world['auto'];world['auto']=0;return None
        return orig_native(name,aa)
    def hll(lib,method,st,ops,pc,loc,li):
        if lib=='String' and method=='ToInt':x=st.pop();st.append(int(x) if x else 0);return
        return orig_hll(lib,method,st,ops,pc,loc,li)
    v.native=native;v.hll=hll
    def hide():
        if world['flag']==OWN:world['flag']=-OWN
    def event(during=lambda:None):
        v.run('KR_T8EventStart',[]);seen=world['auto'];during();v.run('KR_T8EventEnd',[]);return seen
    def talk(flag,saved,during=lambda:None):
        world.update(flag=flag,auto=0,saved=saved,stops=0,shows=[])
        v.run('KR_T8TalkBegin',[0]);hide();seen=event(during);v.run('KR_T8TalkEnd',[1,200]);return seen
    seen=talk(OWN,0);assert seen==1 and world['auto']==0 and world['saved']==0 and world['flag']==OWN and world['stops']==0 and world['shows']==[(1,200)],(seen,world);counts['talk_moving_run_auto_and_resumes']+=1
    seen=talk(OWN,1);assert seen==1 and world['auto']==0 and world['saved']==1 and world['flag']==OWN,(seen,world);counts['talk_player_auto_setting_kept']+=1
    def click():world['auto']=0
    seen=talk(OWN,0,click);assert seen==1 and world['saved']==0 and world['flag']==OWN,(seen,world);counts['talk_click_released_auto']+=1
    seen=talk(0,0);assert seen==0 and world['stops']==1 and world['saved']==0 and world['flag']==0 and world['shows']==[(1,200)],(seen,world);counts['talk_manual_walk_unchanged']+=1
    seen=talk(0,1);assert seen==1 and world['saved']==1 and world['flag']==0,(seen,world);counts['talk_manual_walk_player_auto']+=1
    seen=talk(-OWN,0);assert seen==1 and world['flag']==-OWN and world['saved']==0,(seen,world);counts['talk_pending_object_kept']+=1
    def lost():world['flag']=0
    seen=talk(OWN,0,lost);assert seen==1 and world['flag']==0 and world['saved']==0 and world['auto']==0,(seen,world);counts['talk_lost_walk_not_revived_setting_kept']+=1
    # a later event with a stale mark (save loaded during a talk: the walk is cleared) behaves like the engine alone
    world.update(flag=0,auto=0,saved=1);v.cache['YoruKR.T8.TalkFlag']=str(OWN);v.cache['YoruKR.T8.TalkAuto']='1'
    seen=event();assert seen==1 and world['saved']==1 and v.cache['YoruKR.T8.TalkFlag']=='' and v.cache['YoruKR.T8.TalkAuto']=='',(seen,world);counts['talk_stale_mark_dropped']+=1
    world.update(flag=OWN,auto=0,saved=0);seen=event();assert seen==0 and world['saved']==0,(seen,world)
    world.update(flag=OWN,auto=0,saved=1);seen=event();assert seen==1 and world['saved']==1,(seen,world);counts['talk_other_events_unchanged']+=1
    world.update(flag=-OWN,auto=0,shows=[]);v.run('KR_T8TalkEnd',[1,200]);assert world['flag']==-OWN and world['shows']==[(1,200)],world;counts['talk_end_without_begin']+=1
    assert v.cache['YoruKR.T8.TalkFlag']=='' and v.cache['YoruKR.T8.TalkAuto']==''
    v.native=orig_native;v.hll=orig_hll
    # r13 home pick: RunHome relocated = original + exactly the two insertions (labels renamed in order of definition)
    import re as _re
    def _norm(text):
        lines=[l for l in text.splitlines() if l.strip() and not l.startswith((';','FUNC ','ENDFUNC '))]
        labels=[l[:-1] for l in lines if _re.fullmatch(r'0x[0-9a-f]+:',l)]
        names={x:f'L{i}' for i,x in enumerate(labels)}
        return '\n'.join(_re.sub(r'\b0x[0-9a-f]+\b',lambda z:names.get(z[0],z[0]),l) for l in lines)+'\n',names
    orig,on=_norm((O/'original_28543.jam').read_text('utf8'));built,bn=_norm((O/'built_28543.jam').read_text('utf8'))
    call=e.HOME_MENU_CALL;loop=on['0x6026b2']
    assert orig.count(call)==1 and built==orig.replace(call,'\tCALLFUNC KR_T8HomeMenuOpen\n'+call+'\t.LOCALREF res\n\tCALLFUNC KR_T8HomeMenuClose\n\tIFNZ '+loop+'\n'),'RunHome relocation is not original + insertions'
    assert 28543 in a.readj(O/'build_evidence.json')['relocated'];counts['home_runhome_relocated_exact']+=1
    # r13 home pick: row mapping, click gating, menu open/close, clickable parts (engine calls stubbed)
    CODE=2026092401
    for y,p in [(0,0),(51,0),(52,0),(219,0),(220,2),(243,2),(244,3),(256,3),(364,8),(387,8),(388,0),(700,0)]:
        assert v.run('KR_T8HomeRow',[y])==p,(y,v.run('KR_T8HomeRow',[y]))
    counts['home_row_mapping']+=1
    rec=dict(ends=[],clickable=[],page=[],bind=[],inputs=[],parts=[]);orig_native2=v.native
    def native2(name,aa):
        if name=='AFL_Parts_EndWaitForClick':rec['ends'].append(aa[0]);return None
        if name=='KR_T8CharMissingPage':rec['page'].append(aa[0]);return None
        if name=='KR_T8HomeBindClick':rec['bind'].append(aa[0]);return None
        if name=='AFL_Parts_SetEnableInputProcess':rec['inputs'].append((aa[0],int(aa[1])));return None
        if name=='Ｐ＿クリック可能設定':rec['parts'].append((aa[0],int(aa[1])));return None
        if name=='AFL_Activity_IsExistPartsByName':return int(aa[1]=='KR_HomeRateBody' and aa[0] in ('Game\\Scenes\\Common\\AddArea.pact','Game\\Scenes\\Common\\AddArea.pact:1'))
        if name=='AFL_Activity_GetPartsNumber':return {'Game\\Scenes\\Common\\AddArea.pact':102,'Game\\Scenes\\Common\\AddArea.pact:1':202}[aa[0]]
        return orig_native2(name,aa)
    v.native=native2;orig_hll2=v.hll
    def hll2(lib,method,st,ops,pc,loc,li):
        if lib=='String' and method=='ToInt':x=st.pop();st.append(int(x) if x else 0);return
        return orig_hll2(lib,method,st,ops,pc,loc,li)
    v.hll=hll2
    def reset():
        for k in rec:rec[k]=[]
    v.cache['YoruKR.T8.HomeMenu']='1';v.cache['YoruKR.T8.HomePick']='';reset()
    v.run('KR_T8HomeClick',[102,40,256]);assert rec['ends']==[CODE] and v.cache['YoruKR.T8.HomePick']=='3' and v.cache['YoruKR.T8.HomeMenu']=='',(rec,v.cache.get('YoruKR.T8.HomePick'))
    v.run('KR_T8HomeClick',[102,40,280]);assert rec['ends']==[CODE] and v.cache['YoruKR.T8.HomePick']=='3',rec;counts['home_click_once_per_wait']+=1
    v.cache['YoruKR.T8.HomeMenu']='1';v.cache['YoruKR.T8.HomePick']='';reset()
    for y in [60,160,200,400]:v.run('KR_T8HomeClick',[102,40,y])
    assert rec['ends']==[] and v.cache['YoruKR.T8.HomeMenu']=='1' and v.cache['YoruKR.T8.HomePick']=='',rec;counts['home_click_other_rows_ignored']+=1
    v.cache['YoruKR.T8.HomeMenu']='';reset();v.run('KR_T8HomeClick',[102,40,256]);assert rec['ends']==[] and v.cache['YoruKR.T8.HomePick']=='',rec;counts['home_click_outside_menu_ignored']+=1
    reset();assert v.run('KR_T8HomeClickable',[1])==2 and rec['bind']==[102,202] and rec['inputs']==[(102,1),(202,1)] and rec['parts']==[(102,1),(202,1)],rec
    reset();assert v.run('KR_T8HomeClickable',[0])==2 and rec['bind']==[] and rec['inputs']==[] and rec['parts']==[(102,0),(202,0)],rec;counts['home_clickable_parts']+=1
    reset();v.cache['YoruKR.T8.HomePick']='7';v.run('KR_T8HomeMenuOpen');assert v.cache['YoruKR.T8.HomeMenu']=='1' and v.cache['YoruKR.T8.HomePick']=='' and rec['parts']==[(102,1),(202,1)],rec;counts['home_menu_open']+=1
    for res,pick,want,page in [(11,'',0,[]),(14,'3',0,[]),(-1,'',0,[]),(CODE,'4',1,[4]),(CODE,'',1,[]),(CODE,'9',1,[]),(CODE,'1',1,[])]:
        reset();v.cache['YoruKR.T8.HomeMenu']='1';v.cache['YoruKR.T8.HomePick']=pick
        assert v.run('KR_T8HomeMenuClose',[res])==want and rec['page']==page and v.cache['YoruKR.T8.HomeMenu']=='' and rec['parts']==[(102,0),(202,0)],(res,pick,rec)
        if res==CODE:assert v.cache['YoruKR.T8.HomePick']==''
        counts['home_menu_close_cases']+=1
    v.native=orig_native2;v.hll=orig_hll2
    # r14 floor skip: StepedOnCell's KR_ExploreFloorDialog call swapped; KR_T8FloorDialog with Codex's real dialog code
    finfo=a.readj(O/'build_evidence.json')['floor_skip']
    assert struct.unpack_from('<Hi',raw,16+finfo['site'])==(0x30,fnid('KR_T8FloorDialog')) and struct.unpack_from('<Hi',base,16+finfo['site'])==(0x30,fnid('KR_ExploreFloorDialog')),finfo
    counts['floor_site']+=1
    fw=dict(flag=0);orig_native3=v.native;orig_hll3=v.hll;OWN=2026092203
    def native3(name,aa):
        if name=='KR_Flag':assert list(aa)==[71],aa;return fw['flag']
        if name=='KR_Poke':assert aa[0]==71,aa;fw['flag']=aa[1];return None
        return orig_native3(name,aa)
    def hll3(lib,method,st,ops,pc,loc,li):
        if lib=='String' and method=='ToInt':x=st.pop();st.append(int(x) if x else 0);return
        return orig_hll3(lib,method,st,ops,pc,loc,li)
    v.native=native3;v.hll=hll3
    def floor(flag,pending,auto,dialog):
        fw['flag']=flag;v.cache['YoruKR.Explore.Pending']=pending;v.cache['YoruKR.Explore.AutoFloor']=auto;v.cache['YoruKR.Explore.FloorResume']=''
        v.dialog=list(dialog);v.exec_titles=[];r=v.run('KR_T8FloorDialog',[1,200]);return r,len(v.exec_titles),v.dialog
    r,shown,left=floor(-OWN,'2','',[]);assert r==1 and shown==0 and v.cache['YoruKR.Explore.FloorResume']=='1' and v.cache['YoruKR.Explore.AutoFloor']=='',(r,shown,v.cache.get('YoruKR.Explore.FloorResume'));counts['floor_walk_skips_question']+=1
    r,shown,left=floor(OWN,'2','1',[]);assert r==1 and shown==0 and v.cache['YoruKR.Explore.FloorResume']=='1' and v.cache['YoruKR.Explore.AutoFloor']=='1';counts['floor_trip_preference_kept']+=1
    r,shown,left=floor(-OWN,'0','',[1]);assert r==1 and shown==1 and not left and v.cache['YoruKR.Explore.FloorResume']=='0';counts['floor_walk_not_from_gate_asks']+=1
    r,shown,left=floor(0,'','',[2]);assert r==2 and shown==1 and v.cache['YoruKR.Explore.FloorResume']=='0' and fw['flag']==0;counts['floor_manual_asks']+=1
    r,shown,left=floor(0,'','1',[]);assert r==1 and shown==0 and v.cache['YoruKR.Explore.FloorResume']=='0' and v.cache['YoruKR.Explore.AutoFloor']=='1';counts['floor_manual_trip_preference']+=1
    v.native=orig_native3;v.hll=orig_hll3
    res=a.readj(O/'vm_verification.json');res['r14']=dict(counts=dict(counts),widest=widest,tallest=tallest,raw_widest=raw_widest)
    (O/'vm_verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r14=counts,widest=widest,tallest=tallest,raw_widest=raw_widest),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
