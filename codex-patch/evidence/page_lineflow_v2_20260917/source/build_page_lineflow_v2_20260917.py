"""Reflow complete ordinary pages from the pre-comma-polish snapshot."""
import collections,functools,json,re,shutil,struct,sys,zlib
from pathlib import Path
import polish_translation_20260917 as p
import audit_message_pixel_widths as metric
sys.stdout.reconfigure(encoding='utf-8')
WORK=p.WORK/'page_lineflow_v2'

def build():
    WORK.mkdir(exist_ok=True)
    source=p.WORK/'output/NightRemaster.ain';source_bytes=source.read_bytes()
    assert p.sha(source_bytes)=='e252d93441069fb75f70504528facb30983544ea7e204c8fd1a9a65501d360e8'
    ptr=p.readj(p.ROOT/'ui_cumulative/current.json');live=Path(ptr['runtime'])/'NightRemaster.ain';live_bytes=live.read_bytes()
    assert p.sha(live_bytes)=='fc0107fff4b153b03261bfe4d2835d626afb93efddc76b1da5dc2172507b3c77'
    (WORK/'installed_before.ain').write_bytes(live_bytes)
    p.writej(WORK/'source_pointer.json',ptr)
    jp,base,_,classes,proxy=p.load();plain,start,end,raw=p.raw_messages(source_bytes)
    fwd={x['unicode_character']:x['proxy_character'] for x in proxy['mapping']};rev={v:k for k,v in fwd.items()}
    decode=lambda b:''.join(rev.get(c,c) for c in b.decode('cp932'))
    targets=[decode(b) for b in raw]
    pages=p.readj(p.HERE/'message_page_groups.json')['pages']
    excluded=set(p.readj(p.WORK/'semantic_exclusions.json')['message_ids'])
    uses=collections.Counter(i for pg in pages for i in pg['body_message_ids'])
    _,faces=metric.parse_fnl_font(p.INPUT/'font.fnl',0);face,den,_=metric.select_fnl_face(faces,60)
    indices,_=metric.load_proxy_indices(proxy,len(face.widths));meter=metric.WidthMeasurer(face,den,indices,-2.,2.,0.)
    @functools.lru_cache(maxsize=400000)
    def width(s):return meter.measure(s,True)['max_width_px']
    norm=lambda s:re.sub(r'\s','',s)
    cstart=plain.index(b'CODE');clen=struct.unpack_from('<I',plain,cstart+4)[0];code=plain[cstart+8:cstart+8+clen]
    positions=collections.defaultdict(list)
    for match in re.finditer(rb'\x59\x00(.{4})\x30\x00(.{4})',code,re.S):
        mid,func=struct.unpack('<I',match[1])[0],struct.unpack('<I',match[2])[0]
        if func in (6972,6973):positions[mid].append(match.start())
    wordfreq=collections.Counter(re.findall(r'[가-힣]+', ' '.join(targets)))
    # Potentially split endings/words are held instead of guessing new spacing.
    attached={'가','거나','고','과','까지','나','는','는데','니','니까','도','든지','라고','라며','라면','라서','라니','라도','를','로','마저','만','며','면서','면','부터','서','은','은데','을','의','이고','이며','이니','인데','처럼','조차','지만','와','였다','이었다','졌고','졌다'}
    def ambiguous(a,b):
        if not a or not b:return True
        right=re.match(r'([가-힣]+)',b)
        if not right:return False
        y=right[1]
        # Conjugated endings are not standalone words, even when the corpus
        # contains their joined form only once. Hold these original boundaries.
        suffix_start=r'^(?:잖|였|입니다|입니까|이라는|이라고|이라며|이라면|이라니|이라서|이란|이랄|이래|이랬|이었다|이었|이겠|이에요|이야|이냐|인가|인지|인걸|인건|인거|인줄|인듯|다고|다며|다니|다니까|네요|네요오|군요|구나|거든요|으면서|예요|라는|됐다가)'
        if y in attached or re.match(suffix_start,y):return True
        # Quoted punctuation and Latin nouns can also precede attached endings.
        if re.search(r'[,，、.!?。！？…」』）)]$',a):return False
        left=re.search(r'([가-힣]+)$',a)
        if not left:return False
        x=left[1]
        return min(len(x),len(y))<=2 and wordfreq[x+y]>=2
    counts=collections.Counter();records=[];held=[];edits={};empty=[]
    for pg in pages:
        ids=pg['body_message_ids']
        if len(ids)<2:continue
        vals=[targets[i] for i in ids];why=None
        if not pg['complete']:why='incomplete_control_chain'
        elif pg['window_type'] not in ('Text','Face','All') or pg['font_command']!=0:why='nonstandard_window_font'
        elif any(i in excluded for i in ids):why='preserved_scene_scope'
        elif any(uses[i]!=1 for i in ids):why='multiple_message_uses'
        elif len(pg['speaker_message_ids'])>1:why='multiple_speakers'
        elif any(not s.strip() or re.search(r'[\x00-\x1f\x7f]|\$\{|【|】|료　　　　|%[0-9$.]*[sdif]',s) for s in vals):why='protected_or_blank'
        elif any(re.match(r'^\s*(?:[※◆◇■□●○☆★◎＊*•]|[-―─]{2,}|\d+[.)、])',s) for s in vals):why='list_or_decorative'
        elif any(not re.search(r'[가-힣A-Za-z0-9]',s) for s in vals):why='standalone_pause_or_symbol'
        quoted=vals[0].startswith('「') and vals[-1].endswith('」')
        if not why:
            if quoted:
                if sum(s.count('「') for s in vals)!=1 or sum(s.count('」') for s in vals)!=1 or any(not s.startswith('　') for s in vals[1:]):why='irregular_dialogue_format'
            elif any(s.startswith(('　',' ')) or '「' in s or '」' in s for s in vals):why='irregular_narration_format'
        budget=668 if pg['window_type']=='Face' else 884
        if not why and any(width(s)>budget for s in vals):why='existing_width_exception'
        # Bind grouping evidence to the actual current bytes, not only old JAM metadata.
        if not why:
            chain=b''.join(struct.pack('<HIHI',0x59,r['message_id'],0x30,6972 if r['terminator']=='R' else 6973) for r in pg['messages'])
            locs=positions[pg['messages'][0]['message_id']]
            if len(locs)!=1 or code[locs[0]:locs[0]+len(chain)]!=chain:why='current_CODE_chain_mismatch'
        clean=[s[1:] if quoted and n else s for n,s in enumerate(vals)]
        if not why and any(ambiguous(a.rstrip(),b.lstrip()) for a,b in zip(clean,clean[1:])):why='ambiguous_word_boundary'
        if why:
            counts[why]+=1;held.append({'page_id':pg['page_id'],'ids':ids,'reason':why});continue
        combined=clean[0].rstrip()
        for s in clean[1:]:
            s=s.strip(' ')
            separator='' if s[:1] in '」』）】!?！？.,、。' else ' '
            combined+=separator+s
        lines=[];rest=combined;failed=False
        while rest:
            indent='　' if quoted and lines else ''
            if width(indent+rest)<=budget:lines.append(indent+rest);break
            legal=[i for i,c in enumerate(rest) if c==' ' and i and width(indent+rest[:i])<=budget and rest[i+1:i+2] not in '」』）】!?！？.,、。']
            if not legal:failed=True;break
            cut=max(legal);lines.append(indent+rest[:cut]);rest=rest[cut+1:]
        if failed or len(lines)>len(ids):
            counts['unfit_without_splitting_word']+=1;held.append({'page_id':pg['page_id'],'ids':ids,'reason':'unfit_without_splitting_word'});continue
        # Avoid a very short final line by moving whole words from its predecessor.
        while len(lines)>1 and width(lines[-1])<budget*.18:
            previous=lines[-2];plain_last=lines[-1].lstrip('　');cut=previous.rfind(' ')
            if cut<1:break
            moved=('　' if quoted else '')+previous[cut+1:]+' '+plain_last
            if width(moved)>budget or not previous[:cut].strip('　 '):break
            lines[-2]=previous[:cut];lines[-1]=moved
        padded=lines+['']*(len(ids)-len(lines))
        assert norm(''.join(vals))==norm(''.join(padded))
        assert all(width(s)<=budget for s in padded)
        if padded==vals:counts['already_suitable']+=1;continue
        records.append({'page_id':pg['page_id'],'ids':ids,'speaker_ids':pg['speaker_message_ids'],'window':pg['window_type'],'widths':[width(s) for s in padded],'empty_tail_count':len(ids)-len(lines)})
        for i,old,new in zip(ids,vals,padded):
            if old!=new:edits[str(i)]=new
            if not new:empty.append(i)
        counts['changed_pages']+=1
    newraw=list(raw)
    for key,text in edits.items():
        i=int(key);newraw[i]=''.join(fwd.get(c,c) for c in text).encode('cp932');assert decode(newraw[i])==text
        assert re.findall(r'[\x00-\x1f\x7f]',targets[i])==re.findall(r'[\x00-\x1f\x7f]',text)
    assert not excluded.intersection(map(int,edits))
    body=b''.join(struct.pack('<I',len(b))+bytes((c+n+0x60)&255 for n,c in enumerate(b)) for b in newraw)
    newplain=plain[:start+12]+body+plain[end:];z=zlib.compress(newplain,9);packed=source_bytes[:8]+struct.pack('<II',len(newplain),len(z))+z
    check,a,b,out=p.raw_messages(packed);assert len(out)==100944 and check[:a+12]==plain[:start+12] and check[b:]==plain[end:]
    assert {i for i,(x,y) in enumerate(zip(raw,out)) if x!=y}==set(map(int,edits))
    installed_raw=p.raw_messages(live_bytes)[3];actual_changed=[i for i,(x,y) in enumerate(zip(installed_raw,out)) if x!=y]
    output=WORK/'output';output.mkdir(exist_ok=True);(output/'NightRemaster.ain').write_bytes(packed)
    p.writej(WORK/'layout_map.json',edits);p.writej(WORK/'layout_records.json',records);p.writej(WORK/'held_pages.json',held)
    report={'status':'STATIC_PASS_NATIVE_PENDING','translator_model':'Codex internal','operation':'Page-wide deterministic layout of already authored Korean; no wording changes','pre_comma_polish_sha256':p.sha(source_bytes),'baseline_sha256':p.sha(live_bytes),'ain_sha256':p.sha(packed),'counts':dict(counts),'layout_fields_from_polish':len(edits),'changed_fields_from_installed':len(actual_changed),'changed_ids_from_installed':actual_changed,'empty_tail_ids':empty,'page_text_except_whitespace_exact':True,'outside_MSG1_exact':True,'MSG_count':100944,'safe_width_overflow':0,'protected_tokens_preserved':True,'current_code_chains_validated':True,'rule':'Join the whole ordinary same-speaker page, then wrap at whitespace by actual FNL metrics. Preserve special/ambiguous pages from the pre-comma polish source.','font_sha256':p.sha((p.INPUT/'font.fnl').read_bytes())}
    p.writej(WORK/'build_evidence.json',report)
    examples={str(i):[edits.get(str(n),targets[n]) for n in range(i,i+3)] for i in [2280,22178]}
    p.writej(WORK/'reported_examples.json',examples)
    print(json.dumps({'counts':dict(counts),'layout_fields':len(edits),'changed_fields_from_installed':len(actual_changed),'empty_tail_fields':len(empty),'sha256':p.sha(packed),'examples':examples},ensure_ascii=False))
    progress=p.readj(p.WORK/'progress.json');progress['page_lineflow_v2']={'stage':'built_static_pass','work':str(WORK),'next':'Independent layout check, representative runtime/backlog, scan and transactional live update'};p.writej(p.WORK/'progress.json',progress)

if __name__=='__main__':build()
