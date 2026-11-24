"""Hash-bound two-file live update; preserves saves and the recovery runtime."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_cheat_menu_20260915 as p
W=Path(__file__).resolve().parent;O=W/'loot_notice_20260915';R=p.R;E=R/'evidence/loot_notice_20260915';RT=p.RT
CONTRACTS=p.CONTRACTS+p.NEWCONTRACTS+['required_native_opcode_fix.json','required_route_cache_fix.json','required_route_map_refresh.json','required_department_route.json','required_mod_tab.json','required_instant_loot.json']
NEW='required_loot_notice.json';STATUS='LOOT_NOTICE_STATIC_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain','NightRemasterPact.afa']
INSTRUCTION='Instant-mode collision wrapper snapshots actual level/lifetimeEXP/training/moonpiece before and after unchanged native KR_TryInstantLoot and Settle. Never modify payout/levelup logic for this receipt. One native activity KR_LootNotice, appended PACT186 Asra/LootNotice, click-through white-on-navy native frame, native font259. Show per-character earned amounts and old-to-new level only after success. At most6lines,6000ms real-time,500ms fade. Repeated kills replace latest receipt and reset its timer. No per-frame text writes. Clear/unregister on expiry, dungeon Hide/destructor/map change, ConfigBegin. Missing UI must not alter payout success. No globals, structs, saves, raster files, prior Mods controls, translations or routes changed; original PACT0..185 exact. Native gameplay remains pending.'

def main():
 ev=p.read(O/'build_evidence.json');qa=p.read(O/'verification.json');after=ev['files'];before=ev['source_files']
 assert qa['status']==STATUS and qa['files']==after
 for filename,status in [('independent_review.json','STATIC_REVIEW_PASS'),('visual_review.json','STATIC_FONT_GEOMETRY_VISUAL_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
  x=p.read(O/filename);assert x['status']==status and x['files']==after
 assert all(p.sha(O/n)==after[n] for n in p.FILES)
 ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
 if E.exists():
  j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256'];assert all(p.sha(RT/n)==after[n] for n in p.FILES);print('ALREADY_INSTALLED');return
 assert current==ev['source_pointer'];mp=Path(current['manifest']);assert p.sha(mp)==current['manifest_sha256'];m=p.read(mp);rt=Path(current['runtime']).resolve();assert rt==RT.resolve()
 if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
 fx=p.fixture();p.exact_tree(rt,m['files']);assert all(p.sha(rt/n)==before[n] for n in p.FILES);assert p.sha(rt/'NightRemasterEX.ex')==ev['EX_unchanged_sha256']
 keep=p.read(R/'required_build_retention.json');rm=Path(keep['recovery_manifest']);rec=Path(keep['recovery_runtime']);assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
 saved=p.snapshot_saves();snapshots={x:x.read_bytes() if x.exists() else None for x in [mp,ptr,R/'progress.md']+[R/n for n in CONTRACTS+[NEW]]};assert snapshots[R/NEW] is None
 for n in CONTRACTS:
  c=p.read(R/n)
  for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
   if key in c:assert c[key]==current['manifest_sha256']
 E.mkdir(parents=True)
 for n in ['before','candidate','source']:(E/n).mkdir()
 metadata=[]
 for x,data in snapshots.items():
  if data is not None:p.put(E/'before'/x.name,data)
  metadata.append(dict(path=str(x),name=x.name,existed=data is not None,sha256=p.sha(x) if data is not None else None))
 for n in p.FILES:
  shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n);assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
 for f in O.iterdir():
  if f.is_file() and f.suffix in ['.json','.jam','.pactex','.png','.jaf'] and f.name!='native_raw_code.jam':shutil.copy2(f,E/'source'/f.name)
 for n in ['build_loot_notice_20260915.py','verify_loot_notice_20260915.py','publish_loot_notice_20260915.py','scan_loot_notice_20260915.ps1','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py','loot_notice_vm_20260915.py','audit_sys43_native_opcodes_20260915.py']:
  shutil.copy2(W/n,E/'source'/n)
 p.put(E/'save_hashes_before.json',p.js(saved));journal=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fx);p.put(E/'journal.json',p.js(journal))
 def write_meta(x,data):
  assert x in snapshots;journal.setdefault('metadata_after',{})[str(x)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(journal));p.put(x,data)
 attempted=False
 try:
  assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
  now=datetime.datetime.now().astimezone().isoformat();nm=copy.deepcopy(m)
  rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),previous_manifest_sha256=current['manifest_sha256'],AIN=ev['AIN'],PACT=ev['PACT'],native_gameplay_verified=False,save_schema_unchanged=True,translator_model='Codex internal')
  nm.update(status=STATUS,time=now,runtime_verified=False,loot_notice_revision=rev)
  nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],loot_notice_overlay=str(E/'source/build_evidence.json'),inherited_evidence_scope='Earlier reports describe frozen bytes. Current receipt overlay preserves all old CODE and original metadata except five function addresses and two owned switches;13 new helpers, no new serialized fields. Original instant payout code unchanged. Native gameplay remains pending.')
  for row in nm['files']:
   if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
  nm['next']='Enable 일반 적 즉시 처치 in Mods and touch an ordinary enemy: confirm actual reward amounts and level changes in a click-through receipt, disappearance after6seconds, repeated encounters reset notice, menus/maps clear it. Native game check pending.'
  write_meta(mp,p.js(nm));mh=p.sha(mp)
  for n in CONTRACTS:
   x=R/n;c=p.read(x)
   for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
    if key in c:c[key]=mh
   for file,h in after.items():
    if file in c.get('required_files',{}):c['required_files'][file]=h
   c['loot_notice_overlay']=str(E/'source/build_evidence.json')

   write_meta(x,p.js(c))
  write_meta(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction=INSTRUCTION)))
  write_meta(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
  note=f'\n\n### {now[:10]} Instant loot: transient reward receipt\n- Added optional-instant-kill receipt automatically when contact payout succeeds: per-party actual EXP/training/moonpiece differences and level old -> new; missing UI never alters success. Existing native Settle and instant encounter/payout/removal unchanged.\n- New PACT186 Asra/LootNotice native frame and Korean FNL259; white/cyan text on navy, no raster changes. Click-through, no wait loop. Latest encounter replaces receipt; real-time6000ms,500ms fade; no per-frame text allocation. Clear on expiry/dungeon Hide/destructor/map change/ConfigBegin. No serialized globals/fields or save edits.\n- Five existing function hooks +13 helpers; old CODE/STR0/MSG1 and all existing metadata except allowed addresses/switch450/451 preserved. Prior186PACT entries byte-identical. Static compiled EXP297/receipt120/failure7/rapidreplace300 fixtures, native opcodes, native-FNL glyph/width proof, independent review, Defender, transactional install/restore fixture passed. Native gameplay and real save/reload are NOT verified.\n- Installed {after};96other runtime files exact;{len(saved)}save hashes and recovery unchanged. Manifest {mh}; evidence/rollback {E}.\n- Next: user verifies in-game receipt and6-second expiration in current save. Prior localization scope still incomplete; no full-game completion claim.\n'
  write_meta(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'));p.exact_tree(rt,nm['files']);assert saved==p.snapshot_saves()
  assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={n:p.sha(rec/n) for n in p.FILES} and len(list((R/'ui_cumulative').glob('*/runtime')))==2
  journal.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(journal))
 except BaseException as err:
  failures=[]
  if attempted:
   try:p.pair_restore(E/'before',rt,before,after)
   except BaseException as x:failures.append(repr(x))
  for x,data in reversed(list(snapshots.items())):
   try:
    if data is not None:p.put(x,data)
    elif x.exists():x.unlink()
   except BaseException as e:failures.append(repr(e))
  journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(err),rollback_errors=failures);p.put(E/'journal.json',p.js(journal));raise
 report=dict(status=STATUS,runtime=str(rt),manifest_sha256=mh,files=after,unchanged_other_runtime_files=96,save_files_hashes_unchanged=len(saved),recovery_build_unchanged=True,native_gameplay_verified=False,evidence=str(E));p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))

if __name__=='__main__':
 if '--restore' in sys.argv:p.restore()
 elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
 else:main()
