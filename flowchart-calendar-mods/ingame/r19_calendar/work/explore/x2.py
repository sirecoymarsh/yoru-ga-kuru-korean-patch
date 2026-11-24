import sys, json, pickle, collections
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
data = pickle.load(open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'rb'))
sch = json.load(open(FLOW + r'\graph\schedule.json', encoding='utf-8'))
lab = json.load(open(FLOW + r'\graph\labels.json', encoding='utf-8'))
ev = {e['id']: e for e in sch['events']}
r15 = json.load(open(FLOW + r'\ingame\r15_calendar\work\build\tables.json', encoding='utf-8'))
r18 = json.load(open(FLOW + r'\ingame\r18_calendar\work\build\tables.json', encoding='utf-8'))
tails = r18['tails']
cards = r15['cards']
for k, v in sorted(tails.items(), key=lambda x: int(x[0])):
    c = cards[int(k)]
    e = ev[c['entry']]
    sp = lab['cards'][str(c['entry'])]['speakers']
    trig = [(t['kind'], t.get('source'), t.get('date'), t.get('time_id'), t.get('guards')) for t in e['triggers']]
    print(k, c['key'], c['month'], c['lane'], c['day'], c['slot'], 'size', c['size'], 'entry', c['entry'], 'cond', c['cond'], '| tail', v['row'])
    print('    speakers', sp, 'cat', e['category'], 'p', e['person'], e['person2'])
    print('    trig', json.dumps(trig, ensure_ascii=False)[:400])
