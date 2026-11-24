# -*- coding: utf-8 -*-
"""이벤트 캘린더 · 달성률 새 화면 시안 (2026-10-17, Claude Opus 5.5).

사용자(10-17): 캘린더는 「게임 이야기 전체를 총괄해서 볼 수 있다는 느낌이 안 든다」 · 열기 번거로움 · 넘길 쪽이 많음 ·
칸만 봐선 모름 · 인물별로 못 봄. 달성률은 「텍스트만 있어서 정보 파악이 느리다」 · 숫자 기준이 섞임 · 이름 누르는 창.

장면 수(달 × 줄)는 설치된 차트의 칸 표(r22 cells.json)와 schedule.json 의 줄 배정(build_chart.lane_of)에서 센다.
본 수는 예시다(그림에 적음). 줄거리는 4월 요약만 쓴다. 출력: 시안/*.png
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FLOW = HERE.parent.parent                                   # YoruGaKuru_flowchart_20260922
CODEX = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')
OUT = HERE / '시안'
sys.path.insert(0, str(FLOW / 'chart'))
import build_chart as B                                     # noqa: E402  (lane_of, LANES)

W, H = 1280, 720
BG = (8, 12, 30)
PANEL = (15, 23, 56)
PANEL2 = (24, 36, 84)
BORDER = (110, 150, 230)
BORDER_DIM = (52, 70, 128)
GOLD = (244, 205, 96)
GOLD_FILL = (72, 58, 22)
WHITE = (238, 240, 248)
GRAY = (165, 170, 186)
DIM = (92, 98, 124)
SKY = (128, 224, 255)
SEEN = (122, 148, 205)
MISSED = (255, 152, 92)
FUTURE = (40, 48, 78)

FONT_R = r'C:\Windows\Fonts\malgun.ttf'
FONT_B = r'C:\Windows\Fonts\malgunbd.ttf'
_fc = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FONT_B if bold else FONT_R, size)
    return _fc[key]


def text(d, xy, s, size=16, fill=WHITE, bold=False, anchor='la'):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def tw(s, size=16, bold=False):
    return font(size, bold).getlength(s)


def box(d, xyxy, fill=PANEL, outline=BORDER_DIM, width=1, r=6):
    d.rounded_rectangle(xyxy, radius=r, fill=fill, outline=outline, width=width)


def button(d, xyxy, label, size=17, selected=False, bold=True):
    box(d, xyxy, fill=GOLD_FILL if selected else PANEL, outline=GOLD if selected else BORDER, width=2, r=4)
    cx, cy = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2
    text(d, (cx, cy), label, size, GOLD if selected else WHITE, bold, 'mm')


def bar(d, x0, y0, x1, y1, parts, total):
    d.rectangle((x0, y0, x1, y1), fill=FUTURE)
    if total <= 0:
        return
    x = x0
    for v, c in parts:
        if v <= 0:
            continue
        x2 = x + (x1 - x0) * v / total
        d.rectangle((x, y0, x2, y1), fill=c)
        x = x2


# ---------------------------------------------------------------- data
def lane_counts():
    s = B.load('schedule.json')
    lane = {e['id']: B.lane_of(e) for e in s['events']}
    cells = json.loads((FLOW / 'ingame' / 'r22_chart' / 'work' / 'build' / 'cells.json').read_text('utf8'))['rows']
    cnt = {}
    for c in cells:
        k = (lane[c['no']], c['tab'])
        cnt[k] = cnt.get(k, 0) + 1
    return cnt, cells, lane


CNT, CELLS, LANE = lane_counts()
MONTHS = ['4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월']
NOW = 6                                                      # 예시: 지금 = 10월
ROWS = [('main', '본편', 0), ('p2', '이즈미', 1), ('p3', '쿄카', 2), ('p4', '마나미', 3), ('p5', '마코토', 4),
        ('p6', '신카이', 5), ('p7', '호시카와', 6), ('p8', '모모세', 7), ('dungeon', '던전 동행', None)]
RATE = {'main': 0.96, 'p2': 0.82, 'p3': 0.78, 'p4': 0.74, 'p5': 0.7, 'p6': 0.66, 'p7': 0.72, 'p8': 0.62, 'dungeon': 0.34}


def sample(lane, m):
    """예시 숫자: (봄, 놓침, 남음, 아직) — 지난 달은 봄/놓침, 지금 달은 봄/남음, 다음 달은 아직."""
    t = CNT.get((lane, m), 0)
    if lane == 'dungeon':                                    # 짝꿍별 무작위 대화: 놓침이 없고 남음만 있다
        seen = round(t * RATE[lane])
        return seen, 0, t - seen, 0
    if m < NOW:
        seen = min(t, round(t * RATE[lane] + ((m * 7 + len(lane)) % 3) - 1))
        seen = max(0, seen)
        return seen, t - seen, 0, 0
    if m == NOW:
        seen = round(t * 0.45)
        return seen, 0, t - seen, 0
    return 0, 0, 0, t


# portraits: the calendar's own roster (asset test screenshot, first row = main cast)
ROSTER = Image.open(CODEX / 'staging' / 'calendar_portraits_20260929' / 'evidence' / 'native_portraits' /
                    'portraits_roster_asset_test.png').convert('RGB')


def portrait(i, w, h):
    x0 = 108 + 136 * i
    return ROSTER.crop((x0, 210, x0 + 104, 328)).resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- 1. 한눈에 보기
def overview():
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    text(d, (24, 16), '이벤트 캘린더', 24, GOLD, True)
    text(d, (24 + tw('이벤트 캘린더', 24, True) + 16, 19), '한눈에 보기', 21, WHITE, True)
    button(d, (812, 12, 952, 50), '이 세이브', 16, True)
    button(d, (956, 12, 1096, 50), '모든 세이브', 16, False)
    button(d, (1136, 12, 1256, 50), '닫기', 17)

    tot = {'seen': 0, 'missed': 0, 'remain': 0, 'future': 0}
    grid = {}
    for lane, _, _ in ROWS:
        for m in range(8):
            v = sample(lane, m)
            grid[(lane, m)] = v
            for k, x in zip(tot, v):
                tot[k] += x
    mem = (60, 25, 0, 0)
    etc = (18, 11, 0, 0)
    for k, x in zip(tot, mem):
        tot[k] += x
    for k, x in zip(tot, etc):
        tot[k] += x
    total = sum(tot.values())
    text(d, (24, 66), '전체', 17, WHITE, True)
    bar(d, 80, 70, 1010, 84, [(tot['seen'], SEEN), (tot['missed'], MISSED), (tot['remain'], SKY)], total)
    text(d, (1024, 77), f"본 장면 {tot['seen']} / {total}  ·  {round(100 * tot['seen'] / total)}%", 16, WHITE, False, 'lm')

    x0, cw, y0, rh = 200, 116, 132, 50
    # month header + now marker
    d.rectangle((x0 + NOW * cw + 2, 104, x0 + NOW * cw + cw - 2, y0 + rh * (len(ROWS) - 1)), fill=(20, 30, 66))
    for m, name in enumerate(MONTHS):
        cx = x0 + m * cw + cw / 2
        text(d, (cx, 116), name, 18, GOLD if m == NOW else WHITE, True, 'mm')
    text(d, (x0 + NOW * cw + cw - 8, 116), '지금', 12, GOLD, True, 'rm')
    text(d, (x0 + 8 * cw + cw / 2, 116), '합계', 18, GRAY, True, 'mm')

    for r, (lane, name, pi) in enumerate(ROWS):
        y = y0 + r * rh
        if pi is not None:
            im.paste(portrait(pi, 32, 36), (24, y + 7))
        text(d, (66 if pi is not None else 24, y + rh / 2), name, 17, WHITE, True, 'lm')
        lt = [0, 0, 0, 0]
        if lane == 'dungeon':
            # 던전 동행은 달과 상관없이 짝꿍별로 나오는 대화 → 한 칸으로 모은다(지금은 4~6월 탭에 242장면이 몰려 있음)
            s_ = sum(grid[(lane, m)][0] for m in range(8))
            t_ = sum(sum(grid[(lane, m)]) for m in range(8))
            lt = [s_, 0, t_ - s_, 0]
            cell = (x0 + 4, y + 4, x0 + 8 * cw - 4, y + rh - 4)
            box(d, cell, fill=PANEL, outline=BORDER_DIM)
            text(d, (cell[0] + 14, y + 17), f'{s_}/{t_}', 16, WHITE, True, 'lm')
            text(d, (cell[0] + 90, y + 17), '달과 상관없이 짝꿍에 따라 나오는 대화  ·  누르면 짝꿍별로 봅니다', 14, GRAY, False, 'lm')
            bar(d, cell[0] + 10, y + 32, cell[2] - 10, y + 37, [(s_, SEEN), (t_ - s_, SKY)], t_)
            cx0 = x0 + 8 * cw
            cell = (cx0 + 4, y + 4, cx0 + cw - 4, y + rh - 4)
            box(d, cell, fill=(12, 18, 44), outline=BORDER_DIM)
            text(d, ((cell[0] + cell[2]) / 2, y + 17), f'{s_}/{t_}  {round(100 * s_ / t_)}%', 15, WHITE, True, 'mm')
            bar(d, cell[0] + 10, y + 32, cell[2] - 10, y + 37, [(s_, SEEN), (t_ - s_, SKY)], t_)
            continue
        for m in range(8):
            v = grid[(lane, m)]
            t = sum(v)
            for i in range(4):
                lt[i] += v[i]
            cx0 = x0 + m * cw
            cell = (cx0 + 4, y + 4, cx0 + cw - 4, y + rh - 4)
            if t == 0:
                box(d, cell, fill=(11, 16, 38), outline=(30, 40, 72))
                text(d, ((cell[0] + cell[2]) / 2, y + rh / 2), '—', 16, DIM, False, 'mm')
                continue
            sel = (lane == 'p3' and m == 4)
            box(d, cell, fill=PANEL2 if sel else PANEL, outline=GOLD if sel else BORDER_DIM, width=2 if sel else 1)
            col = DIM if m > NOW else (GRAY if v[0] == t else WHITE)
            label = f'{v[0]}/{t}' if m <= NOW else f'{t}'
            text(d, ((cell[0] + cell[2]) / 2, y + 17), label, 16, col, True, 'mm')
            bar(d, cell[0] + 10, y + 32, cell[2] - 10, y + 37, [(v[0], SEEN), (v[1], MISSED), (v[2], SKY)], t)
        t = sum(lt)
        cx0 = x0 + 8 * cw
        cell = (cx0 + 4, y + 4, cx0 + cw - 4, y + rh - 4)
        box(d, cell, fill=(12, 18, 44), outline=BORDER_DIM)
        text(d, ((cell[0] + cell[2]) / 2, y + 17), f'{lt[0]}/{t}  {round(100 * lt[0] / t)}%', 15, WHITE, True, 'mm')
        bar(d, cell[0] + 10, y + 32, cell[2] - 10, y + 37, [(lt[0], SEEN), (lt[1], MISSED), (lt[2], SKY)], t)

    yb = y0 + rh * len(ROWS) + 14
    for i, (name, v) in enumerate([('회상', mem), ('그 밖', etc)]):
        bx = 24 + i * 300
        box(d, (bx, yb, bx + 288, yb + 46), fill=PANEL, outline=BORDER, width=2, r=4)
        text(d, (bx + 16, yb + 16), name, 17, WHITE, True, 'lm')
        text(d, (bx + 276, yb + 16), f'{v[0]}/{sum(v)}', 15, WHITE, True, 'rm')
        bar(d, bx + 16, yb + 32, bx + 272, yb + 37, [(v[0], SEEN), (v[1], MISSED)], sum(v))
    text(d, (650, yb + 12), '칸을 누르면 그 달 · 그 인물 장면만 모아 봅니다.', 15, GRAY)
    text(d, (650, yb + 34), '이름을 누르면 그 인물의 모든 달, 달을 누르면 그 달 전체.', 15, GRAY)

    ly = 688
    lx = 24
    for c, s in [(SEEN, '본 장면'), (MISSED, '놓친 장면(지난 날)'), (SKY, '남은 장면'), (FUTURE, '아직 안 온 달')]:
        d.rectangle((lx, ly - 6, lx + 14, ly + 6), fill=c)
        text(d, (lx + 20, ly), s, 15, GRAY, False, 'lm')
        lx += 40 + tw(s, 15)
    text(d, (1256, ly), '시안 · 장면 수는 실제, 본 수는 예시', 14, DIM, False, 'rm')
    return im


# ---------------------------------------------------------------- 2. 목록 (4월 · 이즈미)
def listing():
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    text(d, (24, 16), '이벤트 캘린더', 24, GOLD, True)
    text(d, (24 + tw('이벤트 캘린더', 24, True) + 16, 19), '한눈에 보기  ›  4월  ›  이즈미', 20, WHITE, True)
    button(d, (812, 12, 952, 50), '이 세이브', 16, True)
    button(d, (956, 12, 1096, 50), '모든 세이브', 16, False)
    button(d, (1136, 12, 1256, 50), '닫기', 17)

    chips = ['전체'] + MONTHS
    x = 24
    for c in chips:
        w = 70 if c != '전체' else 70
        button(d, (x, 62, x + w, 92), c, 15, c == '4월')
        x += w + 6
    x = 24
    for c in ['전체', '본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전 동행']:
        w = int(tw(c, 15, True)) + 30
        button(d, (x, 100, x + w, 130), c, 15, c == '이즈미')
        x += w + 6
    button(d, (1100, 100, 1256, 130), '한눈에 보기로', 15)

    summ = json.loads((CODEX / 'staging' / 'calendar_april_summary_20260929' / 'design' / 'summaries.json').read_text('utf8'))
    story = {e['no']: e['summary'] for e in summ['events']}
    rows = [c for c in CELLS if c['tab'] == 0 and LANE[c['no']] == 'p2']
    order = {'after_training_priority': 0, 'after_training': 1, 'training_invite': 2}
    # status pattern (예시): 봄 10 · 놓침 2 · 지금 달이면 남음
    status = ['seen', 'seen', 'seen', 'seen', 'missed', 'seen', 'seen', 'seen', 'seen', 'seen', 'missed', 'seen', 'seen', 'seen']

    lx0, lx1 = 24, 800
    hy = 144
    for xx, s in [(40, '상태'), (86, '종류'), (238, '함께'), (322, '장면')]:
        text(d, (lx0 + xx - 24, hy + 10), s, 14, DIM, True, 'lm')
    d.line((lx0, hy + 22, lx1, hy + 22), fill=BORDER_DIM)
    rh = 34
    sel = 2
    for i, c in enumerate(rows):
        y = hy + 28 + i * rh
        st = status[i]
        if i == sel:
            box(d, (lx0, y, lx1, y + rh - 4), fill=PANEL2, outline=GOLD, width=2, r=4)
        mark, mc = {'seen': ('●', SEEN), 'missed': ('▲', MISSED), 'remain': ('○', SKY)}[st]
        text(d, (lx0 + 16, y + 15), mark, 15, mc, True, 'mm')
        kind = c['name'].split(' · ', 1)[1]
        text(d, (lx0 + 62, y + 15), kind, 15, WHITE if st != 'missed' else GRAY, False, 'lm')
        im.paste(portrait(0, 20, 24), (lx0 + 214, y + 3))
        im.paste(portrait(1, 20, 24), (lx0 + 238, y + 3))
        if st == 'seen':
            s = story.get(c['no'], '')
            cut = s
            while tw(cut + '…', 15) > lx1 - (lx0 + 298) - 12 and len(cut) > 4:
                cut = cut[:-1]
            text(d, (lx0 + 298, y + 15), cut + ('…' if cut != s else ''), 15, WHITE, False, 'lm')
        else:
            text(d, (lx0 + 298, y + 15), '이 세이브에서는 놓친 장면 · 줄거리는 본 뒤에', 15, DIM, False, 'lm')

    # preview pane
    px0, px1, py0, py1 = 816, 1256, 144, 664
    box(d, (px0, py0, px1, py1), fill=PANEL, outline=BORDER, width=2, r=6)
    c = rows[sel]
    im.paste(portrait(0, 104, 118), (px0 + 20, py0 + 20))
    im.paste(portrait(1, 104, 118), (px0 + 136, py0 + 20))
    text(d, (px0 + 20, py0 + 156), c['name'], 19, GOLD, True)
    info = [('언제', '4월 · 특훈을 마친 날'), ('함께', '이즈미, 주인공'), ('상태', '이 세이브에서 봄'), ('다시 보기', '가능')]
    for i, (k, v) in enumerate(info):
        text(d, (px0 + 20, py0 + 196 + i * 28), k, 16, SKY, True)
        text(d, (px0 + 110, py0 + 196 + i * 28), v, 16, WHITE)
    text(d, (px0 + 20, py0 + 318), '줄거리', 16, GOLD, True)
    s = story.get(c['no'], '')
    line, ly = '', py0 + 346
    for ch in s:
        if tw(line + ch, 16) > px1 - px0 - 40:
            text(d, (px0 + 20, ly), line, 16, WHITE)
            line, ly = ch, ly + 26
        else:
            line += ch
    if line:
        text(d, (px0 + 20, ly), line, 16, WHITE)
    button(d, (px0 + 20, py1 - 64, px0 + 210, py1 - 20), '다시 보기', 17, True)
    button(d, (px0 + 230, py1 - 64, px1 - 20, py1 - 20), '이즈미의 다른 달', 17)

    text(d, (412, 690), f'1 / 1쪽  ·  {len(rows)}장면', 16, WHITE, True, 'mm')
    lx = 24
    for mk, c2, s2 in [('●', SEEN, '봄'), ('▲', MISSED, '놓침'), ('○', SKY, '남음')]:
        text(d, (lx, 690), mk, 15, c2, True, 'lm')
        text(d, (lx + 18, 690), s2, 15, GRAY, False, 'lm')
        lx += 64
    text(d, (1256, 690), '시안 · 장면 이름과 줄거리는 실제(4월), 상태는 예시', 14, DIM, False, 'rm')
    return im


# ---------------------------------------------------------------- 3. 본거지 달성률 패널
def panel():
    home = Image.open(CODEX / 'evidence' / 'autonav_20261015' / 'source' / 'probe' / 'an_home.png').convert('RGB')
    im = home.copy()
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 159, 664), fill=(0, 0, 0))
    text(d, (10, 8), '달성률', 19, GOLD, True)
    text(d, (10, 40), '이 세이브', 12, GRAY, True)
    seen = sum(sample(l, m)[0] for l, _, _ in ROWS for m in range(8))
    tot = sum(sum(sample(l, m)) for l, _, _ in ROWS for m in range(8))
    text(d, (10, 64), '이벤트', 14, WHITE, True, 'lm')
    text(d, (152, 64), f'{round(100 * seen / tot)}%', 14, SKY, True, 'rm')
    bar(d, 10, 76, 150, 81, [(seen, SEEN)], tot)
    text(d, (10, 98), '본편', 14, WHITE, True, 'lm')
    text(d, (152, 98), '서양관 이후', 13, GRAY, False, 'rm')
    y = 116
    for lane, name, pi in ROWS[1:8]:
        s_ = sum(sample(lane, m)[0] for m in range(8))
        t_ = sum(sum(sample(lane, m)) for m in range(8))
        hover = lane == 'p3'
        box(d, (4, y, 156, y + 40), fill=PANEL2 if hover else PANEL, outline=GOLD if hover else BORDER_DIM, width=2 if hover else 1, r=4)
        im.paste(portrait(pi, 26, 32), (8, y + 4))
        text(d, (40, y + 13), name, 14, WHITE, True, 'lm')
        text(d, (152, y + 13), f'{round(100 * s_ / t_)}%', 13, SKY, True, 'rm')
        bar(d, 40, y + 27, 150, y + 32, [(s_, SEEN)], t_)
        y += 44
    text(d, (10, y + 8), '모든 세이브 합산', 12, GRAY, True)
    y += 28
    for name, v, t in [('대사', 45.3, 100), ('CG', 55.0, 100), ('회상', 53.0, 100), ('엔딩', 0, 5)]:
        text(d, (10, y + 8), name, 13, GRAY, True, 'lm')
        text(d, (152, y + 8), (f'{v}%' if t == 100 else f'{v} / {t}'), 13, GRAY, False, 'rm')
        bar(d, 10, y + 19, 150, y + 23, [(v, (110, 120, 150))], t)
        y += 30
    box(d, (6, 612, 154, 652), fill=GOLD_FILL, outline=GOLD, width=2, r=4)
    text(d, (80, 632), '이벤트 캘린더', 15, GOLD, True, 'mm')
    text(d, (1256, 712), '시안 · 퍼센트는 예시', 13, DIM, False, 'rs')
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    overview().save(OUT / '1_한눈에_보기.png')
    listing().save(OUT / '2_목록_4월_이즈미.png')
    panel().save(OUT / '3_본거지_달성률.png')
    print('ok', sorted(p.name for p in OUT.glob('*.png')))


if __name__ == '__main__':
    main()
