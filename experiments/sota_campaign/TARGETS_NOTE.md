# SOTA 战役目标说明

**更新 2026-06-16（用户决策）**

战役成功条件已收窄为相对 advanced LB-CL baseline **+33% margin**：

| 指标 | 阈值 |
|------|------|
| `seen_avg_score` | ≥ 0.3153 |
| `seen_avg_task_aware_score` | ≥ 0.3785 |
| `token_f1_mean` | ≥ 0.4461 |

绝对目标（seen/f1/lcs ≥ 0.6001）**不再**驱动迭代代理升版或停止训练。

历史文件 `new_true_sota_targets.json`（绝对 0.6001 目标）已归档至：
`archive_candidates/root_cleanup_20260615_012746/state/new_true_sota_targets.json`
