# Codex instruction — WI-001: 소탕 보상 환산과 정상 하루 종료 경로 확정

프로젝트: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908
설계 문서: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow
선행 accepted 필요: 없음. 현재는 planned이며 이 문서 생성은 구현 승인이 아니다.

먼저 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\00-project-brief.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\01-design-decisions.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\03-design-notes.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\04-verification-plan.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\work-items\WI-001.md 및 프로젝트 progress.md/current.json을 읽는다.

목표/범위: 환산 정책(공유 시간 예산/현재 층/반올림), 일반/스토리 판정(DEC-007; IsTrainingDungeon을 잘못 제외하지 않음), UI 이벤트 경로, 공통 옵션 저장 위치, 원자적 보상 반영 계약과 정상 귀환 이후 다음 날 호출 경로.
제외: 실제 보상 지급, 사용자 세이브/런타임 교체, 디자인 확장, 알림 버그 수정.
검증: 기존 dungeon_skip_20260916/original_*.jam, 최신 AIN/PACT/EX 읽기, reward-policy.json 및 guard/side-effect/transition 증거 작성. 필요 실험은 격리하고 사용자 세이브에 적용하지 않는다.

사용자 확정 흐름은 소탕 토글→일반 던전 지도 버튼→취소 기본 확인창→수동 실행이다. 입장 자동 실행으로 되돌리지 않는다. 합격 기준은 작업 문서 그대로 적용한다. 설계 불가능/모순 발견 시 최소 경계에서 멈춰 설계 수정안을 기록하고 실패 검사를 약화하지 않는다. CUA/외부 번역/무단 게임 종료/실행 중 파일 교체/사용자 세이브 덮어쓰기를 하지 않는다. 보조 에이전트는 읽기 전용 검토만 수행한다.

완료 보고: implemented/partial/blocked, 생성·변경·삭제 파일, 주요 판단, 실제 실행한 검증과 증거, 합격 기준별 결과, 설계 이탈, 남은 네이티브 검증/위험. 현재 작업 번호 하나의 범위만 구현한다.
