# -*- coding: utf-8 -*-
"""Read only (10-15): how the other config pages (Asra/*.pactex) draw their sliders and section art, and which
config CGs exist. Reads the installed runtime archives (NightRemasterPact.afa, NightRemasterCG.afa); writes only to tmp."""
import sys, json, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / 'pact' / 'lib'))
sys.path.insert(0, str(HERE / 'pact'))
sys.path.insert(0, str(HERE / 'work'))
from codex_pact_helpers import ex, read_afa3, maybe, name, coords  # noqa: E402
import render_layout_proof as proof  # noqa: E402
from mods_dump import kind_info, leaf, show  # noqa: E402

ptr = json.loads(Path('P:/AI/Codex/projects/YoruGaKuru_KR_asset_opening_20260908/ui_cumulative/current.json').read_text('utf-8-sig'))
rt = Path(ptr['runtime'])
arc = read_afa3(rt / 'NightRemasterPact.afa')
tmp = HERE / 'tmp' / 'asra'
tmp.mkdir(parents=True, exist_ok=True)
pages = [e for e in arc.entries if e.name.startswith('Asra/')]
print('Asra pages:', [(e.no, e.name) for e in pages])


def walk(t, depth=0):
    if maybe(t, '座標') is not None:
        yield t, depth
    kids = maybe(t, '子パーツ')
    if kids:
        for c in kids.children:
            yield from walk(c, depth + 1)


cmds = collections.Counter()
for e in pages:
    if e.name.endswith('Mods.pactex'):
        continue
    raw = (rt / 'NightRemasterPact.afa').open('rb')
    raw.seek(e.absolute_offset)
    p = tmp / (e.name.replace('/', '_'))
    p.write_bytes(raw.read(e.size))
    raw.close()
    d = ex.decode_ex(p)
    root = d.blocks[2].payload.children[0]
    print('====', e.no, e.name)
    for t, depth in walk(root):
        info = maybe(t, '種類別情報')
        ptype = None
        if info is not None:
            pt = maybe(info, 'パーツタイプ')
            ptype = show(leaf(pt)) if pt is not None else None
        ki = kind_info(t)
        cg = {k: v for k, v in ki.items() if 'ＣＧ名' in k and v}
        txt = {k: v for k, v in ki.items() if k.endswith('テキスト') and v}
        line = f"{'  ' * depth}{name(t)} [{ptype}] xyz={coords(t)}"
        if cg:
            line += ' cg=' + json.dumps(cg, ensure_ascii=False)
        if txt:
            line += ' txt=' + json.dumps(txt, ensure_ascii=False)[:120]
        if ptype == '横スクロールバー':
            sub = {c.name.value.decode('cp932'): show(leaf(c)) for c in info.children if leaf(c) is not None and not getattr(c, 'children', None)}
            line += ' bar=' + json.dumps({k: sub.get(k) for k in ('長さ', '幅', '全体スクロール量', 'ＣＧ名', '上書きバーＣＧ名', '上書き背景ＣＧ名')}, ensure_ascii=False)
        print(line[:400])
        # construction commands in use
        if info is not None:
            for st in ('通常状態',):
                s = maybe(info, st)
                if s is not None and maybe(s, '手順リスト') is not None:
                    for step in maybe(s, '手順リスト').children:
                        c = maybe(step, 'コマンド')
                        if c is not None:
                            cmds[show(leaf(c))] += 1
print('construction commands used on these pages:', dict(cmds))
idx = proof._cg_index(rt / 'NightRemasterCG.afa')
names = sorted(n for n in idx if 'コンフィグ' in n)
print(len(names), 'config CGs')
for n in names:
    print('  ', n, idx[n][1])
