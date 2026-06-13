#!/bin/bash
# v8_sota_14: v8_sota_5 + router.learning_rate=0.010 (aggressive prototype routing).
set -e
cd /root/autodl-tmp/Lora-code
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 core/train.py --config configs/paper/v8_sota_14.yaml 2>&1 | tee v8_sota_14.log
