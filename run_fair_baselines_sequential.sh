#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

echo "Running router_only"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids router_only \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair \
  --set router.num_initial_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_router_only.log

echo "Running periodic_latest"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids periodic_latest \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair \
  --set periodic.max_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_periodic.log

echo "Running bank_no_router"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids bank_no_router \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair \
  --set bank.max_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_bank_no_router.log

echo "Running replay_b50"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids replay_b50 \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair \
  --set replay.buffer_size=200 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_replay.log

