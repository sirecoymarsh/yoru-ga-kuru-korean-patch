"""Source-bound April summary render leaves; append-only private candidate."""
from pathlib import Path
import sys,re,json,struct,shutil,hashlib
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from calendar_april_summaries_20260929 import SUMMARIES,TRANSLATOR_MODEL
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
R=L.CODEX;O=R/'staging/calendar_april_summary_20260929';W=O/'work/build';L.TMP=O/'work/tmp'
BASE='442c7eea651c605ce76e51b7efe24584da0059efb96d919fb85b74a0fc0df22d'
LIVE='1a7bd3352132f123f2dd1cf8491b8faf16391b7361a57d6f76585843b4757542'
src=O/'source/NightRemaster.ain';cur=L.readj(L.CURRENT);rt=Path(cur['runtime'])
assert cur==L.readj(O/'source_pointer.json')
assert L.sha(rt/'NightRemaster.ain')==LIVE and L.sha(src)==BASE
ids=L.readj(O/'design/scope.json')['april_event_ids']
assert set(SUMMARIES)==set(ids) and len(SUMMARIES)==146
assert all(v.strip() and '\n' not in v for v in SUMMARIES.values())
frozen=L.readj(O/'design/summaries.json');scenes=L.readj(O/'source/scenarios.json')
rows={x['no']:x for x in scenes['events']}
for event in frozen['events']:
    n=event['no'];row=rows[n]
    assert event['source_message_ids']==[r['m'] for r in row['lines']]
    assert event['source_event_sha256']==hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    event['summary']=SUMMARIES[n];event['status']='source_qa_pass'
L.writej(O/'design/summaries.json',frozen)
L.writej(O/'evidence/semantic_qa.json',dict(translator_model=TRANSLATOR_MODEL,author='/root',reviewer='/root/april_summary_review',
    reviewed_events=146,reviewed_japanese_messages=7049,source_sha256=L.sha(O/'source/scenarios.json'),summary_sha256=L.sha(O/'design/summaries.json'),
    findings=[dict(no=1506,message_id=99992,severity='P3',source='昨日、ちょっと夜更かしして',before='밤을 새운',after='전날 늦게 잠든',status='resolved by primary')],
    group_e00004_scope='E4 only: message IDs 5131–5149',unresolved=[]))
shutil.copy2(H/'calendar_april_summaries_20260929.py',O/'source/calendar_april_summaries_20260929.py')

def function(text,name):
    start=re.search(r'^(?:void|int|string|bool) '+re.escape(name)+r'\(',text,re.M).start()
    pos=text.index('{',start)+1;depth=1
    while depth:
        depth+=(text[pos]=='{')-(text[pos]=='}');pos+=1
    return text[start:pos]

def tree(items,indent='    '):
    if not items:return indent+'return "";\n'
    mid=len(items)//2;n,t=items[mid]
    out=indent+f'if(no=={n})return '+json.dumps(t,ensure_ascii=False)+';\n'
    if items[:mid]:out+=indent+f'if(no<{n}) {{\n'+tree(items[:mid],indent+'    ')+indent+'}\n'
    return out+tree(items[mid+1:],indent)

old=(O/'source/helpers_readable.jaf').read_text('utf-8')
info=function(old,'KR_U29Info').replace('string KR_U29Info(','string KR_AS29Info(')
start=info.index('    string story="";')
info=info[:start]+'    return t;\n}'
board=function(old,'KR_U29Board').replace('void KR_U29Board(','void KR_AS29Board(').replace('KR_U29Info(','KR_AS29Info(')
anchor='        if(labelH>infoH)infoH=labelH;'
assert board.count(anchor)==1
board=board.replace(anchor,anchor+'''
        if (read) {
            string heading="줄거리";
            if(stages>1)heading="첫 장면 줄거리";
            int storyFont=font-2;
            if(storyFont<18)storyFont=18;
            int storyWidth=infoWidth/storyFont-1;
            int storyY=bodyY-28+infoH+16;
            KR_CText(KR_P29Part(8),root,float(infoX),float(storyY),storyFont,KR_CTint(heading,KR_CGold()),3);
            int hw=0;int hh=0;int sw=0;int sh=0;
            PartsEngine.Parts_GetPartsSize(KR_P29Part(8),hw,hh,1);
            KR_CText(KR_P29Part(9),root,float(infoX),float(storyY+hh+8),storyFont,KR_B29Wrap(KR_AS29Story(no),storyWidth),3);
            PartsEngine.Parts_GetPartsSize(KR_P29Part(9),sw,sh,1);
            infoH=infoH+16+hh+8+sh;
            if(hw>infoW)infoW=hw;
            if(sw>infoW)infoW=sw;
        }''')
jaf='string KR_AS29Story(int no) {\n'+tree(sorted(SUMMARIES.items()))+'}\n'+info+'\n'+board+'''
void KR_AS29Router(int no,string head,int stages,bool canplay) {
    if(KR_U29April(no))KR_AS29Board(no,head,stages,canplay);
    else KR_U29Router(no,head,stages,canplay);
}
'''
(W/'helpers_readable.jaf').write_text(jaf,'utf-8');(W/'helpers.jaf').write_text(L.jaf_literal_encode(jaf),'utf-8')
decl=W/'declared.ain';out=O/'candidate/NightRemaster.ain';m=L.read_meta(O/'source/candidate_meta.json')
L.cmd('ain','edit','--jaf',W/'helpers.jaf','-o',decl,src)
L.cmd('ain','dump','-j','-o',W/'declared_meta.json',decl);dm=L.read_meta(W/'declared_meta.json')
added={f['name']:f['index'] for f in dm['functions'][len(m['functions']):]}
assert set(added)=={'KR_AS29Story','KR_AS29Info','KR_AS29Board','KR_AS29Router'}
patch=[]
for n in added:
    p=W/(n+'.jam');L.cmd('ain','dump','--function',n,'-o',p,decl)
    jam=L.native_lower(p.read_text('utf-8'))
    jam=re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',lambda z:'\t.LOCALASSIGN '+z[1]+' '+str(struct.unpack('<i',struct.pack('<f',float(z[2])))[0]),jam)
    patch.append(L.clean(jam.replace('\tF_ASSIGN\n','\tX_ASSIGN 1\n'),n))
name='KR_P29Board';p=W/(name+'_original.jam');L.cmd('ain','dump','--function',name,'-o',p,src)
body=L.clean(p.read_text('utf-8'),name);assert body.count('CALLFUNC KR_U29Router')==1
patch.append(body.replace('CALLFUNC KR_U29Router','CALLFUNC KR_AS29Router'))
(W/'patch.jam').write_text('\n'.join(patch),'utf-8');L.cmd('ain','edit','--jam',W/'patch.jam','-o',out,decl)
base=L.unpack(src.read_bytes());raw=bytearray(L.unpack(out.read_bytes()));size=struct.unpack_from('<I',raw,12)[0]
struct.pack_into('<I',raw,24+size,m['functions'][0]['address']);out.write_bytes(L.pack(bytes(raw),src.read_bytes()[:8]))
L.cmd('ain','dump','-j','-o',W/'candidate_meta.json',out);nm=L.read_meta(W/'candidate_meta.json');changed=L.fid_of(m,name)
assert [i for i,(a,b) in enumerate(zip(m['functions'],nm['functions'])) if a!=b]==[changed]
assert {k:v for k,v in m['functions'][changed].items() if k!='address'}=={k:v for k,v in nm['functions'][changed].items() if k!='address'}
for k in m:
    if k!='functions':assert m[k]==nm[k],k
oldn=struct.unpack_from('<I',base,12)[0];assert raw[16:16+oldn]==base[16:16+oldn]
assert L.strings(raw)[2][:len(L.strings(base)[2])]==L.strings(base)[2]
assert L.raw_messages(out.read_bytes())[3]==L.raw_messages(src.read_bytes())[3]
L.cmd('ain','dump','--raw-code','--no-macros','-o',W/'candidate_raw_code.jam',out)
audit=L.audit(out,W/'candidate_meta.json',W/'candidate_raw_code.jam',rt/'NightRemaster.exe');assert audit['all_active_opcodes_supported']
L.writej(W/'native_opcode_audit.json',audit);shutil.copy2(O/'source/winmm.dll',O/'candidate/winmm.dll')
L.writej(O/'candidate/manifest.json',dict(status='APRIL_SUMMARIES_NATIVE_PENDING',source_sha256=BASE,live_sha256=LIVE,
    files={n:dict(sha256=L.sha(O/'candidate'/n)) for n in ('NightRemaster.ain','winmm.dll')},changed_functions=[name],added_functions=added,
    summary_count=146,summary_ids=ids,summary_source_sha256=L.sha(O/'design/summaries.json'),original_code_prefix_exact=True,
    original_strings_prefix_exact=True,messages_exact=True,serialized_schema_changes=0,translator_model=TRANSLATOR_MODEL,author='/root',installed=False))
print(json.dumps({'candidate':str(out),'sha256':L.sha(out),'summary_count':146,'helpers':len(added)},ensure_ascii=False))
