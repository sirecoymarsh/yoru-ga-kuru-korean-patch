"""User cancelled the wall placard: restore only its two original payloads, keep bilingual banners."""
from pathlib import Path
import json,copy,hashlib,shutil,datetime
import publish_cheat_menu_20260915 as p
from build_remaster_multiplier_20260915 import rebuild,read_afa3
R=p.R;O=R/'staging/club_wall_cancel_20260924';E=R/'evidence/club_wall_cancel_20260924'
PREV=R/'evidence/club_wall_bilingual_20260924';B=R/'staging/club_wall_bilingual_20260924'
NEW='required_club_wall_cancel_20260924.json';STATUS='BILINGUAL_BANNERS_INSTALLED_CLUB_WALL_ORIGINAL'
def read(x):return json.loads(Path(x).read_text('utf8'))
def h(x):return p.sha(Path(x))
def put(x,d):p.put(x,p.js(d))

def main():
    O.mkdir(exist_ok=True);ptr=R/'ui_cumulative/current.json';cur=read(ptr);rt=Path(cur['runtime']).resolve();mp=Path(cur['manifest'])
    failed_attempt=None
    if E.exists():
        j=read(E/'journal.json')
        if j['status']=='COMMITTED':
            assert h(ptr)==j['committed_pointer_sha256'];print('ALREADY_RESTORED_WALL');return
        assert j['status']=='ROLLED_BACK' and not j.get('rollback_errors')
        for row in j['metadata']:
            path=Path(row['path'])
            assert (h(path)==row['sha256']) if row['existed'] else not path.exists()
        assert all(h(rt/n)==v for n,v in j['before'].items())
        failed_attempt=j
    old=read(PREV/'journal.json');assert old['status']=='COMMITTED' and h(ptr)==old['committed_pointer_sha256']
    assert h(mp)==cur['manifest_sha256'];m=read(mp);p.exact_tree(rt,m['files'])
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    p.FILES=['NightRemasterCG.afa'];p.O=O;p.E=E
    before={n:h(rt/n) for n in p.FILES};code={n:h(rt/n) for n in ['NightRemaster.ain','NightRemasterPact.afa']};saves=p.snapshot_saves()
    ev=read(B/'build_evidence.json');repl={}
    for n in [1318,1319]:
        src=B/f'{n}_installed_before.payload';record=next(r for r in ev['records'] if r['id']==n)
        assert h(src)==record['original_sha256']==record['installed_before_sha256'];repl[n]=src
    audit=rebuild(rt/'NightRemasterCG.afa',O/'NightRemasterCG.afa',repl)
    aa=read_afa3(rt/'NightRemasterCG.afa');bb=read_afa3(O/'NightRemasterCG.afa');a=(rt/'NightRemasterCG.afa').read_bytes();b=(O/'NightRemasterCG.afa').read_bytes();changes=[]
    assert len(aa.entries)==len(bb.entries)
    for x,y in zip(aa.entries,bb.entries):
        assert x.no==y.no and x.name==y.name
        left=a[x.absolute_offset:x.absolute_offset+x.size];right=b[y.absolute_offset:y.absolute_offset+y.size]
        if left!=right:changes.append(x.no)
        if x.no in repl:assert right==repl[x.no].read_bytes()
        if x.no in [485,981,1004]:assert left==right and hashlib.sha256(right).hexdigest()==next(r['payload_sha256'] for r in ev['records'] if r['id']==x.no)
    assert changes==[1318,1319];after={'NightRemasterCG.afa':h(O/'NightRemasterCG.afa')}
    put(O/'verification.json',dict(status='PASS',changed_entries=changes,restored_wall_original_exact=True,bilingual_banners_unchanged=True,code_unchanged=code,files=after,archive=audit))
    contracts=sorted(R.glob('required_*.json'));paths=[mp,ptr,R/'ui_integration_registry.json',R/'latest_worked_translation.json',R/'progress.md',R/NEW]+contracts
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for x in contracts:
        for k,v in read(x).items():
            if k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:assert v==cur['manifest_sha256']
    E.mkdir(parents=True,exist_ok=True)
    for name in ['before','candidate','source']:(E/name).mkdir(exist_ok=True)
    if failed_attempt:put(E/'source/previous_failed_journal.json',failed_attempt)
    metadata=[]
    for x,d in snapshots.items():
        if d is not None:p.put(E/'before'/x.name,d)
        metadata.append(dict(path=str(x),name=x.name,existed=d is not None,sha256=h(x) if d is not None else None))
    shutil.copy2(rt/'NightRemasterCG.afa',E/'before/NightRemasterCG.afa');shutil.copy2(O/'NightRemasterCG.afa',E/'candidate/NightRemasterCG.afa')
    shutil.copy2(__file__,E/'source'/Path(__file__).name);shutil.copy2(O/'verification.json',E/'source/verification.json')
    j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,prior_rolled_back_attempt=str(E/'source/previous_failed_journal.json') if failed_attempt else None);put(E/'journal.json',j);put(E/'save_hashes_before.json',saves)
    def write(x,d):
        assert x in snapshots;j.setdefault('metadata_after',{})[str(x)]=hashlib.sha256(d).hexdigest();put(E/'journal.json',j);p.put(x,d)
    attempted=False
    try:
        assert p.stopped(rt) and read(ptr)==cur and p.snapshot_saves()==saves
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        rev=dict(status=STATUS,time=datetime.datetime.now().astimezone().isoformat(),reason='User explicitly cancelled clubroom placard localization.',restored_entries=[1318,1319],retained_bilingual_entries=[485,981,1004],files=after,evidence=str(E),code_unchanged=code,save_writes=0)
        reg=read(R/'ui_integration_registry.json');previous_reg=read(PREV/'before/ui_integration_registry.json')
        rr={x['id']:x for x in reg['replacements']};pr={x['id']:x for x in previous_reg['replacements']}
        for n in [1318,1319]:
            if n in pr:rr[n]=pr[n]
            else:rr.pop(n,None)
        reg['replacements']=[rr[k] for k in sorted(rr)];reg['approved_replacement_count']=len(rr);reg['club_wall_cancel_revision']=rev;write(R/'ui_integration_registry.json',p.js(reg))
        nm=copy.deepcopy(m);previous_m=read(PREV/'before/manifest.json')
        nm.update(status=STATUS,club_wall_cancel_revision=rev,ui_registry_sha256=h(R/'ui_integration_registry.json'))
        for key in ['merged_raster_ids']:
            nm[key]=sorted((set(nm[key])-{1318,1319})|(set(previous_m[key])&{1318,1319}))
        nm['merged_raster_count']=len(nm['merged_raster_ids']);nm['cg']['candidate_sha256']=after['NightRemasterCG.afa']
        nm['cg']['replaced_ids']=sorted((set(nm['cg']['replaced_ids'])-{1318,1319})|(set(previous_m['cg']['replaced_ids'])&{1318,1319}))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User gameplay check of bilingual encounter/rest banners; clubroom placard deliberately original.'
        write(mp,p.js(nm));mh=h(mp)
        for x in contracts:
            doc=read(x)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in doc:doc[k]=mh
            if 'NightRemasterCG.afa' in doc.get('required_files',{}):doc['required_files']['NightRemasterCG.afa']=after['NightRemasterCG.afa']
            doc['club_wall_cancel_preserved_by']=str(E)
            if x.name=='required_club_wall_bilingual_20260924.json':
                doc['changed_entries']=[485,981,1004];doc['instruction']='Preserve Korean upper captions and original English lower captions in CG4014/CG4013/CG5070. User cancelled the wall placard: CG1541/CG1542 must remain original. Code and saves unchanged.'
            write(x,p.js(doc))
        write(R/NEW,p.js(dict(**rev,manifest=str(mp),manifest_sha256=mh,required_files={**after,**code},instruction='User cancelled the clubroom wall placard. Preserve its original two payloads; do not reinstall the generated Korean wall assets. Retain bilingual banner fixes.')))
        nc=copy.deepcopy(cur);nc.update(status=STATUS,manifest_sha256=mh,club_wall_cancel_revision=rev);write(ptr,p.js(nc))
        latest=read(R/'latest_worked_translation.json');latest.update(manifest_sha256=mh,club_wall_cancel_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {rev["time"]} 사용자 요청: 부실 족자 한국어화 취소\n- CG1541/CG1542(1318/1319)만 원본 payload로 정확히 복원. 한영 안내 485/981/1004는 그대로 유지. 코드 및 세이브 변경 없음.\n- 증거/복구 {E}; CG {after["NightRemasterCG.afa"]}; manifest {mh}. 생성된 한국어 족자를 다시 적용하지 말 것.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves() and all(h(rt/n)==v for n,v in code.items())
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=h(ptr));put(E/'journal.json',j)
    except BaseException as error:
        errors=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as ex:errors.append(repr(ex))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:p.put(path,data)
                elif path.exists():path.unlink()
            except BaseException as ex:errors.append(repr(ex))
        j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);put(E/'journal.json',j);raise
    result=dict(status=STATUS,files=after,restored_wall_entries=[1318,1319],retained_bilingual_entries=[485,981,1004],user_save_files_unchanged=len(saves),code_unchanged=code)
    put(O/'publish_report.json',result);put(E/'publish_report.json',result)
    (O/'README.md').write_text('# 부실 족자 취소 반영\n\n부실 낮·밤 족자는 원본으로 복원했습니다. 한영 안내 3종(선제 공격 / First Attack, 기습 공격 / Back Attack, 휴식 중 / resting)은 유지합니다. 코드와 세이브는 변경하지 않았습니다.\n','utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
