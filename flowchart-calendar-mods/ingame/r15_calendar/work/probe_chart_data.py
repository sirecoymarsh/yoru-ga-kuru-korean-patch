"""r15 study: call chart/build_chart_v2.build() as a module (output HTML into r15 tmp) and look at the returned data."""
import sys, os, json, collections, io, contextlib
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r15lib as L
sys.path.insert(0, str(L.FLOW / 'chart'))
import build_chart_v2 as V2

out = L.TMP / 'chart_v2_probe.html'
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    data = V2.build(str(out))
print('build printed', len(buf.getvalue()), 'chars')
pickle_path = L.WORK / 'chart_v2_data.json'
pickle_path.write_text(json.dumps(data, ensure_ascii=False), 'utf8')
print('keys', list(data))
print('counts', data['counts'])
print('join', data['join'], 'lanes', data['lanes'])
print('pages', [(p['key'], p['sum']['cards'], p['sum']['entries'], p['sum']['chips']) for p in data['pages']])
c = data['cards'][0]
print('card0', {k: v for k, v in c.items() if k != 'rows'})
print('card0 rows', c['rows'][:3])
big = max(data['cards'], key=lambda c: c['n'])
print('biggest card', big['key'], big['n'], big['lane'], big['page'], big['pl'])
print('card lanes', collections.Counter(c['lane'] for c in data['cards']))
print('card types', collections.Counter(c['type'] for c in data['cards']))
print('chips', len(data['chips']), collections.Counter(ch['kind'] for ch in data['chips']))
ch = data['chips'][0]
print('chip0', {k: v for k, v in ch.items() if k not in ('order',)})
print('ev sample', {k: v for k, v in data['ev'][str(c['entry'])].items() if k not in ('first', 'ans')})
print('ev keys', list(data['ev'][str(c['entry'])].keys()))
print('refchips', len(data['refchips']), 'bands', len(data['bands']))
print('marks', data['marks'][:5])
