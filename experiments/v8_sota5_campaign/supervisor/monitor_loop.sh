#!/bin/bash
# v8_sota5 campaign supervisor — periodic health ticks.
# Launch:
#   tmux new-session -d -s v8s5camp_supervisor \
#     'bash experiments/v8_sota5_campaign/supervisor/monitor_loop.sh'
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

SUPERVISOR_DIR="experiments/v8_sota5_campaign/supervisor"
INTERVAL_SEC="${CAMPAIGN_MONITOR_INTERVAL_SEC:-120}"

mkdir -p "$SUPERVISOR_DIR"
echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] monitor_loop started (interval=${INTERVAL_SEC}s)" \
  | tee -a "${SUPERVISOR_DIR}/CAMPAIGN_MONITOR.log"

while true; do
  python3 experiments/v8_sota5_campaign/supervisor/monitor_tick.py \
    || echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] tick failed exit=$?" \
      >> "${SUPERVISOR_DIR}/CAMPAIGN_MONITOR.log"
  sleep "${INTERVAL_SEC}"
done
