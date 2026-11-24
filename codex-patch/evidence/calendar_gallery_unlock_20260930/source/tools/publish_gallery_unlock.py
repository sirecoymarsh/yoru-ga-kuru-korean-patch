"""Stopped-game-only install transaction of the KR_G25 gallery unlock (Claude Opus 5.5 (claude-opus-5-5), 2026-09-30).

  python publish_gallery_unlock.py --check      read-only preflight: every gate + every file the install copies; prints PREFLIGHT_PASS
  python publish_gallery_unlock.py --install    the install (only after the user's explicit permission; run by the coordinator)
  python publish_gallery_unlock.py --restore    exact pre-install bytes (journal-driven)

The summary-stack publisher (staging/calendar_summary_layer_tools_20260929/publish_summary_layer.py) for this layer:
KEY calendar_gallery_unlock_20260930, STATUS CALENDAR_GALLERY_UNLOCK_20260930_INSTALLED_NATIVE_PASS, evidence
<project>/evidence/<KEY>, contract <project>/required_<KEY>.json. Payload NightRemaster.ain (+ winmm.dll, byte-identical to the
installed one). Refuses: a candidate without GALLERY_UNLOCK_PREFLIGHT_PASS / Defender scan / transaction fixture for exactly these
bytes, a moved live build, a running game, an unexpected runtime tree, an existing journal, a missing install source.
--check runs every assertion --install runs before its first write, including the existence of every file it copies.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse, copy, datetime, hashlib, shutil, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import g25lib as G
L = G.L
sys.path.insert(0, str(G.F))
import publish_chart_r24 as P      # read-only reference: stopped / exact_tree / put / pair_apply / pair_restore / restore_ctx / js
R = L.CODEX
FILES = ['NightRemaster.ain', 'winmm.dll']
KEY, STATUS = G.KEY, G.STATUS_INSTALLED
E = R / 'evidence' / KEY
NEW = R / f'required_{KEY}.json'
TOOL_FILES = ['g25lib.py', 'g25vm.py', 'kr_g25_gallery_unlock.jaf', 'build_gallery_unlock.py', 'verify_gallery_unlock.py',
              'probe_gallery_unlock.py', 'probe_gallery_unlock.jaf', 'scan_gallery_unlock.ps1', 'preflight_gallery_unlock.py',
              'publish_gallery_unlock.py', '인계_갤러리개방.md']
SOURCE_RELS = ['candidate/manifest.json', 'candidate/scan_report.json', 'evidence/install_preflight.json', 'evidence/vm_verification.json',
               'evidence/native_probe.json', 'evidence/transaction_verification.json', 'design/sites.json',
               'work/build/helpers_readable.jaf', 'work/build/kr_msetunlock_r21_readable.jaf', 'work/build/native_opcode_audit.json',
               'source/source_pointer.json']


def gates():
    """Everything --install asserts before its first write. Returns the context the install uses."""
    man = G.readj(H / 'candidate/manifest.json')
    assert man.get('tool') == G.TOOL and man.get('kind') == 'gallery_unlock_layer', 'not a gallery-unlock build'
    after = {n: L.sha(H / 'candidate' / n) for n in FILES}
    assert after == {n: man['files'][n]['sha256'] for n in FILES}, 'candidate differs from its manifest'
    before = {'NightRemaster.ain': man['live_sha256'], 'winmm.dll': after['winmm.dll']}
    qa = G.readj(H / 'evidence/install_preflight.json')
    assert qa['status'] == 'GALLERY_UNLOCK_PREFLIGHT_PASS' and qa['files'] == after and qa['key'] == KEY, 'preflight missing / stale'
    for path, status in [(H / 'candidate/scan_report.json', 'SCANNED_NO_TARGET_DETECTIONS'),
                         (H / 'evidence/transaction_verification.json', 'TRANSACTION_FIXTURE_PASS')]:
        v = G.readj(path)
        assert v['status'] == status and v.get('payload', v.get('files')) == after, str(path)
    vm = G.readj(H / 'evidence/vm_verification.json')
    nat = G.readj(H / 'evidence/native_probe.json')
    assert vm['status'] == 'GALLERY_UNLOCK_VM_PASS' and vm['candidate_sha256'] == after['NightRemaster.ain']
    assert nat['status'] == 'GALLERY_UNLOCK_NATIVE_PASS' and nat['candidate_sha256'] == after['NightRemaster.ain']
    cur = L.readj(L.CURRENT)
    assert cur == G.readj(H / 'source/source_pointer.json'), 'Live build moved since staging: rebuild the layer'
    rt = Path(cur['runtime'])
    mp = Path(cur['manifest'])
    assert P.stopped(rt), 'Do not replace a running game'
    assert L.sha(mp) == cur['manifest_sha256']
    manifest = L.readj(mp)
    P.exact_tree(rt, manifest['files'])
    assert all(L.sha(rt / n) == h for n, h in before.items()), 'runtime files differ from the build base'
    latest = L.readj(R / 'latest_worked_translation.json')
    assert latest['manifest_sha256'] == cur['manifest_sha256'] and latest['ain_sha256'] == before['NightRemaster.ain']
    assert L.sha(Path(latest['translation_map'])) == latest['translation_map_sha256']
    # every file the transaction copies must exist now (the 09-30 00:12 lesson: --check must see what --install copies)
    missing = [rel for rel in SOURCE_RELS if not (H / rel).exists()]
    missing += ['tool ' + n for n in TOOL_FILES if not (H / n).exists()]
    shots = sorted((H / 'evidence/native_candidate').glob('*.png')) + sorted((H / 'evidence/native_installed').glob('*.png'))
    if not shots:
        missing.append('evidence/native_candidate/*.png')
    for n in FILES:
        if not (rt / n).exists():
            missing.append('runtime ' + n)
    assert not missing, ('install sources missing', missing)
    contracts = sorted(R.glob('required_*.json'))
    paths = [mp, L.CURRENT, R / 'progress.md', R / 'latest_worked_translation.json', NEW] + contracts
    assert len(paths) == len({x.name for x in paths})
    for p in paths:
        if p != NEW:
            assert p.exists(), ('metadata file missing', str(p))
    assert not E.exists() and not NEW.exists(), 'Inspect existing journal / contract (installed already?)'
    return SimpleNamespace(man=man, after=after, before=before, qa=qa, vm=vm, nat=nat, cur=cur, rt=rt, mp=mp, manifest=manifest,
                           latest=latest, contracts=contracts, paths=paths, shots=shots)


def install(c):
    snapshots = {p: p.read_bytes() if p.exists() else None for p in c.paths}
    for d in ['before', 'candidate', 'source', 'source/tools', 'screenshots/candidate', 'screenshots/installed']:
        (E / d).mkdir(parents=True)
    metadata = []
    for p, data in snapshots.items():
        if data is not None:
            P.put(E / 'before' / p.name, data)
        metadata.append(dict(path=str(p), name=p.name, existed=data is not None, sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    for n in FILES:
        shutil.copy2(c.rt / n, E / 'before' / n)
        shutil.copy2(H / 'candidate' / n, E / 'candidate' / n)
    for rel in SOURCE_RELS:
        shutil.copy2(H / rel, E / 'source' / Path(rel).name)
    for n in TOOL_FILES:
        shutil.copy2(H / n, E / 'source/tools' / n)
    for png in c.shots:
        shutil.copy2(png, E / 'screenshots' / png.parent.name.replace('native_', '') / png.name)
    saves = P.snapshot_folder(L.SAVES)
    menu = P.snapshot_folder(c.rt / 'KRMenu') if (c.rt / 'KRMenu').exists() else None
    P.put(E / 'save_hashes_before.json', P.js(saves))
    full = L.readj(Path(c.latest['translation_map']))
    full['installed_ain_sha256'] = c.after['NightRemaster.ain']
    full[KEY] = dict(evidence=str(E), semantic_dialogue_changes=0, text_changes=[dict(kind='menu notice', old=G.OLD_NOTE, new=G.NEW_NOTE)],
                     author=G.AUTHOR)
    translation = E / 'source/installed_translation_map.json'
    P.put(translation, P.js(full))
    journal = dict(status='PREPARED', runtime=str(c.rt), files=FILES, before=c.before, after=c.after, metadata=metadata)
    P.put(E / 'journal.json', P.js(journal))

    def write(p, data):
        assert p in snapshots
        journal.setdefault('metadata_after', {})[str(p)] = hashlib.sha256(data).hexdigest()
        P.put(E / 'journal.json', P.js(journal))
        P.put(p, data)
    attempted = False
    try:
        assert P.stopped(c.rt) and L.readj(L.CURRENT) == c.cur and P.snapshot_folder(L.SAVES) == saves
        assert all((p.read_bytes() if p.exists() else None) == v for p, v in snapshots.items())
        attempted = True
        P.pair_apply(E / 'candidate', E / 'before', c.rt, c.before, c.after, files=FILES)
        now = datetime.datetime.now().astimezone().isoformat()
        man = c.man
        rev = dict(status=STATUS, time=now, files=c.after, source_files=c.before, evidence=str(E), schema_changes=0,
                   added_functions=man['added_functions'], forwarded=man['forwarded'], clones=man['clones'],
                   same_length_sites=[{k: s[k] for k in ('tag', 'function', 'site_hex', 'before', 'after', 'what')} for s in man['same_length_sites']],
                   cache_variable=G.CACHE_VAR, notice=man['notice'], provenance=man['provenance'], author=G.AUTHOR,
                   limitations=c.qa['limitations'])
        nm = copy.deepcopy(c.manifest)
        nm.update(status=STATUS, time=now)
        nm[KEY + '_revision'] = rev
        nm['ain'].update(status=STATUS, candidate_sha256=c.after['NightRemaster.ain'])
        nm['ain'][KEY] = str(E / 'source/install_preflight.json')
        for row in nm['files']:
            if row['path'] in c.after:
                row.update(sha256=c.after[row['path']], size=(c.rt / row['path']).stat().st_size)
        nm['next'] = ('Gallery unlock installed (KR_G25): 전체 개방 also opens 추억 감상 and CG 감상. Keep KR_MSetUnlock a forwarder to '
                      'KR_G25SetUnlock, the five same-length sites (CheckEnabelScenario x2, KR_CGlobal, UpdateEnableCG, KR_CDo) and KR_CGlobal '
                      'on KR_G25SceneBase (the calendar keeps the original judgment everywhere).')
        write(c.mp, P.js(nm))
        mh = L.sha(c.mp)
        for p in c.contracts:
            co = L.readj(p)
            for k in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if k in co:
                    co[k] = mh
            for n, h in c.after.items():
                if n in co.get('required_files', {}):
                    co['required_files'][n] = h
            co[KEY + '_preserved_by'] = str(E)
            write(p, P.js(co))
        write(NEW, P.js({**rev, 'manifest': str(c.mp), 'manifest_sha256': mh, 'required_files': c.after,
                         'verification': dict(vm=c.qa['vm'], native=c.qa['native'], scan=c.qa['scan'], transaction_fixture_pass=True),
                         'instruction': ('Keep N_ModeScene::CheckEnabelScenario sites A/B (CALLFUNC KR_G25All; PUSH 0; POP / PUSH 1; PUSH 0; POP), '
                                         'KR_CGlobal site C on KR_G25SceneBase (a byte clone of the original judgment: the event calendar and '
                                         'the in-game calendar labels never see the flag), UpdateEnableCG site D on KR_G25Exist, KR_CDo site E '
                                         'on the new notice row, and KR_MSetUnlock a one-line forwarder to KR_G25SetUnlock (it refreshes the '
                                         'session cache YoruKR.G25.All). A later layer that wraps KR_MSetUnlock must clone the forwarder. '
                                         'Pinned functions and every earlier contract stay in force.')}))
        nc = copy.deepcopy(c.cur)
        nc.update(status=STATUS, manifest_sha256=mh)
        nc[KEY + '_revision'] = rev
        write(L.CURRENT, P.js(nc))
        latest = dict(c.latest)
        latest.update(manifest_sha256=mh, ain_sha256=c.after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation))
        latest[KEY + '_evidence'] = str(E)
        write(R / 'latest_worked_translation.json', P.js(latest))
        note = (f'\n\n### {now} 갤러리 전체 개방 연동(KR_G25) 설치\n'
                '- 메뉴바 「전체 개방」이 게임의 추억 감상(회상 76칸)·CG 감상(60칸 90장)에도 적용된다(이벤트 캘린더가 열려 있으면 적용 안 함). '
                '음악 감상은 원래 전부 열려 있어 변경 없음.\n'
                '- 같은 길이 교체 5곳(CheckEnabelScenario 2·KR_CGlobal·UpdateEnableCG·KR_CDo), KR_MSetUnlock 전달문, 새 함수 6개. '
                '원본 CODE/STR prefix·MSG·직렬화 구조·DLL·세이브 보존. 캘린더·인게임 달력 판정은 원래 판정 그대로.\n'
                f'- 설치 {c.rt}; 백업 {E / "before"}; 복구 publish_gallery_unlock.py --restore. 층 빌드·검증 {G.AUTHOR}.\n')
        write(R / 'progress.md', snapshots[R / 'progress.md'] + note.encode('utf8'))
        P.exact_tree(c.rt, nm['files'])
        assert P.snapshot_folder(L.SAVES) == saves
        assert (P.snapshot_folder(c.rt / 'KRMenu') if (c.rt / 'KRMenu').exists() else None) == menu
        journal.update(status='COMMITTED', manifest_sha256=mh, committed_pointer_sha256=L.sha(L.CURRENT))
        P.put(E / 'journal.json', P.js(journal))
    except BaseException as error:
        failures = []
        if attempted:
            try:
                P.pair_restore(E / 'before', c.rt, c.before, c.after, files=FILES)
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
    report = dict(status=STATUS, files=c.after, manifest_sha256=mh, runtime=str(c.rt), user_save_files_unchanged=len(saves),
                  backup=str(E / 'before'), prior_contracts_preserved=len(c.contracts))
    P.put(E / 'publish_report.json', P.js(report))
    P.put(E / 'README.md', ('# 갤러리 전체 개방 연동 (KR_G25)\n\n메뉴바 「전체 개방」이 추억 감상·CG 감상에도 적용됩니다. 이벤트 캘린더와 '
                            '인게임 달력의 판정은 원래 그대로입니다.\n\n- screenshots: 무음 사본 엔진 화면(candidate / installed 비교)\n'
                            '- before: 설치 전 백업\n- source: 검증 기록·설치/복구 도구\n').encode('utf8'))
    print(P.js(report).decode())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--check', action='store_true')
    g.add_argument('--install', action='store_true')
    g.add_argument('--restore', action='store_true')
    a = ap.parse_args()
    if a.restore:
        P.restore_ctx(SimpleNamespace(root=R, evidence=E, pointer=L.CURRENT, stop_check=P.stopped))
    else:
        ctx = gates()
        if a.check:
            print('PREFLIGHT_PASS', KEY, ctx.after, 'base_is_live', 'sources', len(SOURCE_RELS), 'tools', len(TOOL_FILES), 'shots', len(ctx.shots))
        else:
            install(ctx)
