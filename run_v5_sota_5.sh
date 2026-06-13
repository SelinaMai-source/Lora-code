#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 5 \
  --batch-size 1 \
  --run-name-suffix v5_sota_5 \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.08 \
  --set router.soft_routing_top_k=3 \
  --set drift.threshold=0.5 \
  --set bank.max_branches=15 \
  --set router.training_strategy=learned_router \
  --set router.vib_beta=0.05 \
  --set overlap.beta=0.2 \
  --set router.learning_rate=0.01 \
  --set overlap.weight_similarity=information_bottleneck \
  --skip-existing > v5_sota_5.log 2>&1
