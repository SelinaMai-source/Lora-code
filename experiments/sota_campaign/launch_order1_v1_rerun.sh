#!/usr/bin/env bash
set -euo pipefail
ROOT="/root/autodl-tmp/Lora-code"
CFG="${ROOT}/experiments/sota_campaign/v1_citb_kalman_drift/configs/citb_instrdialog_order1_seed1_ours_v1_strict.yaml"
LOG="${ROOT}/experiments/sota_campaign/logs/citb_instrdialog_order1_seed1_ours_v1_strict_rerun.nohup.log"
touch "${ROOT}/experiments/sota_campaign/PAUSE_SOTA_ITERATION_LOOP"
cd "$ROOT"
export PYTHONUNBUFFERED=1
export WANDB_PROJECT="${WANDB_PROJECT:-ours-sota-campaign}"
nohup python core/train.py --config "$CFG" >> "$LOG" 2>&1 &
echo "Started order1 v1 strict rerun pid=$! log=$LOG"
