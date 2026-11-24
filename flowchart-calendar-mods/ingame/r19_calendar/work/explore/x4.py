import sys, json, pickle, collections, re
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
data = pickle.load(open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'rb'))
sch = json.load(open(FLOW + r'\graph\schedule.json', encoding='utf-8'))
S = {e['id']: e for e in sch['events']}
ev = {int(k): v for k, v in data['ev'].items()}
persons = data['persons']
print('persons', persons)
c = collections.Counter()
for ch in data['chips']:
    c[(ch['page'], ch['lane'], ch['kind'])] = len(ch['entries'])
# walks
wc = collections.Counter()
for ch in data['chips']:
    if ch['kind'] == 'walk':
        for no in ch['entries']:
            e = S[no]
            wc[(ch['lane'], e['person'], e['person2'])] += 1
for k, v in sorted(wc.items(), key=lambda x: (x[0][0], x[0][1] or 0, x[0][2] or 0)): print('walk', k, v)
# dungeon-lane chips
for ch in data['chips']:
    if ch['lane'] == 'dungeon':
        print('dungeon chip', ch['id'], ch['entries'], [S[n]['category'] for n in ch['entries']], [(S[n]['person'], S[n]['person2']) for n in ch['entries']])
# walks per drawer and person2 counts
per = collections.Counter()
for ch in data['chips']:
    if ch['kind'] == 'walk':
        for no in ch['entries']:
            e = S[no]
            other = e['person2'] if ('p%d' % e['person']) == ch['lane'] else e['person']
            per[(ch['id'], other)] += 1
print('max walks per drawer&partner', max(per.values()), per.most_common(5))
# after/prio/invite/turned max count per drawer
for kind in ('after', 'prio', 'invite', 'turned', 'etc', 'mem', 'unused'):
    ns = [len(ch['entries']) for ch in data['chips'] if ch['kind'] == kind]
    print(kind, len(ns), 'max', max(ns) if ns else None, 'sum', sum(ns))
