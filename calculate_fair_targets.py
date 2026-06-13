import json
import os
import glob
import time

def get_metrics(run_id):
    path = f"results/runs/{run_id}/final_metrics.json"
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

runs = [
    "paper_instrdialog_router_only_s123_fair",
    "paper_instrdialog_periodic_latest_s123_fair",
    "paper_instrdialog_bank_no_router_s123_fair",
    "paper_instrdialog_replay_b50_s123_fair"
]

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
    print(f"\n--- {run} ---")
    for k in best_metrics.keys():
        val = metrics.get(k, 0.0)
        print(f"{k}: {val:.4f}")
        if "forgetting" in k:
            best_metrics[k] = min(best_metrics[k], val)
        else:
            best_metrics[k] = max(best_metrics[k], val)

print("\n=== NEW SOTA TARGETS ===")
targets = {
    "seen_avg_score": best_metrics["seen_avg_score"] * 1.333,
    "seen_avg_task_aware_score": best_metrics["seen_avg_task_aware_score"] * 1.333,
    "forgetting": best_metrics["forgetting"] * 0.666,
    "task_aware_forgetting": best_metrics["task_aware_forgetting"] * 0.666,
    "token_f1_mean": best_metrics["token_f1_mean"] * 1.333,
    "lcs_overlap_mean": best_metrics["lcs_overlap_mean"] * 1.333
}

for k, v in targets.items():
    if "forgetting" in k:
        print(f"{k} < {v:.4f} (Best baseline: {best_metrics[k]:.4f})")
    else:
        print(f"{k} > {v:.4f} (Best baseline: {best_metrics[k]:.4f})")

with open("new_sota_targets.json", "w") as f:
    json.dump(targets, f, indent=2)

