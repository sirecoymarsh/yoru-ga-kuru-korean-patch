# 밤이 온다! (夜が来る！ Remastered) 한국어 패치 작업물

비공개 보관용 저장소. 패치 코드·도구·번역 텍스트와 한국어화한 그림만 담는다.
원본 게임 파일, 추출한 원문 데이터, 음성·영상, 실행 파일과 빌드 결과는 넣지 않았다.

## 폴더와 원래 위치 (2026-11-25 복사)

| 폴더 | 원래 위치 | 내용 |
|---|---|---|
| `codex-patch/evidence/*/source/` | `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\evidence\*\source` | 기능마다 만든 빌드 소스(jaf·py·후크 C++ 등). 1MB 넘는 중간 자료는 뺌 |
| `codex-patch/evidence/calendar_title_20261018/source/installed_translation_map.json` | 같은 곳 | 설치본 번역 지도(11-17 패치의 기준) |
| `codex-patch/evidence/argon_select_20261117/화면별_반영_내역.jsonl` | 같은 곳 | 11-17 아르곤 선별 반영 125개 |
| `codex-patch/delivery/20261117_cumulative_game_patch/` | 같은 곳 | 11-17 누적 패치의 매니페스트·안내·반영 내역·매뉴얼 |
| `codex-patch/docs/` 외 | 같은 곳 | 에이전트 작업 문서·진행 기록 |
| `flowchart-calendar-mods/` | `P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922` | 이벤트 캘린더(r15~r24)·메뉴바 차트·모드 탭·오토 내비·전투 속도·용어 설정 등 기능 소스와 설계서 |
| `autonav/` | `P:\AI\yoru-autonav` | 오토 내비게이션 도구 |
| `early-2026-08/` | `P:\AI\Codex\game_localization\…`, `YoruGaKuru_KR_*` | 8월 첫 한국어화 어댑터·한글 이름 입력 후크 |
| `assets-ko/` | 11-17 누적 패치의 `NightRemasterCG.afa`·`NightRemasterPact.afa` | 원본 게임 묶음과 비교해 달라지거나 새로 생긴 항목만 게임 형식 그대로(.qnt/.pcf/.dcf/.pactex). `changed_files.json` 이 목록 |

`assets-ko/CG` 의 CG980xxx 등 1280×720 새 그림 801장은 한국어 자막이 든 오프닝 장면이다. 고해상도(4K) 그림은 없다.
