#!/bin/bash
TARGET_PID=$1
while ps -p $TARGET_PID > /dev/null
do
    sleep 30
done

echo "Process $TARGET_PID finished."
touch /root/autodl-tmp/Lora-code/v12_done.flag
echo "Flag /root/autodl-tmp/Lora-code/v12_done.flag created."
