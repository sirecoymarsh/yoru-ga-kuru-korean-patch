"""r23: zoomed crops of the native screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour: the moons with the moon text
(two heroines, page 1 and the hover preview; the man's page 1 without one; the dungeon's page 1), the top of the 「이벤트」 page
(two heroines, the man, the dungeon). Read only elsewhere."""
import sys, json
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r23lib as L
from PIL import Image

src = L.EVID / 'probe'
dst = L.EVID / 'probe_zoom'
dst.mkdir(exist_ok=True)
MOON = (500, 55, 740, 170)             # the status root is at (160, 0): moons 534,66 / label 534,96 / our text 534,114
PAGE4 = (185, 60, 540, 250)            # the top of the 「이벤트」 page: title, the affinity block, the first r20 lines
CROPS = {
    'zoom_feel_moon_heroine_a_p1.png': ('cal_feel_heroine_a_p1.png', MOON),
    'zoom_feel_moon_heroine_a_preview.png': ('cal_feel_heroine_a_preview.png', MOON),
    'zoom_feel_moon_heroine_b_p1.png': ('cal_feel_heroine_b_p1.png', MOON),
    'zoom_feel_moon_heroine_b_preview.png': ('cal_feel_heroine_b_preview.png', MOON),
    'zoom_feel_moon_man_p1.png': ('cal_status_p1.png', MOON),
    'zoom_feel_page4_heroine_a.png': ('cal_status_event_c.png', PAGE4),
    'zoom_feel_page4_heroine_b.png': ('cal_feel_heroine_b_p4.png', PAGE4),
    'zoom_feel_page4_man.png': ('cal_status_event_a.png', PAGE4),
    # the dungeon's status window sits at the same place (its root at 160,0 as at home: the probe logged the moon text at 374,114
    # under that root, and the shots show the same frame)
    'zoom_feel_moon_dungeon_p1.png': ('cal_feel_dungeon_p1.png', MOON),
    'zoom_feel_page4_dungeon.png': ('cal_status_event_dungeon.png', PAGE4),
}
out = {}
for name, (shot, box) in CROPS.items():
    p = src / shot
    if not p.exists():
        out[name] = 'missing ' + shot
        continue
    im = Image.open(p).crop(box)
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(dst / name)
    out[name] = L.sha(dst / name)
print(json.dumps(out, ensure_ascii=False, indent=1))
