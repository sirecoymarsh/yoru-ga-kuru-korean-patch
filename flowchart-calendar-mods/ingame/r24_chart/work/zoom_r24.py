"""r24: zoomed crops of the native chart screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour: the three top buttons,
the target page's rows locked (names, conditions, the empty frame) / after 「전체 개방」 / after 「다시 가리기」, the header with
「전체 개방」, the legend, the locked cell's detail page, the 회상 tab's locked frames, the chart back after a replay (the played
cell's gold border; title and home). Read only elsewhere."""
import sys, json
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r24lib as L
from PIL import Image

src = L.EVID / 'probe'
dst = L.EVID / 'probe_zoom'
dst.mkdir(exist_ok=True)
BUTTONS = (860, 4, 1270, 60)
ROW1 = (20, 110, 1260, 292)
ROW2 = (20, 292, 1260, 474)
HEADER = (0, 0, 700, 110)
LEGEND = (0, 650, 700, 716)
DIALOG = (195, 220, 1070, 485)
CROPS = {
    'zoom_chart_buttons.png': ('chart_target_locked.png', BUTTONS),
    'zoom_chart_locked_row1.png': ('chart_target_locked.png', ROW1),
    'zoom_chart_locked_row2.png': ('chart_target_locked.png', ROW2),
    'zoom_chart_button_all_row1.png': ('chart_button_all.png', ROW1),
    'zoom_chart_button_all_row2.png': ('chart_button_all.png', ROW2),
    'zoom_chart_button_hide_row1.png': ('chart_button_hide.png', ROW1),
    'zoom_chart_button_hide_row2.png': ('chart_button_hide.png', ROW2),
    'zoom_chart_header_all.png': ('chart_button_all.png', HEADER),
    'zoom_chart_header_hidden.png': ('chart_button_hide.png', HEADER),
    'zoom_chart_legend.png': ('chart_target_locked.png', LEGEND),
    'zoom_chart_locked_detail.png': ('chart_locked_detail.png', DIALOG),
    'zoom_chart_memory_row2.png': ('chart_tab_memory_p1.png', ROW2),
    'zoom_chart_title_reset_confirm.png': ('chart_title_reset_confirm.png', DIALOG),
    'zoom_chart_resumed_row1.png': ('chart_resumed.png', ROW1),
    'zoom_chart_resumed_header.png': ('chart_resumed.png', HEADER),
    'zoom_chart_home_resumed_row1.png': ('chart_home_resumed.png', ROW1),
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
