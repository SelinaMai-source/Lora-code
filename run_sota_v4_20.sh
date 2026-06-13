#!/bin/bash
cd /root/autodl-tmp/Lora-code
export PYTHONPATH=$(pwd)
export CUDA_VISIBLE_DEVICES=0

RUN_ID="paper_instrdialog_ours_full_s123_v4_sota_20"
LOG_FILE="results/overnight_logs/sota_run_v4_20.log"

# Create a temporary config with the new run_id
TEMP_CONFIG=$(mktemp --suffix .yaml)
cp configs/paper/instrdialog__ours_full__s123.yaml $TEMP_CONFIG
sed -i "s/run_name: .*/run_name: $RUN_ID/" $TEMP_CONFIG

echo "Starting run $RUN_ID" > $LOG_FILE
python core/train.py --config $TEMP_CONFIG >> $LOG_FILE 2>&1
