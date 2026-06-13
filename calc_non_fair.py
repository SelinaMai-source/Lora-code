import json
import os

runs = [
    "paper_instrdialog_router_only_s123",
    "paper_instrdialog_periodic_latest_s123",
    "paper_instrdialog_bank_no_router_s123",
    "paper_instrdialog_replay_b50_s123"
]

def get_metrics(run_id):
    path = f"results/runs/{run_id}/final_metrics.json"
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        return None
    with open(path, "r") as f:
        return json.load(f)

for run in runs:
    metrics = get_metrics(run)
    print(run, type(metrics))
