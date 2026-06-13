#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 4 \
  --run-name-suffix v5_sota_31 \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.08 \
  --set router.soft_routing_top_k=3 \
  --set drift.threshold=0.5 \
  --set bank.max_branches=15 \
  --set router.training_strategy=learned_router \
  --set router.ising_beta=1.5 \
  --set router.ising_steps=3 \
  --set router.ising_j_scale=0.05 \
  --set overlap.beta=0.1 \
  --set router.learning_rate=0.01 \
  --set overlap.weight_similarity=lennard_jones \
  --skip-existing > v5_sota_31.log 2>&1
