"""r20 reading aid: the LIVE body of functions in the base AIN (alice ain dump --function; cached). Read only.
  python live.py NAME [NAME...]
"""
import sys, subprocess, os, json
from pathlib import Path
R20 = Path(__file__).resolve().parent.parent.parent
BASE = R20.parent / 'r19_calendar' / 'candidate' / 'NightRemaster.ain'
META = R20.parent / 'r19_calendar' / 'work' / 'build' / 'candidate_meta.json'
ALICE = r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe'
C = R20 / 'work' / 'base_dump' / 'fn'
C.mkdir(parents=True, exist_ok=True)
_m = None


def meta():
    global _m
    if _m is None:
        _m = json.loads(META.read_text(encoding='utf-8', errors='surrogateescape'), strict=False)
    return _m


def name_of(i):
    n = meta()['functions'][i]['name']
    return n.encode('utf8', 'surrogateescape').decode('cp932') if any(0xdc80 <= ord(c) <= 0xdcff for c in n) else n


def body(name):
    m = meta()
    if name.startswith('#'):
        ids = [int(name[1:])]
        name = name_of(ids[0])
    else:
        ids = [f['index'] for f in m['functions'] if name_of(f['index']) == name]
    out = []
    for i in ids:
        p = C / f'{i}.jam'
        if not p.exists():
            prior = sum(1 for f in m['functions'][:i] if f['name'] == m['functions'][i]['name'])
            sym = name + (f'#{prior}' if prior else '')
            env = dict(os.environ, TEMP=str(R20 / 'tmp'), TMP=str(R20 / 'tmp'))
            q = subprocess.run([ALICE, 'ain', 'dump', '--function', sym, '-o', str(p), str(BASE)], capture_output=True, env=env)
            if q.returncode != 0:
                raise SystemExit(q.stderr.decode('utf8', 'replace'))
        out.append((i, m['functions'][i]['address'], p.read_text('utf8', errors='replace')))
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for n in sys.argv[1:]:
        for i, a, t in body(n):
            print(f'##### {n} index {i} address {a}')
            print(t)
