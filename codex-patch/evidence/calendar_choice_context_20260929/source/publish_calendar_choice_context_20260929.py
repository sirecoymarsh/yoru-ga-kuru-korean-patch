"""Live-only, reversible two-file calendar UI update; no user saves are written."""
from pathlib import Path
from types import SimpleNamespace
import sys,copy,shutil,datetime,hashlib
sys.dont_write_bytecode=True
F=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922/ingame/r24_chart')
sys.path.insert(0,str(F));import r24lib as L;import publish_chart_r24 as P
R=L.CODEX;O=R/'staging/calendar_choice_context_20260929';E=R/'evidence/calendar_choice_context_20260929'
FILES=['NightRemaster.ain','winmm.dll'];NEW=R/'required_calendar_choice_context_20260929.json';HERE=Path(__file__).resolve().parent
STATUS='CALENDAR_CHOICE_CONTEXT_20260929_INSTALLED_NATIVE_VISUAL_PASS'
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
    for p in [O/'source_pointer.json',O/'source_hashes.json',O/'verification.json',O/'candidate/manifest.json',O/'candidate/scan_report.json',O/'evidence/native_choices_probe.json',O/'evidence/save_frames.json',O/'evidence/transaction_verification.json',O/'design/cast_evidence.json',O/'design/cells.json',O/'design/label_patch.json',O/'evidence/label_review.json',O/'design/schedule.json',O/'design/groups.json',O/'work/build/helpers_readable.jaf',HERE/'calendar_detail_layout_20260929.jaf']:
        shutil.copy2(p,E/'source'/p.name)
    for p in HERE.glob('*calendar_choice_context_20260929.*'):
        if p.suffix in ['.py','.jaf','.ps1']:shutil.copy2(p,E/'source'/p.name)
    for p in (O/'evidence/native_choices').glob('*.png'):shutil.copy2(p,E/'screenshots'/p.name)
    saves=P.snapshot_folder(L.SAVES);menu=P.snapshot_folder(rt/'KRMenu') if (rt/'KRMenu').exists() else None
    P.put(E/'save_hashes_before.json',P.js(saves))
    full=L.readj(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain']
    full['calendar_choice_context_20260929']=dict(evidence=str(E),semantic_dialogue_changes=0,summary_events=[11],translator_model='Codex internal')
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
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,calendar_choice_context_20260929_revision=rev)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],calendar_choice_context=str(E/'source/manifest.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Twenty character choices now show source-backed situation, preceding prompt, and exact option in a separate detail choice field. Unread identities hidden; original gameplay and save code preserved.'
        write(mp,P.js(nm));mh=L.sha(mp)
        for p in contracts:
            co=L.readj(p)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for n,h in after.items():
                if n in co.get('required_files',{}):co['required_files'][n]=h
            co['calendar_choice_context_20260929_preserved_by']=str(E);write(p,P.js(co))
        write(NEW,P.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'added_functions':man['added_functions'],'forwarded':man['forwarded'],'portrait_assets':str(E/'source/cast_evidence.json'),'verification':qa,
            'instruction':'Preserve KR_S29* context display overrides and exact cloned fallbacks, including KR_S29Info dedicated choice field. Twenty character-selection branches distinguish photography, slideshow narration and cinema. Quote actual installed options, not invented character dialogue. Preserve all prior KR_R29 labels and common joins, original choices, endings, unread masking, portrait sizes, summaries and save guards.'}))
        hook=L.readj(R/'ui_hangul_input_fix.json');hook['files']['winmm.dll'].update(source=str(E/'candidate/winmm.dll'),sha256=after['winmm.dll'])
        hook['calendar_choice_context_revision']=rev;write(R/'ui_hangul_input_fix.json',P.js(hook))
        nc=copy.deepcopy(cur);nc.update(status=STATUS,manifest_sha256=mh,calendar_choice_context_20260929_revision=rev);write(L.CURRENT,P.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=L.sha(translation),calendar_choice_context_20260929_evidence=str(E));write(R/'latest_worked_translation.json',P.js(latest))
        note=f'\n\n### {now} 캘린더 선택 상황·실제 문구 표기 설치 — Codex internal\n- 인물 선택 20개: 함께 촬영할 사람 / 슬라이드 해설자 / 영화에 초대할 사람을 제목과 목록에서 구분. 상세 선택 칸에 앞선 질문·독백과 실제 선택지 문구 표시.\n- 원본 JP 및 현재 설치 한국어를 대조했고 미열람 선택 정보는 숨김. 이전 일반 선택 18개와 공통 합류 7개, 시나리오/선택지/엔딩/초상화/저장 구조 유지.\n- 독립 문맥 검수, native 무음 915칸 및 변경 상세/목록/취소·재생/열람·미열람 확인, 저장 {qa["existing_resume_saves"]}개와 복귀 주소 {qa["saved_return_frames"]}개 보존, Defender·설치/복구 검증 통과.\n- 설치 {rt}; 백업·검증 {E}; 복구 publish_calendar_choice_context_20260929.py --restore.\n'
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
    P.put(E/'README.md',('# 캘린더 선택 상황·문구\n\n촬영 상대, 슬라이드 해설자, 영화 동행자를 고르는 인물 선택 20개를 구분합니다. 상세 보드의 선택 칸에 앞선 질문/독백과 실제 게임 선택지 문구를 함께 표시합니다. 미열람 정보는 숨기며 원본 대사·선택지·엔딩 조건·저장은 변경하지 않았습니다.\n\nscreenshots: 실제 native 무음 검증 / before: 설치 전 백업 / source: 문맥 근거, 소스, 검수 기록.\n').encode('utf8'))
    print(P.js(report).decode())
if __name__=='__main__':
    if '--restore' in sys.argv:P.restore_ctx(SimpleNamespace(root=R,evidence=E,pointer=L.CURRENT,stop_check=P.stopped))
    else:main('--check' in sys.argv)
