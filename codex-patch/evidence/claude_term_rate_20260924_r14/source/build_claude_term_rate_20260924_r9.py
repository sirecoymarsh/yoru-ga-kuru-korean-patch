"""Claude Opus 5.5 (2026-09-24) r9: r8 + per-character missing events in 플레이 정보 (user: 「달성률에서 각 캐릭터별로
몇월 며칠의 어느 이벤트가 비어있는지」): counts by month and kind, date windows and intimacy conditions of personal and
main-story events, 「지남」 once a window has passed in this save. r8 was never installed; r9 installs over r7.

r8 docstring: r7 + daily and weekly autosaves (user: 「일간 자동 세이브랑 주간 자동 세이브를 분리」).
The game's own day-start autosave runs every morning: Mondays go to the weekly slot 49 (page 10, 「주간」), other days to
999 (「일간」); dungeon rest cells and the ending keep writing 999. Operands only in 呼出／１日の始まり / IsExecLoad /
ExecGameOver; four save/load screen functions (never on a saved stack) are relocated for labels, lock and newest search.

r7 docstring: r6 + eight monster names localized (EX block 7, user decisions) + Codex review
CT-RATE-003 (home-rate toggle commits only after a verified write). EX joins the payload.

r6 docstring: r5 + the sweep report names the rewards the carry limit kept out.

r5 docstring: r4 + coloured result texts (treasure, trap, instant-kill receipt, sweep report)
+ per-character event rates in the homebase panel.

r4 docstring: r3 + trap result notices + homebase achievement panel (mods-tab toggle).

r3 docstring follows. Eight-term preferences, missing term display paths, achievement page.

Incremental over the installed runtime_repairs AIN. Display/UI only: MSG1, STR0 prefix, globals,
structures, save layout and every saved return frame stay exact. Existing helpers are redirected
in place (relocated) or edited with same-length operands; nothing in the translation changes.
"""
from pathlib import Path
import json,struct,re,copy,shutil,collections
import build_runtime_repairs_20260923 as previous
from build_dungeon_sweep_20260916 import lr,cf,push
from build_instant_loot_20260915 import begin
R=previous.R;HERE=previous.HERE;b=previous.b;p=previous.p;q=previous.q;a=b.a
BASE=previous.O
O=R/'staging/claude_term_rate_20260924_r9'
EXPECTED='cfda0681fb0c55d2088aa7d08be4b00259d3cefd0be512d353cf69db831a6a3d'
# r2..r9 rebuild the whole overlay on the pre-Claude base kept by the first install; r9 installs over r7 (r8 never installed).
INSTALLED=R/'evidence/claude_term_rate_20260924_r7/journal.json'
PREV=R/'evidence/claude_term_rate_20260924'
BASE_AIN=PREV/'before/NightRemaster.ain';BASE_PACT=PREV/'before/NightRemasterPact.afa'
BASE_PACT_SHA='efc527e804c4ae1abfd2b50ceca5a1bfa1384cc91afdc399cc6567468736ae49'
FILES=['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']
# The monster renames apply to the EX that r7 replaced (Codex's, kept in r7's evidence), not to the installed r7 EX.
BASE_EX=R/'evidence/claude_term_rate_20260924_r7/before/NightRemasterEX.ex'
BASE_EX_SHA='83304ebe454b756c46778de9d3e746b2cce59adad2943b96fb0a48015416072a'
AUTHOR='Claude Opus 5.5 (claude-opus-5-5)'
JP_EX=Path(r'P:\GAME\Compacted Files\[Ryuugames] RY-r119676\夜が来る！-Square of the MOON- Remastered\NightRemasterEX.ex')
CATALOG=R/'handoff_claude_terms_progress_20260923/event_catalog.json'
TMAP=R/'evidence/runtime_repairs_20260923/source/installed_translation_map.json'
# Index order is the preference file order; entries 0-6 keep their keys, 7 is new.
TERMS8=[('히카리',['히카리','광수','빛잡이'],108),('카샤',['카샤','화자','불지기'],108),('치로',['치로','쉭쉭이'],108),
        ('틈새',['틈새','하자마','틈'],108),('얼어붙은 밤',['얼어붙은 밤','토야','동야'],192),
        # Japanese readings: 真月 しんげつ (voices 1188/1471), 真夜 しんや (script ruby); つ as 츠 per this translation.
        ('참된 달',['참된 달','진월','신게츠'],120),('참된 밤',['참된 밤','진야','신야'],120),
        ('호무라',['호무라','화군','불무리'],108)]
# r3: the original Japanese word each row replaces (term menu labels).
LABELS8=['光狩','火者','チロ','狭間','凍夜','真月','真夜','火群']
ENDINGS=[(10523,'이즈미'),(20523,'쿄카'),(30523,'마나미'),(40523,'마코토'),(999,'보통 결말')]
def h(path):return a.sha(path)
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
def quote(s):return json.dumps(s,ensure_ascii=False)
def ex_strings(path):
    d=b.ex.decode_ex(path);return d,{k:v.value for k,v in d.strings.items()}

def use_terms():
    # b.tokens/render/expr read b.TERMS; the first seven keep Codex's attested behaviour.
    assert [t[0] for t in b.TERMS]==[t[0] for t in TERMS8[:7]]
    b.TERMS[:]=TERMS8

def dungeon_rows(kr,jp):
    rows=[]
    for k,v in kr.items():
        if k[:3]!=('block',5,'value') or k[-2:]!=('column',2):continue
        src=jp[k].decode('cp932');text=b.decode(v)
        if '狭間' in src:
            assert text.count('틈')==1 and '틈새' not in text,(src,text)
            i=text.index('틈');rows.append(dict(source=text,jp=src,tokens=[('s',text[:i]),('t',3),('s',text[i+1:])]))
        elif '火群' in src:
            assert text.startswith('화군 ') and text.count('화군')==1,(src,text)
            rows.append(dict(source=text,jp=src,tokens=[('t',7),('s',text[2:])]))
        else:
            assert not any(w in src for w in ['光狩','火者','チロ','凍夜','真月','真夜']),src
    assert sum('狭間' in r['jp'] for r in rows)==10 and sum('火群' in r['jp'] for r in rows)==61,len(rows)
    return rows

def joined(kr,prefix,skip_last_empty):
    items=sorted((k[-2],b.decode(v)) for k,v in kr.items() if k[:len(prefix)]==prefix and k[-3:-2]==('item',) and k[-1]=='value')
    lines=[t for _,t in items]
    if skip_last_empty and lines and lines[-1]=='':lines=lines[:-1]
    return '\n'.join(lines)

def display_rows(kr):
    old=a.readj(R/'evidence/term_switch_20260923/source/display_terms.json');rows=[]
    for r in old:
        if re.fullmatch(r'수수께끼의 틈 \d',r['source']):continue   # now dungeon rows, always on
        ts=b.tokens(r['source'])
        assert [list(x) if isinstance(x,tuple) else x for x in json.loads(json.dumps(ts))]==r['tokens'],(r['source'],ts,r['tokens'])
        rows.append(dict(source=r['source'],tokens=ts,origin='codex'))
    # L_Weapon::LoadComment joins lines with \n; ■ＡＤＶダイアログ joins with \n and drops the trailing empty line.
    comment=joined(kr,('block',40,'value','child',66,'child',0,'leaf_value'),False)
    adv=joined(kr,('block',41,'value','child',4,'leaf_value'),True)
    assert comment=='용에게 효과적인 검이지만,\n히카리에게 얼마나 통할지는\n알 수 없습니다.',comment
    assert adv.startswith('【이즈미】\n「틈새 안에서 가끔') and adv.endswith('물건인데…」'),adv
    for text in [comment,adv]:
        ts=b.tokens(text);assert any(k=='t' for k,v in ts),text
        rows.append(dict(source=text,tokens=ts,origin='claude'))
    return rows

def homura_pages(msgs,tmap):
    src={int(e['numeric_id']):e['source'] for e in tmap['entries'] if e['kind']=='message'}
    pages=a.readj(a.HERE/'message_page_groups.json')['pages'];hit=[]
    for pg in pages:
        ids=pg['body_message_ids'];jp=''.join(src.get(i,'') for i in ids)
        if '火群' in jp:
            assert '穂群' not in jp,ids
            hit.append(pg)
    covered=sorted(i for pg in hit for i in pg['body_message_ids'] if '호무라' in msgs[i])
    fire=sorted(i for i,s in src.items() if '火群' in s)
    assert covered and all(any(i in pg['body_message_ids'] for pg in hit) for i in fire),(covered,fire)
    # Every Korean 호무라 outside these pages must be 穂群 (shrine), never a term occurrence.
    for i,s in enumerate(msgs):
        if '호무라' in s and not any(i in pg['body_message_ids'] for pg in hit):
            pg=next((pg for pg in pages if i in pg['body_message_ids']),None)
            jp=''.join(src.get(j,'') for j in (pg['body_message_ids'] if pg else [i]))
            assert '穂群' in jp and '火群' not in jp,(i,s)
    return hit

def message_rows(msgs,hit):
    rows={};dynamic=[];static=[]
    for pg in hit:
        ids=pg['body_message_ids'];budget=716 if pg['window_type']=='Face' else 932
        entries={i:b.tokens(msgs[i]) for i in ids if any(k=='t' for k,v in b.tokens(msgs[i]))}
        assert all(b.render(t)==msgs[i] for i,t in entries.items())
        if all(b.width(b.render(entries.get(i,[('s',msgs[i])]),worst=True))<=budget for i in ids):
            for i,t in entries.items():rows[i]=b.expr(t);static.append(dict(id=i,source=msgs[i],tokens=t))
            continue
        assert pg['complete'] and pg['font_command']==0 and pg['window_type'] in ['Face','Text','All']
        nonempty=[msgs[i] for i in ids if msgs[i].strip()];quoted=nonempty[0].startswith(('「','（'))
        full=' '.join(t.strip('　 ') for t in nonempty);full=re.sub(r' (?=[」』）】!?！？.,、。])','',full)
        ts=b.tokens(full);lines=b.wrap(b.render(ts,worst=True),budget,quoted)
        assert lines is not None and len(lines)<=len(ids),(ids,lines)
        for pos,i in enumerate(ids):rows[i]=f'KR_TermWrapLine({b.expr(ts)}, {budget}, {pos}, {str(quoted).lower()})'
        dynamic.append(dict(ids=ids,budget=budget,worst=lines,quoted=quoted,source=full))
    return rows,static,dynamic

def event_ranges(m,raw_versions):
    cat=a.readj(CATALOG);spans=[]
    for e in cat['events']:
        fid=e['fid'];start=m['functions'][fid]['address'];v=next(v for v in raw_versions[fid] if v['start']==start)
        nums=[int(op.split()[1],16) for _,op in v['ops'] if op.startswith('MSG ')]
        assert len(nums)==e['messages'] and nums==list(range(nums[0],nums[0]+len(nums))),e['key']
        spans.append((nums[0],nums[-1]))
    spans.sort();merged=[]
    for s,t in spans:
        assert not merged or s>merged[-1][1]
        if merged and s==merged[-1][1]+1:merged[-1]=(merged[-1][0],t)
        else:merged.append((s,t))
    total=sum(t-s+1 for s,t in merged);assert total==sum(e['messages'] for e in cat['events'])
    return merged,total,cat['group_counts']

def gallery(d):
    # CG閲覧.データ: columns txt, thumb, cg1..cg7 ("CG%04d"); a cell is open when any of its CGs is registered.
    # 回想.ページ１..７: columns id, needEvNo, playEvNo; unlock number = first position of needEvNo + 1
    # (N_ModeScene: g_MemModeNoList.Find(needEvNo)+1), checked with Ａ＿回想確認.
    ss={k:b.decode(v.value) for k,v in d.strings.items()}
    def ival(n):return struct.unpack('<i',n.raw)[0]
    def blk(name):return next(i for i,bk in enumerate(d.blocks) if b.decode(bk.name.value)==name)
    def children(bi):return sorted((k[4],t) for k,t in ss.items() if k[:4]==('block',bi,'value','child') and len(k)==6 and k[-1]=='name')
    def table(bi,ci):
        rows=collections.defaultdict(dict)
        for k,v in d.scalars.items():
            if k[:6]==('block',bi,'value','child',ci,'leaf_value') and len(k)==10 and k[6]=='row':rows[k[7]][k[9]]=ival(v)
        return [rows[r] for r in sorted(rows)]
    cgb=blk('CG閲覧');ci=next(c for c,t in children(cgb) if t=='データ');cells=[]
    for r,row in enumerate(table(cgb,ci)):
        names=[f'CG{row[c]:04d}' for c in range(2,9) if row.get(c,0)];assert names,r;cells.append(dict(row=r,cg_names=names))
    scb=blk('回想');pages=children(scb);assert [t for _,t in pages]==['ページ'+c for c in '１２３４５６７'],pages
    need=[row[1] for ci,_ in pages for row in table(scb,ci)]
    numbers=sorted(set(need.index(n)+1 for n in need))
    ending={str(ev):need.index(ev)+1 for ev,_ in ENDINGS}
    return dict(cells=cells),dict(entries=len(need),need=need,reg_numbers=numbers,ending_reg=ending)

def widen_map_name(rt):
    src=BASE_PACT;assert h(src)==BASE_PACT_SHA
    # Dungeon name plate (SceneDungeon 構築_マップ名土台): canvas 300x36, inner fill 298x34, text at (5,4), font 1 28px.
    # With 호무라 as default, 「… 최심층⑩」/「…·이면층」 measure 312px; widen to keep a 5px right margin.
    from build_remaster_multiplier_20260915 import read_afa3,rebuild
    arc=read_afa3(src);entry=arc.entries[160];assert entry.name.endswith('SceneDungeon.pactex'),entry.name
    with src.open('rb') as f:f.seek(entry.absolute_offset);raw=f.read(entry.size)
    (O/'original_160.pactex').write_bytes(raw);doc=b.ex.decode_ex(O/'original_160.pactex')
    hits=[k for k,v in doc.strings.items() if k[-1]=='leaf_value' and v.value==('構築_マップ名土台').encode('cp932')];assert len(hits)==1,hits
    base=hits[0][:-3];changes=[]
    for cmd,old,new,height in [(0,300,324,36),(2,298,322,34)]:
        pre=base+('child',43,'child',2,'child',1,'child',cmd,'child',3,'leaf_value','item')
        w=doc.scalars[pre+(4,'value')];hgt=doc.scalars[pre+(5,'value')]
        assert struct.unpack('<i',w.raw)[0]==old and struct.unpack('<i',hgt.raw)[0]==height,(cmd,w.raw,hgt.raw)
        w.raw=struct.pack('<i',new);changes.append(dict(command=cmd,before=old,after=new,height=height))
    text=[k for k,v in doc.strings.items() if k[-1]=='leaf_value' and v.value==('テキスト_マップ名').encode('cp932') and k[:len(base)]==base]
    assert text,'map name text part must sit inside the widened base'
    out=O/'pact_160.pactex';out.write_bytes(b.ex.encode_ex(doc.header,doc.serialize_payload()))
    back=b.ex.decode_ex(out)
    for c in changes:
        pre=base+('child',43,'child',2,'child',1,'child',c['command'],'child',3,'leaf_value','item')
        assert struct.unpack('<i',back.scalars[pre+(4,'value')].raw)[0]==c['after'];back.scalars[pre+(4,'value')].raw=struct.pack('<i',c['before'])
    assert back.serialize_payload()==doc.raw_payload,'reverting the two widths must reproduce the original payload'
    return out,dict(entry=160,name=entry.name,changes=changes,reverse_exact=True)

# ---- r4 (Claude Opus 5.5, 2026-09-24): trap result notices, homebase achievement panel ----
HOME_PANEL={};TRAP_NOTICE={}
TOGGLE_LABEL='    본거지에 달성률 표시'
NOTICE_TITLE=('보물상자','보물상자 · 함정')
MAPCELL={27005:'C_MapCellInfo@ObjectId::get',27008:'C_MapCellInfo@ObjectSubId::get',27029:'C_MapCellInfo@IsEventDungeon::get',
         27025:'C_MapCellInfo@IsRemoved::set',27022:'C_MapCellInfo@IsShowObject::set'}

def trap_cell_body(fid):
    # ObjectId == 5 && (!IsEventDungeon || ObjectSubId == 0): the live StepedOnCell instant-disarm test, same CALLMETHODs.
    no='kr_t8_trapcell_no';yes='kr_t8_trapcell_yes'
    body=f'FUNC {fid}\n'
    body+=lr('cell')+push(27005)+'\tCALLMETHOD 0\n'+push(5)+f'\tNOTE\n\tIFNZ {no}\n'
    body+=lr('cell')+push(27029)+f'\tCALLMETHOD 0\n\tIFZ {yes}\n'
    body+=lr('cell')+push(27008)+'\tCALLMETHOD 0\n'+push(0)+f'\tNOTE\n\tIFNZ {no}\n'
    body+=f'{yes}:\n'+push(1)+'\tRETURN\n'+f'{no}:\n'+push(0)+'\tRETURN\nENDFUNC KR_T8TrapCell\n'
    return body

def checkbox_sync(method,fno):
    # Codex's pattern in C_ConfigView@EventConf*: SetCheckStatForParts/ForAsra(partsName, delegate of a free function).
    return '\tPUSHSTRUCTPAGE\n'+push(method)+'\tS_PUSH "KR_HomeRateToggle"\n'+push(-1)+push(fno)+'\tDG_NEW_FROM_METHOD\n\tCALLMETHOD 2\n'

def fidof(m,name):
    hits=[f['index'] for f in m['functions'] if b.raw_symbol(m,f['index'])==name];assert len(hits)==1,(name,hits)
    return hits[0]

def trap_edits(m,dm,ids,live,edit):
    same=lambda x,y:[v['type'] for v in m['functions'][x]['arguments']]==[v['type'] for v in dm['functions'][y]['arguments']] and m['functions'][x]['return-type']==dm['functions'][y]['return-type']
    for fid,name in MAPCELL.items():assert b.raw_symbol(m,fid)==name,(fid,b.raw_symbol(m,fid))
    assert b.raw_symbol(m,29827)=='C_ConfigView@SetCheckStatForParts' and b.raw_symbol(m,29828)=='C_ConfigView@SetCheckStatForAsra'
    assert b.raw_symbol(m,28571)=='C_SceneHomebaseView@BeginTop' and b.raw_symbol(m,28572)=='C_SceneHomebaseView@EndTop'
    # 1) instant disarm: StepedOnCell removes the trap cell silently right after KR_NoticeInstant returns false.
    notice=fidof(m,'KR_NoticeInstant');step=fidof(m,'C_SceneDungeon@StepedOnCell');assert same(notice,ids['KR_T8NoticeInstant'])
    ops=live(step)['ops'];calls=[k for k,(ad,op) in enumerate(ops) if op==f'CALLFUNC 0x{notice:x}'];assert len(calls)==1,calls
    tail=[op for _,op in ops[calls[0]:calls[0]+80]]
    seq=[f'CALLFUNC 0x{fidof(m,"KR_GetTrap"):x}',f'PUSH 0x{27005:x}','PUSH 0x5','NOTE',f'PUSH 0x{27029:x}',
         f'PUSH 0x{27008:x}','PUSH 0x0','NOTE',f'PUSH 0x{27025:x}',f'PUSH 0x{27022:x}']
    pos=0
    for op in tail:
        if pos<len(seq) and op==seq[pos]:pos+=1
    assert pos==len(seq),('instant-disarm branch changed',pos,tail)
    edit(step,ops[calls[0]][0],struct.pack('<Hi',0x30,notice),struct.pack('<Hi',0x30,ids['KR_T8NoticeInstant']),'instant disarm posts a notice (that path has no dialog)')
    # 2) disarm attempt (C_SceneDungeon@Trap -> L_Dungeon::RelieveTrap; instant disarm answers true there).
    relieve=fidof(m,'L_Dungeon::RelieveTrap');trap=fidof(m,'C_SceneDungeon@Trap');assert same(relieve,ids['KR_T8RelieveTrap'])
    calls=[ad for ad,op in live(trap)['ops'] if op==f'CALLFUNC 0x{relieve:x}'];assert len(calls)==1,calls
    edit(trap,calls[0],struct.pack('<Hi',0x30,relieve),struct.pack('<Hi',0x30,ids['KR_T8RelieveTrap']),'disarm result kept as a notice line')
    # 3) every trap effect dialog (L_Trap::Execute01-12) also becomes a notice line; the dialog itself is unchanged.
    dialog=fidof(m,'■シンプルダイアログ');assert same(dialog,ids['KR_T8TrapDialog'])
    want={1:2,2:3,3:6,4:6,5:1,6:1,7:1,8:1,9:1,10:1,11:1,12:1};n=0
    for k,count in want.items():
        fid=fidof(m,f'L_Trap::Execute{k:02d}');calls=[ad for ad,op in live(fid)['ops'] if op==f'CALLFUNC 0x{dialog:x}'];assert len(calls)==count,(k,calls)
        for ad in calls:
            edit(fid,ad,struct.pack('<Hi',0x30,dialog),struct.pack('<Hi',0x30,ids['KR_T8TrapDialog']),'trap effect dialog also kept as a notice line');n+=1
    TRAP_NOTICE.update(instant_site=b.raw_symbol(m,step),relieve_site=b.raw_symbol(m,trap),dialog_sites=n,notice='KR_ChestShow (Codex dungeon notice, 3 lines, 4.5 s)')

def build_pacts():
    from build_remaster_multiplier_20260915 import read_afa3,rebuild,part,child,val,allparts,rename,setlist,ss,si,txt_info
    import build_mod_tab_20260915 as mt
    src=BASE_PACT;assert h(src)==BASE_PACT_SHA;arc=read_afa3(src)
    out160,info160=widen_map_name(None)
    # Codex's dungeon notice (KR_ChestNotice, in SceneDungeon since notice_repair) now also carries trap result
    # lines: its fixed title names both. Same entry as the map-name widening, applied on top of it.
    doc=b.ex.decode_ex(out160);ti=txt_info(part(doc,'KR_ChestTitle'));assert b.decode(val(ti,'テキスト').value)==NOTICE_TITLE[0],b.decode(val(ti,'テキスト').value)
    widened=doc.serialize_payload();ss(ti,'テキスト',NOTICE_TITLE[1],True)
    tagged=[]
    for key in ['KR_ChestLine1','KR_ChestLine2','KR_ChestLine3','KR_ReceiptBody']:
        tx=txt_info(part(doc,key));dd=child(tx,'テキスト装飾');before=(mt.scalar(val(tx,'タグ処理有効')),[mt.scalar(i.value.payload) for i in val(dd,'フォント色').items])
        si(tx,'タグ処理有効',1);setlist(dd,'フォント色',[255,255,255]);tagged.append((key,tx,dd,before))
    changed=doc.serialize_payload()
    out160.write_bytes(b.ex.encode_ex(doc.header,changed));assert b.ex.decode_ex(out160).serialize_payload()==changed
    for key,tx,dd,(tag0,col0) in tagged:si(tx,'タグ処理有効',tag0);setlist(dd,'フォント色',col0)
    ss(ti,'テキスト',NOTICE_TITLE[0],True);assert doc.serialize_payload()==widened,'notice edits revert must give the widened entry'
    COLOR_INFO.update(pact160={k:dict(tag_before=t0,color_before=c0,tag_after=1,color_after=[255,255,255]) for k,_,_,(t0,c0) in tagged})
    docs={}
    for i,tail in [(177,'Common/AddArea.pactex'),(185,'Asra/Mods.pactex')]:
        entry=arc.entries[i];assert entry.name.endswith(tail),(i,entry.name)
        with src.open('rb') as f:f.seek(entry.absolute_offset);(O/f'original_{i}.pactex').write_bytes(f.read(entry.size))
        docs[i]=b.ex.decode_ex(O/f'original_{i}.pactex')
    # AddArea is drawn above the game (root Z 100000): a hidden container in the left margin (x 0-160,
    # far above the homebase system button) holding a title and a body text part, font 259 like Codex's notices.
    doc=docs[177];parent=part(doc,'矩形_000');mt.ORDER=copy.deepcopy(val(parent,'子パーツリスト').items[0])
    grp=copy.deepcopy(part(doc,'矩形_デバッグ'));rename(grp,'KR_HomeRate');setlist(grp,'座標',[0,20,40]);si(grp,'表示',0)
    child(grp,'子パーツ').children=[];val(grp,'子パーツリスト').items=[]
    donor=part(doc,'テキスト_デバッグ情報')
    # 18px keeps the widest line (「대사　　100.0%」, about 150px) inside the 160px margin.
    rows=[('KR_HomeRateTitle','달성률',0,22,[255,224,96]),('KR_HomeRateBody','',32,18,[255,255,255])]
    for name,text,y,size,color in rows:
        p=copy.deepcopy(donor);rename(p,name);setlist(p,'座標',[8,y,1]);si(p,'原点座標モード',1);si(p,'表示',1)
        ti=txt_info(p);ss(ti,'テキスト',text,True);si(ti,'タグ処理有効',int(name=='KR_HomeRateBody'));si(ti,'一文字辺りの表示時間',0)
        d=child(ti,'テキスト装飾');si(d,'フォントタイプ',259);si(d,'フォントサイズ',size);si(d,'字間隔',0);si(d,'行間隔',4)
        setlist(d,'フォント色',color);si(d,'フォント縁取り',1);setlist(d,'フォント縁取り色',[0,0,0])
        mt.add(grp,p)
    for p in allparts(grp):si(p,'クリック許可',0);si(p,'オンカーソル透過',1);si(p,'メッセージウィンドウ表示連動',0)
    mt.add(parent,grp)
    out177=O/'pact_177.pactex';out177.write_bytes(b.ex.encode_ex(doc.header,doc.serialize_payload()))
    assert b.ex.decode_ex(out177).serialize_payload()==doc.serialize_payload()
    mt.remove(parent,'KR_HomeRate');assert doc.serialize_payload()==b.ex.decode_ex(O/'original_177.pactex').serialize_payload(),'AddArea: removing KR_HomeRate must give the original'
    # Mods tab: checkbox cloned from Codex's KR_SmartAutoToggle, right column (x 783) on the title row.
    doc=docs[185];root=part(doc,'ルートパーツ');mt.ORDER=copy.deepcopy(val(root,'子パーツリスト').items[0])
    assert any(mt.name(t)=='KR_SmartAutoToggle' for t in child(root,'子パーツ').children),'toggle donor must be a root child'
    tog=copy.deepcopy(part(doc,'KR_SmartAutoToggle'));rename(tog,'KR_HomeRateToggle');setlist(tog,'座標',[783,38,252])
    info=child(tog,'種類別情報');ss(info,'テキスト',TOGGLE_LABEL,True);si(info,'チェック状態',0)
    mt.add(root,tog)
    out185=O/'pact_185.pactex';out185.write_bytes(b.ex.encode_ex(doc.header,doc.serialize_payload()))
    assert b.ex.decode_ex(out185).serialize_payload()==doc.serialize_payload()
    mt.remove(root,'KR_HomeRateToggle');assert doc.serialize_payload()==b.ex.decode_ex(O/'original_185.pactex').serialize_payload(),'Mods: removing the toggle must give the original'
    archive=rebuild(src,O/'NightRemasterPact.afa',{160:out160,177:out177,185:out185})
    HOME_PANEL.update(pact_entry=177,group='KR_HomeRate',parts=['KR_HomeRateTitle','KR_HomeRateBody'],origin=[0,20],font_type=259,
                      toggle='KR_HomeRateToggle',toggle_pos=[783,38],toggle_label=TOGGLE_LABEL.strip(),preference_file='YoruKR_HomeRate.dat',default='off',
                      shown_by='C_SceneHomebaseView@BeginTop (prepended KR_T8HomeEnter)',hidden_by='C_SceneHomebaseView@EndTop (prepended KR_T8HomeLeave)')
    return dict(map_name=info160,dungeon_notice=dict(entry=160,part='KR_ChestTitle',before=NOTICE_TITLE[0],after=NOTICE_TITLE[1],reverse_exact=True),
                add_area=dict(entry=177,added='KR_HomeRate',reverse_exact=True),mods=dict(entry=185,added='KR_HomeRateToggle',reverse_exact=True),archive=archive)

# ---- r5 (Claude Opus 5.5, 2026-09-24): coloured result texts, per-character event rates ----
COLOR_INFO={};CHAR_INFO={};SWEEP_LOST={}
# Party members by catalog person id (pool names いずみ/鏡花/真言美/マコト/新開/星川/百瀬), labels as in the translation.
CHARS=[(2,'이즈미'),(3,'쿄카'),(4,'마나미'),(5,'마코토'),(6,'신카이'),(7,'호시카와'),(8,'모모세')]
TEXT_SET=('\tPUSHSTRUCTPAGE\n\tPUSH 2\n\tX_REF 2\n\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n\tPUSH 0\n\tX_REF 1\n\tX_MOV 2 1\n'
          '\tPUSH 7\n\tADD\n\tX_REF 1\n\t.LOCALREF txt\n')
# ITextParts vtable slot 25 = CTextParts@Tag::set (vtable of parts::detail::CTextParts@2: slot 7 Text::set,
# 10 Font::set, 22 OriginPos::set, 25 Tag::set). Only a text that carries a ${font tag switches it on.
TAG_ON=('\t.LOCALREF txt\n\tS_PUSH "${font"\n\tCALLHLL String Find 0\n\tPUSH 0\n\tLT\n\tIFNZ kr_t8_msgdlg_plain\n'
        '\tPUSHSTRUCTPAGE\n\tPUSH 2\n\tX_REF 2\n\tX_MOV 2 1\n\tX_DUP 1\n\tX_MOV 3 1\n\tPUSH 0\n\tX_REF 1\n\tX_MOV 2 1\n'
        '\tPUSH 25\n\tADD\n\tX_REF 1\n\tPUSH 1\n\tX_DUP 1\n\tX_MOV 4 1\n\tCALLMETHOD 1\n\tPOP\nkr_t8_msgdlg_plain:\n')
def reassign(arg,fn):
    # arg = fn(arg), the same sequence C_MessageDialog@Create uses for txt = KR_ResolveJosa(KR_TermDisplay(txt)).
    return '\tPUSHLOCALPAGE\n\tPUSH 0\n'+lr(arg)+'\tA_REF\n'+cf(fn)+'\tS_ASSIGN\n\tDELETE\n'

def char_jaf(jaf,m,src):
    cat=a.readj(CATALOG);events=cat['events']
    # Same registration names as the live KR_PlayerEventCount (Codex): every catalog fn, nothing else.
    path=O/'original_KR_PlayerEventCount.jam';b.cmd('ain','dump','--function','KR_PlayerEventCount','-o',path,src)
    pushed=[json.loads(x) for x in re.findall(r'S_PUSH (".*")',path.read_text('utf8'))]
    assert sorted(pushed)==sorted(e['fn'] for e in events) and len(pushed)==1043,(len(pushed),)
    rows=[];body='';totals='';labels=''
    for p,name in CHARS:
        fns=[e['fn'] for e in events if any(t.get('person')==p or t.get('person2')==p for t in e['triggers'])]
        assert fns and len(set(fns))==len(fns),p
        groups=collections.Counter(e['group'] for e in events if e['fn'] in set(fns))
        body+=f'    if (p == {p}) {{\n'+''.join(f'        if (N_ScenarioRegister::IsRegisteredEvent({quote(fn)})) n++;\n' for fn in fns)+'    }\n'
        totals+=f'if (p == {p}) return {len(fns)}; '
        label=name+'　'*(4-len(name));assert len(label)==4,label
        labels+=f'if (p == {p}) return {quote(label)}; '
        rows.append(dict(person=p,name=name,events=len(fns),by_group={str(k):v for k,v in sorted(groups.items())}))
    CHAR_INFO.update(rows=rows,basis='catalog triggers naming the person (person or person2); this save (IsRegisteredEvent)')
    return jaf.replace('/*CHAR_EVENTS*/',body).replace('/*CHAR_TOTALS*/',totals).replace('/*CHAR_LABELS*/',labels)

# ---- r7 (Claude Opus 5.5, 2026-09-24): monster names the user chose to localize (EX block 7, name field) ----
MONSTER_INFO={}
# id: (Japanese source, current Korean, new Korean, reason) - user decisions 2026-09-24.
MONSTER_RENAMES={
 17:('獏','바쿠','맥','꿈을 먹는 맥(獏); 사용자 예시'),
 28:('ベロベロ','베로베로','날름날름','혀로 핥는 의태어 べろべろ; 공격도 핥기'),
 23:('御牛頭','어우두','소머리','지옥의 소머리 귀신(牛頭); 짝인 牝馬頭가 이미 암말머리'),
 27:('虹光鳥','무지개빛 새','무지갯빛 새','맞춤법(사이시옷)'),
 3:('ケムジラー','케무질러','털뭉치','毛むくじゃら(털북숭이)에서 온 이름, 갈색 털 뭉치 그림'),
 21:('ケムゲラー','케무게라','푸른 털뭉치','같은 계열의 파란 털 뭉치(번개)'),
 6:('車地虎','샤치토라','범고래호랑이','シャチ(범고래)+トラ(호랑이), 호랑이 머리에 물고기 꼬리'),
 18:('炎円羅','염원라','불바퀴','炎(불)+円(둥근 바퀴), 불타는 바퀴 그림; 煙々羅 말장난'),
}
def monster_names(rt):
    from build_item_skill_names_20260915 import replace_ex
    from audit_dynamic_ui_20260915 import ENC
    from audit_message_pixel_widths import parse_fnl_font,select_fnl_face,WidthMeasurer,sjis_bytes_to_fnl_index
    src=BASE_EX;assert h(src)==BASE_EX_SHA,'EX base moved';jp=b.ex.decode_ex(JP_EX);kr=b.ex.decode_ex(src);edits=[]
    rows={}
    for tj,tk in zip(jp.blocks[7].payload.children,kr.blocks[7].payload.children):
        mid=int(tj.name.value.decode('cp932'));assert tk.name.value==tj.name.value
        jn=jp.strings[tj.leaf_value.payload.items[2].value.payload.path].value.decode('cp932')
        node=tk.leaf_value.payload.items[2].value.payload;kn=b.decode(kr.strings[node.path].value)
        rows[mid]=(jn,kn,node.path)
    assert len(rows)==85
    for mid,(jn,old,new,why) in MONSTER_RENAMES.items():
        j,k,path=rows[mid];assert (j,k)==(jn,old),(mid,j,k)
        edits.append(dict(stable_id=f'EX:7:{mid}:name',path=list(path),before=old,source=jn,target=new,category='enemy_name',reason=why))
    # every other appearance of the old names is checked: they occur only in this field
    olds={e['before'] for e in edits};seen=collections.Counter()
    for p,n in kr.strings.items():
        try:s=b.decode(n.value)
        except Exception:continue
        for o in olds:
            if o in s:seen[o]+=1
    assert all(seen[o]==1 for o in olds),seen
    report=replace_ex(src,O/'NightRemasterEX.ex',edits)
    _,faces=parse_fnl_font(rt/'NightRemasterFont.fnl',1);proxy={c:sjis_bytes_to_fnl_index(x) for c,x in ENC.items()}
    face,den,_=select_fnl_face(faces,20);meter=WidthMeasurer(face,den,proxy,0,0,0);widths={}
    for e in edits:
        w=meter.measure(e['target'],True)['lines'][0]['width_px'];assert w<=140,(e['target'],w);widths[e['target']]=w
        assert b.decode(b.encode(e['target']))==e['target']
    MONSTER_INFO.update(edits=[dict(e,width_px=widths[e['target']]) for e in edits],ex=report,budget='font 1, 20px, 140px (Codex enemy-name layout check)')
    return MONSTER_INFO

# ---- r8 (Claude Opus 5.5, 2026-09-24): daily and weekly autosaves through the game's own autosave call ----
AUTOSAVE_INFO={}
WEEKLY_SLOT=49
def _fn(m,s):
    hit=[f['index'] for f in m['functions'] if b.raw_symbol(m,f['index'])==s];assert len(hit)==1,(s,hit);return hit[0]

def autosave_edit(m,dm,ids,live,edit):
    """Same-length operand edits in unchanged original functions.
    呼出／１日の始まり: CALLFUNC L_Calendar::GetDayOfWeek; PUSH 1; EQUALE; IFNZ -> PUSH 999; CALLFUNC ■セーブ／オートセーブ実行; POP
      -> CALLFUNC KR_T8AutoSaveDay (every morning) and PUSH 999 -> CALLFUNC KR_T8AutoSaveSlot (Monday -> weekly slot).
    C_SceneSaveLoad@IsExecLoad: CALLFUNC ■選択ダイアログ／タイトル設定 -> KR_T8SlotTitle (「●[주간]」/「●[일간]」 titles).
    C_SceneGame@ExecGameOver: both PUSH 999 (exists check, load) -> CALLFUNC KR_T8NewestAutoSlot."""
    day=30087;assert b.raw_symbol(m,day)=='呼出／１日の始まり'
    dow=_fn(m,'L_Calendar::GetDayOfWeek');auto=_fn(m,'■セーブ／オートセーブ実行')
    exist=_fn(m,'AFL_GameSave_IsExistFile');load=_fn(m,'AFL_GameSave_Load');title=_fn(m,'■選択ダイアログ／タイトル設定')
    sig=lambda f:([v['type'] for v in f['arguments']],f['return-type'])
    for new,old in [('KR_T8AutoSaveDay',dow),('KR_T8AutoSaveSlot',dow),('KR_T8NewestAutoSlot',dow),('KR_T8SlotTitle',title)]:
        assert sig(dm['functions'][ids[new]])==sig(m['functions'][old]),(new,sig(dm['functions'][ids[new]]),sig(m['functions'][old]))
    v=live(day);ops=v['ops'];at={ad:k for k,(ad,_) in enumerate(ops)};sites=[];calls=[]
    for k,(ad,op) in enumerate(ops):
        if op!=f'CALLFUNC 0x{dow:x}':continue
        calls.append(ad)
        if [o for _,o in ops[k+1:k+3]]==['PUSH 0x1','EQUALE'] and ops[k+3][1].startswith('IFNZ ') and ops[k+4][1].startswith('JUMP '):
            j=at[int(ops[k+3][1].split()[1],16)]
            if [o for _,o in ops[j:j+3]]==['PUSH 0x3e7',f'CALLFUNC 0x{auto:x}','POP'] and ops[j+3][0]==int(ops[k+4][1].split()[1],16):sites.append((ad,ops[j][0],ops[j+1][0]))
    assert len(calls)==2 and len(sites)==1 and sites[0][0]==calls[0],(calls,sites)
    site,slot,save_call=sites[0]
    edit(day,site,struct.pack('<Hi',0x30,dow),struct.pack('<Hi',0x30,ids['KR_T8AutoSaveDay']),'day-start autosave every morning (was Mondays only)')
    edit(day,slot,struct.pack('<Hi',0,999),struct.pack('<Hi',0x30,ids['KR_T8AutoSaveSlot']),'day-start autosave slot: Monday -> weekly slot 49, other days -> 999')
    isl=_fn(m,'C_SceneSaveLoad@IsExecLoad');tv=[ad for ad,op in live(isl)['ops'] if op==f'CALLFUNC 0x{title:x}'];assert len(tv)==1,tv
    edit(isl,tv[0],struct.pack('<Hi',0x30,title),struct.pack('<Hi',0x30,ids['KR_T8SlotTitle']),'load confirm title names the daily/weekly autosave')
    go=_fn(m,'C_SceneGame@ExecGameOver');gops=live(go)['ops'];gs=[]
    for k,(ad,op) in enumerate(gops):
        if op=='PUSH 0x3e7':
            assert gops[k+1][1] in (f'CALLFUNC 0x{exist:x}',f'CALLFUNC 0x{load:x}'),gops[k+1];gs.append((ad,gops[k+1][1]))
    assert [x[1] for x in gs]==[f'CALLFUNC 0x{exist:x}',f'CALLFUNC 0x{load:x}'],gs
    for ad,_ in gs:edit(go,ad,struct.pack('<Hi',0,999),struct.pack('<Hi',0x30,ids['KR_T8NewestAutoSlot']),'game-over resume: the newer of the daily/weekly autosave')
    AUTOSAVE_INFO.update(function='呼出／１日の始まり',fid=day,site_offset=site-v['start'],slot_offset=slot-v['start'],autosave_call_offset=save_call-v['start'],
                         autosave_return_offset=save_call+6-v['start'],kept_day_of_week_call_offset=calls[1]-v['start'],
                         daily_slot=999,weekly_slot=WEEKLY_SLOT,is_exec_load=dict(fid=isl,site=tv[0]),game_over=dict(fid=go,sites=[ad for ad,_ in gs]),
                         schedule='Monday morning -> weekly slot 49; other mornings, dungeon rest cells, before an ending -> 999',
                         labels={'999':'일간',str(WEEKLY_SLOT):'주간'},original='GetDayOfWeek()==1 (Monday; 0 = Sunday in C_GameDate@GetDateString) -> 999',
                         saved_stack='C_SceneGame@Run > 呼出／１日の始まり > ■セーブ／オートセーブ実行 > C_SceneSaveLoad@RunAutoSave > ExecSave > Save (all original)')
    return AUTOSAVE_INFO

UPDATE_LOCK_OLD='\t.LOCALREF saveNo\n\tPUSH 999\n\tNOTE\n'
UPDATE_LOCK_NEW='\t.LOCALREF saveNo\n\tCALLFUNC KR_T8IsManualSlot\n'
NEWEST_OLD='\t.LOCALREF chkDataNo\n\tCALLFUNC AFL_GameSave_IsExistFile\n'
NEWEST_NEW='\t.LOCALREF chkDataNo\n\t.LOCALREF bAuto\n\tCALLFUNC KR_T8NewestExists\n'
ALIAS_PREFIX='\tPUSHLOCALPAGE\n\tPUSH 0\n\t.LOCALREF saveNo\n\tCALLFUNC KR_T8AutoAlias\n\tX_ASSIGN 1\n\tPOP\n'
def autosave_relocations(m,src):
    """Save/load screen functions (never on a saved stack: they return before AFL_GameSave_Save): relocated bodies."""
    out=[]
    def orig(fid):
        name=b.symbol(m,fid);path=O/f'original_{fid}.jam';b.cmd('ain','dump','--function',name,'-o',path,src);return name,b.clean(path.read_text('utf8'),name)
    # label: 999 -> 일간, 49 -> 주간, others %02d
    fid=_fn(m,'C_SaveLoadViewCell@GetDispSaveNo');name,body=orig(fid)
    assert [v['name'] for v in m['functions'][fid]['arguments']]==['saveNo'] and m['functions'][fid]['return-type'][0]==12 and body.count('PUSH 999')==1
    out.append((fid,f'FUNC {fid}\n'+lr('saveNo')+cf('KR_T8DispSaveNo')+'\tRETURN\nENDFUNC '+name+'\n'))
    # the weekly slot's label uses the same text font as 999 (CASFont 259, 28)
    fid=_fn(m,'C_SaveLoadViewCell@GetSaveNoFont');name,body=orig(fid)
    assert [v['name'] for v in m['functions'][fid]['arguments']]==['saveNo'] and body.count('PUSH 999')==1
    out.append((fid,begin(body,ALIAS_PREFIX)))
    # the save comment (the stats the load screen shows) comes from cell 0 for 999; the weekly slot does the same
    fid=_fn(m,'C_SceneSaveLoadView@GetSaveComment');name,body=orig(fid)
    assert [v['name'] for v in m['functions'][fid]['arguments']][:1]==['saveNo'] and 'PUSH 29581' in body
    out.append((fid,begin(body,ALIAS_PREFIX)))
    # save screen: the weekly slot is dimmed, not clickable and has no hover handlers, like 999
    fid=_fn(m,'C_SceneSaveLoadView@Update');name,body=orig(fid)
    assert body.count(UPDATE_LOCK_OLD)==3 and body.count('PUSH 999')==3,body.count(UPDATE_LOCK_OLD)
    out.append((fid,body.replace(UPDATE_LOCK_OLD,UPDATE_LOCK_NEW)))
    # newest-manual-save search (save/load screen opening page, 「New」 marker) skips the weekly slot like 999
    fid=_fn(m,'N_SaveLoad::GetNewDataNo');name,body=orig(fid)
    assert body.count(NEWEST_OLD)==1,body.count(NEWEST_OLD)
    out.append((fid,body.replace(NEWEST_OLD,NEWEST_NEW)))
    AUTOSAVE_INFO.update(relocated={b.raw_symbol(m,f):d for f,d in zip([x for x,_ in out],['redirect to KR_T8DispSaveNo','prepend saveNo = KR_T8AutoAlias(saveNo)','prepend saveNo = KR_T8AutoAlias(saveNo)',
                         '3x (saveNo != 999) -> KR_T8IsManualSlot(saveNo) in the save-mode branch','IsExistFile(chkDataNo) -> KR_T8NewestExists(chkDataNo, bAuto)'])})
    return out

# ---- r9 (Claude Opus 5.5, 2026-09-24): per-character missing events (categories and date windows from the catalog) ----
MISSING_INFO={}
def _cond_text(parts):
    return ' ' + ' · '.join(parts) if parts else ''
def _window(frm,to):
    if frm and to and frm==to:return f'{frm[0]}/{frm[1]}'
    if frm and to:return f'{frm[0]}/{frm[1]}～{to[0]}/{to[1]}'
    if frm:return f'{frm[0]}/{frm[1]}부터'
    if to:return f'{to[0]}/{to[1]}까지'
    return '날짜 무관'
def _parse_priority(expr):
    out={}
    z=re.search(r'IsTodayOrAfter\((\d+), (\d+)\)',expr);out['from']=(int(z[1]),int(z[2])) if z else None
    z=re.search(r'IsTodayOrBefore\((\d+), (\d+)\)',expr);out['to']=(int(z[1]),int(z[2])) if z else None
    z=re.search(r'IsDay\((\d+), (\d+)\)',expr)
    if z:out['from']=out['to']=(int(z[1]),int(z[2]))
    z=re.search(r'GetFeeling\(\) >= (\d+)',expr);out['feeling']=int(z[1]) if z else None
    own=set(re.findall(r'!\(LEventFlag::GetOnce\("(E\d+)"\)\)',expr))
    out['after']=[x for x in re.findall(r'LEventFlag::GetOnce\("(E\d+)"\)',expr) if x not in own]
    out['turning']='IsTurning' in expr
    return out
def char_missing_jaf(jaf):
    cat=a.readj(CATALOG);events=cat['events']
    names=dict(CHARS);counts='';dated='';dcounts='';rows=[]
    for p,name in CHARS:
        evs=[e for e in events if any(t.get('person')==p or t.get('person2')==p for t in e['triggers'])]
        groups=collections.defaultdict(list);personal=[]
        for e in evs:
            pools=[t for t in e['triggers'] if t['kind']=='pool' and (t.get('person')==p or t.get('person2')==p)]
            pri=[t for t in e['triggers'] if t['kind']=='after_training_priority' and t.get('person')==p]
            inv=[t for t in e['triggers'] if t['kind']=='invitation' and t.get('person')==p]
            if pools:
                t=pools[0];k=t['pool_kind']
                if k=='after_training':assert 4<=t['month']<=11,e['key'];groups[100+t['month']].append(e['fn'])
                elif k=='after_training_turned':groups[200].append(e['fn'])
                elif k=='training_invite':groups[201].append(e['fn'])
                elif k=='dungeon_first':groups[203].append(e['fn'])
                elif k=='dungeon_walk':
                    other=t['person2'] if t['person']==p else t['person'];groups[300+(other or 0)].append(e['fn'])
                else:raise AssertionError((e['key'],k))
            elif pri:personal.append((e,_parse_priority(pri[0]['condition_expr'])))
            elif inv:groups[202].append(e['fn'])
            else:raise AssertionError(('uncategorised',e['key']))
        story=[(e,t) for e in events for t in e['triggers'] if t['kind']=='conditional' and t['raw_args'][5]==p]
        assert sum(len(v) for v in groups.values())+len(personal)==len(evs),(p,len(evs))
        for c,fns in sorted(groups.items()):
            counts+=f'    if (p == {p} && cat == {c}) {{\n'+''.join(f'        if (!KR_T8Seen({quote(fn)})) n++;\n' for fn in fns)+'        return n;\n    }\n'
        lines=[];dc_personal='';dc_story=''
        for e,c in sorted(personal,key=lambda x:(x[1]['from'] or (0,0),x[1]['to'] or (99,0))):
            parts=([f"친밀도 {c['feeling']} 이상"] if c['feeling'] else [])+(['반한 상태'] if c['turning'] else [])+(['앞 이벤트 뒤'] if c['after'] else [])
            text='\n개인 '+_window(c['from'],c['to'])+_cond_text(parts)
            passed=f" + KR_T8Passed({c['to'][0]}, {c['to'][1]})" if c['to'] else ''
            lines.append(f'        if (!KR_T8Seen({quote(e["fn"])})) t = t + {quote(text)}{passed};\n')
            dc_personal+=f'        if (!KR_T8Seen({quote(e["fn"])})) n++;\n'
            MISSING_INFO.setdefault('dated',[]).append(dict(person=p,key=e['key'],kind='personal',text=text.strip(),to=c['to']))
        for e,t in sorted(story,key=lambda x:(tuple(x[1]['date_from']),x[0]['key'])):
            aff=t['affection'];parts=([f"친밀도 {aff['min']} 이상"] if aff and aff.get('min') is not None and aff['min']>=0 else [])+(['앞 이벤트 뒤'] if t['requires_events'] else [])
            text='\n본편 '+_window(tuple(t['date_from']),tuple(t['date_to']))+_cond_text(parts)
            lines.append(f'        if (!KR_T8Seen({quote(e["fn"])})) t = t + {quote(text)} + KR_T8Passed({t["date_to"][0]}, {t["date_to"][1]});\n')
            dc_story+=f'        if (!KR_T8Seen({quote(e["fn"])})) n++;\n'
            MISSING_INFO.setdefault('dated',[]).append(dict(person=p,key=e['key'],kind='story',text=text.strip(),to=t['date_to']))
        if lines:dated+=f'    if (p == {p}) {{\n'+''.join(lines)+'    }\n'
        if dc_personal:dcounts+=f'    if (p == {p} && !story) {{\n'+dc_personal+'    }\n'
        if dc_story:dcounts+=f'    if (p == {p} && story) {{\n'+dc_story+'    }\n'
        rows.append(dict(person=p,name=name,total=len(evs),categories={str(k):len(v) for k,v in sorted(groups.items())},personal=len(personal),story=len(story)))
    MISSING_INFO.update(rows=rows,basis='same attribution as the per-character rate (triggers naming the person); story = conditional events whose feeling person is the character (not in the rate)')
    names_js=' '.join(f'if (p == {p}) return {quote(n)};' for p,n in CHARS)
    out=jaf.replace('/*CHAR_NAMES*/',names_js).replace('/*MISS_COUNTS*/',counts).replace('/*DATED_LINES*/',dated).replace('/*DATED_COUNTS*/',dcounts)
    return out

def main():
    O.mkdir(exist_ok=True);ptr=a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);src=BASE_AIN
    prev=a.readj(INSTALLED);assert prev['status']=='COMMITTED' and all(h(rt/n)==x for n,x in prev['after'].items()),'runtime is not the r7 Claude install'
    assert h(src)==EXPECTED==h(BASE/'NightRemaster.ain') and h(Path(ptr['manifest']))==ptr['manifest_sha256']
    p.exact_tree(rt,a.readj(Path(ptr['manifest']))['files'])
    save('source_pointer.json',ptr);save('save_hashes_before_build.json',p.snapshot_saves());shutil.copy2(src,O/'baseline_NightRemaster.ain')
    proxy_map=a.readj(a.PROXY);alphabet_valid=''.join(x['unicode_character'] for x in proxy_map['mapping'] if '가'<=x['unicode_character']<='힣')+' '
    m=b.read_meta(BASE/'candidate_meta.json');byname={f['name']:f['index'] for f in m['functions']}
    versions=q.versions(BASE/'native_raw_code.jam')
    def live(fid):
        start=m['functions'][fid]['address'];return next(v for v in versions[fid] if v['start']==start)
    use_terms()
    assert h(BASE_EX)==BASE_EX_SHA,'EX base moved';kr_d,kr=ex_strings(BASE_EX);_,jp=ex_strings(JP_EX)
    msgs=[b.decode(x) for x in b.raw_messages(src.read_bytes())[3]];tmap=a.readj(TMAP)
    drows=dungeon_rows(kr,jp);disp=display_rows(kr)
    hit=homura_pages(msgs,tmap);mrows,mstatic,mdynamic=message_rows(msgs,hit)
    spans,read_total,groups=event_ranges(m,versions)
    cg,scenes=gallery(kr_d);save('gallery_cg.json',cg);save('gallery_scenes.json',scenes)
    assert len(cg['cells'])==60 and sum(len(c['cg_names']) for c in cg['cells'])==90 and scenes['entries']==76 and len(scenes['reg_numbers'])==66,(len(cg['cells']),scenes['entries'])
    assert scenes['ending_reg']=={'10523':12,'20523':24,'30523':34,'40523':44,'999':64},scenes['ending_reg']
    # Alphabet check: every preset and every generated literal must exist in the proxy font map.
    proxy=a.readj(a.PROXY);alphabet={x['unicode_character'] for x in proxy['mapping']}
    for t in TERMS8:
        for s in t[1]:assert all(c in alphabet or c==' ' for c in s) and b.width(s)<=t[2],(s,t)
    auto_src=(HERE/'claude_autosave_20260924.jaf').read_text('utf8')+(HERE/'claude_char_missing_20260924.jaf').read_text('utf8')+'반한 상태 앞 이벤트 뒤 친밀도 이상 개인 본편 부터 까지 날짜 무관 혼자 첫 동행 지난 달에 놓친 대화'
    assert all(c in alphabet for c in auto_src if '가'<=c<='힣'),[c for c in auto_src if '가'<=c<='힣' and c not in alphabet]
    jaf='\n'.join((HERE/n).read_text('utf8') for n in ['claude_term_rate_20260924_r9.jaf','claude_colors_20260924_r6.jaf','claude_home_trap_20260924_r7.jaf','claude_autosave_20260924.jaf','claude_char_missing_20260924.jaf'])
    jaf=jaf.replace('/*DEFAULTS*/',' '.join(f'if (i == {i}) return {quote(t[0])};' for i,t in enumerate(TERMS8)))
    jaf=jaf.replace('/*LABELS*/',' '.join(f'if (i == {i}) return {quote(t)};' for i,t in enumerate(LABELS8)))
    jaf=jaf.replace('/*CAPS*/',' '.join(f'if (i == {i}) return {t[2]};' for i,t in enumerate(TERMS8)))
    jaf=jaf.replace('/*PRESETS*/',' '.join(f'if (i == {i} && n == {j}) return {quote(s)};' for i,t in enumerate(TERMS8) for j,s in enumerate(t[1])))
    homura=[r for r in drows if r['tokens'][0]==('t',7)];hazama=[r for r in drows if r['tokens'][1]==('t',3)]
    dungeon='if (text.Find("라이코 동굴") >= 0) {\n'+''.join(f'if (text == {quote(r["source"])}) return {b.expr(r["tokens"])};\n' for r in homura)+'}\n'
    dungeon+='if (text.Find("틈 ") >= 0) {\n'+''.join(f'if (text == {quote(r["source"])}) return {b.expr(r["tokens"])};\n' for r in hazama)+'}\n'
    jaf=jaf.replace('/*DUNGEON*/',dungeon)
    jaf=jaf.replace('/*DISPLAY_ROWS*/',''.join(f'if (text == {quote(r["source"])}) return {b.expr(r["tokens"])};\n' for r in disp))
    jaf=jaf.replace('/*MESSAGE_ROWS*/',''.join(f'if (id == {i} && text == {quote(msgs[i])}) return {e};\n' for i,e in sorted(mrows.items())))
    groups_old=sorted(int(z[1]) for f in m['functions'] if (z:=re.fullmatch(r'KR_TermMsg(\d+)',f['name'])))
    jaf=jaf.replace('/*OLD_DISPATCH*/',''.join(f'if (id >= {g*1000} && id < {(g+1)*1000}) return KR_TermMsg{g}(id, text);\n' for g in groups_old))
    chunks=[spans[i:i+120] for i in range(0,len(spans),120)]
    reads=''.join(f'int KR_T8Read{c}() {{\n    int n = 0;\n'+''.join(f'    n += KR_T8ReadRange({s}, {t});\n' for s,t in part)+'    return n;\n}\n' for c,part in enumerate(chunks))
    reads+='int KR_T8ReadCount() { return '+' + '.join(f'KR_T8Read{c}()' for c in range(len(chunks)))+'; }\n'
    jaf=jaf.replace('/*READ_FUNCS*/',reads)
    jaf=jaf.replace('/*CG_CELLS*/',''.join('    if ('+' || '.join(f'Ａ＿ＣＧモード確認({quote(n)})' for n in cell['cg_names'])+') n++;\n' for cell in cg['cells']))
    jaf=jaf.replace('/*SCENES*/',''.join(f'    if (Ａ＿回想確認({num})) n++;\n' for num in scenes['reg_numbers']))
    ending=''
    for pos,(ev,name) in enumerate(ENDINGS):
        reg=scenes['ending_reg'][str(ev)];sep='' if pos==0 else ' · '
        ending+=f'    if (Ａ＿回想確認({reg})) {{ n++; names = names + {quote(sep+name)}; }} else {{ names = names + {quote(sep+"???")}; }}\n'
    jaf=jaf.replace('/*ENDINGS*/',ending).replace('/*ENDING_TOTAL*/',str(len(ENDINGS)))
    jaf=jaf.replace('/*ENDING_COUNT*/',''.join(f'    if (Ａ＿回想確認({scenes["ending_reg"][str(ev)]})) n++;\n' for ev,_ in ENDINGS))
    jaf=char_jaf(jaf,m,src)
    jaf=char_missing_jaf(jaf)
    ev_total=sum(groups.values())
    for k,v in {'EV_TOTAL':ev_total,'EV_STORY':groups['0'],'EV_TRAINING':groups['1'],'EV_INVITE':groups['2'],'EV_WALK':groups['3'],
                'READ_TOTAL':read_total,'CG_TOTAL':len(cg['cells']),'SCENE_TOTAL':len(scenes['reg_numbers'])}.items():
        jaf=jaf.replace(f'/*{k}*/',str(v))
    jaf=jaf.replace('@@ALPHABET@@',alphabet_valid)
    assert '/*' not in jaf.replace('// ','') and '@@' not in jaf
    (O/'helpers_readable.jaf').write_text(jaf,'utf8')
    jaf=re.sub(r'"(?:[^"\\]|\\.)*"',lambda z:json.dumps(b.encode(json.loads(z[0])).decode('cp932'),ensure_ascii=False) if any('\uac00'<=c<='\ud7a3' or c in '·…「」【】　' for c in json.loads(z[0])) else z[0],jaf)
    (O/'helpers.jaf').write_text(jaf,'utf8');decl=O/'declared.ain';b.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,src)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json');added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[]
    for f in added:
        path=O/f"jaf_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl)
        if f['name']=='KR_T8TrapCell':patch.append(trap_cell_body(f['index']));continue
        patch.append(b.clean(b.native_lower(path.read_text('utf8')),f['name']))
    def args(fid):return [v['name'] for v in m['functions'][fid]['arguments']]
    def redirect(name,target,refs=()):
        fid=byname[name];body=f'FUNC {fid}\n'
        for n in args(fid):body+=lr(n)+('\tA_REF\n' if n in refs else '')
        return fid,body+cf(target)+'\tRETURN\nENDFUNC '+name+'\n'
    relocated=[]
    for name,target,refs in [('KR_TermDefault','KR_T8Default',()),('KR_TermPreset','KR_T8Preset',()),('KR_TermCap','KR_T8Cap',()),
                             ('KR_TermMessage','KR_T8Message',('text',)),('KR_TermDisplay','KR_T8Display',('text',)),
                             ('KR_TermReadSafe','KR_T8ReadSafe',('path',)),('KR_TermSaveSafe','KR_T8SaveSafe',()),
                             ('KR_PlayerInfoMenu','KR_T8PlayerInfoMenu',())]:
        fid,body=redirect(name,target,refs);patch.append(body);relocated.append(fid)
    getters=[26902,26671,26672]
    for fid in getters:
        name=b.symbol(m,fid);path=O/f'original_{fid}.jam';b.cmd('ain','dump','--function',name,'-o',path,src);body=b.clean(path.read_text('utf8'),name)
        assert m['functions'][fid]['return-type'][0]==12 and 'KR_TermDisplay' not in body,name
        patch.append(body.replace('\tRETURN\n',cf('KR_TermDisplay')+'\tRETURN\n'));relocated.append(fid)
    # r4: homebase panel follows the top menu; the mods-tab checkbox joins Codex's config sync (both prepended).
    for fid,code in [(28571,cf('KR_T8HomeEnter')),(28572,cf('KR_T8HomeLeave')),
                     (29817,checkbox_sync(29827,ids['KR_T8HomeRateGet'])),(29818,checkbox_sync(29828,ids['KR_T8HomeRateSet'])),
                     (byname['KR_ChestShow'],reassign('text','KR_T8ChestColor')),(byname['KR_NoticeShow'],reassign('text','KR_T8ReceiptColor')),
                     (byname['KR_SweepReport'],reassign('txt','KR_T8SweepColor')),
                     (27194,lr('txt')+'\tA_REF\n'+cf('KR_T8SweepChest')),(byname['KR_SweepPay'],cf('KR_T8SweepLostReset'))]:
        name=b.symbol(m,fid);path=O/f'original_{fid}.jam';b.cmd('ain','dump','--function',name,'-o',path,src);body=b.clean(path.read_text('utf8'),name)
        assert 'KR_HomeRate' not in body and 'KR_T8Home' not in body,name
        patch.append(begin(body,code));relocated.append(fid)
    # r5: C_MessageDialog@Create switches tag processing on (ITextParts Tag::set) before Text::set, only for tagged text.
    assert b.raw_symbol(m,27194)=='L_TreasureBox::ShowGetDialog' and [v['name'] for v in m['functions'][27194]['arguments']]==['txt']
    SWEEP_LOST.update(recorder='L_TreasureBox::ShowGetDialog (prepended KR_T8SweepChest(txt); records only while KR_SweepActive)',
                      reset='KR_SweepPay (prepended KR_T8SweepLostReset)',report='KR_T8SweepColor: KR_SweepItems fixed line replaced by the lost list')
    cr=27778;assert b.raw_symbol(m,cr)=='C_MessageDialog@Create';name=b.symbol(m,cr);path=O/f'original_{cr}.jam'
    b.cmd('ain','dump','--function',name,'-o',path,src);body=b.clean(path.read_text('utf8'),name)
    assert body.count(TEXT_SET)==1 and 'kr_t8_msgdlg' not in body,body.count(TEXT_SET)
    patch.append(body.replace(TEXT_SET,TAG_ON+TEXT_SET));relocated.append(cr)
    COLOR_INFO.update(prepended={'KR_ChestShow':'KR_T8ChestColor','KR_NoticeShow':'KR_T8ReceiptColor','KR_SweepReport':'KR_T8SweepColor'},
                      message_dialog='C_MessageDialog@Create: Tag::set(true) (vtable slot 25) before Text::set when the text contains ${font')
    # r8: save/load screen functions for the daily/weekly autosave slots (relocated; none is ever on a saved stack)
    for fid,body in autosave_relocations(m,src):patch.append(body);relocated.append(fid)
    (O/'patch.jam').write_text('\n'.join(patch),'utf8');out=O/'NightRemaster.ain';b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    old=b.unpack(src.read_bytes());raw=bytearray(b.unpack(out.read_bytes()));oldn=struct.unpack_from('<I',old,12)[0];newn=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+newn,m['functions'][0]['address']);assert raw[16:16+oldn]==old[16:16+oldn]
    # Same-length operand edits inside unchanged functions: addresses never move.
    sites=[]
    def edit(fid,addr,before,after,why):
        cur=bytes(raw[16+addr:16+addr+6]);assert cur==before==old[16+addr:16+addr+6],(fid,hex(addr),cur.hex(),before.hex())
        raw[16+addr:16+addr+6]=after;sites.append(dict(fid=fid,name=b.symbol(m,fid),address=addr,before=before.hex(),after=after.hex(),why=why))
    def op_bytes(addr):return bytes(old[16+addr:16+addr+6])
    resolve=byname['KR_ResolveJosa'];assert [v['type'] for v in m['functions'][resolve]['arguments']]==[v['type'] for v in dm['functions'][ids['KR_T8BattleText']]['arguments']]
    assert m['functions'][resolve]['return-type']==dm['functions'][ids['KR_T8BattleText']]['return-type']
    v=live(29214);hitc=[(ad,op) for ad,op in v['ops'] if op==f'CALLFUNC 0x{resolve:x}'];assert len(hitc)==1,hitc
    edit(29214,hitc[0][0],struct.pack('<Hi',0x30,resolve),struct.pack('<Hi',0x30,ids['KR_T8BattleText']),'battle message Printf: term display before particle resolution')
    st=b.strings(old)[2];fmt=[i for i,s in enumerate(st) if b.decode(s)=='%s{YORU_KR_JOSA:n} 히카리의 기척을 감지했다'];assert len(fmt)==1,fmt
    v=live(27141);hits=[(ad,op) for ad,op in v['ops'] if op==f'S_PUSH 0x{fmt[0]:x}'];assert len(hits)==1,hits
    spush=struct.unpack_from('<H',old,16+hits[0][0])[0];assert op_bytes(hits[0][0])==struct.pack('<Hi',spush,fmt[0])
    edit(27141,hits[0][0],struct.pack('<Hi',spush,fmt[0]),struct.pack('<Hi',0x30,ids['KR_T8SenseFormat']),'sense dialog format built with the chosen term')
    want={byname['KR_TermMenu']:['LT','LT','LTE'],byname['KR_TermRefresh']:['LT'],byname['KR_TermLoad']:['LT'],byname['KR_TermValid']:['GTE','LT']}
    for fid,cmp in want.items():
        ops=live(fid)['ops'];found=[]
        for k,(ad,op) in enumerate(ops):
            # local <op> 7: PUSHLOCALPAGE, PUSH idx, X_REF 1, PUSH 7, compare
            if op=='PUSH 0x7' and k>2 and ops[k-3][1]=='PUSHLOCALPAGE' and ops[k-2][1].startswith('PUSH 0x') and ops[k-1][1]=='X_REF 0x1' and ops[k+1][1] in ['LT','LTE','GTE']:found.append((ad,ops[k+1][1]))
        assert [c for _,c in found]==cmp,(b.symbol(m,fid),found)
        for ad,c in found:edit(fid,ad,struct.pack('<Hi',0,7),struct.pack('<Hi',0,8),f'term count 7 -> 8 ({c})')
    # r2 CT-RATE-001: the menu's opening KR_TermLoad (first of three; the others restore after a failed save).
    load=byname['KR_TermLoad'];menu=byname['KR_TermMenu'];calls=[ad for ad,op in live(menu)['ops'] if op==f'CALLFUNC 0x{load:x}']
    assert len(calls)==3 and calls[0]<calls[1]<calls[2],calls
    edit(menu,calls[0],struct.pack('<Hi',0x30,load),struct.pack('<Hi',0x30,ids['KR_T8MenuLoad']),'term menu opening load reports v2 entries reset by the new default')
    # r2 CT-RATE-002: C_SelectDialog@CreateParts, titleBackHeight = titleHeight + (type 2026091602 ? 48 : 24).
    cp=27936;assert m['functions'][cp]['name']=='C_SelectDialog@CreateParts';ops=live(cp)['ops'];pads=[]
    for k in range(8,len(ops)-4):
        window=[o for _,o in ops[k-8:k+5]]
        if window==['PUSHLOCALPAGE','PUSH 0x10','PUSHLOCALPAGE','PUSH 0xf','X_REF 0x1','PUSHSTRUCTPAGE','PUSH 0x6d04','CALLMETHOD 0x0',f'PUSH 0x{2026091602:x}','EQUALE',ops[k+2][1],'PUSH 0x30',ops[k+4][1]] and ops[k+2][1].startswith('IFZ') and ops[k+4][1].startswith('JUMP'):
            pads.append(ops[k+3][0])
    assert len(pads)==1,pads
    assert dm['functions'][ids['KR_T8TitlePad']]['arguments']==[] and dm['functions'][ids['KR_T8TitlePad']]['return-type'][0]==10,dm['functions'][ids['KR_T8TitlePad']]['return-type']
    edit(cp,pads[0],struct.pack('<Hi',0,48),struct.pack('<Hi',0x30,ids['KR_T8TitlePad']),'select dialog type 2026091602 title padding from KR_T8TitlePad (48 unless an achievement page opted in)')
    # r3: the term menu names rows and the preset title by the Japanese word (both KR_TermDefault calls in the menu).
    default=byname['KR_TermDefault'];labels=[ad for ad,op in live(menu)['ops'] if op==f'CALLFUNC 0x{default:x}'];assert len(labels)==2,labels
    same=lambda x,y:[v['type'] for v in m['functions'][x]['arguments']]==[v['type'] for v in dm['functions'][y]['arguments']] and m['functions'][x]['return-type']==dm['functions'][y]['return-type']
    assert same(default,ids['KR_T8Label'])
    for ad in labels:edit(menu,ad,struct.pack('<Hi',0x30,default),struct.pack('<Hi',0x30,ids['KR_T8Label']),'term menu row/preset title shows the original Japanese word')
    # r3: the winmm IME hook delivers FNL proxy carriers; keep them instead of re-encoding as CP949 (name and term input).
    old_in=byname['KR_KoreanInputDialog'];assert same(old_in,ids['KR_T8InputDialog'])
    for fid in [byname['KR_PlayerRename'],menu]:
        calls=[ad for ad,op in live(fid)['ops'] if op==f'CALLFUNC 0x{old_in:x}'];assert len(calls)==1,(fid,calls)
        edit(fid,calls[0],struct.pack('<Hi',0x30,old_in),struct.pack('<Hi',0x30,ids['KR_T8InputDialog']),'text input keeps the hook-delivered proxy text; CP949 still converted')
    trap_edits(m,dm,ids,live,edit)
    autosave=autosave_edit(m,dm,ids,live,edit)
    out.write_bytes(b.pack(bytes(raw),src.read_bytes()[:8]));b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    for f,g in zip(m['functions'],nm['functions']):
        test=dict(f)
        if f['index'] in relocated:test['address']=g['address']
        assert test==g,f['index']
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    new=b.unpack(out.read_bytes());diff=[i for i in range(oldn) if old[16+i]!=new[16+i]]
    allowed=set(x for s in sites for x in range(s['address'],s['address']+6));assert set(diff)<=allowed,[hex(x) for x in diff if x not in allowed][:10]
    assert b.raw_messages(src.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(new)[2][:len(b.strings(old)[2])]==b.strings(old)[2]
    for fid in relocated+list(ids.values()):b.cmd('ain','dump','--function',b.symbol(nm,fid),'-o',O/f'built_{fid}.jam',out)
    for fid in set(s['fid'] for s in sites):b.cmd('ain','dump','--function',b.symbol(nm,fid),'-o',O/f'built_{fid}.jam',out)
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out);audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',audit);assert audit['all_active_opcodes_supported']
    pact=build_pacts()
    monsters=monster_names(rt)
    save('term_definitions.json',[dict(default=t[0],choices=t[1],max_width=t[2]) for t in TERMS8])
    save('display_terms.json',[dict(source=r['source'],tokens=r['tokens'],origin=r['origin']) for r in disp]);save('dungeon_terms.json',drows)
    save('homura_messages.json',dict(static=mstatic,dynamic=mdynamic));save('read_ranges.json',dict(ranges=spans,total=read_total))
    save('build_evidence.json',dict(status='CLAUDE_TERM_RATE_STAGED',author=AUTHOR,source_pointer=ptr,source_files={n:h(rt/n) for n in FILES},files={n:h(O/n) for n in FILES},
        added_functions=ids,relocated=sorted(relocated),same_length_sites=sites,terms=[t[0] for t in TERMS8],read_total=read_total,cg_cells=len(cg['cells']),
        scene_numbers=len(scenes['reg_numbers']),PACT=pact,home_panel=HOME_PANEL,trap_notice=TRAP_NOTICE,colors=COLOR_INFO,char_events=CHAR_INFO,sweep_lost=SWEEP_LOST,monster_names=monsters,autosave=autosave,char_missing=MISSING_INFO,endings=[n for _,n in ENDINGS],MSG1_exact=True,STR0_prefix_exact=True,serialized_schema_changes=0,translator_model=AUTHOR))
    print('STAGED',O,h(out))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
