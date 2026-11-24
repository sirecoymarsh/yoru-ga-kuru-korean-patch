"""r20: zoomed crops of the native probe screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour: the 「이벤트」 page of
the status window (two persons + the second opening), the partner labels (no hover, hover A, hover B, entered again), and the
r18/r19 crops kept from zoom_r19.py (panel before / after the replay). Read only elsewhere."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r20lib as L
from PIL import Image

src = L.EVID / 'probe'
dst = L.EVID / 'probe_zoom'
dst.mkdir(exist_ok=True)
CROPS = {
    # r20: the status page (panel at 192..530 x 64..512), the partner labels (above the portraits, y 490..548)
    'zoom_status_event_a.png': ('cal_status_event_a.png', (180, 20, 560, 520)),
    'zoom_status_event_b.png': ('cal_status_event_b.png', (180, 20, 560, 520)),
    'zoom_status_event_c.png': ('cal_status_event_c.png', (180, 20, 560, 520)),
    'zoom_status_event_dungeon.png': ('cal_status_event_dungeon.png', (180, 20, 560, 520)),
    'zoom_partner_nohover.png': ('cal_partner_nohover.png', (170, 480, 990, 720)),
    'zoom_partner_hover_a.png': ('cal_partner_hover_a.png', (170, 480, 990, 720)),
    'zoom_partner_hover_b.png': ('cal_partner_hover_b.png', (170, 480, 990, 720)),
    'zoom_partner_again.png': ('cal_partner_again.png', (170, 480, 990, 720)),
    # r18/r19 kept
    'zoom_home_before_panel.png': ('cal_home_before.png', (0, 0, 160, 390)),
    'zoom_home_after_panel.png': ('cal_home_after.png', (0, 0, 160, 390)),
}
out = {}
for name, (f, box) in CROPS.items():
    if not (src / f).exists():
        out[name] = dict(source=f, missing=True)
        continue
    im = Image.open(src / f).convert('RGB').crop(box)
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(dst / name)
    out[name] = dict(source=f, box=box, sha256=L.sha(dst / name))
L.writej(dst / 'crops.json', out)
print('\n'.join(out))
assert not any(v.get('missing') for v in out.values()), [k for k, v in out.items() if v.get('missing')]
