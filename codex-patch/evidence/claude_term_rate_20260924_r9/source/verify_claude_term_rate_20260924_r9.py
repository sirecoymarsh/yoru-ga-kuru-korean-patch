"""Claude Opus 5.5 (2026-09-24) r9: every r8 check (r3/r5/r6/r7 + daily/weekly autosaves) against the r9 candidate, then the
per-character missing events:
- with nothing seen, each (character, category) count equals the catalog grouping the build recorded, the dated lines
  list every personal/story event, and nothing is marked 「지남」 on 4/1;
- with everything seen, counts are 0 and the page says every event was seen;
- a partial save lowers exactly the seen events; after the windows close (12/1) dated lines and months say 「지남」;
- the menu flow: 플레이 정보 -> 캐릭터별 남은 이벤트 -> a character -> 날짜 이벤트 보기 -> back.
"""
import collections,json,re
import build_claude_term_rate_20260924_r9 as e
import verify_claude_term_rate_20260924_r8 as V8
V7=V8.V7;V6=V7.V6;V5=V7.V5
for mod in (V8,V7,V6,V5):mod.e=e;mod.O=e.O
V5.v3.e=e;V5.v3.O=e.O
V8.NEW_FUNCTIONS=22;V8.STRICT_SHIFT=False
V5.v3.MENU_EXTRA=['캐릭터별 남은 이벤트']
b=e.b;a=e.a;O=e.O;proxy=V5.proxy;ko=V5.ko

class VM9(V8.VM8):
    def __init__(self):
        super().__init__();self.today=(4,1)
    def native(self,name,aa):
        if name=='L_Calendar::IsTodayOrBefore':return int(self.today<=(aa[0],aa[1]))
        return super().native(name,aa)

def main():
    V8.main()
    ev=a.readj(O/'build_evidence.json');cm=ev['char_missing'];counts=collections.Counter();v=VM9()
    cat=a.readj(e.CATALOG)['events'];fn_of={x['key']:x['fn'] for x in cat}
    rows={r['person']:r for r in cm['rows']}
    # 1. nothing seen on 4/1: counts equal the recorded grouping; every dated line present, none passed
    v.registered=set();v.today=(4,1)
    for p,name in e.CHARS:
        r=rows[p];assert ko(v.run('KR_T8CharName',[p]))==name
        for c,n in r['categories'].items():assert v.run('KR_T8MissCount',[p,int(c)])==n,(p,c,n)
        assert v.run('KR_T8MissCount',[p,999])==0
        assert v.run('KR_T8DatedCount',[p,0])==r['personal'] and v.run('KR_T8DatedCount',[p,1])==r['story'],p
        lines=[x for x in ko(v.run('KR_T8DatedLines',[p])).split('\n') if x]
        want=[d['text'] for d in cm['dated'] if d['person']==p];assert lines==want,(p,lines,want)
        text=ko(v.run('KR_T8CharMissingText',[p]))
        assert text.split('\n')[0]==f"{name} · 남은 이벤트 {r['total']} / {r['total']}" and '(지남)' not in text,text
        counts['empty_save_character_pages']+=1
    # 2. everything seen: nothing left
    v.registered={x['fn'] for x in cat}
    for p,name in e.CHARS:
        assert all(v.run('KR_T8MissCount',[p,int(c)])==0 for c in rows[p]['categories']) and v.run('KR_T8DatedLines',[p])==''
        assert ko(v.run('KR_T8CharMissingText',[p]))==f"{name} · 남은 이벤트 0 / {rows[p]['total']}\n이 저장에서 모두 봤습니다.";counts['complete_save_pages']+=1
    # 3. partial: 이즈미 saw E10001 and every April talk; 12/1 closes every window
    v.registered={fn_of['E10001']}|{x['fn'] for x in cat if any(t.get('kind')=='pool' and t.get('person')==2 and t.get('pool_kind')=='after_training' and t.get('month')==4 for t in x['triggers'])}
    assert v.run('KR_T8MissCount',[2,104])==0 and v.run('KR_T8MissCount',[2,105])==rows[2]['categories']['105']
    lines=[x for x in ko(v.run('KR_T8DatedLines',[2])).split('\n') if x];assert not any('4/21～6/16' in x for x in lines) and len(lines)==rows[2]['personal']+rows[2]['story']-1
    v.today=(12,1);lines=[x for x in ko(v.run('KR_T8DatedLines',[2])).split('\n') if x]
    assert all(x.endswith(' (지남)') for x in lines if '부터' not in x) and any('부터' in x and not x.endswith('(지남)') for x in lines),lines
    tl=ko(v.run('KR_T8CharMissingText',[2])).split('\n');i=tl.index('지난 달에 놓친 대화  5월 7 · 6월 6 · 7월 8')
    assert tl[i+1:i+3]==['　　8월 7 · 9월 8 · 10월 5','　　11월 6'] and not any(x.startswith('특훈 뒤 대화') for x in tl),tl;counts['partial_and_passed']+=1
    v.today=(7,10);tl=ko(v.run('KR_T8CharMissingText',[2])).split('\n')
    i=tl.index('특훈 뒤 대화  7월 8 · 8월 7 · 9월 8');assert tl[i+1]=='　　10월 5 · 11월 6' and tl[i+2]=='지난 달에 놓친 대화  5월 7 · 6월 6',tl
    counts['month_passed_boundary']+=1
    # every line fits the dialog frame (about 40 characters; the engine refuses a text texture wider than 2048px)
    widest=''
    for regs in [set(),{x['fn'] for x in cat if x['key'] in ('E10001','E20021','E30001')}]:
        for today in [(4,1),(7,10),(12,1)]:
            v.registered=regs;v.today=today
            for p,_ in e.CHARS:
                for x in ko(v.run('KR_T8CharMissingText',[p])).split('\n')+[ko(v.run('KR_T8CharName',[p]))+' · 날짜가 정해진 남은 이벤트']+ko(v.run('KR_T8DatedLines',[p])).split('\n'):
                    if len(x)>len(widest):widest=x
    assert len(widest)<=38,(len(widest),widest);counts['lines_fit_38_chars']+=1
    # 4. menu flow: player info (choice 3) -> character list (이즈미) -> page (날짜 이벤트 보기) -> dated page -> back x3
    v.registered=set();v.today=(5,1);v.titles=[];v.choices=[];v.dialog=[3,2,1,0,0,0,0]
    v.run('KR_T8PlayerInfoMenu');assert not v.dialog,v.dialog
    labels=[[c[1] for c in ch] for ch in v.choices]
    assert '캐릭터별 남은 이벤트' in labels[0] and labels[1][:7]==[f"{n}  {rows[p]['total']}" for p,n in e.CHARS] and labels[1][7]=='돌아가기',labels[:2]
    assert labels[2]==['날짜 이벤트 보기','돌아가기'] and labels[3]==['돌아가기'],labels[2:4]
    assert v.titles[1].startswith('캐릭터별 남은 이벤트') and v.titles[2].startswith('이즈미 · 남은 이벤트 126 / 126') and v.titles[3].startswith('이즈미 · 날짜가 정해진 남은 이벤트'),v.titles
    assert v.titles[3].endswith('본편 이벤트는 위 남은 수에 넣지 않았습니다.');counts['menu_flow']+=1
    # 5. no page text is wider than the widest line the r3 achievement page already shows (checked on screen by the probe)
    longest=max((x for p,_ in e.CHARS for x in ko(v.run('KR_T8DatedLines',[p])).split('\n')),key=len)
    counts['longest_dated_line_chars']=len(longest)
    res=a.readj(O/'vm_verification.json');res['r9']=dict(counts=dict(counts),longest_dated_line=longest)
    (O/'vm_verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r9=counts,longest=longest),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
