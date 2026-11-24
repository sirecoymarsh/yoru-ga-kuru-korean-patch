"""r23: save copies with the least new writing (copy of r22 work/savecopy_r22.py).

The user's save folder (OneDrive, C:) is only READ. Every file is hashed; a file identical to the copy the r22 map points to
(r22_chart\\work\\savecopy_manifest.json -> an r15-r22 copy, read only) is used from there, anything new or changed is copied
into r23 work\\savecopy. work\\savecopy_manifest.json maps every file to the copy that holds it
(path, size, sha256, reused_from).
"""
import sys, shutil, datetime
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r23lib as L

free = shutil.disk_usage('P:\\').free
assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
prev = L.readj(L.R22_SAVEMAP)["files"]
out = {}
copied = reused = 0
for p in sorted(L.SAVES.rglob('*')):
    if not p.is_file():
        continue
    rel = p.relative_to(L.SAVES).as_posix()
    data = p.read_bytes()
    h = L.sha_bytes(data)
    old = prev.get(rel)
    if old and old['size'] == len(data) and old['sha256'] == h and Path(old['path']).exists() and L.sha(old['path']) == h:
        where = next((n for n, d in (('r15', L.R15), ('r16', L.R16), ('r17', L.R17), ('r18', L.R18), ('r19', L.R19), ('r20', L.R20),
                                     ('r21', L.R21), ('r22', L.R22))
                      if Path(old['path']).is_relative_to(d)), 'r23')
        out[rel] = dict(path=old['path'], size=len(data), sha256=h, reused_from=where)
        reused += 1
        continue
    dst = L.SAVECOPY / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    shutil.copystat(p, dst)
    assert L.sha(dst) == h
    out[rel] = dict(path=str(dst), size=len(data), sha256=h, reused_from=None)
    copied += 1
L.writej(L.WORK / 'savecopy_manifest.json', dict(source=str(L.SAVES), copied=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                 reused=reused, copied_new_or_changed=copied, files=out))
print('files', len(out), 'reused', reused, 'copied', copied, 'bytes copied', sum(v['size'] for v in out.values() if not v['reused_from']))
