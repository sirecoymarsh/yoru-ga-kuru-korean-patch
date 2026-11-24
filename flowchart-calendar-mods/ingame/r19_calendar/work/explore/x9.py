import sys, io, json, contextlib, collections, re, pickle
sys.dont_write_bytecode = True
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
sys.path.insert(0, FLOW + r'\chart')
import build_chart_v2 as V2
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    data = V2.build(FLOW + r'\ingame\r19_calendar\tmp\chart_v2_names.html')
pickle.dump(data, open(FLOW + r'\ingame\r19_calendar\work\explore\data_r19.pkl', 'wb'))
ev = {int(k): v for k, v in data['ev'].items()}
print('max nm', max(len(v['nm']) for v in ev.values()), max(ev.values(), key=lambda v: len(v['nm']))['nm'])
print('max card nm', max(len(c['nm']) for c in data['cards']))
tails = [(c['key'], c['tail'], c['nm']) for c in data['cards'] if c['tail']]
print('tails', len(tails))
for t in tails: print('  ', t)
empty = [(no, v['ns']) for no, v in ev.items() if re.fullmatch(r'\d+\.', v['ns'])]
print('empty stage shorts', empty)
# samples
def show(nos):
    for no in nos:
        v = ev[no]; print('  E%05d' % no, '|', v['nm'], '|', v['ns'], '|', v['nr'], '|', v.get('nk'))
print('stage samples'); show([273, 258, 110, 109, 54, 832, 801, 59, 60, 802])
print('drawer samples'); show([1001, 10001, 30021, 30022, 30023, 30024, 5000, 6001, 60015, 60201, 60205, 50101])
walks = [no for no, v in ev.items() if v['cat'] == 'dungeon_walk'][:6]
show(walks)
unused = [no for no, v in ev.items() if v['cat'] == 'unknown'][:3]; show(unused)
for no in (401, 10001, 30157, 30158, 10501, 20501, 40061):
    print('when', no, ev[no]['when'])
# chars outside font? list distinct chars in names
chars = collections.Counter(ch for v in ev.values() for f in ('nm', 'ns', 'nr') for ch in v[f])
print(''.join(sorted(chars)))
