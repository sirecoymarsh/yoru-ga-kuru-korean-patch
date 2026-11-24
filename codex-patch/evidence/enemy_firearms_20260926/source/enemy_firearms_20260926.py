"""Two EX display-name corrections; cumulative, reversible, and save-read-only."""
from pathlib import Path
import copy, datetime, hashlib, shutil, struct, subprocess, sys, zlib
import publish_event_navigation_20260926 as prior
from audit_dynamic_ui_20260915 import ex, decode, ENC
from build_item_skill_names_20260915 import replace_ex, ALICE
from audit_message_pixel_widths import parse_fnl_font, select_fnl_face, WidthMeasurer, sjis_bytes_to_fnl_index
from repair_ui_runtime_weapon_text_20260913 import unpack, strings
from audit_item_name_references_20260915 import messages
from build_afa3_cumulative_20260912 import read_afa3

p=prior.p; R=prior.R; HERE=Path(__file__).resolve().parent
O=R/'staging/enemy_firearms_20260926'; E=R/'evidence/enemy_firearms_20260926'
NAME='NightRemasterEX.ex'; FILES=[NAME]; NEW='required_enemy_firearms_20260926.json'
CONTRACTS=prior.CONTRACTS+[prior.NEW]
p.O=O; p.E=E; p.FILES=FILES
STATUS='ENEMY_FIREARMS_INSTALLED_STATIC_PASS'
EXPECTED='cb9362104b08e0c92cd33fab3ab2d2f779f3a21db294c4e3928697f031d620f0'
TARGETS={58:('ライトアームズ','경무장','경화기'),59:('ヘビーアームズ','중무장','중화기')}

def save(path,obj):p.put(path,p.js(obj))

def font_check(font):
    raw=font.read_bytes(); _,faces=parse_fnl_font(font,1); tables={}; pos=20
    for fontno in range(struct.unpack_from('<I',raw,16)[0]):
        nf=struct.unpack_from('<I',raw,pos)[0];pos+=4
        for face in range(nf):
            height,unknown,ng=struct.unpack_from('<III',raw,pos);pos+=12
            if fontno==1:tables[face]=[struct.unpack_from('<HII',raw,pos+10*i) for i in range(ng)]
            pos+=10*ng
    proxy={c:sjis_bytes_to_fnl_index(b) for c,b in ENC.items()};checks=[]
    for size in [20,24,30]:
        face,den,_=select_fnl_face(faces,size); measure=WidthMeasurer(face,den,proxy,0,0,0)
        for jp,old,new in TARGETS.values():
            for c in new:
                i=measure.glyph_index(c,True);w,offset,n=tables[face.face_index][i]
                assert w>0 and offset>0 and n>0 and any(zlib.decompress(raw[offset:offset+n]))
            width=measure.measure(new,True)['lines'][0]['width_px']
            assert width<=140
            checks.append(dict(text=new,size=size,width=width,budget=140,nonempty_glyphs=True))
    return dict(font_sha256=p.sha(font),checks=checks,native_screen_verified=False)

def build():
    assert not O.exists(), 'Use the existing frozen candidate; do not overwrite it.'
    ptr=p.read(R/'ui_cumulative/current.json');rt=Path(ptr['runtime']);mp=Path(ptr['manifest'])
    assert p.sha(mp)==ptr['manifest_sha256'] and p.sha(rt/NAME)==EXPECTED
    manifest=p.read(mp);original=Path(p.read(R/'project.json')['source'])/NAME
    sx=ex.decode_ex(original);cx=ex.decode_ex(rt/NAME)
    O.mkdir(parents=True);(O/'before').mkdir();shutil.copy2(rt/NAME,O/'before'/NAME)
    save(O/'source_pointer.json',ptr)
    edits=[]
    for mid,(jp,old,new) in TARGETS.items():
        path=('block',7,'value','child',mid-1,'leaf_value','item',2,'value')
        assert sx.strings[path].value.decode('cp932')==jp and decode(cx.strings[path].value)==old
        edits.append(dict(stable_id=f'EX:7:{mid}:name',path=list(path),source=jp,before=old,target=new,category='enemy_name'))
    # Re-read the exact latest data, never rebuild from the old enemy-name release.
    result=replace_ex(O/'before'/NAME,O/NAME,edits)
    proof=manifest['item_skill_name_revision'];oldmap=Path(proof['translation_map'])
    assert p.sha(oldmap)==proof['translation_map_sha256']
    tm=p.read(oldmap)
    for row in tm['rows']+tm['enemy_rows']:
        text=decode(cx.strings[tuple(row['string_paths']['name'])].value)
        if text!=row['target_name']:row['inherited_latest_name']=text
        row['current']['name']=text;row['target_name']=text;row['target_fields']={}
        if row['block']==7 and row['id'] in TARGETS:
            row['target_name']=TARGETS[row['id']][2];row['target_fields']={'name':row['target_name']}
            row['rationale']='총기 자체로 이루어진 적. 저격/기관총/유탄 공격 문맥에서 무장 상태가 아닌 경화기·중화기로 번역.'
            row['translator_model']='Codex internal'
    tm.update(source_pointer=ptr,source_EX_sha256=EXPECTED,translator_model='Codex internal',
              provenance='Codex internal /root; user-approved firearm enemy names, 2026-09-26. Other current display names inherited unchanged.')
    save(O/'translation_map.json',tm)
    save(O/'display_edits.json',dict(EX=edits,PACT=[],AIN=[],translator_model='Codex internal'))
    # Occurrence closure: inspect original source and current aliases, not global replacements.
    aliases=[x for triple in TARGETS.values() for x in triple[:2]]
    hits=[];counts={};allowed={tuple(e['path']) for e in edits}
    for lane,tree,decoder in [('original_EX',sx,lambda b:b.decode('cp932')),('current_EX',cx,decode)]:
        for path,node in tree.strings.items():
            if path not in allowed and any(t in decoder(node.value) for t in aliases):hits.append(dict(lane=lane,path=list(path)))
    for prefix,ain,decoder in [('original',original.parent/'NightRemaster.ain',lambda b:b.decode('cp932')),('current',rt/'NightRemaster.ain',decode)]:
        raw=unpack(ain.read_bytes())
        for lane,rows in [('STR0',strings(raw)[2]),('MSG1',messages(raw)[2])]:
            counts[prefix+'_'+lane]=len(rows)
            for i,row in enumerate(rows):
                if any(t in decoder(row) for t in aliases):hits.append(dict(lane=prefix+'_'+lane,id=i))
    pak=rt/'NightRemasterPact.afa';archive=read_afa3(pak);raw=pak.read_bytes();tmp=O/'reference_read.ex'
    for entry in archive.entries:
        tmp.write_bytes(raw[entry.absolute_offset:entry.absolute_offset+entry.size]);tree=ex.decode_ex(tmp)
        for path,node in tree.strings.items():
            if any(t in decode(node.value) for t in aliases):hits.append(dict(lane='PACT',index=entry.no,path=list(path)))
    tmp.unlink();counts['PACT']=len(archive.entries);assert not hits,hits
    consumer=subprocess.check_output([str(ALICE),'ain','dump','--function','C_Monster@LoadEX',str(rt/'NightRemaster.ain')]).decode('utf8')
    assert 'CALLFUNC EX_AString' in consumer and 'S_PUSH "モンスターデータ"' in consumer
    (O/'monster_load_consumer.jam').write_text(consumer,'utf8')
    save(O/'reference_audit.json',dict(counts=counts,external_hits=hits,consumer_sha256=p.sha(O/'monster_load_consumer.jam')))
    qa=dict(status='EXACT_TWO_DISPLAY_LEAVES_PASS',EX=result,edits=edits,font=font_check(rt/'NightRemasterFont.fnl'),
            files={NAME:p.sha(O/NAME)},AIN_sha256=p.sha(rt/'NightRemaster.ain'),PACT_sha256=p.sha(pak),
            no_code_or_save_schema_change=True,translator_model='Codex internal',native_screen_verified=False,
            translation_map_sha256=p.sha(O/'translation_map.json'),display_edits_sha256=p.sha(O/'display_edits.json'),
            semantic_review='Source names, firearm sprites, and attack text reviewed. User approved both exact target names. Only display leaves differ; all keys and numbers unchanged.')
    save(O/'verification.json',qa);p.fixture();print(p.js(qa).decode())

def install():
    current=p.read(R/'ui_cumulative/current.json');rt=Path(current['runtime']).resolve();mp=Path(current['manifest']);ptr=R/'ui_cumulative/current.json'
    if E.exists():
        j=p.read(E/'journal.json');assert j['status']=='COMMITTED' and p.sha(ptr)==j['committed_pointer_sha256']
        assert p.sha(rt/NAME)==j['after'][NAME];print('ALREADY_INSTALLED');return
    assert current==p.read(O/'source_pointer.json') and p.sha(mp)==current['manifest_sha256']
    if not p.stopped(rt):print('READY_WAITING_FOR_GAME_EXIT');return
    qa=p.read(O/'verification.json');assert qa['status']=='EXACT_TWO_DISPLAY_LEAVES_PASS'
    after=qa['files'];before={NAME:EXPECTED}
    assert p.sha(O/NAME)==after[NAME] and p.sha(rt/NAME)==before[NAME]
    assert p.sha(O/'translation_map.json')==qa['translation_map_sha256'] and p.sha(O/'display_edits.json')==qa['display_edits_sha256']
    for fname,status in [('scan_report.json','SCANNED_NO_TARGET_DETECTIONS'),('transaction_verification.json','TRANSACTION_FIXTURE_PASS')]:
        data=p.read(O/fname);assert data['status']==status and data.get('files',data.get('payload'))==after
    manifest=p.read(mp);p.exact_tree(rt,manifest['files']);saves=p.snapshot_saves()
    paths=[mp,ptr,R/'progress.md',R/'latest_worked_translation.json']+[R/n for n in CONTRACTS+[NEW]]
    snapshots={x:x.read_bytes() if x.exists() else None for x in paths};assert snapshots[R/NEW] is None
    for name in CONTRACTS:
        co=p.read(R/name)
        for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
            if key in co:assert co[key]==current['manifest_sha256'],name
    for folder in ['before','candidate','source']:(E/folder).mkdir(parents=True,exist_ok=True)
    metadata=[]
    for path,data in snapshots.items():
        if data is not None:p.put(E/'before'/path.name,data)
        metadata.append(dict(path=str(path),name=path.name,existed=data is not None,sha256=p.sha(path) if data is not None else None))
    shutil.copy2(rt/NAME,E/'before'/NAME);shutil.copy2(O/NAME,E/'candidate'/NAME)
    for name in ['translation_map.json','display_edits.json','verification.json','reference_audit.json','monster_load_consumer.jam','scan_report.json','transaction_verification.json']:
        shutil.copy2(O/name,E/'source'/name)
    shutil.copy2(__file__,E/'source'/Path(__file__).name)
    save(E/'save_hashes_before.json',saves)
    j=dict(status='PREPARED',runtime=str(rt),before=before,after=after,metadata=metadata);save(E/'journal.json',j)
    def write(path,data):
        assert path in snapshots;j.setdefault('metadata_after',{})[str(path)]=hashlib.sha256(data).hexdigest();save(E/'journal.json',j);p.put(path,data)
    attempted=False
    try:
        assert p.stopped(rt) and p.read(ptr)==current and p.sha(mp)==current['manifest_sha256']
        assert saves==p.snapshot_saves();attempted=True;p.pair_apply(E/'candidate',E/'before',rt,before,after)
        final=ex.decode_ex(rt/NAME)
        for edit in qa['edits']:assert decode(final.strings[tuple(edit['path'])].value)==edit['target']
        now=datetime.datetime.now().astimezone().isoformat()
        rev=dict(status=STATUS,time=now,files=after,source_files=before,evidence=str(E),changed_names=qa['edits'],
                 native_screen_verified=False,translator_model='Codex internal',no_code_or_save_changes=True)
        nm=copy.deepcopy(manifest);nm.update(status=STATUS,time=now,enemy_firearms_revision=rev)
        for row in nm['files']:
            if row['path']==NAME:row.update(sha256=after[NAME],size=(rt/NAME).stat().st_size)
        oldproof=nm['item_skill_name_revision'];nm.setdefault('item_skill_name_revision_history',[]).append(copy.deepcopy(oldproof))
        oldproof.update(translation_map=str(E/'source/translation_map.json'),translation_map_sha256=qa['translation_map_sha256'],
                        display_edits=str(E/'source/display_edits.json'),display_edits_sha256=qa['display_edits_sha256'],
                        latest_firearms_revision=rev,static_qa=str(E/'source/verification.json'),static_qa_sha256=p.sha(E/'source/verification.json'))
        nm['next']='Restart normally. Enemy IDs58/59 display 경화기/중화기. Exact data/font checks pass; battle-screen confirmation remains manual.'
        write(mp,p.js(nm));mh=p.sha(mp)
        for name in CONTRACTS:
            co=p.read(R/name)
            for key in ['manifest_sha256','reference_manifest_sha256','latest_manifest_sha256']:
                if key in co:co[key]=mh
            if NAME in co.get('required_files',{}):co['required_files'][NAME]=after[NAME]
            if name=='required_item_skill_names.json':
                for key in ['translation_map','translation_map_sha256','display_edits','display_edits_sha256']:co[key]=oldproof[key]
            co['enemy_firearms_preserved_by']=str(E);write(R/name,p.js(co))
        write(R/NEW,p.js({**rev,'manifest':str(mp),'manifest_sha256':mh,'required_files':after,
              'instruction':'Preserve numeric EX monster IDs58/59 and display names 경화기/중화기. Do not restore 경무장/중무장 from historical name catalogs.'}))
        nc=copy.deepcopy(current);nc.update(status=STATUS,manifest_sha256=mh,enemy_firearms_revision=rev);write(ptr,p.js(nc))
        latest=p.read(R/'latest_worked_translation.json');assert latest['manifest_sha256']==current['manifest_sha256']
        latest.update(manifest_sha256=mh,enemy_firearms_evidence=str(E),enemy_names_translation_map=oldproof['translation_map'],enemy_names_translation_map_sha256=oldproof['translation_map_sha256'])
        write(R/'latest_worked_translation.json',p.js(latest))
        note=f'\n\n### {now} 몬스터 이름 경화기·중화기 적용 — Codex internal\n- EX7 ID58/59 표시명만 경무장→경화기, 중무장→중화기 수정. 원문 ライトアームズ/ヘビーアームズ 및 총기 형태·저격/기관총/유탄 문맥 확인, 사용자 승인.\n- EX 정확히 2개 표시값 변경/역변환/구조/수치/원작 로더 검사, 실제 FNL 글리프와 폭, 외부 참조 검사 PASS. AIN·PACT·그 외 파일 및 세이브 불변. 전투 화면 실측은 미실시.\n- 백업/검증: {E}; EX {after[NAME]}; 복구: {HERE/Path(__file__).name} --restore\n'
        write(R/'progress.md',snapshots[R/'progress.md']+note.encode('utf8'))
        p.exact_tree(rt,nm['files']);assert saves==p.snapshot_saves()
        j.update(status='COMMITTED',manifest_sha256=mh,committed_pointer_sha256=p.sha(ptr));save(E/'journal.json',j)
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
        j.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK',error=repr(error),rollback_errors=failures);save(E/'journal.json',j);raise
    report=dict(status=STATUS,files=after,manifest_sha256=mh,unchanged_save_files=len(saves),evidence=str(E))
    save(E/'publish_report.json',report);print(p.js(report).decode())

if __name__=='__main__':
    if '--build' in sys.argv:build()
    elif '--install' in sys.argv:install()
    elif '--restore' in sys.argv:p.restore()
    else:raise SystemExit('Choose --build, --install, or --restore')
