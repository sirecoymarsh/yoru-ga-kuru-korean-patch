#!/bin/bash
# r22 full chain (build -> regs -> verify -> selftest -> calendar tour -> chart tours -> kinds -> native -> zoom); stops at the first
# failure. The per-kind replays (probe_chart_r22.py --kinds) run on the candidate being verified; their verdicts must equal the ones
# the build baked (V41 checks KR_CNoPlay against 증거/replay_kinds.json), else rebuild and run the chain again.
set -u
R22="P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r22_chart"
cd "/p/AI/Codex/projects/YoruGaKuru_flowchart_20260922/ingame/r22_chart"
export TEMP="$R22\tmp" TMP="$R22\tmp" PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
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
if [ "${1:-}" != "--no-build" ]; then step build python -B build_chart_r22.py; fi   # (--from skips it too)
step regs python -B probe_calendar_tour_r22.py --regs
step verify python -B verify_chart_r22.py
step selftest python -B verify_chart_r22.py --selftest
step caltour python -B probe_calendar_tour_r22.py
step title python -B probe_chart_r22.py --title
step home python -B probe_chart_r22.py --home
step kinds python -B probe_chart_r22.py --kinds
step native python -B verify_chart_r22.py --native
step zoom python -B work/zoom_r22.py
echo "== $(date +%H:%M:%S) CHAIN DONE" >> work/chain_all.log
