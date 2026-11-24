"""Install preflight of the KR_G25 gallery-unlock candidate (Claude Opus 5.5 (claude-opus-5-5), 2026-09-30).

  python preflight_gallery_unlock.py     -> evidence/install_preflight.json  status GALLERY_UNLOCK_PREFLIGHT_PASS

Read only except the report files in evidence/ and the disposable transaction fixture under work/. Requires, for exactly the
candidate bytes in candidate/: the VM verification (verify_gallery_unlock.py: GALLERY_UNLOCK_VM_PASS, static re-check included),
the native probe (probe_gallery_unlock.py: GALLERY_UNLOCK_NATIVE_PASS, user save folder unchanged), the Defender scan
(scan_gallery_unlock.ps1: SCANNED_NO_TARGET_DETECTIONS), and runs the pair-install transaction fixture of the r24 publisher
(publish_chart_r24.fixture: disposable projects, injected failures, interrupted restore) on this payload.
"""
from pathlib import Path
import datetime, json, sys
sys.dont_write_bytecode = True
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import g25lib as G
L = G.L


def main():
    cur, rt, got = G.assert_live()
    man = G.readj(H / 'candidate/manifest.json')
    files = {n: L.sha(H / 'candidate' / n) for n in ('NightRemaster.ain', 'winmm.dll')}
    assert files == {n: v['sha256'] for n, v in man['files'].items()}, 'candidate differs from its manifest'
    assert G.readj(H / 'source/source_pointer.json') == cur, 'current.json moved since the build'
    vm = G.readj(H / 'evidence/vm_verification.json')
    assert vm['status'] == 'GALLERY_UNLOCK_VM_PASS' and vm['candidate_sha256'] == files['NightRemaster.ain'], ('VM verification', vm['status'])
    assert all(d['caught'] for d in vm['planted_defects'].values())
    nat = G.readj(H / 'evidence/native_probe.json')
    assert nat['status'] == 'GALLERY_UNLOCK_NATIVE_PASS' and nat['candidate_sha256'] == files['NightRemaster.ain'], ('native probe', nat['status'])
    assert not nat['user_files_changed']
    scan = G.readj(H / 'candidate/scan_report.json')
    assert scan['status'] == 'SCANNED_NO_TARGET_DETECTIONS' and scan['files'] == files, 'Defender scan missing or for other bytes'
    sys.path.insert(0, str(G.F))
    import publish_chart_r24 as P
    P.FILES = ['NightRemaster.ain', 'winmm.dll']
    P.O = H / 'candidate'
    L.WORK = H / 'work'
    tx = P.fixture()
    assert tx['status'] == 'TRANSACTION_FIXTURE_PASS' and tx['payload'] == files
    G.writej(H / 'evidence/transaction_verification.json', tx)
    shots = sorted(p.name for p in (H / 'evidence/native_candidate').glob('*.png'))
    report = dict(
        status='GALLERY_UNLOCK_PREFLIGHT_PASS', key=G.KEY, time=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        author=G.AUTHOR, files=files, live_sha256=G.LIVE_AIN, live_manifest_sha256=G.LIVE_MANIFEST,
        vm=dict(status=vm['status'], seconds=vm['seconds'], planted_defects={k: v['caught'] for k, v in vm['planted_defects'].items()},
                static={k: vm['static'][k] for k in ('old_code_bytes_changed', 'str0_added', 'metadata_changed', 'appended', 'saved_frames')}),
        native=dict(status=nat['status'], checks={k: v['ok'] for k, v in nat['checks'].items()}, seconds=nat['seconds'],
                    user_files_changed=nat['user_files_changed'], screenshots=len(shots)),
        scan=dict(status=scan['status'], engine=scan.get('engine'), signatures=scan.get('signatures')),
        transaction_fixture_pass=True, dll_unchanged=files['winmm.dll'] == G.LIVE_WINMM, serialized_schema_changes=0,
        limitations=[
            'The galleries follow the menu-bar flag only in the same session order the probe used (title -> gallery); the flag is '
            'cached per session and refreshed by every KR_MSetUnlock call. A flag file edited by hand while the game runs is seen '
            'after a restart (the hook only touches global records at startup).',
            'A recollection scene played through 전체 개방 registers what the game itself registers on a replay (read marks of its '
            'messages, the gallery CGs it shows: the probe replay of E50301 added CG1022 and one calendar read mark); those stay '
            'after 전체 개방 되돌리기, like the chart replays since r22. The recollection slot itself (needEvNo) locks again.',
            'The probe ran on the r24 COPIES of the user\'s global records (09-28), not the current ones; screen checks by the user remain.',
            'Music mode needed no change (both of its checks are constant true in this build).',
        ])
    G.writej(H / 'evidence/install_preflight.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'limitations'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
