#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix v4_sota_42 \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.08 \
  --set router.soft_routing_top_k=3 \
  --set overlap.beta=0.03 \
  --set drift.threshold=0.025 \
  --set bank.max_branches=15 \
  --set router.learning_rate=0.008 \
  --set router.training_strategy=learned_router \
  --skip-existing 2>&1 | tee results/overnight_logs/sota_run_v4_42.log
