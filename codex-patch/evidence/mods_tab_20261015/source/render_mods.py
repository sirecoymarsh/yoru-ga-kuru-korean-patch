"""Static proof of the redesigned Mods page (NOT a game capture): shipped FNL glyphs, shipped config CGs, the parts'
own geometry, plus what the shared renderer does not draw - the heading sparkles (背景_星 steps), the slider tracks
(dim + filled 'シス／コンフィグ／バー' gauges) with the cursor at a sample value, and sample check states.
usage: python render_mods.py <pactex> <out.png>"""
from pathlib import Path
import json, sys

HERE = Path(__file__).resolve().parent
AN = HERE.parent / 'autonav_20261015'
sys.path.insert(0, str(AN / 'pact' / 'lib')); sys.path.insert(0, str(AN / 'pact'))
from codex_pact_helpers import ex, child, maybe, val, name, scalar, coords  # noqa: E402
import render_layout_proof as proof  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SAMPLE_RATE = {'KR_Multiplier_EX': 1.0, 'KR_Multiplier_Training': 4 / 19, 'KR_Multiplier_Money': 0.0,
               'KR_Multiplier_PairTraining': 9 / 19, 'KR_CheatSpeed': 1.0}
SAMPLE_VALUE = {'KR_Multiplier_Value_EX': '20배', 'KR_Multiplier_Value_Training': '5배', 'KR_Multiplier_Value_Money': '1배',
                'KR_Multiplier_Value_PairTraining': '10배', 'KR_CheatSpeedValue': '5배'}
SAMPLE_CHECKED = {'KR_NavIzumi', 'KR_CheatRoute', 'KR_CheatSweep', 'KR_SmartAutoToggle', 'KR_AutoEquipToggle', 'KR_HomeRateToggle'}


def load_extra_cgs(runtime):
    extra = {'bar': 'シス／コンフィグ／バー.qnt', 'icon': 'シス／コンフィグ／見出しアイコン.qnt'}
    proof.CG_NAMES.update(extra)
    return proof.load_cgs(runtime)


def render(pactex, out_png, runtime=None):
    runtime = runtime or Path(json.loads(Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908/ui_cumulative/current.json')
                                         .read_text(encoding='utf-8-sig'))['runtime'])
    doc = ex.decode_ex(Path(pactex)); fnl = proof.Fnl(Path(runtime) / 'NightRemasterFont.fnl'); cg = load_extra_cgs(runtime)
    parts = proof.collect(doc)
    im = Image.new('RGBA', (1280, 720), (40, 40, 44, 255))
    im.alpha_composite(cg['bg'], (0, 0))
    root = doc.blocks[2].payload.children[0]
    nodes = {}

    def walk(t, ox, oy):
        c = coords(t) if maybe(t, '座標') is not None else [0, 0, 0]
        nodes[name(t)] = (t, ox + c[0], oy + c[1])
        kids = maybe(t, '子パーツ')
        if kids:
            for k in kids.children: walk(k, ox + c[0], oy + c[1])
    walk(root, 0, 0)
    # sparkles
    star, sx0, sy0 = nodes['背景_星']
    for step in child(child(child(star, '種類別情報'), '通常状態'), '手順リスト').children:
        if scalar(val(step, 'コマンド')) == 19:
            r = [scalar(i.value.payload) for i in val(step, '先矩形').items]
            im.alpha_composite(cg['icon'], (round(sx0 + r[0]), round(sy0 + r[1])))
    # gauges (dim track full, fill to the sample rate of the slider they belong to)
    sliders = {p['name']: p for p in parts if p.get('kind') == 'slider'}
    for n, (t, ax, ay) in nodes.items():
        if not (n.startswith('KR_MD_Track') or n.startswith('KR_MD_Fill')):
            continue
        scale = [scalar(i.value.payload) for i in val(t, '拡大縮小').items]
        mul = [scalar(i.value.payload) for i in val(t, '乗算色').items]
        w = round(300 * scale[0]); bar = cg['bar'].resize((w, 12), Image.Resampling.LANCZOS)
        if n.startswith('KR_MD_Track'):
            px = bar.load()
            for yy in range(bar.size[1]):
                for xx in range(bar.size[0]):
                    r, g, b, a = px[xx, yy]; px[xx, yy] = (r * mul[0] // 255, g * mul[1] // 255, b * mul[2] // 255, a)
            im.alpha_composite(bar, (round(ax), round(ay)))
        else:
            key = n[len('KR_MD_Fill'):]
            sl = 'KR_CheatSpeed' if key == 'Speed' else f'KR_Multiplier_{key}'
            fw = round(w * SAMPLE_RATE.get(sl, 1.0))
            if fw > 0:
                im.alpha_composite(bar.crop((0, 0, fw, 12)), (round(ax), round(ay)))
    draw = ImageDraw.Draw(im)
    for p in parts:
        if p['name'] == 'デバッグボタン' or not p['shown']:
            continue
        k = p.get('kind')
        if k == 'button':
            key = p['name'] if p['name'] in cg else ('tab' if p['enabled'] else 'tab_off')
            plate = cg[key]; w, h = p['size']; w, h = round(w), round(h)
            if plate.size != (w, h): plate = plate.resize((w, h), Image.Resampling.LANCZOS)
            im.alpha_composite(plate, (round(p['x']), round(p['y'])))
        elif k == 'slider':
            w, h = p['size']; rate = SAMPLE_RATE.get(p['name'], 0.0)
            im.alpha_composite(cg['cursor'], (round(p['x'] + rate * (w - 25)), round(p['y'])))
        elif k == 'checkbox':
            im.alpha_composite(cg['check_on'] if p['name'] in SAMPLE_CHECKED else cg['check'], (round(p['x']), round(p['y'])))
            st = p['style']; bw, bh = p['box']; ty = p['y'] + (bh - fnl.line_height(st['size'])) / 2
            fnl.draw(im, p['x'] + bw, ty, p['text'], st['size'], st['spacing'], st['edge'], st['bold'], st['color'], st['edge_color'])
        elif k == 'text':
            st = p['style']; x0 = p['x']; text = SAMPLE_VALUE.get(p['name'], p['text'])
            if p['origin_mode'] == 2: x0 -= fnl.width(text, st['size'], st['spacing'], st['edge'], st['bold']) / 2
            fnl.draw(im, x0, p['y'], text, st['size'], st['spacing'], st['edge'], st['bold'], st['color'], st['edge_color'], st['line_gap'])
    im.convert('RGB').save(out_png)


if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2])
    print('ok')
