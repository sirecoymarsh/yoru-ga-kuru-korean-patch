"""r16 study: chart v2 data questions before designing (read only; writes work/study_data.json).

  - month-12 (회상 · 그 밖) drawers: which lanes; per lane / per month scene units (card stages + drawer scenes)
  - month-page menu size per month (lanes with scenes), weeks per month (title height)
  - r15 lane-row collisions (when + cond + suffix equal inside (month, lane))
  - the 1,164 calendar events against the 1,043 of the home achievement panel (KR_PlayerEventCount groups 0-3)
"""
import sys, json, collections, math
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import r16lib as L
import build_calendar_r16 as B

m = L.read_meta(L.WORK / 'base' / 'meta.json')
vers = L.versions(L.WORK / 'base' / 'raw_code.jam')
data, V2, chart = B.chart_data()
T = B.tables(data, V2, m, vers)
cards, chips = T['cards'], T['chips']
ev = {int(k): v for k, v in data['ev'].items()}
out = {}
# units per (month, lane)
units = collections.Counter()
for c in cards:
    units[(c['month'], c['lane'])] += c['size']
for ch in chips:
    units[(ch['month'], ch['lane'])] += ch['size']
out['units_total'] = sum(units.values())
out['units_by_month'] = {mo: sum(v for (a, _), v in units.items() if a == mo) for mo in range(4, 13)}
out['units_by_lane'] = {l: sum(v for (_, b), v in units.items() if b == l) for l in range(17)}
out['month12_lanes'] = sorted({ch['lane'] for ch in chips if ch['month'] == 12})
out['month12_chips'] = [(ch['id'], ch['lane'], ch['kind'], ch['size']) for ch in chips if ch['month'] == 12]
out['max_units_month_lane'] = max(v for (a, b), v in units.items() if a <= 11)
out['max_units_month_lane_at'] = [k for k, v in units.items() if v == out['max_units_month_lane']]
out['max_scenes_month'] = max(sum(ch['size'] for ch in chips if ch['month'] == mo) for mo in range(4, 13))
# menu sizes and weeks
menu = {}
for mo in range(4, 12):
    lanes = [l for l in range(9) if units[(mo, l)] > 0]
    weeks = math.ceil((T['w1'][mo] + T['mlen'][mo]) / 7)
    items = len(lanes) + 1 + (1 if mo > 4 else 0) + 1 + 1 + 1        # lanes, 서랍, ←, →, 달성도 보기, 돌아가기
    rows = math.ceil(items / 2)
    lines = 3 + weeks
    menu[mo] = dict(lanes=len(lanes), items=items, weeks=weeks, title_lines=lines, rows=rows, height=64 + 34 * lines + 48 * rows)
out['month_pages'] = menu
# collisions (r15 row text without the mark)
rows = collections.defaultdict(list)
for c in cards:
    when = ('%d/%d' % (c['month'], c['day'])) if c['day'] else ('%d월 중' % c['month'])
    if c['slot']:
        when += ' ' + B.SLOT_KR[c['slot']]
    suffix = (' (%d단계)' % c['size']) if c['size'] > 1 else ''
    rows[(c['month'], c['lane'], when + '|' + c['cond'] + '|' + suffix)].append(c['entry'])
groups = {k: v for k, v in rows.items() if len(v) > 1}
out['collision_groups'] = len(groups)
out['collision_cards'] = sum(len(v) for v in groups.values())
out['collisions'] = [dict(month=k[0], lane=k[1], row=k[2], entries=v) for k, v in sorted(groups.items())]
# panel comparison
panel = json.loads((HERE / 'panel_event_groups.json').read_text('utf8'))
pset = {n for v in panel.values() for n in v}
cal = {e['fn']: no for no, e in ev.items()}
where = {}
for c in cards:
    for s in c['stages']:
        where[s] = ('card', c['month'], c['lane'])
for ch in chips:
    for s in ch['scenes']:
        where[s] = ('drawer', ch['month'], ch['lane'], B.KINDS[ch['kind']])
only_cal = sorted(no for fn, no in cal.items() if fn not in pset)
only_panel = sorted(fn for fn in pset if fn not in cal)
out['calendar_events'] = len(cal)
out['panel_events'] = len(pset)
out['in_both'] = len(pset & set(cal))
out['only_calendar'] = len(only_cal)
out['only_panel'] = only_panel
cnt = collections.Counter()
for no in only_cal:
    w = where[no]
    key = (w[0], 'month12' if w[1] == 12 else 'month', w[3] if w[0] == 'drawer' else 'lane%d' % w[2], ev[no].get('cat'))
    cnt[key] += 1
out['only_calendar_by_place'] = sorted([list(k) + [v] for k, v in cnt.items()], key=lambda x: -x[-1])
out['only_calendar_numbers'] = only_cal
catc = collections.Counter(ev[no].get('cat') for no in ev)
out['calendar_by_cat'] = dict(catc)
out['panel_groups'] = {g: len(v) for g, v in panel.items()}
L.writej(HERE / 'study_data.json', out)
print(json.dumps({k: v for k, v in out.items() if k not in ('collisions', 'only_calendar_numbers', 'month12_chips')}, ensure_ascii=False, indent=1))
print(json.dumps(out['collisions'], ensure_ascii=False))
