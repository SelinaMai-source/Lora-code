import json
import os
import time

runs = [
    "paper_instrdialog_seq_s123_true_fair",
    "paper_instrdialog_router_only_s123_true_fair",
    "paper_instrdialog_periodic_latest_s123_true_fair",
    "paper_instrdialog_bank_no_router_s123_true_fair",
    "paper_instrdialog_replay_b50_s123_true_fair"
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

while True:
    all_done = True
    for run in runs:
        if get_metrics(run) is None:
            all_done = False
            break
    if all_done:
        break
    time.sleep(60)

print("All TRUE fair baselines completed.")
