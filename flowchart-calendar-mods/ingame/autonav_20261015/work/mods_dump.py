# -*- coding: utf-8 -*-
"""Read only (10-15): every part of the Mods page (PACT 185 Asra/Mods.pactex) with its parent, coordinates, kind and
texts, from the installed entry (pact/pact_185_autonav.pactex = installed runtime entry 185). --tree NAME prints one
part's whole node tree."""
import sys, json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / 'pact' / 'lib'))
sys.path.insert(0, str(HERE / 'pact'))
from codex_pact_helpers import ex, decode, child, maybe, val, name, scalar, coords  # noqa: E402


def leaf(n):
    p = n.leaf_value.payload if getattr(n, 'leaf_value', None) is not None else None
    return p


def show(p):
    if p is None:
        return None
    if isinstance(p, ex.ScalarNode):
        return scalar(p)
    if hasattr(p, 'items'):
        return [show(i.value.payload) for i in p.items]
    if hasattr(p, 'value') and isinstance(getattr(p, 'value'), (bytes, bytearray)):
        b = p.replacement if getattr(p, 'replacement', None) else p.value
        try:
            return decode(b)
        except Exception:
            return b.hex()
    return type(p).__name__


def tree(n, depth=0, out=None):
    out = [] if out is None else out
    nm = (n.name.replacement or n.name.value).decode('cp932') if getattr(n, 'name', None) is not None else '?'
    p = leaf(n)
    if p is not None and not getattr(n, 'children', None):
        out.append('  ' * depth + f'{nm} = {show(p)!r}')
    else:
        out.append('  ' * depth + nm)
        for c in getattr(n, 'children', []) or []:
            tree(c, depth + 1, out)
    return out


def parts_with_parent(t, parent=None, depth=0):
    if maybe(t, '座標') is not None:
        yield t, parent, depth
        parent_name = name(t)
    else:
        parent_name = parent
    kids = maybe(t, '子パーツ')
    if kids:
        for c in kids.children:
            yield from parts_with_parent(c, parent_name if maybe(t, '座標') is not None else parent, depth + 1)


def kind_info(t):
    info = maybe(t, '種類別情報')
    out = {}
    if info is None:
        return out
    def walk(n, prefix=''):
        for c in getattr(n, 'children', []) or []:
            k = (c.name.replacement or c.name.value).decode('cp932')
            p = leaf(c)
            if p is not None and not getattr(c, 'children', None):
                v = show(p)
                if k in ('テキスト', 'フォントサイズ', 'チェック状態', '有効状態', 'CG名', '幅', '高さ', 'サイズ', '矩形', '最小値', '最大値',
                         '値', '行間隔', '文字間隔', 'フォントの種類', '縁の太さ', '文字色', '縁の色', 'ボタンの種類') or k.endswith('CG名'):
                    out[prefix + k] = v
            else:
                walk(c, prefix + k + '/')
    walk(info)
    return out


def main():
    src = HERE / 'pact' / ('original_pact_185.pactex' if '--original' in sys.argv else 'pact_185_autonav.pactex')
    d = ex.decode_ex(src)
    root = d.blocks[2].payload.children[0]
    if '--tree' in sys.argv:
        want = sys.argv[sys.argv.index('--tree') + 1]
        for t, parent, depth in parts_with_parent(root):
            if name(t) == want:
                print('\n'.join(tree(t)))
        return
    rows = []
    for t, parent, depth in parts_with_parent(root):
        typ = show(leaf(child(t, '種類'))) if maybe(t, '種類') is not None else None
        rows.append(dict(name=name(t), parent=parent, depth=depth, kind=typ, xyz=coords(t), info=kind_info(t)))
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    print(len(rows), 'parts')


if __name__ == '__main__':
    main()
