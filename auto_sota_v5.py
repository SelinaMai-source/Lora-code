import json
import os
import time
import subprocess

runs = [
    "paper_instrdialog_router_only_s123_fair",
    "paper_instrdialog_periodic_latest_s123_fair",
    "paper_instrdialog_bank_no_router_s123_fair",
    "paper_instrdialog_replay_b50_s123_fair"
]

def get_metrics(run_id):
    path = f"results/runs/{run_id}/final_metrics.json"
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("final", {})
    except:
        return None

print("Waiting for fair baselines to complete...")
while True:
    all_done = True
    for run in runs:
        if get_metrics(run) is None:
            all_done = False
            break
    if all_done:
        break
    time.sleep(60)

print("All fair baselines completed. Calculating new targets...")

best_metrics = {
    "seen_avg_score": 0.0,
    "seen_avg_task_aware_score": 0.0,
    "forgetting": 1.0,
    "task_aware_forgetting": 1.0,
    "token_f1_mean": 0.0,
    "lcs_overlap_mean": 0.0
}

for run in runs:
    metrics = get_metrics(run)
    for k in best_metrics.keys():
        val = metrics.get(f"eval.{k}", 0.0)
        if "forgetting" in k:
            best_metrics[k] = min(best_metrics[k], val)
        else:
            best_metrics[k] = max(best_metrics[k], val)

targets = {
    "seen_avg_score": best_metrics["seen_avg_score"] * 1.333,
    "seen_avg_task_aware_score": best_metrics["seen_avg_task_aware_score"] * 1.333,
    "forgetting": best_metrics["forgetting"] * 0.666,
    "task_aware_forgetting": best_metrics["task_aware_forgetting"] * 0.666,
    "token_f1_mean": best_metrics["token_f1_mean"] * 1.333,
    "lcs_overlap_mean": best_metrics["lcs_overlap_mean"] * 1.333
}

with open("new_sota_targets.json", "w") as f:
    json.dump(targets, f, indent=2)

print("Targets calculated. Waiting for GPU memory to free up before starting v5_sota_1...")

# Wait until GPU memory usage drops below 5GB
while True:
    try:
        smi_out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True)
        mem_used = int(smi_out.strip())
        if mem_used < 5000:
            break
    except:
        pass
    time.sleep(60)

print("GPU memory is free. Starting v5_sota_1...")

v5_script = """#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \\
  --benchmarks instrdialog \\
  --modes ours \\
  --categories main \\
  --epochs-per-segment 1 \\
  --batch-size 2 \\
  --run-name-suffix v5_sota_1 \\
  --set router.soft_routing=true \\
  --set router.soft_routing_temperature=0.08 \\
  --set router.soft_routing_top_k=3 \\
  --set overlap.beta=0.05 \\
  --set drift.threshold=0.025 \\
  --set bank.max_branches=15 \\
  --set router.learning_rate=0.008 \\
  --set router.training_strategy=learned_router \\
  --set router.prototype_update_ema=true \\
  --set router.prototype_ema_alpha=0.1 \\
  --skip-existing > results/overnight_logs/sota_run_v5_1.log 2>&1
"""

with open("run_v5_sota_1.sh", "w") as f:
    f.write(v5_script)

os.chmod("run_v5_sota_1.sh", 0o755)
subprocess.Popen(["nohup", "./run_v5_sota_1.sh"])
print("v5_sota_1 started in background.")

