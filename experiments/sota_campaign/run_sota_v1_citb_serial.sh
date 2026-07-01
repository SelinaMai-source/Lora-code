#!/usr/bin/env bash
set -o pipefail
if [[ -f "$(dirname "$0")/PAUSE_SOTA_V1_SERIAL" ]]; then echo "PAUSE_SOTA_V1_SERIAL set; use start_sota_loop_tmux.sh"; exit 0; fi
ROOT="/root/autodl-tmp/Lora-code"
CFG="${ROOT}/experiments/sota_campaign/v1_citb_kalman_drift/configs"
LOG_DIR="${ROOT}/experiments/sota_campaign/logs"
QUEUE_LOG="${LOG_DIR}/sota_v1_citb_serial_queue.log"
PID_FILE="${LOG_DIR}/sota_v1_citb_serial_queue.pid"

mkdir -p "$LOG_DIR"
echo $$ > "$PID_FILE"
cd "$ROOT" || exit 1
export PYTHONUNBUFFERED=1

run_one() {
  local cfg="$1"
  local name
  name="$(basename "$cfg" .yaml)"
  local log="${LOG_DIR}/${name}.nohup.log"
  echo "[$(date -Is)] START ${name}" | tee -a "$QUEUE_LOG"
  python core/train.py --config "$cfg" > "$log" 2>&1
  local st=$?
  echo "[$(date -Is)] END ${name} status=${st} log=${log}" | tee -a "$QUEUE_LOG"
  return "$st"
}

CONFIGS=(
  "${CFG}/citb_instrdialog_smoke_v1.yaml"
  "${CFG}/citb_instrdialog_order1_seed1_ours_v1_strict.yaml"
  "${CFG}/citb_instrdialog_order2_seed2_ours_v1_strict.yaml"
  "${CFG}/citb_instrdialog_order3_seed3_ours_v1_strict.yaml"
)

echo "[$(date -Is)] SOTA v1 CITB serial queue started pid=$$" | tee -a "$QUEUE_LOG"
for cfg in "${CONFIGS[@]}"; do
  run_one "$cfg" || exit "$?"
done
echo "[$(date -Is)] SOTA v1 CITB serial queue completed" | tee -a "$QUEUE_LOG"
