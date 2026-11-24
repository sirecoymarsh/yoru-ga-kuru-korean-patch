"""One-file, hash-bound live install; preserves all gameplay CODE, other files and saves."""
from pathlib import Path
import copy,datetime,hashlib,shutil,sys
import publish_auto_walk_20260922 as previous
import publish_cheat_menu_20260915 as p
import integrate_claude_revision_20260923 as b
R=b.a.R;O=b.O;E=R/'evidence/claude_integration_20260923';HERE=Path(__file__).resolve().parent
CONTRACTS=previous.CONTRACTS+[previous.NEW];NEW='required_claude_revision_20260923.json'
STATUS='CLAUDE_REVISION_INSTALLED_STATIC_PASS_NATIVE_PENDING'
p.R=R;p.O=O;p.E=E;p.FILES=['NightRemaster.ain']

def main():
    ev=p.read(O/'build_evidence.json');before=ev['source_files'];after=ev['files']
    ptr=R/'ui_cumulative/current.json';current=p.read(ptr);mp=Path(current['manifest']);rt=Path(current['runtime']).resolve()
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert p.sha(rt/'NightRemaster.ain')==after['NightRemaster.ain'];print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'] and rt==p.RT.resolve() and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    for name,status in [('verification.json','MSG1_STRUCTURE_FONT_LAYOUT_PASS'),('independent_review.json','STATIC_REVIEW_PASS'),('scan_report.json','SCANNED_NO_TARGET_DETECTIONS'),('semantic_review.json','CHANGED_PROPOSALS_REVIEWED')]:
        q=p.read(O/name);assert q['status']==status and q['files']==after,name
    assert not p.read(O/'layout_failures.json') and not p.read(O/'unresolved_width.json')
    assert p.sha(O/'NightRemaster.ain')==after['NightRemaster.ain'] and p.sha(rt/'NightRemaster.ain')==before['NightRemaster.ain']
    old,os,oe,oldraw=b.a.raw_messages((rt/'NightRemaster.ain').read_bytes());new,ns,ne,newraw=b.a.raw_messages((O/'NightRemaster.ain').read_bytes())
    edits={int(i):v for i,v in p.read(O/'final_edits.json').items()}
    assert old[:os+12]==new[:ns+12] and old[oe:]==new[ne:] and len(oldraw)==len(newraw)==100944
    assert {i for i,(x,y) in enumerate(zip(oldraw,newraw)) if x!=y}==set(edits)
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);assert len(manifest['files'])==98
    fixture=p.fixture();saves=p.snapshot_saves();keep=p.read(R/'required_build_retention.json')
    rec=Path(keep['recovery_runtime']);rm=Path(keep['recovery_manifest']);rh=p.sha(rec/'NightRemaster.ain')
    assert p.sha(rm)==keep['recovery_manifest_sha256']
    latest=p.read(R/'latest_worked_translation.json');assert latest['ain_sha256']==before['NightRemaster.ain']
    assert latest['manifest_sha256']==current['manifest_sha256'] and p.sha(Path(latest['translation_map']))==latest['translation_map_sha256']
    full=p.read(Path(latest['translation_map']));proxy=p.read(b.a.PROXY);dec={x['proxy_character']:x['unicode_character'] for x in proxy['mapping']}
    decode=lambda bs:''.join(dec.get(c,c) for c in bs.decode('cp932'))
    baseline=[decode(x) for x in oldraw];targets=[decode(x) for x in newraw]
    existing={x['numeric_id']:x for x in full['entries']};assert all(x['target']==baseline[i] for i,x in existing.items())
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    assert len(paths)==len(set(x.name for x in paths)) and all(x.resolve().is_relative_to(R.resolve()) for x in paths)
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for n in CONTRACTS:
        c=p.read(R/n)
        for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if k in c:assert c[k]==current['manifest_sha256'],n
    E.mkdir(parents=True)
    for n in ['before','candidate','source']:(E/n).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    shutil.copy2(rt/'NightRemaster.ain',E/'before/NightRemaster.ain');shutil.copy2(O/'NightRemaster.ain',E/'candidate/NightRemaster.ain')
    for f in O.iterdir():
        if f.is_file() and f.suffix in ['.json','.jsonl','.png']:shutil.copy2(f,E/'source'/f.name)
    for n in ['integrate_claude_revision_20260923.py','verify_claude_integration_20260923.py','publish_claude_integration_20260923.py','review_claude_handoff_20260923.py','publish_cheat_menu_20260915.py','publish_remaster_multiplier_20260915.py']:
        shutil.copy2(HERE/n,E/'source'/n)
    # Preserve original Japanese/old provider history, add truthful correction lineage.
    jp=None;layout_ids={i for row in p.read(O/'layout_records.json') for i in row['ids']}
    for i in edits:
        if i not in existing:
            if jp is None:jp=[x.decode('cp932') for x in b.a.raw_messages((R/'translation_polish_20260917/input/jp.ain').read_bytes())[3]]
            existing[i]=dict(stable_id=f'NightRemaster.ain::m[{i}]',kind='message',numeric_id=i,source=jp[i],source_sha256=hashlib.sha256(jp[i].encode()).hexdigest(),translation_required=True)
            full['entries'].append(existing[i])
        row=existing[i];row['target']=targets[i];row['target_snapshot_provenance']='Exact installed MSG1; original provider fields are historical, correction lineage is separate'
        row['correction_provenance']=dict(input='User-supplied Claude/Fable/Opus corrections; exact external model IDs unrecorded',reviewer_model='Codex internal',translator_model='Codex internal' if i in b.OVERRIDES else 'external supplied correction and/or Codex prior name edit; see review candidate',evidence=str(E/'source/semantic_review.json'))
        if i in layout_ids:row['layout_provenance']='Codex native-page reflow; reviewed authored Korean unchanged except whitespace'
        if not targets[i]:row['empty_target_reason']='Trailing physical MSG field; content retained in same original MSG/R/A page'
        else:row.pop('empty_target_reason',None)
    full['entries'].sort(key=lambda x:x['numeric_id']);h=hashlib.sha256()
    for row in full['entries']:h.update(row['stable_id'].encode());h.update(b'\0');h.update(row['target'].encode());h.update(b'\0')
    full.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),entry_count=len(full['entries']),target_character_count=sum(len(x['target']) for x in full['entries']),target_text_sequence_sha256=h.hexdigest(),installed_ain_sha256=after['NightRemaster.ain'],current_revision=dict(operation='Claude handoff corrections reviewed and repaired; real-name policy; native-page layout',reviewer_model='Codex internal',external_translation_provenance_preserved=True,native_verified=False))
    fullpath=E/'source/installed_translation_map.json';p.put(fullpath,p.js(full));p.put(E/'save_hashes_before.json',p.js(saves))
    j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata,fixture=fixture);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256'];assert saves==p.snapshot_saves()
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),changed_fields=len(edits),outside_MSG1_exact=True,save_schema_changes=0,native_verified=False)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,claude_revision=rev,runtime_verified=False)
        nm['ain'].update(status=STATUS,candidate_sha256=after['NightRemaster.ain'],claude_revision_overlay=str(E/'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='Reviewed external correction batch and real names installed; new overflow91 resolved. Native dialogue/backlog check pending. All gameplay CODE and other97 runtime files unchanged.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for n in CONTRACTS:
            c=p.read(R/n)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in c:c[k]=mh
            if 'NightRemaster.ain' in c.get('required_files',{}):c['required_files']['NightRemaster.ain']=after['NightRemaster.ain']
            c['claude_revision_overlay']=str(E/'source/build_evidence.json');write(R/n,p.js(c))
        write(R/NEW,p.js(dict(rev,manifest=str(mp),manifest_sha256=mh,required_files=after,instruction='Preserve exact installed MSG1 correction snapshot. Original count and all non-MSG1 bytes unchanged, including latest auto-walk/auto-items/gameplay fixes. External provenance recorded; current batch reviewed, whole game not newly retranslated.')))
        latest.update(manifest_sha256=mh,ain_sha256=after['NightRemaster.ain'],translation_map=str(fullpath),translation_map_sha256=p.sha(fullpath),claude_revision_overlay=str(E/'source/build_evidence.json'));write(R/'latest_worked_translation.json',p.js(latest))
        write(ptr,p.js(dict(current,status=STATUS,manifest_sha256=mh,runtime_verified=False)))
        note=f'\n\n### {now} 클로드 교정 인계본 오류/줄배치 수정 후 최신 빌드 적용\n- 외부1,774행과 Codex 실명 정책의 결합후보1,777행 변경 QA 완료. 잘못된 화자 반말화·교사 오인장면·비꼬는 존대·조사/오타·지시어·분할문장 연결 오류 수정, 같은 장면 다른루트에도 적용.\n- 새 폭초과91행 해결: 네이티브 페이지74개 재배치와 원문 의미/확정용어를 유지한 짧은 문구. 최종 {len(edits)}필드 변경, MSG1 총100,944필드 및 MSG-R/A 체인·CODE 등 MSG1밖 바이트 정확히 보존.\n- 실제FNL 글리프/폭·AIN파싱·독립검토·Defender·설치복구fixture 통과. 게임화면 대사/백로그 재검증은 남음. 전체게임 신규 의미검수 완료를 뜻하지 않음.\n- 다른97개 runtime파일·세이브{len(saves)}개·기존 복구빌드 보존. 최신지도 {fullpath}; manifest {mh}; rollback {E}.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves();assert p.sha(rec/'NightRemaster.ain')==rh and p.sha(rm)==keep['recovery_manifest_sha256']
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
    report=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_other_runtime_files=97,unchanged_save_files=len(saves),recovery_unchanged=True,native_verified=False,evidence=str(E))
    p.put(E/'publish_report.json',p.js(report));p.put(O/'publish_report.json',p.js(report));print(p.js(report).decode('utf8'))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    else:main()
