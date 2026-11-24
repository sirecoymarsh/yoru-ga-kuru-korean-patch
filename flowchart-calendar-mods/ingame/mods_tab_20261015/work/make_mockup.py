# -*- coding: utf-8 -*-
"""10-16: before / after mock-up sheet for the user (「시안으로 보여줘」): the two in-game captures with numbered callouts, and the
Windows confirmation dialog before / after drawn as a mock (the probe captured the dialog text, not the window)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
BEFORE = HERE.parent / 'autonav_20261015' / '증거' / 'probe' / 'an_mods_before.png'
AFTER = HERE / '증거' / 'probe' / 'md_mods_a.png'
ITEMS = HERE / '증거' / 'probe' / 'md_items.png'
OUT = HERE / '증거' / '시안_모드탭_전후.png'
F = 'C:/Windows/Fonts/malgun.ttf'
FB = 'C:/Windows/Fonts/malgunbd.ttf'


def font(size, bold=False):
    return ImageFont.truetype(FB if bold else F, size)


RED = (255, 84, 120)
GREEN = (80, 230, 140)
INK = (230, 236, 250)
DIM = (150, 164, 196)
BG = (16, 20, 36)


def badge(d, x, y, text, color):
    r = 17
    d.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=(255, 255, 255), width=2)
    f = font(19, True)
    w = d.textlength(text, font=f)
    d.text((x - w / 2, y - 14), text, font=f, fill=(20, 20, 30))


def box(d, rect, color, width=3, dash=False):
    x0, y0, x1, y1 = rect
    if not dash:
        d.rectangle(rect, outline=color, width=width)
        return
    step = 12
    for x in range(int(x0), int(x1), step * 2):
        d.line((x, y0, min(x + step, x1), y0), fill=color, width=width)
        d.line((x, y1, min(x + step, x1), y1), fill=color, width=width)
    for y in range(int(y0), int(y1), step * 2):
        d.line((x0, y, x0, min(y + step, y1)), fill=color, width=width)
        d.line((x1, y, x1, min(y + step, y1)), fill=color, width=width)


def annotate(path, marks, color):
    im = Image.open(path).convert('RGB')
    d = ImageDraw.Draw(im)
    for rect, label, at, dash in marks:
        if rect:
            box(d, rect, color, dash=dash)
        badge(d, at[0], at[1], label, color)
    return im


def legend(d, x, y, title, rows, color, width):
    d.text((x, y), title, font=font(26, True), fill=INK)
    y += 44
    for label, text in rows:
        badge(d, x + 18, y + 16, label, color)
        lines = text.split('\n')
        for k, line in enumerate(lines):
            d.text((x + 48, y + 2 + k * 28), line, font=font(20, k == 0), fill=INK if k == 0 else DIM)
        y += 28 * len(lines) + 18
    return y


def dialog(text, title='밤이 온다! -Square of the MOON- Remastered'):
    w, h = 460, 190
    im = Image.new('RGB', (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), outline=(120, 120, 120))
    d.rectangle((1, 1, w - 2, 34), fill=(243, 243, 243))
    d.text((12, 7), title, font=font(14), fill=(30, 30, 30))
    d.line((w - 26, 12, w - 14, 24), fill=(60, 60, 60), width=2)
    d.line((w - 26, 24, w - 14, 12), fill=(60, 60, 60), width=2)
    d.ellipse((22, 58, 58, 94), fill=(30, 110, 210))
    d.text((33, 59), '?', font=font(24, True), fill=(255, 255, 255))
    for k, line in enumerate(text.split('\n')):
        d.text((76, 52 + k * 24), line, font=font(15), fill=(20, 20, 20))
    d.rectangle((0, h - 52, w - 1, h - 1), fill=(240, 240, 240))
    for k, b in enumerate(('확인', '취소')):
        x0 = w - 200 + k * 96
        d.rectangle((x0, h - 40, x0 + 86, h - 12), fill=(253, 253, 253), outline=(0, 120, 215) if k == 0 else (180, 180, 180), width=2 if k == 0 else 1)
        tw = d.textlength(b, font=font(14))
        d.text((x0 + 43 - tw / 2, h - 36), b, font=font(14), fill=(20, 20, 20))
    return im


def main():
    before_marks = [
        ((4, 14, 162, 388), 'A', (140, 30), False),
        ((655, 192, 690, 232), 'B', (712, 200), False),
        ((360, 86, 812, 108), 'C', (838, 97), False),
        ((172, 655, 600, 716), 'D', (624, 668), False),
    ]
    after_marks = [
        ((370, 18, 1074, 58), '1', (1094, 38), False),
        ((372, 66, 470, 98), '2', (350, 108), False),
        ((488, 104, 672, 148), '3', (690, 104), False),
        ((478, 410, 682, 434), '4', (700, 422), False),
        ((372, 282, 935, 326), '5', (955, 300), False),
        ((4, 14, 162, 388), '6', (140, 30), True),
    ]
    b = annotate(BEFORE, before_marks, RED)
    a = annotate(AFTER, after_marks, GREEN)
    LW = 600
    W = 1280 + LW + 60
    H = 70 + 720 + 60 + 720 + 90 + 230 + 40
    sheet = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((30, 18), '모드 탭 시안 — 실제 게임 화면(격리 사본) · 위: 지금, 아래: 바뀐 뒤', font=font(28, True), fill=INK)
    y = 70
    d.text((30, y - 2), '지금', font=font(22, True), fill=RED)
    sheet.paste(b, (30, y + 30))
    legend(d, 30 + 1280 + 30, y + 30, '지금 문제', [
        ('A', '달성률 패널이 왼쪽 탭을 가림\n홈에서 옵션을 열면 늘 이렇게'),
        ('B', '슬라이더에 바가 없음\n화살표만 떠 있어 값 위치가 안 보임'),
        ('C', '하늘색 안내문이 여기저기\n제목처럼 보여서 눈이 분산'),
        ('D', '오토 내비 설명이\n아래 단추 줄 옆까지 밀려남'),
    ], RED, LW)
    y += 30 + 720 + 40
    d.text((30, y - 2), '바뀐 뒤', font=font(22, True), fill=GREEN)
    sheet.paste(a, (30, y + 30))
    legend(d, 30 + 1280 + 30, y + 30, '바뀌는 것', [
        ('1', '단추 넷을 맨 위 한 줄로\n저장 화면 · 자동 회복 · 용어 표기 · 플레이 정보'),
        ('2', '구역마다 제목\n보상 배율 · 오토 내비게이션 · 전투 · 던전 · 편의'),
        ('3', '슬라이더 바\n손잡이까지 차오름(다른 옵션 탭과 같은 그림)'),
        ('4', '전투 속도 단계 글자\n기본 · 2배 … 5배'),
        ('5', '안내문은 짧게, 차분한 색으로'),
        ('6', '옵션을 연 동안 달성률 패널 숨김\n홈으로 돌아가면 다시 보임'),
    ], GREEN, LW)
    y += 30 + 720 + 50
    d.text((30, y), '게임 종료 · 타이틀로 확인 창 (창 모양은 모형, 글자는 실제 값)', font=font(22, True), fill=INK)
    broken = '?귽긣깑됪뽋궸뽣귟귏궥궔갎\n\n겍긜?긳궠귢궲궋궶궋긢??궼렪귦귢귏궥'
    fixed = '타이틀 화면으로 돌아가시겠습니까?\n\n※저장하지 않은 데이터는 사라집니다'
    d1 = dialog(broken)
    d2 = dialog(fixed)
    sheet.paste(d1, (30, y + 44))
    d.text((30, y + 44 + 196), '지금: 깨진 글자 (오늘 PV 사본에서 읽은 그대로)', font=font(18), fill=RED)
    sheet.paste(d2, (560, y + 44))
    d.text((560, y + 44 + 196), '바뀐 뒤: 한국어 (시험에서 창에 들어간 글자를 읽어 확인)', font=font(18), fill=GREEN)
    d.text((1100, y + 60), '같은 방식으로 바뀌는 창\n· 게임을 종료하시겠습니까?\n· 세이브 · 불러오기 오류 등\n  모두 42곳', font=font(19), fill=INK)
    sheet.save(OUT)
    small = sheet.resize((W // 2, H // 2), Image.Resampling.LANCZOS)
    small.save(OUT.with_name('시안_모드탭_전후_작게.png'))
    print('ok', OUT, sheet.size)


if __name__ == '__main__':
    main()
