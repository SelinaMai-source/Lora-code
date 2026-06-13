#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --categories main \
  --variant-ids router_only \
  --batch-size 2 \
  --run-name-suffix fair \
  --set router.num_initial_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_router_only.log
