"""Auto-nav layer shared helpers (Claude Opus 5.5, 2026-10-15) - a copy of r23_feeling/r23lib.py (the r15-r23 folders are
evidence: read only) with the base moved to the runtime current.json points at on 10-15 (claude_text_20261001 install).

Everything this project writes stays under ingame/autonav_20261015/ on P:. Nothing is ever written into the runtime, the save
folders or the Codex project.
"""
from pathlib import Path
import collections, hashlib, json, os, re, struct, subprocess, zlib

HERE = Path(__file__).resolve().parent                     # ...\ingame\autonav_20261015
FLOW = HERE.parent.parent                                  # ...\YoruGaKuru_flowchart_20260922
WORK = HERE / 'work'
TMP = HERE / 'tmp'
EVID = HERE / '증거'
CODEX = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908')   # read only
CURRENT = CODEX / 'ui_cumulative' / 'current.json'
ALICE = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe')
PROXY = Path(r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_hangul_name_v4\wansung_build\build_output\fnl_proxy_map_wansung2350.json')
SAVES = Path(r'C:\Users\CadriacLord\OneDrive\문서\AliceSoft\밤이 온다! -Square of the MOON- Remastered\SaveData_KR_UI_Integrated_20260913')  # read only
BASE_AIN_SHA = '3afdd2b1e11a107defa4b91465f97241e7ddc70fb681f0561e8b67fd897aa8f9'   # claude_text_20261001 install (10-01 15:06)
BASE_PACT_SHA = 'd4de68c5d44ff5c80b9c41be21f86059d0ebca2717284f4ed8a7d43f6f029403'
BASE_EX_SHA = 'de2f9f8affe75a08bc38e577c25ac25b5816b9b1714adf3b3a7ac102db5589c6'
BASE_WINMM_SHA = '0df1aa37edae29a9eb878e8043779b620ba0a3de5ee450cd872a5eac9c1e495e'
BASE_STATUS = 'CLAUDE_TEXT_20261001_INSTALLED_VM_PASS'
BASE_MANIFEST_SHA = 'fcfb8a49c6910889c2f49f50ed796210c2a04211f6e194d0ad992cd796ecd1ea'
BASE_CHART_SHA = 'cc645872b062e42e9d5ed103555bb173c7e6a5df5f24f3a113646bb72de208ea'
AUTHOR = 'Claude Opus 5.5 (claude-opus-5-5)'
PREFIX = 'KR_AN'
# Functions that sit on saved resume stacks and were pinned by earlier layers: every code byte stays (r18-r23 rule).
PINNED = ['KR_T9HomeCasual', 'KR_T9HomeConfig', 'C_SceneHomebase@CheckGameSysButtons', 'C_SceneHomebase@Run', 'LSys3xScript::RunEvent']
SANDBOX = 'KR_T18RunSandboxed'
PINNED_ALL = PINNED + [SANDBOX, 'KR_CReplayRun']

for d in (WORK, TMP, EVID):
    d.mkdir(parents=True, exist_ok=True)


def env():
    """Child processes keep their temp files on P: (09-24 C: 0B incident, user rule 09-25)."""
    e = dict(os.environ)
    e['TEMP'] = e['TMP'] = str(TMP)
    e['PYTHONUTF8'] = '1'
    e['PYTHONDONTWRITEBYTECODE'] = '1'
    return e


