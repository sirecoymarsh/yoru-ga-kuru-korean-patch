"""Stopped-game-only install transaction for one summary layer (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).

  python publish_summary_layer.py --out <layer staging folder> --check                 read-only preflight, prints PREFLIGHT_PASS
  python publish_summary_layer.py --out <layer staging folder> --install [--include-base]
  python publish_summary_layer.py --tag <mm> --restore                                  exact pre-install bytes (journal-driven)

The label-particles publisher (docs/.../publish_calendar_label_particles_20260929.py) with the month as a parameter:
KEY calendar_<tag>_summaries_20260929, STATUS CALENDAR_<TAG>_SUMMARIES_20260929_INSTALLED_NATIVE_PASS, evidence
<project>/evidence/<KEY>, contract <project>/required_<KEY>.json, provenance Claude Opus 5.5 (claude-opus-5-5).
Refuses: a dry-run build, a layer without SUMMARY_LAYER_PREFLIGHT_PASS (verify_summary_layer.py) / Defender scan
(scan_summary_layer.ps1) / transaction fixture for exactly these bytes, a moved live build, a running game, an unexpected runtime
tree, an existing journal. A layer built on a staged (not installed) base candidate also installs that base's changes; that needs
--include-base and a base whose manifest status holds PREFLIGHT_PASS (normally install the base with its own publisher first and
rebuild the layer on it). --install / --restore are run only by Claude after the user's explicit permission.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse, copy, datetime, hashlib, shutil, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import sltools as T
L = T.L
sys.path.insert(0, str(T.F))
import publish_chart_r24 as P      # read-only reference: stopped / exact_tree / put / pair_apply / pair_restore / restore_ctx
R = L.CODEX
FILES = ['NightRemaster.ain', 'winmm.dll']
TOOL_FILES = ['sltools.py', 'build_summary_layer.py', 'prepare_summary_layer.py', 'build_board_layer.py', 'probe_summary_layer.py', 'probe_summary_layer.jaf', 'verify_summary_layer.py',
              'publish_summary_layer.py', 'check_summary_consistency.py', 'scan_summary_layer.ps1', 'README_요약층도구.md']


STACK_KEY = 'calendar_summary_stack_20260929'


def names(tag, stack=False):
    key = STACK_KEY if stack else T.key(tag)
    status = 'CALENDAR_SUMMARY_STACK_20260929_INSTALLED_NATIVE_PASS' if stack else f'CALENDAR_{tag.upper()}_SUMMARIES_20260929_INSTALLED_NATIVE_PASS'
    return key, status, R / 'evidence' / key, R / f'required_{key}.json'


def main(out, check=False, include_base=False, stack=False):
    out = Path(out).resolve()
    man = T.readj(out / 'candidate/manifest.json')
    assert man.get('tool') == T.TOOL_NAME, 'not a summary-layer build'
    assert not man.get('dry_run'), 'dry-run candidates (시험용, 설치 금지) are never installed'
    assert not man.get('superseded'), ('superseded build', man.get('superseded'))
    tag = man['tag']
    KEY, STATUS, E, NEW = names(tag, stack)
    qa = T.readj(out / 'evidence/install_preflight.json')
    after = {n: L.sha(out / 'candidate' / n) for n in FILES}
    before = {'NightRemaster.ain': man['live_sha256'], 'winmm.dll': after['winmm.dll']}
    assert qa['status'] == 'SUMMARY_LAYER_PREFLIGHT_PASS' and qa['files'] == after and qa['key'] == KEY
    assert after == {n: man['files'][n]['sha256'] for n in FILES}
    carries_base = man['base_sha256'] != man['live_sha256']
    layers = T.chain(out) if stack else None
    if stack:
        assert qa.get('stack'), 'the preflight was not run with --stack'
        foreign = layers[-1]
        base_status = foreign['manifest'].get('status') or ''
        if foreign['manifest']['files']['NightRemaster.ain']['sha256'] != man['live_sha256']:
            # the stack stands on a staged (not installed) WI-009 candidate: installing it installs that candidate too
            assert include_base, 'the stack carries the staged WI-009 candidate: pass --include-base'
            assert 'PREFLIGHT_PASS' in base_status, ('the WI-009 candidate under the stack has no preflight pass', base_status)
    elif carries_base:
        assert include_base, 'this layer sits on a staged base candidate: install the base first (then rebuild), or pass --include-base'
        assert 'PREFLIGHT_PASS' in (man.get('base_manifest_status') or ''), 'the base candidate has no preflight pass'
    sources = [f for lay in (layers or []) if not lay['foreign'] for f in lay['manifest'].get('summary_sources', [])] if stack else man['summary_sources']
    if stack:
        summ = [lay['manifest'] for lay in layers if not lay['foreign'] and 'summary_sources' in lay['manifest']]
        counts = dict(summary_count=sum(m_['summary_count'] for m_ in summ), copy_count=sum(m_['copy_count'] for m_ in summ),
                      id_range=[min(m_['id_range'][0] for m_ in summ), max(m_['id_range'][1] for m_ in summ)],
                      tabs={k: sum(m_['tabs'].get(k, 0) for m_ in summ) for k in sorted({k for m_ in summ for k in m_['tabs']})})
    else:
        counts = dict(summary_count=man['summary_count'], copy_count=man['copy_count'], id_range=man['id_range'], tabs=man['tabs'])
    for path, status in [(out / 'candidate/scan_report.json', 'SCANNED_NO_TARGET_DETECTIONS'),
                         (out / 'evidence/transaction_verification.json', 'TRANSACTION_FIXTURE_PASS')]:
        v = T.readj(path)
        assert v['status'] == status and v.get('payload', v.get('files')) == after, str(path)
    cur = L.readj(L.CURRENT)
    assert cur == L.readj(out / 'source_pointer.json'), 'Live build moved since staging: rebuild the layer'
    rt = Path(cur['runtime'])
    mp = Path(cur['manifest'])
    assert P.stopped(rt), 'Do not replace a running game'
    assert L.sha(mp) == cur['manifest_sha256']
    manifest = L.readj(mp)
    P.exact_tree(rt, manifest['files'])
    assert all(L.sha(rt / n) == h for n, h in before.items())
    latest = L.readj(R / 'latest_worked_translation.json')
    assert latest['manifest_sha256'] == cur['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    for f in sources:
        assert L.sha(Path(f['path'])) == f['sha256'], ('summaries changed after the build', f['path'])
    # Claude Fable 5.1 2026-09-30: every file the transaction copies is checked here, so --check catches a missing one
    # (the first --install stopped at a readable JAF the top KR_TF29 layer never produces; the live build was untouched).
    rels = ['candidate/scan_report.json', 'candidate/manifest.json', 'evidence/install_preflight.json', 'evidence/save_frames.json',
            'evidence/transaction_verification.json', 'evidence/native_summary_probe.json', 'design/summaries_baked.json',
            'design/effective_summaries.json']
    optional_rels = ['work/build/helpers_readable.jaf', 'design/consistency_review.json', 'design/qa_acceptance.json',
                     'evidence/term_patch_applied.json', 'source/external_manifest.json', 'evidence/native_term_probe_stack_twin.json']
    missing = [rel for rel in rels if not (out / rel).exists()]
    assert not missing, ('install sources missing from the layer folder', missing)
    missing_optional = [rel for rel in optional_rels if not (out / rel).exists()]
    rels = rels + [rel for rel in optional_rels if (out / rel).exists()]
    cons = qa['consistency']['result']
    assert Path(cons).exists(), ('consistency result missing', cons)
    assert (out / 'evidence/native_summary').is_dir(), 'native_summary screenshots missing'
    for name in TOOL_FILES:
        assert (H / name).exists(), ('tool file missing', name)
    if stack:
        assert (out.parent / 'final_static_check.json').exists(), 'final_static_check.json missing'
    if check:
        print('PREFLIGHT_PASS', KEY, after, 'carries_base' if carries_base else 'base_is_live')
        return
    assert not E.exists() and not NEW.exists(), 'Inspect existing journal'
    contracts = sorted(R.glob('required_*.json'))
    paths = [mp, L.CURRENT, R / 'progress.md', R / 'latest_worked_translation.json', NEW] + contracts
    assert len(paths) == len({x.name for x in paths})
    snapshots = {p: p.read_bytes() if p.exists() else None for p in paths}
    for d in ['before', 'candidate', 'source', 'source/tools', 'source/summaries', 'screenshots']:
        (E / d).mkdir(parents=True)
    metadata = []
    for p, data in snapshots.items():
        if data is not None:
            P.put(E / 'before' / p.name, data)
        metadata.append(dict(path=str(p), name=p.name, existed=data is not None, sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    for n in FILES:
        shutil.copy2(rt / n, E / 'before' / n)
        shutil.copy2(out / 'candidate' / n, E / 'candidate' / n)
    for rel in rels:
        shutil.copy2(out / rel, E / 'source' / Path(rel).name)
    shutil.copy2(cons, E / 'source' / Path(cons).name)
    for name in TOOL_FILES:
        shutil.copy2(H / name, E / 'source/tools' / name)
    if stack:
        (E / 'source/layers').mkdir(parents=True, exist_ok=True)
        for lay in reversed(layers):
            if lay['foreign']:
                continue
            ld = Path(lay['folder'])
            dst = E / 'source/layers' / ld.name
            dst.mkdir(parents=True, exist_ok=True)
            for rel in ('candidate/manifest.json', 'design/summaries_baked.json', 'evidence/term_patch_applied.json', 'work/build/helpers_readable.jaf',
                        'source/external_manifest.json', 'work/build/board_diff.txt'):
                if (ld / rel).exists():
                    shutil.copy2(ld / rel, dst / Path(rel).name)
        shutil.copy2(out.parent / 'final_static_check.json', E / 'source/final_static_check.json')
        if (out.parent / 'stack.json').exists():
            shutil.copy2(out.parent / 'stack.json', E / 'source/stack.json')
    for i, f in enumerate(sources):
        sp = Path(f['path'])
        shutil.copy2(sp, E / 'source/summaries' / f'{i}_{sp.parent.parent.name}_summaries.json')
        for qn in ('independent_review.json', 'semantic_qa.json'):
            qp = sp.parent.parent / 'evidence' / qn
            if qp.exists():
                shutil.copy2(qp, E / 'source/summaries' / f'{i}_{sp.parent.parent.name}_{qn}')
    for path in (out / 'evidence/native_summary').glob('*.png'):
        shutil.copy2(path, E / 'screenshots' / path.name)
    saves = P.snapshot_folder(L.SAVES)
    menu = P.snapshot_folder(rt / 'KRMenu') if (rt / 'KRMenu').exists() else None
    P.put(E / 'save_hashes_before.json', P.js(saves))
    full = L.readj(Path(latest['translation_map']))
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full[KEY] = dict(evidence=str(E), semantic_dialogue_changes=0, summary_count=counts['summary_count'], copy_count=counts['copy_count'],
                     id_range=man['id_range'], tabs=man['tabs'], map=str(E / 'source/summaries_baked.json'),
                     map_sha256=L.sha(E / 'source/summaries_baked.json'), translator_model=man['translator_models'], author=T.AUTHOR)
    translation = E / 'source/installed_translation_map.json'
    P.put(translation, P.js(full))
    journal = dict(status='PREPARED', runtime=str(rt), files=FILES, before=before, after=after, metadata=metadata,
                   missing_optional_sources=missing_optional)
    P.put(E / 'journal.json', P.js(journal))

    def write(p, data):
        assert p in snapshots
        journal.setdefault('metadata_after', {})[str(p)] = hashlib.sha256(data).hexdigest()
        P.put(E / 'journal.json', P.js(journal))
        P.put(p, data)
    attempted = False
    try:
        assert P.stopped(rt) and L.readj(L.CURRENT) == cur and P.snapshot_folder(L.SAVES) == saves
        assert all((p.read_bytes() if p.exists() else None) == v for p, v in snapshots.items())
        attempted = True
        P.pair_apply(E / 'candidate', E / 'before', rt, before, after, files=FILES)
        now = datetime.datetime.now().astimezone().isoformat()
        rev = dict(status=STATUS, time=now, files=after, source_files=before, evidence=str(E), schema_changes=0,
                   summary_count=counts['summary_count'], copy_count=counts['copy_count'], id_range=counts['id_range'], tabs=counts['tabs'],
                   story_getter=man['story_getter'], added_functions=man['added_functions'], translator_model=man['translator_models'],
                   provenance=man.get('provenance'), term_patch=man.get('term_patch'),
                   author=T.AUTHOR, limitations=qa['limitations'])
        if carries_base:
            rev['includes_base_candidate'] = dict(path=man['base'], sha256=man['base_sha256'], status=man.get('base_manifest_status'))
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now)
        nm[KEY + '_revision'] = rev
        nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'])
        nm['ain'][KEY] = str(E / 'source/install_preflight.json')
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = (f'Summary layer {tag} installed (KR_ST{tag}Story over {man["story_getter"]}). Preserve the April summaries, E00011, '
                      'lower layers, the unread masking and the original scenario / saves.')
        write(mp, P.js(nm))
        mh = L.sha(mp)
        for p in contracts:
            co = L.readj(p)
            for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if k in co:
                    co[k] = mh
            for n, h in after.items():
                if n in co.get('required_files', {}):
                    co['required_files'][n] = h
            co[KEY + '_preserved_by'] = str(E)
            write(p, P.js(co))
        if stack:
            rev['stack'] = dict(layers=qa['stack']['layers'], final_static=qa['stack']['final_static'],
                                base=dict(folder=layers[-1]['folder'], sha256=layers[-1]['manifest']['files']['NightRemaster.ain']['sha256'],
                                          status=layers[-1]['manifest'].get('status'), author=layers[-1]['manifest'].get('author'),
                                          designer=layers[-1]['manifest'].get('designer')),
                                summary_provenance=qa['provenance'])
        write(NEW, P.js({**rev, 'manifest': str(mp), 'manifest_sha256': mh, 'required_files': after,
                         'verification': {k: qa[k] for k in ('status', 'native', 'consistency', 'provenance', 'transaction_fixture_pass')},
                         'instruction': (f'Keep {man["story_getter"]} a one-line forwarder to KR_ST{tag}Story; KR_ST{tag}StoryBase keeps the '
                                         'previous getter body (April KR_AS29Story, E00011 KR_P29Story and every lower layer). A later layer '
                                         'clones the forwarder as its own Base. Summaries show only on read scenes; unread scenes hide them '
                                         'even under 전체 개방. No scenario, choice, read-flag or save-layout change.')}))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh)
        nc[KEY + '_revision'] = rev
        write(L.CURRENT, P.js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation))
        latest[KEY + '_evidence'] = str(E)
        write(R / 'latest_worked_translation.json', P.js(latest))
        tabs = ', '.join(f'{k} {v}' for k, v in counts['tabs'].items())
        note = (f'\n\n### {now} 이벤트 캘린더 장면 요약 층 {tag} 설치\n'
                f'- 요약 {counts["summary_count"]}개 + 원본 요약 재사용 {counts["copy_count"]}개 ({tabs}); ID {counts["id_range"][0]}–{counts["id_range"][1]}. '
                f'집필 {", ".join(man["translator_models"])}; 층 빌드·검증 {T.AUTHOR}.\n'
                f'- 상세 보드 줄거리 getter {man["story_getter"]} → KR_ST{tag}Story(없으면 이전 getter 몸체 KR_ST{tag}StoryBase). 감상한 장면에만 표시, '
                '미열람은 전체 개방에서도 숨김. 원본 CODE/STR prefix·MSG·직렬화 구조·DLL·세이브 보존.\n'
                f'- 무음 native: 최대 {qa["native"]["worst"]["lines"]}줄 / 보드 {qa["native"]["worst"]["board_height"]}px / 버튼 위 여백 '
                f'{qa["native"]["worst"]["gap"]}px.\n'
                f'- 설치 {rt}; 백업 {E / "before"}; 복구 publish_summary_layer.py --tag {tag} --restore.\n')
        write(R / 'progress.md', snapshots[R / 'progress.md'] + note.encode('utf8'))
        P.exact_tree(rt, nm['files'])
        assert P.snapshot_folder(L.SAVES) == saves
        assert (P.snapshot_folder(rt / 'KRMenu') if (rt / 'KRMenu').exists() else None) == menu
        journal.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=L.sha(L.CURRENT))
        P.put(E / 'journal.json', P.js(journal))
    except BaseException as error:
        failures = []
        if attempted:
            try:
                P.pair_restore(E / 'before', rt, before, after, files=FILES)
            except BaseException as er:
                failures.append(repr(er))
        for p, data in reversed(list(snapshots.items())):
            try:
                if data is not None:
                    P.put(p, data)
                elif p.exists():
                    assert p == NEW
                    p.unlink()
            except BaseException as er:
                failures.append(repr(er))
        journal.update(status='ROLLBACK_INCOMPLETE' if failures else 'ROLLED_BACK', error=repr(error), rollback_errors=failures)
        P.put(E / 'journal.json', P.js(journal))
        raise
    report = dict(status=STATUS, files=after, manifest_sha256=mh, runtime=str(rt), user_save_files_unchanged=len(saves),
                  backup=str(E / 'before'), prior_contracts_preserved=len(contracts))
    P.put(E / 'publish_report.json', P.js(report))
    P.put(out / 'publish_report.json', P.js(report))
    P.put(E / 'README.md', (f'# 이벤트 캘린더 장면 요약 층 {tag}\n\n상세 보드의 줄거리에 요약 {counts["summary_count"]}개를 더했습니다(원본 요약 재사용 '
                            f'{counts["copy_count"]}개). 감상한 장면에만 보이고, 기존 4월 요약·E00011·아래 층은 그대로입니다.\n\n'
                            '- screenshots: 무음 사본 엔진 화면\n- before: 설치 전 백업\n- source: 요약표·검증·설치/복구 도구\n').encode('utf8'))
    print(P.js(report).decode())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--tag')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--check', action='store_true')
    g.add_argument('--install', action='store_true')
    g.add_argument('--restore', action='store_true')
    ap.add_argument('--include-base', action='store_true')
    ap.add_argument('--stack', action='store_true', help='install the top of a stack_layers.py stack (KEY calendar_summary_stack_20260929)')
    a = ap.parse_args()
    if a.restore:
        assert a.tag or a.stack, '--restore needs --tag (or --stack)'
        _, _, E, _ = names(a.tag, a.stack)
        P.restore_ctx(SimpleNamespace(root=R, evidence=E, pointer=L.CURRENT, stop_check=P.stopped))
    else:
        assert a.out, '--check / --install need --out'
        main(a.out, check=a.check, include_base=a.include_base, stack=a.stack)
