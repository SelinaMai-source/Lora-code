#!/usr/bin/env bash
# Category B — v8_sota_5 champion 多种子 × instrdialog / instrdialog++
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source experiments/v8_sota5_campaign/campaign.env

LOG_DIR="$ROOT/results/logs/v8_sota5_campaign"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/ours_multiseed_$(date +%Y%m%d_%H%M%S).log"

echo "WANDB_PROJECT=$WANDB_PROJECT"
echo "Category B -> groups: $WANDB_GROUP_OURS_INSTRDIALOG, $WANDB_GROUP_OURS_INSTRDIALOGPP"
echo "Seeds: $CAMPAIGN_SEEDS"
echo "Log: $LOG_FILE"

python3 experiments/v8_sota5_campaign/run_from_manifest.py \
  --categories ours_multiseed \
  --skip-existing \
  --continue-on-error \
  2>&1 | tee -a "$LOG_FILE"
