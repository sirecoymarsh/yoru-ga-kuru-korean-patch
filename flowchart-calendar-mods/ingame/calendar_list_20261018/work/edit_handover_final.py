# -*- coding: utf-8 -*-
"""One-off edit (10-18): the handover's status and checks for the final candidate fe4b6db8."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / '인계_20261018.md'
s = p.read_text('utf8')
a = s[s.index('## 지금 상태'):s.index('## 바뀌는 것')]
b = '''## 지금 상태: 설치 준비 끝(READY) · 설치 안 함 · 사용자 허락 대기

- 후보 AIN `fe4b6db8a7e59813f14901feda812d9ab4451f6c4493bfb1877b75a57bc4a855`(AIN 하나). 바탕은 ② 설치본(AIN b5a6ceb0, manifest 6ec96913, status CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS).
- `publish_list.py --verify`: CALENDAR_LIST_20261018_STATIC_NATIVE_PASS_NOT_INSTALLED, issues 0, 게임 꺼짐, 계약 96개. 계약 초안 `required_calendar_list_20261018.json`.
- 설치는 사용자 허락(Codex 정지 · 게임 종료 확인) 뒤에만: `publish_list.py --install`. 되돌리기는 사용자 요청 때만 `--restore`.
- 실행본 · 사용자 세이브 · Codex 루트에는 아직 아무것도 쓰지 않았다.

'''
s = s.replace(a, b)
a = s[s.index('## 확인한 것'):s.index('## 다시 만들 때')]
b = '''## 확인한 것 (최종 후보 fe4b6db8)

- 빌드 불변식: 원본 함수 항목 그대로, 옛 CODE 는 피연산자 2곳(3바이트)만, MSG1 · STR0 앞부분 그대로, 고정 함수 바이트 그대로, 네이티브 명령 감사 통과. KR_LV* 38개.
- 격리 실제 게임(`probe_list.py`, 음소거 · 숨긴 창 · 입력 차단, 사용자 세이브 폴더 그대로)
  - NightR47(11/4, 본거지): 확인 28개 통과. 판 칸 → 목록(4월 · 이즈미 14장면 = 판 칸 숫자), 다른 세이브에서만 읽은 줄은 줄거리 · 얼굴 닫힘, ↓, 모든 세이브, 달 칩 전체, → 쪽, 줄 칩 전체(801장면 = 판 합계 − 회상 · 그 밖), 이즈미 칩, 줄 클릭 → 미리보기, 자세히(상세 창이 목록 위, 목록 숨김) → 복귀, 다시 보기(9문장 재생) → 같은 거르기 · 같은 줄로 복귀, 한눈에 보기로 → 판, 줄 이름 → 목록, 닫기 → 판 → 본거지, 패널 인물 단추 → 그 인물 목록(판 없이) → 닫기 → 본거지.
  - NightR16(5/20): 확인 10개 통과. 판 줄 · 목록 칩에 마코토 · 모모세 없음, 던전 동행 242장면 중 두 사람 이름이 든 117장면이 모두 「？？？」(조건 · 등장인물 · 자세히 꺼짐), 화면에 그린 줄 이름에 두 사람 이름 없음.
  - 타이틀: 확인 5개 통과. 7월 머리 → 목록(7월 · 모든 줄, 「이 세이브」 단추 없음), 달 화면으로 → 7월 달별 화면 → 목록, 닫기 → 판.
  - 그림 `증거\\probe\\lv_*.png`, 보고용(스포일러 없는 4월 · 이즈미, 줄 칩 줄을 잘라 냄) `증거\\목록_4월_이즈미_보고용.png`.
- 저장 스택(읽기만): 이어하기 세이브 51개 · 프레임 1,256개 중 바꾼 함수에 걸린 것 0, 문제 0.
- Defender 통과(SCANNED_NO_TARGET_DETECTIONS), 설치 리허설 TRANSACTION_FIXTURE_PASS.
- 고친 것(시험 중 찾음): 글자 폭 어림(한글 1.0 → 0.8 × 크기, 0.1픽셀 단위), 단추 글자 가운데 맞춤(그린 뒤 크기를 잼), 이름 속 줄바꿈(던전 단계 이름이 줄 밖으로 넘침), 본거지 공개 기준(모든 세이브 읽음 → 이 세이브에서 봄).
- 시험 못 한 것: 진짜 마우스 클릭(탐침은 클릭이 돌려줄 부품 번호로 대기를 끝냄), 상세 창의 단계 고르기(달별 화면의 것 그대로).
- 사용자에게 물을 것: 타이틀(세이브 없음)에서 연 판 · 목록은 ②처럼 「어느 세이브에서든 만난 동료 · 읽은 장면」 기준이라, 9월의 11월 세이브 기록 때문에 뒤 동료가 보일 수 있다.

'''
s = s.replace(a, b)
s = s.replace('- AIN(KR_LV* 37개, 같은 길이 CALLFUNC 피연산자 2곳)', '- AIN(KR_LV* 38개, 같은 길이 CALLFUNC 피연산자 2곳)')
p.write_text(s, 'utf8')
print('ok')
