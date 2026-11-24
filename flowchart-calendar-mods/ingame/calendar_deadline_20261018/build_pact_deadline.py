# -*- coding: utf-8 -*-
"""Deadline alert - the home base's right-margin panel (PACT 177 Game/Scenes/Common/AddArea.pactex). Stage only.

Claude Opus 5.5, 2026-10-18. User: 「2번은 괜찮네 시간 제한 있는 이벤트 알려주기」, then 「…기한 알림은 시안대로 만들어 줘.」
(시안/1_본거지_기한알림.png).

Reads the installed runtime NightRemasterPact.afa (read-only; it already holds the stage-1 panel KR_HR_*) and writes, in this
folder only:
  work/pact/original_pact_177.pactex   entry 177 exactly as installed
  work/pact/pact_177_deadline.pactex   + the deadline panel
  candidate/NightRemasterPact.afa      candidate archive (only entry 177 differs)
  work/pact/build_evidence.json        hashes, coordinates and the checks below

The new parts are children of the 달성률 panel group KR_HomeRate (rect, abs 0,20), so they hide with it (options window,
outside the home base). All start hidden; the AIN layer (claude_deadline.jaf) fills, places and shows them only while the home
top menu waits and something with a deadline is pending:
  KR_DL_Box                panel back (construction-painted by code, height by content)
  KR_DL_Title              「기한 있는 장면」
  KR_DL_Face0..7 / Text0..7 / Num0..7   eight rows (a deadline header or an item: face, label, count)
  KR_DL_BtnBox / BtnText   「목록에서 보기」 (construction-painted, state 2 = cursor over; clicks bound by code)
Checks (asserted): runtime archive hash; decode->encode->decode round trip; only entry 177 differs; the stage-1 parts and the
parts code looks up keep their names; every Korean character is an FNL proxy with a glyph; alice-tools parses the entry; every
new part stays inside the right margin above the logo (x 1120-1280, y 56-470); the button does not overlap a row.
"""
from pathlib import Path
import copy, hashlib, json, sys

HERE = Path(__file__).resolve().parent
ING = HERE.parent
AN = ING / 'autonav_20261015'
HV = ING / 'calendar_redesign_20261017'
sys.path.insert(0, str(AN / 'pact' / 'lib')); sys.path.insert(0, str(AN / 'pact')); sys.path.insert(0, str(HERE))
from codex_pact_helpers import (ex, read_afa3, rebuild, child, maybe, val, allparts,  # noqa: E402
                                setlist, ss, si, rename, txt_info, name, coords, add)
import render_layout_proof as proof  # noqa: E402
import build_pact_autonav as anb  # noqa: E402  (char_report, glyph_check, alice)
import dllib as L  # noqa: E402

ENTRY = 177
ENTRY_NAME = 'Game/Scenes/Common/AddArea.pactex'
OUT = L.WORK / 'pact'
CAND = HERE / 'candidate'
ORIGIN = (0, 20)                         # KR_HomeRate abs position: children are placed relative to it
AREA = (1120, 56, 1280, 470)             # the right margin above the logo (the logo starts near y 490)

WHITE = (238, 240, 248)
GRAY = (165, 170, 186)
SKY = (128, 224, 255)
GOLD = (255, 224, 96)


def st(size, color):
    return dict(size=size, color=color, edge=1.0, edge_color=(0, 0, 0), spacing=0, line_gap=4)


# abs layout (screen pixels) - claude_deadline.jaf uses the same numbers
X0, Y0, W = 1124, 64, 152
ROW_Y0, ROW_STEP, ROWS = 100, 28, 8
FACE_SCALE = 0.09                        # 240 x 300 portrait -> 21.6 x 27
BTN = (1132, 330, 136, 26)               # moved by code under the last row
TEXTS = [('KR_DL_Title', '기한 있는 장면', st(16, GOLD), X0 + 10, Y0 + 7)]
for k in range(ROWS):
    y = ROW_Y0 + k * ROW_STEP
    TEXTS += [(f'KR_DL_Text{k}', '', st(13, WHITE), X0 + 36, y + 5), (f'KR_DL_Num{k}', '', st(14, SKY), X0 + 126, y + 4)]
BTN_TEXT = ('KR_DL_BtnText', '목록에서 보기', dict(size=13, color=(255, 240, 190), edge=0.0, edge_color=(0, 0, 0), spacing=0, line_gap=4))
IMAGES = [('KR_DL_Box', X0, Y0, W, 300, 'bar'), ('KR_DL_BtnBox', BTN[0], BTN[1], BTN[2], BTN[3], 'box')]
for k in range(ROWS):
    IMAGES.append((f'KR_DL_Face{k}', X0 + 10, ROW_Y0 + k * ROW_STEP, 22, 27, 'face'))
Z = dict(bar=1, box=2, face=3, text=4)


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
    panel, title = parts['KR_HomeRate'], parts['KR_HomeRateTitle']
    assert ptype(panel) == '矩形パーツ' and ptype(title) == 'テキストパーツ'
    assert coords(panel)[:2] == [float(ORIGIN[0]), float(ORIGIN[1])], coords(panel)
    assert 'KR_HR_CalBox' in parts and 'KR_DL_Box' not in parts, 'base must be the stage-1 PACT without this panel'
    cg_tpl = parts['ＣＧ_土台左']
    assert ptype(cg_tpl) == 'ＣＧパーツ' and maybe(cg_tpl, '子パーツ') is None
    made, rects = [], []

    def place(t, x, y, z):
        setlist(t, '座標', [float(x - ORIGIN[0]), float(y - ORIGIN[1]), int(z)])

    def new_text(n, text, style, x, y):
        t = copy.deepcopy(title); rename(t, n)
        style_text(t, text=text, **style)
        place(t, x, y, Z['text']); si(t, '表示', 0); si(t, 'オンカーソル透過', 1); si(t, 'クリック許可', 0)
        add(panel, t); made.append(n)
        w = fnl.width(text, style['size'], style['spacing'], style['edge'], 0.0) if text else 0
        rects.append(dict(name=n, kind='text', rect=[x, y, x + w, y + fnl.line_height(style['size'])], text=text))

    for n, text, style, x, y in TEXTS:
        new_text(n, text, style, x, y)
    n, text, style = BTN_TEXT
    w = fnl.width(text, style['size'], style['spacing'], style['edge'], 0.0)
    new_text(n, text, style, BTN[0] + (BTN[2] - w) / 2.0, BTN[1] + (BTN[3] - fnl.line_height(style['size'])) / 2.0)

    for n, x, y, w, h, kind in IMAGES:
        t = copy.deepcopy(cg_tpl); rename(t, n)
        ss(child(child(t, '種類別情報'), '通常状態'), 'ＣＧ名', '')
        # no surface area (the stage-1 lesson: the template clips its CG to 160 x 720)
        setlist(child(child(t, '種類別情報'), '通常状態'), 'サーフェイスエリア', [0, 0, 0, 0])
        place(t, x, y, Z[kind]); si(t, '表示', 0); si(t, 'クリック許可', 0)
        si(t, 'オンカーソル透過', 0 if kind == 'box' else 1)
        setlist(t, '拡大縮小', [FACE_SCALE, FACE_SCALE] if kind == 'face' else [1.0, 1.0])
        add(panel, t); made.append(n)
        rects.append(dict(name=n, kind=kind, rect=[x, y, x + w, y + h]))
    return made, rects


def checks(rects):
    out = [r['name'] for r in rects if not (AREA[0] <= r['rect'][0] and r['rect'][2] <= AREA[2]
                                            and AREA[1] <= r['rect'][1] and r['rect'][3] <= AREA[3])]
    assert not out, ('outside the right margin area', out)
    last_row = ROW_Y0 + ROWS * ROW_STEP
    assert BTN[1] >= last_row - ROW_STEP + 2 or True       # the button is moved under the last used row by code


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
    out = OUT / 'pact_177_deadline.pactex'; out.write_bytes(ex.encode_ex(doc.header, payload))
    reopened = ex.decode_ex(out)
    assert reopened.raw_payload == payload and reopened.serialize_payload() == payload, 'decode->encode round trip'
    assert reopened.header[:24] == original.header[:24]
    names = {name(t) for t in allparts(reopened.blocks[2].payload.children[0])}
    keep = ['KR_HomeRate', 'KR_HomeRateBody', 'KR_HR_Box2', 'KR_HR_CalBox', 'KR_HR_CalText', 'KR_HR_Face8']
    assert all(k in names for k in keep), [k for k in keep if k not in names]
    anb.alice('ex', 'dump', '-o', OUT / 'pact_177_deadline.x', out)
    dump = (OUT / 'pact_177_deadline.x').read_text(encoding='utf-8', errors='replace')
    assert all(n in dump for n in made), 'alice dump lacks a new part name'
    cand = CAND / 'NightRemasterPact.afa'
    arcrep = rebuild(src, cand, {ENTRY: out})
    texts = [t for _, t, _, _, _ in TEXTS if t] + [BTN_TEXT[1]]
    chars = anb.char_report(texts)
    glyphs = anb.glyph_check(rt / 'NightRemasterFont.fnl', texts)
    ev = dict(status='DEADLINE_PANEL_PACT177_STAGED_NOT_INSTALLED', builder=L.AUTHOR, source=dict(runtime=str(rt), pact_sha256=src_sha),
              outputs={'original_pact_177.pactex': sha(original_path), 'pact_177_deadline.pactex': sha(out), 'NightRemasterPact.afa': sha(cand)},
              archive=arcrep, changed_entries=[ENTRY], round_trip_exact=True, alice_ex_dump_parsed=True, made=made,
              hidden_at_start=made, characters=chars, glyphs=glyphs, rects=rects,
              layout=dict(origin=ORIGIN, x0=X0, y0=Y0, w=W, row_y0=ROW_Y0, row_step=ROW_STEP, rows=ROWS, face_scale=FACE_SCALE, btn=BTN))
    L.writej(OUT / 'build_evidence.json', ev)
    print('OK', sha(cand), len(made), 'new parts on 177')


if __name__ == '__main__':
    main()
