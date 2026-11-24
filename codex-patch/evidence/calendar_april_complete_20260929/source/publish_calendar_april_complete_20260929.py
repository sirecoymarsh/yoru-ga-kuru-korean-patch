"""Hash-bound reversible installation of the completed April-only calendar."""
from pathlib import Path
from types import SimpleNamespace
import sys,copy,shutil,datetime,hashlib
sys.dont_write_bytecode=True
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/calendar_april_adaptive_minis_20260929';E=R/'evidence/calendar_april_complete_20260929'
FILES=['NightRemaster.ain','winmm.dll'];NEW=R/'required_calendar_april_complete_20260929.json';H=Path(__file__).resolve().parent
STATUS='CALENDAR_APRIL_COMPLETE_20260929_INSTALLED_NATIVE_PASS'

def main(check=False):
    qa=L.readj(O/'evidence/install_preflight.json');man=L.readj(O/'candidate/manifest.json')
    after={n:L.sha(O/'candidate'/n) for n in FILES}
    before={'NightRemaster.ain':man['live_sha256'],'winmm.dll':after['winmm.dll']}
    assert qa['status']=='APRIL_CUMULATIVE_INSTALL_PREFLIGHT_PASS' and qa['files']==after
    assert after=={n:man['files'][n]['sha256'] for n in FILES}
    for path,status in [(O/'candidate/scan_report.json','SCANNED_NO_TARGET_DETECTIONS'),(O/'evidence/transaction_verification.json','TRANSACTION_FIXTURE_PASS')]:
        v=L.readj(path);assert v['status']==status and v.get('payload',v.get('files'))==after
    cur=L.readj(L.CURRENT);assert cur==L.readj(O/'source_pointer.json'),'Live build moved since staging'
    rt=Path(cur['runtime']);mp=Path(cur['manifest']);assert P.stopped(rt),'Do not replace a running game'
    assert L.sha(mp)==cur['manifest_sha256'];manifest=L.readj(mp);P.exact_tree(rt,manifest['files'])
    assert all(L.sha(rt/n)==h for n,h in before.items())
    latest=L.readj(R/'latest_worked_translation.json')
    assert latest['manifest_sha256']==cur['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    if check:print('PREFLIGHT_PASS',after);return
    assert not E.exists() and not NEW.exists(),'Inspect existing installation journal'
    contracts=sorted(R.glob('required_*.json'))
    paths=[mp,L.CURRENT,R/'progress.md',R/'latest_worked_translation.json',NEW]+contracts
    assert len(paths)==len({x.name for x in paths})
    snapshots={p:p.read_bytes() if p.exists() else None for p in paths}
    for d in ['before','candidate','source','screenshots']:(E/d).mkdir(parents=True)
    metadata=[]
    for p,data in snapshots.items():
        if data is not None:P.put(E/'before'/p.name,data)
        metadata.append(dict(path=str(p),name=p.name,existed=data is not None,sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    for n in FILES:
        shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/'candidate'/n,E/'candidate'/n)
    for stage in ['calendar_april_readability_20260929','calendar_april_summary_20260929','calendar_april_adaptive_minis_20260929']:
        base=R/'staging'/stage;dest=E/'source'/stage;dest.mkdir()
        for name in ['verification.json','source_pointer.json','candidate/manifest.json','work/build/helpers_readable.jaf','evidence/native_april_probe.json']:
            shutil.copy2(base/name,dest/Path(name).name)
        L.writej(dest/'source_reference.json',dict(source=str(base/'source'),source_ain_sha256=L.sha(base/'source/NightRemaster.ain')))
    for path in [O/'candidate/scan_report.json',O/'evidence/install_preflight.json',O/'evidence/save_frames.json',O/'evidence/transaction_verification.json',
                 R/'staging/calendar_april_summary_20260929/design/summaries.json',R/'staging/calendar_april_summary_20260929/evidence/semantic_qa.json']:
        shutil.copy2(path,E/'source'/path.name)
    for stem in ['publish_calendar_april_complete_20260929.py','preflight_calendar_april_install_20260929.py','scan_calendar_april_install_20260929.ps1']:
        shutil.copy2(H/stem,E/'source'/stem)
    for path in (O/'evidence/native_april').glob('*.png'):shutil.copy2(path,E/'screenshots'/path.name)
    saves=P.snapshot_folder(L.SAVES);menu=P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None
    P.put(E/'save_hashes_before.json',P.js(saves))
    full=L.readj(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full['calendar_april_complete_20260929']=dict(evidence=str(E),semantic_dialogue_changes=0,summary_events=146,
        summary_source=str(E/'source/summaries.json'),summary_sha256=L.sha(E/'source/summaries.json'),translator_model='Codex internal')
    translation=E/'source/installed_translation_map.json';P.put(translation,P.js(full))
    journal=dict(status='PREPARED',runtime=str(rt),files=FILES,before=before,after=after,metadata=metadata)
    P.put(E/'journal.json',P.js(journal))
    def write(p,data):
        assert p in snapshots;journal.setdefault('metadata_after',{})[str(p)]=hashlib.sha256(data).hexdigest()
        P.put(E/'journal.json',P.js(journal));P.put(p,data)
    attempted=False
    try:
        assert P.stopped(rt) and L.readj(L.CURRENT)==cur and P.snapshot_folder(L.SAVES)==saves
        assert all((p.read_bytes() if p.exists() else None)==v for p,v in snapshots.items())
        attempted=True;P.pair_apply(E/'candidate',E/'before',rt,before,after,files=FILES)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),schema_changes=0,april_cells=143,
                 april_events=146,summary_events=146,mini_size=[32,40],mini_capacity=8,actual_april_max=5,detail_size=[104,130],
                 translator_model='Codex internal',other_months_unchanged=True,limitations=qa['limitations'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,calendar_april_complete_20260929_revision=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],calendar_april_complete=str(E/'source/install_preflight.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='April calendar complete: readable states, centered names, source-backed summaries and adaptive list portraits. Other months retain previous behavior.'
        write(mp,P.js(nm));mh=L.sha(mp)
        for p in contracts:
            co=L.readj(p)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for n,h in after.items():
                if n in co.get('required_files',{}):co['required_files'][n]=h
            co['calendar_april_complete_20260929_preserved_by']=str(E)
            if p.name.startswith('required_calendar_'):
                co['april_display_override']='For April only, preserve KR_U29/KR_AS29/KR_AM29: plain read-state wording, centered detail names, source-backed hidden-until-read summaries, adaptive 32x40 list minis instead of fixed three. Other months unchanged.'
            write(p,P.js(co))
        write(NEW,P.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'verification':qa,
            'instruction':'Preserve April-only routing. Lists retain protagonist, E IDs, dates, conditions, CGs and 32x40 portraits; show as many as fit after measuring text, with exact +N. Details keep 104x130 portraits, centered names and aligned fields. Read/access differ; unlock-all never reveals unread cast or summaries. All 146 source-bound summaries are Codex-authored; grouped E00004 summarizes only its first scene. Preserve original scenario messages, choices, saves and other months.'}))
        nc=copy.deepcopy(cur);nc.update(status=STATUS,manifest_sha256=mh,calendar_april_complete_20260929_revision=rev);write(L.CURRENT,P.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=L.sha(translation),calendar_april_complete_20260929_evidence=str(E));write(R/'latest_worked_translation.json',P.js(latest))
        note=f'\n\n### {now} 4월 이벤트 캘린더 완료본 설치\n- 143칸/146장면: 감상 상태·주인공·중앙 정렬 이름·기존 정보 유지, 줄거리 전체 작성, 미열람 숨김. 남는 폭에 따른 목록 초상 추가(실제 4~5명), 나머지 +N.\n- 기존 세이브 {qa["existing_resume_saves"]}개 / 복귀 주소 {qa["saved_return_frames"]}개 보존. 원본 CODE/STR prefix·MSG·직렬화 구조·DLL 보존. 무음 native·설치/복구·Defender 검사 통과.\n- 실제 실행 경로 {rt}; 백업 {E/"before"}; 복구 publish_calendar_april_complete_20260929.py --restore. 다른 달·게임 시나리오·세이브 내용은 미변경.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf-8'))
        P.exact_tree(rt,nm['files']);assert P.snapshot_folder(L.SAVES)==saves
        assert (P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None)==menu
        journal.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=L.sha(L.CURRENT));P.put(E/'journal.json',P.js(journal))
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
        journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(error),rollback_errors=failures)
        P.put(E/'journal.json',P.js(journal));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),user_save_files_unchanged=len(saves),backup=str(E/'before'),prior_contracts_preserved=len(contracts))
    P.put(E/'publish_report.json',P.js(report));P.put(O/'publish_report.json',P.js(report))
    P.put(E/'README.md',('# 4월 이벤트 캘린더 완료본\n\n4월 143칸/146장면의 상태 표기·포트레이트·요약을 실제 실행본에 반영했습니다. 다른 달과 원작 대사, 선택 결과, 저장 구조는 그대로입니다.\n\n- screenshots: 실제 게임 엔진 캡처\n- before: 설치 전 파일/메타데이터 백업\n- source: 원문 근거 요약, 검증, 설치/복구 도구\n- 기존 테스트 실행본의 세이브도 원위치에 보존하며 원래 세이브로 덮어쓰지 않았습니다.\n').encode('utf-8'))
    print(P.js(report).decode())

if __name__=='__main__':
    if '--restore' in sys.argv:P.restore_ctx(SimpleNamespace(root=R,evidence=E,pointer=L.CURRENT,stop_check=P.stopped))
    else:main('--check' in sys.argv)
