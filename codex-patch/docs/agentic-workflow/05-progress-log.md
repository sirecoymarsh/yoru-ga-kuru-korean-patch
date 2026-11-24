# Progress log

- 2026-09-16T00:36:20+09:00 — Workflow initialized for **밤이 온다 — 일반 던전 소탕 기능**; design state is draft.
- 2026-09-16T00:36:20+09:00 — WI-001 planned — 소탕 보상 환산과 정상 하루 종료 경로 확정
- 2026-09-16T00:36:20+09:00 — WI-002 planned — 모드 토글와 지도 버튼 및 확인창
- 2026-09-16T00:36:20+09:00 — WI-003 planned — 보상 일괄 처리와 하루 종료 연결
- 2026-09-16T00:36:21+09:00 — WI-004 planned — 최신 빌드 통합 및 게임 내 검증

## 2026-09-16T00:42:10+09:00 — 소탕 설계 v1
사용자 경험은 확정: 토글 소탕/지도 자동 소탕/경고 후 수동 실행. 입장 즉시 실행안 폐기. 기술 설계와 WI-001~004 작성; 모두 planned. 환산 계수·원작 다음 날 인계·설정 저장 위치·원자적 지급 경계는 WI-001에서 확정할 기술 게이트다. 게임/세이브/설정/프로세스 변경 없음. 기존 알림 버그 조사는 중단 상태 유지.

- 2026-09-16T00:44:42+09:00 — 읽기 전용 독립 설계 검토: 승인 UX 충돌 없음. 파티 유효성/행동 가능 인원과 SettleOnlyMonsAtb 부수효과 감사 항목 보완. workflow validation 0 errors/0 warnings; 모든 WI planned, 기술 게이트는 WI-001 pending. 게임 관련 6개 보호 파일 해시 동일.
- 2026-09-16T00:47:51+09:00 — WI-001 status planned -> in-progress — User approved starting the sweep work; inspect time/reward/return contracts without changing the game

## 2026-09-16T01:02:37+09:00 — WI-001 부분 완료: 일반 던전 한정 조건 고정
사용자 스토리 던전 제외 지시를 DEC-007/FR-002에 반영했다. 기존 Training 명칭 오독 정정. EX118개 전체 분류: 일반80, 스토리36, 특수종점2 차단. 1110의 map11 예외와 현재 층 ID 매칭을 코드로 확인했으며, 이벤트 객체 null 실검사를 유지한다. 정상 시간0 귀환→다음 날 상위 호출을 추적했다. 독립 읽기 전용 검토도 이 두 결론 확인. scope_contract.py 162개 정적 설계 모델 테스트 통과. 실제 UI/게임 실행 검증은 아니다.
WI-001은 in-progress 유지. 남은 필수 게이트: 시간 환산 계수/단위 동결, 전체 보상 변경 집합 및 복구 경계, UI 이벤트 ID/공통 저장 위치 충돌 감사. 새 발견: 동영상 공통 플래그 동적 접근27839는95/96/0만 반환하므로99번 후보와 충돌하지 않음(전체 슬롯 감사 완료를 뜻하지 않음).
현재 pointer/manifest/AIN/PACT/EX/EXE 6개 보호 파일 해시 동일. 게임·세이브·설정·프로세스 수정 없음. 중단했던 즉시처치 알림 조사 재개하지 않음. 다음 실행 단계는 기존 original_26258/26259/27187~27191/27302와 원본 시간 비용을 대상으로 보상/복구 계약을 마무리하는 것이다.

- 2026-09-16 — scope_contract 독립 읽기 전용 검토 통과: 162개 증거 수/소스 해시, 일반80 목록, 취소/층 이동/현재ID·지도·씬 세대·파티·배율 변경 차단 확인. 범위 판정 모델만 검증했으며 원자성/중복 지급/실제 AIN·PACT 성공으로 확대하지 않는다. workflow validate: 0 errors, 0 warnings.
- 2026-09-16T01:50:05+09:00 — WI-001 status in-progress -> implemented — 구현/정적 검수 완료; native acceptance pending
- 2026-09-16T01:50:05+09:00 — WI-002 status planned -> in-progress — 명시적 제작/적용 승인에 따른 통합 구현
- 2026-09-16T01:50:05+09:00 — WI-002 status in-progress -> implemented — 구현/정적 검수 완료; native acceptance pending
- 2026-09-16T01:50:05+09:00 — WI-003 status planned -> in-progress — 명시적 제작/적용 승인에 따른 통합 구현
- 2026-09-16T01:50:05+09:00 — WI-003 status in-progress -> implemented — 구현/정적 검수 완료; native acceptance pending
- 2026-09-16T01:50:06+09:00 — WI-004 status planned -> in-progress — 명시적 제작/적용 승인에 따른 통합 구현


## 2026-09-16T01:50:05.229571+09:00 소탕 구현 및 정적 검수 완료
DEC-008과evidence를동결했다. UI geometry/Config재진입/nativeopcode/refarray0레벨 미가입인물 문제를수정했다. WI001~003implemented,WI004시험설치진행;accepted아님. 최초게임검증과순차native수치비교·성능은남음.


### 2026-09-16T01:51:44.225056+09:00 최신 빌드 시험 적용 완료
- AIN/PACT 두 파일 적용. 나머지96개 파일,192개 세이브 해시, 복구용 빌드 보존. current manifest 7edcb8961a86778d407c1b4713e60a6485afd8929a962dbc2fc34cc4d662c576.
- 롤백 journal COMMITTED. evidence/dungeon_sweep_20260916/before에 변경 전 파일 및 메타데이터 보존.
- WI-004는 실제 게임 확인을 기다리는 in-progress 상태를 유지한다. accepted/전체완료 아님. 게임 프로세스 실행·화면 조작은 수행하지 않았다.


## DEC-009 — 일반 무한 반복층 제외 오판 정정 (2026-09-16)
- 사용자 확인: 구교사 최하층1201은 일반 무한 던전. 원작 일반생성/전투/보물 경로 검토로2601도 동일 구조임을 확인. nextId=self와배치rank0을특수층근거로사용한이전판단을폐기한다.
- 허용 범위는기존80개+1201+2601=82개. 과거 scope-contract/DEC-007/008의1201·2601제외문구보다이결정이우선한다. 스토리/이벤트문맥차단과모든보상·날짜·UI동작은유지.
- 최신 AIN의31888단일함수만수정. 나머지97runtime파일과198세이브,복구용그대로. evidence/sweep-infinite-* 참조. 실제게임화면/보상검증은아직미완료.


## DEC-010 — 소탕 확인창 표현과 안내 개선 (2026-09-16T20:40:18.169577+09:00)
- Status: implemented; native UI visual acceptance pending. WI-002/WI-004.
- 사용자 화면에서 녹색 제목 배경과 다섯 줄 문구가 영역 하단을 침범함을 확인. 소탕 전용 type2026091602에서만 네이비 팔레트와 24px/4행/줄간격8/제목여백48을 사용한다. 원본 선택창의 취소·이벤트·정리 흐름과 다른 선택창은 보존한다.
- 남은 탐색 시간과 floor(R/40) 전투·floor(R/200) 상자 수를 확인창에서 명시. HP 비율/함정 시뮬레이션 방식으로 바꾸지 않는다. 경험치·훈련치·달조각 배율만 해당 원작 보상 경로에서 적용되며 동료특훈·아이템 수량 배율과 구분한다.
- AIN31892/27936만 변경. 80개 compiled confirmation fixture, shippedFNL55glyph/폭664px, native opcode, 복구/손상거부 fixture, Defender 통과. PACT/EX/EXE/FNL과 보상/날짜 함수 불변.
- 사용자 실게임 보고: 기존5429AIN으로 소탕 후 메인 스토리 정상 진입 확인. 전체 게임 또는 모든 보상/세이브 검증으로 확대 해석하지 않는다. evidence/sweep-user-story-progression-20260916.json.
- 설치 manifest 9f918dafa71449cceb264cb6c8107041bf7562f2b7a203d39f835452d1b9522f. 실제 확인창 최종 화면은 남음.


## DEC-011 — 경로 표시의 이동 중 끊김 최적화 (2026-09-16T21:02:48.507228+09:00)
- Status: implemented and installed; native performance acceptance pending. WI-004 follow-up.
- 기존31860은 좌표가 바뀔 때마다900칸 NS_AStar::MapInfo를 새로 만들고 목표마다 객체형 AStar를 실행했다. 신규 helper31907..31909는 로컬 정수 배열과 단일4방향 BFS를 사용하며 미니맵의 원래 경로 마커만 그린다.
- 동일 좌표에서는31860의 기존 캐시 경계에서 조기 반환한다.27007/27010/27025/27031은 실제 필드가 변할 때만 무효화하며 맵 바인딩/층 이동/전체 갱신/옵션/로드의 기존 무효화는 그대로다.
- native PossibleToWalk, 시작점 제외·목표 포함, 거리0목표 제외, 행 우선 동거리 목표, 백화점202/204의7:0 및203미제거0..3우선(이후4)을 보존한다. 동률의 경로 모양 자체는 다른 최단 경로가 될 수 있다.
- 152개 compiled helper 지도 fixture, 24개 setter case, 동일좌표1000회 추가탐색0, 실제 EX백화점/무작위 맵/긴 경로/단절/제거벽/시작목표 검증. 참조 해제와 큐 경계 검사, 독립 실제 후보 검토, native opcode 및 Defender/트랜잭션 fixture 통과.
- AIN 0130135eff6c1b156a76f2fa9505addae18d5b2bdbaedc27ab711a54e368ad39; manifest 9b1824dda50a9cda257f8c2f6e7003ca31c5722735ed95a76f5dc4a2f8672fb2. 번역/소탕/UI/보상·날짜 코드 및 다른97개 runtime파일, 216개 세이브와 복구용 빌드 보존.
- 다음 실행 단계: 경로ON/OFF 이동 체감, 정지·회전, 다음 층, 백화점202/203/204, 저장 후 로드 비교. 실제 FPS/프레임시간은 측정하지 않았으며 전체 프로젝트 승인으로 확대하지 않는다.


### 2026-09-16 수수께끼의 틈1(401) 경로 미표시 조사
- 사용자 미표시 보고 후 이벤트 잠금 가능성을 제시. EX의 출구(15,15)는 존재하지만 초기에는 접근 불가. native28957가 퍼즐 조건 후29175(1,4,0,0)로 벽4칸을 통로로 바꾸고 UpdateMapView를 호출한다.
- 현행013013AIN의 compiledroute를 실제401맵 두 출발점으로 검증: 잠금 전0칸, 동일 native벽 교체 후59/16칸으로 출구에 도달. 경로안내는 통행 가능한 출구 탐색이며 퍼즐풀이 안내는 아님. 사용자 실시간 이벤트 상태는 읽지 않았음.
- 게임 파일과 실행 중 프로세스는 변경하지 않았고 설치 manifest9b1824... 유지. evidence/route-401-event-lock-20260916.json.


## DEC-012 — 수수께끼의 틈 전용 퍼즐 경로 (2026-09-16T22:38:43.901578+09:00)
- Status: installed; native walkthrough pending. WI-004 follow-up only.
- 사용자 요청: 수수께끼의 틈 시리즈에서 이벤트를 강제 완료하지 않고 실제 걸어서 기믹을 해결하는 경로 안내.401/403/405만 전용 처리,402/404 및 다른 모든 맵은 기존 단일 BFS 경로를 유지한다.
-401: B1..4의 원래 방문 카운터를 읽어 미방문 지점→합계12회 충족→B5→열린 벽 너머 출구로 안내. 수동 조사로 벽을 이미 열었다면 방문 카운터보다 열린 벽 상태를 우선한다.
-403: 열린 선택 열의 올바른 지점을 순차 안내. 닫힌 열의 오답이 있으면 원작 R8 재시도 지점으로 안내한다. 재시도 도중 B7을 통과해야 하며 원작 성공 조건이 거짓이므로 무해하다. 재시도 후 답안 배열이 남아 있어도 다시 열린 열을 우선한다. 완료 후 원래 출구 안내.
-405: 활성7:0 워프 트리거를 피하고 원래6:0 보스 트리거로 안내한다. 전투/이벤트/다음날 진행 자체는 원작 처리, 강제 변경 없음.
- GetActiveScene의 native interface 반환을 읽어 현재 scene/map/view/event의 타입과 동일성을 검사한다. 참조 획득/해제를 균형 유지하고 실패 상태는 캐시하지 않는다.29176은 기존 owner 이벤트 실행 후 경로를 갱신한다. 변경된 기존 함수29176/31860, 새 함수31910..31913, 세이브/글로벌 스키마 불변.
- 후보 AIN 75d721bc318296fa1e2f4d1e4a86bd220c5d1c7977d753473bf12962b4711b07. 컴파일 코드로 기존152지도/24setter 및 퍼즐14시나리오, 실패상태16가지 검증. 같은 좌표1000갱신의 추가 지도 스캔0. native scene/delegate/event effect/render는 fixture이며 실제 게임 완주나 FPS 검증은 아니다.
- 다음 단계: 기존 경로 표시 옵션으로1/3/5층의 새 진입·중간 로드·오답 재시도·토글을 실제 플레이에서 확인.


## 2026-09-17 — 퍼즐 안내 사용자 확인 및 자동 장착 가능성 조사
- 사용자 피드백: "잘되네." 직전 실행한 퍼즐 안내 패치에 대한 동작 확인으로 기록. 확인한 층/세이브/상세 시나리오는 지정되지 않았으므로1·3·5층 전체 완주 또는 FPS 검증으로 확대하지 않는다. 적용 manifest 276c55c9dd74b55fd1a89b27e344fa1cef658d312356c0435e73e30d11afae2c.
- 새 요청은 장비/요소석 자동 장착 제작 가능성 문의. 현재 runtime/세이브 변경 없이 기존26781 아이템 재고 이동·장착·스킬 갱신,26908 무기 조합 결과 계산,26895 비용/능력 조건,28586 확정 및28587 임시 배치 회수 경로를 읽었다.
- 설계 후보: 보유물 기반 추천→능력/효과/비용 미리보기→확정. 요소석은 단순 등급 비교가 아니라 생성 무기·보정 조합을 평가해야 함. 자동 합성/구매/자원 소비나 타인 장비 이동은 기본으로 하지 않음. 아직 구현 또는 적용하지 않음.
- 2026-09-17T00:27:55+09:00 — WI-005 planned — 장비·요소석 추천과 승인 후 원작 장착 통합

## 2026-09-17 — WI-005 자동 장착 구현 시작
- 사용자 추가 승인 및 유틸리티 기준 요청 반영. 장비26781/스킬27315/가공28585–28587 독립 읽기 전용 검토 완료: 장착 전 재고 검사, 배열복제, 예약정리 주의사항 설계에 반영.
- JAF 초안 작성과 compile 통과. AIN/PACT 격리 후보 작업 중. live 설치/실제 기능 완료 아님.
- 다음: 후보 JAM bridge/ref 수명과 fixture, native opcode/PACT 검증 후 재검토·설치. 이전 퍼즐 안내와 번역/모드는 기준 빌드에서 보존.
- 2026-09-17T00:42:57+09:00 — WI-005 status planned -> in-progress — 4개 추천 기준과 원작 장착 보존 계약으로 격리 후보 구현 중
- 2026-09-17T01:05:51+09:00 — WI-005 status in-progress -> implemented — 자동 장착·요소석 추천 4기준을 현재 빌드에 적용. 최종 static/fixture/독립검토/보안/복구 검증 통과; 실제 게임 검증은 대기.

## 2026-09-17T01:05:51.684784+09:00 — WI-005 구현·설치 완료, native 검증 대기
- 사용자 유틸리티 승인까지4기준에 포함. 버튼을 누를 때만 평가하며 함정/탐색 기능 중복은 가중치 축소.
- 이전 독립검토3건(CALLMETHOD ref-int인수폭,99한도 복원,none예약set표식) 모두 수정 후 최종 정적 재검토 PASS.
- staging 최종pair와 installed exact pair 일치; 컴파일fixture/원작메타·콜백·archive allowlist/글리프·실측중앙/보안검사/복구fixture PASS.
- 설치 manifest d8661eef0afc262831887eb26a0d9feecb5ca8250b4dcdf61235911ba3835f60; 보존: 다른96runtime파일,232세이브,복구빌드.
- 근거 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\autoequip_20260917. 새 완전빌드 없음. WI-005 implemented; native UI,가공/취소,응답속도,세이브로드는 실제 게임 확인 필요.
- 다음 실행: 현재게임 시작 → 모드 자동 장착·요소석 추천 ON → 장비/무기가공 버튼에서4기준·취소·승인을 확인. 실제 증거 없이 accepted/runtime_verified로 올리지 않는다.


## 2026-09-17T01:46:09.548961+09:00 — 모드 메뉴 원작형 프레임 및 노란 글자 적용
- 사용자 요청: 소탕·자동 장착/요소석 메뉴를 원작 버튼처럼, 모드임을 구분하는 노란 글자. 원작 CG1840 프레임과 CG1500의 글자 없는 배경·양끝을 재사용했으며 래스터 수정 없음.
- normal RGB255/224/96, hover255/250/180, 비활성 원본. 진입 버튼3개의 글자도 노랑. 기능·선택값·콜백·보상·저장 스키마는 변경 없음.
- AIN27936 단독, PACT153/154/161 FontColor만. 다른 타입의 렌더링/기존 CODE/STR0/MSG1, 나머지184 PACT entry 및96 runtime파일 정확 보존.
- 60 컴파일 렌더러 fixture, 실제 긴 아이템명 너비, 독립 읽기전용 ABI/시각 검토, Defender, 설치·복구·실패 fixture PASS. proof PNG는 native CG+FNL 재구성이며 게임 캡처 아님.
- 설치 manifest 99c50a0dc3eae59b7a7f6f947aebac5c599aea34fdc69402206d34f3744ae680; 세이브240파일과 복구빌드 보존. Evidence P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\mod_menu_style_20260917.
- 다음: 실제 게임에서 소탕/자동 장착/요소석 메뉴의 진입·마우스 올림·취소·확정 확인. native_verified/accepted로 올리지 않음.
- 2026-09-29T06:12:09+09:00 — WI-006 planned — 이벤트 캘린더 월별 지도·서랍·선택 흐름


## 2026-09-29T06:32:48.315349+09:00 — WI-006 부분 시안 완료 / 전체 구현 보류
- 사용자 요청으로 전체 구현을 중단하고 10월만 작동하는 독립 시안으로 범위 축소.
- 39사건, 13서랍(52장면), 10/13 선택/합류와 10/11 선택, 우측 상세 및 미열람 숨김.
- 열람률은 시안용 예시. 사용자 게임/세이브와 연결하지 않음. 줄거리는 미작성으로 명시.
- 결과: P:\AI\Codex\visualizations\2026\09\07\01a07e30-6ebc-7ee3-b99e-a40a5c786912\event-calendar-map-preview.html
- 검증: P:\AI\Codex\visualizations\2026\09\07\01a07e30-6ebc-7ee3-b99e-a40a5c786912\event-calendar-map-preview-verification.json (5너비, 10상호작용, JS 오류 0, AIN/DLL/manifest 불변)
- 다음: 사용자 디자인 피드백. 전체 네이티브 빌드/설치 및 다른 달은 승인 전 보류.


### 2026-09-29T06:48:46.746363+09:00 기존 격자 유지 · 4월 목록에서만 주인공 제외 — 네이티브 시안 / 미설치
- 사용자 결정: 월별 레인 지도 대신 기존 격자 유지. 목록 소형 초상에서는 주인공을 제외하고 상세판에는 유지.
- 4월 143칸에만 적용한 사본. 다른 인물을 앞으로 당겨 최대 3명, +N도 주인공 제외. 상세 및 5월 목록은 이전 설치본 캡처와 픽셀 동일.
- 무음 private native 실행 PID 18472, 286개 목록 레이아웃 검증, 미열람 숨김·복귀·정리 확인. 실제 게임/세이브 무변경.
- 결과: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_minis_20260929\evidence\native_april; 검증: P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_minis_20260929\verification.json; 후보 AIN: 6147926b795dd19cb63ae77d6dc9eca4283fbf2c2520c7039c11fcf834e66adb.
- 다음: 사용자가 이 4월 시안을 승인하면 다른 달 확대 및 설치 여부를 별도로 결정. 이전 지도 시안의 전체 구현은 진행하지 않음.


### 2026-09-29T13:32:39.302049+09:00 — CALENDAR_GRID_PREIMPLEMENTATION_CHECKPOINT_20260929
- 기존 격자/주인공 포함/E번호 유지, 이름·항목 정렬, 미열람 보호를 DEC-014에 정리. 설치 완료와 4월 사본 검증, 미구현 문구/요약을 구분.
- 계획표의 폐기된 지도형 전체 구현 문구 및 WI-006 사용자 승인 대기를 최신 미채택 결정으로 정정. WI-005 상태/검수 차수 표기는 기존 JSON과만 동기화(새 합격 주장 없음).
- 전체 UI 정리의 다음 순서와 조건 기록. 이번은 점검만 수행; 게임/저장/시나리오/시안 바이너리 무변경.
- 남은 문구는 proposed; 전체 요약은 E00011 외 미작성. 다음 실행은 사람 중심 표기 4월 시안 및 전체 확대 작업의 범위 확정 후 구현.

- 2026-09-29T13:43:55+09:00 — WI-007 planned — 4월 이벤트 캘린더 직관적 표기 시안
- 2026-09-29T13:43:55+09:00 — WI-007 status planned -> in-progress — 사용자 승인: 4월만 먼저 구현·확인, 다른 달 확대와 라이브 설치는 아직 하지 않음


### 2026-09-29T14:00:35.368479+09:00 — WI-007 4월 직관적 표기 인게임 시안 / 미설치
- 목록의 △/●를 감상 완료/아직 보지 않음으로 대체. E번호·날짜·인물/초상 유지. 감상 완료 개수는 전체 개방과 분리.
- 중앙 정렬 이름 및 언제/인물/열람 상태의 두 열 유지; 재생 가능/잠김 별도. 공원 4장면은 전체 N개 중 M개 감상, 장면 고르기와 개별 E번호 유지.
- 무음 private native: 143칸 × 3읽음 상태, 146상세 × 읽음/미열람, 부분 감상/잠김/전체 개방, 실제 장면 선택창 취소, 버튼 재그리기, 5월 픽셀 동일 및 타이틀 복귀 통과.
- 후보 442c7eea651c605ce76e51b7efe24584da0059efb96d919fb85b74a0fc0df22d; 검증 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_readability_20260929\verification.json; 화면 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_readability_20260929\evidence\native_april. 실제 게임/사용자 저장 무변경.
- 남음: 사용자 디자인 확인 후 다른 달 확대 여부 결정. 이번은 시안이며 live 설치·전체 요약·실제 재생 완주 검증 아님.
- 2026-09-29T14:01:40+09:00 — WI-007 status in-progress -> implemented — 4월 전용 무음 네이티브 시안 검증 완료, 미설치·사용자 디자인 확인 대기
- 2026-09-29T14:12:19+09:00 — WI-008 planned — 4월 이벤트 146개 요약과 인게임 상세 완성
- 2026-09-29T14:20:54+09:00 — WI-008 status planned -> in-progress — 4월 146개 원문 기반 요약 작성 완료, 의미 QA 및 인게임 통합 진행


### 2026-09-29T14:32:20.135549+09:00 — WI-008 4월 146개 요약 인게임 완성 / 미설치
- Codex internal 직접 작성, 일본어 7,049메시지 원문 대조. 읽기 전용 독립 QA 1건(E01506 철야 단정) 수정.
- 기존 오른쪽 정보 아래 줄거리. 묶음은 첫 장면만, 미열람은 전체 개방 상태에서도 숨김. 짧은 장면은 내용에 맞춰 짧게.
- 무음 native 143칸 × 3상태, 146상세 × 감상/미감상, 최대 4줄 / 509px. 글자 보존 및 버튼/정보/초상 경계 통과.
- 4월 목록/미열람 상세/장면 고르기/5월 목록·상세 픽셀 동일. 타이틀 복귀·실제 저장 무변경.
- 후보 928c52bb738d57ffddce3abeeac640a18a1e686b3782c6f6308156f31fcaff38; 검증 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_summary_20260929\verification.json; 화면 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_summary_20260929\evidence\native_april.
- 남음: 사용자 디자인 확인. 실제 설치/다른 달은 이번 범위 밖, 원작 시나리오와 저장 스키마 무변경.
- 2026-09-29T14:33:16+09:00 — WI-008 status in-progress -> implemented — 4월 146개 원문 근거 요약 및 무음 native 143칸/146상세 검증 완료. 미열람 숨김·5월 픽셀 동일·실제 저장 무변경. 별도 후보이며 미설치.


### 2026-09-29T17:59:39.564889+09:00 — 4월 목록 포트레이트 여유 폭 활용
- 사용자: 4월 완성본 긍정 평가, 목록에 여유가 있으면 3명보다 많이 표시 요청. 기존 3명 고정 정책을 4월에서 가변 인원으로 대체.
- 기존 32×40 크기, 주인공 포함, 조건/CG와의 여백 유지. 현재 4월 데이터는 최대 5명 표시, 더 있으면 실제 남은 수만 +N. 늘어난 칸 3/143.
- 별도 무음 native 143칸 × 3상태, 146상세 × 2상태 통과. 상세 요약/초상/5월 픽셀 동일. 확장 parts의 월/쪽/종료 정리, 미열람 숨김, 글자/CG 경계 확인.
- 후보 7579a581f60e989d07f9abca13e4bc620aa6f65952974bbddbf0fa99e5f107d3; 검증 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_adaptive_minis_20260929\verification.json; 화면 P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\calendar_april_adaptive_minis_20260929\evidence\native_april.
- 실행 중인 기존 4월 사본 PID 84756 및 live 설치본 무변경. 남음: 사용자 화면 확인 후 종료 시 적용. 다른 달 확대는 아직 하지 않음.
- 2026-09-29T18:12:12+09:00 — WI-007 review 01: accepted — 사용자가 확인한 4월 UI를 기준으로 네이티브 전 칸/상세, 미열람, 페이지·월·종료 정리와 설치 일치를 확인했다.
- 2026-09-29T18:12:12+09:00 — WI-008 review 01: accepted — 146개 일본어 원문 근거 요약의 QA, 모든 상세 경계/숨김 및 실제 설치 해시와 백업을 확인했다. 가변 목록 초상도 통합되어 있다.
- 2026-09-29T19:34:32+09:00 — WI-009 planned — 4월 승인 캘린더 UI의 나머지 탭·달성률 진입 경로 확장
- 2026-09-29T19:34:32+09:00 — WI-010 planned — 5월 미작성 150개 장면 요약과 상세 보드 검증


### 2026-09-29T19:38:42.893613+09:00 클로드 후속 인계 완료
- WI-009 UI확대 / WI-010 5월150요약 계획 등록. 나머지 안정ID/원본 도구 복사/최신 b74ebc 기준 기록.
- 4월147기작성 범위(4월146+E00011), 잔여1,017. 사용자 미채택 디자인·금지된 회귀와 세이브/무음 검증 조건 명시.
- 인계 `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\docs\agentic-workflow\handoffs\CLAUDE-CALENDAR-REMAINING-20260929.md`. 이번은 문서만 작성; 게임/세이브/설치 포인터/기존 설치 journal-bound progress.md 무변경. 클로드에 직접 전송하거나 실행하지 않음.
