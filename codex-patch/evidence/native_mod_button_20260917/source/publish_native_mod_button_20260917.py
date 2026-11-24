"""Install only the reviewed notice and menu repair pair, preserving the newest translation provenance."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys,os
import publish_notice_repair_20260917 as previous
import publish_cheat_menu_20260915 as p
R=p.R;O=R/'staging/native_mod_button_20260917';E=R/'evidence/native_mod_button_20260917';HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_native_mod_button.json'
STATUS='NATIVE_MOD_BUTTON_INSTALLED_COMPILED_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemasterPact.afa','NightRemasterCG.afa']

def replace_restore_link(src,dest,expected):
    """Same-volume immutable restore without allocating a second CG archive."""
    src=Path(src).absolute();dest=Path(dest).absolute()
    assert src.name==dest.name and dest.name in p.FILES
    assert src!=dest and src.is_file() and dest.is_file()
    for path in (src,dest):
        assert path.resolve()==path
        for ancestor in (path,*path.parents):
            assert not getattr(ancestor.stat(),'st_file_attributes',0)&0x400
    assert src.stat().st_dev==dest.parent.stat().st_dev
    assert p.sha(src)==expected,('restore source mismatch',str(src))
    tmp=dest.with_name(dest.name+'.multiplier-copy.tmp')
    assert not tmp.exists() and not tmp.is_symlink()
    try:
        os.link(src,tmp)
        assert os.path.samefile(src,tmp) and p.sha(tmp)==expected
        os.replace(tmp,dest)
        assert p.sha(dest)==expected and p.sha(src)==expected
    finally:
        if tmp.exists():tmp.unlink()

def verify_low_space_restore():
    # Exercise the full actual-payload transaction matrix on disposable C data.
    # This never invokes restore against the user's runtime or metadata.
    saved=(p.O,p.replace_checked)
    fxroot=HERE/'native_mod_button_transaction_fixture_20260917'
    assert fxroot.is_dir() and all(p.sha(fxroot/n)==p.sha(O/n) for n in p.FILES)
    try:
        p.O=fxroot;p.replace_checked=replace_restore_link
        result=p.fixture()
    finally:p.O,p.replace_checked=saved
    result.update(status='LOW_SPACE_HARDLINK_RESTORE_FIXTURE_PASS',
        restore_archive_allocation_bytes=0,installed_runtime_modified=False,
        immutable_sources=True,files=p.read(O/'build_evidence.json')['files'])
    p.put(O/'low_space_restore_verification.json',p.js(result))
    p.put(E/'source/low_space_restore_verification.json',p.js(result))
    shutil.copy2(HERE/Path(__file__).name,E/'source'/Path(__file__).name)
    print(p.js(result).decode('utf8'))

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for filename,status in [('verification.json','NATIVE_MOD_BUTTON_COMPILED_PASS'),('independent_review.json','STATIC_REVIEW_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/filename);assert check['status']==status and check['files']==after
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    # P is nearly full. Run the exact-payload disposable transaction fixture on C.
    fxroot=HERE/'native_mod_button_transaction_fixture_20260917';fxroot.mkdir(exist_ok=False)
    for n in p.FILES:shutil.copy2(O/n,fxroot/n)
    p.O=fxroot
    try:fixture=p.fixture()
    finally:p.O=O
    shutil.copy2(fxroot/'transaction_verification.json',O/'transaction_verification.json')
    saves=p.snapshot_saves();keep=p.read(R/'required_build_retention.json');rec=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
    assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in p.FILES}
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths))
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for n in CONTRACTS:
        c=p.read(R/n)
        for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if k in c:assert c[k]==current['manifest_sha256'],n
    E.mkdir(parents=True)
    assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for folder in ['before','candidate','source','before/saves']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        # Same-volume immutable hardlinks survive replace_checked's atomic rename.
        # Neither rollback nor installation ever writes through these linked files.
        os.link(rt/n,E/'before'/n);os.link(O/n,E/'candidate'/n)
        assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
    for name,h in saves.items():
        dst=E/'before/saves'/name;dst.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p.SAVE/name,dst);assert p.sha(dst)==h
    assert saves==p.snapshot_saves()
    for f in O.iterdir():
        if f.is_file() and f.suffix in ['.json','.jam','.pactex','.jaf','.png'] and f.name!='raw.jam':shutil.copy2(f,E/'source'/f.name)
    for n in ['build_native_mod_button_20260917.py','publish_native_mod_button_20260917.py','scan_native_mod_button_20260917.ps1','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==ev['ain_unchanged_sha256']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=ev['ain_unchanged_sha256']
    full['native_mod_button_overlay']=dict(evidence=str(E),semantic_text_changes=0,MSG1_exact=True)
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),patched_existing=ev['patched_existing'],added_functions=ev['added_functions'],PACT=ev['PACT'],old_CODE_STR0_MSG1_exact=True,save_schema_changes=0,native_verified=False)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,native_mod_button_revision=rev,runtime_verified=False);nm['ain'].update(status=STATUS,candidate_sha256=ev['ain_unchanged_sha256'],native_mod_button_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Check mod buttons against native rest/item Normal/Hover/Down states and click area. Native retest of earlier notice/crash fixes still pending; AIN unchanged.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['native_mod_button_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
        write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Reuse original rest116x55 clean states1668-1671 with zero pixel edits and dynamic yellow text. Sweep size/position/scale match native adjacent controls,4 CG entries appended, no original CG changed. Only3 PACT button subtrees changed. AIN/rewards/progression/notice fixes unchanged. Native check pending.')))
        latest.update(manifest_sha256=mh,ain_sha256=ev['ain_unchanged_sha256'],translation_map=str(translation),translation_map_sha256=p.sha(translation),native_mod_button_overlay=str(E/'source/build_evidence.json'));write(R/'latest_worked_translation.json',p.js(latest))
        write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 사용자 지정 휴식·아이템 버튼 스타일로 재적용\n- 앞선 압축 전투프레임 대신 기존 휴식 버튼의 검증된 cleanplate1668–1671을 픽셀 수정 없이 재사용.4개QNT추가, 기존CG2820항목 전부 byte-exact. 원본발광·테두리·상태별색 그대로.\n- 소탕 원본캔버스116×55·scale1·x1142·y381(휴식/아이템 아래55간격), 노란 독립텍스트 중심. 자동장착/요소석도 같은 버튼계열, 기존폭·높이42 유지.\n- PACT153/154/161의 버튼 시각 구성만 변경. AIN3b7b... 및 방금 적용한 알림/소탕창복구·모든보상·진행·세이브스키마 불변.\n- QNT재디코딩 pixel차이0·보호영역차이0·모든원본CG보존·독립검토·Defender·설치복구fixture 통과. 실제게임 버튼·알림·소탕 재확인은 남음.\n- 다른96파일과 세이브{len(saves)}개/복구빌드 보존. Manifest {mh}; evidence/rollback {E}.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves();assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={n:p.sha(rec/n) for n in p.FILES}
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));p.put(E/'journal.json',p.js(j))
    except BaseException as error:
        errors=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as failure:errors.append(repr(failure))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:p.put(path,data)
                elif path.exists():path.unlink()
            except BaseException as failure:errors.append(repr(failure))
        j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);p.put(E/'journal.json',p.js(j));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=96,unchanged_save_files=len(saves),save_backup=str(E/'before/saves'),recovery_unchanged=True,native_verified=False,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--verify-low-space-restore' in sys.argv:verify_low_space_restore()
    elif '--restore' in sys.argv:
        p.replace_checked=replace_restore_link
        p.restore()
    else:main()
