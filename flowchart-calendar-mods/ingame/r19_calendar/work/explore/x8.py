import sys, json, pickle, collections, re
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
data = pickle.load(open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'rb'))
sch = json.load(open(FLOW + r'\graph\schedule.json', encoding='utf-8'))
S = {e['id']: e for e in sch['events']}
ev = {int(k): v for k, v in data['ev'].items()}
for ch in data['chips']:
    if ch['id'] == 'mem:mem6:mem':
        for x in ch['order']:
            print(x, ch['slots'].get(str(x[0])), ev[x[0]]['when'], S[x[0]]['replay_of'])
cards = {c['key']: c for c in data['cards']}
# replay_of targets: dated main?
ro = collections.Counter()
for no, e in ev.items():
    if e['cat'] == 'memory_replay':
        r = S[no]['replay_of']
        if r is None:
            ro['none'] += 1; continue
        u = ev[r]['unit']
        if u.startswith('c:'):
            c = cards[u[2:]]
            ro[('card', c['lane'], 'd' in c['pl'])] += 1
        else:
            ro[('drawer', u)] += 1
print(ro)
