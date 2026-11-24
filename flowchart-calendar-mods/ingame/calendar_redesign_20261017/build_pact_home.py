# -*- coding: utf-8 -*-
"""Home 달성률 panel redesign, stage 1 (PACT 177 Game/Scenes/Common/AddArea.pactex). Stage only.

Claude Opus 5.5, 2026-10-17. User: 달성률 「텍스트만 있어서 정보 파악이 느려」 · 숫자 기준이 섞임 · 이름 누르는 창; 시안
시안/3_본거지_달성률.png approved (「왜 이리 멋져? 좋아 가자」).

Reads the installed runtime NightRemasterPact.afa (read-only) and writes, in this folder only:
  work/pact/original_pact_177.pactex   entry 177 exactly as installed
  work/pact/pact_177_home.pactex       the redesigned panel
  candidate/NightRemasterPact.afa      candidate archive (only entry 177 differs)
  work/pact/build_evidence.json        hashes, coordinates and the checks below

The panel group KR_HomeRate (rect, abs 0,20) keeps its title and its body text part; the body is hidden and becomes the
change key the AIN layer writes (KR_HVText). New children are placeholders the AIN layer fills (KR_HVApply):
  texts   KR_HR_* labels (static Korean) and values (empty here)
  images  KR_HR_Box2..8 / KR_HR_CalBox (construction-painted buttons; state 2 = cursor over),
          KR_HR_Bar* (construction-painted bars), KR_HR_Face2..8 (portrait CG set by code, scale 0.25)
Checks (asserted): runtime archive hash; decode->encode->decode round trip; only entry 177 differs; the parts code looks
up (KR_HomeRate, KR_HomeRateBody) keep their names and types; every Korean character is an FNL proxy with a glyph;
alice-tools parses the entry; every new part stays inside the panel (x 0-160, y 20-664); buttons do not overlap.
"""
from pathlib import Path
import copy, hashlib, json, sys

HERE = Path(__file__).resolve().parent
AN = HERE.parent / 'autonav_20261015'
sys.path.insert(0, str(AN / 'pact' / 'lib')); sys.path.insert(0, str(AN / 'pact')); sys.path.insert(0, str(HERE))
from codex_pact_helpers import (ex, encode, decode, read_afa3, rebuild, child, maybe, val, allparts,  # noqa: E402
                                setlist, ss, si, rename, txt_info, name, coords, scalar, add)
import render_layout_proof as proof  # noqa: E402
import build_pact_autonav as anb  # noqa: E402  (char_report, glyph_check, alice)
import hvlib as L  # noqa: E402

ENTRY = 177
ENTRY_NAME = 'Game/Scenes/Common/AddArea.pactex'
OUT = L.WORK / 'pact'
CAND = HERE / 'candidate'
ORIGIN = (0, 20)                         # KR_HomeRate abs position: children are placed relative to it
PANEL = (0, 20, 160, 664)                # the left margin above the 시스템 button (672)

WHITE = (238, 240, 248)
GRAY = (165, 170, 186)
SKY = (128, 224, 255)
GOLD = (255, 224, 96)


def st(size, color):
    return dict(size=size, color=color, edge=1.0, edge_color=(0, 0, 0), spacing=0, line_gap=4)


# abs layout (screen pixels) - the AIN layer uses the same numbers (claude_home_panel.jaf KR_HVRow / sizes)
ROW_Y0, ROW_STEP, ROW_H = 124, 44, 40
NAMES = {2: '이즈미', 3: '쿄카', 4: '마나미', 5: '마코토', 6: '신카이', 7: '호시카와', 8: '모모세'}
ALL = ['대사', 'CG', '회상', '엔딩']
ALL_Y0, ALL_STEP = 456, 30
CAL = (6, 588, 148, 40)
TEXTS = [  # name, text, style, x, y
    ('KR_HR_SecSave', '이 세이브', st(12, GRAY), 10, 52),
    ('KR_HR_EvLabel', '이벤트', st(14, WHITE), 10, 68),
    ('KR_HR_EvValue', '', st(14, SKY), 104, 68),
    ('KR_HR_Story', '', st(14, WHITE), 10, 98),
    ('KR_HR_SecAll', '모든 세이브 합산', st(12, GRAY), 10, 438),
]
for p, nm in NAMES.items():
    ry = ROW_Y0 + (p - 2) * ROW_STEP
    TEXTS += [(f'KR_HR_Name{p}', nm, st(14, WHITE), 40, ry + 5), (f'KR_HR_Pct{p}', '', st(13, SKY), 106, ry + 6)]
for j, nm in enumerate(ALL):
    y = ALL_Y0 + j * ALL_STEP
    TEXTS += [(f'KR_HR_AllName{j}', nm, st(13, GRAY), 10, y), (f'KR_HR_AllValue{j}', '', st(13, GRAY), 96, y)]
CAL_TEXT = ('KR_HR_CalText', '이벤트 캘린더', dict(size=16, color=(255, 240, 190), edge=0.0, edge_color=(0, 0, 0), spacing=0, line_gap=4))
IMAGES = [  # name, x, y, w, h, kind (box: takes the cursor; bar/face: lets it pass)
    ('KR_HR_EvBar', 10, 88, 140, 5, 'bar'),
    ('KR_HR_CalBox', CAL[0], CAL[1], CAL[2], CAL[3], 'box'),
]
for p in NAMES:
    ry = ROW_Y0 + (p - 2) * ROW_STEP
    IMAGES += [(f'KR_HR_Box{p}', 4, ry, 152, ROW_H, 'box'), (f'KR_HR_Face{p}', 8, ry + 4, 26, 32, 'face'),
               (f'KR_HR_Bar{p}', 40, ry + 28, 110, 5, 'bar')]
for j in range(len(ALL)):
    IMAGES.append((f'KR_HR_AllBar{j}', 10, ALL_Y0 + j * ALL_STEP + 19, 140, 4, 'bar'))
Z = dict(box=2, bar=3, face=3, text=4)
FACE_SCALE = 26.0 / 240.0                # the portrait CGs are 240 x 300 (the calendar's minis: 32 x 40 = 0.1333)
HIDDEN_AT_START = ['KR_HR_CalBox', 'KR_HR_CalText']     # shown by the AIN layer only while the home top menu waits


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def style_text(t, text=None, size=None, color=None, edge=None, edge_color=None, spacing=None, line_gap=None, **_):
    ti = txt_info(t); dec = child(ti, 'テキスト装飾')
    if text is not None: ss(ti, 'テキスト', text, True)
    if size is not None: si(dec, 'フォントサイズ', size)
    if color is not None: setlist(dec, 'フォント色', list(color))
    if edge is not None: si(dec, 'フォント縁取り', edge)
    if edge_color is not None: setlist(dec, 'フォント縁取り色', list(edge_color))
    if spacing is not None: si(dec, '字間隔', spacing)
    if line_gap is not None: si(dec, '行間隔', line_gap)


def ptype(t):
    return val(child(child(t, '種類別情報'), '通常状態'), 'パーツタイプ').value.decode('cp932')


def make(doc, fnl):
    parts = {name(t): t for t in allparts(doc.blocks[2].payload.children[0])}
    panel, title, body = parts['KR_HomeRate'], parts['KR_HomeRateTitle'], parts['KR_HomeRateBody']
    assert ptype(panel) == '矩形パーツ' and ptype(title) == 'テキストパーツ' and ptype(body) == 'テキストパーツ'
    assert coords(panel)[:2] == [float(ORIGIN[0]), float(ORIGIN[1])], coords(panel)
    cg_tpl = parts['ＣＧ_土台左']
    assert ptype(cg_tpl) == 'ＣＧパーツ' and maybe(cg_tpl, '子パーツ') is None
    si(body, '表示', 0)                                   # the body keeps the change key only
    made, rects = [], []

    def place(t, x, y, z):
        setlist(t, '座標', [float(x - ORIGIN[0]), float(y - ORIGIN[1]), int(z)])

    def new_text(n, text, style, x, y):
        t = copy.deepcopy(title); rename(t, n)
        style_text(t, text=text, **style)
        place(t, x, y, Z['text']); si(t, '表示', 0 if n in HIDDEN_AT_START else 1); si(t, 'オンカーソル透過', 1); si(t, 'クリック許可', 0)
        add(panel, t); made.append(n)
        w = fnl.width(text, style['size'], style['spacing'], style['edge'], 0.0) if text else 0
        rects.append(dict(name=n, kind='text', rect=[x, y, x + w, y + fnl.line_height(style['size'])], text=text))

    for n, text, style, x, y in TEXTS:
        new_text(n, text, style, x, y)
    n, text, style = CAL_TEXT
    w = fnl.width(text, style['size'], style['spacing'], style['edge'], 0.0)
    new_text(n, text, style, CAL[0] + (CAL[2] - w) / 2.0, CAL[1] + (CAL[3] - fnl.line_height(style['size'])) / 2.0)

    for n, x, y, w, h, kind in IMAGES:
        t = copy.deepcopy(cg_tpl); rename(t, n)
        ss(child(child(t, '種類別情報'), '通常状態'), 'ＣＧ名', '')
        # the template (ＣＧ_土台左) clips its CG to 160 x 720; a 240 x 300 portrait lost its right half (user 10-17 「얼굴 반쪽이
        # 가려지는데?」) -> no surface area: the whole CG / construction is drawn
        setlist(child(child(t, '種類別情報'), '通常状態'), 'サーフェイスエリア', [0, 0, 0, 0])
        place(t, x, y, Z[kind]); si(t, '表示', 0 if n in HIDDEN_AT_START else 1); si(t, 'クリック許可', 0)
        si(t, 'オンカーソル透過', 0 if kind == 'box' else 1)
        setlist(t, '拡大縮小', [FACE_SCALE, FACE_SCALE] if kind == 'face' else [1.0, 1.0])
        add(panel, t); made.append(n)
        rects.append(dict(name=n, kind=kind, rect=[x, y, x + w, y + h]))
    return made, rects


def checks(rects):
    out = [r['name'] for r in rects if not (PANEL[0] <= r['rect'][0] and r['rect'][2] <= PANEL[2]
                                            and PANEL[1] <= r['rect'][1] and r['rect'][3] <= PANEL[3])]
    assert not out, ('outside the panel', out)
    boxes = [r for r in rects if r['kind'] == 'box']
    ov = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            ax0, ay0, ax1, ay1 = a['rect']; bx0, by0, bx1, by1 = b['rect']
            if ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1:
                ov.append((a['name'], b['name']))
    assert not ov, ('buttons overlap', ov)


def main():
    OUT.mkdir(parents=True, exist_ok=True); CAND.mkdir(parents=True, exist_ok=True)
    ptr, rt = L.runtime(); src = rt / 'NightRemasterPact.afa'
    src_sha = sha(src)
    assert src_sha == L.BASE_PACT_SHA, ('runtime PACT moved', src_sha)
    arc = read_afa3(src); e = arc.entries[ENTRY]; assert e.name == ENTRY_NAME, e.name
    with src.open('rb') as f:
        f.seek(e.absolute_offset); raw = f.read(e.size)
    original_path = OUT / 'original_pact_177.pactex'; original_path.write_bytes(raw)
    original = ex.decode_ex(original_path); assert original.serialize_payload() == original.raw_payload
    doc = ex.decode_ex(original_path)
    fnl = proof.Fnl(rt / 'NightRemasterFont.fnl')
    made, rects = make(doc, fnl)
    checks(rects)
    payload = doc.serialize_payload()
    out = OUT / 'pact_177_home.pactex'; out.write_bytes(ex.encode_ex(doc.header, payload))
    reopened = ex.decode_ex(out)
    assert reopened.raw_payload == payload and reopened.serialize_payload() == payload, 'decode->encode round trip'
    assert reopened.header[:24] == original.header[:24]
    kept = {name(t): ptype(t) for t in allparts(reopened.blocks[2].payload.children[0]) if name(t) in ('KR_HomeRate', 'KR_HomeRateBody')}
    assert kept == {'KR_HomeRate': '矩形パーツ', 'KR_HomeRateBody': 'テキストパーツ'}, kept
    anb.alice('ex', 'dump', '-o', OUT / 'pact_177_home.x', out)
    dump = (OUT / 'pact_177_home.x').read_text(encoding='utf-8', errors='replace')
    assert all(n in dump for n in made), 'alice dump lacks a new part name'
    cand = CAND / 'NightRemasterPact.afa'
    arcrep = rebuild(src, cand, {ENTRY: out})
    texts = [t for _, t, _, _, _ in TEXTS if t] + [CAL_TEXT[1]]
    chars = anb.char_report(texts)
    glyphs = anb.glyph_check(rt / 'NightRemasterFont.fnl', texts)
    ev = dict(status='HOME_PANEL_PACT177_STAGED_NOT_INSTALLED', builder=L.AUTHOR, source=dict(runtime=str(rt), pact_sha256=src_sha),
              outputs={'original_pact_177.pactex': sha(original_path), 'pact_177_home.pactex': sha(out), 'NightRemasterPact.afa': sha(cand)},
              archive=arcrep, changed_entries=[ENTRY], round_trip_exact=True, alice_ex_dump_parsed=True, made=made,
              hidden_at_start=HIDDEN_AT_START, body_hidden=True, characters=chars, glyphs=glyphs, rects=rects,
              layout=dict(origin=ORIGIN, row_y0=ROW_Y0, row_step=ROW_STEP, row_h=ROW_H, all_y0=ALL_Y0, all_step=ALL_STEP, cal=CAL))
    L.writej(OUT / 'build_evidence.json', ev)
    print('OK', sha(cand), len(made), 'new parts on 177')


if __name__ == '__main__':
    main()
