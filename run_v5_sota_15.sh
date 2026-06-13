#!/bin/bash
export WANDB_MODE=offline
python scripts/run_paper_matrix.py --run-names paper_instrdialog_ours_full_s123 --run-name-suffix v5_sota_15 \
  --set router.fluid_lambda=0.1 \
  --set router.fluid_gamma=0.01
