#!/bin/bash
# r23 full chain (build -> regs -> verify -> selftest -> calendar tour (r20 status + r23 stages) -> chart tours -> kinds -> native ->
# zoom); stops at the first failure. The chart tours and the per-kind replays are r22's, run on the r23 candidate (the verifier's
# R22N checks need them logged by this candidate; V41 compares the per-kind verdicts with the ones r22 baked).
set -u
R23="P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r23_feeling"
cd "/p/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r23_feeling"
export TEMP="$R23\tmp" TMP="$R23\tmp" PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
# --from STEP: skip the steps before STEP (their results must still be for the same candidate; publish --verify checks that)
FROM=""
if [ "${1:-}" = "--from" ]; then FROM=$2; fi
STARTED=""
step() {
  name=$1; shift
  if [ -n "$FROM" ] && [ -z "$STARTED" ] && [ "$name" != "$FROM" ]; then echo "== skip $name" >> work/chain_all.log; return 0; fi
  STARTED=1
  echo "== $(date +%H:%M:%S) $name" >> work/chain_all.log
  timeout 9000 "$@" > "work/chain_$name.log" 2>&1
  rc=$?
  echo "   exit $rc" >> work/chain_all.log
  tail -2 "work/chain_$name.log" >> work/chain_all.log
  if [ $rc -ne 0 ]; then echo "STOPPED at $name" >> work/chain_all.log; exit $rc; fi
}
: > work/chain_all.log
if [ "${1:-}" != "--no-build" ]; then step build python -B build_feeling_r23.py; fi   # (--from skips it too)
step eventcg python -B event_cg_r23.py --check
step regs python -B probe_calendar_tour_r23.py --regs
step verify python -B verify_feeling_r23.py
step selftest python -B verify_feeling_r23.py --selftest
step caltour python -B probe_calendar_tour_r23.py
step title python -B probe_chart_r23.py --title
step home python -B probe_chart_r23.py --home
step kinds python -B probe_chart_r23.py --kinds
step native python -B verify_feeling_r23.py --native
step zoom python -B work/zoom_r23.py
echo "== $(date +%H:%M:%S) CHAIN DONE" >> work/chain_all.log
