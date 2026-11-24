"""r16: per-page maxima (title lines, raw title characters incl. colour marks, items, rows, height px, item width units,
dialog width px) over the none / partial / all-seen / mid-August states, using the verifier's VM on the candidate.
Writes 증거/page_stats.json (copy of r15 work/page_stats.py with the r16 pages: 달 쪽 2열·3열, 달성도 요약 쪽)."""
import sys, json, math, random, collections
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r16lib as L
import verify_calendar_r16 as V

man = L.readj(V.O / 'manifest.json')
nm = L.read_meta(V.W / 'candidate_meta.json')
X = V.expectations()
vm = V.VM(V.O / 'NightRemaster.ain', nm)
stats = collections.defaultdict(lambda: dict(dialogs=0, title_lines=0, title_chars=0, items=0, rows=0, height=0, item_units=0.0, width_px=0, cols=set()))


def rec(page, d):
    lines, rows, h = V.geometry(d)
    s = stats[page]
    s['dialogs'] += 1
    s['title_lines'] = max(s['title_lines'], len(lines))
    s['title_chars'] = max(s['title_chars'], max(len(x) for x in lines))
    s['items'] = max(s['items'], len(d['items']))
    s['rows'] = max(s['rows'], rows)
    s['height'] = max(s['height'], h)
    widest = max([V.units_w(V.ko(t)) for _, t, _, _ in d['items']] or [0])
    s['item_units'] = max(s['item_units'], widest)
    s['width_px'] = max(s['width_px'], int(max(d['cols'] * (widest * 28 + 52), max(len(x) for x in lines) * 28.5 + 48) + 4))
    s['cols'].add(d['cols'])


def walk(page, fn, args, script, ctx='P'):
    vm.reset()
    vm.vars['YoruKR.T9.Ctx'] = ctx
    vm.script = list(script)
    vm.run(fn, args)
    for d in vm.dialogs:
        rec(page, d)


rnd = random.Random(20260927)
evs = X['ev']
mid, mid_today = V.synthetic_mid_month(X)
states = [set(), {e['fn'] for e in evs.values() if rnd.random() < 0.5}, {e['fn'] for e in evs.values()}, mid]
for regs in states:
    vm.registered = regs
    for today in [(4, 9), mid_today, (9, 30), (11, 17)]:
        vm.today = today
        for mo in range(4, 12):
            walk('달 쪽 (%d열)' % V.month_cols(X, mo), 'KR_T9MonthPage', [mo], [0])
    walk('달성도 요약 쪽', 'KR_T16SummaryPage', [], [0])
    walk('회상 · 그 밖', 'KR_T9MemPage', [], [0])
    for mo in range(4, 12):
        for lane in range(9):
            nc = sum(1 for c in X['cards'] if c['month'] == mo and c['lane'] == lane)
            nd = sum(1 for ch in X['chips'] if ch['month'] == mo and ch['lane'] == lane)
            if nc + nd:
                n = nc + nd
                walk('레인 쪽', 'KR_T9LanePage', [mo, lane], [12] * (math.ceil(n / (10 if n <= 10 else 8)) - 1) + [0])
        n = sum(1 for ch in X['chips'] if ch['month'] == mo)
        walk('이달의 서랍', 'KR_T9MonthChips', [mo], [12] * (math.ceil(n / (10 if n <= 10 else 8)) - 1) + [0])
    for k, c in enumerate(X['cards']):
        for ctx in ('P', 'C', ''):
            walk('카드 쪽', 'KR_T9CardPage', [k, c['month']], [0], ctx)
        if c['size'] > 1:
            walk('단계 목록', 'KR_T9StagePage', [k, c['month']], [12] * (math.ceil(c['size'] / 30) - 1) + [0])
    for i, ch in enumerate(X['chips']):
        walk('서랍 장면 목록', 'KR_T9ChipPage', [i], [12] * (math.ceil(len(ch['scenes']) / 30) - 1) + [0])
vm.registered = states[1]
for no in sorted(evs):
    for ctx in ('P', 'C', ''):
        walk('장면 쪽', 'KR_T9EventPage', [no, V.proxy('6월 · 호시카와 · 특훈 뒤 대화')], [0], ctx)
out = {k: dict(v, cols=sorted(v['cols'])) for k, v in stats.items()}
out['_limits'] = dict(title_chars=38, height=704, width_px=1280, item_units={'1': 38, '2': 20, '3': 13})
L.writej(L.EVID / 'page_stats.json', out)
print(json.dumps(out, ensure_ascii=False, indent=1))
