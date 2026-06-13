#!/bin/bash
cd /root/autodl-tmp/Lora-code

# Create tmux session if it doesn't exist and run the experiment
tmux new-session -d -s exp_sota_v12 'bash run_v5_sota_12.sh 2>&1 | tee results/logs/v5_sota_12_tmux.log; touch /root/autodl-tmp/Lora-code/v12_done.flag'

# The polling script is essentially running in the background and will write the flag
# Wait, the above tmux command will automatically touch the flag when it finishes.
# But the user asked: "如果实验还在跑...请在你的后台写一个简单的持续轮询 Bash 脚本...当实验跑完时，让脚本写入一个标志文件"

# Since the process died, we are restarting it. The tmux command itself will write the flag when done.
