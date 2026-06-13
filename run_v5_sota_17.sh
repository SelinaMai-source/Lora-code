#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
WANDB_MODE=offline python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 4 \
  --run-name-suffix v5_sota_17 \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.08 \
  --set router.soft_routing_top_k=3 \
  --set drift.threshold=0.5 \
  --set bank.max_branches=15 \
  --set router.training_strategy=learned_router \
  --set router.vib_beta=0.01 \
  --set overlap.beta=0.1 \
  --set router.learning_rate=0.01 \
  --set overlap.weight_similarity=lennard_jones \
  --set router.fluid_lambda=0.1 \
  --set router.fluid_gamma=0.01 \
  --skip-existing > v5_sota_17.log 2>&1
