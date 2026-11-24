# -*- coding: utf-8 -*-
"""User-facing picture of the list without spoilers (10-18): the 4월 · 이즈미 list from the probe, with the row-chip line (it names
companions who join later) cut out. Output: 증거/목록_4월_이즈미_보고용.png"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
src = Image.open(HERE / '증거' / 'probe' / 'lv_list_apr_izumi.png').convert('RGB')
top = src.crop((0, 0, 1280, 97))
rest = src.crop((0, 139, 1280, 720))
out = Image.new('RGB', (1280, top.height + rest.height), (6, 10, 26))
out.paste(top, (0, 0))
out.paste(rest, (0, top.height))
dest = HERE / '증거' / '목록_4월_이즈미_보고용.png'
out.save(dest)
print(dest, out.size)
