#!/usr/bin/env bash
# 等待 v8s5camp_baselines（若仍存在）结束后，串行跑完剩余战役：
# baseline_multiseed → ours_multiseed → ablation_single_seed
# （若 baseline 会话已意外退出，会从 manifest 继续未完成的 baseline run）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source experiments/v8_sota5_campaign/campaign.env

LOG_DIR="$ROOT/results/logs/v8_sota5_campaign"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/queue_after_baselines_$(date +%Y%m%d_%H%M%S).log"

MANIFEST_ARGS=(
  --skip-existing
  --continue-on-error
)

_wait_gpu_idle() {
  while pgrep -f "[p]ython.*core/train.py" >/dev/null 2>&1; do
    echo "[queue] waiting for train.py to exit..." | tee -a "$LOG_FILE"
    sleep 60
  done
}

_run_category() {
  local category="$1"
  _wait_gpu_idle
  echo "[queue] category=$category" | tee -a "$LOG_FILE"
  python3 experiments/v8_sota5_campaign/run_from_manifest.py \
    --categories "$category" \
    "${MANIFEST_ARGS[@]}" \
    2>&1 | tee -a "$LOG_FILE"
}

if tmux has-session -t v8s5camp_baselines 2>/dev/null; then
  echo "[queue] waiting for tmux session v8s5camp_baselines..." | tee -a "$LOG_FILE"
  while tmux has-session -t v8s5camp_baselines 2>/dev/null; do
    sleep 120
  done
  _wait_gpu_idle
else
  echo "[queue] no v8s5camp_baselines session; will run/continue baselines from manifest" | tee -a "$LOG_FILE"
fi

_run_category baseline_multiseed
_run_category ours_multiseed
_run_category ablation_single_seed

echo "[queue] campaign queue finished" | tee -a "$LOG_FILE"
