"""r16: save copies with the least new writing.

The user's save folder (OneDrive, C:) is only READ. Every file is hashed; a file identical to its r15 copy
(r15_calendar\\work\\savecopy, read only) is used from there, anything new or changed is copied into r16 work\\savecopy.
work\\savecopy_manifest.json maps every file to the copy that holds it (path, size, sha256, reused_from_r15).
"""
import sys, shutil, datetime
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r16lib as L

r15 = L.readj(L.R15 / 'work' / 'savecopy_manifest.json')['files']
out = {}
copied = reused = 0
for p in sorted(L.SAVES.rglob('*')):
    if not p.is_file():
        continue
    rel = p.relative_to(L.SAVES).as_posix()
    data = p.read_bytes()
    h = L.sha_bytes(data)
    old = L.R15_SAVECOPY / rel
    if rel in r15 and tuple(r15[rel]) == (len(data), h) and old.exists() and L.sha(old) == h:
        out[rel] = dict(path=str(old), size=len(data), sha256=h, reused_from_r15=True)
        reused += 1
        continue
    dst = L.SAVECOPY / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    shutil.copystat(p, dst)
    assert L.sha(dst) == h
    out[rel] = dict(path=str(dst), size=len(data), sha256=h, reused_from_r15=False)
    copied += 1
L.writej(L.WORK / 'savecopy_manifest.json', dict(source=str(L.SAVES), copied=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                 reused_from_r15=reused, copied_new_or_changed=copied, files=out))
print('files', len(out), 'reused', reused, 'copied', copied)
