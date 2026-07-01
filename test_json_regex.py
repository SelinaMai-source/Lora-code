import re, json

line = '[2026-07-01 20:50:52] Eval metrics: {"current_score": 0.25, "seen_avg_score": 0.0625, "forgetting": 0.0, "num_seen_segments": 4, "extra": {"per_segment_accuracy": [{"segment_id": 0, "accuracy": 0.0}, {"segment_id": 1, "accuracy": 0.0}, {"segment_id": 2, "accuracy": 0.0}, {"segment_id": 3, "accuracy": 0.25}], "routing": {"num_routed": 30400, "branch_counts": {"b0": 30400}}}}'

eval_lines = re.findall(r'Eval metrics:\s*({.*})', line)
print(eval_lines)
if eval_lines:
    try:
        data = json.loads(eval_lines[-1])
        print("Success:", data["current_score"])
    except Exception as e:
        print("Error:", e)
