"""Claude Opus 5.5 (2026-09-24) r4: every r3 VM check against the r4 candidate, then the r4 additions.

r4 checks (bounded execution of the compiled candidate JAM, native HLLs modelled):
- KR_T8TrapCell (hand-written CALLMETHOD body) against the StepedOnCell instant-disarm test, all cell kinds.
- KR_T8NoticeInstant / KR_T8RelieveTrap / KR_T8TrapDialog: which notice lines appear, dialogs unchanged.
- Homebase panel: toggle file, cached state, percent format, panel text, part lookup over AddArea names.
- Relocated BeginTop/EndTop/config events: original body plus exactly the prepended call.
- Every character the r4 UI prints exists in the proxy map / FNL fonts.
Screens (panel position, checkbox layout, notice in auto explore) are checked natively and by the user.
"""
from pathlib import Path
import collections,copy,json,re,struct,sys
import build_claude_term_rate_20260924_r4 as e
import verify_claude_term_rate_20260924 as v3
v3.e=e;v3.O=e.O
b=e.b;a=e.a;O=e.O
proxy=v3.proxy;ko=v3.ko
AREA='Game\\Scenes\\Common\\AddArea.pact'

class VM4(v3.VM):
    def __init__(self):
        super().__init__()
        self.notices=[];self.get_trap=False;self.instant=False;self.relieve=True;self.cell=None
        self.acts={};self.texts=[];self.shows=[];self.calls=collections.Counter();self.in_dungeon=True;self.writes=[]
    def native(self,name,aa):
        self.calls[name]+=1
        if name=='KR_ChestShow':self.notices.append(ko(aa[0]));return None
        if name=='KR_ChestPart':return 55 if (self.in_dungeon and aa[0]=='KR_ChestTitle') else -1
        if name=='KR_ChestWrite':self.writes.append((aa[0],ko(aa[1])));return None
        if name=='KR_NoticeInstant':return int(self.instant)
        if name=='KR_GetTrap':return int(self.get_trap)
        if name=='L_Dungeon::RelieveTrap':return int(self.relieve)
        if name=='KR_T8TrapCell':return trap_cell(self,aa[0])
        if name=='AFL_Activity_IsExistPartsByName':return int(aa[1] in self.acts.get(aa[0],{}))
        if name=='AFL_Activity_GetPartsNumber':return self.acts[aa[0]][aa[1]]
        if name=='Ｐ＿テキスト設定':self.texts.append((aa[0],ko(aa[1]),aa[2]));return None
        if name=='Ｐ＿表示設定':self.shows.append((aa[0],int(aa[1])));return None
        return super().native(name,aa)

GETTERS={27005:'ObjectId',27008:'ObjectSubId',27029:'IsEventDungeon'}
def trap_cell(vm,cell):
    # Executes the built KR_T8TrapCell ops (LOCALREF/PUSH/CALLMETHOD/NOTE/IFZ/IFNZ/RETURN only).
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

def static_relocations(ev,counts):
    # built body == original body with exactly one prepended block
    ids=ev['added_functions']
    want={28571:'\tCALLFUNC KR_T8HomeEnter\n',28572:'\tCALLFUNC KR_T8HomeLeave\n',
          29817:e.checkbox_sync(29827,ids['KR_T8HomeRateGet']),29818:e.checkbox_sync(29828,ids['KR_T8HomeRateSet'])}
    def norm(text):
        out=[]
        for l in text.splitlines():
            s=l.rstrip()
            if not s or s.startswith(';') or s.startswith('EOF ') or s.startswith('ENDFUNC '):continue
            out.append(re.sub(r'0x[0-9a-f]+','ADDR',s))
        return out
    for fid,code in want.items():
        orig=norm((O/f'original_{fid}.jam').read_text('utf8'));built=norm((O/f'built_{fid}.jam').read_text('utf8'))
        ins=norm(code)
        assert built[0]==orig[0] and built[1:1+len(ins)]==ins and built[1+len(ins):]==orig[1:],(fid,built[:12],orig[:6])
        counts['relocated_body_is_original_plus_prefix']+=1

def main():
    v3.main()   # all r3 checks, now on the r4 candidate (writes vm_verification.json)
    ev=a.readj(O/'build_evidence.json');counts=collections.Counter();v=VM4()
    call=lambda n,*args:v.run(n,[proxy(x) if isinstance(x,str) else x for x in args])
    static_relocations(ev,counts)
    # 1. Trap cell predicate == live StepedOnCell instant-disarm test, every combination.
    for oid in [0,3,5,6,7]:
        for evd in [0,1]:
            for sub in [0,1,2]:
                cell=dict(ObjectId=oid,IsEventDungeon=evd,ObjectSubId=sub)
                assert trap_cell(v,cell)==int(oid==5 and (not evd or sub==0)),cell;counts['trap_cell_cases']+=1
    CLEAR='함정 해제 성공 · 피해 없음'
    trap=dict(ObjectId=5,IsEventDungeon=0,ObjectSubId=0);chest=dict(ObjectId=3,IsEventDungeon=0,ObjectSubId=0);evtrap=dict(ObjectId=5,IsEventDungeon=1,ObjectSubId=2)
    # 2. KR_T8NoticeInstant: loot result untouched, instant disarm gets one line, nothing else.
    TITLE=(55,e.NOTICE_TITLE[1])
    for instant,gt,cell,ret,lines in [(True,True,trap,1,[]),(False,False,trap,0,[]),(False,True,trap,0,[CLEAR]),
                                      (False,True,chest,0,[]),(False,True,evtrap,0,[]),(True,False,chest,1,[])]:
        v.notices=[];v.writes=[];v.instant=instant;v.get_trap=gt
        assert v.run('KR_T8NoticeInstant',[cell,7])==ret and v.notices==lines and v.writes==[TITLE]*len(lines),(instant,gt,cell,v.notices,v.writes)
        counts['instant_notice_cases']+=1
    # 3. KR_T8RelieveTrap: result passed through, one line either way.
    for ok,lines in [(True,[CLEAR]),(False,['함정 해제 실패'])]:
        v.notices=[];v.writes=[];v.relieve=ok;assert v.run('KR_T8RelieveTrap',[3])==int(ok) and v.notices==lines and v.writes==[TITLE];counts['relieve_notice_cases']+=1
    # 4. KR_T8TrapDialog: notice (with the shared title) first, then the very same dialog text and fade time.
    for text in ['독침이(가) 튀어나왔다!','%s{YORU_KR_JOSA:n} 독에 걸렸다','던전에서 쫓겨났다']:
        v.notices=[];v.simple=[];v.writes=[];v.calls=collections.Counter()
        assert call('KR_T8TrapDialog',text,150) is None and v.notices==[text] and v.simple==[text] and v.writes==[TITLE],(v.notices,v.simple,v.writes)
        counts['trap_dialog_mirrored']+=1
    # outside a dungeon view the title part is absent: no write, KR_ChestShow keeps its own guard
    v.in_dungeon=False;v.notices=[];v.writes=[];v.run('KR_T8TrapNotice',[proxy(CLEAR)]);assert v.notices==[CLEAR] and v.writes==[];v.in_dungeon=True
    counts['title_write_needs_dungeon_part']+=1
    # 5. Toggle: default off, file format, cached, set writes only on change.
    dat='SaveData_Test\\YoruKR_HomeRate.dat'
    v.files={};v.cache={};assert v.run('KR_T8HomeRateOn')==0 and v.cache['YoruKR.HomeRate']=='0' and dat not in v.files;counts['toggle_default_off']+=1
    v.run('KR_T8HomeRateSet',[1]);assert v.files[dat]=='YoruKR.HomeRate.1\r\n1\r\n' and v.cache['YoruKR.HomeRate']=='1'
    v.cache={};assert v.run('KR_T8HomeRateOn')==1 and v.run('KR_T8HomeRateGet')==1;counts['toggle_on_persists']+=1
    v.fail={('write',dat)};v.run('KR_T8HomeRateSet',[1]);v.fail=set();assert v.files[dat]=='YoruKR.HomeRate.1\r\n1\r\n';counts['toggle_same_state_no_write']+=1
    v.run('KR_T8HomeRateSet',[0]);assert v.files[dat]=='YoruKR.HomeRate.1\r\n0\r\n';v.cache={};assert v.run('KR_T8HomeRateOn')==0;counts['toggle_off_persists']+=1
    for bad in ['','1','YoruKR.HomeRate.1\r\n2\r\n','YoruKR.HomeRate.2\r\n1\r\n']:
        v.files={dat:bad};v.cache={};assert v.run('KR_T8HomeRateOn')==0,bad;counts['toggle_bad_file_off']+=1
    # 6. Percent and panel text (same sources as the play-info page).
    for n,t,want in [(0,74966,'0.0%'),(74966,74966,'100.0%'),(1000,74966,'1.3%'),(37,1043,'3.5%'),(74965,74966,'99.9%'),(5,0,'0.0%'),(-1,10,'0.0%')]:
        assert v.run('KR_T8Pct',[n,t])==want,(n,t,v.run('KR_T8Pct',[n,t]));counts['percent_cases']+=1
    rr=a.readj(O/'read_ranges.json');allmsg=[n for s,t in rr['ranges'] for n in range(s,t+1)]
    v.flags=set(allmsg[:1000]);v.cg={'CG1001'};v.scenes={24,12};v.events=[10,20,3,4]
    text=ko(v.run('KR_T8HomeRateText'));lines=text.split('\n')
    assert lines==['대사　　1.3%','ＣＧ　　1.6%','회상　　3.0%','엔딩　　2 / 5','이벤트　3.5%'],lines;counts['panel_text']+=1
    # 7. Part lookup: base activity name, GetFreeName copies, none.
    v.acts={AREA:{'KR_HomeRate':101,'KR_HomeRateBody':102}};v.texts=[];v.shows=[]
    assert v.run('KR_T8HomeShow',[1])==1 and v.texts==[(102,text,1)] and v.shows==[(101,1)],(v.texts,v.shows);counts['panel_show_base_name']+=1
    v.acts[AREA+':0']={'KR_HomeRate':201,'KR_HomeRateBody':202};v.acts[AREA+':3']={'KR_HomeRate':301,'KR_HomeRateBody':302};v.acts['Other']={'KR_HomeRate':9}
    v.texts=[];v.shows=[];assert v.run('KR_T8HomeShow',[0])==3 and v.texts==[] and sorted(v.shows)==[(101,0),(201,0),(301,0)];counts['panel_hide_all_copies']+=1
    v.acts={AREA+':1':{'KR_HomeRate':5}};v.texts=[];v.shows=[];assert v.run('KR_T8HomeShow',[1])==0 and not v.texts and not v.shows;counts['panel_needs_both_parts']+=1
    v.acts={};assert v.run('KR_T8HomeShow',[1])==0;counts['panel_no_addarea_noop']+=1
    # 8. BeginTop/EndTop hooks follow the toggle and the loaded-game guard.
    v.acts={AREA:{'KR_HomeRate':101,'KR_HomeRateBody':102}}
    for on,ready,shows,texts in [(1,True,[(101,1)],1),(0,True,[(101,0)],0),(1,False,[(101,0)],0)]:
        v.files={dat:f'YoruKR.HomeRate.1\r\n{on}\r\n'};v.cache={};v.ready=ready;v.texts=[];v.shows=[]
        v.run('KR_T8HomeEnter');assert v.shows==shows and len(v.texts)==texts,(on,ready,v.shows,v.texts);counts['home_enter_cases']+=1
    v.ready=True;v.shows=[];v.run('KR_T8HomeLeave');assert v.shows==[(101,0)];counts['home_leave_hides']+=1
    # 9. Glyphs: everything the r4 UI prints (panel, notices, checkbox label) is a proxy carrier or an FNL glyph.
    from audit_message_pixel_widths import parse_fnl_font,sjis_bytes_to_fnl_index
    alphabet={x['unicode_character'] for x in a.readj(a.PROXY)['mapping']};carriers={x['proxy_character'] for x in a.readj(a.PROXY)['mapping']}
    ui=text+'달성률'+CLEAR+'함정 해제 실패'+e.TOGGLE_LABEL+e.NOTICE_TITLE[1]+'0123456789.%/ '
    other=sorted({c for c in ui if c not in alphabet and c not in ' \n'})
    for c in other:assert c not in carriers,c
    for font in range(4):
        _,fl=parse_fnl_font(Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl',font)
        for c in other:
            idx=sjis_bytes_to_fnl_index(c.encode('cp932'));assert all(idx<len(f.widths) and f.widths[idx]>0 for f in fl),(font,c)
    counts['r4_non_proxy_glyphs']=len(other);counts['r4_ui_chars']=len(set(ui))
    out=a.readj(O/'vm_verification.json');out['r4']=dict(counts=dict(counts),panel_example=lines,non_proxy_glyphs=other)
    (O/'vm_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r4=counts),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
