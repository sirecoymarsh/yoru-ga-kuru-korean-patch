"""r23: gather the evidence into 증거\\ and record the base hashes a final time (did Codex move the runtime meanwhile?).
If the runtime moved, the candidate is not installable (publish --verify says so) and the whole chain is rebuilt on the new base.
Keeps a copy of the design section r23 was built from (설계_v3 「r23 요구」; the design file is not touched). (after r22
work/finalize_evidence_r22.py; r23 writes no shared data file)"""
import sys, json, shutil, datetime, re
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import r23lib as L

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
    'gates.json': L.WORK / 'build' / 'gates.json',
    'scan_report.json': L.WORK / 'scan_report.json',
    'transaction_verification.json': L.WORK / 'transaction_verification.json',
    'savecopy_manifest.json': L.WORK / 'savecopy_manifest.json',
    'contract_draft_required_feeling_r23.json': HERE / 'required_feeling_r23.json',
    'explore_result_base.json': L.WORK / 'explore' / 'shots' / 'result.json',
    'explore_result_candidate.json': L.WORK / 'explore' / 'shots_candidate' / 'result.json',
}
for name, src in copies.items():
    if src.exists() and src.resolve() != (ev / name).resolve():
        shutil.copy2(src, ev / name)
design = L.FLOW / 'ingame' / '설계_v3_글메뉴판.md'
text = design.read_text('utf8')
z = re.search(r'^## r23 요구.*?(?=^## |\Z)', text, re.S | re.M)
assert z, 'design section 「r23 요구」 not found'
(ev / 'r23_요구_원문.md').write_text('<!-- 설계_v3_글메뉴판.md 의 「r23 요구」 절 사본 (sha256 %s, %s 에 읽음) -->\n\n' % (
    L.sha(design), datetime.datetime.now().astimezone().isoformat()) + z.group(0).rstrip() + '\n', 'utf8')
runtime_now = {n: L.sha(rt / n) for n in ['NightRemaster.ain', 'NightRemasterPact.afa', 'NightRemasterEX.ex', 'winmm.dll']}
chart_now = L.sha(rt / 'Manual' / 'chart' / 'yoru_flowchart_v2.html')
unchanged = (runtime_now == {'NightRemaster.ain': L.BASE_AIN_SHA, 'NightRemasterPact.afa': L.BASE_PACT_SHA, 'NightRemasterEX.ex': L.BASE_EX_SHA,
                             'winmm.dll': L.BASE_WINMM_SHA}
             and ptr['manifest_sha256'] == man['base']['manifest_sha256'] and ptr['status'] == man['base']['status']
             and chart_now == man['base']['chart_sha256'])
contracts = sorted(p.name for p in L.CODEX.glob('required_*.json'))
draft = L.readj(HERE / 'required_feeling_r23.json')
j22 = L.readj(L.R22_JOURNAL)
jh = L.readj(L.HOOK_JOURNAL)
R22_CAND = L.R22 / 'candidate' / 'NightRemaster.ain'
hashes = dict(
    checked=datetime.datetime.now().astimezone().isoformat(),
    base_at_start=dict(ain=L.BASE_AIN_SHA, pact=L.BASE_PACT_SHA, ex=L.BASE_EX_SHA, winmm=L.BASE_WINMM_SHA, manifest=man['base']['manifest_sha256'],
                       status=man['base']['status'], manual_chart=man['base']['chart_sha256']),
    runtime_at_end=dict(runtime_now, manifest=ptr['manifest_sha256'], status=ptr['status'], current_json_sha256=L.sha(L.CURRENT), manual_chart=chart_now),
    runtime_unchanged=unchanged,
    r22_install=dict(journal_status=j22['status'], ain=j22['after']['NightRemaster.ain'], required_chart_r22_present=(L.CODEX / 'required_chart_r22.json').exists()),
    hook_r2_install=dict(journal_status=jh['status'], winmm=jh['after']['winmm.dll']),
    contracts_at_end=len(contracts), contracts_same_as_draft=contracts == sorted(draft['preserves_contracts']),
    earlier_candidates_untouched=dict(
        r15=L.sha(L.R15 / 'candidate' / 'NightRemaster.ain') == L.R15_AIN_SHA,
        r16=L.sha(L.R16 / 'candidate' / 'NightRemaster.ain') == L.R16_AIN_SHA,
        r17=L.sha(L.R17 / 'candidate' / 'NightRemaster.ain') == L.R17_AIN_SHA,
        r18=L.sha(L.R18 / 'candidate' / 'NightRemaster.ain') == L.R18_AIN_SHA,
        r19=L.sha(L.R19 / 'candidate' / 'NightRemaster.ain') == L.R19_AIN_SHA,
        r20=L.sha(L.R20 / 'candidate' / 'NightRemaster.ain') == L.R20_AIN_SHA,
        r21=L.sha(L.R21 / 'candidate' / 'NightRemaster.ain') == L.R21_AIN_SHA,
        r22=L.sha(R22_CAND) == L.R22_AIN_SHA),
    candidate=dict(ain=L.sha(HERE / 'candidate' / 'NightRemaster.ain'), ain_size=(HERE / 'candidate' / 'NightRemaster.ain').stat().st_size,
                   manifest=L.sha(HERE / 'candidate' / 'manifest.json')),
    contract_draft=L.sha(HERE / 'required_feeling_r23.json'),
    shared_data_untouched=dict(event_cg=L.sha(L.FLOW / 'graph' / 'event_cg.json'), schedule=L.sha(L.FLOW / 'graph' / 'schedule.json'),
                               schedule_as_built=man['data']['schedule_sha256']),
    design_file_sha256=L.sha(design),
    scripts={p.name: L.sha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.suffix in ('.py', '.jaf', '.ps1', '.json', '.md')},
    work_scripts={p.name: L.sha(p) for p in sorted(L.WORK.iterdir()) if p.is_file() and p.suffix in ('.py', '.sh')},
    screenshots={p.name: L.sha(p) for p in sorted((ev / 'probe').glob('*.png'))} if (ev / 'probe').exists() else {},
    kind_screenshots={p.name: L.sha(p) for p in sorted((ev / 'probe_kinds').glob('*.png'))} if (ev / 'probe_kinds').exists() else {},
    zooms={p.name: L.sha(p) for p in sorted((ev / 'probe_zoom').glob('*.png'))} if (ev / 'probe_zoom').exists() else {},
    evidence_files=sorted(p.name for p in ev.iterdir()),
)
L.writej(ev / 'hashes.json', hashes)
print(json.dumps({k: v for k, v in hashes.items() if k not in ('scripts', 'work_scripts', 'screenshots', 'kind_screenshots', 'zooms', 'evidence_files')},
                 ensure_ascii=False, indent=1))
assert unchanged, 'RUNTIME MOVED - discard this candidate and rebuild on the new base'
assert hashes['contracts_same_as_draft'], 'required_*.json list changed - rerun publish --contract'
assert j22['status'] == 'COMMITTED' and jh['status'] == 'COMMITTED', 'r22 / the hook r2 is no longer installed'
assert all(hashes['earlier_candidates_untouched'].values()), 'an earlier candidate folder changed'
assert hashes['shared_data_untouched']['schedule'] == hashes['shared_data_untouched']['schedule_as_built'], 'graph/schedule.json moved since the build'
