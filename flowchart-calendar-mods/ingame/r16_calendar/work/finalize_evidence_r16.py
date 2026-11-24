"""r16: gather the evidence into 증거\\ and record the base hashes a second time (did Codex move the runtime meanwhile?).
If the runtime moved, the candidate is not installable (publish --verify says so) and the whole chain is rebuilt on the new base."""
import sys, json, shutil, datetime
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r16lib as L

HERE = L.HERE
ev = L.EVID
ptr, rt = L.runtime()
man = L.readj(HERE / 'candidate' / 'manifest.json')
copies = {
    'candidate_manifest.json': HERE / 'candidate' / 'manifest.json',
    'vm_verification.json': L.WORK / 'build' / 'vm_verification.json',
    'vm_verification_selftest.json': L.WORK / 'build' / 'vm_verification_selftest.json',
    'native_compare.json': L.WORK / 'build' / 'native_compare.json',
    'native_opcode_audit.json': L.WORK / 'build' / 'native_opcode_audit.json',
    'scan_report.json': L.WORK / 'scan_report.json',
    'transaction_verification.json': L.WORK / 'transaction_verification.json',
    'baked_tables_r16.json': L.WORK / 'build' / 'tables.json',
    'savecopy_manifest.json': L.WORK / 'savecopy_manifest.json',
    'base_snapshot.json': L.WORK / 'base' / 'snapshot.json',
    'base_moved_check_0515.json': L.WORK / 'base_moved_check' / 'result.json',
    'contract_draft_required_calendar_r16.json': HERE / 'required_calendar_r16.json',
    'study_data.json': L.WORK / 'study_data.json',
}
for name, src in copies.items():
    shutil.copy2(src, ev / name)
runtime_now = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'NightRemasterPact.afa', 'NightRemasterEX.ex']}
unchanged = (runtime_now == {'NightRemaster.ain': L.BASE_AIN_SHA, 'NightRemasterPact.afa': L.BASE_PACT_SHA, 'NightRemasterEX.ex': L.BASE_EX_SHA}
             and ptr['manifest_sha256'] == man['base']['manifest_sha256'] and ptr['status'] == man['base']['status'])
hashes = dict(
    checked=datetime.datetime.now().astimezone().isoformat(),
    base_at_start=dict(ain=L.BASE_AIN_SHA, pact=L.BASE_PACT_SHA, ex=L.BASE_EX_SHA, manifest=man['base']['manifest_sha256'], status=man['base']['status']),
    runtime_at_end=dict(runtime_now, manifest=ptr['manifest_sha256'], status=ptr['status'], current_json_sha256=L.sha(L.CURRENT)),
    runtime_unchanged=unchanged,
    r15_candidate=dict(ain=L.R15_AIN_SHA, same_as_file=L.sha(L.R15 / 'candidate' / 'NightRemaster.ain') == L.R15_AIN_SHA),
    candidate=dict(ain=L.sha(HERE / 'candidate' / 'NightRemaster.ain'), ain_size=(HERE / 'candidate' / 'NightRemaster.ain').stat().st_size,
                   manifest=L.sha(HERE / 'candidate' / 'manifest.json')),
    contract_draft=L.sha(HERE / 'required_calendar_r16.json'),
    scripts={p.name: L.sha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.suffix in ('.py', '.jaf', '.ps1', '.json', '.md')},
    work_scripts={p.name: L.sha(p) for p in sorted(L.WORK.iterdir()) if p.is_file() and p.suffix == '.py'},
    screenshots={p.name: L.sha(p) for p in sorted((ev / 'probe').glob('*.png'))},
    evidence_files=sorted(p.name for p in ev.iterdir()),
)
L.writej(ev / 'hashes.json', hashes)
print(json.dumps({k: v for k, v in hashes.items() if k not in ('scripts', 'work_scripts', 'screenshots', 'evidence_files')}, ensure_ascii=False, indent=1))
assert unchanged, 'RUNTIME MOVED — discard this candidate and rebuild on the new base'
