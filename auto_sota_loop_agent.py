import os
import json
import time
import subprocess
import itertools
from pathlib import Path
import datetime

TARGETS_FILE = "/root/autodl-tmp/Lora-code/new_true_sota_targets.json"
BASE_SCRIPT_TEMPLATE = """#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# Ensure WANDB is enabled
python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes ours \
  --categories main \
  --epochs-per-segment 1 \
  --batch-size 4 \
  --run-name-suffix {run_name} \
  --set router.soft_routing=true \
  --set router.soft_routing_temperature=0.08 \
  --set router.soft_routing_top_k=3 \
  --set drift.threshold=0.5 \
  --set bank.max_branches=15 \
  --set router.training_strategy=learned_router \
  --set router.vib_beta=0.01 \
  --set overlap.beta=0.1 \
  --set router.learning_rate=0.01 \
  --set overlap.weight_similarity=cdma \
  --set router.fluid_lambda={fluid_lambda} \
  --set router.fluid_gamma={fluid_gamma} \
  --set router.pid_kp=0.1 \
  --set router.pid_ki=0.01 \
  --set router.pid_kd=0.05 \
  --skip-existing > {log_file} 2>&1
"""

def load_targets():
    with open(TARGETS_FILE, "r") as f:
        return json.load(f)

def is_sota_reached(metrics, targets):
    for key, target_val in targets.items():
        if key not in metrics:
            return False
        if "forgetting" in key:
            if metrics[key] > target_val: return False
        else:
            if metrics[key] < target_val: return False
    return True

def extract_metrics_from_log(log_file):
    if not os.path.exists(log_file): return None
    latest_metrics = None
    try:
        with open(log_file, "r") as f:
            for line in f:
                if "Eval metrics:" in line:
                    try:
                        metrics_str = line.split("Eval metrics:")[1].strip()
                        latest_metrics = json.loads(metrics_str)
                    except: pass
    except: pass
    return latest_metrics

def check_early_stopping(metrics):
    if not metrics: return False
    num_seen = metrics.get("num_seen_segments", 0)
    seen_avg = metrics.get("seen_avg_score", 0.0)
    if num_seen >= 3 and seen_avg < 0.1:
        return True
    return False

def get_next_version():
    archive_dir = Path("/root/autodl-tmp/Lora-code/archive")
    max_v = 0
    if archive_dir.exists():
        for d in archive_dir.iterdir():
            if d.is_dir() and d.name.startswith("v5_sota_"):
                try: max_v = max(max_v, int(d.name.split("_")[-1]))
                except: pass
    return max_v + 1

def log_agent(msg):
    with open("/root/autodl-tmp/Lora-code/agent_master.log", "a") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")
    print(f"[{datetime.datetime.now().isoformat()}] {msg}")

def run_experiment(version, fluid_lambda, fluid_gamma):
    run_name = f"v5_sota_{version}"
    log_file = f"{run_name}.log"
    script_file = f"run_{run_name}.sh"
    
    # 1. Archive core/
    archive_path = f"/root/autodl-tmp/Lora-code/archive/{run_name}"
    os.makedirs(archive_path, exist_ok=True)
    subprocess.run(["cp", "-r", "core", archive_path])
    
    script_content = BASE_SCRIPT_TEMPLATE.format(run_name=run_name, fluid_lambda=fluid_lambda, fluid_gamma=fluid_gamma, log_file=log_file)
    with open(script_file, "w") as f: f.write(script_content)
    os.chmod(script_file, 0o755)
    
    log_agent(f"Starting {run_name} with fluid_lambda={fluid_lambda}, fluid_gamma={fluid_gamma}")
    tmux_session = f"exp_{run_name}"
    
    # Kill if already exists
    subprocess.run(["tmux", "kill-session", "-t", tmux_session], stderr=subprocess.DEVNULL)
    subprocess.run(["tmux", "new-session", "-d", "-s", tmux_session, f"./{script_file}"])
    
    while True:
        time.sleep(30)
        result = subprocess.run(["tmux", "has-session", "-t", tmux_session], capture_output=True)
        is_running = result.returncode == 0
        
        metrics = extract_metrics_from_log(log_file)
        if metrics:
            if check_early_stopping(metrics):
                log_agent(f"Early stopping triggered for {run_name}! Score: {metrics.get('seen_avg_score')}")
                subprocess.run(["tmux", "kill-session", "-t", tmux_session])
                return False, metrics
        
        if not is_running:
            log_agent(f"Experiment {run_name} finished naturally.")
            return True, metrics

def main():
    os.chdir("/root/autodl-tmp/Lora-code")
    targets = load_targets()
    log_agent(f"Started Master loop. Targets: {targets}")
    
    lambdas = [0.1, 0.15, 0.08, 0.2, 0.05]
    gammas = [0.01, 0.015, 0.008, 0.02, 0.005]
    param_grid = list(itertools.product(lambdas, gammas))
    
    for fluid_lambda, fluid_gamma in param_grid:
        # TODO: Here we could inject the LLM-driven core/ modifications for CDMA/Lennard-Jones
        # For now, it searches the hyperparameter space of the current core/ implementation.
        
        version = get_next_version()
        finished, final_metrics = run_experiment(version, fluid_lambda, fluid_gamma)
        
        if finished and final_metrics:
            if is_sota_reached(final_metrics, targets):
                log_agent(f"SOTA REACHED with {version}!")
                log_agent(f"Metrics: {final_metrics}")
                break
        time.sleep(10)

if __name__ == "__main__":
    main()
