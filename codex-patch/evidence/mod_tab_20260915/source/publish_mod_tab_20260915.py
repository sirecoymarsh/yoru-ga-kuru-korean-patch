"""Three-file latest-build transaction; no process kill or save writes."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_cheat_menu_20260915 as p

W=Path(__file__).resolve().parent;O=W/'mod_tab_20260915';R=p.R;E=R/'evidence/mod_tab_20260915';RT=p.RT
CONTRACTS=p.CONTRACTS+p.NEWCONTRACTS+['required_native_opcode_fix.json','required_route_cache_fix.json','required_route_map_refresh.json','required_department_route.json']
NEW='required_mod_tab.json';STATUS='MOD_TAB_STATIC_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex']
INSTRUCTION='Keep all eight added controls ONLY on the registered Mods page PACT185 (Asra/Mods, EX block23 appended row9), with native tab KR_ModTab below Remaster. Original Korean game settings123 and remaster125 retain their vanilla controls. Reward globals201..204 remain shared percentages; exact2x getters and unchanged-input no-op setters prevent passive 5x/20x loss. Explicit legacy checkbox toggles set1x/2x. Battle speed default follows original flag15/full-skip behavior; explicit2..5x overrides; quick is highest priority. Quick Run29387 presents the complete initial formation once before the action loop, with active recheck after update, then suppresses interim presentation until original results. Preserve saves, translations, fonts, opening, native opcode repairs and department route31860/cache/refresh.'

def main():
 ev=p.read(O/'build_evidence.json');qa=p.read(O/'verification.json');after=ev['files'];before=ev['source_files']
 assert qa['status']==STATUS and qa['files']==after
 for file,status in [('independent_review.json','STATIC_REVIEW_PASS'),('visual_review.json','STATIC_FONT_GEOMETRY_VISUAL_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
  r=p.read(O/file);assert r['status']==status and r['files']==after
 assert all(p.sha(O/n)==after[n] for n in p.FILES)
 ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
 if E.exists():
  j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256'];assert all(p.sha(RT/n)==after[n] for n in p.FILES);print('ALREADY_INSTALLED');return
 assert current==ev['source_pointer'];mp=Path(current['manifest']);assert p.sha(mp)==current['manifest_sha256'];m=p.read(mp);rt=Path(current['runtime']).resolve();assert rt==RT.resolve()
 if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
 fx=p.fixture();p.exact_tree(rt,m['files']);assert all(p.sha(rt/n)==before[n] for n in p.FILES)
 keep=p.read(R/'required_build_retention.json');rm=Path(keep['recovery_manifest']);rec=Path(keep['recovery_runtime']);assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
 saved=p.snapshot_saves();snapshots={path:path.read_bytes() if path.exists() else None for path in [mp,ptr,R/'progress.md']+[R/n for n in CONTRACTS+[NEW]]};assert snapshots[R/NEW] is None
 for n in CONTRACTS:
  c=p.read(R/n)
  for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
   if key in c:assert c[key]==current['manifest_sha256']
 E.mkdir(parents=True)
 for d in ['before','candidate','source']:(E/d).mkdir()
 metadata=[]
 for path,data in snapshots.items():
  if data is not None:p.put(E/'before'/path.name,data)
  metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
 for n in p.FILES:
  shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n);assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
 # Freeze reviewed source and proofs outside the live directory, not toolchain binaries.
 for f in O.iterdir():
  if f.is_file() and f.suffix in ['.json','.jam','.pactex','.png'] and f.name!='native_raw_code.jam':shutil.copy2(f,E/'source'/f.name)
 for n in ['build_mod_tab_20260915.py','verify_mod_tab_20260915.py','publish_mod_tab_20260915.py','scan_mod_tab_20260915.ps1','audit_sys43_native_opcodes_20260915.py','verify_cheat_menu_20260915.py','verify_remaster_multiplier_20260915.py','build_afa3_cumulative_20260912.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
  shutil.copy2(W/n,E/'source'/n)
 p.put(E/'save_hashes_before.json',p.js(saved));journal=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fx);p.put(E/'journal.json',p.js(journal))
 def meta_put(path,data):
  assert path in snapshots;journal.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(journal));p.put(path,data)
 attempted=False
 try:
  assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
  now=datetime.datetime.now().astimezone().isoformat();nm=copy.deepcopy(m)
  rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),previous_manifest=str(E/'before/manifest.json'),previous_manifest_sha256=current['manifest_sha256'],
   changed_functions=ev['AIN']['patched_functions'],PACT_entries=list(range(117,127)),appended_PACT_entry=185,EX_block=23,appended_EX_row=9,
   save_schema_unchanged=True,speed_precedence=ev['AIN']['speed_precedence'],reward_sync=ev['AIN']['reward_sync'],quick_preview=ev['AIN']['quick_preview'],native_gameplay_verified=False,translator_model='Codex internal')
  nm.update(status=STATUS,time=now,runtime_verified=False,mod_tab_revision=rev)
  nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],mod_tab_overlay=str(E/'source/build_evidence.json'),inherited_evidence_scope='Historical evidence remains bound to its frozen revision. This revision moves controls to native Mods page, restores original controls with synchronization guards and vanilla speed fallback, and adds initial-formation presentation for quick battle. All other function addresses, old CODE prefix, original STR0 prefix, MSG1, globals and structures exact.')
  nm['department_route']['user_confirmation']=dict(source_ain=before['NightRemaster.ain'],date=now[:10],result='User confirmed department route works; code retained unchanged in mod-tab revision')
  for row in nm['files']:
   if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
  nm['next']='Launch latest build. Verify native Mod tab navigation/selection; original Game settings and Remaster controls; preserved independent reward values; quick battle initial enemy formation then original results. No native UI or save/reload result claimed.'
  meta_put(mp,p.js(nm));mh=p.sha(mp)
  for n in CONTRACTS:
   path=R/n;c=p.read(path)
   for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
    if k in c:c[k]=mh
   for file,h in after.items():
    if file in c.get('required_files',{}):c['required_files'][file]=h
   c['mod_tab_overlay']=str(E/'source/build_evidence.json')
   if n in ['required_remaster_multiplier.json','required_cheat_menu.json']:
    c.setdefault('instruction_history',[]).append(dict(instruction=c.get('instruction'),superseded_by='User requested dedicated Mods tab and original config restoration',date=now));c['instruction']=INSTRUCTION
   meta_put(path,p.js(c))
  meta_put(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction=INSTRUCTION)))
  meta_put(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
  note=f'\n\n### {now[:10]} Dedicated Mods tab and initial quick-battle formation\n- User confirmed department-route fix532f works. Latest31860/cache/refresh bytecode preserved. New request moves all8 custom controls out of original pages; additional request shows initial enemy formation before hidden automatic calculations/results.\n- Native tab KR_ModTab below Remaster on all10 original PACT pages; appended page185 Asra/Mods, EX registry block23 row9. Korean pre-mod123/125 surfaces restored before tab addition. Original raster/font/particles/footer unchanged.\n- Four reward sliders share existing save globals201..204. Restored2x checkbox getters use equality200 and setters ignore unchanged inputs, so passive visits preserve5x/20x. Explicit toggle sets1x/2x. Default battle speed follows nativeflag15/full-skip; explicit2..5x and quick1000 override. Quick29387 presents once after complete enemy/gauge/control setup and before first action; active recheck prevents double presentation on cancellation.\n- AIN12functions repointed, no new functions/globals/structs; originalCODE/STR0prefix/MSG1 preserved. EX otherblocks/original9rows exact. PACT175unmodified entries exact. Compiled slider/sync/speed/preview fixtures, shippedFNL geometry/glyph proof, nativeopcodeaudit, independentreview, Defender and3-file transaction fixture passed. Native UI/presentation and actual save/reload remain pending.\n- Installed {after};95other runtimefiles exact,{len(saved)}save hashes unchanged,recovery unchanged. Manifest {mh}; evidence/backups {E}.\n- Next: user native verification in one launch, Mods navigation and oldoptions, 1/2/5/20 independentrates across pagevisits, then quick battle initialformation/results. Full localization review remains incomplete; no whole-game completion claim.\n'
  meta_put(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'));p.exact_tree(rt,nm['files']);assert saved==p.snapshot_saves()
  assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={n:p.sha(rec/n) for n in p.FILES} and len(list((R/'ui_cumulative').glob('*/runtime')))==2
  journal.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(journal))
 except BaseException as err:
  failures=[]
  if attempted:
   try:p.pair_restore(E/'before',rt,before,after)
   except BaseException as x:failures.append(repr(x))
  for path,data in reversed(list(snapshots.items())):
   try:
    if data is not None:p.put(path,data)
    elif path.exists():path.unlink()
   except BaseException as x:failures.append(repr(x))
  journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(err),rollback_errors=failures);p.put(E/'journal.json',p.js(journal));raise
 report=dict(status=STATUS,runtime=str(rt),manifest_sha256=mh,files=after,unchanged_other_runtime_files=95,save_files_hashes_unchanged=len(saved),recovery_build_unchanged=True,native_gameplay_verified=False,evidence=str(E));p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))

if __name__=='__main__':
 if '--restore' in sys.argv:p.restore()
 elif '--fixture' in sys.argv:print(p.js(p.fixture()).decode('utf8'))
 else:main()
