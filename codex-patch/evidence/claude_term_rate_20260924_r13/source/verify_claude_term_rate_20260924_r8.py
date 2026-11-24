"""Claude Opus 5.5 (2026-09-24) r8: the r3/r5/r6/r7 VM checks against the r8 candidate, then the daily/weekly autosaves:
- KR_T8AutoSaveDay() == 1 every day; KR_T8AutoSaveSlot() = 49 on Mondays (GetDayOfWeek 1), 999 otherwise;
- labels 일간/주간/%02d, the weekly slot's font maps to 999's, the save-screen lock covers 999 and 49 only,
  the newest-manual search skips 49 only when bAuto is false, the load-confirm title names both autosaves,
  the game-over resume picks the newer of 999/49 by the saved file time (date first, then time of day);
- the four relocated save/load functions are the original bodies with exactly the intended replacement;
- 呼出／１日の始まり / IsExecLoad / ExecGameOver changed only at the listed operands; the base code is r7's otherwise;
- r7's functions keep their metadata (appended bodies shift); PACT and EX are byte-identical to r7.
"""
from pathlib import Path
import collections,json,re,struct
import build_claude_term_rate_20260924_r8 as e
import verify_claude_term_rate_20260924_r7 as V7
V6=V7.V6;V5=V7.V5
for mod in (V7,V6,V5):mod.e=e;mod.O=e.O
V5.v3.e=e;V5.v3.O=e.O
b=e.b;a=e.a;O=e.O
R7=e.R/'staging/claude_term_rate_20260924_r7'
proxy=V5.proxy;ko=V5.ko
# later revisions reuse these checks: they add functions and may change r7 jaf bodies (then appended addresses shift unevenly)
NEW_FUNCTIONS=10;STRICT_SHIFT=True
EXTRA_SITES=[]   # same-length operand sites added by later revisions (absolute code addresses)
EXTRA_RELOCATED=[]   # functions later revisions relocate (their own checks prove the bodies; r13: C_SceneHomebase@RunHome)

def r7_checks():
    """verify_claude_term_rate_20260924_r7.main after V6.main, with the EX diff taken against BASE_EX."""
    ev=a.readj(O/'build_evidence.json');counts=collections.Counter();v=V7.VM7()
    dat='SaveData_Test\\YoruKR_HomeRate.dat';OFF='YoruKR.HomeRate.1\r\n0\r\n';ON='YoruKR.HomeRate.1\r\n1\r\n'
    on=lambda:v.run('KR_T8HomeRateGet')
    v.files={dat:OFF};v.cache={};v.fail={('write',dat)};v.writes=0
    v.run('KR_T8HomeRateSet',[1]);assert on()==0 and v.files[dat]==OFF and v.writes==1 and v.cache['YoruKR.HomeRate.Failed']=='1',v.cache
    for _ in range(5):v.run('KR_T8HomeRateSet',[1])
    assert v.writes==1,v.writes;counts['failed_write_keeps_state_no_retry_storm']+=1
    v.cache.pop('YoruKR.HomeRate');assert on()==0;counts['failed_write_off_after_cache_reset']+=1
    v.fail=set();v.run('KR_T8HomeRateSet',[0]);assert v.cache['YoruKR.HomeRate.Failed']=='' and v.writes==1
    v.run('KR_T8HomeRateSet',[1]);assert on()==1 and v.files[dat]==ON and v.writes==2;counts['retry_after_change_succeeds']+=1
    v.corrupt=True;v.run('KR_T8HomeRateSet',[0]);assert on()==1 and v.cache['YoruKR.HomeRate.Failed']=='0';v.corrupt=False;counts['readback_mismatch_is_failure']+=1
    v.files={dat:ON};v.cache={};v.writes=0
    for _ in range(3):v.run('KR_T8HomeRateSet',[1])
    assert v.writes==0 and on()==1;counts['same_value_no_write']+=1
    v.files={};v.cache={};v.run('KR_T8HomeRateSet',[1]);assert on()==1 and v.files[dat]==ON;counts['plain_success']+=1
    old=b.ex.decode_ex(e.BASE_EX);new=b.ex.decode_ex(O/'NightRemasterEX.ex')
    diff={p:(b.decode(old.strings[p].value),b.decode(new.strings[p].value)) for p in old.strings if old.strings[p].value!=new.strings[p].value}
    want={tuple(x['path']):(x['before'],x['target']) for x in ev['monster_names']['edits']}
    assert diff==want and len(diff)==8,(diff,want);assert {p:n.raw for p,n in old.scalars.items()}=={p:n.raw for p,n in new.scalars.items()}
    counts['ex_only_eight_names_changed']+=1
    names={int(t.name.value.decode('cp932')):b.decode(new.strings[t.leaf_value.payload.items[2].value.payload.path].value) for t in new.blocks[7].payload.children}
    for mid,(jp,before,target,why) in e.MONSTER_RENAMES.items():assert names[mid]==target,(mid,names[mid])
    counts['renamed_monsters']=len(e.MONSTER_RENAMES)
    alphabet={x['unicode_character'] for x in a.readj(a.PROXY)['mapping']}
    assert all(c in alphabet or c==' ' for x in e.MONSTER_RENAMES.values() for c in x[2]);counts['monster_glyphs_in_proxy_map']+=1
    res=a.readj(O/'vm_verification.json');res['r7']=dict(counts=dict(counts),monster_names={str(k):v[2] for k,v in e.MONSTER_RENAMES.items()},ex_base=str(e.BASE_EX))
    (O/'vm_verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r7=counts),ensure_ascii=False))

class VM8(V7.VM7):
    """Adds the engine calls the autosave helpers make: weekday, save-slot existence, saved file time."""
    def __init__(self):
        super().__init__();self.dow=1;self.slots={}
    def native(self,name,aa):
        if name=='L_Calendar::GetDayOfWeek':return self.dow
        if name=='AFL_GameSave_IsExistFile':return int(aa[0] in self.slots)
        if name=='AFL_GameSave_GetFileInfo':
            if aa[0] not in self.slots:return 0
            y,mo,d,h,mi,s=self.slots[aa[0]];vals=[y,mo,d,0,h,mi,s]
            for k,val in enumerate(vals):pg,idx=aa[1+2*k],aa[2+2*k];pg[idx]=val
            return 1
        return super().native(name,aa)

def norm(text):
    """Instruction list with jump targets rewritten as instruction indices (relocated bodies have new addresses)."""
    ops=[];labels={}
    for line in text.splitlines():
        l=line.strip()
        if not l or l.startswith((';','FUNC ','ENDFUNC ','EOF ')):continue
        if l.endswith(':'):labels[l[:-1]]=len(ops);continue
        ops.append(l)
    out=[]
    for l in ops:
        p=l.split(maxsplit=1)
        if p[0] in ('IFZ','IFNZ','JUMP','SJUMP','CALLONJUMP') and len(p)>1 and p[1] in labels:l=p[0]+' @'+str(labels[p[1]])
        out.append(l)
    return out

def main():
    V6.main();r7_checks()
    ev=a.readj(O/'build_evidence.json');info=ev['autosave'];counts=collections.Counter();v=VM8()
    W=info['weekly_slot'];assert W==49 and v.run('KR_T8WeeklySlot')==49
    # 1. schedule: every morning; Monday -> weekly, other weekdays -> 999
    for dow in range(7):
        v.dow=dow;assert v.run('KR_T8AutoSaveDay')==1 and v.run('KR_T8AutoSaveSlot')==(W if dow==1 else 999),dow
    counts['schedule_all_weekdays']=7
    # 2. labels, font slot, save-screen lock
    assert ko(v.run('KR_T8DispSaveNo',[999]))=='일간' and ko(v.run('KR_T8DispSaveNo',[W]))=='주간'
    assert [v.run('KR_T8DispSaveNo',[n]) for n in (1,7,12,48)]==['01','07','12','48']
    assert v.run('C_SaveLoadViewCell@GetDispSaveNo',[W])==v.run('KR_T8DispSaveNo',[W]);counts['labels']+=1
    assert v.run('KR_T8AutoAlias',[W])==999 and v.run('KR_T8AutoAlias',[999])==999 and v.run('KR_T8AutoAlias',[5])==5;counts['auto_alias']+=1
    assert [v.run('KR_T8IsManualSlot',[n]) for n in (999,W)]==[0,0] and all(v.run('KR_T8IsManualSlot',[n])==1 for n in range(1,49));counts['lock_only_autosaves']+=1
    # 3. newest search: the weekly slot counts only when autosaves are included
    v.slots={W:(2026,9,21,8,0,0),3:(2026,9,20,8,0,0)}
    assert v.run('KR_T8NewestExists',[W,0])==0 and v.run('KR_T8NewestExists',[W,1])==1 and v.run('KR_T8NewestExists',[3,0])==1 and v.run('KR_T8NewestExists',[4,1])==0
    counts['newest_search_skips_weekly_without_auto']+=1
    # 4. load-confirm title (the runtime strings as IsExecLoad builds them)
    v.titles=[]
    v.run('KR_T8SlotTitle',['●[No.'+str(W)+']'+proxy('불러오기 확인')]);v.run('KR_T8SlotTitle',['●['+proxy('자동')+'] '+proxy('불러오기 확인')])
    v.run('KR_T8SlotTitle',['●[No.12]'+proxy('불러오기 확인')])
    assert v.titles==['●[주간] 불러오기 확인','●[일간] 불러오기 확인','●[No.12]불러오기 확인'],v.titles;counts['load_confirm_titles']=3
    # 5. game-over resume: newer file time of the two autosaves
    cases=[({},999),({999:(2026,9,24,3,20,0)},999),({W:(2026,9,21,8,0,0)},W),
           ({999:(2026,9,24,3,20,0),W:(2026,9,21,8,0,0)},999),({999:(2026,9,20,23,0,0),W:(2026,9,21,8,0,0)},W),
           ({999:(2026,9,21,7,59,59),W:(2026,9,21,8,0,0)},W),({999:(2026,9,21,8,0,1),W:(2026,9,21,8,0,0)},999),
           ({999:(2026,9,21,8,0,0),W:(2026,9,21,8,0,0)},999),({999:(2025,12,31,23,0,0),W:(2026,1,1,0,0,0)},W)]
    for slots,want in cases:v.slots=dict(slots);assert v.run('KR_T8NewestAutoSlot')==want,(slots,want)
    counts['game_over_newest_cases']=len(cases)
    # 6. relocated save/load functions: original body with exactly the intended replacement
    m=b.read_meta(O/'candidate_meta.json');fn=lambda s:next(f['index'] for f in m['functions'] if b.raw_symbol(m,f['index'])==s)
    exp={}
    fid=fn('C_SaveLoadViewCell@GetDispSaveNo');exp[fid]=['.LOCALREF saveNo','CALLFUNC KR_T8DispSaveNo','RETURN']
    for n in ['C_SaveLoadViewCell@GetSaveNoFont','C_SceneSaveLoadView@GetSaveComment']:
        fid=fn(n);exp[fid]=norm(e.begin((O/f'original_{fid}.jam').read_text('utf8'),e.ALIAS_PREFIX))
        assert exp[fid][:6]==['PUSHLOCALPAGE','PUSH 0','.LOCALREF saveNo','CALLFUNC KR_T8AutoAlias','X_ASSIGN 1','POP'],exp[fid][:6]
        assert [v['name'] for v in m['functions'][fid]['arguments']][0]=='saveNo'
    fid=fn('C_SceneSaveLoadView@Update');src=(O/f'original_{fid}.jam').read_text('utf8');assert src.count(e.UPDATE_LOCK_OLD)==3
    exp[fid]=norm(src.replace(e.UPDATE_LOCK_OLD,e.UPDATE_LOCK_NEW))
    fid=fn('N_SaveLoad::GetNewDataNo');src=(O/f'original_{fid}.jam').read_text('utf8');assert src.count(e.NEWEST_OLD)==1
    exp[fid]=norm(src.replace(e.NEWEST_OLD,e.NEWEST_NEW))
    for fid,want in exp.items():
        got=norm((O/f'built_{fid}.jam').read_text('utf8'));assert got==want,(fid,[(i,x,y) for i,(x,y) in enumerate(zip(got,want)) if x!=y][:3],len(got),len(want))
        assert fid in ev['relocated'];counts['relocated_body_exact']+=1
    # 7. operands, read back from the built code; the base code is r7's except these sites
    raw=b.unpack((O/'NightRemaster.ain').read_bytes());base=b.unpack((O/'baseline_NightRemaster.ain').read_bytes())
    ids=ev['added_functions'];day=info['fid'];start=m['functions'][day]['address']
    op=lambda addr:struct.unpack_from('<Hi',raw,16+addr);bop=lambda addr:struct.unpack_from('<Hi',base,16+addr)
    dow=fn('L_Calendar::GetDayOfWeek');auto=fn('■セーブ／オートセーブ実行')
    assert op(start+info['site_offset'])==(0x30,ids['KR_T8AutoSaveDay']) and bop(start+info['site_offset'])==(0x30,dow)
    assert op(start+info['slot_offset'])==(0x30,ids['KR_T8AutoSaveSlot']) and bop(start+info['slot_offset'])==(0,999)
    assert op(start+info['autosave_call_offset'])==(0x30,auto) and op(start+info['kept_day_of_week_call_offset'])==(0x30,dow)
    assert op(info['is_exec_load']['site'])==(0x30,ids['KR_T8SlotTitle']) and bop(info['is_exec_load']['site'])==(0x30,fn('■選択ダイアログ／タイトル設定'))
    for ad in info['game_over']['sites']:assert op(ad)==(0x30,ids['KR_T8NewestAutoSlot']) and bop(ad)==(0,999)
    counts['operand_sites']=5
    sites=set()
    for ad in [start+info['site_offset'],start+info['slot_offset'],info['is_exec_load']['site']]+info['game_over']['sites']+list(EXTRA_SITES):sites|=set(range(ad,ad+6))
    r7raw=b.unpack((R7/'NightRemaster.ain').read_bytes());nb=struct.unpack_from('<I',base,12)[0]
    diff={i for i in range(nb) if r7raw[16+i]!=raw[16+i]};assert diff and diff<=sites,[hex(i) for i in sorted(diff-sites)][:8]
    counts['base_code_r7_except_operands']+=1
    assert info['autosave_return_offset']==354;counts['user_autosave_frame_offset_matches']+=1
    # 8. r7 functions keep their metadata; PACT/EX byte-identical to r7
    m7=b.read_meta(R7/'candidate_meta.json');ev7=a.readj(R7/'build_evidence.json')
    new_ids={k:v for k,v in ids.items() if k not in ev7['added_functions']};assert len(new_ids)==NEW_FUNCTIONS and min(new_ids.values())==len(m7['functions']),len(new_ids)
    assert {k:v for k,v in ids.items() if k in ev7['added_functions']}==ev7['added_functions']
    new_reloc=set(ev['relocated'])-set(ev7['relocated']);assert new_reloc==set(exp)|set(EXTRA_RELOCATED),new_reloc
    shift=collections.defaultdict(set)
    for f7,f8 in zip(m7['functions'],m['functions']):
        if f7==f8:continue
        t=dict(f7);t['address']=f8['address'];assert t==f8,f7['index']
        kind='new_reloc' if f7['index'] in new_reloc else 'relocated' if f7['index'] in ev7['relocated'] else 'added' if f7['index'] in ev7['added_functions'].values() else None
        assert kind,(f7['index'],b.raw_symbol(m7,f7['index']));shift[kind].add(f8['address']-f7['address'])
    if STRICT_SHIFT:
        assert len(shift['added'])==1 and len(shift['relocated'])==1 and shift['new_reloc'],dict(shift)
        sa=next(iter(shift['added']));sr=next(iter(shift['relocated']));assert 0<sa and sr==2*sa,(sa,sr)
    else:
        assert shift['new_reloc'] and all(x>0 for k in ('added','relocated') for x in shift[k]),dict(shift);sa=sorted(shift['added']);sr=sorted(shift['relocated'])
    for k in m7:
        if k!='functions':assert m7[k]==m[k],k
    for n in ['NightRemasterPact.afa','NightRemasterEX.ex']:assert e.h(O/n)==e.h(R7/n),n
    counts['r7_metadata_pact_ex']+=1
    res=a.readj(O/'vm_verification.json');res['r8']=dict(counts=dict(counts),autosave=info,shift_added=sa,shift_relocated=sr)
    (O/'vm_verification.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(dict(r8=counts,shift_added=sa,shift_relocated=sr),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
