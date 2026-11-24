"""Stopped-game-only transaction for the shared character-label correction."""
from pathlib import Path
from types import SimpleNamespace
import sys,copy,shutil,datetime,hashlib
sys.dont_write_bytecode=True
F=Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/calendar_label_particles_20260929_r2';E=R/'evidence/calendar_label_particles_20260929'
FILES=['NightRemaster.ain','winmm.dll'];NEW=R/'required_calendar_label_particles_20260929.json';H=Path(__file__).resolve().parent
KEY='calendar_label_particles_20260929';STATUS='CALENDAR_LABEL_PARTICLES_20260929_INSTALLED_NATIVE_PASS'

def main(check=False):
    qa=L.readj(O/'evidence/install_preflight.json');man=L.readj(O/'candidate/manifest.json')
    after={n:L.sha(O/'candidate'/n) for n in FILES};before={'NightRemaster.ain':man['live_sha256'],'winmm.dll':after['winmm.dll']}
    assert qa['status']=='LABEL_PARTICLES_PREFLIGHT_PASS' and qa['files']==after
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
    assert not E.exists() and not NEW.exists(),'Inspect existing journal'
    contracts=sorted(R.glob('required_*.json'));paths=[mp,L.CURRENT,R/'progress.md',R/'latest_worked_translation.json',NEW]+contracts
    assert len(paths)==len({x.name for x in paths})
    snapshots={p:p.read_bytes() if p.exists() else None for p in paths}
    for d in ['before','candidate','source','screenshots']:(E/d).mkdir(parents=True)
    metadata=[]
    for p,data in snapshots.items():
        if data is not None:P.put(E/'before'/p.name,data)
        metadata.append(dict(path=str(p),name=p.name,existed=data is not None,sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    for n in FILES:shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/'candidate'/n,E/'candidate'/n)
    for rel in ['candidate/scan_report.json','candidate/manifest.json','evidence/install_preflight.json','evidence/save_frames.json',
                'evidence/transaction_verification.json','evidence/semantic_qa.json','evidence/native_labels_probe.json','design/label_patch.json','work/build/helpers_readable.jaf']:
        shutil.copy2(O/rel,E/'source'/Path(rel).name)
    for stem in ['build','probe','verify','publish']:shutil.copy2(H/(stem+'_calendar_label_particles_20260929.py'),E/'source'/(stem+'_calendar_label_particles_20260929.py'))
    for path in (O/'evidence/native_labels').glob('*.png'):shutil.copy2(path,E/'screenshots'/path.name)
    saves=P.snapshot_folder(L.SAVES);menu=P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None
    P.put(E/'save_hashes_before.json',P.js(saves))
    full=L.readj(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full[KEY]=dict(evidence=str(E),semantic_dialogue_changes=0,counts=man['counts'],map=str(E/'source/label_patch.json'),
                  map_sha256=L.sha(E/'source/label_patch.json'),translator_model='Codex internal')
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
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),schema_changes=0,
                 label_counts=man['counts'],translator_model='Codex internal',limitations=qa['limitations'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now);nm[KEY+'_revision']=rev
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain']);nm['ain'][KEY]=str(E/'source/install_preflight.json')
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Shared scene-label correction installed. Preserve prior April calendar, original scenario/saves, and meaningful phrases such as 이즈미와 촬영.'
        write(mp,P.js(nm));mh=L.sha(mp)
        for p in contracts:
            co=L.readj(p)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for n,h in after.items():
                if n in co.get('required_files',{}):co['required_files'][n]=h
            co[KEY+'_preserved_by']=str(E);write(p,P.js(co))
        write(NEW,P.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'verification':qa,
            'instruction':'Preserve KR_N29 exact-ID+old-text label overrides in KR_T19EvShort/EvHead/CardHead/CardTail. Remove only dangling 와 after the seven audited character names; retain 호시카와 itself, numbering, branch choices, unread fallbacks, action phrases, scenario text, and save layout.'}))
        nc=copy.deepcopy(cur);nc.update(status=STATUS,manifest_sha256=mh);nc[KEY+'_revision']=rev;write(L.CURRENT,P.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=L.sha(translation));latest[KEY+'_evidence']=str(E);write(R/'latest_worked_translation.json',P.js(latest))
        note=f'\n\n### {now} 달성률·캘린더 공통 장면명 조사 수정\n- 단독 인물명 뒤 와 제거: {sum(man["counts"].values())}개 표시 필드. 이즈미/쿄카/마나미/마코토/호시카와/신카이/모모세. 촬영·동행 등 의미가 이어지는 문구와 기존 선택 분기는 유지.\n- 2,638개 getter 항목 × 읽음/미열람 검증, 캘린더·달성률 양쪽 장면 선택창 무음 native 확인. 원본 CODE/STR prefix·MSG·직렬화 구조·DLL·세이브 보존.\n- 설치 {rt}; 백업 {E/"before"}; 복구 publish_calendar_label_particles_20260929.py --restore.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
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
        journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(error),rollback_errors=failures);P.put(E/'journal.json',P.js(journal));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),user_save_files_unchanged=len(saves),backup=str(E/'before'),prior_contracts_preserved=len(contracts))
    P.put(E/'publish_report.json',P.js(report));P.put(O/'publish_report.json',P.js(report))
    P.put(E/'README.md',('# 장면명 조사 수정\n\n달성률·캘린더의 공통 제목/장면 선택 목록에서 단독 인물명 뒤의 불필요한 조사를 제거했습니다. E번호, 감상 상태, 촬영·동행 등 문장, 기존 시나리오와 세이브는 유지합니다.\n\n- screenshots: 실제 엔진 수정 화면\n- before: 설치 전 백업\n- source: 정확한 수정표·검증·설치/복구 도구\n').encode('utf8'))
    print(P.js(report).decode())

if __name__=='__main__':
    if '--restore' in sys.argv:P.restore_ctx(SimpleNamespace(root=R,evidence=E,pointer=L.CURRENT,stop_check=P.stopped))
    else:main('--check' in sys.argv)
