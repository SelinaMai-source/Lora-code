#!/usr/bin/env bash
# Category C — 五种 paper baseline 多种子 × instrdialog / instrdialog++
# 复用 configs/paper/instrdialog{,pp}__*__s{123,456,789}.yaml，运行时覆盖 W&B 项目与 group。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source experiments/v8_sota5_campaign/campaign.env

LOG_DIR="$ROOT/results/logs/v8_sota5_campaign"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/baseline_multiseed_$(date +%Y%m%d_%H%M%S).log"

echo "WANDB_PROJECT=$WANDB_PROJECT"
echo "Category C -> groups: $WANDB_GROUP_BASELINE_INSTRDIALOG, $WANDB_GROUP_BASELINE_INSTRDIALOGPP"
echo "Variants: $CAMPAIGN_BASELINE_VARIANTS"
echo "Seeds: $CAMPAIGN_SEEDS"
echo "Log: $LOG_FILE"

python3 experiments/v8_sota5_campaign/run_from_manifest.py \
  --categories baseline_multiseed \
  --skip-existing \
  --continue-on-error \
  2>&1 | tee -a "$LOG_FILE"
