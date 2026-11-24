"""r21: zoomed crops of the native probe screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour: the r21 windows (the
chart notice, the unlock / revert notices, the long last_result window, the two confirmations) and the pending cases (our own
window, the character window outside the home menu), plus the r20 crops kept from zoom_r20.py when the r20 tour ran on the r21
candidate. Read only elsewhere."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r21lib as L
from PIL import Image

src = L.EVID / 'probe'
dst = L.EVID / 'probe_zoom'
dst.mkdir(exist_ok=True)
WIN = (80, 150, 1200, 560)          # the r21 windows sit in the middle of the screen (widest: the last_result window)
CROPS = {
    'zoom_mod_chart.png': ('mod_chart.png', WIN),
    'zoom_mod_unlock_all.png': ('mod_unlock_all.png', WIN),
    'zoom_mod_unlock_revert.png': ('mod_unlock_revert.png', WIN),
    'zoom_mod_last_result.png': ('mod_last_result.png', WIN),
    'zoom_mod_reset_confirm.png': ('mod_reset_confirm.png', WIN),
    'zoom_mod_restore_confirm.png': ('mod_restore_confirm.png', WIN),
    'zoom_mod_outside_home_pending.png': ('mod_outside_home_pending.png', WIN),
    # r20 crops (the r20 tour on the r21 candidate)
    'zoom_status_event_a.png': ('cal_status_event_a.png', (180, 20, 560, 520)),
    'zoom_partner_hover_a.png': ('cal_partner_hover_a.png', (170, 480, 990, 720)),
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
