"""r15 study: event name rule and first message numbers against the live base AIN."""
import sys, json, collections
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r15lib as L

base = L.WORK / 'base'
data = json.loads((L.WORK / 'chart_v2_data.json').read_text('utf8'))
m = L.read_meta(base / 'meta.json')
vers = L.versions(base / 'raw_code.jam')
byname = {}
for f in m['functions']:
    byname.setdefault(L.raw_symbol(m, f['index']), []).append(f['index'])


def label(no):
    return ('E%04d' % no) if no == 1706 else ('E%05d' % no)


def adjust(s):
    return {'E01707': '01707', 'E02132': '02132'}.get(s, s)


bad = []
msg_bad = []
cats = collections.Counter()
nomsg = 0
for k, e in data['ev'].items():
    no = int(k)
    want = 'ＥＶ／元／' + adjust(label(no))
    cats[e['cat']] += 1
    if e['fn'] != want:
        bad.append((no, e['fn'], want))
    ids = byname.get(e['fn'], [])
    if len(ids) != 1:
        bad.append((no, e['fn'], 'fid count %d' % len(ids)))
        continue
    v = L.live_version(m, vers, ids[0])
    nums = [int(op.split()[1], 16) for _, op in v['ops'] if op.startswith('MSG ')]
    if e['lines'] == 0:
        nomsg += 1
        if nums:
            msg_bad.append((no, 'no lines but MSG', nums[:3]))
        if e['m0'] is not None:
            msg_bad.append((no, 'm0 set without lines'))
        continue
    if not nums or nums[0] != e['m0']:
        msg_bad.append((no, e['m0'], nums[:3]))
print('events', len(data['ev']), 'name mismatches', len(bad), bad[:5])
print('first-MSG mismatches', len(msg_bad), msg_bad[:5], 'events without messages', nomsg)
print('categories', dict(cats))
