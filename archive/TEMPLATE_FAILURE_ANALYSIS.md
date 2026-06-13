---
failed_version: v{N}_sota_{M}
next_version: v{N+1}_sota_{K}
status: draft
generated_at: YYYY-MM-DDTHH:MM:SSZ
agent_signoff: false
---

# 失败分析：{failed_version} → {next_version}

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | |
| 终态 | completed / early_stopped / crashed |
| 最后 segment | |
| run_name | |
| wandb | |
| 早停触发 | |

### 关键指标（终局或早停点）

| 指标 | 值 | SOTA 目标 | 达标 |
|------|-----|-----------|------|
| seen_avg_score | | ≥ 0.600 | |
| seen_avg_task_aware_score | | ≥ 0.600 | |
| forgetting | | ≤ 0.0333 | |
| task_aware_forgetting | | ≤ 0.077 | |
| token_f1_mean | | ≥ 0.600 | |
| lcs_overlap_mean | | ≥ 0.600 | |

## 2. 证据链

### 2.1 metrics.jsonl 轨迹要点
（逐 segment 与 v6_sota_2 对比，标注首次偏离点）

### 2.2 路由 / overlap / 训练
- oracle_agreement 曲线：
- overlap_mean_cosine：
- train budget (epochs/batch)：
- 路由后端 / 混合策略：

### 2.3 日志摘录
```
（Early stopping / crash 相关行）
```

## 3. 根因分析（必选一项为主因）

- [ ] 路由（oracle 低 / 原型漂移 / 硬软路由）
- [ ] 混合干扰（soft blend / 分支重叠）
- [ ] 训练预算（欠拟合 / 过拟合）
- [ ] 漂移检测（误 spawn / 迟 spawn）
- [ ] 评测协议 / 公平性
- [ ] 早停过激进

**主因**：（一句话）

**机制**：（2-4 句，引用上表证据）

## 4. 下一版假设（单点变更，必填）

**基座版本**：（如 v6_sota_2）

**唯一代码/配置变更**：

**预期机制**：

**成功判据**（seg3/seg6/seg18）：

## 5. Novelty（CCF-A）

与最近工作区别（2-3 条）：

## 6. ACL/ARR 审稿风险

| 风险 | 缓解 |
|------|------|
| | |

## 7. 监控门禁

- [ ] `status: ready` 已设置（agent 审阅后）
- [ ] `archive/{next_version}/CHANGES.md` 已写
- [ ] `configs/paper/{next_version}.yaml` + `run_{next_version}.sh` 已就绪

<!-- 审阅完成后将 frontmatter 中 status 改为 ready，agent_signoff 改为 true -->
