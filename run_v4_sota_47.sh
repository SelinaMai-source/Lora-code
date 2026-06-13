#!/bin/bash
cd /root/autodl-tmp/Lora-code

WANDB_MODE=offline python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix v4_sota_47 \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.05 \
  --set router.soft_routing_top_k=3 \
  --set overlap.beta=0.03 \
  --set drift.threshold=0.024 \
  --set bank.max_branches=15 \
  --set router.learning_rate=0.01 \
  --set router.training_strategy=learned_router \
  --skip-existing > results/overnight_logs/sota_run_v4_47.log 2>&1

echo "EXIT_CODE=$?" >> results/overnight_logs/sota_run_v4_47.log
