"""Verify WI-008 exact native preview, freeze evidence, and record completion."""
from pathlib import Path
import sys,json,shutil,datetime,re,hashlib
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
from PIL import Image,ImageChops
R=L.CODEX;O=R/'staging/calendar_april_summary_20260929';E=O/'evidence';S=E/'native_april'
PRE=R/'staging/calendar_april_readability_20260929';control=PRE/'evidence/native_april'
probe=L.readj(E/'native_april_probe.json');man=L.readj(O/'candidate/manifest.json')
assert probe['pass'] and not probe['user_files_changed']
assert probe['candidate_sha256']==L.sha(O/'candidate/NightRemaster.ain')==man['files']['NightRemaster.ain']['sha256']
assert L.readj(L.CURRENT)==L.readj(O/'source_pointer.json')
rt=Path(L.readj(L.CURRENT)['runtime']);assert L.sha(rt/'NightRemaster.ain')==man['live_sha256']
assert L.sha(rt/'winmm.dll')==L.sha(O/'source/winmm.dll')==L.sha(O/'candidate/winmm.dll')

def same(a,b):
    assert ImageChops.difference(Image.open(a).convert('RGB'),Image.open(b).convert('RGB')).getbbox() is None,(a,b)

comparisons=['may_list_unchanged','may_detail_unchanged','may_list_after_april',
             'april_list_readable','april_list_mixed','april_list_locked','april_scene_picker',
             'april_detail_unread_open','april_detail_unread_locked']
for name in comparisons:same(S/(name+'.png'),control/(name+'.png'))
same(S/'may_list_unchanged.png',S/'may_list_after_april.png')
same(S/'april_list_readable.png',S/'april_list_return.png')
same(S/'chart_title_before.png',S/'april_title_after.png')
assert 'PASS all 143 April cells in all/none/mixed read fixtures' in probe['log']
assert 'PASS all 146 April events in read/unread fixtures' in probe['log']
assert any('DIALOG april_stage' in line for line in probe['log'])
stats={}
for line in probe['log']:
    match=re.search(r'SUMMARY E(\d+) lines=(\d+) height=(\d+)',line)
    if match:stats[int(match[1])]=dict(lines=int(match[2]),board_height=int(match[3]))
ids=L.readj(O/'design/scope.json')['april_event_ids']
assert set(stats)==set(ids) and len(stats)==146
assert max(v['lines'] for v in stats.values())<=5
assert max(v['board_height'] for v in stats.values())<=680
summaries=L.readj(O/'design/summaries.json');sources=L.readj(O/'source/scenarios.json')
qa=L.readj(E/'semantic_qa.json')
assert qa['reviewed_events']==146 and qa['reviewed_japanese_messages']==7049 and not qa['unresolved']
assert qa['source_sha256']==L.sha(O/'source/scenarios.json')
assert qa['summary_sha256']==man['summary_source_sha256']==L.sha(O/'design/summaries.json')
assert {r['no'] for r in summaries['events']}==set(ids)
assert len({r['summary'] for r in summaries['events']})==146
assert all(r['status']=='source_qa_pass' and r['summary'].strip() for r in summaries['events'])
for src in sources['events']:
    row=next(r for r in summaries['events'] if r['no']==src['no'])
    assert row['source_event_sha256']==hashlib.sha256(json.dumps(src,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
report=dict(status='APRIL_SUMMARIES_NATIVE_PREVIEW_PASS_NOT_INSTALLED',candidate_sha256=probe['candidate_sha256'],
    summaries=146,source_japanese_messages=7049,april_list_cells=143,list_fixture_states=['all read','none read','mixed'],
    detail_events=146,detail_fixture_states=['read','unread'],native_summary_stats=stats,
    summary_max_lines=max(v['lines'] for v in stats.values()),board_max_height=max(v['board_height'] for v in stats.values()),
    summary_characters_exact=True,unread_summary_hidden_even_unlocked=True,fields_and_portraits_preserved=True,
    protagonist_retained=True,names_centered=True,group_first_scene_only=True,scene_picker_native_cancel=True,
    baseline_pixel_exact=comparisons,april_may_transition_clean=True,title_return_pixel_exact=True,
    original_code_and_strings_prefix_preserved=True,scenario_messages_unchanged=True,save_schema_unchanged=True,dll_unchanged=True,
    live_build_unchanged=True,user_files_changed=[],pid=probe['pid'],audio=probe['audio'],translator_model='Codex internal',author='/root',
    limitations=['April-only private native preview; not installed.','Read states are controlled test fixtures, not the user completion rate.',
                 'Scenario replay logic is unchanged and was not replayed end-to-end in this UI test.',
                 'Pre-existing date and cast metadata was preserved, not reauthored by this summary batch.'])
L.writej(O/'verification.json',report)
for name in ['build_calendar_april_summary_20260929.py','probe_calendar_april_summary_20260929.py',
             'verify_calendar_april_summary_20260929.py','calendar_april_summaries_20260929.py','probe_calendar_april_summary_20260929.jaf']:
    shutil.copy2(H/name,O/'source'/name)
man['status']=report['status'];man['verification_sha256']=L.sha(O/'verification.json');L.writej(O/'candidate/manifest.json',man)
scope=L.readj(O/'design/scope.json');scope.update(scope='April detail summary addition over frozen April readability candidate',new_summaries=ids)
L.writej(O/'design/scope.json',scope)
L.writej(O/'design/progress.json',dict(status=report['status'],translator_model='Codex internal',author='/root',total=146,
    completed_ids=ids,remaining_ids=[],candidate_sha256=probe['candidate_sha256'],evidence=str(O/'verification.json'),
    next='Show native captures to user; installation and extension to other months require a separate request.'))
wi=R/'docs/agentic-workflow/work-items/WI-008.md';text=wi.read_text('utf-8').replace('- [ ]','- [x]')
text=text.split('## Completion report')[0]+f'''## Completion report
146/146 요약 완성. 일본어 원문 7,049메시지 대조 및 독립 읽기 전용 QA 완료. E01506의 철야 단정을 늦게 잠듦으로 수정.
4월 상세 오른쪽 기존 정보 아래 줄거리 추가. 장면 묶음은 첫 장면 줄거리로 구분. 최대 {report['summary_max_lines']}줄, 보드 최대 {report['board_max_height']}px.
무음 private native: 143칸 × 3상태, 146상세 × 감상/미감상, 요약 글자 보존/경계/미열람 숨김, 장면 선택창 취소 통과.
4월 목록·미열람 보드·5월 목록/상세 픽셀 동일. 실제 게임/사용자 저장 무변경. 미설치, 사용자 화면 확인 대기.
후보: {O/'candidate/NightRemaster.ain'} ({probe['candidate_sha256']})
검증: {O/'verification.json'}
원문/요약: {O/'source/scenarios.json'}, {O/'design/summaries.json'}
인게임 화면: {S}
재현: source/의 build → probe → verify Python 스크립트. 마지막 정적 검증과 실행 검증은 이 후보 해시에 결합.
변경: KR_P29Board의 호출 대상 및 KR_AS29 표시 함수 4개 추가. CODE/STR prefix, MSG 전체, 저장 구조, DLL 보존.
남음: 사용자 디자인 확인 후 실제 설치 또는 다른 달 확대 여부 결정. 실제 시나리오 재생 완주 검증은 이번 UI 검증 범위 밖.
'''
wi.write_text(text,'utf-8')
now=datetime.datetime.now().astimezone().isoformat()
note=f'''\n\n### {now} — WI-008 4월 146개 요약 인게임 완성 / 미설치
- Codex internal 직접 작성, 일본어 7,049메시지 원문 대조. 읽기 전용 독립 QA 1건(E01506 철야 단정) 수정.
- 기존 오른쪽 정보 아래 줄거리. 묶음은 첫 장면만, 미열람은 전체 개방 상태에서도 숨김. 짧은 장면은 내용에 맞춰 짧게.
- 무음 native 143칸 × 3상태, 146상세 × 감상/미감상, 최대 {report['summary_max_lines']}줄 / {report['board_max_height']}px. 글자 보존 및 버튼/정보/초상 경계 통과.
- 4월 목록/미열람 상세/장면 고르기/5월 목록·상세 픽셀 동일. 타이틀 복귀·실제 저장 무변경.
- 후보 {probe['candidate_sha256']}; 검증 {O/'verification.json'}; 화면 {S}.
- 남음: 사용자 디자인 확인. 실제 설치/다른 달은 이번 범위 밖, 원작 시나리오와 저장 스키마 무변경.
'''
for p in [R/'progress.md',R/'docs/agentic-workflow/05-progress-log.md']:
    with p.open('a',encoding='utf-8') as f:f.write(note)
print(json.dumps({k:v for k,v in report.items() if k!='native_summary_stats'},ensure_ascii=False,indent=2))
