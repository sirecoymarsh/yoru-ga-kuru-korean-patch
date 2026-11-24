"""Static layout proof for PACT 185 (Asra/Mods.pactex). NOT a game capture.

Draws the whole Mods page on a 1280x720 canvas the way Codex drew its
font_layout_proof.png (evidence/mod_tab_20260915/source/verify_mod_tab_20260915.py):
real glyph bitmaps from the shipped NightRemasterFont.fnl (face family 3, the
font type 259 used by every Mods-page text), glyph selection through the same
FNL proxy map, and the parts' own coordinates. In addition to Codex's version it
composites the shipped config CGs (background panel, tab plates, checkbox, slider
cursor, footer buttons, heading sparkle) from the runtime NightRemasterCG.afa and
draws the 1px text outline the parts ask for, so the picture is closer to the
screen. Sliders are drawn as their native hit area (the track CG is fully
transparent) plus the cursor CG at the left end.

Every part's box is returned so the build can assert overlaps and page bounds.
"""
from pathlib import Path
import json, math, struct, subprocess, sys, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'lib'))
from codex_pact_helpers import (ex, ENC, decode, child, maybe, val, name, scalar, coords)  # noqa: E402
from audit_message_pixel_widths import (parse_fnl_font, select_fnl_face, WidthMeasurer,  # noqa: E402
                                        sjis_bytes_to_fnl_index)
from afa3_inplace import BitStream, _read_dict, _read_encrypted_chars, _decrypt_name  # noqa: E402

ALICE = Path('P:/AI/Codex/projects/YoruGaKuru_KR_rebuild_20260830/tools/alice-tools-0.13.0/alice.exe')
TMP = HERE.parent / 'tmp' / 'proof_cg'
PANEL = (160, 0, 1120, 720)          # opaque body of シス／コンフィグ／背景 (alpha >= 250), measured
CG_NAMES = {
    'bg': 'シス／コンフィグ／背景.pcf',
    'icon': 'シス／コンフィグ／見出しアイコン.qnt',
    'tab': 'シス／コンフィグ／タブ／通常.qnt',
    'tab_off': 'シス／コンフィグ／タブ／無効.qnt',
    'check': 'シス／コンフィグ／チェックボックス／通常.qnt',
    'check_on': 'シス／コンフィグ／チェックボックス／チェック／通常.qnt',
    'cursor': 'シス／コンフィグ／バー／カーソル／通常.qnt',
    'SYS_ゲームを終了する': 'シス／コンフィグ／ボタン／ゲームを終了する／通常.qnt',
    'SYS_タイトル画面に戻る': 'シス／コンフィグ／ボタン／タイトルに戻る／通常.qnt',
    'SYS_ゲームに戻る': 'シス／コンフィグ／ボタン／ゲームに戻る／通常.qnt',
}
# Native plate sizes of the button CGs used on this page (alice cg convert of the runtime archive).
CG_SIZES = {'シス／コンフィグ／タブ': (192, 42), 'シス／コンフィグ／ボタン／ゲームを終了する': (150, 40),
            'シス／コンフィグ／ボタン／タイトルに戻る': (150, 40), 'シス／コンフィグ／ボタン／ゲームに戻る': (150, 40)}


def _cg_index(path):
    with open(path, 'rb') as f:
        head = f.read(12); index_size = struct.unpack_from('<I', head, 4)[0]
        f.seek(0); data = f.read(index_size + 8)
    bs = BitStream(data[12:]); bs.read_bits(1); dictionary = _read_dict(bs)
    psize = bs.read_u32le(); bs.read_u32le(); meta = zlib.decompress(bytes(bs.read_bits(8) for _ in range(psize)))
    ibs = BitStream(meta); ibs.read_bits(1); out = {}
    for _ in range(ibs.read_u32le()):
        ibs.read_bits(2); nm, _raw = _decrypt_name(_read_encrypted_chars(ibs), dictionary)
        ibs.read_u32le(); ibs.read_u32le(); off = ibs.read_u32le(); size = ibs.read_u32le()
        out[nm] = (index_size + 8 + off, size)
    return out


def load_cgs(runtime):
    """Extract and convert the few config CGs (read-only on the runtime archive)."""
    TMP.mkdir(parents=True, exist_ok=True)
    afa = Path(runtime) / 'NightRemasterCG.afa'; idx = None; out = {}
    for key, nm in CG_NAMES.items():
        png = TMP / f'{key}.png'
        if not png.exists():
            idx = idx or _cg_index(afa); off, size = idx[nm]
            raw = TMP / (key + '.' + nm.rsplit('.', 1)[1])
            with afa.open('rb') as f: f.seek(off); raw.write_bytes(f.read(size))
            env = dict(__import__('os').environ); env.update(TEMP=str(TMP), TMP=str(TMP))
            q = subprocess.run([str(ALICE), 'cg', 'convert', str(raw), str(png)], capture_output=True, env=env, timeout=60)
            assert q.returncode == 0 and png.exists(), (nm, q.stderr[-400:])
        out[key] = Image.open(png).convert('RGBA')
    return out


class Fnl:
    """Shipped FNL glyphs, face family 3 (font type 259), Korean via the proxy map."""

    def __init__(self, path):
        self.raw = Path(path).read_bytes(); _, self.faces = parse_fnl_font(Path(path), 3)
        self.table = {}; q = 20
        for fno in range(struct.unpack_from('<I', self.raw, 16)[0]):
            nf = struct.unpack_from('<I', self.raw, q)[0]; q += 4
            for fi in range(nf):
                hh, _u, n = struct.unpack_from('<III', self.raw, q); q += 12
                if fno == 3: self.table[fi] = (hh, [struct.unpack_from('<HII', self.raw, q + 10 * j) for j in range(n)])
                q += 10 * n
        self.proxy = {c: sjis_bytes_to_fnl_index(b) for c, b in ENC.items()}

    def measurer(self, size, spacing, edge, bold):
        face, den, _ = select_fnl_face(self.faces, size)
        return face, den, WidthMeasurer(face, den, self.proxy, spacing, edge, bold)

    def width(self, text, size, spacing=0, edge=0.0, bold=0.0):
        _, _, m = self.measurer(size, spacing, edge, bold)
        return m.measure(text, True)['max_width_px']

    def line_height(self, size):
        face, den, _ = select_fnl_face(self.faces, size); return face.height / den

    def draw(self, im, x, y, text, size, spacing=0, edge=0.0, bold=0.0, color=(255, 255, 255), edge_color=(0, 0, 0), line_gap=0):
        face, den, m = self.measurer(size, spacing, edge, bold); hh, es = self.table[face.face_index]
        pitch = size + line_gap; widths = []
        for row, line in enumerate(text.split('\n')):
            cx = x; cy = y + row * pitch
            for ch in line:
                w, pos, n = es[m.glyph_index(ch, True)]
                if pos and n:
                    rg = zlib.decompress(self.raw[pos:pos + n]); stride = len(rg) // hh
                    bits = np.unpackbits(np.frombuffer(rg, dtype=np.uint8).reshape(hh, stride), axis=1, bitorder='big')[::-1] * 255
                    mask = Image.fromarray(bits.astype(np.uint8), 'L').resize((max(1, round(bits.shape[1] / den)), max(1, round(hh / den))), Image.Resampling.LANCZOS)
                    ox = round(cx + edge); oy = round(cy)
                    if edge > 0:
                        k = 2 * math.ceil(edge) + 1
                        ring = mask.filter(ImageFilter.MaxFilter(k))
                        im.paste(tuple(edge_color) + (255,), (ox, oy), ring)
                    im.paste(tuple(color) + (255,), (ox, oy), mask)
                cx += w / den + m.constant_advance
            widths.append(cx - x)
        return max(widths), (len(text.split('\n')) - 1) * pitch + hh / den


def _text_style(dec):
    g = lambda k, d=0: scalar(val(dec, k)) if maybe(dec, k) is not None else d
    gl = lambda k, d: [scalar(i.value.payload) for i in val(dec, k).items] if maybe(dec, k) is not None else d
    return dict(size=g('フォントサイズ'), spacing=g('字間隔', g('文字間隔', 0)), line_gap=g('行間隔', 0), edge=float(g('フォント縁取り', 0)),
                bold=float(g('フォント太さ', 0)), color=tuple(gl('フォント色', [255, 255, 255])), edge_color=tuple(gl('フォント縁取り色', [0, 0, 0])))


def collect(doc):
    """Absolute geometry of every visible part on the page (debug tab is hidden at runtime)."""
    root = doc.blocks[2].payload.children[0]; parts = []

    def walk(t, ox, oy, group):
        c = coords(t); ax, ay = ox + c[0], oy + c[1]; nm = name(t)
        shown = scalar(val(t, '表示')) if maybe(t, '表示') is not None else 1
        info = maybe(t, '種類別情報'); typ = val(info, 'パーツタイプ').value.decode('cp932') if info is not None else ''
        scale = [scalar(i.value.payload) for i in val(t, '拡大縮小').items]
        mode = scalar(val(t, '原点座標モード')) if maybe(t, '原点座標モード') is not None else 1
        rec = dict(name=nm, type=typ, x=ax, y=ay, z=c[2], group=group, shown=shown, scale=scale, origin_mode=mode)
        if typ == 'チェックボックス':
            st = _text_style(info); w, h = [scalar(i.value.payload) for i in val(info, 'サイズ').items]
            rec.update(kind='checkbox', box=(w, h), text=decode(val(info, 'テキスト').value), style=st)
        elif typ == 'ボタン':
            # A button with a CG is drawn at the CG's own size (x scale); サイズ only applies to CG-less buttons.
            w, h = [scalar(i.value.payload) for i in val(info, 'サイズ').items]
            cgname = val(info, 'ＣＧ名').value.decode('cp932')
            if cgname: w, h = CG_SIZES.get(cgname, (w, h))
            rec.update(kind='button', size=(w * scale[0], h * scale[1]), cg=cgname,
                       enabled=scalar(val(info, '有効')) if maybe(info, '有効') is not None else 1)
        elif typ == '横スクロールバー':
            rec.update(kind='slider', size=(scalar(val(info, '長さ')) * scale[0], scalar(val(info, '幅')) * scale[1]))
        elif typ == '低レベルパーツ':
            st = maybe(info, '通常状態')
            if st is not None and val(st, 'パーツタイプ').value.decode('cp932') == 'テキストパーツ':
                rec.update(kind='text', text=decode(val(st, 'テキスト').value), style=_text_style(child(st, 'テキスト装飾')))
            else:
                rec.update(kind='group' if maybe(t, '子パーツ') is not None and child(t, '子パーツ').children else 'surface')
        else:
            rec.update(kind='group')
        parts.append(rec)
        kids = maybe(t, '子パーツ')
        if kids is not None:
            for k in kids.children: walk(k, ax, ay, nm)

    for k in child(root, '子パーツ').children: walk(k, 0, 0, 'ルートパーツ')
    return parts


def boxes(parts, fnl):
    """Ink-free layout boxes: text = measured advance x line height; checkbox = box + label."""
    out = []
    for p in parts:
        if p['name'] == 'デバッグボタン' or not p['shown']: continue    # hidden by C_ConfigView unless debug display is on
        k = p.get('kind')
        if k == 'text':
            st = p['style']; lines = p['text'].split('\n')
            w = max(fnl.width(s, st['size'], st['spacing'], st['edge'], st['bold']) for s in lines)
            h = (len(lines) - 1) * (st['size'] + st['line_gap']) + fnl.line_height(st['size'])
            x0 = p['x'] - w / 2 if p['origin_mode'] == 2 else p['x']     # mode 2 (tab labels): centred on x (approximation)
            if w > 0: out.append(dict(p, rect=(x0, p['y'], x0 + w, p['y'] + h)))
        elif k == 'checkbox':
            st = p['style']; bw, bh = p['box']; w = fnl.width(p['text'], st['size'], st['spacing'], st['edge'], st['bold'])
            out.append(dict(p, rect=(p['x'], p['y'], p['x'] + bw + w, p['y'] + bh)))
        elif k in ('button', 'slider'):
            w, h = p['size']; out.append(dict(p, rect=(p['x'], p['y'], p['x'] + w, p['y'] + h)))
    return out


def icon_rects():
    """背景_星 draws two 58x53 heading sparkles at (320+13, 139) and (320+13, 459)."""
    return [(333, 139, 391, 192), (333, 459, 391, 512)]


def render(pactex, runtime, out_png, mark=(), title='', notes=(), legend_h=0, zoom=None):
    """zoom = (x0, y0, x1, y1, scale): append a magnified copy of that page region under the legend."""
    doc = ex.decode_ex(Path(pactex)); fnl = Fnl(Path(runtime) / 'NightRemasterFont.fnl'); cg = load_cgs(runtime)
    assert cg['tab'].size == CG_SIZES['シス／コンフィグ／タブ'] and cg['SYS_ゲームに戻る'].size == (150, 40)
    assert cg['check'].size == (32, 32) and cg['bg'].size == (1280, 720)
    parts = collect(doc); bx = boxes(parts, fnl)
    im = Image.new('RGBA', (1280, 720 + legend_h), (40, 40, 44, 255))
    # outside the panel the config page is transparent; show it as a neutral checker
    d0 = ImageDraw.Draw(im)
    for yy in range(0, 720 + legend_h, 16):
        for xx in range(0, 1280, 16):
            if (xx // 16 + yy // 16) % 2: d0.rectangle((xx, yy, xx + 15, yy + 15), fill=(52, 52, 58, 255))
    im.alpha_composite(cg['bg'], (0, 0))
    for r in icon_rects(): im.alpha_composite(cg['icon'], (r[0], r[1]))
    draw = ImageDraw.Draw(im)
    for p in parts:
        if p['name'] == 'デバッグボタン' or not p['shown']: continue
        k = p.get('kind')
        if k == 'button':
            key = p['name'] if p['name'] in cg else ('tab' if p['enabled'] else 'tab_off')
            plate = cg[key]; w, h = p['size']; w, h = round(w), round(h)
            if plate.size != (w, h): plate = plate.resize((w, h), Image.Resampling.LANCZOS)
            im.alpha_composite(plate, (round(p['x']), round(p['y'])))
        elif k == 'slider':
            w, h = p['size']; x, y = p['x'], p['y']
            draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(70, 110, 190, 255), width=1)
            cur = cg['cursor'].resize((25, round(h)), Image.Resampling.LANCZOS); im.alpha_composite(cur, (round(x), round(y)))
        elif k == 'checkbox':
            im.alpha_composite(cg['check'], (round(p['x']), round(p['y'])))
            st = p['style']; bw, bh = p['box']; ty = p['y'] + (bh - fnl.line_height(st['size'])) / 2
            fnl.draw(im, p['x'] + bw, ty, p['text'], st['size'], st['spacing'], st['edge'], st['bold'], st['color'], st['edge_color'])
        elif k == 'text':
            st = p['style']; x0 = p['x']
            if p['origin_mode'] == 2: x0 -= fnl.width(p['text'], st['size'], st['spacing'], st['edge'], st['bold']) / 2
            fnl.draw(im, x0, p['y'], p['text'], st['size'], st['spacing'], st['edge'], st['bold'], st['color'], st['edge_color'], st['line_gap'])
    mono = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 12)
    draw = ImageDraw.Draw(im)
    marked = [b for b in bx if b['name'] in mark]
    for b in marked:   # thin corner brackets just outside each new part, so the narrow gaps stay visible
        x0, y0, x1, y1 = b['rect']; x0 -= 1; y0 -= 1; x1 += 1; y1 += 1; k = 7; c = (255, 60, 170, 255)
        for (ax, ay, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
            draw.line((ax, ay, ax + sx * k, ay), fill=c, width=1); draw.line((ax, ay, ax, ay + sy * k), fill=c, width=1)
    if legend_h:
        legend = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 13)   # legend only; the page itself uses the shipped FNL
        draw.rectangle((0, 720, 1279, 719 + legend_h), fill=(20, 22, 30, 255))
        draw.text((8, 724), title or 'PACT 185 Asra/Mods - SHIPPED FNL GLYPHS + SHIPPED CONFIG CG + PART GEOMETRY / NOT A GAME CAPTURE', font=mono, fill=(200, 210, 225, 255))
        for i, line in enumerate(notes): draw.text((8, 742 + 18 * i), line, font=legend, fill=(255, 140, 200, 255) if i == 0 else (200, 210, 225, 255))
    if zoom:
        x0, y0, x1, y1, sc = zoom
        crop = im.crop((x0, y0, x1, y1)); crop = crop.resize((round((x1 - x0) * sc), round((y1 - y0) * sc)), Image.Resampling.NEAREST)
        full = Image.new('RGBA', (1280, im.height + crop.height + 22), (20, 22, 30, 255)); full.alpha_composite(im, (0, 0))
        ImageDraw.Draw(full).text((8, im.height + 4), f'x{sc} zoom of page region x {x0}-{x1}, y {y0}-{y1} (same render)', font=mono, fill=(200, 210, 225, 255))
        full.alpha_composite(crop, ((1280 - crop.width) // 2, im.height + 20)); im = full
    im.convert('RGB').save(out_png)
    return parts, bx


if __name__ == '__main__':
    rt = Path(json.loads(Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908/ui_cumulative/current.json').read_text(encoding='utf-8'))['runtime'])
    parts, bx = render(sys.argv[1], rt, sys.argv[2], mark=sys.argv[3:])
    for b in sorted(bx, key=lambda b: (b['rect'][1], b['rect'][0])):
        print('%-34s %-10s %7.1f %7.1f %7.1f %7.1f' % (b['name'], b['kind'], *b['rect']))
