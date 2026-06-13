#!/bin/bash
# v6_sota_4: v6_sota_2 method + baseline-matched training budget (epochs=5, batch=1).
# Launch inside tmux:
#   tmux new-session -d -s v6_sota_4 'bash /root/autodl-tmp/Lora-code/run_v6_sota_4.sh'
set -e
cd /root/autodl-tmp/Lora-code
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 core/train.py --config configs/paper/v6_sota_4.yaml 2>&1 | tee v6_sota_4.log
