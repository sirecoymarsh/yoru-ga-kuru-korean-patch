"""Live-only, reversible two-file calendar UI update; no user saves are written."""
from pathlib import Path
from types import SimpleNamespace
import sys,copy,shutil,datetime,hashlib
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/calendar_portraits_20260929';E=R/'evidence/calendar_portraits_20260929'
FILES=['NightRemaster.ain','winmm.dll'];NEW=R/'required_calendar_portraits_20260929.json';HERE=Path(__file__).resolve().parent
STATUS='CALENDAR_PORTRAITS_20260929_INSTALLED_NATIVE_VISUAL_PASS'
def main(check=False):
    qa=L.readj(O/'verification.json');man=L.readj(O/'candidate/manifest.json')
    after={n:L.sha(O/'candidate'/n) for n in FILES};before={n:L.sha(O/'source'/n) for n in FILES}
    assert qa['status']=='STATIC_NATIVE_VISUAL_PASS' and qa['files']==after
    assert after=={n:man['files'][n]['sha256'] for n in FILES}
    for path,status in [(O/'candidate/scan_report.json','SCANNED_NO_TARGET_DETECTIONS'),(O/'evidence/transaction_verification.json','TRANSACTION_FIXTURE_PASS')]:
        v=L.readj(path);assert v['status']==status and v.get('payload',v.get('files'))==after
    cur=L.readj(L.CURRENT);assert cur==L.readj(O/'source_pointer.json'),'Live build moved since staging'
    rt=Path(cur['runtime']);mp=Path(cur['manifest']);assert P.stopped(rt),'Game is running; staged only'
    assert L.sha(mp)==cur['manifest_sha256'];manifest=L.readj(mp);P.exact_tree(rt,manifest['files'])
    assert all(L.sha(rt/n)==h for n,h in before.items())
    latest=L.readj(R/'latest_worked_translation.json');assert latest['manifest_sha256']==cur['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    if check:print('PREFLIGHT_PASS',after);return
    assert not E.exists() and not NEW.exists(),'Inspect existing install journal rather than overwriting'
    contracts=sorted(R.glob('required_*.json'))
    paths=[mp,L.CURRENT,R/'progress.md',R/'latest_worked_translation.json',R/'ui_hangul_input_fix.json',NEW]+contracts
    assert len(paths)==len({x.name for x in paths})
    snapshots={p:p.read_bytes() if p.exists() else None for p in paths}
    for d in ['before','candidate','source','screenshots']:(E/d).mkdir(parents=True)
    metadata=[]
    for p,data in snapshots.items():
        if data is not None:P.put(E/'before'/p.name,data)
        metadata.append(dict(path=str(p),name=p.name,existed=data is not None,sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    for n in FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/'candidate'/n,E/'candidate'/n)
    for p in [O/'source_pointer.json',O/'source_hashes.json',O/'verification.json',O/'candidate/manifest.json',O/'candidate/scan_report.json',O/'evidence/native_portrait_probe.json',O/'evidence/save_frames.json',O/'evidence/transaction_verification.json',O/'design/cast_evidence.json',O/'design/cells.json']:
        shutil.copy2(p,E/'source'/p.name)
    for p in HERE.glob('*calendar_portraits_20260929.*'):
        if p.suffix in ['.py','.jaf','.ps1']:shutil.copy2(p,E/'source'/p.name)
    for p in (O/'evidence/native_portraits').glob('*.png'):shutil.copy2(p,E/'screenshots'/p.name)
    saves=P.snapshot_folder(L.SAVES);menu=P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None
    P.put(E/'save_hashes_before.json',P.js(saves))
    full=L.readj(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full['calendar_portraits_20260929']=dict(evidence=str(E),semantic_dialogue_changes=0,summary_events=[11],translator_model='Codex internal')
    translation=E/'source/installed_translation_map.json';P.put(translation,P.js(full))
    j=dict(status='PREPARED',runtime=str(rt),files=FILES,before=before,after=after,metadata=metadata)
    P.put(E/'journal.json',P.js(j))
    def write(p,data):
        assert p in snapshots;j.setdefault('metadata_after',{})[str(p)]=hashlib.sha256(data).hexdigest()
        P.put(E/'journal.json',P.js(j));P.put(p,data)
    attempted=False
    try:
        assert P.stopped(rt) and L.readj(L.CURRENT)==cur and P.snapshot_folder(L.SAVES)==saves
        assert all((p.read_bytes() if p.exists() else None)==v for p,v in snapshots.items())
        attempted=True;P.pair_apply(E/'candidate',E/'before',rt,before,after,files=FILES)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),schema_changes=0,mini_size=[32,40],detail_size=[104,130],translator_model='Codex internal',limitations=qa['limitations'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,calendar_portraits_20260929_revision=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],calendar_portraits=str(E/'source/manifest.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Calendar mini/detail portraits installed. Only E00011 summary authored; silent-only cast not inferred. Existing replay guards, saves and auto-exploration preserved.'
        write(mp,P.js(nm));mh=L.sha(mp)
        for p in contracts:
            co=L.readj(p)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for n,h in after.items():
                if n in co.get('required_files',{}):co['required_files'][n]=h
            co['calendar_portraits_20260929_preserved_by']=str(E);write(p,P.js(co))
        write(NEW,P.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'added_functions':man['added_functions'],'forwarded':man['forwarded'],'portrait_assets':str(E/'source/cast_evidence.json'),'verification':qa,
            'instruction':'Preserve KR_P29* list32x40/detail104x130 portraits and read-only cast gate, filename-based original CG loading, KR_C24* and KR_F28* replay guards. No serialized global or struct changes. Explicit speaker tags, not narrative mentions. Haiji CG0754. Unread names/count/summary hidden even unlock-all. Preserve new part cleanup and all older contracts.'}))
        hook=L.readj(R/'ui_hangul_input_fix.json');hook['files']['winmm.dll'].update(source=str(E/'candidate/winmm.dll'),sha256=after['winmm.dll'])
        hook['calendar_portraits_revision']=rev;write(R/'ui_hangul_input_fix.json',P.js(hook))
        nc=copy.deepcopy(cur);nc.update(status=STATUS,manifest_sha256=mh,calendar_portraits_20260929_revision=rev);write(L.CURRENT,P.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=L.sha(translation),calendar_portraits_20260929_evidence=str(E));write(R/'latest_worked_translation.json',P.js(latest))
        note=f'\n\n### {now} 이벤트 캘린더 포트레이트 설치 — Codex internal\n- 최신 사용자 정정 적용: 목록 칸 크기 유지 + 32×40 포트레이트 최대 3명/+N, 상세 보드는 승인한 104×130 크기로 전체 표시(최대 2행). 이전 상세판에만 표시한다는 계획은 폐기.\n- 미열람은 전체 개방 여부와 무관하게 초상화·인물명/수·요약 숨김. 하이지 원본 CG0754, 나머지 승인 원본 15명. 얼굴 별칭이 native CG 경로로 로드되지 않아 실제 아카이브 파일명을 사용; 이미지/아카이브 수정 없음.\n- 명칭 이벤트 캘린더, 첫 순서 E00001/E00002/E00121. 요약은 승인된 E00011 1건만; 무언 등장/익명 인물 추정 및 전체 줄거리 작성은 미완료.\n- 검증: 915칸 native 렌더, 16명 자산 픽셀/치수, 읽음/미열람(전체 개방)·취소·재생·단계·부품 해제, 원본 CODE/MSG 보존, 저장 {qa["existing_resume_saves"]}개/복귀 주소 {qa["saved_return_frames"]}개, 트랜잭션/Defender 통과. 무음 격리 사본만 사용; 사용자 저장 무변경.\n- 설치 {rt}; 백업/검증 {E}; 복구 publish_calendar_portraits_20260929.py --restore. 다음 단계: 실제 사용자 UI 확인, 필요시 나머지 이벤트 요약을 원문 기반으로 별도 작성.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        P.exact_tree(rt,nm['files']);assert P.snapshot_folder(L.SAVES)==saves
        assert (P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None)==menu
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=L.sha(L.CURRENT));P.put(E/'journal.json',P.js(j))
    except BaseException as error:
        failures=[]
        if attempted:
            try:P.pair_restore(E/'before',rt,before,after,files=FILES)
            except BaseException as er:failures.append(repr(er))
        for p,data in reversed(list(snapshots.items())):
            try:
                if data is not None:P.put(p,data)
                elif p.exists():assert p==NEW;p.unlink()
            except BaseException as er:failures.append(repr(er))
        j.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(error),rollback_errors=failures);P.put(E/'journal.json',P.js(j));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),user_save_files_unchanged=len(saves),backup=str(E/'before'),prior_contracts_preserved=len(contracts))
    P.put(E/'publish_report.json',P.js(report));P.put(O/'publish_report.json',P.js(report))
    P.put(E/'README.md',('# 이벤트 캘린더 포트레이트\n\n목록 32×40, 상세 104×130. 미열람 인물/줄거리 숨김. 원작 CG 16명, E00001/E00002 우선 정렬.\n\n줄거리는 승인된 E00011 1건만 작성했습니다. 인물은 명시된 화자 기준이며 무언 등장 인물은 추정하지 않았습니다.\n\n실행 검증 화면: screenshots. 복구 원본: before. 상세 검증: source/verification.json.\n').encode('utf8'))
    print(P.js(report).decode())
if __name__=='__main__':
    if '--restore' in sys.argv:P.restore_ctx(SimpleNamespace(root=R,evidence=E,pointer=L.CURRENT,stop_check=P.stopped))
    else:main('--check' in sys.argv)
