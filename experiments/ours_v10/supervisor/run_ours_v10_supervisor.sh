#!/bin/bash
# Ours v10 campaign supervisor: gap audit → train weakest → early-stop → bump version.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

STATE_DIR="experiments/ours_v10/supervisor"
mkdir -p "$STATE_DIR" results/logs archives/ours_v10

VERSION="${OURS_V10_VERSION:-1}"
CONFIG="experiments/ours_v10/configs/ours_v10_${VERSION}__seqglue__s123.yaml"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$STATE_DIR/supervisor.log"; }

while true; do
  log "=== ours_v10 supervisor tick (v${VERSION}) ==="
  python3 scripts/ours_v10_sota_gap_audit.py || true

  WEAKEST="$(python3 -c "
import json
from pathlib import Path
p = Path('results/tables/ours_v10_sota_gap_s123.json')
if not p.is_file():
    print('seqglue')
else:
    print(json.loads(p.read_text()).get('weakest_benchmark') or 'seqglue')
")"

  if [ "$WEAKEST" = "null" ] || [ -z "$WEAKEST" ]; then
    log "All benchmarks at SOTA — sleeping 1h"
    sleep 3600
    continue
  fi

  if [ ! -f "$CONFIG" ]; then
    log "Missing config $CONFIG — stop supervisor"
    exit 1
  fi

  LOG="results/logs/ours_v10_v${VERSION}_${WEAKEST}_s123.log"
  if pgrep -f "core/train.py.*ours_v10" >/dev/null 2>&1; then
    log "Training already running"
    sleep 300
    continue
  fi

  log "Launching v${VERSION} on ${WEAKEST}: $CONFIG"
  export OURS_V10_EARLY_STOP=1
  set +e
  python3 core/train.py --config "$CONFIG" 2>&1 | tee -a "$LOG"
  RC=${PIPESTATUS[0]}
  set -e
  log "Train exit code: $RC"

  if [ "$RC" -eq 42 ]; then
    log "Early stop (42) — bump version"
    VERSION=$((VERSION + 1))
    CONFIG="experiments/ours_v10/configs/ours_v10_${VERSION}__seqglue__s123.yaml"
    if [ ! -f "$CONFIG" ]; then
      log "No config for v${VERSION}; waiting for agent to author next version"
      sleep 1800
    fi
  elif [ "$RC" -eq 0 ]; then
    log "Run finished — re-audit gap"
    python3 scripts/ours_v10_sota_gap_audit.py || true
    sleep 600
  else
    log "Train failed rc=$RC — sleep 10min"
    sleep 600
  fi
done
