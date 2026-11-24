"""Install player rename and read-only event counts on the exact latest translation."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_term_switch_20260923 as previous
import publish_cheat_menu_20260915 as p
R=p.R;O=R/'staging/player_tools_20260923';E=R/'evidence/player_tools_20260923';HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_player_tools_20260923.json'
STATUS='PLAYER_TOOLS_INSTALLED_COMPILED_PASS_NATIVE_PENDING'
p.O=O;p.E=E;p.FILES=['NightRemaster.ain','NightRemasterPact.afa']

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files'];ptr=R/'ui_cumulative/current.json';current=p.read(ptr)
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert all(p.sha(p.RT/n)==h for n,h in after.items());print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer']==p.read(O/'source_pointer.json')
    mp=Path(current['manifest']);rt=Path(current['runtime']).resolve();assert rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for filename,status in [('verification.json','PLAYER_TOOLS_COMPILED_PASS'),('visual_review.json','STATIC_FONT_GEOMETRY_PASS'),('independent_review.json','STATIC_REVIEW_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS')]:
        check=p.read(O/filename);assert check['status']==status and check['files']==after
    assert all(p.sha(O/n)==h for n,h in after.items()) and all(p.sha(rt/n)==h for n,h in before.items())
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    fixture=p.read(O/'transaction_verification.json');assert fixture['status']=='TRANSACTION_FIXTURE_PASS' and fixture['payload']==after
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
    for folder in ['before','candidate','source']:(E/folder).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
        assert p.sha(E/'before'/n)==before[n] and p.sha(E/'candidate'/n)==after[n]
    assert saves==p.snapshot_saves()
    for f in O.iterdir():
        if f.is_file() and f.suffix in ['.json','.jam','.pactex','.jaf','.png'] and f.name!='raw.jam':shutil.copy2(f,E/'source'/f.name)
    for n in ['build_player_tools_20260923.py','verify_player_tools_20260923.py','render_player_tools_proof_20260923.py','publish_player_tools_20260923.py','scan_player_tools_20260923.ps1','player_tools_helpers_20260923.jaf','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:shutil.copy2(HERE/n,E/'source'/n)
    latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));sequence=full['target_text_sequence_sha256'];full['installed_ain_sha256']=after['NightRemaster.ain']
    full['player_tools_overlay']=dict(evidence=str(E),semantic_dialogue_changes=0,MSG1_exact=True,UI_text_changes='Current protagonist rename and current-save event completion display')
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full));assert p.read(translation)['target_text_sequence_sha256']==sequence
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),patched_existing=ev['patched_existing'],added_functions=ev['added_functions'],PACT=ev['PACT'],old_CODE_STR0_MSG1_exact=True,save_schema_changes=0,native_verified=False)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,player_tools_revision=rev,runtime_verified=False);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],player_tools_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Native retest: Options > Mods > Player Info. Current-save event counts, name confirmation/cancel, native save/reload. Chart/event replay not included.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            for file,h in after.items():
                if file in c.get('required_files',{}):c['required_files'][file]=h
            c['player_tools_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
        write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Mods > Player Info. Rename uses original name setter and dialogue replacement only; persist through ordinary game save. Event display reads exact current-save registered event IDs; no progress/flag writes, all branches included. Original translation, terms, game balance and other mods preserved. Native interaction and persistence retest pending.')))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=p.sha(translation),player_tools_overlay=str(E/'source/build_evidence.json'));write(R/'latest_worked_translation.json',p.js(latest))
        write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 주인공 이름 변경 / 이벤트 경험률 표시 설치\n- 환경 설정 → 모드 → 플레이 정보. 현재 게임의 주인공 이름만 변경, 한글·영문·숫자 최대5글자. 확정 시 이름 setter/대사 치환/상태 표시만 갱신, 저장은 원작 저장 메뉴 사용. 취소·잘못된 이름·타이틀/회상/선택 중에는 적용하지 않음.\n- 대사가 있고 본편 진입 경로가 확인된1,043 이벤트를 현재 세이브의 고유 등록 키로 집계. 본편398·특훈대화362·특훈초대42·던전동행241. 모든분기 기준의 진입 기록으로 완독률·한회차 스토리 진행률 아님. 회상복사본·미사용·시스템·대사없는연결함수 제외.\n- 신규 이벤트 해금/진행도·능력치·난이도·달력 변경 없음. 페이지를 열 때만 계산, 프레임별 스캔 없음. 차트/이벤트재생 미포함. 최신번역 MSG1/STR0·기존CODE접두부·저장스키마 보존.\n- 컴파일 후보 검증·정적 독립 오라클·원작 버튼/실폰트 배치·Defender·설치복구fixture 통과. 실제 메뉴/IME·게임 저장 후 재실행 확인은 남음.\n- 다른96 runtime파일·세이브{len(saves)}개·복구빌드 해시 보존. Manifest {mh}; evidence/rollback {E}.\n'
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
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=96,unchanged_save_files=len(saves),save_preservation='hash-only: installer never writes saves',recovery_unchanged=True,native_verified=False,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
