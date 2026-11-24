"""Claude Opus 5.5 (2026-09-24): bounded execution of the compiled candidate JAM plus static save checks.

Native HLLs (TextFile, FileOperation, MsgSkip, PassRegister-backed gallery checks, dialogs) are modelled.
This is not a game test: modal input, real files and on-screen layout are checked by the user.
"""
from pathlib import Path
import collections,copy,json,re,struct,sys
import build_claude_term_rate_20260924 as e
b=e.b;p=e.p;q=e.q;a=e.a;O=e.O
def proxy(s):return b.encode(s).decode('cp932')
def ko(s):return b.decode(s.encode('cp932'))

class VM:
    def __init__(self):
        self.meta=b.read_meta(O/'candidate_meta.json');self.fs={}
        for f in self.meta['functions']:self.fs.setdefault(b.raw_symbol(self.meta,f['index']),f)
        self.code={};self.cache={};self.files={};self.handles={};self.fail=set();self.dialog=[];self.steps=0
        self.selection_active=False;self.titles=[];self.choices=[];self.simple=[];self.flags=set();self.cg=set();self.scenes=set()
        self.ready=True;self.events=[0,0,0,0];self.renamed=0;(O/'vm').mkdir(exist_ok=True)
    def load(self,fid):
        if fid in self.code:return self.code[fid]
        path=O/f'built_{fid}.jam'
        if not path.exists():
            path=O/'vm'/f'{fid}.jam'
            if not path.exists():b.cmd('ain','dump','--function',b.symbol(self.meta,fid),'-o',path,O/'NightRemaster.ain')
        ops=[];labels={}
        for line in path.read_text('utf8').splitlines():
            l=line.strip()
            if not l or l.startswith((';','FUNC ','ENDFUNC ','EOF ')):continue
            if l.endswith(':'):labels[l[:-1]]=len(ops)
            else:ops.append(l.split(maxsplit=1))
        self.code[fid]=(ops,labels);return self.code[fid]
    def run(self,name,args=()):
        f=self.fs[name];fid=f['index'];vs=f['arguments']+f['variables'];li={};seen=collections.Counter()
        for i,x in enumerate(vs):
            n=x['name']+(f'#{seen[x["name"]]}' if seen[x['name']] else '');seen[x['name']]+=1;li[n]=i
        loc={i:('' if v['type'][0]==12 else 0) for i,v in enumerate(vs)};loc.update(enumerate(args));st=[]
        ops,labels=self.load(fid);pc=0;steps=0
        while pc<len(ops):
            op,*rest=ops[pc];arg=rest[0] if rest else '';pc+=1;steps+=1;self.steps+=1;assert steps<3000000,(name,pc)
            if op=='PUSH':st.append(int(arg,0))
            elif op=='S_PUSH':st.append(json.loads(arg))
            elif op=='.S_LOCALASSIGN':v,x=arg.split(' ',1);loc[li[v]]=json.loads(x)
            elif op=='.LOCALASSIGN':v,x=arg.rsplit(' ',1);loc[li[v]]=int(x,0)
            elif op=='.LOCALREF':st.append(loc[li[arg]])
            elif op in ['.LOCALINC2','.LOCALINC3','.LOCALINC']:loc[li[arg]]+=1
            elif op=='.LOCALDEC2':loc[li[arg]]-=1
            elif op=='.LOCALPLUSA':v,x=arg.rsplit(' ',1);loc[li[v]]+=int(x)
            elif op=='.LOCALMINUSA':v,x=arg.rsplit(' ',1);loc[li[v]]-=int(x)
            elif op=='PUSHLOCALPAGE':st.append(loc)
            elif op=='A_REF':assert isinstance(st[-1],(str,list)),(name,st[-1])
            elif op in ['S_ASSIGN','X_ASSIGN']:
                assert op=='S_ASSIGN' or arg=='1';v=st.pop();i=st.pop();pg=st.pop()
                if isinstance(pg,list):
                    while len(pg)<=i:pg.append('')
                pg[i]=v;st.append(v)
            elif op=='X_REF':
                assert arg=='1';i=st.pop();pg=st.pop();st.append(pg[i])
            elif op=='PLUSA':
                v=st.pop();i=st.pop();pg=st.pop();pg[i]+=v;st.append(pg[i])
            elif op=='X_DUP':st+=st[-int(arg):]
            elif op=='X_A_INIT':
                n=st.pop();i=st.pop();pg=st.pop();pg[i]=['']*n;st.append(pg[i])
            elif op in ['DELETE','POP']:st.pop()
            elif op=='NOT':st.append(int(not st.pop()))
            elif op in ['ADD','SUB','S_ADD','LT','LTE','GT','GTE','EQUALE','NOTE','S_EQUALE','S_NOTE','MUL','DIV','MOD','S_LT','S_GT']:
                z=st.pop();x=st.pop()
                if op in ['ADD','S_ADD']:v=x+z
                elif op=='SUB':v=x-z
                elif op=='MUL':v=x*z
                elif op=='DIV':v=int(x/z)
                elif op=='MOD':v=x-int(x/z)*z
                elif op in ['LT','S_LT']:v=int(x<z)
                elif op=='LTE':v=int(x<=z)
                elif op in ['GT','S_GT']:v=int(x>z)
                elif op=='GTE':v=int(x>=z)
                elif op in ['EQUALE','S_EQUALE']:v=int(x==z)
                else:v=int(x!=z)
                st.append(v)
            elif op=='S_MOD':
                v=st.pop();s=st.pop();assert arg=='2';st.append(s%v)
            elif op in ['IFZ','IFNZ']:
                if bool(st.pop())==(op=='IFNZ'):pc=labels[arg]
            elif op=='JUMP':pc=labels[arg]
            elif op=='CALLFUNC':
                ff=self.fs[arg];n=len(ff['arguments']);aa=st[-n:] if n else [];st=st[:-n] if n else st
                out=self.native(arg,aa)
                if ff['return-type'][0]!=0:st.append(out)
            elif op=='CALLHLL':
                lib,method,_=arg.split();self.hll(lib,method,st,ops,pc,loc,li)
            elif op=='RETURN':
                assert len(st)==int(f['return-type'][0]!=0),(name,st)
                return st[0] if st else None
            else:raise AssertionError((name,op,arg))
        raise AssertionError(('no return',name))
    def native(self,name,aa):
        if name=='SYS_AddPunct':return aa[0] if aa[0].endswith('\\') else aa[0]+'\\'
        if name=='Ａ＿ＣＧモード確認':return int(ko(aa[0]) in self.cg)
        if name=='Ａ＿回想確認':return int(aa[0] in self.scenes)
        if name=='KR_PlayerReady':return int(self.ready)
        if name=='KR_PlayerEventCount':return self.events[aa[0]]
        if name=='LAbility::GetPlayerName':return proxy('료')
        if name=='KR_PlayerRename':self.renamed+=1;return None
        if name=='KR_KoreanInputDialog':return 0
        if name.startswith('■'):
            if name=='■選択ダイアログ／存在確認':return int(self.selection_active)
            if name=='■選択ダイアログ／初期化':self.choices.append([]);return None
            if name=='■選択ダイアログ／タイトル設定':self.titles.append(ko(aa[0]));return None
            if name=='■選択ダイアログ／選択肢追加':self.choices[-1].append((aa[0],ko(aa[1])));return None
            if name=='■シンプルダイアログ':self.simple.append(ko(aa[0]));return None
            if '実行' in name:return self.dialog.pop(0)
            return 0
        return self.run(name,aa)
    def hll(self,lib,method,st,ops,pc,loc,li):
        def refname():
            assert ops[pc-2][0]=='.LOCALREF',ops[pc-2];return li[ops[pc-2][1]]
        if lib=='system' and method=='GetSaveFolderName':st.append('SaveData_Test');return
        if lib=='SystemService':
            if method=='SystemVariable_Get':st.append(self.cache.get(st.pop(),''));return
            if method=='SystemVariable_Set':v=st.pop();key=st.pop();self.cache[key]=v;return
        if lib=='MsgSkip' and method=='GetFlag':st.append(int(st.pop() in self.flags));return
        if lib=='Array' and method=='Alloc':
            n=st.pop();arr=st.pop();arr[:]=(arr+['']*n)[:n];return
        if lib=='String':
            if method=='Length':st.append(len(st.pop()));return
            if method=='LengthByte':st.append(len(st.pop().encode('cp932')));return
            if method=='Find':key=st.pop();text=st.pop();st.append(text.find(key));return
            if method=='GetPart':idx=st.pop();text=st.pop();st.append(text[idx:]);return
            if method=='GetPart#1':count=st.pop();idx=st.pop();text=st.pop();st.append(text[idx:idx+count]);return
            if method=='Replace':new=st.pop();old=st.pop();text=st.pop();st.append(text.replace(old,new));return
            if method=='Trim':st.append(st.pop().strip());return
            if method=='TrimStart':st.append(st.pop().lstrip());return
            if method=='Empty':st.append(int(st.pop()==''));return
        if lib=='TextFile':
            if method=='OpenReader':
                path=st.pop()
                if ('open',path) in self.fail or path not in self.files:st.append(-1);return
                hnd=len(self.handles);self.handles[hnd]=[path,self.files[path].split('\r\n'),0];st.append(hnd);return
            if method=='ReadLine':
                st.pop();idx=refname();hnd=st.pop();_,lines,cur=self.handles[hnd]
                loc[idx]=lines[cur] if cur<len(lines) else '';self.handles[hnd][2]+=1;st.append(1);return
            if method=='Close':st.pop();st.append(int(('close',) not in self.fail));return
            if method=='ReadAll':
                st.pop();idx=refname();path=st.pop()
                if path not in self.files:st.append(0);return
                loc[idx]=self.files[path];st.append(1);return
            if method=='WriteAll':
                text=st.pop();path=st.pop()
                if ('write',path) in self.fail:st.append(0);return
                self.files[path]=text.replace('\r\n','\n').replace('\n','\r\n');st.append(1);return
        if lib=='FileOperation':
            if method=='ExistFile':st.append(int(st.pop() in self.files));return
            if method=='CopyFile':
                src=st.pop();dst=st.pop();ok=src in self.files and ('copy',dst) not in self.fail
                if ok:self.files[dst]=self.files[src]
                st.append(int(ok));return
            if method=='DeleteFile':self.files.pop(st.pop(),None);st.append(1);return
        raise AssertionError((lib,method))

def main():
    ev=a.readj(O/'build_evidence.json');assert all(a.sha(O/n)==h for n,h in ev['files'].items())
    e.use_terms();v=VM();counts=collections.Counter()
    raw=[b.decode(x) for x in b.raw_messages((O/'baseline_NightRemaster.ain').read_bytes())[3]]
    call=lambda n,*args:v.run(n,[proxy(x) if isinstance(x,str) else x for x in args])
    defaults=[t[0] for t in e.TERMS8]
    def settings(values):
        for i,t in enumerate(values):v.cache[f'YoruKR.Term.v1.{i}']=proxy(t)
        v.run('KR_TermRefresh')
    def reset():
        for i in range(8):v.cache[f'YoruKR.Term.v1.{i}']=''
        v.run('KR_TermRefresh')
    # 1. Defaults: every MSG1 row is returned byte-exact; the display table is inert except dungeon names.
    reset();assert v.cache['YoruKR.Term.Active']=='0'
    for i,s in enumerate(raw):assert ko(call('KR_TermMessage',i,s))==s,i
    counts['default_all_MSG1']=len(raw)
    for r in a.readj(O/'display_terms.json'):assert ko(call('KR_TermDisplay',r['source']))==r['source'];counts['default_display_rows_unchanged']+=1
    drows=a.readj(O/'dungeon_terms.json')
    for r in drows:
        want=b.render([tuple(t) for t in r['tokens']],defaults);assert ko(call('KR_TermDisplay',r['source']))==want,(r['source'],want);counts['default_dungeon_follows_term']+=1
    assert ko(call('KR_TermDisplay','수수께끼의 틈 1'))=='수수께끼의 틈새 1' and ko(call('KR_TermDisplay','화군 라이코 동굴 표층①'))=='호무라 라이코 동굴 표층①'
    fmt='%s{YORU_KR_JOSA:n} 히카리의 기척을 감지했다';assert ko(v.run('KR_T8SenseFormat'))==fmt
    # 2. Scenarios.
    from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer
    _,faces=parse_fnl_font(Path(ev['source_pointer']['runtime'])/'NightRemasterFont.fnl',0);face,den,_=select_fnl_face(faces,60)
    indices,_=a.load_proxy_indices(a.readj(a.PROXY),len(face.widths));meter=WidthMeasurer(face,den,indices,-2,2,0)
    classes={r['message_id']:r for r in a.readj(a.HERE/'message_window_classification.json')['rows']}
    R=e.R;coverage=a.readj(R/'evidence/term_switch_20260923/source/term_coverage.json')
    hm=a.readj(O/'homura_messages.json');dyn=a.readj(R/'evidence/term_switch_20260923/source/dynamic_pages.json')
    scenarios=[['광수','화자','쉭쉭이','하자마','토야','진월','진야','화군'],['빛잡이','불지기','쉭쉭이','틈','동야','신게츠','신야','불무리'],
               ['광군','불씨','하늘','공간','차디찬 겨울','푸른 별','깊은 밤','불떼']]
    examples=[]
    for values in scenarios:
        assert all(call('KR_TermValid',i,x) for i,x in enumerate(values)),values;settings(values);assert v.cache['YoruKR.Term.Active']=='1'
        rows=[dict(id=r['id'],source=r['source'],tokens=r['tokens'],dynamic_page=r['dynamic_page']) for r in coverage]
        rows+=[dict(id=r['id'],source=r['source'],tokens=r['tokens'],dynamic_page=False) for r in hm['static']]
        for row in rows:
            i=row['id'];out=ko(call('KR_TermMessage',i,row['source']));c=classes[i]
            if c['message_roles']==['Body']:
                budget=716 if c['window_types']==['Face'] else 932
                assert meter.measure(out,True)['max_width_px']<=budget,(i,out,budget)
            if not row['dynamic_page']:assert out==b.render(row['tokens'],values),(i,out)
            counts['scenario_term_rows']+=1
        for page in dyn:
            joined=''.join(ko(call('KR_TermMessage',i,raw[i])) for i in page['ids']);want=b.render(b.tokens(page['source']),values)
            assert re.sub(r'\s','',joined)==re.sub(r'\s','',want),(page['ids'],joined,want);counts['scenario_dynamic_pages']+=1
        for r in a.readj(O/'display_terms.json'):
            once=ko(call('KR_TermDisplay',r['source']));want=b.render([(k,tuple(x) if isinstance(x,list) else x) for k,x in r['tokens']],values)
            assert once==want,(r['source'],once,want);assert ko(call('KR_TermDisplay',once))==once;counts['scenario_display_rows']+=1
        for r in drows:
            once=ko(call('KR_TermDisplay',r['source']));want=b.render([(k,tuple(x) if isinstance(x,list) else x) for k,x in r['tokens']],values)
            assert once==want and ko(call('KR_TermDisplay',once))==once,(r['source'],once);counts['scenario_dungeon_rows']+=1
        assert ko(v.run('KR_T8SenseFormat'))==fmt.replace('히카리',values[0])
        battle=ko(call('KR_T8BattleText','히카리를 모두 쓰러뜨렸다'));examples.append(dict(settings=values,battle=battle,
            homura={str(r['id']):ko(call('KR_TermMessage',r['id'],r['source'])) for r in hm['static']},
            dungeon=[ko(call('KR_TermDisplay',x)) for x in ['수수께끼의 틈 1','서양관 내부　틈 5','화군 라이코 동굴 최심층⑩']],
            comment=ko(call('KR_TermDisplay','용에게 효과적인 검이지만,\n히카리에게 얼마나 통할지는\n알 수 없습니다.')),mold=ko(call('KR_TermDisplay','카샤의 영약'))))
        assert battle.startswith(values[0])
    # Battle Printf: strings that are not term rows resolve exactly as before (KR_ResolveJosa alone).
    settings(scenarios[0]);st0=[b.decode(x) for x in b.strings(b.unpack((O/'baseline_NightRemaster.ain').read_bytes()))[2]]
    for s in [x for x in st0 if '{YORU_KR_JOSA' in x][:400]:
        assert ko(call('KR_T8BattleText',s))==ko(call('KR_ResolveJosa',s)),s;counts['battle_non_term_identical']+=1
    for s in ['발치로','입부하자마자','말을 하자마자','마코토야','호무라 신사','평소 훈련 때문에 밤늦게 찾곤 하던 호무라 신사','顔CG変換テーブル.cgName','화군','틈']:
        assert ko(call('KR_TermDisplay',s))==s,s;counts['false_positive_unchanged']+=1
    # 3. Validation.
    for i,t in enumerate(e.TERMS8):
        for s in t[1]:assert call('KR_TermValid',i,s),(i,s);counts['presets_valid']+=1
    for i in range(8):
        for j,s in enumerate(defaults):
            if i!=j:assert not call('KR_TermValid',i,s);counts['cross_term_collision_rejected']+=1
    for bad in ['',' ',' 가','가 ','가\n나','{키}','%s','abc','가가가가가가가가가','불무리야']:
        assert not call('KR_TermValid',7,bad),bad;counts['invalid_custom_rejected']+=1
    assert not call('KR_TermValid',8,'가') and call('KR_TermValid',7,'불') and call('KR_TermValid',7,'화군')
    # 4. Preferences: v3 roundtrip, v2 compatibility, failures keep the previous state.
    dat='SaveData_Test\\YoruKR_Terms.dat';bak='SaveData_Test\\YoruKR_Terms.backup';pend='SaveData_Test\\YoruKR_Terms.pending'
    get=lambda:[ko(call('KR_TermGet',i)) for i in range(8)]
    settings(scenarios[0]);assert v.run('KR_TermSave');assert v.files[dat]==('YoruKR.Terms.3\r\n'+''.join(proxy(x)+'\r\n' for x in scenarios[0])) and pend not in v.files
    v.cache={};v.run('KR_TermLoad');assert get()==scenarios[0] and v.cache['YoruKR.Term.Active']=='1';counts['v3_save_reload']+=1
    v.files={dat:'YoruKR.Terms.2\r\n'+''.join(proxy(x)+'\r\n' for x in scenarios[1][:7])};v.cache={};v.run('KR_TermLoad')
    assert get()==scenarios[1][:7]+['호무라'];counts['v2_file_loads_with_default_homura']+=1
    assert v.run('KR_TermSave') and v.files[dat].startswith('YoruKR.Terms.3\r\n') and v.files[bak].startswith('YoruKR.Terms.2\r\n');counts['v2_upgraded_backup_kept']+=1
    good=copy.deepcopy(v.files);settings(scenarios[2]);v.fail={('write',pend)};assert not v.run('KR_TermSave');assert v.files==good
    v.cache={};v.run('KR_TermLoad');assert get()==scenarios[1][:7]+['호무라'];v.fail=set();counts['failed_write_keeps_previous']+=1
    v.files[dat]='YoruKR.Terms.3\r\nbad\r\n';v.cache={};v.run('KR_TermLoad');assert get()==scenarios[1][:7]+['호무라'] and v.cache['YoruKR.Term.ValidMain']=='0';counts['corrupt_main_uses_backup']+=1
    v.files={};v.cache={};v.run('KR_TermLoad');assert get()==defaults and v.cache['YoruKR.Term.Active']=='0';counts['no_files_defaults']+=1
    # 5. Menu: eight rows, 호무라 preset, restore defaults, cancel writes nothing, active choice untouched.
    v.files={};v.cache={};v.titles=[];v.choices=[];v.dialog=[8,2,0];v.run('KR_TermMenu')
    assert not v.dialog and get()[7]=='화군' and v.files[dat].count('\r\n')==9;menu=v.choices[0]
    assert [c for c,_ in menu]==[1,2,3,4,5,6,7,8,20,0] and menu[7][1]=='호무라 : 호무라',menu;assert [x for _,x in v.choices[1]][:3]==['호무라','화군','불무리'];counts['menu_homura_preset_saved']+=1
    v.cache={};v.run('KR_TermLoad');assert get()[7]=='화군';v.dialog=[6,3,0];v.run('KR_TermMenu');assert get()[5]=='신게츠';v.dialog=[7,3,0];v.run('KR_TermMenu');assert get()[6]=='신야';counts['menu_japanese_readings']+=1
    v.dialog=[20,0];v.run('KR_TermMenu');assert get()==defaults and not v.dialog;counts['menu_restore_defaults']+=1
    for queue in [[0],[1,0,0],[8,0,0]]:
        before=copy.deepcopy(v.files);v.dialog=list(queue);v.run('KR_TermMenu');assert v.files==before and not v.dialog;counts['menu_cancel_no_write']+=1
    v.selection_active=True;before=copy.deepcopy(v.files);n0=len(v.choices);v.run('KR_TermMenu');assert v.files==before and len(v.choices)==n0;v.selection_active=False;counts['active_native_choice_not_deleted']+=1
    # 6. Achievement page.
    rr=a.readj(O/'read_ranges.json');cg=a.readj(O/'gallery_cg.json');sc=a.readj(O/'gallery_scenes.json')
    allmsg=[n for s,t in rr['ranges'] for n in range(s,t+1)];assert len(allmsg)==rr['total']
    v.flags=set(allmsg[::3])|{0,1,2,max(allmsg)+5};assert v.run('KR_T8ReadCount')==len(allmsg[::3]);counts['read_count_matches_model']+=1
    v.flags=set(allmsg);assert v.run('KR_T8ReadCount')==rr['total'];v.flags=set();assert v.run('KR_T8ReadCount')==0
    v.cg={c['cg_names'][-1] for c in cg['cells'][::2]};assert v.run('KR_T8CgCount')==len(cg['cells'][::2]);counts['cg_any_variant_opens_cell']+=1
    v.cg={n for c in cg['cells'] for n in c['cg_names']};assert v.run('KR_T8CgCount')==60
    v.scenes={12,34,64,66,68,99};assert v.run('KR_T8SceneCount')==3;assert ko(v.run('KR_T8EndingText'))=='3 / 5   이즈미 · ??? · 마나미 · ??? · 보통 결말'
    v.scenes=set(sc['reg_numbers']);assert v.run('KR_T8SceneCount')==66 and ko(v.run('KR_T8EndingText'))=='5 / 5   이즈미 · 쿄카 · 마나미 · 마코토 · 보통 결말';counts['scene_and_ending']+=1
    v.flags=set(allmsg[:1000]);v.cg={'CG1001'};v.scenes={24};v.events=[10,20,3,4];v.titles=[];v.choices=[];v.dialog=[2,0,1,0];v.run('KR_PlayerInfoMenu')
    # main -> detail -> main -> (rename) -> main -> close
    assert not v.dialog and v.renamed==1 and len(v.titles)==4 and v.titles[0]==v.titles[2]==v.titles[3],v.titles
    main=v.titles[0].split('\n');detail=v.titles[1].split('\n');counts['info_page_flow']+=1
    assert main==['플레이 정보','대사 완독률  1000 / 74966  (1.3%)','CG  1 / 60  (1.6%)','회상  1 / 66  (1.5%)','엔딩  1 / 5   ??? · 쿄카 · ??? · ??? · ???',
                  '위 네 줄은 모든 저장을 합친 기록 / 전체 분기 포함','이 저장의 이벤트 진입률  37 / 1043  (3.5%)','주인공 : 료'],main
    assert detail[0]=='이벤트 진입 자세히' and detail[1]=='이 저장의 이벤트 진입률  37 / 1043  (3.5%)' and detail[2]=='스토리  10 / 398  (2.5%)',detail
    assert [x for _,x in v.choices[0]]==['이벤트 진입 자세히','주인공 이름 변경','닫기'] and [x for _,x in v.choices[1]]==['돌아가기']
    v.ready=False;v.titles=[];v.run('KR_PlayerInfoMenu');assert not v.titles and v.simple[-1].startswith('게임을 시작하거나');v.ready=True
    v.selection_active=True;v.run('KR_PlayerInfoMenu');assert not v.titles and v.simple[-1].startswith('진행 중인 선택');v.selection_active=False;counts['info_guards']+=1
    # 7. Proxy font: every character the new UI prints exists in the font map.
    alphabet={x['unicode_character'] for x in a.readj(a.PROXY)['mapping']}
    ui=''.join(v.titles+[x for c in v.choices for _,x in c]+v.simple)
    missing=sorted({c for c in ui if ord(c)>127 and c not in alphabet and c not in '　「」【】…'})
    assert not missing,missing
    widths={t:meter.measure(t,True)['max_width_px'] for t in [x for x in main+detail]}
    a_ok=dict(counts=dict(counts),steps=v.steps,examples=examples,info_page=main,detail_page=detail,title_widths=widths)
    (O/'vm_verification.json').write_text(json.dumps(a_ok,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(counts=counts,steps=v.steps),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
