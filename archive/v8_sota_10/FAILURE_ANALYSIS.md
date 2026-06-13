---
failed_version: v8_sota_9
next_version: v8_sota_10
status: ready
agent_signoff: true
generated_at: 2026-06-13T02:15:00Z
---
# 失败分析：v8_sota_9 → v8_sota_10

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_9 |
| 终态 | early_stopped |
| 最后 segment | 8 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_9 |
| 早停 | 是 |

### 六项目标（早停点 seg8）

| 指标 | 值 | 目标 | 达标 |
|------|-----|------|------|
| seen_avg_score | 0.2944 | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.3370 | ≥ 0.6 | ❌ |
| forgetting | 0.1167 | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.1063 | ≤ 0.077 | ❌ |
| token_f1_mean | 0.3504 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | 0.3550 | ≥ 0.6 | ❌ |

**夺冠判定**：seg8 seen=0.294 远差于冠军 v8_sota_5（0.353@seg18，seg8=0.350）；轨迹早停，未跑完全程。

## 2. 证据链

### 2.1 轨迹 vs v8_sota_5（4-pass 致 seg7–8 cliff）

| seg | seen (v8_9) | seen (v8_5) | Δ | oracle (v8_9) | oracle (v8_5) | overlap (v8_9) |
|-----|-------------|-------------|---|---------------|---------------|----------------|
| 5 | 0.431 | 0.431 | 0.000 | 0.370 | 0.444 | 0.744 |
| 6 | 0.426 | 0.455 | -0.029 | 0.242 | 0.341 | 0.767 |
| 7 | 0.335 | 0.350 | -0.015 | 0.208 | 0.436 | 0.761 |
| 8 | 0.294 | 0.350 | -0.056 | 0.117 | 0.306 | 0.618 |

- seg5 持平；seg6 起 oracle 崩塌，seg8 oracle **0.117** vs v8_5 **0.306**
- 模式复现 v8_sota_1/2/3 seg7 早停 cliff（~0.30），但 v8_5 冠军已用 3-pass 突破

### 2.2 路由 / overlap / 训练（末段 seg8）

| 信号 | v8_sota_9 | v8_sota_5 @seg8 |
|------|-----------|-----------------|
| oracle_agreement | 0.117 | 0.306 |
| overlap_mean_cosine | 0.618 | 0.610 |
| prototype_update_steps | **4** | 3 |
| prototype_ema | **0.9** | 0.8 |
| num_branches | 5 | 5 |

4-pass + 高 EMA 未改善 overlap，oracle 反而远低于 3-pass 冠军。

### 2.3 日志摘录

```
Trajectory early stopping: seen_avg_score 0.29444444444444445 < baseline floor 0.328 at segment 8
```

### 2.4 上一版 CHANGES 摘要

v8_sota_9：v8_sota_5 基座 + `prototype_update_steps: 4` + `prototype_ema: 0.9`（4-pass 峰值保留）。

## 3. 根因分析

**主因**：4-pass 原型 EMA（即使 ema=0.9）在分支≥4、overlap≥0.76 时**累积漂移**，seg6 起 oracle 持续下滑，seg7–8 路由崩溃触发轨迹早停。

**机制**：
- 每段 4 遍伪标签 EMA 放大当段噪声；seg7 router_train_acc=0.0、seg8=0.31
- raw branch 分布（b2/b3）与决策 branch（b4）严重失配 → soft blend 在错误分支上混合
- v8_8 跑完全程亦未夺冠 → 4-pass 路线收益递减且 cliff 风险高

**证伪**：
- ❌ 4-pass（v8_8 末段回落、v8_9 seg7–8 cliff）
- ❌ 硬路由 v8_7、anchor refresh v8_6
- ✅ 回归 v8_sota_5（spawn-sync + 3-pass + soft routing）为唯一可靠基座

## 4. 下一版假设（单点变更）

**基座版本**：**v8_sota_5**（spawn-sync + 3-pass EMA + soft routing，prototype_update_steps=3）

**唯一变更**：`overlap.beta: 0.05 → 0.07`（加强分支正交约束，抑制 seg6–7 overlap≥0.76 时的子空间塌缩）

**动机**：
- v8_5 冠军 seg7–8 seen=0.350 但 oracle 仅 0.31–0.44，routing 仍是瓶颈
- v8_1/2/3 cliff 与 v8_9 均发生在 overlap≈0.76、branch≥4；纯 beta 提升未在 v8_5 基座上试过（v8_2 改的是 routing_aware_beta）
- 更强 overlap 有望在 seg7–8 维持路由可分离性，不增 pass 数、不改路由策略

**成功判据**：
- seg7 seen≥0.35（不低于 v8_5）；seg8 seen≥0.35 且 oracle≥0.30
- 终局 seen≥0.36（超 v8_5 冠军 0.353）

## 5. Novelty 与审稿风险

overlap β 扫描为可消融超参；「分支 overlap 上升时需匹配更强正交正则以保路由」叙事清晰。风险低。

## 6. 门禁清单

- [x] Agent 已将 frontmatter `status: ready`
- [x] `archive/v8_sota_10/CHANGES.md`
- [x] `configs/paper/v8_sota_10.yaml` + `run_v8_sota_10.sh`
