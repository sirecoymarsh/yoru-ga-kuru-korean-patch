from pathlib import Path
import json, hashlib, shutil, datetime
R=Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922')
O=R/'staging/claude_fixes_20260928'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
ptr=json.loads((R/'ui_cumulative/current.json').read_text('utf8'))
rt=Path(ptr['runtime'])
assert sha(rt/'NightRemaster.ain')=='b5ec7f01ce25704c505f9f5eabb3f2873ab9aa1fda0d2a1b10b95102346713d3'
assert sha(rt/'winmm.dll')=='a72b1b9d386107bb6370f4ff3f0ff9bd857fbf6223e7d0b1f5399604cd64e199'
assert not (O/'source_pointer.json').exists(), 'Already prepared: reuse immutable source'
for d in ['source','hook','candidate','work','evidence']: (O/d).mkdir(parents=True,exist_ok=True)
(O/'source_pointer.json').write_text(json.dumps(ptr,ensure_ascii=False,indent=2),'utf8')
for n in ['NightRemaster.ain','winmm.dll']: shutil.copy2(rt/n,O/'source'/n)
for p in (F/'hook_modmenu/src').iterdir():
    if p.is_file(): shutil.copy2(p,O/'hook'/p.name)
for n in ['candidate_meta.json','candidate_raw_code.jam']: shutil.copy2(F/'ingame/r24_chart/work/build'/n,O/'source'/('r24_'+n))
shutil.copy2(F/'ingame/r24_chart/candidate/NightRemaster.ain',O/'source/r24.ain')
assert sha(O/'source/r24.ain')=='939e44d03aa87da36613abf6b06a304c45060b700cfcf99bd4d34a8f02535155'
(O/'source_hashes.json').write_text(json.dumps({p.name:sha(p) for p in (O/'source').iterdir()},indent=2),'utf8')
with (R/'progress.md').open('a',encoding='utf8') as f:
    f.write('\n### 2026-09-28 Claude 검수 지적 F01~F04 수정 — Codex internal, IN_PROGRESS\n- 설치 r23과 미설치 r24 후보를 staging/claude_fixes_20260928/source에 해시 고정. 기존 달력/모드/친밀도/자동탐색 유지.\n- 범위: F01/F04 전역 기록 리셋·복원 트랜잭션, F02 재생 중 저장/복귀 안전성, F03 본거지 차트 레이어 및 r24 마무리. 설치·사용자 저장은 아직 변경하지 않음.\n')
print(O)
