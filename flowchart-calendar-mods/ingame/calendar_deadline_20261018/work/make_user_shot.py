# -*- coding: utf-8 -*-
"""User-facing pictures without spoilers (10-18): the probe's 5/20 shots show companions who join later (the user's play is
before 5/19). Panel: its top only (title, the 5/31 header, 이즈미 · 쿄카 rows). List: the title and month chips, then the head
and the 이즈미 · 쿄카 rows (the row-chip line and the 마나미 rows are cut). Output: 증거/기한알림_보고용.png"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
P = HERE / '증거' / 'probe'
home = Image.open(P / 'dl_home_panel.png').convert('RGB')
lst = Image.open(P / 'dl_list_deadline.png').convert('RGB')
panel = home.crop((1120, 60, 1280, 183))                     # title, the 5/31 header, 이즈미, 쿄카 (row 3 starts at 184)
top = lst.crop((0, 0, 1280, 97))                             # title + month chips (기한 chip)
rows = lst.crop((0, 139, 1280, 614))                         # head + rows 0-12 (이즈미 7, 쿄카 6) + the preview
W = 1280 + 24 + panel.width
H = max(top.height + rows.height, panel.height * 2 + 40)
out = Image.new('RGB', (W, H), (6, 10, 26))
out.paste(top, (0, 0))
out.paste(rows, (0, top.height))
big = panel.resize((panel.width * 2, panel.height * 2), Image.LANCZOS)
out = out.resize((W, H))
canvas = Image.new('RGB', (1280 + 24 + big.width, max(H, big.height + 40)), (6, 10, 26))
canvas.paste(out.crop((0, 0, 1280, H)), (0, 0))
canvas.paste(big, (1280 + 24, 30))
d = ImageDraw.Draw(canvas)
d.text((1280 + 24, 8), 'home panel (x2)', fill=(150, 150, 158))
dest = HERE / '증거' / '기한알림_보고용.png'
canvas.save(dest)
print(dest, canvas.size)
