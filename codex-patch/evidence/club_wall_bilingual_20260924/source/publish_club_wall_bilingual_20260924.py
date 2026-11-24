"""CG-only, hash-bound installation over latest Claude R6; full external rollback journal."""
from pathlib import Path
import json, copy, shutil, datetime, sys, hashlib
import numpy as np
from PIL import Image
from build_club_wall_bilingual_20260924 import O,R,h,js,IDS
import publish_cheat_menu_20260915 as p

E=R/'evidence/club_wall_bilingual_20260924'
NEW='required_club_wall_bilingual_20260924.json'
STATUS='CLUB_WALL_BILINGUAL_INSTALLED_ENGINE_PASS'
p.O=O;p.E=E;p.FILES=['NightRemasterCG.afa']
def read(path):return json.loads(Path(path).read_text('utf8'))

def verify():
    ev=read(O/'build_evidence.json');native=read(O/'native_result.json');matches=read(O/'native_matches.json')
    assert native['candidate_files']==matches['files']==read(O/'determinism.json')['files']==ev['files']
    assert native.get('exit_code')==0 and not native['events'] and native['save_files_unchanged']
    assert not any(k in native for k in ['message','vm_error','timeout'])
    assert ev['changed_entries']==IDS and all(h(O/k)==v for k,v in ev['files'].items())
    for r in ev['records']:
        assert h(r['payload'])==r['payload_sha256']
        a=r['artifacts'];source=np.array(Image.open(a['source']));out=np.array(Image.open(O/f"{r['id']}_reopened.png"));clean=np.array(Image.open(a['clean']));mask=np.array(Image.open(a['protected']))>0
        assert source.shape==out.shape==clean.shape and list(out.shape[1::-1])==r['canvas']
        assert np.array_equal(source[mask],out[mask]) and r['roundtrip']=='PASS'
        if r['id'] in [485,981,1004]:
            y=r['split_y'];face=(source[:,:,:3].min(2)>235)&(source[:,:,3]>200);face[:y]=False
            assert np.array_equal(out[face],source[face]);assert r['english_near_face_pixel_identity']
        else:assert r['original_sha256']==r['installed_before_sha256']
    census=read(R/'evidence/ui_source_census.json')
    rows=[dict(id=r['id'],name=r['archive_name'],finding=r.get('review',{}).get('finding','')) for r in census['entries'] if r['id'] in [485,981,988,1004,1318,1319]]
    js(O/'scope_audit.json',dict(source_census_sha256=h(R/'evidence/ui_source_census.json'),reviewed_entries=len(census['entries']),rows=rows,
        paired_status_banners=[485,981,1004],unchanged_status_banner=dict(id=988,reason='全滅 has no English secondary line; keep existing 전멸.'),
        clubroom_scope='Wall placard only, day and night. Japanese book spines remain outside this request.',
        unchanged_scope='Command-button atlases and system menus are not paired encounter/status banners.'))
    # Source consumer evidence, preserving its exact original function context.
    jam=Path('P:/AI/Codex/projects/YoruGaKuru_KR_rebuild_20260830_layout_v3_final/build/dumps/NightRemaster_layout_v3.jam')
    f='';lines=[]
    for no,line in enumerate(jam.read_text('utf8').splitlines(),1):
        if line.startswith('FUNC '):f=line
        if line.strip() in ['S_PUSH "CG1541"','S_PUSH "CG1542"','S_PUSH "CG4013"','S_PUSH "CG4014"']:
            lines.append(dict(file=str(jam),line=no,function=f,command=line.strip()))
    js(O/'consumers.json',dict(jam_sha256=h(jam),references=lines,resting_pact='Game/Scenes/5000Dungeon/SceneDungeon.pactex: CG5070',current_gameplay_code_changes=0))
    report=dict(status='GRAPHICS_STATIC_DETERMINISTIC_ENGINE_PASS',files=ev['files'],changed_entries=IDS,entries=ev['entry_count'],
        protected_pixel_changes=0,all_english_faces_original=True,geometry_and_roundtrip='PASS',determinism='PASS',engine=matches,
        user_save_writes=0,ain_changes=0,pact_changes=0,translator_model='Codex internal',
        not_verified=['Full encounter animation timing and natural story scene playback; engine texture loader/rendering verified.'])
    js(O/'verification.json',report)
    # Registry entries point to stable individual manifests, rather than old full-Korean banners.
    for r in ev['records']:
        js(O/f"{r['id']}_manifest.json",dict(**r,status=report['status'],source_canvas=r['canvas'],runtime_verified=True,
            runtime_scope='Isolated engine CG renderer; not gameplay',source_glyph_erasure='VISUALLY_REVIEWED',
            state_family='day/night' if r['id']>=1318 else 'two-line status banner'))
    (O/'imagegen_prompt.txt').write_text('Codex-authored wording: 我は王なり → 나는 왕이다. Generate five vertically stacked Korean brush syllables 나 / 는 / 왕 / 이 / 다, dark charcoal #17252a, transparent background, no paper/frame/extra text; match the casual calligraphic astronomy-room sign. Built-in image_gen; frozen output retained as korean_brush_generated.png.\n','utf8')
    (O/'README.md').write_text('# 부실 족자·한영 안내 복원\n\n'
        '- 부실 낮/밤 족자: 我は王なり → 나는 왕이다. 배경·책등·인물은 변경하지 않음.\n'
        '- 선제 공격 / First Attack, 기습 공격 / Back Attack, 휴식 중 / resting. 아래 영어의 원본 글자 픽셀 보존.\n'
        '- 전멸은 원래 영어가 없어 기존 한국어 유지.\n'
        '- 최신 Claude R6에서 CG 5개만 교체. AIN·PACT·사용자 세이브 변경 없음.\n'
        '- 원본 크기/PCF 여백/QNT 헤더 보존, 인코딩 재열기 픽셀 일치, 재빌드 해시 일치. 무음 독립 엔진에서 다섯 CG 로드·렌더링 성공.\n'
        '- 전체 전투 연출/자연스러운 스토리 진행을 통한 확인은 별도.\n\n'
        '미리보기: bilingual_comparison.png, wall_comparison.png, native_final/*.png\n'
        '복구: publish_club_wall_bilingual_20260924.py --restore (후속 빌드가 설치되지 않은 상태에서만).\n','utf8')
    print('VERIFIED',ev['files'])

def install():
    ev=read(O/'build_evidence.json');qa=read(O/'verification.json');ptr=R/'ui_cumulative/current.json';current=read(ptr)
    assert qa['status']=='GRAPHICS_STATIC_DETERMINISTIC_ENGINE_PASS' and qa['files']==ev['files']
    if E.exists():
        j=read(E/'journal.json');assert j['status']=='COMMITTED' and h(ptr)==j['committed_pointer_sha256'];print('ALREADY_INSTALLED');return
    assert current==ev['source_pointer'],'Build baseline has moved; rebase instead of overwriting newer work'
    rt=Path(current['runtime']).resolve();mp=Path(current['manifest']);assert h(mp)==current['manifest_sha256']
    assert rt==p.RT.resolve()
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    manifest=read(mp);p.exact_tree(rt,manifest['files']);saves=p.snapshot_saves()
    assert all(h(rt/k)==v for k,v in ev['source_files'].items())
    before={n:ev['source_files'][n] for n in p.FILES};after=ev['files'];contracts=sorted(R.glob('required_*.json'))
    paths=[mp,ptr,R/'ui_integration_registry.json',R/'latest_worked_translation.json',R/'progress.md',R/NEW]+contracts
    assert len(paths)==len(set(paths));snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for path in contracts:
        doc=read(path)
        for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if k in doc:assert doc[k]==current['manifest_sha256'],path
    E.mkdir(parents=True)
    for name in ['before','candidate','source']:(E/name).mkdir()
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=h(path) if data is not None else None))
    for n in p.FILES:shutil.copy2(rt/n,E/'before'/n);shutil.copy2(O/n,E/'candidate'/n)
    for file in O.iterdir():
        if file.is_file() and file.suffix in ['.json','.txt','.md','.png','.payload']:shutil.copy2(file,E/'source'/file.name)
    for name in ['build_club_wall_bilingual_20260924.py','probe_club_wall_bilingual_20260924.py','publish_club_wall_bilingual_20260924.py']:
        shutil.copy2(Path(__file__).parent/name,E/'source'/name)
    p.put(E/'save_hashes_before.json',p.js(saves));j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata);p.put(E/'journal.json',p.js(j))
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();p.put(E/'journal.json',p.js(j));p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and read(ptr)==current and p.snapshot_saves()==saves
        attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        now=datetime.datetime.now().astimezone().isoformat();rev=dict(status=STATUS,time=now,files=after,evidence=str(E),changed_entries=IDS,
            unchanged_code=ev['unchanged_code'],save_writes=0,translator_model='Codex internal',engine_render_verified=True,gameplay_verified=False)
        reg=read(R/'ui_integration_registry.json');index={r['id']:r for r in reg['replacements']}
        for r in ev['records']:
            index[r['id']]=dict(id=r['id'],archive_name=r['archive_name'],provider='club_wall_bilingual_20260924',manifest=str(O/f"{r['id']}_manifest.json"),
                payload=r['payload'],payload_sha256=r['payload_sha256'],source_canvas=r['canvas'],static_pixel_validation='EXACT_RELEASE_RGBA',
                runtime_status='ENGINE_RENDER_PASS_GAMEPLAY_PENDING',release_ready=False)
        reg['replacements']=[index[k] for k in sorted(index)];reg['approved_replacement_count']=len(index);reg['club_wall_bilingual_revision']=rev
        write(R/'ui_integration_registry.json',p.js(reg))
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,club_wall_bilingual_revision=rev,ui_registry_sha256=h(R/'ui_integration_registry.json'))
        nm['merged_raster_ids']=sorted(set(nm['merged_raster_ids'])|set(IDS));nm['merged_raster_count']=len(nm['merged_raster_ids'])
        nm['cg']['candidate_sha256']=after['NightRemasterCG.afa'];nm['cg']['replaced_ids']=sorted(set(nm['cg']['replaced_ids'])|set(IDS));nm['cg']['club_wall_bilingual_overlay']=str(E)
        for row in nm['files']:
            if row['path'] in after:row.update(sha256=after[row['path']],size=(rt/row['path']).stat().st_size)
        nm['next']='User gameplay check: bilingual encounter/rest banners and Korean clubroom wall in day/night scenes.'
        write(mp,p.js(nm));mh=h(mp)
        for path in contracts:
            doc=read(path)
            for k in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if k in doc:doc[k]=mh
            if 'NightRemasterCG.afa' in doc.get('required_files',{}):doc['required_files']['NightRemasterCG.afa']=after['NightRemasterCG.afa']
            doc['club_wall_bilingual_preserved_by']=str(E);write(path,p.js(doc))
        write(R/NEW,p.js(dict(**rev,manifest=str(mp),manifest_sha256=mh,required_files={**ev['unchanged_code'],**after},
            instruction='Preserve five CG entries and their registered payloads. Japanese upper captions become Korean; original English faces remain below. Wall only in CG1541/CG1542. Do not reapply obsolete all-Korean banner payloads or overwrite newer Claude AIN/PACT.')))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,club_wall_bilingual_revision=rev);write(ptr,p.js(nc))
        latest=read(R/'latest_worked_translation.json');assert latest['ain_sha256']==ev['source_files']['NightRemaster.ain'];latest.update(manifest_sha256=mh,club_wall_bilingual_evidence=str(E));write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 부실 족자·한영 상태 안내 수정\n- CG 485/981/1004: 한국어 주 문구 + 원래 영어 First Attack / Back Attack / resting. 1318/1319 낮·밤 족자 我は王なり → 나는 왕이다.\n- 원본 2836개 엔트리 중 5개만 교체; AIN/PACT/세이브 그대로. 기하·보호 픽셀·재빌드·무음 네이티브 렌더링 검증 통과. 자연스러운 전투/스토리 재생은 사용자 확인 대상.\n- 빌드 {O}; 증거/복구 {E}; CG {after["NightRemasterCG.afa"]}; manifest {mh}.\n- Claude R6 검수 P2 달성률 표시 설정 저장 실패는 별도 미수정 상태: reviews/claude_term_rate_20260924_r6_codex/README.md.\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert p.snapshot_saves()==saves
        assert all(h(rt/k)==v for k,v in ev['unchanged_code'].items())
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=h(ptr));p.put(E/'journal.json',p.js(j))
    except BaseException as error:
        errors=[]
        if attempted:
            try:p.pair_restore(E/'before',rt,before,after)
            except BaseException as ex:errors.append(repr(ex))
        for path,data in reversed(list(snapshots.items())):
            try:
                if data is not None:p.put(path,data)
                elif path.exists():path.unlink()
            except BaseException as ex:errors.append(repr(ex))
        j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK',error=repr(error),rollback_errors=errors);p.put(E/'journal.json',p.js(j));raise
    result=dict(status=STATUS,files=after,manifest_sha256=mh,runtime=str(rt),unchanged_save_files=len(saves),unchanged_code=ev['unchanged_code'])
    js(O/'publish_report.json',result);js(E/'publish_report.json',result);js(O/'progress.json',dict(status=STATUS,completed_entries=IDS,next='User gameplay check; no remaining implementation for this graphics batch.'))
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    if '--restore' in sys.argv:p.restore()
    elif '--install' in sys.argv:install()
    else:verify()
