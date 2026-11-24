"""Append-only, hash-bound calendar UI build. Never writes the live runtime."""
from pathlib import Path
import sys,json,struct,re,textwrap
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922')
sys.path.insert(0,str(F/'ingame/r24_chart'));import r24lib as L
O=L.CODEX/'staging/calendar_portraits_20260929';W=O/'work/build'
W.mkdir(parents=True,exist_ok=True);L.TMP=O/'work/tmp';L.TMP.mkdir(exist_ok=True)
src=O/'source/NightRemaster.ain';out=O/'candidate/NightRemaster.ain'
assert L.sha(src)=='1af260f5adff8b79ccebf27a44401790dff1a7dce555d87985b8b090cbca99f6'
m=L.read_meta(O/'source/candidate_meta.json');fid=lambda n:L.fid_of(m,n)
roster=[
 ('료','주인공',100,'亮／通常'),('이즈미','이즈미',101,'いずみ／楽眼鏡'),
 ('쿄카','쿄카',201,'鏡花／楽'),('마나미','마나미',251,'真言美／楽'),
 ('마코토','마코토',301,'マコト／楽'),('신카이','신카이',351,'新開／楽'),
 ('호시카와','호시카와',401,'星川／楽'),('모모세','모모세',451,'百瀬／楽'),
 ('키라라','키라라',501,'キララ／楽'),('소지','소지',551,'ソウジ／楽'),
 ('미즈키','미즈키',601,'ミズキ／楽'),('하이지','하이지',754,'ハイジ／楽'),
 ('사카키','사카키',801,'サカキ／喜'),('코우야','코우야',701,'コウヤ／楽'),
 ('코이치','코이치',651,'光一／楽'),('미사토','미사토',910,'鏡花の姉／通常')]
names={r[0]:i for i,r in enumerate(roster)}
catalog=L.readj(L.CODEX/'evidence/cg_visual_index.json')
assets=[x for group in catalog.values() if isinstance(group,list) for x in group]
portrait_assets=[]
for r in roster:
    found=[a for a in assets if a['name'].split('.')[0]==f'CG{r[2]:04d}']
    assert len(found)==1 and found[0]['size']==[240,300],(r,found)
    portrait_assets.append(found[0])
events=[]
for line in (F/'graph/lines_kr.jsonl').read_text('utf8').splitlines():
    r=json.loads(line); evidence={};others=[]
    for msg in r['seq']:
        if not msg.get('sp'):continue
        for sp in re.split(r'\s*[＆&·]\s*',msg['sp']):
            sp=sp.strip()
            if sp in names:evidence.setdefault(sp,[]).append(msg['m'])
            elif sp not in others:others.append(sp)
    mask=sum(1<<names[n] for n in evidence)
    events.append(dict(no=r['event'],mask=mask,cast=list(evidence),speaker_messages=evidence,other_speakers=others))
assert next(e for e in events if e['no']==11)['cast']==['료','이즈미','쿄카']
assert max(e['mask'].bit_count() for e in events)<=16
def q(s):return json.dumps(s,ensure_ascii=False)
def tree(ret,name,pairs,default):
    pairs=sorted(pairs);assert len({k for k,v in pairs})==len(pairs)
    lines=[f'{ret} {name}(int i) {{']
    def rec(a,b,p):
        if b-a<=6:
            lines.extend(f'{p}if (i == {k}) return {v};' for k,v in pairs[a:b]);return
        c=(a+b)//2;lines.append(f'{p}if (i < {pairs[c][0]}) {{');rec(a,c,p+'    ')
        lines.append(p+'} else {');rec(c,b,p+'    ');lines.append(p+'}')
    rec(0,len(pairs),'    ');lines.extend([f'    return {default};','}']);return '\n'.join(lines)
tables=[tree('int','KR_P29Mask',[(e['no'],e['mask']) for e in events if e['mask']],0),
 tree('string','KR_P29CG',[(i,q(a['name'])) for i,a in enumerate(portrait_assets)],'""'),
 tree('string','KR_P29Name',[(i,q(r[1])) for i,r in enumerate(roster)],'""'),
 tree('string','KR_P29Others',[(e['no'],q('\n'.join(textwrap.wrap(', '.join(e['other_speakers']),54)))) for e in events if e['other_speakers']],'""')]
story='이즈미의 고문서를 정리하며 법술에 필요한 재능에 관해 이야기를 나눈다.\n쿄카는 뛰어난 연기력을 지닌 마나미를 동료 후보로 추천한다.'
tables.append(tree('string','KR_P29Story',[(11,q(story))],'""'))
cells=L.readj(F/'ingame/r22_chart/work/build/cells.json')['rows']
assert [c['no'] for c in cells[:3]]==[121,1,2]
cells=cells[1:3]+cells[:1]+cells[3:]
forward={}
for field,ret,old,default in [('ref','int','KR_CCellRef',-1),('name','string','KR_CCellName','""'),('when','string','KR_CCellWhen','""'),('cond','string','KR_CCellCond','""')]:
    new='KR_P29'+old[4:];forward[old]=new
    tables.append(tree(ret,new,[(i,q(c[field]) if ret=='string' else c[field]) for i,c in enumerate(cells)],default))
def short(s):
    s=s.replace('\n',' ')
    if len(s)>16:s=s[:15]+'…'
    return s[:8]+ ('\n'+s[8:] if len(s)>8 else '')
tables.append(tree('string','KR_P29ShortCond',[(i,q(short(c['cond']))) for i,c in enumerate(cells) if c['cond']],'""'))
def function(text,name):
    start=re.search(r'^(?:void|int|string|bool) '+re.escape(name)+r'\(',text,re.M).start()
    opening=text.index('{',start);depth=1;end=opening+1
    while depth:
        depth+= (text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
r22=(F/'ingame/r22_chart/claude_chart_r22.jaf').read_text('utf8')
r24=(F/'ingame/r24_chart/claude_chart_r24.jaf').read_text('utf8')
cell=function(r24,'KR_C24DrawCell').replace('KR_C24DrawCell','KR_P29DrawCell',1)
cell=cell.replace('    int box =','    KR_P29DropMinis(s);\n    int box =',1)
cell=cell.replace('        return;\n    }\n    KR_CText(nm', '        KR_P29DrawMinis(s, no, true);\n        return;\n    }\n    KR_CText(nm')
cell=cell.replace('    if (cond != "") KR_CText(cd, box, 10.0, 76.0, 15, KR_CTint(cond, KR_CGray()), 2);',
    '    if (KR_P29Read(no) && KR_P29Count(no) > 0) cond = KR_P29ShortCond(i);\n    if (cond != "") KR_CText(cd, box, 10.0, 76.0, 15, KR_CTint(cond, KR_CGray()), 2);\n    KR_P29DrawMinis(s, no, false);')
assert cell.count('KR_P29DrawMinis')==2
card=function(r22,'KR_CCardPage').replace('KR_CCardPage','KR_P29CardPage',1)
card=card.replace('{','''{
    if (KR_CActive()) {
        while (true) {
            if (KR_T9Unwinding()) return;
            int no = KR_T9CardEntry(k);
            int r = KR_P29Run(no, KR_T19CardHead(k), KR_T9CardSize(k), KR_CCanPlay(no));
            if (r == 13) { KR_CRequest(no); return; }
            if (r == 14) KR_T9StagePage(k, m);
            else return;
        }
        return;
    }
''',1)
event=function(r22,'KR_CEventPage').replace('KR_CEventPage','KR_P29EventPage',1)
event=event.replace('{','''{
    if (KR_CActive()) {
        if (KR_T9Unwinding()) return;
        int r = KR_P29Run(no, KR_T19EvHead(no), 1, KR_CCanPlay(no));
        if (r == 13) KR_CRequest(no);
        return;
    }
''',1)
jaf='\n'.join(tables)+'\n'+(HERE/'calendar_portraits_20260929.jaf').read_text('utf8')+'\n'+cell+'\n'+card+'\n'+event
forward.update({'KR_C24DrawCell':'KR_P29DrawCell','KR_CClear':'KR_P29Clear','KR_CCardPage':'KR_P29CardPage','KR_CEventPage':'KR_P29EventPage','KR_CPlayNote':'KR_P29PlayNote'})
(W/'helpers_readable.jaf').write_text(jaf,'utf8');(W/'helpers.jaf').write_text(L.jaf_literal_encode(L.strip_comments(jaf)),'utf8')
decl=W/'declared.ain';L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl);dm=L.read_meta(W/'declared_meta.json')
added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added};patch=[]
for f in added:
    n=f['name'];i=f['index']
    if n=='KR_P29WaitRaw':
        body=f'FUNC {i}\n PUSH -1\n PUSH {ids["KR_P29Frame"]}\n DG_NEW_FROM_METHOD\n PUSH 1\n CALLFUNC AFL_Parts_WaitForClick\n RETURN\nENDFUNC {n}\n'
    else:
        p=W/(n+'.jam');L.cmd('ain','dump','--function',n,'-o',p,decl)
        jam=p.read_text('utf8')
        jam=re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',lambda z:'\t.LOCALASSIGN '+z[1]+' '+str(struct.unpack('<i',struct.pack('<f',float(z[2])))[0]),jam)
        body=L.clean(L.native_lower(jam).replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),n)
    patch.append(body)
for old,new in forward.items():
    f=m['functions'][fid(old)];g=dm['functions'][ids[new]]
    assert f['return-type']==g['return-type']
    assert [a['type'] for a in f['arguments']]==[a['type'] for a in g['arguments']],old
    args=''.join(f"\t.LOCALREF {a['name']}\n"+('\tA_REF\n' if a['type'][0]==12 else '') for a in f['arguments'])
    patch.append(f"FUNC {fid(old)}\n{args}\tCALLFUNC {new}\n\tRETURN\nENDFUNC {old}\n")
(W/'patch.jam').write_text('\n'.join(patch),'utf8');L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
old=L.unpack(src.read_bytes());raw=bytearray(L.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address'])
a,b,ss=L.strings(raw);name=L.encode('이벤트 플로우 차트');newname=L.encode('이벤트 캘린더')
renamed=[i for i,s in enumerate(ss) if name in s];assert renamed
newss=[s.replace(name,newname) for s in ss]
raw[a:b]=b'STR0'+struct.pack('<I',len(ss))+b''.join(s+b'\0' for s in newss)
out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out);nm=L.read_meta(W/'candidate_meta.json')
assert [i for i,(a,b) in enumerate(zip(m['functions'],nm['functions'])) if a!=b]==sorted(fid(n) for n in forward)
for k in m:
    if k!='functions':assert m[k]==nm[k],k
oldn=struct.unpack_from('<I',old,12)[0];assert raw[16:16+oldn]==old[16:16+oldn]
assert L.strings(raw)[2][:len(L.strings(old)[2])]==[s.replace(name,newname) for s in L.strings(old)[2]]
assert L.raw_messages(out.read_bytes())[3]==L.raw_messages(src.read_bytes())[3]
assert not set(forward)&set(L.PINNED_ALL)
L.cmd('ain','dump','--raw-code','--no-macros','-o',W/'candidate_raw_code.jam',out)
rt=Path(L.readj(O/'source_pointer.json')['runtime']);audit=L.audit(out,W/'candidate_meta.json',W/'candidate_raw_code.jam',rt/'NightRemaster.exe')
assert audit['all_active_opcodes_supported'];L.writej(W/'native_opcode_audit.json',audit)
dll=(O/'source/winmm.dll').read_bytes();needle='이벤트 플로우 차트(&E)\0'.encode('utf-16-le');replacement='이벤트 캘린더(&E)\0'.encode('utf-16-le')
assert dll.count(needle)==1;offset=dll.index(needle);replacement=replacement.ljust(len(needle),b'\0')
(O/'candidate/winmm.dll').write_bytes(dll[:offset]+replacement+dll[offset+len(needle):])
L.writej(O/'design/cast_evidence.json',dict(translator_model='Codex internal',source_sha256=L.sha(F/'graph/lines_kr.jsonl'),method='explicit speaker tags only; no narrative name matching; composite speaker tags split',roster=roster,portrait_assets=portrait_assets,events=events,summary_events=[11],limitations='silent-only appearances and unnamed speaker identities are not inferred'))
L.writej(O/'design/cells.json',cells)
L.writej(O/'candidate/manifest.json',dict(status='STAGED_NATIVE_PENDING',files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ['NightRemaster.ain','winmm.dll']},source_sha256=L.sha(src),forwarded=forward,added_functions=ids,new_globals=0,serialized_schema_changes=0,old_code_prefix_exact=True,messages_exact=True,renamed_string_indices=renamed,dll_string_patch=dict(offset=offset,before=needle.hex(),after=replacement.hex()),mini_size=[32,40],detail_size=[104,130],summary_events=[11],translator_model='Codex internal'))
print('BUILT',L.sha(out),len(ids),'helpers;',len(events),'events;',len(renamed),'renamed strings')
