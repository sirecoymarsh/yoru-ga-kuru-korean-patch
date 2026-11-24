import sys, json, pickle, collections, re
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
data = pickle.load(open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'rb'))
sch = json.load(open(FLOW + r'\graph\schedule.json', encoding='utf-8'))
lab = json.load(open(FLOW + r'\graph\labels.json', encoding='utf-8'))
S = {e['id']: e for e in sch['events']}
ev = {int(k): v for k, v in data['ev'].items()}
vk = collections.Counter()
multi = [c for c in data['cards'] if c['n'] > 1]
print('multi-stage cards', len(multi), 'stage total', sum(c['n'] for c in multi))
for c in data['cards']:
    for r in c['rows']:
        vk[(r[2], r[6])] += 1
print('via kinds (kind, counts_here)', vk)
# stage own triggers kinds (non-entry)
tk = collections.Counter()
slot_stage = 0
for c in multi:
    stages = [r for r in c['rows'] if r[6]]
    for i, r in enumerate(stages):
        if i == 0: continue
        e = S[r[0]]
        kinds = tuple(sorted({t['kind'] for t in e['triggers']}))
        tk[kinds] += 1
        if any(t.get('time_id') for t in e['triggers']):
            slot_stage += 1
print('non-entry stage trigger kinds', tk)
print('non-entry stages with a time_id trigger', slot_stage)
# show 4 multi-stage cards fully
for c in multi[:6]:
    print(c['key'], c['lane'], c['pl'], 'n', c['n'], 'branches', c['branches'])
    for r in c['rows']:
        e = S[r[0]]
        sp = lab['cards'][str(r[0])]['speakers']
        print('   ', r[:4], r[5:], [ (t['kind'], t.get('from'), t.get('via_choice'), t.get('time_id'), t.get('date')) for t in e['triggers']], sp[:4])
