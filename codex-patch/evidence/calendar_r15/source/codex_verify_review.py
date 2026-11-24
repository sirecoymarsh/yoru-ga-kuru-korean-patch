import sys, json, shutil, collections, pathlib
sys.dont_write_bytecode=True
D=pathlib.Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar')
R=pathlib.Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\reviews\calendar_r15_20260927_codex')
sys.path.insert(0,str(D))
import r15lib as L
import verify_calendar_r15 as v
import publish_calendar_r15 as p
W=R/'work'; (W/'build').mkdir(parents=True,exist_ok=True); (W/'base').mkdir(exist_ok=True)
source_work=L.WORK
L.WORK=W; v.W=W/'build'
for n in ['NightRemaster.ain','meta.json']:
 shutil.copy2(source_work/'base'/n,W/'base'/n)
# Regenerate metadata and raw disassembly from the actual candidate, not handed-off cache.
L.cmd('ain','dump','-j','-o',v.W/'candidate_meta.json',v.O/'NightRemaster.ain')
L.cmd('ain','dump','--no-macros','--raw-code','-o',v.W/'candidate_raw_code.jam',v.O/'NightRemaster.ain')
# Existing save snapshots must match live files before crediting compatibility.
saves={x.relative_to(L.SAVES).as_posix():L.sha(x) for x in L.SAVES.rglob('*') if x.is_file()}
L.writej(R/'save_hashes_before.json',saves)
for x in L.SAVECOPY.glob('NightR*.asd'):
 if x.name[6:-4].isdigit(): assert L.sha(x)==L.sha(L.SAVES/x.name),x.name
sys.argv=['verify_calendar_r15.py','--selftest']; v.main()
# Publisher fixture needs original verified handoff paths; result retained separately.
L.WORK=source_work
f=p.fixture(); L.writej(R/'transaction_fixture.json',f)
ok,report=p.readiness(); assert ok,report
L.writej(R/'readiness.json',report)
assert saves=={x.relative_to(L.SAVES).as_posix():L.sha(x) for x in L.SAVES.rglob('*') if x.is_file()}
print('CODEX_REVIEW_STATIC_VM_FIXTURE_PASS')
