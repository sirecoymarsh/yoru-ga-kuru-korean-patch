"""Build one monthly summary layer as an append-only private candidate (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).

  python build_summary_layer.py --base <candidate folder> --summaries <summaries.json> [...] --tag <mm> --out <staging folder>
        [--story-fn KR_W29Story] [--scenarios <scenarios.json> ...] [--allow-prior-layers] [--allow-override-ids]
        [--dry-run [--allow-draft]]

<candidate folder> holds candidate/NightRemaster.ain (+ winmm.dll, manifest.json) and work/build/candidate_meta.json +
candidate_raw_code.jam of that AIN (the WI-009 staging, a previous layer's --out, or the installed label-particles r2 folder).

Steps: (1) guards: output under staging/ and outside the runtime / other agents' folders; the base was built over the AIN that
is installed now; its meta is re-dumped and must equal the given meta; (2) source/ = copies of the base AIN / DLL / meta (the
raw-code dump only hashed); (3) summaries merged in ID order (A/B halves), duplicate IDs refused, excluded never baked, copy_of resolved and cycle-free,
text gate (<= 100 characters, no line break, encodable), IDs inside the 1,164 calendar events and outside the summaries that already
exist (April 146 + E00011 + lower layers) unless --allow-override-ids; (4) JAF: KR_ST<tag>StoryBase stub with the getter's exact
signature + KR_ST<tag>Story tree -> `ain edit --jaf` -> the getter body cloned into StoryBase, the tree lowered to native opcodes,
the getter replaced by a one-line forwarder -> `ain edit --jam`; (5) gates: only the getter's metadata changed (address only),
every other metadata key identical, original CODE prefix / STR0 prefix / MSG1 identical, the six pinned functions identical, every
active opcode supported by the engine, the forwarder calls only KR_ST<tag>Story, the clone's op sequence equals the old getter's,
a Python twin of the compiled tree returns every baked text / copy target and falls through for every other event, the new STR0
entries decode to the summaries, winmm.dll unchanged; (6) candidate/manifest.json (+ design/ maps). Nothing is installed.
"""
from pathlib import Path
import argparse, datetime, json, re, shutil, struct, sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sltools as T
L = T.L


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--summaries', nargs='+', required=True)
    ap.add_argument('--scenarios', nargs='*', default=[])
    ap.add_argument('--tag', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--story-fn', default='KR_W29Story')
    ap.add_argument('--allow-prior-layers', action='store_true', help='the base already holds other KR_ST<tag> layers (stacking)')
    ap.add_argument('--allow-override-ids', action='store_true', help='let this layer replace summaries that exist below it')
    ap.add_argument('--dry-run', action='store_true', help='test build: manifest says 시험용, 설치 금지; publish refuses it')
    ap.add_argument('--allow-draft', action='store_true', help='bake status draft (only with --dry-run)')
    ap.add_argument('--term-patch', help='term_alignment.json: apply its proposals before baking (summaries.json untouched)')
    ap.add_argument('--term-confidence', default='high', choices=['low', 'medium', 'high'])
    ap.add_argument('--term-strict', action='store_true', help='stop when a patched text fails the gate (default: keep the approved text)')
    ap.add_argument('--only-patched', action='store_true', help='bake only the summaries the term patch changed (e.g. the April fix layer)')
    a = ap.parse_args(argv)
    assert not a.allow_draft or a.dry_run, '--allow-draft needs --dry-run'
    tag = a.tag
    story, base_fn = T.names(tag)
    pre = T.prefix(tag)
    base = Path(a.base).resolve()
    summaries = [Path(p).resolve() for p in a.summaries]
    out = T.assert_writable(a.out, extra_forbidden=[base] + [p.parent.parent for p in summaries])
    W = out / 'work/build'
    L.TMP = out / 'work/tmp'
    # gates first (merge, status, text, frozen source, term patch, copy_of): nothing is written on a refusal
    prep = T.prepare_layer(summaries, a.scenarios, a.allow_draft, a.term_patch, a.term_confidence, a.only_patched, a.term_strict)
    layer = prep['layer']

    # ---- 1. base and live
    b_ain, b_dll = base / 'candidate/NightRemaster.ain', base / 'candidate/winmm.dll'
    b_meta, b_raw, b_man = base / 'work/build/candidate_meta.json', base / 'work/build/candidate_raw_code.jam', base / 'candidate/manifest.json'
    for p in (b_ain, b_dll, b_meta, b_raw):
        assert p.exists(), ('base file missing', str(p))
    cur = L.readj(L.CURRENT)
    rt = Path(cur['runtime'])
    live_ain, live_dll = L.sha(rt / 'NightRemaster.ain'), L.sha(rt / 'winmm.dll')
    assert L.sha(Path(cur['manifest'])) == cur['manifest_sha256'], 'live manifest differs from current.json'
    base_sha = L.sha(b_ain)
    bman = L.readj(b_man) if b_man.exists() else {}
    if bman.get('files'):
        assert bman['files']['NightRemaster.ain']['sha256'] == base_sha, 'base manifest does not describe its AIN (build in progress?)'
    assert L.sha(b_dll) == live_dll, 'base winmm.dll differs from the installed one'
    if base_sha == live_ain:
        chain = 'base is the installed AIN'
    else:
        assert bman.get('live_sha256') == live_ain, ('base candidate was not built over the installed AIN', bman.get('live_sha256'), live_ain)
        assert not bman.get('dry_run') or a.dry_run, 'a dry-run candidate cannot be the base of a real layer'
        chain = 'base is a staged candidate over the installed AIN (installing this layer also installs the base changes)'

    # ---- 2. names, getter, IDs (still nothing written)
    m = L.read_meta(b_meta)
    fnames = [L.raw_symbol(m, f['index']) for f in m['functions']]
    prior = sorted(n for n in fnames if n.startswith('KR_ST'))
    if a.allow_prior_layers:
        assert all(re.fullmatch(r'KR_ST[0-9A-Za-z]{2}Story(Base)?|KR_ST29Mask(Base)?', n) for n in prior), ('unexpected KR_ST names', prior)
        tags = sorted({n[5:7] for n in prior if 'Story' in n})
        assert all(f'KR_ST{t}Story' in prior and f'KR_ST{t}StoryBase' in prior for t in tags), ('incomplete prior layer', prior)
        assert not any(n.startswith(pre) for n in fnames), (pre + ' already used', [n for n in fnames if n.startswith(pre)])
    else:
        assert not prior, ('KR_ST names already in the base (stack with --allow-prior-layers)', prior)
    for n in ('KR_P29Board', 'KR_P29Read', 'KR_CGlobal', 'KR_T9EvNo'):
        assert fnames.count(n) == 1, n
    gid = L.fid_of(m, a.story_fn)
    g = m['functions'][gid]
    assert [T.jaf_type(x['type']) for x in g['arguments']] == ['int'] and T.jaf_type(g['return-type']) == 'string', \
        ('the story getter must be string f(int)', a.story_fn)
    arg = g['arguments'][0]['name']
    texts, cps = prep['texts'], prep['copies']
    ids = sorted(set(texts) | set(cps))
    assert ids, 'nothing to bake'
    universe = T.all_event_ids()
    assert set(ids) <= universe, ('not calendar events', sorted(set(ids) - universe))
    below = dict.fromkeys(T.authored_before(), 'April 146 / E00011')
    for lay in bman.get('summary_layers', []):
        for n in lay['ids']:
            below[int(n)] = 'layer ' + lay['tag']
    for lay in bman.get('summary_layers', []):
        assert lay['tag'] != tag, ('tag already used below', tag)
    over = sorted(n for n in ids if n in below)
    assert not over or a.allow_override_ids, ('these IDs already have a summary below this layer', [(n, below[n]) for n in over])
    unresolved = sorted(n for n, o in cps.items() if o not in texts and o not in below)
    assert not unresolved, ('copy_of target has no summary in this layer or below', [(n, cps[n]) for n in unresolved])
    tabs = T.tab_of()
    tabnames = T.tab_names()

    # ---- 3. source copies (rebuild keeps them; they must still be the same bytes)
    if out.exists() and any(out.iterdir()):
        om = out / 'candidate/manifest.json'
        assert om.exists() and L.readj(om).get('tool') == T.TOOL_NAME, ('output folder not empty and not a previous build of this tool', str(out))
    for d in ('source', 'design', 'work/build', 'work/tmp', 'candidate', 'evidence', 'probe'):
        (out / d).mkdir(parents=True, exist_ok=True)
    # the base raw-code dump (~100 MB) is not needed after the build (the candidate gets its own dump): only its hash is recorded
    base_raw_sha = L.sha(b_raw)
    copies = {'NightRemaster.ain': b_ain, 'winmm.dll': b_dll, 'candidate_meta.json': b_meta}
    if b_man.exists():
        copies['base_manifest.json'] = b_man
    for n, p in copies.items():
        dst = out / 'source' / n
        if dst.exists():
            assert L.sha(dst) == L.sha(p), ('source copy differs from the base now: new output folder needed', n)
        else:
            shutil.copy2(p, dst)
    if (out / 'source_pointer.json').exists():
        assert L.readj(out / 'source_pointer.json') == cur, 'current.json changed since the source copy: new output folder needed'
    else:
        L.writej(out / 'source_pointer.json', cur)
    src = out / 'source/NightRemaster.ain'
    assert L.sha(src) == base_sha
    assert L.read_meta(out / 'source/candidate_meta.json') == m, 'base meta changed while copying'
    L.cmd('ain', 'dump', '-j', '-o', W / 'base_meta_check.json', src)
    assert L.read_meta(W / 'base_meta_check.json') == m, 'the base meta was not dumped from the base AIN'

    # ---- 4. JAF -> declare -> clone / lower / forward -> append
    items = [(n, ('text', texts[n])) for n in texts] + [(n, ('copy', cps[n])) for n in cps]
    items.sort()
    readable = (f'// Summary layer {tag} ({len(texts)} texts, {len(cps)} copies), {T.AUTHOR}. StoryBase = clone of {a.story_fn}.\n'
                + T.stub(base_fn, g) + '\n'
                + f'string {story}(int no) {{\n' + T.tree(items, story, base_fn) + '}\n')
    (W / 'helpers_readable.jaf').write_text(readable, 'utf-8')
    (W / 'helpers.jaf').write_text(L.jaf_literal_encode(L.strip_comments(readable)), 'utf-8')
    decl = W / 'declared.ain'
    cand = out / 'candidate/NightRemaster.ain'
    L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, src)
    L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl)
    dm = L.read_meta(W / 'declared_meta.json')
    added = {f['name']: f['index'] for f in dm['functions'][len(m['functions']):]}
    assert set(added) == {story, base_fn}, added
    assert T.signature(dm['functions'][added[base_fn]]) == T.signature(g), 'StoryBase stub signature differs from the getter'
    sf = dm['functions'][added[story]]
    assert [T.jaf_type(x['type']) for x in sf['arguments']] == ['int'] and T.jaf_type(sf['return-type']) == 'string' and not sf['variables']
    orig = W / (a.story_fn + '_original.jam')
    L.cmd('ain', 'dump', '--function', a.story_fn, '-o', orig, src)
    body = L.clean(orig.read_text('utf-8'), a.story_fn)
    body = re.sub(r'(?m)^FUNC .*$', f'FUNC {added[base_fn]}', body, count=1)
    body = re.sub(r'(?m)^ENDFUNC .*$', f'ENDFUNC {base_fn}', body)
    patch = [body]
    p = W / (story + '.jam')
    L.cmd('ain', 'dump', '--function', story, '-o', p, decl)
    jam = L.native_lower(p.read_text('utf-8'))
    jam = re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',
                 lambda z: '\t.LOCALASSIGN ' + z[1] + ' ' + str(struct.unpack('<i', struct.pack('<f', float(z[2])))[0]), jam)
    patch.append(L.clean(jam.replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), story))
    patch.append(f'FUNC {gid}\n\t.LOCALREF {arg}\n\tCALLFUNC {story}\n\tRETURN\nENDFUNC {a.story_fn}\n')
    (W / 'patch.jam').write_text('\n'.join(patch), 'utf-8')
    L.cmd('ain', 'edit', '--jam', W / 'patch.jam', '-o', cand, decl)
    raw0 = L.unpack(src.read_bytes())
    raw = bytearray(L.unpack(cand.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    cand.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))

    # ---- 5. gates
    gates = {}
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', cand)
    nm = L.read_meta(W / 'candidate_meta.json')
    assert [i for i, (x, y) in enumerate(zip(m['functions'], nm['functions'])) if x != y] == [gid], 'metadata changed beyond the getter'
    assert {k: v for k, v in g.items() if k != 'address'} == {k: v for k, v in nm['functions'][gid].items() if k != 'address'}
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], k
    assert len(nm['functions']) == len(m['functions']) + 2
    assert {L.raw_symbol(nm, i) for i in range(len(m['functions']), len(nm['functions']))} == {story, base_fn}
    gates['metadata_changed'] = [a.story_fn]
    for n in L.PINNED_ALL:
        assert m['functions'][L.fid_of(m, n)] == nm['functions'][L.fid_of(nm, n)], n
    gates['pinned_unchanged'] = list(L.PINNED_ALL)
    raw = L.unpack(cand.read_bytes())
    oldn = struct.unpack_from('<I', raw0, 12)[0]
    assert raw[16:16 + oldn] == raw0[16:16 + oldn], 'original CODE prefix changed'
    s0, s1 = L.strings(raw0)[2], L.strings(raw)[2]
    assert s1[:len(s0)] == s0, 'STR0 prefix changed'
    assert L.raw_messages(cand.read_bytes())[3] == L.raw_messages(src.read_bytes())[3], 'MSG1 changed'
    gates.update(original_code_prefix_exact=True, original_strings_prefix_exact=True, messages_exact=True)
    have = set(s1)
    missing = [n for n, t in texts.items() if L.encode(t) not in have]
    assert not missing, ('summary strings not in STR0', missing)
    gates['summary_strings_in_str0'] = len(texts)
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', cand)
    audit = L.audit(cand, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    gates['native_opcodes_supported'] = True
    fw = W / (a.story_fn + '_candidate.jam')
    L.cmd('ain', 'dump', '--function', a.story_fn, '-o', fw, cand)
    ops = [(op, r) for lab, op, r in T.jam_ops(fw.read_text('utf-8')) if not lab]
    assert ops == [('.LOCALREF', arg), ('CALLFUNC', story), ('RETURN', '')], ('forwarder body', ops)
    cb = W / (base_fn + '_candidate.jam')
    L.cmd('ain', 'dump', '--function', base_fn, '-o', cb, cand)
    assert T.normalized_body(cb.read_text('utf-8')) == T.normalized_body(orig.read_text('utf-8')), 'StoryBase is not a clone of the old getter'
    gates['forwarder_one_call'] = True
    gates['base_clone_op_sequence_equal'] = True
    ct = W / (story + '_candidate.jam')
    L.cmd('ain', 'dump', '--function', story, '-o', ct, cand)
    tree_jam = ct.read_text('utf-8')
    probe_ids = set(ids) | {n + d for n in ids for d in (-1, 1)} | set(list(sorted(universe))[::37]) | set(below)
    twin = 0
    for n in sorted(probe_ids):
        r = T.simulate(tree_jam, n, story, base_fn)
        if n in texts:
            assert r == ('text', texts[n]), (n, r)
        elif n in cps:
            o = cps[n]
            assert r == (('text', texts[o]) if o in texts else ('base', o)), (n, r)
        else:
            assert r == ('base', n), (n, r)
        twin += 1
    gates['tree_twin_checked_arguments'] = twin
    shutil.copy2(out / 'source/winmm.dll', out / 'candidate/winmm.dll')
    assert L.sha(out / 'candidate/winmm.dll') == live_dll
    gates['dll_unchanged'] = True

    # ---- 6. records
    now = datetime.datetime.now().astimezone().isoformat()
    april = T.april_texts()
    effective = {}
    prev_eff = bman.get('effective_summaries')
    if prev_eff and Path(prev_eff).exists():
        effective.update({int(k): v for k, v in L.readj(prev_eff)['texts'].items()})
    else:
        effective.update(april)
    effective.update(texts)
    for n, o in cps.items():
        if o in effective:
            effective[n] = effective[o]
    baked = dict(tag=tag, key=T.key(tag), author=T.AUTHOR, time=now, dry_run=a.dry_run,
                 events=[dict(no=n, tab=tabs.get(n), kind='text', summary=texts[n]) if n in texts else
                         dict(no=n, tab=tabs.get(n), kind='copy_of', copy_of=cps[n]) for n in ids],
                 excluded=layer['excluded'], files=layer['files'], copy_resolution=prep['copy_resolution'])
    T.writej(out / 'design/summaries_baked.json', baked)
    term = prep['term_record']
    if term:
        T.writej(out / 'evidence/term_patch_applied.json', dict(term, tag=tag, author=T.AUTHOR, time=now,
                 note='Applied to the baked text only; the summaries.json files are not modified.'))
    models = sorted({f['translator_model'] or '?' for f in layer['files']})
    provenance = dict(summary_text=models, layer_build=T.AUTHOR)
    if term and term['changed_ids']:
        provenance.update(term_alignment_edit=term['generated_by'], term_alignment_file=term['term_file'],
                          ko=f'원문 요약 {", ".join(models)}, 용어 정합 수정 {term["generated_by"]}')
    T.writej(out / 'design/effective_summaries.json', dict(
        note='Summaries known from files after this layer (April 146 + layers + copies); E00011 (KR_P29Story) is not a file text.',
        texts={str(k): v for k, v in sorted(effective.items())}))
    layers = list(bman.get('summary_layers', [])) + [dict(tag=tag, ids=ids, candidate=str(cand))]
    status = 'SUMMARY_LAYER_DRYRUN_TEST_ONLY_DO_NOT_INSTALL' if a.dry_run else 'SUMMARY_LAYER_STAGED_NATIVE_PENDING'
    man = dict(
        tool=T.TOOL_NAME, status=status, tag=tag, key=T.key(tag), dry_run=a.dry_run,
        note=('시험용, 설치 금지 (dry run: dummy summaries, not a deliverable)' if a.dry_run else
              'Private candidate; install only after probe, verify, Claude review and the user\'s permission.'),
        base=str(base), base_sha256=base_sha, base_manifest_status=bman.get('status'), base_chain=chain,
        base_meta_sha256=L.sha(b_meta), base_raw_code_sha256=base_raw_sha,
        live_sha256=live_ain, live_manifest_sha256=cur['manifest_sha256'], source_sha256=base_sha,
        files={n: dict(sha256=L.sha(out / 'candidate' / n), size=(out / 'candidate' / n).stat().st_size) for n in ('NightRemaster.ain', 'winmm.dll')},
        story_getter=a.story_fn, changed_functions=[a.story_fn], added_functions=added,
        summary_count=len(texts), copy_count=len(cps), excluded_count=len(layer['excluded']),
        summary_ids=ids, text_ids=sorted(texts), copies={str(k): v for k, v in cps.items()}, id_range=[ids[0], ids[-1]],
        tabs={tabnames[t]: sum(1 for n in ids if tabs.get(n) == t) for t in sorted({tabs.get(n) for n in ids if n in tabs})},
        overridden_ids=over, summary_sources=layer['files'],
        summaries_baked=str(out / 'design/summaries_baked.json'), summaries_baked_sha256=L.sha(out / 'design/summaries_baked.json'),
        effective_summaries=str(out / 'design/effective_summaries.json'), summary_layers=layers,
        board_layers=bman.get('board_layers', []),
        gates=gates, original_code_prefix_exact=True, original_strings_prefix_exact=True, messages_exact=True,
        serialized_schema_changes=0, pinned_functions_unchanged=list(L.PINNED_ALL), native_opcodes_supported=True,
        installed=False, time=now, author=T.AUTHOR,
        translator_models=models, provenance=provenance,
        term_patch=None if not term else dict(file=term['term_file'], file_sha256=term['term_file_sha256'], threshold=term['threshold'],
                                              applied=term['applied'], changed_ids=term['changed_ids'],
                                              gate_skipped=[g['no'] for g in term['gate_skipped']],
                                              skipped_summaries=term['skipped_summaries'], skipped_proposals=term['skipped_proposals'],
                                              record=str(out / 'evidence/term_patch_applied.json'),
                                              record_sha256=L.sha(out / 'evidence/term_patch_applied.json')),
        only_patched=a.only_patched)
    T.writej(out / 'candidate/manifest.json', man)
    print(json.dumps(dict(candidate=str(cand), sha256=man['files']['NightRemaster.ain']['sha256'], status=status, texts=len(texts),
                          copies=len(cps), excluded=len(layer['excluded']), id_range=man['id_range'], gates=sorted(gates)), ensure_ascii=False))
    return man


if __name__ == '__main__':
    main()
