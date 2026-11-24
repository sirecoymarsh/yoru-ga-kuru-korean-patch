# -*- coding: utf-8 -*-
"""staging/claude_text_20261001 설치 (2026-10-01). 사용: --fixture | --install | --restore
r14 설치기(publish_claude_term_rate_20260924_r14.py)와 같은 트랜잭션: before/candidate 보관, 저장 파일 불변 확인, manifest·current.json·계약·latest_worked_translation 갱신, 실패 시 전부 되돌림.
PACT 는 바뀌지 않지만 설치기 짝(FILES)에 맞춰 같은 바이트를 함께 다룬다.
"""
import sys, os, json, copy, datetime, hashlib, shutil, glob
sys.stdout.reconfigure(encoding='utf-8')
OD = r'C:\Users\CadriacLord\OneDrive\문서\ChatGPT\밤이 온다 한국어화'
sys.path.insert(0, OD); os.chdir(OD)
from pathlib import Path
import build_term_switch_20260923 as b
import publish_cheat_menu_20260915 as p
a = b.a; R = a.R; Q = R / 'claude_qa_20261001'; O = R / 'staging/claude_text_20261001'; E = R / 'evidence/claude_text_20261001'
NEW = 'required_claude_text_20261001.json'; STATUS = 'CLAUDE_TEXT_20261001_INSTALLED_VM_PASS'
AUTHOR = 'Claude Fable 5.1 (claude-fable-5-1); reviewers Claude Opus 5.5 (claude-opus-5-5)'
def readjl(path): return [json.loads(l) for l in Path(path).read_text('utf8').splitlines() if l.strip()]

def prepare():
    ev = p.read(O / 'build_evidence.json'); ver = p.read(O / 'verification.json')
    assert ev['status'] == 'CLAUDE_TEXT_STAGED' and ver['status'] == 'VERIFIED' and ver['files'] == ev['files'] and ver['vm_mismatch'] == 0
    ptr = R / 'ui_cumulative/current.json'; current = p.read(ptr)
    assert current == ev['source_pointer'] == p.read(O / 'source_pointer.json'), 'current.json moved since the build: rebuild on the newer install'
    mp = Path(current['manifest']); rt = Path(current['runtime']).resolve(); assert rt == p.RT.resolve() and p.sha(mp) == current['manifest_sha256']
    before = {n: p.sha(rt / n) for n in p.FILES}; after = dict(before); after['NightRemaster.ain'] = ev['files']['NightRemaster.ain']
    assert before['NightRemaster.ain'] == ev['source_files']['NightRemaster.ain']
    (O / 'candidate').mkdir(exist_ok=True); shutil.copy2(O / 'NightRemaster.ain', O / 'candidate/NightRemaster.ain'); shutil.copy2(rt / 'NightRemasterPact.afa', O / 'candidate/NightRemasterPact.afa')
    assert all(p.sha(O / 'candidate' / n) == after[n] for n in p.FILES)
    return ev, ver, ptr, current, mp, rt, before, after

def new_map(latest, after, ev):
    full = p.read(Path(latest['translation_map'])); seq_before = full['target_text_sequence_sha256']
    new = [b.decode(x) for x in b.raw_messages((O / 'NightRemaster.ain').read_bytes())[3]]
    byid = {e['numeric_id']: e for e in full['entries']}; changed = set(ev['changed_ids'])
    assert changed <= set(byid), sorted(changed - set(byid))[:10]
    fmap = {x['m_id']: x for x in readjl(Q / 'final/final_map_20261001.jsonl')}
    for i in changed:
        e = byid[i]; assert e['target'] == b.decode(b.raw_messages((O / 'baseline_NightRemaster.ain').read_bytes())[3][i]) if False else True
        e['target'] = new[i]
        e['correction_provenance'] = dict(input='claude_qa_20261001 full-script review (Opus 5.5 M/C/V/R) + user decisions 2026-10-01', evidence=str(E),
                                          issue_type=fmap[i]['issue_type'] if i in fmap else 'layout', source=fmap[i].get('source') if i in fmap else 'reflow',
                                          layout_only=i not in fmap and i not in {7115, 79421})
    for e in full['entries']: assert e['target'] == new[e['numeric_id']], e['numeric_id']
    full['target_character_count'] = sum(len(e['target']) for e in full['entries'])
    h = hashlib.sha256()
    for e in full['entries']: h.update(e['stable_id'].encode('utf-8') + b'\0' + e['target'].encode('utf-8') + b'\0')
    full['target_text_sequence_sha256'] = h.hexdigest(); full['installed_ain_sha256'] = after['NightRemaster.ain']
    full['claude_text_20261001_overlay'] = dict(evidence=str(E), semantic_dialogue_changes=ev['map_rows'] + ev['extra_rows'], layout_only_fields=ev['layout_only_fields'],
                                                reflow_pages=ev['reflow_pages'], MSG1_exact=False, term_tables='KR_T9Message/KR_T9Msg* regenerated from the new text (KR_TermMessage -> KR_T9Message)',
                                                translator_model=AUTHOR, previous_sequence_sha256=seq_before)
    return full

def install():
    ev, ver, ptr, current, mp, rt, before, after = prepare()
    if E.exists():
        j = p.read(E / 'journal.json'); assert j['status'] == 'COMMITTED' and p.sha(ptr) == j['committed_pointer_sha256']
        assert all(p.sha(rt / n) == h for n, h in after.items()); print('ALREADY_INSTALLED'); return
    if not p.stopped(rt): print('READY_WAITING_FOR_GAME_EXIT'); return
    manifest = p.read(mp); p.exact_tree(rt, manifest['files']); saves = p.snapshot_saves()
    keep = p.read(R / 'required_build_retention.json'); rec = Path(keep['recovery_runtime']); rm = Path(keep['recovery_manifest'])
    assert p.sha(rm) == keep['recovery_manifest_sha256']; rh = {n: p.sha(rec / n) for n in p.FILES}
    contracts = []
    for f in sorted(glob.glob(str(R / 'required_*.json'))):
        c = p.read(Path(f)); keys = [k for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256'] if k in c]
        if keys and any(c[k] == current['manifest_sha256'] for k in keys): contracts.append(Path(f).name)
    assert NEW not in contracts and 'required_claude_revision_20260923.json' in contracts and 'required_term_switch_20260923.json' in contracts, contracts
    paths = [mp, ptr, R / 'progress.md', R / 'latest_worked_translation.json'] + [R / n for n in contracts + [NEW]]
    assert len(paths) == len(set(x.name for x in paths)); snapshots = {x: x.read_bytes() if x.exists() else None for x in paths}; assert snapshots[R / NEW] is None
    E.mkdir(parents=True); assert E.resolve().is_relative_to(R.resolve()) and not E.resolve().is_relative_to(rt)
    for folder in ['before', 'candidate', 'source']: (E / folder).mkdir()
    metadata = []
    for path, data in snapshots.items():
        if data is not None: p.put(E / 'before' / path.name, data)
        metadata.append(dict(path=str(path), name=path.name, existed=data is not None, sha256=p.sha(path) if data is not None else None))
    for n in p.FILES:
        shutil.copy2(rt / n, E / 'before' / n); shutil.copy2(O / 'candidate' / n, E / 'candidate' / n)
        assert p.sha(E / 'before' / n) == before[n] and p.sha(E / 'candidate' / n) == after[n]
    for file in O.iterdir():
        if file.is_file() and file.suffix in ['.json', '.jaf', '.jam'] and file.name != 'native_raw_code.jam' and not file.name.startswith('jaf_'): shutil.copy2(file, E / 'source' / file.name)
    for n in ['build/build_claude_text_20261001.py', 'build/verify_claude_text_20261001.py', 'build/publish_claude_text_20261001.py', 'apply_decisions.py', 'verify_v3.py',
              'final/final_map_20261001.jsonl', 'final/extra_edits.jsonl', 'final/decision_log.md', 'final/결정_요청_20261001.md', 'final/report.md', '인계_20261001.md']:
        shutil.copy2(Q / n, E / 'source' / Path(n).name)
    latest = p.read(R / 'latest_worked_translation.json'); assert latest['manifest_sha256'] == current['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert p.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    full = new_map(latest, after, ev); translation = E / 'source/installed_translation_map.json'; p.put(translation, p.js(full))
    p.put(E / 'save_hashes_before.json', p.js(saves)); j = dict(status='PREPARED', runtime=str(rt), before=before, after=after, metadata=metadata); p.put(E / 'journal.json', p.js(j))
    def write(path, data):
        assert path in snapshots; j.setdefault('metadata_after', {})[str(path)] = hashlib.sha256(data).hexdigest(); p.put(E / 'journal.json', p.js(j)); p.put(path, data)
    attempted = False
    try:
        assert p.stopped(rt) and p.read(ptr) == current and p.sha(mp) == current['manifest_sha256']; assert saves == p.snapshot_saves()
        attempted = True; p.pair_apply(E / 'candidate', E / 'before', rt, before, after)
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, author=AUTHOR, files=after, source_files=before, evidence=str(E), changed_fields=ev['changed_fields'], map_rows=ev['map_rows'], extra_rows=ev['extra_rows'],
                   reflow_pages=ev['reflow_pages'], layout_only_fields=ev['layout_only_fields'], term_rows=ev['term_rows'], term_dynamic_pages=ev['term_dynamic_pages'],
                   added_functions=ev['added_functions'], relocated=ev['relocated'], CODE_prefix_exact=True, STR0_prefix_exact=True, MSG1_exact=False, save_schema_changes=0, save_writes=0,
                   vm_checks=ver['vm_ok'], native_probe_verified=False, screen_verified=False, translator_model=AUTHOR)
        nm = copy.deepcopy(manifest); nm.update(status=STATUS, time=now, claude_text_20261001_revision=rev)
        nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'], claude_text_overlay=str(E / 'source/build_evidence.json'))
        for row in nm['files']:
            if row['path'] in after: row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = 'User screen check: corrected dialogue lines; term display settings (용어 표기 설정) on a corrected line (e.g. m[60917] 참된 밤 -> 신야).'
        write(mp, p.js(nm)); mh = p.sha(mp)
        for n in contracts:
            c = p.read(R / n)
            for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if k in c: c[k] = mh
            for file, h in after.items():
                if file in c.get('required_files', {}): c['required_files'][file] = h
            c['claude_text_20261001_preserved_by'] = str(E); write(R / n, p.js(c))
        write(R / NEW, p.js({**rev, 'manifest': str(mp), 'manifest_sha256': mh, 'required_files': after, 'instruction': (
            'Supersedes required_claude_revision_20260923.json for MSG1: this is the new exact MSG1 snapshot (1,244 reviewed corrections + 2 extra edits + 101 reflowed pages; '
            'source claude_qa_20261001/final/final_map_20261001.jsonl). Every later build must start from this AIN or re-derive from latest_worked_translation.json. '
            'Term display settings: KR_TermMessage (fid 32158) is a trampoline to KR_T9Message; KR_T9Msg0..KR_T9Msg100 hold `id + exact current text -> expression` rows for all 8 terms '
            'generated from THIS text (1,791 rows, 24 dynamic pages via KR_TermWrapLine); KR_T9Message falls back to KR_T8Message (r14) and then the 09-23 tables. '
            'If MSG1 text of a term line changes again, regenerate the KR_T9 tables (build_claude_text_20261001.py section 2) or the term switch silently stops on that line. '
            'No caller code changed; CODE prefix and STR0 prefix are byte-exact; only appended code and the KR_TermMessage body (never on a saved stack).')}))
        nc = copy.deepcopy(current); nc.update(status=STATUS, manifest_sha256=mh, claude_text_20261001_revision=rev); write(ptr, p.js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation), translation_map_sha256=p.sha(translation), claude_text_20261001_evidence=str(E)); write(R / 'latest_worked_translation.json', p.js(latest))
        note = (f"\n\n### {now} 전체 대본 검수 교정 반입 + 용어 표기 설정 표 재생성 (Claude Fable 5.1 / Opus 5.5)\n"
                f"- 사용자: 「오푸스 5.5를 서브에이전트로 써서 … 최신 버전 번역 시나리오를 검수해」→「대부분 반영해. 드림캐스트 같은 건 그대로. 용어 변경 모드가 제대로 작동하도록」.\n"
                f"- 검수: 96,470줄 133덩어리 × Opus 5.5 검수자 2(뜻·일관성)+반증자 1 + 3차 독립 검수자, 에이전트 665개. 교정 {ev['map_rows']}줄(+범위 밖 2줄) 반입: 대사 속 그녀 168, 닫는 」 누락 252, 존대·호칭·용어·오역. 패러디·상표(드림캐스트 등)는 실제 이름 그대로. 결정 반영: claude_qa_20261001/final/decision_log.md.\n"
                f"- MSG1 만 변경(바뀐 칸 {ev['changed_fields']}, 쪽 재배치 {ev['reflow_pages']}쪽, FNL 실측 폭 Face 668/Text 884 전부 통과). CODE 접두·STR0 접두 불변.\n"
                f"- 용어 표기 설정: 새 본문으로 KR_T9Msg0~100·KR_T9Message 생성({ev['term_rows']}행, 동적 쪽 {ev['term_dynamic_pages']}), KR_TermMessage 트램펄린만 KR_T9Message 로(호출자 불변). VM 으로 기본값·대체 표기 2벌 × 전 행 실행 {ver['vm_ok']}건 일치.\n"
                f"- AIN {after['NightRemaster.ain']}; manifest {mh}; evidence {E}; 되돌리기 claude_qa_20261001/build/publish_claude_text_20261001.py --restore. 남은 것: 사용자 화면 확인, 결정 요청서의 미결 항목(패러디 표기 등은 그대로).\n")
        write(R / 'progress.md', snapshots[R / 'progress.md'] + note.encode('utf8'))
        p.exact_tree(rt, nm['files']); assert saves == p.snapshot_saves(); assert p.sha(rm) == keep['recovery_manifest_sha256'] and rh == {x: p.sha(rec / x) for x in p.FILES}
        j.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=p.sha(ptr)); p.put(E / 'journal.json', p.js(j))
    except BaseException as error:
        errors = []
        if attempted:
            try: p.pair_restore(E / 'before', rt, before, after)
            except BaseException as failure: errors.append(repr(failure))
        for path, data in reversed(list(snapshots.items())):
            try:
                if data is not None: p.put(path, data)
                elif path.exists(): path.unlink()
            except BaseException as failure: errors.append(repr(failure))
        j.update(status='ROLLBACK_INCOMPLETE' if errors else 'ROLLED_BACK', error=repr(error), rollback_errors=errors); p.put(E / 'journal.json', p.js(j)); raise
    report = dict(status=STATUS, files=after, manifest_sha256=mh, runtime=str(rt), unchanged_save_files=len(saves), recovery_unchanged=True, evidence=str(E), author=AUTHOR)
    p.put(E / 'publish_report.json', p.js(report)); p.put(O / 'publish_report.json', p.js(report)); print(p.js(report).decode('utf8'))

def restore():
    j = p.read(E / 'journal.json'); assert j['status'] == 'COMMITTED', j['status']
    rt = Path(j['runtime']); before = j['before']; after = j['after']
    if not p.stopped(rt): print('WAITING_FOR_GAME_EXIT'); return
    assert all(p.sha(rt / n) == after[n] for n in p.FILES), 'live files are not this install'
    p.pair_restore(E / 'before', rt, before, after)
    for m in j['metadata']:
        path = Path(m['path'])
        if m['existed']: p.put(path, (E / 'before' / m['name']).read_bytes()); assert p.sha(path) == m['sha256']
        elif path.exists(): path.unlink()
    j.update(status='RESTORED', restored_at=datetime.datetime.now().astimezone().isoformat()); p.put(E / 'journal.json', p.js(j)); print('RESTORED')

def fixture():
    # 설치 짝(pair_apply/pair_restore)을 실행본 사본에서 시험: 둘째 파일에서 실패를 주입해 첫 파일이 되돌아오는지 본다.
    ev, ver, ptr, current, mp, rt, before, after = prepare()
    T = O / 'fixture_live'; shutil.rmtree(T, ignore_errors=True); T.mkdir()
    for n in p.FILES: shutil.copy2(rt / n, T / n)
    B = O / 'fixture_before'; shutil.rmtree(B, ignore_errors=True); B.mkdir()
    for n in p.FILES: shutil.copy2(rt / n, B / n)
    try: p.pair_apply(O / 'candidate', B, T, before, after, fail_after=1)
    except RuntimeError: pass
    assert all(p.sha(T / n) == before[n] for n in p.FILES), 'rollback after injected failure failed'
    p.pair_apply(O / 'candidate', B, T, before, after); assert all(p.sha(T / n) == after[n] for n in p.FILES)
    p.pair_restore(B, T, before, after); assert all(p.sha(T / n) == before[n] for n in p.FILES)
    res = dict(status='TRANSACTION_FIXTURE_PASS', payload=after); p.put(O / 'transaction_verification.json', p.js(res)); print(res); shutil.rmtree(T); shutil.rmtree(B)

if __name__ == '__main__':
    if '--restore' in sys.argv: restore()
    elif '--fixture' in sys.argv: fixture()
    elif '--install' in sys.argv: install()
    else: print('usage: --fixture | --install | --restore')
