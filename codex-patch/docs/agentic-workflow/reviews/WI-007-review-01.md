# Review 01 — WI-007: 4월 이벤트 캘린더 직관적 표기 시안

- **Reviewed at:** 2026-09-29T18:12:12+09:00
- **Verdict:** accepted
- **Artifact/commit range:** P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_april_complete_20260929\completion_audit.json
- **Work item:** `../work-items/WI-007.md`

## Summary

사용자가 확인한 4월 UI를 기준으로 네이티브 전 칸/상세, 미열람, 페이지·월·종료 정리와 설치 일치를 확인했다.

## Checks performed

실행한 명령: build/probe/verify_calendar_april_readability_20260929.py, build/probe/verify_calendar_april_summary_20260929.py, build/probe/verify_calendar_april_adaptive_minis_20260929.py, preflight_calendar_april_install_20260929.py, scan_calendar_april_install_20260929.ps1, publish_calendar_april_complete_20260929.py, audit_calendar_april_installed_20260929.py.
검토한 실제 파일: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_april_complete_20260929\completion_audit.json, P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_april_complete_20260929\startup_report.json. 소스, native 로그, 캡처, 실제 실행 AIN을 해시로 결합했다.

## Findings

- No findings.

## Acceptance-criterion matrix

- PASS — 143칸/146상세의 E번호·날짜·인물·정보 보존: native_april_probe.json 및 상세 전후 픽셀 대조.
- PASS — 감상과 개방 상태 분리/미열람 숨김: all/none/mixed 및 unlock-all 상태 검증.
- PASS — 공원 4장면의 실제 개수와 선택창 취소: april_scene_picker.png와 DIALOG april_stage 로그.
- PASS — 경계와 중앙 정렬: 전체 상세 native 측정; 가변 목록 초상은 실제 텍스트 경계와 최대 수 검증.
- PASS — 다른 달 경로 및 화면 정리: KR_AM29Draw tab!=0 원형 전달, May 픽셀 대조, 페이지·월·종료 잔여 parts 없음.
- PASS — 별도 무음 진단 당시 원본 저장 무변경; 이후 승인된 설치에서도 494 저장 파일 그대로. publisher journal/backup 보존.

## Correction instruction

None.

## Residual risks

다른 달 확대, 원작 시나리오 변경, 전 루트 재생 완주는 이번 4월 UI 범위 밖이다. native 읽음 기록은 검증용 fixture였으며 설치된 AIN에는 진단 코드나 강제 읽음이 없다. 실제 실행 보고는 정상 게임 창 준비만 확인하며 전 루트 실행 성공으로 해석하지 않는다.
