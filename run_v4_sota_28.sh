#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix v4_sota_28 \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.1 \
  --set router.soft_routing_top_k=5 \
  --set overlap.beta=0.05 \
  --set drift.threshold=0.02 \
  --skip-existing 2>&1 | tee results/overnight_logs/sota_run_v4_28.log
