# 클로드 인계 — 이벤트 캘린더 남은 작업

작성: 2026-09-29T19:38:42.893613+09:00. 사용자가 “나머지는 클로드에 시킬게 인계좀”이라고 요청했다. **이 문서는 인계이며 신규 게임 구현이나 클로드 실행을 한 것은 아니다.**

## 1. 지금 시작할 일

1. **WI-009:** 승인된 4월 UI를 5~11월·회상·그 밖, 그리고 달성률에서 여는 목록/상세/장면 선택 경로까지 확대한다. 새 디자인을 만들지 않는다.
2. **WI-010:** 그 UI 위에 5월 미작성 150개 장면 요약을 작성·검증한다. 기존 E00011 요약은 보존한다.
3. 이후 같은 방식으로 6월→7월→8월→9월→10월→11월→회상→그 밖을 월별/안정 ID별 배치로 진행한다. 한 번에 전체를 집필·배포하지 않는다. 다음 배치마다 기록과 근거를 남긴다.

작업 지시: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\handoffs\WI-009-codex-instruction.md` → `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\handoffs\WI-010-codex-instruction.md`. 파일명의 codex는 기존 워크플로 관례이며 이번 구현 담당은 클로드다.

## 2. 반드시 현재 설치본에서 출발

- 프로젝트: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908`
- 실제 게임: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\ui_cumulative\enemyscope_fbca7f090e72\runtime`
- 최신 포인터: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\ui_cumulative\current.json`
- AIN: `b74ebc26c77656bd927b9540769fa0b70bff1210b052167cdf22856781c256b8`
- DLL: `0df1aa37edae29a9eb878e8043779b620ba0a3de5ee450cd872a5eac9c1e495e`
- manifest: `54fd6042482905d777efa8ec1a9f7ead4714ee7ab5f52b6ab5d986477f7ca61f`
- 현재 AIN과 일치하는 meta/raw-code: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_label_particles_20260929_r2\work\build`
- 4월 통합 증거: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_april_complete_20260929`
- **그 이후 조사 수정까지 설치됨:** `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\calendar_label_particles_20260929`
- 기준과 도구 사본의 해시: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\handoffs\calendar_remaining_20260929_support\baseline_and_sources.json`

각 작업 시작 시 위 고정값과 live/current를 다시 비교한다. 값이 달라지면 새 작업이 있었던 것이므로 조사 후 재기준화한다. 옛 r24/4월 후보로 통째 덮어쓰면 후속 수정이 사라진다. 과거 `source_pointer.json`·`installed:false`·오래된 워크플로 manifest는 역사 기록이지 현재 상태가 아니다.

## 3. 확정된 디자인 — 되돌리지 말 것

- **이벤트 캘린더** 이름, 기존 월별 탭 + 12칸 격자 유지. 10월 레인 지도/서랍 HTML 시안은 **미채택**. 브라우저에서 열려 있어도 구현 기준 아님.
- 주인공은 목록·상세 모두 포함한다. 사용자 이름이 료로 고정됐다고 가정하지 말고 UI 인물 표기는 주인공을 유지한다.
- 목록 초상 **32×40**, 실제 남는 폭을 측정해서 가능한 만큼 표시. 3명 고정 아님. 4월에서는 최대 5명이 보였고 구현 상한은 8. 남는 인원은 정확한 `+N`. 날짜·조건·CG와 충돌하면 더 적게 보여도 된다.
- 상세 초상 **104×130**, 기존 원본 얼굴·표정(확정된 하이지 포함), 이름은 각 초상 아래 중앙 정렬. 인원 많은 장면은 기존 줄배치 규칙을 보존·검증한다.
- 상세 항목은 **언제 / 인물 / 열람 상태**, 필요하면 **재생 / 조건 / 장면 묶음 / 선택**. 기존 정보 삭제 금지. 항목명·값 두 열 정렬.
- 목록/선택창의 감상 상태는 **감상 완료 / 아직 보지 않음**. E00001 같은 ID는 유지. 재생 가능/잠김과 읽음은 별개다.
- 묶음은 **전체 N개 중 M개 감상**, 장면 고르기. 모든 ‘단계’가 엔딩 분기라는 해석 금지. 번호별 실제 선택 문구와 공통 합류 설명을 보존한다.
- 미열람은 **전체 개방 상태라도 인물·초상·줄거리/선택 스포일러를 숨긴다**. 전체 개방은 읽음 기록을 바꾸지 않는다.
- ‘회상 모드처럼 재생합니다 / 현재 진행 상태는 바뀌지 않습니다’ 같은 상세 안내는 다시 끼워 넣지 않는다. 코드의 재생 격리·복구 안전장치는 삭제하지 않는다.
- 요약은 원문 장면만 간결하게. 길면 화면에 맞춰 적절히 축약하며 중요한 앞 정보를 밀어내지 않는다. 4월 검증은 최대 4줄/약 509px 폭이다. 더 긴 선택·조건이 있는 다른 달에서는 실제 높이 측정 후 안전하게 줄인다.

## 4. 지금 완료된 것과 남은 것

4월 UI 143칸/146장면과 요약 146개는 설치/무음 검증 완료. E00011 요약 1개는 그전부터 존재한다. 나머지 탭에는 아직 옛 상태 기호, 고정 3인, 옛 상세 정렬/빈 요약이 남아 있다.

최신 조사 수정은 **전 탭 공통 표시 getter 596개 필드**에 적용됐다. 이즈미·쿄카·마나미·마코토·호시카와·신카이·모모세의 단독 이름 뒤 `와`만 제거. `이즈미와 촬영`, `쿄카와 동행`은 보존. 이름 호시카와 자체의 마지막 와를 지우면 안 된다. 이 수정은 전체 UI 확대 완료를 의미하지 않는다.

| 탭 | 목록 칸 | 묶음 펼친 장면 | 요약 작성 | 요약 미작성 |
|---|---:|---:|---:|---:|
| 4월 | 143 | 146 | 146 | 0 |
| 5월 | 116 | 151 | 1 | 150 |
| 6월 | 203 | 232 | 0 | 232 |
| 7월 | 56 | 106 | 0 | 106 |
| 8월 | 64 | 68 | 0 | 68 |
| 9월 | 58 | 62 | 0 | 62 |
| 10월 | 91 | 128 | 0 | 128 |
| 11월 | 71 | 158 | 0 | 158 |
| 회상 | 85 | 85 | 0 | 85 |
| 그 밖 | 28 | 28 | 0 | 28 |

합계 **915칸 / 1,164장면 / 작성 147 / 미작성 1,017**. 이는 차트 표 범위 집계이며 게임 달성률 공식이 아니다. 안정 ID 전체 목록은 `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\handoffs\calendar_remaining_20260929_support\remaining_scope.json`. 그 밖의 시스템/미사용 장면은 실제 원문을 확인해 짧은 기능 설명 또는 명시적 제외로 처리하고 서사를 꾸미지 않는다.

## 5. 구현에서 특히 조심할 부분

- `KR_CDraw → KR_AM29Draw → KR_U29Draw → KR_C24Draw`: tab==0인 4월만 상태/가변 초상 변경. 단순히 guard 하나 제거하고 끝내지 말 것.
- `KR_P29Board → KR_AS29Router → KR_AS29Board / KR_U29Router`: 4월에서만 새 상세/요약. **4월 밖의 `KR_S29Info` 선택 문맥을 덮어버리지 않도록 합쳐야 한다.**
- `KR_T9StagePage → KR_U29Stages`: 지금은 k==6 및 `KR_CActive()`에만 새 공원 선택창. 첫 4개 이름/번호를 하드코딩한 코드를 모든 묶음에 재사용하면 안 된다. CardStage/CardSize/StageEv로 일반화한다.
- `KR_CActive()`는 Open==1뿐 아니라 실제 Parts root 존재를 요구한다. 첫 조사 테스트의 fixture는 root 누락으로 옛 경로를 탔다. 수정된 probe가 KR_CDraw 후 두 경로를 각각 검증한다.
- `KR_P29DropMinis → KR_AM29Drop`: 추가 parts 2026095000+slot*20+i는 월/쪽 전환·취소·종료 시 모두 정리. 기존 mini slot4는 상태 문자이므로 함부로 제거하지 않는다.
- `KR_T19EvShort / EvHead / CardHead / CardTail → KR_N29*`: 마지막 조사 수정 exact-ID+old-text guards 유지. `KR_S29*`는 이미 선택 문맥에서 쓰는 이름이다. 새 helper prefix 중복 검사 필수.
- r19 테이블/cells.json 자체는 옛 문구를 포함한다. 런타임 wrapper 오버라이드가 최종값이다. 테이블만 다시 굽지 말고 누적 diff를 추적한다.
- cast는 explicit speaker tags 기반이다. 침묵 등장인물/익명 정체를 추측으로 추가하지 않는다.

## 6. 근거와 재사용 자료

- 편의용 스크립트 사본: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\handoffs\calendar_remaining_20260929_support`. **과거 고정 해시/출력 경로가 있으므로 그대로 실행하지 말고 새 staging에서 참고하여 적용**. 필수 assert를 지워 억지 통과시키지 말 것.
- 4월 UI readable JAF: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_readability_20260929\work\build\helpers_readable.jaf`
- 4월 요약/상세: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_summary_20260929\work\build\helpers_readable.jaf`
- 4월 요약 원문 묶음: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_summary_20260929\source\scenarios.json` 및 같은 폴더 E번호별 txt
- 승인 요약: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_summary_20260929\design\summaries.json`
- 선택 문맥 원문·표: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_choice_context_20260929\design\label_patch.json` 및 `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_choices_20260929\design\label_patch.json`
- 전체 사건/분기/원본 위치: `P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\graph\schedule.json`, `P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\graph\groups.json`, `P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\graph\inputs.json`
- cast/cells: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_adaptive_minis_20260929\design`
- 최신 조사 수정 readable JAF/표/probe: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_label_particles_20260929_r2`
- build/probe 공통 라이브러리: `P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r24_chart\r24lib.py`, `P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r24_chart\probe_chart_r24.py` (read-only reference)
- Python: `P:/AI/forge/venv/Scripts/python.exe`. `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`. `L.read_meta`로 메타 읽기(CP932 surrogate bytes 보존).

## 7. 세이브/게임 보호 및 검증 계약

1. 수정은 별도 P드라이브 staging. 게임 실행 중 live 교체나 강제 종료 금지. 설치 직전 경로 기준 프로세스 종료 확인; 필요하면 사용자에게 저장·종료 요청.
2. 진단은 **무음**, private save folder 사용. 기존 probe/setup_folder가 이 계약을 갖는다. probe용 강제 읽음/자동클릭/종료코드 AIN을 live로 설치하지 않는다.
3. 최신 AIN 원본 CODE prefix/STR prefix/MSG를 보존하는 append-only 및 좁은 display leaf 변경. globals/struct/save schema, 주소 고정 함수/복귀 주소 불변. 최근 검사 **51개 resume save / 1,256개 frame**, 설치 당시 전체500파일 무변경; 다음에는 재집계.
4. `required_*.json` 누적 계약(현재87개)과 manifest/latest_worked_translation/current를 보존·갱신. 최신 publisher의 stop/hash/transaction gates 참고. 실행 중인 세이브 상태를 테스트용으로 복사해 원본에 덮어쓰지 않는다.
5. native 검증: 모든 칸, 읽음/미읽음/일부/잠김/전체개방, 많은 인물, 긴 조건/실제 선택, 다쪽 묶음, 상세→취소→목록 복귀, 달성률/캘린더 양쪽, parts 누수, 대표 재생 및 타이틀/거점 복귀. 화면·PID·후보해시를 연결한다.
6. 검증 범위를 정확히 보고. UI 테스트를 전 엔딩 완주로 부르지 않는다. 변경 없는 4월 회귀도 비교한다. 검수 후 설치/복구/중간 실패/변조 거부 fixture, Defender, 설치 전외부백업, 설치후해시확인.
7. 원본/번역 품질 권위는 `P:/AI/Codex/AGENTS.md`와 `P:/AI/Codex/skills/contextual-game-localization/references/translation-quality.md`. 사용자가 이번 작업을 **클로드에 명시적으로 인계**했다. 신규 클로드 집필물은 실제 모델/작성자 provenance로 기록하고 Codex internal로 위장하지 않는다. 기존 Codex 작성 요약의 provenance는 유지한다. 외부 MT 자동 대체 금지.

## 8. 완료 보고

각 배치에서 완료 ID/남은 ID, 수정 파일, 전후 AIN/manifest 해시, 원문 근거·집필자, native 캡처, 미열람 보호, 세이브 회귀, 설치 여부·백업·복구를 보고한다. 구현은 implemented로 기록하고 검수 없이 accepted로 올리지 않는다.

현재 요청 범위 밖: 던전 자동 탐색/전투 재설계, 세이브 UI/진행률 산식 변경, 부실 족자(사용자 취소), 페이트 엑스트라 화면 문제, 지도형 시안 재추진. 이번 인계에서 게임 파일은 변경하지 않는다.
