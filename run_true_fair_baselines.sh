#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

echo "Running sequential_lora (True Fair)"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids seq \
  --epochs-per-segment 5 \
  --batch-size 1 \
  --run-name-suffix true_fair \
  --skip-existing > results/overnight_logs/true_fair_seq.log 2>&1

echo "Running router_only (True Fair)"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids router_only \
  --epochs-per-segment 5 \
  --batch-size 1 \
  --run-name-suffix true_fair \
  --set router.num_initial_branches=15 \
  --skip-existing > results/overnight_logs/true_fair_router_only.log 2>&1

echo "Running periodic_latest (True Fair)"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids periodic_latest \
  --epochs-per-segment 5 \
  --batch-size 1 \
  --run-name-suffix true_fair \
  --set periodic.max_branches=15 \
  --skip-existing > results/overnight_logs/true_fair_periodic.log 2>&1

echo "Running bank_no_router (True Fair)"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids bank_no_router \
  --epochs-per-segment 5 \
  --batch-size 1 \
  --run-name-suffix true_fair \
  --set bank.max_branches=15 \
  --skip-existing > results/overnight_logs/true_fair_bank_no_router.log 2>&1

echo "Running replay_b50 (True Fair)"
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids replay_b50 \
  --epochs-per-segment 5 \
  --batch-size 1 \
  --run-name-suffix true_fair \
  --set replay.buffer_size=200 \
  --skip-existing > results/overnight_logs/true_fair_replay.log 2>&1

echo "All true fair baselines completed."
