"""Native probe of the KR_G25 gallery unlock (Claude Opus 5.5 (claude-opus-5-5), 2026-09-30): muted, isolated copies.

  python probe_gallery_unlock.py --build-only     compile both probe AINs (candidate / installed), no game run
  python probe_gallery_unlock.py                  both runs (candidate, then the installed AIN as the reference) + comparison

The launcher / run folder / save folder / screenshot plumbing is the r24 chart probe's (probe_chart_r24.py, imported read only;
its module globals are re-pointed into this folder): probe/run = a copy of the runtime (big archives hard-linked read only,
private save folder type 2 inside probe/run, global records = the r24 COPIES of the user's), a hidden window parked off the
desktop, the engine's error handler and MessageBoxA break-pointed. The user's save folder is only hashed (before / after).
The probe AIN = the target AIN + probe_gallery_unlock.jaf + instrumentation: MAIN -> KR_G25PMain (muted, then the original
main), SetMute forced, every C_UserInputManager::Is* false, prefixes KR_CTitleTick <- KR_G25PTitle, C_SceneModeScene@Update
<- KR_G25PScene, C_SceneModeCG@Update <- KR_G25PCG, C_SelectDialog@_Update <- KR_G25PDialog, ■選択メッセージ／選択肢追加 <-
KR_G25PChoiceSeen, ■選択メッセージ／実行 -> the first choice; the message key wait -> click-through; every other
AFL_Parts_WaitForClick site except the title's, the select dialog's, the recollection top / select views' and the CG screen's
-> log + exit 6. Clicks are the game's own path: a frame handler ends the wait with the code a click would give.
Results: evidence/native_probe.json, evidence/native_candidate/*.png, evidence/native_installed/*.png.
"""
from pathlib import Path
import argparse, datetime, json, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import g25lib as G
L = G.L
sys.path.insert(0, str(G.F))
import probe_chart_r24 as P            # read-only reference: setup_folder / one_run / launch / collect_shots / diff_pixels / user_state
import g25vm as V
EVENT_CG = G.readj(Path('P:/AI/Codex/projects/YoruGaKuru_flowchart_20260922/graph/event_cg.json'))    # read only: CGs each scene shows

PROBE = H / 'probe'
RUN = PROBE / 'run'
JAF = H / 'probe_gallery_unlock.jaf'
LIVE_WAITS = ['C_SelectDialog@Run', 'C_SceneTitle@Run', 'C_SceneModeScene@RunTop', 'C_SceneModeScene@RunSelect', 'C_SceneModeCG@Run']
TARGETS = {
    'candidate': dict(ain=H / 'candidate/NightRemaster.ain', meta=H / 'work/build/candidate_meta.json',
                      raw=H / 'work/build/candidate_raw_code.jam', all='return KR_G25All();',
                      cache='return SystemService.SystemVariable_Get("YoruKR.G25.All");'),
    'installed': dict(ain=H / 'source/NightRemaster.ain', meta=H / 'source/base_meta.json', raw=H / 'source/base_raw_code.jam',
                      all='return -1;', cache='return "-";'),
}


def configure():
    P.PROBE = PROBE
    P.RUN = RUN
    P.O = H / 'candidate'
    L.BASE_WINMM_SHA = G.LIVE_WINMM                          # the layer keeps the installed winmm.dll
    assert P.EXE_SHA == G.LIVE_EXE
    PROBE.mkdir(parents=True, exist_ok=True)
    sm = L.WORK / 'savecopy_manifest.json'                   # the r24 map of the global-record COPIES (read only sources)
    src = G.F / 'work/savecopy_manifest.json'
    if not sm.exists():
        shutil.copy2(src, sm)
    assert L.sha(sm) == L.sha(src)


def build_probe(target, mode):
    t = TARGETS[target]
    src = t['ain']
    m = L.read_meta(t['meta'])
    names = G.names_of(m)
    assert not any(n.startswith('KR_G25P') for n in names)
    jaf = JAF.read_text('utf-8').replace('@@ALL@@', t['all']).replace('@@CACHE@@', t['cache']).replace('@@MODE@@', f'{mode} {target}')
    assert '@@' not in jaf
    work = PROBE / f'build_{target}'
    work.mkdir(parents=True, exist_ok=True)
    (work / 'probe_readable.jaf').write_text(jaf, 'utf-8')
    (work / 'probe.jaf').write_text(L.jaf_literal_encode(L.strip_comments(jaf)), 'utf-8')
    decl = work / 'probe_declared.ain'
    L.cmd('ain', 'edit', '--jaf', work / 'probe.jaf', '-o', decl, src, timeout=900)
    L.cmd('ain', 'dump', '-j', '-o', work / 'probe_declared_meta.json', decl, timeout=900)
    dm = L.read_meta(work / 'probe_declared_meta.json')
    added = dm['functions'][len(m['functions']):]
    ids = {f['name']: f['index'] for f in added}
    patch = []
    f = next(f for f in m['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    patch.append(f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\nENDFUNC config::detail::SetMute\n")
    patch += [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n" for f in m['functions']
              if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0] == 47]
    for f in added:
        path = work / f"probe_{f['index']}.jam"
        L.cmd('ain', 'dump', '--function', f['name'], '-o', path, decl)
        patch.append(G.lowered(path, f['name']))

    def prefix(name, code):
        fid = L.fid_of(m, name)
        path = work / f'original_{fid}.jam'
        L.cmd('ain', 'dump', '--function', L.symbol(m, fid), '-o', path, src)
        patch.append(L.begin(L.clean(path.read_text('utf8'), name), code))
    prefix('KR_CTitleTick', '\tCALLFUNC KR_G25PTitle\n')
    prefix('C_SceneModeScene@Update', '\tCALLFUNC KR_G25PScene\n')
    prefix('C_SceneModeCG@Update', '\tCALLFUNC KR_G25PCG\n')
    prefix('C_SelectDialog@_Update', '\tCALLFUNC KR_G25PDialog\n')
    prefix('■選択メッセージ／選択肢追加', '\t.LOCALREF 番号\n\tCALLFUNC KR_G25PChoiceSeen\n')
    run = L.fid_of(m, '■選択メッセージ／実行')
    patch.append(f"FUNC {run}\n\t.LOCALREF bキャンセル\n\t.LOCALREF n時間\n\tCALLFUNC KR_G25PChoice\n\tRETURN\nENDFUNC ■選択メッセージ／実行\n")
    (work / 'probe.jam').write_text('\n'.join(patch), 'utf8')
    out = RUN / 'NightRemaster.ain'
    L.cmd('ain', 'edit', '--jam', work / 'probe.jam', '-o', out, decl, timeout=900)
    raw = bytearray(L.unpack(out.read_bytes()))
    size = struct.unpack_from('<I', raw, 12)[0]
    struct.pack_into('<I', raw, 24 + size, m['functions'][0]['address'])
    struct.pack_into('<I', raw, raw.index(b'MAIN') + 4, ids['KR_G25PMain'])
    wait = L.fid_of(m, 'AFL_Parts_WaitForClick')
    waits = []
    for ad, op, owner in G.live_instructions(m, t['raw']):
        if op != f'CALLFUNC 0x{wait:x}':
            continue
        name = names[owner]
        assert raw[16 + ad:16 + ad + 6] == struct.pack('<Hi', 0x30, wait)
        if name in LIVE_WAITS:
            waits.append((name, 'live', ad))
            continue
        # the message key wait: the r24 probe named it after the nested lambda its dump order suggests; with the FUNC / ENDFUNC
        # nesting the call sits after the lambda bodies, in ExecuteKeyWait itself (same site 0x25db2a)
        msg = name.startswith(P.MSG_LAMBDA) or name == 'message::detail::CMessageTextView@ExecuteKeyWait'
        target_fid = ids['KR_G25PMsgWait'] if msg else ids['KR_G25PWait']
        struct.pack_into('<Hi', raw, 16 + ad, 0x30, target_fid)
        waits.append((name, 'message click-through' if target_fid == ids['KR_G25PMsgWait'] else 'exit', ad))
    live = sorted(n for n, k, _ in waits if k == 'live')
    assert live == sorted(LIVE_WAITS), live
    assert sum(1 for _, k, _ in waits if k.startswith('message')) == 1, [w for w in waits if w[1].startswith('message')]
    out.write_bytes(L.pack(bytes(raw), src.read_bytes()[:8]))
    info = dict(target=target, target_sha256=L.sha(src), probe_sha256=L.sha(out), wait_sites=len(waits), live=live,
                probe_functions=len(ids))
    G.writej(work / 'probe_build.json', dict(info, waits=[dict(function=n, kind=k, site=hex(a)) for n, k, a in waits]))
    return info


def parse(log):
    out = dict(mem={}, cg={}, flags={}, globals={}, labels={}, chart=[], board=[], play=[], mempage=[], chosen=None, dialogs=[])
    i = 0
    while i < len(log):
        line = log[i]
        z = re.match(r'MEMTABLE (\w+) open=(\d+)/(\d+) (.*)$', line)
        if z:
            out['mem'][z[1]] = dict(open=int(z[2]), all=int(z[3]), rows=dict(x.split('=') for x in z[4].split()))
        z = re.match(r'CGTABLE (\w+) cells=(\d+)/(\d+) cgs=(\d+)/(\d+) bits=(\d*) counts=(\d*)$', line)
        if z:
            out['cg'][z[1]] = dict(cells_open=int(z[2]), cells=int(z[3]), cgs_enabled=int(z[4]), cgs=int(z[5]), bits=z[6], counts=z[7])
        z = re.match(r'FLAG (\w+) file=(-?\d+) g25all=(-?\d+) cache=(\S*) open=(\S*)$', line)
        if z:
            out['flags'][z[1]] = dict(file=int(z[2]), g25all=int(z[3]), cache=z[4], open=z[5])
        z = re.match(r'GLOBAL (\w+) open=(\S*) count=(\d+)(.*)$', line)
        if z:
            out['globals'][z[1]] = dict(open=z[2], count=int(z[3]), cells=z[4].split())
        if line.startswith('LABELS ') and line.endswith('<<<'):
            j = log.index('>>>', i)
            out['labels'][line.split()[1]] = log[i + 1:j]
            i = j
        if line.startswith('DIALOG ') and line.endswith('<<<'):
            j = log.index('>>>', i)
            out['dialogs'].append(dict(phase=line.split()[1], text='\n'.join(log[i + 1:j])))
            i = j
        if line.startswith('CHART '):
            out['chart'].append(line)
        if line.startswith('BOARD '):
            out['board'].append(line)
        if line.startswith(('PLAY ', 'RETURNED', 'NOT PLAYED', 'REPLAY ', 'CHOICE ')):
            out['play'].append(line)
        if line.startswith('MEMPAGE '):
            out['mempage'].append(line)
        if line.startswith('CHOSEN '):
            out['chosen'] = line
        i += 1
    return out


def one(target, stamp, timeout):
    info = build_probe(target, 'tour')
    r = P.one_run('title', stamp, timeout=timeout)
    r['probe'] = info
    r['shots'] = P.collect_shots(f'native_{target}')
    log = r['log']
    r['parsed'] = parse(log)
    r['bad_lines'] = [x for x in log if x.startswith(('UNEXPECTED', 'STUCK', 'TOO MANY', 'MESSAGE WAIT outside'))]
    r['ok_run'] = (r.get('exit_code') == 0 and 'END' in log and not r['bad_lines']
                   and not any(k in r for k in ('vm_error', 'message', 'timeout')))
    return r


def compare(rc, ri):
    """Candidate vs installed: tables, read marks, labels, pixels."""
    pc, pi = rc['parsed'], ri['parsed']
    checks = {}
    fails = []

    def check(name, ok, detail=None):
        checks[name] = dict(ok=bool(ok), detail=detail)
        if not ok:
            fails.append(name)
    check('runs completed (exit 0, END, no engine error / unexpected wait)', rc['ok_run'] and ri['ok_run'],
          dict(candidate=[rc.get('exit_code'), rc.get('vm_error'), rc.get('message'), rc['bad_lines'][:3]],
               installed=[ri.get('exit_code'), ri.get('vm_error'), ri.get('message'), ri['bad_lines'][:3]]))
    check('A (flag 0): recollection table = installed', pc['mem'].get('A') == pi['mem'].get('A'), [pc['mem'].get('A'), pi['mem'].get('A')])
    check('A (flag 0): CG table = installed', pc['cg'].get('A') == pi['cg'].get('A'), [pc['cg'].get('A'), pi['cg'].get('A')])
    mb = pc['mem'].get('B', {})
    check('B (flag 1): every recollection slot open', mb and mb['open'] == mb['all'] == pc['mem']['A']['all'], mb)
    cb = pc['cg'].get('B', {})
    check('B (flag 1): every CG cell open, every CG enabled', cb and cb['cells_open'] == cb['cells'] and cb['cgs_enabled'] == cb['cgs'], cb)
    check('B installed: unchanged by the flag (= its A)', pi['mem'].get('B') == pi['mem'].get('A') and pi['cg'].get('B') == pi['cg'].get('A'))
    fb, fcn = pc['flags'].get('B_notice', {}), pc['flags'].get('C_notice', {})
    check('flag / cache follow the menu requests', fb.get('file') == 1 and fb.get('g25all') == 1 and fb.get('cache') == '1'
          and fcn.get('file') == 0 and fcn.get('g25all') == 0 and fcn.get('cache') == '0', dict(B=fb, C=fcn))
    chart_in = [x for x in pc['chart'] if x.startswith('CHART b ') and 'active=1' in x]
    chart_out = [x for x in pc['chart'] if 'closed' in x]
    check('KR_G25All is 0 while the calendar is open, 1 again after', chart_in and 'g25all=0' in chart_in[0] and chart_out and 'g25all=1' in chart_out[0],
          pc['chart'])
    g_c, g_i = pc['globals'], pi['globals']
    same = all(g_c.get(k, {}).get('cells') == g_c['A_title']['cells'] for k in ('B_title', 'b_in_chart'))
    check('calendar read marks (915 cells) identical in A, B (title) and B (inside the chart)', same,
          {k: v['count'] for k, v in g_c.items()})
    check('calendar read marks = installed (A, B, inside the chart)',
          all(g_c.get(k, {}).get('cells') == g_i.get(k, {}).get('cells') for k in ('A_title', 'B_title', 'b_in_chart')),
          dict(candidate={k: v['count'] for k, v in g_c.items()}, installed={k: v['count'] for k, v in g_i.items()}))
    check('in-game calendar labels of recollection-linked scenes: B = A and = installed',
          pc['labels'].get('B_title') == pc['labels'].get('A_title') == pi['labels'].get('B_title') == pi['labels'].get('A_title'),
          dict(lines=len(pc['labels'].get('A_title') or [])))
    check('board lines identical (unread summary hidden, read shown)', pc['board'] == pi['board'], dict(candidate=pc['board'], installed=pi['board']))
    played = [x for x in pc['play'] if x.startswith('RETURNED')]
    check('B: an originally locked recollection scene was judged open and replayed (messages clicked through)',
          any('judged=1' in x for x in pc['play']) and played and 'msgs=0' not in played[0] and 'NOT PLAYED' not in pc['play'], pc['play'])
    check('installed B: the same scene stays locked (ExecScene refuses, nothing played)',
          any('judged=0' in x for x in pi['play']) and 'NOT PLAYED' in pi['play'], pi['play'])
    ma, mc = pc['mem'].get('A', {}), pc['mem'].get('C', {})
    diff_c = {p: (ma['rows'][p], mc['rows'][p]) for p in ma.get('rows', {}) if mc.get('rows', {}).get(p) != ma['rows'][p]}
    check('C (flag 0 again): locked again (= A except slots the replay itself registered)', mc and mc['open'] <= ma['open'] + 1,
          dict(A=ma.get('open'), C=mc.get('open'), rows_changed=diff_c))
    # the replay itself shows the scene's gallery CGs and the game registers them (PassRegister 0), as every replay does since r22:
    # C may exceed A exactly by those CGs (cells of the CG閲覧 table that hold them), nothing else
    fn = next((re.search(r'fn=E(\d+)', x) for x in pc['play'] if x.startswith('REPLAY first message')), None)
    played = int(fn[1]) if fn else None
    shown = set(EVENT_CG['events'].get(str(played), {}).get('gallery', [])) if played else set()
    tables = V.ex_tables()
    want = {i: len([c for c in row['cgs'] if c in shown]) for i, row in enumerate(tables['cg']) if set(row['cgs']) & shown}
    ca, cc = pc['cg'].get('A', {}), pc['cg'].get('C', {})
    delta = {i: int(y) - int(x) for i, (x, y) in enumerate(zip(ca.get('counts', ''), cc.get('counts', ''))) if x != y}
    ok = bool(ca and cc and ca.get('counts') and len(ca['counts']) == len(cc.get('counts', '')))
    if ok:
        bits_changed = [i for i, (x, y) in enumerate(zip(ca['bits'], cc['bits'])) if x != y]
        ok = all(i in want for i in bits_changed) and all(0 < d <= want.get(i, 0) for i, d in delta.items())
    check('C (flag 0 again): CG table = A except the CGs the replayed scene itself showed', ok,
          dict(played=played, scene_gallery_cgs=sorted(shown), delta_per_cell=delta, allowed=want,
               A=dict(cells=ca.get('cells_open'), cgs=ca.get('cgs_enabled')), C=dict(cells=cc.get('cells_open'), cgs=cc.get('cgs_enabled'))))
    notes = [d['text'] for d in pc['dialogs'] if d['phase'] == 'unlock']
    check('the unlock notice shows the new text', notes and '회상·CG도' in notes[0], notes)
    notes_i = [d['text'] for d in pi['dialogs'] if d['phase'] == 'unlock']
    check('installed notice keeps the old text (reference)', notes_i and '회상·CG도' not in notes_i[0], notes_i)
    rv, rv_i = [d['text'] for d in pc['dialogs'] if d['phase'] == 'revert'], [d['text'] for d in pi['dialogs'] if d['phase'] == 'revert']
    check('the revert notice is unchanged', rv == rv_i and rv, rv)
    # pixels (same screen on both runs)
    dc, di = L.EVID / 'native_candidate', L.EVID / 'native_installed'
    px = {}
    for png in sorted(dc.glob('g25_*.png')):
        other = di / png.name
        px[png.name] = P.diff_pixels(png, other) if other.exists() else None
    must_equal = [n for n in px if n.startswith(('g25_a_', 'g25_b_chart_', 'g25_b_title')) or n in ('g25_c_title_end.png',)]
    check('pixels identical: all of A (flag 0), the calendar recollection tab and boards under 전체 개방, the title',
          all(px[n] == 0 for n in must_equal), {n: px[n] for n in must_equal})
    must_differ = [n for n in px if n.startswith(('g25_b_memory_page', 'g25_b_cg_p', 'g25_b_unlock_notice'))]
    assert len(must_differ) == 5, must_differ
    check('pixels differ where the flag opens the galleries (B recollection page, B CG pages, the notice)',
          all(px[n] and px[n] > 0 for n in must_differ), {n: px[n] for n in must_differ})
    return checks, fails, px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build-only', action='store_true')
    ap.add_argument('--timeout', type=int, default=1500)
    a = ap.parse_args()
    cur, rt, got = G.assert_live()
    man = G.readj(H / 'candidate/manifest.json')
    assert L.sha(H / 'candidate/NightRemaster.ain') == man['files']['NightRemaster.ain']['sha256']
    configure()
    if a.build_only:
        RUN.mkdir(parents=True, exist_ok=True)
        infos = {t: build_probe(t, 'build-only') for t in TARGETS}
        for p in RUN.glob('NightRemaster.ain'):
            p.unlink()
        G.writej(H / 'evidence/probe_build_only.json', dict(author=G.AUTHOR, builds=infos, note='compiled only, not launched'))
        print(json.dumps(infos, ensure_ascii=False, indent=1))
        return
    free = shutil.disk_usage('P:\\').free
    assert free >= 10 * 1024 ** 3, ('P: free space below 10 GB', free)
    before = P.user_state()
    playing = P.user_game_running()
    t0 = time.time()
    P.setup_folder()
    results = {}
    for target in ('candidate', 'installed'):
        dest = L.EVID / f'native_{target}'
        if dest.exists():
            shutil.rmtree(dest)
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        r = one(target, stamp, a.timeout)
        results[target] = r
        print(target, 'exit', r.get('exit_code'), r.get('vm_error'), r.get('message'), r['seconds'], 's', 'bad', r['bad_lines'][:3], flush=True)
    after = P.user_state()
    checks, fails, px = compare(results['candidate'], results['installed'])
    changed = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
    rep = dict(author=G.AUTHOR, time=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
               candidate_sha256=man['files']['NightRemaster.ain']['sha256'], installed_sha256=G.LIVE_AIN,
               seconds=round(time.time() - t0, 1), user_save_files=len(before), user_files_changed=changed,
               user_game_running=bool(playing or P.user_game_running()), audio=P.AUDIO_POLICY,
               checks=checks, failures=fails, pixels=px,
               runs={t: {k: v for k, v in r.items() if k not in ('events',)} for t, r in results.items()})
    rep['status'] = 'GALLERY_UNLOCK_NATIVE_PASS' if not fails and not changed else 'FAIL'
    G.writej(H / 'evidence/native_probe.json', rep)
    print(json.dumps(dict(status=rep['status'], failures=fails, user_files_changed=changed[:5], seconds=rep['seconds']), ensure_ascii=False))
    for k, v in checks.items():
        print(('PASS ' if v['ok'] else 'FAIL ') + k)
    assert rep['status'] == 'GALLERY_UNLOCK_NATIVE_PASS'


if __name__ == '__main__':
    main()
