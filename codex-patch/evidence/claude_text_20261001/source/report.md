# 밤이 온다! 전체 대본 검수 보고 (2026-10-01, Opus 5.5 검수 2갈래 + 반증)

- 기준 설치본 AIN: `fae56fb70c8d9c0c…`
- 덩어리 133/133 완료, 패킷 checked 686/686, 미표시 패킷 0
- 반증 통과 교정 **1071줄** (keep 1049 · amend 22), 기각(drop) 344, 집계 게이트 기각 0, 질문 125
- 유형별: artifact 569, mistranslation 192, register 129, term 96, address 44, omission 23, addition 12, shift 5, other_sentence 1
- 출처별(M 뜻 / C 일관성 / MC 둘 다 / V 반증자 추가): MC 443, B 249, C 204, M 84, R 72, V 16, MCB 2, CB 1
- 확신도: high 848, low 223
- 이전 검수 이력별 교정 밀도: codex_0914 875/39187 (2.23%), review_0923 196/17184 (1.14%)
- 글자 수 늘어난 줄 621 (최대 +20자) → Codex 픽셀 폭 게이트 필수
- 용어 표기 설정(8용어)이 걸린 줄 39 → 반입 시 KR_TermMessage 표 재생성 필요
- 괄호 기계 수리(닫는 괄호 누락, bracket_scan.py): 새 레코드 249 · 에이전트 교정에 덧붙임 3 · 이미 포함 0
- 괄호 기계 수리로 못 고친 블록 67 → `bracket_manual.jsonl`(kind 별: 여는 괄호 부족 48, 닫는 괄호 남음 17, 닫는 괄호 부족(블록 끝 줄에 자동 추가 불가) 2); 사람·Codex 가 줄 구조를 보고 고칠 것(검증기 규칙상 레코드로 못 냄). 괄호（）만 다른 블록 32 은 결함 아님

## 덩어리별

| 덩어리 | keep | amend | drop | 기타 |
|---|---|---|---|---|
| chunk_001 | 4 | 0 | 2 |  |
| chunk_002 | 2 | 0 | 4 | R_drop 2 |
| chunk_003 | 7 | 0 | 0 | R_keep 2 |
| chunk_004 | 3 | 0 | 1 | R_drop 2 |
| chunk_005 | 6 | 0 | 1 | R_drop 1 |
| chunk_006 | 3 | 0 | 0 | R_drop 3, R_keep 3 |
| chunk_007 | 10 | 1 | 3 | R_drop 1 |
| chunk_008 | 2 | 0 | 1 | R_drop 2 |
| chunk_009 | 1 | 0 | 0 | R_drop 2 |
| chunk_010 | 5 | 0 | 0 | R_drop 2 |
| chunk_011 | 7 | 0 | 1 | R_drop 2 |
| chunk_012 | 11 | 0 | 0 |  |
| chunk_013 | 7 | 0 | 0 |  |
| chunk_014 | 7 | 0 | 2 | R_drop 2, R_keep 1 |
| chunk_015 | 4 | 0 | 0 | R_drop 2 |
| chunk_016 | 3 | 0 | 3 | R_drop 1, R_keep 1 |
| chunk_017 | 5 | 0 | 1 | R_drop 1 |
| chunk_018 | 3 | 0 | 1 |  |
| chunk_019 | 2 | 0 | 0 | R_drop 2 |
| chunk_020 | 0 | 0 | 1 | R_drop 1 |
| chunk_021 | 3 | 0 | 0 |  |
| chunk_022 | 5 | 0 | 0 | R_drop 1 |
| chunk_023 | 6 | 0 | 1 | R_keep 1, R_drop 2 |
| chunk_024 | 13 | 0 | 1 |  |
| chunk_025 | 8 | 0 | 4 | R_drop 5 |
| chunk_026 | 8 | 0 | 0 | R_drop 1 |
| chunk_027 | 10 | 0 | 1 |  |
| chunk_028 | 2 | 0 | 0 |  |
| chunk_029 | 5 | 0 | 0 |  |
| chunk_030 | 3 | 0 | 2 | R_drop 2 |
| chunk_031 | 4 | 0 | 1 | R_drop 3 |
| chunk_032 | 7 | 0 | 0 | R_keep 1 |
| chunk_033 | 4 | 0 | 1 |  |
| chunk_034 | 3 | 0 | 3 | R_drop 3 |
| chunk_035 | 3 | 0 | 1 | R_keep 1 |
| chunk_036 | 6 | 0 | 1 | R_keep 1, R_drop 3 |
| chunk_037 | 2 | 0 | 4 | R_drop 1 |
| chunk_038 | 5 | 0 | 0 | R_drop 1 |
| chunk_039 | 3 | 0 | 0 | R_drop 4, R_keep 2 |
| chunk_040 | 5 | 0 | 2 | R_drop 3 |
| chunk_041 | 8 | 0 | 0 | R_keep 1 |
| chunk_042 | 11 | 1 | 0 | R_drop 1 |
| chunk_043 | 3 | 0 | 2 | R_drop 1 |
| chunk_044 | 14 | 1 | 0 | R_keep 3, R_drop 1 |
| chunk_045 | 14 | 0 | 0 | R_drop 3 |
| chunk_046 | 11 | 0 | 1 |  |
| chunk_047 | 1 | 0 | 0 |  |
| chunk_048 | 35 | 0 | 0 |  |
| chunk_049 | 33 | 0 | 0 |  |
| chunk_050 | 18 | 0 | 0 |  |
| chunk_051 | 0 | 0 | 1 | R_drop 16 |
| chunk_052 | 6 | 0 | 0 |  |
| chunk_053 | 6 | 0 | 0 | R_drop 1 |
| chunk_054 | 3 | 0 | 0 | R_keep 1, R_drop 1 |
| chunk_055 | 1 | 0 | 0 | R_drop 5 |
| chunk_056 | 2 | 0 | 3 | R_drop 1 |
| chunk_057 | 2 | 0 | 2 | R_drop 1 |
| chunk_058 | 1 | 0 | 1 | R_drop 2 |
| chunk_059 | 5 | 0 | 3 | R_keep 1, R_drop 3 |
| chunk_060 | 5 | 0 | 0 | R_drop 1 |
| chunk_061 | 8 | 0 | 2 |  |
| chunk_062 | 3 | 0 | 1 |  |
| chunk_063 | 6 | 0 | 1 | R_drop 1 |
| chunk_064 | 4 | 0 | 0 | R_drop 1 |
| chunk_065 | 4 | 0 | 0 | R_drop 1, R_keep 1 |
| chunk_066 | 4 | 1 | 0 | R_amend 1 |
| chunk_067 | 4 | 1 | 1 |  |
| chunk_068 | 5 | 0 | 1 | R_drop 2, R_keep 2 |
| chunk_069 | 5 | 0 | 0 | R_drop 1 |
| chunk_070 | 6 | 0 | 1 |  |
| chunk_071 | 4 | 0 | 2 | R_drop 1 |
| chunk_072 | 3 | 0 | 0 | R_keep 6, R_drop 1 |
| chunk_073 | 2 | 0 | 2 | R_drop 1 |
| chunk_074 | 2 | 1 | 3 | R_drop 1 |
| chunk_075 | 2 | 0 | 0 |  |
| chunk_076 | 3 | 0 | 1 | R_drop 3 |
| chunk_077 | 4 | 0 | 0 | R_keep 1, R_drop 1 |
| chunk_078 | 6 | 0 | 2 |  |
| chunk_079 | 3 | 0 | 1 | R_drop 3 |
| chunk_080 | 5 | 0 | 1 | R_drop 1, R_keep 1 |
| chunk_081 | 10 | 0 | 3 | R_drop 1, R_keep 1 |
| chunk_082 | 5 | 1 | 2 | R_drop 3 |
| chunk_083 | 3 | 0 | 0 | R_drop 3 |
| chunk_084 | 8 | 0 | 1 | R_drop 1, R_keep 1, R_amend 1 |
| chunk_085 | 4 | 0 | 3 | R_keep 4, R_drop 2 |
| chunk_086 | 5 | 0 | 0 | R_drop 2, R_keep 1 |
| chunk_087 | 8 | 0 | 0 | R_keep 1 |
| chunk_088 | 5 | 0 | 2 | R_drop 2, R_keep 1 |
| chunk_089 | 2 | 0 | 1 | R_drop 1 |
| chunk_090 | 4 | 0 | 4 | R_drop 3, R_keep 1 |
| chunk_091 | 4 | 0 | 1 | R_drop 2 |
| chunk_092 | 6 | 0 | 2 | R_keep 1 |
| chunk_093 | 3 | 0 | 1 | R_drop 2 |
| chunk_094 | 6 | 0 | 0 | R_drop 1 |
| chunk_095 | 5 | 0 | 1 | R_drop 3, R_amend 2 |
| chunk_096 | 5 | 0 | 2 | R_keep 1, R_amend 1 |
| chunk_097 | 7 | 0 | 1 | R_keep 1 |
| chunk_098 | 3 | 0 | 0 | R_keep 1, R_drop 2 |
| chunk_099 | 4 | 1 | 0 | R_keep 2 |
| chunk_100 | 4 | 0 | 3 | R_drop 2, R_amend 1 |
| chunk_101 | 3 | 1 | 4 | R_drop 2 |
| chunk_102 | 7 | 0 | 3 | R_drop 2 |
| chunk_103 | 2 | 0 | 1 | R_drop 4, R_amend 1 |
| chunk_104 | 4 | 0 | 3 | R_drop 3 |
| chunk_105 | 2 | 2 | 4 | R_drop 1 |
| chunk_106 | 8 | 0 | 0 | R_keep 2, R_drop 2 |
| chunk_107 | 3 | 0 | 3 | R_keep 1, R_drop 6 |
| chunk_108 | 4 | 0 | 0 | R_drop 3 |
| chunk_109 | 7 | 0 | 0 |  |
| chunk_110 | 6 | 0 | 0 | R_drop 2 |
| chunk_111 | 7 | 0 | 1 | R_amend 1 |
| chunk_112 | 9 | 0 | 0 | R_keep 1, R_drop 1 |
| chunk_113 | 2 | 0 | 0 |  |
| chunk_114 | 3 | 0 | 2 | R_amend 1, R_drop 1 |
| chunk_115 | 5 | 0 | 2 |  |
| chunk_116 | 3 | 0 | 2 | R_drop 2, R_amend 1 |
| chunk_117 | 9 | 0 | 0 | R_drop 3 |
| chunk_118 | 5 | 0 | 3 |  |
| chunk_119 | 0 | 0 | 0 | R_drop 2 |
| chunk_120 | 10 | 0 | 1 | R_drop 4, R_keep 2 |
| chunk_121 | 4 | 0 | 2 | R_drop 2, R_keep 1 |
| chunk_122 | 7 | 0 | 0 | R_drop 3, R_keep 1 |
| chunk_123 | 4 | 0 | 2 | R_keep 2, R_drop 1 |
| chunk_124 | 3 | 0 | 1 | R_drop 3 |
| chunk_125 | 10 | 0 | 1 | R_drop 3 |
| chunk_126 | 8 | 0 | 2 | R_drop 1 |
| chunk_127 | 2 | 0 | 0 | R_drop 1 |
| chunk_128 | 8 | 1 | 0 | R_keep 3, R_drop 2 |
| chunk_129 | 10 | 0 | 0 | R_drop 2 |
| chunk_130 | 2 | 0 | 1 | R_drop 1, R_keep 2 |
| chunk_131 | 6 | 0 | 2 | R_drop 1 |
| chunk_132 | 14 | 0 | 0 | R_keep 1, R_drop 1 |
| chunk_133 | 1 | 0 | 2 | R_drop 1 |

## 기각 사유(앞 40자)

- 8 × 「おーい！」는 부름 감탄사로, 현재 줄의 장음 부름(이즈미 누나―! 쿄카
- 8 × 「지금은」은 바로 앞 상자의 今はもう를 이어받은 말로 뜻을 바꾸지 않는다
- 7 × 전각 ？는 폰트에 있는 정상 문장부호로 화면 결함·뜻 오류가 아니다. 설
- 4 × 현재 「마나미」는 대상 지칭이 정확해 뜻 오류가 아니다(low). 쿄카 
- 2 × 「티끌」 자체가 아주 작은 먼지라는 뜻이라 小さき 를 따로 옮기지 않아도
- 2 × 원문 「私も…私の憧れも……、すごく…可哀相で…」는 어미 없이 감정이 터지는
- 2 × 현재 「마나」는 틀린 줄이 아니다. 09-23 사용자 결정의 조롱조 짱 
- 2 × 전각 ？는 폰트에 있는 정상 문장부호로 화면 결함이 아니고 뜻·읽기에 영
- 2 × 현재 줄이 틀리지 않음: 바로 앞 줄(43965-66/44316-17)이
- 2 × 화자는 인형 트윈티(마나미가 목소리 연기하는 별개 캐릭터)라 호칭표 「마
- 2 × 部室은 glossary·사용자 결정에 잠긴 용어가 아니다. 「동아리방」은
- 2 × 전각 ？는 폰트에 있는 정상 문장부호로 화면 결함·뜻 오류가 아니고 지시
- 1 × 원문 「いたのかい」「びっくりしたよ」가 반말이고 현재 줄 반말이 원문과 맞
- 1 × 원문 「思わないかい？」는 반말(かい). 현재 「않나?」는 원문의 부드러운
- 1 × 994 와 같은 원문·같은 번역의 반복 장면. 원문 「いたのかい」「びっく
- 1 × 1020 과 같은 원문·같은 번역의 반복 장면. 원문 「思わないかい？」 
- 1 × 見学→「견학」은 정확한 번역이고 용어집 밖 일반 낱말. 2923·2925
- 1 × 逃げるんじゃ……ないかな 의 「~じゃないかな」는 한국어 「~지 않을까」(추
- 1 × 원문 こすって 는 です·ます 가 아닌 맨 て형이라 이 줄은 원문 자체가 
- 1 × 後藤さん 을 「고토 씨」로 옮긴 것은 오역이 아니다(さん=씨). addr
- 1 × 현재 「무심코 사람 죽이면 곤란해」는 원문 『つい』で殺されちゃかなわない 
- 1 × 원문 m5304 자체가 반각 ( ) 로 쓰여 있어 한국어가 원문 표기를 
- 1 × あてっ은 痛っ 계열 감탄사이지만 바로 앞 「火を…」(불을…)로 상대가 불
- 1 × 바로 앞 10095·10101에서 「당신」을 두 번 부른 뒤라 꿈꾸는 주
- 1 × 부사 「그만」은 사전상 「저도 모르는 사이에」 뜻으로 つい의 정당한 역어

## 3차 검수(R, 독립 검수자 + 새 레코드만 반증)

- R 판정 파일 133/133 덩어리, 새로 살아남은 교정 72, 새 레코드 기각 200
- 2갈래+반증이 놓친 비율 추정: 72/(750+72) = 8.8%
- 표본 탐침(12덩어리, 결과 비공개 상태에서 먼저 실행): 새 교정 9 / 기존 58 → 13.4%
