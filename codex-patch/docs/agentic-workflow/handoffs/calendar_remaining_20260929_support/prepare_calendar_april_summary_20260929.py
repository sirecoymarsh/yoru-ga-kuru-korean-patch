from pathlib import Path
import json,sys,shutil,datetime
sys.dont_write_bytecode=True
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922')
sys.path.insert(0,str(F/'ingame/r24_chart'));import r24lib as L
R=L.CODEX;PRE=R/'staging/calendar_april_readability_20260929';O=R/'staging/calendar_april_summary_20260929'
assert not O.exists(),'Preserve existing summary work'
for d in ['source','design','work/build','work/tmp','candidate','evidence','probe']:(O/d).mkdir(parents=True)
assert L.sha(PRE/'candidate/NightRemaster.ain')=='442c7eea651c605ce76e51b7efe24584da0059efb96d919fb85b74a0fc0df22d'
for n in ['NightRemaster.ain','winmm.dll']:shutil.copy2(PRE/'candidate'/n,O/'source'/n)
for n in ['candidate_meta.json','candidate_raw_code.jam','helpers_readable.jaf']:shutil.copy2(PRE/'work/build'/n,O/'source'/n)
for n in ['cells.json','scope.json','cast_evidence.json','r15_tables.json','r19_tables.json']:shutil.copy2(PRE/'design'/n,O/'design'/n)
shutil.copy2(PRE/'source_pointer.json',O/'source_pointer.json')
ids=L.readj(O/'design/scope.json')['april_event_ids'];events={x['event']:x for x in map(json.loads,(F/'graph/lines_kr.jsonl').read_text('utf-8').splitlines())}
inputs=L.readj(F/'graph/inputs.json');jpath=Path(inputs['files']['NightRemaster.ain']['path']);assert L.sha(jpath)==inputs['files']['NightRemaster.ain']['sha256']
jp=L.raw_messages(jpath.read_bytes())[3];kr=L.raw_messages((O/'source/NightRemaster.ain').read_bytes())[3]
rows=[]
for no in ids:
    rows.append(dict(no=no,lines=[dict(m=r['m'],jp=jp[r['m']].decode('cp932'),kr=L.decode(kr[r['m']]),speaker_hint=r.get('sp')) for r in events[no]['seq']]))
L.writej(O/'source/scenarios.json',dict(source_jp_sha256=L.sha(jpath),source_kr_sha256=L.sha(O/'source/NightRemaster.ain'),extraction_index_sha256=L.sha(F/'graph/lines_kr.jsonl'),events=rows))
for row in rows:
    no=row['no'];lines=['# E%05d'%no]
    for r in row['lines']:
        t=r['jp'].strip()
        if t and set(t)-set('・… .　'):lines.append(str(r['m'])+': '+t)
    (O/'source'/('E%05d.txt'%no)).write_text('\n'.join(lines),'utf-8')
L.writej(O/'design/progress.json',dict(status='drafting',translator_model='Codex internal',author='/root',total=146,completed_ids=[],remaining_ids=ids,scope='4월 143칸의 146개 이벤트 요약. 다른 달/원작 대사/저장 구조 수정 없음',next='Read full scene packets, author source-bound summaries, build and mute native test'))
with (R/'progress.md').open('a',encoding='utf-8') as f:f.write('\n\n### '+datetime.datetime.now().astimezone().isoformat()+' — 4월 요약 작업 시작\n- 사용자: 인게임에서 4월만 작업 완료하고 보여줘. 146개 이벤트 원문·설치 대사를 메시지 ID로 동결.\n- 작업: '+str(O)+'; 다음: 장면별 요약 작성, UI 높이/미열람 숨김/다른 달 무변경 검증. 실제 설치본·저장 데이터는 유지.\n')
print(O);print('events',len(rows),'messages',sum(len(r['lines']) for r in rows))
