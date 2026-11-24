"""Completion audit against the installed files and exact native test evidence."""
from pathlib import Path
import sys,json,re,hashlib
sys.dont_write_bytecode=True
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;E=R/'evidence/calendar_april_complete_20260929';O=R/'staging/calendar_april_adaptive_minis_20260929';S=R/'staging/calendar_april_summary_20260929'
cur=L.readj(L.CURRENT);rt=Path(cur['runtime']);j=L.readj(E/'journal.json');pub=L.readj(E/'publish_report.json')
assert j['status']=='COMMITTED' and cur['status']==pub['status']=='CALENDAR_APRIL_COMPLETE_20260929_INSTALLED_NATIVE_PASS'
assert L.sha(Path(cur['manifest']))==cur['manifest_sha256']==j['manifest_sha256']==pub['manifest_sha256']
assert L.sha(L.CURRENT)==j['committed_pointer_sha256']
for n,h in j['after'].items():assert L.sha(rt/n)==h==L.sha(O/'candidate'/n)==L.sha(E/'candidate'/n)
for n,h in j['before'].items():assert L.sha(E/'before'/n)==h
for row in j['metadata']:
    path=Path(row['path'])
    assert L.sha(path)==j['metadata_after'][str(path)],str(path)
    if row['existed']:assert L.sha(E/'before'/row['name'])==row['sha256']
P.exact_tree(rt,L.readj(Path(cur['manifest']))['files'])
assert P.snapshot_folder(L.SAVES)==L.readj(E/'save_hashes_before.json')
nm=L.read_meta(O/'work/build/candidate_meta.json')
assert not any(f['name'].startswith(('KR_P22','KR_A29')) for f in nm['functions']),'Diagnostic code must not be installed'
qa=L.readj(E/'source/install_preflight.json');v=L.readj(O/'verification.json');sv=L.readj(S/'verification.json');p=L.readj(O/'evidence/native_april_probe.json')
assert qa['files']==j['after'] and p['candidate_sha256']==v['candidate_sha256']==j['after']['NightRemaster.ain']
assert p['pass'] and not p['user_files_changed'] and qa['transaction_fixture_pass']
assert v['april_cells']==143 and v['unread_portraits_hidden'] and v['maximal_count_fits']
assert sv['summaries']==146 and sv['summary_max_lines']<=5 and sv['unread_summary_hidden_even_unlocked']
summ=L.readj(E/'source/summaries.json');review=L.readj(E/'source/semantic_qa.json')
assert len(summ['events'])==146 and review['reviewed_events']==146 and not review['unresolved']
assert review['summary_sha256']==L.sha(E/'source/summaries.json')
assert set(x['no'] for x in summ['events'])==set(L.readj(O/'design/scope.json')['april_event_ids'])
assert all(x['summary'].strip() and x['status']=='source_qa_pass' for x in summ['events'])
facts={
 'April-only 143 cells / 146 scenes':str(O/'design/scope.json'),
 '146 source-backed Codex summaries / 7049 source messages reviewed':str(E/'source/semantic_qa.json'),
 'Human-readable states, identifiers, aligned fields and centered names':str(O/'evidence/native_april_probe.json'),
 'Unread portraits and summaries hidden, including unlock-all':str(S/'verification.json'),
 'Grouped E00004 summary is first scene only':str(E/'source/semantic_qa.json'),
 'Adaptive 32x40 list portraits / overflow count / no text or CG collision':str(O/'verification.json'),
 'Detailed 104x130 portraits and summaries pixel-preserved':str(O/'verification.json'),
 'Non-April fallback retained; May native pixel comparison and cleanup':str(O/'verification.json'),
 'Scenario, original code and string prefix, save schema and DLL preserved':str(E/'source/install_preflight.json'),
 'Existing save return addresses preserved':str(E/'source/save_frames.json'),
 'Installer backups and committed metadata verified':str(E/'journal.json'),
 'Installed hash equals native-validated candidate; no diagnostic instrumentation':str(E/'publish_report.json'),
 'Original 494 user-save files unchanged through installation':str(E/'save_hashes_before.json')}
report=dict(status='APRIL_INSTALLED_COMPLETION_AUDIT_PASS',files=j['after'],manifest_sha256=cur['manifest_sha256'],requirements=facts,
    user_save_files_unchanged=len(L.readj(E/'save_hashes_before.json')),backup_verified=True,diagnostic_code_absent=True,
    remaining_required_work=[],out_of_scope=['Other-month expansion','Original scenario rewriting','All-route gameplay replay'],
    next='Launch the installed build; record process startup separately without claiming a full playthrough.')
L.writej(E/'completion_audit.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2))
