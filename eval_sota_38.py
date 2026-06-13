import json

def check_criteria():
    with open('/root/autodl-tmp/Lora-code/results/runs/paper_instrdialog_ours_full_s123_v4_sota_38/final_metrics.json', 'r') as f:
        data = json.load(f)
    
    final = data['final']
    
    criteria = {
        'eval.seen_avg_score': (final['eval.seen_avg_score'], 0.3017, '>'),
        'eval.seen_avg_task_aware_score': (final['eval.seen_avg_task_aware_score'], 0.4618, '>'),
        'eval.forgetting': (final['eval.forgetting'], 0.1067, '<'),
        'eval.task_aware_forgetting': (final['eval.task_aware_forgetting'], 0.0592, '<'),
        'eval.token_f1_mean': (final['eval.token_f1_mean'], 0.4074, '>'),
        'eval.lcs_overlap_mean': (final['eval.lcs_overlap_mean'], 0.4529, '>')
    }
    
    all_passed = True
    for k, (val, threshold, op) in criteria.items():
        if op == '>':
            passed = val > threshold
        else:
            passed = val < threshold
            
        print(f"{k}: {val:.4f} {op} {threshold:.4f} -> {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_passed = False
            
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")

if __name__ == '__main__':
    check_criteria()
