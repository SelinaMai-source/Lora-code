#!/usr/bin/env bash
# 单 GPU 串行执行四阶段战役（严格顺序）：
#   Phase 1: phase1_priority (1)
#   Phase 2: baseline_multiseed (30)
#   Phase 3: ablation_single_seed (10)
#   Phase 4: ours_multiseed (6)
# --skip-existing 仅当 final_metrics.json 存在时跳过；--continue-on-error 遇错继续。
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<EOF
Usage: bash run_campaign_phased.sh [phase ...]

  无参数：按 Phase 1→4 顺序跑完全部 manifest。
  指定 phase 编号：仅跑对应阶段（如 bash run_campaign_phased.sh 1）。
EOF
  exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source experiments/v8_sota5_campaign/campaign.env

LOG_DIR="$ROOT/results/logs/v8_sota5_campaign"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/campaign_phased_$(date +%Y%m%d_%H%M%S).log"

MANIFEST_ARGS=(
  --skip-existing
  --continue-on-error
)

declare -A PHASE_CATEGORY=(
  [1]="phase1_priority"
  [2]="baseline_multiseed"
  [3]="ablation_single_seed"
  [4]="ours_multiseed"
)

declare -A PHASE_LABEL=(
  [1]="Phase 1: v8_sota_5 instrdialog++ seed=123 (priority)"
  [2]="Phase 2: baselines × 3 seeds × 2 benchmarks"
  [3]="Phase 3: ablation seed=123 (instrdialog + instrdialog++)"
  [4]="Phase 4: v8_sota_5 ours × 3 seeds × 2 benchmarks"
)

if [[ $# -gt 0 ]]; then
  PHASES=("$@")
else
  PHASES=(1 2 3 4)
fi

echo "WANDB_PROJECT=$WANDB_PROJECT" | tee -a "$LOG_FILE"
echo "Phased campaign: ${PHASES[*]}" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"

_run_phase() {
  local phase="$1"
  local category="${PHASE_CATEGORY[$phase]:-}"
  if [[ -z "$category" ]]; then
    echo "[error] unknown phase: $phase" | tee -a "$LOG_FILE"
    return 1
  fi
  echo "======== ${PHASE_LABEL[$phase]} (category=$category) ========" | tee -a "$LOG_FILE"
  python3 experiments/v8_sota5_campaign/run_from_manifest.py \
    --phases "$phase" \
    "${MANIFEST_ARGS[@]}" \
    2>&1 | tee -a "$LOG_FILE"
  local manifest_exit=${PIPESTATUS[0]}

  if [[ "$phase" == "1" ]]; then
    local run_name
    run_name="$(python3 - <<'PY'
import csv
from pathlib import Path
rows = list(csv.DictReader(Path("experiments/v8_sota5_campaign/manifest.csv").open(encoding="utf-8")))
for r in rows:
    if r.get("phase") == "1":
        print(r["run_name"])
        break
PY
)"
    if [[ -n "$run_name" ]] && [[ -f "$ROOT/results/runs/$run_name/final_metrics.json" ]]; then
      echo "[phase1] triggering on_run_complete for $run_name" | tee -a "$LOG_FILE"
      bash experiments/v8_sota5_campaign/on_run_complete.sh \
        --run-name "$run_name" --phase 1 \
        2>&1 | tee -a "$LOG_FILE" || true
    else
      echo "[phase1] FAILED — final_metrics.json missing for $run_name; stopping campaign (Phase 2+ will NOT run)." | tee -a "$LOG_FILE"
      return 1
    fi
  fi

  return "${manifest_exit:-0}"
}

for phase in "${PHASES[@]}"; do
  if ! _run_phase "$phase"; then
    echo "[campaign-phased] aborted at phase $phase" | tee -a "$LOG_FILE"
    exit 1
  fi
done

echo "[campaign-phased] finished phases: ${PHASES[*]}" | tee -a "$LOG_FILE"
