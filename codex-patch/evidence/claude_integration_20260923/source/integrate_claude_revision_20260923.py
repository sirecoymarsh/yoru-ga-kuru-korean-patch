"""MSG1-only integration of reviewed handoff; whole native-page layout, no CODE edits."""
from pathlib import Path
import collections, copy, functools, hashlib, json, re, shutil, struct, sys, zlib
import review_claude_handoff_20260923 as a

O=a.R/'staging/claude_integration_20260923'
BASE='91b827804c22b1a2390312391d0ad4f7178ae8228250354f27f8fbc5de1b3169'
CANDIDATE='1e98fcc50805e756c6f329462aa01dd446d466cccf22118d92bd51dcb1dce11f'
OVERRIDES={
    5123:'「달이 푸르네… 아직 얼어붙은 밤이야」',
    75078:'「달이 푸르네… 아직 얼어붙은 밤이야」',
    5717:'「어둠 밝혀 얼어붙은 밤 녹이는 자…」',
    10446:'「단, 효력은 얼어붙은 밤 동안뿐이다」',
    65344:'「납득의 문제가 아니라니까…」',
    92177:'「……참된 달이 관측을 방해하네…」',
    19005:'「그래, 온통 김치만 아니면 부탁할게……」',
    33019:'「얼어붙은 밤과는 다른 건가요?」',
    58240:'「아뇨, 선배가…」',
    62912:'「아… 쿄카와는,',
    72313:'「뭔가 말하려고 하길래… 중간에 도망칠 줄',
    72314:'　알았어」',
    3549:'참된 달이 푸른 밤에만 전국에서 잇따르는 이상 범죄는',
    32678:'거대한 참된 달이 떠 있었다. 달은 보이지 않았다.',
    33021:'「얼어붙은 밤은 히카리가 만든 결계고,',
    33022:'　참된 밤은 그들이 사는 세계 자체다」',
    33084:'「히카리 들림이 늘면 지상을 비추는',
    33085:'　참된 달의 빛도 강해진다」',
    33093:'「기록상으로도 거의 백 년간 이어진',
    33094:'　얼어붙은 밤 끝에야 완성되었지…」',
    43804:'「얼어붙은 밤에 히카리와 마주할 때마다',
    43805:'　실은 무서워서 울 것만 같았어」',
    44156:'「얼어붙은 밤에 히카리와 마주할 때마다',
    44157:'　실은 무서워서 울 것만 같았어」',
    87176:'「얼어붙은 밤에 히카리와 마주할 때마다',
    87177:'　실은 무서워서 울 것만 같았어」',
    78574:'마지막의 『…라든가……』도 완전히 사족이었다.',
    93312:'「먼저 달이 떠 있나 찾아보고,',
    93313:'　참된 달의 색이 변하지 않나……',
    93314:'　한동안 바라보게 돼요.」',
    47187:'「납득의 문제가 아니라니까…」',
    58389:'「뭔가 말하려고 하길래… 중간에 도망칠 줄',
    58390:'　알았어」',
    25883:'「그야 뭐, 다른 누구도 아닌 네',
    25884:'　일이니까」',
    44740:'「아… 쿄카와는,',
    44741:'　아까 이야기했으니까」',
}
RETAIN_IDS={19060,43330,80246,82933,12670,12671,77928,77929,46565,64100,100595,100596}

def putj(name,value):
    (O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    ptr=a.readj(a.R/'ui_cumulative/current.json');rt=Path(ptr['runtime'])
    assert a.sha(rt/'NightRemaster.ain')==BASE
    assert a.sha(a.OUT/'combined_candidate.jsonl')==CANDIDATE
    assert a.sha(ptr['manifest'])==ptr['manifest_sha256']
    O.mkdir(parents=True,exist_ok=True)
    if not (O/'source_pointer.json').exists():
        putj('source_pointer.json',ptr)
        shutil.copy2(rt/'NightRemaster.ain',O/'baseline.ain')
        shutil.copy2(a.OUT/'combined_candidate.jsonl',O/'input_candidate.jsonl')
    assert a.readj(O/'source_pointer.json')==ptr
    assert a.sha(O/'baseline.ain')==BASE and a.sha(O/'input_candidate.jsonl')==CANDIDATE
    bs=(O/'baseline.ain').read_bytes();plain,start,end,raw=a.raw_messages(bs)
    proxy=a.readj(a.PROXY);enc={x['unicode_character']:bytes.fromhex(x['proxy_sjis_hex']) for x in proxy['mapping']}
    dec={x['proxy_character']:x['unicode_character'] for x in proxy['mapping']}
    decode=lambda b:''.join(dec.get(c,c) for c in b.decode('cp932'))
    encode=lambda text:b''.join(enc[c] if c in enc else c.encode('cp932') for c in text)
    baseline=[decode(b) for b in raw];text=list(baseline)
    proposed=[json.loads(s) for s in (O/'input_candidate.jsonl').read_text('utf8').splitlines()]
    for x in proposed:
        assert x['current']==baseline[x['m_id']]
        text[x['m_id']]=x['proposed']
    original_proposal=list(text)
    for i in RETAIN_IDS:text[i]=baseline[i]
    for i,s in OVERRIDES.items():text[i]=s
    prelayout=list(text)
    _,faces=a.parse_fnl_font(rt/'NightRemasterFont.fnl',0);face,den,_=a.select_fnl_face(faces,60)
    indices,_=a.load_proxy_indices(proxy,len(face.widths));meter=a.WidthMeasurer(face,den,indices,-2.,2.,0.)
    @functools.lru_cache(maxsize=100000)
    def width(s):return meter.measure(s,True)['max_width_px']
    pages=a.readj(a.HERE/'message_page_groups.json')['pages']
    uses=collections.Counter(i for p in pages for i in p['body_message_ids'])
    cs=plain.index(b'CODE');code=plain[cs+8:cs+8+struct.unpack_from('<I',plain,cs+4)[0]]
    records=[];failures=[]
    for pg in pages:
        ids=pg['body_message_ids'];budget=668 if pg['window_type']=='Face' else 884
        if not any(text[i]!=baseline[i] for i in ids):continue
        if not any(width(text[i])>budget for i in ids):continue
        assert pg['complete'] and pg['window_type'] in ('Text','Face','All') and pg['font_command']==0
        assert len(pg['speaker_message_ids'])<=1 and all(uses[i]==1 for i in ids)
        chain=b''.join(struct.pack('<HIHI',0x59,r['message_id'],0x30,6972 if r['terminator']=='R' else 6973) for r in pg['messages'])
        assert code.count(chain)==1,('native page chain changed',pg['page_id'])
        vals=[text[i] for i in ids];nonempty=[s for s in vals if s.strip()]
        assert all(not re.search(r'[\x00-\x1f\x7f]|\$\{|%[0-9$.]*[sdif]',s) for s in vals)
        # Existing page-level flow uses blank trailing fields. Preserve their slots.
        # Readable source boundaries are spaces; ambiguous morphology is recorded for review.
        quote=nonempty[0].startswith(('「','（'))
        indent='　' if quote else ''
        combined=' '.join(s.strip('　 ') for s in nonempty)
        combined=re.sub(r' (?=[」』）】!?！？.,、。])','',combined)
        lines=[];rest=combined
        while rest:
            prefix=indent if lines else ''
            if width(prefix+rest)<=budget:lines.append(prefix+rest);break
            splits=[i for i,c in enumerate(rest) if c==' ' and i>0 and width(prefix+rest[:i])<=budget
                    and rest[i+1:i+2] not in '」』）】!?！？.,、。']
            if not splits:break
            pos=max(splits);lines.append(prefix+rest[:pos]);rest=rest[pos+1:]
        else:rest=''
        if not lines or width(lines[-1])>budget or ''.join(lines).replace(' ','').replace('　','')!=combined.replace(' ','') or len(lines)>len(ids):
            failures.append(dict(page_id=pg['page_id'],ids=ids,window=pg['window_type'],budget=budget,before=vals,attempt=lines))
            continue
        while len(lines)>1 and width(lines[-1])<budget*.18:
            previous=lines[-2];cut=previous.rfind(' ')
            if cut<1:break
            move=indent+previous[cut+1:]+' '+lines[-1].lstrip('　')
            if width(move)>budget or not previous[:cut].strip('　 '):break
            lines[-2]=previous[:cut];lines[-1]=move
        final=lines+['']*(len(ids)-len(lines))
        assert re.sub(r'\s','',''.join(vals))==re.sub(r'\s','',''.join(final))
        assert all(width(s)<=budget for s in final)
        for i,s in zip(ids,final):text[i]=s
        records.append(dict(page_id=pg['page_id'],ids=ids,window=pg['window_type'],budget=budget,
                            before=vals,after=final,widths=[width(s) for s in final],native_chain_exact=True))
    changes={i:s for i,s in enumerate(text) if s!=baseline[i]}
    classes={x['message_id']:x for x in a.readj(a.HERE/'message_window_classification.json')['rows']}
    unresolved=[]
    for i,s in changes.items():
        c=classes[i];assert not c['ambiguous'] and c['font_commands']==[0] and c['message_roles']==['Body']
        budget=668 if c['window_types']==['Face'] else 884
        if width(s)>budget:unresolved.append(dict(m_id=i,width=width(s),budget=budget,text=s))
        assert decode(encode(s))==s
        assert re.findall(r'[\x00-\x1f\x7f]',baseline[i])==re.findall(r'[\x00-\x1f\x7f]',s)
    putj('layout_records.json',records);putj('layout_failures.json',failures);putj('unresolved_width.json',unresolved)
    putj('semantic_overrides.json',[dict(m_id=i,external_proposed=original_proposal[i],final=text[i],authored=OVERRIDES.get(i),
                                      decision='retain installed text' if i in RETAIN_IDS else 'Codex internal correction')
                                     for i in sorted(set(OVERRIDES)|RETAIN_IDS)])
    putj('final_edits.json',{str(i):s for i,s in changes.items()})
    if failures or unresolved:
        print(json.dumps(dict(status='LAYOUT_NEEDS_MANUAL',failures=failures,unresolved=unresolved),ensure_ascii=False,indent=2))
        raise SystemExit(2)  # A prior candidate is not proof that this build succeeded.
    out=list(raw)
    for i,s in changes.items():out[i]=encode(s)
    body=b''.join(struct.pack('<I',len(b))+bytes((c+n+0x60)&255 for n,c in enumerate(b)) for b in out)
    newplain=plain[:start+12]+body+plain[end:];z=zlib.compress(newplain,9)
    packed=bs[:8]+struct.pack('<II',len(newplain),len(z))+z
    check,s,e,decoded=a.raw_messages(packed)
    assert check[:s+12]==plain[:start+12] and check[e:]==plain[end:]
    assert len(decoded)==len(raw)==100944 and {i for i,(x,y) in enumerate(zip(raw,decoded)) if x!=y}==set(changes)
    assert [decode(b) for b in decoded]==text
    (O/'NightRemaster.ain').write_bytes(packed)
    evidence=dict(status='MSG1_LAYOUT_STATIC_PASS_SEMANTIC_REVIEW_PENDING',source_pointer=ptr,
                  source_files={'NightRemaster.ain':BASE},files={'NightRemaster.ain':a.sha(O/'NightRemaster.ain')},
                  input_candidate_sha256=CANDIDATE,font_sha256=a.sha(rt/'NightRemasterFont.fnl'),
                  changed_fields=len(changes),changed_ids=sorted(changes),reflow_pages=len(records),
                  layout_only_fields=sum(text[i]!=prelayout[i] for i in range(len(text))),
                  outside_MSG1_exact=True,MSG_count=100944,safe_width_overflow=0,
                  semantic_overrides_ids=sorted(set(OVERRIDES)|RETAIN_IDS),native_tested=False)
    putj('build_evidence.json',evidence)
    print(json.dumps(evidence,ensure_ascii=False,indent=2)[:2200])

if __name__=='__main__':main()
