"""r18: zoomed crops of the native probe screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour so the glyphs
(■ □ ▲ ● ○), the drawer rows and the panel 「전체」 value next to the summary's first line can be read. Read only elsewhere."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r18lib as L
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
    # r18: the lock line instead of 「이 장면 재생」, the sandbox note on a ○ scene, the panel before / after the replay
    'zoom_card_locked_unseen.png': ('cal_card_locked_unseen.png', (130, 200, 1140, 500)),
    'zoom_card_locked_other.png': ('cal_card_locked_other.png', (80, 225, 1190, 480)),
    'zoom_event_open_note.png': ('cal_event_open.png', (170, 185, 1100, 520)),
    'zoom_home_before_panel.png': ('cal_home_before.png', (0, 0, 160, 390)),
    'zoom_home_after_panel.png': ('cal_home_after.png', (0, 0, 160, 390)),
    'zoom_home_midload_panel.png': ('cal_home_midload.png', (0, 0, 160, 390)),
}
out = {}
for name, (f, box) in CROPS.items():
    im = Image.open(src / f).convert('RGB').crop(box)
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    im.save(dst / name)
    out[name] = dict(source=f, box=box, sha256=L.sha(dst / name))
L.writej(dst / 'crops.json', out)
print('\n'.join(out))
