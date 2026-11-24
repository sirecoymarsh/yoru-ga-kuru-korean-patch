#!/bin/bash
# r21 full chain (build -> regs -> verify -> selftest -> r20 tour -> r21 tour -> native -> zoom); stops at the first failure
set -u
R21="P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r21_modmenu"
cd "/p/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r21_modmenu"
export TEMP="$R21\tmp" TMP="$R21\tmp" PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
step() {
  name=$1; shift
  echo "== $(date +%H:%M:%S) $name" >> work/chain_all.log
  timeout 9000 "$@" > "work/chain_$name.log" 2>&1
  rc=$?
  echo "   exit $rc" >> work/chain_all.log
  tail -2 "work/chain_$name.log" >> work/chain_all.log
  if [ $rc -ne 0 ]; then echo "STOPPED at $name" >> work/chain_all.log; exit $rc; fi
}
: > work/chain_all.log
step build python -B build_modmenu_r21.py
step regs python -B probe_modmenu_r21.py --regs
step verify python -B verify_modmenu_r21.py
step selftest python -B verify_modmenu_r21.py --selftest
step probe python -B probe_modmenu_r21.py
step probe21 python -B probe_modmenu_r21.py --r21
step native python -B verify_modmenu_r21.py --native
step zoom python -B work/zoom_r21.py
echo "== $(date +%H:%M:%S) CHAIN DONE" >> work/chain_all.log
