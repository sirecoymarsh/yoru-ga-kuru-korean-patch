#!/bin/bash
# r24 full chain (build -> event_cg check -> regs -> verify -> selftest -> calendar tour -> chart tours (title with the r24 steps,
# home) -> per-kind replays -> native -> zoom); stops at the first failure. The calendar tour and the per-kind replays are the
# r22 / r23 ones run on the r24 candidate (the verifier's native checks need them logged by this candidate).
set -u
R24="P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r24_chart"
cd "/p/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r24_chart"
export TEMP="$R24\tmp" TMP="$R24\tmp" PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
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
if [ "${1:-}" != "--no-build" ]; then step build python -B build_chart_r24.py; fi   # (--from skips it too)
step eventcg python -B event_cg_r24.py --check
step regs python -B probe_calendar_tour_r24.py --regs
step verify python -B verify_chart_r24.py
step selftest python -B verify_chart_r24.py --selftest
step caltour python -B probe_calendar_tour_r24.py
step title python -B probe_chart_r24.py --title
step home python -B probe_chart_r24.py --home
step kinds python -B probe_chart_r24.py --kinds
step native python -B verify_chart_r24.py --native
step zoom python -B work/zoom_r24.py
echo "== $(date +%H:%M:%S) CHAIN DONE" >> work/chain_all.log
