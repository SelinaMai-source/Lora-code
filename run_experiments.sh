#!/bin/bash
set -e
echo "Starting baseline experiment..."
WANDB_MODE=online python3 core/train.py --config configs/baseline.yaml 2>&1 | tee results/overnight_logs/paper_baseline_$(date +%Y%m%d_%H%M%S).log
echo "Baseline completed. Starting ours experiment..."
WANDB_MODE=online python3 core/train.py --config configs/ours.yaml 2>&1 | tee results/overnight_logs/paper_ours_$(date +%Y%m%d_%H%M%S).log
echo "All experiments completed."
