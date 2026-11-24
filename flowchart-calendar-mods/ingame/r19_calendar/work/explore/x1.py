import sys, io, json, contextlib, collections, re, os, pickle
sys.dont_write_bytecode = True
FLOW = r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922'
sys.path.insert(0, FLOW + r'\chart')
import build_chart_v2 as V2
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    data = V2.build(FLOW + r'\ingame\r19_calendar\tmp\chart_v2_explore.html')
pickle.dump(data, open(FLOW + r'\ingame\r19_calendar\work\explore\data.pkl', 'wb'))
print(buf.getvalue()[-800:])
print(data.keys())
