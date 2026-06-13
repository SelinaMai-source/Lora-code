#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids bank_no_router \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair_15 \
  --set bank.max_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_bank.log
