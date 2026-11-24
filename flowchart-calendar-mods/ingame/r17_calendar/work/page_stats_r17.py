"""r17: per-page maxima (title lines, raw title characters incl. colour marks, items, rows, height px, item width units,
dialog width px) over the none / partial / all-seen / all-but-one / mid-August states, using the verifier's VM on the
candidate. Writes 증거/page_stats.json (copy of r16 work/page_stats_r16.py with the r17 pages: 달 쪽 2열·3열, 달성도 요약 쪽
(lowered below the panel: top + height), 회상 · 그 밖 (3 title lines), 이달의 서랍, drawer rows)."""
import sys, json, math, random, collections
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r17lib as L
import verify_calendar_r17 as V

man = L.readj(V.O / 'manifest.json')
nm = L.read_meta(V.W / 'candidate_meta.json')
X = V.expectations()
vm = V.VM(V.O / 'NightRemaster.ain', nm)
stats = collections.defaultdict(lambda: dict(dialogs=0, title_lines=0, title_chars=0, items=0, rows=0, height=0, bottom=0,
                                             item_units=0.0, item_chars=0, width_px=0, cols=set()))


def rec(page, d):
    lines, rows, h = V.geometry(d)
    s = stats[page]
    s['dialogs'] += 1
    s['title_lines'] = max(s['title_lines'], len(lines))
    s['title_chars'] = max(s['title_chars'], max(len(x) for x in lines))
    s['items'] = max(s['items'], len(d['items']))
    s['rows'] = max(s['rows'], rows)
    s['height'] = max(s['height'], h)
    s['bottom'] = max(s['bottom'], (d['top'] + h) if d.get('top') is not None else (720 + h) // 2)
    texts = [V.ko(t) for _, t, _, _ in d['items']]
    widest = max([V.units_w(t) for t in texts] or [0])
    s['item_units'] = max(s['item_units'], widest)
    s['item_chars'] = max(s['item_chars'], max([len(t) for t in texts] or [0]))
    s['width_px'] = max(s['width_px'], int(max(d['cols'] * (widest * 28 + 52), max(len(x) for x in lines) * 28.5 + 48) + 4))
    s['cols'].add(d['cols'])
    if d.get('top') is not None:
        s['top'] = d['top']


def walk(page, fn, args, script, ctx='P'):
    vm.reset()
    vm.vars['YoruKR.T9.Ctx'] = ctx
    vm.script = list(script)
    vm.run(fn, args)
    for d in vm.dialogs:
        rec(page, d)
    return vm.dialogs


rnd = random.Random(20260927)
evs = X['ev']
mid, mid_today = V.synthetic_mid_month(X)
states = [set(), {e['fn'] for e in evs.values() if rnd.random() < 0.5}, {e['fn'] for e in evs.values()}, V.all_but_one(X), mid]
drawer = dict(chars=0, units=0.0, text='')
for regs in states:
    vm.registered = regs
    for today in [(4, 9), mid_today, (9, 30), (11, 17)]:
        vm.today = today
        for mo in range(4, 12):
            walk('달 쪽 (%d열)' % V.month_cols(X, mo), 'KR_T9MonthPage', [mo], [0])
    walk('달성도 요약 쪽', 'KR_T17SummaryPage', [], [0])
    for d in walk('회상 · 그 밖 (패널 밖)', 'KR_T9MemPage', [], [0]):
        for iid, t, _, _ in d['items']:
            if iid >= 100 and len(V.ko(t)) > drawer['chars']:
                drawer.update(chars=len(V.ko(t)), units=V.units_w(V.ko(t)), text=V.ko(t), page='회상 · 그 밖')
    for mo in range(4, 12):
        for lane in range(9):
            nc = sum(1 for c in X['cards'] if c['month'] == mo and c['lane'] == lane)
            nd = sum(1 for ch in X['chips'] if ch['month'] == mo and ch['lane'] == lane)
            if nc + nd:
                n = nc + nd
                for d in walk('레인 쪽', 'KR_T9LanePage', [mo, lane], [12] * (math.ceil(n / (10 if n <= 10 else 8)) - 1) + [0]):
                    for iid, t, _, _ in d['items']:
                        if iid >= 100 + nc and len(V.ko(t)) > drawer['chars']:
                            drawer.update(chars=len(V.ko(t)), units=V.units_w(V.ko(t)), text=V.ko(t), page='레인 쪽')
        n = sum(1 for ch in X['chips'] if ch['month'] == mo)
        for d in walk('이달의 서랍', 'KR_T9MonthChips', [mo], [12] * (math.ceil(n / (10 if n <= 10 else 8)) - 1) + [0]):
            for iid, t, _, _ in d['items']:
                if iid >= 100 and len(V.ko(t)) > drawer['chars']:
                    drawer.update(chars=len(V.ko(t)), units=V.units_w(V.ko(t)), text=V.ko(t), page='이달의 서랍')
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
out['_widest_drawer_row'] = drawer
out['_limits'] = dict(title_chars=38, height=704, bottom=712, width_px=1280, item_units={'1': 38, '2': 20, '3': 13}, item_chars=38)
L.writej(L.EVID / 'page_stats.json', out)
print(json.dumps(out, ensure_ascii=False, indent=1))
