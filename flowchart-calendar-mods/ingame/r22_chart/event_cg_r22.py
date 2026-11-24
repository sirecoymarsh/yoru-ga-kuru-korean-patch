"""Claude Opus 5.5 (2026-09-28) r22: graph/event_cg.json - which CGs every event shows (the chart's thumbnails).

  python event_cg_r22.py            extract, run the gates, write graph/event_cg.json + 증거/event_cg_gate.json
  python event_cg_r22.py --check    extract again and compare with the published graph/event_cg.json (exit 1 if it moved)

Sources (read only):
  * the base AIN's event functions (ＥＶ／元／E#####, 1,164 events; named dump work/base_dump/code.jam of the r21 candidate =
    the runtime AIN): every CG call an event makes, in order -
      ■準備壁紙#1(n) / ■準備背景#1(n)   ("CG%04d", n a constant PUSH right before the call; 3,112 sites)
      ■準備壁紙(s) / ■準備背景(s) / ■準備イベント(s)   (a constant S_PUSH; 10 sites)
    and the chain jumps (.GLOBALASSIGN g_EvResult n) and the message count.
  * the runtime EX (alice ex dump of NightRemasterEX.ex): 「CG閲覧」 (the CG gallery: 60 entries, thumbnail CG + cg1..cg7 = 90
    CGs) and 「回想」 (the recollection mode: 7 pages, 76 cells: needEvNo, playEvNo).
Kinds: 「gallery」 = a CG of the CG gallery (the game's event CGs; each has the gallery thumbnail 「シス／ＣＧモード／サムネイル／<first
CG of its entry>」, 120 x 90), 「wallpaper」 = any other ■準備壁紙 CG, 「background」 = ■準備背景 (places).
A message-less event whose body is only 「g_EvResult = n」 (the recollection wrappers E5xxxx and a few others) shows what n
shows: `shown` follows such jumps (a replay of the wrapper plays n).
Thumbnail of an event = the gallery thumbnail of the first gallery CG it shows (`shown`), else none (a small cell).

The recollection mode has NO per-cell thumbnails in this game (each page is one picture of scene titles, CG5411-CG5417, with a
lid part per locked cell), so the gate on 「the 76 recollection cells' thumbnail CGs」 is taken as: the thumbnail the chart shows
for each cell's replay event (playEvNo) must be one of the CGs its source event (needEvNo) shows (and every cell is listed with
both lists), plus: every gallery CG is shown by at least one event; every gallery entry's thumbnail CG exists in the CG archive
listing.
"""
import sys, io, json, re, collections, datetime, hashlib
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r22lib as L

OUT = L.FLOW / 'graph' / 'event_cg.json'
GATE = L.EVID / 'event_cg_gate.json'
CODE = L.WORK / 'base_dump' / 'code.jam'
EXDUMP = L.WORK / 'ex_runtime.x'
CGLIST = L.WORK / 'cg' / 'cg_list.txt'
THUMB = 'シス／ＣＧモード／サムネイル／'


# ---------------------------------------------------------------- EX (a copy of scratch/exparse.py, trimmed)
TOKEN = re.compile(r'''
      (?P<str>"(?:[^"\\]|\\.)*")
    | (?P<num>-?\d+(?:\.\d+)?)
    | (?P<punc>[{}(),;=])
    | (?P<word>[^\s{}(),;="]+)
''', re.X)


def tokenize(text):
    pos, n = 0, len(text)
    while pos < n:
        if text[pos] in ' \t\r\n':
            pos += 1
            continue
        m = TOKEN.match(text, pos)
        assert m, ('EX token', pos, text[pos:pos + 40])
        pos = m.end()
        kind, val = m.lastgroup, m.group()
        if kind == 'str':
            val = val[1:-1].replace('\\\\', '\\').replace('\\"', '"').replace('\\n', '\n')
        elif kind == 'num':
            val = float(val) if '.' in val else int(val)
        yield kind, val


class P:
    def __init__(self, toks):
        self.t, self.i = list(toks), 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def next(self):
        v = self.t[self.i]
        self.i += 1
        return v

    def expect(self, val):
        k, v = self.next()
        assert v == val, (val, v, self.i)


def braced(p):
    p.expect('{')
    out = []
    while True:
        k, v = p.peek()
        if v == '}':
            p.next()
            return out
        if v == ',':
            p.next()
            continue
        if v == '{':
            out.append(braced(p))
            continue
        if v == '(':
            p.next()
            _, tag = p.next()
            p.expect(')')
            out.append(('@cast', tag, braced(p)))
            continue
        k, v = p.next()
        if p.peek()[1] == '=':
            p.next()
            kk, vv = p.peek()
            if vv == '{':
                out.append((v, braced(p)))
            elif vv == '(':
                p.next()
                _, tag = p.next()
                p.expect(')')
                out.append((v, ('@cast', tag, braced(p))))
            else:
                out.append((v, p.next()[1]))
            continue
        out.append(v)


def ex_blocks(path):
    p = P(tokenize(Path(path).read_text('utf8', errors='replace')))
    blocks = {}
    while p.i < len(p.t):
        k, kind = p.next()
        if kind == ';':
            continue
        k, name = p.next()
        p.expect('=')
        val = braced(p) if p.peek()[1] == '{' else p.next()[1]
        if p.peek()[1] == ';':
            p.next()
        blocks[name] = (kind, val)
    return blocks


def table(val):
    if isinstance(val, tuple) and val[0] == '@cast':
        val = val[2]
    hdr, fields, i = val[0], [], 0
    while i < len(hdr):
        if hdr[i] in ('int', 'string', 'float', 'bool'):
            nxt = hdr[i + 1]
            fields.append(nxt[0] if isinstance(nxt, tuple) else nxt)
            i += 2
            continue
        i += 1
    return [{f: (r[j] if j < len(r) else None) for j, f in enumerate(fields)} for r in val[1:]]


def gallery_and_memory():
    b = ex_blocks(EXDUMP)
    kind, val = b['CG閲覧']
    rows = table(dict(val)['データ'])
    gallery = []
    for r in rows:
        cgs = ['CG%04d' % r[f] for f in ('cg1', 'cg2', 'cg3', 'cg4', 'cg5', 'cg6', 'cg7') if r.get(f)]
        assert r['thumb'].startswith(THUMB), r
        gallery.append(dict(thumb=r['thumb'], cgs=cgs))
    kind, val = b['回想']
    memory = []
    for pi, (pname, tb) in enumerate(val, start=1):
        for r in table(tb):
            memory.append(dict(page=pi, slot=r['id'], need=r['needEvNo'], play=r['playEvNo']))
    return gallery, memory


# ---------------------------------------------------------------- event functions
def label_name(no):
    return ('E%04d' % no) if no == 1706 else ('E%05d' % no)


def fn_of(no):
    s = label_name(no)
    return 'ＥＶ／元／' + {'E01707': '01707', 'E02132': '02132'}.get(s, s)


def event_functions():
    """{function name: [instruction, ...]} for every ＥＶ／元／ function in the named dump."""
    lines = CODE.read_text('utf8', errors='replace').splitlines()
    out = {}
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith('; ＥＶ／元／'):
            name = l[2:]
            j = i + 1
            while not lines[j].startswith('FUNC '):
                j += 1
            body = []
            j += 1
            while not lines[j].startswith('ENDFUNC'):
                s = lines[j].strip()
                if s and not s.startswith(';') and not s.endswith(':'):
                    body.append(s)
                j += 1
            assert name not in out, name
            out[name] = body
            i = j
        i += 1
    return out


CALL_INT = {'CALLFUNC ■準備壁紙#1': 'wallpaper', 'CALLFUNC ■準備背景#1': 'background'}
CALL_STR = {'CALLFUNC ■準備壁紙': 'wallpaper', 'CALLFUNC ■準備背景': 'background', 'CALLFUNC ■準備イベント': 'event'}


def scan(body):
    cgs, jumps, msgs, sites = [], [], 0, 0
    prev = ''
    for s in body:
        if s in CALL_INT:
            z = re.fullmatch(r'PUSH (-?\d+)', prev)
            assert z, ('non-constant CG number', prev, s)
            n = int(z.group(1))
            sites += 1
            if n > 0:                          # 0 / negative = the 「…消し」 branch (clear), no CG
                cgs.append(('CG%04d' % n, CALL_INT[s]))
        elif s in CALL_STR:
            z = re.fullmatch(r'S_PUSH "(CG\d{4})"', prev)
            assert z, ('non-constant CG name', prev, s)
            sites += 1
            cgs.append((z.group(1), CALL_STR[s]))
        elif s.startswith('.GLOBALASSIGN g_EvResult '):
            jumps.append(int(s.split()[-1]))
        elif s.startswith('MSG '):
            msgs += 1
        prev = s
    return cgs, jumps, msgs, sites


def extract():
    gallery, memory = gallery_and_memory()
    gal = {}
    for e in gallery:
        for c in e['cgs']:
            assert c not in gal, ('a CG in two gallery entries', c)
            gal[c] = e['thumb']
    funcs = event_functions()
    sched = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    ids = sorted(e['id'] for e in sched['events'])
    assert len(ids) == 1164, len(ids)
    events, sites = {}, 0
    for no in ids:
        body = funcs[fn_of(no)]
        cgs, jumps, msgs, n = scan(body)
        sites += n
        own, seen = [], set()
        for c, k in cgs:
            if c in seen:
                continue
            seen.add(c)
            own.append(dict(cg=c, kind='gallery' if c in gal else k if k != 'event' else 'wallpaper'))
        pure_jump = msgs == 0 and not cgs and len(jumps) == 1 and jumps[0] > 0 and all(s.startswith('.GLOBALASSIGN g_EvResult ') for s in body if s != 'RETURN')
        events[no] = dict(fn=fn_of(no), messages=msgs, own=own, jumps=sorted(set(jumps)), jump_to=jumps[0] if pure_jump else None)
    extra = sorted(set(funcs) - {fn_of(no) for no in ids})
    # shown = own CGs, or (pure jump) what the target shows
    for no, e in events.items():
        cur, hops = no, 0
        while events[cur]['jump_to'] is not None:
            cur = events[cur]['jump_to']
            hops += 1
            assert cur in events and hops < 8, (no, cur)
        e['shown_from'] = cur
        e['shown'] = [x['cg'] for x in events[cur]['own']]
        e['gallery'] = [c for c in e['shown'] if c in gal]
        e['thumb'] = gal[e['gallery'][0]] if e['gallery'] else None
        e['thumb_cg'] = e['gallery'][0] if e['gallery'] else None
    return gallery, gal, memory, events, dict(cg_call_sites=sites, other_ev_functions=extra)


SUMMER = {'CG1013': 'CG1011', 'CG1014': 'CG1012'}     # ■準備壁紙#1: L_Calendar::IsSummer() and cgNo 1013 / 1014 -> cgNo - 2


NAME_OPEN, NAME_CLOSE = '【'.encode('cp932'), '】'.encode('cp932')     # a speaker name box line 「【name】」


def replay_sources(memory, events):
    """The original events a recollection replay reproduces. A message-less pure jump (the wrappers E501xx...) plays its target
    itself; a copy (E502xx..., E60xxx) combines several originals: its sources are the cell's needEvNo (the game's own
    「original」 of the cell) and every original event (category != memory_replay in graph/schedule.json) that shares >= 3
    distinctive lines with it - 12+ bytes after trimming, not a speaker name box (【…】), found in at most 3 original events. The
    texts are compared as raw MSG1 bytes of the base AIN (never written anywhere)."""
    _, _, _, raw = L.raw_messages(L.base_paths()['ain'].read_bytes())
    sched = json.loads((L.FLOW / 'graph' / 'schedule.json').read_text('utf8'))
    cat = {e['id']: e['category'] for e in sched['events']}
    msgs = collections.defaultdict(list)
    for line in (L.FLOW / 'graph' / 'lines.jsonl').read_text('utf8').splitlines():
        d = json.loads(line)
        msgs[d['event']].append(d['m'])

    def key(m):
        t = raw[m].strip()
        if len(t) < 12 or (t.startswith(NAME_OPEN) and t.endswith(NAME_CLOSE)):
            return None
        return t
    index = collections.defaultdict(set)
    for no in events:
        if cat[no] == 'memory_replay':
            continue
        for m in msgs[no]:
            t = key(m)
            if t is not None:
                index[t].add(no)
    index = {t: v for t, v in index.items() if len(v) <= 3}
    own = collections.Counter()
    for t, v in index.items():
        for no in v:
            own[no] += 1
    out = {}
    for m in memory:
        n = m['play']
        if events[n]['jump_to'] is not None:
            out[n] = ('jump', [events[n]['shown_from']], {})
            continue
        cnt = collections.Counter()
        for t in {key(k) for k in msgs[n]} - {None}:
            for o in index.get(t, ()):
                cnt[o] += 1
        src = sorted(set(o for o, k in cnt.items() if k >= 3) | {m['need']})
        out[n] = ('text', src, {o: cnt.get(o, 0) for o in src})
    return out


def gates(gallery, gal, memory, events):
    out = {}
    # G1 every gallery CG is shown by an event (the two summer variants through ■準備壁紙#1's summer rule)
    shown_by = collections.defaultdict(list)
    for no, e in events.items():
        for x in e['own']:
            shown_by[x['cg']].append(no)
            if x['cg'] in SUMMER:
                shown_by[SUMMER[x['cg']]].append(no)
    miss = sorted(c for c in gal if not shown_by.get(c))
    out['G1_gallery_cgs_shown'] = dict(gallery_cgs=len(gal), shown_by_some_event=len(gal) - len(miss), not_shown=miss,
                                       via_summer_rule=sorted(SUMMER.values()), ok=not miss)
    # G2 each gallery thumbnail CG exists in the CG archive listing
    listing = CGLIST.read_text('utf8', errors='replace')
    names = set(re.findall(r'^\d+: (.+?)\.\w+$', listing, re.M))
    lacking = sorted(e['thumb'] for e in gallery if e['thumb'] not in names)
    out['G2_thumbnails_in_archive'] = dict(entries=len(gallery), missing=lacking, ok=not lacking)
    # G3 the 76 recollection cells: the thumbnail the chart shows for the cell's replay event is a CG that the original
    #    scene(s) it reproduces show (sources: the jump target, else the originals found by text)
    srcs = replay_sources(memory, events)
    cells = []
    for m in memory:
        play, need = events[m['play']], events[m['need']]
        how, src, shared = srcs[m['play']]
        src_cgs = sorted({c for o in src for c in events[o]['shown']} | {SUMMER[c] for o in src for c in events[o]['shown'] if c in SUMMER})
        cells.append(dict(page=m['page'], slot=m['slot'], need=m['need'], play=m['play'], play_shown_from=play['shown_from'],
                          thumb_cg=play['thumb_cg'], source_method=how, sources=src, shared_lines=shared,
                          thumb_in_sources=(play['thumb_cg'] in src_cgs) if play['thumb_cg'] else None,
                          need_gallery=need['gallery'], play_gallery=play['gallery']))
    bad = [c for c in cells if c['thumb_in_sources'] is False or not c['sources']]
    out['G3_memory_cells'] = dict(cells=len(cells), with_thumbnail=sum(1 for c in cells if c['thumb_cg']),
                                  without_thumbnail=sum(1 for c in cells if not c['thumb_cg']),
                                  by_jump=sum(1 for c in cells if c['source_method'] == 'jump'),
                                  by_text=sum(1 for c in cells if c['source_method'] == 'text'),
                                  failing=[(c['page'], c['slot'], c['play'], c['thumb_cg'], c['sources'][:6]) for c in bad],
                                  ok=len(cells) == 76 and not bad)
    # G4 every event is present exactly once, every jump target exists
    out['G4_events'] = dict(events=len(events), pure_jumps=sum(1 for e in events.values() if e['jump_to'] is not None),
                            with_thumbnail=sum(1 for e in events.values() if e['thumb']),
                            ok=len(events) == 1164 and all(e['shown_from'] in events for e in events.values()))
    return out, cells


def build():
    gallery, gal, memory, events, info = extract()
    g, cells = gates(gallery, gal, memory, events)
    data = dict(schema='yoru-event-cg.v1', author=L.AUTHOR, generated=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                source=dict(ain_sha256=L.BASE_AIN_SHA, named_dump=str(CODE), ex_sha256=L.BASE_EX_SHA, ex_dump=str(EXDUMP),
                            extractor_sha256=L.sha(Path(__file__)), cg_call_sites=info['cg_call_sites'],
                            other_ev_functions=info['other_ev_functions']),
                note=('kinds: gallery = CG閲覧 (the game\'s event CGs, thumbnail = 「シス／ＣＧモード／サムネイル／<entry>」 120x90); '
                      'wallpaper = other ■準備壁紙; background = ■準備背景 (places). shown follows a message-less pure jump '
                      '(g_EvResult = n only). thumb = the gallery thumbnail of the first gallery CG shown, null = small cell.'),
                gallery=gallery,
                events={str(no): dict(fn=e['fn'], messages=e['messages'], own=e['own'], jump_to=e['jump_to'], shown_from=e['shown_from'],
                                      shown=e['shown'], gallery=e['gallery'], thumb=e['thumb']) for no, e in sorted(events.items())},
                memory_cells=cells, gates=g)
    return data


def comparable(d):
    return json.loads(json.dumps({k: v for k, v in d.items() if k not in ('generated',)}, ensure_ascii=False))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    data = build()
    if '--check' in sys.argv:
        pub = json.loads(OUT.read_text('utf8'))
        same = comparable(pub) == comparable(data)
        print('graph/event_cg.json', 'UP TO DATE' if same else 'MOVED')
        raise SystemExit(0 if same else 1)
    ok = all(v['ok'] for v in data['gates'].values())
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', 'utf8')
    L.writej(GATE, dict(time=data['generated'], gates=data['gates'], sha256=L.sha(OUT)))
    for k, v in data['gates'].items():
        print(k, {kk: vv for kk, vv in v.items() if not isinstance(vv, list) or len(vv) < 12})
    print('wrote', OUT, L.sha(OUT))
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
