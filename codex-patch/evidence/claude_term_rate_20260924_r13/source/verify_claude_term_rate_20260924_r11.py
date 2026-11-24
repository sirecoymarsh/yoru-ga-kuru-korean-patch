"""Claude Opus 5.5 (2026-09-24) r11: the r10 checks on the marked-up pages (marks stripped), then the colour runs:
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
import build_claude_term_rate_20260924_r11 as e
import verify_claude_term_rate_20260924_r8 as V8
V7=V8.V7;V6=V7.V6;V5=V7.V5
for mod in (V8,V7,V6,V5):mod.e=e;mod.O=e.O
V5.v3.e=e;V5.v3.O=e.O
V5.v3.MENU_EXTRA=['캐릭터별 남은 이벤트'];V8.STRICT_SHIFT=False
FN=re.compile(r'(?m)^(?:int|string|bool|void) (KR_\w+)\(')
V8.NEW_FUNCTIONS=sum(len(FN.findall((e.HERE/n).read_text('utf8'))) for n in ['claude_autosave_20260924.jaf','claude_char_missing_20260924_r11.jaf','claude_dialog_color_20260924.jaf'])
import json as _j
V8.EXTRA_SITES=[_j.load(open(e.O/'build_evidence.json',encoding='utf8'))['title_color']['site']]
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
    res=a.readj(O/'vm_verification.json');res['r11']=dict(counts=dict(counts),widest=widest,tallest=tallest,raw_widest=raw_widest)
    (O/'vm_verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r11=counts,widest=widest,tallest=tallest,raw_widest=raw_widest),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
