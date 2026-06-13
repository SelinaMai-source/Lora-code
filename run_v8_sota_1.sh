#!/bin/bash
# v8_sota_1: v6_sota_2 + orthogonal-gated soft top-3 blend at eval.
# Launch inside tmux:
#   tmux new-session -d -s v8_sota_1 'bash /root/autodl-tmp/Lora-code/run_v8_sota_1.sh'
set -e
cd /root/autodl-tmp/Lora-code
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 core/train.py --config configs/paper/v8_sota_1.yaml 2>&1 | tee v8_sota_1.log
