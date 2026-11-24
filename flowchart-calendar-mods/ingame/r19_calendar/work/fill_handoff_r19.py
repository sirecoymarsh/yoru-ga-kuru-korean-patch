"""one-off: fill the «…» placeholders of 인계_r19.md from the evidence files (after finalize_evidence_r19.py)."""
import sys, json, os
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r19lib as L

doc = L.HERE / '인계_r19.md'
s = doc.read_text('utf8')
man = L.readj(L.HERE / 'candidate' / 'manifest.json')
nm = L.read_meta(L.WORK / 'build' / 'candidate_meta.json')
vm = L.readj(L.WORK / 'build' / 'vm_verification.json')
native = L.readj(L.WORK / 'build' / 'native_compare.json')
probe = L.readj(L.EVID / 'probe_result.json')
ready = L.readj(L.EVID / 'readiness.json')
hashes = L.readj(L.EVID / 'hashes.json')


def mb(p):
    return round(sum(f.stat().st_size for f in Path(p).rglob('*') if f.is_file() and os.stat(f).st_nlink == 1) / 1e6)


fw = man['forwarded_functions']
rep = {
    '«A1»': str(nm['functions'][fw['KR_T18CardRow']['index']]['address']),
    '«A2»': str(nm['functions'][fw['KR_T18CardTitle']['index']]['address']),
    '«A3»': str(nm['functions'][fw['KR_T18EventTitle']['index']]['address']),
    '«A4»': str(nm['functions'][fw['KR_T9StagePage']['index']]['address']),
    '«A5»': str(nm['functions'][fw['KR_T9ChipPage']['index']]['address']),
    '«AIN»': '`%s`' % man['files']['NightRemaster.ain']['sha256'],
    '«AINSIZE»': '{:,}'.format(man['files']['NightRemaster.ain']['size']),
    '«CHART»': '`%s`' % man['files']['Manual/chart/yoru_flowchart_v2.html']['sha256'],
    '«MANIFEST»': '`%s`' % L.sha(L.HERE / 'candidate' / 'manifest.json'),
    '«VERIFIED_AT»': ready['checked'][:16].replace('T', ' '),
    '«DIALOGS»': '{:,}'.format(vm['counts']['V2_dialogs']),
    '«V21»': '{:,}'.format(vm['counts']['V21_texts_without_e_numbers']),
    '«V22»': '{:,}'.format(vm['counts']['V22_items_unique_on_page']),
    '«V26»': '{:,}'.format(vm['counts']['V26_when_tokens']),
    '«NATIVE»': str(native['counts']['N_blocks_identical']),
    '«SECONDS»': str(round(probe['seconds'])),
    '«SHOTS»': ', '.join('`%s`' % Path(x).stem for x in probe['screenshots']),
    '«ZOOMS»': str(len(hashes['zooms'])),
    '«WORKMB»': str(mb(L.WORK)),
    '«PROBEMB»': str(mb(L.HERE / 'probe')),
    '«EVIDMB»': str(mb(L.EVID)),
    '«SAMPLES»': (L.EVID / 'name_samples.md').read_text('utf8').strip(),
}
for k, v in rep.items():
    assert k in s, k
    s = s.replace(k, v)
assert '«' not in s, [l for l in s.splitlines() if '«' in l][:3]
doc.write_text(s, 'utf8')
print('filled', {k: v[:60] for k, v in rep.items() if k != '«SAMPLES»'})
