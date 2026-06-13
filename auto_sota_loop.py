import os
import json
import time
import subprocess
import itertools
from pathlib import Path

TARGETS_FILE = "/root/autodl-tmp/Lora-code/new_true_sota_targets.json"
BASE_SCRIPT_TEMPLATE = """#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
WANDB_MODE=offline python3 scripts/run_paper_matrix.py \\
  --benchmarks instrdialog \\
  --modes ours \\
  --categories main \\
  --epochs-per-segment 1 \\
  --batch-size 4 \\
  --run-name-suffix {run_name} \\
  --set router.soft_routing=true \\
  --set router.soft_routing_temperature=0.08 \\
  --set router.soft_routing_top_k=3 \\
  --set drift.threshold=0.5 \\
  --set bank.max_branches=15 \\
  --set router.training_strategy=learned_router \\
  --set router.vib_beta=0.01 \\
  --set overlap.beta=0.1 \\
  --set router.learning_rate=0.01 \\
  --set overlap.weight_similarity=lennard_jones \\
  --set router.fluid_lambda={fluid_lambda} \\
  --set router.fluid_gamma={fluid_gamma} \\
  --skip-existing > {log_file} 2>&1
"""

def load_targets():
    with open(TARGETS_FILE, "r") as f:
        return json.load(f)

def is_sota_reached(metrics, targets):
    # Check if all targeted metrics are met or exceeded
    for key, target_val in targets.items():
        if key not in metrics:
            return False
        # Assuming higher is better
        if metrics[key] < target_val:
            return False
    return True

def extract_metrics_from_log(log_file):
    if not os.path.exists(log_file):
        return None
    
    latest_metrics = None
    try:
        with open(log_file, "r") as f:
            for line in f:
                if "Eval metrics:" in line:
                    try:
                        metrics_str = line.split("Eval metrics:")[1].strip()
                        latest_metrics = json.loads(metrics_str)
                    except:
                        pass
    except Exception as e:
        print(f"Error reading log {log_file}: {e}")
    return latest_metrics

def check_early_stopping(metrics):
    if not metrics:
        return False
    
    # Early stopping logic: if segment >= 3 and seen_avg_score < 0.1, stop
    num_seen = metrics.get("num_seen_segments", 0)
    seen_avg = metrics.get("seen_avg_score", 0.0)
    
    if num_seen >= 3 and seen_avg < 0.1:
        return True
    return False

def run_experiment(version, fluid_lambda, fluid_gamma):
    run_name = f"v5_sota_{version}"
    log_file = f"{run_name}.log"
    script_file = f"run_{run_name}.sh"
    
    script_content = BASE_SCRIPT_TEMPLATE.format(
        run_name=run_name,
        fluid_lambda=fluid_lambda,
        fluid_gamma=fluid_gamma,
        log_file=log_file
    )
    
    with open(script_file, "w") as f:
        f.write(script_content)
    os.chmod(script_file, 0o755)
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting experiment {run_name} with fluid_lambda={fluid_lambda}, fluid_gamma={fluid_gamma}")
    
    # Start in tmux
    tmux_session = f"exp_{run_name}"
    subprocess.run(["tmux", "new-session", "-d", "-s", tmux_session, f"./{script_file}"])
    
    # Monitor loop
    while True:
        time.sleep(30)
        
        # Check if tmux session is still running
        result = subprocess.run(["tmux", "has-session", "-t", tmux_session], capture_output=True)
        is_running = result.returncode == 0
        
        metrics = extract_metrics_from_log(log_file)
        
        if metrics:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {run_name} Segments: {metrics.get('num_seen_segments', 0)}, Score: {metrics.get('seen_avg_score', 0):.4f}")
            
            if check_early_stopping(metrics):
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Early stopping triggered for {run_name}!")
                subprocess.run(["tmux", "kill-session", "-t", tmux_session])
                return False, metrics
        
        if not is_running:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Experiment {run_name} finished.")
            return True, metrics

def main():
    os.chdir("/root/autodl-tmp/Lora-code")
    targets = load_targets()
    print(f"Targets to reach: {targets}")
    
    # Grid search parameters for smooth iteration
    lambdas = [0.1, 0.15, 0.08, 0.2, 0.05]
    gammas = [0.01, 0.015, 0.008, 0.02, 0.005]
    
    param_grid = list(itertools.product(lambdas, gammas))
    
    version = 17
    for fluid_lambda, fluid_gamma in param_grid:
        finished, final_metrics = run_experiment(version, fluid_lambda, fluid_gamma)
        
        if finished and final_metrics:
            if is_sota_reached(final_metrics, targets):
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] SOTA REACHED with {version}! fluid_lambda={fluid_lambda}, fluid_gamma={fluid_gamma}")
                print(f"Final metrics: {final_metrics}")
                break
        
        version += 1
        time.sleep(10)

if __name__ == "__main__":
    main()
