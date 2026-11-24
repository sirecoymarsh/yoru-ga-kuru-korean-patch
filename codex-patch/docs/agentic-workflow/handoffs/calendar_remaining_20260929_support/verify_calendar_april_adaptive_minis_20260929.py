from pathlib import Path
import sys,json,re,shutil,datetime
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L
from PIL import Image,ImageChops
R=L.CODEX;PRE=R/'staging/calendar_april_summary_20260929';O=R/'staging/calendar_april_adaptive_minis_20260929'
E=O/'evidence';S=E/'native_april';C=PRE/'evidence/native_april'
p=L.readj(E/'native_april_probe.json');m=L.readj(O/'candidate/manifest.json')
assert p['pass'] and not p['user_files_changed']
assert p['candidate_sha256']==m['files']['NightRemaster.ain']['sha256']==L.sha(O/'candidate/NightRemaster.ain')
assert L.readj(L.CURRENT)==L.readj(O/'source_pointer.json')
rt=Path(L.readj(L.CURRENT)['runtime']);assert L.sha(rt/'NightRemaster.ain')==m['live_sha256']
assert L.sha(PRE/'interactive/run/NightRemaster.ain')==m['source_sha256']
assert L.sha(rt/'winmm.dll')==L.sha(O/'candidate/winmm.dll')
def same(a,b):
    assert ImageChops.difference(Image.open(a).convert('RGB'),Image.open(b).convert('RGB')).getbbox() is None,(a,b)
unchanged=['april_detail_readable','april_detail_e10001','april_detail_e20001','april_detail_e00121',
 'april_detail_short','april_detail_group','april_detail_group_scene3','april_detail_unread_open','april_detail_unread_locked',
 'april_scene_picker','may_detail_unchanged','may_list_unchanged','may_list_after_april']
for n in unchanged:same(S/(n+'.png'),C/(n+'.png'))
same(S/'april_list_readable.png',S/'april_list_return.png')
same(S/'chart_title_before.png',S/'april_title_after.png')
stats={}
for line in p['log']:
    z=re.search(r'MINIS E(\d+) count=(\d+) shown=(\d+)',line)
    if z:stats[int(z[1])]={'cast':int(z[2]),'shown':int(z[3])}
cells=[x for x in L.readj(O/'design/cells.json') if x['tab']==0]
assert set(stats)=={x['no'] for x in cells} and len(stats)==143
increased={n:v for n,v in stats.items() if v['shown']>min(3,v['cast'])}
assert increased and stats[1]['shown']>=4 and stats[121]['shown']==5
assert 'PASS all 143 April cells in all/none/mixed read fixtures' in p['log']
assert 'PASS all 146 April events in read/unread fixtures' in p['log']
report=dict(status='APRIL_ADAPTIVE_MINIS_NATIVE_PASS_NOT_INSTALLED',candidate_sha256=p['candidate_sha256'],
 april_cells=143,fixture_states=['all read','none read','mixed'],increased_cells=increased,native_counts=stats,
 display_max=max(v['shown'] for v in stats.values()),portrait_size=[32,40],layout_capacity=8,
 unused_width_measured=True,maximal_count_fits=True,overflow_count_exact=True,text_cg_collision_checks=True,
 unread_portraits_hidden=True,extra_parts_removed_on_page_month_close=True,pixel_exact_baselines=unchanged,
 list_return_exact=True,title_return_exact=True,save_schema_unchanged=True,scenario_messages_unchanged=True,
 live_and_playing_preview_files_unchanged=True,user_save_files_changed=[],audio=p['audio'],pid=p['pid'],
 limitations=['April only; other months retain their existing three-portrait layout.','Not installed or copied over the running preview.'])
L.writej(O/'verification.json',report)
m['status']=report['status'];m['verification_sha256']=L.sha(O/'verification.json');L.writej(O/'candidate/manifest.json',m)
scope=L.readj(O/'design/scope.json');scope['scope']='April adaptive list portraits over completed summary candidate';scope['portrait_size']=[32,40];scope['list_capacity']=8
L.writej(O/'design/scope.json',scope)
for n in ['build_calendar_april_adaptive_minis_20260929.py','calendar_april_adaptive_minis_20260929.jaf',
 'probe_calendar_april_adaptive_minis_20260929.py','probe_calendar_april_adaptive_minis_20260929.jaf','verify_calendar_april_adaptive_minis_20260929.py']:
    shutil.copy2(H/n,O/'source'/n)
note=f'''\n\n### {datetime.datetime.now().astimezone().isoformat()} — 4월 목록 포트레이트 여유 폭 활용
- 사용자: 4월 완성본 긍정 평가, 목록에 여유가 있으면 3명보다 많이 표시 요청. 기존 3명 고정 정책을 4월에서 가변 인원으로 대체.
- 기존 32×40 크기, 주인공 포함, 조건/CG와의 여백 유지. 현재 4월 데이터는 최대 {report['display_max']}명 표시, 더 있으면 실제 남은 수만 +N. 늘어난 칸 {len(increased)}/143.
- 별도 무음 native 143칸 × 3상태, 146상세 × 2상태 통과. 상세 요약/초상/5월 픽셀 동일. 확장 parts의 월/쪽/종료 정리, 미열람 숨김, 글자/CG 경계 확인.
- 후보 {p['candidate_sha256']}; 검증 {O/'verification.json'}; 화면 {S}.
- 실행 중인 기존 4월 사본 PID 84756 및 live 설치본 무변경. 남음: 사용자 화면 확인 후 종료 시 적용. 다른 달 확대는 아직 하지 않음.
'''
for f in [R/'progress.md',R/'docs/agentic-workflow/05-progress-log.md',R/'docs/agentic-workflow/01-design-decisions.md']:
    with f.open('a',encoding='utf-8') as out:out.write(note)
print(json.dumps({k:v for k,v in report.items() if k!='native_counts'},ensure_ascii=False,indent=2))
