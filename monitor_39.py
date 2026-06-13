import time
import json
import subprocess
import os

LOG_FILE = "/root/autodl-tmp/Lora-code/v5_sota_39.log"
TMUX_SESSION = "exp_v5_sota_39"

def check_metrics():
    if not os.path.exists(LOG_FILE):
        return None
    latest = None
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                if "Eval metrics:" in line:
                    latest = json.loads(line.split("Eval metrics:")[1].strip())
    except:
        pass
    return latest

while True:
    time.sleep(30)
    result = subprocess.run(["tmux", "has-session", "-t", TMUX_SESSION], capture_output=True)
    if result.returncode != 0:
        print('AGENT_LOOP_WAKE_SOTA_MONITOR {"prompt":"Experiment v5_sota_39 finished or died."}', flush=True)
        break
    
    metrics = check_metrics()
    if metrics:
        seen = metrics.get("num_seen_segments", 0)
        score = metrics.get("seen_avg_score", 0.0)
        if seen >= 3 and score < 0.1:
            subprocess.run(["tmux", "kill-session", "-t", TMUX_SESSION])
            print(f'AGENT_LOOP_WAKE_SOTA_MONITOR {{"prompt":"Experiment v5_sota_39 triggered early stopping (score {score} at segment {seen}). Optimize code and start v5_sota_40."}}', flush=True)
            break
