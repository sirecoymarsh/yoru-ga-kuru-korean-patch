# -*- coding: utf-8 -*-
"""기한 있는 장면 알림 시안 (2026-10-18, Claude Opus 5.5). 사용자 10-18: 「2번은 괜찮네 시간 제한 있는 이벤트 알려주기」.

예시 날짜 4/26(4월 특훈 뒤 대화가 4/30에 닫힌다), 처음부터 있는 동료 넷만 쓴다(스포일러 없음). 장면 이름 · 조건 · 기한은
실제 자료(r22 cells.json, schedule.json 의 우선 대화 날짜 창)이고, 「안 본 수」는 예시다.
출력: 시안/1_본거지_기한알림.png (본거지 화면 오른쪽 여백의 패널), 시안/2_목록_기한.png (목록의 「기한」 거르기)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ING = HERE.parent
sys.path.insert(0, str(ING / 'calendar_redesign_20261017'))
import make_mockups as M                                     # noqa: E402  (font · text · box · button, colours)

OUT = HERE / '시안'
ORANGE = (255, 152, 92)
HOME = ING / 'calendar_redesign_20261017' / '증거' / 'probe_may_hv_home.png'
BOARD = ING / 'calendar_list_20261018' / '증거' / 'probe' / 'lv_board.png'
ROW = {'이즈미': 1, '쿄카': 2, '신카이': 5, '호시카와': 6}       # rows of the 11/4 board shot (faces only)


def face(name, w=24, h=30):
    im = Image.open(BOARD).convert('RGB')
    r = ROW[name]
    y = 132 + r * 50 + 5
    return im.crop((24, y, 56, y + 40)).resize((w, h), Image.LANCZOS)


def home_panel():
    im = Image.open(HOME).convert('RGB')
    d = ImageDraw.Draw(im)
    x0, y0, x1 = 1124, 64, 1276
    M.box(d, (x0, y0, x1, 400), fill=(14, 25, 55), outline=(120, 170, 255), width=2, r=4)
    M.text(d, (x0 + 10, y0 + 10), '기한 있는 장면', 15, M.GOLD, True)
    y = y0 + 38
    M.text(d, (x0 + 10, y), '4/30까지 · 4일 남음', 12, ORANGE, True)
    M.text(d, (x0 + 10, y + 17), '특훈 뒤 대화 · 안 본 수', 11, M.GRAY)
    y += 38
    for name, n in [('이즈미', 3), ('쿄카', 2), ('신카이', 1), ('호시카와', 4)]:
        im.paste(face(name), (x0 + 10, y))
        M.text(d, (x0 + 40, y + 15), name, 12, M.WHITE, False, 'lm')
        M.text(d, (x1 - 10, y + 15), '%d' % n, 14, ORANGE, True, 'rm')
        y += 32
    y += 6
    d.line((x0 + 8, y, x1 - 8, y), fill=(52, 70, 128), width=1)
    y += 8
    M.text(d, (x0 + 10, y), '6/16까지 · 51일', 12, M.GRAY, True)
    M.text(d, (x0 + 10, y + 17), '우선 대화', 11, M.GRAY)
    y += 38
    im.paste(face('이즈미'), (x0 + 10, y))
    M.text(d, (x0 + 40, y + 6), '이즈미 1번째', 12, M.WHITE)
    M.text(d, (x0 + 40, y + 22), '친밀도 5 이상', 11, M.GRAY)
    y += 44
    M.button(d, (x0 + 8, y, x1 - 8, y + 30), '목록에서 보기', 13)
    # 설명 (시안에만)
    M.text(d, (1124, 412), '본거지 첫 메뉴에서만 보임', 11, M.GRAY)
    M.text(d, (1124, 428), '누르면 목록의 「기한」', 11, M.GRAY)
    out = im.crop((480, 0, 1280, 720))
    out.save(OUT / '1_본거지_기한알림.png')


ROWS = [
    ('4/30', 4, '이즈미 · 특훈 뒤 대화 2번째', '이즈미 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '이즈미 · 특훈 뒤 대화 4번째', '이즈미 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '이즈미 · 특훈 뒤 대화 6번째', '이즈미 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '쿄카 · 특훈 뒤 대화 3번째', '쿄카 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '쿄카 · 특훈 뒤 대화 6번째', '쿄카 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '신카이 · 특훈 뒤 대화 2번째', '신카이 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '호시카와 · 특훈 뒤 대화 1번째', '호시카와 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '호시카와 · 특훈 뒤 대화 4번째', '호시카와 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '호시카와 · 특훈 뒤 대화 6번째', '호시카와 · 4월 · 특훈 뒤 잡담'),
    ('4/30', 4, '호시카와 · 특훈 뒤 대화 9번째', '호시카와 · 4월 · 특훈 뒤 잡담'),
    ('6/16', 51, '이즈미 · 우선 대화 1번째', '이즈미 특훈 뒤 · 이즈미 친밀도 5 이상'),
]


def listing():
    im = Image.new('RGB', (M.W, M.H), M.BG)
    d = ImageDraw.Draw(im)
    M.text(d, (24, 30), '이벤트 캘린더', 24, M.GOLD, True, 'lm')
    M.text(d, (196, 30), '장면 목록', 22, M.WHITE, True, 'lm')
    M.text(d, (336, 30), '기한 있는 장면 · 모든 줄', 19, ORANGE, True, 'lm')
    M.button(d, (812, 12, 952, 52), '이 세이브', 19, True)
    M.button(d, (956, 12, 1096, 52), '모든 세이브', 19)
    M.button(d, (1136, 12, 1256, 52), '닫기', 20)
    x = 24
    for k, lab in enumerate(['전체', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월']):
        M.button(d, (x, 62, x + 68, 94), lab, 16)
        x += 74
    M.box(d, (x, 62, x + 92, 94), fill=(80, 46, 22), outline=ORANGE, width=2, r=4)
    M.text(d, (x + 46, 78), '기한', 16, ORANGE, True, 'mm')
    x = 24
    for lab, sel in [('전체', True), ('본편', False), ('이즈미', False), ('쿄카', False), ('신카이', False), ('호시카와', False), ('던전 동행', False)]:
        w = int(M.tw(lab, 16, True)) + 30
        M.button(d, (x, 102, x + w, 134), lab, 16, sel)
        x += w + 6
    M.button(d, (1100, 62, 1256, 94), '달 화면으로', 15)
    M.button(d, (1100, 102, 1256, 134), '한눈에 보기로', 15)
    for xx, s in [(28, '상태'), (62, '기한'), (176, '장면'), (440, '조건')]:
        M.text(d, (xx, 156), s, 13, M.GRAY)
    d.line((24, 168, 800, 168), fill=(52, 70, 128), width=1)
    sel = 10
    for s, (due, left, name, cond) in enumerate(ROWS):
        y = 174 + s * 34
        fill = (30, 42, 88) if s == sel else ((12, 18, 42) if s % 2 == 0 else (9, 14, 34))
        M.box(d, (24, y, 800, y + 32), fill=fill, outline=M.GOLD if s == sel else fill, width=2, r=2)
        M.text(d, (40, y + 16), '○', 15, M.SKY, False, 'mm')
        c = ORANGE if left <= 7 else M.GRAY
        M.text(d, (62, y + 16), '%s · %d일' % (due, left), 14, c, True, 'lm')
        M.text(d, (176, y + 16), name, 14, M.WHITE, False, 'lm')
        M.text(d, (440, y + 16), cond, 14, M.GRAY, False, 'lm')
    # preview of the selected row
    M.box(d, (816, 146, 1256, 702), fill=(14, 25, 55), outline=(120, 170, 255), width=2, r=4)
    M.text(d, (836, 210), '등장인물은 본 뒤에 나옵니다', 15, M.GRAY)
    M.text(d, (836, 300), '이즈미 · 우선 대화 1번째', 19, M.GOLD, True)
    labs = [('기한', '6/16까지 · 51일 남음'), ('조건', '이즈미 특훈 뒤 · 4/21부터 6/16까지'), ('', '이즈미 친밀도 5 이상'),
            ('상태', '아직 안 봄'), ('다시 보기', '본 뒤에 가능')]
    y = 336
    for a, b in labs:
        M.text(d, (836, y), a, 15, M.SKY)
        M.text(d, (916, y), b, 15, ORANGE if a == '기한' else M.WHITE)
        y += 24
    M.text(d, (836, y + 12), '줄거리', 16, M.GOLD, True)
    M.text(d, (836, y + 40), '본 뒤에 나옵니다', 15, M.GRAY)
    M.button(d, (836, 640, 1030, 684), '다시 보기', 19)
    M.button(d, (1042, 640, 1236, 684), '자세히', 19)
    M.text(d, (24, 690), '○ 아직 안 봄　', 14, M.GRAY, False, 'lm')
    M.text(d, (130, 690), '주황 = 7일 안에 닫힘', 14, ORANGE, False, 'lm')
    M.text(d, (330, 690), '11장면 · 1 / 1쪽', 15, M.WHITE, True, 'lm')
    M.text(d, (1256, 712), '시안 · 이름 · 조건 · 기한은 실제(4월), 안 본 장면은 예시', 12, M.DIM, False, 'rm')
    im.save(OUT / '2_목록_기한.png')


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    home_panel()
    listing()
    print('ok', sorted(p.name for p in OUT.glob('*.png')))
