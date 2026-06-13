#!/bin/bash
while tmux has-session -t exp_sota_v13 2>/dev/null; do
    sleep 30
done
echo "exp_sota_v13 finished."
