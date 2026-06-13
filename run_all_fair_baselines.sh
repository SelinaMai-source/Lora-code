#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

echo "Running router_only"
./run_fair_baseline_router_only.sh

echo "Running periodic"
./run_fair_baseline_periodic.sh

echo "Running bank_no_router"
./run_fair_baseline_bank_no_router.sh

echo "Running replay"
./run_fair_baseline_replay.sh

echo "All fair baselines completed."
