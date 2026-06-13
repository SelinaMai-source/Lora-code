#!/bin/bash
# v8_sota_15: v8_sota_5 + prototype_ema=0.85 (damp prototype overshoot after v14 lr failure).
set -e
cd /root/autodl-tmp/Lora-code
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 core/train.py --config configs/paper/v8_sota_15.yaml 2>&1 | tee v8_sota_15.log
