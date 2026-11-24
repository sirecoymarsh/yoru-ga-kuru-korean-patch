#!/bin/bash
# r19 full chain (build -> regs -> verify -> selftest -> probe -> native -> page stats -> zoom); stops at the first failure
set -u
R19="P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r19_calendar"
cd "/p/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r19_calendar"
export TEMP="$R19\tmp" TMP="$R19\tmp" PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
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
step build python -B build_calendar_r19.py
step regs python -B probe_calendar_r19.py --regs
step verify python -B verify_calendar_r19.py
step selftest python -B verify_calendar_r19.py --selftest
step probe python -B probe_calendar_r19.py
step native python -B verify_calendar_r19.py --native
step pagestats python -B work/page_stats_r19.py
step zoom python -B work/zoom_r19.py
step samples python -B work/name_samples_r19.py
echo "== $(date +%H:%M:%S) CHAIN DONE" >> work/chain_all.log
