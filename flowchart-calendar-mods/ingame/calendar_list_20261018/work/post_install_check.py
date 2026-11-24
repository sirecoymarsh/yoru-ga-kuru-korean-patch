# -*- coding: utf-8 -*-
"""Read only (10-18): independent check of the stage-3 install - journal, pointer, manifest rows, runtime files, contracts, saves,
progress note. Writes work/post_install_check.json."""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import lvlib as L

CODEX = L.CODEX
out = {}
ptr = json.loads(L.CURRENT.read_text('utf8'))
man_path = Path(ptr['manifest'])
out['pointer'] = dict(status=ptr['status'], manifest_sha256=ptr['manifest_sha256'],
                      manifest_hash_matches=L.sha(man_path) == ptr['manifest_sha256'])
ev = CODEX / 'evidence' / 'calendar_list_20261018'
j = json.loads((ev / 'journal.json').read_text('utf8'))
out['journal'] = j.get('status')
man = json.loads(man_path.read_text('utf8'))
rt = Path(ptr['runtime']) if 'runtime' in ptr else man_path.parent / 'runtime'
rows = {r['path']: r for r in man['files']}
bad = [p for p, r in rows.items() if not (rt / p).exists() or L.sha(rt / p) != r['sha256']]
out['runtime_files'] = len(rows)
out['runtime_mismatches'] = bad
out['runtime_ain'] = L.sha(rt / 'NightRemaster.ain')
# the previous manifest (stage 2) - which rows differ
prev_path = None
for cand in [ev / 'source' / 'previous_manifest.json', ev / 'previous_manifest.json']:
    if cand.exists():
        prev_path = cand
if prev_path is None:
    for cand in sorted(ev.rglob('*.json')):
        try:
            d = json.loads(cand.read_text('utf8'))
        except Exception:
            continue
        if isinstance(d, dict) and isinstance(d.get('files'), list) and d.get('status') == 'CALENDAR_OVERVIEW_20261018_INSTALLED_NATIVE_PASS':
            prev_path = cand
            break
if prev_path is not None:
    prev = {r['path']: r['sha256'] for r in json.loads(prev_path.read_text('utf8'))['files']}
    out['previous_manifest'] = str(prev_path)
    out['rows_changed'] = sorted(p for p in set(prev) | set(rows) if prev.get(p) != (rows[p]['sha256'] if p in rows else None))
# contracts
R = man_path.parent if (man_path.parent / 'required_calendar_list_20261018.json').exists() else CODEX
cs = sorted(R.glob('required_*.json'))
if not cs:
    cs = sorted(CODEX.rglob('required_calendar_list_20261018.json'))
    R = cs[0].parent if cs else R
    cs = sorted(R.glob('required_*.json'))
out['contracts_dir'] = str(R)
out['contracts'] = len(cs)
wrong = []
for c in cs:
    d = json.loads(c.read_text('utf8'))
    rf = d.get('required_files') or {}
    if rf.get('NightRemaster.ain') not in (None, out['runtime_ain']):
        wrong.append(c.name)
out['contracts_with_other_ain'] = wrong
new = json.loads((R / 'required_calendar_list_20261018.json').read_text('utf8'))
out['new_contract_status'] = new.get('status')
# saves
before = json.loads((HERE / 'work' / 'saves_before_install.json').read_text('utf8'))
now = {p.relative_to(L.SAVES).as_posix(): L.sha(p) for p in L.SAVES.rglob('*') if p.is_file()}
out['saves'] = len(now)
out['saves_changed'] = sorted(k for k in set(before) | set(now) if before.get(k) != now.get(k))
# progress note
prog = (CODEX / 'progress.md').read_text('utf8')
out['progress_note'] = '이벤트 캘린더 장면 목록' in prog[-20000:]
(HERE / 'work' / 'post_install_check.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), 'utf8')
print(json.dumps(out, ensure_ascii=False, indent=1))
