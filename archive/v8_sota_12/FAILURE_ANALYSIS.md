---
failed_version: v8_sota_11
next_version: v8_sota_12
status: ready
generated_at: 2026-06-13T03:30:00Z
agent_signoff: true
---
# 失败分析：v8_sota_11 → v8_sota_12

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_11 |
| 终态 | early_stopped |
| 最后 segment | 4 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_11 |
| 早停 | 是 |

### 六项目标（终局/早停点）

| 指标 | 值 | 目标 | 达标 |
|------|-----|------|------|
| seen_avg_score | 0.2200 | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.2200 | ≥ 0.6 | ❌ |
| forgetting | 0.2250 | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.2250 | ≤ 0.077 | ❌ |
| token_f1_mean | 0.3814 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | 0.4101 | ≥ 0.6 | ❌ |

**夺冠判定**：seg4 seen=0.22，远低于冠军 v8_sota_5（0.353）及 v6_2 地板（0.34@seg4）；灾难性，劣于 cliff runs。

## 2. 证据链

### 2.1 轨迹 vs v8_sota_5（冠军）

| seg | seen (v11) | seen (v8_5) | Δ | oracle (v11) | overlap_cos |
|-----|------------|-------------|---|--------------|-------------|
| 0 | 0.000 | 0.000 | 0 | 1.0 | 0.0 |
| 1 | 0.000 | 0.000 | 0 | 1.0 | 0.0 |
| 2 | 0.000 | 0.033 | -0.033 | 0.776 | 0.779 |
| 3 | 0.250 | 0.275 | -0.025 | 0.746 | 0.660 |
| 4 | **0.220** | **0.420** | **-0.200** | 0.768 | 0.569 |

- seg4 断崖：v8_5 @seg5=0.42 vs v11 @seg5=0.22
- seg3 accuracy 1.0→0.1（forgetting=0.225）

### 2.2 路由 / overlap / 训练（末段 seg4）

| 信号 | v8_sota_11 | v8_sota_5 |
|------|------------|-----------|
| router_warmup_segments | **2** | 1 |
| fallback seg0–1 | 100% | partial |
| fallback seg2 | 100% | learned routing active |
| oracle_agreement | 0.768 | ~0.75 |
| num_branches | 3 | 3 |

### 2.3 日志摘录

```
[2026-06-13 03:18:20] Trajectory early stopping: seen_avg_score 0.22000000000000003 < baseline floor 0.29000000000000004 at segment 4
```

### 2.4 上一版 CHANGES 摘要

v8_sota_11：v8_sota_5 + `router_warmup_segments: 2`（seg0–1 强制 latest-branch）。

## 3. 根因分析

**主因**：router_warmup=2 证伪 — 过度延后原型路由学习，seg4 路由切换引发 seg3 灾难性遗忘。

**机制**：
- seg0–2 原型 head 几乎无有效训练（100% fallback）
- seg4 路由全开时旧 segment acc 从 1.0→0.1
- oracle 0.77 但 seen 0.22 → 路由–性能严重脱节

**已证伪路线**：4-pass、hard routing、anchor refresh、overlap.beta 0.07、router_warmup 延长。

## 4. 下一版假设（单点变更）

**基座版本**：**v8_sota_5**（spawn-sync + 3-pass + soft routing + warmup=1 + overlap.beta=0.05）

**唯一变更**：**无** — v8_sota_12 为 v8_sota_5 精确复刻（仅 run_name/tags 不同），验证 pipeline 能否复现 seen=0.353。

**动机**：
- v11 单点变更即 catastrophic，需排除环境/pipeline 退化
- 复现成功后再试：spawn-sync + router lr 调整，或 3-pass + segment-boundary prototype snapshot

**成功判据**：
- seg5 seen≥0.40；seg7 seen≥0.35；终局 seen≥0.35（对齐 v8_5 冠军）
- 若失败 → 检查代码/数据 drift，非超参问题

## 5. Novelty 与审稿风险

pipeline 验证 run，无新 novelty；为后续增量实验提供可靠 baseline。风险无。

## 6. 门禁清单

- [x] Agent 已将 frontmatter `status: ready`
- [x] `archive/v8_sota_12/CHANGES.md`
- [x] `configs/paper/v8_sota_12.yaml` + `run_v8_sota_12.sh`
