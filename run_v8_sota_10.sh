#!/bin/bash
# v8_sota_10: v8_sota_5 champion base + stronger overlap beta (0.07).
set -e
cd /root/autodl-tmp/Lora-code
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 core/train.py --config configs/paper/v8_sota_10.yaml 2>&1 | tee v8_sota_10.log
