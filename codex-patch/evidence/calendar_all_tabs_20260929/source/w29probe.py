"""WI-009 probe plumbing (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29): the r24 probe (probe_chart_r24, read-only reference)
pointed at a folder of this staging, with the read fixture and the detail-board wait hook added to its instrumentation.

Everything a run writes stays under staging/calendar_all_tabs_20260929 (probe folder, run copy with hard-linked read-only big
assets, private save folder type 2). The user's save folder is only hashed before / after."""
from pathlib import Path
import inspect, re, shutil, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import w29common as C
import probe_chart_r24 as P
L = P.L
O = C.O
BASE_LIVE_WAITS = list(P.LIVE_WAITS)
BASE_PROBE_JAF = P.PROBE_JAF
BASE_BUILD_SOURCE = inspect.getsource(P.build_probe)
DIALOG_ANCHOR = 'KR_P22Block("DIALOG", ph, title + "\\nITEMS " + KR_P22Get("Items"));'
BUILD_ANCHOR = "    prefix('KR_C24Frame', '\\tCALLFUNC KR_P22ChartTick\\n')"

FIXTURE_PATCH = r'''
    # WI-009 probe instrumentation: KR_CGlobal / KR_P29Read -> the fixture (@@GLOBAL@@ / @@READ@@), @@FRAME@@
    path = work / 'original_global.jam'
    L.cmd('ain', 'dump', '--function', 'KR_CGlobal', '-o', path, src)
    a = m['functions'][L.fid_of(m, 'KR_CGlobal')]
    b = dm['functions'][ids['@@GLOBAL@@Base']]
    assert a['arguments'] == b['arguments'] and a['variables'] == b['variables'], (a, b)
    body = L.clean(path.read_text('utf8'), 'KR_CGlobal')
    body = re.sub(r'^FUNC \d+', f"FUNC {ids['@@GLOBAL@@Base']}", body, flags=re.M).replace('ENDFUNC KR_CGlobal', 'ENDFUNC @@GLOBAL@@Base')
    patch = [v for v in patch if 'ENDFUNC @@GLOBAL@@Base' not in v]
    patch.append(body)
    for old, new in [('KR_CGlobal', '@@GLOBAL@@'), ('KR_P29Read', '@@READ@@')]:
        patch.append(f"FUNC {L.fid_of(m, old)}\n\t.LOCALREF no\n\tCALLFUNC {new}\n\tRETURN\nENDFUNC {old}\n")
    @@FRAME@@
'''


def configure(probe_dir, ain_dir, work_dir, tour_jaf, boot_call, dialog_hook, fixture=('KR_W29PGlobal', 'KR_W29PRead'),
              frame_prefix='KR_W29PFrame'):
    """Point the r24 probe at probe_dir (run copy + build), the AIN in ain_dir (its meta / raw dump in work_dir/build) and add
    the tour. Returns the instrumented build_probe namespace (P)."""
    assert Path(probe_dir).resolve().is_relative_to(O.resolve()) and Path(work_dir).resolve().is_relative_to(O.resolve())
    L.WORK = Path(work_dir)
    L.EVID = O / 'evidence'
    L.TMP = O / 'work/tmp'
    L.WORK.mkdir(parents=True, exist_ok=True)
    shutil.copy2(C.F / 'work/savecopy_manifest.json', L.WORK / 'savecopy_manifest.json')
    P.O = Path(ain_dir)
    P.PROBE = Path(probe_dir)
    P.RUN = P.PROBE / 'run'
    L.BASE_WINMM_SHA = C.BASE_DLL
    P.LIVE_WAITS = BASE_LIVE_WAITS + ['KR_P29WaitRaw']
    jaf = BASE_PROBE_JAF + '\n' + tour_jaf
    jaf = jaf.replace('        @@BOOT@@', '        ' + boot_call + '\n        @@BOOT@@')
    assert jaf.count(DIALOG_ANCHOR) == 1
    jaf = jaf.replace(DIALOG_ANCHOR, DIALOG_ANCHOR + '\n' + dialog_hook)
    P.PROBE_JAF = jaf
    frame = f"prefix('KR_P29Frame', '\\tCALLFUNC {frame_prefix}\\n')" if frame_prefix else 'pass'
    insert = FIXTURE_PATCH.replace('@@GLOBAL@@', fixture[0]).replace('@@READ@@', fixture[1]).replace('@@FRAME@@', frame)
    source = BASE_BUILD_SOURCE
    assert source.count(BUILD_ANCHOR) == 1
    source = source.replace(BUILD_ANCHOR, BUILD_ANCHOR + '\n' + insert)
    P.PROBE.mkdir(parents=True, exist_ok=True)
    (P.PROBE / 'build_probe_instrumentation.py').write_text(source, 'utf-8')
    exec(compile(source, 'w29_probe_instrumentation', 'exec'), P.__dict__)
    orig = P.setup_folder

    def setup():
        assert P.RUN.resolve().is_relative_to(O.resolve())
        return orig()
    P.setup_folder = setup
    return P


def run(P, tag, timeout):
    """setup the run copy, build the probe AIN, one muted private run, collect the shots into evidence/<tag>."""
    import datetime
    assert shutil.disk_usage('P:\\').free >= 8 * 1024 ** 3, 'P: free space below 8 GB'
    before = P.user_state()
    playing = P.user_game_running()
    rt = P.setup_folder()
    info = P.build_probe('title')
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    r = P.one_run('title', stamp, timeout=timeout)
    r['probe'] = info
    r['shots'] = P.collect_shots(tag)
    r['candidate_sha256'] = L.sha(P.O / 'NightRemaster.ain')
    after = P.user_state()
    r['user_files_changed'] = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
    r['user_game_running'] = bool(playing or P.user_game_running())
    r['time'] = stamp
    return r
