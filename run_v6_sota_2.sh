#!/bin/bash
set -e
cd "$(dirname "$0")"
WANDB_MODE=online python3 core/train.py --config configs/paper/v6_sota_2.yaml
