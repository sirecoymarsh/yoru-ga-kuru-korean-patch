"""r20: gather the evidence into 증거\\ and record the base hashes a final time (did Codex move the runtime meanwhile?).
If the runtime moved, the candidate is not installable (publish --verify says so) and the whole chain is rebuilt on the new
base. Keeps a copy of the r20 requirement text as read for this build (the design file itself is not touched).
(after r19 work/finalize_evidence_r19.py; r20 changes no shared data file: chart / graph / builder hashes are recorded unchanged)"""
import sys, json, shutil, datetime, re
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r20lib as L

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
    'baked_tables_r20.json': L.WORK / 'build' / 'tables.json',
    'savecopy_manifest.json': L.WORK / 'savecopy_manifest.json',
    'contract_draft_required_calendar_r20.json': HERE / 'required_calendar_r20.json',
}
for name, src in copies.items():
    if src.resolve() != (ev / name).resolve():
        shutil.copy2(src, ev / name)
design = L.FLOW / 'ingame' / '설계_v3_글메뉴판.md'
text = design.read_text('utf8')
z = re.search(r'^## r20 요구.*?(?=^## |\Z)', text, re.S | re.M)
assert z, 'r20 requirement section not found in the design file'
(ev / 'r20_요구_원문.md').write_text('<!-- 설계_v3_글메뉴판.md 의 「## r20 요구」 절 사본 (sha256 %s, %s 에 읽음) -->\n\n' % (
    L.sha(design), datetime.datetime.now().astimezone().isoformat()) + z.group(0), 'utf8')
runtime_now = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'NightRemasterPact.afa', 'NightRemasterEX.ex']}
chart_now = L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html')
unchanged = (runtime_now == {'NightRemaster.ain': L.BASE_AIN_SHA, 'NightRemasterPact.afa': L.BASE_PACT_SHA, 'NightRemasterEX.ex': L.BASE_EX_SHA}
             and ptr['manifest_sha256'] == man['base']['manifest_sha256'] and ptr['status'] == man['base']['status']
             and chart_now == man['base']['chart_sha256'])
contracts = sorted(p.name for p in L.CODEX.glob('required_*.json'))
draft = L.readj(HERE / 'required_calendar_r20.json')
j19 = L.readj(L.R19_JOURNAL)
hashes = dict(
    checked=datetime.datetime.now().astimezone().isoformat(),
    base_at_start=dict(ain=L.BASE_AIN_SHA, pact=L.BASE_PACT_SHA, ex=L.BASE_EX_SHA, manifest=man['base']['manifest_sha256'], status=man['base']['status'],
                       help_menu_chart=man['base']['chart_sha256']),
    runtime_at_end=dict(runtime_now, manifest=ptr['manifest_sha256'], status=ptr['status'], current_json_sha256=L.sha(L.CURRENT), help_menu_chart=chart_now),
    runtime_unchanged=unchanged,
    r19_install=dict(journal_status=j19['status'], ain=j19['after']['NightRemaster.ain'], required_calendar_r19_present=(L.CODEX / 'required_calendar_r19.json').exists()),
    contracts_at_end=len(contracts), contracts_same_as_draft=contracts == sorted(draft['preserves_contracts']),
    earlier_candidates_untouched=dict(
        r15=L.sha(L.R15 / 'candidate' / 'NightRemaster.ain') == L.R15_AIN_SHA,
        r16=L.sha(L.R16 / 'candidate' / 'NightRemaster.ain') == L.R16_AIN_SHA,
        r17=L.sha(L.R17 / 'candidate' / 'NightRemaster.ain') == L.R17_AIN_SHA,
        r18=L.sha(L.R18 / 'candidate' / 'NightRemaster.ain') == L.R18_AIN_SHA,
        r19=L.sha(L.R19 / 'candidate' / 'NightRemaster.ain') == L.R19_AIN_SHA),
    candidate=dict(ain=L.sha(HERE / 'candidate' / 'NightRemaster.ain'), ain_size=(HERE / 'candidate' / 'NightRemaster.ain').stat().st_size,
                   manifest=L.sha(HERE / 'candidate' / 'manifest.json')),
    contract_draft=L.sha(HERE / 'required_calendar_r20.json'),
    design_file_sha256=L.sha(design),
    shared_data_unchanged=dict(
        schedule_json=L.sha(L.FLOW / 'graph' / 'schedule.json'), build_chart_v2_py=L.sha(L.FLOW / 'chart' / 'build_chart_v2.py'),
        chart_html=L.sha(L.FLOW / 'chart' / 'yoru_flowchart_v2.html'), same_as_r19_build=man['chart_inputs']),
    scripts={p.name: L.sha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.suffix in ('.py', '.jaf', '.ps1', '.json', '.md')},
    work_scripts={p.name: L.sha(p) for p in sorted(L.WORK.iterdir()) if p.is_file() and p.suffix in ('.py', '.sh')},
    tool_scripts={p.name: L.sha(p) for p in sorted((L.WORK / 'tools').iterdir()) if p.is_file() and p.suffix == '.py'},
    screenshots={p.name: L.sha(p) for p in sorted((ev / 'probe').glob('*.png'))},
    zooms={p.name: L.sha(p) for p in sorted((ev / 'probe_zoom').glob('*.png'))},
    evidence_files=sorted(p.name for p in ev.iterdir()),
)
L.writej(ev / 'hashes.json', hashes)
print(json.dumps({k: v for k, v in hashes.items() if k not in ('scripts', 'work_scripts', 'tool_scripts', 'screenshots', 'zooms', 'evidence_files')},
                 ensure_ascii=False, indent=1))
assert unchanged, 'RUNTIME MOVED - discard this candidate and rebuild on the new base'
assert hashes['contracts_same_as_draft'], 'required_*.json list changed - rerun publish --contract'
assert j19['status'] == 'COMMITTED', 'r19 is no longer installed'
assert all(hashes['earlier_candidates_untouched'].values()), 'an earlier candidate folder changed'
