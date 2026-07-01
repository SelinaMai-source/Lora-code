#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

SUPERVISOR_DIR="experiments/lora_strict_campaign/supervisor"
INTERVAL_SEC="${STRICT_MONITOR_INTERVAL_SEC:-180}"

mkdir -p "$SUPERVISOR_DIR"
echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] strict monitor_loop started (interval=${INTERVAL_SEC}s)" \
  | tee -a "${SUPERVISOR_DIR}/STRICT_MONITOR.log"

while true; do
  python3 experiments/lora_strict_campaign/supervisor/monitor_tick.py \
    || echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] tick failed exit=$?" \
      >> "${SUPERVISOR_DIR}/STRICT_MONITOR.log"
  sleep "${INTERVAL_SEC}"
done
