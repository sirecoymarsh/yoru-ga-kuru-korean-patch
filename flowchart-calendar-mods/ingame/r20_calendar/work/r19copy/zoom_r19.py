"""r19: zoomed crops of the native probe screenshots (증거/probe -> 증거/probe_zoom), 2x nearest-neighbour so the names
(카드 · 장면 쪽 첫 줄, 단계 목록, 서랍 장면 목록, 10월 마나미 레인의 갈래 줄) and the r18 panel / lock crops can be read.
(copy of r18 work/zoom_r18.py with the r19 name pages added). Read only elsewhere."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r19lib as L
from PIL import Image

src = L.EVID / 'probe'
dst = L.EVID / 'probe_zoom'
dst.mkdir(exist_ok=True)
CROPS = {
    # r19 names
    'zoom_card_main_title.png': ('cal_card_open.png', (175, 180, 1095, 360)),            # 9/15 아침 · 본편 · 3단계
    'zoom_stages_main.png': ('cal_stages.png', (150, 240, 1120, 470)),                   # 1. 쿄카와 ○ / 2. 갈래 1 쿄카와 ○
    'zoom_card_dungeon_title.png': ('cal_card_dungeon.png', (60, 200, 1210, 390)),       # 10월 중 · 던전 · 서양관 내부　틈 1 · 입구
    'zoom_stages_dungeon.png': ('cal_stages_dungeon.png', (60, 190, 1220, 520)),
    'zoom_drawer_walk.png': ('cal_drawer_walk.png', (120, 60, 1160, 640)),               # 마코토와 n번째 ●
    'zoom_scene_walk_title.png': ('cal_scene_walk.png', (250, 240, 1020, 400)),          # 6월 · 마나미 · 마코토와 동행 1번째
    'zoom_drawer_after.png': ('cal_drawer_after.png', (60, 40, 1220, 660)),              # n번째 ●
    'zoom_scene_after_title.png': ('cal_scene_after.png', (60, 180, 1220, 480)),         # 4월 · 이즈미 · 특훈 뒤 대화 1번째
    'zoom_oct_manami_rows.png': ('cal_lane_oct_manami_p1.png', (240, 145, 1040, 525)),   # 갈래 · 이즈미 친밀도 50 미만 이즈미와 1
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
