"""Print FUNC..(next header) blocks (with their ; header) from the base code.jam by exact name or regex.
usage: python funcs.py NAME [NAME ...]   (prefix re: for a regex)"""
import re, sys
from pathlib import Path
CODE = Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\mods_tab_20261015\work\base\code.jam')
_blocks = None


def blocks():
    global _blocks
    if _blocks is None:
        txt = CODE.read_text('utf8', errors='replace')
        lines = txt.split('\n')
        starts = []
        for i, l in enumerate(lines):
            if l.startswith('FUNC ') and l[5:].strip().isdigit():
                j = i
                while j > 0 and lines[j - 1].startswith('; '):
                    j -= 1
                starts.append((j, i))
        out = {}
        for k, (j, i) in enumerate(starts):
            end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
            name = lines[j][2:] if j < i else '?'
            out.setdefault(name, []).append('\n'.join(lines[j:end]) + '\n')
        _blocks = out
    return _blocks


if __name__ == '__main__':
    b = blocks()
    for a in sys.argv[1:]:
        if a.startswith('re:'):
            r = re.compile(a[3:])
            for n in b:
                if r.search(n):
                    for x in b[n]:
                        print(x)
        else:
            for x in b.get(a, ['?? ' + a + '\n']):
                print(x)
