"""Live-only, reversible two-file calendar UI update; no user saves are written."""
from pathlib import Path
from types import SimpleNamespace
import sys,copy,shutil,datetime,hashlib
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/calendar_choices_20260929';E=R/'evidence/calendar_choices_20260929'
FILES=['NightRemaster.ain','winmm.dll'];NEW=R/'required_calendar_choices_20260929.json';HERE=Path(__file__).resolve().parent
STATUS='CALENDAR_CHOICES_20260929_INSTALLED_NATIVE_VISUAL_PASS'
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
    for p in [O/'source_pointer.json',O/'source_hashes.json',O/'verification.json',O/'candidate/manifest.json',O/'candidate/scan_report.json',O/'evidence/native_choices_probe.json',O/'evidence/save_frames.json',O/'evidence/transaction_verification.json',O/'design/cast_evidence.json',O/'design/cells.json',O/'design/label_patch.json',O/'evidence/label_review.json',O/'design/schedule.json',O/'design/groups.json',O/'work/build/helpers_readable.jaf']:
        shutil.copy2(p,E/'source'/p.name)
    for p in HERE.glob('*calendar_choices_20260929.*'):
        if p.suffix in ['.py','.jaf','.ps1']:shutil.copy2(p,E/'source'/p.name)
    for p in (O/'evidence/native_choices').glob('*.png'):shutil.copy2(p,E/'screenshots'/p.name)
    saves=P.snapshot_folder(L.SAVES);menu=P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None
    P.put(E/'save_hashes_before.json',P.js(saves))
    full=L.readj(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full['calendar_choices_20260929']=dict(evidence=str(E),semantic_dialogue_changes=0,summary_events=[11],translator_model='Codex internal')
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
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),schema_changes=0,mini_size=[32,40],detail_size=[104,130],changed_counts=man['changed_counts'],choice_label_sha256=man['choice_label_sha256'],translator_model='Codex internal',limitations=qa['limitations'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,calendar_choices_20260929_revision=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],calendar_choices=str(E/'source/manifest.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Calendar choice labels now show actual choices instead of numbered branches, with verified common joins. Unread new choice identities hidden; original gameplay and save code preserved.'
        write(mp,P.js(nm));mh=L.sha(mp)
        for p in contracts:
            co=L.readj(p)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for n,h in after.items():
                if n in co.get('required_files',{}):co['required_files'][n]=h
            co['calendar_choices_20260929_preserved_by']=str(E);write(p,P.js(co))
        write(NEW,P.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'added_functions':man['added_functions'],'forwarded':man['forwarded'],'portrait_assets':str(E/'source/cast_evidence.json'),'verification':qa,
            'instruction':'Preserve KR_R29* choice-label overrides and exact cloned fallback getters. Thirty-eight numbered branches use real choice labels; seven common joins include all alternatives. Do not infer selected person from first speaker. Preserve original choices, endings, unread masking, portrait sizes, summaries and prior replay/save guards.'}))
        hook=L.readj(R/'ui_hangul_input_fix.json');hook['files']['winmm.dll'].update(source=str(E/'candidate/winmm.dll'),sha256=after['winmm.dll'])
        hook['calendar_choices_revision']=rev;write(R/'ui_hangul_input_fix.json',P.js(hook))
        nc=copy.deepcopy(cur);nc.update(status=STATUS,manifest_sha256=mh,calendar_choices_20260929_revision=rev);write(L.CURRENT,P.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=L.sha(translation),calendar_choices_20260929_evidence=str(E));write(R/'latest_worked_translation.json',P.js(latest))
        note=f'\n\n### {now} 캘린더 선택지 이름 표기 설치 — Codex internal\n- 번호뿐인 갈래 표기 38개를 실제 선택 내용으로 교체. 7개 합류 장면은 선택 후 공통 장면으로 표기하고 특정 인물 전용으로 오인할 자동 이름 제거. 공통 합류는 모든 선택 연결 확인, 회상 참조의 원본 날짜/시간 보존.\n- 목록/제목은 간결한 선택명, 상세는 선택지 전문. 미열람은 새 선택 인물/행동을 숨기며 전체 개방도 열람으로 간주하지 않음. 선택 목록 12개/회상 목록 1개는 2열로 넓혀 표시.\n- 원래 시나리오/선택지/엔딩 조건/저장 구조/초상화/요약 수정 없음. 아직 특훈 우선 이벤트의 답 번호 14개는 이번 범위 밖.\n- 정적 독립 검수, native 무음 화면/열람·미열람 getter/915칸 및 변경 상세/선택 목록/취소·재생 가드, 저장 {qa["existing_resume_saves"]}개/복귀 주소 {qa["saved_return_frames"]}개 보존, Defender와 트랜잭션 검증 통과.\n- 설치 {rt}; 백업·검증 {E}; 복구 publish_calendar_choices_20260929.py --restore.\n'
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
    P.put(E/'README.md',('# 캘린더 선택지 표기\n\n번호 대신 실제 선택 내용을 표시합니다. 38개 분기와 7개 공통 합류를 대상으로 하며 회상 참조 원본 날짜/시간을 보존했습니다. 목록/제목은 짧게, 상세는 원래 선택지 전문. 새 선택 정보는 미열람 상태에서 숨깁니다. 원본 시나리오와 엔딩 조건은 변경하지 않았습니다.\n\n특훈 우선 이벤트의 답 번호 14개는 이번 범위 밖입니다. screenshots는 실제 무음 native 검증, before는 설치 전 백업, source는 변경표/소스/검수 기록입니다.\n').encode('utf8'))
    print(P.js(report).decode())
if __name__=='__main__':
    if '--restore' in sys.argv:P.restore_ctx(SimpleNamespace(root=R,evidence=E,pointer=L.CURRENT,stop_check=P.stopped))
    else:main('--check' in sys.argv)
