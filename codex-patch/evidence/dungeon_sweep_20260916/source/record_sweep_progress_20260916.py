"""Reconcile the existing workflow at the completed implementation boundary."""
from pathlib import Path
import json,datetime,subprocess,sys,shutil
from cheat_support_20260915 import R,savej
O=Path('dungeon_skip_20260916');D=R/'docs/agentic-workflow';now=datetime.datetime.now().astimezone().isoformat()
def append(path,text):path.write_text(path.read_text(encoding='utf8')+'\n\n'+text+'\n',encoding='utf8')
def main():
 ev=json.loads((O/'build_evidence.json').read_text());qa=json.loads((O/'verification.json').read_text());assert qa['files']==ev['files']
 policy=json.loads((O/'reward-policy.json').read_text());savej(D/'evidence/reward-policy.json',policy)
 for file in ['build_evidence.json','verification.json','release_checks.json','independent_review.json','scan_report.json','transaction_verification.json']:
  shutil.copy2(O/file,D/'evidence'/('sweep-'+file))
 decision='''## DEC-008 — 일반 던전 소탕 구현/시험 적용 경계 (2026-09-16)
- 사용자가 설계 후 제작과 적용을 명시적으로 승인했다. WI-001~004는 한 후보의 연속 구현/검수로 진행하되, **implemented와accepted를 구별**한다. 최신 빌드 시험 적용은 기능 전체 합격 선언이 아니다.
- 정책: 현재 일반 층, 잔여시간R(raw calendar units), B=floor(R/40), H=floor(R/200); 200공유예산당 전투5회+상자1개로 가정했다. 측정된 전투 소요시간/실제 무한 던전 총보상이라고 주장하지 않는다. R<40 최소지급 없음. 1일 최대25회/5개. 상세 evidence/reward-policy.json.
- 원작 placement/Settle/Chest 함수를 재사용하되, 소탕 중에만 보상 UI·AddExp UI를 억제하고 별도 RNG를 사용한다. 원래 배율과 상한은 원작 코드에서 한 번 적용한다.
- 원자성의 정확한 범위: 반환값으로 감지한 실패는 모든 보상 대상 scalar/array원소를 깊게 저장한 snapshot으로 복구한다. 치명적인 VM Ref/프로세스 종료는 엔진에서 예외로 잡을 수 없다. 그 상황까지 무오류/자동복구를 보장하지 않는다. 반영 도중 저장·UI yield 없고 사용자 디스크 세이브를 쓰지 않는다.
- flag99는 전용tag20260916과 음수 transient private RNG로 재사용; 기존owner84 검증, reset/load에서 transient회수. 저장스키마/변수명/기존문자열 변경 없음. 별도 신규직렬화 전역을 추가하지 않는다.
- 확인/결과창의 실제 전역Config 재진입 경로가 발견되어 DisableConfig를 기존값 보존→잠금→복원한다. Confirm로컬Wait가 이동/전투/503 재생성/던전Load콜백을 실행하지 않음을 원작코드에서 추적했다.
- 소탕 후 AdvanceRemainTime→기존Run 종료→정상DayEnd 경로 사용. 직접날짜증가/두 번째FixedIncome 호출 없음. 실제 다음날 화면과 실제 지급 차등/성능은 WI-004 사용자 검증에 남긴다.
- UI: 모드 탭 소탕, 일반 지도 자동 소탕, 취소 우선. 원본 native CG5상태를138px로표시하되 한글은1:1별도레이어, root는투명hit검출/cursor통과. 글리프폭으로중앙정렬. 결과6초 timed nativeMessageDialog이며 기존 고장난loot알림과 무관하다.
'''
 if '## DEC-008' not in (D/'01-design-decisions.md').read_text(encoding='utf8'):append(D/'01-design-decisions.md',decision)
 for file in ['00-project-brief.md','03-design-notes.md']:
  append(D/file,f'## {now[:10]} 구현 경계 확정\n현재 상태와 원자성/정산 계수의 정확한 범위는 DEC-008 및 evidence/reward-policy.json이 우선한다. 일반80층만 허용한다. 최신본 시험 적용까지 승인됨. native gameplay/실제 저장재독해/성능 합격은 아직 아니다. 진행 중 고정 프레임은 현재 던전 화면이며 별도 진행률 UI는 추가하지 않았다.')
 plan=D/'02-implementation-plan.md';s=plan.read_text(encoding='utf8').replace('현재 요청은 **설계**다. 아래 항목은 모두 planned이며 실행 승인이나 구현 완료를 뜻하지 않는다.','현재 요청은 **구현 및 최신 빌드 시험 적용**이다. 구현 증거를 기록했고 실제 게임 합격은 아직 남아 있다.').replace('활성 항목만 구현하고 검토 accepted 이후 다음으로 넘어간다.','DEC-008의 명시적 시험 적용 승인에 따라 WI-001~004 구현을 한 후보로 묶었다. 실제 검증 전 accepted로 올리지 않는다.');plan.write_text(s,encoding='utf8')
 tool=Path('P:/AI/Codex/skills/project-command-center/scripts/workflow.py')
 state=json.loads((D/'workflow-state.json').read_text())
 for item in state['work_items']:
  id=item['id'];status=item['status']
  if status=='planned':subprocess.run([sys.executable,str(tool),'set-status','--project-root',str(R),id,'--status','in-progress','--summary','명시적 제작/적용 승인에 따른 통합 구현'],check=True);status='in-progress'
  if id!='WI-004' and status=='in-progress':subprocess.run([sys.executable,str(tool),'set-status','--project-root',str(R),id,'--status','implemented','--summary','구현/정적 검수 완료; native acceptance pending'],check=True)
  p=D/'work-items'/f'{id}.md';s=p.read_text(encoding='utf8');s=s.replace('아직 구현하지 않았다. 구현 후 변경 파일·판단·검증 명령/결과·각 합격 기준 증거·이탈·남은 위험을 기록하고 implemented로 바꾼다. 검토 없이 accepted로 올리지 않는다.','구현 증거: evidence/sweep-build_evidence.json, sweep-verification.json, sweep-release_checks.json, sweep-independent_review.json. 상세 변경/판단은 DEC-008. 실제 게임 acceptance 미완료. 이 아래 최신 배치 보고를 따른다.');p.write_text(s,encoding='utf8')
  append(p,f'### {now} 통합 배치 보고\n- 파일: build_dungeon_sweep_20260916.py, sweep_helpers.jaf; 최종 AIN/PACT 해시는 evidence/sweep-build_evidence.json.\n- 검증 명령: verify_dungeon_sweep_20260916.py / sweep_release_checks_20260916.py / publish_dungeon_sweep_20260916.py --fixture / scan_dungeon_sweep_final_20260916.ps1. 모두 성공.\n- completed: scope10002IDs, scalar snapshot895fixture, privateRNG4000, quietEXP36, 시간경계11, 실패복구7, 취소·중복·변경검출·모달잠금·timeout cleanup. 원본 switch/globals/structures와14nestedlambda,185PACTentry 보존.\n- 한계: native settlement/chest/UI/HLL은 fixture경계, 실제 게임 수치 차등·상한·성능·다음날·재독해 아직 미실행. 이 기준은 체크 완료/accepted 처리하지 않는다.\n- 다음: WI-004의 단일 게임 검증. 게임 실행/조작을 이 보고에서 수행했다고 주장하지 않는다.')
 append(D/'04-verification-plan.md','## 현재 실행 증거와 남은 검사\n자동 검사는 evidence/sweep-verification.json과release_checks,独立review,Defender,transactionfixture. 모의 payout 경계로 네이티브 동등성을 대신하지 않는다. 사용자 단일검사: 기존 일반던전세이브→모드소탕ON→버튼→취소시무변경→실행→실제보상/레벨→다음날정상진입, 스토리에서는버튼없음. OFF/재실행/기존세이브로드와 실제2초목표도 확인 필요.')
 append(D/'05-progress-log.md',f'## {now} 소탕 구현 및 정적 검수 완료\nDEC-008과evidence를동결했다. UI geometry/Config재진입/nativeopcode/refarray0레벨 미가입인물 문제를수정했다. WI001~003implemented,WI004시험설치진행;accepted아님. 최초게임검증과순차native수치비교·성능은남음.')
 subprocess.run([sys.executable,str(tool),'validate','--project-root',str(R)],check=True)
if __name__=='__main__':main()
