---
failed_version: v8_sota_11
next_version: v8_sota_12
status: ready
generated_at: 2026-06-13T03:30:00Z
agent_signoff: true
---
# 失败分析：v8_sota_11（router_warmup=2 灾难性早停）

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_11 |
| 终态 | early_stopped |
| 最后 segment | 4（轨迹地板触发） |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_11 |
| 早停 | 是 — seen=0.22 < floor 0.29 @seg4 |

### 六项目标（早停点 seg4/5 eval）

| 指标 | 值 | 目标 | 达标 |
|------|-----|------|------|
| seen_avg_score | **0.220** | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.220 | ≥ 0.6 | ❌ |
| forgetting | **0.225** | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.225 | ≤ 0.077 | ❌ |
| token_f1_mean | 0.381 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | 0.410 | ≥ 0.6 | ❌ |

**判定**：seg4 seen=0.22，远低于冠军 v8_sota_5（0.353@seg18）及 v6_2 地板（0.34@seg4）；比 v8_1/2/3 cliff（~0.30@seg7）更早、更惨。

## 2. 证据链

### 2.1 轨迹 vs v8_sota_5（冠军）vs v6_sota_2（地板）

| seg | seen (v11) | seen (v8_5) | seen (v6_2) | Δ vs v8_5 | oracle (v11) |
|-----|------------|-------------|-------------|-----------|--------------|
| 0 | 0.000 | 0.000 | 0.000 | 0 | 1.0 |
| 1 | 0.000 | 0.000 | 0.050 | 0 | 1.0 |
| 2 | 0.000 | 0.033 | 0.000 | -0.033 | 0.776 |
| 3 | 0.250 | 0.275 | 0.250 | -0.025 | 0.746 |
| 4 | **0.220** | **0.420** | 0.340 | **-0.200** | 0.768 |

- seg4 起 seen 断崖：v8_5 @seg5=0.42，v11 @seg5=0.22（差 0.20）
- seg3 per-segment accuracy：v11 从 1.0 → **0.1**（灾难性遗忘）；v8_5 保持 1.0

### 2.2 路由 / warmup 信号

| 信号 | v8_sota_11 @seg4 | v8_sota_5 @seg4 |
|------|------------------|-----------------|
| router_warmup_segments | **2** | 1 |
| routed_train_fallback (seg0–1) | **50/50 (100%)** | 部分 fallback |
| routed_train_fallback (seg2) | **91/91 (100%)** | 学习路由已介入 |
| routed_train_fallback (seg4 train) | 0/50 | — |
| oracle_agreement | 0.768 | ~0.75 |
| overlap_mean_cosine | 0.569 | ~0.57 |
| num_branches | 3 | 3 |

**关键**：warmup=2 使 seg0–1 完全跳过原型路由学习；seg2 训练仍 100% fallback；seg3 eval 尚可（seen=0.25），seg4 训练路由全开但 seg3 准确率崩塌至 0.1。

### 2.3 日志摘录

```
[2026-06-13 03:18:20] Trajectory early stopping: seen_avg_score 0.22000000000000003 < baseline floor 0.29000000000000004 at segment 4
```

### 2.4 配置差异（vs v8_sota_5）

| 参数 | v8_sota_11 | v8_sota_5 |
|------|------------|-----------|
| router_warmup_segments | **2** | 1 |
| 其余 | 相同 | 相同 |

## 3. 根因分析

**主因**：`router_warmup_segments=2` 过度延后原型路由学习，导致 seg2–3 分支/原型与 LoRA 训练不同步，seg4 路由介入时旧 segment 灾难性遗忘。

**机制**：
- seg0–1 强制 latest-branch（100% fallback），原型 head 无有效梯度
- seg2 虽结束 warmup，训练仍全 fallback → 原型未在分支增多期（b0→b1→b2）充分拟合
- seg4 路由切换至 b1-only 训练，seg3 从 acc=1.0 跌至 0.1 → forgetting=0.225
- oracle 仍 0.77 但 seen 仅 0.22 → 路由–性能严重脱节

**证伪汇总**：
- ❌ router_warmup 延长（v8_sota_11 灾难性，比 cliff 更差）
- ❌ overlap.beta 0.07（v8_sota_10）
- ❌ 4-pass / 高 EMA（v8_sota_8/9）
- ❌ anchor refresh（v8_sota_6）
- ❌ 硬路由（v8_sota_7）
- ✅ **v8_sota_5 仍为唯一可靠基座**

## 4. 下一版方向（→ v8_sota_12）

**策略**：**v8_sota_5 精确复刻**（pipeline 验证 run），零配置变更。

**动机**：v11 单点变更即 catastrophic；需确认 pipeline/环境未退化，能否复现 seen=0.353。

**成功判据**：
- seg5 seen≥0.40（对齐 v8_5 的 0.42）
- seg7 seen≥0.35；终局 seen≥0.35
- 若复现成功 → 下一版再试 spawn-sync + router lr 或 segment-boundary prototype snapshot

## 5. 门禁

- [x] status: ready
- [x] agent_signoff: true
