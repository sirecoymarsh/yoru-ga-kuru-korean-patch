# Review 01 — WI-008: 4월 이벤트 146개 요약과 인게임 상세 완성

- **Reviewed at:** 2026-09-29T18:12:12+09:00
- **Verdict:** accepted
- **Artifact/commit range:** P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_april_complete_20260929\completion_audit.json
- **Work item:** `../work-items/WI-008.md`

## Summary

146개 일본어 원문 근거 요약의 QA, 모든 상세 경계/숨김 및 실제 설치 해시와 백업을 확인했다. 가변 목록 초상도 통합되어 있다.

## Checks performed

실행한 명령: build/probe/verify_calendar_april_readability_20260929.py, build/probe/verify_calendar_april_summary_20260929.py, build/probe/verify_calendar_april_adaptive_minis_20260929.py, preflight_calendar_april_install_20260929.py, scan_calendar_april_install_20260929.ps1, publish_calendar_april_complete_20260929.py, audit_calendar_april_installed_20260929.py.
검토한 실제 파일: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_april_complete_20260929\completion_audit.json, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_april_complete_20260929\startup_report.json. 소스, native 로그, 캡처, 실제 실행 AIN을 해시로 결합했다.

## Findings

- No findings.

## Acceptance-criterion matrix

- PASS — 146/146 요약에 실제 원문 메시지 ID 연결; 7,049개 원문 메시지 독립 대조, 경미한 E01506 의미 강화 수정.
- PASS — E00004는 첫 장면만 요약, 묶음 전체로 표시하지 않음.
- PASS — 기존 상세 인물/필드/재생 유지, 모든 요약 최대 4줄 및 보드 최대 509px.
- PASS — 읽기/미읽기 전환에서 요약 parts와 초상 잔상 없음, 전체 개방도 미열람 요약 숨김.
- PASS — 4월 146상세×2상태 및 143칸×3상태, 목록/5월/복귀 비교. 적응형 목록 외 상세는 기존 완성본과 픽셀 동일.

## Correction instruction

None.

## Residual risks

다른 달 확대, 원작 시나리오 변경, 전 루트 재생 완주는 이번 4월 UI 범위 밖이다. native 읽음 기록은 검증용 fixture였으며 설치된 AIN에는 진단 코드나 강제 읽음이 없다. 실제 실행 보고는 정상 게임 창 준비만 확인하며 전 루트 실행 성공으로 해석하지 않는다.
