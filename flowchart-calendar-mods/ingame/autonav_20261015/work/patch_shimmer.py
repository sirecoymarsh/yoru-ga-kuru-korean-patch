# -*- coding: utf-8 -*-
"""10-15: replace the star (user: 「별이 뜨는건 별로네. 선택지 자체가 반짝거리는건 어떨까?」) with a shimmer of the answer row
itself (its parts tinted white <-> gold, a gold band behind the row) and of the target's portrait on the partner screen."""
from pathlib import Path

LAYER = Path(__file__).resolve().parent.parent
p = LAYER / 'claude_autonav.jaf'
s = p.read_text('utf8')
mid = (LAYER / 'work' / 'shimmer_mid.jaf').read_text('utf8')
a = s.index('int KR_ANVersion() { return 2026101501; }')
b = s.index('// ---- 친밀도 보충 (모자랄 때만, 대상만)')
s = s[:a] + mid + s[b:]
reps = [
    ("//   · 대사 선택지: 창은 그대로, 자동으로 고를 답에 깜빡이는 무지개 ★, 20초 동안 안 고르면 그 답을 고른다(직접 골라도 된다).",
     "//   · 대사 선택지: 창은 그대로, 자동으로 고를 답 줄이 금빛으로 반짝이고(처음엔 별 표시였으나 사용자가 바꿈), 20초 동안 안 고르면 그 답을 고른다."),
    ("//   · 특훈: 대상의 특훈 뒤 우선 대화가 기다리는 토요일(L_RandomScenario::GetAfterTrainingEvent(대상) > 0)에만 대상 초상 위에 ★,",
     "//   · 특훈: 대상의 특훈 뒤 우선 대화가 기다리는 토요일(L_RandomScenario::GetAfterTrainingEvent(대상) > 0)에만 대상 초상이 반짝이고,"),
    ("//   C_SelectMessage@CreateParts  PUSH C_SelectMessInfo@CreateParts -> KR_ANInfoCreate (CALLMETHOD 대상; 고를 답 줄에 ★)",
     "//   C_SelectMessage@CreateParts  PUSH C_SelectMessInfo@CreateParts -> KR_ANInfoCreate (CALLMETHOD 대상; 고를 답 줄의 부품을 적는다)"),
    ("//   C_SelectMessage@Update       CALLFUNC ■バックログ起動監視      -> KR_ANSelFrame   (매 프레임: ★ 깜빡임 · 20초)",
     "//   C_SelectMessage@Update       CALLFUNC ■バックログ起動監視      -> KR_ANSelFrame   (매 프레임: 반짝임 · 20초)"),
    ('고른 인물 쪽 답에 ★가 붙고 20초 뒤 자동으로 골라집니다.', '고른 인물 쪽 답이 반짝이고 20초 뒤 자동으로 골라집니다.'),
]
for old, new in reps:
    assert s.count(old) == 1, old[:40]
    s = s.replace(old, new)
assert '★' not in s and 'Star' not in s, [l for l in s.splitlines() if '★' in l or 'Star' in l][:5]
p.write_text(s, 'utf8')
print('ok', len(s.splitlines()))
