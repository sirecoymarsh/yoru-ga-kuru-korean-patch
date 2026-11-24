"""r20 reading aid: print a function body from work/base_dump/code.jam (the base AIN, named dump). Read only.
  python show.py NAME [NAME...]        exact function names (as in the '; NAME' header)
  python show.py --grep REGEX          function names matching
  python show.py --callers NAME        functions whose body mentions NAME as a CALLFUNC/CALLMETHOD target
"""
import sys, re, pickle
from pathlib import Path
D = Path(__file__).resolve().parent.parent / 'base_dump'
CODE = D / 'code.jam'
IDX = D / 'code_index.pkl'


def index():
    if IDX.exists() and IDX.stat().st_mtime > CODE.stat().st_mtime:
        return pickle.loads(IDX.read_bytes())
    lines = CODE.read_text('utf8', errors='replace').splitlines()
    heads = []
    for i, l in enumerate(lines):
        if l.startswith('FUNC '):
            j = i - 1
            while j >= 0 and lines[j].startswith(';'):
                j -= 1
            name = lines[j + 1][2:] if j + 1 < i else '?'
            heads.append((j + 1, i, name))
    funcs = {}
    for k, (h, f, name) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        funcs.setdefault(name, []).append((h, end))
    IDX.write_bytes(pickle.dumps((lines, funcs)))
    return lines, funcs


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    lines, funcs = index()
    a = sys.argv[1:]
    if a[0] == '--grep':
        rx = re.compile(a[1])
        for n in sorted(funcs):
            if rx.search(n):
                print(n, [e - s for s, e in funcs[n]])
        return
    if a[0] == '--callers':
        t = a[1]
        for n, rs in funcs.items():
            for s, e in rs:
                for l in lines[s:e]:
                    st = l.strip()
                    if st.startswith(('CALLFUNC', 'CALLMETHOD', 'DG_', 'PUSH', 'CALLSYS', 'S_PUSH')) and (st.endswith(' ' + t) or (' ' + t + ' ') in st):
                        print(n)
                        break
        return
    for n in a:
        for s, e in funcs.get(n, []):
            print('\n'.join(lines[s:e]))
            print('=' * 40)


if __name__ == '__main__':
    main()


def refs(num):
    """functions that PUSH `num` (a method index) or CALLFUNC it, with the line inside the function"""
    lines, funcs = index()
    spans = sorted((s, e, n) for n, rs in funcs.items() for s, e in rs)
    import bisect
    starts = [s for s, _, _ in spans]
    out = []
    pats = ('PUSH %s' % num, 'CALLFUNC %s' % num)
    for i, l in enumerate(lines):
        st = l.strip()
        if st in pats:
            k = bisect.bisect_right(starts, i) - 1
            s, e, n = spans[k]
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ''
            out.append((n, i - s, st, nxt))
    return out


if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[1] == '--refs':
    for r in refs(sys.argv[2]):
        print(r)
