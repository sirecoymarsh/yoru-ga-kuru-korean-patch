"""Claude Opus 5.5 (2026-09-24) r5: every r3 VM check against the r5 candidate, the r4 checks (colour-aware),
and the r5 additions (bounded execution of the compiled candidate JAM, native HLLs modelled):
- colour rules for treasure / trap / receipt / sweep texts, hand-written expected tagged strings;
- josa is resolved before tags go in, tagged text is left alone by KR_ResolveJosa and by a second pass;
- per-character event counts against the catalog; panel text;
- relocated KR_ChestShow / KR_NoticeShow / KR_SweepReport = original + one reassignment,
  C_MessageDialog@Create = original + the conditional Tag::set block before Text::set.
Screens (tag rendering in each part, the sweep dialog, the panel) are checked natively and by the user.
"""
from pathlib import Path
import collections,copy,json,re,struct,sys
import build_claude_term_rate_20260924_r5 as e
import verify_claude_term_rate_20260924 as v3
v3.e=e;v3.O=e.O
b=e.b;a=e.a;O=e.O
proxy=v3.proxy;ko=v3.ko
AREA='Game\\Scenes\\Common\\AddArea.pact'
GOLD='r=255 g=224 b=96';CYAN='r=128 g=224 b=255';GREEN='r=128 g=255 b=144';RED='r=255 g=120 b=104';ORANGE='r=255 g=176 b=88'
PURPLE='r=208 g=150 b=255';YELLOW='r=255 g=240 b=120';GRAY='r=176 g=176 b=176';DARK='r=190 g=130 b=255'
def T(s,c):return '' if s=='' else '${font '+c+'}'+s+'${/font}'
CLEAR='함정 해제 성공 · 피해 없음'
PARTS={'KR_ChestTitle':55,'KR_ChestLine1':61,'KR_ChestLine2':62,'KR_ChestLine3':63,'KR_ReceiptBody':71}

class VM5(v3.VM):
    def __init__(self):
        super().__init__()
        self.notices=[];self.get_trap=False;self.instant=False;self.relieve=True;self.in_dungeon=True
        self.acts={};self.texts=[];self.shows=[];self.writes=[];self.tags=[];self.colors=[];self.registered=set();self.receipts=[]
    def native(self,name,aa):
        if name=='KR_ChestShow':self.notices.append(ko(aa[0]));return None
        if name=='KR_NoticeShow':self.receipts.append(ko(aa[0]));return None
        if name=='KR_ChestPart':return PARTS.get(aa[0],-1) if self.in_dungeon else -1
        if name=='KR_ChestWrite':self.writes.append((aa[0],ko(aa[1])));return None
        if name=='KR_NoticeInstant':return int(self.instant)
        if name=='KR_GetTrap':return int(self.get_trap)
        if name=='L_Dungeon::RelieveTrap':return int(self.relieve)
        if name=='KR_T8TrapCell':return trap_cell(self,aa[0])
        if name=='AFL_Activity_IsExistPartsByName':return int(aa[1] in self.acts.get(aa[0],{}))
        if name=='AFL_Activity_GetPartsNumber':return self.acts[aa[0]][aa[1]]
        if name=='Ｐ＿テキスト設定':self.texts.append((aa[0],ko(aa[1]),aa[2]));return None
        if name=='Ｐ＿表示設定':self.shows.append((aa[0],int(aa[1])));return None
        if name=='Ｐ＿テキストタグ有効設定':self.tags.append((aa[0],int(aa[1]),aa[2]));return None
        if name=='Ｐ＿フォント色設定':self.colors.append(tuple(aa));return None
        if name=='N_ScenarioRegister::IsRegisteredEvent':return int(aa[0] in self.registered)
        return super().native(name,aa)

GETTERS={27005:'ObjectId',27008:'ObjectSubId',27029:'IsEventDungeon'}
def trap_cell(vm,cell):
    fid=vm.fs['KR_T8TrapCell']['index'];ops,labels=vm.load(fid);st=[];pc=0;n=0
    while True:
        op,*rest=ops[pc];arg=rest[0] if rest else '';pc+=1;n+=1;assert n<100
        if op=='.LOCALREF':assert arg=='cell';st.append(cell)
        elif op=='PUSH':st.append(int(arg,0))
        elif op=='CALLMETHOD':
            assert arg=='0';mid=st.pop();obj=st.pop();st.append(int(obj[GETTERS[mid]]))
        elif op=='NOTE':z=st.pop();x=st.pop();st.append(int(x!=z))
        elif op in ['IFZ','IFNZ']:
            if bool(st.pop())==(op=='IFNZ'):pc=labels[arg]
        elif op=='RETURN':assert len(st)==1;return st[0]
        else:raise AssertionError(('KR_T8TrapCell op',op))

def norm(text):
    out=[]
    for l in text.splitlines():
        s=l.rstrip()
        if not s or s.startswith(';') or s.startswith('EOF ') or s.startswith('ENDFUNC '):continue
        out.append(re.sub(r'0x[0-9a-f]+','ADDR',s))
    return out
def static_relocations(ev,counts):
    ids=ev['added_functions'];by={f['name']:f['index'] for f in b.read_meta(O/'candidate_meta.json')['functions']}
    want={28571:'\tCALLFUNC KR_T8HomeEnter\n',28572:'\tCALLFUNC KR_T8HomeLeave\n',
          29817:e.checkbox_sync(29827,ids['KR_T8HomeRateGet']),29818:e.checkbox_sync(29828,ids['KR_T8HomeRateSet']),
          by['KR_ChestShow']:e.reassign('text','KR_T8ChestColor'),by['KR_NoticeShow']:e.reassign('text','KR_T8ReceiptColor'),
          by['KR_SweepReport']:e.reassign('txt','KR_T8SweepColor')}
    for fid,code in want.items():
        orig=norm((O/f'original_{fid}.jam').read_text('utf8'));built=norm((O/f'built_{fid}.jam').read_text('utf8'));ins=norm(code)
        assert built[0]==orig[0] and built[1:1+len(ins)]==ins and built[1+len(ins):]==orig[1:],(fid,built[:12],orig[:6])
        counts['relocated_body_is_original_plus_prefix']+=1
    orig=(O/'original_27778.jam').read_text('utf8');built=(O/'built_27778.jam').read_text('utf8')
    o=norm(orig);bl=norm(built);ins=[x.replace('kr_t8_msgdlg_plain','ADDR') for x in norm(e.TAG_ON)];anchor=norm(e.TEXT_SET)
    k=next(i for i in range(len(o)) if o[i:i+len(anchor)]==anchor)
    # the label line of the inserted block is renamed by the assembler to an address; compare with it normalised
    assert bl[:k]==o[:k] and bl[k+len(ins):]==o[k:] and bl[k:k+len(ins)-1]==ins[:-1] and bl[k+len(ins)-1]=='ADDR:',(bl[k:k+len(ins)+2])
    assert '\tPUSH 25' in bl[k:k+len(ins)] and '\tCALLHLL String Find 0' in bl[k:k+len(ins)];counts['message_dialog_tag_block_only_change']+=1

def main():
    v3.main()
    ev=a.readj(O/'build_evidence.json');counts=collections.Counter();v=VM5()
    call=lambda n,*args:v.run(n,[proxy(x) if isinstance(x,str) else x for x in args])
    static_relocations(ev,counts)
    # 1. r4 trap flow, now coloured at KR_T8TrapNotice.
    for oid in [0,3,5,6,7]:
        for evd in [0,1]:
            for sub in [0,1,2]:
                cell=dict(ObjectId=oid,IsEventDungeon=evd,ObjectSubId=sub)
                assert trap_cell(v,cell)==int(oid==5 and (not evd or sub==0)),cell;counts['trap_cell_cases']+=1
    trap=dict(ObjectId=5,IsEventDungeon=0,ObjectSubId=0);chest=dict(ObjectId=3,IsEventDungeon=0,ObjectSubId=0);evtrap=dict(ObjectId=5,IsEventDungeon=1,ObjectSubId=2)
    TITLE=(55,e.NOTICE_TITLE[1])
    for instant,gt,cell,ret,lines in [(True,True,trap,1,[]),(False,False,trap,0,[]),(False,True,trap,0,[T(CLEAR,GREEN)]),
                                      (False,True,chest,0,[]),(False,True,evtrap,0,[]),(True,False,chest,1,[])]:
        v.notices=[];v.writes=[];v.instant=instant;v.get_trap=gt
        assert v.run('KR_T8NoticeInstant',[cell,7])==ret and v.notices==lines and v.writes==[TITLE]*len(lines),(instant,gt,cell,v.notices,v.writes)
        counts['instant_notice_cases']+=1
    for ok,lines in [(True,[T(CLEAR,GREEN)]),(False,[T('함정 해제 실패',RED)])]:
        v.notices=[];v.writes=[];v.relieve=ok;assert v.run('KR_T8RelieveTrap',[3])==int(ok) and v.notices==lines and v.writes==[TITLE];counts['relieve_notice_cases']+=1
    for text,want in [('독침이(가) 튀어나왔다!',T('독침이(가) 튀어나왔다!',ORANGE)),('이즈미{YORU_KR_JOSA:n} 독에 걸렸다',T('이즈미는 독에 걸렸다',PURPLE)),
                      ('쿄카{YORU_KR_JOSA:n} 마비됐다',T('쿄카는 마비됐다',YELLOW)),('마나미{YORU_KR_JOSA:n} 회피했다',T('마나미는 회피했다',GREEN)),
                      ('신카이이(가) 피해를 입었다',T('신카이이(가) 피해를 입었다',RED)),('수상한 빛을 받았지만 아무 일도 일어나지 않았다',T('수상한 빛을 받았지만 아무 일도 일어나지 않았다',GRAY)),
                      ('어째서인지 시간이 흘러 버렸다',T('어째서인지 시간이 흘러 버렸다',ORANGE)),('던전에서 쫓겨났다',T('던전에서 쫓겨났다',RED)),
                      ('어딘가에 적이 나타났다',T('어딘가에 적이 나타났다',RED))]:
        v.notices=[];v.simple=[];v.writes=[]
        assert call('KR_T8TrapDialog',text,150) is None and v.notices==[want] and v.simple==[text] and v.writes==[TITLE],(text,v.notices,v.simple)
        counts['trap_dialog_coloured_dialog_unchanged']+=1
    v.in_dungeon=False;v.notices=[];v.writes=[];v.run('KR_T8TrapNotice',[proxy(CLEAR)]);assert v.notices==[T(CLEAR,GREEN)] and v.writes==[];v.in_dungeon=True
    counts['title_write_needs_dungeon_part']+=1
    # 2. Colour rules (hand-written expectations).
    col=lambda text,kind:ko(v.run('KR_T8Colorize',[proxy(text),kind]))
    cases=[(0,'회복 아이템「회복약」{YORU_KR_JOSA:O} 손에 넣었다','회복 아이템「'+T('회복약',GREEN)+'」을 손에 넣었다'),
           (0,'장비 아이템「목검」{YORU_KR_JOSA:O} 손에 넣었다','장비 아이템「'+T('목검',GOLD)+'」을 손에 넣었다'),
           (0,'요소석「어둠」(레벨 3)을 손에 넣었다','요소석「'+T('어둠',DARK)+'」(레벨 '+T('3',CYAN)+')을 손에 넣었다'),
           (0,'요소석「파랑」(레벨 12)을 손에 넣었다','요소석「'+T('파랑','r=120 g=176 b=255')+'」(레벨 '+T('12',CYAN)+')을 손에 넣었다'),
           (0,'달조각을 12개 손에 넣었다',T('달조각',GOLD)+'을 '+T('12',CYAN)+'개 손에 넣었다'),
           (0,'꽝',T('꽝',GRAY)),(0,'하지만 더는 소지할 수 없다',T('하지만 더는 소지할 수 없다',RED)),
           (0,'회복 아이템「약초2」{YORU_KR_JOSA:O} 손에 넣었다\n하지만 더는 소지할 수 없다',
            ko(call('KR_ResolveJosa','회복 아이템「약초2」{YORU_KR_JOSA:O} 손에 넣었다')).replace('「약초2」','「'+T('약초2',GREEN)+'」')+'\n'+T('하지만 더는 소지할 수 없다',RED)),
           (1,CLEAR,T(CLEAR,GREEN)),(1,'함정 해제 실패',T('함정 해제 실패',RED)),
           (2,'이즈미  레벨업! 12 → 13\n경험치 +1234 / 훈련치 +56 / 달조각 +7',
            '이즈미  '+T('레벨업!',GOLD)+' '+T('12',CYAN)+' → '+T('13',CYAN)+'\n경험치 '+T('+1234',CYAN)+' / 훈련치 '+T('+56',CYAN)+' / 달조각 '+T('+7',CYAN)),
           (2,'자동 탐색\n이동할 수 있는 탐색 경로가 없습니다.','자동 탐색\n이동할 수 있는 탐색 경로가 없습니다.'),
           (3,'이즈미  Lv 12 → 13  경험치 +1234 / 훈련치 +56\n\n달조각 +5\n회복약 +2\n소지 한도를 넘은 보상은 제외됩니다.\n잠시 후 다음 날로 진행합니다.',
            '이즈미  Lv '+T('12',CYAN)+' → '+T('13',CYAN)+'  경험치 '+T('+1234',CYAN)+' / 훈련치 '+T('+56',CYAN)+'\n\n'+T('달조각',GOLD)+' '+T('+5',CYAN)+'\n'
            +T('회복약',GOLD)+' '+T('+2',CYAN)+'\n'+T('소지 한도를 넘은 보상은 제외됩니다.',ORANGE)+'\n'+T('잠시 후 다음 날로 진행합니다.',GRAY)),
           (3,'소탕을 중단했습니다.\n보상과 탐색 시간은 변경되지 않았습니다.',T('소탕을 중단했습니다.',ORANGE)+'\n'+T('보상과 탐색 시간은 변경되지 않았습니다.',GRAY))]
    for kind,text,want in cases:
        got=col(text,kind);assert got==want,(kind,text,got,want);counts['colour_rule_cases']+=1
        assert col(got,kind)==got,got;counts['second_pass_unchanged']+=1
        assert ko(call('KR_ResolveJosa',got))==got,got;counts['josa_resolver_leaves_tags']+=1
    # the notice writers: tag processing + white base on their parts first, then the coloured text
    v.tags=[];v.colors=[];out=ko(call('KR_T8ChestColor','꽝'))
    assert out==T('꽝',GRAY) and v.tags==[(61,1,1),(62,1,1),(63,1,1)] and v.colors==[(61,255,255,255,1),(62,255,255,255,1),(63,255,255,255,1)],(v.tags,v.colors)
    v.tags=[];v.colors=[];out=ko(call('KR_T8ReceiptColor','경험치 +5'));assert out=='경험치 '+T('+5',CYAN) and v.tags==[(71,1,1)] and v.colors==[(71,255,255,255,1)]
    v.in_dungeon=False;v.tags=[];assert ko(call('KR_T8ChestColor','꽝'))==T('꽝',GRAY) and v.tags==[];v.in_dungeon=True;counts['writers_enable_tags_first']+=1
    # 3. Toggle (r4) unchanged.
    dat='SaveData_Test\\YoruKR_HomeRate.dat'
    v.files={};v.cache={};assert v.run('KR_T8HomeRateOn')==0 and dat not in v.files
    v.run('KR_T8HomeRateSet',[1]);assert v.files[dat]=='YoruKR.HomeRate.1\r\n1\r\n';v.cache={};assert v.run('KR_T8HomeRateOn')==1
    v.fail={('write',dat)};v.run('KR_T8HomeRateSet',[1]);v.fail=set();v.run('KR_T8HomeRateSet',[0]);assert v.files[dat]=='YoruKR.HomeRate.1\r\n0\r\n';counts['toggle_roundtrip']+=1
    # 4. Per-character events against the catalog; panel text.
    cat=a.readj(e.CATALOG);rows={r['person']:r for r in ev['char_events']['rows']}
    per={p:[x['fn'] for x in cat['events'] if any(t.get('person')==p or t.get('person2')==p for t in x['triggers'])] for p,_ in e.CHARS}
    import random
    rnd=random.Random(20260924);v.registered=set(rnd.sample([x['fn'] for x in cat['events']],300))
    for p,name in e.CHARS:
        want=sum(1 for fn in per[p] if fn in v.registered)
        assert v.run('KR_T8CharEvents',[p])==want and v.run('KR_T8CharTotal',[p])==len(per[p])==rows[p]['events'],(p,want)
        assert ko(v.run('KR_T8CharLabel',[p]))==name+'　'*(4-len(name));counts['char_event_counts']+=1
    assert v.run('KR_T8CharEvents',[9])==0 and v.run('KR_T8CharTotal',[1])==0
    rr=a.readj(O/'read_ranges.json');allmsg=[n for s,t in rr['ranges'] for n in range(s,t+1)]
    v.flags=set(allmsg[:1000]);v.cg={'CG1001'};v.scenes={24,12};v.events=[10,20,3,4]
    v.registered=set(per[2][:10])|set(per[7])
    text=ko(v.run('KR_T8HomeRateText'));lines=text.split('\n')
    pct=lambda n,t:'0.0%' if t<=0 or n<=0 else f'{min(n*1000//t,1000)//10}.{min(n*1000//t,1000)%10}%'
    want=['대사　　 '+T('1.3%',CYAN),'ＣＧ　　 '+T('1.6%',CYAN),'회상　　 '+T('3.0%',CYAN),'엔딩　　 '+T('2 / 5',CYAN),'이벤트　 '+T('3.5%',CYAN),'',T('캐릭터별 이벤트',GOLD)]
    for p,name in e.CHARS:want.append(name+'　'*(4-len(name))+' '+T(pct(sum(1 for fn in per[p] if fn in v.registered),len(per[p])),CYAN))
    assert lines==want,(lines,want);counts['panel_text']+=1
    # 호시카와 fully registered -> 100.0%; 이즈미 shares two-person walks with 호시카와, so it counts above its own first 10
    both=len(set(per[2])&set(per[7]));assert lines[12].endswith(T('100.0%',CYAN)) and both>0 and sum(1 for fn in per[2] if fn in v.registered)==10+len(set(per[2][10:])&set(per[7])),lines
    counts['pair_walk_counts_for_both']+=1
    v.acts={AREA:{'KR_HomeRate':101,'KR_HomeRateBody':102}};v.texts=[];v.shows=[];v.tags=[]
    assert v.run('KR_T8HomeShow',[1])==1 and v.tags==[(102,1,1)] and v.texts==[(102,text,1)] and v.shows==[(101,1)],(v.tags,v.texts,v.shows);counts['panel_tags_before_text']+=1
    v.acts[AREA+':0']={'KR_HomeRate':201,'KR_HomeRateBody':202};v.texts=[];v.shows=[];v.tags=[]
    assert v.run('KR_T8HomeShow',[0])==2 and v.texts==[] and v.tags==[] and sorted(v.shows)==[(101,0),(201,0)];counts['panel_hide']+=1
    # 5. Glyphs of what the r5 UI prints outside tags.
    from audit_message_pixel_widths import parse_fnl_font,sjis_bytes_to_fnl_index
    alphabet={x['unicode_character'] for x in a.readj(a.PROXY)['mapping']};carriers={x['proxy_character'] for x in a.readj(a.PROXY)['mapping']}
    visible=re.sub(r'\$\{[^}]*\}','',text+''.join(w for _,_,w in cases)+e.NOTICE_TITLE[1]+e.TOGGLE_LABEL)
    other=sorted({c for c in visible if c not in alphabet and c not in ' \n'})
    for c in other:assert c not in carriers,c
    for font in range(4):
        _,fl=parse_fnl_font(Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl',font)
        for c in other:
            idx=sjis_bytes_to_fnl_index(c.encode('cp932'));assert all(idx<len(f.widths) and f.widths[idx]>0 for f in fl),(font,c)
    counts['r5_non_proxy_glyphs']=len(other)
    out=a.readj(O/'vm_verification.json');out['r5']=dict(counts=dict(counts),panel_example=lines,colour_cases=[dict(kind=k,source=s,tagged=w) for k,s,w in cases])
    (O/'vm_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r5=counts),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
