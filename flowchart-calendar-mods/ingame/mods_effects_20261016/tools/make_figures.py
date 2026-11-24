"""Side-by-side evidence figures (off / on) from the probe screenshots. Writes into 증거/그림/."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
SHOTS = HERE / '증거' / 'shots'
OUT = HERE / '증거' / '그림'
OUT.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf', 26)


def latest(prefix):
    return sorted(p for p in SHOTS.iterdir() if p.name.startswith(prefix + '_'))[-1]


def run_dir(name):
    return SHOTS / name


def panel(path, label, crop=None, scale=0.5):
    im = Image.open(path).convert('RGB')
    if crop:
        im = im.crop(crop)
    else:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    top = 44
    out = Image.new('RGB', (im.width, im.height + top), 'white')
    out.paste(im, (0, top))
    ImageDraw.Draw(out).text((8, 6), label, fill='black', font=FONT)
    return out


def row(panels, name):
    gap = 12
    w = sum(p.width for p in panels) + gap * (len(panels) - 1)
    h = max(p.height for p in panels)
    out = Image.new('RGB', (w, h), 'white')
    x = 0
    for p in panels:
        out.paste(p, (x, 0))
        x += p.width + gap
    out.save(OUT / name)
    print(OUT / name)


off = run_dir('off_20261016_003445')
on = run_dir('on_20261016_010331')
row([panel(off / 'pe_dialog_1.png', '끔: 해제할 캐릭터 선택 창'), panel(off / 'pe_msgdlg_3.png', '끔: 해제 실패 → 독'),
     panel(on / 'pe_on_after_t1.png', '켬: 「함정 해제 성공 · 피해 없음」')], '함정_즉시_해체.png')
row([panel(off / 'pe_result_b1.png', '끔: 전투가 일어남(결과 화면)'), panel(on / 'pe_on_after_e1.png', '켬: 전투 없이 「즉시 처치 · 획득 보상」')],
    '일반_적_즉시_처치.png')
rt = latest('routetoggle')
mm = (530, 415, 815, 700)
row([panel(rt / 'pe_rt_on_2.png', '켬', crop=mm), panel(rt / 'pe_rt_off_1.png', '끔', crop=mm), panel(rt / 'pe_rt_off_2.png', '끔(한 칸 더)', crop=mm),
     panel(rt / 'pe_rt_on_3.png', '다시 켬', crop=mm), panel(off / 'pe_off_start.png', '옛 세이브+끔: 시작', crop=mm),
     panel(off / 'pe_off_after_t1.png', '옛 세이브+끔: 9칸 뒤', crop=mm)], '다음_층_경로_표시.png')
row([panel(run_dir('speed1_20261016_012500') / 'pe_result_b1.png', '1배: 적 1마리(달조각 원값 32)'),
     panel(run_dir('rates20battle_20261016_011411') / 'pe_result_b1.png', '20배: 같은 꼴 적 1마리')], '보상_배율_전투결과.png')
row([panel(run_dir('sweep_20261016_010507') / 'pe_dialog_1.png', '켬: 소탕 확인 창'),
     panel(run_dir('sweep_20261016_010507') / 'pe_sweep_start.png', '켬: 「자동 소탕」 단추'),
     panel(off / 'pe_off_start.png', '끔: 단추 없음')], '소탕_버튼.png')
q = latest('quick')
s1 = run_dir('speed1_20261016_012500')
row([panel(s1 / 'pe_battle_b1.png', '기본(2배): 전투 화면'), panel(q / 'pe_battle_b1.png', '이펙트 보지 않기: 전투 화면(내부 그림)')], '전투_화면.png')
