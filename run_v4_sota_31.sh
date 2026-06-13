#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix v4_sota_31 \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.05 \
  --set router.soft_routing_top_k=3 \
  --set overlap.beta=0.01 \
  --set drift.threshold=0.025 \
  --set bank.max_branches=8 \
  --skip-existing 2>&1 | tee results/overnight_logs/sota_run_v4_31.log
