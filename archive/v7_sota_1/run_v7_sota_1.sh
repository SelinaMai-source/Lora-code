#!/bin/bash
# v7_sota_1: calibrated prototype router + uncertainty-gated NLL arbitration.
# Launch inside tmux:
#   tmux new-session -d -s v7_sota_1 'bash /root/autodl-tmp/Lora-code/run_v7_sota_1.sh'
set -e
cd /root/autodl-tmp/Lora-code
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 core/train.py --config configs/paper/v7_sota_1.yaml 2>&1 | tee v7_sota_1.log
