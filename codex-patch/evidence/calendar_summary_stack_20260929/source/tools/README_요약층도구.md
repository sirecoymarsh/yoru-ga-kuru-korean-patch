# 이벤트 캘린더 요약 층 도구 · 최종 후보 쌓기

작성: Claude Opus 5.5 (claude-opus-5-5), 2026-09-29.

- 이 폴더의 도구는 **굽기 · 검사 · 탐침까지만** 한다. 설치는 사용자 허락 뒤 조율자가 한다(`publish_summary_layer.py`).
- README 와 콘솔 출력에는 요약 본문을 싣지 않는다. 사용자가 실플레이 중이라 요약 본문은 JSON 파일 안에만 둔다.

## 1. 최종 층 순서 (조율자 22:1x · 22:2x · 22:3x 지시)

| # | 층 | 새 함수 · 바뀐 함수 | 만드는 도구 |
|---|---|---|---|
| 1 | WI-009 r2 = **설치본** `626743ef…` | — | (그 에이전트) |
| 2 | 라벨 수정 KR_L30 (107행, 제외 없음) | P29CellName · CellCond · ShortCond, T19EvWhen · CardCond | 그 에이전트의 build/verify(인계 6절 명령). `stack_layers.py` 가 실행하고 사본으로 들여온다 |
| 3 | 6열 보드 KR_SB29Board | KR_W29Board → 전달문 | `build_board_layer.py` |
| 4 | 달별 요약 KR_ST<tag>Story/StoryBase | KR_W29Story → 전달문(층마다) | `build_summary_layer.py` |
| 5 | copy_of 등장인물 KR_ST29Mask/MaskBase | KR_P29Mask → 전달문 | `build_mask_layer.py` |
| 6 | 용어 연동 KR_TF29 (**맨 위**) | W29Story · Info · Cell · HeadWrap · Title · StageItem | 그 에이전트의 build(`run_external_tf29.py build`). 사본으로 들여온다 |

- 4번 달별 요약 층은 04(4월 용어 수정 17개만) → 05 → 06 → 07 → 08 → 09 → OT(그 밖) → 10 → 11(A+B 병합) → ME(회상 A+B) 순서로 쌓는다. 전부 `--term-patch high` 를 쓰고, getter 는 `KR_W29Story` 다.
- 요약 층은 **용어 층 아래**에 둔다. 용어 층의 StoryBase 가 빌드 시점 몸체를 복제하므로, 요약 층이 위에 오면 새 요약이 치환을 건너뛴다.
- 요약 층 하나는 getter 몸체를 `KR_ST<tag>StoryBase` 로 복제한다. `KR_ST<tag>Story` 는 정렬 if-트리다. copy_of 는 `KR_ST<tag>Story(원본)` 을 다시 부른다. 없는 번호는 Base 로 넘어가고, getter 는 한 줄 전달문이 된다. 다음 층은 이 전달문을 다시 복제하므로 찾기가 층을 따라 내려간다.

## 2. 파일

| 파일 | 역할 |
|---|---|
| `sltools.py` | 공용 도구 모음: 병합 · 게이트(`load_layer`), 용어 패치(`apply_terms`, 조사 검사 `josa_problems`), copy_of 해석, `prepare_layer`, 트리 · 스텁, jam 쌍둥이(`simulate`), 쓰기 금지 가드, `chain` |
| `prepare_summary_layer.py` | 기준 AIN 없이 하는 단계만: 병합 · 게이트 · 용어 패치 · copy_of 해석 → `design/prepared_layer.json`, `evidence/term_patch_applied.json` |
| `build_summary_layer.py` | 달별 요약 층(`--term-patch/--term-confidence/--term-strict/--only-patched/--allow-prior-layers/--allow-override-ids/--dry-run`) |
| `build_board_layer.py` | 6열(등장 9명 이상) 보드: 줄거리를 초상 격자 아래 전체 폭(x 28, 20px, 52자)에 그린다. 3·4열은 같은 문장 경로 |
| `build_mask_layer.py` | copy_of 30장면에 원본의 등장인물(KR_P29Mask)을 되부른다 |
| `stack_layers.py` | 위 순서를 한 번에 쌓는다(층마다 앞 후보를 source 로 복사하고 게이트를 돌린다). 마지막에 전체 사슬 정적 검사 → `final_static_check.json`, `stack.json` |
| `run_external_tf29.py` | 용어 층 에이전트의 build/probe 를 그대로 실행한다. 설치본 해시 두 상수만 현재값으로 고정하고, `--twin-summaries` 로 탐침 쌍둥이를 스택 요약으로 바꾼다 |
| `probe_summary_layer.py` + `.jaf` | 무음 사본 탐침(아래 4절). `--build-only` 는 게임 없이 탐침 AIN 만 굽는다. `--all-events` 는 최종 후보용이다 |
| `verify_summary_layer.py` | 설치 전 검사(`--stack` 은 사슬 전체, `--static-only` 는 정적 재검사만) |
| `scan_summary_layer.ps1` | Defender 검사 → `candidate/scan_report.json` |
| `publish_summary_layer.py` | `--check` / `--install` / `--restore`. `--stack` 이면 KEY `calendar_summary_stack_20260929`. 계약에 층 목록 · 층별 provenance · 요약 집필/검수 provenance 를 적는다 |
| `check_summary_consistency.py` | 집필 요약과 동결 원문 교차 검사 → `checks/consistency_<시각>.json` |
| `board_layer/predict_sb29.py` | 배치 예측기(`calendar_layout_predictor_20260929`, 읽기 전용 import)에 6열 규칙을 더한다 → `predict_sb29.json` |
| `fable_check_month_summaries.py` | 조율자가 둔 정적 검사기(읽기만 했다) |
| `prep/<tag>/` | 달별 base-무관 준비 결과 |
| `layers/final_stack/` | **최종 후보**. 대체된 옛 폴더(r2_stack · stack_r1 · may · board_sb29 · TF29 무-마스크판)는 23:0x 에 지웠다(`layers/cleanup_20260929.json`). 용어 층의 이전 r2 후보 백업은 `layers/_tf29_before_rebuild` |
| `probe_april_regression.py` + `.jaf` | 4월 회귀: 설치본과 최종 후보에서 같은 투어(4월 목록 12쪽 · 146장면 · 묶음 카드)를 찍어 픽셀과 부품 글자를 대조하고, 전 1,164장면의 인물 값을 표와 대조 → `regress/april_regression.json` |
| `who_patch/` | 인물 칸 「와」 꼬리 조사(`prepare_who_patch.py` → `design/who_patch.json`): 0행, 적용할 것 없음 |
| `dryrun/` | 시험용이며 설치 금지다. 더미 층, r1 전 층 시험, 게이트 자체 시험(`dryrun/selftest/`)이 들어 있다 |

## 3. 사용 순서

1. 달 폴더의 검수 기록 확인:
   - `evidence/independent_review.json`(없으면 `semantic_qa.json`)의 해시가 지금 `summaries.json` 을 덮어야 한다.
   - `unresolved` 가 비어 있어야 한다. 남겨 둘 것은 검토자가 `<top>/design/qa_acceptance.json` 에 개수와 이유를 적는다.
2. `python check_summary_consistency.py <달 폴더…>` → error 를 판정한다(`<top>/design/consistency_review.json` 의 `waivers[{no, type, token, reason}]` + `reviewer`).
3. `python stack_layers.py --base <WI-009 폴더> --root layers/<새 폴더> --expect-base-sha <설치본 sha>`
   - 이미 있는 층은 건너뛴다. 만든 뒤 summaries.json 이나 용어 표가 바뀐 층이 있으면 멈추고 그 층을 알려 준다.
   - 그때는 `--rebuild-from <그 달 tag>` 로 다시 쌓는다. 그 층과 위 층(… ME → MASK → TF29)은 `_superseded_<시각>/` 로 옮기고 표시한 뒤 다시 굽는다.
   - 예: 판정 에이전트가 8월을 고치면 `--root layers/final_stack --rebuild-from 08`.
   - 설치본이 바뀌면 새 폴더에 다시 쌓는다(결정적이라 AIN 바이트가 같다).
4. `python probe_summary_layer.py --out <root>/<top> --all-events`
   - P: 여유 10GB 이상, 사용자 게임 미실행일 때만 돈다(assert).
5. `python run_external_tf29.py probe --twin-summaries <root>/<top>`: 용어 fixture.
6. `powershell -NoProfile -ExecutionPolicy Bypass -File scan_summary_layer.ps1 -Out <root>/<top>`
7. `python verify_summary_layer.py --out <root>/<top> --stack` → `SUMMARY_LAYER_PREFLIGHT_PASS`
8. `python publish_summary_layer.py --out <root>/<top> --stack --check` → 사용자 허락 → `--install`(조율자). 복구는 `--stack --restore`.

## 4. 게이트

**요약 층**
- 상태 · 글 게이트: ≤100자, 줄바꿈 · 따옴표 · 역슬래시 없음, 프록시 글리프 표현 가능.
- 동결 원문 결합(메시지 ID · `source_event_sha256`).
- ID 는 1,164 이벤트 안에 있어야 하고, 아래 층과 겹치지 않아야 한다(`--allow-override-ids` 제외). copy_of 원본은 이 층이나 아래 층에 있어야 하며, 순환 · 자기 참조는 거부한다.
- 메타는 getter 주소만 바뀐다. 원본 CODE · STR0 · MSG1, PINNED_ALL, opcode, DLL 이 그대로다.
- 전달문은 한 줄, 복제본 명령열은 옛 getter 와 같다. 트리 쌍둥이로 요약 ID · ±1 · 아래 층 ID · 표본을 확인하고, 문자열이 STR0 에 있는지 본다.

**용어 패치** (`term_alignment.json`)
- confidence 가 지정 등급 이상인 제안만 적용한다.
- 요약의 현재 sha256 이 감사 때 값과 같아야 한다. 다르면 건너뛰고 경고를 남긴다.
- `before` 가 정확히 1번 나와야 한다.
- 적용한 뒤 글 게이트와 조사 검사를 다시 돈다. 걸리면 승인 원문을 그대로 굽고 `gate_skipped` 에 적는다. `--term-strict` 면 멈춘다.
- 원본 summaries.json 은 고치지 않는다.

**보드 층**
- 읽기용 KR_W29Board 원문을 그대로 컴파일(버리는 AIN)한 명령열이 기준 함수와 같아야 한다. 고정 편집 4곳은 각각 1번만 적용한다.

**copy_of 등장인물 층**
- copy 표는 아래 요약 층들의 `summaries_baked.json` 에서 모은다. 쌍둥이 79 인자, 원본 등장인물 0 인 경우 0건.

**사슬 전체** (`final_static_check.json`)
- 설치본 · WI-009 대비 메타 차이는 선언된 전달문(주소만)뿐이고, 붙은 함수가 층들의 추가 함수 합과 같아야 한다.
- 원본 CODE · STR0 · MSG1, PINNED_ALL, opcode, DLL 이 그대로다.

**교차 검사기**
- 이름: 대사 · 화자 힌트 · 일본어 원명에 있어야 하고, 메타에만 있으면 경고다.
- 숫자: 전각 · 한자 숫자까지 포함해 원문에 있어야 하고, 메타에만 있으면 경고다.
- 문구: 「료」는 앞이 한글이 아닐 때만 잡는다(단독형과 조사형 둘 다). 그/그녀 · 단계 · E0 · 가나/한자 · 줄바꿈 · 100자 초과 · 3문장 이상 · 「다.」 이외 종결 · 미열람을 잡는다.
- 중복: 달 안 · 달 사이 · 4월과 겹치는 요약.
- 원문 결합: sha 대조.
- 묶음 이웃 이름은 경고다. copy_of 는 원본 존재만 본다.
- `dryrun/selftest/` 가 심은 사례 37 · 조사 6/6 · 거부 11종이 발화하고, 음성 사례는 조용하다.

## 5. 지금 상태 (22:59)

**최종 후보** `layers/final_stack/15_TF29/candidate/NightRemaster.ain` = `549e0be4f9e884b37acecb43b974fd9cd8f7d7f67901af75297ea4e8bdeb5cd6` (설치 안 함)
- `final_static_check.json` = FINAL_STATIC_PASS. 설치본 · WI-009 대비 바뀐 메타는 13개(모두 전달문)이고 붙은 함수는 61개다.
- 요약 층 텍스트는 997개다(4월 용어 수정 17개 포함) + copy_of 30개.
  - 화면 기준으로는 4월 129 + E00011 + 달별 980 + copy 30 = 요약 있는 장면 1,157개, 제외 7개다.
  - 용어 패치는 79개 적용되어 요약 66개가 바뀌었다.
  - 100자를 넘게 되어 원문을 유지한 것이 12개(E00019 · 41 · 47 · 51 · 60 · 88 · 653 · 961 · 963 · 50501 · 60001 · 60006), 감사 뒤 글이 바뀌어 건너뛴 것이 3개다.

**native (무음 사본, 62.8초, 사용자 세이브 무변경)**
- 목록 80쪽 × 읽음/안 읽음.
- 보드 3,597장(1,164장면 + 35카드 × 읽음 · 안 읽음 · 잠김), 실패 0.
- 요약 1,157개: 최대 5줄 · 보드 623px · 버튼 위 여백 최소 26px.
- 6열 보드 22장 × 2: 17건 최대 2줄.
- copy_of 30장면이 원본과 같은 등장인물(30/30).
- 스크린샷 26장.

**용어 층 탐침** (그 에이전트 스크립트)
- 첫 실행은 26 FAIL 이었다. 모두 용어 패치된 4월 요약 7개를 원래 4월 글로 만든 쌍둥이와 비교해서 생긴 것이다.
- `--twin-summaries` 로 스택 요약 쌍둥이를 쓰니 PASS, 실패 0.
- 두 기록 모두 `15_TF29/evidence/` 에 있다.

**verify --stack 이 멈춘 곳**: 검수 기록의 미해결 항목.

| 달 | 미해결 |
|---|---:|
| 6월 | 3 |
| 7월 | 2 |
| 8월 | 3 |
| 9월 | 1 |
| 그 밖 | 1 |
| 10월 | 7 |
| 11월 A | 5 |
| 회상 A | 1 |
| 회상 B | 5 |

- 11월 B 는 지금 summaries.json 을 덮는 검수 기록이 없다.
- 그다음 교차 검사 error 25건(모두 `name_not_in_scene`)에 검토 판정이 필요하다. 5월 4 · 6월 5 · 7월 2 · 8월 3 · 10월 7 · 11월 A 4.
- publish `--check` 는 install_preflight 가 생긴 뒤에야 할 수 있다. 정적 재검사(`--static-only`)는 통과했다: resume 세이브 51 · 프레임 1,256.

## 6. 주의 · 한계

**다른 에이전트 폴더에 쓴 것** (조율자 지시)
- 라벨 층 빌드/검증 실행: `calendar_label_fix_20260929` 의 `candidate/stack_626743efc0b3`, `evidence/verification_stack_626743efc0b3.json`.
- 용어 층 빌드 · 탐침 실행: `calendar_term_free_20260929` 의 candidate/source/work/design/probe/evidence. 실행 전 r2 후보(b0d8c902…)와 탐침 기록을 `layers/_tf29_before_rebuild` 에 복사해 두었다.

**용어 층 러너**
- 그 스크립트의 설치본 상수(`LIVE_AIN/LIVE_MANIFEST`, 옛 설치본 값)를 실행 중에만 현재 값으로 바꾼다. 파일은 고치지 않았다.

**탐침 범위**
- 탐침은 읽음 fixture 기준이다. 전 루트 재생 시험이 아니다.
- 본거지(`--home`) 경로는 이번 최종 후보에서 돌리지 않았다. WI-009 r2 의 home 탐침(22:06, PASS)이 같은 진입 경로를 확인했고, 이 층들은 진입 경로를 바꾸지 않는다.
- 4월 회귀는 텍스트 · 배치 판정뿐이다. 픽셀 비교는 하지 않았다.

**copy_of 원본 위치**
- 원본은 **아래 층**에 있어야 한다. 그래서 회상 층이 마지막이다.

**교차 검사기 이름 판정**
- 표면 문자열 기준이다. 별명 · 호칭 · 대명사로 번역된 인물은 error 로 나오고, 사람이 판정해야 한다.
- 예: 일본어 「新さん」이 한국어에서 「선배」가 된 경우.

**인물 칸 「호시카와와,」 정정** (23:0x)
- 22:5x 보고의 「호시카와와,」는 작은 스크린샷을 내가 잘못 읽은 것이다. 확대하면 「호시카와,」다(`who_patch/work/e60205_info_zoom.png`).
- 인물 표 1,164값에 이름+「와」 꼬리는 0건이다. 「호시카와」 208회는 모두 이름 자체다.

## 7. 23:0x 추가 작업

**4월 회귀 픽셀 대조** (`regress/april_regression.json`, PASS)
- 설치본 `626743ef…` 과 최종 후보 `549e0be4…` 에서 같은 투어를 무음 사본으로 돌렸다. 두 번 다 사용자 세이브 무변경.
- 159장 가운데 138장이 픽셀까지 같다. 바뀐 21장은 모두 글자가 바뀐 곳이고, 설명되지 않는 것은 0장이다.
  - 용어 수정된 4월 요약 17장 + 그 첫 장면을 보이는 묶음 카드 6 1장.
  - 라벨 층 3장: 목록 1쪽 칸 이름 「와」 꼬리 제거, 목록 12쪽과 E05000 의 「부르는 자리 없음」 → 「혼자 · 첫 던전 (4/15)」.
- 인물 값 대조(1,164장면):
  - 설치본은 0건 다름.
  - 최종 후보는 14건 다름(E00041~52 · 60 · 61). 모두 인물 목록에 「히카리」(화자 태그 【光狩】)가 있는 장면이다. 맨 위 용어 층이 사본에 복사된 용어 설정대로 표기를 바꾼 것으로, 설계대로다.

**인물 칸 「와」 꼬리**: 0건이라 적용할 것이 없다(6절).

**정리**: 설치 금지 표시된 대체 폴더 25개 층(약 3.7GB)을 지웠다. 목록과 해시는 `layers/cleanup_20260929.json` 에 있다.

**판정 에이전트 뒤 순서**
1. `stack_layers.py … --rebuild-from <가장 아래 바뀐 달>`
2. `verify --stack`
3. `probe_summary_layer.py --all-events`
4. `run_external_tf29.py probe --twin-summaries`
5. `probe_april_regression.py`
6. 스캔
7. `publish --stack --check`

- 23:1x 에 이미 8월 summaries.json 이 바뀌어 있다. stack 이 `08_08` 을 낡은 층으로 알린다.

## 8. 23:4x 최종 (판정 반영 · 8월부터 다시 쌓음)

**최종 후보** `layers/final_stack/15_TF29/candidate/NightRemaster.ain` = `abae5787031cbf8330a429a4b5d9683241268d87f077d88de24974465ff5c109`
- 8월 E02603 수정본(`9a79d9e6…`)부터 위를 `--rebuild-from 08` 로 다시 쌓았다. 이전 층은 `_superseded_20260929_232353/` 에 두었다.
- FINAL_STATIC_PASS: 바뀐 메타 13개(모두 전달문), 붙은 함수 61개.

**탐침**
- 요약 층 탐침: PASS(63.4초, 실패 0).
  - 보드 3,597장, 요약 1,157개: 최대 5줄 · 623px · 버튼 위 여백 26px.
  - 6열 22장 × 2: 17건 최대 2줄.
  - copy_of 등장인물 30/30.
- 용어 층 탐침(`--twin-summaries`): PASS(181초, 실패 0).
- 4월 회귀(픽셀): PASS. 159장 중 같음 138, 설명된 변경 21, 설명 안 됨 0. 인물 값 차이 14는 모두 히카리 표기 전환.

**검사 · 판정**
- Defender 이상 없음.
- `verify --stack` = SUMMARY_LAYER_PREFLIGHT_PASS: 미해결 검수 항목은 전부 판정 파일로 수락됐고, 교차 검사 오류 43/43 판정 완료, 트랜잭션 fixture 통과, 세이브 51/1,256.
- `publish --stack --check` = PREFLIGHT_PASS.

**설치**(사용자 허락 뒤, 게임 종료 상태에서)
- 설치: `python publish_summary_layer.py --out layers\final_stack\15_TF29 --stack --install`
- 복구: `python publish_summary_layer.py --stack --restore`
