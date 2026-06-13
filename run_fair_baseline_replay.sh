#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --categories main \
  --variant-ids replay_b50 \
  --batch-size 2 \
  --run-name-suffix fair \
  --set replay.buffer_size=200 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_replay.log
