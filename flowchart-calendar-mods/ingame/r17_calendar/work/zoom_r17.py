"""r17: zoomed crops of the native probe screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour so the glyphs
(■ □ ▲ ● ○), the drawer rows and the panel 「전체」 value next to the summary's first line can be read. Read only elsewhere."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r17lib as L
from PIL import Image

src = L.EVID / 'probe'
dst = L.EVID / 'probe_zoom'
dst.mkdir(exist_ok=True)
CROPS = {
    'zoom_summary_with_panel.png': ('cal_summary.png', (0, 140, 960, 262)),     # panel 전체 row + summary first line
    'zoom_summary_out_line.png': ('cal_summary.png', (60, 520, 960, 600)),      # 던전 lane + 패널 밖 n/121
    'zoom_month_head_legend.png': ('cal_month.png', (90, 40, 940, 110)),
    'zoom_month_cells.png': ('cal_month.png', (90, 110, 900, 320)),
    'zoom_month_items.png': ('cal_month.png', (90, 340, 1190, 690)),
    'zoom_lane_drawer_rows.png': ('cal_lane.png', (40, 160, 1230, 510)),
    'zoom_apr_dungeon_lane.png': ('cal_lane_apr_dungeon.png', (60, 200, 1210, 460)),
    'zoom_memory_title_rows.png': ('cal_memory.png', (190, 40, 1080, 580)),
}
out = {}
for name, (f, box) in CROPS.items():
    im = Image.open(src / f).convert('RGB').crop(box)
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(dst / name)
    out[name] = dict(source=f, box=box, sha256=L.sha(dst / name))
L.writej(dst / 'crops.json', out)
print('\n'.join(out))
