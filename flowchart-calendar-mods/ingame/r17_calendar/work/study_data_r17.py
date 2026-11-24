"""r17 study: data facts before designing (read only; writes work/study_data_r17.json).

  - the panel set (KR_PlayerEventCount literals in the BASE AIN) against the 1,164 calendar events: the 121 outside, by place
  - where the 8 outside events of months 4-11 sit (cards: dated or not, bundle stages; drawers: size)
  - drawer rows per (month, lane) with the r17 counting (panel set) and the longest drawer row text in the new form
  - month-12 (회상 · 그 밖): every event outside the panel?
"""
import sys, json, collections, re
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import r17lib as L

T = L.readj(L.R15 / 'work' / 'build' / 'tables.json')           # r15 baked tables (= base)
cards, chips = T['cards'], T['chips']
KIND_KR = ['우선 대화', '특훈 뒤 대화', '반한 뒤 대화', '초대', '던전 동행', '그 밖', '회상', '쓰이지 않음']
LANE_KR = ['본편', '이즈미', '쿄카', '마나미', '마코토', '신카이', '호시카와', '모모세', '던전']


def lane_name(l):
    if l <= 8:
        return LANE_KR[l]
    if l <= 15:
        return '회상 %d쪽' % (l - 8)
    return '쓰이지 않는 장면'


bd = L.base_dir()
path = L.WORK / 'study' / 'base_KR_PlayerEventCount.jam'
if not path.exists():
    L.cmd('ain', 'dump', '--function', 'KR_PlayerEventCount', '-o', path, bd / 'NightRemaster.ain')
lines = [l.strip() for l in path.read_text('utf8').splitlines()]
groups = collections.defaultdict(list)
cur = None
for i, l in enumerate(lines):
    if l == '.LOCALREF group' and i + 2 < len(lines) and lines[i + 1].startswith('PUSH ') and lines[i + 2] == 'EQUALE':
        cur = int(lines[i + 1].split()[1])
        continue
    z = re.match(r'S_PUSH "(.*)"', l)
    if z and cur is not None:
        groups[cur].append(json.loads('"' + z.group(1) + '"'))
pset = {n for v in groups.values() for n in v}
ev = {int(k): v for k, v in T['events'].items()}
# calendar event names: the r15 tables do not hold fn; rebuild from the label rule (verified in r15/r16: KR_T9Fn == chart fn)
def fn(no):
    s = ('E%04d' % no) if no == 1706 else ('E%05d' % no)
    s = {'E01707': '01707', 'E02132': '02132'}.get(s, s)
    return 'ＥＶ／元／' + s
allev = sorted(set(T['stages']) | set(T['scenes']))
out_set = sorted(no for no in allev if fn(no) not in pset)
assert len(allev) == 1164 and len(pset) == 1043 and not (pset - {fn(no) for no in allev}), (len(allev), len(pset))
res = dict(calendar=len(allev), panel=len(pset), outside=len(out_set))
where = {}
for c in cards:
    for i, s in enumerate(c['stages']):
        where[s] = dict(kind='card', month=c['month'], lane=c['lane'], day=c['day'], card=c['k'], key=c['key'], stage=i + 1, size=c['size'])
for ch in chips:
    for s in ch['scenes']:
        where[s] = dict(kind='drawer', month=ch['month'], lane=ch['lane'], chip=ch['c'], id=ch['id'], size=ch['size'], drawer=KIND_KR[ch['kind']])
res['outside_by_month'] = dict(collections.Counter(where[no]['month'] for no in out_set))
res['outside_months_4_11'] = [dict(event='E%05d' % no, **where[no]) for no in out_set if where[no]['month'] <= 11]
res['month12_all_outside'] = all(no in set(out_set) for no in allev if where[no]['month'] == 12)
res['month12_events'] = sum(1 for no in allev if where[no]['month'] == 12)
res['outside_in_dated_cards'] = [no for no in out_set if where[no]['kind'] == 'card' and where[no]['day']]
# drawer rows in the new form (panel-set counts for months 4-11, all for month 12)
outs = set(out_set)
rows = []
for ch in chips:
    n = len([s for s in ch['scenes'] if ch['month'] == 12 or s not in outs])
    name = lane_name(ch['lane']) if ch['lane'] >= 9 else KIND_KR[ch['kind']]
    t = '%s %d/%d □□□□□' % (name, n, n)
    t2 = ('%s · %s %d/%d □□□□□' % (LANE_KR[ch['lane']], name, n, n)) if ch['lane'] < 9 else t
    rows.append((len(t2), t2, len(t), t, ch['id'], n, ch['size']))
rows.sort(reverse=True)
res['longest_drawer_rows'] = rows[:5]
res['drawer_rows_zero_count'] = [r[4] for r in rows if r[5] == 0]
# (month, lane) with both cards and drawers on the first lane page (<= 10 rows)
pages = []
for mo in range(4, 12):
    for l in range(9):
        nc = sum(1 for c in cards if c['month'] == mo and c['lane'] == l)
        nd = sum(1 for ch in chips if ch['month'] == mo and ch['lane'] == l)
        if nc and nd:
            pages.append((mo, l, nc, nd))
res['lanes_with_cards_and_drawers'] = pages
res['month12_chips'] = [(ch['c'], ch['id'], ch['size']) for ch in chips if ch['month'] == 12]
L.writej(L.WORK / 'study_data_r17.json', dict(res, outside_numbers=out_set))
print(json.dumps(res, ensure_ascii=False, indent=1))
