"""Claude Opus 5.5 (2026-09-24): eight-term preferences, missing term display paths, achievement page.

Incremental over the installed runtime_repairs AIN. Display/UI only: MSG1, STR0 prefix, globals,
structures, save layout and every saved return frame stay exact. Existing helpers are redirected
in place (relocated) or edited with same-length operands; nothing in the translation changes.
"""
from pathlib import Path
import json,struct,re,copy,shutil,collections
import build_runtime_repairs_20260923 as previous
from build_dungeon_sweep_20260916 import lr,cf,push
R=previous.R;HERE=previous.HERE;b=previous.b;p=previous.p;q=previous.q;a=b.a
BASE=previous.O
O=R/'staging/claude_term_rate_20260924_r3'
EXPECTED='cfda0681fb0c55d2088aa7d08be4b00259d3cefd0be512d353cf69db831a6a3d'
# r2/r3 rebuild the whole overlay on the pre-Claude base kept by the first install; r3 installs over r2.
INSTALLED=R/'evidence/claude_term_rate_20260924_r2/journal.json'
PREV=R/'evidence/claude_term_rate_20260924'
BASE_AIN=PREV/'before/NightRemaster.ain';BASE_PACT=PREV/'before/NightRemasterPact.afa'
BASE_PACT_SHA='efc527e804c4ae1abfd2b50ceca5a1bfa1384cc91afdc399cc6567468736ae49'
FILES=['NightRemaster.ain','NightRemasterPact.afa']
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
    archive=rebuild(src,O/'NightRemasterPact.afa',{160:out})
    return dict(entry=160,name=entry.name,changes=changes,reverse_exact=True,archive=archive)

def main():
    O.mkdir(exist_ok=True);ptr=a.readj(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);src=BASE_AIN
    prev=a.readj(INSTALLED);assert prev['status']=='COMMITTED' and all(h(rt/n)==x for n,x in prev['after'].items()),'runtime is not the r2 Claude install'
    assert h(src)==EXPECTED==h(BASE/'NightRemaster.ain') and h(Path(ptr['manifest']))==ptr['manifest_sha256']
    p.exact_tree(rt,a.readj(Path(ptr['manifest']))['files'])
    save('source_pointer.json',ptr);save('save_hashes_before_build.json',p.snapshot_saves());shutil.copy2(src,O/'baseline_NightRemaster.ain')
    proxy_map=a.readj(a.PROXY);alphabet_valid=''.join(x['unicode_character'] for x in proxy_map['mapping'] if '가'<=x['unicode_character']<='힣')+' '
    m=b.read_meta(BASE/'candidate_meta.json');byname={f['name']:f['index'] for f in m['functions']}
    versions=q.versions(BASE/'native_raw_code.jam')
    def live(fid):
        start=m['functions'][fid]['address'];return next(v for v in versions[fid] if v['start']==start)
    use_terms()
    kr_d,kr=ex_strings(rt/'NightRemasterEX.ex');_,jp=ex_strings(JP_EX)
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
    jaf=(HERE/'claude_term_rate_20260924.jaf').read_text('utf8')
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
        path=O/f"jaf_{f['index']}.jam";b.cmd('ain','dump','--function',f['name'],'-o',path,decl);patch.append(b.clean(b.native_lower(path.read_text('utf8')),f['name']))
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
    pact=widen_map_name(rt)
    save('term_definitions.json',[dict(default=t[0],choices=t[1],max_width=t[2]) for t in TERMS8])
    save('display_terms.json',[dict(source=r['source'],tokens=r['tokens'],origin=r['origin']) for r in disp]);save('dungeon_terms.json',drows)
    save('homura_messages.json',dict(static=mstatic,dynamic=mdynamic));save('read_ranges.json',dict(ranges=spans,total=read_total))
    save('build_evidence.json',dict(status='CLAUDE_TERM_RATE_STAGED',author=AUTHOR,source_pointer=ptr,source_files={n:h(rt/n) for n in FILES},files={n:h(O/n) for n in FILES},
        added_functions=ids,relocated=sorted(relocated),same_length_sites=sites,terms=[t[0] for t in TERMS8],read_total=read_total,cg_cells=len(cg['cells']),
        scene_numbers=len(scenes['reg_numbers']),PACT=pact,endings=[n for _,n in ENDINGS],MSG1_exact=True,STR0_prefix_exact=True,serialized_schema_changes=0,translator_model=AUTHOR))
    print('STAGED',O,h(out))
if __name__=='__main__':
    try:main()
    except AssertionError as ex:print('ASSERT',str(ex)[-3000:]);raise SystemExit(1)
