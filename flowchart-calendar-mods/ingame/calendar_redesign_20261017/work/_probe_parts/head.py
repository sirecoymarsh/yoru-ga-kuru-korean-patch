# -*- coding: utf-8 -*-
"""Claude Opus 5.5 (2026-10-15): isolated, muted native probe of the redesigned Mods page (user: 「모드 옵션을 좀 보기좋게
다시 만들 수 있을까 … 모든 기능이 제대로 동작하나 체크좀」; isolated-copy testing approved earlier today).

  python probe_mods.py        a copied home save (NightR47), the 달성률 panel switched on in the probe's own save folder:
                              home shot -> the options opened from the home screen on the Mods page (the real path calls
                              ▲コンフィグ実行 directly, as the casual site does here) -> page shot (panel must be hidden, tracks
                              filled) -> every control driven between the two per-frame events and read back from the setting
                              it is bound to (4 reward sliders, battle speed, 9 checkboxes, the 5 navigation boxes) -> the three
                              dialog buttons clicked through their registered click handler (dialog shot, cancelled) -> page
                              shot -> options closed (AFL_Activity_End) -> home: the panel must be back -> the 자동 회복 설정
                              page (config page 10, the EX table row of KR_ItemConfigButton) opened and shot -> END

Everything lives under mods_tab_20261015/probe/ on P: (run/ = a copy of the runtime folder; exe/dll/ini/Data copied, big assets
hard-linked read only; PACT = the candidate PACT; InstallInfo/SaveFolderSetting.ini type 2 so saves stay inside run/). The user's
save folder is only read (hashed before and after).
The probe AIN = the candidate + probe-only code (never shipped): as probe_autonav.py (mute, no user input, dialog tick prefix,
waits, casual site, ▲コンフィグ実行 casual start page 7 -> 9), and the Mods layer site in EventConfAsraDataForParts
(KR_MDSeenToParts) wrapped by KR_ProbeCfgToParts, which calls it first.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mdlib as L

O = HERE / 'candidate'
PACT = HERE / 'NightRemasterPact.afa'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterModsProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat']
SAVE_TYPE = 2
HOME_SAVE = 'NightR47.asd'
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ('C_SelectDialog@Run', 'C_SelectMessage@Run', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>')
MODS_PAGE = 9
ITEMS_PAGE = 10

