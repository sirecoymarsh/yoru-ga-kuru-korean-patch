"""r22: zoomed crops of the native chart screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour: a thumbnail cell, a small
cell and a locked cell of the target page, the header / tabs, the locked-cell notice, the scene page (chart branch). Read only
elsewhere."""
import sys, json
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r22lib as L
from PIL import Image

src = L.EVID / 'probe'
dst = L.EVID / 'probe_zoom'
dst.mkdir(exist_ok=True)
CROPS = {
    'zoom_chart_header_tabs.png': ('chart_tab_apr_p1.png', (0, 0, 1280, 110)),
    'zoom_chart_row1.png': ('chart_target_locked.png', (20, 110, 1260, 292)),
    'zoom_chart_row3_locked.png': ('chart_target_locked.png', (20, 474, 1260, 656)),
    'zoom_chart_row3_unlocked.png': ('chart_target_unlocked.png', (20, 474, 1260, 656)),
    'zoom_chart_row3_reverted.png': ('chart_target_reverted.png', (20, 474, 1260, 656)),
    'zoom_chart_bottom.png': ('chart_tab_apr_p1.png', (0, 650, 1280, 720)),
    'zoom_chart_locked_notice.png': ('chart_locked_notice.png', (80, 150, 1200, 560)),
    'zoom_chart_title_reset_confirm.png': ('chart_title_reset_confirm.png', (80, 150, 1200, 560)),
    'zoom_chart_detail_open.png': ('chart_detail_open.png', (100, 180, 1180, 530)),
    'zoom_chart_memory_tab.png': ('chart_tab_memory_p1.png', (20, 110, 1260, 420)),
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
