"""SB29 board layer: the full-width summary below the portrait grid on 6-column boards (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).

  python build_board_layer.py --base <candidate folder> --out <staging folder>
        [--board-source <WI-009 work/build/helpers_readable.jaf>] [--dry-run]

Coordinator 09-29: with 9+ people (cols == 6) the right field column is 356 px (16 characters) and 17 summaries run to 6-7 lines.
Instead of shortening them, KR_W29Board becomes a one-line forwarder to KR_SB29Board = the KR_W29Board body with one change:
only when cols == 6 the heading (KR_P29Part(8)) and the summary (KR_P29Part(9)) are drawn below the portrait grid at full width
(x 28, font 20, storyWidth 1064/20 - 1 = 52); their height goes into bottom / height, not into the field column's infoH (the field
font attempts see the fields only). The vertical divider (KR_P29Part(6)) keeps the grid / field bottom so it never crosses the
summary. 3 / 4 columns run exactly the old statements (the story block of the attempt loop is guarded by cols != 6).
board_layer/predict_sb29.py predicts the result (17 listed scenes: 6-7 -> <= 2 lines, boards <= 623).

Gates: the readable KR_W29Board source compiled unchanged (scratch AIN, not shipped) has the op sequence of the base's KR_W29Board
(so the clone is the installed function); the four text edits apply exactly once each; then the summary-layer gates: only
KR_W29Board's metadata changed (address only), one function appended, other metadata keys identical, pinned functions identical,
original CODE / STR0 / MSG1 identical, every active opcode supported, the forwarder is one call, winmm.dll unchanged.
Stack order (coordinator): W29 -> term-link layer (other agent, if any) -> this board layer -> monthly summary layers.
"""
from pathlib import Path
import argparse, datetime, difflib, json, re, shutil, struct, sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sltools as T
L = T.L
BOARD, NEW = 'KR_W29Board', 'KR_SB29Board'
DEFAULT_SOURCE = T.STAGING / 'calendar_all_tabs_20260929/work/build/helpers_readable.jaf'
EDITS = [
    ('void KR_W29Board(', 'void KR_SB29Board('),
    ('        if (story!="") {\n            string heading="줄거리";',
     '        if (story!="" && cols!=6) {\n            string heading="줄거리";'),
    ('    int bottom=bodyY+rows*168-10;\n    if (bodyY-28+infoH>bottom) bottom=bodyY-28+infoH;\n    int height=bottom+92;\n',
     '    int bottom=bodyY+rows*168-10;\n    if (bodyY-28+infoH>bottom) bottom=bodyY-28+infoH;\n    int lineBottom=bottom;\n'
     '    if (story!="" && cols==6) {\n'
     '        string wideHeading="줄거리";\n'
     '        if(stages>1)wideHeading="첫 장면 줄거리";\n'
     '        int wideWidth=1064/20-1;\n'
     '        int wideY=bottom+16;\n'
     '        KR_CText(KR_P29Part(8),root,28.0,float(wideY),20,KR_CTint(wideHeading,KR_CGold()),3);\n'
     '        int wideHW=0;int wideHH=0;int wideSW=0;int wideSH=0;\n'
     '        PartsEngine.Parts_GetPartsSize(KR_P29Part(8),wideHW,wideHH,1);\n'
     '        KR_CText(KR_P29Part(9),root,28.0,float(wideY+wideHH+8),20,KR_B29Wrap(story,wideWidth),3);\n'
     '        PartsEngine.Parts_GetPartsSize(KR_P29Part(9),wideSW,wideSH,1);\n'
     '        bottom=wideY+wideHH+8+wideSH;\n'
     '    }\n'
     '    int height=bottom+92;\n'),
    ('KR_CBox(KR_P29Part(6),root,float(infoX-20),float(bodyY-28),2,bottom-bodyY+28,',
     'KR_CBox(KR_P29Part(6),root,float(infoX-20),float(bodyY-28),2,lineBottom-bodyY+28,'),
]


def function(text, name):
    start = re.search(r'^(?:void|int|string|bool) ' + re.escape(name) + r'\(', text, re.M).start()
    pos = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[pos] == '{') - (text[pos] == '}')
        pos += 1
    return text[start:pos]


def lowered(p, name):
    jam = L.native_lower(Path(p).read_text('utf-8'))
    jam = re.sub(r'(?m)^\t\.F_LOCALASSIGN (\w+) ([-+0-9.eE]+)$',
                 lambda z: '\t.LOCALASSIGN ' + z[1] + ' ' + str(struct.unpack('<i', struct.pack('<f', float(z[2])))[0]), jam)
    return L.clean(jam.replace('\tF_ASSIGN\n', '\tX_ASSIGN 1\n'), name)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--board-source', default=str(DEFAULT_SOURCE))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    base = Path(a.base).resolve()
    src_jaf = Path(a.board_source).resolve()
    out = T.assert_writable(a.out, extra_forbidden=[base])
    W = out / 'work/build'
    L.TMP = out / 'work/tmp'
    b_ain, b_dll = base / 'candidate/NightRemaster.ain', base / 'candidate/winmm.dll'
    b_meta, b_raw, b_man = base / 'work/build/candidate_meta.json', base / 'work/build/candidate_raw_code.jam', base / 'candidate/manifest.json'
    for p in (b_ain, b_dll, b_meta, b_raw, src_jaf):
        assert p.exists(), ('missing', str(p))
    cur = L.readj(L.CURRENT)
    rt = Path(cur['runtime'])
    live_ain, live_dll = L.sha(rt / 'NightRemaster.ain'), L.sha(rt / 'winmm.dll')
    base_sha = L.sha(b_ain)
    bman = L.readj(b_man) if b_man.exists() else {}
    if bman.get('files'):
        assert bman['files']['NightRemaster.ain']['sha256'] == base_sha, 'base manifest does not describe its AIN'
    assert L.sha(b_dll) == live_dll
    if base_sha != live_ain:
        assert bman.get('live_sha256') == live_ain, 'base candidate was not built over the installed AIN'
        assert not bman.get('dry_run') or a.dry_run
    m = L.read_meta(b_meta)
    fnames = [L.raw_symbol(m, f['index']) for f in m['functions']]
    assert not any(n.startswith('KR_SB29') for n in fnames), 'KR_SB29 already present'
    assert fnames.count(BOARD) == 1 and fnames.count('KR_P29Board') == 1
    gid = L.fid_of(m, BOARD)
    g = m['functions'][gid]
    old_text = function(src_jaf.read_text('utf-8'), BOARD)
    new_text = old_text
    for x, y in EDITS:
        assert new_text.count(x) == 1, ('edit anchor not found exactly once', x[:60])
        new_text = new_text.replace(x, y)
    # ---- write only now
    if out.exists() and any(out.iterdir()):
        om = out / 'candidate/manifest.json'
        assert om.exists() and L.readj(om).get('tool') == T.TOOL_NAME, ('output folder not empty', str(out))
    for d in ('source', 'design', 'work/build', 'work/tmp', 'candidate', 'evidence'):
        (out / d).mkdir(parents=True, exist_ok=True)
    for n, p in {'NightRemaster.ain': b_ain, 'winmm.dll': b_dll, 'candidate_meta.json': b_meta}.items():
        dst = out / 'source' / n
        if dst.exists():
            assert L.sha(dst) == L.sha(p), ('source copy differs from the base now', n)
        else:
            shutil.copy2(p, dst)
    if b_man.exists():
        shutil.copy2(b_man, out / 'source/base_manifest.json')
    if not (out / 'source_pointer.json').exists():
        L.writej(out / 'source_pointer.json', cur)
    assert L.readj(out / 'source_pointer.json') == cur
    src = out / 'source/NightRemaster.ain'
    L.cmd('ain', 'dump', '-j', '-o', W / 'base_meta_check.json', src)
    assert L.read_meta(W / 'base_meta_check.json') == m, 'the base meta was not dumped from the base AIN'
    # ---- gate: the readable source is the installed KR_W29Board (compiled unchanged under a scratch name, never shipped)
    check = old_text.replace(f'void {BOARD}(', 'void KR_SB29SourceCheck(', 1)
    (W / 'source_check.jaf').write_text(L.jaf_literal_encode(L.strip_comments(check)), 'utf-8')
    L.cmd('ain', 'edit', '--jaf', W / 'source_check.jaf', '-o', W / 'source_check_decl.ain', src)
    L.cmd('ain', 'dump', '--function', 'KR_SB29SourceCheck', '-o', W / 'source_check.jam', W / 'source_check_decl.ain')
    (W / 'source_check_patch.jam').write_text(lowered(W / 'source_check.jam', 'KR_SB29SourceCheck'), 'utf-8')
    L.cmd('ain', 'edit', '--jam', W / 'source_check_patch.jam', '-o', W / 'source_check.ain', W / 'source_check_decl.ain')
    L.cmd('ain', 'dump', '--function', 'KR_SB29SourceCheck', '-o', W / 'source_check_assembled.jam', W / 'source_check.ain')
    L.cmd('ain', 'dump', '--function', BOARD, '-o', W / (BOARD + '_original.jam'), src)
    base_ops = T.normalized_body((W / (BOARD + '_original.jam')).read_text('utf-8'))
    check_ops = T.normalized_body((W / 'source_check_assembled.jam').read_text('utf-8'))
    assert check_ops == base_ops, ('the readable KR_W29Board source is not the base function', len(check_ops), len(base_ops),
                                   next(((i, x, y) for i, (x, y) in enumerate(zip(check_ops, base_ops)) if x != y), None))
    for n in ('source_check.ain', 'source_check_decl.ain'):
        (W / n).unlink()
    # ---- the layer
    (W / 'helpers_readable.jaf').write_text(f'// SB29 board layer, {T.AUTHOR}. KR_W29Board body + the 6-column full-width summary.\n' + new_text + '\n', 'utf-8')
    (W / 'board_diff.txt').write_text(''.join(difflib.unified_diff(old_text.splitlines(True), new_text.splitlines(True), 'KR_W29Board', 'KR_SB29Board')), 'utf-8')
    (W / 'helpers.jaf').write_text(L.jaf_literal_encode(L.strip_comments(new_text + '\n')), 'utf-8')
    decl = W / 'declared.ain'
    cand = out / 'candidate/NightRemaster.ain'
    L.cmd('ain', 'edit', '--jaf', W / 'helpers.jaf', '-o', decl, src)
    L.cmd('ain', 'dump', '-j', '-o', W / 'declared_meta.json', decl)
    dm = L.read_meta(W / 'declared_meta.json')
    added = {f['name']: f['index'] for f in dm['functions'][len(m['functions']):]}
    assert set(added) == {NEW}, added
    nf = dm['functions'][added[NEW]]
    assert [x['type'] for x in nf['arguments']] == [x['type'] for x in g['arguments']] and nf['return-type'] == g['return-type']
    L.cmd('ain', 'dump', '--function', NEW, '-o', W / (NEW + '.jam'), decl)
    patch = [lowered(W / (NEW + '.jam'), NEW)]
    fw = [f'FUNC {gid}']
    for x in g['arguments']:
        fw.append(f'\t.LOCALREF {x["name"]}')
        if T.jaf_type(x['type']) == 'string':
            fw.append('\tA_REF')
    fw += [f'\tCALLFUNC {NEW}', '\tRETURN', f'ENDFUNC {BOARD}', '']
    patch.append('\n'.join(fw))
    (W / 'patch.jam').write_text('\n'.join(patch), 'utf-8')
    L.cmd('ain', 'edit', '--jam', W / 'patch.jam', '-o', cand, decl)
    raw0 = L.unpack(src.read_bytes())
    raw = bytearray(L.unpack(cand.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    cand.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    # ---- gates
    L.cmd('ain', 'dump', '-j', '-o', W / 'candidate_meta.json', cand)
    nm = L.read_meta(W / 'candidate_meta.json')
    assert [i for i, (x, y) in enumerate(zip(m['functions'], nm['functions'])) if x != y] == [gid]
    assert {k: v for k, v in g.items() if k != 'address'} == {k: v for k, v in nm['functions'][gid].items() if k != 'address'}
    assert len(nm['functions']) == len(m['functions']) + 1
    for k in m:
        if k != 'functions':
            assert m[k] == nm[k], k
    for n in L.PINNED_ALL:
        assert m['functions'][L.fid_of(m, n)] == nm['functions'][L.fid_of(nm, n)], n
    raw = L.unpack(cand.read_bytes())
    oldn = struct.unpack_from('<I', raw0, 12)[0]
    assert raw[16:16 + oldn] == raw0[16:16 + oldn]
    assert L.strings(raw)[2][:len(L.strings(raw0)[2])] == L.strings(raw0)[2]
    assert L.raw_messages(cand.read_bytes())[3] == L.raw_messages(src.read_bytes())[3]
    L.cmd('ain', 'dump', '--raw-code', '--no-macros', '-o', W / 'candidate_raw_code.jam', cand)
    audit = L.audit(cand, W / 'candidate_meta.json', W / 'candidate_raw_code.jam', rt / 'NightRemaster.exe')
    assert audit['all_active_opcodes_supported'], audit['unsupported'][:5]
    L.writej(W / 'native_opcode_audit.json', audit)
    L.cmd('ain', 'dump', '--function', BOARD, '-o', W / (BOARD + '_candidate.jam'), cand)
    ops = [(op, r) for lab, op, r in T.jam_ops((W / (BOARD + '_candidate.jam')).read_text('utf-8')) if not lab]
    assert [o for o in ops if o[0] == 'CALLFUNC'] == [('CALLFUNC', NEW)] and ops[-1][0] == 'RETURN', ops
    shutil.copy2(out / 'source/winmm.dll', out / 'candidate/winmm.dll')
    assert L.sha(out / 'candidate/winmm.dll') == live_dll
    now = datetime.datetime.now().astimezone().isoformat()
    status = 'BOARD_LAYER_DRYRUN_TEST_ONLY_DO_NOT_INSTALL' if a.dry_run else 'BOARD_LAYER_STAGED_NATIVE_PENDING'
    pred = T.TOOLS / 'board_layer/predict_sb29.json'
    man = dict(tool=T.TOOL_NAME, kind='board_layer', status=status, tag='SB29', key='calendar_board_sb29_20260929', dry_run=a.dry_run,
               note='6-column boards: summary below the portrait grid at full width; 3 / 4 columns unchanged. Not installed.',
               base=str(base), base_sha256=base_sha, base_manifest_status=bman.get('status'),
               base_chain='base is the installed AIN' if base_sha == live_ain else 'base is a staged candidate over the installed AIN',
               live_sha256=live_ain, live_manifest_sha256=cur['manifest_sha256'], source_sha256=base_sha,
               board_source=str(src_jaf), board_source_sha256=L.sha(src_jaf),
               files={n: dict(sha256=L.sha(out / 'candidate' / n), size=(out / 'candidate' / n).stat().st_size) for n in ('NightRemaster.ain', 'winmm.dll')},
               changed_functions=[BOARD], added_functions=added, rule=dict(cols=6, x=28, font=20, story_width='1064/20-1 = 52',
               story_y='max(grid bottom, field bottom) + 16', height='story bottom + 92', divider='grid / field bottom'),
               prediction=str(pred) if pred.exists() else None, prediction_sha256=L.sha(pred) if pred.exists() else None,
               gates=dict(readable_source_equals_base_function=True, edits_applied_once=len(EDITS), metadata_changed=[BOARD],
                          pinned_unchanged=list(L.PINNED_ALL), original_code_prefix_exact=True, original_strings_prefix_exact=True,
                          messages_exact=True, native_opcodes_supported=True, forwarder_one_call=True, dll_unchanged=True),
               summary_layers=bman.get('summary_layers', []), effective_summaries=bman.get('effective_summaries'),
               board_layers=list(bman.get('board_layers', [])) + [dict(tag='SB29', candidate=str(cand))],
               story_getter=bman.get('story_getter', 'KR_W29Story'), serialized_schema_changes=0, installed=False, time=now, author=T.AUTHOR)
    T.writej(out / 'candidate/manifest.json', man)
    print(json.dumps(dict(candidate=str(cand), sha256=man['files']['NightRemaster.ain']['sha256'], status=status, added=added), ensure_ascii=False))
    return man


if __name__ == '__main__':
    main()
