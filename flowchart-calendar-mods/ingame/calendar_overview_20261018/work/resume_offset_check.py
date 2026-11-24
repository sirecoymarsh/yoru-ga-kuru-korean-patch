# -*- coding: utf-8 -*-
"""Read only (10-18): the user's saves against the calendar-overview candidate (copied from calendar_redesign_20261017/work).
For every return record (RSM14) of every save: does its function sit in a function this layer changes, does its crc equal the
function table crc of the base AND of the candidate, and does it resume at (or inside) a swapped instruction?
Also lists saves whose stack holds an open choice / partner confirm / new-game question (they resume in the original call chain)."""
import sys, json, collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ovlib as L

HERE = Path(__file__).resolve().parent.parent
bm = L.read_meta(L.base_paths()['meta'])
cm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
man = L.readj(HERE / 'candidate' / 'manifest.json')
sites = collections.defaultdict(list)
for s in man['same_length_sites'] + man.get('message_box_sites', []):
    sites[s['function']].append(s)
names = collections.defaultdict(list)
for f in bm['functions']:
    names[L.raw_symbol(bm, f['index'])].append(f['index'])
OPEN = {'■選択メッセージ／実行': 'choice', 'C_SelectMessage@Run': 'choice', '■選択ダイアログ／実行': 'dialog',
        'C_SceneTraining@RunSelectPartner': 'partner screen'}


def bare(name):
    """'f(int, string)' -> 'f'; lambda names keep their inner '(...)' (only the final parameter list is cut)."""
    if not name.endswith(')'):
        return name
    depth = 0
    for i in range(len(name) - 1, -1, -1):
        depth += name[i] == ')'
        depth -= name[i] == '('
        if depth == 0:
            return name[:i]
    return name


def u32(v):
    return None if v is None else v & 0xffffffff
stats = collections.Counter()
hits, opened, bad = [], [], []
saves = sorted(L.SAVES.glob('NightR*.asd'))
for p in saves:
    try:
        r = L.save_records(p)
    except AssertionError:
        stats['other_format'] += 1
        stats['other_format_head_' + p.read_bytes()[:4].hex()] += 1
        continue
    if not r:
        stats['not_resume_save'] += 1
        continue
    stats['resume_saves'] += 1
    frames = [dict(x, name=bare(x['name'])) for x in [r['ip']] + r['returns'] if x['address'] != -1]
    if stats['resume_saves'] == 1:
        print('SAMPLE', p.name, [(x['name'], x['address'], x['offset'], x['crc']) for x in frames][:5])
    kinds = sorted({OPEN[x['name']] for x in frames if x['name'] in OPEN})
    if kinds:
        opened.append(dict(save=p.name, kinds=kinds, chain=[x['name'] for x in frames][-6:]))
    for x in frames:
        stats['frames'] += 1
        fids = [i for i in names.get(x['name'], []) if u32(bm['functions'][i].get('crc')) == x['crc']] or names.get(x['name'], [])
        if not fids:
            stats['frame_function_unknown'] += 1
            bad.append(dict(save=p.name, fn=x['name'], why='unknown function'))
            continue
        if len(fids) > 1:
            stats['frame_name_ambiguous'] += 1
        fid = fids[0]
        bcrc = u32(bm['functions'][fid].get('crc'))
        ccrc = u32(cm['functions'][fid].get('crc'))
        if x['crc'] != bcrc or bcrc != ccrc:
            bad.append(dict(save=p.name, fn=x['name'], why='crc', frame=x['crc'], base=bcrc, cand=ccrc))
        if bm['functions'][fid]['address'] != cm['functions'][fid]['address']:
            bad.append(dict(save=p.name, fn=x['name'], why='function moved'))
        if x['name'] in sites:
            stats['frames_in_changed_functions'] += 1
            addr = bm['functions'][fid]['address']
            here = x['address']
            rel = []
            for s in sites[x['name']]:
                if s['site'] <= here < s['site'] + 6:
                    bad.append(dict(save=p.name, fn=x['name'], why='resumes at a swapped instruction', at=here, site=s['site']))
                rel.append(here - s['site'])
            hits.append(dict(save=p.name, fn=x['name'], resume=here, offset=x['offset'], from_function_start=here - addr,
                             to_sites=rel))
out = dict(candidate_ain=L.sha(HERE / 'candidate' / 'NightRemaster.ain'), candidate_meta=L.sha(L.WORK / 'build' / 'candidate_meta.json'),
           base_ain=L.BASE_AIN_SHA, save_folder=str(L.SAVES), read_only=True, stats=stats, saves=len(saves), problems=bad, open_on_stack=opened,
           frames_in_changed_functions=hits, functions=sorted({h['fn'] for h in hits}))
(L.WORK / 'resume_offset_check.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf8')
print(json.dumps(dict(stats=stats, saves=len(saves), problems=bad[:10], open_on_stack=opened,
                      functions=collections.Counter(h['fn'] for h in hits)), ensure_ascii=False, indent=1))
