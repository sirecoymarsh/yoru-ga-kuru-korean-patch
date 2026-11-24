# -*- coding: utf-8 -*-
"""One-off edit (10-18): the publish generator's contract text follows the reveal rule."""
from pathlib import Path

p = Path(__file__).resolve().parent / 'make_publish_list.py'
s = p.read_text('utf8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep("""              '자세히 its detail board (KR_CClick). Rows follow the board (본편, joined / met companions, 던전 동행); a row naming a '
              'companion not joined (title: not met) shows ？？？ until read; the cast and the summary show for read scenes only. '""",
    """              '자세히 its detail board (KR_CClick). Rows follow the board (본편, joined / met companions, 던전 동행). The cast, the '
              'summary, 다시 보기 and 자세히 open only for a scene the player has seen (home: registered in this save, because the '
              'user\\'s save folder holds later saves than the current play; title: read in any save; everywhere with 전체 개방); a row '
              'naming a companion outside the rows shows ？？？ until then. '""")
rep("""                 '(본편 · 합류한/만난 동료 · 던전 동행), 합류 전 동료 이름이 든 줄은 읽기 전까지 ？？？, 등장인물 · 줄거리는 읽은 장면만. '""",
    """                 '(본편 · 합류한/만난 동료 · 던전 동행). 등장인물 · 줄거리 · 다시 보기 · 자세히는 본 장면만 연다(본거지는 이 세이브에서 본 '
                 '장면 — 세이브 폴더에 지금 진도보다 앞선 세이브가 있다; 타이틀은 어느 세이브에서든 읽은 장면; 전체 개방이면 모두). 합류 전 '
                 '동료 이름이 든 줄은 그때까지 ？？？. '""")
p.write_text(s, 'utf8')
print('ok')
