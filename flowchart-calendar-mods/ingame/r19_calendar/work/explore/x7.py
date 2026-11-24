import sys, json, pickle, collections, re
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
data = pickle.load(open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'rb'))
sch = json.load(open(FLOW + r'\graph\schedule.json', encoding='utf-8'))
lab = json.load(open(FLOW + r'\graph\labels.json', encoding='utf-8'))
mem = json.load(open(FLOW + r'\graph\memory.json', encoding='utf-8'))
S = {e['id']: e for e in sch['events']}
ev = {int(k): v for k, v in data['ev'].items()}
# drawer order vs number order
bad = 0
for ch in data['chips']:
    order = [x[0] for x in ch['order'] if x[4]]
    if order != sorted(order):
        bad += 1
        print('order differs', ch['id'], order[:12])
print('drawers with order != number order', bad)
# mem chips: slots
for ch in data['chips']:
    if ch['kind'] == 'mem':
        noslot = [n for n in ch['entries'] if str(n) not in ch['slots']]
        print(ch['id'], 'n', len(ch['entries']), 'no slot', noslot, [ (n, S[n]['replay_of'], [t['kind'] for t in S[n]['triggers']]) for n in noslot][:6])
print(mem.keys(), mem['entries'][:3])
# stage names stats
party = {data['persons'][str(p)] for p in range(2, 9)}
def comp(no):
    for s in lab['cards'][str(no)]['speakers']:
        for p in s.split('＆'):
            p = p.strip('\u3000 ')
            if p in party:
                return p
    return None
none = 0; both = 0; tot = 0
for c in data['cards']:
    if c['n'] < 2: continue
    stages = [r for r in c['rows'] if r[6]]
    for i, r in enumerate(stages):
        tot += 1
        via = r[3] if r[2] == 'answer' else None
        cp = comp(r[0])
        if not via and not cp: none += 1
        if via and cp: both += 1
print('stages', tot, 'neither via nor companion', none, 'both', both)
# E05000
print(5000, S[5000]['category'], S[5000]['triggers'], lab['cards']['5000']['speakers'])
print(6001, S[6001]['triggers'])
