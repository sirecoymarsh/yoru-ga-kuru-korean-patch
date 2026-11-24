"""Reversible in-place installation; originals, saves, old contracts and calendar pinned frames preserved."""
from pathlib import Path
import sys,copy,shutil,datetime,hashlib
import build_story_explore_20260927 as b
l=b.l;p=b.p;R=b.R;O=b.O;S=b.S;E=R/'evidence/story_explore_20260927';NEW='required_story_explore_20260927.json'
p.E=E;p.O=O;p.FILES=b.FILES
STATUS='STORY_EXPLORE_INSTALLED_NATIVE_PASS'
def main():
    ev=l.readj(O/'build_evidence.json');qa=l.readj(O/'verification.json');after=ev['files'];before={n:l.sha(S/n) for n in b.FILES}
    assert qa['status']=='STORY_EXPLORE_STATIC_NATIVE_PASS' and qa['files']==after
    for name,status in [('scan_report.json','SCANNED_NO_TARGET_DETECTIONS'),('transaction_verification.json','TRANSACTION_FIXTURE_PASS')]:
        report=l.readj(O/name);assert report['status']==status and report.get('files',report.get('payload'))==after
    assert all(l.sha(O/n)==h for n,h in after.items())
    current=l.readj(l.CURRENT);rt=Path(current['runtime']);mp=Path(current['manifest'])
    assert current==ev['source_pointer'] and l.sha(mp)==current['manifest_sha256']
    assert p.stopped(rt),'Game is still running; install withheld'
    assert not E.exists(),'Evidence directory already exists; inspect journal instead of overwriting'
    manifest=l.readj(mp);p.exact_tree(rt,manifest['files']);assert all(l.sha(rt/n)==h for n,h in before.items())
    contracts=sorted(R.glob('required_*.json'));paths=[mp,l.CURRENT,R/'progress.md',R/'latest_worked_translation.json',R/NEW]+contracts
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for folder in ['before','candidate','source','screenshots']:(E/folder).mkdir(parents=True)
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=l.sha(path) if data is not None else None))
    for n in b.FILES:shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
    for n in ['build_evidence.json','verification.json','patch.jam','helpers.jaf','native_opcode_audit.json','scan_report.json','transaction_verification.json','save_frames.json']:
        shutil.copy2(O/n,E/'source'/n)
    for n in ['build_story_explore_20260927.py','story_explore_20260927.jaf','probe_story_explore_20260927.py','verify_story_explore_20260927.py','publish_story_explore_20260927.py']:
        shutil.copy2(b.HERE/n,E/'source'/n)
    for mode,path in qa['native_probes'].items():
        root=Path(path).parent;shutil.copy2(path,E/'source'/('native_'+mode+'.json'))
        for img in root.glob('*.png'):shutil.copy2(img,E/'screenshots'/(mode+'_'+img.name))
    saves=p.snapshot_saves();p.put(E/'save_hashes_before.json',p.js(saves))
    latest=l.readj(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256'] and latest['ain_sha256']==before['NightRemaster.ain']
    assert l.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=l.readj(Path(latest['translation_map']));full['installed_ain_sha256']=after['NightRemaster.ain'];full['story_explore']={'evidence':str(E),'semantic_dialogue_changes':0,'translator_model':'Codex internal'}
    translation=E/'source/installed_translation_map.json';p.put(translation,p.js(full))
    j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and l.readj(l.CURRENT)==current and p.snapshot_saves()==saves
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),existing_saves_checked=qa['existing_resume_saves'],frames_checked=qa['saved_return_frames'],same_length_sites=ev['same_length_sites'],relocated=[],serialized_schema_changes=0,translator_model='Codex internal',native_contexts=list(qa['native_probes']),limitations=qa['limitations'])
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,story_explore_revision=rev);nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],story_explore=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Auto exploration: native story events and complete rest continue into replanning; native next-floor transitions preserve ownership. Choices remain manual. No story/party/reward/save-format changes.'
        write(mp,p.js(nm));mh=l.sha(mp)
        for path in contracts:
            co=l.readj(path)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            for n,h in after.items():
                if n in co.get('required_files',{}):co['required_files'][n]=h
            co['story_explore_preserved_by']=str(E)
            if 'claude_term_rate' in path.name:co['story_explore_scope']='Story/rest continuation extends existing talk/floor ownership. Original events and player choices remain authoritative.'
            write(path,p.js(co))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,'instruction':'Preserve KR_Story* event/rest/transition hooks. Original story handlers and rest recovery run to completion before replanning. Native choices stay manual. Session-only ownership; reset on load/new trip; do not alter serialized schema, rewards, or calendar pinned bodies. Assets are unchanged.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,story_explore_revision=rev);write(l.CURRENT,p.js(nc))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(translation),translation_map_sha256=l.sha(translation),story_explore_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 스토리 던전 자동 탐색·휴식 후 재개 — Codex internal\n- 기존 자동 탐색 상태를 스토리 이벤트·퍼즐 상자·휴식 지점에서도 보존. 원작 이벤트/휴식 완료 뒤 현재 좌표로 경로를 재계산. 이벤트 던전 다음 층 및 진입 대화에 연계. 선택지는 수동 유지.\n- 검증: {", ".join(qa["native_probes"])}. 범위/한계: {"; ".join(qa["limitations"])}.\n- 기존 함수 위치·스키마·메시지·문자열 접두 보존, 호출 {len(ev["same_length_sites"])}곳 동일 길이 교체. {qa["existing_resume_saves"]}개 저장/{qa["saved_return_frames"]}개 복귀 지점 구조 검사. 사용자 파일 {len(saves)}개 무변경. 달력·달성률·그래픽·보상 불변.\n- 증거 {E}; 다음 단계: 사용자 실제 연속 플레이 확인. 복구 publish_story_explore_20260927.py --restore.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves();j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=l.sha(l.CURRENT));p.put(E/'journal.json',p.js(j))
    except BaseException as error:
        failures=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as er:failures.append(repr(er))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:p.put(path,data)
                elif path.exists():path.unlink()
            except BaseException as er:failures.append(repr(er))
        j.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(error),rollback_errors=failures);p.put(E/'journal.json',p.js(j));raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,user_save_files_unchanged=len(saves),prior_contracts_preserved=len(contracts),runtime=str(rt),backup=str(E/'before'))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode())
if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
