"""Install preflight of one summary-layer candidate (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).

  python verify_summary_layer.py --out <layer staging folder> [--static-only]

The label-particles / April-summary verifiers generalized to a month tag. Everything is read-only except the report files in
<out>/evidence (and the disposable transaction fixture under <out>/work). Gates:
  1. the layer: a real build of this tool (not --dry-run), candidate files = manifest, current.json = the pointer copied at build
     time, live AIN = manifest live_sha256, live winmm.dll = candidate winmm.dll
  2. static, recomputed here: vs the base AND vs the live AIN: original CODE prefix, STR0 prefix, MSG1 identical; metadata vs the
     base: only the story getter changed (address only), two KR_ST<tag> functions appended, other keys identical, pinned functions
     identical; the getter forwards to KR_ST<tag>Story only; the tree twin returns every baked summary / copy target
  3. user resume saves (read only): every saved IP / return frame points at identical code bytes in the live and candidate AIN
  4. provenance: every summaries.json still has the hash it had at build time; a QA record next to it covers exactly those bytes
     (evidence/independent_review.json summary_sha256_after, else evidence/semantic_qa.json summary_sha256) and that frozen
     source, with no unresolved finding / open question unless a reviewer accepted exactly that many in <out>/design/qa_acceptance.json;
     independent_qa_pass rows need the independent review record
  5. consistency: check_summary_consistency on the source folders; every error-severity finding of a baked ID must be waived in
     <out>/design/consistency_review.json ({"reviewer", "waivers": [{"no", "type", "token", "reason"}]}) by the reviewing Claude
  6. native: evidence/native_summary_probe.json passed on this candidate for every baked ID (<= 5 lines, board <= 680, gap >= 12)
  7. the pair-install transaction fixture (publish_chart_r24.fixture, disposable projects) passes on this payload
--static-only runs 1-3 and writes evidence/static_recheck.json (no preflight verdict, nothing publish consumes).
Result: evidence/install_preflight.json status SUMMARY_LAYER_PREFLIGHT_PASS (publish_summary_layer.py requires it).
"""
from pathlib import Path
import argparse, datetime, json, struct, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import sltools as T
L = T.L


def static(out, man):
    cur = L.readj(L.CURRENT)
    rt = Path(cur['runtime'])
    assert cur == L.readj(out / 'source_pointer.json'), 'live build moved since the layer was built: rebuild the layer'
    assert L.sha(rt / 'NightRemaster.ain') == man['live_sha256'], 'live AIN differs from the one the layer was built over'
    files = {n: L.sha(out / 'candidate' / n) for n in ('NightRemaster.ain', 'winmm.dll')}
    assert files == {n: v['sha256'] for n, v in man['files'].items()}, 'candidate files differ from the manifest'
    external = man.get('kind') == 'external_layer'       # an adopted layer (stack top KR_TF29): no source/ copy of its base
    base_ain = Path(man['base']) / 'candidate/NightRemaster.ain' if external else out / 'source/NightRemaster.ain'
    assert (rt / 'winmm.dll').read_bytes() == (out / 'candidate/winmm.dll').read_bytes()
    assert L.sha(base_ain) == man['base_sha256']
    cand_b = (out / 'candidate/NightRemaster.ain').read_bytes()
    raw = L.unpack(cand_b)
    report = dict(files=files)
    for label, path in (('base', base_ain), ('live', rt / 'NightRemaster.ain')):
        b = path.read_bytes()
        r0 = L.unpack(b)
        n0 = struct.unpack_from('<I', r0, 12)[0]
        assert raw[16:16 + n0] == r0[16:16 + n0], ('original CODE prefix changed vs', label)
        s0 = L.strings(r0)[2]
        assert L.strings(raw)[2][:len(s0)] == s0, ('STR0 prefix changed vs', label)
        assert L.raw_messages(cand_b)[3] == L.raw_messages(b)[3], ('MSG1 changed vs', label)
        report[f'{label}_code_prefix_exact'] = report[f'{label}_strings_prefix_exact'] = report[f'{label}_messages_exact'] = True
    if external:
        report.update(layer_checks='adopted layer: gated by stack_layers.static_step at adoption; the whole chain by final_static_check.json')
        baked = T.readj(out / 'design/summaries_baked.json')
        return report | save_frames(out, rt, raw), baked
    m = L.read_meta(out / 'source/candidate_meta.json')
    nm = L.read_meta(out / 'work/build/candidate_meta.json')
    getter = man['story_getter']
    story, base_fn = T.names(man['tag'])
    changed = [L.raw_symbol(m, i) for i, (a, b) in enumerate(zip(m['functions'], nm['functions'])) if a != b]
    assert changed == [getter], ('metadata changed beyond the getter', changed)
    gid = L.fid_of(m, getter)
    assert {k: v for k, v in m['functions'][gid].items() if k != 'address'} == {k: v for k, v in nm['functions'][gid].items() if k != 'address'}
    assert [L.raw_symbol(nm, i) for i in range(len(m['functions']), len(nm['functions']))] and \
        {L.raw_symbol(nm, i) for i in range(len(m['functions']), len(nm['functions']))} == {story, base_fn}
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], k
    for n in L.PINNED_ALL:
        assert m['functions'][L.fid_of(m, n)] == nm['functions'][L.fid_of(nm, n)], n
    L.TMP = out / 'work/tmp'
    chk = out / 'work/verify'
    chk.mkdir(parents=True, exist_ok=True)
    L.cmd('ain', 'dump', '-j', '-o', chk / 'candidate_meta.json', out / 'candidate/NightRemaster.ain')
    assert L.read_meta(chk / 'candidate_meta.json') == nm, 'work/build/candidate_meta.json is not the candidate meta'
    L.cmd('ain', 'dump', '--function', getter, '-o', chk / 'getter.jam', out / 'candidate/NightRemaster.ain')
    ops = [(op, r) for lab, op, r in T.jam_ops((chk / 'getter.jam').read_text('utf-8')) if not lab]
    assert len(ops) == 3 and ops[1] == ('CALLFUNC', story) and ops[2][0] == 'RETURN', ('forwarder', ops)
    L.cmd('ain', 'dump', '--function', story, '-o', chk / 'story.jam', out / 'candidate/NightRemaster.ain')
    tree = (chk / 'story.jam').read_text('utf-8')
    baked = T.readj(out / 'design/summaries_baked.json')
    assert L.sha(out / 'design/summaries_baked.json') == man['summaries_baked_sha256'], 'summaries_baked.json changed after the build'
    for e in baked['events']:
        r = T.simulate(tree, e['no'], story, base_fn)
        if e['kind'] == 'text':
            assert r == ('text', e['summary']), e['no']
        else:
            o = e['copy_of']
            want = next((('text', x['summary']) for x in baked['events'] if x['no'] == o and x['kind'] == 'text'), ('base', o))
            assert r == want, (e['no'], r)
    report.update(metadata_changed=changed, pinned_unchanged=list(L.PINNED_ALL), forwarder_one_call=True,
                  tree_twin_events=len(baked['events']))
    return report | save_frames(out, rt, raw), baked


def save_frames(out, rt, raw):
    """User resume saves (read only): every saved IP / return frame points at identical code bytes in the live and candidate AIN."""
    live = L.unpack((rt / 'NightRemaster.ain').read_bytes())
    saves, frames = [], []
    for path in sorted(L.SAVES.glob('NightR*.asd')):
        if not path.stem[6:].isdigit():
            continue
        rec = L.save_records(path)
        if rec is None:
            continue
        saves.append(path.name)
        for fr in [rec['ip']] + rec['returns']:
            a = fr['address']
            if a < 0:
                continue
            assert live[16 + a:22 + a] == raw[16 + a:22 + a], (path.name, fr)
            frames.append(dict(save=path.name, **fr))
    (out / 'evidence').mkdir(parents=True, exist_ok=True)
    T.writej(out / 'evidence/save_frames.json', dict(saves=saves, frames=frames))
    return dict(existing_resume_saves=len(saves), saved_return_frames=len(frames))


QA_RECORDS = ('independent_review.json', 'semantic_qa.json')     # evidence/ of a summaries folder, newest review first


def qa_record(summaries_path, sha):
    """The QA record that covers exactly these summaries bytes: evidence/independent_review.json (summary_sha256_after) or
    evidence/semantic_qa.json (summary_sha256). Returns (path, doc) or (None, None)."""
    ev = Path(summaries_path).parent.parent / 'evidence'
    for name in QA_RECORDS:
        q = ev / name
        if q.exists():
            d = T.readj(q)
            if (d.get('summary_sha256_after') or d.get('summary_sha256')) == sha:
                return q, d
    return None, None


def acceptance(out):
    """<out>/design/qa_acceptance.json: open QA questions a reviewer accepted explicitly
    {"reviewer": "...", "accepted": [{"qa_sha256": "<sha of the QA record>", "count": n, "reason": "..."}]}."""
    f = out / 'design/qa_acceptance.json'
    doc = T.readj(f) if f.exists() else dict(accepted=[])
    return {a['qa_sha256']: dict(a, reviewer=doc.get('reviewer')) for a in doc.get('accepted', []) if a.get('reason') and doc.get('reviewer')}


def provenance(man, accepted=None):
    accepted = accepted or {}
    rows = []
    for f in man['summary_sources']:
        p = Path(f['path'])
        assert L.sha(p) == f['sha256'], ('summaries changed after the build: rebuild', str(p))
        qa_path, qa = qa_record(p, f['sha256'])
        assert qa_path, ('no QA record (independent_review.json / semantic_qa.json) covers this summaries.json', str(p))
        src = qa.get('source_scenarios_sha256') or qa.get('source_sha256')
        if f.get('scenarios_sha256') and src:
            assert src == f['scenarios_sha256'], ('the QA record covers another frozen source', str(qa_path))
        open_q = len(qa.get('unresolved') or [])
        acc = accepted.get(L.sha(qa_path))
        assert not open_q or (acc and acc.get('count') == open_q), ('unresolved QA findings / open questions (fix them, or accept them in '
                                                                   'design/qa_acceptance.json)', str(qa_path), open_q)
        statuses = {e.get('status') for e in T.readj(p).get('events', [])}
        if 'independent_qa_pass' in statuses:
            assert qa_path.name == 'independent_review.json', ('independent_qa_pass rows need the independent review record', str(p))
        rows.append(dict(summaries=str(p), qa=str(qa_path), qa_sha256=L.sha(qa_path), status=qa.get('status'), reviewer=qa.get('reviewer'),
                         reviewed_events=qa.get('reviewed_events'), translator_model=f.get('translator_model'), open_questions=open_q,
                         accepted_by=(acc or {}).get('reviewer'), accepted_reason=(acc or {}).get('reason')))
    tp = man.get('term_patch')
    if tp:
        assert L.sha(tp['record']) == tp['record_sha256'], 'term_patch_applied.json changed after the build'
        assert L.sha(tp['file']) == tp['file_sha256'], 'term_alignment.json changed after the build: rebuild'
        rows.append(dict(term_patch=tp['record'], term_file=tp['file'], applied=tp['applied'], changed=len(tp['changed_ids']),
                         gate_skipped=tp['gate_skipped'], editor=man.get('provenance', {}).get('term_alignment_edit')))
    return rows


def consistency(out, man):
    import check_summary_consistency as C
    folders = sorted({str(Path(f['path']).parent.parent) for f in man['summary_sources']})
    res = C.run([Path(x) for x in folders])
    baked = set(man['summary_ids'])
    errors = [f for f in res['findings'] if f['severity'] == 'error' and f.get('no') in baked]
    review_path = out / 'design/consistency_review.json'
    review = T.readj(review_path) if review_path.exists() else dict(waivers=[])
    waived = {(w['no'], w['type'], w.get('token')) for w in review.get('waivers', []) if w.get('reason')}
    open_ = [f for f in errors if (f['no'], f['type'], f.get('token')) not in waived]
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    T.writej(out / f'evidence/consistency_{stamp}.json', res)
    return dict(result=str(out / f'evidence/consistency_{stamp}.json'), errors=len(errors), warnings=sum(1 for f in res['findings'] if f['severity'] == 'warning'),
                waived=len(errors) - len(open_), open=len(open_), review=str(review_path) if review_path.exists() else None,
                reviewer=review.get('reviewer')), open_


def native(out, man, files, want=None, all_events=False):
    p = T.readj(out / 'evidence/native_summary_probe.json')
    assert p['pass'] and p['candidate_sha256'] == files['NightRemaster.ain'], 'native probe missing / failed / other candidate'
    assert set(man['summary_ids']) <= set(p['ids']), 'the native probe did not cover every baked ID'
    assert p.get('all_events') or not all_events, 'the stacked candidate needs the --all-events probe'
    stats = p['summary_stats']
    if want is None:
        want = [e['no'] for e in T.readj(out / 'design/summaries_baked.json')['events']]
    missing = [n for n in want if f'scene {n}' not in stats]
    assert not missing and not p.get('missing_summary_logs'), ('no SUMMARY log for', missing[:10])
    worst = dict(lines=max(v['lines'] for v in stats.values()), board_height=max(v['board_height'] for v in stats.values()),
                 gap=min(v['gap'] for v in stats.values()))
    assert worst['lines'] <= 5 and worst['board_height'] <= 680 and worst['gap'] >= 12, worst
    assert not p['user_files_changed']
    return dict(pid=p.get('pid'), audio=p.get('audio'), shots=p.get('shots'), worst=worst, scenes=len(want), cards=p.get('cards'),
                controls=p.get('controls'))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--static-only', action='store_true')
    ap.add_argument('--stack', action='store_true', help='the top of a stack_layers.py stack: every layer below is verified too')
    a = ap.parse_args(argv)
    out = T.assert_writable(a.out)
    man = T.readj(out / 'candidate/manifest.json')
    assert man.get('tool') == T.TOOL_NAME, 'not a summary-layer build'
    assert a.static_only or not man.get('dry_run'), 'a dry-run candidate (시험용, 설치 금지) is never verified for install'
    rep, baked = static(out, man)
    now = datetime.datetime.now().astimezone().isoformat()
    if a.static_only:
        doc = dict(status='SUMMARY_LAYER_STATIC_RECHECK_PASS', time=now, author=T.AUTHOR, tag=man['tag'], key=man['key'],
                   candidate_sha256=rep['files']['NightRemaster.ain'], base_sha256=man['base_sha256'], live_sha256=man['live_sha256'],
                   summary_count=man['summary_count'], copy_count=man['copy_count'], id_range=man['id_range'], **rep,
                   note='Static recheck only: not an install preflight (no native probe, QA, consistency or transaction gate).')
        T.writej(out / 'evidence/static_recheck.json', doc)
        print(json.dumps({k: v for k, v in doc.items() if k != 'files'}, ensure_ascii=False))
        return doc
    stack = None
    vman = man
    if a.stack:
        layers = T.chain(out)
        fs = T.readj(out.parent / 'final_static_check.json')
        assert fs['status'] == 'FINAL_STATIC_PASS' and fs['final_sha256'] == rep['files']['NightRemaster.ain'], 'final_static_check.json is not for this candidate'
        summ = [c['manifest'] for c in layers if not c['foreign'] and 'summary_sources' in c['manifest']]
        ids = sorted({n for mm in summ for n in mm['summary_ids']})
        vman = dict(man, summary_sources=[f for mm in summ for f in mm['summary_sources']], summary_ids=ids)
        prov = [row for mm in reversed(summ) for row in provenance(mm, acceptance(out))]
        stack = dict(final_static=str(out.parent / 'final_static_check.json'),
                     layers=[dict(folder=c['folder'], kind=c['manifest'].get('kind', 'summary_layer' if 'summary_sources' in c['manifest'] else 'base'),
                                  name=c['manifest'].get('name') or c['manifest'].get('tag'), sha256=c['manifest']['files']['NightRemaster.ain']['sha256'],
                                  status=c['manifest'].get('status'), provenance=c['manifest'].get('provenance'),
                                  translator_models=c['manifest'].get('translator_models'), summary_count=c['manifest'].get('summary_count'),
                                  copy_count=c['manifest'].get('copy_count'), term_patch=c['manifest'].get('term_patch'))
                             for c in reversed(layers)])
    else:
        prov = provenance(man, acceptance(out))
    cons, open_ = consistency(out, vman)
    assert not open_, ('consistency errors without a review waiver', len(open_), [(f['no'], f['type'], f.get('token')) for f in open_[:12]])
    nat = native(out, vman, rep['files'], want=vman['summary_ids'] if a.stack else None, all_events=a.stack)
    sys.path.insert(0, str(T.F))
    import publish_chart_r24 as P
    P.FILES = ['NightRemaster.ain', 'winmm.dll']
    P.O = out / 'candidate'
    L.WORK = out / 'work'
    tx = P.fixture()
    T.writej(out / 'evidence/transaction_verification.json', tx)
    base_note = man.get('base_chain', 'stack of layers over the installed AIN (stack.json / final_static_check.json)')
    report = dict(status='SUMMARY_LAYER_PREFLIGHT_PASS', time=now, author=T.AUTHOR, tag=man['tag'],
                  key='calendar_summary_stack_20260929' if a.stack else man['key'], stack=stack, files=rep['files'],
                  source_sha256=man['base_sha256'], live_sha256=man['live_sha256'], base_chain=base_note,
                  base_manifest_status=man.get('base_manifest_status'), summary_count=man['summary_count'], copy_count=man['copy_count'],
                  excluded_count=man['excluded_count'], summary_ids=vman['summary_ids'], id_range=[vman['summary_ids'][0], vman['summary_ids'][-1]],
                  tabs=man['tabs'],
                  static=rep, provenance=prov, consistency=cons, native=nat, transaction_fixture_pass=tx['status'] == 'TRANSACTION_FIXTURE_PASS',
                  translator_models=man['translator_models'], dll_unchanged=True, serialized_schema_changes=0,
                  limitations=['Display-only summaries on the event-calendar detail board; no scenario, choice, read-flag or save-layout change.',
                               'Native diagnostics used a muted private copy with read fixtures, not the user completion state or an all-route play test.',
                               'Summary meaning was reviewed by the semantic QA recorded per source folder; this preflight checks its coverage, not its content.'])
    assert report['transaction_fixture_pass']
    T.writej(out / 'evidence/install_preflight.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('summary_ids', 'static', 'provenance')}, ensure_ascii=False, indent=1))
    return report


if __name__ == '__main__':
    main()
