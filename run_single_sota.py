import os
import json
import subprocess
import time

TARGETS_FILE = "/root/autodl-tmp/Lora-code/new_true_sota_targets.json"

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

def check_early_stopping(metrics):
    if not metrics: return False
    num_seen = metrics.get("num_seen_segments", 0)
    seen_avg = metrics.get("seen_avg_score", 0.0)
    if num_seen >= 3 and seen_avg < 0.1:
        return True
    return False

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

def main():
    targets = load_targets()
    
    # Get version
    archive_dir = "/root/autodl-tmp/Lora-code/archive"
    os.makedirs(archive_dir, exist_ok=True)
    max_v = 0
    for d in os.listdir(archive_dir):
        if d.startswith("v5_sota_"):
            try: max_v = max(max_v, int(d.split("_")[-1]))
            except: pass
    version = max_v + 1
    
    run_name = f"v5_sota_{version}"
    log_file = f"{run_name}.log"
    
    # Archive core
    subprocess.run(["cp", "-r", "core", f"{archive_dir}/{run_name}"])
    
    script_content = f"""#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
python3 scripts/run_paper_matrix.py \\
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
  --set overlap.weight_similarity=cdma \\
  --set router.fluid_lambda=0.1 \\
  --set router.fluid_gamma=0.01 \\
  --set router.pid_kp=0.1 \\
  --set router.pid_ki=0.01 \\
  --set router.pid_kd=0.05 \\
  --skip-existing > {log_file} 2>&1
"""
    with open(f"run_{run_name}.sh", "w") as f:
        f.write(script_content)
    os.chmod(f"run_{run_name}.sh", 0o755)
    
    print(f"Starting {run_name}...")
    tmux_session = f"exp_{run_name}"
    subprocess.run(["tmux", "kill-session", "-t", tmux_session], stderr=subprocess.DEVNULL)
    subprocess.run(["tmux", "new-session", "-d", "-s", tmux_session, f"./run_{run_name}.sh"])
    
    while True:
        time.sleep(10)
        result = subprocess.run(["tmux", "has-session", "-t", tmux_session], capture_output=True)
        is_running = result.returncode == 0
        
        metrics = extract_metrics_from_log(log_file)
        if metrics:
            if check_early_stopping(metrics):
                print(f"EXPERIMENT_FAILED: Early stopping triggered. Score: {metrics.get('seen_avg_score')}")
                subprocess.run(["tmux", "kill-session", "-t", tmux_session])
                return
        
        if not is_running:
            # Check if it crashed
            with open(log_file, "r") as f:
                content = f.read()
                if "CUDA out of memory" in content or "Traceback" in content:
                    print("EXPERIMENT_FAILED: Crashed or OOM.")
                    return
            
            if metrics and is_sota_reached(metrics, targets):
                print("EXPERIMENT_SUCCESS: SOTA REACHED!")
            else:
                print("EXPERIMENT_FAILED: Finished but SOTA not reached.")
            return

if __name__ == "__main__":
    main()
