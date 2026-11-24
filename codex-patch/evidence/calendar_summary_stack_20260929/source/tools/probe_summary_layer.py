"""Native probe of a summary-layer candidate (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29): one muted private run.

  python probe_summary_layer.py --out <layer staging folder> [--ids N ...] [--shots 5] [--timeout 1800] [--build-only]

The April summary probe generalized (staging/calendar_april_summary_20260929/source/probe_calendar_april_summary_20260929.*):
read fixture KR_CGlobal -> KR_SLPGlobal (clone of KR_CGlobal + all / none mode, no April guard), KR_P29Read -> KR_SLPRead.
IDs default to the layer's manifest (summary_ids); --ids narrows them. Checked on every ID (scene page) and every group card whose
first scene is one of them (card page), plus control scenes (an April summary, E00011, one scene without a summary), in three
fixtures (read + 전체 개방, unread + 전체 개방, unread + locked): the summary exists iff read (and written), characters kept
(spaces aside), <= 5 lines, board <= 680, right-column width, 12px above the buttons, heading position, portraits and centred
names, E number, replay button. Logs `SUMMARY <page> E<no> lines height gap`; a few representative screenshots.

--build-only: no game, no run copy: only the probe AIN is built (the JAF tour declared with `ain edit --jaf` on the candidate +
the instrumentation jam) into <out>/probe/build_only/. That is the syntax / declaration test before a real run.
A real run needs >= 10 GB free on P: and the user's game closed (both asserted); it copies the runtime into <out>/probe/run (big
assets hard-linked read-only), uses a private save folder (type 2) and only hashes the user's save folder. Results: <out>/evidence/native_summary_probe.json, <out>/evidence/native_summary/*.png.
"""
from pathlib import Path
import argparse, datetime, inspect, json, re, shutil, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import sltools as T
import probe_chart_r24 as P          # read-only reference (r24 probe plumbing); only module globals are re-pointed
L = P.L
BASE_LIVE_WAITS = list(P.LIVE_WAITS)
BASE_PROBE_JAF = P.PROBE_JAF
BASE_BUILD_SOURCE = inspect.getsource(P.build_probe)
BASE_SETUP = P.setup_folder          # the r24 original (configure() wraps it again for every run folder)
BUILD_ANCHOR = "    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')"
FIXTURE_PATCH = r'''
    # summary-layer probe instrumentation: KR_CGlobal -> KR_SLPGlobal (clone in KR_SLPGlobalBase), KR_P29Read -> KR_SLPRead
    path = work / 'original_global.jam'
    L.cmd('ain', 'dump', '--function', 'KR_CGlobal', '-o', path, src)
    a = m['functions'][L.fid_of(m, 'KR_CGlobal')]
    b = dm['functions'][ids['KR_SLPGlobalBase']]
    assert a['arguments'] == b['arguments'] and a['variables'] == b['variables'], (a, b)
    body = L.clean(path.read_text('utf8'), 'KR_CGlobal')
    body = re.sub(r'^FUNC \d+', f"FUNC {ids['KR_SLPGlobalBase']}", body, flags=re.M).replace('ENDFUNC KR_CGlobal', 'ENDFUNC KR_SLPGlobalBase')
    patch = [v for v in patch if 'ENDFUNC KR_SLPGlobalBase' not in v]
    patch.append(body)
    for old, new in [('KR_CGlobal', 'KR_SLPGlobal'), ('KR_P29Read', 'KR_SLPRead')]:
        patch.append(f"FUNC {L.fid_of(m, old)}\n\t.LOCALREF no\n\tCALLFUNC {new}\n\tRETURN\nENDFUNC {old}\n")
'''
q = lambda s: json.dumps(s, ensure_ascii=False)
LISTED = [201, 181, 182, 97, 107, 50408, 60006, 60008, 60009, 60205, 40145, 901, 984, 985, 328, 523, 524]   # coordinator 09-29


def fn(ret, name, var, pairs, default):
    body = [f'{ret} {name}(int {var}) {{']
    for k, v in pairs:
        body.append(f'    if ({var} == {k}) return {v};')
    body.append(f'    return {default};\n}}')
    return '\n'.join(body)


def chain_copies(man):
    """copy_of rows of every summary layer in the chain (from each layer's design/summaries_baked.json)."""
    out = {}
    for lay in man.get('summary_layers', []):
        f = Path(lay['candidate']).parent.parent / 'design/summaries_baked.json'
        for e in T.readj(f)['events']:
            if e['kind'] == 'copy_of':
                out[e['no']] = e['copy_of']
    return out


def plan(out, only=None, shots=5, all_events=False):
    """Everything the tour needs, from the layer's manifest / design files (no AIN access). all_events: every calendar event as a
    scene page and every group card as a card page, expectations from the chain's effective summaries (E00011 = pre-existing)."""
    man = T.readj(out / 'candidate/manifest.json')
    baked = T.readj(out / 'design/summaries_baked.json')
    eff = {int(k): v for k, v in T.readj(out / 'design/effective_summaries.json')['texts'].items()}
    texts = {e['no']: e['summary'] for e in baked['events'] if e['kind'] == 'text'}
    copies = {e['no']: e['copy_of'] for e in baked['events'] if e['kind'] == 'copy_of'}
    controls = []
    if all_events:
        ids = sorted(T.all_event_ids())
        cc = chain_copies(man)
        expect = {n: eff.get(n, '') for n in ids}
        if 11 not in eff:
            expect[11] = '*'
        for n, o in cc.items():
            if o == 11:
                expect[n] = '*'
        cards = [c for c in T.cards() if c['size'] > 1]
        texts = {n: t for n, t in eff.items() if n in expect and n not in cc}
        copies = cc
    else:
        ids = sorted(set(texts) | set(copies))
        if only:
            assert set(only) <= set(ids), ('not in this layer', sorted(set(only) - set(ids)))
            ids = sorted(only)
        expect = {}
        for n in ids:
            if n in texts:
                expect[n] = texts[n]
            else:
                o = copies[n]
                expect[n] = texts.get(o, eff.get(o, '*'))
        cards = [c for c in T.cards() if c['size'] > 1 and c['entry'] in ids]
        april = T.april_texts()
        a0 = min(april)
        controls.append((a0, eff.get(a0, april[a0]) if a0 not in ids else expect[a0]))
        if 11 not in ids:
            controls.append((11, eff.get(11, '*')))
        below = set(eff) | {11} | set(ids)
        blank = next((n for n in sorted(T.all_event_ids()) if n not in below), None)
        if blank is not None:
            controls.append((blank, ''))
        controls = [(n, e) for n, e in controls if n not in ids]
        for n, e in controls:
            expect[n] = e
    tabs = T.tab_of()
    tab = tabs[ids[0]]
    # screenshots: longest / shortest text, a card page, a copy_of scene, the longest one unread (+ a 6-column board)
    tx = [n for n in ids if n in texts]
    pick = []
    if tx:
        longest = max(tx, key=lambda n: (len(texts[n]), n))
        shortest = min(tx, key=lambda n: (len(texts[n]), n))
        pick += [(longest, -1, 'all', 'read_longest'), (shortest, -1, 'all', 'read_shortest')]
    if cards:
        pick.append((cards[0]['entry'], cards[0]['k'], 'all', 'card_read'))
    cp = [n for n in ids if n in copies]
    if cp:
        pick.append((cp[0], -1, 'all', 'copy_read'))
    if tx:
        pick.append((longest, -1, 'none', 'unread'))
    tag = man['tag']
    # SB29 board layer in the chain: every 6-column board of the calendar (board_layer/predict_sb29.json: scene + card pages)
    wide = []
    has_board = bool(man.get('board_layers')) or any(c['manifest'].get('kind') == 'board_layer' for c in T.chain(out) if not c['foreign'])
    if has_board:
        pred = T.readj(T.TOOLS / 'board_layer/predict_sb29.json')
        for b in pred['boards']:
            k = int(b['page'].split()[1]) if b['page'].startswith('card') else -1
            wide.append((b['no'], k))
            expect.setdefault(b['no'], eff.get(b['no'], '?'))
        listed = [b for b in pred['boards'] if b['listed']]
        if listed:
            w = max(listed, key=lambda b: (b['old']['story_lines'], b['no']))
            pick.insert(0, (w['no'], int(w['page'].split()[1]) if w['page'].startswith('card') else -1, 'all', 'wide_read'))
    pick = [(n, k, mode, f'slp{tag}_E{n:05d}_{what}') for n, k, mode, what in pick[:max(0, shots)]]
    return dict(man=man, ids=ids, expect=expect, cards=cards, controls=controls, tab=tab, shots=pick, texts=texts, copies=copies,
                wide=wide, all_events=all_events, has_board=has_board)


def tour_jaf(pl):
    man = pl['man']
    tables = [
        f'int KR_SLPN() {{ return {len(pl["ids"])}; }}',
        fn('int', 'KR_SLPNo', 'j', list(enumerate(pl['ids'])), -1),
        fn('string', 'KR_SLPExpect', 'no', [(n, q(e)) for n, e in sorted(pl['expect'].items())], '""'),
        f'int KR_SLPCardN() {{ return {len(pl["cards"])}; }}',
        fn('int', 'KR_SLPCardK', 'j', [(j, c['k']) for j, c in enumerate(pl['cards'])], -1),
        f'int KR_SLPCtrlN() {{ return {len(pl["controls"])}; }}',
        fn('int', 'KR_SLPCtrlNo', 'j', [(j, n) for j, (n, _) in enumerate(pl['controls'])], -1),
        f'int KR_SLPShotN() {{ return {len(pl["shots"])}; }}',
        fn('int', 'KR_SLPShotNo', 'j', [(j, s[0]) for j, s in enumerate(pl['shots'])], -1),
        fn('int', 'KR_SLPShotK', 'j', [(j, s[1]) for j, s in enumerate(pl['shots'])], -1),
        fn('string', 'KR_SLPShotMode', 'j', [(j, q(s[2])) for j, s in enumerate(pl['shots'])], '"all"'),
        fn('string', 'KR_SLPShotName', 'j', [(j, q(s[3])) for j, s in enumerate(pl['shots'])], '"slp_shot"'),
        'bool KR_SLPWideLayer() { return %s; }' % ('true' if pl['has_board'] else 'false'),
        'bool KR_SLPListPass() { return %s; }' % ('true' if pl['all_events'] else 'false'),
        f'int KR_SLPCopyN() {{ return {len(pl["copies"])}; }}',
        fn('int', 'KR_SLPCopyNo', 'j', [(j, n) for j, n in enumerate(sorted(pl['copies']))], -1),
        fn('int', 'KR_SLPCopyOrig', 'j', [(j, pl['copies'][n]) for j, n in enumerate(sorted(pl['copies']))], -1),
        f'int KR_SLPWideN() {{ return {len(pl["wide"])}; }}',
        fn('int', 'KR_SLPWideNo', 'j', [(j, n) for j, (n, _) in enumerate(pl['wide'])], -1),
        fn('int', 'KR_SLPWideK', 'j', [(j, k) for j, (_, k) in enumerate(pl['wide'])], -1),
    ]
    jaf = (H / 'probe_summary_layer.jaf').read_text('utf-8')
    assert jaf.count('/*TABLES*/') == 1
    jaf = (jaf.replace('/*TABLES*/', '\n\n'.join(tables)).replace('@@GETTER@@', man.get('text_getter', man['story_getter']))
           .replace('@@SHOWN@@', man.get('shown_getter', man['story_getter']))
           .replace('@@TAB@@', str(pl['tab'])).replace('@@TAG@@', man['tag']))
    assert '@@' not in jaf
    return jaf


def configure(out, run_dir, tour, boot='KR_SLPTour();'):
    """Point the r24 probe module at this layer folder and add the tour + the read fixture (as the April / WI-009 probes do)."""
    out = Path(out).resolve()
    assert Path(run_dir).resolve().is_relative_to(out)
    L.WORK = out / 'work'
    L.EVID = out / 'evidence'
    L.TMP = out / 'work/tmp'
    L.TMP.mkdir(parents=True, exist_ok=True)
    P.O = out / 'candidate'
    P.PROBE = Path(run_dir).parent
    P.RUN = Path(run_dir)
    L.BASE_WINMM_SHA = L.sha(out / 'candidate/winmm.dll')          # every layer keeps the installed winmm.dll
    P.LIVE_WAITS = BASE_LIVE_WAITS + ['KR_P29WaitRaw']
    jaf = BASE_PROBE_JAF + '\n' + tour
    assert jaf.count('        @@BOOT@@') == 1
    P.PROBE_JAF = jaf.replace('        @@BOOT@@', '        ' + boot + '\n        @@BOOT@@')
    source = BASE_BUILD_SOURCE
    assert source.count(BUILD_ANCHOR) == 1
    source = source.replace(BUILD_ANCHOR, BUILD_ANCHOR + '\n' + FIXTURE_PATCH)
    P.PROBE.mkdir(parents=True, exist_ok=True)
    (P.PROBE / 'build_probe_instrumentation.py').write_text(source, 'utf-8')
    P.__dict__['re'] = re
    exec(compile(source, 'summary_layer_probe_instrumentation', 'exec'), P.__dict__)
    orig = BASE_SETUP

    def setup():
        assert P.RUN.resolve().is_relative_to(out) and (P.RUN / 'KRMenu').resolve().is_relative_to(out)
        return orig()
    P.setup_folder = setup


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--ids', nargs='*', type=int)
    ap.add_argument('--shots', type=int, default=5)
    ap.add_argument('--timeout', type=int, default=1800)
    ap.add_argument('--build-only', action='store_true')
    ap.add_argument('--any-getter', action='store_true', help='allow a layer whose getter is not KR_W29Story (build-only tests)')
    ap.add_argument('--all-events', action='store_true', help='every calendar event + every group card (the final stacked candidate)')
    a = ap.parse_args(argv)
    out = T.assert_writable(a.out)
    man = T.readj(out / 'candidate/manifest.json')
    assert man.get('tool') == T.TOOL_NAME, 'not a summary-layer build'
    assert L.sha(out / 'candidate/NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256'], 'candidate differs from its manifest'
    for n in ('candidate_meta.json', 'candidate_raw_code.jam'):
        assert (out / 'work/build' / n).exists(), n
    pl = plan(out, a.ids, a.shots, a.all_events)
    tour = tour_jaf(pl)
    cm = L.read_meta(out / 'work/build/candidate_meta.json')
    names = [L.raw_symbol(cm, f['index']) for f in cm['functions']]
    assert man.get('text_getter', man['story_getter']) in ('KR_W29Story', 'KR_TF29StoryBase') or a.any_getter, \
        ('the detail board draws KR_W29Story (WI-009); a layer on another getter is not visible on every tab', man['story_getter'])
    assert not any(n.startswith('KR_SLP') for n in names), 'KR_SLP prefix already used in the candidate'
    if a.build_only:
        run = out / 'probe/build_only/run'
        run.mkdir(parents=True, exist_ok=True)
        configure(out, run, tour)
        (P.PROBE / 'tour_readable.jaf').write_text(tour, 'utf-8')
        info = P.build_probe('title')
        dm = L.read_meta(P.PROBE / 'build' / 'probe_declared_meta.json')
        added = [f['name'] for f in dm['functions'][len(names):]]
        want = {'KR_SLPTour', 'KR_SLPBoard', 'KR_SLPAll', 'KR_SLPGlobal', 'KR_SLPGlobalBase', 'KR_SLPRead', 'KR_SLPExpect', 'KR_SLPNo'}
        assert want <= set(added), sorted(want - set(added))
        rep = dict(mode='build-only (declaration + instrumentation, no game run)', author=T.AUTHOR, wide_boards=len(pl['wide']),
                   all_events=pl['all_events'],
                   time=datetime.datetime.now().astimezone().isoformat(), candidate_sha256=man['files']['NightRemaster.ain']['sha256'],
                   probe=info, declared_probe_functions=len(added), ids=len(pl['ids']), cards=len(pl['cards']),
                   controls=[n for n, _ in pl['controls']], shots=[s[3] for s in pl['shots']], tab=pl['tab'],
                   note='The probe AIN in probe/build_only/run is never installed and was not launched.')
        T.writej(out / 'evidence/probe_build_only.json', rep)
        print(json.dumps({k: v for k, v in rep.items() if k != 'probe'}, ensure_ascii=False))
        return rep
    # ---- real run (after the WI-009 candidate exists; see README): private muted copy, user saves hashed only
    cur = L.readj(L.CURRENT)
    assert L.sha(Path(cur['runtime']) / 'NightRemaster.ain') == man['live_sha256'], 'live AIN moved since the build'
    assert shutil.disk_usage('P:\\').free >= 10 * 1024 ** 3, 'P: free space below 10 GB (09-29 rule): write only, do not run'
    assert not P.user_game_running(), 'the user is playing (NightRemaster.exe of the live runtime is running): run the probe later'
    run = out / 'probe/run'
    configure(out, run, tour)
    (P.PROBE / 'tour_readable.jaf').write_text(tour, 'utf-8')
    L.WORK.mkdir(parents=True, exist_ok=True)
    shutil.copy2(T.F / 'work/savecopy_manifest.json', L.WORK / 'savecopy_manifest.json')
    before = P.user_state()
    playing = P.user_game_running()
    P.setup_folder()
    info = P.build_probe('title')
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    r = P.one_run('title', stamp, timeout=a.timeout)
    r['probe'] = info
    r['shots'] = P.collect_shots('native_summary')
    r['candidate_sha256'] = L.sha(P.O / 'NightRemaster.ain')
    after = P.user_state()
    r['user_files_changed'] = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
    r['user_game_running'] = bool(playing or P.user_game_running())
    log = r['log']
    r['fail_lines'] = [x for x in log if x.startswith('FAIL')]
    stats = {}
    for line in log:
        z = re.match(r'SUMMARY (scene|card|control|wide) E(\d+) lines=(\d+) height=(\d+) gap=(-?\d+)( wide)?', line)
        if z:
            key_ = f'{z[1]} {int(z[2])}'
            if z[1] == 'wide':
                key_ += f' #{sum(1 for x in stats if x.startswith(key_))}'
            stats[key_] = dict(lines=int(z[3]), board_height=int(z[4]), gap=int(z[5]), wide=bool(z[6]))
    r['summary_stats'] = stats
    r['ids'] = pl['ids']
    r['cards'] = [c['k'] for c in pl['cards']]
    r['controls'] = [n for n, _ in pl['controls']]
    r['lists'] = [x for x in log if x.startswith('LISTS')]
    r['copy_cast'] = [x for x in log if x.startswith('COPYCAST')]
    r['wide_boards'] = len(pl['wide'])
    r['all_events'] = pl['all_events']
    r['copies_checked'] = len(pl['copies'])
    r['wide_listed_17'] = {k: v for k, v in stats.items() if k.startswith('wide') and int(k.split()[1]) in LISTED}
    want = {f'scene {n}' for n in pl['ids'] if pl['expect'][n] != ''}
    r['missing_summary_logs'] = sorted(want - set(stats))
    r['author'] = T.AUTHOR
    r['time'] = stamp
    r['pass'] = (r.get('exit_code') == 0 and 'END' in log and not r['fail_lines'] and not any(k in r for k in ('vm_error', 'message', 'timeout'))
                 and not r['user_files_changed'] and not r['missing_summary_logs']
                 and all(v['lines'] <= 5 and v['board_height'] <= 680 and v['gap'] >= 12 for v in stats.values()))
    T.writej(out / 'evidence/native_summary_probe.json', r)
    print(json.dumps({k: v for k, v in r.items() if k not in ('events', 'probe', 'log', 'summary_stats')}, ensure_ascii=False, indent=1)[:4000])
    assert r['pass']
    return r


if __name__ == '__main__':
    main()
