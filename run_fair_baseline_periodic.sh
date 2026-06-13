#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --categories main \
  --variant-ids periodic_latest \
  --batch-size 2 \
  --run-name-suffix fair \
  --set periodic.max_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_periodic.log
