# -*- coding: utf-8 -*-
"""Claude Opus 5.5 (2026-10-17): isolated, muted native probe of the redesigned home 달성률 panel (stage 1).

  python probe_home.py     a copied home save (NightR47), the panel switched on in the probe's own save folder:
                           home shot (values must equal the old panel's sources, the old text body hidden, the calendar
                           button shown while the top menu waits) -> the calendar button clicked through the panel's click
                           handler (KR_T8HomeClick with the button's screen y) -> the event calendar opens (KR_CDoHome) ->
                           chart shot -> closed -> home shot -> the 쿄카 row clicked -> the character window -> shot ->
                           cancelled -> home shot -> row map checks -> END

Everything lives under calendar_redesign_20261017/probe/ on P: (run/ = a copy of the runtime folder; exe/dll/ini/Data copied,
big assets hard-linked read only; PACT = the candidate PACT; InstallInfo/SaveFolderSetting.ini type 2 so saves stay inside
run/). The user's save folder is only read (hashed before and after).
The probe AIN = the candidate + probe-only code (never shipped), as probe_mods.py: mute, no user input, the dialog tick prefix in
C_SelectDialog@_Update, waits; plus a tick prefix in the chart's frame delegate KR_CFrame. Real mouse hit-testing and the
cursor-over state are not exercised (input is cut off); the click handler is called with the button's coordinates.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import datetime, hashlib, json, os, re, shutil, struct, sys, time
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hvlib as L

O = HERE / 'candidate'
PACT = O / 'NightRemasterPact.afa'
PROBE = HERE / 'probe'
RUN = PROBE / 'run'
BOOT = 'NightRemasterHomeProbe'
EXE_SHA = '7250430736c7640dd213c7148fbc37f7e9e8c73e647407625942c2edd74e572e'
COPY_GLOBAL = ['NightRMsgSkip.msk', 'NightRAFCGMode.asd', 'NightRAFMemMode.asd', 'NightRAFBGMMode.asd', 'NightRAFCommon.asd',
               'NightRAFInfo.asd', 'CommonGameData.asd', 'CommonSystemData.sav', 'Volume.sav', 'AFConfig.asd', '3DConfig.vsf',
               'MouseCursorSetting.sav', 'ShowDPSetting.sav', 'YoruKR_Terms.dat', 'YoruKR_Terms.backup', 'YoruKR_HomeRate.dat',
               'YoruKR_Chart.dat']
SAVE_TYPE = 2
HOME_SAVE = 'NightR47.asd'          # latest save made from the home screen (stack: C_SceneHomebase@Run -> CheckGameSysButtons)
MSG_LAMBDA = 'message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@<lambda : message::detail::CMessageTextView@ExecuteKeyWait(bool)'
LIVE_WAITS = ('C_SelectDialog@Run', 'C_SelectMessage@Run', 'C_SceneTraining@<lambda : C_SceneTraining@RunSelectPartner()(229, 46)>', 'KR_CWait')
ROW_Y0, ROW_STEP = 124, 44
CAL_Y = 588

