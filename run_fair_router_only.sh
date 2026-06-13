#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids router_only \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair_15 \
  --set router.num_initial_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_router_only.log
