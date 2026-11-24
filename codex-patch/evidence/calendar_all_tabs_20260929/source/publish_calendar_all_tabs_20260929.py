"""WI-009 install / restore (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29): stopped-game-only transaction for the all-tabs
event-calendar UI, in the form of publish_calendar_label_particles_20260929.py.

  python publish_calendar_all_tabs_20260929.py --check     read-only preflight: prints PREFLIGHT_PASS (writes nothing)
  python publish_calendar_all_tabs_20260929.py --install   INSTALL (only with the user's permission, the game closed, Codex idle)
  python publish_calendar_all_tabs_20260929.py --restore   exact return to the pre-install state (journal-driven, idempotent)
Any other argument (or none) prints this text and exits with status 2 - nothing is installed (r2, review F-06).

Payload: NightRemaster.ain (winmm.dll carried unchanged). One journaled transaction: external backup under
evidence/calendar_all_tabs_20260929/before -> hash-checked pair replacement -> runtime manifest + current.json + every required_*.json
(their manifest / file hashes follow, calendar_all_tabs_20260929_preserved_by) + new required_calendar_all_tabs_20260929.json +
latest_worked_translation.json (+ installed translation map) + progress.md note -> exact tree (KRMenu ignored) / saves re-checked ->
COMMITTED. Any failure rolls every file back. The game must not be running.
"""
from pathlib import Path
from types import SimpleNamespace
import sys, copy, shutil, datetime, hashlib
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import w29common as C
L = C.L
import publish_chart_r24 as P
R, O = C.R, C.O
E = R / 'evidence' / C.KEY
FILES = ['NightRemaster.ain', 'winmm.dll']
NEW = R / ('required_' + C.KEY + '.json')
KEY = C.KEY
STATUS = 'CALENDAR_ALL_TABS_20260929_INSTALLED_NATIVE_PASS'
L.TMP = O / 'work/tmp'
# the files the install copies into evidence/calendar_all_tabs_20260929/source (checked by --check too: review F-06)
SOURCE_REL = ['candidate/scan_report.json', 'candidate/manifest.json', 'evidence/install_preflight.json', 'evidence/save_frames.json',
              'evidence/transaction_verification.json', 'evidence/semantic_qa.json', 'evidence/native_all_tabs_probe.json',
              'evidence/native_home_probe.json', 'evidence/april_regression.json', 'evidence/r1_vs_r2_screens.json',
              'design/wording_map.json', 'design/scope.json', 'design/static_gates.json', 'work/build/helpers_readable.jaf',
              'probe/tour_readable.jaf', 'probe_home/tour_home_readable.jaf']
SOURCE_FILES = ['w29common.py', 'w29probe.py', 'build_calendar_all_tabs_20260929.py', 'probe_calendar_all_tabs_20260929.py',
                'probe_calendar_all_tabs_20260929.jaf', 'probe_calendar_home_20260929.py', 'probe_calendar_home_20260929.jaf',
                'probe_calendar_april_regression_20260929.py', 'verify_calendar_all_tabs_20260929.py', 'publish_calendar_all_tabs_20260929.py',
                'scan_calendar_all_tabs_20260929.ps1', '인계_WI009.md']
SHOT_DIRS = ['evidence/native_all_tabs', 'evidence/native_home']
INSTRUCTION = (
    'WI-009 (Claude Opus 5.5, design Claude Fable 5.1): the approved April event-calendar UI on every tab (4..11월, 회상, 그 밖) of the '
    'calendar opened from the mod menu (KR_CActive() true). Preserve the KR_W29* helpers and the three one-call forwarders '
    '(KR_CDraw -> KR_W29Minis, KR_P29Board -> KR_W29Board, KR_T9StagePage -> KR_W29Stages; index, arguments and return kept). '
    'Display rules: 「N단계」 -> 「장면 N」 (card / group heads 「장면 N개」); group list names without the stage-count tail, the count on '
    'the state line 「전체 N개 중 M개 감상」; 감상 완료 / 아직 보지 않음 / 잠김; E numbers kept; adaptive 32x40 list portraits (KR_AM29Render, '
    'max 8, exact +N); 104x130 detail portraits with centred names; two-column fields 언제 / [선택] / 인물 / 열람 상태 / 재생 / [장면 묶음] / '
    '[조건]; the 20 choice-context scenes show their real date and 선택 only once read; unread scenes hide people, portraits, summary '
    'and choice even under 전체 개방; summaries come from KR_W29Story (April KR_AS29Story, else E00011 KR_P29Story) - later monthly '
    'summary layers wrap KR_W29Story; one-column scene picker for every group (10 per page, 8 with paging), card 6 keeps the approved '
    'April picker (KR_U29Stages). Keep the KR_N29 / KR_S29 / KR_R29 label getters and their unread masks, the April summaries, '
    'the in-game calendar / achievement dialogs (r18 / r19 bodies, user 09-28), replay isolation code, scenario messages, '
    'read records and the save layout. Never rebuild from the r24 / April candidates: rebuild on the current.json runtime.')


def main(check=False):
    qa = L.readj(O / 'evidence/install_preflight.json')
    man = L.readj(O / 'candidate/manifest.json')
    after = {n: L.sha(O / 'candidate' / n) for n in FILES}
    before = {'NightRemaster.ain': man['live_sha256'], 'winmm.dll': after['winmm.dll']}
    assert qa['status'] == 'ALL_TABS_PREFLIGHT_PASS' and qa['files'] == after, 'preflight did not pass on this candidate'
    assert after == {n: man['files'][n]['sha256'] for n in FILES}
    for path, status in [(O / 'candidate/scan_report.json', 'SCANNED_NO_TARGET_DETECTIONS'),
                         (O / 'evidence/transaction_verification.json', 'TRANSACTION_FIXTURE_PASS')]:
        v = L.readj(path)
        assert v['status'] == status and v.get('payload', v.get('files')) == after, path
    probe = L.readj(O / 'evidence/native_all_tabs_probe.json')
    assert probe['pass'] and probe['candidate_sha256'] == after['NightRemaster.ain']
    home = L.readj(O / 'evidence/native_home_probe.json')
    assert home['pass'] and home['candidate_sha256'] == after['NightRemaster.ain'], 'home-context probe not passed on this candidate'
    missing = [rel for rel in SOURCE_REL if not (O / rel).is_file()] + [n for n in SOURCE_FILES if not (H / n).is_file()]
    missing += [d for d in SHOT_DIRS if not list((O / d).glob('*.png'))]
    assert not missing, ('source copies missing - the install would stop after creating its evidence folder', missing)
    april = L.readj(O / 'evidence/april_regression.json')
    assert april['status'] == 'APRIL_REGRESSION_PASS' and april['candidate_sha256'] == after['NightRemaster.ain']
    sqa = L.readj(O / 'evidence/semantic_qa.json')
    assert sqa['status'] == 'PASS' and not sqa['unresolved'] and sqa['translation_map_sha256'] == L.sha(O / 'design/wording_map.json')
    cur = L.readj(L.CURRENT)
    assert cur == L.readj(O / 'source_pointer.json'), 'Live build moved since staging'
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
    if check:
        print('PREFLIGHT_PASS', after)
        return
    assert not E.exists() and not NEW.exists(), 'Inspect existing journal'
    contracts = sorted(R.glob('required_*.json'))
    paths = [mp, L.CURRENT, R / 'progress.md', R / 'latest_worked_translation.json', NEW] + contracts
    assert len(paths) == len({x.name for x in paths})
    snapshots = {p: p.read_bytes() if p.exists() else None for p in paths}
    for d in ['before', 'candidate', 'source', 'screenshots']:
        (E / d).mkdir(parents=True)
    metadata = []
    for p, data in snapshots.items():
        if data is not None:
            P.put(E / 'before' / p.name, data)
        metadata.append(dict(path=str(p), name=p.name, existed=data is not None, sha256=hashlib.sha256(data).hexdigest() if data is not None else None))
    for n in FILES:
        shutil.copy2(rt / n, E / 'before' / n)
        shutil.copy2(O / 'candidate' / n, E / 'candidate' / n)
    for rel in SOURCE_REL:
        shutil.copy2(O / rel, E / 'source' / Path(rel).name)
    for name in SOURCE_FILES:
        shutil.copy2(H / name, E / 'source' / name)
    for d in SHOT_DIRS:
        for path in (O / d).glob('*.png'):
            shutil.copy2(path, E / 'screenshots' / path.name)
    saves = P.snapshot_folder(L.SAVES)
    menu = P.snapshot_folder(rt / 'KRMenu') if (rt / 'KRMenu').exists() else None
    P.put(E / 'save_hashes_before.json', P.js(saves))
    wording = L.readj(O / 'design/wording_map.json')
    full = L.readj(Path(latest['translation_map']))
    full['installed_ain_sha256'] = after['NightRemaster.ain']
    full[KEY] = dict(evidence=str(E), semantic_dialogue_changes=0, counts=wording['counts'], map=str(E / 'source/wording_map.json'),
                     map_sha256=L.sha(E / 'source/wording_map.json'), translator_model=C.AUTHOR, author=C.AUTHOR, designer=C.DESIGNER)
    translation = E / 'source/installed_translation_map.json'
    P.put(translation, P.js(full))
    journal = dict(status='PREPARED', runtime=str(rt), files=FILES, before=before, after=after, metadata=metadata)
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
                   rerouted={k: v[1] for k, v in C.ROUTES.items()}, added_functions=sorted(C.ADDED), wording_counts=wording['counts'],
                   translator_model=C.AUTHOR, author=C.AUTHOR, designer=C.DESIGNER, limitations=qa['limitations'],
                   revision=man.get('revision'), review=str(R / 'staging/calendar_all_tabs_review_20260929/review.md'))
        nm = copy.deepcopy(manifest)
        nm.update(status=STATUS, time=now)
        nm[KEY + '_revision'] = rev
        nm['ain'].update(status=STATUS, candidate_sha256=after['NightRemaster.ain'])
        nm['ain'][KEY] = str(E / 'source/install_preflight.json')
        for row in nm['files']:
            if row['path'] in after:
                row.update(sha256=after[row['path']], size=(rt / row['path']).stat().st_size)
        nm['next'] = ('All-tabs event-calendar UI installed (WI-009). Next: WI-010 May summaries wrap KR_W29Story; keep the KR_W29 '
                      'forwarders, the April screens, KR_N29 / KR_S29 / KR_R29 getters and the in-game r18 / r19 dialogs.')
        write(mp, P.js(nm))
        mh = L.sha(mp)
        for p in contracts:
            co = L.readj(p)
            for key in ['manifest_sha256', 'reference_manifest_sha256', 'latest_manifest_sha256']:
                if key in co:
                    co[key] = mh
            for n, h in after.items():
                if n in co.get('required_files', {}):
                    co['required_files'][n] = h
            co[KEY + '_preserved_by'] = str(E)
            write(p, P.js(co))
        write(NEW, P.js({**rev, 'manifest': str(mp), 'manifest_sha256': mh, 'required_files': after, 'verification': qa,
                         'instruction': INSTRUCTION}))
        nc = copy.deepcopy(cur)
        nc.update(status=STATUS, manifest_sha256=mh)
        nc[KEY + '_revision'] = rev
        write(L.CURRENT, P.js(nc))
        latest.update(manifest_sha256=mh, ain_sha256=after['NightRemaster.ain'], translation_map=str(translation),
                      translation_map_sha256=L.sha(translation))
        latest[KEY + '_evidence'] = str(E)
        write(R / 'latest_worked_translation.json', P.js(latest))
        np_ = qa['native_probe']
        april_diff = ', '.join(april['differing'])
        note = (f'\n\n### {now} 이벤트 캘린더 전 탭 확대 (WI-009 {man.get("revision", "")}, Claude Opus 5.5)\n'
                f'- 4월 승인 UI(목록·상세·장면 고르기)를 5~11월·회상·그 밖 전 탭으로 확대. 「N단계」→「장면 N」, 묶음 이름 꼬리 제거·상태 줄 「전체 N개 중 M개 감상」, '
                f'가변 32×40 초상·정확한 +N, 상세 104×130·이름 중앙·두 열, 선택 문맥 20건은 읽은 뒤에만 날짜·선택 표시, 미열람 가림 유지. '
                f'언제 칸의 r19 제목 이음 표식(†+들여쓰기) 23건 정리, 긴 상세 제목은 「 · 」에서 줄바꿈, 아래 줄 썸네일 칸이 가리는 8쪽은 안내문을 아래 막대로.\n'
                f'- 무음 native: 목록 {np_["list_cells_checked"]}칸(5가지 읽음/잠김 상태), 상세 {np_["detail_boards"]}장, 장면 고르기 35묶음×2, 달성률 선택창 3, '
                f'실제 대기 경로 2, 목록·타이틀 픽셀 복귀, 본거지에서 연 캘린더(목록·상세·장면 고르기)와 대표 재생 뒤 같은 쪽 복귀. 4월 회귀(설치본 대비 차이 화면): {april_diff} — E00006 제목 조사, E10001 언제 표식 정리, 5월은 의도된 확대.\n'
                f'- 달성률(인게임 달력) 선택창은 r18/r19 그대로(사용자 09-28 지시). 원본 CODE/STR prefix·MSG·직렬화 구조·DLL·세이브 보존.\n'
                f'- 설치 {rt}; 백업 {E / "before"}; 복구 publish_calendar_all_tabs_20260929.py --restore.\n')
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
    P.put(O / 'publish_report.json', P.js(report))
    P.put(E / 'README.md', ('# 이벤트 캘린더 전 탭 확대 (WI-009)\n\n4월에 승인된 목록·상세·장면 고르기 화면을 5~11월·회상·그 밖 탭 전체로 넓혔습니다. '
                            'E번호, 날짜·조건, 선택 문맥, 미열람 가림, 시나리오와 세이브는 그대로입니다. 달성률(인게임 달력) 선택창은 바꾸지 않았습니다.\n\n'
                            '- screenshots: 무음 native 탐침 화면\n- before: 설치 전 백업\n- source: 수정표·검증·설치/복구 도구\n').encode('utf8'))
    print(P.js(report).decode())


if __name__ == '__main__':
    args = sys.argv[1:]
    if args == ['--restore']:
        P.restore_ctx(SimpleNamespace(root=R, evidence=E, pointer=L.CURRENT, stop_check=P.stopped))
    elif args == ['--check']:
        main(check=True)
    elif args == ['--install']:
        main(check=False)
    else:
        print(__doc__)
        sys.exit(2)
