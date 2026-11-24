"""Read-only story checkpoints, separately labeled all-branch event collection."""
from pathlib import Path
import copy,json,re,shutil,struct
import inspect_story_progress_20260926 as src
import build_save_slots_20260925 as base
b=base.b;p=base.p;q=base.q;a=base.a;n=base.n
R=src.R;O=src.O;S=src.S;HERE=Path(__file__).parent;AUTHOR='Codex internal'
h=base.h;clean=base.clean;textdump=base.textdump;wrapper=base.wrapper
def save(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
# Hand-reviewed checkpoints; never calendar interpolation, branch counts, or global gallery flags.
STAGES=[
 (1,'도입부',[1,2,121]),
 (2,'백화점 진입',[22]),(3,'백화점 이후',[65]),
 (4,'학교 진입',[74]),(5,'학교 이후',[102]),
 (6,'수수께끼의 틈',[180,*range(154,175)]),(7,'수수께끼의 틈 이후',[185,201]),
 (8,'서양관 진입',[404,452,501,525,10121,20121,30121,40121]),
 (9,'서양관 이후',[5024]),
 (10,'학원제',[602,10161,20141,30041,40143]),
 (11,'최종장 직전',[901,5023,10181,10182,10183,40144,652,653,654,658,10201,10202,20181,30101]),
 (12,'최종장',[903]),
]
LABELS={0:'기록 없음',**{i:t for i,t,_ in STAGES},13:'엔딩 완료'}
def quote(t):return json.dumps(t,ensure_ascii=False)
def main():
    ptr=a.readj(S/'current.json');rt=Path(ptr['runtime']);assert a.readj(R/'ui_cumulative/current.json')==ptr
    assert h(rt/'NightRemaster.ain')==src.EXPECTED
    m=b.read_meta(S/'candidate_meta.json');source=S/'NightRemaster.ain';ids0={f['name']:f['index'] for f in m['functions']}
    schedule=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/graph/schedule.json')
    catalog=a.readj(schedule);events={e['id']:e for e in catalog['events']}
    anchors=[];stage='int KR_StoryStage() {\n    int stage=0;\n'
    for code,label,evs in STAGES:
        for event in evs:
            e=events[event];assert e['category']=='main' and e['registers_self'] and e['triggers']
            anchors.append(dict(stage=code,label=label,id=event,fn=e['fn'],triggers=e['triggers']))
        condition=' || '.join('LEventFlag::GetOnce('+quote('E%05d'%i)+')' for i in evs)
        stage+=f'    if({condition}) stage={code};\n'
    # GetOnce is a read-only test of this save's scenario registry, not a consuming getter.
    stage+='    if(LEventFlag::GetOnce("エンディング終了")) stage=13;\n    return stage;\n}\n'
    stage+='string KR_StoryLabel(int stage) {\n'+''.join(f'    if(stage=={k}) return {quote(v)};\n' for k,v in LABELS.items())+'    return "기록 없음";\n}\n'
    stage+='string KR_StoryNow() { return "본편 진행: "+KR_StoryLabel(KR_StoryStage()); }\n'
    stage+='string KR_StoryHome() { int stage=KR_StoryStage(); if(stage==6) return "본편　틈 진입"; if(stage==7) return "본편　틈 이후"; return "본편　"+KR_StoryLabel(stage); }\n'
    old=(HERE/'save_slots_20260925.jaf').read_text('utf8')
    snapshot=old[old.index('string KR_SaveSnapshot('):old.index('string KR_SavePlace(')]
    snapshot=snapshot.replace('KR_SaveSnapshot(','KR_ProgressSnapshot(').replace('+",1043";','+",1043,KR_MAIN1,"+("%d" % KR_StoryStage());')
    paint=old[old.index('void KR_SavePaint('):]
    paint=paint.replace('KR_SavePaint(','KR_ProgressPaint(')
    olddoc=n.ex.decode_ex(base.O/'pact_168.pactex')
    oldparts=[x.name.value.decode('cp932') for x in n.child(n.part(olddoc,'矩形_000'),'子パーツ').children]
    paint=paint.replace('/*HIDE_LEGACY_PARTS*/','\n'.join('PartsEngine.SetComponentShow(KR_SaveCellPart(view,'+quote(key)+'),false);' for key in oldparts))
    paint=paint.replace('string rate="이벤트 진입률 --";','string rate="본편: 미기록 (재저장 필요)";')
    paint=paint.replace('string detail="다시 저장하면 진행 정보 표시";','string detail="전체 달성률 -- / 재저장 필요";')
    paint=paint.replace('rate="이벤트 진입률 "+KR_T8Pct(ev,total);\n        detail=("%d" % ev)+" / "+("%d" % total)+" · 전체 분기";\n        if(kind==13) detail="남은 탐색 시간 "+fields[6];',
        'detail="전체 달성률 "+KR_T8Pct(ev,total)+" (이벤트)";\n        if(fields.Numof()>=30) { if(fields[28]=="KR_MAIN1") rate="본편: "+KR_StoryLabel(fields[29].ToInt()); }\n        if(kind==13) place=place+" · 남은 시간 "+fields[6];')
    assert '이벤트 진입률' not in paint and 'KR_MAIN1' in snapshot and 'KR_MAIN1' in paint
    jaf=stage+'\n'+snapshot+'\n'+paint
    (O/'helpers_readable.jaf').write_text(jaf,'utf8');(O/'helpers.jaf').write_text(base.korean(jaf),'utf8')
    decl=O/'declared.ain';b.cmd('ain','edit','--jaf',O/'helpers.jaf','-o',decl,source)
    b.cmd('ain','dump','-j','-o',O/'declared_meta.json',decl);dm=b.read_meta(O/'declared_meta.json')
    added=dm['functions'][len(m['functions']):];ids={f['name']:f['index'] for f in added}
    patches=[b.clean(b.native_lower(textdump(dm,f['index'],decl)),f['name']) for f in added];relocated=[]
    def change(name,body):relocated.append(ids0[name]);patches.append(body)
    change('KR_SaveSnapshot',wrapper(m,ids0['KR_SaveSnapshot'],'\t.LOCALREF saveNo\n\tCALLFUNC KR_ProgressSnapshot\n'))
    change('KR_SavePaint',wrapper(m,ids0['KR_SavePaint'],'\t.LOCALREF view\n\t.LOCALREF type\n\tCALLFUNC KR_ProgressPaint\n'))
    def qs(text):return 'S_PUSH '+quote(base.encode(text).decode('cp932'))
    # Preserve the existing menu, result routing, locals and character click line offsets.
    for name in ['KR_T8PlayerInfoMenu','KR_T8EventDetail','KR_T8HomeRateText']:
        body=clean(m,ids0[name],source)
        if name=='KR_T8HomeRateText':
            body=base.once(body,qs('\n이벤트　'),qs('\n전체 이벤트　'))
            body=base.once(body,'\t'+qs('\n\n')+'\n','\t'+qs('\n')+'\n\tCALLFUNC KR_StoryHome\n\tS_ADD\n\t'+qs('\n')+'\n\tS_ADD\n')
        else:
            oldlabel='이 저장의 이벤트 진입률  ' if name=='KR_T8EventDetail' else '\n이 저장의 이벤트 진입률  '
            body=base.once(body,qs(oldlabel),qs('전체 이벤트 달성률  ' if name=='KR_T8EventDetail' else '\n이 저장의 전체 이벤트 달성률  '))
            if name=='KR_T8EventDetail':
                body=base.once(body,qs('\n스토리  '),qs('\n본편·분기 이벤트 수집  '))
                head='이벤트 진입 자세히\n'
            else:head='플레이 정보\n'
            body=base.once(body,'\t'+qs(head)+'\n','\t'+qs(head)+'\n\tCALLFUNC KR_StoryNow\n\tS_ADD\n\t'+qs('\n')+'\n\tS_ADD\n')
        change(name,body)
    (O/'patch.jam').write_text('\n'.join(patches),'utf8');out=O/'NightRemaster.ain'
    b.cmd('ain','edit','--jam',O/'patch.jam','-o',out,decl)
    oldraw=b.unpack(source.read_bytes());raw=bytearray(b.unpack(out.read_bytes()));oldn=struct.unpack_from('<I',oldraw,12)[0];newn=struct.unpack_from('<I',raw,12)[0]
    struct.pack_into('<I',raw,24+newn,m['functions'][0]['address'])
    assert raw[16:16+oldn]==oldraw[16:16+oldn];out.write_bytes(b.pack(raw,source.read_bytes()[:8]))
    b.cmd('ain','dump','-j','-o',O/'candidate_meta.json',out);nm=b.read_meta(O/'candidate_meta.json')
    for f,g in zip(m['functions'],nm['functions']):
        same=dict(f)
        if f['index'] in relocated:same['address']=g['address']
        assert same==g,f['index']
    for k in m:
        if k!='functions':assert m[k]==nm[k],k
    assert b.raw_messages(source.read_bytes())[3]==b.raw_messages(out.read_bytes())[3]
    assert b.strings(raw)[2][:len(b.strings(oldraw)[2])]==b.strings(oldraw)[2]
    b.cmd('ain','dump','--raw-code','--no-macros','-o',O/'native_raw_code.jam',out)
    audit=b.audit(out,O/'candidate_meta.json',O/'native_raw_code.jam',rt/'NightRemaster.exe');save('native_opcode_audit.json',audit);assert audit['all_active_opcodes_supported']
    # Existing save card layout fits the two separately labeled measures; all native assets untouched.
    for name in ['NightRemasterPact.afa','NightRemasterEX.ex']:shutil.copy2(S/name,O/name)
    save('source_pointer.json',ptr)
    save('story_catalog.json',dict(source=str(schedule),sha256=h(schedule),anchors=anchors,labels=LABELS,end_flag='エンディング終了',count_basis='Last entered mandatory story checkpoint, not a completion percentage; current-save flags only',translator_model=AUTHOR))
    save('build_evidence.json',dict(status='STAGED_UNVERIFIED',files={name:h(O/name) for name in ['NightRemaster.ain','NightRemasterPact.afa']},source_pointer=ptr,added_functions=ids,relocated=relocated,same_length_sites=[],PACT={'changed_entries':[]},serialized_schema_changes=0,MSG1_exact=True,STR0_prefix_exact=True,translator_model=AUTHOR))
    print('STAGED',O,flush=True)
if __name__=='__main__':main()
