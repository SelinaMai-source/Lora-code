#!/usr/bin/env bash
# SOTA campaign: serial GPU queue + gap check + iteration state (tmux session: sota_loop)
set -euo pipefail

ROOT="/root/autodl-tmp/Lora-code"
CAMPAIGN="${ROOT}/experiments/sota_campaign"
LOG_DIR="${CAMPAIGN}/logs"
LOOP_LOG="${LOG_DIR}/sota_iteration_loop.log"
STATE_JSON="${CAMPAIGN}/ITERATION_AGENT_STATE.json"
PID_FILE="${LOG_DIR}/sota_iteration_loop.pid"
PAUSE_FLAG="${CAMPAIGN}/PAUSE_SOTA_ITERATION_LOOP"

mkdir -p "$LOG_DIR"
cd "$ROOT" || exit 1
echo $$ > "$PID_FILE"
export PYTHONUNBUFFERED=1
export WANDB_PROJECT="${WANDB_PROJECT:-ours-sota-campaign}"

log() { echo "[$(date -Is)] $*" | tee -a "$LOOP_LOG"; }

if [[ -f "$PAUSE_FLAG" ]]; then
  log "PAUSE flag present ($PAUSE_FLAG); exiting."
  exit 0
fi

VERSION_DIR="${SOTA_VERSION_DIR:-v1_citb_kalman_drift}"
CFG_DIR="${CAMPAIGN}/${VERSION_DIR}/configs"
RESULTS_DIR="${CAMPAIGN}/${VERSION_DIR}/results"

update_state() {
  local phase="$1" status="$2" current_run="${3:-}"
  python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path
p = Path("${STATE_JSON}")
state = {}
if p.is_file():
    try:
        state = json.loads(p.read_text())
    except Exception:
        state = {}
state.update({
    "campaign": "ours_sota_three_suite",
    "version_dir": "${VERSION_DIR}",
    "phase": "${phase}",
    "status": "${status}",
    "current_run": "${current_run}",
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "wandb_project": "${WANDB_PROJECT}",
    "tmux_session": "sota_loop",
    "loop_pid": $$,
})
p.write_text(json.dumps(state, indent=2) + "\n")
PY
}

run_one() {
  local cfg="$1"
  local name
  name="$(basename "$cfg" .yaml)"
  local log="${LOG_DIR}/${name}.nohup.log"
  if [[ ! -f "$cfg" ]]; then
    log "SKIP missing config $cfg"
    return 0
  fi
  update_state "training" "running" "$name"
  log "START ${name} config=${cfg}"
  if ! python core/train.py --config "$cfg" >> "$log" 2>&1; then
    local st=$?
    log "FAIL ${name} status=${st} log=${log}"
    update_state "training" "failed" "$name"
    return "$st"
  fi
  log "END ${name} ok log=${log}"
  python3 "${CAMPAIGN}/sota_gap_check.py" --version-dir "${VERSION_DIR}" --run "$name" \
    >> "${LOG_DIR}/sota_gap_check.log" 2>&1 || true
  return 0
}

build_queue() {
  QUEUE=()
  local smoke="${CFG_DIR}/citb_instrdialog_smoke_v1.yaml"
  local smoke_done="${RESULTS_DIR}/runs/citb_instrdialog_smoke_v1/final_metrics.json"
  if [[ -f "$smoke" && ! -f "$smoke_done" ]]; then
    QUEUE+=("$smoke")
  elif [[ -f "$smoke_done" ]]; then
    log "Smoke already complete; skipping citb_instrdialog_smoke_v1"
  fi
  # Suite 1 priority (CITB InstrDialog strict, v1 aligned)
  for base in \
    citb_instrdialog_order1_seed1_ours_v1_strict \
    citb_instrdialog_order2_seed2_ours_v1_strict \
    citb_instrdialog_order3_seed3_ours_v1_strict; do
    QUEUE+=("${CFG_DIR}/${base}.yaml")
  done
  # Suite 1B+ (when configs exist under version dir)
  for cfg in "${CFG_DIR}"/citb_instrdialogpp_*_ours_v1_strict.yaml; do
    [[ -f "$cfg" ]] && QUEUE+=("$cfg")
  done
  # Suite 2 / 3: add strict ours configs from ccfa_three_suite when queued in STATE
  local ext="${CAMPAIGN}/suite23_queue.txt"
  if [[ -f "$ext" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" || "$line" =~ ^# ]] && continue
      [[ -f "$line" ]] && QUEUE+=("$line")
    done < "$ext"
  fi
}

log "=== SOTA iteration loop start pid=$$ version=${VERSION_DIR} wandb_project=${WANDB_PROJECT} ==="
update_state "loop" "started" ""

while true; do
  if [[ -f "$PAUSE_FLAG" ]]; then
    log "PAUSE detected; stopping loop."
    update_state "loop" "paused" ""
    exit 0
  fi

  build_queue
  if [[ ${#QUEUE[@]} -eq 0 ]]; then
    log "Empty queue; sleeping 300s"
    update_state "loop" "idle_empty_queue" ""
    sleep 300
    continue
  fi

  local_failed=0
  for cfg in "${QUEUE[@]}"; do
  if [[ -f "$PAUSE_FLAG" ]]; then break; fi
    run_one "$cfg" || local_failed=1
  done

  if python3 "${CAMPAIGN}/sota_gap_check.py" --version-dir "${VERSION_DIR}" \
      --run citb_instrdialog_order1_seed1_ours_v1_strict >> "${LOG_DIR}/sota_gap_check.log" 2>&1; then
    log "Suite1A order1 gap check PASSED (full campaign may still need other suites)"
    update_state "gap_check" "suite1a_order1_pass" ""
  else
    log "Gap check FAILED — awaiting incremental v{N+1} (archive under experiments/sota_campaign/v*_*/)"
    update_state "gap_check" "needs_optimization" ""
    echo "$(date -Is) needs_optimization see logs/sota_gap_check_latest.json" >> "${CAMPAIGN}/NEXT_OPTIMIZATION_HOOK.txt"
  fi

  if [[ "$local_failed" -eq 1 ]]; then
    log "Queue had failures; sleep 120s before retry pass"
    update_state "loop" "retry_after_failure" ""
    sleep 120
  else
    log "Queue pass complete; sleep 600s before next gap-driven iteration"
    update_state "loop" "queue_complete" ""
    sleep 600
  fi
done
