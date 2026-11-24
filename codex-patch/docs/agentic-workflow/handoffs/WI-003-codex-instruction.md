# Codex instruction — WI-003: 보상 일괄 처리와 하루 종료 연결

프로젝트: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908
설계 문서: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow
선행 accepted 필요: WI-002. 현재는 planned이며 이 문서 생성은 구현 승인이 아니다.

먼저 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\00-project-brief.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\01-design-decisions.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\03-design-notes.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\04-verification-plan.md, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\work-items\WI-003.md 및 프로젝트 progress.md/current.json을 읽는다.

목표/범위: 동결된 환산 정책, 계획·사전검증·순차 원작 지급, 중복 잠금/오류 복구, 실제 결과 UI, 정상 잔여시간 소진/귀환 인계.
제외: 보스 승리/이벤트 삭제/최심층 해금, 자동 세이브 덮어쓰기, 기존 순간 처치 알림 의존.
검증: 동결 정책 경계·순차 지급 차등·원자성 실패 주입·참조 소유/지원 opcode 검사. 네이티브 UI/다음 날 미검증 항목을 WI-004에 명시 인계.

사용자 확정 흐름은 소탕 토글→일반 던전 지도 버튼→취소 기본 확인창→수동 실행이다. 입장 자동 실행으로 되돌리지 않는다. 합격 기준은 작업 문서 그대로 적용한다. 설계 불가능/모순 발견 시 최소 경계에서 멈춰 설계 수정안을 기록하고 실패 검사를 약화하지 않는다. CUA/외부 번역/무단 게임 종료/실행 중 파일 교체/사용자 세이브 덮어쓰기를 하지 않는다. 보조 에이전트는 읽기 전용 검토만 수행한다.

완료 보고: implemented/partial/blocked, 생성·변경·삭제 파일, 주요 판단, 실제 실행한 검증과 증거, 합격 기준별 결과, 설계 이탈, 남은 네이티브 검증/위험. 현재 작업 번호 하나의 범위만 구현한다.
