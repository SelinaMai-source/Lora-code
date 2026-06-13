#!/usr/bin/env bash
# Category A — v8_sota_5 单 seed 消融（seed=123, instrdialog）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source experiments/v8_sota5_campaign/campaign.env

LOG_DIR="$ROOT/results/logs/v8_sota5_campaign"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/ablation_single_seed_$(date +%Y%m%d_%H%M%S).log"

echo "WANDB_PROJECT=$WANDB_PROJECT"
echo "Category A -> group: $WANDB_GROUP_ABLATION"
echo "Log: $LOG_FILE"

python3 experiments/v8_sota5_campaign/run_from_manifest.py \
  --categories ablation_single_seed \
  --skip-existing \
  --continue-on-error \
  2>&1 | tee -a "$LOG_FILE"
