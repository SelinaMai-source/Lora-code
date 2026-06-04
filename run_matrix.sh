#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

# Execute the paper matrix for single seed 123
# Includes baselines, ours_full, and ours ablations
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline,ours \
  --categories main,ablation \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix v2 \
  --skip-existing 2>&1 | tee results/overnight_logs/paper_matrix_$(date +%Y%m%d_%H%M%S).log
