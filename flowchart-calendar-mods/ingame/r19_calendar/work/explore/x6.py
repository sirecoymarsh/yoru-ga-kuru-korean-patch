import sys, json, pickle, collections, re
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
data = pickle.load(open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'rb'))
sch = json.load(open(FLOW + r'\graph\schedule.json', encoding='utf-8'))
lab = json.load(open(FLOW + r'\graph\labels.json', encoding='utf-8'))
S = {e['id']: e for e in sch['events']}
for c in data['cards']:
    if c['lane'] != 'dungeon': continue
    stages = [r[0] for r in c['rows'] if r[6]]
    srcs = []
    for no in stages:
        ss = sorted({t['source'] for t in S[no]['triggers'] if t['kind'] == 'dungeon'})
        srcs.append((no, [s.split('@')[-1] if '@' in s else s for s in ss], S[no]['category']))
    ent = S[c['entry']]
    print(c['key'], c['pl'], 'n', c['n'], 'entry', c['entry'], sorted({t['source'] for t in ent['triggers'] if t['kind']=='dungeon'}))
    print('     ', srcs[:25])
# non-card dungeon-trigger events
nc = [e for e in sch['events'] if any(t['kind']=='dungeon' for t in e['triggers']) and ('c:' not in data['ev'][str(e['id'])]['unit'])]
print('dungeon-trigger events outside cards', [(e['id'], e['category'], data['ev'][str(e['id'])]['unit']) for e in nc])
# dungeon-trigger events inside non-dungeon cards
for c in data['cards']:
    if c['lane'] == 'dungeon': continue
    for r in c['rows']:
        if r[6] and any(t['kind']=='dungeon' for t in S[r[0]]['triggers']):
            print('dungeon trig in', c['key'], c['lane'], r[0], sorted({t['source'] for t in S[r[0]]['triggers'] if t['kind']=='dungeon'}))
