#!/bin/bash
# v8_sota_4: v6_sota_2 + spawn-sync prototype init from drift anchors.
set -e
cd /root/autodl-tmp/Lora-code
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 core/train.py --config configs/paper/v8_sota_4.yaml 2>&1 | tee v8_sota_4.log
