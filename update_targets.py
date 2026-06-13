import json

targets = {
  "seen_avg_score": 0.6001,
  "seen_avg_task_aware_score": 0.6001,
  "forgetting": 0.0333,
  "task_aware_forgetting": 0.0770,
  "token_f1_mean": 0.6001,
  "lcs_overlap_mean": 0.6001
}

with open('/root/autodl-tmp/Lora-code/new_true_sota_targets.json', 'w') as f:
    json.dump(targets, f, indent=2)

print("Targets updated to >= 0.6 for main metrics.")
