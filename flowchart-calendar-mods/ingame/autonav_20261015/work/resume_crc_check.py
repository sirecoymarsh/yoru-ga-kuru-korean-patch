# -*- coding: utf-8 -*-
"""Read only: what does the per-frame crc in a resume save (RSM14 return record) cover? For every return record of the user's
saves, compare the record's crc with candidate checksums of that function in the base AIN (raw code bytes, bytes without the
operand, ...). Also lists every saved frame that sits in a function this layer changes, with the return offset."""
import sys, zlib, struct, json, collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import anlib as L

bp = L.base_paths()
m = L.read_meta(bp['meta'])
raw = L.unpack(bp['ain'].read_bytes())
n = struct.unpack_from('<I', raw, 12)[0]
code = raw[16:16 + n]
vers = L.versions(bp['raw'])
starts = sorted({v['start'] for vs in vers.values() for v in vs})
import bisect


def body(fid):
    a = m['functions'][fid]['address']
    i = bisect.bisect_right(starts, a)
    end = starts[i] - 6 if i < len(starts) else len(code)
    return code[a - 6:end], code[a:end]


name_to_fid = collections.defaultdict(list)
for f in m['functions']:
    name_to_fid[L.raw_symbol(m, f['index'])].append(f['index'])
man = L.readj(Path(__file__).resolve().parent.parent / 'candidate' / 'manifest.json')
changed = {s['function'] for s in man['same_length_sites']}
stats = collections.Counter()
hits = []
examples = []
for name, p in L.SAVES.glob('NightR*.asd') and [(q.name, q) for q in sorted(L.SAVES.glob('NightR*.asd'))]:
    try:
        r = L.save_records(p)
    except Exception as ex:
        continue
    if not r:
        continue
    for rec in [r['ip']] + r['returns']:
        if rec['address'] == -1:
            continue
        fname = rec['name'].split('(')[0] if '(' in rec['name'] and not rec['name'].startswith('C_') else rec['name']
        fname = rec['name']
        fids = name_to_fid.get(fname) or name_to_fid.get(fname.split('(')[0])
        if not fids:
            stats['unknown_function'] += 1
            continue
        fid = fids[0]
        whole, after_hdr = body(fid)
        c1 = zlib.crc32(whole) & 0xffffffff
        c2 = zlib.crc32(after_hdr) & 0xffffffff
        stats['frames'] += 1
        if rec['crc'] == c1:
            stats['crc_eq_code_with_header'] += 1
        elif rec['crc'] == c2:
            stats['crc_eq_code_body'] += 1
        else:
            stats['crc_other'] += 1
            if len(examples) < 5:
                examples.append(dict(save=name, fn=fname, crc=hex(rec['crc']), body_crc=hex(c2), len=len(after_hdr)))
        if fname in changed:
            hits.append(dict(save=name, fn=fname, offset=rec['offset'], address=rec['address']))
print(json.dumps(dict(stats=stats, examples=examples, frames_in_changed_functions=hits[:40], n_hits=len(hits)), ensure_ascii=False, indent=1))
