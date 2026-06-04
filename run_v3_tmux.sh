#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix v3 \
  --skip-existing 2>&1 | tee results/overnight_logs/paper_matrix_v3_$(date +%Y%m%d_%H%M%S).log
