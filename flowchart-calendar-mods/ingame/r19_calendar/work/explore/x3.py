import sys, json, pickle, collections, re
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
data = pickle.load(open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'rb'))
ev = {int(k): v for k, v in data['ev'].items()}
pat = re.compile(r'E\d{4,5}')
kinds = collections.Counter()
ex = collections.defaultdict(list)
for no, e in sorted(ev.items()):
    for i, w in enumerate(e['when']):
        if pat.search(w):
            shape = pat.sub('E#', w)
            shape = re.sub(r'\d+', 'n', shape)
            kinds[(i == 0, shape)] += 1
            if len(ex[shape]) < 3:
                ex[shape].append((no, e['unit'], w))
for k, v in kinds.most_common():
    print(v, k, ex[k[1]][:2])
