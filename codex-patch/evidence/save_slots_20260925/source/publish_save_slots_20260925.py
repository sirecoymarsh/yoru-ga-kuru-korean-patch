"""Inactive-runtime, hash-bound installation; old saves are never overwritten."""
from pathlib import Path
import copy,datetime,hashlib,json,os,shutil,sys
import publish_claude_term_rate_20260924_r14 as previous
import build_save_slots_20260925 as build
p=build.p;R=build.R;O=build.O;HERE=build.HERE
E=R/'evidence/save_slots_20260925';NEW='required_save_slots_20260925.json'
CONTRACTS=previous.CONTRACTS+[previous.NEW]
FILES=['NightRemaster.ain','NightRemasterPact.afa'];p.O=O;p.E=E;p.FILES=FILES
STATUS='SAVE_CARDS_INSTALLED_NATIVE_PASS'

def migration_plan():
    # Only a proven day-start autosave can be copied from the former slot 49.
    # Manual 49 is always retained, even after migration.
    if any(p.SAVE.glob('NightR998.*')):return []
    if not all((p.SAVE/f'NightR49.{ext}').is_file() for ext in ['asd','vsf']):return []
    row=build.q.records(p.SAVE/'NightR49.asd');stack=[r.get('name','') for r in row['returns']]
    if not all(any(s.startswith(prefix) for s in stack) for prefix in ['呼出／１日の始まり(','■セーブ／オートセーブ実行(','C_SceneSaveLoad@RunAutoSave(']):return []
    return [dict(source=str(p.SAVE/f'NightR49.{ext}'),destination=str(p.SAVE/f'NightR998.{ext}'),sha256=p.sha(p.SAVE/f'NightR49.{ext}')) for ext in ['asd','vsf']]

def copy_weekly(plan,rt):
    created=[]
    assert p.stopped(rt)
    try:
        for row in plan:
            src=Path(row['source']);dst=Path(row['destination'])
            assert src.resolve().parent==dst.resolve().parent==p.SAVE.resolve()
            assert p.sha(src)==row['sha256'] and not dst.exists()
            with src.open('rb') as a,dst.open('xb') as b:
                created.append(dst);shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())
            shutil.copystat(src,dst);assert p.sha(dst)==row['sha256']
    except BaseException:
        # These paths were absent and created exclusively by this copy operation.
        for dst in created:
            assert dst.resolve().parent==p.SAVE.resolve();dst.unlink()
        raise

def main():
    ev=p.read(O/'build_evidence.json');after=ev['files'];before={n:p.sha(build.S/n) for n in FILES}
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for name,status in [('verification.json','SAVE_CARDS_STATIC_NATIVE_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/name);assert check['status']==status and check['files']==after
    fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
    qa=p.read(O/'verification.json');assert qa['save_schema_equal'] and qa['old_CODE_allowlist_exact']
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    saves=p.snapshot_saves();assert saves==p.read(O/'save_hashes_before_validation.json')
    migration=migration_plan()
    keep=p.read(R/'required_build_retention.json');rec=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest'])
    assert p.sha(rm)==keep['recovery_manifest_sha256'];rh={n:p.sha(rec/n) for n in FILES}
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths));snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for name in CONTRACTS:
        contract=p.read(R/name)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in contract:assert contract[key]==current['manifest_sha256'],name
    E.mkdir(parents=True);assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for folder in ['before','candidate','source','screenshots']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for name in FILES:shutil.copy2(rt/name,E/'before'/name);shutil.copy2(O/name,E/'candidate'/name)
    for path in O.iterdir():
        if path.is_file() and path.suffix in ['.json','.jaf','.pactex'] and path.name!='declared_meta.json':shutil.copy2(path,E/'source'/path.name)
    for name in ['build_save_slots_20260925.py','save_slots_20260925.jaf','probe_save_slots_20260925.py','verify_save_slots_20260925.py','publish_save_slots_20260925.py','scan_save_slots_20260925.ps1']:
        shutil.copy2(HERE/name,E/'source'/name)
    for save,path in qa['native_probes'].items():
        root=Path(path).parent
        shutil.copy2(path,E/'source'/('native_'+save+'.json'))
        for image in ['auto_probe_load_page0.png','auto_probe_load_page9.png','auto_probe_save_page0.png','auto_probe_resumed.png']:
            shutil.copy2(root/image,E/'screenshots'/(save.removesuffix('.asd')+'_'+image))
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['save_cards_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,translator_model='Codex internal')
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,weekly_migration=migration);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),native_render_verified=True,os_mouse_hit_test_verified=False,persistent_return_offsets_exact=True,MSG1_exact=True,save_schema_changes=0,existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],changed_PACT=[168],old_CODE_allowlist=ev['same_length_sites'],relocated=ev['relocated'],translator_model='Codex internal')
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,save_cards_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],save_cards_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User restart: new saves capture per-save metadata. Legacy saves retain known date/level and explicitly mark missing progress. Autosaves are 999/998; all manual slots 1..49 retained.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for name in CONTRACTS:
            contract=p.read(R/name)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in contract:contract[key]=mh
            for file,h in after.items():
                if file in contract.get('required_files',{}):contract['required_files'][file]=h
            contract['save_cards_preserved_by']=str(E)
            if name.startswith('required_claude_term_rate_20260924'):contract['autosave_slot49_rule_superseded_by']=str(R/NEW)
            write(R/name,p.js(contract))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':'Use independent daily999/weekly998, never overwrite manual1..49 automatically. Keep first-page six rows and 51 unique slots, native keyboard/click locks, KR_SAVE2 comment extension with 21-field legacy prefix, per-save event entry count rather than global achievements, protagonist label 주인공. Old saves with missing metadata must not show current-game values. This supersedes Claude R8-R14 slot49 autosave rules.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,save_cards_revision=rev);write(ptr,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),save_cards_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 저장 슬롯/진행 정보 개선 설치 — Codex internal\n- 일간999·주간998을 첫 페이지 위 두 칸으로 분리. 수동1–49 모두 유지. 월요일 주간 원본 저장 성공 뒤 일간으로도 복사. 저장 화면 자동 두 칸 잠금, 키보드 선택에서도 거부.\n- 저장 카드: 게임 날짜·위치·주인공/동료 레벨·이 저장의 이벤트 진입률(전체1043분기 포함)·실제 저장시각·플레이시간, 던전 남은시간. 원래 빈칸 그래픽을 재사용. 구형 저장 미기록 정보는 다시 저장해야 표시.\n- 원본 CSV21필드 뒤 KR_SAVE2 숫자 확장, 구조/전역/기존로컬 불변. {qa["existing_resume_saves"]}저장/{qa["saved_return_frames"]}복귀주소 검사PASS. 던전/월요일 사본으로 각각 저장·주간 재개, UI10페이지·51번호·클릭/키보드 잠금·원본 수동49보존 네이티브PASS. Defender/설치복구fixturePASS. OS 실제 마우스 적중 및 장시간 게임 진행은 별도 확인.\n- 검증된 기존 주간49의 두 파일만998에 비파괴 복사 예정({len(migration)}개). 기존49 및 그 외 원본 저장은 보존. 복구 시에도 새 저장 파일은 삭제하지 않음.\n- evidence {E}; AIN {after["NightRemaster.ain"]}; manifest {mh}; rollback publish_save_slots_20260925.py --restore. 기존 CT-RATE-004/장시간 자동탐색 종료 미해결 여부는 이번 수정 범위 밖.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves();assert p.sha(rm)==keep['recovery_manifest_sha256'] and rh=={n:p.sha(rec/n) for n in FILES}
        copy_weekly(migration,rt)
        expected=dict(saves);expected.update({Path(row['destination']).name:row['sha256'] for row in migration});assert expected==p.snapshot_saves()
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr),weekly_migration_completed=True);p.put(E/'journal.json',p.js(j))
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
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),existing_save_files_unchanged=len(saves),added_weekly_files=migration,unchanged_other_runtime_files=96,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report))
    readme=f'''# 저장 목록 개선\n\n- 첫 페이지: 일간 자동 저장 / 주간 자동 저장 / 수동 01–04. 수동 01–49는 유지됩니다.\n- 새 저장 정보: 날짜, 위치, 주인공과 동료 레벨, 이벤트 진입률, 저장 시각, 플레이 시간. 던전에서는 남은 탐색 시간도 표시합니다.\n- 이벤트 진입률은 해당 저장에서 진입한 이벤트 수 / 전체 분기 1043개이며, 메인 스토리 진행률이나 대사를 끝까지 읽은 비율은 아닙니다.\n- 기존 저장에는 없었던 위치·파티·진입률 정보가 미기록으로 나옵니다. 다시 저장하면 표시됩니다.\n- 기존 주간 저장은 검증 후 998번으로 복사했습니다. 기존 49번과 모든 원본 저장은 그대로 남겼습니다.\n- 실제 엔진 무음 테스트: 던전/월요일 각각 저장 및 새 주간 저장 재개, 전 페이지 51개 슬롯, 자동 슬롯 클릭·키보드 보호, 선택 테두리 표시 통과.\n- 기존 47개 저장/1173개 복귀 위치와 데이터 구조 호환성 검사 통과. 실제 OS 마우스 적중 검사는 하지 않았습니다.\n\n## 복구\n`{HERE / 'publish_save_slots_20260925.py'} --restore`\n\n제품 파일과 메타데이터를 설치 전으로 돌립니다. 사용자 저장 파일은 삭제하거나 덮어쓰지 않습니다.\n\n실행 경로: `{rt / 'NightRemaster.exe'}`\n'''
    p.put(E/'README.md',readme.encode('utf8'));print(p.js(report).decode('utf8'))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
